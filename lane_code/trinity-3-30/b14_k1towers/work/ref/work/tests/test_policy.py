from types import SimpleNamespace
import json

from geo_bakeoff.pricing_policy import missing_selector_names, rule_for, row_membership, validate_pricing, load_scene_result
from geo_bakeoff.io import json_hash
import pytest


def test_missing_selector_names_are_not_zero_counts():
    parser = lambda question: {"cat": "chair"}
    assert missing_selector_names({}, SimpleNamespace(name2ids={}), parser)
    assert not missing_selector_names({}, SimpleNamespace(name2ids={"chair": []}), parser)
    assert not missing_selector_names({}, SimpleNamespace(name2ids={"chair": [1]}), parser)


def test_fixed_type_aware_rule_has_no_per_item_tuning():
    for question_type in ("object_abs_distance", "camera_obj_abs_dist"):
        assert rule_for(question_type, "policy") == "best1"
    assert rule_for("object_size_estimation", "policy") == "voteb5"
    assert rule_for("object_abs_distance", "all") == "all"


def test_counted_program_errors_do_not_fail_a_complete_pricing_cell():
    rows = [{"set": "vsi", "id": "1", "scene": "s1", "type": "object_size_estimation",
             "mask": "selector", "pred": None, "score": 0., "fb": .4, "error": "ValueError: synthetic"}]
    config = {"items_expected": 1, "membership_sha256": row_membership(rows)}
    validate_pricing(rows, config, [])
    with pytest.raises(ValueError):
        validate_pricing([], config, [])
    with pytest.raises(ValueError):
        validate_pricing(rows, config, [{"mismatch": True}])


def test_pricing_resume_rejects_a_corrupt_scene_checkpoint(tmp_path):
    rows = [{"set": "vsi", "id": "1", "scene": "s1", "type": "object_size_estimation",
             "mask": "selector", "pred": None, "score": 0., "fb": .4, "error": None}]
    result = {"scene": "s1", "rows": rows, "errors": [], "parity": [], "raw": None}
    envelope = {"configuration_fingerprint": "fixed", "result_sha256": json_hash(result), "result": result}
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(envelope))
    assert load_scene_result(path, "s1", rows, "fixed") == result
    envelope["result"]["rows"][0]["fb"] = .9
    path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError):
        load_scene_result(path, "s1", rows, "fixed")


def test_real_program_exception_produces_a_fallback_row():
    import geo_bakeoff.pricing_policy as policy
    policy.initialize({"exports": str(policy.TOWER.parent / "heads_g3s64"), "mode": "gt",
                       "fusion": "policy", "native": None, "parity": None, "raw": False})
    set_name, original = next((s, q) for s, q in policy.modules()["run_tg"].items() if s == "vsi")
    question = {key: value for key, value in original.items() if key != "question"}
    result = policy.scene_job((original["scene_name"], [(set_name, question)]))
    assert len(result["rows"]) == len(result["errors"]) == 1
    row = result["rows"][0]
    assert row["pred"] is None and row["error"] and row["fb"] >= 0
    policy.validate_pricing(result["rows"], {"items_expected": 1, "membership_sha256": policy.row_membership(result["rows"])}, [])
