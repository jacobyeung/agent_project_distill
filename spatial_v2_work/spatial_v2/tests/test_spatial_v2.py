"""Comprehensive unit tests for Spatial-V2 clean-sheet modules."""

from __future__ import annotations

import math
import time

import torch
import torch.nn as nn

from spatial_v2 import (
    DA3SmallStemAdapter, DecoupledDepthLoss, DeltaGeoBias, EpiAdapter, FlowExpert,
    GeoDepthHead, GeoDepthOutput, GeoPoseHead, Metric3DRoPE, PluckerGeoInjector, QWEN35_9B_DELTANET_LAYERS,
    QWEN35_9B_FULL_ATTN_LAYERS, SpatialV2CompositeLoss, SpatialV2Config, TTBA, TTBAConfig,
    apply_rope_phases, build_intrinsics_matrix, build_viewset_batch,
    compute_gravity_leveled_poses, compute_plucker_rays, compute_ray_yaw_disagreement_deg,
    deltanet_3d_step, matrix_to_rotation_6d, pack_views_for_temporal_patch2,
    prevent_temporal_patch_bleeding, project_points, rotation_6d_to_matrix, se3_exp, se3_log,
    so3_exp, so3_log, unproject_depth,
)


def _seed(s: int = 42) -> None:
    torch.manual_seed(s)


def test_config_qwen35_topology_and_viewset_packing() -> None:
    cfg16 = SpatialV2Config.qwen35_9b(l_geo=16, stem_type="epi_adapter", viewset_mode="video")
    assert cfg16.num_layers == 32
    assert len(QWEN35_9B_FULL_ATTN_LAYERS) == 8 and len(QWEN35_9B_DELTANET_LAYERS) == 24
    assert cfg16.lower_full_attn_layers == (4, 8, 12, 16)
    assert cfg16.upper_full_attn_layers == (20, 24, 28, 32)
    assert len(cfg16.upper_deltanet_layers) == 12

    cfg12 = SpatialV2Config.qwen35_9b(l_geo=12, stem_type="da3_small", viewset_mode="robot_wrist_exo")
    assert cfg12.lower_full_attn_layers == (4, 8, 12)
    assert cfg12.upper_full_attn_layers == (16, 20, 24, 28, 32)
    assert cfg12.stem_type == "da3_small"

    for n_views in (2, 5, 16, 48):
        vb_vid = build_viewset_batch("video", 2, n_views)
        assert vb_vid.temporal_merge_allowed.all() and torch.equal(vb_vid.mrope_time_ids[0], torch.arange(n_views))
        vb_mv = build_viewset_batch("multiview", 2, n_views)
        assert (not vb_mv.temporal_merge_allowed.any()) and (vb_mv.mrope_time_ids == 0).all()
        assert not build_viewset_batch("robot_wrist_exo", 2, n_views).temporal_merge_allowed.any()

    vis = torch.randn(2, 4, 6, 16)
    out_rob, iso_rob = prevent_temporal_patch_bleeding(vis, build_viewset_batch("robot_wrist_exo", 2, 4))
    assert iso_rob.all() and torch.allclose(out_rob, vis, atol=0.0)
    out_vid, iso_vid = prevent_temporal_patch_bleeding(vis, build_viewset_batch("video", 2, 4))
    assert (not iso_vid.any()) and torch.allclose(out_vid[:, 0], 0.5 * (vis[:, 0] + vis[:, 1]), atol=1e-6)


