Fixed GT-depth eligibility and hole sampling. **10 of 17 audited refusals now answer; seven lack usable depth.** All **19 tests pass**, and **10,024 served-depth row/cell outputs remain identical**. `out/` is untouched.

Part 1: held-out MRA-point changes, with 95% CIs. A uses the full population; B uses identical valid frame support.

| Contrast | A | B | ARKit A / B | ScanNet/++ A / B |
|---|---:|---:|---:|---:|
| C1 | −0.46 [−4.86, 3.51] | +1.69 [−1.79, 5.72] | −2.25 / +2.35 | +1.14 / +1.18 |
| C3 depth | +3.94 [0.86, 7.22] | +3.94 [0.86, 7.22] | +2.94 / +2.94 | +4.82 / +4.82 |
| C3 pose | −0.19 [−3.54, 3.69] | −0.19 [−3.54, 3.69] | +1.47 / +1.47 | −1.67 / −1.67 |
| C3 joint, own scale | +3.70 [−0.30, 8.06] | +3.70 [−0.30, 8.06] | +4.51 / +4.51 | +2.98 / +2.98 |
| C3 full GT geometry | +7.13 [3.08, 11.59] | +7.13 [3.08, 11.59] | +11.96 / +11.96 | +2.81 / +2.81 |

A includes 216 rows. C1 B retains **195/216 rows across 46 rooms**: ARKit 85/102; ScanNet/++ 110/114. C3 B retains all 216 rows.

**Verdicts:** Overall C1 says “geometry waits for masks” under both readings. **ARKit disagrees: A says “waits,” B says “undecided”; neither reading is preferred.** Overall C3 depth/pose gates and the full arm-B gate fail. ARKit meets the interaction criterion.

Part 2: BOX scores under deployed masks.

| Rule | Held-out MRA | Δ [95% CI] | Train1012 | GT-mask held-out | Δ ARKit / ScanNet++ combined |
|---|---:|---:|---:|---:|---:|
| Base | 63.29 | — | 56.93 | 72.64 | — |
| E3 fusion | 66.25 | +2.96 [−0.90, 7.13] | 57.83 | 61.30 | +0.20 / +5.44 |
| `vote_10_3_best` | **68.94** | **+5.65 [2.09, 9.62]** | 60.20 | 78.98 | +3.53 / +7.54 |
| Robust centre | 58.98 | −4.31 [−8.65, 0.00] | 55.39 | 67.96 | −5.98 / −2.81 |
| Area floor, F=0 | 63.29 | 0.00 [0.00, 0.00] | 56.93 | 72.64 | 0.00 / 0.00 |

**Frozen voting clears the held-out bar; a proposal remains pending rank 1’s dev-item check.** The other rules fail the bar.

Files, including all eight GT-depth rows under A and B:

- Part 1: [report](out4/REPORT_R2_4.md), [K1X4.json](out4/K1X4.json), [SHA256SUMS](out4/SHA256SUMS).
- BOX: [report](out_box/REPORT_BOX.md), [BOX.json](out_box/BOX.json), [SHA256SUMS](out_box/SHA256SUMS).

Both checksum manifests verify. Deviations: persistent command sessions replaced tmux; small required skill files were read under `/home`. Experiment data stayed on `/scratch`.