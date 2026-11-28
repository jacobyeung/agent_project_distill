"""Mid-trunk GeoHeads: focal-normalized depth, 4D rigidity/flow, SE(3) pose & unprojection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import GeoHeadsConfig
from .epi_adapter import RMSNorm


# ---------------------------------------------------------------------------
# Exact SE(3) / SO(3) & Pinhole Geometry Primitives (fp32-safe, fx < 0 aware)
# ---------------------------------------------------------------------------


def skew_symmetric(w: torch.Tensor) -> torch.Tensor:
    wx, wy, wz = w.unbind(dim=-1)
    z = torch.zeros_like(wx)
    return torch.stack(
        [torch.stack([z, -wz, wy], dim=-1), torch.stack([wz, z, -wx], dim=-1), torch.stack([-wy, wx, z], dim=-1)],
        dim=-2,
    )


def so3_exp(w: torch.Tensor) -> torch.Tensor:
    """Rodrigues exponential map so(3) [..., 3] -> SO(3) [..., 3, 3]."""
    wf = w.float()
    th2 = (wf * wf).sum(dim=-1, keepdim=True)
    th = torch.sqrt(th2 + 1e-16)
    small = th < 1e-4
    a = torch.where(small, 1.0 - th2 / 6.0 + (th2 * th2) / 120.0, torch.sin(th) / th)
    b = torch.where(small, 0.5 - th2 / 24.0 + (th2 * th2) / 720.0, (1.0 - torch.cos(th)) / th2.clamp_min(1e-12))
    k = skew_symmetric(wf)
    eye = torch.eye(3, device=wf.device, dtype=torch.float32).expand_as(k)
    return (eye + a.unsqueeze(-1) * k + b.unsqueeze(-1) * (k @ k)).to(w.dtype)


def so3_log(rot: torch.Tensor) -> torch.Tensor:
    """Logarithm map SO(3) [..., 3, 3] -> so(3) [..., 3] with exact sign-preserving 0/pi guards."""
    rf = rot.float()
    trace = rf[..., 0, 0] + rf[..., 1, 1] + rf[..., 2, 2]
    cos_th = ((trace - 1.0) * 0.5).clamp(-1.0, 1.0)
    vee = torch.stack(
        [rf[..., 2, 1] - rf[..., 1, 2], rf[..., 0, 2] - rf[..., 2, 0], rf[..., 1, 0] - rf[..., 0, 1]], dim=-1
    ) * 0.5
    sin_th = torch.sqrt((vee * vee).sum(dim=-1) + 1e-16)
    th = torch.atan2(sin_th, cos_th)
    small = sin_th < 1e-4
    scale = torch.where(small & (cos_th >= 0.0), 1.0 + (th * th) / 6.0, th / sin_th.clamp_min(1e-7))
    w_reg = vee * scale.unsqueeze(-1)

    near_pi = (sin_th < 1e-3) & (cos_th < 0.0)
    eye = torch.eye(3, device=rf.device, dtype=torch.float32).expand_as(rf)
    b_mat = 0.5 * (rf + rf.transpose(-1, -2)) - cos_th[..., None, None] * eye
    diag = torch.stack([rf[..., 0, 0], rf[..., 1, 1], rf[..., 2, 2]], dim=-1)
    k_star = diag.argmax(dim=-1)
    gather_idx = k_star[..., None, None].expand(*rf.shape[:-1], 1)
    col = b_mat.gather(-1, gather_idx).squeeze(-1)
    axis = col / torch.sqrt((col * col).sum(dim=-1, keepdim=True) + 1e-12)
    dot = (axis * vee).sum(dim=-1, keepdim=True)
    sign = torch.where(dot < -1e-12, -torch.ones_like(dot), torch.ones_like(dot))
    axis = axis * sign
    w_pi = axis * th.unsqueeze(-1) - (vee - vee.detach())
    w = torch.where(near_pi.unsqueeze(-1), w_pi, w_reg)
    return w.to(rot.dtype)


def se3_exp(xi: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Exponential map se(3) [..., 6] ([w, v]) -> (R [..., 3, 3], t [..., 3])."""
    xif = xi.float()
    w, v = xif[..., :3], xif[..., 3:6]
    rot = so3_exp(w)
    th2 = (w * w).sum(dim=-1, keepdim=True)
    th = torch.sqrt(th2 + 1e-16)
    small = th < 1e-4
    b = torch.where(small, 0.5 - th2 / 24.0, (1.0 - torch.cos(th)) / th2.clamp_min(1e-12))
    c = torch.where(small, 1.0 / 6.0 - th2 / 120.0, (th - torch.sin(th)) / (th * th2).clamp_min(1e-12))
    k = skew_symmetric(w)
    eye = torch.eye(3, device=xif.device, dtype=torch.float32).expand_as(k)
    jac = eye + b.unsqueeze(-1) * k + c.unsqueeze(-1) * (k @ k)
    return rot.to(xi.dtype), (jac @ v.unsqueeze(-1)).squeeze(-1).to(xi.dtype)


