#!/usr/bin/env python3
"""Unit tests for the Leak-Free Pilot-0 Gemini API Spatial/4D Data Factory (`e05_api_factory`)."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pytest

FACTORY_DIR = Path(__file__).resolve().parent.parent
if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(FACTORY_DIR))

from exclusions import DEFAULT_PINNED_TRAIN, LeakageFatalError, RoomExclusionGuard
from gemini_client import build_contact_sheet_jpeg_b64, encode_frame_jpeg_b64
from geo_solver import (
    PARAPHRASE_TEMPLATES,
    GeoAPIV2Session,
    Scene3DGraph,
    box_iou_1000,
    convert_length,
    ego_polar_metrics,
    format_scalar,
    mra_10,
    obb_surface_gap_m,
    recompute_and_verify_trace,
)
from pilot0_runner import DEFAULT_TRAIN_LABELS, build_scaffold_calls, mine_candidate_specs


@pytest.fixture(scope="module")
def guard() -> RoomExclusionGuard:
    return RoomExclusionGuard()


@pytest.fixture(scope="module")
def pinned_doc() -> dict:
    return json.loads(DEFAULT_PINNED_TRAIN.read_bytes())


@pytest.fixture(scope="module")
def known_convs() -> dict:
    doc = json.loads(DEFAULT_TRAIN_LABELS.read_bytes())
    return {r["capture"]: r["convention"] for r in doc["rows"]}


def test_exclusion_canaries_and_fail_closed(guard: RoomExclusionGuard) -> None:
    report = guard.assert_canaries()
    assert report["passed"] == report["total"] == 9
    assert len(guard.manifest_sha256) == 64

    # Exhaustive check across every ReSTI ScanNet room scene0000..scene0149
    for idx in range(150):
        with pytest.raises(LeakageFatalError):
            guard.assert_clean(f"scannet/scene{idx:04d}_01")

    # Fail-closed on unknown datasets or unmapped ARKit visit IDs
    with pytest.raises(LeakageFatalError):
        guard.assert_clean("unknown_corpus/room_123")
    with pytest.raises(LeakageFatalError):
        guard.assert_clean("arkitscenes/99999999")


def test_pinned_train_filtering_blocks_all_withheld(guard: RoomExclusionGuard, pinned_doc: dict) -> None:
    clean, blocked = guard.filter_captures(pinned_doc["captures"])
    assert len(clean) == 233
    assert len(blocked) == 6
    for b in blocked:
        assert "withheld_80" in b["hits"]
        assert b["allowed"] is False
    for c in clean:
        verdict = guard.assert_clean(c)
        assert verdict["allowed"] is True


def test_half_extent_calibration_and_surface_gap_parity(pinned_doc: dict, known_convs: dict) -> None:
    labels_doc = json.loads(DEFAULT_TRAIN_LABELS.read_bytes())
    label_by_rowid = {r["id"]: r for r in labels_doc["rows"]}
    checked = 0
    for cap in pinned_doc["captures"][:20]:
        if not Path(cap["gt"]["path"]).is_file():
            continue
        scene = Scene3DGraph.from_capture(cap, known_conventions=known_convs)
        by_iid = {o.instance_id: o for o in scene.instances}
        for r in cap.get("rows", []):
            rid = r.get("id") or r.get("row_id")
            lrow = label_by_rowid.get(rid)
            if lrow is None or lrow.get("corrected") is None:
                continue
            assert scene.extent_convention == lrow["convention"]
            ops = r["operands"]
            gt_inst = r["gt_instances"]
            oa = by_iid.get(int(gt_inst[ops[0]]))
            ob = by_iid.get(int(gt_inst[ops[1]]))
            if oa is None or ob is None:
                continue
            gap = obb_surface_gap_m(oa.as_box_dict(), ob.as_box_dict())
            assert abs(gap - float(lrow["corrected"])) < 1e-6
            checked += 1
    assert checked >= 15


def test_chiral_180_facing_inversion_and_units() -> None:
    ref = np.array([1.0, 2.0, 0.5])
    look_at = np.array([1.0, 5.0, 0.5])  # +Y is forward
    target_right = np.array([3.5, 2.2, 0.8])  # +X is right when facing toward look_at

    pol_toward = ego_polar_metrics(ref, look_at - ref, target_right, facing="toward", unit="ft")
    pol_away = ego_polar_metrics(ref, look_at - ref, target_right, facing="away", unit="ft")

    assert pol_toward["quadrant_4way"] == "right"
    assert pol_away["quadrant_4way"] == "left"
    assert pol_toward["boundary_margin_deg"] >= 15.0
    assert abs(abs(pol_toward["bearing_deg"] - pol_away["bearing_deg"]) - 180.0) < 0.2

    # Unit conversions
    assert abs(convert_length(1.0, "cm") - 100.0) < 1e-9
    assert abs(convert_length(0.3048, "ft") - 1.0) < 1e-9
    assert abs(convert_length(0.0254, "in") - 1.0) < 1e-9
    assert format_scalar(142.44, "cm") == (142.4, "142.4")
    assert format_scalar(1.426, "m") == (1.43, "1.43")
    assert mra_10(1.43, 1.43) == 1.0


def test_paraphrase_templates_diversity() -> None:
    total = sum(len(v) for v in PARAPHRASE_TEMPLATES.values())
    assert total >= 40
    assert len(PARAPHRASE_TEMPLATES) == 8


def test_s3_epistemic_value_gating_and_recompute(
    guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict
) -> None:
    clean, _ = guard.filter_captures(pinned_doc["captures"])
    specs, scenes = mine_candidate_specs(clean[:30], guard, known_convs, max_candidates=20, seed=42)
    assert len(specs) >= 12

    families_seen = set()
    for sp in specs:
        scene = scenes[sp["canonical_scene"]]
        families_seen.add(sp["task_family"])

        # Verify S3 value-gating when UNSEEN mode is active
        if sp["epistemic_mode"] == "UNSEEN_BOX_HINT_RECOVERY":
            sess = GeoAPIV2Session(scene, simulated_modes=sp["simulated_modes"])
            unseen_res = sess.execute_call({"op": "locate", "q": sp["operands"][0]})
            assert unseen_res["status"] == "UNSEEN"
            assert "slots" not in unseen_res
            with pytest.raises(ValueError, match="S3 refusal"):
                sess.execute_call({
                    "op": "measure",
                    "op_type": "surface_gap",
                    "a": sp["operands"][0],
                    "b": sp["operands"][1],
                })

        scaffold = build_scaffold_calls(scene, sp, consensus_boxes={})
        turns = []
        for st in scaffold:
            t = dict(st)
            t["think"] = t.pop("default_think")
            turns.append(t)

        verdict = recompute_and_verify_trace(scene, sp, turns)
        assert verdict["valid"] is True, f"Failed on {sp['task_family']}: {verdict}"

        # Tampering with final answer must be caught by recompute gate
        bad_turns = [dict(t) for t in turns]
        bad_turns[-1]["answer"] = "99999.99" if sp["gt_solver"]["answer_type"] != "categorical" else "invalid_cat"
        bad_verdict = recompute_and_verify_trace(scene, sp, bad_turns)
        assert bad_verdict["valid"] is False

    assert len(families_seen) >= 5


def test_inline_jpeg_encoding(guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict) -> None:
    clean, _ = guard.filter_captures(pinned_doc["captures"])
    scene = Scene3DGraph.from_capture(clean[0], known_conventions=known_convs)
    png_path = scene.anchor_dense_paths[0]
    b64, nbytes, dims = encode_frame_jpeg_b64(png_path)
    raw = base64.b64decode(b64)
    assert raw[:2] == b"\xff\xd8"
    assert 5_000 <= nbytes <= 150_000
    assert dims[0] > 0 and dims[1] > 0

    sheet_b64, sheet_bytes = build_contact_sheet_jpeg_b64(
        [(1, scene.anchor_dense_paths[0]), (2, scene.anchor_dense_paths[1])]
    )
    assert base64.b64decode(sheet_b64)[:2] == b"\xff\xd8"
    assert sheet_bytes > 5_000
    assert box_iou_1000([100, 100, 500, 500], [100, 100, 500, 500]) == 1.0


def test_emitted_pilot0_smoke_jsonl_integrity(guard: RoomExclusionGuard) -> None:
    smoke_path = FACTORY_DIR / "pilot0_smoke.jsonl"
    boxes_path = FACTORY_DIR / "pilot0_ownhead_boxes.jsonl"
    assert smoke_path.is_file() and boxes_path.is_file()

    rows = [json.loads(line) for line in smoke_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert 20 <= len(rows) <= 50

    ious = []
    for r in rows:
        verdict = guard.assert_clean({"canonical": r["canonical_scene"], "room": r["canonical_room"]})
        assert verdict["allowed"] is True
        assert r["exclusion_sha256"] == guard.manifest_sha256
        assert r["metric_scale_locked"] == 1
        assert r["audit"]["recompute_math_exact"] is True
        assert r["audit"]["referent_unique"] is True
        assert r["audit"]["think_words"] <= 220
        assert "<geo>" in r["wire_xml"] and "<answer>" in r["wire_xml"]
        ious.append(float(r["audit"]["argon_carbon_mean_iou"]))

    assert float(np.mean(ious)) >= 0.96

