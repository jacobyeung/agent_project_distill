"""Pre-LM EpiAdapter: permutation-invariant alternating 2D/global epipolar blocks."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import EpiAdapterConfig, ViewSetBatch


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        xf = x.float()
        return (xf * torch.rsqrt(xf.pow(2).mean(dim=-1, keepdim=True) + self.eps) * self.weight.float()).to(x.dtype)


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    return torch.stack((-x[..., 1::2], x[..., ::2]), dim=-1).flatten(-2)


def apply_2d_axial_rope(
    q: torch.Tensor, k: torch.Tensor, h: int, w: int, has_cam_token: bool = True, base: float = 10000.0
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Apply 2D axial RoPE (u, v) to patch tokens; leave leading [CAM] token unrotated."""
    d_head = q.shape[-1]
    half, quarter = d_head // 2, d_head // 4
    if quarter == 0:
        return q, k
    device = q.device
    inv_freq = 1.0 / (base ** (torch.arange(0, quarter, device=device, dtype=torch.float32) / quarter))
    grid_y, grid_x = torch.meshgrid(
        torch.arange(h, device=device, dtype=torch.float32),
        torch.arange(w, device=device, dtype=torch.float32),
        indexing="ij",
    )
    angles = torch.cat([grid_y.reshape(-1, 1) * inv_freq, grid_x.reshape(-1, 1) * inv_freq], dim=-1)
    if angles.shape[-1] < half:
        angles = F.pad(angles, (0, half - angles.shape[-1]))
    cos_p = torch.repeat_interleave(torch.cos(angles), 2, dim=-1)
    sin_p = torch.repeat_interleave(torch.sin(angles), 2, dim=-1)
    if has_cam_token:
        cos_p = torch.cat([torch.ones((1, d_head), device=device), cos_p], dim=0)
        sin_p = torch.cat([torch.zeros((1, d_head), device=device), sin_p], dim=0)
    cos_p = cos_p.to(q.dtype).view(1, 1, -1, d_head)
    sin_p = sin_p.to(q.dtype).view(1, 1, -1, d_head)
    return q * cos_p + _rotate_half(q) * sin_p, k * cos_p + _rotate_half(k) * sin_p


class _MultiHeadAttention(nn.Module):
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.0) -> None:
        super().__init__()
        if d_model % num_heads != 0:
            raise ValueError(f"d_model={d_model} not divisible by num_heads={num_heads}")
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = dropout

    def forward(
        self,
        x: torch.Tensor,
        rope_hw: Optional[Tuple[int, int]] = None,
        has_cam_token: bool = True,
        key_valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bsz, seqlen, dim = x.shape
        q, k, v = self.qkv(x).view(bsz, seqlen, 3, self.num_heads, self.head_dim).unbind(dim=2)
        q, k, v = q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
        if rope_hw is not None:
            q, k = apply_2d_axial_rope(q, k, rope_hw[0], rope_hw[1], has_cam_token=has_cam_token)
        attn_mask = key_valid_mask[:, None, None, :] if key_valid_mask is not None else None
        out = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attn_mask, dropout_p=self.dropout if self.training else 0.0, is_causal=False
        )
        return self.proj(out.transpose(1, 2).contiguous().view(bsz, seqlen, dim))


