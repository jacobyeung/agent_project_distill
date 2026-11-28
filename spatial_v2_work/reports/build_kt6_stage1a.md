# Build & Smoke-Test Receipt: KT-6 Stage-1A Correspondence Trainer (`Arm A epi_vit` vs `Arm B corresp_stem`)

**Date:** `2026-11-28` | **Host:** `trinity-2-28` | **GPU Tested:** `GPU 5` (`RTX 6000 Ada 49 GB`, wrapped in `/data3/shared/scripts/vnice/vnice.sh`; GPUs `0..3` untouched)
**Status:** `BUILT, UNIT-TESTED & 10-STEP GPU SMOKE VERIFIED` (`0` NFS thrash during training/eval)

---

## 1. Deliverable Inventory & Codex Astra Guardrail Compliance

| File | Role & Verified Contract |
|---|---|
| `spatial_v2/data_k1_local.py` | `RoomExclusionGuard` (all 5 blocklists: `R0_ROOMS.txt` [372], `dev_scene_exclusions.json` [100 groups/224 aliases], `benchmark_scene_exclusions.json` [511 groups/1,212 scenes incl. VSI/ReVSI/VSTI/ReSTI], `WITHHELD_ROOMS_80.json` [80], `K1_SPLIT.json` [58]) + `5/5` startup canaries (incl. ScanNet `_07`/`_99` rescan stripping) + `LocalK1CaptureDataset` returning paired Qwen (`16px` patch) & DA3 (`14px` patch) RGB tensors on aligned `(grid_h, grid_w)` grids with canonical `+Z`-up metric GT depth, `SE(3)` poses, gravity, FoV, Plucker rays, and pointmaps. |
| `spatial_v2/stage1a_model.py` | Zero-`transformers` standalone `Qwen35VisionEncoder` (`415.89M` total / `385.41M` trainable up to tap `25`, loaded from `/scratch/jjyeung/orch_home_distill/spatial_v2/cache/qwen35_9b_visual.safetensors`), `DA3CorrespStemEncoder` (`304.37M` DINOv2-L/14 taps `(7,15,23)` from local `/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors`), frozen `bf16` `DA3GiantTeacher` (`1,136.49M` 40L multi-view ViT-G/14, `teacher_dim=3072`), and unified `Stage1ACorrespondenceModel` (`EpiAdapter 66.4M` + `GeoPoseHead 30.45M` + `GeoDepthHead 2.65M` + `SpatialForcing2Loss 3.94M`). |
| `spatial_v2/train_stage1a.py` | Single-GPU & multi-GPU `torchrun` DDP Stage-1A trainer for `--arm {epi_vit, corresp_stem}` with matched splits, seed, cosine warmup schedule, `weight_decay=0.0` isolation for `GeoDepthHead.no_weight_decay_parameters()`, gradient checkpointing, per-step JSONL logging, atomic checkpointing, and held-out evaluation. |
| `spatial_v2/eval_stage1a.py` | Held-out geometric evaluator on the `53` clean `K1-heldout` captures (`50` rooms, `0` room overlap with train) reporting pairwise geodesic rotation error (`med`, `mean`, `<5°`, `<15°`), translation direction error (`med`, `mean`, `<15°`), metric `AbsRel`, median-aligned `SI-AbsRel`, `delta < 1.25`, median scale ratio, gravity angle error, and FoV error overall and per dataset (`arkitscenes`, `scannet`, `scannetpp`). |
| `spatial_v2/tests/test_stage1a.py` | 4 unit test suites verifying `RoomExclusionGuard` canaries/leakage rejection, real K1 GT `unproject <-> project` roundtrip, Stage-1A isolation (`use_metric_3d_rope=False`, `use_delta_geo_bias=False`, zero unused trainable params in both arms), and exact evaluator math. |

