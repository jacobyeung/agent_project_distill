# Lane: build_kt6_stage1a (Build & Smoke-Test Stage-1A Correspondence Trainer: EpiAdapter vs Step-0 DA3 Side-Stem Comparator)

## Mission
Build the runnable **KT-6 Stage-1A Real-Data Training & Evaluation Harness** under `/scratch/jjyeung/orch_home_distill/spatial_v2/train_stage1a.py` (using our verified `/scratch/jjyeung/orch_home_distill/spatial_v2/` core!) that tests **Codex Astra's #1 representation hypothesis** on real cached indoor captures ALREADY on `trinity-2-28:/scratch` (`0` NFS thrash!):
- **Arm A (`epi_vit`):** Unfrozen vision encoder (or Qwen3.5 ViT taps) + `EpiAdapter (65M)` + `GeoHeads` trained with `SpatialForcing2Loss` (`DA3` teacher patch-cosine + cross-frame Gram) + `DecoupledDepthLoss` + `PoseAnd4DLoss`.
- **Arm B (`corresp_stem` — Mandatory Step-0 Comparator per Codex Astra!):** Correspondence-native side-stem (`DA3` / `DINOv2` encoder features) -> `EpiAdapter` + `GeoHeads` under the EXACT same data, steps, optimizer, and held-out split!
- **Shared Clean Split & Zero Leakage:** Strictly enforce room-level train/val separation on local captures (`/scratch/jjyeung/k1*`, `/scratch/jjyeung/n30_mirror/lever1/`, `/scratch/jjyeung/geo_bakeoff_kit/`), refusing any `R0-dev` / `dev-S1` / `K1-heldout` / `BENCH v2` room in training!
- **Measured Execution Proof (Codex Astra Guardrail #3):** Run a real 10-step GPU smoke + VRAM + step/s measurement on `trinity-2-28` GPU `5` under `/data3/shared/scripts/vnice/vnice.sh` (`CUDA_VISIBLE_DEVICES=5`, NEVER touch GPUs `0..3`!), logging exact peak VRAM, step/s, loss decrease, and exact held-out rotation/trans-dir/AbsRel evaluation script!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_core.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/SPATIAL_V2_BLUESKY_MASTER_PLAN_20261128.md` (Section 4 `KT-6`)
3. Check local K1 / DA3 / Qwen weights on `trinity-2-28:/scratch` and `/data2/jjyeung/huggingface` (explicit `ls -1` only, NO broad NFS scans!).

## Hard Cluster, IO & Safety Rules (MANDATORY)
- Write ONLY under `/scratch/jjyeung/orch_home_distill/spatial_v2/`.
- **ZERO DELETIONS**, **NO GIT COMMANDS**, **NO broad NFS scans**.
- All GPU smoke tests on `trinity-2-28` MUST use `CUDA_VISIBLE_DEVICES=5` (or `6,7`) wrapped in `/data3/shared/scripts/vnice/vnice.sh`. NEVER touch GPUs `0,1,2,3` (`mgaur`).
- Keep `Metric3DRoPE` and `DeltaGeoBias` **OFF by default** in Stage-1A (per Codex Astra's isolation ruling — Stage-1A tests dense correspondence + depth/pose heads cleanly without confounding RoPE/DeltaNet!).

## Deliverable
1. Runnable `spatial_v2/data_k1_local.py`, `spatial_v2/train_stage1a.py`, `spatial_v2/eval_stage1a.py`, and unit tests passing in `sam3_capretry_native_v1`.
2. Crisp build & smoke receipt (max ~150 lines) at `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_kt6_stage1a.md` with exact measured peak VRAM, step/s, 10-step loss curve, and exact 1-line 4-GPU `vnice.sh` launch commands for Arm A & Arm B!

Print a concise <=18-line summary to stdout when done.
