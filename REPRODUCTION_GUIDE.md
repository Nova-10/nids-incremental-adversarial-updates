# Reproduction guide

This repository supports the manuscript in manuscript/ (v11). Table and figure numbers follow v8 to v11, which share numbering. Paths below are relative to the archive root.

## 1. What this archive can and cannot show
- Regenerating tables from per-run outputs (results/*) is not the same as regenerating the experiment from raw data. Both were done for v7, and they are reported separately below.
- The raw data are not included (the dataset terms grant academic use but do not grant redistribution). Download them from Zenodo record 10.5281/zenodo.3768048, a third-party redistribution, and check the MD5 values in data/README_DATA.md. Both partitions were compared with the official UNSW files and are identical in content (checks/PROVENANCE.md). Run data/verify_data.py after placing the files.
- The original five-seed outputs (results/reported_matrix) were produced in an environment that was not recorded. The v7 re-run reproduces them exactly for some runs and with small numerical drift for others (checks/REPRODUCTION_RESULT.md). Bit-for-bit reproduction is not claimed.

## 2. Environment used for v7 runs and analysis
Python 3.13.17, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, Matplotlib 3.11.2, Linux x86_64, 2 vCPU. Manuscript build: Node.js 22 with the docx package. Render: LibreOffice 24.2.7.2.

## 3. Setup
    mkdir -p work/data/UNSW-NB15
    cp code/run_pilot_v2.py code/run_matrix_ext.py code/run_matched.py work/
    # place UNSW_NB15_training-set.csv and UNSW_NB15_testing-set.csv (Zenodo names) in work/data/UNSW-NB15/
    md5sum work/data/UNSW-NB15/*.csv   # compare with data/README_DATA.md

## 4. Experiments
| Experiment | Command (run in work/) | Outputs |
|---|---|---|
| Main comparison re-run (15 runs, seeds 17-21) | python3 run_matrix_ext.py --seeds 17 18 19 20 21 --presets control | results_ext/ -> results/rerun_matrix |
| Budget-matched extension (60 runs, seeds 17-36) | see code/jobs_main.txt. Each line is appended to: python3 run_matched.py --rounds 5 --max-train 0 --epochs 5 --control-arm --matched-arms | results/matched_main |
| M1-seq addendum (60 runs, seeds 17-36; all earlier arms recomputed and identical to results/matched_main) | see code/jobs_seq.txt, prefix: python3 run_matched_seq.py --rounds 5 --max-train 0 --epochs 5 --control-arm --matched-arms | results/matched_seq |
| Sensitivity (120 runs, FGSM-like, seeds 17-36) | see code/jobs_sens.txt (same prefix) | results/sensitivity |
| Feature realism (seeds 17-21, initial model) | python3 -I code/realism.py (edit paths at top) | analysis/realism_results.json |
The design of the extension and sensitivity analysis was written before any run: design/DESIGN.md. The M1-seq arm was designed after those results were known and before its own runs: design/DESIGN_ADDENDUM.md.

## 5. Table and figure map (v8 numbering)
| Item | Source files | How produced |
|---|---|---|
| Table 1 | literature | manuscript text |
| Table 2 | raw data | code/check_table2_counts.py -> checks/table2_counts_check.txt |
| Tables 3, 4, 5, 6 | code/run_pilot_v2.py, code/run_matched.py, code/run_matched_seq.py, design/*.md | protocol description |
| Tables 7-11, Figures 2-4 | results/reported_matrix (ORIGINAL outputs) | code/section4_tables.py, code/make_fig234.py; cell check: code/compare_tables_v8.py -> checks/v8/original_tables_check.txt (198/198) |
| Figure 1 | none (diagram) | code/make_fig1.py |
| Section 4.8 reproduction figures | results/rerun_matrix vs results/reported_matrix | code/tol_compare.py -> checks/repro_comparison.txt; code/section4_tables.py on both folders (analysis/section4_rerun) |
| Tables 12, 13, Figure 5, Section 5.8 | results/matched_seq (contains all extension arms, including M1-seq; RERUN environment) | code/analyze_matched_v2.py -> analysis/matched_seq/*; code/make_fig5_v2.py |
| Table 14, Section 5.9 | results/sensitivity, results/matched_main (default configuration) | code/analyze_sens.py -> analysis/sensitivity/sensitivity_round5.csv |
| Table 15, Section 5.10 | raw data, code/run_pilot_v2.py | code/realism.py -> analysis/realism_results.json |
| Section 4.2 provenance | Zenodo and official files | checks/PROVENANCE.md |
| Reference fields | Crossref, publisher pages, [34] full text | checks/REFERENCE_LEDGER_v7.md |

## 6. Integrity
SHA256SUMS.txt lists every file in the archive.
