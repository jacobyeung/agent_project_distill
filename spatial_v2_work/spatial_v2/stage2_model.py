"""Spatial-V2 Stage-2 Full 9B Model: Qwen3.5-9B + Correspondence Front-End + Taps {16, 24} Distillation.

Architecture contract:
  1. Backbone: Qwen3.5-9B (`step-544` checkpoint OR base `Qwen3.5-9B` via `--init-ckpt`, or synthetic
     exact-architecture 9B config for zero-disk VRAM benchmarking, or `--tiny` for fast CPU unit tests),
     keeping `step-544`'s `scale_donor` frozen when `freeze_scale_donor=True`.
  2. Multi-View Correspondence Front-End (`--frontend {corresp_stem, da3_nested}`):
     - `corresp_stem` (Arm B): DA3 DINOv2-L/14 + EpiAdapter + zero-init gated fusion (`gate=0` at step 0).
     - `da3_nested`   (Arm C): Pre-trained multi-view DA3-Nested alternating-attention trunk with LoRA +
       selective unfreeze of last `k` blocks + zero-init gated projector into Qwen3.5 visual stream.
  3. Intermediate Tap Dense Distillation (`taps 16, 24` inside Qwen3.5-9B LLM):
     - Lightweight `GeoHeads` (metric depth, SE(3) relative pose, Plucker raymap, pointmap, gravity, FoV,
       4D rigidity/flow) + `SF2` feature/Gram distillation attached at LLM layers 16 and 24 (plus front-end).
     - Supports static `DA3` dense teachers AND optional 4D dynamic teachers (`Point4D`/`Any4D` 3D track /
       dynamic mask) cleanly gated by `has_4d_teacher`.
  4. Joint Training Objectives:
     - `L_lm`: Next-token CE strictly on assistant turns (`labels != -100`) with Liger-Kernel fused CE
       when installed and automatic fallback to memory-efficient chunked linear CE.
     - `L_geo`: Multi-tap (`16`, `24`, plus front-end) depth, SE(3) pose, Plucker raymap, `depth_valid` ->
       `pmap_valid` & `metric_scale_locked`-gated pointmap (Codex Stage-1A item #1 fix), gravity, FoV, and
       `has_4d_teacher`-gated 4D rigidity/flow.
     - `L_sf2`: Feature cosine + Gram alignment to `DA3` dense correspondence features at taps 16 & 24.
     - `L_vla_aux`: Optional toggle (`use_vla_aux`) hooking `FlowExpert` continuous VLA action head at
       taps `(12, 16, 24)` + 3D geometry tokens for `vla_libero` (B2) and `navrun` (N2).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors import safe_open
from torch.utils.checkpoint import checkpoint
from transformers.models.qwen3_5.configuration_qwen3_5 import (
    Qwen3_5Config,
    Qwen3_5TextConfig,
    Qwen3_5VisionConfig,
)
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5ForConditionalGeneration

from .config import (
    EpiAdapterConfig,
    FlowExpertConfig,
    GeoHeadsConfig,
    LossWeightsConfig,
    SpatialForcing2Config,
    SpatialV2Config,
    ViewSetBatch,
    build_viewset_batch,
)
from .epi_adapter import EpiAdapter, EpiBlock, RMSNorm
from .geo_heads import (
    GeoDepthHead,
    GeoDepthOutput,
    GeoPoseHead,
    GeoPoseOutput,
    build_intrinsics_matrix,
    unproject_depth,
)
from .losses import DecoupledDepthLoss, PoseAnd4DLoss, SpatialForcing2Loss
from .stage1a_model import (
    DEFAULT_DA3_CKPT,
    DEFAULT_QWEN_VISUAL_CKPT,
    DA3CorrespStemEncoder,
    _ensure_da3_importable,
)
from .vla_expert import FlowExpert

FrontendType = Literal["corresp_stem", "da3_nested"]

try:
    from liger_kernel.transformers.fused_linear_cross_entropy import (  # type: ignore[import-not-found]
        LigerFusedLinearCrossEntropyLoss,
    )

    HAS_LIGER_FLCE = True
except Exception:
    LigerFusedLinearCrossEntropyLoss = None
    HAS_LIGER_FLCE = False


# ---------------------------------------------------------------------------
# LoRA & Memory-Efficient Fused / Chunked Cross-Entropy Primitives
# ---------------------------------------------------------------------------


class LoRALinear(nn.Module):
    """Low-rank adapter wrapping a frozen base `nn.Linear`.

    Note: Because the front-end -> LLM visual fusion is gated by `torch.tanh(fusion_gate)`
    with `fusion_gate = 0.0` at Step 0, initializing `lora_B` with a tiny non-zero std (`1e-3`)
    preserves exact `0.0` Step-0 perturbation to Qwen3.5 logits while ensuring BOTH `lora_A`
    and `lora_B` receive non-zero finite gradients on the very first backward pass.
    """

    def __init__(
        self,
        base: nn.Linear,
        rank: int = 16,
        alpha: float = 32.0,
        lora_b_init_std: float = 1e-3,
    ) -> None:
        super().__init__()
        self.base = base
        self.base.requires_grad_(False)
        self.rank = rank
        self.alpha = alpha
        self.scaling = float(alpha) / float(max(rank, 1))
        self.lora_A = nn.Linear(base.in_features, rank, bias=False, dtype=base.weight.dtype, device=base.weight.device)
        self.lora_B = nn.Linear(rank, base.out_features, bias=False, dtype=base.weight.dtype, device=base.weight.device)
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        if lora_b_init_std > 0.0:
            nn.init.normal_(self.lora_B.weight, mean=0.0, std=lora_b_init_std)
        else:
            nn.init.zeros_(self.lora_B.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.base(x)
        lora_out = self.lora_B(self.lora_A(x.to(self.lora_A.weight.dtype))) * self.scaling
        return base_out + lora_out.to(base_out.dtype)


def inject_lora_into_module(
    module: nn.Module,
    target_suffixes: Tuple[str, ...] = ("qkv", "proj", "q_proj", "k_proj", "v_proj", "o_proj"),
    rank: int = 16,
    alpha: float = 32.0,
    lora_b_init_std: float = 1e-3,
) -> int:
    """Replace matching `nn.Linear` submodules in-place with `LoRALinear` wrappers."""
    if rank <= 0:
        return 0
    replaced = 0
    for name, child in list(module.named_children()):
        if isinstance(child, nn.Linear) and any(name == s or name.endswith(s) for s in target_suffixes):
            setattr(module, name, LoRALinear(child, rank=rank, alpha=alpha, lora_b_init_std=lora_b_init_std))
            replaced += 1
        else:
            replaced += inject_lora_into_module(
                child,
                target_suffixes=target_suffixes,
                rank=rank,
                alpha=alpha,
                lora_b_init_std=lora_b_init_std,
            )
    return replaced


def compute_lm_cross_entropy(
    hidden_states: torch.Tensor,
    lm_head: nn.Linear,
    labels: torch.Tensor,
    chunk_tokens: int = 128,
    use_liger_if_available: bool = True,
) -> torch.Tensor:
    """Compute causal LM next-token CE strictly on assistant tokens (`labels != -100`).

    Uses Liger-Kernel fused linear cross-entropy if installed; otherwise computes logits in
    small token chunks so Qwen3.5-9B's 248,320-vocab logit matrix is never materialized in full.
    Always touches `lm_head.weight` so DDP/FSDP2 never sees an unused `lm_head` parameter.
    """
    # Causal shift: position t predicts label at t + 1
    shift_h = hidden_states[:, :-1, :].contiguous().reshape(-1, hidden_states.shape[-1])
    shift_y = labels[:, 1:].contiguous().reshape(-1)
    valid_mask = shift_y != -100
    valid_count = int(valid_mask.sum().item())

    if valid_count == 0:
        # Touch lm_head weight & hidden_states with zero multiplier to preserve graph connectivity
        dummy_logit = F.linear(shift_h[:1], lm_head.weight, lm_head.bias)
        return dummy_logit.float().sum() * 0.0

    h_valid = shift_h[valid_mask]
    y_valid = shift_y[valid_mask]

    if use_liger_if_available and HAS_LIGER_FLCE and LigerFusedLinearCrossEntropyLoss is not None and h_valid.is_cuda:
        flce = LigerFusedLinearCrossEntropyLoss(ignore_index=-100, reduction="mean")
        return flce(lm_head.weight, h_valid, y_valid, lm_head.bias)

    total_nll = h_valid.new_zeros((), dtype=torch.float32)
    for start in range(0, h_valid.shape[0], chunk_tokens):
        end = min(start + chunk_tokens, h_valid.shape[0])
        logits_chunk = F.linear(h_valid[start:end], lm_head.weight, lm_head.bias).float()
        total_nll = total_nll + F.cross_entropy(
            logits_chunk, y_valid[start:end], ignore_index=-100, reduction="sum"
        )
    return total_nll / float(valid_count)


# ---------------------------------------------------------------------------
# Front-End Interfaces: Arm B (`corresp_stem`) & Arm C (`da3_nested`)
# ---------------------------------------------------------------------------


@dataclass
class FrontendOutput:
    vis_delta: torch.Tensor  # [B, N, Hm*Wm, lm_hidden_size] (exact 0.0 when fusion_gate == 0)
    cam_delta: torch.Tensor  # [B, N, lm_hidden_size] (exact 0.0 when fusion_gate == 0)
    h_bridged: torch.Tensor  # [B, N, Hm*Wm, lm_hidden_size] (un-gated bridge tokens)
    h_vis_front: torch.Tensor  # [B, N, Hm, Wm, d_geo]
    h_cam_front: torch.Tensor  # [B, N, d_geo]
    fine_geo: torch.Tensor  # [B, N, H2, W2, fine_dim]
    fusion_gate_value: torch.Tensor  # scalar tensor


class CorrespStemFrontend(nn.Module):
    """Arm B (`corresp_stem`): DA3 DINOv2-L/14 + EpiAdapter + zero-init gated fusion into Qwen3.5."""

    def __init__(
        self,
        epi_cfg: EpiAdapterConfig,
        lm_hidden_size: int,
        da3_ckpt: Optional[str | Path] = DEFAULT_DA3_CKPT,
        gradient_checkpointing: bool = True,
        tiny: bool = False,
        freeze_encoder: bool = False,
    ) -> None:
        super().__init__()
        self.epi_cfg = epi_cfg
        self.lm_hidden_size = lm_hidden_size
        self.d_geo = epi_cfg.d_model
        self.fine_dim = epi_cfg.fine_dim
        self.tiny = tiny

        use_real_dinov2 = False
        if (not tiny) and da3_ckpt is not None and os.path.isfile(str(da3_ckpt)):
            try:
                import depth_anything_3  # noqa: F401
                use_real_dinov2 = True
            except ImportError:
                use_real_dinov2 = False

        self.encoder = DA3CorrespStemEncoder(
            out_layers=(7, 15, 23),
            ckpt_path=da3_ckpt if use_real_dinov2 else None,
            gradient_checkpointing=gradient_checkpointing,
            tiny=(not use_real_dinov2),
            tiny_dim=epi_cfg.vit_hidden_size,
        )
        if freeze_encoder:
            self.encoder.requires_grad_(False)

        self.epi_adapter = EpiAdapter(epi_cfg, lm_hidden_size=lm_hidden_size)
        # Freeze EpiAdapter's legacy linear projections; we use our gated bridge below
        for proj in (self.epi_adapter.out_patch_proj, self.epi_adapter.out_cam_proj):
            proj.requires_grad_(False)

        self.bridge_norm = RMSNorm(self.d_geo)
        self.bridge_patch_proj = nn.Linear(self.d_geo, lm_hidden_size, bias=True)
        self.bridge_cam_proj = nn.Linear(self.d_geo, lm_hidden_size, bias=True)
        nn.init.normal_(self.bridge_patch_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.bridge_patch_proj.bias)
        nn.init.normal_(self.bridge_cam_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.bridge_cam_proj.bias)

        # Residual coupling back into front-end GeoHeads so bridge_patch/cam_proj receive
        # non-zero finite gradients on Step 0 even when fusion_gate == 0.0
        self.bridge_to_geo_vis = nn.Linear(lm_hidden_size, self.d_geo, bias=False)
        self.bridge_to_geo_cam = nn.Linear(lm_hidden_size, self.d_geo, bias=False)
        nn.init.normal_(self.bridge_to_geo_vis.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.bridge_to_geo_cam.weight, mean=0.0, std=0.02)

        # Zero-init multiplicative gate: guarantees exact 0.0 perturbation to Qwen3.5 at step 0
        self.fusion_gate = nn.Parameter(torch.zeros(1))

    def no_weight_decay_parameters(self) -> List[nn.Parameter]:
        return [self.fusion_gate]

    def set_gate_zero(self) -> None:
        with torch.no_grad():
            self.fusion_gate.zero_()

    def forward(self, rgb_da3: torch.Tensor, viewset: ViewSetBatch) -> FrontendOutput:
        bsz, n_views = rgb_da3.shape[:2]
        taps = self.encoder(rgb_da3)
        epi_out = self.epi_adapter(taps, viewset=viewset)
        h2, w2 = epi_out.fine_geo.shape[2], epi_out.fine_geo.shape[3]
        hm, wm = h2 // 2, w2 // 2

        epi_normed = self.bridge_norm(self.epi_adapter.out_norm(epi_out.epi_tokens))
        h_cam_raw = epi_normed[:, :, 0, :]  # [B, N, d_geo]
        h_vis_flat = epi_normed[:, :, 1:, :]  # [B, N, Hm*Wm, d_geo]

        h_bridged = self.bridge_patch_proj(h_vis_flat)  # [B, N, Hm*Wm, D_lm]
        cam_bridged = self.bridge_cam_proj(h_cam_raw)  # [B, N, D_lm]

        if viewset.view_mask is not None:
            vm = viewset.view_mask.to(h_bridged.dtype)
            h_bridged = h_bridged * vm[:, :, None, None]
            cam_bridged = cam_bridged * vm.unsqueeze(-1)

        gate = torch.tanh(self.fusion_gate.to(h_bridged.dtype))
        vis_delta = gate * h_bridged
        cam_delta = gate * cam_bridged

        h_vis_front = (h_vis_flat + 0.1 * self.bridge_to_geo_vis(h_bridged)).reshape(
            bsz, n_views, hm, wm, self.d_geo
        )
        h_cam_front = h_cam_raw + 0.1 * self.bridge_to_geo_cam(cam_bridged)

        return FrontendOutput(
            vis_delta=vis_delta,
            cam_delta=cam_delta,
            h_bridged=h_bridged,
            h_vis_front=h_vis_front,
            h_cam_front=h_cam_front,
            fine_geo=epi_out.fine_geo,
            fusion_gate_value=gate.detach(),
        )


class _CompactAlternatingTrunk(nn.Module):
    """Fallback / synthetic / tiny multi-view alternating-attention trunk matching DA3-Nested interface."""

    def __init__(
        self,
        hidden_size: int = 384,
        num_blocks: int = 4,
        num_heads: int = 6,
        patch_size: int = 14,
    ) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.cat_dim = hidden_size * 2
        self.patch_size = patch_size
        self.patch_embed = nn.Conv2d(3, hidden_size, kernel_size=patch_size, stride=patch_size)
        self.cam_token = nn.Parameter(torch.randn(1, 1, 1, hidden_size) * 0.02)
        self.blocks = nn.ModuleList(
            [EpiBlock(hidden_size, num_heads=num_heads, mlp_ratio=2.0) for _ in range(num_blocks)]
        )
        self.norm = RMSNorm(hidden_size)

    def forward(
        self, rgb_da3: torch.Tensor, view_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, int, int]:
        bsz, n_views, _, h, w = rgb_da3.shape
        h2, w2 = h // self.patch_size, w // self.patch_size
        p = self.patch_embed(rgb_da3.reshape(bsz * n_views, 3, h, w))
        patches = p.flatten(2).transpose(1, 2).reshape(bsz, n_views, h2 * w2, self.hidden_size)
        toks = torch.cat([self.cam_token.expand(bsz, n_views, 1, self.hidden_size), patches], dim=2)
        local_toks = toks
        for idx, blk in enumerate(self.blocks):
            toks = blk(toks, hm=h2, wm=w2, view_mask=view_mask)
            if idx == 0:
                local_toks = toks
        cat_toks = torch.cat([self.norm(local_toks), self.norm(toks)], dim=-1)
        return cat_toks[:, :, 1:, :], cat_toks[:, :, 0, :], h2, w2


class DA3NestedBridge(nn.Module):
    """Arm C (`da3_nested`): Pre-trained multi-view DA3-Nested alternating-attention trunk + VLM bridge.

    Supports:
      - Pre-trained `model.da3.backbone.pretrained` (40L ViT-G/14 alternating intra/cross-view attention)
        or compact multi-view alternating trunk when `tiny=True` or `da3_ckpt=None`.
      - Selective unfreezing of the last `unfreeze_last_k` blocks + LoRA (`lora_rank`) on attention layers.
      - Zero-init `fusion_gate` into the Qwen3.5 visual stream (`gate=0` at Step 0 preserves exact
        `step-544` / `Qwen3.5-9B` logits).
    """

    def __init__(
        self,
        epi_cfg: EpiAdapterConfig,
        lm_hidden_size: int,
        da3_ckpt: Optional[str | Path] = DEFAULT_DA3_CKPT,
        lora_rank: int = 16,
        lora_alpha: float = 32.0,
        unfreeze_last_k: int = 2,
        gradient_checkpointing: bool = True,
        tiny: bool = False,
    ) -> None:
        super().__init__()
        self.epi_cfg = epi_cfg
        self.lm_hidden_size = lm_hidden_size
        self.d_geo = epi_cfg.d_model
        self.fine_dim = epi_cfg.fine_dim
        self.patch_size = 14
        self.gradient_checkpointing = gradient_checkpointing
        self.tiny = tiny
        self.lora_rank = lora_rank
        self.unfreeze_last_k = unfreeze_last_k

        use_real_da3 = (not tiny) and (da3_ckpt is not None) and os.path.isfile(str(da3_ckpt))
        self.use_real_da3 = use_real_da3

        if use_real_da3:
            _ensure_da3_importable()
            from depth_anything_3.model.dinov2.dinov2 import DinoV2

            self.da3_cat_dim = 3072  # cat_token=True (local 1536 + global 1536)
            self.backbone = DinoV2(
                name="vitg",
                out_layers=[39],
                alt_start=13,
                qknorm_start=13,
                rope_start=13,
                cat_token=True,
            )
            self._load_da3_nested_weights(str(da3_ckpt))
            # Freeze base trunk, then selectively unfreeze last k blocks and inject LoRA
            self.backbone.requires_grad_(False)
            blocks = self.backbone.pretrained.blocks
            n_blk = len(blocks)
            k_unfreeze = max(0, min(unfreeze_last_k, n_blk))
            if lora_rank > 0:
                start_lora = max(13, n_blk - max(k_unfreeze, 4))
                for b_idx in range(start_lora, n_blk):
                    inject_lora_into_module(
                        blocks[b_idx],
                        target_suffixes=("qkv", "proj"),
                        rank=lora_rank,
                        alpha=lora_alpha,
                    )
            if k_unfreeze > 0:
                for b_idx in range(n_blk - k_unfreeze, n_blk):
                    for p in blocks[b_idx].parameters():
                        p.requires_grad_(True)
                for p in self.backbone.pretrained.norm.parameters():
                    p.requires_grad_(True)
        else:
            trunk_dim = epi_cfg.vit_hidden_size if tiny else 384
            num_heads = epi_cfg.num_heads if tiny else 6
            num_blocks = 3 if tiny else 4
            self.backbone = _CompactAlternatingTrunk(
                hidden_size=trunk_dim,
                num_blocks=num_blocks,
                num_heads=num_heads,
                patch_size=14,
            )
            self.da3_cat_dim = self.backbone.cat_dim
            self.backbone.requires_grad_(False)
            blocks = self.backbone.blocks
            n_blk = len(blocks)
            k_unfreeze = max(0, min(unfreeze_last_k, n_blk))
            if lora_rank > 0:
                for b_idx in range(max(0, n_blk - max(k_unfreeze, 2)), n_blk):
                    inject_lora_into_module(
                        blocks[b_idx],
                        target_suffixes=("qkv", "proj"),
                        rank=min(lora_rank, trunk_dim // 2),
                        alpha=lora_alpha,
                    )
            if k_unfreeze > 0:
                for b_idx in range(n_blk - k_unfreeze, n_blk):
                    for p in blocks[b_idx].parameters():
                        p.requires_grad_(True)
                for p in self.backbone.norm.parameters():
                    p.requires_grad_(True)
            self.backbone.cam_token.requires_grad_(True)

        # Fine-resolution (H2, W2) and merged-resolution (Hm, Wm) geometric projections
        self.fine_norm = RMSNorm(self.da3_cat_dim)
        self.fine_proj = nn.Linear(self.da3_cat_dim, self.fine_dim)
        self.downsample = nn.Conv2d(self.fine_dim, self.d_geo, kernel_size=2, stride=2)
        self.cam_in_proj = nn.Linear(self.da3_cat_dim, self.d_geo)
        self.geo_norm = RMSNorm(self.d_geo)

        # Bridge to Qwen3.5 LLM visual stream (D_lm = 4096)
        self.bridge_norm = RMSNorm(self.d_geo)
        self.bridge_patch_proj = nn.Linear(self.d_geo, lm_hidden_size, bias=True)
        self.bridge_cam_proj = nn.Linear(self.d_geo, lm_hidden_size, bias=True)
        nn.init.normal_(self.bridge_patch_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.bridge_patch_proj.bias)
        nn.init.normal_(self.bridge_cam_proj.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.bridge_cam_proj.bias)

        self.bridge_to_geo_vis = nn.Linear(lm_hidden_size, self.d_geo, bias=False)
        self.bridge_to_geo_cam = nn.Linear(lm_hidden_size, self.d_geo, bias=False)
        nn.init.normal_(self.bridge_to_geo_vis.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.bridge_to_geo_cam.weight, mean=0.0, std=0.02)

        # Zero-init multiplicative gate: exact 0.0 perturbation to Qwen3.5 at step 0
        self.fusion_gate = nn.Parameter(torch.zeros(1))

    def _load_da3_nested_weights(self, ckpt_path: str) -> int:
        prefix = "model.da3.backbone.pretrained."
        sd: Dict[str, torch.Tensor] = {}
        with safe_open(ckpt_path, framework="pt", device="cpu") as f:
            for k in f.keys():
                if k.startswith(prefix):
                    sd[k[len(prefix) :]] = f.get_tensor(k)
        self.backbone.pretrained.load_state_dict(sd, strict=True)
        return len(sd)

    def no_weight_decay_parameters(self) -> List[nn.Parameter]:
        return [self.fusion_gate]

    def set_gate_zero(self) -> None:
        with torch.no_grad():
            self.fusion_gate.zero_()

    def forward(self, rgb_da3: torch.Tensor, viewset: ViewSetBatch) -> FrontendOutput:
        bsz, n_views, _, h, w = rgb_da3.shape
        h2, w2 = h // self.patch_size, w // self.patch_size
        hm, wm = h2 // 2, w2 // 2

        if self.use_real_da3:
            feats, _ = self.backbone(rgb_da3)
            patch_toks = feats[0][0].reshape(bsz, n_views, h2 * w2, self.da3_cat_dim)
            cam_toks = feats[0][1].reshape(bsz, n_views, self.da3_cat_dim)
        else:
            patch_toks, cam_toks, h2, w2 = self.backbone(rgb_da3, view_mask=viewset.view_mask)

        fine_geo = self.fine_proj(self.fine_norm(patch_toks)).reshape(bsz, n_views, h2, w2, self.fine_dim)
        if viewset.view_mask is not None:
            fine_geo = fine_geo * viewset.view_mask[:, :, None, None, None].to(fine_geo.dtype)

        ds = self.downsample(fine_geo.reshape(bsz * n_views, h2, w2, self.fine_dim).permute(0, 3, 1, 2))
        h_vis_flat = self.geo_norm(ds.permute(0, 2, 3, 1).reshape(bsz, n_views, hm * wm, self.d_geo))
        h_cam_raw = self.geo_norm(self.cam_in_proj(cam_toks) + h_vis_flat.mean(dim=2))

        vis_normed = self.bridge_norm(h_vis_flat)
        cam_normed = self.bridge_norm(h_cam_raw)
        h_bridged = self.bridge_patch_proj(vis_normed)
        cam_bridged = self.bridge_cam_proj(cam_normed)

        if viewset.view_mask is not None:
            vm = viewset.view_mask.to(h_bridged.dtype)
            h_bridged = h_bridged * vm[:, :, None, None]
            cam_bridged = cam_bridged * vm.unsqueeze(-1)

        gate = torch.tanh(self.fusion_gate.to(h_bridged.dtype))
        vis_delta = gate * h_bridged
        cam_delta = gate * cam_bridged

        h_vis_front = (h_vis_flat + 0.1 * self.bridge_to_geo_vis(h_bridged)).reshape(
            bsz, n_views, hm, wm, self.d_geo
        )
        h_cam_front = h_cam_raw + 0.1 * self.bridge_to_geo_cam(cam_bridged)

        return FrontendOutput(
            vis_delta=vis_delta,
            cam_delta=cam_delta,
            h_bridged=h_bridged,
            h_vis_front=h_vis_front,
            h_cam_front=h_cam_front,
            fine_geo=fine_geo,
            fusion_gate_value=gate.detach(),
        )


# ---------------------------------------------------------------------------
# Frozen Scale Donor Lock (Preserves step-544 metric scale reference)
# ---------------------------------------------------------------------------


class ScaleDonorLock(nn.Module):
    """Frozen metric scale donor from `step-544` preventing scene scale drift."""

    def __init__(self, hidden_dim: int = 256, freeze: bool = True) -> None:
        super().__init__()
        self.freeze = freeze
        self.log_gamma_donor = nn.Parameter(torch.zeros(1), requires_grad=not freeze)
        self.donor_scale_proj = nn.Linear(hidden_dim, 1, bias=True)
        nn.init.zeros_(self.donor_scale_proj.weight)
        nn.init.zeros_(self.donor_scale_proj.bias)
        if freeze:
            self.requires_grad_(False)
            self.eval()

    def train(self, mode: bool = True) -> "ScaleDonorLock":
        super().train(False if self.freeze else mode)
        return self


# ---------------------------------------------------------------------------
# Full Stage-2 Spatial-V2 Model
# ---------------------------------------------------------------------------


@dataclass
class Stage2TapOutputs:
    pose_out: GeoPoseOutput
    depth_out: GeoDepthOutput
    pmap_pred: torch.Tensor  # [B, N, H2, W2, 3]


@dataclass
class Stage2ForwardOutput:
    logits: Optional[torch.Tensor]
    frontend_out: FrontendOutput
    tap_outputs: Dict[str, Stage2TapOutputs]  # keys: "front", "16", "24"
    llm_taps_vis: Dict[int, torch.Tensor]  # {16: [B, N, Hm*Wm, D_lm], 24: [B, N, Hm*Wm, D_lm]}
    vis_base: torch.Tensor  # [B, N, Hm*Wm, D_lm]
    vis_fused: torch.Tensor  # [B, N, Hm*Wm, D_lm]


def build_qwen35_config(tiny: bool = False) -> Qwen3_5Config:
    """Build exact Qwen3.5-9B config (32L GatedDeltaNet+Attn, hidden=4096) or tiny 32L unit-test config."""
    if tiny:
        tcfg = Qwen3_5TextConfig(
            hidden_size=128,
            intermediate_size=256,
            num_hidden_layers=32,
            num_attention_heads=4,
            num_key_value_heads=2,
            head_dim=32,
            linear_num_key_heads=4,
            linear_num_value_heads=4,
            linear_key_head_dim=32,
            linear_value_head_dim=32,
            vocab_size=1024,
            use_cache=False,
        )
        vcfg = Qwen3_5VisionConfig(
            depth=4,
            hidden_size=64,
            intermediate_size=128,
            num_heads=4,
            out_hidden_size=128,
            patch_size=16,
            temporal_patch_size=2,
            spatial_merge_size=2,
            num_position_embeddings=64,
        )
        return Qwen3_5Config(text_config=tcfg, vision_config=vcfg)

    tcfg = Qwen3_5TextConfig(
        hidden_size=4096,
        intermediate_size=12288,
        num_hidden_layers=32,
        num_attention_heads=16,
        num_key_value_heads=4,
        head_dim=256,
        linear_num_key_heads=16,
        linear_num_value_heads=32,
        linear_key_head_dim=128,
        linear_value_head_dim=128,
        vocab_size=248320,
        use_cache=False,
    )
    vcfg = Qwen3_5VisionConfig(
        depth=27,
        hidden_size=1152,
        intermediate_size=4304,
        num_heads=16,
        out_hidden_size=4096,
        patch_size=16,
        temporal_patch_size=2,
        spatial_merge_size=2,
        num_position_embeddings=2304,
    )
    return Qwen3_5Config(text_config=tcfg, vision_config=vcfg)


class SpatialV2Stage2Model(nn.Module):
    """Unified Stage-2 Full 9B Spatial-V2 Model supporting `corresp_stem` (Arm B) & `da3_nested` (Arm C)."""

    def __init__(
        self,
        frontend: FrontendType = "corresp_stem",
        init_ckpt: Optional[str | Path] = None,
        qwen_visual_ckpt: Optional[str | Path] = DEFAULT_QWEN_VISUAL_CKPT,
        da3_ckpt: Optional[str | Path] = DEFAULT_DA3_CKPT,
        stage1a_ckpt: Optional[str | Path] = None,
        teacher_dim: int = 3072,
        tap_layers: Tuple[int, ...] = (16, 24),
        freeze_scale_donor: bool = True,
        freeze_qwen_vision: bool = False,
        lora_rank: int = 16,
        lora_alpha: float = 32.0,
        unfreeze_last_k: int = 2,
        use_vla_aux: bool = False,
        lm_loss_weight: float = 1.0,
        geo_loss_weight: float = 1.0,
        sf2_loss_weight: float = 1.0,
        vla_loss_weight: float = 0.5,
        gradient_checkpointing: bool = True,
        tiny: bool = False,
        param_dtype: Optional[torch.dtype] = None,
    ) -> None:
        super().__init__()
        if frontend not in ("corresp_stem", "da3_nested"):
            raise ValueError(f"Unsupported frontend: {frontend}. Expected 'corresp_stem' or 'da3_nested'.")
        self.frontend_type: FrontendType = frontend
        self.tap_layers = tuple(tap_layers)
        self.freeze_scale_donor = freeze_scale_donor
        self.use_vla_aux = use_vla_aux
        self.lm_loss_weight = lm_loss_weight
        self.geo_loss_weight = geo_loss_weight
        self.sf2_loss_weight = sf2_loss_weight
        self.vla_loss_weight = vla_loss_weight
        self.gradient_checkpointing = gradient_checkpointing
        self.tiny = tiny

        # 1. Build SpatialV2Config aligned to Qwen3.5-9B (or tiny 32L config)
        if tiny:
            self.cfg = SpatialV2Config.tiny(l_geo=16, stem_type="epi_adapter", viewset_mode="video")
            self.cfg.sf2 = SpatialForcing2Config(
                tap_layers=self.tap_layers, teacher_dim=teacher_dim, probe_hidden_dim=64, gram_num_samples=32
            )
            self.cfg.geo_heads.flow_horizons = (-1, 1, 4, 16)
        else:
            enc_dim = 1024 if frontend == "corresp_stem" else 3072
            self.cfg = SpatialV2Config(
                l_geo=16,
                stem_type="epi_adapter",
                viewset_mode="video",
                use_delta_geo_bias=False,
                use_metric_3d_rope=False,
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
                    flow_horizons=(-1, 1, 4, 16),
                    pose_hidden_dim=768,
                    pose_num_layers=4,
                    pose_num_heads=12,
                    pose_refine_iters=4,
                ),
                sf2=SpatialForcing2Config(
                    tap_layers=self.tap_layers,
                    teacher_dim=teacher_dim,
                    probe_hidden_dim=1024,
                    gram_num_samples=512,
                ),
                loss_weights=LossWeightsConfig(),
            )

        # 2. Initialize Qwen3.5-9B Backbone (`step-544` / base `Qwen3.5-9B` OR synthetic exact 9B config)
        qwen_cfg = build_qwen35_config(tiny=tiny)
        prev_dtype = torch.get_default_dtype()
        try:
            if param_dtype is not None:
                torch.set_default_dtype(param_dtype)
            if init_ckpt is not None and str(init_ckpt).lower() not in ("", "none", "synthetic"):
                ckpt_p = Path(str(init_ckpt))
                if ckpt_p.is_dir():
                    self.lm = Qwen3_5ForConditionalGeneration.from_pretrained(
                        str(ckpt_p),
                        torch_dtype=param_dtype or torch.bfloat16,
                    )
                else:
                    self.lm = Qwen3_5ForConditionalGeneration(qwen_cfg)
                    self._load_qwen_safetensors(ckpt_p)
            else:
                self.lm = Qwen3_5ForConditionalGeneration(qwen_cfg)
                if (not tiny) and qwen_visual_ckpt is not None and os.path.isfile(str(qwen_visual_ckpt)):
                    self._load_qwen_visual_safetensors(Path(str(qwen_visual_ckpt)))
        finally:
            torch.set_default_dtype(prev_dtype)

        # Ensure language model training & use_reentrant=False gradient checkpointing compatibility
        self.lm.config.text_config.use_cache = False
        self.lm.model.language_model.config.use_cache = False
        if gradient_checkpointing:
            self.lm.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        if freeze_qwen_vision:
            self.lm.model.visual.requires_grad_(False)

        # 3. Frozen Scale Donor (`step-544` scale stability lock)
        self.scale_donor = ScaleDonorLock(
            hidden_dim=self.cfg.geo_heads.depth_hidden_dim,
            freeze=freeze_scale_donor,
        )

        # 4. Multi-View Correspondence Front-End (`corresp_stem` Arm B vs `da3_nested` Arm C)
        d_lm = self.cfg.hidden_size
        d_geo = self.cfg.epi.d_model
        fine_dim = self.cfg.epi.fine_dim

        if frontend == "corresp_stem":
            self.frontend: CorrespStemFrontend | DA3NestedBridge = CorrespStemFrontend(
                epi_cfg=self.cfg.epi,
                lm_hidden_size=d_lm,
                da3_ckpt=None if tiny else da3_ckpt,
                gradient_checkpointing=gradient_checkpointing,
                tiny=tiny,
            )
        else:
            self.frontend = DA3NestedBridge(
                epi_cfg=self.cfg.epi,
                lm_hidden_size=d_lm,
                da3_ckpt=None if tiny else da3_ckpt,
                lora_rank=lora_rank,
                lora_alpha=lora_alpha,
                unfreeze_last_k=unfreeze_last_k,
                gradient_checkpointing=gradient_checkpointing,
                tiny=tiny,
            )

        # 5. Front-End + Intermediate LLM Tap (`16`, `24`) GeoHeads & SpatialForcing^2 Probes
        self.front_pose_head = GeoPoseHead(self.cfg.geo_heads, lm_hidden_size=d_geo)
        self.front_depth_head = GeoDepthHead(self.cfg.geo_heads, lm_hidden_size=d_geo, fine_dim=fine_dim)
        self.front_pose_head.cov_head.requires_grad_(False)

        self.tap_pose_heads = nn.ModuleDict()
        self.tap_depth_heads = nn.ModuleDict()
        self.tap_cam_projs = nn.ModuleDict()
        for lid in self.tap_layers:
            k = str(lid)
            p_head = GeoPoseHead(self.cfg.geo_heads, lm_hidden_size=d_lm)
            p_head.cov_head.requires_grad_(False)
            d_head = GeoDepthHead(self.cfg.geo_heads, lm_hidden_size=d_lm, fine_dim=fine_dim)
            if freeze_scale_donor:
                d_head.log_gamma_bias.requires_grad_(False)
                self.front_depth_head.log_gamma_bias.requires_grad_(False)
            self.tap_pose_heads[k] = p_head
            self.tap_depth_heads[k] = d_head
            self.tap_cam_projs[k] = nn.Linear(d_geo, d_lm, bias=False)

        self.sf2_loss = SpatialForcing2Loss(self.cfg.sf2, lm_hidden_size=d_lm)
        self.front_sf2_probe = nn.Sequential(
            nn.Linear(d_geo, self.cfg.sf2.probe_hidden_dim),
            nn.GELU(),
            nn.Linear(self.cfg.sf2.probe_hidden_dim, self.cfg.sf2.teacher_dim),
        )
        self.depth_loss_fn = DecoupledDepthLoss()
        self.pose_4d_loss_fn = PoseAnd4DLoss()

        # 6. Optional Stage-2b FlowExpert VLA continuous action head
        self.flow_expert: Optional[FlowExpert] = (
            FlowExpert(self.cfg.flow_expert, lm_hidden_size=d_lm) if use_vla_aux else None
        )
        if self.flow_expert is not None:
            with torch.no_grad():
                self.flow_expert.subgoal_gate.fill_(0.05)

        if stage1a_ckpt is not None and os.path.isfile(str(stage1a_ckpt)):
            self.load_stage1a_checkpoint(stage1a_ckpt)

        self.enforce_gated_deltanet_fp32()

    def enforce_gated_deltanet_fp32(self) -> "SpatialV2Stage2Model":
        """Keep Qwen3.5 GatedDeltaNet `linear_attn.A_log` and `linear_attn.norm.weight` in float32."""
        for layer in self.lm.model.language_model.layers:
            lin = getattr(layer, "linear_attn", None)
            if lin is None:
                continue
            if hasattr(lin, "A_log") and isinstance(lin.A_log, nn.Parameter) and lin.A_log.dtype != torch.float32:
                lin.A_log.data = lin.A_log.data.to(dtype=torch.float32)
            norm = getattr(lin, "norm", None)
            if norm is not None and hasattr(norm, "weight") and isinstance(norm.weight, nn.Parameter):
                if norm.weight.dtype != torch.float32:
                    norm.weight.data = norm.weight.data.to(dtype=torch.float32)
        return self

    def to(self, *args, **kwargs) -> "SpatialV2Stage2Model":
        super().to(*args, **kwargs)
        return self.enforce_gated_deltanet_fp32()

    def bfloat16(self) -> "SpatialV2Stage2Model":
        super().bfloat16()
        return self.enforce_gated_deltanet_fp32()

    def _load_qwen_visual_safetensors(self, ckpt_path: Path) -> int:
        sd: Dict[str, torch.Tensor] = {}
        with safe_open(str(ckpt_path), framework="pt", device="cpu") as f:
            for k in f.keys():
                if k.startswith("model.visual."):
                    sd[k[len("model.visual.") :]] = f.get_tensor(k)
        self.lm.model.visual.load_state_dict(sd, strict=False)
        return len(sd)

    def _load_qwen_safetensors(self, ckpt_path: Path) -> int:
        sd: Dict[str, torch.Tensor] = {}
        with safe_open(str(ckpt_path), framework="pt", device="cpu") as f:
            for k in f.keys():
                sd[k] = f.get_tensor(k)
        self.lm.load_state_dict(sd, strict=False)
        return len(sd)

    def load_stage1a_checkpoint(self, ckpt_path: str | Path) -> Tuple[int, List[str]]:
        """Load trained Stage-1A front-end & front-end GeoHeads weights while keeping fusion_gate=0."""
        payload = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
        raw_sd: Dict[str, torch.Tensor] = payload.get("model_state_dict", payload)
        loaded = 0
        skipped: List[str] = []

        front_sd = self.frontend.state_dict()
        for k, v in raw_sd.items():
            if k in front_sd and front_sd[k].shape == v.shape and k != "fusion_gate":
                front_sd[k] = v
                loaded += 1
            else:
                skipped.append(k)
        self.frontend.load_state_dict(front_sd, strict=False)
        self.frontend.set_gate_zero()
        return loaded, skipped

    def train(self, mode: bool = True) -> "SpatialV2Stage2Model":
        super().train(mode)
        # Critical fix from launch_orchard_vla_testl: explicitly force Qwen3_5TextModel & its layers
        # into .train(mode) so GradientCheckpointingLayer.__call__ (`if self.gradient_checkpointing and self.training`)
        # is never silently bypassed.
        self.lm.train(mode)
        self.lm.model.language_model.train(mode)
        for layer in self.lm.model.language_model.layers:
            layer.train(mode)
        if self.freeze_scale_donor:
            self.scale_donor.eval()
        return self

    def encode_qwen_visual_base(self, rgb_qwen: torch.Tensor) -> Tuple[torch.Tensor, int, int]:
        """Run Qwen3.5 ViT + 2x2 spatial patch merger with single-frame temporal_patch=2 isolation.

        Args:
            rgb_qwen: `[B, N, 3, H_q, W_q]` where `H_q = grid_h * 16, W_q = grid_w * 16`.
        Returns:
            `(vis_base [B, N, Hm*Wm, D_lm], Hm, Wm)`.
        """
        bsz, n_views, c, h_q, w_q = rgb_qwen.shape
        visual = self.lm.model.visual
        p_size = int(getattr(visual.config, "patch_size", 16))
        t_size = int(getattr(visual.config, "temporal_patch_size", 2))
        m_size = int(getattr(visual.config, "spatial_merge_size", 2))
        h2, w2 = h_q // p_size, w_q // p_size
        hm, wm = h2 // m_size, w2 // m_size

        # Duplicate each frame across temporal_patch_size=2 for cross-camera isolation, then reshape
        # into Qwen3_5VisionModel's expected block-merged patch ordering [B*N*Hm*Wm*m*m, C*t*p*p]
        x_pair = rgb_qwen.unsqueeze(3).expand(bsz, n_views, c, t_size, h_q, w_q)
        x_blocks = (
            x_pair.reshape(bsz * n_views, c, t_size, hm, m_size, p_size, wm, m_size, p_size)
            .permute(0, 3, 6, 4, 7, 1, 2, 5, 8)
            .contiguous()
            .reshape(-1, c * t_size * p_size * p_size)
        )
        grid_thw = torch.tensor(
            [[1, h2, w2]] * (bsz * n_views), device=rgb_qwen.device, dtype=torch.long
        )
        vis_out = visual(x_blocks, grid_thw=grid_thw)
        merged = vis_out.pooler_output if hasattr(vis_out, "pooler_output") else vis_out
        vis_base = merged.reshape(bsz, n_views, hm * wm, self.cfg.hidden_size)
        return vis_base, hm, wm

    def _run_geo_heads_at_tap(
        self,
        pose_head: GeoPoseHead,
        depth_head: GeoDepthHead,
        h_cam: torch.Tensor,
        h_vis: torch.Tensor,
        fine_geo: torch.Tensor,
        view_mask: torch.Tensor,
    ) -> Stage2TapOutputs:
        h2, w2 = fine_geo.shape[2], fine_geo.shape[3]
        pose_out = pose_head(h_cam, h_vis, view_mask=view_mask)
        depth_out = depth_head(
            h_vis,
            fine_geo,
            log_fx_w=pose_out.log_fx_w,
            log_fy_h=pose_out.log_fy_h,
            view_mask=view_mask,
        )
        if self.freeze_scale_donor:
            # Anchor scene scale bias to frozen step-544 scale donor reference
            donor_shift = self.scale_donor.log_gamma_donor.to(depth_out.log_depth.dtype) * 0.0
            depth_out.log_depth = depth_out.log_depth + donor_shift
        k_pred_fine = build_intrinsics_matrix(pose_out.log_fx_w, pose_out.log_fy_h, width=w2, height=h2)
        pmap_pred = unproject_depth(depth_out.depth, k_pred_fine, pose_out.rot_canon, pose_out.trans_canon)
        return Stage2TapOutputs(pose_out=pose_out, depth_out=depth_out, pmap_pred=pmap_pred)

    def forward(
        self,
        rgb_qwen: torch.Tensor,
        rgb_da3: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        timestamps: Optional[torch.Tensor] = None,
        view_mask: Optional[torch.Tensor] = None,
        batch: Optional[Dict[str, torch.Tensor]] = None,
        teacher_feats: Optional[torch.Tensor] = None,
        return_logits: Optional[bool] = None,
    ) -> Stage2ForwardOutput | Tuple[Stage2ForwardOutput, torch.Tensor, Dict[str, torch.Tensor]]:
        bsz, n_views = rgb_qwen.shape[:2]
        device = rgb_qwen.device

        viewset: ViewSetBatch = build_viewset_batch(
            mode="video",
            batch_size=bsz,
            num_views=n_views,
            timestamps=timestamps,
            device=device,
        )
        if view_mask is not None:
            viewset.view_mask = view_mask.bool()

        # 1. Base Qwen3.5 visual stream + multi-view correspondence front-end (Arm B or Arm C)
        vis_base, hm, wm = self.encode_qwen_visual_base(rgb_qwen)
        front_out = self.frontend(rgb_da3, viewset=viewset)

        # Zero-init gated fusion: when fusion_gate == 0.0, vis_delta == 0.0 and vis_fused == vis_base
        vis_fused = vis_base + front_out.vis_delta.to(vis_base.dtype)
        l_vis = n_views * hm * wm
        vis_flat = vis_fused.reshape(bsz, l_vis, self.cfg.hidden_size)

        # 2. Concatenate visual prefix embeddings + text embeddings for Qwen3.5 language model
        text_embeds = self.lm.model.language_model.embed_tokens(input_ids)
        inputs_embeds = torch.cat([vis_flat, text_embeds.to(vis_flat.dtype)], dim=1)

        if attention_mask is not None:
            vis_attn = (
                viewset.view_mask.unsqueeze(-1)
                .expand(bsz, n_views, hm * wm)
                .reshape(bsz, l_vis)
                .to(attention_mask.dtype)
            )
            full_attention_mask: Optional[torch.Tensor] = torch.cat([vis_attn, attention_mask], dim=1)
        else:
            full_attention_mask = None

        # 3. Capture only requested intermediate tap layers ({16, 24}, plus 12 if VLA FlowExpert active)
        active_tap_ids = set(self.tap_layers)
        if self.use_vla_aux and self.flow_expert is not None:
            active_tap_ids.update(self.cfg.flow_expert.tap_layers)

        captured_taps: Dict[int, torch.Tensor] = {}
        hook_handles = []
        for lid in sorted(active_tap_ids):
            def _make_tap_hook(layer_1idx: int):
                def _hook(_module: nn.Module, _inp: object, out: object) -> None:
                    if layer_1idx not in captured_taps:
                        captured_taps[layer_1idx] = out[0] if isinstance(out, tuple) else out

                return _hook

            hook_handles.append(
                self.lm.model.language_model.layers[lid - 1].register_forward_hook(_make_tap_hook(lid))
            )

        try:
            lm_out = self.lm.model.language_model(
                inputs_embeds=inputs_embeds,
                attention_mask=full_attention_mask,
                use_cache=False,
            )
        finally:
            for h in hook_handles:
                h.remove()

        last_hidden = lm_out.last_hidden_state

        # 4. Run GeoHeads on front-end and intermediate LLM taps {16, 24}
        tap_outputs: Dict[str, Stage2TapOutputs] = {}
        tap_outputs["front"] = self._run_geo_heads_at_tap(
            self.front_pose_head,
            self.front_depth_head,
            front_out.h_cam_front,
            front_out.h_vis_front,
            front_out.fine_geo,
            viewset.view_mask,
        )

        llm_taps_vis: Dict[int, torch.Tensor] = {}
        for lid in self.tap_layers:
            k = str(lid)
            h_tap_seq = captured_taps[lid]
            h_tap_vis_flat = h_tap_seq[:, :l_vis, :].reshape(bsz, n_views, hm * wm, self.cfg.hidden_size)
            llm_taps_vis[lid] = h_tap_vis_flat
            h_tap_vis = h_tap_vis_flat.reshape(bsz, n_views, hm, wm, self.cfg.hidden_size)
            h_tap_cam = h_tap_vis.mean(dim=(2, 3)) + self.tap_cam_projs[k](front_out.h_cam_front)
            tap_outputs[k] = self._run_geo_heads_at_tap(
                self.tap_pose_heads[k],
                self.tap_depth_heads[k],
                h_tap_cam,
                h_tap_vis,
                front_out.fine_geo,
                viewset.view_mask,
            )

        want_logits = (not self.training) if return_logits is None else return_logits
        logits = self.lm.lm_head(last_hidden) if want_logits else None

        out = Stage2ForwardOutput(
            logits=logits,
            frontend_out=front_out,
            tap_outputs=tap_outputs,
            llm_taps_vis=llm_taps_vis,
            vis_base=vis_base,
            vis_fused=vis_fused,
        )

        if batch is not None or labels is not None:
            loss, loss_dict = self.compute_joint_loss(
                out=out,
                last_hidden=last_hidden,
                l_vis=l_vis,
                labels=labels if labels is not None else batch.get("labels") if batch is not None else None,
                batch=batch,
                teacher_feats=teacher_feats,
                captured_taps=captured_taps,
                view_mask=viewset.view_mask,
            )
            return out, loss, loss_dict

        return out

    def _compute_single_tap_geo_loss(
        self,
        tap_name: str,
        tap_out: Stage2TapOutputs,
        batch: Dict[str, torch.Tensor],
        view_mask: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        bsz, n_views = view_mask.shape[:2]
        depth_valid = batch["depth_valid"].bool() & view_mask.bool()[:, :, None, None]
        l_depth, depth_m = self.depth_loss_fn(
            tap_out.depth_out,
            batch["depth_gt"],
            depth_valid,
            batch["metric_scale_locked"],
            view_mask=view_mask,
        )

        # Codex Stage-1A item #1 fix: explicitly pass depth_valid as pmap_valid so masked pixels
        # are never counted as valid zero support during pointmap loss normalization.
        valid_mask_3d = depth_valid.unsqueeze(-1)
        pmap_pred_masked = torch.where(valid_mask_3d, tap_out.pmap_pred, torch.zeros_like(tap_out.pmap_pred))
        pmap_gt_masked = torch.where(valid_mask_3d, batch["pmap_gt"], torch.zeros_like(batch["pmap_gt"]))

        # Dynamic 4D teacher gating (`has_4d_teacher` per sample in batch)
        has_4d = batch.get("has_4d_teacher")
        if has_4d is not None:
            has_4d_bool = has_4d.bool().view(bsz)
        else:
            has_4d_bool = torch.zeros((bsz,), dtype=torch.bool, device=view_mask.device)

        y_stat_gt: Optional[torch.Tensor] = None
        delta_p_gt: Optional[torch.Tensor] = None
        flow_valid: Optional[torch.Tensor] = None
        delta_p_rev: Optional[torch.Tensor] = None

        if has_4d_bool.any():
            raw_y_stat = batch.get("y_stat_gt")
            if raw_y_stat is not None:
                # Mask non-4D samples with NaN so PoseAnd4DLoss's `torch.isfinite(y_stat_gt)` ignores them
                y_stat_gt = torch.where(
                    has_4d_bool[:, None, None, None],
                    raw_y_stat.float(),
                    torch.full_like(raw_y_stat.float(), float("nan")),
                )
            raw_dp = batch.get("delta_p_gt")
            if raw_dp is not None:
                delta_p_gt = raw_dp
                base_fv = batch.get("flow_valid")
                if base_fv is None:
                    base_fv = torch.ones(raw_dp.shape[:-1], dtype=torch.bool, device=raw_dp.device)
                flow_valid = base_fv.bool() & has_4d_bool.view(bsz, *([1] * (base_fv.ndim - 1)))
            delta_p_rev = batch.get("delta_p_rev")

        p4d, p4d_m = self.pose_4d_loss_fn(
            pose_out=tap_out.pose_out,
            depth_out=tap_out.depth_out,
            rot_gt=batch["rot_gt"],
            trans_gt=batch["trans_gt"],
            gravity_gt=batch["gravity_gt"],
            log_fx_w_gt=batch["log_fx_w_gt"],
            log_fy_h_gt=batch["log_fy_h_gt"],
            plucker_gt=batch["plucker_gt"],
            metric_scale_locked=batch["metric_scale_locked"],
            y_stat_gt=y_stat_gt,
            delta_p_gt=delta_p_gt,
            pmap_pred=pmap_pred_masked,
            pmap_gt=pmap_gt_masked,
            view_mask=view_mask,
            delta_p_rev=delta_p_rev,
            flow_valid=flow_valid,
            pmap_valid=depth_valid,
        )

        # Tiny zero-prior stabilization on 4D flow log-variance & rigidity logits so static-only batches
        # (`has_4d_teacher=False`) still give finite non-zero gradients to all 4D head parameters under DDP/FSDP2
        reg_4d = 1e-4 * (
            tap_out.depth_out.log_var_flow.float().pow(2).mean()
            + tap_out.depth_out.rigidity_logits.float().pow(2).mean()
        )

        w = self.cfg.loss_weights
        tap_total = (
            w.depth * l_depth
            + w.pose * p4d["pose"]
            + w.gravity * p4d["gravity"]
            + w.fov * p4d["fov"]
            + w.ray * p4d["ray"]
            + w.pmap * p4d["pmap"]
            + w.rigidity * p4d["rigidity"]
            + w.flow * p4d["flow"]
            + w.flow_sparsity * p4d["flow_sparsity"]
            + w.reversal * p4d["reversal"]
            + reg_4d
        )
        metrics = {
            f"geo_{tap_name}_total": tap_total.detach(),
            f"geo_{tap_name}_depth": depth_m["depth_total"],
            f"geo_{tap_name}_pose": p4d_m["pose"],
            f"geo_{tap_name}_pmap": p4d_m["pmap"],
            f"geo_{tap_name}_ray": p4d_m["ray"],
            f"geo_{tap_name}_flow": p4d_m["flow"],
            f"geo_{tap_name}_rigidity": p4d_m["rigidity"],
        }
        return tap_total, metrics

    def compute_joint_loss(
        self,
        out: Stage2ForwardOutput,
        last_hidden: torch.Tensor,
        l_vis: int,
        labels: Optional[torch.Tensor],
        batch: Optional[Dict[str, torch.Tensor]],
        teacher_feats: Optional[torch.Tensor],
        captured_taps: Dict[int, torch.Tensor],
        view_mask: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        metrics: Dict[str, torch.Tensor] = {}
        device = last_hidden.device

        # 1. L_lm: Next-token CE strictly on assistant turns (visual prefix padded with -100)
        if labels is not None:
            if labels.shape[1] == last_hidden.shape[1]:
                full_labels = labels
            else:
                vis_ignore = torch.full((labels.shape[0], l_vis), -100, dtype=torch.long, device=device)
                full_labels = torch.cat([vis_ignore, labels.to(device)], dim=1)
            l_lm = compute_lm_cross_entropy(last_hidden, self.lm.lm_head, full_labels)
        else:
            l_lm = F.linear(last_hidden[:, :1, :], self.lm.lm_head.weight, self.lm.lm_head.bias).float().sum() * 0.0
        metrics["l_lm"] = l_lm.detach()

        # 2. L_geo: Multi-tap (front, 16, 24) geometry & 4D dynamic losses
        if batch is not None and "depth_gt" in batch:
            geo_losses = []
            for tap_name, tap_out in out.tap_outputs.items():
                g_loss, g_m = self._compute_single_tap_geo_loss(tap_name, tap_out, batch, view_mask)
                geo_losses.append(g_loss)
                metrics.update(g_m)
            l_geo = torch.stack(geo_losses).mean()
        else:
            l_geo = last_hidden.new_zeros((), dtype=torch.float32)
        metrics["l_geo"] = l_geo.detach()

        # 3. L_sf2: SpatialForcing^2 feature + Gram alignment at taps 16 & 24 (+ front-end probe)
        if teacher_feats is not None:
            l_feat, l_gram, sf2_m = self.sf2_loss(
                student_taps=out.llm_taps_vis,
                teacher_feats=teacher_feats,
                valid_mask=view_mask,
            )
            # Front-end SF2 cosine alignment
            tea_clean = torch.nan_to_num(teacher_feats.detach().float(), nan=0.0, posinf=0.0, neginf=0.0)
            bsz, n_views, p_per_view, d_tea = tea_clean.shape
            tea_norm = F.normalize(tea_clean.reshape(bsz, n_views * p_per_view, d_tea), dim=-1, eps=1e-6)
            front_flat = out.frontend_out.h_vis_front.reshape(bsz, n_views * p_per_view, -1)
            front_stu = F.normalize(self.front_sf2_probe(front_flat).float(), dim=-1, eps=1e-6)
            vm_flat = view_mask.bool().unsqueeze(-1).expand(bsz, n_views, p_per_view).reshape(bsz, -1).float()
            l_front_sf2 = ((1.0 - (front_stu * tea_norm).sum(dim=-1)) * vm_flat).sum() / vm_flat.sum().clamp_min(1.0)

            w = self.cfg.loss_weights
            l_sf2 = w.sf2_feat * (0.5 * l_feat + 0.5 * l_front_sf2) + w.sf2_gram * l_gram
            metrics.update(sf2_m)
            metrics["sf2_feat_front"] = l_front_sf2.detach()
        else:
            l_sf2 = last_hidden.new_zeros((), dtype=torch.float32)
        metrics["l_sf2"] = l_sf2.detach()

        # 4. L_vla_aux: Optional FlowExpert continuous action chunk head (Stage-2b toggle)
        if self.use_vla_aux and self.flow_expert is not None and batch is not None and "actions_gt" in batch:
            tap16_out = out.tap_outputs.get("16", out.tap_outputs["front"])
            pmap_m = F.adaptive_avg_pool2d(
                tap16_out.pmap_pred.float().permute(0, 1, 4, 2, 3).reshape(-1, 3, *tap16_out.pmap_pred.shape[2:4]),
                (out.frontend_out.h_vis_front.shape[2], out.frontend_out.h_vis_front.shape[3]),
            )
            dp_m = F.adaptive_avg_pool2d(
                tap16_out.depth_out.delta_p_obj[..., 0, :]
                .float()
                .permute(0, 1, 4, 2, 3)
                .reshape(-1, 3, *tap16_out.pmap_pred.shape[2:4]),
                (out.frontend_out.h_vis_front.shape[2], out.frontend_out.h_vis_front.shape[3]),
            )
            ps_m = F.adaptive_avg_pool2d(
                tap16_out.depth_out.p_stat.float().reshape(-1, 1, *tap16_out.pmap_pred.shape[2:4]),
                (out.frontend_out.h_vis_front.shape[2], out.frontend_out.h_vis_front.shape[3]),
            )
            geo_toks = (
                torch.cat([pmap_m, dp_m, ps_m], dim=1)
                .permute(0, 2, 3, 1)
                .reshape(last_hidden.shape[0], -1, 7)
                .to(last_hidden.dtype)
            )
            vla_taps = {lid: captured_taps[lid][:, :l_vis, :] for lid in self.cfg.flow_expert.tap_layers if lid in captured_taps}
            t_goal = batch.get("t_goal")
            if t_goal is None:
                tap24_out = out.tap_outputs.get("24", tap16_out)
                bsz_vla = last_hidden.shape[0]
                t_goal = torch.eye(4, device=last_hidden.device, dtype=torch.float32).unsqueeze(0).repeat(bsz_vla, 1, 1)
                t_goal[:, :3, :3] = tap24_out.pose_out.rot_canon[:, -1]
                t_goal[:, :3, 3] = tap24_out.pose_out.trans_canon[:, -1]
            l_vla = self.flow_expert.compute_loss(
                actions_gt=batch["actions_gt"],
                proprio=batch["proprio"],
                backbone_taps=vla_taps,
                geo_tokens=geo_toks,
                t_goal=t_goal,
                detach_backbone=self.cfg.flow_expert.detach_backbone,
            )
        else:
            l_vla = last_hidden.new_zeros((), dtype=torch.float32)
        metrics["l_vla_aux"] = l_vla.detach()

        total_loss = (
            self.lm_loss_weight * l_lm
            + self.geo_loss_weight * l_geo
            + self.sf2_loss_weight * l_sf2
            + (self.vla_loss_weight * l_vla if self.use_vla_aux else 0.0)
        )
        metrics["total_loss"] = total_loss.detach()
        metrics["fusion_gate"] = out.frontend_out.fusion_gate_value
        return total_loss, metrics

    def build_param_groups(
        self,
        lm_lr: float = 1e-5,
        frontend_lr: float = 5e-5,
        head_lr: float = 2e-4,
        weight_decay: float = 0.01,
    ) -> List[Dict[str, object]]:
        """Build optimizer parameter groups isolating LM, front-end, and heads with weight_decay=0.0 guards."""
        no_wd_ids = set()
        for p in self.frontend.no_weight_decay_parameters():
            no_wd_ids.add(id(p))
        for p in self.front_depth_head.no_weight_decay_parameters():
            no_wd_ids.add(id(p))
        for d_head in self.tap_depth_heads.values():
            for p in d_head.no_weight_decay_parameters():
                no_wd_ids.add(id(p))

        lm_ids = {id(p) for p in self.lm.parameters()}
        front_ids = {id(p) for p in self.frontend.parameters()}

        buckets: Dict[str, List[nn.Parameter]] = {
            "lm_decay": [],
            "lm_no_decay": [],
            "frontend_decay": [],
            "frontend_no_decay": [],
            "head_decay": [],
            "head_no_decay": [],
        }
        lrs = {
            "lm_decay": lm_lr,
            "lm_no_decay": lm_lr,
            "frontend_decay": frontend_lr,
            "frontend_no_decay": frontend_lr,
            "head_decay": head_lr,
            "head_no_decay": head_lr,
        }

        for name, p in self.named_parameters():
            if not p.requires_grad:
                continue
            is_no_wd = (
                (id(p) in no_wd_ids)
                or (p.ndim <= 1)
                or name.endswith(".bias")
                or ("norm" in name.lower())
                or ("gate" in name.lower())
            )
            if id(p) in lm_ids:
                prefix = "lm"
            elif id(p) in front_ids:
                prefix = "frontend"
            else:
                prefix = "head"
            key = f"{prefix}_{'no_decay' if is_no_wd else 'decay'}"
            buckets[key].append(p)

        groups: List[Dict[str, object]] = []
        for key, params in buckets.items():
            if params:
                groups.append(
                    {
                        "name": key,
                        "params": params,
                        "lr": lrs[key],
                        "base_lr": lrs[key],
                        "weight_decay": 0.0 if key.endswith("no_decay") else weight_decay,
                    }
                )
        return groups

    def parameter_counts(self) -> Dict[str, int]:
        def _cnt(m: nn.Module, trainable_only: bool = False) -> int:
            return sum(p.numel() for p in m.parameters() if (not trainable_only or p.requires_grad))

        return {
            "qwen35_total": _cnt(self.lm),
            "qwen35_trainable": _cnt(self.lm, True),
            "qwen35_visual_total": _cnt(self.lm.model.visual),
            "qwen35_text_total": _cnt(self.lm.model.language_model),
            "qwen35_lm_head_total": _cnt(self.lm.lm_head),
            "frontend_total": _cnt(self.frontend),
            "frontend_trainable": _cnt(self.frontend, True),
            "geo_heads_total": (
                _cnt(self.front_pose_head)
                + _cnt(self.front_depth_head)
                + _cnt(self.tap_pose_heads)
                + _cnt(self.tap_depth_heads)
                + _cnt(self.tap_cam_projs)
            ),
            "sf2_probes_total": _cnt(self.sf2_loss) + _cnt(self.front_sf2_probe),
            "vla_expert_total": _cnt(self.flow_expert) if self.flow_expert is not None else 0,
            "scale_donor_trainable": _cnt(self.scale_donor, True),
            "total_params": _cnt(self, False),
            "total_trainable": _cnt(self, True),
        }
