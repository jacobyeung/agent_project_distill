# K1 training camera-displacement scale analysis

One fixed factor gives step 544 a small improvement: **+0.153 MRA points [+0.087, +0.222]** across the two test folds. The fitted factors are 0.996786 and 0.994333. Both folds meet the frozen improvement rule. This is evidence about K1 training rooms; it does not establish performance on any held-out split.

**Q2 is MISSING.** Step-400 K1 own-depth predictions were not found. B, D, B−A, and D−B cannot be estimated. The step-400 export manifest verifies artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`, step 400, run `6ed2c7aa`.

| Arm | Fold 1 MRA [95% CI] | Fold 2 MRA [95% CI] | Combined MRA [95% CI] | Combined median served/GT |
|---|---:|---:|---:|---:|
| A: step 544 scale | 83.098 [81.138, 84.933] | 84.509 [81.790, 86.838] | 83.800 [82.183, 85.343] | 1.010964 |
| B: step 400 scale | MISSING | MISSING | MISSING | MISSING |
| C: calibrated A | 83.211 [81.262, 85.034] | 84.701 [81.992, 87.029] | 83.953 [82.336, 85.497] | 1.006438 |
| D: calibrated B | MISSING | MISSING | MISSING | MISSING |
| E: GT per-capture scale | 87.035 [85.224, 88.726] | 88.588 [86.189, 90.612] | 87.808 [86.321, 89.187] | 0.999379 |
| F: global raw-G3T scale | 46.018 [40.207, 51.769] | 46.272 [40.615, 51.786] | 46.144 [42.094, 50.127] | 1.012308 |

| Contrast | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] |
|---|---:|---:|---:|
| B-A | MISSING | MISSING | MISSING |
| C-A | +0.114 [+0.049, +0.179] | +0.193 [+0.075, +0.314] | +0.153 [+0.087, +0.222] |
| D-B | MISSING | MISSING | MISSING |

| Quantity | Fold 1 | Fold 2 |
|---|---:|---:|
| Fit factor C | 0.996786 | 0.994333 |
| Fit factor F | 2.680037 | 2.743450 |
| Median served/GT A | 1.011215 | 1.010756 |
| Median served/GT C | 1.007965 | 1.005028 |
| Median served/GT E | 0.998502 | 1.000096 |
| Median served/GT F | 0.975708 | 1.051209 |

The existing per-capture scale is close to calibrated: its combined pair-median served/GT ratio is 1.010964. Removing own depth and fitting one global raw-G3T scale gives 46.144 MRA. The GT per-capture diagnostic reaches 87.808; it uses test GT and is not deployable. Its least-squares objective does not guarantee the maximum possible MRA.

## Population and frozen method

The manifest contains 242 K1 training captures in 221 rooms. Local GT is available for **239 captures in 219 rooms**, yielding **117,551 eligible pairs**. The frozen halves have 110 and 111 rooms; the scored test halves have 110 and 109 rooms after missing-GT exclusions. Each room appears in exactly one test fold. No held-out capture payload, R0-dev, dev-S1 item, BENCH item, or withheld item row was scored or opened as an evaluation input. The combined split manifest was parsed to select training captures and verify their existing capture digests; its item rows were not used.

The item rule is the prompt's all-pairs rule: all i<j among the 32 anchors with both GT poses valid and GT displacement at least 0.1 m. This is not the dev-S1 item generator. G3T camera encodings are decoded to camera centres before distances are computed. MRA averages ten strict tests `abs(pred−GT)/GT < 1−theta`, theta=0.50,…,0.95. Pair scores are pooled within each room, then rooms receive equal weight. Ratios in the table are pooled pair medians; the JSON also records the median of per-room medians.

C and F minimize room-balanced squared log error on the opposite half: `c=exp(mean_room(mean_pair(log(GT/pred))))`. E fits a separate zero-intercept distance least-squares scale per capture. Intervals use 10,000 room bootstrap draws, seed 17, with paired draws for C−A. They condition on the fitted coefficients and do not include coefficient-refitting uncertainty. The combined estimate pools out-of-fold room scores. The decision requires a strictly positive paired lower bound in both folds and combined; it does not impose a minimum practical gain.

`out/BARS_FROZEN.json` contains the room lists, complete metric, decision rule, missing-input policy, and code SHA-256. It was written before displacement scoring. Both freezing and scoring refuse when score files exist.

## Input identity and missing data

The 242 training `own.npz` files under `/scratch/jjyeung/k1/own_170235/native/probe` have per-capture receipts tied to the step-544 artifact manifest (SHA-256 `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`). That manifest explicitly records step 544 and private-ViT depth backing. Every scored depth, tower, and GT file was hash-verified.

The additional `own7/canary/native/probe` set has two training captures and the same step-544 identity. The `own7/ad2472b1be07d4193.result.tar.gz` and `own7/canary/c75955208369b4e48.result.tar.gz` archives have 242 and 2 training receipts respectively; all inspected training receipts bind to step 544. Archive and member hashes are in `NEEDS_INPUTS.json`. `run_convert_1` and `run_convert_2` receipts also bind to step 544; they are derived geometry, not independent own-depth checkpoints. The report recomputes scale from raw own-depth grids. Detailed set counts and receipt hashes are in the bars file. The bounded searches found no step-400 K1 depth set or local step-400 weight bundle.

The rule JSON and estimator were read from `/scratch/jjyeung/orch_n30/sb_records/work/policy_tree/student_pilot/`. The exact implementation takes the clip-wide median of finite confidence and keeps only confidence strictly above it, finite positive G3T depth, and finite own depth strictly between 0.1 and 10 m. It then takes the median own/G3T depth ratio across the 32×51×51 grid. The requested decision-record lines 13 and 35 were read once and agree with this rule.

Missing GT captures:

- `arkitscenes/41125829`: `/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41125829.npz` (expected SHA-256 `563b03cf22ecd138a6f2462932250a0fda5dc966ae35d505d362eb0a6528ac4d`).

- `arkitscenes/42899325`: `/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899325.npz` (expected SHA-256 `86e16716c78549d15a676496e0232b0bae8729613e7e0f3f50bc058e055e9cd8`).

- `scannetpp/ef69d58016`: `/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__ef69d58016.npz` (expected SHA-256 `feb9d0b8f5d13acf0729744b4a00bca6e62cfbc9a500d13dbb754abfdefc50aa`).

## Reproduction and validation

Run from `/scratch/jjyeung/orch_n30/sb_scale1`. All reported MRA scores, intervals, ratios, counts, and coefficients come from:

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/scale_analysis.py freeze
/usr/bin/time -v env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/scale_analysis.py score > out/score.log 2> out/resources.log
```

The existing outputs intentionally prevent another scoring run in this workspace. The scorer reuses the exact named E3 `load_capture` and `mra` functions and camera decoder through AST extraction, avoiding the harness's workspace-writing startup hook. The harness directory was not modified.

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/test_scale.py
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/finish_report.py
```

Six unit tests passed: synthetic strict scale filters, room disjointness/determinism, existing-score refusal, MRA parity, camera-centre decoding, and equal-room log fitting. Scoring took 26.31 seconds wall time and 147,512 KiB peak RSS (`out/resources.log`). No GPU or network code ran. Inputs and code are pinned in each output JSON. `NEEDS.md` specifies the missing forward pass and resource estimate; `NEEDS_INPUTS.json` enumerates its exact 242 training captures and 32 anchor-frame pins per capture.

This internal report retains requested checkpoint names and split details because they are necessary to reproduce the experiment. It contains no superseded result narrative.
