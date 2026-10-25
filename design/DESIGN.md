# Budget-matched comparison: design (fixed before any matched run)

Written 2026-10-26, before any matched-arm output existed. This experiment is new. It is kept separate from the reported five-seed exploratory matrix.

## Question
With the same adversarial-example budget, the same source flows, the same update procedure and the same evaluation, does a one-time schedule differ from an incremental schedule in attack-induced ASR and clean-side measures?

## Shared protocol (unchanged from the reported runs)
Same raw files (Zenodo 3768048, MD5-verified), the same stratified split per seed, the same preprocessing, MLP, initial training (5 epochs), attack settings (FGSM-like, BIM-like, decision-only; eps 0.03; 11 features), per-round attacker budget (100 malicious adaptation flows, and for decision-only at most 50 queries per flow and 5,000 per round), evaluation cohort (up to 1,000 malicious test flows detected by the initial model), fixed threshold, and validation-calibrated threshold rule (at most 5% validation FPR per checkpoint). The test set is never used for fitting, updating or threshold choice.

## Counting rule (fixed in advance)
One adversarial training example = one attacked malicious flow, labeled malicious, counted whether or not the perturbation evaded the target model. Counting attempts rather than successes lets both schedules receive exactly the same number (success counts depend on each model). For the decision-only attack, a failed attempt leaves the flow unperturbed, and it still counts as one example.

## New arms (added after the six original arms, so the original arms' random streams are unchanged)
- M1 one-time matched: starts from the clean initial model. Before round 1 it attacks the union of the 500 adaptation flows that rounds 1 to 5 will attack (the per-round selections depend only on the seed and stream, not on any model). The attacks target the initial model with the setting's attack. It then makes one update on 500 adversarial examples plus the 1,000-example clean memory, for 2 epochs at lr 0.001. No later updates.
- M2 incremental matched: starts from the clean initial model. In each round it attacks that round's 100 flows against its current model and makes one update on all 100 attempts plus the same 1,000-example clean memory, for 2 epochs at lr 0.001. Total: 500 adversarial examples over five rounds.
- M1-e10 (bracketing variant): as M1, but the single update runs for 10 epochs. M2 replays the clean memory for 2 x 5 = 10 epochs in total, while M1 replays it for 2. M1-e10 matches that exposure, but sees each adversarial example for 10 epochs instead of 2. M1 and M1-e10 bracket the schedule comparison, and neither is chosen after seeing results.
- Decision-only threat-matched static baseline (decision-only setting only): B-dec follows the original static procedure (500 initial-training malicious flows, extra 5 epochs on initial data plus the examples), with examples from the decision-only attack against the initial model at the fixed threshold. In this setting M1 is also threat-matched.

What remains different between M1 and M2 is the schedule, as intended: when the examples are generated, which model they target (initial versus current), and the number of update calls. This is the contrast under study, and it is reported as such.

## Seeds and analysis
- Seeds 17 to 36 (20 seeds). Seeds 17 to 21 are the original seeds, and the original arms must reproduce the reported outputs on them.
- Primary measure: round-5 attack-induced ASR at validation-calibrated thresholds, reported with pre-attack detection, post-attack benign rate, clean recall, FPR, F1 and AUC.
- Paired contrasts by seed: M1 - M2, M1-e10 - M2, B - M1, B - B-dec. Report the mean difference, a 95% t interval (df 19), the count of seeds in which the first arm was lower, and an exact two-sided sign test as a descriptive check, with no multiplicity claims of superiority. The family of contrasts is listed in advance, and all of them are reported.

## Update-setting sensitivity (exploratory, pre-declared, FGSM-like setting, seeds 17 to 36)
One factor at a time around the default (2 update epochs, lr 0.001, memory 1,000), applied to arms C, M1 and M2: update epochs {1, 4}, lr {0.0005, 0.002}, memory {500, 2000}. Every configuration is reported. None is selected as best, and none is chosen on test results.