class EpiBlock(nn.Module):
    """Alternating intra-frame 2D-RoPE attention + permutation-invariant global attention."""

    def __init__(self, d_model: int, num_heads: int, mlp_ratio: float = 4.0, dropout: float = 0.0) -> None:
        super().__init__()
        self.norm_intra = RMSNorm(d_model)
        self.intra_attn = _MultiHeadAttention(d_model, num_heads, dropout=dropout)
        self.norm_global = RMSNorm(d_model)
        self.global_attn = _MultiHeadAttention(d_model, num_heads, dropout=dropout)
        self.norm_mlp = RMSNorm(d_model)
        hid = int(d_model * mlp_ratio)
        self.mlp = nn.Sequential(nn.Linear(d_model, hid), nn.GELU(), nn.Linear(hid, d_model))

    def forward(
        self, x: torch.Tensor, hm: int, wm: int, view_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        bsz, n_views, tok_per_view, dim = x.shape
        x_in = x.reshape(bsz * n_views, tok_per_view, dim)
        x = (x_in + self.intra_attn(self.norm_intra(x_in), rope_hw=(hm, wm), has_cam_token=True)).reshape(
            bsz, n_views, tok_per_view, dim
        )
        key_valid = (
            view_mask.unsqueeze(-1).expand(bsz, n_views, tok_per_view).reshape(bsz, -1)
            if view_mask is not None
            else None
        )
        x_g = x.reshape(bsz, n_views * tok_per_view, dim)
        x = (x_g + self.global_attn(self.norm_global(x_g), key_valid_mask=key_valid)).reshape(
            bsz, n_views, tok_per_view, dim
        )
        x = x + self.mlp(self.norm_mlp(x))
        return x * view_mask[:, :, None, None].to(x.dtype) if view_mask is not None else x


def _sinusoidal_stream_embedding(stream_ids: torch.Tensor, dim: int, base: float = 10000.0) -> torch.Tensor:
    """Deterministic sinusoidal/Fourier embedding for arbitrary integer stream IDs (>=0, no 16-stream clamp)."""
    half = max(dim // 2, 1)
    freqs = torch.exp(
        -math.log(base) * torch.arange(half, device=stream_ids.device, dtype=torch.float32) / max(half, 1)
    )
    args = stream_ids.float().unsqueeze(-1) * (freqs.unsqueeze(0) + 0.137)
    emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
    if emb.shape[-1] < dim:
        emb = F.pad(emb, (0, dim - emb.shape[-1]))
    return emb[..., :dim]


class StreamMetadataEncoder(nn.Module):
    """Encodes ViewSet-Unified (stream_id, timestamp, is_video) for arbitrary >16 stream IDs without collision."""

    def __init__(self, d_model: int, max_streams: int = 16) -> None:
        super().__init__()
        self.d_model = d_model
        self.max_streams = max_streams
        self.stream_mlp = nn.Sequential(nn.Linear(d_model, d_model), nn.SiLU(), nn.Linear(d_model, d_model))
        self.meta_mlp = nn.Sequential(nn.Linear(2, d_model), nn.SiLU(), nn.Linear(d_model, d_model))
        nn.init.zeros_(self.stream_mlp[-1].weight)
        nn.init.zeros_(self.stream_mlp[-1].bias)
        nn.init.zeros_(self.meta_mlp[-1].weight)
        nn.init.zeros_(self.meta_mlp[-1].bias)

    def forward(self, viewset: ViewSetBatch) -> torch.Tensor:
        dtype = self.meta_mlp[0].weight.dtype
        s_fourier = _sinusoidal_stream_embedding(viewset.stream_ids, self.d_model).to(dtype)
        s_emb = s_fourier + self.stream_mlp(s_fourier)
        cont = torch.stack([viewset.is_video, viewset.timestamps], dim=-1).to(dtype)
        out = s_emb + self.meta_mlp(cont)
        return out * viewset.view_mask.unsqueeze(-1).to(out.dtype)


def pack_views_for_temporal_patch2(
    views: torch.Tensor, viewset: ViewSetBatch
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Pre-ViT view packer enforcing cross-camera isolation BEFORE temporal_patch=2 patch embedding.

    Given `views` of shape `[B, N, ...]` (e.g. raw RGB images `[B, N, C, H, W]`), constructs
    temporal pairs `[B, N, 2, ...]` where adjacent views `(i, i+1)` share a 2-frame pair ONLY if
    `viewset.temporal_merge_allowed[:, i]` is True (same camera stream, valid, and video mode).
    Isolated views are duplicated `[v_i, v_i]` along the temporal_patch=2 axis so a 2-frame 3D
    patch embedder never bleeds information across distinct cameras.
    """
    bsz, n_views = views.shape[:2]
    rest_shape = views.shape[2:]
    exp_ones = (1,) * len(rest_shape)
    vm = viewset.view_mask.view(bsz, n_views, *exp_ones).to(views.dtype)
    v_masked = views * vm

    f0 = v_masked.clone()
    f1 = v_masked.clone()
    isolated = torch.ones((bsz, n_views), dtype=torch.bool, device=views.device)

    for i in range(0, n_views - 1, 2):
        can_merge = viewset.temporal_merge_allowed[:, i] & viewset.view_mask[:, i] & viewset.view_mask[:, i + 1]
        if can_merge.any():
            m_bool = can_merge.view(bsz, *exp_ones)
            f1[:, i] = torch.where(m_bool, v_masked[:, i + 1], v_masked[:, i])
            f0[:, i + 1] = torch.where(m_bool, v_masked[:, i], v_masked[:, i + 1])
            isolated[:, i] = ~can_merge
            isolated[:, i + 1] = ~can_merge

    packed_pairs = torch.stack([f0, f1], dim=2) * vm.unsqueeze(2)
    return packed_pairs, isolated


def prevent_temporal_patch_bleeding(
    vis_tokens: torch.Tensor,
    viewset: ViewSetBatch,
    temporal_patch_embed: Optional[Callable[[torch.Tensor], torch.Tensor] | nn.Module] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Isolate temporal_patch=2 packing/embedding across distinct cameras or non-video views.

    Packs `[B, N, ...]` into isolated temporal pairs `[B, N, 2, ...]` via `pack_views_for_temporal_patch2`
    first, then applies `temporal_patch_embed` (e.g. `nn.Conv3d` with `kernel_size=(2, P, P)`) or
    2-frame temporal pooling before ViT blocks run.
    """
    packed_pairs, isolated = pack_views_for_temporal_patch2(vis_tokens, viewset)
    if temporal_patch_embed is not None:
        if isinstance(temporal_patch_embed, nn.Conv3d) and packed_pairs.ndim == 6:
            # packed_pairs: [B, N, 2, C, H, W] -> Conv3d expects [B*N, C, 2, H, W]
            bsz, n_views, t_p, c, h, w = packed_pairs.shape
            x_3d = packed_pairs.permute(0, 1, 3, 2, 4, 5).reshape(bsz * n_views, c, t_p, h, w)
            emb = temporal_patch_embed(x_3d)  # [B*N, D, 1, H', W']
            _, d_out, _, hp, wp = emb.shape
            out = emb.squeeze(2).permute(0, 2, 3, 1).reshape(bsz, n_views, hp, wp, d_out)
        else:
            out = temporal_patch_embed(packed_pairs)
    else:
        out = 0.5 * (packed_pairs[:, :, 0] + packed_pairs[:, :, 1])
    return out, isolated


@dataclass
class EpiAdapterOutput:
    patch_delta: torch.Tensor  # [B, N, Hm*Wm, lm_hidden_size] (zero at init)
    cam_delta: torch.Tensor  # [B, N, lm_hidden_size] (zero at init)
    fine_geo: torch.Tensor  # [B, N, 2*Hm, 2*Wm, fine_dim]
    epi_tokens: torch.Tensor  # [B, N, 1 + Hm*Wm, d_model]


class EpiAdapter(nn.Module):
    """Pre-LM epipolar adapter with exact zero-init residual into LM Layer 1."""

    def __init__(self, cfg: EpiAdapterConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.cfg = cfg
        n_taps = len(cfg.vit_tap_layers)
        self.tap_norms = nn.ModuleList([nn.LayerNorm(cfg.vit_hidden_size) for _ in range(n_taps)])
        self.tap_projs = nn.ModuleList([nn.Linear(cfg.vit_hidden_size, cfg.fine_dim) for _ in range(n_taps)])
        self.fine_norm = RMSNorm(cfg.fine_dim)
        self.downsample = nn.Conv2d(cfg.fine_dim, cfg.d_model, kernel_size=2, stride=2)
        self.cam_token = nn.Parameter(torch.randn(1, 1, 1, cfg.d_model) * 0.02)
        self.meta_enc = StreamMetadataEncoder(cfg.d_model, max_streams=cfg.max_streams)
        self.blocks = nn.ModuleList(
            [EpiBlock(cfg.d_model, cfg.num_heads, cfg.mlp_ratio, cfg.dropout) for _ in range(cfg.num_blocks)]
        )
        self.out_norm = RMSNorm(cfg.d_model)
        self.out_patch_proj = nn.Linear(cfg.d_model, lm_hidden_size, bias=True)
        self.out_cam_proj = nn.Linear(cfg.d_model, lm_hidden_size, bias=True)
        for p in (self.out_patch_proj, self.out_cam_proj):
            nn.init.zeros_(p.weight)
            nn.init.zeros_(p.bias)

    @staticmethod
    def pack_pre_vit_views(
        images: torch.Tensor,
        viewset: ViewSetBatch,
        temporal_patch_embed: Optional[Callable[[torch.Tensor], torch.Tensor] | nn.Module] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Pack pre-ViT images with temporal_patch=2 camera isolation before ViT stem embedding."""
        if temporal_patch_embed is None:
            return pack_views_for_temporal_patch2(images, viewset)
        return prevent_temporal_patch_bleeding(images, viewset, temporal_patch_embed=temporal_patch_embed)

    def forward(
        self, vit_taps: Sequence[torch.Tensor], viewset: Optional[ViewSetBatch] = None
    ) -> EpiAdapterOutput:
        if len(vit_taps) != len(self.tap_projs):
            raise ValueError(f"Expected {len(self.tap_projs)} ViT taps, got {len(vit_taps)}")
        proc_taps = []
        for tap in vit_taps:
            if tap.ndim == 6 and tap.shape[2] == 2:
                # Pre-ViT temporal_patch=2 pair tensor [B, N, 2, H2, W2, C]
                tap = 0.5 * (tap[:, :, 0] + tap[:, :, 1])
            elif viewset is not None and not viewset.temporal_merge_allowed.any():
                # Enforce zero cross-view bleeding and zero padded views
                tap = prevent_temporal_patch_bleeding(tap, viewset)[0]
            proc_taps.append(tap)
        fine_sum = sum(proj(norm(tap)) for tap, norm, proj in zip(proc_taps, self.tap_norms, self.tap_projs))
        fine_geo = self.fine_norm(fine_sum / len(proc_taps))
        if viewset is not None:
            fine_geo = fine_geo * viewset.view_mask[:, :, None, None, None].to(fine_geo.dtype)

        bsz, n_views, h2, w2, c_fine = fine_geo.shape
        hm, wm = h2 // 2, w2 // 2
        ds = self.downsample(fine_geo.reshape(bsz * n_views, h2, w2, c_fine).permute(0, 3, 1, 2))
        patches = ds.permute(0, 2, 3, 1).reshape(bsz, n_views, hm * wm, self.cfg.d_model)
        tokens = torch.cat([self.cam_token.expand(bsz, n_views, 1, self.cfg.d_model), patches], dim=2)

        view_mask = None
        if viewset is not None:
            tokens = tokens + self.meta_enc(viewset).unsqueeze(2)
            view_mask = viewset.view_mask

        for blk in self.blocks:
            tokens = blk(tokens, hm=hm, wm=wm, view_mask=view_mask)

        normed = self.out_norm(tokens)
        cam_delta = self.out_cam_proj(normed[:, :, 0, :])
        patch_delta = self.out_patch_proj(normed[:, :, 1:, :])
        if view_mask is not None:
            vm = view_mask.to(patch_delta.dtype)
            cam_delta = cam_delta * vm.unsqueeze(-1)
            patch_delta = patch_delta * vm[:, :, None, None]
        return EpiAdapterOutput(patch_delta, cam_delta, fine_geo, tokens)

    def apply_residual(
        self,
        merged_vis_tokens: torch.Tensor,
        cam_tokens: torch.Tensor,
        vit_taps: Sequence[torch.Tensor],
        viewset: Optional[ViewSetBatch] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, EpiAdapterOutput]:
        out = self.forward(vit_taps, viewset=viewset)
        return merged_vis_tokens + out.patch_delta, cam_tokens + out.cam_delta, out


class DA3SmallStemAdapter(nn.Module):
    """Toggleable DA3-Small correspondence stem fallback (zero-init residual)."""

    def __init__(self, cfg: EpiAdapterConfig, lm_hidden_size: int) -> None:
        super().__init__()
        self.fine_proj = nn.Linear(cfg.da3_small_dim, cfg.fine_dim)
        self.patch_norm = RMSNorm(cfg.da3_small_dim)
        self.out_patch_proj = nn.Linear(cfg.da3_small_dim, lm_hidden_size)
        self.out_cam_proj = nn.Linear(cfg.da3_small_dim, lm_hidden_size)
        for p in (self.out_patch_proj, self.out_cam_proj):
            nn.init.zeros_(p.weight)
            nn.init.zeros_(p.bias)

    def forward(
        self, da3_features: torch.Tensor, viewset: Optional[ViewSetBatch] = None
    ) -> EpiAdapterOutput:
        bsz, n_views, hm, wm, dim = da3_features.shape
        normed = self.patch_norm(da3_features)
        flat = normed.reshape(bsz, n_views, hm * wm, dim)
        cam_feat = flat.mean(dim=2)
        patch_delta, cam_delta = self.out_patch_proj(flat), self.out_cam_proj(cam_feat)
        fine_up = (
            F.interpolate(
                self.fine_proj(normed).reshape(bsz * n_views, hm, wm, -1).permute(0, 3, 1, 2),
                scale_factor=2, mode="bilinear", align_corners=False,
            )
            .permute(0, 2, 3, 1)
            .reshape(bsz, n_views, 2 * hm, 2 * wm, -1)
        )
        if viewset is not None:
            vm = viewset.view_mask.to(patch_delta.dtype)
            patch_delta = patch_delta * vm[:, :, None, None]
            cam_delta = cam_delta * vm.unsqueeze(-1)
        return EpiAdapterOutput(patch_delta, cam_delta, fine_up, torch.cat([cam_feat.unsqueeze(2), flat], dim=2))
