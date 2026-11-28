# Build & Verification Receipt: `spatial_v2/` Core Architecture

**Date:** `2026-11-28` | **Host:** `trinity-2-28` | **Path:** `/scratch/jjyeung/orch_home_distill/spatial_v2/`
**Status:** `BUILT & VERIFIED` — `1,933` core LOC (`2,365` total incl. tests, `<2,500` LOC budget), **`8/8` pytest PASS (`0` warnings)**, ready for Codex Astra cross-check and Stage-1A KT-1 training on `trinity-2-28:4..7`.

---

## 1. Module Inventory & Full-Scale `Qwen3.5-9B` Parameter Budget

| File | LOC | Implemented Modules & Key Contracts | `Qwen3.5-9B` Params |
|---|---:|---|---:|
| `spatial_v2/__init__.py` | 38 | Public package exports | — |
| `spatial_v2/config.py` | 280 | `SpatialV2Config` (32L = 24 DeltaNet + 8 full-attn `{4,8,12,16,20,24,28,32}`), `l_geo ∈ {12,16}`, `stem_type ∈ {epi_adapter,da3_small}`, `ViewSet-Unified` (`video`/`multiview`/`robot_wrist_exo`) | — |
| `spatial_v2/epi_adapter.py` | 264 | 6-block permutation-invariant intra-2D-RoPE / global `EpiAdapter`, `(stream_id, timestamp)` metadata, `temporal_patch=2` cross-camera isolation, zero-init residuals; `DA3SmallStemAdapter` fallback | `65.246 M` (`DA3` stem: `3.253 M`) |
| `spatial_v2/geo_heads.py` | 419 | Scale-decoupled `GeoDepthHead` (`d_shape + mu_view + log_gamma_scene`, `sigma_D`, `p_stat`, multi-horizon `delta_P_obj`), bidirectional N-view `GeoPoseHead` (6D rot, `t`, gravity `S^2`, FoV, cov, Plucker rays), exact `fx < 0` MuJoCo unproj/proj & SE(3)-invariant `+Z`-up canonicalizer | `GeoPose`: `35.561 M`<br>`GeoDepth`: `3.526 M` |
| `spatial_v2/ttba.py` | 273 | 3–5 step block-sparse damped Levenberg-Marquardt `TTBA` (`SE(3)` + per-frame scale) under Huber + `p_stat`, `2.5°` ray-yaw trigger gate, full `TTBADiagnostics` | `0` (analytic solver) |
| `spatial_v2/metric_3d_rope.py` | 161 | Zero-init additive `Metric3DRoPE` (`beta_h = 0`, `omega ∈ [0.1, 20]` rad/m), full-rank zero-init `PluckerGeoInjector`, zero-init `DeltaGeoBias` (`GeoDecay`) + `deltanet_3d_step` | `PluckerInj`: `2.396 M`<br>`3D-RoPE`: `0.002 M`/L<br>`DeltaBias`: `0.0003 M`/L |
| `spatial_v2/losses.py` | 283 | `SpatialForcing2Loss` (`taps 16, 24` patch-cosine + stratified Gram, train-only), `DecoupledDepthLoss` (`metric_scale_locked` zero-grad guarantee on `log_gamma`), `PoseAnd4DLoss` (pairwise `SE(3)`, gravity, FoV, ray, pointmap, rigidity, flow, sparsity, reversal), `SpatialV2CompositeLoss` | `10.490 M` (train-only; `0` eval cost) |
| `spatial_v2/vla_expert.py` | 215 | `~300M` System-1 `SE(3)` `FlowExpert` cross-attending to cached `taps {12,16,24}` + 3D/flow tokens + proprio + optional `T_goal`, `detach_backbone=True`, zero-init gates, CUDA-graph-ready 10-step Euler ODE | `297.694 M` |
| `spatial_v2/tests/test_spatial_v2.py` | 432 | 8 mathematical & end-to-end verification tests (CPU + dual-env checked) | — |
| **Total** | **2,365** | **Deployed VLM geometry overhead (`Epi + Pose + Depth + Inj + 4×RoPE + 12×Delta`):** | **`106.74 M`** (`18.9 ms` GPU) |

