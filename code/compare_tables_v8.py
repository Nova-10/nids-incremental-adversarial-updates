"""Recompute the numeric cells of manuscript Tables 6-10 from archived outputs.

Inputs : checks/manuscript/manuscript_v2_tables.json (from dump_manuscript_tables.py)
         analysis/section4/regenerated_from_archive/*.csv (from section4_tables.py)
         results/reported_matrix/*.csv (raw per-run CSVs; used for F1 only)
Rule   : mean and 95% Student-t half-width (df = 4), both rounded to the
         manuscript's decimal places. Values are compared as strings.
"""
import glob, json, math, os, sys
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from scipy import stats

ARC = "/home/claude/archive/NIDS_reported_version_reproducibility"
TABLES = json.load(open(sys.argv[1]))
S4 = os.path.join(ARC, "analysis/section4/regenerated_from_archive")
RAW = os.path.join(ARC, "results/reported_matrix")

def norm(s):
    return s.replace("−", "-").replace(" ", " ").strip()

def fmt(mean, hw, dp):
    return f"{mean:.{dp}f} ± {hw:.{dp}f}"

def hw_from_raw(vals):
    v = np.asarray(vals, float)
    return stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / math.sqrt(len(v))

m5 = pd.read_csv(os.path.join(S4, "s4_round5_means.csv"))
paired = pd.read_csv(os.path.join(S4, "s4_paired_contrasts.csv"))
res = pd.read_csv(os.path.join(S4, "s4_resources.csv"))
raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RAW, "unsw_nb15_ext_*_s*.csv")))])
r5 = raw[raw["round"] == 5]

ATT = {"FGSM-like": "FGSM-like", "BIM-like": "BIM-like", "Decision-only": "decision-only"}
ARMS = ["A Frozen", "B Static", "C Rehearsal", "D No rehearsal", "E Balanced", "F Control"]

def m(attack, arm, col):
    row = m5[(m5.attack == ATT[attack]) & (m5.arm == arm)].iloc[0]
    return row[col], row[col + "_hw"]

RAW_ARM = {"A Frozen": "frozen", "B Static": "static_adversarial", "C Rehearsal": "incremental_rehearsal",
           "D No rehearsal": "incremental_no_rehearsal", "E Balanced": "incremental_balanced_rehearsal",
           "F Control": "clean_continued"}

def f1_stats(attack, arm, col):
    sub = r5[(r5.attack == ATT[attack]) & (r5.arm == RAW_ARM[arm])][col] * 100
    return sub.mean(), hw_from_raw(sub)

results, mism = [], []
def check(label, expected, computed):
    ok = norm(expected) == norm(computed)
    results.append(ok)
    if not ok:
        mism.append(f"{label}: manuscript '{expected}' vs recomputed '{computed}'")
    return ok

# Table 6: round-5 attack success, recalibrated (attack_induced_asr_recalibrated)
for r in TABLES[6][1:]:
    attack_col = {"FGSM-like": 1, "BIM-like": 2, "Decision-only": 3}
    arm = r[0].replace("A Frozen", "A Frozen")
    for att, ci in attack_col.items():
        if r[0] not in ARMS and "Arm" not in r[0]:
            pass
for ti, t in enumerate(TABLES):
    pass

# Table 6 index 5 (0-based) in the JSON export
t6 = TABLES[6]
for row in t6[1:]:
    arm = norm(row[0]).replace("A Frozen", "A Frozen")
    for j, att in enumerate(["FGSM-like", "BIM-like", "Decision-only"], start=1):
        mu, h = m(att, arm, "attack_induced_asr_recalibrated")
        check(f"T6 {att} {arm}", row[j], fmt(mu, h, 2))