def se3_log(rot: torch.Tensor, trans: torch.Tensor) -> torch.Tensor:
    """Logarithm map SE(3) (R, t) -> se(3) [..., 6] ([w, v])."""
    w = so3_log(rot).float()
    th2 = (w * w).sum(dim=-1, keepdim=True)
    th = torch.sqrt(th2 + 1e-16)
    small = th < 1e-4
    half = 0.5 * th
    cot_h = torch.cos(half) / torch.sin(half).clamp_min(1e-7)
    coeff = torch.where(small, 1.0 / 12.0 + th2 / 720.0, (1.0 - half * cot_h) / th2.clamp_min(1e-12))
    k = skew_symmetric(w)
    eye = torch.eye(3, device=w.device, dtype=torch.float32).expand_as(k)
    v = ((eye - 0.5 * k + coeff.unsqueeze(-1) * (k @ k)) @ trans.float().unsqueeze(-1)).squeeze(-1)
    return torch.cat([w, v], dim=-1).to(rot.dtype)


def rotation_6d_to_matrix(r6: torch.Tensor) -> torch.Tensor:
    """Continuous 6D rotation [..., 6] -> SO(3) [..., 3, 3] via Gram-Schmidt with degenerate fallbacks."""
    rf = r6.float()
    a1, a2 = rf[..., :3], rf[..., 3:6]
    e_x = torch.tensor([1.0, 0.0, 0.0], device=rf.device, dtype=torch.float32).expand_as(a1)
    e_y = torch.tensor([0.0, 1.0, 0.0], device=rf.device, dtype=torch.float32).expand_as(a1)
    e_z = torch.tensor([0.0, 0.0, 1.0], device=rf.device, dtype=torch.float32).expand_as(a1)
    a1_norm = torch.sqrt((a1 * a1).sum(dim=-1, keepdim=True) + 1e-16)
    a1_safe = torch.where(a1_norm < 1e-6, e_x + (a1 - a1.detach()), a1)
    b1 = a1_safe / torch.sqrt((a1_safe * a1_safe).sum(dim=-1, keepdim=True) + 1e-14)
    orth = a2 - (b1 * a2).sum(dim=-1, keepdim=True) * b1
    orth_norm = torch.sqrt((orth * orth).sum(dim=-1, keepdim=True) + 1e-16)
    alt_basis = torch.where(b1[..., 1:2].abs() < 0.9, e_y, e_z)
    alt_orth = alt_basis - (b1 * alt_basis).sum(dim=-1, keepdim=True) * b1
    orth_safe = torch.where(orth_norm < 1e-6, alt_orth + (orth - orth.detach()), orth)
    b2 = orth_safe / torch.sqrt((orth_safe * orth_safe).sum(dim=-1, keepdim=True) + 1e-14)
    b3 = torch.cross(b1, b2, dim=-1)
    return torch.stack([b1, b2, b3], dim=-1).to(r6.dtype)