---

## 2. Exact Pytest Output & Verified Mathematical Invariants

Executed via `/scratch/jjyeung/envs/p1cpu/bin/pytest -v` (`torch 2.11.0+cpu`, `pytest 8.4.2`) and cross-verified under `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` (`torch 2.10.0+cu128`):

```text
spatial_v2/tests/test_spatial_v2.py::test_config_qwen35_topology_and_viewset_packing PASSED [ 12%]
spatial_v2/tests/test_spatial_v2.py::test_zero_init_exact_identity PASSED [ 25%]
spatial_v2/tests/test_spatial_v2.py::test_epi_adapter_permutation_invariance PASSED [ 37%]
spatial_v2/tests/test_spatial_v2.py::test_se3_invariance_and_unprojection_roundtrip_including_mujoco_mirror PASSED [ 50%]
spatial_v2/tests/test_spatial_v2.py::test_metric_3d_rope_relative_distance_property PASSED [ 62%]
spatial_v2/tests/test_spatial_v2.py::test_ttba_recovers_rotation_and_scale_under_25ms PASSED [ 75%]
spatial_v2/tests/test_spatial_v2.py::test_losses_and_exact_finite_gradients_all_viewset_modes PASSED [ 87%]
spatial_v2/tests/test_spatial_v2.py::test_flow_expert_ode_sampling_and_latency PASSED [100%]
============================== 8 passed in 1.56s ===============================
```

Verified guarantees:
- **Zero-init exact identity (`<1e-6`):** `EpiAdapter`, `DA3SmallStemAdapter`, `Metric3DRoPE`, `PluckerGeoInjector`, `DeltaGeoBias` (`+ deltanet_3d_step`), and `FlowExpert` cross-attention/`T_goal` residual gates all match base outputs to `<1e-6` at initialization.
- **Permutation invariance (`<1e-5`):** Permuting `N` unordered views in `EpiAdapter` (`multiview`) permutes outputs identically (zero temporal-index leakage).
- **`SE(3)` invariance & `fx < 0` MuJoCo mirror (`<1e-5`):** `so3`/`se3` exp-log and 6D rotation round-trip cleanly; `unproject_depth <-> project_points` round-trips to `<1e-4` for both `fx > 0` and `fx < 0`; `compute_gravity_leveled_poses` + canonical unprojection are strictly invariant to global `SE(3)` transforms (`<1e-5`), placing View 0 at `[0,0,0]` and gravity at `+Z`.
- **Metric 3D-RoPE relative displacement (`<1e-4`):** Shifting all 3D visual coordinates by arbitrary `delta ∈ R^3` leaves all visual attention logits invariant while text tokens remain unperturbed.
- **Scale-locked gradient isolation:** `DecoupledDepthLoss` with `metric_scale_locked = 0` yields exact `0.0` gradient on `GeoDepthHead.log_gamma_bias` while preserving finite non-zero shape gradients; `FlowExpert(..., detach_backbone=True)` yields `None` gradients on backbone taps and `geo_tokens`. All losses and parameter gradients across `video`, `multiview`, and `robot_wrist_exo` are strictly finite (`0` NaN/Inf).

---

## 3. Measured `TT-BA` Convergence (CPU fp32) & RTX 6000 Ada `bf16` Latency

### 3.1 `TT-BA` (5 Damped LM Steps, 6 Views, 15% Dynamic Outliers, `10°` Rot + `1.94×` Scale Error)

