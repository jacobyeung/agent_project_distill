# K5-S: tower instability against tower error (CPU, banked K5 returns)
Disagreement: A1 vs D1 by score_k5.compare(); rot = largest per-frame rotation diff (deg, primary), trans = largest metric centre diff (m, secondary). Error: A1 cm vs GT at the 32 anchors by gt/v2.alignment(). Classes: audit (CAMERA_SPLIT.json); A1-class by the same rule, not used for the verdict.

| dataset | capture | audit | A1-class | A1 t RMS m | A1 rot max deg | dis rot deg | dis trans m |
|---|---|---|---|---|---|---|---|
| ARKit | 41069053 | gross | gross | 1.315 | 167.27 | 11.5 | 0.697 |
| ARKit | 41069054 | gross | gross | 1.190 | 179.21 | 2.65 | 0.265 |
| ARKit | 41098140 | moderate | moderate | 0.123 | 9.54 | 2.67 | 0.0887 |
| ARKit | 41098149 | moderate | moderate | 0.212 | 13.99 | 0.187 | 0.0207 |
| ARKit | 41159782 | pass | pass | 0.063 | 4.71 | 0.134 | 0.00595 |
| ARKit | 41291639 | gross | gross | 0.446 | 158.44 | 3.61 | 0.0458 |
| ARKit | 41291643 | gross | gross | 0.273 | 85.25 | 1.7 | 0.0396 |
| ARKit | 42446117 | moderate | moderate | 0.340 | 38.14 | 48.7 | 1.07 |
| ARKit | 42897921 | moderate | moderate | 0.226 | 23.39 | 3.23 | 0.0228 |
| ARKit | 42897936 | moderate | moderate | 0.138 | 13.00 | 0.311 | 0.02 |
| ARKit | 42897942 | moderate | moderate | 0.189 | 15.47 | 0.267 | 0.0135 |
| ARKit | 42899532 | gross | gross | 0.418 | 70.87 | 2.66 | 0.186 |
| ARKit | 42899535 | gross | gross | 0.329 | 83.86 | 1.76 | 0.0351 |
| ARKit | 43649603 | moderate | moderate | 0.179 | 5.30 | 0.154 | 0.00751 |
| ARKit | 43828324 | moderate | moderate | 0.201 | 7.50 | 0.291 | 0.0129 |
| ARKit | 43828368 | moderate | moderate | 0.099 | 6.30 | 0.119 | 0.00517 |
| ARKit | 44358634 | moderate | moderate | 0.147 | 9.52 | 8.27 | 0.591 |
| ARKit | 45261332 | pass | pass | 0.072 | 3.61 | 0.15 | 0.00443 |
| ARKit | 45663051 | gross | gross | 0.144 | 176.03 | 0.252 | 0.00777 |
| ARKit | 47330997 | moderate | moderate | 0.299 | 48.26 | 0.641 | 0.0219 |
| ARKit | 47332556 | moderate | moderate | 0.165 | 35.07 | 0.458 | 0.0103 |
| ARKit | 47332598 | gross | gross | 0.198 | 72.99 | 0.344 | 0.00701 |
| ARKit | 47332599 | moderate | moderate | 0.116 | 12.39 | 0.222 | 0.00538 |
| ScanNet | scene0166_00 | moderate | moderate | 0.117 | 6.25 | 0.09 | 0.00326 |
| ScanNet | scene0166_02 | moderate | moderate | 0.087 | 5.18 | 0.085 | 0.00358 |
| ScanNet | scene0250_01 | pass | pass | 0.055 | 4.72 | 0.151 | 0.00419 |
| ScanNet | scene0515_02 | moderate | moderate | 0.112 | 5.38 | 0.121 | 0.00681 |
| ScanNet++ | 0c7962bd64 | pass | pass | 0.051 | 3.71 | 0.156 | 0.00386 |
| ScanNet++ | 17c5e6a336 | moderate | moderate | 0.226 | 10.03 | 0.185 | 0.00671 |
| ScanNet++ | 307e3262f1 | gross | gross | 0.318 | 64.67 | 3.59 | 0.0734 |
| ScanNet++ | 6a217fbcb0 | moderate | moderate | 0.050 | 6.66 | 0.138 | 0.00321 |
| ScanNet++ | 7e7cd69a59 | moderate | moderate | 0.225 | 3.19 | 0.151 | 0.0221 |
| ScanNet++ | 80ffca8a48 | gross | gross | 1.063 | 140.36 | 4.56 | 0.106 |
| ScanNet++ | 99a2503d63 | pass | pass | 0.084 | 4.54 | 0.196 | 0.00658 |
| ScanNet++ | aaa9c251de | moderate | moderate | 0.144 | 6.79 | 0.107 | 0.00639 |
| ScanNet++ | ad562ce09b | moderate | moderate | 0.173 | 13.97 | 0.452 | 0.0117 |
| ScanNet++ | e7ccd75e5d | pass | pass | 0.058 | 3.26 | 0.0752 | 0.00688 |
| ScanNet++ | eb8ef9b4cc | moderate | moderate | 0.089 | 5.48 | 0.147 | 0.00659 |

