"""Clean-sheet configuration and ViewSet-Unified packing for Spatial-V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Tuple

import torch

ViewSetMode = Literal["video", "multiview", "robot_wrist_exo"]
StemType = Literal["epi_adapter", "da3_small"]

QWEN35_9B_FULL_ATTN_LAYERS: Tuple[int, ...] = (4, 8, 12, 16, 20, 24, 28, 32)
QWEN35_9B_DELTANET_LAYERS: Tuple[int, ...] = tuple(
    i for i in range(1, 33) if i not in QWEN35_9B_FULL_ATTN_LAYERS
)


@dataclass
class EpiAdapterConfig:
    vit_hidden_size: int = 1152
    vit_tap_layers: Tuple[int, ...] = (9, 17, 25)
    fine_dim: int = 256
    d_model: int = 768
    num_blocks: int = 6
    num_heads: int = 12
    mlp_ratio: float = 4.0
    max_streams: int = 16
    dropout: float = 0.0
    da3_small_dim: int = 384


@dataclass
class GeoHeadsConfig:
    depth_hidden_dim: int = 256
    depth_cross_blocks: int = 2
    depth_num_heads: int = 8
    flow_horizons: Tuple[int, ...] = (-1, 1, 4, 16)
    pose_hidden_dim: int = 768
    pose_num_layers: int = 4
    pose_num_heads: int = 12
    pose_refine_iters: int = 4
    min_log_depth: float = -4.0
    max_log_depth: float = 6.0
    min_log_var: float = -6.0
    max_log_var: float = 4.0
    min_log_focal: float = -2.5
    max_log_focal: float = 2.5


@dataclass
class TTBAConfig:
    num_steps: int = 5
    init_damping: float = 1e-2
    min_damping: float = 1e-6
    max_damping: float = 1e4
    huber_delta_px: float = 4.0
    huber_delta_logz: float = 0.15
    depth_weight: float = 1.0
    reproj_weight: float = 1.0
    trigger_yaw_deg: float = 2.5
    min_improvement_ratio: float = 0.10
    min_depth: float = 0.05


@dataclass
class Metric3DRoPEConfig:
    num_heads: int = 32
    head_dim: int = 128
    rotary_dim: int = 128
    omega_min: float = 0.1
    omega_max: float = 20.0
    fourier_bands: int = 8
    injector_hidden_dim: int = 512
    max_coord_abs: float = 1e4


@dataclass
class DeltaGeoBiasConfig:
    num_heads: int = 32
    cue_dim: int = 4  # [log_depth, confidence, p_stat, pose_step_norm]


@dataclass
class SpatialForcing2Config:
    tap_layers: Tuple[int, ...] = (16, 24)
    teacher_dim: int = 1024
    probe_hidden_dim: int = 1024
    gram_num_samples: int = 512


@dataclass
class FlowExpertConfig:
    tap_layers: Tuple[int, ...] = (12, 16, 24)
    d_model: int = 1280
    num_layers: int = 7  # ~298M params at qwen35_9b scale
    num_heads: int = 16
    mlp_ratio: float = 4.0
    action_dim: int = 7
    chunk_size: int = 8
    proprio_dim: int = 8
    subgoal_dim: int = 9  # 6D rot + 3D trans in world frame
    geo_token_dim: int = 7  # [P(3), dP(3), p_stat(1)]
    detach_backbone: bool = True
    beta_alpha: float = 1.5
    beta_beta: float = 1.0
    default_ode_steps: int = 10


@dataclass
class LossWeightsConfig:
    sf2_feat: float = 0.5
    sf2_gram: float = 0.5
    depth: float = 0.4
    pose: float = 1.5
    ray: float = 0.4
    pmap: float = 0.4
    rigidity: float = 0.3
    flow: float = 0.4
    flow_sparsity: float = 0.05
    gravity: float = 0.3
    fov: float = 0.2
    reversal: float = 0.2


@dataclass
class SpatialV2Config:
    """Top-level configuration aligned to Qwen3.5-9B's 32-layer hybrid topology."""

    num_layers: int = 32
    hidden_size: int = 4096
    num_attention_heads: int = 32
    head_dim: int = 128
    full_attn_layers: Tuple[int, ...] = QWEN35_9B_FULL_ATTN_LAYERS
    deltanet_layers: Tuple[int, ...] = QWEN35_9B_DELTANET_LAYERS
    l_geo: int = 16
    stem_type: StemType = "epi_adapter"
    viewset_mode: ViewSetMode = "video"
    use_delta_geo_bias: bool = False
    use_metric_3d_rope: bool = False

    epi: EpiAdapterConfig = field(default_factory=EpiAdapterConfig)
    geo_heads: GeoHeadsConfig = field(default_factory=GeoHeadsConfig)
    ttba: TTBAConfig = field(default_factory=TTBAConfig)
    rope3d: Metric3DRoPEConfig = field(default_factory=Metric3DRoPEConfig)
    delta_bias: DeltaGeoBiasConfig = field(default_factory=DeltaGeoBiasConfig)
    sf2: SpatialForcing2Config = field(default_factory=SpatialForcing2Config)
    flow_expert: FlowExpertConfig = field(default_factory=FlowExpertConfig)
    loss_weights: LossWeightsConfig = field(default_factory=LossWeightsConfig)

    def __post_init__(self) -> None:
        if self.l_geo not in (12, 16):
            raise ValueError(f"l_geo must be 12 or 16, got {self.l_geo}")
        if self.stem_type not in ("epi_adapter", "da3_small"):
            raise ValueError(f"Unsupported stem_type: {self.stem_type}")
        if self.viewset_mode not in ("video", "multiview", "robot_wrist_exo"):
            raise ValueError(f"Unsupported viewset_mode: {self.viewset_mode}")
        if len(self.full_attn_layers) + len(self.deltanet_layers) != self.num_layers:
            raise ValueError("full_attn_layers + deltanet_layers must partition num_layers")
        if set(self.full_attn_layers) & set(self.deltanet_layers):
            raise ValueError("full_attn_layers and deltanet_layers must be disjoint")

    @property
    def lower_full_attn_layers(self) -> Tuple[int, ...]:
        return tuple(l for l in self.full_attn_layers if l <= self.l_geo)

    @property
    def upper_full_attn_layers(self) -> Tuple[int, ...]:
        return tuple(l for l in self.full_attn_layers if l > self.l_geo)

    @property
    def upper_deltanet_layers(self) -> Tuple[int, ...]:
        return tuple(l for l in self.deltanet_layers if l > self.l_geo)

    @classmethod
    def qwen35_9b(
        cls, l_geo: int = 16, stem_type: StemType = "epi_adapter", viewset_mode: ViewSetMode = "video"
    ) -> "SpatialV2Config":
        return cls(l_geo=l_geo, stem_type=stem_type, viewset_mode=viewset_mode)

    @classmethod
    def tiny(
        cls, l_geo: int = 16, stem_type: StemType = "epi_adapter", viewset_mode: ViewSetMode = "video"
    ) -> "SpatialV2Config":
        return cls(
            hidden_size=128,
            num_attention_heads=4,
            head_dim=32,
            l_geo=l_geo,
            stem_type=stem_type,
            viewset_mode=viewset_mode,
            epi=EpiAdapterConfig(vit_hidden_size=64, fine_dim=32, d_model=64, num_blocks=2, num_heads=4, da3_small_dim=48),
            geo_heads=GeoHeadsConfig(
                depth_hidden_dim=32, depth_cross_blocks=1, depth_num_heads=4,
                flow_horizons=(1,), pose_hidden_dim=64, pose_num_layers=2, pose_num_heads=4, pose_refine_iters=2,
            ),
            rope3d=Metric3DRoPEConfig(num_heads=4, head_dim=32, rotary_dim=32, fourier_bands=4, injector_hidden_dim=64),
            delta_bias=DeltaGeoBiasConfig(num_heads=4, cue_dim=4),
            sf2=SpatialForcing2Config(tap_layers=(16, 24), teacher_dim=64, probe_hidden_dim=64, gram_num_samples=32),
            flow_expert=FlowExpertConfig(
                tap_layers=(12, 16, 24), d_model=64, num_layers=2, num_heads=4, mlp_ratio=2.0,
                action_dim=7, chunk_size=8, proprio_dim=8, default_ode_steps=4,
            ),
        )


