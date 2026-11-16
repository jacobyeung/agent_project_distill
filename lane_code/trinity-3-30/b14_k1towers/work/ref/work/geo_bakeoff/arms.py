MODELS = ("moge2", "mapanything", "da3", "pi3x", "moge3")
ARMS = {f"{model}_native": {"model": model, "kind": "native"} for model in MODELS}
ARMS["tower_g3t"] = {"kind": "cached", "baseline": "heads_g3s64"}
ARMS["tower_vcd"] = {"kind": "cached", "baseline": "heads_g3s64_vcd"}
for model in MODELS:
    for suffix, kind, baseline in (
        ("depth", "depth", "heads_g3s64_vcd"),
        ("g3t_clip_scale", "clip_scale", "heads_g3s64"),
        ("g3t_scale_depth_only", "clip_scale_depth_only", "heads_g3s64"),
        ("g3t_frame_affine", "frame_affine", "heads_g3s64"),
        ("consensus", "consensus", "heads_g3s64_vcd"),
    ):
        ARMS[f"{model}_{suffix}"] = {"kind": kind, "candidate": model, "baseline": baseline}
ARMS["average_moge2_mapanything"] = {
    "kind": "average", "candidate": "moge2", "second": "mapanything", "baseline": "heads_g3s64_vcd",
}
ARMS["average_mapanything_da3"] = {
    "kind": "average", "candidate": "mapanything", "second": "da3", "baseline": "heads_g3s64_vcd",
}

for model in ("mapanything", "da3", "pi3x"):
    ARMS[f"{model}_g3t_pose_candidate_calibration"] = {
        "kind": "pose_g3t", "candidate": model, "baseline": "heads_g3s64_vcd",
    }
