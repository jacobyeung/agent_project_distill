"""Unit & Integration Tests for Spatial-V2 Stage-2 Dynamic 4D Teacher Schema & Zero-Leak Guard."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from spatial_v2.config import (
    EpiAdapterConfig,
    GeoHeadsConfig,
    SpatialForcing2Config,
    SpatialV2Config,
)
from spatial_v2.data_k1_local import DEFAULT_MANIFEST_PATH
from spatial_v2.dynamic_4d_schema import (
    DEFAULT_FLOW_HORIZONS,
    Dynamic4DExclusionGuard,
    certified_stationarity_gate,
    estimate_ego_and_object_4d_kinematics,
    load_point4d_store_to_sample,
)
from spatial_v2.geo_heads import GeoDepthHead, GeoPoseHead
from spatial_v2.losses import PoseAnd4DLoss, SpatialV2CompositeLoss


def _write_synthetic_point4d_bundle(root: Path, scene: str = "syn_4d_clip") -> Tuple[Path, Path, Path]:
    """Create a synthetic 32-frame Point4D + tracks + gravity .npz bundle with moving camera & moving object."""
    N, H, W = 32, 60, 80
    p3d_dir = root / "point4d_32"
    trk_dir = p3d_dir / "tracks"
    grv_dir = root / "gravity" / "stores"
    p3d_dir.mkdir(parents=True, exist_ok=True)
    trk_dir.mkdir(parents=True, exist_ok=True)
    grv_dir.mkdir(parents=True, exist_ok=True)

    # Moving ego camera in common frame (translates 1.6m along X, 0.4m along Z)
    timestamps_s = np.linspace(0.0, 3.1, N, dtype=np.float64)
    c2w = np.tile(np.eye(4, dtype=np.float32), (N, 1, 1))
    for t in range(N):
        angle = 0.01 * t
        c, s = np.cos(angle), np.sin(angle)
        c2w[t, :3, :3] = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float32)
        c2w[t, :3, 3] = np.array([0.05 * t, 0.0, 0.012 * t], dtype=np.float32)

    K = np.tile(
        np.array([[60.0, 0.0, 40.0], [0.0, 60.0, 30.0], [0.0, 0.0, 1.0]], dtype=np.float32),
        (N, 1, 1),
    )
    depth_z = np.full((N, H, W), 2.5, dtype=np.float16)
    conf = np.full((N, H, W), 0.9, dtype=np.float16)
    mask = np.ones((N, H, W), dtype=bool)

    # Unproject pixels into common world frame with scene extent ~ 4.0m
    yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
    z = depth_z.astype(np.float32)
    x_cam = (xx[None] - 40.0) / 60.0 * z
    y_cam = (yy[None] - 30.0) / 60.0 * z
    pts_cam = np.stack([x_cam, y_cam, z], axis=-1)
    pts3d_world = (
        np.einsum("nij,nhwj->nhwi", c2w[:, :3, :3], pts_cam) + c2w[:, None, None, :3, 3]
    ).astype(np.float16)

    p3d_path = p3d_dir / f"{scene}.npz"
    np.savez_compressed(
        p3d_path,
        depth_z=depth_z,
        intrinsics=K,
        camera_poses=c2w,
        conf=conf,
        mask=mask,
        pts3d_world=pts3d_world,
        indices=np.arange(N, dtype=np.int64),
        source_indices=np.arange(N, dtype=np.int64),
        baseline_slots=np.arange(N, dtype=np.int64),
        native_to_world=np.eye(4, dtype=np.float32),
        timestamps_s=timestamps_s,
    )

    # Create 10x10 = 100 queries per source frame: right half (u >= 40) is a dynamic object moving at +0.15 m/frame
    gy, gx = np.meshgrid(
        np.linspace(3, H - 4, 10).astype(np.float32),
        np.linspace(4, W - 5, 10).astype(np.float32),
        indexing="ij",
    )
    uv_single = np.stack([gx.ravel(), gy.ravel()], axis=-1)  # [100, 2]
    Q_per_frame = len(uv_single)
    Q_total = N * Q_per_frame
    query_source_slots = np.repeat(np.arange(N, dtype=np.int64), Q_per_frame)
    query_uv = np.tile(uv_single, (N, 1)).astype(np.float32)

    tracks_world = np.zeros((N, Q_total, 3), dtype=np.float32)
    track_conf = np.full((N, Q_total), 0.95, dtype=np.float16)
    vel_obj = np.array([0.15, 0.05, 0.0], dtype=np.float32)  # meters per frame in common frame

    for s in range(N):
        q0 = s * Q_per_frame
        q1 = (s + 1) * Q_per_frame
        u_s = uv_single[:, 0]
        v_s = uv_single[:, 1]
        # Static base position in common world frame
        base_xyz = np.stack([(u_s - 40.0) * 0.05, (v_s - 30.0) * 0.05, np.full_like(u_s, 2.5)], axis=-1)
        is_dyn = (u_s >= 40.0)[:, None]  # Right half of image is dynamic
        for t in range(N):
            tracks_world[t, q0:q1, :] = base_xyz + is_dyn * ((t - s) * vel_obj[None, :])

    trk_path = trk_dir / f"{scene}.npz"
    np.savez_compressed(
        trk_path,
        tracks_world=tracks_world,
        track_confidence=track_conf,
        query_source_slots=query_source_slots,
        query_uv=query_uv,
    )

    # Identity common_to_world (+Z already aligned) so world velocity is preserved verbatim
    grv_path = grv_dir / f"{scene}.npz"
    np.savez_compressed(
        grv_path,
        common_to_world=np.eye(4, dtype=np.float64),
        up_vector_common=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        up_vector_world=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        up_available=np.asarray(True, dtype=bool),
    )
    return p3d_path, trk_path, grv_path


class TestDynamic4DSchema(unittest.TestCase):
    def test_zero_leak_all_benchmarks_and_k1_train(self) -> None:
        guard = Dynamic4DExclusionGuard()
        verdict = guard.verify_all_benchmarks_blocked()
        self.assertEqual(verdict["vsti_450_captures_blocked"], "50/50")
        self.assertEqual(verdict["resti_sti_scannet_rooms_blocked"], "150/150")
        self.assertEqual(verdict["egoexo4d_takes_blocked"], "41/41")

        # Audit all 233 clean Spatial-V2 K1 training captures if local manifest exists
        if Path(DEFAULT_MANIFEST_PATH).is_file():
            audit = guard.audit_k1_train_zero_leak()
            self.assertTrue(audit["zero_leak_verified"])
            self.assertEqual(audit["clean_train_captures"], 233)
            self.assertEqual(audit["clean_train_unique_rooms"], 214)

    def test_point4d_store_roundtrip_and_ego_decoupling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p3d_path, trk_path, grv_path = _write_synthetic_point4d_bundle(Path(tmp))
            sample = load_point4d_store_to_sample(
                p3d_path,
                tracks_npz_path=trk_path,
                gravity_npz_path=grv_path,
                grid_hw=(10, 10),
                flow_horizons=DEFAULT_FLOW_HORIZONS,
            )
            stats = sample.validate()
            self.assertEqual(stats["shape_bnhw"], [1, 32, 10, 10])
            self.assertLess(stats["so3_ortho_max_err"], 1e-4)
            self.assertLess(stats["plucker_ortho_max_err"], 1e-4)

            # Left half (cols 0..4) is static despite moving ego camera; right half (cols 5..9) is dynamic
            p_dyn_left = float(sample.p_dyn_gt[0, :, :, :5].mean().item())
            p_dyn_right = float(sample.p_dyn_gt[0, :, :, 5:].mean().item())
            self.assertLess(p_dyn_left, 0.02)
            self.assertGreater(p_dyn_right, 0.98)

            # Static 3D flow must be strictly 0.0 even though ego camera translated > 1.5m
            static_flow_max = float(sample.delta_p_gt[0, :, :, :5, :, :].abs().max().item())
            self.assertLess(static_flow_max, 1e-5)

            # Dynamic 3D flow at horizon +1 (index 1) on frame 5 must match [0.15, 0.05, 0.0]
            dyn_flow_h1 = sample.delta_p_gt[0, 5, :, 5:, 1, :]  # [10, 5, 3]
            expected_h1 = torch.tensor([0.15, 0.05, 0.0], dtype=torch.float32)
            err_h1 = float((dyn_flow_h1 - expected_h1).abs().max().item())
            self.assertLess(err_h1, 1e-4)

            # Reversal symmetry: delta_p_rev == -delta_p_gt on all valid horizons
            rev_sum_max = float((sample.delta_p_gt + sample.delta_p_rev).abs().max().item())
            self.assertLess(rev_sum_max, 1e-6)

            kin = estimate_ego_and_object_4d_kinematics(sample, horizon_idx=1)
            self.assertFalse(kin["ego_is_stationary"])
            self.assertGreater(kin["mean_dynamic_disp_m"], 0.14)
            self.assertLess(kin["mean_static_residual_m"], 1e-5)

    def test_geo_heads_and_composite_4d_loss_backward(self) -> None:
        torch.manual_seed(7)
        with tempfile.TemporaryDirectory() as tmp:
            p3d_path, trk_path, grv_path = _write_synthetic_point4d_bundle(Path(tmp))
            sample_full = load_point4d_store_to_sample(
                p3d_path, trk_path, grv_path, grid_hw=(8, 8)
            )
            # Slice first 6 views for fast unit test
            N_sub = 6
            cfg = SpatialV2Config(
                hidden_size=128,
                epi=EpiAdapterConfig(vit_hidden_size=128, fine_dim=32, d_model=64, num_blocks=2, num_heads=4),
                geo_heads=GeoHeadsConfig(
                    depth_hidden_dim=32,
                    depth_cross_blocks=1,
                    depth_num_heads=4,
                    flow_horizons=DEFAULT_FLOW_HORIZONS,
                    pose_hidden_dim=64,
                    pose_num_layers=2,
                    pose_num_heads=4,
                ),
                sf2=SpatialForcing2Config(tap_layers=(16, 24), teacher_dim=64, probe_hidden_dim=64, gram_num_samples=32),
            )
            pose_head = GeoPoseHead(cfg.geo_heads, lm_hidden_size=cfg.hidden_size)
            depth_head = GeoDepthHead(cfg.geo_heads, lm_hidden_size=cfg.hidden_size, fine_dim=cfg.epi.fine_dim)
            comp_loss = SpatialV2CompositeLoss(cfg.sf2, cfg.loss_weights, lm_hidden_size=cfg.hidden_size)

            B, H, W = 1, 8, 8
            h_vis = torch.randn(B, N_sub, H, W, cfg.hidden_size, requires_grad=True)
            h_cam = torch.randn(B, N_sub, cfg.hidden_size, requires_grad=True)
            fine_geo = torch.randn(B, N_sub, H, W, cfg.epi.fine_dim, requires_grad=True)
            student_taps = {
                16: torch.randn(B, N_sub, H * W, cfg.hidden_size, requires_grad=True),
                24: torch.randn(B, N_sub, H * W, cfg.hidden_size, requires_grad=True),
            }
            teacher_feats = torch.randn(B, N_sub, H * W, cfg.sf2.teacher_dim)

            kw = sample_full.to_loss_kwargs()
            kw_sub = {
                k: (v[:, :N_sub] if v.ndim >= 2 and v.shape[1] == 32 else v)
                for k, v in kw.items()
            }
            pose_out = pose_head(h_cam, h_vis, view_mask=kw_sub["view_mask"])
            depth_out = depth_head(
                h_vis,
                fine_geo,
                log_fx_w=pose_out.log_fx_w,
                log_fy_h=pose_out.log_fy_h,
                view_mask=kw_sub["view_mask"],
            )

            total_loss, loss_metrics = comp_loss(
                student_taps=student_taps,
                teacher_feats=teacher_feats,
                depth_out=depth_out,
                pose_out=pose_out,
                targets=kw_sub,
                pmap_pred=kw_sub["pmap_gt"] + 0.05 * torch.randn_like(kw_sub["pmap_gt"]),
                view_mask=kw_sub["view_mask"],
            )
            self.assertTrue(bool(torch.isfinite(total_loss).item()))
            self.assertGreater(float(loss_metrics["flow"].item()), 0.0)
            self.assertGreater(float(loss_metrics["rigidity"].item()), 0.0)
            self.assertGreater(float(loss_metrics["reversal"].item()), 0.0)

            total_loss.backward()
            # Verify gradients reach rigidity_head, flow_head, depth_head, and pose_head
            rig_grad = sum(p.grad.abs().sum().item() for p in depth_head.rigidity_head.parameters() if p.grad is not None)
            flow_grad = sum(p.grad.abs().sum().item() for p in depth_head.flow_head.parameters() if p.grad is not None)
            pose_grad = sum(p.grad.abs().sum().item() for p in pose_head.parameters() if p.grad is not None)
            self.assertGreater(rig_grad, 0.0)
            self.assertGreater(flow_grad, 0.0)
            self.assertGreater(pose_grad, 0.0)

    def test_certified_stationarity_gate(self) -> None:
        torch.manual_seed(42)
        B, N, H, W = 1, 16, 8, 8
        rot = torch.eye(3).view(1, 1, 3, 3).expand(B, N, 3, 3).clone()
        # Tiny 1.5mm stationary camera jitter
        trans_jitter = 0.0015 * torch.randn(B, N, 3)
        trans_jitter[:, 0] = 0.0
        p_stat_high = torch.full((B, N, H, W), 0.92)
        ts = torch.linspace(0.0, 1.5, N).unsqueeze(0)

        res_stat = certified_stationarity_gate(rot, trans_jitter, p_stat_high, ts)
        self.assertTrue(bool(res_stat["is_stationary"][0].item()))
        self.assertEqual(float(res_stat["gated_speed_mps"][0].item()), 0.0)
        self.assertGreater(float(res_stat["raw_speed_mps"][0].item()), 0.0)

        # Genuinely moving camera (0.8 m/s along X)
        trans_moving = torch.zeros(B, N, 3)
        trans_moving[0, :, 0] = -torch.linspace(0.0, 1.2, N)
        res_mov = certified_stationarity_gate(rot, trans_moving, p_stat_high, ts)
        self.assertFalse(bool(res_mov["is_stationary"][0].item()))
        self.assertAlmostEqual(
            float(res_mov["gated_speed_mps"][0].item()),
            float(res_mov["raw_speed_mps"][0].item()),
            places=5,
        )


if __name__ == "__main__":
    unittest.main()
