# Switching a duplicate-trained pose student to P0.5 partner frames (C1-a-sw P3 read, 2026-11-08)

## Question
FP1's frozen probe put P0.5 partner frames ahead of the duplicate layout (middle-layer rotation 68.1 vs 75.2 deg). T0 warm-starts from C1-a m800, which trained on the duplicate layout. Should CP1 (Mon 10:30 PT) switch the final run to P0.5?

## Test
C1-a-sw forks C1-a's step-170 state (pin ap/7b30c1e4/pin/a170) into the P0.5 layout and trains steps 171-400 on C1-a's rows in C1-a's order (trainer a981cd79, root ap/a5ed51d1, run runs/e2f0b052). The only difference from C1-a is the frame layout. Both arms are read at m400 with the same sparse readout: 38 held-out scenes (18 ScanNet, 20 ScanNet++; the bank has no ARKit scenes), paired per scene, seeded bootstrap 90% CI over scenes. Evidence: ap/a5ed51d1/o/114623.5.json (artifact d4f48613, readout 808a0a04) against ap/7b30c1e4/o/112147.5.json. Summary script: heads_up/work/h6/readout_summary.py; output heads_up/work/h6/c1p/p3_read_sw400_vs_a400.txt.

## Result
P0.5 loses. Differences are sw minus a, so positive means the switch is worse.

| Measure | C1-a-sw m400 | C1-a m400 | Paired diff [90% CI] | sw better on |
|---|---|---|---|---|
| Rotation, even-gate mean / median | 33.1 / 22.1 deg | 29.8 / 19.1 deg | +3.3 [+0.8, +6.1] | 12/38 |
| ScanNet rotation | 31.5 / 20.4 | 26.1 / 17.1 | +5.4 [+1.7, +10.8] | 3/18 |
| ScanNet++ rotation | 34.5 / 23.3 | 33.0 / 20.4 | +1.5 [-1.5, +4.5] | 9/20 |
| Centre mean / median | 1.18 / 0.73 m | 1.08 / 0.67 m | +0.08 [+0.00, +0.17] | 16/38 |
| ScanNet centre | 1.11 / 0.71 | 0.98 / 0.61 | +0.13 [+0.03, +0.25] | 6/18 |
| ScanNet++ centre | 1.21 / 0.74 | 1.12 / 0.69 | +0.04 [-0.09, +0.16] | 10/20 |
| Pair-displacement MRA (scale) | 0.50 | 0.50 | - | - |
| Training pose loss / no-pixel prior | 0.418 | 0.390 | - | - |

The readout reports no FoV metric and a null log-scale error for both arms, so pair-displacement MRA is the only scale measure (ScanNet 0.40 vs 0.50).

FP2 (frozen probe, one seed, no CI) adds P0.2: it keeps P0.5's middle-layer rotation gain (66.8 vs 68.1 deg; D 75.2) but loses P0.5's position gain (2.16 vs 1.79 m; D 1.92).

## Decision
Keep the duplicate layout at CP1. Every run after T0 inherits duplicate-trained weights, so a later layout change is a switch, and the switch costs 3.3 deg of rotation and 0.08 m of centre error at m400 with both CIs at or above zero. The frozen-probe edge for P0.5 did not survive 230 trained steps.

Two lever arms stay unrun. C1-a-p (P0.5 from base) and C1-a-ei (carrier init at embedding scale) test from-scratch starts, which no CP1 run uses. Run either only if a decision appears that takes a from-scratch start.