def test_zero_init_exact_identity() -> None:
    _seed(1)
    cfg = SpatialV2Config.tiny()
    bsz, n_views, hm, wm, d_lm = 2, 4, 4, 5, cfg.hidden_size

    # 1. EpiAdapter & DA3-Small stem zero-init identity
    epi = EpiAdapter(cfg.epi, lm_hidden_size=d_lm)
    taps = [torch.randn(bsz, n_views, 2 * hm, 2 * wm, cfg.epi.vit_hidden_size) for _ in cfg.epi.vit_tap_layers]
    merged_vis, cam_tok = torch.randn(bsz, n_views, hm * wm, d_lm), torch.randn(bsz, n_views, d_lm)
    vb = build_viewset_batch("video", bsz, n_views)
    vis_out, cam_out, epi_out = epi.apply_residual(merged_vis, cam_tok, taps, viewset=vb)
    assert (vis_out - merged_vis).abs().max().item() < 1e-6
    assert (cam_out - cam_tok).abs().max().item() < 1e-6
    assert epi_out.fine_geo.shape == (bsz, n_views, 2 * hm, 2 * wm, cfg.epi.fine_dim)

    da3_out = DA3SmallStemAdapter(cfg.epi, d_lm)(torch.randn(bsz, n_views, hm, wm, cfg.epi.da3_small_dim), vb)
    assert da3_out.patch_delta.abs().max().item() < 1e-6 and da3_out.cam_delta.abs().max().item() < 1e-6

    # 2. Metric 3D-RoPE zero-init exact identity
    rope3d = Metric3DRoPE(cfg.rope3d)
    seq_len = 24
    q = torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim)
    k = torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim)
    theta_m = torch.randn(bsz, seq_len, cfg.rope3d.rotary_dim // 2)
    coords = torch.randn(bsz, seq_len, 3) * 5.0
    is_vis = torch.ones(bsz, seq_len, dtype=torch.bool)
    q_b, k_b = apply_rope_phases(q, k, theta_m.unsqueeze(1))
    q_g, k_g = rope3d(q, k, theta_m, coords, is_visual_mask=is_vis)
    assert (q_g - q_b).abs().max().item() < 1e-6 and (k_g - k_b).abs().max().item() < 1e-6

    # 3. PluckerGeoInjector & DeltaGeoBias zero-init exact identity
    h_lm = torch.randn(bsz, seq_len, d_lm)
    h_out = PluckerGeoInjector(cfg.rope3d, d_lm)(
        h_lm, coords, torch.randn(bsz, seq_len, 6), torch.randn(bsz, seq_len),
        torch.rand(bsz, seq_len), torch.rand(bsz, seq_len), is_visual_mask=is_vis,
    )
    assert (h_out - h_lm).abs().max().item() < 1e-6

    dgb = DeltaGeoBias(cfg.delta_bias)
    log_a = -0.1 * torch.ones(bsz, seq_len, cfg.delta_bias.num_heads)
    logit_b = torch.zeros(bsz, seq_len, cfg.delta_bias.num_heads)
    la_out, lb_out = dgb(log_a, logit_b, torch.randn(bsz, seq_len, 4), is_visual_mask=is_vis)
    assert (la_out - log_a).abs().max().item() < 1e-6 and (lb_out - logit_b).abs().max().item() < 1e-6

    st = torch.randn(bsz, cfg.delta_bias.num_heads, 8, 8)
    kk, vv, qq = [torch.randn(bsz, cfg.delta_bias.num_heads, 8) for _ in range(3)]
    o1, s1 = deltanet_3d_step(st, kk, vv, qq, log_a[:, 0], logit_b[:, 0])
    o2, s2 = deltanet_3d_step(st, kk, vv, qq, la_out[:, 0], lb_out[:, 0])
    assert (o1 - o2).abs().max().item() < 1e-6 and (s1 - s2).abs().max().item() < 1e-6

    # 4. FlowExpert zero-init residual gates (cross-attention & T_goal)
    expert = FlowExpert(cfg.flow_expert, d_lm).eval()
    taps_a = {l: torch.randn(bsz, 10, d_lm) for l in (12, 16, 24)}
    taps_b = {l: torch.randn(bsz, 10, d_lm) * 5.0 for l in (12, 16, 24)}
    proprio = torch.randn(bsz, cfg.flow_expert.proprio_dim)
    noisy = torch.randn(bsz, cfg.flow_expert.chunk_size, cfg.flow_expert.action_dim)
    flow_t = torch.full((bsz,), 0.5)
    t_goal = torch.eye(4).unsqueeze(0).expand(bsz, -1, -1).clone()
    t_goal[:, :3, 3] = torch.randn(bsz, 3)
    v_a = expert.predict_velocity(noisy, flow_t, proprio, expert.precompute_memory(taps_a), t_goal=None)
    v_b = expert.predict_velocity(noisy, flow_t, proprio, expert.precompute_memory(taps_b), t_goal=t_goal)
    assert (v_a - v_b).abs().max().item() < 1e-6


def test_epi_adapter_permutation_invariance() -> None:
    _seed(2)
    cfg = SpatialV2Config.tiny(viewset_mode="multiview")
    epi = EpiAdapter(cfg.epi, lm_hidden_size=cfg.hidden_size).eval()
    nn.init.normal_(epi.out_patch_proj.weight, std=0.05)
    nn.init.normal_(epi.out_cam_proj.weight, std=0.05)

    bsz, n_views, hm, wm = 2, 5, 4, 4
    taps = [torch.randn(bsz, n_views, 2 * hm, 2 * wm, cfg.epi.vit_hidden_size) for _ in cfg.epi.vit_tap_layers]
    vb = build_viewset_batch("multiview", bsz, n_views, stream_ids=[0] * n_views, timestamps=[0.0] * n_views)
    perm = torch.tensor([3, 0, 4, 1, 2])
    out_orig = epi(taps, viewset=vb)
    out_perm = epi([t[:, perm] for t in taps], viewset=vb)
    assert (out_orig.patch_delta[:, perm] - out_perm.patch_delta).abs().max().item() < 1e-5
    assert (out_orig.cam_delta[:, perm] - out_perm.cam_delta).abs().max().item() < 1e-5


def test_se3_invariance_and_unprojection_roundtrip_including_mujoco_mirror() -> None:
    _seed(3)
    rot = rotation_6d_to_matrix(torch.randn(4, 5, 6))
    eye = torch.eye(3).expand_as(rot)
    assert (rot @ rot.transpose(-1, -2) - eye).abs().max().item() < 1e-5
    assert (torch.linalg.det(rot) - 1.0).abs().max().item() < 1e-5
    assert (rot - rotation_6d_to_matrix(matrix_to_rotation_6d(rot))).abs().max().item() < 1e-5

    xi = torch.tensor([[1e-7, -2e-7, 1e-7, 0.1, -0.2, 0.3], [0.3, -0.5, 0.4, 1.2, -0.8, 0.5], [1.4, -1.2, 0.9, -0.4, 2.0, -1.1]])
    assert (xi - se3_log(*se3_exp(xi))).abs().max().item() < 1e-4

    bsz, n_views, h, w = 2, 4, 8, 10
    r_gt = so3_exp(torch.randn(bsz, n_views, 3) * 0.4)
    t_gt = torch.randn(bsz, n_views, 3) * 1.5
    depth_gt = torch.rand(bsz, n_views, h, w) * 3.0 + 0.5
    log_fx, log_fy = torch.zeros(bsz, n_views), torch.zeros(bsz, n_views)
    ev, eu = torch.meshgrid(torch.arange(h, dtype=torch.float32) + 0.5, torch.arange(w, dtype=torch.float32) + 0.5, indexing="ij")

    for mirror_x in (False, True):
        K = build_intrinsics_matrix(log_fx, log_fy, float(w), float(h), mirror_x=mirror_x)
        assert (K[..., 0, 0] < 0).all() if mirror_x else (K[..., 0, 0] > 0).all()
        u_rt, v_rt, z_rt = project_points(unproject_depth(depth_gt, K, r_gt, t_gt), K, r_gt, t_gt)
        assert (u_rt - eu).abs().max().item() < 1e-4 and (v_rt - ev).abs().max().item() < 1e-4
        assert (z_rt - depth_gt).abs().max().item() < 1e-4

    # Global SE(3) invariance of canonical gravity-leveled frame + unprojection (with fx < 0)
    g_world = torch.tensor([0.0, 0.0, 1.0]).view(1, 3).expand(bsz, 3)
    g_cam0 = (r_gt[:, 0] @ g_world.unsqueeze(-1)).squeeze(-1)
    q_rand, p_rand = so3_exp(torch.randn(bsz, 1, 3) * 1.2), torch.randn(bsz, 1, 3) * 4.0
    r_tr = r_gt @ q_rand.transpose(-1, -2)
    t_tr = t_gt - (r_tr @ p_rand.unsqueeze(-1)).squeeze(-1)
    r_c1, t_c1 = compute_gravity_leveled_poses(r_gt, t_gt, g_cam0)
    r_c2, t_c2 = compute_gravity_leveled_poses(r_tr, t_tr, g_cam0)
    assert (r_c1 - r_c2).abs().max().item() < 1e-5 and (t_c1 - t_c2).abs().max().item() < 1e-5
    o0 = -(r_c1[:, 0].transpose(-1, -2) @ t_c1[:, 0].unsqueeze(-1)).squeeze(-1)
    assert o0.abs().max().item() < 1e-5
    assert ((r_c1[:, 0].transpose(-1, -2) @ g_cam0.unsqueeze(-1)).squeeze(-1) - g_world).abs().max().item() < 1e-5
    K_m = build_intrinsics_matrix(log_fx, log_fy, float(w), float(h), mirror_x=True)
    assert (unproject_depth(depth_gt, K_m, r_c1, t_c1) - unproject_depth(depth_gt, K_m, r_c2, t_c2)).abs().max().item() < 1e-5

    cfg = SpatialV2Config.tiny()
    d_head = GeoDepthHead(cfg.geo_heads, cfg.hidden_size, cfg.epi.fine_dim)
    p_head = GeoPoseHead(cfg.geo_heads, cfg.hidden_size)
    for nv in (2, 5):
        h_vis, h_cam = torch.randn(bsz, nv, 4, 5, cfg.hidden_size), torch.randn(bsz, nv, cfg.hidden_size)
        p_out = p_head(h_cam, h_vis)
        d_out = d_head(h_vis, torch.randn(bsz, nv, 8, 10, cfg.epi.fine_dim), p_out.log_fx_w, p_out.log_fy_h)
        assert (d_out.depth > 0).all() and (d_out.p_stat > 0).all() and (d_out.p_stat < 1).all()
        assert (p_out.gravity.norm(dim=-1) - 1.0).abs().max().item() < 1e-5


def test_metric_3d_rope_relative_distance_property() -> None:
    _seed(4)
    cfg = SpatialV2Config.tiny()
    rope = Metric3DRoPE(cfg.rope3d)
    with torch.no_grad():
        rope.beta_h.copy_(torch.randn_like(rope.beta_h) * 0.5 + 0.5)

    bsz, n_h, seq_len, d_h = 2, cfg.rope3d.num_heads, 16, cfg.rope3d.head_dim
    q, k = torch.randn(bsz, n_h, seq_len, d_h), torch.randn(bsz, n_h, seq_len, d_h)
    th0 = torch.zeros(bsz, seq_len, cfg.rope3d.rotary_dim // 2)
    coords = torch.randn(bsz, seq_len, 3) * 2.0
    is_vis = torch.ones(bsz, seq_len, dtype=torch.bool)
    is_vis[:, -4:] = False

    delta = torch.tensor([3.7, -5.2, 2.1]).view(1, 1, 3)
    q1, k1 = rope(q, k, th0, coords, is_visual_mask=is_vis)
    q2, k2 = rope(q, k, th0, coords + delta, is_visual_mask=is_vis)
    l1 = torch.matmul(q1[:, :, :-4, :], k1[:, :, :-4, :].transpose(-1, -2))
    l2 = torch.matmul(q2[:, :, :-4, :], k2[:, :, :-4, :].transpose(-1, -2))
    assert (l1 - l2).abs().max().item() < 1e-4
    assert (q1[:, :, -4:, :] - q2[:, :, -4:, :]).abs().max().item() < 1e-6

    q3, k3 = rope(q, k, th0, coords * 2.0, is_visual_mask=is_vis)
    assert (l1 - torch.matmul(q3[:, :, :-4, :], k3[:, :, :-4, :].transpose(-1, -2))).abs().max().item() > 0.1


def _build_synthetic_ba(n_views: int = 6, n_pts: int = 90, mirror_x: bool = False, global_drift: bool = False):
    K = build_intrinsics_matrix(
        torch.full((n_views,), math.log(0.9)), torch.full((n_views,), math.log(1.2)), 320.0, 240.0, mirror_x=mirror_x
    )
    rots_gt, trans_gt = [], []
    for v in range(n_views):
        r_v = so3_exp(torch.tensor([0.03 * math.sin(v), (v - n_views / 2.0) * 0.12, 0.02 * math.cos(v)]))
        rots_gt.append(r_v)
        trans_gt.append(-(r_v @ torch.tensor([0.55 * v, 0.15 * math.sin(v), 0.15 * v])))
    r_gt, t_gt = torch.stack(rots_gt), torch.stack(trans_gt)
    pts = torch.stack([torch.rand(n_pts) * 3.0 - 0.3, torch.rand(n_pts) * 2.0 - 1.0, torch.rand(n_pts) * 2.5 + 2.5], dim=-1)

    edges = [(i, i + 1) for i in range(n_views - 1)] + [(0, i) for i in range(2, n_views)]
    bufs = [[] for _ in range(7)]
    for i, j in edges:
        ui, vi, zi = project_points(pts, K[i], r_gt[i], t_gt[i])
        uj, vj, zj = project_points(pts, K[j], r_gt[j], t_gt[j])
        idx = ((zi > 0.5) & (zj > 0.5)).nonzero(as_tuple=False).squeeze(-1)
        m = idx.numel()
        if m == 0:
            continue
        uv_i, uv_j = torch.stack([ui[idx], vi[idx]], dim=-1), torch.stack([uj[idx], vj[idx]], dim=-1)
        p_s = torch.full((m,), 0.95)
        n_dyn = max(1, int(0.15 * m))
        uv_j[:n_dyn] += torch.randn(n_dyn, 2) * 35.0
        p_s[:n_dyn] = 0.02
        for b_l, val in zip(bufs, [torch.full((m,), i, dtype=torch.long), torch.full((m,), j, dtype=torch.long), uv_i, uv_j, zi[idx], zj[idx], p_s]):
            b_l.append(val)
    src, dst, uvs, uvd, ds, dd, p_stat = [torch.cat(b) for b in bufs]

    r_init, t_init = r_gt.clone(), t_gt.clone()
    for v in range(1, n_views):
        r_init[v] = so3_exp(nn.functional.normalize(torch.randn(3), dim=0) * math.radians(10.0)) @ r_gt[v]
        if not global_drift:
            t_init[v] = t_gt[v] + torch.randn(3) * 0.08
    s_err = torch.full((n_views,), 1.94) if global_drift else torch.tensor([1.0] + [1.94] * (n_views - 1))
    return K, r_gt, t_gt, r_init, t_init, src, dst, uvs, uvd, ds * s_err[src], dd * s_err[dst], p_stat, s_err


def test_ttba_recovers_rotation_and_scale_under_25ms() -> None:
    _seed(5)
    ttba = TTBA(TTBAConfig(num_steps=5))
    for label, g_drift, mirror_x in [
        ("rel_1.94x_fx_pos", False, False),
        ("global_1.94x_metric_anchor", True, False),
        ("rel_1.94x_mujoco_mirror", False, True),
    ]:
        K, r_gt, t_gt, r_init, t_init, src, dst, uvs, uvd, ds, dd, p_stat, s_err = _build_synthetic_ba(
            mirror_x=mirror_x, global_drift=g_drift
        )
        if label == "rel_1.94x_fx_pos":
            _ = ttba(r_init, t_init, K, src, dst, uvs, uvd, ds, dd, p_stat)
        out = ttba(
            r_init, t_init, K, src, dst, uvs, uvd, ds, dd, p_stat,
            trans_prior=t_gt if g_drift else None, trans_prior_weight=50.0 if g_drift else 0.0,
            fix_first_scale=not g_drift,
        )
        r_b = so3_log(r_gt[1:].transpose(-1, -2) @ r_init[1:]).norm(dim=-1).mean().item()
        r_a = so3_log(r_gt[1:].transpose(-1, -2) @ out.rot[1:]).norm(dim=-1).mean().item()
        target_ls = -torch.log(s_err)
        sl = slice(0, None) if g_drift else slice(1, None)
        s_rec = 1.0 - (out.log_scale[sl] - target_ls[sl]).abs().mean().item() / target_ls[sl].abs().mean().item()
        assert 1.0 - r_a / r_b > 0.70 and s_rec > 0.70, f"{label}: rot_rec={1-r_a/r_b:.3f}, scale_rec={s_rec:.3f}"
        assert out.diagnostics.committed and out.diagnostics.reproj_err_after < out.diagnostics.reproj_err_before
        assert out.diagnostics.parallax_deg > 1.0 and math.isfinite(out.diagnostics.pose_cond)
        assert out.diagnostics.elapsed_ms < 25.0, f"{label}: {out.diagnostics.elapsed_ms:.2f} ms"

    ray_a = compute_plucker_rays(K[:2], r_gt[:2], t_gt[:2], 4, 4)
    yaw_d = compute_ray_yaw_disagreement_deg(ray_a, ray_a)
    assert yaw_d < 1e-3
    out_skip = ttba(r_init, t_init, K, src, dst, uvs, uvd, ds, dd, p_stat, ray_yaw_disagreement_deg=yaw_d)
    assert (not out_skip.diagnostics.triggered) and (not out_skip.diagnostics.committed)


def test_losses_and_exact_finite_gradients_all_viewset_modes() -> None:
    _seed(6)
    cfg = SpatialV2Config.tiny()
    bsz, n_views, hm, wm, d_lm = 2, 4, 4, 4, cfg.hidden_size

    epi = EpiAdapter(cfg.epi, d_lm)
    d_head = GeoDepthHead(cfg.geo_heads, d_lm, cfg.epi.fine_dim)
    p_head = GeoPoseHead(cfg.geo_heads, d_lm)
    rope3d = Metric3DRoPE(cfg.rope3d)
    injector = PluckerGeoInjector(cfg.rope3d, d_lm)
    dgb = DeltaGeoBias(cfg.delta_bias)
    comp_loss = SpatialV2CompositeLoss(cfg.sf2, cfg.loss_weights, d_lm)
    expert = FlowExpert(cfg.flow_expert, d_lm)

    # 1. Uncalibrated clips (metric_scale_locked=0) give EXACT zero grad on log_gamma_bias
    dl = DecoupledDepthLoss()
    hv = torch.randn(bsz, n_views, hm, wm, d_lm, requires_grad=True)
    fg = torch.randn(bsz, n_views, 2 * hm, 2 * wm, cfg.epi.fine_dim, requires_grad=True)
    d_gt = torch.rand(bsz, n_views, 2 * hm, 2 * wm) * 3.0 + 0.5
    d_val = torch.ones_like(d_gt, dtype=torch.bool)
    d_head.zero_grad()
    dl(d_head(hv, fg), d_gt, d_val, torch.zeros(bsz))[0].backward()
    assert d_head.log_gamma_bias.grad is None or d_head.log_gamma_bias.grad.abs().max().item() == 0.0
    assert d_head.shape_head.weight.grad is not None and d_head.shape_head.weight.grad.abs().sum().item() > 0.0

    d_head.zero_grad()
    dl(d_head(hv.detach(), fg.detach()), d_gt, d_val, torch.ones(bsz))[0].backward()
    assert d_head.log_gamma_bias.grad is not None and d_head.log_gamma_bias.grad.abs().sum().item() > 0.0

    # 2. Full end-to-end backward across all 3 ViewSet-Unified modes
    for mode in ("video", "multiview", "robot_wrist_exo"):
        for mod in (epi, d_head, p_head, rope3d, injector, dgb, comp_loss, expert):
            mod.zero_grad()
        vb = build_viewset_batch(mode, bsz, n_views)
        vit_taps = [torch.randn(bsz, n_views, 2 * hm, 2 * wm, cfg.epi.vit_hidden_size, requires_grad=True) for _ in cfg.epi.vit_tap_layers]
        vis_in, cam_in, epi_out = epi.apply_residual(
            torch.randn(bsz, n_views, hm * wm, d_lm, requires_grad=True),
            torch.randn(bsz, n_views, d_lm, requires_grad=True), vit_taps, viewset=vb,
        )
        h_vis = vis_in.view(bsz, n_views, hm, wm, d_lm)
        p_out = p_head(cam_in, h_vis, view_mask=vb.view_mask)
        d_out = d_head(h_vis, epi_out.fine_geo, p_out.log_fx_w, p_out.log_fy_h, view_mask=vb.view_mask)

        K_p = build_intrinsics_matrix(p_out.log_fx_w, p_out.log_fy_h, float(wm), float(hm))
        d_low = nn.functional.interpolate(
            d_out.depth.reshape(bsz * n_views, 1, 2 * hm, 2 * wm), size=(hm, wm), mode="bilinear", align_corners=False
        ).reshape(bsz, n_views, hm, wm)
        pts_w = unproject_depth(d_low, K_p, p_out.rot_canon, p_out.trans_canon)
        seq_len = n_views * hm * wm
        pts_flat = pts_w.reshape(bsz, seq_len, 3)

        h_geo = injector(
            vis_in.reshape(bsz, seq_len, d_lm), pts_flat, p_out.plucker_pred.reshape(bsz, seq_len, 6),
            torch.log(d_low.clamp_min(1e-4)).reshape(bsz, seq_len),
            torch.exp(-0.5 * d_out.log_var_depth[:, :, ::2, ::2]).reshape(bsz, seq_len),
            d_out.p_stat[:, :, ::2, ::2].reshape(bsz, seq_len),
        )
        q_r, k_r = rope3d(
            torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim),
            torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim),
            torch.zeros(bsz, seq_len, cfg.rope3d.rotary_dim // 2), pts_flat,
        )
        la, lb = dgb(
            torch.zeros(bsz, seq_len, cfg.delta_bias.num_heads),
            torch.zeros(bsz, seq_len, cfg.delta_bias.num_heads), torch.randn(bsz, seq_len, 4),
        )

        targets = {
            "depth_gt": torch.rand(bsz, n_views, 2 * hm, 2 * wm) * 3.0 + 0.5,
            "depth_valid": torch.ones(bsz, n_views, 2 * hm, 2 * wm, dtype=torch.bool),
            "metric_scale_locked": torch.tensor([1.0, 0.0]),
            "rot_gt": so3_exp(torch.randn(bsz, n_views, 3) * 0.2),
            "trans_gt": torch.randn(bsz, n_views, 3),
            "gravity_gt": torch.tensor([0.0, 0.0, 1.0]).view(1, 1, 3).expand(bsz, n_views, 3),
            "log_fx_w_gt": torch.zeros(bsz, n_views),
            "log_fy_h_gt": torch.zeros(bsz, n_views),
            "plucker_gt": torch.randn(bsz, n_views, hm, wm, 6),
            "pmap_gt": torch.randn_like(pts_w),
            "y_stat_gt": (torch.rand(bsz, n_views, 2 * hm, 2 * wm) > 0.2).float(),
            "delta_p_gt": torch.randn(bsz, n_views, 2 * hm, 2 * wm, len(cfg.geo_heads.flow_horizons), 3) * 0.1,
            "delta_p_rev": -d_out.delta_p_obj.detach(),
        }
        taps_lm = {16: h_geo.reshape(bsz, n_views, hm * wm, d_lm), 24: h_geo.reshape(bsz, n_views, hm * wm, d_lm)}
        total_loss, metrics = comp_loss(
            taps_lm, torch.randn(bsz, n_views, hm * wm, cfg.sf2.teacher_dim), d_out, p_out, targets,
            pmap_pred=pts_w, view_mask=vb.view_mask,
        )
        (total_loss + 0.01 * (q_r.pow(2).mean() + k_r.pow(2).mean() + la.pow(2).mean() + lb.pow(2).mean())).backward()
        assert torch.isfinite(total_loss) and all(torch.isfinite(v) for v in metrics.values())
        for mod in (epi, d_head, p_head, rope3d, injector, dgb, comp_loss):
            for p in mod.parameters():
                if p.grad is not None:
                    assert torch.isfinite(p.grad).all()

    # 3. FlowExpert detach_backbone isolation vs propagation
    taps_d = {12: torch.randn(bsz, 8, d_lm, requires_grad=True), 16: torch.randn(bsz, 8, d_lm, requires_grad=True)}
    geo_t = torch.randn(bsz, 8, cfg.flow_expert.geo_token_dim, requires_grad=True)
    prop = torch.randn(bsz, cfg.flow_expert.proprio_dim)
    acts = torch.randn(bsz, cfg.flow_expert.chunk_size, cfg.flow_expert.action_dim)
    tg = torch.eye(4).unsqueeze(0).expand(bsz, -1, -1)

    expert.zero_grad()
    loss_d = expert.compute_loss(acts, prop, taps_d, geo_t, tg, detach_backbone=True)
    loss_d.backward()
    assert torch.isfinite(loss_d) and taps_d[12].grad is None and geo_t.grad is None

    with torch.no_grad():
        for blk in expert.blocks:
            blk.ca_gate.fill_(0.1)
    expert.zero_grad()
    expert.compute_loss(acts, prop, taps_d, geo_t, tg, detach_backbone=False).backward()
    assert taps_d[12].grad is not None and taps_d[12].grad.abs().sum().item() > 0.0 and torch.isfinite(taps_d[12].grad).all()
    assert geo_t.grad is not None and torch.isfinite(geo_t.grad).all()


def test_flow_expert_ode_sampling_and_latency() -> None:
    _seed(7)
    cfg = SpatialV2Config.tiny()
    expert = FlowExpert(cfg.flow_expert, cfg.hidden_size).eval()
    bsz = 4
    taps = {l: torch.randn(bsz, 32, cfg.hidden_size) for l in (12, 16, 24)}
    geo_tok = torch.randn(bsz, 32, cfg.flow_expert.geo_token_dim)
    prop = torch.randn(bsz, cfg.flow_expert.proprio_dim)
    tg = torch.eye(4).unsqueeze(0).expand(bsz, -1, -1)

    _ = expert.sample_actions(prop, taps, geo_tok, tg, num_steps=10)
    t0 = time.perf_counter()
    for _ in range(5):
        out = expert.sample_actions(prop, taps, geo_tok, tg, num_steps=10)
    ms = (time.perf_counter() - t0) * 1000.0 / 5
    assert out.shape == (bsz, cfg.flow_expert.chunk_size, cfg.flow_expert.action_dim) and torch.isfinite(out).all()
    assert ms < 200.0, f"Tiny CPU FlowExpert too slow: {ms:.2f} ms"


def test_codex_regressions_all_11_findings() -> None:
    _seed(11)
    cfg = SpatialV2Config.tiny()
    bsz, n_views, hm, wm, d_lm = 2, 4, 4, 4, cfg.hidden_size

    # Finding 7 (BLOCKER): use_delta_geo_bias and use_metric_3d_rope default to False
    default_cfg = SpatialV2Config()
    assert default_cfg.use_delta_geo_bias is False
    assert default_cfg.use_metric_3d_rope is False

    # Finding 1 (BLOCKER): Subgoal conditioning has strictly nonzero gradient on backward()
    expert = FlowExpert(cfg.flow_expert, d_lm)
    taps = {l: torch.randn(bsz, 8, d_lm) for l in (12, 16, 24)}
    prop = torch.randn(bsz, cfg.flow_expert.proprio_dim)
    acts = torch.randn(bsz, cfg.flow_expert.chunk_size, cfg.flow_expert.action_dim)
    t_goal = torch.eye(4).unsqueeze(0).expand(bsz, -1, -1).clone()
    t_goal[:, :3, 3] = torch.tensor([[0.4, -0.2, 0.7], [-0.5, 0.3, 0.2]])
    expert.zero_grad()
    loss_g0 = expert.compute_loss(acts, prop, taps, t_goal=t_goal)
    loss_g0.backward()
    assert expert.subgoal_gate.grad is not None and expert.subgoal_gate.grad.abs().max().item() > 0.0
    # After 1 update step on subgoal_gate, subgoal_proj also receives strictly nonzero gradient
    with torch.no_grad():
        expert.subgoal_gate.add_(-0.1 * expert.subgoal_gate.grad)
    expert.zero_grad()
    expert.compute_loss(acts, prop, taps, t_goal=t_goal).backward()
    proj_grad_norm = sum(p.grad.abs().sum().item() for p in expert.subgoal_proj.parameters() if p.grad is not None)
    assert proj_grad_norm > 0.0

    # Finding 2 (BLOCKER): TT-BA cheirality rejection on behind-camera reproduction + noisy monocular test
    ttba = TTBA(TTBAConfig(num_steps=5))
    K2 = build_intrinsics_matrix(torch.zeros(2), torch.zeros(2), 320.0, 240.0)
    r_id = torch.eye(3).unsqueeze(0).expand(2, 3, 3).clone()
    t_zero = torch.zeros(2, 3)
    src_1 = torch.tensor([0], dtype=torch.long)
    dst_1 = torch.tensor([1], dtype=torch.long)
    uv_c = torch.tensor([[160.0, 120.0]])
    d_s1, d_d1 = torch.tensor([1.0]), torch.tensor([0.06])
    p_s1 = torch.tensor([1.0])
    out_cheir = ttba(r_id, t_zero, K2, src_1, dst_1, uv_c, uv_c, d_s1, d_d1, p_s1)
    # Compute destination Z under returned pose/scale
    _, _, cost_c, _, q_jc, _, viol_c = ttba._eval_residuals(
        out_cheir.rot, out_cheir.trans, out_cheir.log_scale, K2, src_1, dst_1, uv_c, uv_c, d_s1, d_d1, p_s1
    )
    assert (not viol_c.any()) and (q_jc[:, 2] > ttba.cfg.min_depth).all() and float(cost_c.item()) >= 0.0

    # Noisy monocular shape + pixel noise TT-BA recovery without oracle outlier weights
    K_n, r_gt, t_gt, r_init, t_init, src, dst, uvs, uvd, ds, dd, _, s_err = _build_synthetic_ba(n_views=5, n_pts=80)
    ds_noisy = (ds * (1.0 + 0.03 * torch.randn_like(ds))).clamp_min(0.2)
    dd_noisy = (dd * (1.0 + 0.03 * torch.randn_like(dd))).clamp_min(0.2)
    uvd_noisy = uvd + 0.5 * torch.randn_like(uvd)
    p_uniform = torch.full_like(ds, 0.85)
    out_noisy = ttba(r_init, t_init, K_n, src, dst, uvs, uvd_noisy, ds_noisy, dd_noisy, p_uniform)
    assert out_noisy.diagnostics.reproj_err_after < out_noisy.diagnostics.reproj_err_before

    # Finding 3 (BLOCKER) & Finding 11 (WARNING): Pre-ViT temporal_patch=2 camera isolation + >16 stream IDs
    conv3d = nn.Conv3d(3, cfg.epi.vit_hidden_size, kernel_size=(2, 2, 2), stride=(2, 2, 2))
    imgs_a = torch.randn(bsz, 4, 3, 2 * hm, 2 * wm)
    imgs_b = imgs_a.clone()
    imgs_b[:, 1] = torch.randn_like(imgs_b[:, 1]) * 10.0  # Perturb camera 1 dramatically
    for iso_mode in ("multiview", "robot_wrist_exo"):
        vb_iso = build_viewset_batch(iso_mode, bsz, 4)
        pairs_a, iso_m = pack_views_for_temporal_patch2(imgs_a, vb_iso)
        assert iso_m.all() and torch.equal(pairs_a[:, 0, 0], pairs_a[:, 0, 1])
        emb_a, _ = EpiAdapter.pack_pre_vit_views(imgs_a, vb_iso, temporal_patch_embed=conv3d)
        emb_b, _ = EpiAdapter.pack_pre_vit_views(imgs_b, vb_iso, temporal_patch_embed=conv3d)
        # Camera 0, 2, 3 embeddings must have ZERO bleeding from Camera 1
        assert (emb_a[:, 0] - emb_b[:, 0]).abs().max().item() == 0.0
        assert (emb_a[:, 2] - emb_b[:, 2]).abs().max().item() == 0.0

    # >16 stream IDs (48 distinct cameras) must produce 48 pairwise distinct stream embeddings
    epi = EpiAdapter(cfg.epi, d_lm)
    vb_48 = build_viewset_batch("multiview", 1, 48)
    meta_48 = epi.meta_enc(vb_48)[0]  # [48, d_model]
    pdist_48 = torch.cdist(meta_48, meta_48) + torch.eye(48) * 10.0
    assert pdist_48.min().item() > 1e-3, f"Stream ID collision detected: min dist={pdist_48.min().item()}"

    # Finding 6 (BLOCKER) & Finding 8 (WARNING): Exact pi-rotation SO(3) log + finite grads + degenerate 6D/gravity/Plucker
    for axis_raw in (
        torch.tensor([1.0, -1.0, 0.0]),
        torch.tensor([1.0, 0.0, -1.0]),
        torch.tensor([0.0, 1.0, -1.0]),
        torch.tensor([1.0, -2.0, 1.5]),
    ):
        u = axis_raw / axis_raw.norm()
        r_pi = so3_exp(u * math.pi)
        w_log = so3_log(r_pi)
        r_rt = so3_exp(w_log)
        assert (r_rt - r_pi).abs().max().item() < 1e-5, f"Pi round-trip failed for axis {u}: max_err={(r_rt - r_pi).abs().max().item()}"

        # Verify 6D rotation -> geodesic loss at theta=pi produces finite, nonzero gradients
        r6_param = nn.Parameter(matrix_to_rotation_6d(r_pi).clone())
        r_pred = rotation_6d_to_matrix(r6_param)
        w_err = so3_log(r_pred)
        l_geod = torch.sqrt((w_err * w_err).sum() + 1e-8)
        l_geod.backward()
        assert r6_param.grad is not None and torch.isfinite(r6_param.grad).all()
        assert r6_param.grad.abs().sum().item() > 0.0

    # Degenerate 6D inputs (zero & collinear) and zero gravity
    r6_deg = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 2.0, 3.0, 2.0, 4.0, 6.0]], requires_grad=True)
    r_deg = rotation_6d_to_matrix(r6_deg)
    assert (torch.linalg.det(r_deg) - 1.0).abs().max().item() < 1e-5
    assert (r_deg @ r_deg.transpose(-1, -2) - torch.eye(3)).abs().max().item() < 1e-5
    r_deg.sum().backward()
    assert r6_deg.grad is not None and torch.isfinite(r6_deg.grad).all()

    rc_z, tc_z = compute_gravity_leveled_poses(
        torch.eye(3).view(1, 1, 3, 3).expand(2, 3, 3, 3), torch.zeros(2, 3, 3), torch.zeros(2, 3)
    )
    assert (torch.linalg.det(rc_z) - 1.0).abs().max().item() < 1e-5

    p_head = GeoPoseHead(cfg.geo_heads, d_lm)
    p_out = p_head(torch.randn(bsz, n_views, d_lm), torch.randn(bsz, n_views, hm, wm, d_lm))
    plucker_dot = (p_out.plucker_pred[..., :3] * p_out.plucker_pred[..., 3:6]).sum(dim=-1)
    assert plucker_dot.abs().max().item() < 1e-5

    # Finding 4 (BLOCKER), Finding 5 (BLOCKER), Finding 9 (WARNING):
    # NaN masked depth, padded-view zero loss, unlocked-scale zero gamma grad in composite loss, static-flow p_stat sparsity
    d_head = GeoDepthHead(cfg.geo_heads, d_lm, cfg.epi.fine_dim)
    comp_loss = SpatialV2CompositeLoss(cfg.sf2, cfg.loss_weights, d_lm)
    hv = torch.randn(bsz, n_views, hm, wm, d_lm, requires_grad=True)
    fg = torch.randn(bsz, n_views, 2 * hm, 2 * wm, cfg.epi.fine_dim, requires_grad=True)
    d_out = d_head(hv, fg, p_out.log_fx_w.detach(), p_out.log_fy_h.detach())

    # Masked-out NaN target in DecoupledDepthLoss must NOT produce NaN loss or NaN grads
    d_gt_nan = torch.rand(bsz, n_views, 2 * hm, 2 * wm) * 2.0 + 0.5
    d_val_nan = torch.ones_like(d_gt_nan, dtype=torch.bool)
    d_gt_nan[0, 1, 2, 3] = float("nan")
    d_val_nan[0, 1, 2, 3] = False
    l_nan, _ = DecoupledDepthLoss()(d_out, d_gt_nan, d_val_nan, torch.ones(bsz))
    assert torch.isfinite(l_nan)

    # Unlocked scale (metric_scale_locked=0) through full SpatialV2CompositeLoss with unprojected pmap_pred
    # must give strictly 0.0 gradient on log_gamma_bias and scene_scale_head
    d_head.zero_grad()
    p_head.zero_grad()
    comp_loss.zero_grad()
    d_out_u = d_head(hv.detach(), fg.detach())
    p_out_u = p_head(torch.randn(bsz, n_views, d_lm), hv.detach())
    K_u = build_intrinsics_matrix(p_out_u.log_fx_w, p_out_u.log_fy_h, float(wm), float(hm))
    d_low_u = nn.functional.interpolate(
        d_out_u.depth.reshape(bsz * n_views, 1, 2 * hm, 2 * wm), size=(hm, wm), mode="bilinear", align_corners=False
    ).reshape(bsz, n_views, hm, wm)
    pts_u = unproject_depth(d_low_u, K_u, p_out_u.rot_canon, p_out_u.trans_canon)
    targets_u = {
        "depth_gt": torch.rand(bsz, n_views, 2 * hm, 2 * wm) * 3.0 + 0.5,
        "depth_valid": torch.ones(bsz, n_views, 2 * hm, 2 * wm, dtype=torch.bool),
        "metric_scale_locked": torch.zeros(bsz),
        "rot_gt": so3_exp(torch.randn(bsz, n_views, 3) * 0.2),
        "trans_gt": torch.randn(bsz, n_views, 3),
        "gravity_gt": torch.tensor([0.0, 0.0, 1.0]).view(1, 1, 3).expand(bsz, n_views, 3),
        "log_fx_w_gt": torch.zeros(bsz, n_views),
        "log_fy_h_gt": torch.zeros(bsz, n_views),
        "plucker_gt": torch.randn(bsz, n_views, hm, wm, 6),
        "pmap_gt": torch.randn_like(pts_u),
        "y_stat_gt": torch.ones(bsz, n_views, 2 * hm, 2 * wm),
        "delta_p_gt": torch.randn(bsz, n_views, 2 * hm, 2 * wm, len(cfg.geo_heads.flow_horizons), 3) * 0.1,
        "delta_p_rev": torch.randn(bsz, n_views, 2 * hm, 2 * wm, len(cfg.geo_heads.flow_horizons), 3) * 0.1,
    }
    taps_u = {16: torch.randn(bsz, n_views, hm * wm, d_lm), 24: torch.randn(bsz, n_views, hm * wm, d_lm)}
    loss_u, _ = comp_loss(
        taps_u, torch.randn(bsz, n_views, hm * wm, cfg.sf2.teacher_dim), d_out_u, p_out_u, targets_u, pmap_pred=pts_u
    )
    loss_u.backward()
    assert d_head.log_gamma_bias.grad is None or d_head.log_gamma_bias.grad.abs().max().item() == 0.0
    for p in d_head.scene_scale_head.parameters():
        assert p.grad is None or p.grad.abs().max().item() == 0.0

    # Padded views (view_mask=False) with massive errors or NaNs must contribute 0.0 to losses
    vm_pad = torch.tensor([[True, True, False, False], [True, True, True, False]])
    targets_locked = {**targets_u, "metric_scale_locked": torch.ones(bsz)}
    targets_corrupt = {k: v.clone() for k, v in targets_locked.items()}
    targets_corrupt["pmap_gt"][~vm_pad] = 1e6
    targets_corrupt["delta_p_rev"][~vm_pad] = 1e6
    targets_corrupt["delta_p_gt"][~vm_pad] = float("nan")
    targets_corrupt["depth_gt"][~vm_pad] = float("nan")
    _seed(99)
    l_clean, m_clean = comp_loss(
        taps_u, torch.zeros(bsz, n_views, hm * wm, cfg.sf2.teacher_dim), d_out_u, p_out_u, targets_locked,
        pmap_pred=pts_u, view_mask=vm_pad,
    )
    _seed(99)
    l_corrupt, m_corrupt = comp_loss(
        taps_u, torch.zeros(bsz, n_views, hm * wm, cfg.sf2.teacher_dim), d_out_u, p_out_u, targets_corrupt,
        pmap_pred=pts_u, view_mask=vm_pad,
    )
    assert torch.isfinite(l_corrupt) and (l_clean - l_corrupt).abs().item() < 1e-6
    assert (m_clean["pmap"] - m_corrupt["pmap"]).abs().item() < 1e-6
    assert (m_clean["reversal"] - m_corrupt["reversal"]).abs().item() < 1e-6

    # Static-flow sparsity weights by p_stat (static p_stat->1 penalized > dynamic p_stat->0)
    d_stat = GeoDepthOutput(
        **{**d_out_u.__dict__, "p_stat": torch.ones_like(d_out_u.p_stat), "delta_p_obj": torch.ones_like(d_out_u.delta_p_obj)}
    )
    d_dyn = GeoDepthOutput(
        **{**d_out_u.__dict__, "p_stat": torch.zeros_like(d_out_u.p_stat), "delta_p_obj": torch.ones_like(d_out_u.delta_p_obj)}
    )
    t_stat, _ = comp_loss.pose_4d_loss(
        p_out_u, d_stat, targets_locked["rot_gt"], targets_locked["trans_gt"], targets_locked["gravity_gt"],
        targets_locked["log_fx_w_gt"], targets_locked["log_fy_h_gt"], targets_locked["plucker_gt"],
        targets_locked["metric_scale_locked"], view_mask=vm_pad,
    )
    t_dyn, _ = comp_loss.pose_4d_loss(
        p_out_u, d_dyn, targets_locked["rot_gt"], targets_locked["trans_gt"], targets_locked["gravity_gt"],
        targets_locked["log_fx_w_gt"], targets_locked["log_fy_h_gt"], targets_locked["plucker_gt"],
        targets_locked["metric_scale_locked"], view_mask=vm_pad,
    )
    assert t_stat["flow_sparsity"].item() == 1.0 and t_dyn["flow_sparsity"].item() == 0.0

    # Finding 10 (WARNING): Metric3DRoPE large-origin shifts (10^6) and extreme bf16 (3e38) coordinates
    rope = Metric3DRoPE(cfg.rope3d)
    seq_len = 16
    q = torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim)
    k = torch.randn(bsz, cfg.rope3d.num_heads, seq_len, cfg.rope3d.head_dim)
    th0 = torch.zeros(bsz, seq_len, cfg.rope3d.rotary_dim // 2)
    c_extreme = torch.full((bsz, seq_len, 3), 3e38, dtype=torch.bfloat16)
    q_ex0, k_ex0 = rope(q, k, th0, c_extreme)
    assert torch.isfinite(q_ex0).all() and torch.isfinite(k_ex0).all()
    with torch.no_grad():
        rope.beta_h.fill_(0.5)
    q_ex1, k_ex1 = rope(q, k, th0, c_extreme)
    assert torch.isfinite(q_ex1).all() and torch.isfinite(k_ex1).all()
    c_base = torch.randn(bsz, seq_len, 3)
    q_b0, k_b0 = rope(q, k, th0, c_base)
    q_b3, k_b3 = rope(q, k, th0, c_base + 1e3)
    q_b6, k_b6 = rope(q, k, th0, c_base.double() + 1e6)
    l_b0 = torch.matmul(q_b0, k_b0.transpose(-1, -2))
    l_b3 = torch.matmul(q_b3, k_b3.transpose(-1, -2))
    l_b6 = torch.matmul(q_b6, k_b6.transpose(-1, -2))
    assert (l_b0 - l_b3).abs().max().item() < 5e-3
    assert (l_b0 - l_b6).abs().max().item() < 1e-5


if __name__ == "__main__":
    for fn in [
        test_config_qwen35_topology_and_viewset_packing,
        test_zero_init_exact_identity,
        test_epi_adapter_permutation_invariance,
        test_se3_invariance_and_unprojection_roundtrip_including_mujoco_mirror,
        test_metric_3d_rope_relative_distance_property,
        test_ttba_recovers_rotation_and_scale_under_25ms,
        test_losses_and_exact_finite_gradients_all_viewset_modes,
        test_flow_expert_ode_sampling_and_latency,
        test_codex_regressions_all_11_findings,
    ]:
        t0 = time.perf_counter()
        fn()
        print(f"PASS {fn.__name__} ({(time.perf_counter() - t0) * 1000.0:.1f} ms)")
