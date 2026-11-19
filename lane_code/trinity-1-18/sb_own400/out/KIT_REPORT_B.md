The frozen-FoV kit is built. Real-weight CPU output, real V1/V2 scores, and dataset-wide real FoV agreement are MISSING. The target command is `kit/cpu_check_228.sh`; it must run on trinity-2-28 after the reader lane prepares its pinned runtime and assets.

All 28 CPU tests pass. The one-capture fixture for arkitscenes/41048124 produces B, V1, and V2 grids with one LM pass and one private vision pass. The actual PointDepthHead test reproduces the unchanged HeadState pose-FoV path exactly; another test changes pose FoV and confirms V1/V2 grids stay fixed.

`out/BARS_FROZEN.json` is unchanged. `out/BARS_FROZEN_B.json` freezes the variant arms before scoring. A is step 544 with pose-head FoV; B is step 400 with pose-head FoV. V1 uses the checkpoint’s private `depth.fov`; V2 uses cached G3T FoV. Only A/B can select the donor. V1/V2 comparisons against A and B are report-only, with the same folds, eligibility, metric and paired room bootstrap. Missing arms are explicitly listed and contrasts use paired capture support.

The serving switch rejects non-pose FoV. `kit/fov_variants.py` therefore adds a separate explicit-FoV encode/query function. It captures the private features from the unchanged serving call and runs two additional head encodes/queries. V1 computes `1e-4 + (pi-2e-4)*sigmoid(depth.fov(captured.states.float()))`. This private branch is unused for training when pose-head conditioning is active, so its calibration is an empirical question.

G3T’s `pose9` already converts square-raster FoV to the source raster as `2*atan(crop_hw*tan(local_fov/2))`. The cached `raw_pose[anchor_slots,7:9]` therefore needs no second conversion. Its columns match the depth head’s vertical/horizontal radians. The builder authenticates cache hashes, capture identities and anchor indices. Every capture saves `fov_B`, `fov_V1`, `fov_V2`, `depth_V1`, and `depth_V2` beside `depth` in `own.npz`; a missing module yields an explicit MISSING receipt.

The fixture forward took 0.372391 seconds. V1 added 0.000863 seconds and V2 added 0.008200 seconds, measured inside the shared pass. Total fixture wall time was 4.085 seconds; peak RSS was 400,203,776 bytes. These small random-weight timings do not predict checkpoint GPU latency. Production receipts measure each arm separately. All three share the existing 4,320-second hard GPU cap; there is no extra GPU allocation.

The CPU fixture’s median absolute FoV differences are shown below. Only its G3T values come from a real cached model; the pose/private values are fixture outputs. Real per-dataset values remain MISSING until real captures return.

| Dataset / fixture | Pose–private | Pose–G3T | Private–G3T |
|---|---:|---:|---:|
| ARKitScenes, 32 anchors, degrees | 52.786739 | 6.613080 | 58.328117 |

The synthetic scorer smoke run covers 239 captures and 117,551 eligible pairs. Its V1 and V2 fixture grids equal B=1.014*A depth, so V1−B and V2−B are zero. Combined B−A is -0.644739 MRA points, with 95% CI [-0.840045, -0.451843]. These are plumbing checks, not step-400 results. The full routed-distance path is implemented but was not run for this fixture; the displacement smoke and unit suite passed.

The required interpreter is `/scratch/jjyeung/b01ec87a6f29b/d/v/py` with `-B -I`, using base environment `/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e`. The pin requires Torch 2.13.0+cu130, Transformers 5.19.0, torchvision 0.28.0+cu130, and SciPy 1.14.1. `ENV_REQUIRED.json` records the reader plan, receipt, runtime parts, and a2/a3/a4 hashes. The launcher checks archive hashes, module versions, and module roots before running. Every new receipt records the required environment; capture bindings also record observed Torch/Transformers/NumPy versions. Fixture receipts explicitly mark synthetic weights.

The environment is a confound: step 400 runs under Torch 2.13 while A’s step-544 grids came from Torch 2.11.0+cu129 / Transformers 5.12.1. The decision rule remains unchanged. The sensitivity check defines synthetic B scale as m times A’s OwnDepthScale, and sweeps every metric boundary outward from m=1 without assuming monotonicity. It does not measure an actual environment shift.

The smallest increasing multiplier is **1.000020583194919**, or **+0.002058319%**. The immediately preceding representable float still selects 400; this multiplier selects 544. The closest decreasing multiplier is 0.931984413504365, or -6.801559%. The increasing boundary has tiny margins; it should not be treated as a measured numerical error tolerance.

| Increasing multiplier contrast | B−A MRA points | 95% CI |
|---|---:|---|
| fold1 | -0.001195270 | [-0.002487653, -0.000002253] |
| fold2 | -0.001583390 | [-0.003261004, -0.000010199] |
| combined | -0.001388444 | [-0.002444460, -0.000410324] |

`kit/cpu_check_228.sh` exposes no GPUs, uses nice 10 and eight threads, and stops at 39 GB RSS. It loads step-400 weights once and forwards only arkitscenes/41048124. It writes all three grids, their OwnDepthScale values, their scale ratios to the bundled 544 grid, and median grid ratios. A BF16 unsupported-operation error alone allows a float32 retry for this CPU run; the receipt records the error and dtype change. Other errors stop. No real forward or target verification was performed here.

`out/STAGE_228.txt` and `out/STAGE_228_B.json` separate reported target files from the 31,400,339 bytes to copy. The reader lane must relocate its base runtime; a2/a3/a4 alone do not provide it. The local wrapper still contains an Orchard interpreter path. Exact missing local inputs are listed in `out/MISSING_B.json`. Earlier outputs remain, and the input kit snapshot is in `out/kit_before_b`.

Commands producing the reported numbers, from this workspace (CPU Python `/scratch/jjyeung/envs/p1cpu/bin/python`):

```bash
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES=
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/build_b.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/cpu_stub.py --out out/cpu_b_final
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/test_400b.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/env_sensitivity.py --out out/env_sensitivity_b
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/score_400b.py --synthetic --displacement-only --out out/synthetic_b_final
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/check_env_boundary.py
python -B kit/finalize_b.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/report_b.py
```

The builder refuses to overwrite frozen variant bars. Use fresh output names when reproducing forwards or scores. Boundary verification is recorded in `ENV_BOUNDARY_CHECK_FINAL_B.json`; source, input and output hashes accompany the JSON results.

After staging, the user can run:

```bash
kit/cpu_check_228.sh
# GPU run only when the coordinator authorizes it:
kit/launch_gpu.sh --card <i>
# Score returned captures on 1-18:
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/score_400b.py --own-root out/gpu_b/captures --out out/real_score_b
```

The no-archaeology skill governs this report. The environment comparison remains because it defines the requested confound. No GPU, SSH, network, Git, tmux operation, process termination, or external write was performed.