| Scenario | Rot Error (Before -> After) | Rot Recovery | `1.94×` Scale Recovery | Reproj (px) | Parallax | Cond | CPU Time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Relative `1.94×` (`fx > 0`) | `10.00° -> 0.004°` | **`100.0%`** | **`100.0%`** | `57.68 -> 0.007` | `18.2°` | `3.2e4` | **`21.22 ms`** |
| Global `1.94×` (metric anchor) | `10.00° -> 0.003°` | **`100.0%`** | **`98.0%`** | `92.48 -> 0.040` | `19.1°` | `9.3e4` | **`21.71 ms`** |
| Relative `1.94×` (`fx < 0` MuJoCo) | `10.00° -> 0.002°` | **`100.0%`** | **`100.0%`** | `43.92 -> 0.006` | `18.3°` | `3.1e4` | **`21.30 ms`** |

*(Yaw-disagreement trigger gate verified: `<2.5°` clips skip LM with `triggered=False, committed=False`.)*

### 3.2 Full-Scale `Qwen3.5-9B` GPU Latency (`trinity-2-28` GPU `5`, RTX 6000 Ada, `bf16`, `vnice.sh`)

| Component | Workload | Measured Latency | Target / Status |
|---|---|---:|---|
| `EpiAdapter` (`65.25M`) | `32f`, `20×26 -> 10×13` (`3` ViT taps) | **`10.82 ms`** | `<14 ms` PASS |
| `GeoPoseHead` (`35.56M`) | `32f`, `10×13` + Plucker rays | **`2.09 ms`** | `<5 ms` PASS |
| `GeoDepthHead` (`3.53M`) | `32f`, `20×26` + 4D flow (`4` horizons) | **`1.66 ms`** | `<5 ms` PASS |
| `PluckerGeoInjector` (`2.40M`) | `4,160` tokens (`L_geo -> L_geo+1`) | **`0.29 ms`** | `<1 ms` PASS |
| `Metric3DRoPE` (`4` upper full-attn layers) | `4,160` tokens (`0.90 ms/L`) | **`3.60 ms`** | `<5 ms` PASS |
| `DeltaGeoBias` (`12` upper DeltaNet layers) | `4,160` tokens (`0.04 ms/L`) | **`0.48 ms`** | `<1 ms` PASS |
| **Total Native 3D VLM Overhead** | **Full 32-frame GeoLoop pass** | **`18.94 ms`** | **`<25 ms` PASS (`~1000×` vs G3T)** |
| `FlowExpert` (`297.69M`, Eager) | `10`-step ODE, `1,040` mem tokens (`bs=1` / `bs=4`) | `41.33 ms` / `10.50 ms/chunk` | `mem=0.61/1.47 ms` |
| **`FlowExpert` (`297.69M`, CUDA Graph)** | **`10`-step ODE, `1,040` mem tokens (`bs=1` / `bs=4`)** | **`13.51 ms`** / **`4.09 ms/chunk`** | **`<18 ms` PASS (`74 Hz` @ `bs=1`)** |

---

## 4. Handoff for Codex Astra Cross-Check & Stage-1A KT-1 Launch

1. **Environments on `trinity-2-28`:** `pytest` runs cleanly in `/scratch/jjyeung/envs/p1cpu/bin/pytest`; CUDA `bf16` training/benchmarks run in `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` (`torch 2.10.0+cu128`). Note: `bf16` GPU test caught two fp32/bf16 cast sites (`StreamMetadataEncoder` and `GeoDepthHead` `view_mask`/`fov_film`), both fixed and re-verified on GPU `5`.
2. **Optimizer Parameter Groups for KT-1:** Pass `GeoDepthHead.no_weight_decay_parameters()` and `Metric3DRoPE.no_weight_decay_parameters()` into `weight_decay=0.0` groups per `w2_geoloop_trunk.md` Section 3.1.
3. **Ready for Immediate Stage-1A KT-1 (`trinity-2-28:4..7` `vnice.sh`):** Attach `EpiAdapter` + `GeoDepthHead` + `GeoPoseHead` + `SpatialV2CompositeLoss` directly to unfrozen Qwen3.5 ViT taps `[9, 17, 25]` and cached `DA3-Nested` targets (no 9B LM in loop; `<15 ms` geometry overhead).
