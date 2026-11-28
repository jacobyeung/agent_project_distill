# Brief: Build `Spatial-V2` Unified End-to-End `G0` Base Codebase (`Astra 6.2` Blueprint)

## Objective
Implement **Codex Astra 6.2's** verified modular end-to-end single-checkpoint `Spatial-V2` codebase blueprint (`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/astra62_e2e_master_plan_20261128.md`), resolving **ALL FOUR `G0` admission blockers** so that our codebase is rock-solid, registry-modular ("fail quick, improve quicker"), and **100% end-to-end differentiable from RGB + optional `K`/proprio through native depth/pose/4D/grounding slots into BOTH Spatial QA AND VLA action heads**!

## Hard Rules
- **DO NOT modify `spatial_v2/stage1a_arm_c.py` or `spatial_v2/train_arm_c.py`** while live `kt6_s1a_arm_c_v1` is training on `2-28` GPU 4! Read them read-only so you match `Arm C`'s exact `CameraDec`, `DualDPT`, RoPE, and `trainable_state_dict` key conventions 100%!
- **Zero external tool calls at inference/VLA time** (`SpatialV2.forward(RGB, timestamps, view_ids, valid, text, K?, proprio?, state?) -> logits, geometry, action_distribution, state'`).
- **Assigned GPU for `G0` parity + action-gradient + real-C VRAM admission tests:** `trinity-0-18` GPU `4` (49 GB, MUST wrap in `/data3/shared/scripts/vnice/vnice.sh`; `0-18:/scratch` has only `34 GB` free — NEVER copy huge checkpoints onto `0-18`!) OR check `nvidia-smi` on `trinity-2-28` (GPUs `5` or `7` if `0% / <10 MiB` free when you reach GPU testing, wrapped in `vnice.sh`, where `DA3` + `step-544` + `K1` live locally with `1.8 TB` free!). Never touch busy GPUs (`2-28:0..4,6`).
- Zero deletions, zero `git`, zero broad NFS scans.

## Exact Modular Implementation Contract (Read `astra62_e2e_master_plan_20261128.md` Lines 33–54 & 85–93 FIRST!)

1. **Fix Blocker A — Exact `Arm C` Pretrained + Delta Loader (`spatial_v2/arm_c_loader.py`):**
   - Load **unmodified real `Arm C`** (`DA3` 40-block ViT-G/14 width 1536, `alt_start=13`, `CameraDec`, relative `DualDPT`, calibrated RoPE) + explicit key-mapped loading of `train_arm_c.py`'s `trainable_state_dict` (zero silent fallback, strict key verification + SHA256 manifest, NO compact dummy trunk substitution!).
   - **Native Distilled Metric Log-Depth Head + Single Focal Scaling (`spatial_v2/native_depth.py`):**
     - Trainable log-depth head predicting `z0` at predicted focal (centered shape + per-view shift + shared clip log-scale) — so we do NOT export the second Nested metric ViT!
     - Predict `log(|fx|/W), log(|fy|/H)` + principal point; when calibrated `K` is supplied, apply `zK = z0 * (|fx|/W) / (|fx_pred|/W)` **once** on the exact same raster (carry focal sign separately in ray construction; `zK = z0` if `K` absent).
     - Compose zero-init residual `exp(δξ)` with `CameraDec`'s relative `SE(3)`; fit positive shared translation scale `s_cam = Σw z_rel zK / (Σw z_rel^2 + ε)` in `fp32`; predict normalized per-view gravity, rotate into view-0, soft-pool to `+Z`-up; single continuous confidence-weighted `ScaleAnchor` residual when observable (FK baseline or known camera height).

2. **Fix Blocker B — 100% Differentiable Live Geometry & Native `32`-Slot Grounding/Motion Interface (`spatial_v2/native_slots.py`):**
   - **Zero detached paths:** Rebuild student pointmaps `P_world = R^T (z K^{-1}[u,v,1] - t)`, Plücker rays, scale solves, and 3D slot lifts strictly in `fp32` from live differentiable student tensors (never teacher caches, never `.detach()` on student depth/pose/memory paths!).
   - **`GeoControlSlots` (`K = 32` soft queries = `1` camera/scale + `31` entity/region slots):**
     - Shallow shared high-res RGB stem + differentiable `F.grid_sample` (`28×28` masklets) + fixed full-frame multiscale grid (so missed coarse boxes recover; NO argmax crop, NO thresholded mask, NO external `SAM 3` call!).
     - Predicts per-view presence, soft box center/extent, foreground weights, 3D center/extent, visibility, covariance, rigidity `p_stat`, and ego-decoupled 4D world displacement at offsets `{-1, +1, +4, +16}`.
     - Optional world→robot-base or gravity-level nav transform via calibrated hand-eye/FK (with explicit validity flag; view-0 fallback if unknown).
   - **Gated Fusion (`stage2_model.py` update):**
     - Project `Arm C` patches + camera/point/ray/depth/confidence features to `4096`; add `tanh(g) * W(geometry)` (`g=0`, `W` normal init — never double zero-init!) to matching Qwen visual embeddings (aligned `280²` C / `320²` Qwen → `20²` patches → `10²` merged tokens).
     - Zero-init gated residual cross-attention reading the `32` `GeoControlSlots` at LLM layers `16` and `24` (`use_geo_slots` config flag).
     - Ensure `vla_expert.py` / `QwenOFT` / `navrun` readouts support `detach_backbone=False` by default so **`action_loss` ALONE** flows finite non-zero gradients all the way back through slots, mask sampler, depth/scale, pose residual, 4D flow, `Arm C` tail, bridge, and LM taps!
     - Enforce all `48` `linear_attn.{A_log, norm.weight}` tensors in strict `float32` across load, forward, optimizer, FSDP, and export/reload.

