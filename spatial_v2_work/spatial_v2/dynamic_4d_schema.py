"""Dynamic 4D Teacher Extraction Contract & Zero-Leak Benchmark Guard for Spatial-V2 Stage-2.

Aligns Point4D / Any4D / MapAnything + DA3 4D teacher stores directly to Spatial-V2's
GeoHeads (`GeoDepthHead`, `GeoPoseHead`) and losses (`PoseAnd4DLoss`, `SpatialV2CompositeLoss`):
  - Per-frame metric depth `depth_gt` [B, N, H, W] & `valid_depth` [B, N, H, W]
  - Camera pose SE(3) `rot_gt` [B, N, 3, 3] (R_w2c), `trans_gt` [B, N, 3] (t_w2c),
    `gravity_gt` [B, N, 3], `fov_x_gt` / `fov_y_gt` [B, N], `plucker_gt` [B, N, H, W, 6],
    and canonical +Z-up world pointmap `pmap_gt` [B, N, H, W, 3]
  - Per-pixel dynamic probability `p_dyn_gt = 1 - y_stat_gt` [B, N, H, W] supervising
    `GeoDepthHead.rigidity_logits` (`p_stat = sigmoid(rigidity_logits)`)
  - Ego-decoupled 3D scene-flow / world-space point tracks `delta_p_gt` [B, N, H, W, K, 3]
    and time-reversed `delta_p_rev` [B, N, H, W, K, 3] across horizons
    `flow_horizons = (-1, 1, 4, 16)` in canonical +Z-up world meters
  - Certified Stationarity Gate & Kabsch/Procrustes 3D heading turn kinematics
  - Fail-closed `Dynamic4DExclusionGuard` guaranteeing zero room/video/take overlap with
    BENCH_v2, VSTI-450 (50 ScanNet captures), ReSTI/STI (150 ScanNet rooms 0000..0149
    including the 75 ReSTI ScanNet rooms + 100 Waymo + 119 Omni6DPose), OSI-150 / DSI-1000,
    Ego-Exo4D (41 takes / 210 questions), HD-EPIC (62 recordings / 152 questions),
    R0_dev, dev_S1, K1_heldout, and withheld_80.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from .config import SpatialV2Config
from .data_k1_local import (
    DEFAULT_EXCL_DIR,
    DEFAULT_FRAMES_ROOT,
    DEFAULT_MANIFEST_PATH,
    RoomExclusionGuard,
    build_clean_k1_splits,
    canonical_room_keys,
)
from .geo_heads import compute_plucker_rays, unproject_depth


def canonical_room_id(canonical: str) -> str:
    """Return canonical physical room ID (e.g. `scannet/scene0011_01` -> `scannet/scene0011`)."""
    norm = canonical.strip().lower().replace("::", "/").replace("__", "/")
    if norm.startswith("scannet/scene") and len(norm) >= 17 and norm[13:17].isdigit():
        return f"scannet/scene{norm[13:17]}"
    return norm

DEFAULT_FLOW_HORIZONS: Tuple[int, ...] = (-1, 1, 4, 16)

# All 50 VSTI-450 ScanNet evaluation captures (31 unique physical rooms).
VSTI_450_SCANNET_CAPTURES: Tuple[str, ...] = (
    "scene0011_00", "scene0011_01", "scene0019_01", "scene0025_00", "scene0025_02",
    "scene0030_00", "scene0030_01", "scene0030_02", "scene0046_01", "scene0046_02",
    "scene0064_00", "scene0064_01", "scene0077_01", "scene0081_00", "scene0081_02",
    "scene0084_00", "scene0084_01", "scene0086_00", "scene0086_01", "scene0086_02",
    "scene0088_00", "scene0088_01", "scene0088_02", "scene0088_03", "scene0095_00",
    "scene0095_01", "scene0100_00", "scene0100_01", "scene0100_02", "scene0131_00",
    "scene0131_01", "scene0144_00", "scene0144_01", "scene0146_00", "scene0146_01",
    "scene0217_00", "scene0304_00", "scene0412_00", "scene0412_01", "scene0426_03",
    "scene0488_00", "scene0488_01", "scene0549_00", "scene0568_01", "scene0568_02",
    "scene0575_00", "scene0575_01", "scene0575_02", "scene0598_02", "scene0690_01",
)

# All 150 ReSTI / STI ScanNet rooms (scene0000 .. scene0149), superset of the 75 ReSTI ScanNet rooms.
RESTI_STI_SCANNET_ROOMS: Tuple[str, ...] = tuple(f"scannet/scene{i:04d}" for i in range(150))

# All 41 Ego-Exo4D Suite 2A/2B evaluation take UIDs (210 questions).
EGOEXO4D_TRACK2_TAKES: Tuple[str, ...] = (
    "05367d8f-6e4b-4373-b5ad-ea192014bcaa", "1d0f3c10-ed0a-4f60-b0d2-a516690ff1cf",
    "2403cd07-b094-45ec-b5e7-8cbb5fd66158", "2660fb72-9d4c-4412-a4fe-24faf8bfec92",
    "2e00eb80-4fd0-4ba5-bcbb-5e671d7f3627", "38fe389f-a9a9-4bc5-bf6c-7f1eefffbf9a",
    "3a2fb128-922e-4f16-b62c-1c7e7463fd21", "44e77068-7a1c-4210-ad14-cd1fc2e0dc38",
    "454ff920-66be-4a57-a03f-d93ef0fe9ac9", "46d7913e-8d19-4af6-a654-1c290ff73d65",
    "49a77e12-5588-4605-8ff5-a054ef0eb74c", "4c7d65c0-a6a8-4fb6-a3d3-e3fd5ef8c208",
    "55e7b0e2-878e-4821-b867-513f8e051214", "5a1a62ec-0a0a-4a5f-9e8a-7468c83c593c",
    "61213ef1-2258-42c2-96d0-ef8e56f59819", "6a23d2fc-98b2-4361-a6e7-a7026d887e70",
    "6d0e9960-c544-4c68-9e1e-358ee1a26149", "717a7a88-c586-49a4-97ef-9f16c9d6e35c",
    "763858a7-6d20-4c9a-9040-17a6c0f76c16", "7c2f3f0c-227c-41a6-a367-16f61f84f84a",
    "7f23210b-8c1a-4c3c-a3b5-9e083286424a", "84995d57-7c05-4176-9f64-782f684160a6",
    "88c07671-b854-4a34-8722-c3902c6293d5", "8f35a7e6-5c11-4895-a76f-78a750f22f5b",
    "91650b60-2009-4347-9348-70458e2f80cb", "99a0b940-87e1-4c96-8e33-4a9140b42c2f",
    "a1e23c95-9614-4d05-88c5-88d77f902863", "a8474c90-90b5-4c03-9963-8b10b613849c",
    "b092a357-7d2a-4396-9668-e455c42e9e0e", "b52a5c32-119b-4174-93f6-a9b06526d6a3",
    "bd632a60-5234-4a51-b983-4c53087f1e76", "c102883c-5893-4781-9f36-74872365692a",
    "c7f6c1a2-5862-4b02-8873-84c60186f362", "d1a7b58a-2088-4642-81c9-278246893a83",
    "d6428388-0295-4c96-8900-86e923488a71", "d9a8414e-0861-4252-9b8b-29842c835361",
    "e3088577-1595-470c-8565-282036470244", "e9404155-3911-457c-9988-26258367527c",
    "f0418257-6110-4b23-851c-18480565890c", "f5507943-9575-4747-9375-491042718251",
    "fa809234-5112-4062-8421-389104827164",
)

# Forbidden evaluation benchmark corpora / prefixes that must never enter training.
FORBIDDEN_EVAL_CORPORA: Tuple[str, ...] = (
    "waymo",
    "omni6dpose",
    "osi",
    "osibench",
    "dsi",
    "dsibench",
    "sti",
    "stibench",
    "resti",
    "restibench",
    "vsti",
    "vstibench",
    "egoexo",
    "ego-exo4d",
    "egoexo4d",
    "hdepic",
    "hd-epic",
    "hourvideo",
)

_HD_EPIC_REC_RE = re.compile(r"^p0[1-9]-\d{8}-\d{6}$", re.IGNORECASE)
_WAYMO_SEG_RE = re.compile(r"^\d+_\d+_\d+_\d+_\d+_camera_[1-5]$", re.IGNORECASE)
_OMNI6D_VID_RE = re.compile(r"^(?:sti_)?\d{6}$", re.IGNORECASE)
_OSI_VID_RE = re.compile(r"^(?:osi_)?\d{4}$", re.IGNORECASE)


@dataclass
class Dynamic4DTeacherSample:
    """Standardized Spatial-V2 Stage-2 dynamic 4D teacher tensor bundle (`has_4d_teacher`)."""

    capture_id: str
    has_4d_teacher: torch.Tensor        # [B] bool
    metric_scale_locked: torch.Tensor   # [B] bool
    view_mask: torch.Tensor             # [B, N] bool
    depth_gt: torch.Tensor              # [B, N, H, W] float32 (metric meters)
    valid_depth: torch.Tensor           # [B, N, H, W] bool
    rot_gt: torch.Tensor                # [B, N, 3, 3] float32 (R_w2c in canonical +Z-up world)
    trans_gt: torch.Tensor              # [B, N, 3] float32 (t_w2c in canonical +Z-up world)
    gravity_gt: torch.Tensor            # [B, N, 3] float32 (unit gravity in cam-t frame)
    intrinsics: torch.Tensor            # [B, N, 3, 3] float32 (pinhole K on [H, W] grid)
    fov_x_gt: torch.Tensor              # [B, N] float32 (radians)
    fov_y_gt: torch.Tensor              # [B, N] float32 (radians)
    plucker_gt: torch.Tensor            # [B, N, H, W, 6] float32
    pmap_gt: torch.Tensor               # [B, N, H, W, 3] float32 (canonical +Z-up world meters)
    pmap_valid: torch.Tensor            # [B, N, H, W] bool
    y_stat_gt: torch.Tensor             # [B, N, H, W] float32 in [0, 1] (1=static, 0=dynamic)
    p_dyn_gt: torch.Tensor              # [B, N, H, W] float32 in [0, 1] (1 - y_stat_gt)
    delta_p_gt: torch.Tensor            # [B, N, H, W, K, 3] float32 (ego-decoupled 3D displacement, m)
    delta_p_rev: torch.Tensor           # [B, N, H, W, K, 3] float32 (time-reversed 3D displacement, m)
    flow_valid: torch.Tensor            # [B, N, H, W, K] bool
    timestamps_s: torch.Tensor          # [B, N] float32
    flow_horizons: Tuple[int, ...] = DEFAULT_FLOW_HORIZONS
    metadata: Optional[Dict[str, Any]] = None

    def validate(self, atol_rot: float = 1e-3, atol_plucker: float = 1e-3) -> Dict[str, Any]:
        """Verify tensor shapes, dtypes, SO(3) pose invariants, Plucker orthogonality, and finite masks."""
        B, N, H, W = self.depth_gt.shape
        K = len(self.flow_horizons)

        assert self.has_4d_teacher.shape == (B,) and self.has_4d_teacher.dtype == torch.bool
        assert self.metric_scale_locked.shape == (B,) and self.metric_scale_locked.dtype == torch.bool
        assert self.view_mask.shape == (B, N) and self.view_mask.dtype == torch.bool
        assert self.valid_depth.shape == (B, N, H, W) and self.valid_depth.dtype == torch.bool
        assert self.rot_gt.shape == (B, N, 3, 3)
        assert self.trans_gt.shape == (B, N, 3)
        assert self.gravity_gt.shape == (B, N, 3)
        assert self.intrinsics.shape == (B, N, 3, 3)
        assert self.fov_x_gt.shape == (B, N) and self.fov_y_gt.shape == (B, N)
        assert self.plucker_gt.shape == (B, N, H, W, 6)
        assert self.pmap_gt.shape == (B, N, H, W, 3)
        assert self.pmap_valid.shape == (B, N, H, W) and self.pmap_valid.dtype == torch.bool
        assert self.y_stat_gt.shape == (B, N, H, W)
        assert self.p_dyn_gt.shape == (B, N, H, W)
        assert self.delta_p_gt.shape == (B, N, H, W, K, 3)
        assert self.delta_p_rev.shape == (B, N, H, W, K, 3)
        assert self.flow_valid.shape == (B, N, H, W, K) and self.flow_valid.dtype == torch.bool
        assert self.timestamps_s.shape == (B, N)

        # 1. Rotation SO(3) check on valid views
        rot_valid = self.rot_gt[self.view_mask]
        eye = torch.eye(3, device=rot_valid.device, dtype=rot_valid.dtype).unsqueeze(0)
        ortho_err = float((rot_valid.transpose(-1, -2) @ rot_valid - eye).abs().max().item())
        det_err = float((torch.linalg.det(rot_valid) - 1.0).abs().max().item())
        if ortho_err > atol_rot or det_err > atol_rot:
            raise ValueError(f"SO(3) violation on {self.capture_id}: ortho_err={ortho_err}, det_err={det_err}")

        # 2. Gravity unit norm check
        g_norm_err = float((self.gravity_gt[self.view_mask].norm(dim=-1) - 1.0).abs().max().item())
        if g_norm_err > atol_rot:
            raise ValueError(f"Gravity norm violation on {self.capture_id}: {g_norm_err}")

        # 3. Plucker unit-direction and moment orthogonality check
        d_ray = self.plucker_gt[..., :3]
        m_ray = self.plucker_gt[..., 3:]
        ray_norm_err = float((d_ray.norm(dim=-1) - 1.0).abs().max().item())
        ray_ortho_err = float((d_ray * m_ray).sum(dim=-1).abs().max().item())
        if ray_norm_err > atol_plucker or ray_ortho_err > atol_plucker:
            raise ValueError(
                f"Plucker violation on {self.capture_id}: norm_err={ray_norm_err}, ortho_err={ray_ortho_err}"
            )

        # 4. Depth positivity on valid_depth
        if self.valid_depth.any():
            d_val = self.depth_gt[self.valid_depth]
            if not bool(torch.isfinite(d_val).all().item()) or float(d_val.min().item()) <= 0.0:
                raise ValueError(f"Invalid depth values inside valid_depth on {self.capture_id}")

        # 5. p_dyn + y_stat == 1 and bounded in [0, 1]
        prob_sum_err = float((self.p_dyn_gt + self.y_stat_gt - 1.0).abs().max().item())
        if prob_sum_err > 1e-4:
            raise ValueError(f"p_dyn_gt + y_stat_gt != 1 on {self.capture_id}: max_err={prob_sum_err}")
        if float(self.p_dyn_gt.min().item()) < -1e-5 or float(self.p_dyn_gt.max().item()) > 1.0 + 1e-5:
            raise ValueError(f"p_dyn_gt out of [0, 1] on {self.capture_id}")

        # 6. Flow finite on flow_valid & reversal consistency
        if self.flow_valid.any():
            f_val = self.delta_p_gt[self.flow_valid]
            r_val = self.delta_p_rev[self.flow_valid]
            if not bool(torch.isfinite(f_val).all().item()) or not bool(torch.isfinite(r_val).all().item()):
                raise ValueError(f"Non-finite 3D flow inside flow_valid on {self.capture_id}")

        return {
            "capture_id": self.capture_id,
            "shape_bnhw": [B, N, H, W],
            "num_horizons": K,
            "so3_ortho_max_err": ortho_err,
            "so3_det_max_err": det_err,
            "plucker_ortho_max_err": ray_ortho_err,
            "valid_depth_fraction": float(self.valid_depth.float().mean().item()),
            "flow_valid_fraction": float(self.flow_valid.float().mean().item()),
            "mean_p_dyn": float(self.p_dyn_gt[self.valid_depth].mean().item()) if self.valid_depth.any() else 0.0,
            "mean_y_stat": float(self.y_stat_gt[self.valid_depth].mean().item()) if self.valid_depth.any() else 1.0,
        }

    def to(self, device: torch.device | str) -> "Dynamic4DTeacherSample":
        """Move all tensor fields to target device."""
        return Dynamic4DTeacherSample(
            capture_id=self.capture_id,
            has_4d_teacher=self.has_4d_teacher.to(device),
            metric_scale_locked=self.metric_scale_locked.to(device),
            view_mask=self.view_mask.to(device),
            depth_gt=self.depth_gt.to(device),
            valid_depth=self.valid_depth.to(device),
            rot_gt=self.rot_gt.to(device),
            trans_gt=self.trans_gt.to(device),
            gravity_gt=self.gravity_gt.to(device),
            intrinsics=self.intrinsics.to(device),
            fov_x_gt=self.fov_x_gt.to(device),
            fov_y_gt=self.fov_y_gt.to(device),
            plucker_gt=self.plucker_gt.to(device),
            pmap_gt=self.pmap_gt.to(device),
            pmap_valid=self.pmap_valid.to(device),
            y_stat_gt=self.y_stat_gt.to(device),
            p_dyn_gt=self.p_dyn_gt.to(device),
            delta_p_gt=self.delta_p_gt.to(device),
            delta_p_rev=self.delta_p_rev.to(device),
            flow_valid=self.flow_valid.to(device),
            timestamps_s=self.timestamps_s.to(device),
            flow_horizons=self.flow_horizons,
            metadata=self.metadata,
        )

    def to_loss_kwargs(self, device: Optional[torch.device | str] = None) -> Dict[str, torch.Tensor]:
        """Format exact target dictionary expected by `SpatialV2CompositeLoss` and `PoseAnd4DLoss`."""
        s = self.to(device) if device is not None else self
        has_4d = s.has_4d_teacher[:, None, None, None]  # [B, 1, 1, 1]
        flow_valid_gated = s.flow_valid & has_4d.unsqueeze(-1)
        H, W = s.depth_gt.shape[-2], s.depth_gt.shape[-1]
        log_fx_w_gt = torch.log((s.intrinsics[..., 0, 0] / float(W)).clamp_min(1e-6))
        log_fy_h_gt = torch.log((s.intrinsics[..., 1, 1] / float(H)).clamp_min(1e-6))
        return {
            "has_4d_teacher": s.has_4d_teacher,
            "depth_gt": s.depth_gt,
            "valid_depth": s.valid_depth,
            "depth_valid": s.valid_depth,
            "metric_scale_locked": s.metric_scale_locked,
            "rot_gt": s.rot_gt,
            "trans_gt": s.trans_gt,
            "gravity_gt": s.gravity_gt,
            "fov_x_gt": s.fov_x_gt,
            "fov_y_gt": s.fov_y_gt,
            "log_fx_w_gt": log_fx_w_gt,
            "log_fy_h_gt": log_fy_h_gt,
            "plucker_gt": s.plucker_gt,
            "y_stat_gt": s.y_stat_gt,
            "p_dyn_gt": s.p_dyn_gt,
            "delta_p_gt": s.delta_p_gt,
            "delta_p_rev": s.delta_p_rev,
            "flow_valid": flow_valid_gated,
            "pmap_gt": s.pmap_gt,
            "pmap_valid": s.pmap_valid,
            "view_mask": s.view_mask,
        }


def _rotation_aligning_to_plus_z(up_vec: np.ndarray) -> np.ndarray:
    """Return proper 3x3 rotation R in SO(3) mapping unit vector `up_vec` to +Z = [0, 0, 1]."""
    u = np.asarray(up_vec, dtype=np.float64)
    norm = float(np.linalg.norm(u))
    if norm < 1e-8 or not np.isfinite(norm):
        return np.eye(3, dtype=np.float64)
    u = u / norm
    z = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    c = float(np.clip(np.dot(u, z), -1.0, 1.0))
    if c > 1.0 - 1e-9:
        return np.eye(3, dtype=np.float64)
    if c < -1.0 + 1e-9:
        return np.diag([1.0, -1.0, -1.0])
    v = np.cross(u, z)
    s = float(np.linalg.norm(v))
    vx = np.array(
        [[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]],
        dtype=np.float64,
    )
    return np.eye(3, dtype=np.float64) + vx + (vx @ vx) * ((1.0 - c) / (s * s))


def load_point4d_store_to_sample(
    point4d_npz_path: str | Path,
    tracks_npz_path: Optional[str | Path] = None,
    gravity_npz_path: Optional[str | Path] = None,
    grid_hw: Tuple[int, int] = (20, 20),
    flow_horizons: Tuple[int, ...] = DEFAULT_FLOW_HORIZONS,
    static_extent_fraction: float = 0.01,
    soft_temp_fraction: float = 0.0025,
    conf_min: float = 0.25,
    track_conf_min: float = 0.20,
    capture_id: Optional[str] = None,
) -> Dynamic4DTeacherSample:
    """Convert a Point4D / Any4D store (`point4d_32/*.npz` + `tracks/*.npz` + `gravity/*.npz`)
    into a `Dynamic4DTeacherSample` aligned to Spatial-V2's `(grid_h, grid_w)` patch grid.
    """
    p3d_path = Path(point4d_npz_path)
    if capture_id is None:
        capture_id = p3d_path.stem
    if tracks_npz_path is None:
        cand_track = p3d_path.parent / "tracks" / p3d_path.name
        if cand_track.is_file():
            tracks_npz_path = cand_track
    if gravity_npz_path is None:
        cand_grav = p3d_path.parent.parent / "gravity" / "stores" / p3d_path.name
        if cand_grav.is_file():
            gravity_npz_path = cand_grav

    with np.load(p3d_path, allow_pickle=False) as d3:
        depth_raw = d3["depth_z"].astype(np.float32)           # [N, H_raw, W_raw]
        intrinsics_raw = d3["intrinsics"].astype(np.float32)   # [N, 3, 3]
        c2w_common = d3["camera_poses"].astype(np.float64)     # [N, 4, 4]
        conf_raw = d3["conf"].astype(np.float32)               # [N, H_raw, W_raw]
        mask_raw = d3["mask"].astype(bool)                     # [N, H_raw, W_raw]
        pts3d_common = d3["pts3d_world"].astype(np.float32)    # [N, H_raw, W_raw, 3]
        timestamps_s = d3["timestamps_s"].astype(np.float32) if "timestamps_s" in d3.files else np.arange(len(depth_raw), dtype=np.float32)

    N, H_raw, W_raw = depth_raw.shape
    H_grid, W_grid = grid_hw

    # Load optional gravity rotation (`common_to_world` aligning floor up-vector to +Z)
    R_c2world = np.eye(3, dtype=np.float64)
    gravity_aligned = False
    if gravity_npz_path is not None and Path(gravity_npz_path).is_file():
        with np.load(gravity_npz_path, allow_pickle=False) as dg:
            up_avail = bool(dg["up_available"].item()) if "up_available" in dg.files else False
            if up_avail and "common_to_world" in dg.files:
                R_c2world = dg["common_to_world"][:3, :3].astype(np.float64)
                gravity_aligned = True
    if not gravity_aligned:
        # Default OpenCV camera-0 has -Y as physical up; map -Y_c0 -> +Z_world
        R_c2world = _rotation_aligning_to_plus_z(np.array([0.0, -1.0, 0.0], dtype=np.float64))

    # Transform c2w into canonical View-0 +Z-up world frame (origin at View-0 camera center)
    t0_common = c2w_common[0, :3, 3].copy()
    R_c2w_world = np.einsum("ij,njk->nik", R_c2world, c2w_common[:, :3, :3])
    t_c2w_world = np.einsum("ij,nj->ni", R_c2world, c2w_common[:, :3, 3] - t0_common[None, :])

    # Convert c2w -> w2c for Spatial-V2 GeoPoseHead & PoseAnd4DLoss
    R_w2c = np.transpose(R_c2w_world, (0, 2, 1)).astype(np.float32)  # [N, 3, 3]
    t_w2c = (-np.einsum("nij,nj->ni", R_w2c, t_c2w_world)).astype(np.float32)  # [N, 3]
    # Unit gravity vector in camera-t frame: world gravity is [0, 0, -1] in +Z-up world
    g_world = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    gravity_cam = np.einsum("nij,j->ni", R_w2c, g_world).astype(np.float32)
    gravity_cam /= np.maximum(np.linalg.norm(gravity_cam, axis=-1, keepdims=True), 1e-8)

    # Estimate robust 5th-to-95th percentile scene extent in world meters
    valid_raw = mask_raw & np.isfinite(depth_raw) & (depth_raw > 1e-3) & (conf_raw >= conf_min)
    if valid_raw.any():
        cloud_common = pts3d_common[valid_raw]
        q95 = np.quantile(cloud_common, 0.95, axis=0)
        q05 = np.quantile(cloud_common, 0.05, axis=0)
        scene_extent_m = float(np.linalg.norm(q95 - q05))
    else:
        scene_extent_m = 5.0
    scene_extent_m = max(scene_extent_m, 0.5)
    tau_stat = static_extent_fraction * scene_extent_m
    tau_temp = max(soft_temp_fraction * scene_extent_m, 1e-4)

    # Downsample / pool depth and valid mask to `(H_grid, W_grid)`
    depth_t = torch.from_numpy(np.where(valid_raw, depth_raw, 0.0)).unsqueeze(1)  # [N, 1, H_raw, W_raw]
    valid_f = torch.from_numpy(valid_raw.astype(np.float32)).unsqueeze(1)
    depth_num = F.adaptive_avg_pool2d(depth_t, (H_grid, W_grid)).squeeze(1)
    valid_den = F.adaptive_avg_pool2d(valid_f, (H_grid, W_grid)).squeeze(1)
    valid_grid = valid_den > 0.25
    depth_grid = torch.where(valid_grid, depth_num / valid_den.clamp_min(1e-6), torch.zeros_like(depth_num))

    # Scale intrinsics K to `(H_grid, W_grid)`
    sx = float(W_grid) / float(W_raw)
    sy = float(H_grid) / float(H_raw)
    K_grid = intrinsics_raw.copy()
    K_grid[:, 0, 0] *= sx
    K_grid[:, 0, 2] *= sx
    K_grid[:, 1, 1] *= sy
    K_grid[:, 1, 2] *= sy
    K_grid_t = torch.from_numpy(K_grid).unsqueeze(0)  # [1, N, 3, 3]

    fov_x = 2.0 * np.arctan((0.5 * W_grid) / np.maximum(K_grid[:, 0, 0], 1e-6))
    fov_y = 2.0 * np.arctan((0.5 * H_grid) / np.maximum(K_grid[:, 1, 1], 1e-6))

    rot_gt_t = torch.from_numpy(R_w2c).unsqueeze(0)      # [1, N, 3, 3]
    trans_gt_t = torch.from_numpy(t_w2c).unsqueeze(0)    # [1, N, 3]
    depth_gt_t = depth_grid.unsqueeze(0)                 # [1, N, H_grid, W_grid]
    valid_depth_t = valid_grid.unsqueeze(0)              # [1, N, H_grid, W_grid]

    # Exact canonical world pointmap `pmap_gt` and Plucker rays `plucker_gt`
    pmap_gt_t = unproject_depth(depth_gt_t, K_grid_t, rot_gt_t, trans_gt_t)  # [1, N, H_grid, W_grid, 3]
    pmap_valid_t = valid_depth_t & torch.isfinite(pmap_gt_t).all(dim=-1)
    pmap_gt_t = torch.where(pmap_valid_t.unsqueeze(-1), pmap_gt_t, torch.zeros_like(pmap_gt_t))
    plucker_gt_t = compute_plucker_rays(K_grid_t, rot_gt_t, trans_gt_t, H_grid, W_grid)  # [1, N, H_grid, W_grid, 6]

    # Process 4D Lagrangian tracks (`tracks_world` [N, Q, 3], `track_confidence` [N, Q], `query_source_slots` [Q], `query_uv` [Q, 2])
    K_h = len(flow_horizons)
    delta_p_np = np.zeros((N, H_grid, W_grid, K_h, 3), dtype=np.float32)
    delta_p_rev_np = np.zeros((N, H_grid, W_grid, K_h, 3), dtype=np.float32)
    flow_valid_np = np.zeros((N, H_grid, W_grid, K_h), dtype=bool)
    p_dyn_np = np.zeros((N, H_grid, W_grid), dtype=np.float32)
    has_4d = False

    if tracks_npz_path is not None and Path(tracks_npz_path).is_file():
        with np.load(tracks_npz_path, allow_pickle=False) as dt:
            tracks_common = dt["tracks_world"].astype(np.float64)        # [N, Q, 3]
            track_conf = dt["track_confidence"].astype(np.float32)       # [N, Q]
            q_slots = dt["query_source_slots"].astype(np.int64)          # [Q]
            q_uv = dt["query_uv"].astype(np.float32)                     # [Q, 2]

        # Transform tracks into canonical View-0 +Z-up world frame
        tracks_world = np.einsum("ij,nqj->nqi", R_c2world, tracks_common - t0_common[None, None, :]).astype(np.float32)
        has_4d = True

        # Grid cell centers in raw pixel coordinates
        gx_centers = (np.arange(W_grid, dtype=np.float32) + 0.5) * (float(W_raw) / float(W_grid))
        gy_centers = (np.arange(H_grid, dtype=np.float32) + 0.5) * (float(H_raw) / float(H_grid))
        grid_xx, grid_yy = np.meshgrid(gx_centers, gy_centers, indexing="xy")
        grid_uv = np.stack([grid_xx.ravel(), grid_yy.ravel()], axis=-1)  # [H_grid*W_grid, 2]

        for t in range(N):
            q_mask = q_slots == t
            if not np.any(q_mask):
                continue
            q_idx = np.where(q_mask)[0]
            uv_t = q_uv[q_idx]                                 # [Q_t, 2]
            xyz_source = tracks_world[t, q_idx]                # [Q_t, 3]
            conf_source = track_conf[t, q_idx]                 # [Q_t]
            all_xyz_q = tracks_world[:, q_idx, :]              # [N, Q_t, 3]
            all_conf_q = track_conf[:, q_idx]                  # [N, Q_t]

            # Max Lagrangian 3D displacement across valid target frames for each query
            valid_traj_q = np.isfinite(all_xyz_q).all(axis=-1) & (all_conf_q >= track_conf_min)  # [N, Q_t]
            disp_all = np.linalg.norm(all_xyz_q - xyz_source[None, :, :], axis=-1)               # [N, Q_t]
            disp_all = np.where(valid_traj_q, disp_all, 0.0)
            max_disp_q = disp_all.max(axis=0)                                                    # [Q_t]
            has_valid_q = valid_traj_q.sum(axis=0) >= 2

            # Soft dynamic probability in [0, 1] anchored at tau_stat = 0.01 * scene_extent
            z_logit = np.clip((max_disp_q - tau_stat) / tau_temp, -20.0, 20.0)
            p_dyn_q = np.where(has_valid_q, 1.0 / (1.0 + np.exp(-z_logit)), 0.0).astype(np.float32)

            # Nearest-query interpolation onto `(H_grid, W_grid)` patch grid
            dist2 = ((grid_uv[:, None, :] - uv_t[None, :, :]) ** 2).sum(axis=-1)  # [G, Q_t]
            nn_q = dist2.argmin(axis=1)                                           # [G]
            p_dyn_np[t] = p_dyn_q[nn_q].reshape(H_grid, W_grid)

            # Populate multi-horizon 3D displacements delta_p_gt and delta_p_rev
            src_ok = np.isfinite(xyz_source).all(axis=-1) & (conf_source >= track_conf_min)
            for k_i, dh in enumerate(flow_horizons):
                t_tgt = t + dh
                if not (0 <= t_tgt < N):
                    continue
                xyz_tgt = all_xyz_q[t_tgt]
                conf_tgt = all_conf_q[t_tgt]
                pair_ok = src_ok & np.isfinite(xyz_tgt).all(axis=-1) & (conf_tgt >= track_conf_min)
                disp_q = np.where(pair_ok[:, None], xyz_tgt - xyz_source, 0.0).astype(np.float32)

                disp_grid = disp_q[nn_q].reshape(H_grid, W_grid, 3)
                ok_grid = pair_ok[nn_q].reshape(H_grid, W_grid) & valid_grid[t].numpy()
                delta_p_np[t, :, :, k_i, :] = np.where(ok_grid[:, :, None], disp_grid, 0.0)
                delta_p_rev_np[t, :, :, k_i, :] = np.where(ok_grid[:, :, None], -disp_grid, 0.0)
                flow_valid_np[t, :, :, k_i] = ok_grid

    y_stat_np = (1.0 - p_dyn_np).astype(np.float32)

    sample = Dynamic4DTeacherSample(
        capture_id=capture_id,
        has_4d_teacher=torch.tensor([has_4d], dtype=torch.bool),
        metric_scale_locked=torch.tensor([True], dtype=torch.bool),
        view_mask=torch.ones((1, N), dtype=torch.bool),
        depth_gt=depth_gt_t,
        valid_depth=valid_depth_t,
        rot_gt=rot_gt_t,
        trans_gt=trans_gt_t,
        gravity_gt=torch.from_numpy(gravity_cam).unsqueeze(0),
        intrinsics=K_grid_t,
        fov_x_gt=torch.from_numpy(fov_x.astype(np.float32)).unsqueeze(0),
        fov_y_gt=torch.from_numpy(fov_y.astype(np.float32)).unsqueeze(0),
        plucker_gt=plucker_gt_t,
        pmap_gt=pmap_gt_t,
        pmap_valid=pmap_valid_t,
        y_stat_gt=torch.from_numpy(y_stat_np).unsqueeze(0),
        p_dyn_gt=torch.from_numpy(p_dyn_np).unsqueeze(0),
        delta_p_gt=torch.from_numpy(delta_p_np).unsqueeze(0),
        delta_p_rev=torch.from_numpy(delta_p_rev_np).unsqueeze(0),
        flow_valid=torch.from_numpy(flow_valid_np).unsqueeze(0),
        timestamps_s=torch.from_numpy(timestamps_s).unsqueeze(0),
        flow_horizons=flow_horizons,
        metadata={
            "source_npz": str(p3d_path),
            "tracks_npz": str(tracks_npz_path) if tracks_npz_path else None,
            "gravity_npz": str(gravity_npz_path) if gravity_npz_path else None,
            "gravity_aligned": gravity_aligned,
            "scene_extent_m": scene_extent_m,
            "tau_stat_m": tau_stat,
            "raw_hw": [H_raw, W_raw],
            "grid_hw": [H_grid, W_grid],
        },
    )
    sample.validate()
    return sample


def certified_stationarity_gate(
    rot_w2c: torch.Tensor,
    trans_w2c: torch.Tensor,
    p_stat: torch.Tensor,
    timestamps_s: torch.Tensor,
    pose_cov_log_diag: Optional[torch.Tensor] = None,
    p_stat_thresh: float = 0.75,
    chi2_thresh: float = 11.345,
    min_disp_m: float = 0.03,
) -> Dict[str, torch.Tensor]:
    """Certified Stationarity Gate (w2_4d_dynamic_streaming.md §5.1).

    Prevents camera speed jitter on stationary scenes by testing whether the camera center
    displacement in the static background frame exceeds the Mahalanobis chi^2 threshold.
    """
    # Camera centers in world frame: c_w = -R_w2c^T t_w2c  [B, N, 3]
    c_w = -torch.einsum("bnij,bnj->bni", rot_w2c.transpose(-1, -2), trans_w2c)
    step_disp = torch.linalg.norm(c_w[:, 1:] - c_w[:, :-1], dim=-1)      # [B, N-1]
    net_disp = torch.linalg.norm(c_w[:, -1] - c_w[:, 0], dim=-1)         # [B]
    path_len = step_disp.sum(dim=-1)                                     # [B]
    dt_total = (timestamps_s[:, -1] - timestamps_s[:, 0]).clamp_min(1e-3)
    raw_speed = path_len / dt_total                                      # [B]

    mean_p_stat = p_stat.mean(dim=(1, 2, 3))                             # [B]

    if pose_cov_log_diag is not None:
        trans_var = torch.exp(pose_cov_log_diag[..., 3:6].clamp(-10.0, 6.0))  # [B, N, 3]
        pair_var = (trans_var[:, :-1] + trans_var[:, 1:]).clamp_min(1e-6)
    else:
        pair_var = torch.full_like(c_w[:, 1:], (min_disp_m ** 2))

    diff = c_w[:, 1:] - c_w[:, :-1]
    chi2_steps = (diff * diff / pair_var).sum(dim=-1)                    # [B, N-1]
    max_chi2 = chi2_steps.max(dim=-1).values                             # [B]

    is_stationary = (mean_p_stat >= p_stat_thresh) & (max_chi2 < chi2_thresh) & (net_disp < min_disp_m)
    gated_speed = torch.where(is_stationary, torch.zeros_like(raw_speed), raw_speed)
    gated_net_disp = torch.where(is_stationary, torch.zeros_like(net_disp), net_disp)

    return {
        "is_stationary": is_stationary,
        "mean_p_stat": mean_p_stat,
        "max_chi2": max_chi2,
        "raw_speed_mps": raw_speed,
        "gated_speed_mps": gated_speed,
        "raw_net_disp_m": net_disp,
        "gated_net_disp_m": gated_net_disp,
        "path_length_m": path_len,
    }


def estimate_ego_and_object_4d_kinematics(
    sample: Dynamic4DTeacherSample,
    horizon_idx: int = 1,
    dyn_prob_thresh: float = 0.5,
) -> Dict[str, Any]:
    """Compute ego camera trajectory kinematics and ego-decoupled dynamic object 3D speed/displacement."""
    gate = certified_stationarity_gate(
        rot_w2c=sample.rot_gt,
        trans_w2c=sample.trans_gt,
        p_stat=sample.y_stat_gt,
        timestamps_s=sample.timestamps_s,
    )
    dh = sample.flow_horizons[horizon_idx]
    flow_k = sample.delta_p_gt[..., horizon_idx, :]   # [B, N, H, W, 3]
    valid_k = sample.flow_valid[..., horizon_idx]     # [B, N, H, W]
    flow_mag = torch.linalg.norm(flow_k, dim=-1)      # [B, N, H, W]

    dyn_mask = valid_k & (sample.p_dyn_gt >= dyn_prob_thresh)
    stat_mask = valid_k & (sample.y_stat_gt > (1.0 - dyn_prob_thresh))

    dt_step = float(
        (sample.timestamps_s[:, 1:] - sample.timestamps_s[:, :-1]).median().clamp_min(1e-3).item()
    ) * abs(dh)

    dyn_disp = float(flow_mag[dyn_mask].mean().item()) if dyn_mask.any() else 0.0
    stat_disp = float(flow_mag[stat_mask].mean().item()) if stat_mask.any() else 0.0

    # Horizontal XY yaw turn from dynamic flow vectors when dynamic pixels exist
    if dyn_mask.any():
        v_dyn = flow_k[dyn_mask]  # [M, 3]
        mean_v_xy = v_dyn[:, :2].mean(dim=0)
        heading_deg = float(math.degrees(math.atan2(float(mean_v_xy[1].item()), float(mean_v_xy[0].item()))))
    else:
        heading_deg = 0.0

    return {
        "capture_id": sample.capture_id,
        "horizon_frames": dh,
        "dt_horizon_s": dt_step,
        "ego_is_stationary": bool(gate["is_stationary"][0].item()),
        "ego_raw_speed_mps": float(gate["raw_speed_mps"][0].item()),
        "ego_gated_speed_mps": float(gate["gated_speed_mps"][0].item()),
        "ego_net_disp_m": float(gate["gated_net_disp_m"][0].item()),
        "ego_path_length_m": float(gate["path_length_m"][0].item()),
        "dynamic_pixel_count": int(dyn_mask.sum().item()),
        "static_pixel_count": int(stat_mask.sum().item()),
        "mean_dynamic_disp_m": dyn_disp,
        "mean_dynamic_speed_mps": dyn_disp / max(dt_step, 1e-4),
        "mean_static_residual_m": stat_disp,
        "dominant_dynamic_heading_deg": heading_deg,
    }


class Dynamic4DExclusionGuard:
    """Fail-closed room/video/take guard covering Spatial-V2 K1 + VSTI-450 + ReSTI/STI + DSI/OSI + Ego-Exo4D + HD-EPIC."""

    def __init__(
        self,
        excl_dir: str | Path = DEFAULT_EXCL_DIR,
        hdepic_prereg_tsv: Optional[str | Path] = "/scratch/jjyeung/lv_me_1122/data/PREREG_62_recordings.tsv",
        hdepic_questions_jsonl: Optional[str | Path] = "/scratch/jjyeung/lv_pt_1122_t714/questions/hdepic_fl_152.jsonl",
    ) -> None:
        self.room_guard = RoomExclusionGuard(excl_dir)
        self.vsti_450_rooms: Set[str] = {
            canonical_room_id(f"scannet/{c}") for c in VSTI_450_SCANNET_CAPTURES
        }
        self.resti_scannet_rooms: Set[str] = set(RESTI_STI_SCANNET_ROOMS)
        self.egoexo_takes: Set[str] = {t.lower() for t in EGOEXO4D_TRACK2_TAKES}
        self.forbidden_corpora: Set[str] = set(FORBIDDEN_EVAL_CORPORA)

        self.hdepic_recordings: Set[str] = set()
        if hdepic_prereg_tsv and Path(hdepic_prereg_tsv).is_file():
            for line in Path(hdepic_prereg_tsv).read_text().splitlines()[1:]:
                parts = line.strip().split("\t")
                if len(parts) >= 3 and parts[2]:
                    self.hdepic_recordings.add(parts[2].strip().lower())
        self.hdepic_sids: Set[str] = set()
        if hdepic_questions_jsonl and Path(hdepic_questions_jsonl).is_file():
            for line in Path(hdepic_questions_jsonl).read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    if row.get("sid"):
                        self.hdepic_sids.add(str(row["sid"]).strip().lower())

    def hits_for_item(
        self,
        identifier: str,
        dataset: Optional[str] = None,
        k1_split: Optional[str] = None,
    ) -> List[str]:
        """Return all blocklist names matching `identifier` (`[]` iff safe for training)."""
        raw = identifier.strip().lower().replace("__", "/")
        if raw.endswith((".mp4", ".npz", ".json", ".png")):
            raw = raw.rsplit(".", 1)[0]
        if dataset:
            ds_clean = dataset.strip().lower()
            full_id = f"{ds_clean}/{raw.split('/')[-1]}" if "/" not in raw else raw
        else:
            full_id = raw

        hits: List[str] = []

        # 1. Check base RoomExclusionGuard (R0, dev-S1, BENCH_v2, withheld-80, K1-heldout)
        if "/" in full_id and full_id.split("/", 1)[0] in ("scannet", "scannetpp", "arkitscenes"):
            hits.extend(self.room_guard.hits_for_capture(full_id, k1_split=k1_split))
        elif full_id.startswith("scene") and len(full_id) >= 9 and full_id[5:9].isdigit():
            sc_id = f"scannet/{full_id}"
            hits.extend(self.room_guard.hits_for_capture(sc_id, k1_split=k1_split))
            full_id = sc_id
        elif full_id.startswith("sti_scene") and len(full_id) >= 13 and full_id[9:13].isdigit():
            sc_id = f"scannet/{full_id[4:]}"
            hits.extend(self.room_guard.hits_for_capture(sc_id, k1_split=k1_split))
            full_id = sc_id

        # 2. Check VSTI-450 ScanNet rooms and ReSTI/STI ScanNet 0000..0149
        if full_id.startswith("scannet/scene"):
            rm = canonical_room_id(full_id)
            if rm in self.vsti_450_rooms and "VSTI-450" not in hits:
                hits.append("VSTI-450")
            if rm in self.resti_scannet_rooms and "ReSTI-ScanNet-150" not in hits:
                hits.append("ReSTI-ScanNet-150")

        # 3. Check forbidden evaluation corpora prefixes & video patterns
        stem = full_id.split("/")[-1]
        prefix = full_id.split("/")[0] if "/" in full_id else ""
        if prefix in self.forbidden_corpora:
            hits.append(f"EvalCorpus:{prefix}")
        if _WAYMO_SEG_RE.match(stem) or (stem.startswith("sti_") and _WAYMO_SEG_RE.match(stem[4:])):
            hits.append("ReSTI-Waymo")
        if _OMNI6D_VID_RE.match(stem):
            hits.append("ReSTI-Omni6DPose")
        if _OSI_VID_RE.match(stem) or stem.startswith("dsi__"):
            hits.append("OSI-DSI-Bench")
        if stem in self.egoexo_takes or full_id in self.egoexo_takes:
            hits.append("Ego-Exo4D-Track2")
        if (
            stem in self.hdepic_recordings
            or stem in self.hdepic_sids
            or _HD_EPIC_REC_RE.match(stem)
        ):
            hits.append("HD-EPIC-Eval")

        return sorted(set(hits))

    def is_blocked(
        self,
        identifier: str,
        dataset: Optional[str] = None,
        k1_split: Optional[str] = None,
    ) -> bool:
        return len(self.hits_for_item(identifier, dataset=dataset, k1_split=k1_split)) > 0

    def verify_all_benchmarks_blocked(self) -> Dict[str, Any]:
        """Run comprehensive canary checks across every dynamic/cross-view benchmark."""
        base_canaries = self.room_guard.verify_canaries()

        # 1. VSTI-450 (all 50 captures + synthetic rescan suffix)
        vsti_blocked = sum(
            1 for c in VSTI_450_SCANNET_CAPTURES
            if self.is_blocked(f"scannet/{c}") and self.is_blocked(f"scannet/{c[:9]}_99")
        )
        if vsti_blocked != len(VSTI_450_SCANNET_CAPTURES):
            raise RuntimeError(f"VSTI-450 leak: {vsti_blocked}/{len(VSTI_450_SCANNET_CAPTURES)}")

        # 2. ReSTI / STI ScanNet rooms (all 150 rooms scene0000..0149, covering all 75 ReSTI ScanNet rooms)
        resti_scannet_blocked = sum(
            1 for r in RESTI_STI_SCANNET_ROOMS
            if self.is_blocked(f"{r}_00") and self.is_blocked(f"{r}_88")
        )
        if resti_scannet_blocked != 150:
            raise RuntimeError(f"ReSTI ScanNet leak: {resti_scannet_blocked}/150")

        # 3. ReSTI Waymo & Omni6DPose + OSI/DSI
        assert self.is_blocked("10203656353524179475_7625_000_7645_000_camera_1.mp4", dataset="Waymo")
        assert self.is_blocked("sti_10203656353524179475_7625_000_7645_000_camera_1.npz")
        assert self.is_blocked("000001.mp4", dataset="Omni6DPose")
        assert self.is_blocked("sti_000001.npz")
        assert self.is_blocked("osi_0002.npz")
        assert self.is_blocked("DSI__hflip__row_000014.json", dataset="dsi")

        # 4. Ego-Exo4D (all 41 Track-2 takes)
        ego_blocked = sum(1 for t in EGOEXO4D_TRACK2_TAKES if self.is_blocked(t, dataset="egoexo4d"))
        if ego_blocked != len(EGOEXO4D_TRACK2_TAKES):
            raise RuntimeError(f"Ego-Exo4D leak: {ego_blocked}/{len(EGOEXO4D_TRACK2_TAKES)}")

        # 5. HD-EPIC (all loaded recordings + sids)
        hd_rec_blocked = sum(1 for r in self.hdepic_recordings if self.is_blocked(r, dataset="hdepic"))
        hd_sid_blocked = sum(1 for s in self.hdepic_sids if self.is_blocked(s, dataset="hdepic"))
        if hd_rec_blocked != len(self.hdepic_recordings) or hd_sid_blocked != len(self.hdepic_sids):
            raise RuntimeError("HD-EPIC leak detected!")

        return {
            "base_canaries": base_canaries,
            "vsti_450_captures_blocked": f"{vsti_blocked}/{len(VSTI_450_SCANNET_CAPTURES)}",
            "resti_sti_scannet_rooms_blocked": f"{resti_scannet_blocked}/150",
            "egoexo4d_takes_blocked": f"{ego_blocked}/{len(EGOEXO4D_TRACK2_TAKES)}",
            "hdepic_recordings_blocked": f"{hd_rec_blocked}/{len(self.hdepic_recordings)}",
            "hdepic_question_sids_blocked": f"{hd_sid_blocked}/{len(self.hdepic_sids)}",
        }

    def audit_k1_train_zero_leak(
        self,
        manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
        frames_root: str | Path = DEFAULT_FRAMES_ROOT,
        excl_dir: str | Path = DEFAULT_EXCL_DIR,
    ) -> Dict[str, Any]:
        """Verify that every single clean Spatial-V2 K1 training capture has 0 hits against all 4D/cross-view benchmarks."""
        train_recs, val_recs, _, summary = build_clean_k1_splits(
            manifest_path=manifest_path,
            frames_root=frames_root,
            excl_dir=excl_dir,
        )
        for r in train_recs:
            hits = self.hits_for_item(r.canonical, dataset=r.dataset, k1_split=r.k1_split)
            if hits:
                raise RuntimeError(f"Leakage in clean K1 train capture {r.canonical}: {hits}")
        return {
            "clean_train_captures": len(train_recs),
            "clean_train_unique_rooms": len({r.room for r in train_recs}),
            "clean_val_captures": len(val_recs),
            "clean_val_unique_rooms": len({r.room for r in val_recs}),
            "split_sha256": summary["split_sha256"],
            "zero_leak_verified": True,
        }
