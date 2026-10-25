# NIDS v11: official training-partition check (not part of the manuscript)

The file was found at RM Lab/UNSW_NB15_training-set.csv (32,293,018 bytes, saved 2026-10-25 18:59). Its timestamp matches the second browser download from the official UNSW SharePoint folder (CSV Files/Training and Testing Sets). The download had completed into RM Lab and was missed earlier. A copy was placed in RM Lab/UNSW-NB15_official/. The original is left in place.

- Official UNSW_NB15_training-set.csv: MD5 e55caabaa6cd4a8f1c06a227bcfababc; comma-separated with a UTF-8 BOM and header; 175,341 records.
- Compared with the Zenodo file used in every run (named UNSW_NB15_testing-set.csv, MD5 07a1566e74e89f4c970fd1dc3b5d554b, tab-separated, no header): all 175,341 records, matched by id, are identical in all 45 columns (string-exact). Class counts are identical (119,341 malicious, 56,000 benign).
- Together with the earlier test-partition check (82,332 records identical), both partitions used in the study have the same content as the official files. Only the format and the swapped file names differ.

Manuscript v11 (NIDS_Master_Paper_Final_v11.docx; v10 unchanged): Section 4.2 and the Data provenance row of Table 16 are updated. No results changed. The original tables still match 198/198 cells.

Remaining open items: [12] page range, author details, deposit decision, target journal, similarity check.
