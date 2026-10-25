#!/usr/bin/env python3
"""Small, reproducible feature-space pilot for incremental NIDS adaptation.

This is a protocol/pipeline pilot, not the paper's confirmatory experiment.

*** run_pilot_v2.py: Tier 2 extension of run_pilot.py (the original is untouched). ***
Everything that existed before is computed exactly as before (same RNG streams, same
columns). Additions, all PROPOSED until actually run and checked:
  1. Extra logged columns: pre_attack_detection_rate, attack_induced_asr,
     asr_recalibrated, attack_induced_asr_recalibrated, clean_auc.
  2. --control-arm: a sixth arm, "clean_continued", that receives the same extra
     training epochs as the static arm but no adversarial examples.
  3. The original multi-step attack has no random start, so it is a BIM (iterative FGSM)
     and is labelled "BIM-like" here (the final matrix called it "PGD-like"; same attack).
     --random-start / --alpha-scale allow a genuine PGD, labelled "PGD-RS". OPTIONAL, run only if time allows.
  4. --out-dir: results go to results_ext/ by default so the final matrix is never overwritten.
It uses the official UNSW-NB15 train/test partition, keeps test rows out of
training and adaptation, and labels generated evasions with their known
dataset labels (a simulated label oracle).
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "UNSW-NB15"
OUT = ROOT / "results"
PERTURB_FEATURES = ["dur", "rate", "sload", "dload", "sinpkt", "dinpkt", "sjit", "djit", "tcprtt", "synack", "ackdat"]
UNSW_COLUMNS = [
    "id", "dur", "proto", "service", "state", "spkts", "dpkts", "sbytes", "dbytes",
    "rate", "sttl", "dttl", "sload", "dload", "sloss", "dloss", "sinpkt", "dinpkt",
    "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin", "tcprtt", "synack", "ackdat",
    "smean", "dmean", "trans_depth", "response_body_len", "ct_srv_src", "ct_state_ttl",
    "ct_dst_ltm", "ct_src_dport_ltm", "ct_dst_sport_ltm", "ct_dst_src_ltm", "is_ftp_login",
    "ct_ftp_cmd", "ct_flw_http_mthd", "ct_src_ltm", "ct_srv_dst", "is_sm_ips_ports",
    "attack_cat", "label",
]


class MLP:
    def __init__(self, n_in: int, seed: int):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, np.sqrt(2 / n_in), (n_in, 48)).astype(np.float32)
        self.b1 = np.zeros(48, np.float32)
        self.W2 = rng.normal(0, np.sqrt(2 / 48), (48, 1)).astype(np.float32)
        self.b2 = np.zeros(1, np.float32)
        self.m = [np.zeros_like(x) for x in self.params]
        self.v = [np.zeros_like(x) for x in self.params]
        self.step = 0

    @property
    def params(self):
        return [self.W1, self.b1, self.W2, self.b2]

    def forward(self, x):
        h = np.maximum(x @ self.W1 + self.b1, 0)
        z = h @ self.W2 + self.b2
        return z.reshape(-1), h

    def prob(self, x):
        z, _ = self.forward(x)
        z = np.clip(z, -30, 30)
        return 1 / (1 + np.exp(-z))

    def predict_label(self, x, threshold):
        """Attacker-visible hard label only; never returns score or margin."""
        return (self.prob(x) >= threshold).astype(np.int8)

    def grad_input_target_benign(self, x):
        # Gradient of BCE with target 0; descending it pushes attack score down.
        z, h = self.forward(x)
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        dz = p[:, None]
        dh = dz @ self.W2.T
        dh[h <= 0] = 0
        return dh @ self.W1.T

    def train(self, X, y, epochs=5, batch=256, lr=0.001, seed=0):
        if len(X) == 0:
            return 0.0
        rng = np.random.default_rng(seed)
        start = time.perf_counter()
        for _ in range(epochs):
            order = rng.permutation(len(X))
            for ids in np.array_split(order, max(1, int(np.ceil(len(order) / batch)))):
                x, t = X[ids], y[ids].reshape(-1, 1)
                z, h = self.forward(x)
                p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
                dz = (p.reshape(-1, 1) - t) / max(1, len(ids))
                gW2 = h.T @ dz
                gb2 = dz.sum(axis=0)
                dh = dz @ self.W2.T
                dh[h <= 0] = 0
                gW1 = x.T @ dh
                gb1 = dh.sum(axis=0)
                self.step += 1
                for i, (param, grad) in enumerate(zip(self.params, [gW1, gb1, gW2, gb2])):
                    self.m[i] = .9 * self.m[i] + .1 * grad
                    self.v[i] = .999 * self.v[i] + .001 * grad * grad
                    mh = self.m[i] / (1 - .9 ** self.step)
                    vh = self.v[i] / (1 - .999 ** self.step)
                    param -= lr * mh / (np.sqrt(vh) + 1e-8)
        return time.perf_counter() - start


def stratified_split(y, seed, fractions=(.70, .15, .15)):
    rng = np.random.default_rng(seed)
    parts = [[], [], []]
    for cls in np.unique(y):
        ids = rng.permutation(np.flatnonzero(y == cls))
        n0 = int(len(ids) * fractions[0])
        n1 = int(len(ids) * fractions[1])
        for part, group in zip(parts, (ids[:n0], ids[n0:n0+n1], ids[n0+n1:])):
            part.extend(group.tolist())
    return [np.asarray(x, dtype=int) for x in parts]


def prepare_raw(train_df, test_df):
    if "label" not in train_df or "label" not in test_df:
        raise ValueError("Expected the binary target column 'label' in both CSVs.")
    ytr = train_df["label"].astype(int).to_numpy()
    yte = test_df["label"].astype(int).to_numpy()
    drop = {"label", "attack_cat", "id"}
    tr = train_df.drop(columns=[c for c in drop if c in train_df], errors="ignore")
    te = test_df.drop(columns=[c for c in drop if c in test_df], errors="ignore")
    return tr, ytr, te, yte


def fit_preprocessor(reference_df, frames):
    """Fit categorical levels, imputation values, and ranges on initial training only."""
    cats = [c for c in reference_df.columns if not pd.api.types.is_numeric_dtype(reference_df[c])]
    nums = [c for c in reference_df.columns if c not in cats]
    ref_num = reference_df[nums].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    med = ref_num.median().fillna(0)
    ref_filled = ref_num.fillna(med)
    lo, hi = ref_filled.min(), ref_filled.max()
    scale = (hi - lo).replace(0, 1)
    cat_columns = pd.get_dummies(reference_df[cats].fillna("__missing__").astype(str), dtype=np.float32).columns
    transformed = []
    for frame in frames:
        num = frame[nums].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(med)
        num = ((num - lo) / scale).clip(0, 1)
        cat = pd.get_dummies(frame[cats].fillna("__missing__").astype(str), dtype=np.float32).reindex(columns=cat_columns, fill_value=0)
        transformed.append(np.concatenate([num.to_numpy(np.float32), cat.to_numpy(np.float32)], axis=1))
    # Restrict attacks to selected continuous features; categorical and one-hot inputs stay fixed.
    cont = np.asarray([nums.index(name) for name in PERTURB_FEATURES if name in nums], dtype=int)
    return transformed, cont


# Module-level attack options; defaults reproduce the original attack exactly.
ATTACK_OPTS = {"random_start": False, "alpha_scale": 1.0, "rng": None}


def attack(model, X, cont, eps=.03, steps=1):
    xa = X.copy()
    if ATTACK_OPTS["random_start"]:
        xa[:, cont] += ATTACK_OPTS["rng"].uniform(-eps, eps, size=(len(X), len(cont))).astype(np.float32)
        xa[:, cont] = np.clip(xa[:, cont], np.clip(X[:, cont] - eps, 0, 1), np.clip(X[:, cont] + eps, 0, 1))
    if steps == 1:
        xa[:, cont] -= eps * np.sign(model.grad_input_target_benign(xa)[:, cont])
    else:
        alpha = ATTACK_OPTS["alpha_scale"] * eps / steps
        for _ in range(steps):
            xa[:, cont] -= alpha * np.sign(model.grad_input_target_benign(xa)[:, cont])
            xa[:, cont] = np.clip(xa[:, cont], X[:, cont] - eps, X[:, cont] + eps)
    xa[:, cont] = np.clip(xa[:, cont], 0, 1)
    return xa


def decision_only_attack(model, X, cont, threshold, eps=.03, queries_per_example=50, seed=0):
    """Random-search hard-label evasion; the attack observes binary labels only."""
    rng = np.random.default_rng(seed)
    adv = X.copy()
    labels = model.predict_label(adv, threshold)
    success = labels == 0
    queries = len(X)
    for i in np.flatnonzero(~success):
        for _ in range(max(0, queries_per_example - 1)):
            candidate = X[i].copy()
            candidate[cont] += rng.uniform(-eps, eps, size=len(cont))
            candidate[cont] = np.clip(candidate[cont], np.maximum(0, X[i, cont] - eps), np.minimum(1, X[i, cont] + eps))
            queries += 1
            if model.predict_label(candidate[None, :], threshold)[0] == 0:
                adv[i] = candidate
                success[i] = True
                break
    return adv, success, queries


def select_threshold_at_fpr(model, X_val, y_val, max_fpr=.05):
    benign_scores = model.prob(X_val[y_val == 0])
    candidates = np.sort(np.unique(np.append(benign_scores, np.nextafter(benign_scores.max(), np.inf))))
    for threshold in candidates:
        if np.mean(benign_scores >= threshold) <= max_fpr:
            return float(threshold)
    return float(np.nextafter(benign_scores.max(), np.inf))


def metrics(model, X, y, eligible, cont, eps, steps, threshold, recalibrated_threshold, X_val, y_val,
            attack_mode="gradient", queries_per_example=50, eval_ids=None, seed=0):
    p_clean = model.prob(X)
    pred = p_clean >= threshold
    calibrated_pred = p_clean >= recalibrated_threshold
    attack_ids = np.flatnonzero(eligible) if eval_ids is None else eval_ids
    if attack_mode == "decision-only":
        _, adv_success, query_count = decision_only_attack(model, X[attack_ids], cont, threshold, eps, queries_per_example, seed)
        # PROPOSED: same attack against the arm's own recalibrated operating point.
        _, adv_success_recal, query_count_recal = decision_only_attack(model, X[attack_ids], cont, recalibrated_threshold, eps, queries_per_example, seed)
    else:
        adv = attack(model, X[attack_ids], cont, eps, steps)
        adv_success = model.prob(adv) < threshold
        adv_success_recal = model.prob(adv) < recalibrated_threshold
        query_count = 0
        query_count_recal = 0
    # PROPOSED: split ASR into flows the arm already missed before any perturbation and flows
    # that were detected clean and then evaded. Flows missed clean count as "successes" in the
    # original ASR, which matters most for arms whose clean recall fell.
    pre_detected = p_clean[attack_ids] >= threshold
    pre_detected_recal = p_clean[attack_ids] >= recalibrated_threshold
    ranks = pd.Series(p_clean).rank().to_numpy()
    n_pos, n_neg = int(np.sum(y == 1)), int(np.sum(y == 0))
    clean_auc = float((ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / max(1, n_pos * n_neg))
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    tn = int(np.sum(~pred & (y == 0)))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    ctp = int(np.sum(calibrated_pred & (y == 1))); cfp = int(np.sum(calibrated_pred & (y == 0)))
    cfn = int(np.sum(~calibrated_pred & (y == 1))); ctn = int(np.sum(~calibrated_pred & (y == 0)))
    cp = ctp / max(1, ctp + cfp); cr = ctp / max(1, ctp + cfn)
    return {"clean_recall": recall, "clean_f1": f1, "clean_fpr": fp / max(1, fp + tn),
            "recalibrated_clean_recall": cr, "recalibrated_clean_f1": 2 * cp * cr / max(1e-12, cp + cr),
            "recalibrated_clean_fpr": cfp / max(1, cfp + ctn), "recalibrated_threshold": recalibrated_threshold,
            "recalibrated_validation_fpr": float(np.mean(model.prob(X_val[y_val == 0]) >= recalibrated_threshold)),
            "attack_success_rate": float(np.mean(adv_success)) if len(adv_success) else float("nan"),
            "eligible_attack_flows": int(len(attack_ids)), "decision_oracle_queries": int(query_count), "test_flows": int(len(y)),
            "pre_attack_detection_rate": float(np.mean(pre_detected)),
            "attack_induced_asr": float(np.mean(adv_success[pre_detected])) if pre_detected.any() else float("nan"),
            "asr_recalibrated": float(np.mean(adv_success_recal)),
            "pre_attack_detection_rate_recalibrated": float(np.mean(pre_detected_recal)),
            "attack_induced_asr_recalibrated": float(np.mean(adv_success_recal[pre_detected_recal])) if pre_detected_recal.any() else float("nan"),
            "decision_oracle_queries_recalibrated": int(query_count_recal), "clean_auc": clean_auc}


def main():
    ap = argparse.ArgumentParser()
    # The Zenodo record has these two filenames reversed relative to the
    # canonical UNSW partitions. Canonical train has 175,341 rows; test 82,332.
    ap.add_argument("--train", type=Path, default=DATA / "UNSW_NB15_testing-set.csv")
    ap.add_argument("--test", type=Path, default=DATA / "UNSW_NB15_training-set.csv")
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--max-train", type=int, default=30000, help="pilot cap; use 0 for all official training rows")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--attack-steps", type=int, default=1, help="1=FGSM-like; >1=iterative projected attack")
    ap.add_argument("--attack-mode", choices=["gradient", "decision-only"], default="gradient")
    ap.add_argument("--eps", type=float, default=.03)
    ap.add_argument("--queries-per-example", type=int, default=50)
    ap.add_argument("--decision-query-budget-round", type=int, default=5000)
    ap.add_argument("--decision-test-samples", type=int, default=1000)
    ap.add_argument("--attack-examples-per-round", type=int, default=100)
    ap.add_argument("--update-lr", type=float, default=0.0002)
    ap.add_argument("--replay-memory-size", type=int, default=1000)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--run-id", default=None, help="unique label for this run's output files")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results_ext", help="never defaults to the final-matrix folder")
    ap.add_argument("--control-arm", action="store_true", help="add the clean_continued control (extra epochs, no adversarial data)")
    ap.add_argument("--random-start", action="store_true", help="random start inside the eps-ball (use with --attack-steps >= 5 for PGD)")
    ap.add_argument("--alpha-scale", type=float, default=1.0, help="step size = alpha_scale * eps / steps (original = 1.0)")
    # --- budget-matched extension (run_matched.py); see DESIGN.md ---
    ap.add_argument("--matched-arms", action="store_true", help="add M1 (one-time matched), M1-e10 and M2 (incremental matched)")
    ap.add_argument("--static-decision-arm", action="store_true", help="decision-only setting: static arm trained on decision-only examples")
    ap.add_argument("--matched-seq", action="store_true", help="add M1-seq: M1's vectors applied in M2's five-update structure before round 1 (DESIGN_ADDENDUM.md)")
    ap.add_argument("--update-epochs", type=int, default=None, help="update epochs for arms C, M1, M2 (default max(1, epochs // 2))")
    ap.add_argument("--update-lr-main", type=float, default=0.001, help="update lr for arms C, M1, M2 (original 0.001)")
    args = ap.parse_args()
    ATTACK_OPTS.update(random_start=args.random_start, alpha_scale=args.alpha_scale,
                       rng=np.random.default_rng(args.seed + 7000))
    for f in (args.train, args.test):
        if not f.exists():
            raise SystemExit(f"Missing dataset file: {f}\nDownload the official UNSW-NB15 CSVs into {DATA}")
    def read_dataset(path):
        with path.open("r", encoding="utf-8", errors="replace") as f:
            sample = f.read(4096)
        delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
        if delimiter == "\t":
            return pd.read_csv(path, sep=delimiter, header=None, names=UNSW_COLUMNS, low_memory=False)
        return pd.read_csv(path, sep=delimiter, low_memory=False)

    train_df = read_dataset(args.train)
    test_df = read_dataset(args.test)
    raw_X, y, raw_Xt, yt = prepare_raw(train_df, test_df)
    if args.max_train and len(y) > args.max_train:
        rng = np.random.default_rng(args.seed)
        selected = []
        for cls in (0, 1):
            ids = np.flatnonzero(y == cls)
            selected.extend(rng.choice(ids, min(len(ids), round(args.max_train * len(ids) / len(y))), replace=False))
        raw_X, y = raw_X.iloc[selected].reset_index(drop=True), y[selected]
    init_ids, val_ids, adapt_ids = stratified_split(y, args.seed)
    # Validation split is reserved; adaptation stream is never included in initial fit.
    (X, Xt), cont = fit_preprocessor(raw_X.iloc[init_ids], [raw_X, raw_Xt])
    X0, y0 = X[init_ids], y[init_ids]
    Xa, ya = X[adapt_ids], y[adapt_ids]
    clean = MLP(X.shape[1], args.seed)
    train_seconds = clean.train(X0, y0, epochs=args.epochs, seed=args.seed)
    threshold = select_threshold_at_fpr(clean, X[val_ids], y[val_ids], max_fpr=.05)
    eligible = (yt == 1) & (clean.prob(Xt) >= threshold)
    eval_rng = np.random.default_rng(args.seed + 1000)
    eligible_ids = np.flatnonzero(eligible)
    attack_eval_ids = eval_rng.choice(eligible_ids, min(len(eligible_ids), args.decision_test_samples), replace=False) if len(eligible_ids) else np.array([], dtype=int)
    static = MLP(X.shape[1], args.seed)
    static_initial_seconds = static.train(X0, y0, epochs=args.epochs, seed=args.seed)
    static_attack_start = time.perf_counter()
    static_pool = np.flatnonzero(y0 == 1)
    static_rng = np.random.default_rng(args.seed + 500)
    static_ids = static_rng.choice(static_pool, min(len(static_pool), args.rounds * args.attack_examples_per_round), replace=False)
    Xstatic = attack(static, X0[static_ids], cont, args.eps, args.attack_steps)
    static_attack_seconds = time.perf_counter() - static_attack_start
    static_seconds = static.train(np.concatenate([X0, Xstatic]), np.concatenate([y0, np.ones(len(Xstatic), dtype=int)]), epochs=args.epochs, seed=args.seed + 1)
    incremental = MLP(X.shape[1], args.seed)
    incremental_initial_seconds = incremental.train(X0, y0, epochs=args.epochs, seed=args.seed)
    no_rehearsal = MLP(X.shape[1], args.seed)
    no_rehearsal_initial_seconds = no_rehearsal.train(X0, y0, epochs=args.epochs, seed=args.seed)
    balanced_rehearsal = MLP(X.shape[1], args.seed)
    balanced_initial_seconds = balanced_rehearsal.train(X0, y0, epochs=args.epochs, seed=args.seed)
    rng = np.random.default_rng(args.seed + 10)
    adapt_order = rng.permutation(len(Xa))
    stream = np.array_split(adapt_order, args.rounds)
    memory_ids = rng.choice(len(X0), min(args.replay_memory_size, len(X0)), replace=False)
    clean_memory, clean_memory_y = X0[memory_ids], y0[memory_ids]
    per_class = max(1, args.replay_memory_size // 2)
    benign_memory_ids = rng.choice(np.flatnonzero(y0 == 0), min(per_class, int(np.sum(y0 == 0))), replace=False)
    malicious_memory_ids = rng.choice(np.flatnonzero(y0 == 1), min(per_class, int(np.sum(y0 == 1))), replace=False)
    balanced_memory_ids = np.concatenate([benign_memory_ids, malicious_memory_ids])
    balanced_memory, balanced_memory_y = X0[balanced_memory_ids], y0[balanced_memory_ids]
    arms = {"frozen": clean, "static_adversarial": static}
    incremental_arms = {
        "incremental_rehearsal": incremental,
        "incremental_no_rehearsal": no_rehearsal,
        "incremental_balanced_rehearsal": balanced_rehearsal,
    }
    arms.update(incremental_arms)
    control_extra_seconds = None
    if args.control_arm:
        control = MLP(X.shape[1], args.seed)
        control_initial_seconds = control.train(X0, y0, epochs=args.epochs, seed=args.seed)
        control_extra_seconds = control.train(X0, y0, epochs=args.epochs, seed=args.seed + 1)  # mirrors static's second training phase
        arms["clean_continued"] = control
    upd_epochs = args.update_epochs if args.update_epochs else max(1, args.epochs // 2)
    adv_examples = {name: 0 for name in arms}
    adv_examples["static_adversarial"] = int(len(Xstatic))
    extra_times = {}
    def round_attacked_ids(rid):
        ids = stream[rid - 1]
        mal = np.flatnonzero(ya[ids] == 1)
        rr = np.random.default_rng(args.seed + 2000 + rid)
        chosen = rr.choice(mal, min(len(mal), args.attack_examples_per_round), replace=False)
        if args.attack_mode == "decision-only":
            chosen = chosen[:min(len(chosen), max(1, args.decision_query_budget_round // max(1, args.queries_per_example)))]
        return ids[chosen]  # indices into Xa
    if args.static_decision_arm and args.attack_mode == "decision-only":
        sdec = MLP(X.shape[1], args.seed)
        t0 = sdec.train(X0, y0, epochs=args.epochs, seed=args.seed)
        a0 = time.perf_counter()
        Xsdec, _, _ = decision_only_attack(sdec, X0[static_ids], cont, threshold, args.eps, args.queries_per_example, args.seed + 9500)
        a1 = time.perf_counter() - a0
        t1 = sdec.train(np.concatenate([X0, Xsdec]), np.concatenate([y0, np.ones(len(Xsdec), dtype=int)]), epochs=args.epochs, seed=args.seed + 1)
        arms["static_decision_trained"] = sdec
        adv_examples["static_decision_trained"] = int(len(Xsdec))
        extra_times["static_decision_trained"] = t0 + a1 + t1
    if args.matched_arms:
        union = np.concatenate([round_attacked_ids(r) for r in range(1, args.rounds + 1)])
        m1 = MLP(X.shape[1], args.seed)
        t0 = m1.train(X0, y0, epochs=args.epochs, seed=args.seed)
        a0 = time.perf_counter()
        if args.attack_mode == "decision-only":
            Xm1, _, _ = decision_only_attack(m1, Xa[union], cont, threshold, args.eps, args.queries_per_example, args.seed + 9000)
        else:
            Xm1 = attack(m1, Xa[union], cont, args.eps, args.attack_steps)
        a1 = time.perf_counter() - a0
        m1e10 = MLP(X.shape[1], args.seed)
        t0b = m1e10.train(X0, y0, epochs=args.epochs, seed=args.seed)
        rx = np.concatenate([Xm1, clean_memory]); ry = np.concatenate([np.ones(len(Xm1), dtype=int), clean_memory_y])
        t1 = m1.train(rx, ry, epochs=upd_epochs, lr=args.update_lr_main, seed=args.seed + 1)
        t1b = m1e10.train(rx, ry, epochs=5 * upd_epochs, lr=args.update_lr_main, seed=args.seed + 1)
        m2 = MLP(X.shape[1], args.seed)
        t2 = m2.train(X0, y0, epochs=args.epochs, seed=args.seed)
        arms["matched_one_time"] = m1; arms["matched_one_time_e10"] = m1e10; arms["matched_incremental"] = m2
        adv_examples["matched_one_time"] = int(len(Xm1)); adv_examples["matched_one_time_e10"] = int(len(Xm1)); adv_examples["matched_incremental"] = 0
        extra_times.update({"matched_one_time": t0 + a1 + t1, "matched_one_time_e10": t0b + a1 + t1b, "matched_incremental": t2})
        matched_union_size = int(len(union))
        if args.matched_seq:
            m1s = MLP(X.shape[1], args.seed)
            t0s = m1s.train(X0, y0, epochs=args.epochs, seed=args.seed)
            sizes = [len(round_attacked_ids(r)) for r in range(1, args.rounds + 1)]
            bounds = np.cumsum([0] + sizes)
            t1s = 0.0
            for r in range(1, args.rounds + 1):
                grp = Xm1[bounds[r - 1]:bounds[r]]
                gx = np.concatenate([grp, clean_memory]); gy = np.concatenate([np.ones(len(grp), dtype=int), clean_memory_y])
                t1s += m1s.train(gx, gy, epochs=upd_epochs, lr=args.update_lr_main, seed=args.seed + r)
            arms["matched_one_time_seq"] = m1s
            adv_examples["matched_one_time_seq"] = int(len(Xm1))
            extra_times["matched_one_time_seq"] = t0s + a1 + t1s
    round_records = []
    cumulative_times = {
        "frozen": train_seconds,
        "static_adversarial": static_initial_seconds + static_attack_seconds + static_seconds,
        "incremental_rehearsal": incremental_initial_seconds,
        "incremental_no_rehearsal": no_rehearsal_initial_seconds,
        "incremental_balanced_rehearsal": balanced_initial_seconds,
    }
    if control_extra_seconds is not None:
        cumulative_times["clean_continued"] = control_initial_seconds + control_extra_seconds
    cumulative_times.update(extra_times)
    cumulative_labels = {name: 0 for name in incremental_arms}
    for rid, ids in enumerate(stream, 1):
        batch_x, batch_y = Xa[ids], ya[ids]
        malicious_ids = np.flatnonzero(batch_y == 1)
        round_rng = np.random.default_rng(args.seed + 2000 + rid)
        attacked_ids = round_rng.choice(malicious_ids, min(len(malicious_ids), args.attack_examples_per_round), replace=False)
        if args.attack_mode == "decision-only":
            # The starting label query is included in queries_per_example.
            budget_examples = min(len(attacked_ids), max(1, args.decision_query_budget_round // max(1, args.queries_per_example)))
            attacked_ids = attacked_ids[:budget_examples]
        stream_attack = {}
        for name, model in arms.items():
            arm_start = time.perf_counter()
            attack_start = time.perf_counter()
            if args.attack_mode == "decision-only":
                candidate_adv, successful, update_queries = decision_only_attack(
                    model, batch_x[attacked_ids], cont, threshold, args.eps,
                    args.queries_per_example, args.seed + rid + 100 * list(arms).index(name))
            else:
                candidate_adv = attack(model, batch_x[attacked_ids], cont, args.eps, args.attack_steps)
                successful = model.prob(candidate_adv) < threshold
                update_queries = 0
            update_attack_seconds = time.perf_counter() - attack_start
            evaded = candidate_adv[successful]
            update_seconds = 0.0
            if name in incremental_arms:
                # Each adaptive arm receives only its own successful evasions.
                if name == "incremental_rehearsal":
                    replay_x, replay_y, learning_rate = clean_memory, clean_memory_y, args.update_lr_main
                elif name == "incremental_balanced_rehearsal":
                    replay_x, replay_y, learning_rate = balanced_memory, balanced_memory_y, args.update_lr
                else:
                    replay_x, replay_y, learning_rate = X0[:0], y0[:0], 0.001
                retrain_x = np.concatenate([evaded, replay_x])
                retrain_y = np.concatenate([np.ones(len(evaded), dtype=int), replay_y])
                arm_epochs = upd_epochs if name == "incremental_rehearsal" else max(1, args.epochs // 2)
                update_seconds = model.train(retrain_x, retrain_y, epochs=arm_epochs,
                                             lr=learning_rate, seed=args.seed + rid)
                cumulative_labels[name] += len(evaded)
            elif name == "matched_incremental":
                # M2: every attacked flow (attempt) is a training example, labeled malicious.
                retrain_x = np.concatenate([candidate_adv, clean_memory])
                retrain_y = np.concatenate([np.ones(len(candidate_adv), dtype=int), clean_memory_y])
                update_seconds = model.train(retrain_x, retrain_y, epochs=upd_epochs, lr=args.update_lr_main, seed=args.seed + rid)
                adv_examples["matched_incremental"] += len(candidate_adv)
            cumulative_times[name] += update_attack_seconds + update_seconds
            stream_attack[name] = {
                "successful": successful, "new_labels": len(evaded),
                "queries": update_queries, "elapsed": time.perf_counter() - arm_start,
            }
        for name, model in arms.items():
            attack_result = stream_attack[name]
            recalibrated_threshold = select_threshold_at_fpr(model, X[val_ids], y[val_ids], max_fpr=.05)
            row = {"seed": args.seed, "round": rid, "arm": name, "attack": ("decision-only" if args.attack_mode == "decision-only" else ("PGD-RS" if args.random_start else ("BIM-like" if args.attack_steps > 1 else "FGSM-like"))),
                   "update_round_wall_seconds": attack_result["elapsed"], "cumulative_train_and_attack_seconds": cumulative_times[name],
                   "new_evasion_labels_this_round": attack_result["new_labels"] if name in incremental_arms else 0,
                   "cumulative_new_evasion_labels": cumulative_labels[name] if name in incremental_arms else 0,
                   "attack_examples_this_round": len(attacked_ids), "decision_oracle_queries_this_round": attack_result["queries"],
                   "adaptation_attack_success_rate": float(np.mean(attack_result["successful"])) if len(attack_result["successful"]) else 0.0,
                   **metrics(model, Xt, yt, eligible, cont, args.eps, args.attack_steps, threshold, recalibrated_threshold, X[val_ids], y[val_ids], args.attack_mode, args.queries_per_example, attack_eval_ids, args.seed + rid)}
            row["adversarial_training_examples_cumulative"] = int(cumulative_labels[name]) if name in incremental_arms else int(adv_examples.get(name, 0))
            round_records.append(row)
    OUT_DIR = args.out_dir
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"ext_s{args.seed}_{args.attack_mode}_steps{args.attack_steps}"
    out_csv = OUT_DIR / f"unsw_nb15_{run_id}.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=round_records[0].keys())
        writer.writeheader(); writer.writerows(round_records)
    metadata = {"status": "pilot_only", "seed": args.seed, "rounds": args.rounds, "epochs": args.epochs,
                "max_train": args.max_train, "epsilon": args.eps, "attack_steps": args.attack_steps,
                "input_dimensions": int(X.shape[1]), "train_rows_used": int(len(y)), "initial_rows": int(len(X0)),
                "preprocessing_fit_rows": int(len(X0)),
                "validation_rows_reserved": int(len(val_ids)), "adaptation_rows": int(len(Xa)),
                "train_file": str(args.train), "train_file_rows": int(len(train_df)),
                "test_file": str(args.test), "test_rows": int(len(yt)),
                "continuous_features_perturbed": int(len(cont)), "perturbable_feature_names": PERTURB_FEATURES,
                "attack_mode": args.attack_mode, "queries_per_example": args.queries_per_example,
                "decision_query_budget_round": args.decision_query_budget_round,
                "decision_test_samples": int(len(attack_eval_ids)), "attack_test_samples": int(len(attack_eval_ids)),
                "attack_examples_per_round": args.attack_examples_per_round,
                "update_lr_balanced_rehearsal": args.update_lr,
                "replay_memory_size": args.replay_memory_size,
                "balanced_replay_classes": {"benign": int(len(benign_memory_ids)), "malicious": int(len(malicious_memory_ids))},
                "attacker_feedback_isolated_per_arm": True,
                "static_adversarial_examples": int(len(Xstatic)), "fixed_threshold": threshold,
                "validation_fpr_target": 0.05,
                "simulated_label_oracle": True, "initial_train_seconds": train_seconds,
                "static_update_seconds": static_seconds, "results_csv": str(out_csv)}
    metadata["matched_options"] = {"matched_arms": args.matched_arms, "static_decision_arm": args.static_decision_arm,
                                   "update_epochs": upd_epochs, "update_lr_main": args.update_lr_main,
                                   "matched_union_size": matched_union_size if args.matched_arms else None, "matched_seq": args.matched_seq, "design_addendum": "DESIGN_ADDENDUM.md",
                                   "numpy": np.__version__, "pandas": pd.__version__, "design": "DESIGN.md"}
    metadata["tier2_options"] = {"control_arm": args.control_arm, "random_start": args.random_start,
                                 "alpha_scale": args.alpha_scale, "extra_metrics": True}
    metadata_path = OUT_DIR / f"unsw_nb15_{run_id}_metadata.json"
    metadata["run_id"] = run_id
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    print(f"Results: {out_csv}")


if __name__ == "__main__":
    main()
