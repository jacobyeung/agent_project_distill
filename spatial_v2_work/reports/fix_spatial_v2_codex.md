# Spatial-V2 Codex Astra Review Fix Receipt

All 7 BLOCKERs and 4 WARNINGs in `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/codex_review_spatial_v2.md` have been resolved across the 8 owned core files (`config.py`, `epi_adapter.py`, `geo_heads.py`, `ttba.py`, `metric_3d_rope.py`, `losses.py`, `vla_expert.py`, `tests/test_spatial_v2.py`, plus export in `__init__.py`). Zero edits were made to `data_k1_local.py`, `train_stage1a.py`, or `eval_stage1a.py`.

## Summary of Fixes by Finding

1. **BLOCKER 1 — Subgoal conditioning zero gradient (`vla_expert.py:100-102`)**
   - Removed zero-initialization from `self.subgoal_proj[-1]` and kept only `self.subgoal_gate = nn.Parameter(torch.zeros(d))` zero-initialized.
   - Preserves exact zero-init forward identity at step 0 while guaranteeing strictly non-zero gradients on `subgoal_gate` on the very first `.backward()` and on `subgoal_proj` immediately after the first gate update.

2. **BLOCKER 2 — TT-BA cheirality violation & support-drop cost reduction (`ttba.py:67-105, 135-256`)**
   - Fixed the active observation support $M_0$ (`support_mask`) at initialization `(rot_init, trans_init, log_scale_init)` so observations in $M_0$ never drop out of the objective during optimization.
   - Flagged any candidate with $q_{j,z} \le z_{\min}$ or $q_{i,z} \le z_{\min}$ on $M_0$ as `cheirality_viol`, added a hard $10^6 (1 + \Delta z)$ penalty in `_eval_residuals`, rejected any LM candidate step with `cand_viol.any()`, and required `(not final_viol.any())` and `accepted_steps > 0` for commitment.
   - Reused evaluated residuals/weights across accepted steps and cached normal equations across rejected damping steps (`test_ttba_recovers_rotation_and_scale_under_25ms` completes in 90 ms total across all 3 suites).

3. **BLOCKER 3 — Cross-camera `temporal_patch=2` isolation before ViT patch embedding (`epi_adapter.py:157-244`)**
   - Added `pack_views_for_temporal_patch2(views, viewset)` and `EpiAdapter.pack_pre_vit_views(images, viewset, temporal_patch_embed=...)`, which pack `[B, N, ...]` inputs into `[B, N, 2, ...]` temporal pairs before 2-frame 3D conv / patch embedding.
   - Adjacent views share a 2-frame pair only when `viewset.temporal_merge_allowed` is True; distinct cameras or non-video views self-duplicate `[v_i, v_i]` so 2-frame `Conv3d` patch embedding has zero cross-camera bleeding.

4. **BLOCKER 4 — Padded-view and masked-NaN loss contamination (`losses.py:47-56, 102-145, 150-274, 287-305`)**
   - In `DecoupledDepthLoss`, intersected `valid_mask` with `torch.isfinite(depth_gt) & (depth_gt > 1e-4)` and `view_mask`, and sanitized `depth_gt` with `torch.where` **before** `torch.log`, preventing masked-out `NaN` targets from producing `0 * NaN = NaN`.
   - In `PoseAnd4DLoss` and `SpatialV2CompositeLoss`, masked and normalized `pmap`, `reversal`, `flow_sparsity`, `flow`, `rigidity`, `ray`, `fov`, `gravity`, and `pose` strictly over valid support (`view_mask`, `flow_valid`, `pmap_valid`, and `torch.isfinite`), sanitizing masked entries before arithmetic.

5. **BLOCKER 5 — Unlocked-scale `log_gamma_scene` gradient leak via composite pointmap loss (`losses.py:225-245`)**
   - Gated absolute metric pointmap loss by `metric_scale_locked` (`locked[:, :, None, None]`) and detached unlocked predictions before residual evaluation so uncalibrated samples (`metric_scale_locked == 0`) produce **strictly `0.0`** gradient on `log_gamma_bias` and `scene_scale_head` through the full `SpatialV2CompositeLoss`.

6. **BLOCKER 6 — Sign loss and `NaN` gradients in $\pi$-rotation $SO(3)$ logarithm (`geo_heads.py:43-72`)**
   - Replaced the diagonal `sqrt` axis extraction in `so3_log` with the column $B_{:, k^*}$ of $B = \frac{1}{2}(R + R^T) - (\cos\theta) I$ at $k^* = \arg\max_k R_{kk}$ (where $\|B_{:, k^*}\| \ge 1/\sqrt{3}$, avoiding `sqrt(0)` singularities while preserving exact relative signs of all off-diagonal components), aligned with `vee` and equipped with a zero-forward straight-through radial tangent `-(vee - vee.detach())` for finite, non-zero geodesic gradients at $\theta = \pi$.

7. **BLOCKER 7 — `use_delta_geo_bias` and `use_metric_3d_rope` defaults (`config.py:139-140`)**
   - Set `use_delta_geo_bias: bool = False` and `use_metric_3d_rope: bool = False` by default on `SpatialV2Config`.

8. **WARNING 8 — Degenerate 6D rotation, zero gravity, and Plücker orthogonality (`geo_heads.py:98-119, 183-204, 410-427`)**
   - Added straight-through canonical basis fallbacks in `rotation_6d_to_matrix` for zero or collinear 6D inputs (`det(R) = +1`, $R^T R = I$) and in `compute_gravity_leveled_poses` / `GeoPoseHead` for zero gravity vectors.
   - Enforced Plücker orthogonality in `GeoPoseHead`: `p_mom = p_mom - (p_dir * p_mom).sum(dim=-1, keepdim=True) * p_dir`.

9. **WARNING 9 — Static-flow sparsity weighting & per-pixel flow validity (`losses.py:249-280`)**
   - Weighted `flow_sparsity` by `depth_out.p_stat` (penalizing nonzero object motion on static pixels rather than dynamic pixels) and normalized over valid support only.
   - Added optional per-pixel / per-horizon `flow_valid` masking to `flow`, `flow_sparsity`, and `reversal` losses.

10. **WARNING 10 — `Metric3DRoPE` & `PluckerGeoInjector` extreme-coordinate & large-origin stability (`metric_3d_rope.py:64-86, 118-137`)**
    - Sanitized non-finite coordinates, subtracted the detached per-sample visual centroid in `float64` to eliminate large-origin phase precision loss ($10^3..10^6$ shifts), and clamped coordinates in `float32` to `[-max_coord_abs, max_coord_abs]` (`1e4`) so `bfloat16` `3e38` inputs never overflow or produce `NaN`.

11. **WARNING 11 — Stream ID collision above 16 cameras (`epi_adapter.py:124-154`)**
    - Replaced `stream_ids.clamp(0, 15)` table lookup in `StreamMetadataEncoder` with deterministic multi-frequency sinusoidal/Fourier stream embeddings plus a zero-init residual MLP (`stream_mlp`), supporting arbitrary $>16$ stream IDs (tested at 48 streams) with zero collision.

## Verification

```
PYTHONPATH=/scratch/jjyeung/orch_home_distill:/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages \
  /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B -m pytest tests/test_spatial_v2.py -v
============================== 9 passed in 1.90s ===============================
```
