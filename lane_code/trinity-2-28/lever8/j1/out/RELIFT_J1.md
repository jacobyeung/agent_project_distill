# RELIFT_J1: SAM 3 frozen detector per frame (h1), pool oracle (h0), box oracle (k), paired inside dump 174135

Status: complete. Parity: 7410 of 7424 operand-frames match (0.9981; bar 0.95; passed); strict rule (same count, all paired, not gating) 6636 (0.8939).
Pick agreement (h1, h0 rules on both pools; gate 0.95 each): h1 7394/7424 (passed); h0 7411/7424 (passed)

| dataset | items | rooms | h1 - a | h0 - a | k - a | e - a |
|---|---|---|---|---|---|---|
| all (decides) | 117 | 35 | -12.0 [-21.7, -2.6] | -12.3 [-23.0, -1.9] | +11.0 [+0.7, +20.9] | +13.8 [+5.5, +22.3] |
| ARKit | 33 | 10 | -11.8 [-31.6, +2.9] | -7.0 [-24.5, +11.8] | +1.8 [-9.3, +14.4] | +7.0 [-3.9, +20.0] |
| ScanNet | 24 | 7 | -12.1 [-22.7, +27.8] | +7.5 [-9.5, +78.3] | +11.7 [+0.0, +40.0] | +27.1 [+14.3, +82.0] |
| ScanNet++ | 60 | 18 | -12.0 [-28.4, +1.8] | -23.2 [-40.6, -9.8] | +15.8 [-3.9, +31.2] | +12.2 [-3.0, +24.8] |

Verdicts (all 117 items): h1 closes (share of e-a -0.87); h0 closes (share of e-a -0.89); k opens (share of e-a 0.80)

| arm | dataset | precision | recall | anchors with mask, GT empty |
|---|---|---|---|---|
| a | ARKit | 0.627 | 0.398 | 30 |
| a | ScanNet | 0.629 | 0.459 | 34 |
| a | ScanNet++ | 0.591 | 0.457 | 57 |
| a | all | 0.609 | 0.443 | 121 |
| e | ARKit | 1.000 | 1.000 | 0 |
| e | ScanNet | 1.000 | 1.000 | 0 |
| e | ScanNet++ | 1.000 | 1.000 | 0 |
| e | all | 1.000 | 1.000 | 0 |
| h1 | ARKit | 0.321 | 0.597 | 340 |
| h1 | ScanNet | 0.319 | 0.570 | 293 |
| h1 | ScanNet++ | 0.328 | 0.516 | 465 |
| h1 | all | 0.323 | 0.549 | 1098 |
| h0 | ARKit | 0.897 | 0.502 | 0 |
| h0 | ScanNet | 0.870 | 0.529 | 0 |
| h0 | ScanNet++ | 0.885 | 0.471 | 0 |
| h0 | all | 0.884 | 0.492 | 0 |
| k | ARKit | 0.744 | 0.686 | 0 |
| k | ScanNet | 0.712 | 0.725 | 0 |
| k | ScanNet++ | 0.713 | 0.780 | 0 |
| k | all | 0.721 | 0.744 | 0 |

Supply outside the 117: GT capture missing: 2 items, 1 rooms (1 new); portrait GT orientation censored: 12 items, 8 rooms (8 new); unbound operand: 19 items, 14 rooms (2 new). R0-dev stays unspent.