@dataclass
class ViewSetBatch:
    """Order-agnostic ViewSet-Unified metadata for arbitrary N views."""

    mode: ViewSetMode
    stream_ids: torch.Tensor  # [B, N] long
    timestamps: torch.Tensor  # [B, N] float
    is_video: torch.Tensor  # [B, N] float
    view_mask: torch.Tensor  # [B, N] bool
    temporal_merge_allowed: torch.Tensor  # [B, N-1] bool
    mrope_time_ids: torch.Tensor  # [B, N] long


def build_viewset_batch(
    mode: ViewSetMode,
    batch_size: int,
    num_views: int,
    stream_ids: Optional[Sequence[int] | torch.Tensor] = None,
    timestamps: Optional[Sequence[float] | torch.Tensor] = None,
    valid_counts: Optional[Sequence[int]] = None,
    device: Optional[torch.device] = None,
) -> ViewSetBatch:
    """Pack ViewSet-Unified metadata and cross-camera temporal_patch=2 isolation mask."""
    if num_views < 1:
        raise ValueError(f"num_views must be >= 1, got {num_views}")

    if stream_ids is None:
        if mode == "video":
            s_ids = torch.zeros((batch_size, num_views), dtype=torch.long, device=device)
        elif mode == "multiview":
            s_ids = torch.arange(num_views, dtype=torch.long, device=device).unsqueeze(0).expand(batch_size, -1).clone()
        elif mode == "robot_wrist_exo":
            s_ids = (torch.arange(num_views, dtype=torch.long, device=device) % 2).unsqueeze(0).expand(batch_size, -1).clone()
        else:
            raise ValueError(f"Unsupported ViewSetMode: {mode}")
    else:
        s_ids = torch.as_tensor(stream_ids, dtype=torch.long, device=device)
        s_ids = s_ids.unsqueeze(0).expand(batch_size, -1).clone() if s_ids.ndim == 1 else s_ids.clone()

    if timestamps is None:
        if mode == "video":
            ts = torch.linspace(0.0, 1.0, num_views, device=device).unsqueeze(0).expand(batch_size, -1).clone()
        elif mode == "multiview":
            ts = torch.zeros((batch_size, num_views), dtype=torch.float32, device=device)
        else:
            pair_idx = (torch.arange(num_views, device=device) // 2).float()
            ts = (pair_idx / max(float(pair_idx.max().item()), 1.0)).unsqueeze(0).expand(batch_size, -1).clone()
    else:
        ts = torch.as_tensor(timestamps, dtype=torch.float32, device=device)
        ts = ts.unsqueeze(0).expand(batch_size, -1).clone() if ts.ndim == 1 else ts.clone()

    is_video = torch.full((batch_size, num_views), 1.0 if mode == "video" else 0.0, dtype=torch.float32, device=device)
    view_mask = torch.ones((batch_size, num_views), dtype=torch.bool, device=device)
    if valid_counts is not None:
        for b, cnt in enumerate(valid_counts):
            view_mask[b, cnt:] = False

    if num_views > 1:
        temporal_merge_allowed = (
            (s_ids[:, :-1] == s_ids[:, 1:])
            & view_mask[:, :-1]
            & view_mask[:, 1:]
            & (is_video[:, :-1] > 0.5)
            & (is_video[:, 1:] > 0.5)
        )
    else:
        temporal_merge_allowed = torch.zeros((batch_size, 0), dtype=torch.bool, device=device)

    if mode == "video":
        mrope_time_ids = torch.arange(num_views, dtype=torch.long, device=device).unsqueeze(0).expand(batch_size, -1).clone()
    elif mode == "multiview":
        mrope_time_ids = torch.zeros((batch_size, num_views), dtype=torch.long, device=device)
    else:
        mrope_time_ids = (torch.arange(num_views, dtype=torch.long, device=device) // 2).unsqueeze(0).expand(batch_size, -1).clone()

    return ViewSetBatch(mode, s_ids, ts, is_video, view_mask, temporal_merge_allowed, mrope_time_ids)
