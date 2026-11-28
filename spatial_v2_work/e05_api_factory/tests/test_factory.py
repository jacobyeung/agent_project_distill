#!/usr/bin/env python3
"""Unit & regression tests for the Leak-Free E05 v2 Gemini API Spatial/4D Data Factory."""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

import numpy as np
import pytest

FACTORY_DIR = Path(__file__).resolve().parent.parent
if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(FACTORY_DIR))

from exclusions import DEFAULT_PINNED_TRAIN, K1_ROWSETS_PINS, LeakageFatalError, RoomExclusionGuard
from gemini_client import (
    DEFAULT_LOCAL_USAGE_LOG,
    GeminiInlineClient,
    build_contact_sheet_jpeg_b64,
    encode_frame_jpeg_b64,
)
from geo_solver import (
    PARAPHRASE_TEMPLATES,
    GeoAPIV2Session,
    Scene3DGraph,
    box_iou_1000,
    compute_frame_pair_parallax,
    convert_length,
    ego_polar_metrics,
    format_scalar,
    mra_10,
    obb_surface_gap_m,
    recompute_and_verify_trace,
    sample_vis_frames_including_best,
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


# ---------------------------------------------------------------------------
# WARNING 5: Split R0_dev (100) vs R0_rl (272) + SHA256-pinned K1_ROWSETS
# ---------------------------------------------------------------------------
def test_exclusion_canaries_r0_split_and_k1_pins(guard: RoomExclusionGuard, tmp_path: Path) -> None:
    report = guard.assert_canaries()
    assert report["passed"] == report["total"] == 11
    assert len(guard.manifest_sha256) == 64

    # R0_dev (100 scannetpp rooms) and R0_rl (272 rooms) are cleanly partitioned and disjoint
    assert len(guard.sets["R0_dev"]) == 100
    assert all(r.startswith("scannetpp/") for r in guard.sets["R0_dev"])
    assert len(guard.sets["R0_rl"]) == 272
    assert len(guard.sets["R0_dev"] & guard.sets["R0_rl"]) == 0
    assert len(guard.sets["K1_heldout"]) >= 55

    # Both K1_ROWSETS files are SHA256-pinned in file_pins
    pinned_names = {Path(k).name: v for k, v in guard.file_pins.items()}
    for fname, expected_sha in K1_ROWSETS_PINS.items():
        assert pinned_names.get(fname) == expected_sha

    # Missing K1_ROWSETS directory MUST fail closed with LeakageFatalError
    empty_dir = tmp_path / "missing_k1_rowsets"
    empty_dir.mkdir()
    with pytest.raises(LeakageFatalError, match="Missing exclusion authority file"):
        RoomExclusionGuard(k1_rowsets_dir=empty_dir)

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


# ---------------------------------------------------------------------------
# WARNING 6: Real Half-Extent Tests Across ALL Datasets + ScanNet++ Raster Check + no_raster Reject
# ---------------------------------------------------------------------------
def test_half_extent_calibration_all_datasets_and_no_raster_rejection(
    guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict
) -> None:
    labels_doc = json.loads(DEFAULT_TRAIN_LABELS.read_bytes())
    label_by_rowid = {r["id"]: r for r in labels_doc["rows"]}
    clean, _ = guard.filter_captures(pinned_doc["captures"])

    # Select representative captures covering arkitscenes full, scannet full, scannet half, and scannetpp half
    selected: list[dict] = []
    buckets_wanted = {"arkitscenes:full": 4, "scannet:full": 4, "scannet:half": 4, "scannetpp:half": 4}
    for cap in clean:
        ds = cap["canonical"].split("/")[0]
        conv = known_convs.get(cap["canonical"])
        key = f"{ds}:{conv}"
        if buckets_wanted.get(key, 0) > 0 and Path(cap["gt"]["path"]).is_file():
            selected.append(cap)
            buckets_wanted[key] -= 1

    assert all(v == 0 for v in buckets_wanted.values()), f"Missing test captures: {buckets_wanted}"

    checked_rows = 0
    for cap in selected:
        canonical = cap["canonical"]
        expected_conv = known_convs[canonical]
        expected_tag = "half_corrected_2x" if expected_conv == "half" else "full"

        # Test BOTH with known_conventions AND pure raster containment auto-detection (known_conventions=None)
        scene_known = Scene3DGraph.from_capture(cap, known_conventions=known_convs)
        scene_auto = Scene3DGraph.from_capture(cap, known_conventions=None)
        assert scene_known.extent_convention == expected_tag
        assert scene_auto.extent_convention == expected_tag

        by_iid = {o.instance_id: o for o in scene_auto.instances}
        for r in cap.get("rows", []):
            rid = r.get("id") or r.get("row_id")
            lrow = label_by_rowid.get(rid)
            if lrow is None or lrow.get("corrected") is None:
                continue
            exp_row_tag = "half_corrected_2x" if lrow["convention"] == "half" else "full"
            assert scene_auto.extent_convention == exp_row_tag
            ops = r["operands"]
            gt_inst = r["gt_instances"]
            oa = by_iid.get(int(gt_inst[ops[0]]))
            ob = by_iid.get(int(gt_inst[ops[1]]))
            if oa is None or ob is None:
                continue
            gap = obb_surface_gap_m(oa.as_box_dict(), ob.as_box_dict())
            assert abs(gap - float(lrow["corrected"])) < 1e-6
            checked_rows += 1

    assert checked_rows >= 20

    # Explicit rejection of "no_raster" convention
    with pytest.raises(ValueError, match="no_raster"):
        Scene3DGraph.from_capture(selected[0], known_conventions={selected[0]["canonical"]: "no_raster"})


# ---------------------------------------------------------------------------
# BLOCKER 1: Zero GT Leaks in <tool_obs>, Real OOF UNSEEN, Real AND Parallax Gate
# ---------------------------------------------------------------------------
def test_zero_gt_leak_rgb_inspect_and_real_oof_unseen(
    guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict
) -> None:
    clean, _ = guard.filter_captures(pinned_doc["captures"])
    # Load a scannetpp scene known to have a real queried OOF UNSEEN object
    target_cap = next(c for c in clean if c["canonical"] == "scannetpp/3a520af32a")
    scene = Scene3DGraph.from_capture(target_cap, known_conventions=known_convs)

    # Unqueried objects MUST NOT be fabricated as UNSEEN / score=0.0
    unqueried = [o for o in scene.instances if not o.oof_queried]
    assert len(unqueried) > 0
    for o in unqueried:
        assert o.oof_max_joint_score is None
        assert o.oof_status != "UNSEEN"

    # Real queried UNSEEN object must exist
    real_unseen = [o for o in scene.instances if o.oof_queried and o.oof_max_joint_score is not None and o.oof_max_joint_score < 0.30]
    assert len(real_unseen) >= 1
    uobj = real_unseen[0]

    sess = GeoAPIV2Session(scene, simulated_modes={uobj.label: "UNSEEN"})
    loc_res = sess.execute_call({"op": "locate", "q": uobj.label})
    assert loc_res["status"] == "UNSEEN"
    assert "best_cand_f" not in loc_res
    assert "slots" not in loc_res
    assert loc_res["oof_joint_score"] == uobj.oof_max_joint_score

    # RGB inspect MUST return ONLY frame metadata — ZERO GT visible_targets / box_1000 / slot_id / px
    obs = sess.execute_call({"op": "inspect", "frame": uobj.best_frame, "q": uobj.label, "view": "rgb"})
    assert obs["view"] == "rgb"
    assert obs["frame"] == uobj.best_frame
    assert "image_ref" in obs and "resolution_hw" in obs and "valid_pose" in obs
    for forbidden in ("visible_targets", "box_1000", "slot_id", "slots", "px"):
        assert forbidden not in obs


def test_real_and_parallax_gate_and_non_constant_metrics(
    guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict
) -> None:
    clean, _ = guard.filter_captures(pinned_doc["captures"])
    # Find a scene/object with both a real narrow pair and a real wide pair passing AND gate
    found_scene = None
    found_obj = None
    narrow_pair = None
    wide_pair = None
    for cap in clean[:40]:
        try:
            sc = Scene3DGraph.from_capture(cap, known_conventions=known_convs)
        except Exception:
            continue
        for o in sc.instances:
            if len(sc.by_label[o.label]) == 1 and len(o.vis_frames) >= 4:
                npair, wpair = sc.find_narrow_and_wide_pairs(o)
                if npair is not None and wpair is not None:
                    found_scene, found_obj, narrow_pair, wide_pair = sc, o, npair, wpair
                    break
        if found_obj is not None:
            break

    assert found_scene is not None and found_obj is not None
    assert narrow_pair is not None and wide_pair is not None
    assert narrow_pair[2]["passes_gate"] is False
    assert wide_pair[2]["passes_gate"] is True
    assert wide_pair[2]["parallax_deg"] >= 15.0
    assert wide_pair[2]["beta"] >= 0.20
    assert wide_pair[2]["frame_gap"] >= 2

    sess = GeoAPIV2Session(found_scene, simulated_modes={found_obj.label: "LOW_PARALLAX"})
    r0 = sess.execute_call({"op": "locate", "q": found_obj.label})
    assert r0["status"] == "LOW_PARALLAX"
    assert "wide_cand_f" not in r0
    assert r0["parallax_deg"] == narrow_pair[2]["parallax_deg"]
    assert r0["baseline_ratio_beta"] == narrow_pair[2]["beta"]

    # Degenerate frames=[f, f] MUST fail the AND gate and keep LOW_PARALLAX active
    r_bad1 = sess.execute_call({"op": "locate", "q": found_obj.label, "frames": [found_obj.vis_frames[0], found_obj.vis_frames[0]]})
    assert r_bad1["status"] == "LOW_PARALLAX"
    assert r_bad1["reason"] == "parallax_gate_failed"

    # Real narrow pair MUST fail the AND gate
    r_bad2 = sess.execute_call({"op": "locate", "q": found_obj.label, "frames": [narrow_pair[0], narrow_pair[1]]})
    assert r_bad2["status"] == "LOW_PARALLAX"
    assert r_bad2["reason"] == "parallax_gate_failed"

    # Measure MUST still refuse while LOW_PARALLAX is unrecovered
    with pytest.raises(ValueError, match="S3 refusal"):
        sess.execute_call({"op": "measure", "op_type": "obb_size", "a": found_obj.label, "unit": "m"})

    # Genuine wide-baseline pair MUST pass and emit real parallax_deg, beta, reproj_m, pose_cond_deg
    r_ok = sess.execute_call({"op": "locate", "q": found_obj.label, "frames": [wide_pair[0], wide_pair[1]]})
    assert r_ok["status"] == "OK"
    slot = r_ok["slots"][0]
    assert slot["parallax_deg"] == wide_pair[2]["parallax_deg"]
    assert slot["baseline_ratio_beta"] == wide_pair[2]["beta"]
    assert slot["best_t"] in slot["vis_f"]
    assert slot["first_t"] in slot["vis_f"]
    assert r_ok["pose_cond_deg"] == found_scene.pose_cond_deg


# ---------------------------------------------------------------------------
# WARNING 8: yaw_deg sign (+ = left), vis_f includes best_t, randomized disambig, no BEV echo, no boilerplate
# ---------------------------------------------------------------------------
def test_yaw_deg_sign_dev_s1_left_positive() -> None:
    # Build synthetic Scene3DGraph with 3 camera poses:
    # Frame 1: facing +X (OpenCV +Z_cam = +X_world, +X_cam = -Y_world, +Y_cam = -Z_world)
    # Frame 2: turned 90 deg LEFT (CCW around +Z) -> facing +Y (+Z_cam = +Y_world)
    # Frame 3: turned 90 deg RIGHT (CW around +Z) -> facing -Y (+Z_cam = -Y_world)
    c2w = np.zeros((3, 4, 4), dtype=np.float64)
    c2w[:, 3, 3] = 1.0
    # Frame 1: fwd = +X
    c2w[0, :3, 0] = [0.0, -1.0, 0.0]
    c2w[0, :3, 1] = [0.0, 0.0, -1.0]
    c2w[0, :3, 2] = [1.0, 0.0, 0.0]
    c2w[0, :3, 3] = [0.0, 0.0, 1.0]
    # Frame 2: fwd = +Y (90 deg LEFT from +X)
    c2w[1, :3, 0] = [1.0, 0.0, 0.0]
    c2w[1, :3, 1] = [0.0, 0.0, -1.0]
    c2w[1, :3, 2] = [0.0, 1.0, 0.0]
    c2w[1, :3, 3] = [1.0, 0.0, 1.0]
    # Frame 3: fwd = -Y (90 deg RIGHT from +X)
    c2w[2, :3, 0] = [-1.0, 0.0, 0.0]
    c2w[2, :3, 1] = [0.0, 0.0, -1.0]
    c2w[2, :3, 2] = [0.0, -1.0, 0.0]
    c2w[2, :3, 3] = [0.0, -1.0, 1.0]

    sc = Scene3DGraph(
        canonical_scene="synthetic/test",
        canonical_room="synthetic/test",
        dataset="synthetic",
        extent_convention="full",
        n_anchors=3,
        image_hw=(480, 640),
        c2w=c2w,
        valid_frames=np.array([True, True, True]),
        K_frames=np.broadcast_to(np.eye(3), (3, 3, 3)).copy(),
        anchor_dense_paths=["", "", ""],
        instances=[],
        pose_cond_deg=1.1,
    )
    mot_left = sc.camera_motion(1, 2, unit="m")
    mot_right = sc.camera_motion(1, 3, unit="m")
    assert abs(mot_left["yaw_deg"] - 90.0) < 1e-4, f"Expected +90 deg for left turn, got {mot_left['yaw_deg']}"
    assert abs(mot_right["yaw_deg"] - (-90.0)) < 1e-4, f"Expected -90 deg for right turn, got {mot_right['yaw_deg']}"

    # Verify vis_f sampling ALWAYS preserves first_frame and best_frame even when late in clip
    vis_sample = sample_vis_frames_including_best(list(range(1, 31)), first_frame=2, best_frame=28, limit=8)
    assert len(vis_sample) == 8
    assert 2 in vis_sample and 28 in vis_sample


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


# ---------------------------------------------------------------------------
# BLOCKER 2 + WARNING 8: Scaling past 102 cap, randomized disambig, no BEV echo, boilerplate gate
# ---------------------------------------------------------------------------
def test_candidate_mining_scales_past_102_and_scaffold_hygiene(
    guard: RoomExclusionGuard, pinned_doc: dict, known_convs: dict
) -> None:
    clean, _ = guard.filter_captures(pinned_doc["captures"])
    specs, scenes = mine_candidate_specs(clean, guard, known_convs, max_candidates=1100, seed=20261128)
    assert len(specs) == 1100
    assert len(scenes) >= 220  # Must NOT stop at 48 scenes!

    # Verify multi_instance_disambig randomizes target_slot_index (not always 0)
    disambig_specs = [sp for sp in specs if sp["task_family"] == "multi_instance_disambig"]
    assert len(disambig_specs) >= 20
    slot_indices = {sp["target_slot_index"] for sp in disambig_specs}
    assert len(slot_indices) >= 2 and any(i > 0 for i in slot_indices)

    # Verify ALL UNSEEN specs come from real queried candidates.json objects
    unseen_specs = [sp for sp in specs if sp["epistemic_mode"] == "UNSEEN_BOX_HINT_RECOVERY"]
    assert len(unseen_specs) >= 15
    for sp in unseen_specs:
        oa = sp["verify_targets"][0][0]
        assert oa.oof_queried is True
        assert oa.oof_max_joint_score is not None and oa.oof_max_joint_score < 0.30

    # Verify scaffold execution, recompute, zero BEV echo, and boilerplate rejection on diverse slice
    families_seen = set()
    for sp in specs[:60]:
        scene = scenes[sp["canonical_scene"]]
        families_seen.add(sp["task_family"])

        scaffold = build_scaffold_calls(scene, sp, consensus_boxes={})
        # No redundant BEV inspect in multi_instance_disambig
        if sp["task_family"] == "multi_instance_disambig":
            assert all('"view":"bev"' not in st.get("call", "") for st in scaffold)

        turns = []
        for st in scaffold:
            t = dict(st)
            t["think"] = t.pop("default_think")
            turns.append(t)

        verdict = recompute_and_verify_trace(scene, sp, turns)
        assert verdict["valid"] is True, f"Failed on {sp['task_family']}: {verdict}"

        # Robotic boilerplate MUST be rejected by recompute gate
        if sp is specs[0]:
            bp_turns = [dict(t) for t in turns]
            bp_turns[-1]["think"] = "Standard measurement processing applied; emit answer."
            bp_verdict = recompute_and_verify_trace(scene, sp, bp_turns)
            assert bp_verdict["valid"] is False
            assert "robotic_boilerplate" in bp_verdict["reason"]

            bad_turns = [dict(t) for t in turns]
            bad_turns[-1]["answer"] = "99999.99" if sp["gt_solver"]["answer_type"] != "categorical" else "invalid_cat"
            assert recompute_and_verify_trace(scene, sp, bad_turns)["valid"] is False

    assert len(families_seen) >= 7


# ---------------------------------------------------------------------------
# WARNING 7 & WARNING 4: Multi-Instance Box No Disjoint Averaging + Zero NFS Usage Writes / OVER_CAP TTL
# ---------------------------------------------------------------------------
def test_multi_instance_box_never_averages_disjoint_and_local_usage_only(tmp_path: Path) -> None:
    # Local usage log MUST be on /scratch, NEVER /data* or /home*
    assert str(DEFAULT_LOCAL_USAGE_LOG).startswith("/scratch/")
    with pytest.raises(ValueError, match="local /scratch"):
        GeminiInlineClient(api_key="dummy", local_usage_log=Path("/data2/forbidden/usage.jsonl"))

    # Mock client to verify disjoint multi-instance boxes select GT-matching box rather than averaging
    client = GeminiInlineClient(
        api_key="dummy",
        over_cap_path=tmp_path / "OVER_CAP",
        over_cap_ttl_s=30.0,
        local_usage_log=Path("/scratch/jjyeung/orch_home_distill/e05_api_factory/usage.test.jsonl"),
        enable_usage_log=False,
    )
    assert client.over_cap_ttl_s >= 30.0

    # Case 1: Disjoint boxes [100,100,300,300] (matches GT) and [700,700,900,900] (other chair)
    async def mock_gen_disjoint(model: str, **kwargs: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if model == "gemini-4-argon":
            return {"present": True, "referent_clear": True, "box_2d": [100, 100, 300, 300], "visible_count": 3}, {"latency_s": 1.0}
        return {"present": True, "referent_clear": True, "box_2d": [700, 700, 900, 900], "visible_count": 3}, {"latency_s": 1.0}

    client.generate_json = mock_gen_disjoint  # type: ignore[method-assign]
    res = asyncio.run(
        client.verify_referent_argon_carbon(
            frame_jpeg_b64="AAAA",
            object_label="chair",
            gt_box_1000=[105, 105, 295, 295],
        )
    )
    assert res["agreed"] is True
    assert res["consensus_source"] == "argon_gt_selected"
    assert res["consensus_box_1000"] == [100, 100, 300, 300]  # Selected Argon box, NEVER averaged to [400,400,600,600]!
    assert res["gt_iou"] is not None and res["gt_iou"] > 0.85

    # Case 2: Disjoint boxes where NEITHER matches GT -> MUST REJECT
    async def mock_gen_both_wrong(model: str, **kwargs: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if model == "gemini-4-argon":
            return {"present": True, "referent_clear": True, "box_2d": [10, 10, 100, 100], "visible_count": 2}, {"latency_s": 1.0}
        return {"present": True, "referent_clear": True, "box_2d": [800, 800, 950, 950], "visible_count": 2}, {"latency_s": 1.0}

    client.generate_json = mock_gen_both_wrong  # type: ignore[method-assign]
    res2 = asyncio.run(
        client.verify_referent_argon_carbon(
            frame_jpeg_b64="AAAA",
            object_label="chair",
            gt_box_1000=[400, 400, 550, 550],
        )
    )
    assert res2["agreed"] is False
    assert res2["consensus_box_1000"] == [0, 0, 0, 0]

    # Verify OVER_CAP TTL caches stat checks across concurrent workers (1 stat, not 24!)
    stat_calls = 0
    orig_exists = Path.exists

    def counting_exists(self_p: Path) -> bool:
        nonlocal stat_calls
        if self_p == client.over_cap_path:
            stat_calls += 1
            return False
        return orig_exists(self_p)

    monkey = pytest.MonkeyPatch()
    monkey.setattr(Path, "exists", counting_exists)
    try:
        async def burst() -> None:
            await asyncio.gather(*(client._respect_over_cap() for _ in range(24)))

        asyncio.run(burst())
        assert stat_calls == 1
    finally:
        monkey.undo()


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
        assert len(r["exclusion_sha256"]) == 64
        assert r["metric_scale_locked"] == 1
        assert r["audit"]["recompute_math_exact"] is True
        assert r["audit"]["think_words"] <= 220
        assert "<geo>" in r["wire_xml"] and "<answer>" in r["wire_xml"]
        ious.append(float(r["audit"]["argon_carbon_mean_iou"]))

    assert float(np.mean(ious)) >= 0.95
