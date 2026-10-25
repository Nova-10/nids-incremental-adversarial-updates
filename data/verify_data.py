"""Check that the UNSW-NB15 partition files placed in data/UNSW-NB15/ are the ones used in the paper.
The CSV files are not distributed in this repository. Obtain them from the official UNSW source
(https://research.unsw.edu.au/projects/unsw-nb15-dataset) or from Zenodo record 10.5281/zenodo.3768048.
Usage: python3 data/verify_data.py"""
import hashlib, pathlib, sys
D = pathlib.Path(__file__).resolve().parent / "UNSW-NB15"
KNOWN = {  # filename -> {md5: description}
    "UNSW_NB15_testing-set.csv": {"07a1566e74e89f4c970fd1dc3b5d554b": "Zenodo copy (tab-separated, 175,341 rows = official TRAINING partition)",
                                  "e0beea40262e46168cdb81476dbc27b4": "official UNSW file (82,332 rows = official TEST partition)"},
    "UNSW_NB15_training-set.csv": {"b5a3168217dee84d94574e697130c8aa": "Zenodo copy (tab-separated, 82,332 rows = official TEST partition)",
                                   "e55caabaa6cd4a8f1c06a227bcfababc": "official UNSW file (175,341 rows = official TRAINING partition)"},
}
ok = True
for name, known in KNOWN.items():
    f = D / name
    if not f.exists():
        print(f"missing: {f}"); ok = False; continue
    h = hashlib.md5(f.read_bytes()).hexdigest()
    print(f"{name}: {h} -> {known.get(h, 'UNKNOWN (not a file checked for the paper)')}")
    ok &= h in known
print("The runners expect the Zenodo copies (tab-separated, swapped names). With the official files, swap the --train/--test arguments; content is identical." )
sys.exit(0 if ok else 1)
