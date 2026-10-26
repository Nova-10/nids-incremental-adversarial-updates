# Design addendum 2: recipe-matched incremental arm (M2-full)

Written 2026-10-27, after all earlier results were known and BEFORE any M2-full run. Added because the original static arm (B) trains on the full initial training part together with its adversarial examples, while every incremental arm (C, M2) trains on adversarial examples plus a 1,000-example clean memory only. The extension therefore never compared one-time and incremental schedules under B's training recipe. The results are reported whatever they show.

## Arm
M2-full starts from the same clean initial model (5 epochs on the initial training part). In each round r = 1..5 it is attacked at its current model with the same 100 adaptation flows as M2 (same attack, bound, and query limit). Every attempt, successful or not, is kept and labeled malicious. After round r's attack it makes one update of 1 epoch on the full initial training part plus all attempts collected in rounds 1..r, learning rate 0.001, batch size 256, shuffling seed (seed + r). Adam state carries across updates.

## What is matched with the original static arm B
- Total extra passes over the full initial training part: 5 (B: one 5-epoch update; M2-full: five 1-epoch updates).
- Number of adversarial attempts: 500 (B: 500 vectors; M2-full: 5 x 100).
- Learning rate, batch size, optimizer, initial model.

## What differs
1. Schedule: B updates once before round 1; M2-full updates after each round.
2. Source flows: B's 500 vectors come from the initial training part, M2-full's from the adaptation stream (as for all matched arms).
3. Generating model: B's vectors are generated against the initial model; M2-full's against its current model in each round.
4. Exposure of adversarial vectors: B sees each of its vectors 5 times (2,500 example-passes); M2-full sees round-r vectors 6 - r times (1,500 example-passes in total).
5. Labels: B's vectors are all successful or not at the static step in the same way (all labeled malicious); M2-full likewise labels every attempt malicious.
6. In the decision-only setting B is trained on FGSM-like vectors (cross-attack); M2-full uses decision-only attempts, so it is also compared with B-dec there.

## Runs and analysis
Seeds 17-36, all three settings, same command as the M1-seq runs plus --full-arm (runner run_matched_full.py). All earlier arms are recomputed in the same runs and must equal results_seq exactly. Pre-declared round-5 contrasts at validation-calibrated thresholds: M2-full - B (primary), M2-full - M2, M2-full - M1-e10, M2-full - A, and in the decision-only setting M2-full - B-dec. 95% t intervals (df 19), seed counts and descriptive sign tests, no multiplicity correction. Clean recall, FPR, F1, AUC, pre-attack detection and time are reported for M2-full and B.
