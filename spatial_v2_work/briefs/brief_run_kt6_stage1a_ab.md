# Lane: run_kt6_stage1a_ab (GPU Experimenter: KT-6 Stage-1A Head-to-Head Arm A epi_vit vs Arm B corresp_stem)

## Mission
Execute the decisive **2,000-step head-to-head scientific comparison** on `trinity-2-28` (`vnice.sh`, `0 MB/s` NFS) answering Codex Astra's #1 representation question:
- **Arm A (`epi_vit`):** Unfrozen Qwen3.5-9B ViT + `EpiAdapter (65M)` + `GeoHeads` under dense `DA3-Giant` `Spatial-Forcing²` + `DecoupledDepthLoss` + `PoseAnd4DLoss` (`Metric3DRoPE=OFF`, `DeltaGeoBias=OFF`).
- **Arm B (`corresp_stem` — Step-0 Correspondence-Native Comparator):** `DA3` DINOv2-L/14 correspondence stem + `EpiAdapter` + `GeoHeads` under the EXACT same split (`233` clean train / `53` clean `K1-heldout` rooms, `0` overlap), same steps (`2,000`), same batch/LR/seed!
- **Pre-Registered Scientific Bar (`SPATIAL_V2_BLUESKY_MASTER_PLAN_20261128.md` `KT-6`):**
  - Does `Arm A` break our old `18–20°` pose plateau (and frozen ViT `58–93°` blindness) and reach `<6.5°–8.0°` held-out rotation / `AbsRel <= 0.085`?
  - Or does `Arm B` (`DA3` correspondence side-stem) decisively outperform `Arm A` from step 250–2,000, proving we should adopt the correspondence side-stem for Stage-2 full 9B training?

## Mandatory Launch & Monitoring Cadence (USER-RULING 2026-11-25)
- First, verify `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B -m pytest /scratch/jjyeung/orch_home_distill/spatial_v2/tests/ -v` passes 100% after `fix_spatial_v2_r2`'s fixes (if `train_stage1a.py` needs any tiny 1-line signature adjustment for the fixed `spatial_v2` losses/config, fix cleanly and verify tests pass!).
- Check `nvidia-smi` on `trinity-2-28`: ONLY touch FREE GPUs among `4, 5, 6, 7` (NEVER touch `0, 1, 2, 3` owned by `mgaur`!). Pick TWO free GPUs (default `GPU 5` for Arm A, `GPU 7` for Arm B; or 2+2 GPUs if `4, 5, 6, 7` are all free and no other lane is using `4` or `6`!).
- Launch **BOTH Arm A and Arm B simultaneously** under `/data3/shared/scripts/vnice/vnice.sh` (using `setsid` / `nohup` or direct background inside your session — watch BOTH processes and logs!).
  - Single-GPU command pattern (since 10-step smoke proved `11.20 GiB` @ `1.75 step/s` -> 2,000 steps takes only ~20–30 min on 1 GPU, or ~12 min on 2 GPUs with `torchrun --nproc_per_node=2 --master_port 29511 / 29512`!):
    - `Arm A`: `--arm epi_vit --out-dir /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_a_v1 --steps 2000 --batch-size 1 --grad-accum 4 --num-views 16 --grid-h 20 --grid-w 20 --backbone-lr 2e-5 --head-lr 2e-4 --warmup-steps 100 --random-subsample --eval-every 250 --save-every 500`
    - `Arm B`: `--arm corresp_stem --out-dir /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_s1a_arm_b_v1 --steps 2000 --batch-size 1 --grad-accum 4 --num-views 16 --grid-h 20 --grid-w 20 --backbone-lr 2e-5 --head-lr 2e-4 --warmup-steps 100 --random-subsample --eval-every 250 --save-every 500`
    *(Adjust `--grad-accum` so effective global batch size is identical across both arms — e.g., `grad-accum=4` on 1 GPU = global batch 4, or `grad-accum=2` on 2 GPUs = global batch 4!)*
- **1-min -> 5-min Monitoring:** Check BOTH PID/GPU liveness AND training step/loss lines every **1 minute** for the first 3 minutes (two empty 1-min checks = debug immediately!). Once stably stepping (`step >= 50` with decreasing finite loss and `0` NaN/Inf), check every **3–5 minutes** until BOTH 2,000-step runs AND their final held-out `K1-heldout` (`n=53`) evaluations complete!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **ZERO DELETIONS**, **NO GIT COMMANDS**, **NO broad NFS scans**.
- All checkpoints, logs, and eval JSONs stay on local `/scratch/jjyeung/orch_home_distill/spatial_v2/runs/`.
- ALWAYS wrap every GPU process on `trinity-2-28` in `/data3/shared/scripts/vnice/vnice.sh`. NEVER touch GPUs `0, 1, 2, 3`.

## Deliverable
Write a crisp, quantitative head-to-head result record (max ~150 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_kt6_stage1a_ab.md`
Include: exact matched hyperparameters, `K1-heldout` (`n=53`, broken down by ScanNet / ScanNet++ / ARKitScenes!) metrics table across steps `{0, 250, 500, 1000, 1500, 2000}` (`Rot deg`, `TransDir deg`, `AbsRel`, `SI-AbsRel`, `d1`, `Scale`, `Grav deg`), peak VRAM, wall-clock time, checkpoint paths, and a clear verdict (`ARM_A_WINS`, `ARM_B_WINS`, or `NEEDS_SCALE_UP`). Print a concise <=18-line summary to stdout.
