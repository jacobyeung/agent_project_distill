# T1 grounding funnel

stages: First failing stage; IoU >0.5; at least half of nonempty selected masks match; count only matched support; full OBB outside distance >0.25m fails.

objects: 300 requested question-operand occurrences, including the two uncalled operands; no-GT includes missing capture or missing unique instance binding.

item: Earliest known failure dominates no-GT. A censored operand blocks only failures that might occur later than its earliest unresolved stage. With no known failure, any no-GT operand makes no-GT.

cameras: NPZ self-consistent on 38/38; S4/S5 only on the six captures passing rank>=2, translation RMS<=0.10m and every rotation<=5deg. No scale fit.

portrait: Unchanged adapter leaves nine portrait raster-to-reader mappings unresolved; these are censored, not no-GT, when uniquely bound.

dense: Only 32 anchor frames have GT. Full 64-frame stages are resolved only when every possible labeling of extra masks gives the same first failure. Additional anchor-only matrices are diagnostics, not full dense stages.

extent: ARKit full lengths; ScanNet++ doubled half lengths; both ScanNet interpretations retained; disagreement censors placement.

scores: Routed distance official MRA, 0–100, released label authority, printed metres converted to requested units; missing gaps score zero.

budget: Signed (n_stage/N)*(mean_S5-mean_stage), recomputed per room draw. N=150. Undefined without an S5 item group.

bootstrap: 10,000 draws of all 46 physical rooms; random.Random(20261120); item weighted; same draws in every table; undefined draws counted and omitted.


## t1