**Hard Isolation & Split Summary (`split_sha256: fcaee4f9b02b4ecbc125e5bc7c9a1c2067d322a52df33ec9c59dfa8cf1ec8436`):**
- `Metric3DRoPE`: **OFF** (`model.use_metric_3d_rope == False`, not instantiated)
- `DeltaGeoBias`: **OFF** (`model.use_delta_geo_bias == False`, `cfg.use_delta_geo_bias == False`)
- `EpiAdapter` LM Layer-1 projections (`out_patch_proj`, `out_cam_proj`): frozen at exact `0.0` (`requires_grad=False`) for step-0 LM identity preservation when promoted to Stage-2.
- **Clean Train Split:** `233` captures (`214` unique rooms) — `0` hits on `R0`, `dev-S1`, `BENCH_v2`, `withheld-80`, or `K1-heldout`.
- **Clean Held-Out Val Split:** `53` captures (`50` unique rooms: `32` `arkitscenes`, `8` `scannet`, `13` `scannetpp`) — `0` room overlap with train (`10` `withheld-80` captures excluded).

---

## 2. Unit Test Verification

- `sam3_capretry_native_v1`: `PYTHONPATH=/scratch/jjyeung/orch_home_distill /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -m unittest spatial_v2.tests.test_stage1a -v` -> **`4/4 PASS` in `1.68s`**
- `p1cpu` full suite: `PYTHONPATH=/scratch/jjyeung/orch_home_distill /scratch/jjyeung/envs/p1cpu/bin/pytest spatial_v2/tests/ -v` -> **`12/12 PASS` in `2.63s`**

---

## 3. Measured 10-Step Real-Data GPU-5 Smoke Benchmark (`num_views=8`, `grid=20x20`, `bs=1`, `grad_accum=2`, `bf16`)

Both arms trained on the exact same 10 real K1 batches (`effective_batch_size=2` clips = `16` views/step) with online frozen `DA3-Giant` (`1.14B`) `SpatialForcing2Loss` teacher + `DecoupledDepthLoss` + `PoseAnd4DLoss`:

| Metric / Spec | Arm A (`epi_vit`: Qwen3.5 ViT + `EpiAdapter`) | Arm B (`corresp_stem`: DA3 DINOv2-L/14 + `EpiAdapter`) |
|---|---:|---:|
| Trainable Parameters (+ `1,136.5M` frozen Teacher) | **`482.54 M`** (`385.4M` ViT + `60.1M` Epi + `37.0M` Heads/Probes) | **`401.40 M`** (`304.4M` DINOv2 + `60.0M` Epi + `37.0M` Heads/Probes) |
| **Measured Peak VRAM Allocated (`GPU 5`)** | **`11.20 GiB`** (`13.68 GiB` reserved) | **`9.78 GiB`** (`11.66 GiB` reserved) |
| **Measured Steady Throughput (`step 2..10`)** | **`1.75 step/s`** (`0.570 s/step`) | **`1.97 step/s`** (`0.507 s/step`) |
| Total Loss (`Step 1 -> Min -> Step 10`) | `5.7659 -> 5.2766 (s9) -> 5.5491` | `7.0184 -> 5.7683 (s9) -> 6.0675` |
| `SpatialForcing2` Cosine Loss (`Step 1 -> Step 10`) | **`0.9923 -> 0.6462`** (`-34.9%`) | **`0.9840 -> 0.6710`** (`-31.8%`) |
| `DecoupledDepthLoss` (`Step 1 -> Step 10`) | **`1.5141 -> 0.4254`** (`-71.9%`) | **`1.3150 -> 0.1008`** (`-92.3%`) |
| **Held-Out Eval (`n=53` `K1-heldout`, `3.1–3.2s`)** | | |
| — Metric Depth `AbsRel` / `SI-AbsRel` | `0.4797` / `0.3710` (ScanNet: `0.3308` / `0.2456`) | **`0.4355` / `0.3446`** (ScanNet: **`0.3190` / `0.2416`**) |
| — Depth `delta < 1.25` / Median Scale Ratio | `33.6%` / `1.054` | **`34.4%` / `1.015`** |
| — Pairwise Rotation Med / Trans-Dir Med (`<15°`) | `99.39°` / `83.85°` (`2.6%`) | `99.46°` / **`81.48°` (`3.6%`)** |
| — Gravity Error | **`22.91°`** | `24.18°` |

