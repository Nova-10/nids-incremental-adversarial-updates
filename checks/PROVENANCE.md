# Dataset provenance check (2026-10-26)

## Files used for every run
Zenodo record 10.5281/zenodo.3768048 ("Tagged original datasets for 'Genetically Optimized Massively Parallel Binary Neural Networks for Intrusion Detection Systems'"). This is a third-party redistribution, not the official UNSW source. It holds the two partitions as tab-separated files with no header, and swaps their names: the Zenodo "testing-set" has 175,341 rows, which is the official training partition.
- UNSW_NB15_training-set.csv (Zenodo name) MD5 b5a3168217dee84d94574e697130c8aa, 82,332 rows. Matches the Zenodo API checksum.
- UNSW_NB15_testing-set.csv (Zenodo name) MD5 07a1566e74e89f4c970fd1dc3b5d554b, 175,341 rows. Matches the Zenodo API checksum.
Both MD5s also equal the values in the experiment record DATASET_CHECKSUMS.txt.

## Official source
https://research.unsw.edu.au/projects/unsw-nb15-dataset lists UNSW_NB15_training-set.csv (175,341 records) and UNSW_NB15_testing-set.csv (82,332 records), distributed via a UNSW SharePoint folder (CSV Files/Training and Testing Sets).
- Official UNSW_NB15_testing-set.csv (comma-separated, with header; MD5 e0beea40262e46168cdb81476dbc27b4) was downloaded and compared with the Zenodo file holding 82,332 rows. All 82,332 rows (matched by id) and all 45 columns are identical, and the class counts are identical (45,332 malicious, 37,000 benign).
- Official UNSW_NB15_training-set.csv: the download did not start from the browser pane. NOT compared. The 175,341-row partition is verified only against the Zenodo checksum.
- Official NUSW-NB15_features.csv (MD5 9e6f08b95bc19e4c4986d4d5729f3ce9) defines tcprtt as "the sum of synack and ackdat".

## Update (v11)
The official UNSW_NB15_training-set.csv (MD5 e55caabaa6cd4a8f1c06a227bcfababc, 175,341 records) was obtained from the official source and compared with the Zenodo file holding 175,341 rows. All records, matched by id, are identical in all 45 columns, string-exact. Both official partitions therefore match the files used in every run in content.