Spearman (n=38): rot vs A1 t RMS 0.758 (p 3.57e-08), rot vs A1 rot max 0.764 (p 2.35e-08); trans vs A1 t RMS 0.835 (p 6.85e-11), trans vs A1 rot max 0.680 (p 2.59e-06). AUC [95% capture bootstrap, 10000 draws, seed 0] (n positive/n pass), audit classes:

| metric | scope | gross vs pass | moderate vs pass | gross+moderate vs pass |
|---|---|---|---|---|
| primary rot | pooled | 1.000 [1.000, 1.000] (10/6) | 0.697 [0.478, 0.891] (22/6) | 0.792 [0.629, 0.927] (32/6) |
| primary rot | ARKit | 1.000 [1.000, 1.000] (8/2) | 0.923 [0.750, 1.000] (13/2) | 0.952 [0.850, 1.000] (21/2) |
| primary rot | ScanNet | n/a (0/1) | 0.000 [0.000, 0.000] (3/1) | 0.000 [0.000, 0.000] (3/1) |
| primary rot | ScanNet++ | 1.000 [1.000, 1.000] (2/3) | 0.500 [0.000, 1.000] (6/3) | 0.625 [0.200, 1.000] (8/3) |
| secondary trans | pooled | 1.000 [1.000, 1.000] (10/6) | 0.780 [0.591, 0.939] (22/6) | 0.849 [0.713, 0.959] (32/6) |

Replicate A2 vs D2: rotation disagreement equal to A1 vs D1 on 38/38 audit captures (84/84 of all K5), translation on 38/38; max diff 0 deg, 0 m; replicate primary gross-vs-pass pooled AUC 1.000 [1.000, 1.000] (10/6).
K5 tail (primary > 3.9 deg; observed p90 4.21 deg): 9/84 captures; ScanNet 1/29, ScanNet++ 2/25, ARKit 6/30; 4 of the tail are among the 38.
Classes: audit {'gross': 10, 'moderate': 22, 'pass': 6}; A1 {'gross': 10, 'moderate': 22, 'pass': 6}; audit and A1 class agree on 38/38. Fit check: alignment() on the audit's own T1 cameras reproduces CAMERA_SPLIT rigid_fit on 38 captures (all within 1e-5: True, accepted equal: True, max dev 0); GT.json sha matches audit provenance: True.

**Reading as registered** (primary, gross vs pass, pooled; >=0.80 candidate, <0.65 closed, else undecided): AUC 1.000 [1.000, 1.000] -> **candidate**. With 10 gross and 6 passing captures the area is fragile: the smallest gross disagreement is 0.252 deg against a largest pass of 0.196 deg, and the interval is degenerate because every resample keeps the separation, so it cannot show that fragility.
