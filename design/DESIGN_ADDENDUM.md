# Design addendum: exposure-matched one-time arm (M1-seq)

Written 2026-10-26, AFTER the results of the first matched runs (M1, M1-e10, M2) and the sensitivity analysis were known, and BEFORE any M1-seq run. It was added in response to review: M1 and M2 matched the number and source-flow set of attack attempts, but not optimizer steps or per-example exposure. Its results are reported whatever they show.

## Arm
M1-seq starts from the clean initial model. It uses exactly the 500 perturbed vectors that M1 generated against the initial model before round 1, split into the five per-round groups of 100 (the same source-flow groups that M2 attacks in rounds 1 to 5). Before round 1 it makes five consecutive updates. Update r uses group r plus the same 1,000-example clean memory, the same epochs (2), learning rate (0.001) and batch size (256), and the same shuffling seed (seed + r) as M2's round-r update. Adam state carries across the updates, as it does for M2.

## What is matched between M1-seq and M2
The number of update calls (5), optimizer steps, batch sizes, per-example exposure (each adversarial vector for 2 epochs, the clean memory for 10 epochs in total), learning rate, shuffling seeds, source-flow groups, and labels.

## What differs
1. The model the examples were generated against: the initial model for M1-seq, and M2's current model in each round.
2. When the updates happen relative to evaluation: M1-seq completes all five before round 1, while M2 completes update r after round r's evaluation attack.
At round 5 both have completed all five updates, so the round-5 contrast M1-seq - M2 isolates difference 1. M1 - M1-seq holds the perturbed vectors fixed and isolates the update structure (one 2-epoch update against five).

## Runs and analysis
Seeds 17-36, all three settings, with the same command as the main matched runs plus --matched-seq (runner run_matched_seq.py). All earlier arms are recomputed in the same runs and must equal results_main exactly. Round-5 calibrated attack-induced ASR, seed-paired contrasts M1-seq - M2, M1 - M1-seq and M1-seq - A, with 95% t intervals, seed counts and descriptive sign tests, as in DESIGN.md. Clean-side measures are reported as for the other matched arms.
