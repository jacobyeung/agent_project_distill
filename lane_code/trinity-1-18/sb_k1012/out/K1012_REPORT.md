# K1 training tables on the 1,012 rows outside the 80 withheld rooms
On the 1,012 rows one bar verdict changes: selector_worth goes PASS → FAIL (oracle selection A1 − A0 on the table rows, bar ≥ +4: +4.10 → +3.91 [+1.88, +6.05] on 868 rows). Every other bar and every frozen choice keeps its 1,037 verdict.
The phrase fold policy stays heater → radiator in all five folds, and the mask-failure table keeps the ranking of its independent gains and each interval's relation to zero.
The fixed checker (sb_auditfix2) puts 6 K1 training captures in 5 withheld rooms, as the ruling says; 5 of them hold 25 priced rows (15 in the 883 table rows), leaving 1,012 rows in 188 rooms and 868 table rows.
Rowset `out/K1_TRAIN_1012.txt` sha256 `48c13fac3205b7c53c79d4efda1e661eb7dae88021dc261639ce4b5581a646d7`; all four planted probes and the planted-row filter test pass, and a raw-list check without checker code agrees. Every number uses the kits' own code (1,037 parity exact), 10,000 room draws, seed 20261119.
### Box ladder (sb_kbox4, LADDER_TRAIN): MRA or paired gain [95% CI]; cross-fitted choices and the A8 selector refit on the 1,012
| Quantity | 1,037 | 1,012 | Bar: verdict 1,037 → 1,012 |
|---|---:|---:|---|
| A0 deployed | 56.77 [52.48, 61.04] | 56.93 [52.52, 61.34] | |
| A1 oracle selection (883 / 868 table rows) | 61.65 [57.22, 65.73] | 61.66 [57.06, 65.90] | |
| A2 GT masks | 73.97 [69.70, 77.64] | 74.39 [70.11, 78.14] | |
| Fusion on GT, cross-fitted (fused_cf) | 78.62 [74.55, 82.12] | 78.74 [74.52, 82.35] | |
| A7 DA3 tower, GT masks, best1 | 77.81 [74.57, 80.89] | 78.08 [74.80, 81.16] | tower_challenger: SKIPPED → SKIPPED |
| A7 Pi3X tower, GT masks, best1 | 77.71 [74.29, 80.72] | 77.98 [74.59, 81.04] | |
| A8 non-null selector, OOF (tables) | 53.74 [49.01, 58.18] | 53.55 [48.79, 58.38] | |
| Object variant cross-fitted − A0 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | replace_box: FAIL → FAIL (≥ 3, low > 0) |
| fused_cf − A2 | +4.65 [+3.04, +6.44] | +4.35 [+2.71, +6.14] | fused_path: PASS → PASS (≥ 3, low > 0) |
| A1 − A0 (tables) | +4.10 [+2.06, +6.22] | +3.91 [+1.88, +6.05] | selector_worth: PASS → FAIL (≥ 4) |
| A8 − A0 (tables) | -3.82 [-5.84, -1.83] | -4.21 [-6.48, -2.03] | selector_adopt: FAIL → FAIL (low > 0) |
| Size MRA, object variant cross-fitted − A0 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | size_screen: FAIL → FAIL (≥ 5, low > 0) |
| Member precision τ 0.25 / 0.15 / 0.40, all rows | 72.5% / 73.3% / 73.1% | 74.6% / 75.5% / 75.4% | merge_safe: NA → NA (no variant reaches 90%) |
| First-seen pair order, linker | 76.56% of 1,314 | 76.12% of 1,277 | first_seen_screen: FAIL → FAIL (≥ 90%) |

