r"""KT-6 Stage-1A Arm C: Pre-Trained Multi-View DA3-Nested Trunk + VLM Geometry Bridge.

Architecture (`da3_multiview_bridge`):
  1. Pre-trained multi-view DA3-Nested trunk (`/scratch/jjyeung/geo_bakeoff_kit/assets/da3`):
     - `model.da3.backbone`: 40-layer DINOv2 ViT-G/14 (`d=1536`, `alt_start=13`, `cat_token=True`)
       with alternating intra-view (even blocks) and cross-view all-pairs global attention
       (odd blocks 13..39) plus learned camera token (`1, 2, 1536`) and 2D RoPE calibrated
       to `DA3`'s native FoV coordinate grid (`rope_max_coord=27`).
     - `model.da3.cam_dec` & `model.da3.head`: pre-trained multi-view camera pose decoder
       and DualDPT relative depth/confidence head.
     - `model.da3_metric`: pre-trained ViT-L/14 metric depth branch aligned to the multi-view
       depth and camera translations via `least_squares_scale_scalar`.
  2. Trunk adaptation modes (`--trunk-mode {last4, lora16, frozen}`):
     - `last4` (default): freezes `blocks[0..35]` and `da3_metric`, runs the 36 frozen blocks
       once under `torch.no_grad()`, and trains the final 4 alternating local/global multi-view
       blocks (`blocks[36..39]`), `backbone.norm`, `cam_dec`, residual `GeoHeads`, and
       `VLMGeometryBridge`. Keeps a lightweight frozen copy of `blocks[36..39]` (`113.6M` params)
       for exact Step-0 `SpatialForcing2Loss` teacher feature anchoring.
     - `lora16`: freezes all backbone weights and injects rank-16 LoRA adapters (`qkv`, `proj`)
       into alternating multi-view blocks `13..39`.
     - `frozen`: freezes the entire `DA3-Nested` trunk and trains only the residual `GeoHeads`
       and `VLMGeometryBridge`.
  3. Residual `ArmCGeoPoseHead` & `ArmCGeoDepthHead`:
     - Zero-initialized residual SE(3) pose refinement `(\Delta \omega, \Delta t, \Delta \log f)`
       around `DA3-Nested`'s metric-scaled multi-view poses so Step 0 preserves `DA3-Nested`'s
       zero-shot multi-view pose accuracy.
     - Multi-view SE(3)-consistent gravity head pooling per-view gravity predictions across all
       `N` views via `R_j^T \tilde{g}_j` in the shared scene frame.
     - Exact orthogonal decomposition of `log(D_da3)` into `(d_shape_da3, mu_view_da3, log_gamma_da3)`
       plus zero-initialized residuals so `DecoupledDepthLoss` starts from `DA3-Nested`'s metric depth
       floor while preserving zero scale gradient on unlocked clips.
  4. Lightweight `VLMGeometryBridge` (`<50 ms`, `d_vlm=4096`, taps `(16, 24, -1)`):
     - Fuses multi-view `DA3` patch tokens (`3072`-d) with explicit 3D geometric embeddings
       (canonical 3D pointmap, Plucker ray map, log-depth, confidence, and gravity) into `d=4096`
       VLM/VLA tokens with an auxiliary linear 3D readout head.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors.torch import load_file

from spatial_v2.geo_heads import (
    GeoDepthOutput,
    GeoPoseOutput,
    build_intrinsics_matrix,
    compute_gravity_leveled_poses,
    compute_plucker_rays,
    matrix_to_rotation_6d,
    so3_exp,
    unproject_depth,
)

DEFAULT_DA3_DIR = "/scratch/jjyeung/geo_bakeoff_kit/assets/da3"
DEFAULT_DA3_SRC = (
    "/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/"
    "Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src"
)
DEFAULT_BAKEOFF_SITE = "/scratch/jjyeung/geo_bakeoff_kit/runtime/site"


def _ensure_da3_importable() -> None:
    for p in (DEFAULT_DA3_SRC, DEFAULT_BAKEOFF_SITE):
        if Path(p).is_dir() and p not in sys.path:
            sys.path.insert(0, p)
    import depth_anything_3  # noqa: F401


@dataclass
class Stage1AArmCOutput:
    """Unified output container for KT-6 Stage-1A Arm C."""

    depth_out: GeoDepthOutput
    pose_out: GeoPoseOutput
    K_pred_merged: torch.Tensor      # [B, N, 3, 3] on (hm, wm)
    K_pred_fine: torch.Tensor        # [B, N, 3, 3] on (grid_h, grid_w)
    pmap_pred: torch.Tensor          # [B, N, H_2, W_2, 3] canonical world frame
    plucker_pred: torch.Tensor       # [B, N, H_m, W_m, 6] canonical world frame
    student_feats: torch.Tensor      # [B, N, P, 3072] post-trunk multi-view patch tokens
    teacher_feats: torch.Tensor      # [B, N, P, 3072] frozen DA3-Giant reference tokens
    vlm_tokens: torch.Tensor         # [B, N, P, d_vlm] projected VLM/VLA visual-geometry tokens
    vlm_tap_tokens: Dict[int, torch.Tensor]  # tap_layer -> [B, N, P, d_vlm]
    vlm_linear_3d_pred: torch.Tensor  # [B, N, P, 10] linear 3D readout from vlm_tokens


class LoRALinear(nn.Module):
    """Low-rank adapter wrapper around a frozen nn.Linear layer."""

    def __init__(self, base: nn.Linear, rank: int = 16, alpha: float = 16.0) -> None:
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.rank = int(rank)
        self.scale = float(alpha) / float(rank)
        self.lora_a = nn.Linear(base.in_features, self.rank, bias=False)
        self.lora_b = nn.Linear(self.rank, base.out_features, bias=False)
        nn.init.kaiming_uniform_(self.lora_a.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_b.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.base(x)
        delta = self.lora_b(self.lora_a(x.to(self.lora_a.weight.dtype))).to(out.dtype)
        return out + self.scale * delta


class CalibratedPositionGetter:
    """2D RoPE patch coordinate generator calibrated to DA3's native FoV grid (`max_coord=27`)."""

    def __init__(self, max_coord: int = 27) -> None:
        self.max_coord = int(max_coord)
        self._cache: Dict[Tuple[int, int, int, torch.device], torch.Tensor] = {}

    def __call__(self, batch_size: int, height: int, width: int, device: torch.device) -> torch.Tensor:
        key = (height, width, self.max_coord, device)
        if key not in self._cache:
            if self.max_coord <= 0 or (height == self.max_coord + 1 and width == self.max_coord + 1):
                y = torch.arange(height, device=device)
                x = torch.arange(width, device=device)
            else:
                y = torch.linspace(0, self.max_coord, height, device=device).round().long()
                x = torch.linspace(0, self.max_coord, width, device=device).round().long()
            self._cache[key] = torch.cartesian_prod(y, x)
        return self._cache[key].reshape(1, height * width, 2).expand(batch_size, -1, -1).clone()