### 10-Step Loss Trajectory (`total_loss` | `sf2_feat` | `depth_total` | `pose`)

| Step | Arm A (`epi_vit`) `total` | Arm A `sf2_feat` | Arm A `depth` | Arm A `pose` | Arm B (`corresp_stem`) `total` | Arm B `sf2_feat` | Arm B `depth` | Arm B `pose` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `5.7659` | `0.9923` | `1.5141` | `2.6801` | `7.0184` | `0.9840` | `1.3150` | `3.4358` |
| 2 | `7.1221` | `0.9693` | `2.3820` | `3.4437` | `8.0288` | `0.9557` | `3.4520` | `3.5597` |
| 3 | `7.3859` | `0.9334` | `3.4017` | `3.4451` | `6.8406` | `0.9519` | `1.4790` | `3.4337` |
| 4 | `6.5355` | `0.8781` | `1.0615` | `3.4424` | `6.4871` | `0.8938` | `1.7473` | `3.2291` |
| 5 | `5.8480` | `0.7985` | `1.0510` | `3.1322` | `5.9794` | `0.8398` | `0.2709` | `3.3563` |
| 6 | `6.2766` | `0.7433` | `0.6164` | `3.4979` | `6.4140` | `0.7973` | `0.3230` | `3.6027` |
| 7 | `6.0180` | `0.7052` | `0.5567` | `3.3627` | `6.0904` | `0.7604` | `1.5926` | `3.0991` |
| 8 | `6.2130` | `0.6731` | `0.5542` | `3.5162` | `5.7759` | `0.7408` | `0.5698` | `3.1628` |
| 9 | `5.2766` | `0.6251` | `0.1948` | `3.1038` | `5.7683` | `0.7097` | `0.6194` | `3.1453` |
| 10 | **`5.5491`** | **`0.6462`** | **`0.4254`** | **`3.1620`** | **`6.0675`** | **`0.6710`** | **`0.1008`** | **`3.5117`** |

---

## 4. Exact 1-Line 4-GPU `vnice.sh` Launch Commands (`trinity-2-28:4,5,6,7`)

**Arm A (`epi_vit` — Unfrozen Qwen3.5 ViT + `EpiAdapter` + `GeoHeads`, 2,000 steps, `~19 min` wall-clock on 4x Ada):**
```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 PYTHONPATH=/scratch/jjyeung/orch_home_distill /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/torchrun --standalone --nproc_per_node=4 -m spatial_v2.train_stage1a --arm epi_vit --out-dir /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_stage1a_arm_a_epi_vit --steps 2000 --batch-size 1 --grad-accum 2 --num-views 16 --grid-h 20 --grid-w 20 --backbone-lr 2e-5 --head-lr 2e-4 --warmup-steps 100 --random-subsample --eval-every 250 --save-every 500
```

**Arm B (`corresp_stem` — Step-0 DA3 DINOv2-L/14 Side-Stem Comparator + `EpiAdapter` + `GeoHeads`, 2,000 steps, `~17 min` wall-clock on 4x Ada):**
```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 PYTHONPATH=/scratch/jjyeung/orch_home_distill /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/torchrun --standalone --nproc_per_node=4 -m spatial_v2.train_stage1a --arm corresp_stem --out-dir /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_stage1a_arm_b_corresp_stem --steps 2000 --batch-size 1 --grad-accum 2 --num-views 16 --grid-h 20 --grid-w 20 --backbone-lr 2e-5 --head-lr 2e-4 --warmup-steps 100 --random-subsample --eval-every 250 --save-every 500
```

**Standalone Held-Out Evaluation (`53` `K1-heldout` captures / `50` rooms):**
```bash
CUDA_VISIBLE_DEVICES=5 PYTHONPATH=/scratch/jjyeung/orch_home_distill /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -m spatial_v2.eval_stage1a --checkpoint /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_stage1a_arm_a_epi_vit/latest.pt --num-views 16 --out /scratch/jjyeung/orch_home_distill/spatial_v2/runs/kt6_stage1a_arm_a_epi_vit/eval_heldout.json
```
