"""Stage-1A correspondence models: Arm A (epi_vit) vs Arm B (corresp_stem) + DA3-Giant teacher.

Strict Codex Astra Stage-1A isolation contract:
  - Metric3DRoPE is OFF (not instantiated).
  - DeltaGeoBias is OFF (`cfg.use_delta_geo_bias = False`).
  - No 9B LM in loop; tests dense correspondence + GeoPoseHead + GeoDepthHead cleanly.
  - EpiAdapter's LM Layer-1 zero-init residual projections (`out_patch_proj`, `out_cam_proj`)
    remain frozen at exact 0.0 during Stage-1A for step-0 preservation when plugged into Stage-2.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors import safe_open
from torch.utils.checkpoint import checkpoint

from .config import (
    EpiAdapterConfig,
    GeoHeadsConfig,
    LossWeightsConfig,
    SpatialForcing2Config,
    SpatialV2Config,
    ViewSetBatch,
    build_viewset_batch,
)
from .epi_adapter import EpiAdapter, EpiAdapterOutput
from .geo_heads import (
    GeoDepthHead,
    GeoDepthOutput,
    GeoPoseHead,
    GeoPoseOutput,
    build_intrinsics_matrix,
    unproject_depth,
)
from .losses import SpatialV2CompositeLoss

DEFAULT_QWEN_VISUAL_CKPT = "/scratch/jjyeung/orch_home_distill/spatial_v2/cache/qwen35_9b_visual.safetensors"
DEFAULT_DA3_CKPT = "/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors"
DEFAULT_DA3_SRC = (
    "/scratch/jjyeung/geo_bakeoff_kit/assets/da3-src/"
    "Depth-Anything-3-3d835ec1a5802d64a8b8b15f817a1ab54809bfe4/src"
)
DEFAULT_BAKEOFF_SITE = "/scratch/jjyeung/geo_bakeoff_kit/runtime/site"

ArmType = Literal["epi_vit", "corresp_stem"]


def _ensure_da3_importable() -> None:
    for p in (DEFAULT_DA3_SRC, DEFAULT_BAKEOFF_SITE):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def _hf_rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


# ---------------------------------------------------------------------------
# Arm A Backbone: Exact Qwen3.5-9B Vision Encoder (zero `transformers` dep)
# ---------------------------------------------------------------------------


class _Qwen35VisionPatchEmbed(nn.Module):
    def __init__(self, hidden_size: int = 1152, patch_size: int = 16, temporal_patch_size: int = 2) -> None:
        super().__init__()
        self.patch_size = patch_size
        self.temporal_patch_size = temporal_patch_size
        self.proj = nn.Conv3d(
            3,
            hidden_size,
            kernel_size=(temporal_patch_size, patch_size, patch_size),
            stride=(temporal_patch_size, patch_size, patch_size),
            bias=True,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B*N, 3, H, W] -> duplicate along temporal_patch=2 for single-frame isolation
        x_t = x.unsqueeze(2).expand(-1, -1, self.temporal_patch_size, -1, -1)
        out = self.proj(x_t).squeeze(2)  # [B*N, D, H2, W2]
        return out.flatten(2).transpose(1, 2).contiguous()  # [B*N, H2*W2, D]


class _Qwen35VisionAttention(nn.Module):
    def __init__(self, hidden_size: int = 1152, num_heads: int = 16) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.qkv = nn.Linear(hidden_size, hidden_size * 3, bias=True)
        self.proj = nn.Linear(hidden_size, hidden_size, bias=True)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        # x: [BN, L, D]; cos/sin: [1, 1, L, head_dim]
        bn, seqlen, dim = x.shape
        qkv = self.qkv(x).reshape(bn, seqlen, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)  # each [BN, H, L, head_dim]
        qf, kf = q.float(), k.float()
        q = (qf * cos + _hf_rotate_half(qf) * sin).to(x.dtype)
        k = (kf * cos + _hf_rotate_half(kf) * sin).to(x.dtype)
        out = F.scaled_dot_product_attention(q, k, v, is_causal=False)
        return self.proj(out.transpose(1, 2).contiguous().reshape(bn, seqlen, dim))


class _Qwen35VisionMLP(nn.Module):
    def __init__(self, hidden_size: int = 1152, intermediate_size: int = 4304) -> None:
        super().__init__()
        self.linear_fc1 = nn.Linear(hidden_size, intermediate_size, bias=True)
        self.linear_fc2 = nn.Linear(intermediate_size, hidden_size, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear_fc2(F.gelu(self.linear_fc1(x), approximate="tanh"))


class _Qwen35VisionBlock(nn.Module):
    def __init__(self, hidden_size: int = 1152, num_heads: int = 16, intermediate_size: int = 4304) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_size, eps=1e-6)
        self.norm2 = nn.LayerNorm(hidden_size, eps=1e-6)
        self.attn = _Qwen35VisionAttention(hidden_size=hidden_size, num_heads=num_heads)
        self.mlp = _Qwen35VisionMLP(hidden_size=hidden_size, intermediate_size=intermediate_size)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), cos, sin)
        x = x + self.mlp(self.norm2(x))
        return x


class Qwen35VisionEncoder(nn.Module):
    """Exact standalone Qwen3.5-9B ViT returning multi-layer pre-merger spatial taps."""

    def __init__(
        self,
        depth: int = 27,
        hidden_size: int = 1152,
        num_heads: int = 16,
        intermediate_size: int = 4304,
        patch_size: int = 16,
        temporal_patch_size: int = 2,
        num_position_embeddings: int = 2304,
        tap_layers: Tuple[int, ...] = (9, 17, 25),
        gradient_checkpointing: bool = False,
    ) -> None:
        super().__init__()
        self.depth = depth
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        self.patch_size = patch_size
        self.tap_layers = tuple(tap_layers)
        self.num_grid_per_side = int(round(num_position_embeddings**0.5))
        self.gradient_checkpointing = gradient_checkpointing

        self.patch_embed = _Qwen35VisionPatchEmbed(hidden_size, patch_size, temporal_patch_size)
        self.pos_embed = nn.Embedding(num_position_embeddings, hidden_size)
        self.blocks = nn.ModuleList(
            [_Qwen35VisionBlock(hidden_size, num_heads, intermediate_size) for _ in range(depth)]
        )
        rot_dim = self.head_dim // 2
        inv_freq = 1.0 / (10000.0 ** (torch.arange(0, rot_dim, 2, dtype=torch.float32) / rot_dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def load_pretrained(self, ckpt_path: str | Path = DEFAULT_QWEN_VISUAL_CKPT) -> Tuple[int, List[str]]:
        sd: Dict[str, torch.Tensor] = {}
        with safe_open(str(ckpt_path), framework="pt", device="cpu") as f:
            for k in f.keys():
                if not k.startswith("model.visual."):
                    continue
                sub = k[len("model.visual.") :]
                if sub.startswith("merger."):
                    continue
                sd[sub] = f.get_tensor(k)
        missing, unexpected = self.load_state_dict(sd, strict=False)
        if missing:
            raise RuntimeError(f"Missing keys loading Qwen35VisionEncoder from {ckpt_path}: {missing[:10]}")
        return len(sd), list(unexpected)

    def _interp_pos_embed(self, h2: int, w2: int, dtype: torch.dtype) -> torch.Tensor:
        g = self.num_grid_per_side
        w = self.pos_embed.weight.float().view(g, g, self.hidden_size).permute(2, 0, 1).unsqueeze(0)
        pe = F.interpolate(w, size=(h2, w2), mode="bilinear", align_corners=True)
        return pe.squeeze(0).flatten(1).transpose(0, 1).unsqueeze(0).to(dtype)  # [1, h2*w2, D]

    def _build_2d_rope(self, h2: int, w2: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        gy, gx = torch.meshgrid(
            torch.arange(h2, device=device, dtype=torch.float32),
            torch.arange(w2, device=device, dtype=torch.float32),
            indexing="ij",
        )
        pos = torch.stack([gy.reshape(-1), gx.reshape(-1)], dim=-1)  # [L, 2]
        freqs = (pos.unsqueeze(-1) * self.inv_freq.to(device)).flatten(1)  # [L, head_dim//2]
        emb = torch.cat([freqs, freqs], dim=-1)  # [L, head_dim]
        cos = emb.cos().view(1, 1, h2 * w2, self.head_dim)
        sin = emb.sin().view(1, 1, h2 * w2, self.head_dim)
        return cos, sin

    def forward(self, rgb_qwen: torch.Tensor) -> List[torch.Tensor]:
        # rgb_qwen: [B, N, 3, H, W]
        bsz, n_views, _, h, w = rgb_qwen.shape
        h2, w2 = h // self.patch_size, w // self.patch_size
        x = self.patch_embed(rgb_qwen.reshape(bsz * n_views, 3, h, w))
        x = x + self._interp_pos_embed(h2, w2, x.dtype)
        cos, sin = self._build_2d_rope(h2, w2, x.device)

        tap_set = set(self.tap_layers)
        max_tap = max(tap_set)
        taps: Dict[int, torch.Tensor] = {}
        for idx, blk in enumerate(self.blocks):
            layer_1idx = idx + 1
            if self.gradient_checkpointing and self.training and x.requires_grad:
                x = checkpoint(blk, x, cos, sin, use_reentrant=False)
            else:
                x = blk(x, cos, sin)
            if layer_1idx in tap_set:
                taps[layer_1idx] = x.reshape(bsz, n_views, h2, w2, self.hidden_size)
            if layer_1idx >= max_tap:
                break
        return [taps[l] for l in self.tap_layers]


# ---------------------------------------------------------------------------
# Arm B Backbone: Correspondence-Native Side-Stem (DA3 Metric DINOv2-L/14)
# ---------------------------------------------------------------------------


class DA3CorrespStemEncoder(nn.Module):
    """Correspondence-native DINOv2-L/14 encoder loaded from local DA3 checkpoint."""

    def __init__(
        self,
        out_layers: Tuple[int, ...] = (7, 15, 23),
        ckpt_path: Optional[str | Path] = DEFAULT_DA3_CKPT,
        gradient_checkpointing: bool = False,
        tiny: bool = False,
        tiny_dim: int = 64,
    ) -> None:
        super().__init__()
        self.out_layers = tuple(out_layers)
        self.tiny = tiny
        self.gradient_checkpointing = gradient_checkpointing
        self.patch_size = 14

        if tiny:
            self.hidden_size = tiny_dim
            self.patch_embed = nn.Conv2d(3, tiny_dim, kernel_size=14, stride=14)
            self.blocks = nn.ModuleList(
                [
                    nn.Sequential(
                        nn.LayerNorm(tiny_dim),
                        nn.Linear(tiny_dim, tiny_dim),
                        nn.GELU(),
                        nn.Linear(tiny_dim, tiny_dim),
                    )
                    for _ in range(3)
                ]
            )
            return

        _ensure_da3_importable()
        from depth_anything_3.model.dinov2.dinov2 import DinoV2

        self.hidden_size = 1024
        self.backbone = DinoV2(
            name="vitl",
            out_layers=list(self.out_layers),
            alt_start=-1,
            qknorm_start=-1,
            rope_start=-1,
            cat_token=False,
        )
        if ckpt_path is not None:
            self.load_pretrained(ckpt_path)

    def load_pretrained(self, ckpt_path: str | Path = DEFAULT_DA3_CKPT) -> int:
        if self.tiny:
            return 0
        prefix = "model.da3_metric.backbone.pretrained."
        sd: Dict[str, torch.Tensor] = {}
        with safe_open(str(ckpt_path), framework="pt", device="cpu") as f:
            for k in f.keys():
                if k.startswith(prefix):
                    sd[k[len(prefix) :]] = f.get_tensor(k)
        self.backbone.pretrained.load_state_dict(sd, strict=True)
        return len(sd)

    def forward(self, rgb_da3: torch.Tensor) -> List[torch.Tensor]:
        # rgb_da3: [B, N, 3, H, W]
        bsz, n_views, _, h, w = rgb_da3.shape
        h2, w2 = h // self.patch_size, w // self.patch_size
        if self.tiny:
            x = self.patch_embed(rgb_da3.reshape(bsz * n_views, 3, h, w))
            x = x.permute(0, 2, 3, 1).contiguous()  # [BN, H2, W2, D]
            taps = []
            for blk in self.blocks:
                x = x + blk(x)
                taps.append(x.reshape(bsz, n_views, h2, w2, self.hidden_size))
            return taps

        if not (self.gradient_checkpointing and self.training):
            feats, _ = self.backbone(rgb_da3)
            return [f[0].reshape(bsz, n_views, h2, w2, self.hidden_size) for f in feats]

        # Gradient-checkpointed per-frame pass through vitl blocks (alt_start == -1)
        vit = self.backbone.pretrained
        x = vit.prepare_tokens_with_masks(rgb_da3)  # [B, N, 1 + H2*W2, D]
        x = x.reshape(bsz * n_views, -1, self.hidden_size)
        tap_set = set(self.out_layers)
        max_tap = max(tap_set)
        taps_map: Dict[int, torch.Tensor] = {}
        for idx, blk in enumerate(vit.blocks):
            if x.requires_grad:
                x = checkpoint(blk, x, use_reentrant=False)
            else:
                x = blk(x)
            if idx in tap_set:
                xn = vit.norm(x)[:, vit.patch_start_idx :, :]
                taps_map[idx] = xn.reshape(bsz, n_views, h2, w2, self.hidden_size)
            if idx >= max_tap:
                break
        return [taps_map[l] for l in self.out_layers]


# ---------------------------------------------------------------------------
# Frozen DA3-Giant Teacher for SpatialForcing2Loss (patch-cosine + Gram)
# ---------------------------------------------------------------------------


class DA3GiantTeacher(nn.Module):
    """Frozen DA3-Nested Giant (40L ViT-G/14, alt_start=13) teacher for SpatialForcing2Loss."""

    def __init__(
        self,
        ckpt_path: Optional[str | Path] = DEFAULT_DA3_CKPT,
        out_layer: int = 39,
        tiny: bool = False,
        tiny_dim: int = 64,
    ) -> None:
        super().__init__()
        self.tiny = tiny
        self.patch_size = 14
        if tiny:
            self.teacher_dim = tiny_dim
            self.proj = nn.Conv2d(3, tiny_dim, kernel_size=14, stride=14)
            self.requires_grad_(False)
            self.eval()
            return

        _ensure_da3_importable()
        from depth_anything_3.model.dinov2.dinov2 import DinoV2

        self.teacher_dim = 3072  # cat_token=True concatenates local + global (2 * 1536)
        self.backbone = DinoV2(
            name="vitg",
            out_layers=[out_layer],
            alt_start=13,
            qknorm_start=13,
            rope_start=13,
            cat_token=True,
        )
        if ckpt_path is not None:
            prefix = "model.da3.backbone.pretrained."
            sd: Dict[str, torch.Tensor] = {}
            with safe_open(str(ckpt_path), framework="pt", device="cpu") as f:
                for k in f.keys():
                    if k.startswith(prefix):
                        sd[k[len(prefix) :]] = f.get_tensor(k)
            self.backbone.pretrained.load_state_dict(sd, strict=True)
        self.requires_grad_(False)
        self.eval()

    @torch.no_grad()
    def forward(self, rgb_da3: torch.Tensor) -> torch.Tensor:
        """Return merged-grid teacher patch features [B, N, Hm*Wm, teacher_dim]."""
        bsz, n_views, _, h, w = rgb_da3.shape
        h2, w2 = h // self.patch_size, w // self.patch_size
        hm, wm = h2 // 2, w2 // 2
        if self.tiny:
            f = self.proj(rgb_da3.reshape(bsz * n_views, 3, h, w))  # [BN, D, H2, W2]
            f_m = F.avg_pool2d(f, kernel_size=2, stride=2)
            return f_m.flatten(2).transpose(1, 2).reshape(bsz, n_views, hm * wm, self.teacher_dim)

        feats, _ = self.backbone(rgb_da3)
        patch_toks = feats[0][0]  # [B, N, H2*W2, 3072]
        f_grid = patch_toks.reshape(bsz * n_views, h2, w2, self.teacher_dim).permute(0, 3, 1, 2)
        f_m = F.avg_pool2d(f_grid, kernel_size=2, stride=2)  # [BN, 3072, Hm, Wm]
        return f_m.flatten(2).transpose(1, 2).reshape(bsz, n_views, hm * wm, self.teacher_dim)


# ---------------------------------------------------------------------------
# Unified Stage-1A Model: Arm A (epi_vit) vs Arm B (corresp_stem)
# ---------------------------------------------------------------------------


@dataclass
class Stage1AOutput:
    epi_out: EpiAdapterOutput
    pose_out: GeoPoseOutput
    depth_out: GeoDepthOutput
    student_tap_flat: torch.Tensor  # [B, N, Hm*Wm, d_model]
    pmap_pred: torch.Tensor  # [B, N, H2, W2, 3]


def build_stage1a_config(
    arm: ArmType,
    teacher_dim: int = 3072,
    tiny: bool = False,
) -> SpatialV2Config:
    """Build Stage-1A SpatialV2Config with Metric3DRoPE & DeltaGeoBias strictly OFF."""
    if tiny:
        cfg = SpatialV2Config.tiny(l_geo=16, stem_type="epi_adapter", viewset_mode="video")
        cfg.use_delta_geo_bias = False
        cfg.epi.vit_hidden_size = 64
        cfg.sf2 = SpatialForcing2Config(
            tap_layers=(16,), teacher_dim=teacher_dim, probe_hidden_dim=64, gram_num_samples=32
        )
        return cfg

    enc_dim = 1152 if arm == "epi_vit" else 1024
    return SpatialV2Config(
        l_geo=16,
        stem_type="epi_adapter",
        viewset_mode="video",
        use_delta_geo_bias=False,  # Codex Astra isolation guardrail: OFF in Stage-1A
        epi=EpiAdapterConfig(
            vit_hidden_size=enc_dim,
            vit_tap_layers=(9, 17, 25),
            fine_dim=256,
            d_model=768,
            num_blocks=6,
            num_heads=12,
            mlp_ratio=4.0,
        ),
        geo_heads=GeoHeadsConfig(
            depth_hidden_dim=256,
            depth_cross_blocks=2,
            depth_num_heads=8,
            flow_horizons=(1,),  # Stage-1A static K1 scenes; 4D multi-horizon flow deferred to Stage-2
            pose_hidden_dim=768,
            pose_num_layers=4,
            pose_num_heads=12,
            pose_refine_iters=4,
        ),
        sf2=SpatialForcing2Config(
            tap_layers=(16,),
            teacher_dim=teacher_dim,
            probe_hidden_dim=1024,
            gram_num_samples=512,
        ),
        loss_weights=LossWeightsConfig(
            sf2_feat=0.5,
            sf2_gram=0.5,
            depth=0.4,
            pose=1.5,
            ray=0.4,
            pmap=0.4,
            rigidity=0.0,
            flow=0.0,
            flow_sparsity=0.0,
            gravity=0.3,
            fov=0.2,
            reversal=0.0,
        ),
    )


class Stage1ACorrespondenceModel(nn.Module):
    """Unified Stage-1A trainer module for Arm A (epi_vit) and Arm B (corresp_stem)."""

    def __init__(
        self,
        arm: ArmType,
        teacher_dim: int = 3072,
        qwen_ckpt: Optional[str | Path] = DEFAULT_QWEN_VISUAL_CKPT,
        da3_ckpt: Optional[str | Path] = DEFAULT_DA3_CKPT,
        freeze_backbone: bool = False,
        gradient_checkpointing: bool = True,
        tiny: bool = False,
    ) -> None:
        super().__init__()
        if arm not in ("epi_vit", "corresp_stem"):
            raise ValueError(f"Unsupported arm: {arm}")
        self.arm: ArmType = arm
        self.tiny = tiny
        self.use_metric_3d_rope = False
        self.use_delta_geo_bias = False

        self.cfg = build_stage1a_config(arm=arm, teacher_dim=teacher_dim, tiny=tiny)
        assert not self.cfg.use_delta_geo_bias, "DeltaGeoBias must remain OFF in Stage-1A"

        # 1. Vision backbone (Arm A: Qwen3.5 ViT vs Arm B: DA3 DINOv2-L/14 correspondence stem)
        if arm == "epi_vit":
            if tiny:
                self.encoder: nn.Module = Qwen35VisionEncoder(
                    depth=6,
                    hidden_size=64,
                    num_heads=4,
                    intermediate_size=128,
                    patch_size=16,
                    temporal_patch_size=2,
                    num_position_embeddings=64,
                    tap_layers=(2, 4, 6),
                    gradient_checkpointing=gradient_checkpointing,
                )
            else:
                self.encoder = Qwen35VisionEncoder(
                    depth=27,
                    hidden_size=1152,
                    num_heads=16,
                    intermediate_size=4304,
                    patch_size=16,
                    temporal_patch_size=2,
                    num_position_embeddings=2304,
                    tap_layers=(9, 17, 25),
                    gradient_checkpointing=gradient_checkpointing,
                )
                if qwen_ckpt is not None:
                    self.encoder.load_pretrained(qwen_ckpt)
        else:
            self.encoder = DA3CorrespStemEncoder(
                out_layers=(7, 15, 23),
                ckpt_path=None if tiny else da3_ckpt,
                gradient_checkpointing=gradient_checkpointing,
                tiny=tiny,
                tiny_dim=64,
            )

        if freeze_backbone:
            self.encoder.requires_grad_(False)
        elif arm == "epi_vit":
            # Freeze unused blocks past max tap layer so optimizer & DDP have zero unused params
            max_tap = max(self.encoder.tap_layers)
            for idx in range(max_tap, len(self.encoder.blocks)):
                self.encoder.blocks[idx].requires_grad_(False)

        # 2. Shared EpiAdapter (65M full-scale) + GeoPoseHead + GeoDepthHead
        d_epi = self.cfg.epi.d_model
        self.epi_adapter = EpiAdapter(self.cfg.epi, lm_hidden_size=self.cfg.hidden_size)
        # Keep LM Layer-1 zero-init residual projections frozen at exact 0.0 during Stage-1A
        for proj in (self.epi_adapter.out_patch_proj, self.epi_adapter.out_cam_proj):
            proj.requires_grad_(False)

        self.pose_head = GeoPoseHead(self.cfg.geo_heads, lm_hidden_size=d_epi)
        # Pose covariance is not supervised in Stage-1A; freeze to keep DDP strictly clean
        self.pose_head.cov_head.requires_grad_(False)
        self.depth_head = GeoDepthHead(self.cfg.geo_heads, lm_hidden_size=d_epi, fine_dim=self.cfg.epi.fine_dim)
        # 4D rigidity & multi-horizon flow are Stage-2 add-ons; freeze in Stage-1A
        self.depth_head.rigidity_head.requires_grad_(False)
        self.depth_head.flow_head.requires_grad_(False)
        self.criterion = SpatialV2CompositeLoss(
            sf2_cfg=self.cfg.sf2, weights_cfg=self.cfg.loss_weights, lm_hidden_size=d_epi
        )

    def rgb_key(self) -> str:
        return "rgb_qwen" if self.arm == "epi_vit" else "rgb_da3"

    def forward(
        self,
        rgb: torch.Tensor,
        timestamps: Optional[torch.Tensor] = None,
        view_mask: Optional[torch.Tensor] = None,
        batch: Optional[Dict[str, torch.Tensor]] = None,
        teacher_feats: Optional[torch.Tensor] = None,
    ) -> Stage1AOutput | Tuple[Stage1AOutput, torch.Tensor, Dict[str, torch.Tensor]]:
        bsz, n_views = rgb.shape[:2]
        viewset: ViewSetBatch = build_viewset_batch(
            mode="video",
            batch_size=bsz,
            num_views=n_views,
            timestamps=timestamps,
            device=rgb.device,
        )
        if view_mask is not None:
            viewset.view_mask = view_mask.bool()

        taps = self.encoder(rgb)
        epi_out = self.epi_adapter(taps, viewset=viewset)
        h2, w2 = epi_out.fine_geo.shape[2], epi_out.fine_geo.shape[3]
        hm, wm = h2 // 2, w2 // 2

        epi_normed = self.epi_adapter.out_norm(epi_out.epi_tokens)
        h_cam = epi_normed[:, :, 0, :]
        h_vis_flat = epi_normed[:, :, 1:, :]
        h_vis = h_vis_flat.reshape(bsz, n_views, hm, wm, -1)

        pose_out = self.pose_head(h_cam, h_vis, view_mask=viewset.view_mask)
        depth_out = self.depth_head(
            h_vis,
            epi_out.fine_geo,
            log_fx_w=pose_out.log_fx_w,
            log_fy_h=pose_out.log_fy_h,
            view_mask=viewset.view_mask,
        )
        K_pred_fine = build_intrinsics_matrix(pose_out.log_fx_w, pose_out.log_fy_h, width=w2, height=h2)
        pmap_pred = unproject_depth(depth_out.depth, K_pred_fine, pose_out.rot_canon, pose_out.trans_canon)
        out = Stage1AOutput(
            epi_out=epi_out,
            pose_out=pose_out,
            depth_out=depth_out,
            student_tap_flat=h_vis_flat,
            pmap_pred=pmap_pred,
        )
        if batch is not None and teacher_feats is not None:
            loss, loss_dict = self.compute_loss(out, batch, teacher_feats)
            return out, loss, loss_dict
        return out

    def compute_loss(
        self,
        out: Stage1AOutput,
        batch: Dict[str, torch.Tensor],
        teacher_feats: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        valid_mask = batch["depth_valid"].unsqueeze(-1)
        pmap_pred_masked = torch.where(valid_mask, out.pmap_pred, torch.zeros_like(out.pmap_pred))
        pmap_gt_masked = torch.where(valid_mask, batch["pmap_gt"], torch.zeros_like(batch["pmap_gt"]))
        targets = {
            "depth_gt": batch["depth_gt"],
            "depth_valid": batch["depth_valid"],
            "metric_scale_locked": batch["metric_scale_locked"],
            "rot_gt": batch["rot_gt"],
            "trans_gt": batch["trans_gt"],
            "gravity_gt": batch["gravity_gt"],
            "log_fx_w_gt": batch["log_fx_w_gt"],
            "log_fy_h_gt": batch["log_fy_h_gt"],
            "plucker_gt": batch["plucker_gt"],
            "pmap_gt": pmap_gt_masked,
        }
        return self.criterion(
            student_taps={16: out.student_tap_flat},
            teacher_feats=teacher_feats,
            depth_out=out.depth_out,
            pose_out=out.pose_out,
            targets=targets,
            pmap_pred=pmap_pred_masked,
            view_mask=batch["view_mask"],
        )

    def build_param_groups(
        self, backbone_lr: float, head_lr: float, weight_decay: float
    ) -> List[Dict[str, object]]:
        """Separate backbone LR, head LR, and exact weight_decay=0.0 scale/norm/bias groups."""
        no_wd_ids = {id(p) for p in self.depth_head.no_weight_decay_parameters()}
        enc_ids = {id(p) for p in self.encoder.parameters()}

        bb_decay, bb_no_decay, hd_decay, hd_no_decay = [], [], [], []
        for name, p in self.named_parameters():
            if not p.requires_grad:
                continue
            is_no_wd = (id(p) in no_wd_ids) or (p.ndim <= 1) or name.endswith(".bias") or ("norm" in name)
            if id(p) in enc_ids:
                (bb_no_decay if is_no_wd else bb_decay).append(p)
            else:
                (hd_no_decay if is_no_wd else hd_decay).append(p)

        groups: List[Dict[str, object]] = []
        if bb_decay:
            groups.append({"name": "backbone_decay", "params": bb_decay, "lr": backbone_lr, "weight_decay": weight_decay})
        if bb_no_decay:
            groups.append({"name": "backbone_no_decay", "params": bb_no_decay, "lr": backbone_lr, "weight_decay": 0.0})
        if hd_decay:
            groups.append({"name": "head_decay", "params": hd_decay, "lr": head_lr, "weight_decay": weight_decay})
        if hd_no_decay:
            groups.append({"name": "head_no_decay", "params": hd_no_decay, "lr": head_lr, "weight_decay": 0.0})
        return groups

    def parameter_counts(self) -> Dict[str, int]:
        def _count(m: nn.Module, trainable_only: bool = False) -> int:
            return sum(p.numel() for p in m.parameters() if (not trainable_only or p.requires_grad))

        return {
            "encoder_total": _count(self.encoder),
            "encoder_trainable": _count(self.encoder, True),
            "epi_adapter_total": _count(self.epi_adapter),
            "epi_adapter_trainable": _count(self.epi_adapter, True),
            "pose_head": _count(self.pose_head),
            "depth_head": _count(self.depth_head),
            "sf2_probes": _count(self.criterion.sf2),
            "total_trainable": _count(self, True),
        }
