"""Zero-init Metric 3D-RoPE, Plucker ray injector, and DeltaGeoBias (GeoDecay)."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import torch
import torch.nn as nn

from .config import DeltaGeoBiasConfig, Metric3DRoPEConfig
from .epi_adapter import RMSNorm


def _rotate_pairs(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    xe, xo = x[..., ::2], x[..., 1::2]
    return torch.stack([xe * cos - xo * sin, xe * sin + xo * cos], dim=-1).flatten(-2)


def apply_rope_phases(
    q: torch.Tensor, k: torch.Tensor, phases: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Apply rotary phases [B, 1 or H, L, D_rot//2] to q, k [B, H, L, D_head]."""
    d_rot = phases.shape[-1] * 2
    cos, sin = torch.cos(phases.float()).to(q.dtype), torch.sin(phases.float()).to(q.dtype)
    q_rot, k_rot = _rotate_pairs(q[..., :d_rot], cos, sin), _rotate_pairs(k[..., :d_rot], cos, sin)
    if d_rot < q.shape[-1]:
        q_rot = torch.cat([q_rot, q[..., d_rot:]], dim=-1)
        k_rot = torch.cat([k_rot, k[..., d_rot:]], dim=-1)
    return q_rot, k_rot


class Metric3DRoPE(nn.Module):
    """Zero-init additive Metric 3D-RoPE for upper full-attention layers {16,20,24,28,32}.

    theta_Geo(i) = theta_M-RoPE(i) + beta_h * Omega_3D(P_i), beta_h = 0 at init.
    """

    def __init__(self, cfg: Metric3DRoPEConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.half_rot = cfg.rotary_dim // 2
        bands = max(self.half_rot // 3, 1)
        freqs = torch.exp(torch.linspace(math.log(cfg.omega_min), math.log(cfg.omega_max), bands))
        self.register_buffer("omega", freqs, persistent=True)
        self.beta_h = nn.Parameter(torch.zeros(cfg.num_heads, self.half_rot))  # weight_decay=0.0

    def no_weight_decay_parameters(self) -> List[nn.Parameter]:
        return [self.beta_h]

    @staticmethod
    def anneal_coords(
        coords_own: torch.Tensor,
        coords_teacher: Optional[torch.Tensor] = None,
        teacher_ratio: float = 0.0,
        alpha_loop: float = 0.0,
    ) -> torch.Tensor:
        """Blend teacher -> student 3D coords with straight-through gradient scaling."""
        p_own = alpha_loop * coords_own + (1.0 - alpha_loop) * coords_own.detach()
        if coords_teacher is not None and teacher_ratio > 0.0:
            return teacher_ratio * coords_teacher.detach() + (1.0 - teacher_ratio) * p_own
        return p_own

    def compute_3d_phases(
        self, coords_3d: torch.Tensor, is_visual_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        max_c = float(getattr(self.cfg, "max_coord_abs", 1e4))
        p64 = torch.nan_to_num(coords_3d.double(), nan=0.0, posinf=1e12, neginf=-1e12).clamp(-1e12, 1e12)
        if is_visual_mask is not None:
            vm = is_visual_mask.bool().unsqueeze(-1)
            p64 = torch.where(vm, p64, torch.zeros_like(p64))
            cnt = vm.double().sum(dim=-2, keepdim=True).clamp_min(1.0)
            center = (p64.detach() * vm.double()).sum(dim=-2, keepdim=True) / cnt
            p = torch.where(vm, (p64 - center).float().clamp(-max_c, max_c), torch.zeros_like(p64, dtype=torch.float32))
        else:
            center = p64.detach().mean(dim=-2, keepdim=True) if p64.shape[-2] > 1 else torch.zeros_like(p64)
            p = (p64 - center).float().clamp(-max_c, max_c)
        w = self.omega.float()
        omega_3d = torch.cat([p[..., 0:1] * w, p[..., 1:2] * w, p[..., 2:3] * w], dim=-1)
        if omega_3d.shape[-1] < self.half_rot:
            pad = torch.zeros((*omega_3d.shape[:-1], self.half_rot - omega_3d.shape[-1]), device=p.device)
            omega_3d = torch.cat([omega_3d, pad], dim=-1)
        elif omega_3d.shape[-1] > self.half_rot:
            omega_3d = omega_3d[..., : self.half_rot]
        return omega_3d.unsqueeze(1) * self.beta_h.float()[None, :, None, :]

    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        theta_mrope: torch.Tensor,
        coords_3d: torch.Tensor,
        is_visual_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        base = theta_mrope.float().unsqueeze(1) if theta_mrope.ndim == 3 else theta_mrope.float()
        return apply_rope_phases(q, k, base + self.compute_3d_phases(coords_3d, is_visual_mask=is_visual_mask))


class PluckerGeoInjector(nn.Module):
    """Zero-init full-rank residual MLP injecting 3D world points + Plucker rays into LM states."""

    def __init__(self, cfg: Metric3DRoPEConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.cfg = cfg
        self.register_buffer("fourier_freqs", (2.0 ** torch.arange(cfg.fourier_bands).float()) * math.pi)
        in_dim = 3 * 2 * cfg.fourier_bands + 3 + 6 + 3
        hid = cfg.injector_hidden_dim
        self.mlp = nn.Sequential(nn.Linear(in_dim, hid), nn.SiLU(), RMSNorm(hid), nn.Linear(hid, hid), nn.SiLU())
        self.out_proj = nn.Linear(hid, lm_hidden_size, bias=True)
        nn.init.zeros_(self.out_proj.weight)
        nn.init.zeros_(self.out_proj.bias)

    def forward(
        self,
        h_lm: torch.Tensor,
        coords_3d: torch.Tensor,
        plucker_rays: torch.Tensor,
        log_depth: torch.Tensor,
        confidence: torch.Tensor,
        p_stat: torch.Tensor,
        is_visual_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        max_c = float(getattr(self.cfg, "max_coord_abs", 1e4))
        c_safe = torch.nan_to_num(coords_3d.float(), nan=0.0, posinf=max_c, neginf=-max_c).clamp(-max_c, max_c)
        r_safe = torch.nan_to_num(plucker_rays.float(), nan=0.0, posinf=max_c, neginf=-max_c).clamp(-max_c, max_c)
        ld_safe = torch.nan_to_num(log_depth.float(), nan=0.0, posinf=20.0, neginf=-20.0).clamp(-20.0, 20.0)
        cf_safe = torch.nan_to_num(confidence.float(), nan=0.0, posinf=1.0, neginf=0.0).clamp(0.0, 1.0)
        ps_safe = torch.nan_to_num(p_stat.float(), nan=0.0, posinf=1.0, neginf=0.0).clamp(0.0, 1.0)
        ang = c_safe.unsqueeze(-1) * self.fourier_freqs.float()
        fourier = torch.cat([torch.sin(ang), torch.cos(ang)], dim=-1).flatten(-2).to(h_lm.dtype)
        scalars = torch.stack([ld_safe, cf_safe, ps_safe], dim=-1).to(h_lm.dtype)
        feats = torch.cat([fourier, c_safe.to(h_lm.dtype), r_safe.to(h_lm.dtype), scalars], dim=-1)
        delta = self.out_proj(self.mlp(feats))
        if is_visual_mask is not None:
            delta = delta * is_visual_mask.to(delta.dtype).unsqueeze(-1)
        return h_lm + delta


class DeltaGeoBias(nn.Module):
    """Zero-init GeoDecay gate bias for upper Gated DeltaNet layers {17..31}."""

    def __init__(self, cfg: DeltaGeoBiasConfig) -> None:
        super().__init__()
        self.proj = nn.Linear(cfg.cue_dim, 2 * cfg.num_heads, bias=True)
        nn.init.zeros_(self.proj.weight)
        nn.init.zeros_(self.proj.bias)

    def forward(
        self,
        log_alpha_base: torch.Tensor,
        logit_beta_base: torch.Tensor,
        geo_cues: torch.Tensor,
        is_visual_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        delta = self.proj(geo_cues.to(self.proj.weight.dtype))
        if is_visual_mask is not None:
            delta = delta * is_visual_mask.to(delta.dtype).unsqueeze(-1)
        d_la, d_lb = delta.chunk(2, dim=-1)
        return log_alpha_base + d_la.to(log_alpha_base.dtype), logit_beta_base + d_lb.to(logit_beta_base.dtype)


def deltanet_3d_step(
    state: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    q: torch.Tensor,
    log_alpha: torch.Tensor,
    logit_beta: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Single differentiable Gated DeltaNet recurrent step on state [B, H, D_k, D_v]."""
    alpha = torch.exp(log_alpha.float().clamp(-10.0, 0.0))[..., None, None]
    beta = torch.sigmoid(logit_beta.float())[..., None, None]
    kf, vf, qf, sf = k.float(), v.float(), q.float(), state.float()
    sk = torch.einsum("bhkv,bhk->bhv", sf, kf)
    new_state = alpha * (sf - beta * torch.einsum("bhk,bhv->bhkv", kf, sk)) + beta * torch.einsum("bhk,bhv->bhkv", kf, vf)
    return torch.einsum("bhkv,bhk->bhv", new_state, qf).to(v.dtype), new_state.to(state.dtype)
