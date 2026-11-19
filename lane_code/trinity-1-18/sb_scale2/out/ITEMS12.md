# K1 training scale bias and depth consistency

The two swapped test halves measure calibration at step 544. Step-400 predictions remain MISSING. Dataset-specific calibration must beat global calibration in both halves and combined before it is preferred.

The population contains 239 captures, 219 rooms and 117,551 displacement pairs. Three unavailable GT archives are listed in the JSON. No held-out payload or item was evaluated.

MRA uses ten strict relative-error thresholds and averages within room, then across rooms. Intervals resample rooms 10,000 times with seed 17. Factors are fixed during bootstrap. Ratio distributions are descriptive: pooled item median and p10/p50/p90 across capture medians. Distance refusals score zero and do not enter ratio summaries.

## Displacement

| Dataset | A MRA [95% CI] | Pooled predicted/GT | Capture medians p10 / p50 / p90 | Items / rooms |
|---|---:|---:|---:|---:|
| all | 83.800 [82.183, 85.343] | 1.0110 | 0.9255 / 1.0087 / 1.0941 | 117551 / 219 |
| arkitscenes | 81.537 [79.430, 83.471] | 1.0018 | 0.9167 / 0.9943 / 1.1057 | 62594 / 115 |
| scannet | 84.926 [81.538, 87.738] | 1.0372 | 0.9628 / 1.0414 / 1.0839 | 19896 / 33 |
| scannetpp | 86.941 [83.684, 89.750] | 1.0074 | 0.9391 / 1.0068 / 1.0639 | 35061 / 71 |

| Contrast | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] | Decision |
|---|---:|---:|---:|---|
| G-A | +0.114 [+0.049, +0.179] | +0.193 [+0.075, +0.314] | +0.153 [+0.087, +0.222] | SUPPORTED |
| D-A | -0.122 [-0.466, +0.225] | +0.135 [-0.063, +0.341] | +0.006 [-0.193, +0.214] | INCONCLUSIVE |
| D-G | -0.235 [-0.578, +0.106] | -0.058 [-0.222, +0.105] | -0.147 [-0.337, +0.047] | INCONCLUSIVE |

## Distance

| Dataset | A MRA [95% CI] | Pooled predicted/GT | Capture medians p10 / p50 / p90 | Items / rooms |
|---|---:|---:|---:|---:|
| all | 68.295 [64.396, 71.964] | 0.9351 | 0.7882 / 0.9511 / 1.1821 | 1037 / 192 |
| arkitscenes | 64.403 [58.896, 69.748] | 0.9739 | 0.7777 / 0.9918 / 1.2073 | 344 / 115 |
| scannet | 74.477 [64.949, 83.179] | 1.0438 | 0.8974 / 1.0437 / 1.2743 | 72 / 17 |
| scannetpp | 74.001 [68.898, 78.473] | 0.9184 | 0.7916 / 0.9136 / 0.9885 | 621 / 60 |

| Contrast | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] | Decision |
|---|---:|---:|---:|---|
| G-A | +0.016 [-0.458, +0.482] | +0.298 [-0.295, +0.933] | +0.158 [-0.230, +0.552] | INCONCLUSIVE |
| D-A | +0.295 [-0.383, +0.953] | +0.718 [+0.122, +1.357] | +0.509 [+0.041, +0.957] | INCONCLUSIVE |
| D-G | +0.279 [-0.315, +0.820] | +0.420 [-0.071, +0.953] | +0.350 [-0.041, +0.731] | INCONCLUSIVE |

G is global calibration; D is calibration per dataset. Both are fit to displacement in fit-half rooms only. The exact same factor scales G3T depth and translations for distance; E3 relifts the GT masks for every arm, retaining its bestspread-style box grid, 5 cm gap grid and two-decimal output. Distance is a GT-mask geometry diagnostic, not an end-to-end grounding score.

| Fit half | Global c | ARKitScenes c | ScanNet c | ScanNet++ c |
|---|---:|---:|---:|---:|
| fold1 | 0.996786 | 0.996077 | 0.951757 | 1.018642 |
| fold2 | 0.994333 | 0.988925 | 0.990638 | 1.006222 |

## Depth versus metric poses

Depth comparisons sample the same 51×51 grid using E3 floor-and-clip coordinates. The matched mask requires finite GT and own depth in (0.1,10) m, positive G3T depth, valid GT frames, and G3T confidence above the clip median. GT-depth-implied scale uses the frozen GT-depth mask without the own-depth restriction. Pose scale fits all eligible pose lengths by zero-intercept least squares.

| Dataset | Own/GT pooled; capture p10/p50/p90 | Pose-scaled G3T/GT pooled; capture p10/p50/p90 | Depth-scale/pose-scale capture p10/p50/p90 |
|---|---:|---:|---:|
| all | 1.0164; 0.9526 / 1.0129 / 1.1013 | 1.0077; 0.9668 / 1.0084 / 1.0742 | 0.9310 / 0.9917 / 1.0344 |
| arkitscenes | 1.0276; 0.9464 / 1.0230 / 1.1299 | 1.0229; 0.9897 / 1.0218 / 1.0967 | 0.9118 / 0.9786 / 1.0104 |
| scannet | 1.0009; 0.9703 / 0.9987 / 1.0282 | 0.9661; 0.9040 / 0.9718 / 1.0052 | 0.9949 / 1.0290 / 1.1061 |
| scannetpp | 1.0145; 0.9692 / 1.0172 / 1.0662 | 1.0073; 0.9862 / 1.0059 / 1.0329 | 0.9681 / 0.9941 / 1.0139 |

Depth/pose scale mismatch can reflect G3T shape or intrinsics as well as GT labels; it alone cannot identify a biased training source.

## Pose-stream sources

The bounded filename search found receipts and identifier-only scene lists. Neither receipt states a real dataset-name mapping. No local target depths, corresponding G3T depth, or metric pose-length labels were found in these copies. All four comparisons and source-removal prices are MISSING.

| Source | Receipt depth rows | Missing target database | Dataset mapping |
|---|---:|---|---|
| a2v3 d1 | 20080 | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/rows.sqlite` | MISSING |
| a2v3 d2 | 7524 | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/rows.sqlite` | MISSING |
| a3v2 d1 | 91280 | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a3v2/rows.sqlite` | MISSING |
| a3v2 d3 | 112240 | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a3v2/rows.sqlite` | MISSING |

The exact searched names were `*8957d119*`, `*a2v3*`, and `*a3v2*` under `/scratch/jjyeung` to depth 6. `SOURCE_SEARCH.txt` records all matches. Scene lists have only dataset code, row index, question identifier, scene, and optionally recording identifier. Counts do not supply metric targets.

## Commands and provenance

All scored numbers and intervals in this report come from:

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/scale_drift.py score
```

The source search command is:

```sh
find /scratch/jjyeung -maxdepth 6 \( -name '*8957d119*' -o -name '*a2v3*' -o -name '*a3v2*' \) -print > out/SOURCE_SEARCH.txt
```

Each JSON pins its input files by SHA-256. BARS_FROZEN.json copies sb_scale1 folds exactly and freezes metrics, fitting and decisions before scoring. Existing score files cause a refusal. No code, data or outputs outside this workspace were changed.
