# RELIFT_J1: SAM 3 frozen detector per frame (h1), pool oracle (h0), box oracle (k), paired inside dump 174135

Status: complete (h1 not read: pool parity 5104/7424 below 95%; h0 not read: pool parity 5104/7424 below 95%; k is read). Parity: 5104 of 7424 operand-frames match (0.6875; bar 0.95; FAILED: parity below 95% of operand-frames: h1 and h0 are not read; k is read); strict rule (same count, all paired, not gating) 4930 (0.6641).
Pick agreement (h1, h0 rules on both pools; gate 0.95 each): h1 4969/7424 (FAILED); h0 6049/7424 (FAILED)

| dataset | items | rooms | k - a | e - a |
|---|---|---|---|---|
| all (decides) | 117 | 35 | +13.8 [+5.5, +22.3] | +13.8 [+5.5, +22.3] |
| ARKit | 33 | 10 | +7.0 [-3.9, +20.0] | +7.0 [-3.9, +20.0] |
| ScanNet | 24 | 7 | +27.1 [+14.3, +82.0] | +27.1 [+14.3, +82.0] |
| ScanNet++ | 60 | 18 | +12.2 [-3.0, +24.8] | +12.2 [-3.0, +24.8] |

Verdicts (all 117 items): k opens (share of e-a 1.00)

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
| k | ARKit | 1.000 | 1.000 | 0 |
| k | ScanNet | 1.000 | 1.000 | 0 |
| k | ScanNet++ | 1.000 | 1.000 | 0 |
| k | all | 1.000 | 1.000 | 0 |

Supply outside the 117: GT capture missing: 2 items, 1 rooms (1 new); portrait GT orientation censored: 12 items, 8 rooms (8 new); unbound operand: 19 items, 14 rooms (2 new). R0-dev stays unspent.
