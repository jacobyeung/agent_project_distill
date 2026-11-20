# DEV-POSE

raw: 1. Parity: STOP; same signed / label-free / audit terms 10.00 / 0.00 / 27.43; L2 within 10% on 98.48%.
raw: 2. Pose binds on dev: NOT EVALUATED (parity stop).
raw: 3. Pose costs no distance: NOT EVALUATED (parity stop).
raw: 4. Reopen dense ARKit tower work: NOT EVALUATED (parity stop).
rescaled: 1. Parity: STOP; same signed / label-free / audit terms 10.00 / 0.00 / 27.57; L2 within 10% on 98.48%.
rescaled: 2. Pose binds on dev: NOT EVALUATED (parity stop).
rescaled: 3. Pose costs no distance: NOT EVALUATED (parity stop).
rescaled: 4. Reopen dense ARKit tower work: NOT EVALUATED (parity stop).

Ladder: 66/150 items, 37/38 captures; all-pairs audit covers 38 captures. Exclusions: {'missing GT capture': 74, 'missing unique binding': 10}.
Actual transport anchors: 1 same, 65 different (98.48%); 17 operand fallbacks. Printed-anchor census: {'different': 139, 'unknown': 8, 'same': 3}.
Expected 72 items: 66 bind both operands; 74 lack a GT capture and 10 bind only one operand. The funnel count of 72 includes six known-failure items with a missing binding. One all-zero-mask operand remains in the binding-only ladder. The ladder has 29 rooms; the audit has 30.
Audit: 1381 eligible instances, 43657 unordered pairs (2004 same / 41653 different).

