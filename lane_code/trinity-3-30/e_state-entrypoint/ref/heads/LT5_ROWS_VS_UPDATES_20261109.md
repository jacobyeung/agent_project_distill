# LT5: is pose training rows-bound or update-bound? (2026-11-09)

## Question
T0 trains pose at 64 rows per update. If pose loss depends on the number of updates rather than the number of rows, CP2 should cut pose to 32 rows per update or rotate streams. TRAINING_EFFICIENCY_20261108.md pre-registered LT5 to decide this.

## Test
LT5 forks C1-a's step-170 state (pin ap/7b30c1e4/pin/a170) and trains updates 171-255 at B=64, on exactly the rows of C1-a's steps 171-340 (B=32) in the same order. The LR is indexed by rows: each update uses the source LR of its last row's step. Each update reports `source_step_first`/`source_step_last` (update 231 reads C1-a steps 291-292, as designed). Only the batch size differs. Trainer b01712bb, root ap/93c3fb09, run runs/b55a0001, legs 114096, 114140 and 114714 (budget stops at 222/230 and 252, exact resume states; final state checkpoint_000255).

Metric: online pose loss on the same rows, LT5 over C1-a. On equal rows the no-pixel prior cancels, so this ratio equals the pre-registered "pose loss over prior" comparison. Rule: rel <= 1.04 means rows-bound; rel >= 1.08 with the CI above 1.04 means update-bound. Script: heads_up/work/h6/lt5_aws.py (same pairing and bootstrap as loss_doctor bin/lt5.py); output heads_up/work/h6/lt/lt5_read.txt.

## Result
Pose is rows-bound.

| LT5 updates | C1-a steps | LT5 loss | C1-a loss | rel |
|---|---|---|---|---|
| 171-180 | 171-190 | 0.4411 | 0.4428 | 0.996 |
| 181-190 | 191-210 | 0.4174 | 0.4199 | 0.994 |
| 191-200 | 211-230 | 0.4116 | 0.4130 | 0.997 |
| 201-210 | 231-250 | 0.3845 | 0.3857 | 0.997 |
| 211-220 | 251-270 | 0.3893 | 0.3859 | 1.009 |
| 221-230 | 271-290 | 0.3655 | 0.3615 | 1.011 |
| 231-240 | 291-310 | 0.3577 | 0.3542 | 1.010 |
| 241-250 | 311-330 | 0.3508 | 0.3580 | 0.980 |
| 251-255 | 331-340 | 0.3403 | 0.3343 | 1.018 |

Over all 85 updates rel = 1.000 [90% CI 0.996, 1.004]; over the last 40, 1.005 [0.999, 1.010]; over the last 20, 0.994 [0.984, 1.004]. The windows show no upward trend, and the whole CI sits far below the +4% bound.

## Decision (CP2)
Keep 64 pose rows per update. Halving the update count at equal rows costs no measurable pose loss, so pose improves by buying rows, not updates; do not cut to 32 rows or rotate streams for pose. Raising the LR or moving to B=16 stays unsupported.

