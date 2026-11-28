# Spatial-V2 Stage-2 Full 9B Model + Orchard 4× H100 Launcher Build Report

**Status:** READY TO LAUNCH (zero delay once `KT-6 Stage-1A` selects `corresp_stem` vs `da3_nested`).
**Date:** 2026-11-28 (UTC)
**Scope:** Built five new Stage-2 modules cleanly under `/scratch/jjyeung/orch_home_distill/spatial_v2/` without modifying any files used by live `run_kt6_stage1a_ab` (`stage1a_model.py`, `train_stage1a.py`, `eval_stage1a.py`, `data_k1_local.py`).

---

## 1. Deliverables Created

| File | Size | Role |
|---|---|---|
| `spatial_v2/stage2_model.py` | 60 KB | `SpatialV2Stage2Model`: `Qwen3.5-9B` hybrid backbone (`32` layers: `24` `GatedDeltaNet` + `8` `FullAttn`), dual `--frontend {corresp_stem, da3_nested}` zero-init gated bridges, frozen `step-544` `ScaleDonorLock`, selective forward hooks at LLM `taps 16, 24` (`GeoPoseHead`, `GeoDepthHead`, `SF2` feature + Gram probes), 4D dynamic teacher gating (`has_4d_teacher`), optional Stage-2b `FlowExpert` VLA head (`taps 12, 16, 24`), Liger fused CE with 128-token chunked CE fallback, and `enforce_gated_deltanet_fp32()`. |
| `spatial_v2/stage2_data.py` | 29 KB | `Stage2RoomExclusionGuard` (6 blocklists including `ReSTI_ScanNet` `scene0000..0149`), E05 multi-turn epistemic trace encoder with strict assistant-only CE masking (`<verify>`, `<think>`, `<geo>`, `<answer>` supervised; user prompts, `<tool_response>`, `<tool_obs>` masked to `-100`), `Stage2SpatialDataset` with deterministic capture/epoch-keyed view sampling, and zero-disk `build_synthetic_stage2_batch`. |
| `spatial_v2/train_stage2.py` | 29 KB | Full BF16 trainer supporting `FSDP2` (`fully_shard` + `MixedPrecisionPolicy`), `DDP`, and single-GPU 49 GB `StatelessLowMemAdamW` mode; logs exact `weights_vram_gib`, `activation_vram_gib`, `peak_vram_gib`, throughput, and Orchard `4× H100` FSDP2 VRAM projections; syncs checkpoints directly to `gs://cmu-gpucloud-jjyeung/spatial_v2/`. |
| `spatial_v2/orchard_stage2_launch.sh` | 6.3 KB | Executable Slurm launcher (`#SBATCH --job-name=a15_cot_aps2v2`, `4× H100`, `advanced` or overrideable to `preempt`), redirects all caches/staging (`step-544`, `DA3`, optional `Point4D`) to node-local `/tmp` (`>=250 GiB` check, `0 B` written to `/project/community`), runs `torchrun --standalone --nproc_per_node=4 -m spatial_v2.train_stage2 --sharding fsdp2`, and syncs checkpoints/logs to GCS. |
| `spatial_v2/tests/test_stage2.py` | 23 KB | CPU unit test suite verifying Step-0 zero-init identity, full-graph gradient flow + `GatedDeltaNet` grad-checkpointing equivalence + `A_log`/`norm.weight` FP32 retention, masked `NaN` depth / `pmap_valid` / `has_4d_teacher=False` edge cases, and `Stage2RoomExclusionGuard` + E05 assistant-only masking. |

---

## 2. Key Engineering & Correctness Fixes Built In

1. **`Qwen3_5DecoderLayer` Gradient Checkpointing + `GatedDeltaNet` FP32 Safety:**
   - Explicitly forces `.train(mode)` on `self.lm`, `self.lm.model.language_model`, and all 32 `Qwen3_5DecoderLayer` instances (`use_cache=False`, `use_reentrant=False`), preventing the silent checkpointing bypass seen in `launch_orchard_vla_testl` (`max_activation_vram_gib = 1.04–1.16 GiB` verified on full 9.6B model).
   - `enforce_gated_deltanet_fp32()` is invoked at init and inside overridden `.to()` and `.bfloat16()`, keeping `linear_attn.A_log` and `linear_attn.norm.weight` strictly in `torch.float32`.
   - Selective forward hooks on `layers[15]` and `layers[23]` (plus `layers[11]` when `--use-vla-aux` is set) avoid `output_hidden_states=True` VRAM bloat and match uncheckpointed gradients to `<1e-6`.
