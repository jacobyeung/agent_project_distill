# E3: tool geometry priced in benchmark points without training (2026-11-16)

Status: COMPLETE for every candidate except the deployed column, which waits for K1 own depth and gravity. The integrated run equals the shard tables (10:05Z). The two harness edits are unreviewed: review them before a number from this harness enters a paper or a route decision. Lane e3_geom on trinity-1-18 (/scratch/jjyeung/orch_n30/e3_geom).

## Question
Does a stronger metric scale or a floor rule make room programs beat direct answers by at least 10 task points on m² questions, and lift metre-distance programs by at least 5, on held-out K1 rooms?

## Answer
No deployable candidate clears either bar. On held-out K1 room rows the best pre-registered challenger, S4+G1 with the train-fitted area factor (R2), scores 63.3 [48.8, 77.4], level with f17's direct 63.40 and 10.1 below the 73.4 bar. The best diagnostic arm, the camera-height rule S2+G1+R2, scores 67.1 [53.3, 80.4], also below the bar, and it was the best of many arms. Only a per-capture GT scale (SO, not deployable) reaches the bar: 75.0 to 76.7 with R2, 73.8 to 76.2 with R0. The floor-band rule R1 halves room scores on every geometry, so floor rules other than a multiplier are rejected.

On metre distance with GT masks, the deployable scale rule S4+G1 scores 62.9 [56.1, 68.9] against 66.0 [60.1, 71.8] for the GT-scale oracle and 77.9 [71.4, 85.5] for GT geometry. A perfect scale therefore buys at most about 3 task points over S4, and the remaining 12-point gap to GT geometry is depth shape and pose error that no scale or floor rule removes. Whether S4 beats the deployed own-depth scale cannot be read until phase own lands. dev-S1's deployed G3T with GT masks scored 66.1, the oracle level here, so the +5 distance bar is very unlikely to be met by a scale rule.

Room size should not route on any of these candidates. The geometry-fusion leg should target depth and pose quality on distance and per-capture metric scale on room: room needs scale within a few percent, because area grows with the square of scale.

## Evidence (held-out K1 rooms; MRA x100; 95% room-bootstrap; paired vs the interim reference S1+G1)
| Arm | Distance, 216 rows / 48 rooms (GT masks) | Room, 24 rows / 23 rooms (mask-free), R0 | Room, R2 |
|---|---|---|---|
| GT geometry | 77.9 [71.4, 85.5] | 100.0 (labels are this rule on GT; see caveats) | n/a |
| SO+GO (GT scale, GT gravity; ceiling of scale) | 66.0 [60.1, 71.8] | 76.2 [62.6, 88.7] | 76.7 [63.3, 88.7] |
| SO+G1 | 65.6 [60.2, 71.0] | 73.8 [60.8, 85.7] | 75.0 [62.3, 86.5] |
| S4+G1 (primary) | 62.9 [56.1, 68.9]; +20.0 [+12.6, +29.1] | 56.2 [42.9, 69.6]; +24.6 [+11.2, +38.8] | 63.3 [48.8, 77.4]; +30.0 [+17.1, +43.6] |
| S2+G1 (camera height) | 60.7 [54.0, 66.8] | 61.7 [48.3, 74.8] | 67.1 [53.3, 80.4] |
| S3+G1 (floor to ceiling) | 60.5 [51.5, 68.4] | 37.5 [22.7, 53.0] | 43.3 [28.7, 58.3] |
| S1+G1 (one constant, 2.587) | 42.9 [33.7, 51.0] | 31.7 [17.0, 47.8] | 33.3 [20.4, 47.4] |
| R1 floor band on S4+G1 / GT / SO+GO | | 16.2 / 50.0 / 32.5 | |
- C-rule (vs S1+G1): distance S4+G1 passes (train +17.0 [+13.1, +21.0], held-out +20.0); room S4+G1+R0 passes (train +29.4 [+21.7, +36.7], held-out +24.6); S4+G1+R2 passes (train +26.9 [+19.4, +34.6], held-out +30.0); S4+G1+R1 fails (train +2.5 [-1.7, +7.2]). Passing it against a one-constant scale shows only that S1 is weak; it says nothing about the deployed scale.
- Scale accuracy (held-out, 53 captures with geometry): s/SO within [0.8, 1.2] for 94% (S2, S4), 75% (S3), 40% (S1). G1 gravity is 5.3 degrees from GT gravity at the median (90th percentile 13.4).
- Fits (train only, 225 captures): S1 = 2.587; h_prior = 1.533 m; H_prior = 2.767 m; S4: log s = 0.514 - 0.858 log h - 0.067 log span; R2 k = 0.927 (S4+G1), 0.936 (S2+G1), 0.973 (SO+G1).
- Train split (1,037 distance rows / 192 rooms; 110 room rows / 102 rooms): GT 82.3 and 100.0; SO+G1 70.6 and 76.9; S4+G1 67.4 and 56.3 (R2 58.5); S1+G1 50.4 and 26.9.
- dev-S1 room, 36 ScanNet items / 9 rooms, K1-fitted rules on dev-S1 raw G3T caches (/scratch/jjyeung/devs1_r2/g3s*/g3t), asked units: S2+G1 46.1 [26.1, 65.2], S4+G1 45.0 [25.2, 64.2], with R2 45.6 and 43.9, S1+G1 31.7; G3T's own gravity output gives the same level. All far below the bar, and below the deployed G3T's 55.0 there.
