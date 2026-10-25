# Reference verification ledger, v7 (2026-10-26)

Sources: Crossref REST API (publisher-deposited metadata), fetched from the user's computer through the built-in browser; publisher landing pages (wiserpub OJS, AAAI OJS); the full text of [34] (AAAI OJS PDF).
Google Scholar returned an "unusual traffic" CAPTCHA, which was not bypassed. IEEE Xplore returned an error page (code 418), and the ACM Digital Library returned a Cloudflare challenge, so neither could be read.

| Ref | Field status after v7 | Source |
|---|---|---|
| [1] | vol. 137, Art. no. 110173 restored | Crossref |
| [2] | vol. 4, no. 1, pp. 16–59, Jan. 2025 confirmed; author spelled "M. El-Shehaby" | Publisher page (Crossref lacks these fields) |
| [3] | vol. 13, pp. 148613–148645 restored | Crossref |
| [4]–[8] | vol. and Art. no. restored (134/103433, 129/103176, 128/103141, 137/103644, 145/104028) | Crossref |
| [9] | vol. 21, no. 6, Art. no. e0350737 restored (Crossref gives e0350737 as the page field) | Crossref |
| [10] | pp. 23–26 confirmed | Crossref |
| [11] | vol. 272, Art. no. 111712 restored | Crossref |
| [12] | Pages still omitted, as instructed. Crossref (IEEE deposit) and the UMass repository both give pp. 1–6, not 478–483. IEEE Xplore could not be read. The full text was not accessible, so claims stay limited to the abstract. | Crossref, repository |
| [14] | Crossref gives pp. 1–6. Not added, because earlier pages were removed as unverified; can be added from Crossref if wanted | Crossref |
| [15] | vol. 36, no. 25, Art. no. e8242 | Crossref |
| [17], [21], [26], [30], [32] | Existing fields match Crossref | Crossref |
| [23] | "Art. no. 31" replaced by pp. 1–19 (Crossref). The ACM article number was not confirmed | Crossref |
| [24] | Issue added: no. 11–12 (vol. 77, pp. 763–775 match) | Crossref |
| [28] | pp. 17156–17169 added | Crossref |
| [33] | pp. 547–554 added | Crossref |
| [34] | vol. 9, no. 1, pp. 309–314 restored. Full text read: XGBoost classifier on CICIDS-2017 packet features; contrastively trained reinforcement-learning attackers deployed sequentially; a reinforcement-learning defender chooses among online, active and continual learning and pseudo-labeling; post-attack accuracy falls to an average of 35% in their runs | Crossref, publisher page, full text |
| [35] | Zenodo DOI (DataCite, not in Crossref); title and files confirmed through the Zenodo API | Zenodo API |
| [13], [16], [18]–[20], [22], [25], [27], [29], [31], [36], [37] | Not rechecked in this pass (arXiv, ICLR, USENIX, NeurIPS entries without Crossref DOIs) | — |

Citation order and the in-text-to-entry mapping are checked in the v7 build.
