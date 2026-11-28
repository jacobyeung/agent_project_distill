# Lane: build_spatial_v2_core (Clean-Sheet `spatial_v2/` Architecture Scaffold & Verified Unit Tests)

## Mission
Follow `USER 2026-11-09` ("Build experiments first") and `w2_architecture_eval_master.md` Track B: build our clean-sheet, modular, `<2,500`-LOC **`spatial_v2/`** PyTorch codebase under `/scratch/jjyeung/orch_home_distill/spatial_v2/` implementing the core **GeoLoop-Delta + Spatial-Forcing²** depth/pose/4D-flow/3D-RoPE modules AND verify EVERY module mathematically with a comprehensive pytest/unit-test suite (zero-init identity, SE(3) equivariance, Metric 3D-RoPE relative-distance property, `TT-BA` convergence, gradient flow, and `ViewSet-Unified` video + multi-view + wrist/agentview packing)!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_geoloop_trunk.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_4d_dynamic_streaming.md`
3. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_architecture_eval_master.md`
4. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md`

## Hard Cluster, IO & Safety Rules (MANDATORY)
- Write ONLY under `/scratch/jjyeung/orch_home_distill/spatial_v2/`. Do NOT edit `/home/jjyeung/agent_project_distill` or `/home/jjyeung/agent_project`.
- **ZERO DELETIONS** (`rm_guard`), **NO GIT COMMANDS**, **NO broad NFS scans**.
- Check which local Python env on `trinity-2-28:/scratch/jjyeung/envs/` has PyTorch 2.x (`ls -1 /scratch/jjyeung/envs/` + check `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"` on `planner_local_v1` / `k6cv2` / `sam3_capretry_native_v1`).

## Clean Modular Architecture to Build (`spatial_v2/`)
1. `spatial_v2/config.py`: Dataclass configs for `SpatialV2Config` (aligned to Qwen3.5-9B's 32-layer hybrid topology: 24 DeltaNet + 8 full-attn layers `{4,8,12,16,20,24,28,32}`, toggleable `EpiAdapter` vs `DA3-Small` stem, toggleable `L_geo=12` or `16`, `ViewSet-Unified` modes: `video`, `multiview`, `robot_wrist_exo`).
2. `spatial_v2/epi_adapter.py`: Pre-LM `EpiAdapter` (`6` permutation-invariant alternating intra-frame 2D-RoPE / cross-frame global attention blocks over multi-layer ViT taps, `(stream_id, timestamp)` embeddings disabling cross-camera `temporal_patch=2` bleeding, zero-init output projection!).
3. `spatial_v2/geo_heads.py`: Mid-trunk `GeoHeads`:
   - `GeoDepthHead`: focal-normalized log-depth + aleatoric uncertainty $(\hat{D}_t, \hat{\sigma}_{D,t})$ + static rigidity $p^{\text{stat}}_t \in [0,1]$ + residual 3D scene flow $\Delta\hat{\mathbf{P}}_t$,
   - `GeoPoseHead`: gravity-aligned 6D rotation + metric translation + Plücker ray embedding + covariance $(\hat{T}_t, \hat{\Sigma}_{T,t})$ + intrinsics $(\log f_x/W, \log f_y/H)$,
   - Exact pinhole unprojection to canonical `+Z`-up world coordinates $\mathbf{P}_{t,u,v}$ with `fx < 0` mirror support (for MuJoCo LIBERO!).
4. `spatial_v2/ttba.py`: Fast 3–5 step damped Levenberg-Marquardt `TT-BA` module refining relative SE(3) poses & per-frame scale under Huber + $p^{\text{stat}}$ weighting, emitting geometric health diagnostics (`reproj_err`, `parallax_deg`, `scale_consistency`, `pose_cond`).
5. `spatial_v2/metric_3d_rope.py`: Zero-init **Metric 3D-RoPE** + Plücker ray feedback injector for upper full-attention layers (`16,20,24,28,32`), plus optional `DeltaGeoBias` (`GeoDecay`) module for Gated DeltaNet layers, guaranteeing exact identity at initialization (`output == base_output` to `1e-6` before training!).
6. `spatial_v2/losses.py`:
   - `SpatialForcing2Loss`: dense teacher patch-cosine + cross-frame Gram correspondence distillation (`DA3`/`Point4D` teacher -> `taps 16, 24`),
   - Decoupled scale-invariant + metric Laplacian NLL depth loss (with `metric_scale_locked` flag so uncalibrated robot clips never corrupt metric scale!),
   - Relative pairwise SE(3) + gravity + raymap + 4D rigidity/flow losses.
7. `spatial_v2/vla_expert.py`: Clean `300M`-scalable **System-1 `SE(3)` `FlowExpert`** cross-attending to `taps 12/16/24` metric 3D+flow tokens + proprioception + optional world subgoal `T_goal`, with `detach_backbone=True` support and `<18 ms` batched latency test!
8. `spatial_v2/tests/test_spatial_v2.py`: Comprehensive CPU unit tests (plus optional 30s GPU latency check on `trinity-2-28` GPU `5` under `vnice.sh` — NEVER touch GPUs `0..3`!) verifying:
   - Zero-init exact identity (`<1e-6`) of `EpiAdapter`, `Metric 3D-RoPE`, and `FlowExpert` residual gates,
   - Rigid $SE(3)$ invariance & exact unprojection/reprojection round-trip (including `fx < 0` MuJoCo mirror!),
   - `TT-BA` recovering `>70%` of injected rotation (`10°`) and `1.94×` scale perturbations in `<25 ms`,
   - Exact finite gradients (`0` NaN/Inf) through all losses including `SpatialForcing2Loss` and `ViewSet-Unified` batches (`video`, `multiview`, `wrist+exo`),
   - `FlowExpert` inference latency measurement (`ms/chunk`).

## Deliverable
1. All clean, tested modules under `/scratch/jjyeung/orch_home_distill/spatial_v2/`.
2. Crisp build & test receipt (max ~150 lines) at `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_core.md` (with exact pytest output, parameter counts, and measured timings — ready for Codex Astra cross-check and immediate Stage-1A KT-1 training on `trinity-2-28:4..7`!).

Print a concise <=18-line summary to stdout when done.