2. **Zero-Init Identity Without Dead Step-0 Gradients:**
   - `fusion_gate` initializes at `0.0` (exact `0.0` perturbation to `Qwen3.5` logits at Step 0), while `bridge_patch_proj` / `bridge_cam_proj` use `std=0.02` init with a `0.1` residual into front-end `GeoHeads`, guaranteeing finite non-zero gradients on `fusion_gate`, bridge projections, LoRA/trunk, `taps 16 & 24`, and `Qwen3.5` from Step 1.
3. **Codex Stage-1A Fixes Integrated:**
   - Passes `depth_valid` explicitly as `pmap_valid` to `PoseAnd4DLoss` so masked pixels never dilute pointmap loss normalization.
   - Uses SHA-256 capture/epoch-keyed view subsampling and a dedicated seeded `DataLoader` generator for arm-matched determinism.
4. **Hard Leakage Prevention:**
   - `Stage2RoomExclusionGuard` hard-raises `RuntimeError` if any held-out room (`R0`, `dev-S1`, `BENCH_v2`, `withheld-80`, `K1-heldout`, or `ReSTI_ScanNet` `scene0000..0149`) appears in either K1 captures or E05 JSONL rows. Real `pilot0_smoke.jsonl` rows load with 0 leakage hits.

---

## 3. Verification Results

### A. CPU Unit Tests (`pytest`)
- `spatial_v2/tests/test_stage2.py`: **`4/4 passed`** in `16.37s` (`/scratch/jjyeung/envs/p1cpu/bin/pytest -v`).
- Full `spatial_v2/tests/` suite (`test_stage2.py` + `test_stage1a.py` + `test_spatial_v2.py`): **`17/17 passed`** in `17.66s`.
- Shell syntax check: `bash -n spatial_v2/orchard_stage2_launch.sh` passed with exit code `0`.

### B. 1-GPU BF16 3-Step Full-9B VRAM Smoke Tests (`trinity-0-18` GPU `4`, 49 GB RTX A6000)
- Wrapped in `/data3/shared/scripts/vnice/vnice.sh`; exact `Qwen3.5-9B` architecture (`hidden=4096, 32 layers = 24 GatedDeltaNet + 8 FullAttn`), `batch=1, num_views=8, grid=20×20, seq_len=128` (`928 tok/step`), `has_4d_teacher=True`, `taps=(16, 24)`, `0.0 GB` written to `0-18:/scratch` (`34G` free unchanged; all smoke artifacts kept in `/dev/shm`).

| Metric | `da3_nested` (Arm C) | `corresp_stem` (Arm B) |
|---|---|---|
| Total / Trainable Params | `9.568B` / `9.564B` | `9.632B` / `9.626B` |
| Weights VRAM (BF16 + FP32 `A_log`/`norm`) | `17.821 GiB` | `17.941 GiB` |
| Checkpointed Activation VRAM | `1.038 GiB` | `1.158 GiB` |
| **Measured Peak VRAM (1× A6000 49 GB)** | **`43.286 GiB`** (`43.811` resv) | **`43.521 GiB`** (`44.090` resv) |
| Step 1 → Step 2 → Step 3 Total Loss | `18.858 → 18.049 → 16.274` | `18.332 → 18.211 → 16.542` |
| Step 1 `L_lm` (Step-0 identity proof) | `13.2313` | `13.2313` (exact match) |
| `fusion_gate` progression | `0.0 → 1e-6 → 3e-6` | `0.0 → 1e-6 → 3e-6` |
| Gradient Norms (Steps 1–3, all finite) | `376.05 → 307.81 → 280.59` | `318.68 → 372.94 → 260.75` |
| Steady Throughput (1× A6000, torch fallback) | `0.321 step/s` (`297.4 tok/s`) | `0.313 step/s` (`290.1 tok/s`) |
| **Projected 4× H100 80 GB FSDP2 Peak VRAM** | **`40.168 GiB / GPU`** (`39.0 GiB` free) | **`40.519 GiB / GPU`** (`38.7 GiB` free) |

---

## 4. Orchard `4× H100` Launch Commands

```bash
# If Arm C (da3_nested) wins KT-6 Stage-1A (advanced 4x H100 queue):
sbatch -J a15_cot_aps2c01 spatial_v2/orchard_stage2_launch.sh da3_nested gs://cmu-gpucloud-jjyeung/spatial_v2/stage1a_winner.pt

# If Arm B (corresp_stem) wins KT-6 Stage-1A (advanced 4x H100 queue):
sbatch -J a15_cot_aps2b01 spatial_v2/orchard_stage2_launch.sh corresp_stem gs://cmu-gpucloud-jjyeung/spatial_v2/stage1a_winner.pt

# Optional preempt queue launch (with Stage-2b FlowExpert VLA auxiliary head):
USE_VLA_AUX=1 sbatch -J a15_cot_aps2p01 -p preempt --qos=preempt_qos spatial_v2/orchard_stage2_launch.sh da3_nested
```
