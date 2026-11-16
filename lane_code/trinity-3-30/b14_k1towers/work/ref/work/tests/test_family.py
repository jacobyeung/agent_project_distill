import pytest

from geo_bakeoff.family import holm, paired_inference, primary_family, verify_family_request
from geo_bakeoff.protocol import PRIMARY_TYPES


def test_holm_is_monotone_and_keeps_missing_tests():
    assert holm([.01, .04, .03]) == pytest.approx([.03, .06, .06])
    assert holm([.001]+[1.]*14) == pytest.approx([.015]+[1.]*14)


def test_native_reference_and_primary_arms_require_the_same_sealed_run():
    request = {"kit_seal_sha256": "seal", "run_id": "run"}
    verify_family_request(request, "seal", "run")
    with pytest.raises(ValueError):
        verify_family_request(request, "seal", "other_run")
    with pytest.raises(ValueError):
        verify_family_request(request, "other_seal", "run")


def test_scene_randomization_does_not_treat_questions_as_independent():
    baseline = [{"set": "vsi", "id": str(i), "scene": f"s{i//20}", "score": .2} for i in range(60)]
    rows = [{**row, "score": .3} for row in baseline]
    result = paired_inference(rows, baseline, draws=100)
    assert result["p_one_sided"] == 1/8
    assert result["scenes"] == 3 and result["items"] == 60


def test_primary_family_does_not_shrink_when_a_model_or_scene_is_missing():
    baseline = [{"set": "vsi", "id": f"{typ}_{i}", "scene": f"s{i}", "type": typ,
                 "mask": "selector", "score": .2, "fb": .2} for typ in PRIMARY_TYPES for i in range(3)]
    incomplete = [{**row, "fb": .8} for row in baseline if row["scene"] != "s0"]
    result = primary_family({"moge2": incomplete}, baseline, draws=100, permutations=100)
    assert len(result["hypotheses"]) == 15
    assert all(row["p_one_sided"] == 1 for row in result["hypotheses"])
    assert all(not row["depth_swap_supported"] for row in result["decisions"].values())
