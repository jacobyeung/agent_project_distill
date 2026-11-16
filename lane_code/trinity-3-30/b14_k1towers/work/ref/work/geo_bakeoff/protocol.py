import json
from pathlib import Path

from .arms import MODELS


PRIMARY_TYPES = ("object_abs_distance", "object_size_estimation", "room_size_estimation")
PRIMARY = {
    "family": [{"arm": f"{model}_depth", "type": typ} for model in MODELS for typ in PRIMARY_TYPES],
    "set": "vsi", "mask": "selector", "fusion": "policy", "score": "fixed_fallback",
    "representation": "grid51", "reference": "G3T_depth_head_grid51",
    "representation_reason": "No authenticated native G3T export is available; every primary arm uses the common 51-grid",
    "family_size": 15, "multiplicity": "Holm", "alpha": .05,
    "missing_hypotheses": "p=1; do not shrink the family",
    "primary_win": "Holm-adjusted one-sided paired scene-randomization p<=0.05 and paired ci95 lower>0",
    "protected_types": "paired ci95 lower>=-2 points for both other primary types",
    "secondary_scale_head": "ci95 lower>0 on a target, other lower bounds>=-2, and added full-geometry ci95 inside [-2,2] on all three types",
    "secondary_pose": "joint versus calibration-held G3T-pose ci95 lower>0 on a target and other lower bounds>=-2",
    "secondary_pose_geometry": "paired scene ci95 upper<0 for rotation, translation and centre-scatter error differences",
    "policy_bias": "The policy and its thresholds were selected on G3T geometry; results are conditional on that policy",
    "vsti_policy": "exploratory_in_sample; VSTI decisions use fuse-all",
    "other_comparisons": "secondary; unadjusted paired intervals are descriptive, not confirmatory wins",
    "native_g3t": "deferred; native comparisons become primary only in a new preregistered seal with a native G3T reference",
}


def policy_scope(set_name, fusion):
    if fusion == "all":
        return "fuse_all"
    return "exploratory_in_sample_not_validated_for_vsti" if set_name == "vsti" else "frozen_vsi_policy"


def calibration_label(exports, representation):
    exports = Path(exports)
    if exports.name.startswith("heads_"):
        return "frozen_g3t"
    config = json.loads((exports / "config.json").read_text())
    kind = config.get("kind", "native")
    if kind in ("depth", "clip_scale", "clip_scale_depth_only", "frame_affine", "average"):
        return "frozen_g3t"
    model = config.get("candidate_model", config.get("model"))
    if representation == "native":
        return "predicted_full_intrinsics"
    if model == "mapanything" or representation == "native_centred" or config.get("project_principal_point"):
        return "centre_projected_approx"
    return "predicted_centred_intrinsics"