def matrix_to_rotation_6d(rot: torch.Tensor) -> torch.Tensor:
    return torch.cat([rot[..., :, 0], rot[..., :, 1]], dim=-1)


def build_intrinsics_matrix(
    log_fx_w: torch.Tensor,
    log_fy_h: torch.Tensor,
    width: float,
    height: float,
    cx: Optional[torch.Tensor] = None,
    cy: Optional[torch.Tensor] = None,
    mirror_x: Optional[torch.Tensor | bool] = None,
) -> torch.Tensor:
    """Build pinhole K [..., 3, 3] with explicit signed fx < 0 support (MuJoCo LIBERO)."""
    fx = torch.exp(log_fx_w.float()) * float(width)
    fy = torch.exp(log_fy_h.float()) * float(height)
    if mirror_x is not None:
        fx = -fx if isinstance(mirror_x, bool) and mirror_x else (
            fx * torch.where(mirror_x.bool(), -1.0, 1.0).to(fx.dtype) if not isinstance(mirror_x, bool) else fx
        )
    cx_t = torch.full_like(fx, 0.5 * float(width)) if cx is None else cx.float()
    cy_t = torch.full_like(fy, 0.5 * float(height)) if cy is None else cy.float()
    z, o = torch.zeros_like(fx), torch.ones_like(fx)
    return torch.stack(
        [torch.stack([fx, z, cx_t], dim=-1), torch.stack([z, fy, cy_t], dim=-1), torch.stack([z, z, o], dim=-1)],
        dim=-2,
    )


def make_pixel_grid(
    height: int, width: int, device: torch.device, dtype: torch.dtype = torch.float32
) -> Tuple[torch.Tensor, torch.Tensor]:
    grid_v, grid_u = torch.meshgrid(
        torch.arange(height, device=device, dtype=dtype) + 0.5,
        torch.arange(width, device=device, dtype=dtype) + 0.5,
        indexing="ij",
    )
    return grid_u, grid_v


def unproject_depth(
    depth: torch.Tensor,
    K: torch.Tensor,
    rot: torch.Tensor,
    trans: torch.Tensor,
    pixel_uv: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
) -> torch.Tensor:
    """Exact pinhole unprojection supporting signed fx < 0: P_world = R^T (D K^{-1} u - t)."""
    df, kf, rf, tf = depth.float(), K.float(), rot.float(), trans.float()
    u, v = make_pixel_grid(df.shape[-2], df.shape[-1], df.device) if pixel_uv is None else (
        pixel_uv[0].float(), pixel_uv[1].float()
    )
    fx, fy = kf[..., 0, 0][..., None, None], kf[..., 1, 1][..., None, None]
    cx, cy = kf[..., 0, 2][..., None, None], kf[..., 1, 2][..., None, None]
    p_cam = torch.stack([(u - cx) / fx * df, (v - cy) / fy * df, df], dim=-1)
    return torch.einsum("...ji,...hwj->...hwi", rf, p_cam - tf[..., None, None, :]).to(depth.dtype)


