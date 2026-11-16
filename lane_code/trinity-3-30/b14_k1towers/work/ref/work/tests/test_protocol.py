import json

from geo_bakeoff.protocol import PRIMARY, calibration_label, policy_scope


def test_primary_family_keeps_the_reserve_and_the_common_resolution():
    assert len(PRIMARY["family"]) == PRIMARY["family_size"] == 15
    assert {row["arm"] for row in PRIMARY["family"]} == {
        "moge2_depth", "moge3_depth", "mapanything_depth", "da3_depth", "pi3x_depth"}
    assert PRIMARY["set"] == "vsi" and PRIMARY["mask"] == "selector"
    assert PRIMARY["representation"] == "grid51"


def test_vsti_policy_is_explicitly_exploratory():
    assert policy_scope("vsti", "policy").startswith("exploratory")
    assert policy_scope("vsti", "all") == "fuse_all"
    assert policy_scope("vsi", "policy") == "frozen_vsi_policy"


def test_calibration_labels_separate_mapanything_cells_and_controls(tmp_path):
    config = tmp_path / "config.json"
    for kind in ("native", "pose_g3t", "consensus"):
        config.write_text(json.dumps({"model": "mapanything", "candidate_model": "mapanything", "kind": kind}))
        assert calibration_label(tmp_path, "grid51") == "centre_projected_approx"
        assert calibration_label(tmp_path, "native") == "predicted_full_intrinsics"
    config.write_text(json.dumps({"candidate_model": "mapanything", "kind": "depth"}))
    assert calibration_label(tmp_path, "grid51") == calibration_label(tmp_path, "native") == "frozen_g3t"