class ArmCGeoPoseHead(nn.Module):
    """Residual SE(3) pose, FoV, and multi-view SE(3)-consistent gravity head around DA3."""

    def __init__(
        self,
        d_in: int = 3072,
        d_hidden: int = 512,
        max_rot_step_rad: float = 0.25,
        max_trans_step_m: float = 0.35,
        max_fov_step: float = 0.35,
    ) -> None:
        super().__init__()
        self.max_rot_step_rad = float(max_rot_step_rad)
        self.max_trans_step_m = float(max_trans_step_m)
        self.max_fov_step = float(max_fov_step)

        self.norm_cam = nn.LayerNorm(d_in)
        self.norm_patch = nn.LayerNorm(d_in)
        self.trunk = nn.Sequential(
            nn.Linear(d_in * 2, d_hidden),
            nn.SiLU(),
            nn.LayerNorm(d_hidden),
            nn.Linear(d_hidden, d_hidden),
            nn.SiLU(),
        )

        # Residual pose & FoV heads (zero-initialized so Step 0 == exact DA3-Nested pose/FoV)
        self.delta_pose_head = nn.Linear(d_hidden, 6)
        self.delta_fov_head = nn.Linear(d_hidden, 2)
        self.cov_head = nn.Linear(d_hidden, 6)
        nn.init.zeros_(self.delta_pose_head.weight)
        nn.init.zeros_(self.delta_pose_head.bias)
        nn.init.zeros_(self.delta_fov_head.weight)
        nn.init.zeros_(self.delta_fov_head.bias)
        nn.init.zeros_(self.cov_head.weight)
        nn.init.zeros_(self.cov_head.bias)

        # Multi-view SE(3)-consistent gravity head:
        # Uses camera token + pooled patch tokens + spatial top/bottom vertical tokens
        self.spatial_grav_proj = nn.Linear(d_in * 2, d_hidden)
        self.grav_mlp = nn.Sequential(
            nn.Linear(d_hidden * 2, d_hidden),
            nn.SiLU(),
            nn.LayerNorm(d_hidden),
            nn.Linear(d_hidden, 4),  # [gx, gy, gz, view_conf_logit]
        )
        nn.init.zeros_(self.grav_mlp[-1].weight)
        with torch.no_grad():
            # Standard upright camera prior: world +Z is -Y in OpenCV camera frame (+X right, +Y down, +Z forward)
            self.grav_mlp[-1].bias.copy_(torch.tensor([0.0, -1.0, 0.0, 0.0]))

        # Learnable blend for per-view residual around multi-view consensus gravity
        self.grav_view_res_logit = nn.Parameter(torch.tensor(-1.5))

    def forward(
        self,
        cam_tokens: torch.Tensor,
        patch_tokens: torch.Tensor,
        grid_hw: Tuple[int, int],
        merged_hw: Tuple[int, int],
        r_da3: torch.Tensor,
        t_da3: torch.Tensor,
        log_fx_w_da3: torch.Tensor,
        log_fy_h_da3: torch.Tensor,
    ) -> GeoPoseOutput:
        bsz, n_views, _, d_in = patch_tokens.shape
        h2, w2 = grid_hw
        hm, wm = merged_hw

        cam_h = self.norm_cam(cam_tokens.float())
        patch_f = self.norm_patch(patch_tokens.float())
        patch_mean = patch_f.mean(dim=2)

        h = self.trunk(torch.cat([cam_h, patch_mean], dim=-1))  # [B, N, d_hidden]

        # 1. Residual SE(3) pose refinement around (r_da3, t_da3)
        raw_pose = self.delta_pose_head(h)
        delta_omega = self.max_rot_step_rad * torch.tanh(raw_pose[..., :3])
        delta_t = self.max_trans_step_m * torch.tanh(raw_pose[..., 3:6])

        delta_r = so3_exp(delta_omega)
        rot = delta_r @ r_da3.float()
        trans = t_da3.float() + delta_t
        rot_6d = matrix_to_rotation_6d(rot)
        pose_cov_log_diag = self.cov_head(h).clamp(min=-6.0, max=4.0)

        # 2. Residual log-FoV refinement around (log_fx_w_da3, log_fy_h_da3)
        raw_fov = self.delta_fov_head(h)
        delta_fov = self.max_fov_step * torch.tanh(raw_fov)
        log_fx_w = (log_fx_w_da3.float() + delta_fov[..., 0]).clamp(min=-2.0, max=2.0)
        log_fy_h = (log_fy_h_da3.float() + delta_fov[..., 1]).clamp(min=-2.0, max=2.0)

        # 3. Multi-view SE(3)-consistent gravity prediction
        patch_grid = patch_f.reshape(bsz, n_views, h2, w2, d_in)
        top_half = patch_grid[:, :, : max(1, h2 // 2), :, :].mean(dim=(2, 3))
        bot_half = patch_grid[:, :, h2 // 2 :, :, :].mean(dim=(2, 3))
        v_feat = self.spatial_grav_proj(torch.cat([top_half, bot_half], dim=-1))
        grav_out = self.grav_mlp(torch.cat([h, v_feat], dim=-1))  # [B, N, 4]

        g_local = F.normalize(grav_out[..., :3], dim=-1, eps=1e-6)  # [B, N, 3] in camera_i frame
        w_views = F.softmax(grav_out[..., 3], dim=1)  # [B, N]

        # Transform each view's predicted gravity into the shared scene reference frame via R_j^T g_j
        r_for_grav = rot.detach()
        g_scene_per_view = torch.einsum("bnij,bni->bnj", r_for_grav, g_local)  # [B, N, 3]
        g_scene_consensus = F.normalize(
            (w_views.unsqueeze(-1) * g_scene_per_view).sum(dim=1),
            dim=-1,
            eps=1e-6,
        )  # [B, 3]
        g_mv = torch.einsum("bnij,bj->bni", r_for_grav, g_scene_consensus)  # [B, N, 3]

        alpha_res = 0.25 * torch.sigmoid(self.grav_view_res_logit)
        gravity = F.normalize(g_mv + alpha_res * g_local, dim=-1, eps=1e-6)

        # 4. Canonical gravity-leveled poses (View 0 at origin, leveled by View 0's gravity)
        rot_canon, trans_canon = compute_gravity_leveled_poses(rot, trans, gravity[:, 0])

        # 5. Plucker rays on merged grid (hm, wm) using rot.detach(), trans.detach() so world-frame
        # leveling updates gravity[:, 0] and intrinsics without twisting relative rotations R_i R_0^T.
        rot_world, trans_world = compute_gravity_leveled_poses(
            rot.detach(), trans.detach(), gravity[:, 0]
        )
        K_merged = build_intrinsics_matrix(log_fx_w, log_fy_h, width=float(wm), height=float(hm))
        plucker_pred = compute_plucker_rays(K_merged, rot_world, trans_world, hm, wm)

        return GeoPoseOutput(
            rot_6d=rot_6d,
            rot=rot,
            trans=trans,
            gravity=gravity,
            log_fx_w=log_fx_w,
            log_fy_h=log_fy_h,
            pose_cov_log_diag=pose_cov_log_diag,
            plucker_pred=plucker_pred,
            rot_canon=rot_canon,
            trans_canon=trans_canon,
        )


class ArmCGeoDepthHead(nn.Module):
    """Residual decoupled shape + view-shift + metric scene-scale depth head around DA3-Nested."""

    def __init__(
        self,
        d_in: int = 3072,
        d_hidden: int = 384,
        min_depth: float = 1e-2,
        max_depth: float = 100.0,
        max_shape_delta: float = 0.60,
        max_shift_delta: float = 0.40,
        max_scale_delta: float = 0.40,
    ) -> None:
        super().__init__()
        self.min_log_depth = math.log(min_depth)
        self.max_log_depth = math.log(max_depth)
        self.max_shape_delta = float(max_shape_delta)
        self.max_shift_delta = float(max_shift_delta)
        self.max_scale_delta = float(max_scale_delta)

        self.token_norm = nn.LayerNorm(d_in)
        self.token_proj = nn.Linear(d_in, d_hidden)
        self.conv = nn.Sequential(
            nn.Conv2d(d_hidden + 2, d_hidden, kernel_size=3, padding=1),
            nn.SiLU(),
            nn.Conv2d(d_hidden, d_hidden, kernel_size=3, padding=1),
            nn.SiLU(),
        )
        # Predicts [delta_d_raw (1), log_var_depth (1)] per patch; zero-init so Step 0 == exact DA3 depth
        self.pixel_head = nn.Conv2d(d_hidden, 2, kernel_size=1)
        nn.init.zeros_(self.pixel_head.weight)
        with torch.no_grad():
            self.pixel_head.bias.copy_(torch.tensor([0.0, -3.0]))

        self.view_shift_head = nn.Sequential(
            nn.Linear(d_hidden, d_hidden // 2),
            nn.SiLU(),
            nn.Linear(d_hidden // 2, 1),
        )
        nn.init.zeros_(self.view_shift_head[-1].weight)
        nn.init.zeros_(self.view_shift_head[-1].bias)

        self.scene_scale_head = nn.Sequential(
            nn.Linear(d_hidden, d_hidden // 2),
            nn.SiLU(),
            nn.Linear(d_hidden // 2, 1),
        )
        nn.init.zeros_(self.scene_scale_head[-1].weight)
        nn.init.zeros_(self.scene_scale_head[-1].bias)

    def forward(
        self,
        patch_tokens: torch.Tensor,
        grid_hw: Tuple[int, int],
        da3_depth_grid: torch.Tensor,
        da3_conf_grid: torch.Tensor,
    ) -> GeoDepthOutput:
        bsz, n_views, _, _ = patch_tokens.shape
        h2, w2 = grid_hw

        # Exact orthogonal decomposition of log(D_da3) on (H_2, W_2):
        # log_d_da3 = d_shape_da3 + mu_view_da3[:, :, None, None] + log_gamma_da3[:, None, None, None]
        log_d_da3 = torch.log(da3_depth_grid.float().clamp(min=1e-2, max=100.0))
        view_mean_da3 = log_d_da3.mean(dim=(-2, -1))  # [B, N]
        log_gamma_da3 = view_mean_da3.mean(dim=1)  # [B]
        mu_view_da3 = view_mean_da3 - log_gamma_da3.unsqueeze(1)  # [B, N], zero-mean across views
        d_shape_da3 = log_d_da3 - view_mean_da3.unsqueeze(-1).unsqueeze(-1)  # [B, N, H_2, W_2], zero-mean per view

        # Residual feature trunk
        x = self.token_proj(self.token_norm(patch_tokens.float()))  # [B, N, P, d_hidden]
        x_2d = x.transpose(2, 3).reshape(bsz * n_views, -1, h2, w2)
        prior_2d = torch.stack(
            [
                d_shape_da3.reshape(bsz * n_views, h2, w2),
                torch.log(da3_conf_grid.float().clamp(min=1e-3)).reshape(bsz * n_views, h2, w2),
            ],
            dim=1,
        )
        feat_2d = self.conv(torch.cat([x_2d, prior_2d], dim=1))  # [B*N, d_hidden, H_2, W_2]
        pix = self.pixel_head(feat_2d)

        delta_raw = self.max_shape_delta * torch.tanh(pix[:, 0]).reshape(bsz, n_views, h2, w2)
        delta_shape = delta_raw - delta_raw.mean(dim=(-2, -1), keepdim=True)
        log_var_depth = pix[:, 1].clamp(min=-6.0, max=4.0).reshape(bsz, n_views, h2, w2)
        sigma_depth = torch.exp(0.5 * log_var_depth)

        pooled_view = feat_2d.mean(dim=(-2, -1)).reshape(bsz, n_views, -1)  # [B, N, d_hidden]
        delta_mu_raw = self.max_shift_delta * torch.tanh(self.view_shift_head(pooled_view).squeeze(-1))
        delta_mu_view = delta_mu_raw - delta_mu_raw.mean(dim=1, keepdim=True)

        pooled_scene = pooled_view.mean(dim=1)  # [B, d_hidden]
        delta_log_gamma = self.max_scale_delta * torch.tanh(self.scene_scale_head(pooled_scene).squeeze(-1))

        d_shape = d_shape_da3 + delta_shape
        mu_view = mu_view_da3 + delta_mu_view
        log_gamma_scene = log_gamma_da3 + delta_log_gamma

        log_depth = (
            d_shape
            + mu_view.unsqueeze(-1).unsqueeze(-1)
            + log_gamma_scene.view(bsz, 1, 1, 1)
        ).clamp(min=self.min_log_depth, max=self.max_log_depth)
        depth = torch.exp(log_depth)

        # Static indoor K1 defaults for 4D rigidity/flow slots
        rigidity_logits = torch.full((bsz, n_views, h2, w2), 6.0, device=depth.device, dtype=depth.dtype)
        p_stat = torch.sigmoid(rigidity_logits)
        delta_p_obj = torch.zeros((bsz, n_views, h2, w2, 4, 3), device=depth.device, dtype=depth.dtype)
        log_var_flow = torch.zeros((bsz, n_views, h2, w2, 4, 1), device=depth.device, dtype=depth.dtype)

        return GeoDepthOutput(
            log_depth=log_depth,
            depth=depth,
            d_shape=d_shape,
            mu_view=mu_view,
            log_gamma_scene=log_gamma_scene,
            log_var_depth=log_var_depth,
            sigma_depth=sigma_depth,
            rigidity_logits=rigidity_logits,
            p_stat=p_stat,
            delta_p_obj=delta_p_obj,
            log_var_flow=log_var_flow,
        )


class VLMGeometryBridge(nn.Module):
    """Lightweight (<50 ms) multi-view 3D geometry bridge into d=4096 VLM/VLA token space."""

    def __init__(
        self,
        d_in: int = 3072,
        d_vlm: int = 4096,
        d_geo: int = 256,
        d_bottleneck: int = 1536,
        tap_layers: Sequence[int] = (16, 24, -1),
    ) -> None:
        super().__init__()
        self.d_in = int(d_in)
        self.d_vlm = int(d_vlm)
        self.tap_layers = tuple(int(x) for x in tap_layers)

        # 17-dim raw 3D coordinates + 4-band Fourier features on (P_world, P_cam) (6 * 8 = 48) -> 65 dims
        self.geo_in_dim = 17 + 6 * 8
        self.geo_encoder = nn.Sequential(
            nn.Linear(self.geo_in_dim, d_geo),
            nn.SiLU(),
            nn.LayerNorm(d_geo),
            nn.Linear(d_geo, d_geo),
            nn.SiLU(),
        )
        self.vis_norm = nn.LayerNorm(d_in)
        self.fuse_proj = nn.Sequential(
            nn.Linear(d_in + d_geo, d_bottleneck),
            nn.SiLU(),
            nn.LayerNorm(d_bottleneck),
            nn.Linear(d_bottleneck, d_vlm),
            nn.LayerNorm(d_vlm),
        )
        self.tap_adapters = nn.ModuleDict(
            {
                str(tap): nn.Sequential(
                    nn.Linear(d_vlm, d_vlm),
                    nn.LayerNorm(d_vlm),
                )
                for tap in self.tap_layers
            }
        )
        # Auxiliary linear 3D readout head directly from vlm_tokens (d=4096 -> 10)
        self.linear_3d_readout = nn.Linear(d_vlm, 10)

    @staticmethod
    def _fourier_encode(coords: torch.Tensor) -> torch.Tensor:
        freqs = (1.0, 2.0, 4.0, 8.0)
        outs = []
        for f in freqs:
            outs.append(torch.sin(coords * f))
            outs.append(torch.cos(coords * f))
        return torch.cat(outs, dim=-1)

    def forward(
        self,
        patch_tokens: torch.Tensor,
        pmap_world: torch.Tensor,
        pmap_cam: torch.Tensor,
        plucker_fine: torch.Tensor,
        log_depth: torch.Tensor,
        sigma_depth: torch.Tensor,
        gravity: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[int, torch.Tensor], torch.Tensor]:
        """
        Args:
            patch_tokens: [B, N, P, 3072]
            pmap_world: [B, N, H_2, W_2, 3]
            pmap_cam: [B, N, H_2, W_2, 3]
            plucker_fine: [B, N, H_2, W_2, 6]
            log_depth: [B, N, H_2, W_2]
            sigma_depth: [B, N, H_2, W_2]
            gravity: [B, N, 3]
        """
        bsz, n_views, n_patches, _ = patch_tokens.shape
        pw = pmap_world.float().reshape(bsz, n_views, n_patches, 3).clamp(min=-20.0, max=20.0)
        pc = pmap_cam.float().reshape(bsz, n_views, n_patches, 3).clamp(min=-20.0, max=20.0)
        pl = plucker_fine.float().reshape(bsz, n_views, n_patches, 6).clamp(min=-10.0, max=10.0)
        ld = log_depth.float().reshape(bsz, n_views, n_patches, 1)
        cf = torch.exp(-sigma_depth.float()).reshape(bsz, n_views, n_patches, 1)
        gv = gravity.float().unsqueeze(2).expand(bsz, n_views, n_patches, 3)

        coords_6 = torch.cat([pw, pc], dim=-1)
        fourier_48 = self._fourier_encode(coords_6)
        geo_raw = torch.cat([pw, pc, pl, ld, cf, gv, fourier_48], dim=-1)  # [B, N, P, 65]

        geo_emb = self.geo_encoder(geo_raw)
        vis_emb = self.vis_norm(patch_tokens.float())
        vlm_tokens = self.fuse_proj(torch.cat([vis_emb, geo_emb], dim=-1))  # [B, N, P, 4096]

        tap_tokens: Dict[int, torch.Tensor] = {}
        for tap in self.tap_layers:
            tap_tokens[tap] = vlm_tokens + 0.1 * self.tap_adapters[str(tap)](vlm_tokens)

        linear_3d_pred = self.linear_3d_readout(vlm_tokens)  # [B, N, P, 10]
        return vlm_tokens, tap_tokens, linear_3d_pred


class Stage1AArmCMultiViewBridge(nn.Module):
    """KT-6 Stage-1A Arm C: Pre-Trained Multi-View DA3-Nested Trunk + VLM Geometry Bridge."""

    def __init__(
        self,
        da3_dir: str = DEFAULT_DA3_DIR,
        trunk_mode: Literal["last4", "lora16", "frozen"] = "last4",
        grid_hw: Tuple[int, int] = (20, 20),
        rope_max_coord: int = 27,
        d_vlm: int = 4096,
        tap_layers: Sequence[int] = (16, 24, -1),
        lora_rank: int = 16,
    ) -> None:
        super().__init__()
        _ensure_da3_importable()
        from depth_anything_3.cfg import create_object, load_config
        from depth_anything_3.model.utils.transform import pose_encoding_to_extri_intri
        from depth_anything_3.utils.geometry import affine_inverse
        from depth_anything_3.utils.alignment import (
            apply_metric_scaling,
            compute_alignment_mask,
            compute_sky_mask,
            least_squares_scale_scalar,
            sample_tensor_for_quantile,
        )

        self._affine_inverse = affine_inverse
        self._pose_encoding_to_extri_intri = pose_encoding_to_extri_intri
        self._apply_metric_scaling = apply_metric_scaling
        self._compute_alignment_mask = compute_alignment_mask
        self._compute_sky_mask = compute_sky_mask
        self._least_squares_scale_scalar = least_squares_scale_scalar
        self._sample_tensor_for_quantile = sample_tensor_for_quantile

        self.da3_dir = str(da3_dir)
        self.trunk_mode = str(trunk_mode)
        self.grid_hw = (int(grid_hw[0]), int(grid_hw[1]))
        self.merged_hw = (int(grid_hw[0]) // 2, int(grid_hw[1]) // 2)
        self.rope_max_coord = int(rope_max_coord)
        self.d_vlm = int(d_vlm)
        self.tap_layers = tuple(int(x) for x in tap_layers)

        wt_path = Path(self.da3_dir) / "model.safetensors"
        if not wt_path.exists():
            raise FileNotFoundError(f"Missing local DA3-Nested weights at {wt_path}")

        yaml_path = Path(DEFAULT_DA3_SRC) / "depth_anything_3" / "configs" / "da3nested-giant-large.yaml"
        da3_nested = create_object(load_config(str(yaml_path)))
        sd = load_file(str(wt_path))
        stripped = {k[len("model.") :] if k.startswith("model.") else k: v for k, v in sd.items()}
        da3_nested.load_state_dict(stripped, strict=False)

        self.da3 = da3_nested.da3
        self.da3.cam_enc = None
        self.da3.gs_head = None
        self.da3_metric = da3_nested.da3_metric

        if self.rope_max_coord > 0:
            self.da3.backbone.pretrained.position_getter = CalibratedPositionGetter(
                max_coord=self.rope_max_coord
            )

        self.da3_metric.requires_grad_(False)
        self.da3_metric.eval()
        self.da3.head.requires_grad_(False)
        self.da3.head.eval()

        vit = self.da3.backbone.pretrained
        self.split_block_idx = 36
        self.frozen_tail_blocks = copy.deepcopy(nn.ModuleList([vit.blocks[i] for i in range(self.split_block_idx, 40)]))
        self.frozen_tail_norm = copy.deepcopy(vit.norm)
        self.frozen_tail_blocks.requires_grad_(False)
        self.frozen_tail_norm.requires_grad_(False)
        self.frozen_tail_blocks.eval()
        self.frozen_tail_norm.eval()

        self._configure_trunk_mode(trunk_mode=self.trunk_mode, lora_rank=lora_rank)

        self.pose_head = ArmCGeoPoseHead(d_in=3072, d_hidden=512)
        self.depth_head = ArmCGeoDepthHead(d_in=3072, d_hidden=384)
        self.vlm_bridge = VLMGeometryBridge(
            d_in=3072,
            d_vlm=self.d_vlm,
            d_geo=256,
            d_bottleneck=1536,
            tap_layers=self.tap_layers,
        )

    def _configure_trunk_mode(self, trunk_mode: str, lora_rank: int = 16) -> None:
        vit = self.da3.backbone.pretrained
        self.da3.backbone.requires_grad_(False)
        self.da3.cam_dec.requires_grad_(False)

        if trunk_mode == "frozen":
            return
        elif trunk_mode == "last4":
            for idx in range(self.split_block_idx, len(vit.blocks)):
                vit.blocks[idx].requires_grad_(True)
            vit.norm.requires_grad_(True)
            self.da3.cam_dec.requires_grad_(True)
        elif trunk_mode == "lora16":
            for idx in range(13, len(vit.blocks)):
                blk = vit.blocks[idx]
                blk.attn.qkv = LoRALinear(blk.attn.qkv, rank=lora_rank, alpha=float(lora_rank))
                blk.attn.proj = LoRALinear(blk.attn.proj, rank=lora_rank, alpha=float(lora_rank))
            vit.norm.requires_grad_(True)
            self.da3.cam_dec.requires_grad_(True)
        else:
            raise ValueError(f"Unsupported trunk_mode={trunk_mode!r}; expected 'last4', 'lora16', or 'frozen'")

    def parameter_Breakdown(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        trunk_trainable = sum(
            p.numel()
            for n, p in self.named_parameters()
            if p.requires_grad and (n.startswith("da3.backbone") or n.startswith("da3.cam_dec"))
        )
        heads_trainable = sum(
            p.numel()
            for n, p in self.named_parameters()
            if p.requires_grad and (n.startswith("pose_head") or n.startswith("depth_head"))
        )
        bridge_trainable = sum(
            p.numel()
            for n, p in self.named_parameters()
            if p.requires_grad and n.startswith("vlm_bridge")
        )
        return {
            "total_params": int(total),
            "trainable_params": int(trainable),
            "trunk_trainable_params": int(trunk_trainable),
            "geo_heads_trainable_params": int(heads_trainable),
            "vlm_bridge_trainable_params": int(bridge_trainable),
        }

    def _run_da3_stem_and_tail(
        self,
        rgb: torch.Tensor,
        ref_view_strategy: str = "saddle_balanced",
    ) -> Tuple[List[Tuple[torch.Tensor, torch.Tensor]], torch.Tensor]:
        from depth_anything_3.model.reference_view_selector import (
            reorder_by_reference,
            restore_original_order,
            select_reference_view,
        )
        from depth_anything_3.utils.constants import THRESH_FOR_REF_SELECTION

        vit = self.da3.backbone.pretrained
        bsz, n_views, _, h, w = rgb.shape
        patch_start = 1 + vit.num_register_tokens

        use_shared_stem = self.trunk_mode in ("last4", "frozen")

        if use_shared_stem:
            with torch.no_grad():
                x = vit.prepare_tokens_with_masks(rgb)
                pos, pos_nodiff = vit._prepare_rope(bsz, n_views, h, w, x.device)
                out_early: List[Tuple[torch.Tensor, torch.Tensor]] = []
                local_x: Optional[torch.Tensor] = None
                b_idx: Optional[torch.Tensor] = None

                for i in range(self.split_block_idx):
                    blk = vit.blocks[i]
                    if i < vit.rope_start or vit.rope is None:
                        g_pos, l_pos = None, None
                    else:
                        g_pos, l_pos = pos_nodiff, pos

                    if (
                        vit.alt_start != -1
                        and i == vit.alt_start - 1
                        and x.shape[1] >= THRESH_FOR_REF_SELECTION
                    ):
                        b_idx = select_reference_view(x, strategy=ref_view_strategy)
                        x = reorder_by_reference(x, b_idx)
                        local_x = reorder_by_reference(local_x, b_idx)

                    if vit.alt_start != -1 and i == vit.alt_start:
                        ref_token = vit.camera_token[:, :1].expand(bsz, -1, -1)
                        src_token = vit.camera_token[:, 1:].expand(bsz, n_views - 1, -1)
                        cam_token = torch.cat([ref_token, src_token], dim=1)
                        x[:, :, 0] = cam_token

                    if vit.alt_start != -1 and i >= vit.alt_start and i % 2 == 1:
                        x = vit.process_attention(x, blk, "global", pos=g_pos)
                    else:
                        x = vit.process_attention(x, blk, "local", pos=l_pos)
                        local_x = x

                    if i in (19, 27, 33):
                        out_x = torch.cat([local_x, x], dim=-1)
                        if b_idx is not None:
                            out_x = restore_original_order(out_x, b_idx)
                        cam_i = out_x[:, :, 0]
                        patch_i = torch.cat(
                            [out_x[..., : vit.embed_dim], vit.norm(out_x[..., vit.embed_dim :])],
                            dim=-1,
                        )[..., patch_start:, :]
                        out_early.append((patch_i, cam_i))

                x_stem = x.detach()
                local_x_stem = local_x.detach()

            if self.trunk_mode == "frozen":
                with torch.no_grad():
                    x_s = x_stem
                    local_s = local_x_stem
                    for idx, blk in enumerate(self.frozen_tail_blocks, start=self.split_block_idx):
                        if idx % 2 == 1:
                            x_s = vit.process_attention(x_s, blk, "global", pos=pos_nodiff)
                        else:
                            x_s = vit.process_attention(x_s, blk, "local", pos=pos)
                            local_s = x_s
                    out_39 = torch.cat([local_s, x_s], dim=-1)
                    if b_idx is not None:
                        out_39 = restore_original_order(out_39, b_idx)
                    c_39 = out_39[:, :, 0]
                    p_39 = torch.cat(
                        [
                            out_39[..., : vit.embed_dim],
                            self.frozen_tail_norm(out_39[..., vit.embed_dim :]),
                        ],
                        dim=-1,
                    )[..., patch_start:, :]
                    teacher_feats = p_39.detach()
            else:
                x_s = x_stem
                local_s = local_x_stem
                for idx in range(self.split_block_idx, len(vit.blocks)):
                    blk = vit.blocks[idx]
                    if idx % 2 == 1:
                        x_s = vit.process_attention(x_s, blk, "global", pos=pos_nodiff)
                    else:
                        x_s = vit.process_attention(x_s, blk, "local", pos=pos)
                        local_s = x_s
                out_39 = torch.cat([local_s, x_s], dim=-1)
                if b_idx is not None:
                    out_39 = restore_original_order(out_39, b_idx)
                c_39 = out_39[:, :, 0]
                p_39 = torch.cat(
                    [out_39[..., : vit.embed_dim], vit.norm(out_39[..., vit.embed_dim :])],
                    dim=-1,
                )[..., patch_start:, :]

                with torch.no_grad():
                    x_t = x_stem
                    local_t = local_x_stem
                    for idx, blk in enumerate(self.frozen_tail_blocks, start=self.split_block_idx):
                        if idx % 2 == 1:
                            x_t = vit.process_attention(x_t, blk, "global", pos=pos_nodiff)
                        else:
                            x_t = vit.process_attention(x_t, blk, "local", pos=pos)
                            local_t = x_t
                    out_t39 = torch.cat([local_t, x_t], dim=-1)
                    if b_idx is not None:
                        out_t39 = restore_original_order(out_t39, b_idx)
                    teacher_feats = torch.cat(
                        [
                            out_t39[..., : vit.embed_dim],
                            self.frozen_tail_norm(out_t39[..., vit.embed_dim :]),
                        ],
                        dim=-1,
                    )[..., patch_start:, :].detach()

            feats = out_early + [(p_39, c_39)]
            return feats, teacher_feats

        feats, _ = self.da3.backbone(
            rgb, cam_token=None, export_feat_layers=[], ref_view_strategy=ref_view_strategy
        )
        p_39 = feats[-1][0]
        teacher_feats = p_39.detach()
        return list(feats), teacher_feats

    @torch.no_grad()
    def _compute_da3_metric_depth_and_scale(
        self,
        rgb: torch.Tensor,
        feats: List[Tuple[torch.Tensor, torch.Tensor]],
        ixts_da3: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        bsz, n_views, _, h, w = rgb.shape
        h2, w2 = self.grid_hw
        ph, pw = h // h2, w // w2

        with torch.amp.autocast("cuda", enabled=False):
            feats_fp32 = [(p.detach().float(), c.detach().float()) for p, c in feats]
            rel_out = self.da3.head(feats_fp32, h, w, patch_start_idx=0)
            rel_depth = rel_out.depth.float()
            rel_conf = rel_out.depth_conf.float()

        with torch.amp.autocast("cuda", dtype=torch.bfloat16, enabled=rgb.is_cuda):
            metric_out = self.da3_metric(rgb)
        metric_depth = metric_out.depth.float()
        metric_sky = metric_out.sky.float()

        metric_scaled = self._apply_metric_scaling(metric_depth, ixts_da3.detach().float())
        non_sky_mask = self._compute_sky_mask(metric_sky, threshold=0.3)

        scale_factors: List[torch.Tensor] = []
        scaled_depths: List[torch.Tensor] = []
        for b in range(bsz):
            ns_b = non_sky_mask[b]
            if ns_b.sum() > 10:
                conf_ns = rel_conf[b][ns_b]
                conf_sampled = self._sample_tensor_for_quantile(conf_ns, max_samples=100000)
                median_conf = torch.quantile(conf_sampled, 0.5)
                align_mask = self._compute_alignment_mask(
                    rel_conf[b], ns_b, rel_depth[b], metric_scaled[b], median_conf
                )
                if align_mask.sum() > 10:
                    sf = self._least_squares_scale_scalar(
                        metric_scaled[b][align_mask],
                        rel_depth[b][align_mask],
                    ).clamp(min=0.05, max=50.0)
                else:
                    sf = torch.ones((), device=rgb.device, dtype=torch.float32)
            else:
                sf = torch.ones((), device=rgb.device, dtype=torch.float32)
            scale_factors.append(sf)
            scaled_depths.append((rel_depth[b] * sf).clamp(min=1e-2, max=100.0))

        scale_factor = torch.stack(scale_factors, dim=0)
        metric_full = torch.stack(scaled_depths, dim=0)

        depth_grid = F.avg_pool2d(
            metric_full.reshape(bsz * n_views, 1, h, w),
            kernel_size=(ph, pw),
            stride=(ph, pw),
        ).reshape(bsz, n_views, h2, w2)
        conf_grid = F.avg_pool2d(
            rel_conf.reshape(bsz * n_views, 1, h, w),
            kernel_size=(ph, pw),
            stride=(ph, pw),
        ).reshape(bsz, n_views, h2, w2)
        return depth_grid, conf_grid, scale_factor

    def forward(
        self,
        batch: Dict[str, torch.Tensor],
        ref_view_strategy: str = "saddle_balanced",
    ) -> Stage1AArmCOutput:
        rgb = batch["rgb_da3"]  # [B, N, 3, 280, 280]
        bsz, n_views, _, h, w = rgb.shape
        h2, w2 = self.grid_hw
        hm, wm = self.merged_hw

        # 1. Run multi-view DA3-Giant alternating-attention trunk
        with torch.amp.autocast("cuda", dtype=torch.bfloat16, enabled=rgb.is_cuda):
            feats, teacher_feats = self._run_da3_stem_and_tail(
                rgb, ref_view_strategy=ref_view_strategy
            )

        patch_tokens_39, cam_tokens_39 = feats[-1]  # [B, N, P, 3072], [B, N, 3072]

        # 2. Decode base multi-view poses & intrinsics via DA3's CameraDec
        with torch.amp.autocast("cuda", enabled=False):
            pose_enc = self.da3.cam_dec(cam_tokens_39.float())  # [B, N, 9]
            c2w_da3, ixts_da3 = self._pose_encoding_to_extri_intri(pose_enc, (h, w))
            w2c_da3 = self._affine_inverse(c2w_da3)  # [B, N, 3, 4]

        # 3. Compute DA3-Nested metric depth grid and least-squares metric scale factor
        # Keep raw ixts_da3 for DA3's metric scaling formula; apply RoPE grid calibration
        # only to the normalized pinhole focal length ratios (fx/W, fy/H).
        da3_depth_grid, da3_conf_grid, scale_factor = self._compute_da3_metric_depth_and_scale(
            rgb, feats, ixts_da3
        )

        fov_rope_scale = (
            (float(h2) / float(self.rope_max_coord + 1)) ** 0.75
            if (self.rope_max_coord > 0 and (self.rope_max_coord + 1) != h2)
            else 1.0
        )
        r_da3 = w2c_da3[:, :, :3, :3]
        t_da3 = w2c_da3[:, :, :3, 3] * scale_factor.view(bsz, 1, 1)
        fx_norm_da3 = (ixts_da3[:, :, 0, 0] * fov_rope_scale / float(w)).clamp(min=0.2, max=4.0)
        fy_norm_da3 = (ixts_da3[:, :, 1, 1] * fov_rope_scale / float(h)).clamp(min=0.2, max=4.0)
        log_fx_w_da3 = torch.log(fx_norm_da3)
        log_fy_h_da3 = torch.log(fy_norm_da3)

        # 4. Run residual ArmCGeoPoseHead & ArmCGeoDepthHead
        pose_out = self.pose_head(
            cam_tokens=cam_tokens_39,
            patch_tokens=patch_tokens_39,
            grid_hw=self.grid_hw,
            merged_hw=self.merged_hw,
            r_da3=r_da3,
            t_da3=t_da3,
            log_fx_w_da3=log_fx_w_da3,
            log_fy_h_da3=log_fy_h_da3,
        )
        depth_out = self.depth_head(
            patch_tokens=patch_tokens_39,
            grid_hw=self.grid_hw,
            da3_depth_grid=da3_depth_grid,
            da3_conf_grid=da3_conf_grid,
        )

        # 5. Build predicted intrinsics and canonical 3D pointmap [B, N, H_2, W_2, 3]
        K_pred_merged = build_intrinsics_matrix(pose_out.log_fx_w, pose_out.log_fy_h, width=float(wm), height=float(hm))
        K_pred_fine = build_intrinsics_matrix(pose_out.log_fx_w, pose_out.log_fy_h, width=float(w2), height=float(h2))

        rot_world, trans_world = compute_gravity_leveled_poses(
            pose_out.rot.detach(),
            pose_out.trans.detach(),
            pose_out.gravity[:, 0],
        )
        pmap_pred = unproject_depth(
            depth=depth_out.depth,
            K=K_pred_fine,
            rot=rot_world,
            trans=trans_world,
        )
        plucker_fine = compute_plucker_rays(K_pred_fine, rot_world, trans_world, h2, w2)

        # Camera-frame 3D pointmap for VLM Geometry Bridge
        eye_r = (
            torch.eye(3, device=rgb.device, dtype=torch.float32)
            .view(1, 1, 3, 3)
            .expand(bsz, n_views, 3, 3)
        )
        zero_t = torch.zeros((bsz, n_views, 3), device=rgb.device, dtype=torch.float32)
        pmap_cam = unproject_depth(
            depth=depth_out.depth,
            K=K_pred_fine,
            rot=eye_r,
            trans=zero_t,
        )

        # 6. Run lightweight (<50 ms) VLM Geometry Bridge into d=4096 VLM/VLA token space
        vlm_tokens, vlm_tap_tokens, vlm_linear_3d_pred = self.vlm_bridge(
            patch_tokens=patch_tokens_39,
            pmap_world=pmap_pred,
            pmap_cam=pmap_cam,
            plucker_fine=plucker_fine,
            log_depth=depth_out.log_depth,
            sigma_depth=depth_out.sigma_depth,
            gravity=pose_out.gravity,
        )

        return Stage1AArmCOutput(
            depth_out=depth_out,
            pose_out=pose_out,
            K_pred_merged=K_pred_merged,
            K_pred_fine=K_pred_fine,
            pmap_pred=pmap_pred,
            plucker_pred=pose_out.plucker_pred,
            student_feats=patch_tokens_39.float(),
            teacher_feats=teacher_feats.float(),
            vlm_tokens=vlm_tokens,
            vlm_tap_tokens=vlm_tap_tokens,
            vlm_linear_3d_pred=vlm_linear_3d_pred,
        )
