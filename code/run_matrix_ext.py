#!/usr/bin/env python3
"""Tier 2 matrix runner (PROPOSED, not yet run). Mirrors run_matrix.py but calls run_pilot_v2.py.

Presets
  core      FGSM-like, BIM-like (the original 5-step attack) and decision-only, five seeds, five rounds,
            extra logged columns only. This is the minimum needed to compare ASR and FPR at matched
            operating points. Same 15 runs as the original matrix.
  control   core + the clean_continued control arm (one extra model per run; small added cost).
            `--presets control` alone runs everything agreed so far; `core` is not needed in addition.
  pgd       OPTIONAL, only if time remains: genuine PGD (10 steps, random start, alpha = 2.5 * eps / 10); five more runs.
Combine with e.g. --presets control pgd.
Output goes to experiment/results_ext/, never to results/.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "run_pilot_v2.py"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[17, 18, 19, 20, 21])
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--max-train", type=int, default=0, help="0 = full official training file, as in the final matrix")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--presets", nargs="+", choices=["core", "control", "pgd"], default=["core"])
    args = ap.parse_args()
    control = "control" in args.presets
    runs = [(1, "fgsm", "gradient", []), (5, "bim5", "gradient", []), (1, "decision", "decision-only", [])]
    if "pgd" in args.presets:
        runs.append((10, "pgd10", "gradient", ["--random-start", "--alpha-scale", "2.5"]))
    for seed in args.seeds:
        for steps, name, mode, extra in runs:
            run_id = f"ext_{name}_s{seed}"
            cmd = [sys.executable, str(RUNNER), "--seed", str(seed), "--rounds", str(args.rounds), "--max-train", str(args.max_train),
                   "--epochs", str(args.epochs), "--attack-steps", str(steps), "--attack-mode", mode, "--run-id", run_id] + extra
            if control:
                cmd.append("--control-arm")
            print("Starting", run_id, flush=True)
            subprocess.run(cmd, check=True)
    print("Finished. Outputs are in experiment/results_ext/. Re-run Tier 1 against that folder after checking the regression columns.")


if __name__ == "__main__":
    main()