def project_points(
    points_world: torch.Tensor, K: torch.Tensor, rot: torch.Tensor, trans: torch.Tensor, eps: float = 1e-6
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Exact pinhole projection inverse of unproject_depth (supports fx < 0)."""
    pf, kf, rf, tf = points_world.float(), K.float(), rot.float(), trans.float()
    s_ndim = pf.ndim - rf.ndim + 1
    v_shape = rf.shape[:-2]
    r_exp = rf.reshape(*v_shape, *([1] * s_ndim), 3, 3)
    t_exp = tf.reshape(*v_shape, *([1] * s_ndim), 3)
    k_exp = kf.reshape(*v_shape, *([1] * s_ndim), 3, 3)
    p_cam = (r_exp @ pf.unsqueeze(-1)).squeeze(-1) + t_exp
    z_cam = p_cam[..., 2]
    z_safe = torch.where(z_cam.abs() < eps, torch.full_like(z_cam, eps), z_cam)
    u = k_exp[..., 0, 0] * (p_cam[..., 0] / z_safe) + k_exp[..., 0, 2]
    v = k_exp[..., 1, 1] * (p_cam[..., 1] / z_safe) + k_exp[..., 1, 2]
    return u.to(points_world.dtype), v.to(points_world.dtype), z_cam.to(points_world.dtype)


def compute_gravity_leveled_poses(
    rot: torch.Tensor, trans: torch.Tensor, gravity_cam0: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Transform poses into SE(3)-invariant canonical +Z-up world frame at View 0's center."""
    rf, tf = rot.float(), trans.float()
    g_raw = gravity_cam0.float()
    fwd = torch.tensor([0.0, 0.0, 1.0], device=rf.device, dtype=torch.float32).expand_as(g_raw)
    alt = torch.tensor([1.0, 0.0, 0.0], device=rf.device, dtype=torch.float32).expand_as(g_raw)
    g_norm = torch.sqrt((g_raw * g_raw).sum(dim=-1, keepdim=True) + 1e-16)
    g_safe = torch.where(g_norm < 1e-6, fwd + (g_raw - g_raw.detach()), g_raw)
    e_z = g_safe / torch.sqrt((g_safe * g_safe).sum(dim=-1, keepdim=True) + 1e-14)
    fwd_proj = fwd - (fwd * e_z).sum(dim=-1, keepdim=True) * e_z
    alt_proj = alt - (alt * e_z).sum(dim=-1, keepdim=True) * e_z
    fwd_proj_norm = torch.sqrt((fwd_proj * fwd_proj).sum(dim=-1, keepdim=True) + 1e-16)
    ey_raw = torch.where(fwd_proj_norm < 1e-4, alt_proj, fwd_proj)
    e_y = ey_raw / torch.sqrt((ey_raw * ey_raw).sum(dim=-1, keepdim=True) + 1e-14)
    e_x = torch.cross(e_y, e_z, dim=-1)
    r_canon_from_c0 = torch.stack([e_x, e_y, e_z], dim=-2)
    r_rel = rf @ rf[:, 0:1].transpose(-1, -2)
    rot_canon = r_rel @ r_canon_from_c0.unsqueeze(1).transpose(-1, -2)
    trans_canon = tf - (r_rel @ tf[:, 0:1].unsqueeze(-1)).squeeze(-1)
    return rot_canon.to(rot.dtype), trans_canon.to(trans.dtype)


def compute_plucker_rays(
    K: torch.Tensor, rot: torch.Tensor, trans: torch.Tensor, height: int, width: int
) -> torch.Tensor:
    """Compute dense Plucker raymap [..., H, W, 6] = [dir (3), origin x dir (3)]."""
    kf, rf, tf = K.float(), rot.float(), trans.float()
    u, v = make_pixel_grid(height, width, kf.device)
    fx, fy = kf[..., 0, 0][..., None, None], kf[..., 1, 1][..., None, None]
    cx, cy = kf[..., 0, 2][..., None, None], kf[..., 1, 2][..., None, None]
    ray_cam = torch.stack([(u - cx) / fx, (v - cy) / fy, torch.ones_like(u).expand_as(fx + u)], dim=-1)
    ray_dir = F.normalize(torch.einsum("...ji,...hwj->...hwi", rf, ray_cam), dim=-1, eps=1e-7)
    origin = -torch.einsum("...ji,...j->...i", rf, tf)
    moment = torch.cross(origin[..., None, None, :].expand_as(ray_dir), ray_dir, dim=-1)
    return torch.cat([ray_dir, moment], dim=-1).to(rot.dtype)


# ---------------------------------------------------------------------------
# Mid-Trunk GeoDepthHead & GeoPoseHead
# ---------------------------------------------------------------------------


@dataclass
class GeoDepthOutput:
    log_depth: torch.Tensor
    depth: torch.Tensor
    d_shape: torch.Tensor
    mu_view: torch.Tensor
    log_gamma_scene: torch.Tensor
    log_var_depth: torch.Tensor
    sigma_depth: torch.Tensor
    rigidity_logits: torch.Tensor
    p_stat: torch.Tensor
    delta_p_obj: torch.Tensor
    log_var_flow: torch.Tensor


@dataclass
class GeoPoseOutput:
    rot_6d: torch.Tensor
    rot: torch.Tensor
    trans: torch.Tensor
    gravity: torch.Tensor
    log_fx_w: torch.Tensor
    log_fy_h: torch.Tensor
    pose_cov_log_diag: torch.Tensor
    plucker_pred: torch.Tensor
    rot_canon: torch.Tensor
    trans_canon: torch.Tensor


class _CrossFrameDepthBlock(nn.Module):
    """Lightweight cross-frame attention on downsampled spatial descriptors for depth coherence."""

    def __init__(self, dim: int, num_heads: int) -> None:
        super().__init__()
        self.norm = RMSNorm(dim)
        self.attn = nn.MultiheadAttention(dim, num_heads, batch_first=True)
        self.mlp = nn.Sequential(RMSNorm(dim), nn.Linear(dim, dim * 2), nn.GELU(), nn.Linear(dim * 2, dim))

    def forward(self, x_views: torch.Tensor, key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x_views: [B, N, D]
        h = self.norm(x_views)
        attn_out, _ = self.attn(h, h, h, key_padding_mask=key_padding_mask, need_weights=False)
        x_views = x_views + attn_out
        return x_views + self.mlp(x_views)


class GeoDepthHead(nn.Module):
    """Scale-decoupled metric depth + aleatoric uncertainty + 4D rigidity & scene flow."""

    def __init__(self, cfg: GeoHeadsConfig, lm_hidden_size: int, fine_dim: int) -> None:
        super().__init__()
        self.cfg = cfg
        hid = cfg.depth_hidden_dim
        self.lm_proj = nn.Linear(lm_hidden_size, hid)
        self.fine_proj = nn.Linear(fine_dim, hid)
        self.fov_film = nn.Sequential(nn.Linear(2, hid), nn.SiLU(), nn.Linear(hid, 2 * hid))
        self.cross_blocks = nn.ModuleList(
            [_CrossFrameDepthBlock(hid, cfg.depth_num_heads) for _ in range(cfg.depth_cross_blocks)]
        )
        self.conv_trunk = nn.Sequential(
            nn.Conv2d(hid, hid, 3, padding=1), nn.GroupNorm(min(8, hid), hid), nn.GELU(),
            nn.Conv2d(hid, hid, 3, padding=1), nn.GroupNorm(min(8, hid), hid), nn.GELU(),
        )
        self.shape_head = nn.Conv2d(hid, 1, 3, padding=1)
        self.logvar_head = nn.Conv2d(hid, 1, 3, padding=1)
        self.rigidity_head = nn.Conv2d(hid, 1, 3, padding=1)
        self.flow_head = nn.Conv2d(hid, len(cfg.flow_horizons) * 4, 3, padding=1)
        self.view_shift_head = nn.Linear(hid, 1)
        self.scene_scale_head = nn.Linear(hid, 1)
        self.log_gamma_bias = nn.Parameter(torch.zeros(1))  # weight_decay = 0.0

    def no_weight_decay_parameters(self) -> List[nn.Parameter]:
        return [self.log_gamma_bias, *self.scene_scale_head.parameters()]

    def forward(
        self,
        h_vis: torch.Tensor,
        fine_geo: torch.Tensor,
        log_fx_w: Optional[torch.Tensor] = None,
        log_fy_h: Optional[torch.Tensor] = None,
        view_mask: Optional[torch.Tensor] = None,
    ) -> GeoDepthOutput:
        bsz, n_views, hm, wm, _ = h_vis.shape
        _, _, h_out, w_out, _ = fine_geo.shape
        lm_feat = self.lm_proj(h_vis).reshape(bsz * n_views, hm, wm, -1).permute(0, 3, 1, 2)
        if (hm, wm) != (h_out, w_out):
            lm_feat = F.interpolate(lm_feat, size=(h_out, w_out), mode="bilinear", align_corners=False)
        feat = lm_feat + self.fine_proj(fine_geo).reshape(bsz * n_views, h_out, w_out, -1).permute(0, 3, 1, 2)

        if log_fx_w is not None and log_fy_h is not None:
            fov_in = torch.stack([log_fx_w, log_fy_h], dim=-1).reshape(bsz * n_views, 2).to(feat.dtype)
            gamma, beta = self.fov_film(fov_in).chunk(2, dim=-1)
            feat = feat * (1.0 + gamma[:, :, None, None]) + beta[:, :, None, None]

        # Cross-frame global context conditioning
        if self.cross_blocks:
            ctx = feat.mean(dim=(-2, -1)).reshape(bsz, n_views, -1)
            pad_m = (~view_mask) if view_mask is not None else None
            for blk in self.cross_blocks:
                ctx = blk(ctx, key_padding_mask=pad_m)
            feat = feat + ctx.reshape(bsz * n_views, -1, 1, 1)

        feat = self.conv_trunk(feat)
        d_raw = self.shape_head(feat).reshape(bsz, n_views, h_out, w_out)
        d_shape = d_raw - d_raw.mean(dim=(-2, -1), keepdim=True)

        pooled = feat.mean(dim=(-2, -1)).reshape(bsz, n_views, -1)
        mu_raw = self.view_shift_head(pooled).squeeze(-1)
        if n_views > 1:
            if view_mask is not None:
                vm = view_mask.to(mu_raw.dtype)
                mu_view = (mu_raw - (mu_raw * vm).sum(1, keepdim=True) / vm.sum(1, keepdim=True).clamp_min(1.0)) * vm
            else:
                mu_view = mu_raw - mu_raw.mean(dim=1, keepdim=True)
        else:
            mu_view = torch.zeros_like(mu_raw)

        scene_pool = (
            (pooled * view_mask.to(pooled.dtype).unsqueeze(-1)).sum(1)
            / view_mask.to(pooled.dtype).sum(1, keepdim=True).clamp_min(1.0)
            if view_mask is not None
            else pooled.mean(dim=1)
        )
        log_gamma_scene = self.scene_scale_head(scene_pool).squeeze(-1) + self.log_gamma_bias.to(scene_pool.dtype)
        log_depth = (d_shape + mu_view[:, :, None, None] + log_gamma_scene[:, None, None, None]).clamp(
            self.cfg.min_log_depth, self.cfg.max_log_depth
        )
        log_var_depth = self.logvar_head(feat).reshape(bsz, n_views, h_out, w_out).clamp(
            self.cfg.min_log_var, self.cfg.max_log_var
        )
        rigidity_logits = self.rigidity_head(feat).reshape(bsz, n_views, h_out, w_out)
        flow_raw = (
            self.flow_head(feat)
            .reshape(bsz, n_views, len(self.cfg.flow_horizons), 4, h_out, w_out)
            .permute(0, 1, 4, 5, 2, 3)
        )
        return GeoDepthOutput(
            log_depth=log_depth,
            depth=torch.exp(log_depth),
            d_shape=d_shape,
            mu_view=mu_view,
            log_gamma_scene=log_gamma_scene,
            log_var_depth=log_var_depth,
            sigma_depth=torch.exp(0.5 * log_var_depth),
            rigidity_logits=rigidity_logits,
            p_stat=torch.sigmoid(rigidity_logits),
            delta_p_obj=flow_raw[..., :3],
            log_var_flow=flow_raw[..., 3:4].clamp(self.cfg.min_log_var, self.cfg.max_log_var),
        )


class GeoPoseHead(nn.Module):
    """Bidirectional N-view pose head predicting 6D rot, trans, gravity, FoV, cov & Plucker rays."""

    def __init__(self, cfg: GeoHeadsConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.cfg = cfg
        d = cfg.pose_hidden_dim
        self.cam_proj = nn.Linear(lm_hidden_size, d)
        self.vis_proj = nn.Linear(lm_hidden_size, d)
        self.in_norm = RMSNorm(d)
        enc = nn.TransformerEncoderLayer(
            d_model=d, nhead=cfg.pose_num_heads, dim_feedforward=d * 4,
            activation="gelu", batch_first=True, norm_first=True,
        )
        self.trunk = nn.TransformerEncoder(enc, num_layers=cfg.pose_num_layers, enable_nested_tensor=False)
        self.out_norm = RMSNorm(d)
        self.state_dim = 14
        self.refine_embed = nn.Linear(self.state_dim, d)
        self.refine_delta = nn.Sequential(nn.Linear(d, d), nn.SiLU(), nn.Linear(d, self.state_dim))
        self.cov_head = nn.Linear(d, 6)
        self.plucker_head = nn.Sequential(nn.Linear(d, d // 2), nn.SiLU(), nn.Linear(d // 2, 6))

    def forward(
        self, h_cam: torch.Tensor, h_vis: torch.Tensor, view_mask: Optional[torch.Tensor] = None
    ) -> GeoPoseOutput:
        bsz, n_views = h_vis.shape[:2]
        vis_proj = self.vis_proj(h_vis)
        x = self.in_norm(self.cam_proj(h_cam) + vis_proj.mean(dim=(2, 3)))
        h = self.out_norm(self.trunk(x, src_key_padding_mask=(~view_mask) if view_mask is not None else None))

        state = torch.zeros((bsz, n_views, self.state_dim), device=h.device, dtype=h.dtype)
        state[..., 0], state[..., 4], state[..., 11] = 1.0, 1.0, 1.0
        for _ in range(self.cfg.pose_refine_iters):
            state = state + self.refine_delta(h + self.refine_embed(state))

        rot = rotation_6d_to_matrix(state[..., :6])
        trans = state[..., 6:9]
        g_raw = state[..., 9:12].float()
        g_def = torch.tensor([0.0, 0.0, 1.0], device=g_raw.device, dtype=torch.float32).expand_as(g_raw)
        g_safe = torch.where(torch.sqrt((g_raw * g_raw).sum(dim=-1, keepdim=True) + 1e-16) < 1e-6, g_def + (g_raw - g_raw.detach()), g_raw)
        gravity = (g_safe / torch.sqrt((g_safe * g_safe).sum(dim=-1, keepdim=True) + 1e-14)).to(h.dtype)
        log_fx_w = state[..., 12].clamp(self.cfg.min_log_focal, self.cfg.max_log_focal)
        log_fy_h = state[..., 13].clamp(self.cfg.min_log_focal, self.cfg.max_log_focal)
        plucker_raw = self.plucker_head(vis_proj + h[:, :, None, None, :])
        d_raw = plucker_raw[..., :3].float()
        d_def = torch.tensor([0.0, 0.0, 1.0], device=d_raw.device, dtype=torch.float32).expand_as(d_raw)
        d_safe = torch.where(torch.sqrt((d_raw * d_raw).sum(dim=-1, keepdim=True) + 1e-16) < 1e-6, d_def + (d_raw - d_raw.detach()), d_raw)
        p_dir = d_safe / torch.sqrt((d_safe * d_safe).sum(dim=-1, keepdim=True) + 1e-14)
        p_mom = plucker_raw[..., 3:6].float()
        p_mom = p_mom - (p_dir * p_mom).sum(dim=-1, keepdim=True) * p_dir
        plucker_pred = torch.cat([p_dir, p_mom], dim=-1).to(h.dtype)
        rot_canon, trans_canon = compute_gravity_leveled_poses(rot, trans, gravity[:, 0])
        return GeoPoseOutput(
            rot_6d=state[..., :6], rot=rot, trans=trans, gravity=gravity,
            log_fx_w=log_fx_w, log_fy_h=log_fy_h,
            pose_cov_log_diag=self.cov_head(h).clamp(self.cfg.min_log_var, self.cfg.max_log_var),
            plucker_pred=plucker_pred, rot_canon=rot_canon, trans_canon=trans_canon,
        )
