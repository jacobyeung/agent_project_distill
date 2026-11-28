# Brief: Build & VRAM-Benchmark `Spatial-V2` Stage-2 Full 9B Model + Orchard `4× H100` Launcher

## Objective
Build ahead so that the moment `KT-6 Stage-1A` (`Arm A` vs `Arm B` vs `Arm C`) finishes on `2-28`, we can launch **Stage-2 full 9B `Spatial-V2` training (`Qwen3.5-9B` + winning `KT-6` correspondence front-end + `taps 16, 24` dense `DA3`+`Point4D` distillation + `E05` multi-turn epistemic traces)** on Orchard `4× H100` immediately with ZERO delay.

## Hard Rules
- **DO NOT edit any files currently in use by live `run_kt6_stage1a_ab` (`stage1a_model.py`, `train_stage1a.py`, `eval_stage1a.py`, `data_k1_local.py`)** while GPUs `5,7` are running! Put all Stage-2 modules cleanly in NEW files under `/scratch/jjyeung/orch_home_distill/spatial_v2/`:
  - `spatial_v2/stage2_model.py`
  - `spatial_v2/stage2_data.py`
  - `spatial_v2/train_stage2.py`
  - `spatial_v2/orchard_stage2_launch.sh`
  - `spatial_v2/tests/test_stage2.py`
