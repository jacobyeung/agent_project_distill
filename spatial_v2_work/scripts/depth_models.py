"""Standalone V-C (PrivateDepth / PointDepthHead) + Analytical FoV-Fix + DA3-Nested + ScaleAnchor runner.

Loads:
1. V-C (PrivateDepth from m400/heads.pt, SHA256 e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7):
   - Private 27-block Qwen3.5 vision encoder (`depth.model.visual.*`)
   - Private frame queries (`depth.auxiliary_heads.frame_queries`)
   - Private FoV head (`depth.fov.*`)
   - PointDepthHead (`depth.auxiliary_heads.camera.point_depth.*`)
   Constructed without instantiating the 9B language model.
2. Analytical FoV-Fix variants on V-C:
   - `vc_raw`: uses V-C's own predicted FoV `fov_pred = 1e-4 + (pi - 2e-4) * sigmoid(depth.fov(states))`
   - `vc_fovfix_ratio_pred`: multiplies `vc_raw` depth by analytical focal ratio
     `s_fov = tan(fov_pred_w / 2) / tan(hfov_hab / 2)` (where `hfov_hab = 90 deg = pi/2`, `tan(45 deg) = 1.0`),
     converting depth trained under narrow indoor sensor focal lengths (`~58-62 deg`) to 90 deg Habitat focal length.
   - `vc_fovfix_ratio_60deg`: multiplies `vc_raw` depth by canonical narrow-FoV indoor sensor focal ratio
     `s_60 = tan(29 deg) / tan(45 deg) = 0.5543` (`1 / 1.804`, or `1 / 1.94 = 0.5155` for ScanNet/ARKit `~54.6 deg`).
   - `vc_fov_cond90`: passes ground-truth Habitat FoV `[pi/2, pi/2]` directly into `PointDepthHead.encode(..., fov_hw=[pi/2, pi/2])`
     plus focal ratio scaling `tan(fov_pred_w / 2) / tan(45 deg)`.
   - `vc_scale_anchor`: calibrates `vc_raw` per-frame (or rolling median) using the zero-GT Habitat camera-height
     floor-plane ScaleAnchor (`h_cam = 1.25 m`).
3. DA3-Nested (`da3nested-giant-large`, local safetensors `/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors`):
   - `da3_raw`: raw metric depth predicted by DA3-Nested.
   - `da3_fovfix`: DA3 metric depth scaled by analytical focal ratio `f_hab / f_da3` (using DA3's predicted `K` or nominal FoV).
   - `da3_scale_anchor`: DA3 depth calibrated by zero-GT Habitat camera-height floor-plane ScaleAnchor (`h_cam = 1.25 m`).
"""
from __future__ import annotations

import copy
import json
import math
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

VLA_TREE = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872")
EXT_WHERE = Path("/scratch/jjyeung/preserved_20261128/b15_vla/work/orchard_kit/kit/ext_where")
DA3_SRC = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src")
DA3_WEIGHTS = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors")
DA3_CFG = Path("/scratch/jjyeung/geo_bakeoff_kit/assets/da3/config.json")
QWEN_CFG_DIR = Path("/scratch/jjyeung/models/Qwen3.5-9B")
HEADS_PT = Path("/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/m400/vc_depth_only.pt")
ARTIFACT_JSON = Path("/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/m400/artifact.json")