| Stage | Objects | Items | Item score [95% CI] | Signed budget [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | 1 | 1 | 90.00 [90.00, 90.00] | undefined |
| S1 | 27 | 24 | 65.83 [50.00, 81.67] | undefined |
| S2 | 27 | 20 | 61.00 [32.73, 83.43] | undefined |
| S3 | 29 | 10 | 68.00 [50.00, 89.00] | undefined |
| S4 | 0 | 0 | undefined | undefined |
| S5 | 5 | 0 | undefined | undefined |
| no-GT | 158 | 78 | 50.26 [39.07, 62.02] | undefined |
| censored | 53 | 17 | 76.47 [66.00, 87.27] | undefined |


## points

| Stage | Objects | Items | Item score [95% CI] | Signed budget [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | 1 | 1 | 0.00 [0.00, 0.00] | undefined |
| S1 | 9 | 9 | 41.11 [12.00, 70.00] | undefined |
| S2 | 36 | 28 | 63.21 [37.06, 78.24] | undefined |
| S3 | 17 | 10 | 81.00 [70.00, 90.00] | undefined |
| S4 | 0 | 0 | undefined | undefined |
| S5 | 5 | 0 | undefined | undefined |
| no-GT | 158 | 81 | 61.73 [54.88, 69.86] | undefined |
| censored | 74 | 21 | 75.24 [58.89, 88.89] | undefined |


## dense64

| Stage | Objects | Items | Item score [95% CI] | Signed budget [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | 0 | 0 | undefined | undefined |
| S1 | 12 | 9 | 61.11 [50.00, 86.67] | undefined |
| S2 | 12 | 9 | 47.78 [26.86, 83.33] | undefined |
| S3 | 20 | 6 | 56.67 [10.00, 100.00] | undefined |
| S4 | 0 | 0 | undefined | undefined |
| S5 | 2 | 0 | undefined | undefined |
| no-GT | 158 | 82 | 49.15 [41.42, 60.60] | undefined |
| censored | 96 | 44 | 71.36 [60.49, 80.63] | undefined |


## Stage migration and score changes


### T1 → points, objects

| T1 / destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S1 | 0 | 9 | 10 | 2 | 0 | 0 | 0 | 6 |
| S2 | 0 | 0 | 20 | 4 | 0 | 0 | 0 | 3 |
| S3 | 0 | 0 | 5 | 11 | 0 | 0 | 0 | 13 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 158 | 0 |
| censored | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 52 |

| T1 | Destination | Count | Distinct items | Arm − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | S0 | 1 | 1 | -90.00 [-90.00, -90.00] |
| S1 | S1 | 9 | 9 | -32.22 [-63.33, 0.00] |
| S1 | S2 | 10 | 10 | 3.00 [-40.00, 30.00] |
| S1 | S3 | 2 | 2 | 45.00 [45.00, 45.00] |
| S1 | censored | 6 | 6 | 23.33 [0.00, 60.00] |
| S2 | S2 | 20 | 15 | -3.33 [-17.00, 22.22] |
| S2 | S3 | 4 | 4 | 17.50 [0.00, 23.33] |
| S2 | censored | 3 | 3 | -10.00 [-20.00, 10.00] |
| S3 | S2 | 5 | 5 | 2.00 [0.00, 6.67] |
| S3 | S3 | 11 | 11 | 13.64 [0.00, 22.50] |
| S3 | censored | 13 | 13 | 10.00 [-18.00, 31.43] |
| S5 | S5 | 5 | 5 | -2.00 [-10.00, 0.00] |
| no-GT | no-GT | 158 | 84 | 11.31 [-1.62, 23.95] |
| censored | S2 | 1 | 1 | -70.00 [-70.00, -70.00] |
| censored | censored | 52 | 36 | -9.44 [-20.71, 1.22] |


### T1 → points, items

| T1 / destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S1 | 0 | 9 | 9 | 2 | 0 | 0 | 1 | 3 |
| S2 | 0 | 0 | 15 | 3 | 0 | 0 | 1 | 1 |
| S3 | 0 | 0 | 3 | 5 | 0 | 0 | 1 | 1 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 78 | 0 |
| censored | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 16 |

| T1 | Destination | Count | Distinct items | Arm − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | S0 | 1 | 1 | -90.00 [-90.00, -90.00] |
| S1 | S1 | 9 | 9 | -32.22 [-63.33, 0.00] |
| S1 | S2 | 9 | 9 | 3.33 [-48.00, 30.00] |
| S1 | S3 | 2 | 2 | 45.00 [45.00, 45.00] |
| S1 | no-GT | 1 | 1 | 80.00 [80.00, 80.00] |
| S1 | censored | 3 | 3 | 26.67 [0.00, 60.00] |
| S2 | S2 | 15 | 15 | -3.33 [-17.00, 22.22] |
| S2 | S3 | 3 | 3 | 6.67 [0.00, 10.00] |
| S2 | no-GT | 1 | 1 | 40.00 [40.00, 40.00] |
| S2 | censored | 1 | 1 | 10.00 [10.00, 10.00] |
| S3 | S2 | 3 | 3 | 3.33 [0.00, 10.00] |
| S3 | S3 | 5 | 5 | 8.00 [0.00, 20.00] |
| S3 | no-GT | 1 | 1 | 0.00 [0.00, 0.00] |
| S3 | censored | 1 | 1 | 0.00 [0.00, 0.00] |
| no-GT | no-GT | 78 | 78 | 11.03 [-2.90, 24.69] |
| censored | S2 | 1 | 1 | -70.00 [-70.00, -70.00] |
| censored | censored | 16 | 16 | -1.25 [-14.44, 10.59] |


### T1 → dense64, objects

| T1 / destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| S1 | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 15 |
| S2 | 0 | 0 | 12 | 1 | 0 | 0 | 0 | 14 |
| S3 | 0 | 0 | 0 | 19 | 0 | 0 | 0 | 10 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 3 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 158 | 0 |
| censored | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 53 |

| T1 | Destination | Count | Distinct items | Arm − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | censored | 1 | 1 | 0.00 [0.00, 0.00] |
| S1 | S1 | 12 | 11 | 0.00 [0.00, 0.00] |
| S1 | censored | 15 | 15 | 8.00 [-5.00, 30.00] |
| S2 | S2 | 12 | 10 | 5.00 [0.00, 16.67] |
| S2 | S3 | 1 | 1 | -30.00 [-30.00, -30.00] |
| S2 | censored | 14 | 11 | -12.73 [-17.50, 0.00] |
| S3 | S3 | 19 | 16 | 0.62 [0.00, 2.73] |
| S3 | censored | 10 | 10 | 7.00 [-6.67, 40.00] |
| S5 | S5 | 2 | 2 | 0.00 [0.00, 0.00] |
| S5 | censored | 3 | 3 | 0.00 [0.00, 0.00] |
| no-GT | no-GT | 158 | 84 | -2.26 [-10.47, 5.24] |
| censored | censored | 53 | 36 | -4.44 [-10.26, 1.05] |


### T1 → dense64, items

| T1 / destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| S1 | 0 | 9 | 0 | 0 | 0 | 0 | 1 | 14 |
| S2 | 0 | 0 | 9 | 0 | 0 | 0 | 2 | 9 |
| S3 | 0 | 0 | 0 | 6 | 0 | 0 | 1 | 3 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 78 | 0 |
| censored | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 17 |

| T1 | Destination | Count | Distinct items | Arm − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | censored | 1 | 1 | 0.00 [0.00, 0.00] |
| S1 | S1 | 9 | 9 | 0.00 [0.00, 0.00] |
| S1 | no-GT | 1 | 1 | 0.00 [0.00, 0.00] |
| S1 | censored | 14 | 14 | 8.57 [-5.45, 30.00] |
| S2 | S2 | 9 | 9 | 4.44 [0.00, 20.00] |
| S2 | no-GT | 2 | 2 | -15.00 [-20.00, -10.00] |
| S2 | censored | 9 | 9 | -12.22 [-18.18, 0.00] |
| S3 | S3 | 6 | 6 | 0.00 [0.00, 0.00] |
| S3 | no-GT | 1 | 1 | 10.00 [10.00, 10.00] |
| S3 | censored | 3 | 3 | -6.67 [-20.00, 0.00] |
| no-GT | no-GT | 78 | 78 | -2.69 [-11.48, 5.42] |
| censored | censored | 17 | 17 | -5.88 [-16.88, 0.00] |


## Dense anchor-only diagnostic
These matrices ignore unannotated added masks; they cannot establish full 64-frame stage recovery.

objects
| T1 / anchor destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S1 | 0 | 27 | 0 | 0 | 0 | 0 | 0 | 0 |
| S2 | 0 | 0 | 25 | 1 | 0 | 1 | 0 | 0 |
| S3 | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 2 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 158 | 0 |
| censored | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 52 |

| T1 | Anchor destination | Count | Distinct items | Dense − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | S0 | 1 | 1 | 0.00 [0.00, 0.00] |
| S1 | S1 | 27 | 25 | 4.80 [-2.78, 18.00] |
| S2 | S2 | 25 | 21 | -4.29 [-10.00, 0.00] |
| S2 | S3 | 1 | 1 | -30.00 [-30.00, -30.00] |
| S2 | S5 | 1 | 1 | 0.00 [0.00, 0.00] |
| S3 | S3 | 27 | 23 | 3.04 [-3.12, 14.74] |
| S3 | censored | 2 | 2 | 5.00 [5.00, 5.00] |
| S5 | S5 | 5 | 5 | 0.00 [0.00, 0.00] |
| no-GT | no-GT | 158 | 84 | -2.26 [-10.47, 5.24] |
| censored | S2 | 1 | 1 | -70.00 [-70.00, -70.00] |
| censored | censored | 52 | 36 | -4.44 [-10.26, 1.05] |

items
| T1 / anchor destination | S0 | S1 | S2 | S3 | S4 | S5 | no-GT | censored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S1 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | 0 |
| S2 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0 |
| S3 | 0 | 0 | 0 | 9 | 0 | 0 | 1 | 0 |
| S4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no-GT | 0 | 0 | 0 | 0 | 0 | 0 | 78 | 0 |
| censored | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 16 |

| T1 | Anchor destination | Count | Distinct items | Dense − T1 score [95% CI] |
| --- | --- | --- | --- | --- |
| S0 | S0 | 1 | 1 | 0.00 [0.00, 0.00] |
| S1 | S1 | 24 | 24 | 5.00 [-2.86, 18.18] |
| S2 | S2 | 20 | 20 | -5.00 [-10.59, 0.00] |
| S3 | S3 | 9 | 9 | -2.22 [-8.57, 0.00] |
| S3 | no-GT | 1 | 1 | 10.00 [10.00, 10.00] |
| no-GT | no-GT | 78 | 78 | -2.69 [-11.48, 5.42] |
| censored | S2 | 1 | 1 | -70.00 [-70.00, -70.00] |
| censored | censored | 16 | 16 | -1.88 [-5.71, 0.00] |


## Which stages each lever passes
Advancement includes censoring strictly after the starting stage. Unresolved dense identity is not counted as recovery.

| Unit | T1 stage | Count | Point passes stage | Dense passes stage | Neither proven | Same stage in both | Point score Δ | Dense score Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| objects | S0 | 1 | 0 | 0 | 1 | 0 | -90.00 [-90.00, -90.00] | 0.00 [0.00, 0.00] |
| objects | S1 | 27 | 18 | 0 | 9 | 3 | -4.00 [-33.48, 15.62] | 4.80 [-2.78, 18.00] |
| objects | S2 | 27 | 7 | 1 | 19 | 5 | -2.86 [-16.00, 16.25] | -4.29 [-10.00, 0.00] |
| objects | S3 | 29 | 13 | 0 | 16 | 8 | 7.20 [-6.84, 17.41] | 3.20 [-2.61, 13.75] |
| items | S0 | 1 | 0 | 0 | 1 | 0 | -90.00 [-90.00, -90.00] | 0.00 [0.00, 0.00] |
| items | S1 | 24 | 14 | 0 | 10 | 3 | -0.42 [-33.33, 20.71] | 5.00 [-2.86, 18.18] |
| items | S2 | 20 | 4 | 0 | 16 | 4 | 1.00 [-9.00, 16.67] | -5.00 [-10.59, 0.00] |
| items | S3 | 10 | 1 | 0 | 9 | 3 | 5.00 [0.00, 11.11] | -1.00 [-6.67, 3.33] |
