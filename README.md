# One-time and incremental adversarial updates for network intrusion detection (UNSW-NB15)

Code, run outputs, analysis scripts and checks for the manuscript "An Exploratory Feature-Space Comparison of One-Time and Incremental Adversarial Updates for Network Intrusion Detection" (Ajay Kumar). The manuscript is in `manuscript/`.

This is an offline, exploratory feature-space study: one small MLP on UNSW-NB15, record-level splits, a non-adaptive attacker, labels simulated from dataset ground truth, and round-5 outcomes. The attacks perturb normalized features and do not produce executable traffic.

## Contents
| Folder | What it holds |
|---|---|
| `code/` | Runners (`run_pilot_v2.py`, `run_matrix_ext.py`, `run_matched.py`, `run_matched_seq.py`), job lists, analysis and figure scripts, checks, manuscript build script |
| `design/` | Pre-run design of the matched-attempt extension (`DESIGN.md`) and the M1-seq addendum (`DESIGN_ADDENDUM.md`) |
| `results/reported_matrix/` | Original five-seed per-run outputs (paper Tables 7-11) |
| `results/rerun_matrix/` | Rerun of the five-seed matrix from raw data |
| `results/matched_main`, `matched_seq`, `sensitivity` | 20-seed extension, M1-seq addendum and sensitivity runs (paper Tables 12-14) |
| `analysis/` | Aggregated tables and the perturbation-realism results (Table 15) |
| `checks/` | Reproduction comparison, data provenance, table-cell checks, reference ledger |
| `figures/` | Figures as used in the paper |
| `data/` | Data instructions and `verify_data.py` (CSV files not included) |

See `REPRODUCTION_GUIDE.md` for commands and a table/figure-to-source map, and `SHA256SUMS.txt` for file checksums.

## Data
UNSW-NB15 is not redistributed here. Obtain the partition files from the official UNSW source or Zenodo record 10.5281/zenodo.3768048, place them in `data/UNSW-NB15/`, and run `python3 data/verify_data.py`.

## Reproduction caveats
The original five-seed outputs were produced in an unrecorded environment. Rerunning the archived code reproduced 5 of 15 runs to within float32 rounding, 3 to within 3e-5, and 7 with small numerical drift. The archived runner is not proven to be the exact original code.

## License
No license has been chosen yet. Until one is added, default copyright applies.
