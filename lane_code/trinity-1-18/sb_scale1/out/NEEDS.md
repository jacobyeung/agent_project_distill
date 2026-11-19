# Missing inputs for step-400 comparison

**MISSING:** K1 training own-depth grids for step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`, leg R1 job 172660. The verified export manifest records run `6ed2c7aa`, archive object `q8/8865619b/6ed2c7aa_m400.tar`, archive SHA-256 `dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5`, member directory `m400`. Expected heads: `m400/heads.pt`, SHA-256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. The artifact, full-weight manifest and preparation pins are recorded in `NEEDS_INPUTS.json`. No exact existing local step-400 weights path was found; none is invented here.

Run the step-400 own depth forward on all **242 K1 train captures**, **32 RGB anchors per capture** (7,744 frame slots). `NEEDS_INPUTS.json` lists every capture, room, anchor index, RGB path, RGB SHA-256, capture digest, and proposed new output path. The 239 captures with local GT can be scored immediately after that forward; the three missing GT paths are separately listed. No held-out captures are required.

Reproduce `GPU.own` in the pinned `native_kit/boundaries.py`: load the step-400 artifact and its matched config/data receipt with the sealed runtime; use each capture's original `model_row` RGB-only prompt and exact 32 anchor frames; preserve its frame layout and preprocessing; run `_prepare_decode` under `closed_adapters` without token generation; query `own.depth_head` on the resulting depth map at the 51×51 grid spanning 0–1000 on each anchor. Save a finite `[32,51,51]` metre-depth array and a receipt binding the checkpoint, code, capture, and output hashes. The depth head uses its private ViT backing; the existing runtime must supply all of its required context. Do not substitute a standalone head call without proving matching inputs. Reuse the already cached G3T grids, confidence, and poses. SAM and G3T forwards are unnecessary.

**CPU feasibility: MISSING / unmeasured.** The required step-400 weight bundle was not found in the bounded local K1/checkpoint searches. Export pins and source code alone cannot run a one-capture forward. The existing `GPU` boundary explicitly rejects CPU and requires at least 40 GiB VRAM; a CPU-compatible entrypoint would need verification. Whether a complete forward fits 8 cores and 40 GB RAM remains unknown. No GPU code was run. Do not interpret the lightweight scoring runtime as a model-forward measurement.

**GPU planning estimate:** approximately **1.04 GPU-hours** for 242 captures, plus model loading and staging. This extrapolates the mean **15.49 seconds/capture** from 242 recorded step-544 training-capture own forwards; the median is 14.46 seconds and the 10th–90th percentile is 14.11–17.40 seconds. The source GPU model was not verified, and this is not a measurement of step 400. The existing runner requires one GPU with at least 40 GiB VRAM. Recalibrate with one training capture on the intended device before scheduling the full pass.

The timing estimate comes from train-only `capture_start`/`capture_commit` metadata in `/scratch/jjyeung/k1/own_170235/native/probe/PROGRESS.jsonl`, SHA-256 `60a4ab48b0424e8fc2ed85a958b4f74bf5c17f36a2e347d953f537bd36a6082d`. Produce all counts and timing arithmetic with:

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/finish_report.py
```

After predictions and missing GT are supplied, use a new experiment output directory and freeze its bars before any new scoring; the existing result is protected against overwrite. Keep B−A and D−B on identical frame pairs and room folds.