- **Assigned GPU for 1-GPU VRAM / gradient smoke test:** `trinity-0-18` GPU `4` (49 GB RTX 6000 Ada, MUST wrap in `/data3/shared/scripts/vnice/vnice.sh`!). **CRITICAL `/scratch` limit on `0-18`:** only **`34 GB` free `/scratch`** — NEVER copy `18 GB` Qwen3.5 weights onto `0-18`! Check first if Qwen3.5-9B / `step-544` already exists on `0-18:/scratch`; if not, run a **synthetic-weight Qwen3.5-9B exact-architecture config (`hidden=4096, layers=32/36, GatedDeltaNet+Attn`) 1-GPU BF16 forward+backward VRAM smoke test on `0-18` GPU `4`** (`0 GB` disk footprint!) which tests the exact parameter count, activation checkpointing, `GatedDeltaNet` grad-checkpointing compatibility, and peak VRAM with ZERO disk transfer! Do NOT touch `trinity-2-28` GPUs `0..7` or `0-18` GPUs `0..3`.
- **Architecture Contract (must support BOTH `Arm B` and `Arm C` front-ends via `--frontend {corresp_stem,da3_nested}`!):**
  1. Backbone: `Qwen3.5-9B` (`step-544` checkpoint OR base `Qwen3.5-9B`, configurable via `--init-ckpt`, keeping `step-544`'s `scale_donor` frozen if enabled).
  2. Multi-view Correspondence Front-End (selectable):
     - `corresp_stem` (`Arm B`): `DA3` DINOv2-L + `EpiAdapter` + zero-init gated fusion into Qwen3.5 visual stream (`gate=0` preserves exact `step-544` initialization at step 0!).
     - `da3_nested` (`Arm C`): Pre-trained multi-view `DA3-Nested` alternating-attention trunk (`LoRA` or selective unfreeze of last `k` blocks + zero-init gated projector into Qwen3.5 visual stream, so at step 0 the VLM loses ZERO `step-544` capability while gaining `<5°` multi-view camera pose & dense metric depth!).
  3. **Intermediate Tap Dense Distillation (`taps 16, 24` inside Qwen3.5-9B LLM):**
     - Attach lightweight `GeoHeads` (metric depth, relative pose, Plücker raymap, pointmap, gravity, FoV) + `SF2` feature/Gram distillation to LLM hidden states at **layers `16` and `24`** (matching `step-544` + `GeoAPI` / `VLA` mid-layer readouts!).
     - Support **two teacher sources**: static `DA3` dense teachers (already cached on `/scratch` + GCS) AND optional **4D dynamic teacher (`Point4D`/`Any4D` 3D track / dynamic mask)** cleanly gated by `has_4d_teacher` mask so Stage-2 seamlessly trains on BOTH static 3D rooms and dynamic 4D videos!
  4. **Joint Training Objectives:**
     - `L_lm`: Next-token CE on `E05` multi-turn epistemic traces (loss strictly on assistant turns, with exact `<verify>` / `<think>` / `<answer>` formatting) + existing spatial QA mix.
     - `L_geo`: Multi-tap (`16`, `24`, plus front-end head) depth (scale-invariant + scale-locked when metric), `SE(3)` relative pose, Plücker raymap, `metric_scale_locked`-gated pointmap (fixing Codex Stage-1A item #1: pass `depth_valid` as `pmap_valid`!), gravity, and FoV.
     - `L_sf2`: Feature + Gram alignment to `DA3` dense correspondence features.
     - `L_vla_aux` (optional toggle, default off in Stage-2a, on in Stage-2b): hook for `FlowExpert` / `ActionChunk` continuous VLA head so the exact same checkpoint drops straight into `vla_libero` (`B2`) and `navrun` (`N2`)!
  5. **Memory & Speed Engineering for `4× H100 80GB` (and 48GB smoke test):**
     - FSDP2 (`fully_shard`) / DDP + BF16 + activation checkpointing (CAREFUL with `Qwen3_5DecoderLayer` / `GatedDeltaNet` — inspect whether `launch_orchard_vla_testl` hit a `torch_chunk_gated_delta_rule` grad-checkpointing snag and handle it cleanly with `use_reentrant=False` or selective layer checkpointing!).
     - Liger-Kernel fused CE if installed (graceful fallback to chunked CE).
     - Exact peak-VRAM measurement & step-time logging (`steps/s`, `tokens/s`, `peak_vram_gib`).
     - Opaque Orchard job name (`a15_cot_ap<alnum>`), all caches on `/tmp`, checkpoint sync to `gs://cmu-gpucloud-jjyeung/spatial_v2/` (remember `/project/community` only has `9.0 GiB` free!).
- Zero deletions, zero `git`, zero broad NFS scans.

## Exact Steps
1. Read `/scratch/jjyeung/orch_home_distill/spatial_v2/config.py`, `geo_heads.py`, `epi_adapter.py`, `losses.py`, `stage1a_model.py`, and check `bluesky_20261128/runs/launch_orchard_vla_testl/transcript.jsonl` (only the specific lines around `Qwen3_5DecoderLayer` / `gated_delta_rule` if relevant) so we don't repeat any Qwen3.5 gradient-checkpointing pitfall.
2. Check what `Arm C` wrote (if `spatial_v2/stage1a_arm_c.py` exists yet; if not, define clean modular `DA3NestedBridge` interface compatible with `Arm C`).
3. Implement `stage2_model.py`, `stage2_data.py`, `train_stage2.py`, `orchard_stage2_launch.sh`, and `tests/test_stage2.py`.
4. Run full CPU unit tests (`pytest` on `test_stage2.py`):
   - Zero-init identity test (`gate=0` => `0.0` perturbation to `Qwen3.5` logits at step 0!).
   - Gradient flow test (non-zero finite grads on front-end bridge, LoRA/trunk, `taps 16 & 24` geo heads, AND LLM parameters).
   - Masked `NaN` depth / `depth_valid` -> `pmap_valid` / `has_4d_teacher=False` edge-case tests.
   - RoomExclusionGuard assertion inside `stage2_data.py` (refuses to load any held-out room!).
5. Run a **real 1-GPU BF16 3-step forward+backward VRAM smoke test** with real `Qwen3.5-9B` (or `step-544`) weights on `trinity-0-18` GPU `4` under `vnice.sh` (verify exact peak VRAM, finite loss, zero `gated_delta_rule` grad-checkpointing errors, exact projection for `4× H100 80GB`).
6. Write concise report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_stage2.md`.
