"""Spatial-V2 clean-sheet GeoLoop-Delta + Spatial-Forcing^2 PyTorch modules."""

from .config import (
    DeltaGeoBiasConfig, EpiAdapterConfig, FlowExpertConfig, GeoHeadsConfig,
    LossWeightsConfig, Metric3DRoPEConfig, QWEN35_9B_DELTANET_LAYERS,
    QWEN35_9B_FULL_ATTN_LAYERS, SpatialForcing2Config, SpatialV2Config,
    TTBAConfig, ViewSetBatch, build_viewset_batch,
)
from .epi_adapter import (
    DA3SmallStemAdapter, EpiAdapter, EpiAdapterOutput, EpiBlock,
    RMSNorm, apply_2d_axial_rope, pack_views_for_temporal_patch2, prevent_temporal_patch_bleeding,
)
from .geo_heads import (
    GeoDepthHead, GeoDepthOutput, GeoPoseHead, GeoPoseOutput,
    build_intrinsics_matrix, compute_gravity_leveled_poses, compute_plucker_rays,
    matrix_to_rotation_6d, project_points, rotation_6d_to_matrix,
    se3_exp, se3_log, so3_exp, so3_log, unproject_depth,
)
from .losses import DecoupledDepthLoss, PoseAnd4DLoss, SpatialForcing2Loss, SpatialV2CompositeLoss
from .metric_3d_rope import DeltaGeoBias, Metric3DRoPE, PluckerGeoInjector, apply_rope_phases, deltanet_3d_step
from .ttba import TTBA, TTBADiagnostics, TTBAOutput, compute_ray_yaw_disagreement_deg
from .vla_expert import FlowExpert, FlowMemoryCache

__all__ = [
    "QWEN35_9B_FULL_ATTN_LAYERS", "QWEN35_9B_DELTANET_LAYERS", "SpatialV2Config",
    "EpiAdapterConfig", "GeoHeadsConfig", "TTBAConfig", "Metric3DRoPEConfig",
    "DeltaGeoBiasConfig", "SpatialForcing2Config", "FlowExpertConfig", "LossWeightsConfig",
    "ViewSetBatch", "build_viewset_batch", "RMSNorm", "EpiBlock", "EpiAdapter",
    "EpiAdapterOutput", "DA3SmallStemAdapter", "apply_2d_axial_rope",
    "pack_views_for_temporal_patch2", "prevent_temporal_patch_bleeding", "GeoDepthHead", "GeoDepthOutput", "GeoPoseHead",
    "GeoPoseOutput", "so3_exp", "so3_log", "se3_exp", "se3_log", "rotation_6d_to_matrix",
    "matrix_to_rotation_6d", "build_intrinsics_matrix", "compute_gravity_leveled_poses",
    "compute_plucker_rays", "unproject_depth", "project_points", "TTBA", "TTBAOutput",
    "TTBADiagnostics", "compute_ray_yaw_disagreement_deg", "Metric3DRoPE",
    "PluckerGeoInjector", "DeltaGeoBias", "apply_rope_phases", "deltanet_3d_step",
    "SpatialForcing2Loss", "DecoupledDepthLoss", "PoseAnd4DLoss", "SpatialV2CompositeLoss",
    "FlowExpert", "FlowMemoryCache",
]