The FREEZE choices are unchanged on the 1,012: no object variant qualifies, no appearance τ is frozen, and GT fusion picks vote_10_3_best in all five folds and all rooms. The A8 refit removes 21 withheld-room objects from the fit folds and changes 94 choices on the 868 rows (78 captures); with the kit's own folds, A8 − A0 is -4.12 [-6.16, -2.16].
### Phrase kit (sb_mask_phrase, BARS.json sha256 150d16a2): MRA, gain over A0 [95% CI]; 1,012 uses folds refit without the withheld captures
| Arm | 1,037: MRA, minus A0 | 1,012: MRA, minus A0 | Safe rows minus A0, 1,037 / 1,012 | phrase_worth, phrase_safe: 1,037 → 1,012 |
|---|---:|---:|---:|---|
| P0 | 56.77, +0.00 [+0.00, +0.00] | 56.93, +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] / +0.00 [+0.00, +0.00] | parity arm (= A0) |
| W1 | 60.50, +3.73 [+2.05, +5.48] | 60.75, +3.82 [+2.16, +5.63] | +0.46 [+0.00, +1.22] / +0.48 [+0.00, +1.23] | PASS → PASS, PASS → PASS |
| W2 | 60.36, +3.59 [+1.91, +5.35] | 60.60, +3.68 [+2.01, +5.48] | +0.42 [+0.00, +1.17] / +0.43 [+0.00, +1.18] | PASS → PASS, PASS → PASS |
| W2c | 57.86, +1.09 [+0.04, +2.40] | 58.04, +1.12 [+0.04, +2.50] | +0.00 [+0.00, +0.00] / +0.00 [+0.00, +0.00] | FAIL → FAIL, PASS → PASS |

Safe rows: 456 → 442. Refit folds: heater → radiator in folds 0–4 and all rooms (20 heater objects, none withheld); every other fold choice is unchanged, so the registered-policy re-score equals the refit one. Chosen arm W1 (1,037: W1); rows to rewrite on the 1,012: heater 84.
### Mask failure attribution (sb_mffix first table, IoU 0.5): independent gain over A0 in MRA points [95% CI]
| Failure kind | Visible frames, 1,037 / 1,012 | Independent gain, 1,037 | Independent gain, 1,012 | Ordered increment, 1,012 (% of gap) |
|---|---:|---:|---:|---:|
| no_proposal | 3,200 / 3,155 | +8.18 [+5.64, +10.77] | +8.28 [+5.68, +10.96] | +8.28 (+47.4%) |
| selected track absent | 2,393 / 2,291 | +3.78 [+2.16, +5.51] | +3.83 [+2.21, +5.64] | +3.06 (+17.5%) |
| wrong_instance (structurally empty) | 0 / 0 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 (+0.0%) |
| wrong_class | 336 / 336 | -1.74 [-3.42, +0.05] | -1.77 [-3.51, +0.12] | +3.96 (+22.7%) |
| partial_mask | 442 / 426 | +0.31 [-0.24, +0.94] | +0.32 [-0.25, +0.95] | +0.47 (+2.7%) |
| merged_instances | 390 / 390 | -0.35 [-0.81, +0.11] | -0.36 [-0.83, +0.11] | +0.84 (+4.8%) |
| other_mask_error | 938 / 924 | -0.60 [-1.84, +0.57] | -0.70 [-1.94, +0.48] | +1.71 (+9.8%) |
| correct | 6,094 / 5,873 | +0.11 [-0.83, +1.10] | +0.12 [-0.85, +1.13] | -0.87 (-5.0%) |

A2 − A0 gap: +17.20 [+13.54, +20.89] on 1,037 and +17.46 [+13.69, +21.24] on 1,012 (13,793 → 13,395 visible frames; the withheld rows hold no wrong_class or merged_instances frames).
Caveats. The deployed run_iso selector, used by A0 and by every arm built on it, was fit on 4 of the withheld captures (15 objects); retraining the deployed reader was out of scope, so A0 itself is not withheld-free. The S4 scale fit behind A9 (no bar) used all 6 withheld captures.
Over all fit objects, dropping 4 random non-withheld rooms instead changes 104 OOF choices (median of 5 draws, range 89–121), against 113 for the withheld rooms: the A8 shift is mostly refit noise. No kit file was written (find -newer, K1012.json); CPU only, nice 10, 8 threads.
Commands: `bash run.sh legality.py`, `refit_a8.py`, `a8_placebo.py`, `kbox_1012.py`, `phrase_1012.py`, `mffix_1012.py`, `report.py`. Details and input sha256: out/K1012.json and the per-kit JSONs.