for p in (str(EXT_WHERE), str(VLA_TREE), str(DA3_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)


def compute_floor_scale_anchor(
    depth_hw: np.ndarray,
    hfov_deg: float = 90.0,
    height_m: float = 1.25,
    v_min: float = 0.58,
    v_max: float = 0.95,
    u_min: float = 0.20,
    u_max: float = 0.80,
) -> Tuple[float, dict]:
    """Zero-GT physical camera-height floor-plane ScaleAnchor (`h_cam = 1.25 m`).

    In Habitat R2R-CE, the agent's RGB camera is mounted at known height `h_cam = 1.25 m`
    above the support floor with zero pitch/roll (`hfov = 90 deg`, `W = H = 512`).
    For any pixel `(u, v)` on the horizontal floor plane (`v > 0.5`, downward ray):
      `y_cam = z_metric * (v * H - H / 2) / f_px = h_cam`
      `=> z_floor_analytic(v) = h_cam * f_px / (v * H - H / 2)`
    Wait: we estimate scale using two zero-GT geometric methods:
    1. `g3t_floor_scale` (from `vla_where.nav`): fits floor plane normal via SVD on the lower half
       of the unprojected depth point cloud and returns `s_svd = height_m / h_est`.
    2. Lower-image floor-corridor robust quantile/median ratio (`s_corridor`):
       For pixels in the lower-center floor trapezoid (`v in [v_min, v_max]`, `u in [u_min, u_max]`),
       computes vertical coordinate in predicted depth units `y_pred = d(u, v) * (v - 0.5) / (0.5 * tan(vfov/2))`.
       Since obstacles (walls/furniture) have `d < d_floor` (`y_pred < h_floor`) and the floor is the outer
       lower envelope (`y_pred ~ h_floor`), the 75th-80th percentile (or median when unobstructed) of `y_pred`
       in the bottom center estimates the camera height in model units, giving `s = height_m / h_pred`.
    Returns `(scale_factor, diagnostics_dict)`.
    """
    d = np.asarray(depth_hw, dtype=np.float64)
    H, W = d.shape
    f_px = (W / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
    cx, cy = W / 2.0, H / 2.0

    # Method A: lower-center floor corridor vertical projection y_pred = d * (py - cy) / f_px
    ys = np.arange(int(H * v_min), int(H * v_max))
    xs = np.arange(int(W * u_min), int(W * u_max))
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    d_patch = d[yy, xx]
    valid = np.isfinite(d_patch) & (d_patch > 1e-3)
    if np.sum(valid) < 16:
        return 1.0, {"valid_px": int(np.sum(valid)), "s_median": 1.0, "s_q75": 1.0, "s_svd": 1.0}

    py = yy[valid].astype(np.float64) + 0.5
    d_val = d_patch[valid]
    y_pred = d_val * (py - cy) / f_px  # camera-down coordinate in predicted depth units
    pos = y_pred > 1e-3
    if np.sum(pos) < 16:
        return 1.0, {"valid_px": int(np.sum(pos)), "s_median": 1.0, "s_q75": 1.0, "s_svd": 1.0}

    y_pos = y_pred[pos]
    h_med = float(np.median(y_pos))
    h_q75 = float(np.percentile(y_pos, 75))
    h_q80 = float(np.percentile(y_pos, 80))
    s_median = float(np.clip(height_m / max(h_med, 1e-3), 0.1, 10.0))
    s_q75 = float(np.clip(height_m / max(h_q75, 1e-3), 0.1, 10.0))
    s_q80 = float(np.clip(height_m / max(h_q80, 1e-3), 0.1, 10.0))

    # Method B: vla_where.nav.g3t_floor_scale (SVD plane normal fit on bottom half)
    svd_valid = False
    try:
        from vla_where.nav import g3t_floor_scale
        K = np.array([[f_px, 0.0, cx], [0.0, f_px, cy], [0.0, 0.0, 1.0]], dtype=np.float64)
        up = np.array([0.0, -1.0, 0.0], dtype=np.float64)
        s_svd_val, svd_info = g3t_floor_scale(d, K, up, height_m=height_m)
        if s_svd_val is not None:
            s_svd = float(s_svd_val)
            svd_valid = True
        else:
            # Relax normal/residual threshold slightly if strict 10-deg/0.02 fit rejected a textured floor
            s_svd_Loose, svd_info_loose = g3t_floor_scale(
                d, K, up, height_m=height_m, max_normal_deg=18.0, min_inliers=250, max_residual=0.05
            )
            if s_svd_Loose is not None:
                s_svd = float(s_svd_Loose)
                svd_valid = True
                svd_info = {**svd_info_loose, "relaxed": True}
            else:
                s_svd = float(np.clip(height_m / max(h_q80, 1e-3), 0.1, 10.0))
    except Exception as e:
        s_svd = float(np.clip(height_m / max(h_q80, 1e-3), 0.1, 10.0))
        svd_info = {"why": str(e)}

    return s_svd, {
        "valid_px": int(np.sum(pos)),
        "svd_valid": svd_valid,
        "h_med_pred": h_med,
        "h_q75_pred": h_q75,
        "h_q80_pred": h_q80,
        "s_median": s_median,
        "s_q75": s_q75,
        "s_q80": s_q80,
        "s_svd": s_svd,
        "svd_info": svd_info,
    }


class StandaloneVCDepth(nn.Module):
    """Standalone V-C (`PrivateDepth`) runner loaded directly from `m400/heads.pt` without the 9B LM."""

    def __init__(
        self,
        heads_path: Path = HEADS_PT,
        artifact_path: Path = ARTIFACT_JSON,
        device: str = "cuda",
    ):
        super().__init__()
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5Config
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        from student_pilot.decoupled_v import RECIPE
        from student_pilot.point_depth_head import PointDepthHead, POINT_DEPTH_DEFAULTS

        self.device_str = device
        artifact = json.loads(Path(artifact_path).read_text())
        self.artifact = artifact

        state = torch.load(str(heads_path), map_location="cpu", weights_only=True)
        out_hidden_size = int(state["depth.model.visual.merger.linear_fc2.weight"].shape[0])
        query_dim = int(state["depth.auxiliary_heads.frame_queries"].shape[-1])

        pd_settings = copy.deepcopy(artifact.get("point_depth_head") or POINT_DEPTH_DEFAULTS)
        max_groups = int(state["depth.auxiliary_heads.camera.point_depth.group_embed"].shape[0])
        full_cfg = Qwen3_5Config(
            vision_config={"out_hidden_size": out_hidden_size},
            text_config={"hidden_size": query_dim},
        )
        full_cfg.vision_config.out_hidden_size = out_hidden_size
        full_cfg.p3 = {
            **copy.deepcopy(RECIPE),
            "feature_backing": "decoupled_vc",
            "frame_count": max_groups,
            "anchors": list(range(1, max_groups + 1)),
            "temporal_grouping": "fused_pairs_all_frames",
            "frame_layout": "duplicate",
            "readout": copy.deepcopy(artifact.get("readout_config") or {}),
            "point_depth_head": pd_settings,
        }
        self.config = full_cfg
        vision_cfg = full_cfg.vision_config

        # Construct only the Qwen3.5 Vision transformer (~500M params), NOT the 9B language model
        self.visual = Qwen3_5VisionModel._from_config(vision_cfg)
        vit_dim = int(vision_cfg.hidden_size)
        self.point_depth = PointDepthHead(query_dim, pd_settings, vit_dim)
        if self.point_depth.group_embed.shape[0] != max_groups:
            self.point_depth.group_embed = nn.Parameter(torch.zeros(max_groups, self.point_depth.d_proj))
        self.frame_queries = nn.Parameter(torch.zeros(max_groups, query_dim), requires_grad=False)
        self.fov = nn.Linear(query_dim, 2)

        # Load weights from m400/heads.pt (or vc_depth_only.pt)
        vis_prefix = "depth.model.visual."
        pd_prefix = "depth.auxiliary_heads.camera.point_depth."
        fov_prefix = "depth.fov."

        vis_sd = {k[len(vis_prefix):]: v for k, v in state.items() if k.startswith(vis_prefix)}
        pd_sd = {k[len(pd_prefix):]: v for k, v in state.items() if k.startswith(pd_prefix)}
        fov_sd = {k[len(fov_prefix):]: v for k, v in state.items() if k.startswith(fov_prefix)}

        self.visual.load_state_dict(vis_sd, strict=True)
        self.point_depth.load_state_dict(pd_sd, strict=True)
        self.fov.load_state_dict(fov_sd, strict=True)
        self.frame_queries.data.copy_(state["depth.auxiliary_heads.frame_queries"])

        # Freeze and move to GPU; keep visual parameters in bf16 per decoupled_vc.freeze_for_inference
        self.requires_grad_(False).eval()
        self.to(device)
        for p in self.visual.parameters():
            p.data = p.data.to(torch.bfloat16)

        self.processor = Qwen3VLVideoProcessor(
            patch_size=vision_cfg.patch_size,
            temporal_patch_size=vision_cfg.temporal_patch_size,
            merge_size=vision_cfg.spatial_merge_size,
        )

    @torch.no_grad()
    def infer_single_or_clip(
        self,
        rgb_frames: List[np.ndarray],
        query_grid_size: int = 64,
        hab_hfov_deg: float = 90.0,
    ) -> Dict[str, np.ndarray]:
        """Run V-C on a list of RGB frames (1 to 32 frames, each HxWx3 uint8).

        Follows the exact `duplicate` frame layout used in C1 (`np.repeat(arrays, 2, axis=0)` so each
        viewpoint forms one temporal group `temporal_patch_size=2`).
        Returns dense depth maps resized to `(H, W)` for the last (current decision) frame, plus
        predicted FoV (`fov_vy_deg`, `fov_hx_deg`) and analytical FoV-Fix variants.
        """
        from transformers.video_utils import VideoMetadata
        from student_pilot.decoupled_v import features

        arrays = np.stack([np.asarray(f, dtype=np.uint8) for f in rgb_frames], axis=0)
        K_frames, H, W, _ = arrays.shape
        # Duplicate each viewpoint so each frame is 1 temporal group (temporal_patch_size=2)
        dup_arrays = np.repeat(arrays, 2, axis=0)
        total_dup = dup_arrays.shape[0]
        meta = VideoMetadata(
            total_num_frames=total_dup,
            fps=2.0,
            frames_indices=list(range(total_dup)),
            width=W,
            height=H,
        )
        # Resize to 256x256 multiple of patch_size*merge_size (16*2=32) matching training DEFAULT_PIXELS
        side = 256
        proc_out = self.processor(
            videos=[dup_arrays],
            video_metadata=[meta],
            size={"shortest_edge": side * side, "longest_edge": side * side},
            do_sample_frames=False,
            return_tensors="pt",
        )
        batch = {
            "pixel_values_videos": proc_out["pixel_values_videos"].to(self.device_str),
            "video_grid_thw": proc_out["video_grid_thw"].to(self.device_str),
        }

        heads_ns = SimpleNamespace(
            backing="decoupled_vc",
            camera=SimpleNamespace(point_depth=self.point_depth),
            frame_queries=self.frame_queries,
        )
        visual_owner = nn.Module()
        visual_owner.model = nn.Module()
        visual_owner.model.visual = self.visual
        view = SimpleNamespace(
            config=self.config,
            model=visual_owner.model,
            auxiliary_heads=heads_ns,
            named_modules=visual_owner.named_modules,
            training=False,
            gradient_checkpointing=False,
        )
        captured = features(view, batch, allow_short=True)
        # captured.states: (1, T_groups, hidden_size) where T_groups == K_frames
        states = captured.states.float()
        fov_rad = (1e-4 + (math.pi - 2e-4) * self.fov(states).sigmoid())[0]  # (K_frames, 2) [fov_y, fov_x]

        # Build UV query grid in [0, 1000]^2 of shape (K_frames, G*G, 2) per PointDepthHead.query contract
        axis = torch.linspace(
            (0.5 / query_grid_size) * 1000.0,
            (1.0 - 0.5 / query_grid_size) * 1000.0,
            query_grid_size,
            device=states.device,
        )
        yy, xx = torch.meshgrid(axis, axis, indexing="ij")
        uv = torch.stack((xx, yy), dim=-1).reshape(1, -1, 2).expand(K_frames, -1, -1)

        # 1. Raw V-C depth (using V-C's own predicted FoV)
        latent_raw = self.point_depth.encode(captured.grids[0], captured.vits[0], fov_rad.float())
        d_raw_grid = self.point_depth.query(latent_raw, uv).reshape(K_frames, 1, query_grid_size, query_grid_size)
        d_raw_hw = F.interpolate(d_raw_grid, size=(H, W), mode="bilinear", align_corners=False)[-1, 0]
        d_raw_np = d_raw_hw.detach().cpu().numpy().astype(np.float32)

        # 2. V-C conditioned on true Habitat 90 deg FoV [pi/2, pi/2] inside PointDepthHead.encode
        hab_rad = math.radians(hab_hfov_deg)
        fov_hab = torch.full_like(fov_rad, hab_rad)
        latent_cond90 = self.point_depth.encode(captured.grids[0], captured.vits[0], fov_hab.float())
        d_cond90_grid = self.point_depth.query(latent_cond90, uv).reshape(K_frames, 1, query_grid_size, query_grid_size)
        d_cond90_hw = F.interpolate(d_cond90_grid, size=(H, W), mode="bilinear", align_corners=False)[-1, 0]
        d_cond90_np = d_cond90_hw.detach().cpu().numpy().astype(np.float32)

        # Extract predicted FoV on the last (decision) frame
        pred_fov_y_rad = float(fov_rad[-1, 0].item())
        pred_fov_x_rad = float(fov_rad[-1, 1].item())
        pred_fov_y_deg = math.degrees(pred_fov_y_rad)
        pred_fov_x_deg = math.degrees(pred_fov_x_rad)

        # Analytical focal-length FoV-Fix scale factor:
        # A monocular depth head trained on narrow-FoV indoor RGB-D sensors (fov_train) learns depth
        # proportional to focal length f_train. When fed a wide-FoV (90 deg) image of the same physical scene,
        # objects appear smaller by f_hab / f_train = tan(fov_train / 2) / tan(fov_hab / 2), so the head
        # over-predicts metric depth by f_train / f_hab (~1.80x-1.94x).
        # Multiplying predicted depth by s_fov = tan(fov_train / 2) / tan(fov_hab / 2) corrects the focal mismatch.
        tan_hab = math.tan(hab_rad / 2.0)  # tan(45 deg) = 1.0
        s_fov_pred = math.tan(pred_fov_x_rad / 2.0) / tan_hab
        # Also evaluate the canonical narrow-FoV indoor prior (58 deg -> s = tan(29 deg)/tan(45 deg) = 0.5543,
        # and the prior E0 1.94x empirical drift -> s = 1 / 1.94 = 0.5155 -> effective training HFOV = 54.56 deg)
        s_fov_58deg = math.tan(math.radians(58.0) / 2.0) / tan_hab  # 0.554309
        s_fov_e0_194 = 1.0 / 1.94  # 0.515464 (tan(27.27 deg))

        # Zero-GT camera-height floor-plane ScaleAnchor (`h_cam = 1.25 m`)
        s_anchor, anchor_info = compute_floor_scale_anchor(d_raw_np, hfov_deg=hab_hfov_deg, height_m=1.25)

        return {
            "vc_raw": d_raw_np,
            "vc_cond90_raw": d_cond90_np,
            "vc_fovfix_pred": (d_raw_np * s_fov_pred).astype(np.float32),
            "vc_fovfix_cond90": (d_cond90_np * s_fov_pred).astype(np.float32),
            "vc_fovfix_58deg": (d_raw_np * s_fov_58deg).astype(np.float32),
            "vc_fovfix_e0": (d_raw_np * s_fov_e0_194).astype(np.float32),
            "vc_scale_anchor": (d_raw_np * s_anchor).astype(np.float32),
            "pred_fov_y_deg": pred_fov_y_deg,
            "pred_fov_x_deg": pred_fov_x_deg,
            "s_fov_pred": s_fov_pred,
            "s_fov_58deg": s_fov_58deg,
            "s_fov_e0_194": s_fov_e0_194,
            "s_anchor": s_anchor,
            "anchor_info": anchor_info,
        }


class StandaloneDA3Depth:
    """Standalone DA3-Nested (`da3nested-giant-large`) runner with analytical FoV-Fix & ScaleAnchor."""

    def __init__(self, device: str = "cuda"):
        if "depth_anything_3.utils.export" not in sys.modules:
            sys.modules["depth_anything_3.utils.export"] = SimpleNamespace(export=None)
        from safetensors.torch import load_file
        from depth_anything_3.api import DepthAnything3

        self.device = device
        model = DepthAnything3(model_name="da3nested-giant-large")
        sd = load_file(str(DA3_WEIGHTS), device="cpu")
        model.load_state_dict(sd, strict=False)
        model.to(device)
        model.eval()
        self.model = model

    @torch.no_grad()
    def infer_single_or_window(
        self,
        rgb_frames: List[np.ndarray],
        process_res: int = 504,
        hab_hfov_deg: float = 90.0,
    ) -> Dict[str, np.ndarray]:
        """Run DA3-Nested on 1..N RGB frames and return raw metric depth, FoV-corrected depth, and ScaleAnchor depth."""
        H, W = rgb_frames[-1].shape[:2]
        pred = self.model.inference(
            image=rgb_frames,
            process_res=process_res,
            process_res_method="upper_bound_resize",
            export_dir=None,
        )
        # pred.depth: (N, h_p, w_p)
        d_last = np.asarray(pred.depth[-1], dtype=np.float32)
        if d_last.shape != (H, W):
            d_t = torch.from_numpy(d_last)[None, None]
            d_last = F.interpolate(d_t, size=(H, W), mode="bilinear", align_corners=False)[0, 0].numpy()

        # Extract DA3 predicted intrinsics K if available to get DA3's estimated HFOV
        pred_hfov_deg = 60.0
        s_fov_da3 = 1.0
        if getattr(pred, "intrinsics", None) is not None:
            K_pred = np.asarray(pred.intrinsics[-1], dtype=np.float64)
            fx_pred = float(K_pred[0, 0])
            w_p = float(pred.depth.shape[-1])
            pred_hfov_rad = 2.0 * math.atan((w_p / 2.0) / max(fx_pred, 1e-3))
            pred_hfov_deg = math.degrees(pred_hfov_rad)
            # Focal ratio f_hab / f_da3 = tan(pred_hfov / 2) / tan(hab_hfov / 2)
            s_fov_da3 = math.tan(pred_hfov_rad / 2.0) / math.tan(math.radians(hab_hfov_deg) / 2.0)

        # Zero-GT camera-height floor-plane ScaleAnchor (`h_cam = 1.25 m`)
        s_anchor, anchor_info = compute_floor_scale_anchor(d_last, hfov_deg=hab_hfov_deg, height_m=1.25)

        return {
            "da3_raw": d_last,
            "da3_fovfix": (d_last * s_fov_da3).astype(np.float32),
            "da3_scale_anchor": (d_last * s_anchor).astype(np.float32),
            "da3_scale_median": (d_last * anchor_info["s_median"]).astype(np.float32),
            "da3_scale_svd": (d_last * anchor_info["s_svd"]).astype(np.float32),
            "pred_hfov_deg": pred_hfov_deg,
            "s_fov_da3": s_fov_da3,
            "s_anchor": s_anchor,
            "anchor_info": anchor_info,
        }
