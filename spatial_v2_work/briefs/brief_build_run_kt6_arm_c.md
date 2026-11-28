# Lane: build_run_kt6_arm_c (KT-6 Arm C: Pre-Trained Multi-View DA3-Nested Trunk + VLM Bridge on GPU 4)

## Scientific Motivation (Backed by Live Step-500 Evidence!)
Our live `KT-6 Stage-1A` showdown (`233` clean train / `53` `K1-heldout` rooms) just revealed a decisive finding at step 500:
- Single-frame encoders (`Arm A: Qwen3.5 ViT`, `Arm B: DA3 single-frame DINOv2-L/14`) + 6 random-init `EpiAdapter` blocks learn **depth (`delta1 = 71–77%`), scale (`1.01`), and gravity (`8.2–8.9°`)** immediately — **but multi-view rotation stays stuck at `78°–85°`**, whereas our live `KT-1b` benchmark proved **`DA3-only` achieves `3.63°` median `rot_max` (`1.88°` `rot_rms`, `-70%` ARKit failures vs `G3T`)**!
- **Hypothesis (`Arm C: da3_multiview_bridge`):** Instead of discarding `DA3`'s pre-trained multi-view alternating-attention layers (as `Arm B` did by loading only single-frame `da3_metric.backbone`!), keep a **compact pre-trained multi-view `DA3` trunk (`model.da3`, or frozen/LoRA multi-view `DA3` backbone -> lightweight VLM geometry bridge + `GeoHeads`)** so the model inherits `<4°` multi-view SE(3) correspondence + metric depth FROM STEP 0, AND aligns its multi-view geometric tokens to Qwen3.5-9B's `d=4096` visual/action space (`taps 16, 24, -1`) in `<50 ms`!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **DO NOT MODIFY** `stage1a_model.py`, `train_stage1a.py`, or `eval_stage1a.py` while `run_kt6_stage1a_ab` is still running on GPUs `5` & `7`! Write clean standalone files `spatial_v2/stage1a_arm_c.py` and `spatial_v2/train_arm_c.py` (importing `spatial_v2/data_k1_local.py` & `spatial_v2/geo_heads.py` / `losses.py` read-only!).
- **INCORPORATE ALL 3 CODEX ASTRA `GO_AFTER_FIXES` ITEMS** (`codex_recheck_spatial_v2.md`) into `train_arm_c.py`:
  1. Pass `depth_valid` as `pmap_valid` into `SpatialV2CompositeLoss`,
  2. Use a dedicated seeded `torch.Generator` + capture/epoch-keyed view sampling,
  3. Explicitly fail or report exact finite denominators (`num_valid / num_total`) on every eval metric (never silently drop NaNs!).
- **GPU rule:** Use ONLY `trinity-2-28` **`CUDA_VISIBLE_DEVICES=4`** wrapped in `/data3/shared/scripts/vnice/vnice.sh` (NEVER touch `0,1,2,3` [`mgaur`], `5,7` [`Arm A`/`Arm B`], or `6` [`VLA prechecks`]!).
- **ZERO DELETIONS**, **NO GIT COMMANDS**, **NO broad NFS scans**. Use local `/scratch/jjyeung/geo_bakeoff_kit/assets/da3` and `/scratch/jjyeung/k1*` (`0 MB/s` NFS!).

## Exact Execution Plan
1. Inspect the exact layers/parameter counts inside `/scratch/jjyeung/geo_bakeoff_kit/assets/da3` (`model.da3` multi-view backbone & camera/depth heads vs `model.da3_metric`).
2. Implement `spatial_v2/stage1a_arm_c.py` + `spatial_v2/train_arm_c.py`:
   - Loads `DA3`'s pre-trained multi-view alternating-attention trunk (`LoRA r=16` or last-4-blocks unfrozen + metric scale calibration + gravity-aligned SE(3) readout + `4096`-dim VLM/VLA projection tokens!),
   - Evaluates **Step 0 (zero-training baseline!)** on the EXACT same `53` clean `K1-heldout` rooms (`split_sha256: fcaee4f9...`, `0` leakage!) to establish the true multi-view floor (`rot_med_deg`, `trans_dir_med_deg`, `absrel`, `delta1`, `scale_ratio`, `gravity_err_deg`, plus `ms/16-frame-clip` latency & peak VRAM!),
   - Trains for `500–1,000` steps on the `233` clean train rooms on GPU `4` (`vnice.sh`), evaluating every `250` steps on `K1-heldout` (`n=53`)!
   - Also measures a **linear 3D-geometry probe** on `Arm C`'s projected VLM tokens vs `Arm A`/`Arm B` tokens to quantify how much metric 3D structure enters the VLM/VLA trunk!
3. Check GPU liveness and training steps every 1 min on launch -> 5 min steady state.

## Deliverable
Write a crisp, quantitative comparison report (`Arm A` vs `Arm B` vs `Arm C` on `K1-heldout` `n=53`, broken down by ScanNet / ScanNet++ / ARKitScenes, plus latency & VRAM) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_kt6_arm_c.md`
Print a concise <=18-line summary to stdout.