| Mode | Dataset | Anchors | n | L0 | L1 | L2 | L2−L1 [95% CI] | Label-free loss [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw | all | all | 66 | 68.33 | 83.79 | 97.42 | 13.64 [7.50, 20.97] | 14.09 [7.05, 22.33] |
| raw | all | same | 1 | 0.00 | 80.00 | 90.00 | 10.00 [10.00, 10.00] | 0.00 [0.00, 0.00] |
| raw | all | different | 65 | 69.38 | 83.85 | 97.54 | 13.69 [7.47, 21.13] | 14.31 [7.16, 22.65] |
| raw | ARKit | all | 33 | 61.52 | 76.97 | 98.79 | 21.82 [11.79, 31.18] | 21.82 [10.77, 32.00] |
| raw | ARKit | same | 0 | undefined | undefined | undefined | undefined | undefined |
| raw | ARKit | different | 33 | 61.52 | 76.97 | 98.79 | 21.82 [11.79, 31.18] | 21.82 [10.77, 32.00] |
| raw | ScanNet/ScanNet++ | all | 33 | 75.15 | 90.61 | 96.06 | 5.45 [2.65, 10.00] | 6.36 [2.11, 16.19] |
| raw | ScanNet/ScanNet++ | same | 1 | 0.00 | 80.00 | 90.00 | 10.00 [10.00, 10.00] | 0.00 [0.00, 0.00] |
| raw | ScanNet/ScanNet++ | different | 32 | 77.50 | 90.94 | 96.25 | 5.31 [2.65, 10.00] | 6.56 [2.11, 16.67] |
| rescaled | all | all | 66 | 68.33 | 84.55 | 97.42 | 12.88 [6.18, 20.60] | 13.79 [7.17, 21.49] |
| rescaled | all | same | 1 | 0.00 | 80.00 | 90.00 | 10.00 [10.00, 10.00] | 0.00 [0.00, 0.00] |
| rescaled | all | different | 65 | 69.38 | 84.62 | 97.54 | 12.92 [6.11, 20.75] | 14.00 [7.31, 21.73] |
| rescaled | ARKit | all | 33 | 61.52 | 77.27 | 98.79 | 21.52 [10.59, 31.85] | 20.61 [9.62, 31.00] |
| rescaled | ARKit | same | 0 | undefined | undefined | undefined | undefined | undefined |
| rescaled | ARKit | different | 33 | 61.52 | 77.27 | 98.79 | 21.52 [10.59, 31.85] | 20.61 [9.62, 31.00] |
| rescaled | ScanNet/ScanNet++ | all | 33 | 75.15 | 91.82 | 96.06 | 4.24 [0.75, 9.57] | 6.97 [2.73, 16.50] |
| rescaled | ScanNet/ScanNet++ | same | 1 | 0.00 | 80.00 | 90.00 | 10.00 [10.00, 10.00] | 0.00 [0.00, 0.00] |
| rescaled | ScanNet/ScanNet++ | different | 32 | 77.50 | 92.19 | 96.25 | 4.06 [0.68, 9.55] | 7.19 [2.86, 16.96] |

| Mode | Dataset | Audit n: same / different | Same loss [95% CI] | Different loss [95% CI] | Weighted loss [95% CI] |
| --- | --- | --- | --- | --- | --- |
| raw | all | 2004 / 41653 | 27.43 [23.82, 33.44] | 14.96 [12.97, 18.05] | 15.14 [13.05, 18.36] |
| raw | ARKit | 129 / 2617 | 51.47 [41.52, 60.43] | 23.37 [15.46, 34.20] | 23.37 [15.46, 34.20] |
| raw | ScanNet/ScanNet++ | 1875 / 39036 | 25.77 [22.35, 31.05] | 14.39 [12.38, 17.39] | 14.74 [12.51, 18.07] |
| rescaled | all | 2004 / 41653 | 27.57 [23.93, 33.59] | 13.99 [11.26, 17.98] | 14.20 [11.39, 18.30] |
| rescaled | ARKit | 129 / 2617 | 51.47 [41.52, 60.43] | 20.98 [13.78, 31.16] | 20.98 [13.78, 31.16] |
| rescaled | ScanNet/ScanNet++ | 1875 / 39036 | 25.93 [22.47, 31.18] | 13.52 [10.72, 17.62] | 13.90 [10.93, 18.16] |

Scores are routed-distance MRA ×100. L1/L2 use unrounded reader gaps; JSON also records gaps rounded to 0.01 m and their score sensitivity.
The imported reader gap function uses cached reader grids/trees and a witnessed exact search bound. Every sampled grid point participates; no approximate nearest-neighbour tolerance is used.
Transport uses GT metric camera coordinates and served metric c2w. The saved scale is already in translations; it is not applied again to metric GT points. Rescaled changes only served translations by the fitted similarity factor.
Both worlds use z-up and the reader min-area refit of all eight corners. GT axes are rows. ARKit uses full lengths; ScanNet++ doubles stored half lengths. ScanNet uses stored full lengths, with doubled-length sensitivity in JSON.
The 154-pixel rule is ceil(154 × raster area / 76800); both supplied raster orientations give 154. Largest-anchor ties choose the first anchor, including one all-zero-mask operand. Missing/invisible printed anchors use this flagged fallback.
All intervals use 10,000 paired draws of the 46 manifest rooms, seed 20261120: ladder items, audit pairs, or side-ratio object occurrences receive equal weight. Weighted audit re-estimates the within-dataset ladder same-anchor share in each draw. Undefined draws are counted and omitted in JSON.
Rule 2 compares signed ladder pose losses (different minus same); rule 4 uses the ARKit weighted audit loss. JSON also reports the audit contrast. The parity stop gates every interpretation.

| T1 stage | Side pairs | Printed longest / GT longest, mean [95% CI] | Linked tracks / visible same-name GT instances (matched occurrences) |
| --- | --- | --- | --- |
| S0 | 1 | 0.49 [0.49, 0.49] | 6 / 0 (1) |
| S1 | 27 | 0.68 [0.47, 0.93] | 141 / 27 (27) |
| S2 | 27 | 0.92 [0.67, 1.14] | 224 / 27 (27) |
| S3 | 29 | 0.74 [0.64, 0.82] | 174 / 29 (29) |
| S4 | 0 | undefined | 0 / 0 (0) |
| S5 | 5 | 0.78 [0.60, 1.00] | 95 / 5 (5) |
| censored | 53 | 0.84 [0.75, 0.94] | 334 / 53 (53) |
| no-GT | 0 | undefined | 38 / 0 (10) |

Validation: 142 real printed gaps match exactly after reader rounding; CPU synthetic tests are in test_devpose.py. Full-run seconds: 532.9.
Limits: gravity-aligned refitting is not invariant to a shared tilted rotation; same-anchor loss can therefore be nonzero without relative-pose error. Sampled-grid gaps also have discretization effects.
Limits: the sole same-anchor ladder control comes from a fallback; all three printed same-anchor items lack two GT bindings. Its bootstrap interval is degenerate when defined. Tiny L2 gaps can amplify label-free MRA loss.
Limits: ScanNet extent ambiguity and GT-box/label mismatch can fail parity. NPZ anchors match recorded source indices, but do not independently authenticate native RGB/pose identity. No causal interpretation is made after STOP.
Track diagnostics compare per-name linked/candidate counts with same-name visible GT instances; they are query-conditional counts, not capture-wide recall. Every object, pair, fit, cell, interval and input SHA256 is in DEVPOSE.json.
Rerun in a fresh folder with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B devpose.py --out out_rerun`; run tests with the same interpreter flags and `test_devpose.py`.