3. **Fix Blocker C — Real Tokenizer, Exact Joins & Zero Privileged Inputs (`stage2_data.py` update):**
   - Replace surrogate tokenizer default with the real checkpoint tokenizer + chat template (explicit `allow_surrogate_tokenizer=False` default, only True in tiny CPU unit tests).
   - Require exact `(canonical_capture, frame_ids, crop/K, instance, timestamp)` joins between traces and RGB/geometry (never pair room A's trace with room B's RGB; missing match -> geometry-only example; reject mismatched join or truncated answer).
   - Physically strip ALL privileged tool observations/GT boxes/teacher tags from student input sequences (never rely on `-100` CE masking to hide privileged text from attention!).
   - Add clean modular `GaugeTwin` paired augmentation toggle (`intrinsics`, `mirror`, `reversal`, `reference_change` — exact matched pairs, recomputing relative transforms + signed intrinsics + axial/polar reflections accurately!).

4. **Fix Blocker D — Consolidated Export/Cold-Load + Fast-Falsification Harness (`spatial_v2/fast_eval.py` & `spatial_v2/train_stage2.py`):**
   - Fix `train_stage2.py` checkpoint saving so full consolidated weights (all ranks, trained LM + `Arm C` + native heads + slots + tokenizer/config + `fp32` dtype manifest) save cleanly and cold-load with network disabled & zero teacher files!
   - Build a clean, modular config/registry (`spatial_v2/config.py`) with 1-flag toggles (`frontend`, `depth_fov_norm`, `use_geo_slots`, `use_4d_flow`, `use_gauge_twins`, `vla_head_mode`) AND **`spatial_v2/fast_eval.py`**: a 1-command fast-falsification evaluator producing paired JSON receipts on `K1-heldout` (`n=53`) geometry + Habitat `E0` `90°` FoV depth + latency (`batch=1` p95 ms).

## Mandatory `G0` Acceptance Tests (`spatial_v2/tests/test_g0_admission.py` + Real-GPU Check)
1. **Unit & Contract Tests (`pytest -v spatial_v2/tests/test_g0_admission.py`):**
   - `test_action_loss_only_full_gradient_flow`: with ONLY `action_loss.backward()` (zero aux losses!), assert finite non-zero gradients on mask sampler (`grid_sample` stem), native depth/scale head, pose residual, 4D flow head, `Arm C` tail, bridge, `GeoControlSlots`, and LM taps (`16, 24`)! Repeat with `qa_loss` alone!
   - `test_gate_zero_parent_logit_parity`: `max_abs_diff <= 1e-5` in `fp32` when gates = 0.
   - `test_48_deltanet_fp32_load_forward_export_reload`: all 48 `A_log`/`norm.weight` tensors remain `torch.float32` through init, `.bfloat16()`, forward/backward, consolidated save, and cold reload.
   - `test_strict_join_and_no_privileged_tokens`: mismatched room/frame raises; privileged `<tool_obs>` physically absent from student `input_ids`.
   - `test_focal_scaling_and_anisotropic_unproj_parity`: `zK = z0 * (|fx|/W)/(|fx_pred|/W)` applied exactly once; unprojection matches GT ray geometry for both isotropic and anisotropic resize.
   - `test_streaming_causality`: perturbing future frames `t > now` produces `0.0` change in action/logits at `t <= now`.
2. **Real-GPU `Arm C` Parity Check (if `2-28` GPU 5 or 7 is free, else quick `Arm C` parity script ready to run):**
   - Verify unmodified integrated `Arm C` reproduces `kt6_s1a_arm_c_smoke/eval_step_000000.json` (`rot_med = 9.96° ± 0.1°`, `d1 = 91.6% ± 0.2 pp`) with 100% expected pretrained keys loaded and zero silent fallback!
3. Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_g0_unified_base.md`.