# Table 8: cohort table; attack and arm are carried down in blank cells
t8 = TABLES[8]
cur_att = None
for row in t8[1:]:
    if row[0]:
        cur_att = row[0]
    arm = norm(row[1])
    a = cur_att
    checks8 = [
        (2, "pre_attack_detection_rate_recalibrated", 2),
        (3, "asr_recalibrated", 2),
        (4, "recalibrated_clean_recall", 2),
        (5, "recalibrated_clean_fpr", 2),
        (7, "clean_auc", 3),
    ]
    for j, col, dp in checks8:
        mu, h = m(a, arm, col)
        expected = f"{mu:.3f}" if col == "clean_auc" else fmt(mu, h, dp)  # AUC is reported as a mean only
        check(f"T8 {a} {arm} {col}", row[j], expected)
    mu, h = f1_stats(a, arm, "recalibrated_clean_f1")
    check(f"T8 {a} {arm} recalibrated_clean_f1", row[6], fmt(mu, h, 2))

# Table 9: attack-induced ASR (fixed threshold), clean recall, FPR and clean F1
t9 = TABLES[9]
cur_att = None
for row in t9[1:]:
    if row[0]:
        cur_att = row[0]
    arm = norm(row[1])
    a = cur_att
    for j, col in [(2, "attack_induced_asr"), (3, "clean_recall"), (4, "clean_fpr")]:
        mu, h = m(a, arm, col)
        check(f"T9 {a} {arm} {col}", row[j], fmt(mu, h, 2))
    mu, h = f1_stats(a, arm, "clean_f1")
    check(f"T9 {a} {arm} clean_f1", row[5], fmt(mu, h, 2))

# Table 7: paired contrasts on attack_induced_asr_recalibrated (round 5)
t7 = TABLES[7]
pairs = {"B Static − A Frozen": ("B Static", "A Frozen"),
         "F Control − A Frozen": ("F Control", "A Frozen"),
         "B Static − F Control": ("B Static", "F Control"),
         "C Rehearsal − A Frozen": ("C Rehearsal", "A Frozen"),
         "C Rehearsal − B Static": ("C Rehearsal", "B Static"),
         "D No rehearsal − A Frozen": ("D No rehearsal", "A Frozen"),
         "E Balanced − A Frozen": ("E Balanced", "A Frozen"),
         "E Balanced − B Static": ("E Balanced", "B Static")}
for row in t7[1:]:
    key = {norm(k): v for k, v in pairs.items()}
    first, second = key[norm(row[0])]
    for j, att in enumerate(["FGSM-like", "BIM-like", "Decision-only"], start=1):
        p = paired[(paired.attack == ATT[att]) & (paired["first"] == first) & (paired.second == second)
                   & (paired.metric == "attack_induced_asr_recalibrated")].iloc[0]
        exp = f"{p.mean_diff:.2f} [{p.lo:.2f}, {p.hi:.2f}], {int(p.first_lower_in_seeds)}/5"
        check(f"T7 {row[0]} {att}", row[j], exp)

# Table 10: labels, decision-only adaptation queries, time (FGSM, BIM, decision)
t10 = TABLES[10]
for row in t10[1:]:
    arm = norm(row[0])
    rf = res[(res.attack == "FGSM-like") & (res.arm == arm)].iloc[0]
    rd = res[(res.attack == "decision-only") & (res.arm == arm)].iloc[0]
    rb = res[(res.attack == "BIM-like") & (res.arm == arm)].iloc[0]
    if rf.labels_mean == 0:
        check(f"T10 labels {arm} FGSM", row[1].split(" ")[0], "0")
    else:
        check(f"T10 labels {arm} FGSM", row[1], f"{rf.labels_mean:.1f} ({rf.labels_min} to {rf.labels_max})")
    check(f"T10 decision labels {arm}", row[2].split(" ")[0] if rd.labels_mean == 0 else row[2],
          "0" if rd.labels_mean == 0 else f"{rd.labels_mean:.1f} ({rd.labels_min} to {rd.labels_max})")
    check(f"T10 adapt queries {arm}", row[3], f"{rd.adapt_queries_mean:,.0f}")
    check(f"T10 time FGSM {arm}", row[4], f"{rf.time_s_mean:.2f}")
    check(f"T10 time BIM {arm}", row[5], f"{rb.time_s_mean:.2f}")
    check(f"T10 time decision {arm}", row[6], f"{rd.time_s_mean:.2f}")

print(f"checked cells: {len(results)}  matched: {sum(results)}  mismatched: {len(mism)}")
for x in mism:
    print("MISMATCH", x)
