import copy
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from clean_r1313_fixture import Fixture
from student_pilot import clean_conversion as converter
from student_pilot import clean_source as source
from student_pilot.common import digest_json


class TopupAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Fixture(budget=32768)

    def freeze(self, fixture=None, mapping=None, **kwargs):
        fixture = fixture or self.fixture
        source_map = None
        if mapping:
            source_map = fixture.save(fixture.root / (uuid4().hex + "_map.json"),
                                      {"schema": "clean-vsi590k-source-map-v1", "files": mapping})["path"]
        return source.freeze(fixture.workspace, fixture.run_root, fixture.census, fixture.clean / uuid4().hex,
                             fixture.membership, source_map, **kwargs)

    def test_selected_32k_binds_historical_authority_initial_attempt_and_both_configs(self):
        fixture = self.fixture
        snapshot = source.load_snapshot(fixture.workspace, self.freeze()["path"])
        row = snapshot["rows"][0]
        self.assertEqual(row["selected_budget"], 32768)
        self.assertEqual(row["selection"]["selected_attempt"], "b32768")
        self.assertEqual(row["selection"]["reason"], "accepted_32k_after_authorized_capped_16k")
        self.assertTrue(row["selection"]["topup_authority_verified"])
        self.assertEqual(row["authority"]["topups"]["sha256"], fixture.pin(fixture.topup_paths[row["qid"]])["sha256"])
        self.assertEqual({item["budget"] for item in snapshot["attempt_inventory"]}, {16384, 32768})
        self.assertTrue(all(item["files"] for item in snapshot["attempt_inventory"]))
        frozen = snapshot["frozen_attempt_authority"]
        self.assertTrue(any(item["kind"] == "topup_authority" for item in frozen))
        self.assertEqual(sum(item["kind"] == "collection_config" for item in frozen), 2)
        for item in frozen:
            source.verify_pin(fixture.workspace, item)
        self.assertEqual(source.read_json(fixture.workspace, fixture.census / "TOPUPS.json"), [])

    def test_selected_16k_records_explicit_selection_reason(self):
        fixture = Fixture()
        snapshot = source.load_snapshot(fixture.workspace, self.freeze(fixture)["path"])
        self.assertEqual(snapshot["rows"][0]["selection"]["selected_attempt"], "b16384")
        self.assertEqual(snapshot["rows"][0]["selection"]["reason"], "accepted_initial_16k_by_final_census")
        self.assertEqual(snapshot["rows"][0]["selection"]["census_record_sha256"],
                         digest_json(source.read_json(fixture.workspace, fixture.census / "ACCEPTED.json")[0]))

    def test_missing_historical_topup_authority_refuses_a_runnable_snapshot(self):
        fixture = self.fixture
        path = fixture.topup_paths[fixture.qids[0]]
        mapping = {str(path): str(fixture.root / "not_staged_topups.json")}
        with self.assertRaisesRegex(ValueError, "requires_source_media|top-up"):
            self.freeze(mapping=mapping)
        frozen = self.freeze(mapping=mapping, allow_missing=True)
        snapshot = source.load_snapshot(fixture.workspace, frozen["path"], require_ready=False)
        self.assertFalse(snapshot["runnable"])
        self.assertFalse(snapshot["rows"][0]["selection"]["topup_authority_verified"])
        self.assertTrue(any(item["source_path"] == str(path) for item in snapshot["missing"]))

    def test_strict_missing_initial_trace_uses_the_historical_authority_hash(self):
        fixture = self.fixture
        path = fixture.initial_paths[fixture.qids[0]]
        expected = fixture.pin(path)["sha256"]
        with self.assertRaises(source.SnapshotIncomplete) as caught:
            self.freeze(mapping={str(path): str(fixture.root / "not_staged_initial_trace.json")}, strict=True)
        records = [item for item in caught.exception.inventory["missing"] if item["source_path"] == str(path)]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["sha256"], expected)
        self.assertEqual(records[0]["sha256_expectation"], expected)

    def test_initial_triplet_and_terminal_are_required_even_if_selected_32k_is_complete(self):
        fixture = self.fixture
        qid = fixture.qids[0]
        initial = fixture.initial_paths[qid].parent
        paths = [initial / f"trace_{qid}_clean.json", initial / "attempt.json",
                 fixture.run_root / "terminals" / (qid + "__b16384.json")]
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "requires_source_media|top-up"):
                    self.freeze(mapping={str(path): str(fixture.root / (uuid4().hex + "_missing.json"))})

    def test_missing_topup_reference_in_32k_config_is_rejected(self):
        fixture = Fixture(budget=32768, config_patch=lambda config: config.pop("topups"))
        with self.assertRaisesRegex(ValueError, "top-up"):
            self.freeze(fixture)

    def test_wrong_initial_hash_wrong_qid_and_ineligible_topup_records_are_rejected(self):
        mutations = (
            lambda rows: rows[0].update(original_trace_sha256="0" * 64),
            lambda rows: rows[0]["row"].update(id="vsi590k_999999"),
            lambda rows: rows[0].update(output_budget_tokens=16384),
            lambda rows: rows[0]["row"].update(question="Changed input"),
            lambda rows: rows.append(copy.deepcopy(rows[0])),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                fixture = Fixture(budget=32768, topup_patch=mutate)
                with self.assertRaisesRegex(ValueError, "top-up|Source-hash drift"):
                    self.freeze(fixture)

    def test_initial_attempt_membership_binding_must_match_the_selected_attempt(self):
        def corrupt(raw, clean, attempt):
            for entry in (raw, clean):
                entry["run_receipt"]["membership_sha256"] = "0" * 64
        fixture = Fixture(budget=32768, initial_patch=corrupt)
        with self.assertRaisesRegex(ValueError, "initial.*binding|top-up"):
            self.freeze(fixture)

    def test_changed_nonbudget_config_is_not_an_authorized_budget_topup(self):
        fixture = Fixture(budget=32768, config_patch=lambda config: config.update(temperature=0.8))
        with self.assertRaisesRegex(ValueError, "top-up.*config|configuration"):
            self.freeze(fixture)

    def test_every_selected_qid_has_its_own_32k_selection_authority(self):
        fixture = Fixture(qids=["vsi590k_000001", "vsi590k_000002"], budget=32768)
        snapshot = source.load_snapshot(fixture.workspace, self.freeze(fixture)["path"])
        self.assertEqual(len(snapshot["rows"]), 2)
        for row in snapshot["rows"]:
            self.assertTrue(row["selection"]["topup_authority_verified"])
            self.assertEqual(row["authority"]["topups"]["sha256"], fixture.pin(fixture.topup_paths[row["qid"]])["sha256"])
            self.assertEqual(row["selection"]["selected_trace_path"], str(fixture.raw_paths[row["qid"]]))

    def test_topup_and_config_bytes_remain_pinned_after_freezing(self):
        fixture = self.fixture
        qid = fixture.qids[0]
        raw = source.read_json(fixture.workspace, fixture.raw_paths[qid])
        paths = [fixture.topup_paths[qid], Path(raw["run_receipt"]["collection_config"]["path"])]
        for path in paths:
            with self.subTest(path=path):
                copied = fixture.save(fixture.root / (uuid4().hex + "_authority.json"), source.read_json(fixture.workspace, path))
                frozen = self.freeze(mapping={str(path): copied["path"]})
                with Path(copied["path"]).open("ab") as stream:
                    stream.write(b"\n")
                with self.assertRaisesRegex(ValueError, "Source-hash drift"):
                    source.load_snapshot(fixture.workspace, frozen["path"])

    def test_changed_initial_frame_inputs_are_not_a_budget_only_topup(self):
        def corrupt(raw, clean, attempt):
            for entry in (raw, clean):
                entry["run_receipt"]["student_inputs"]["frames"][0]["timestamp_sec"] = 123
        fixture = Fixture(budget=32768, initial_patch=corrupt)
        with self.assertRaisesRegex(ValueError, "initial inference input binding"):
            self.freeze(fixture)

    def test_loader_refuses_dropped_inventory_even_with_a_recomputed_snapshot_digest(self):
        fixture = self.fixture
        snapshot = source.read_json(fixture.workspace, self.freeze()["path"])
        snapshot["attempt_inventory"] = [item for item in snapshot["attempt_inventory"] if item["budget"] == 32768]
        snapshot["snapshot_payload_sha256"] = digest_json({key: value for key, value in snapshot.items() if key != "snapshot_payload_sha256"})
        changed = fixture.save(fixture.clean / (uuid4().hex + "_changed.json"), snapshot)
        with self.assertRaisesRegex(ValueError, "inventory lost"):
            source.load_snapshot(fixture.workspace, changed["path"])

    def test_rejected_and_missing_partial_attempts_remain_in_the_inventory(self):
        def reject(accepted, decisions):
            accepted.pop()
            decisions[-1].update(accepted=False, answer_correct=False)
        fixture = Fixture(qids=["vsi590k_000001", "vsi590k_000002"], acceptance_patch=reject)
        original_census = fixture.census
        fixture.census = fixture.root / "inputs/census_with_partial"
        for name in ("SUMMARY", "ACCEPTED", "DECISIONS", "TOPUPS"):
            fixture.save(fixture.census / (name + ".json"), source.read_json(fixture.workspace, original_census / (name + ".json")))
        fixture.save(fixture.census / "PARTIAL_ATTEMPTS.json", [{"id": "vsi590k_000003", "budget": 16384,
                                                              "reason": "partial_or_missing_final"}])
        snapshot = source.load_snapshot(fixture.workspace, self.freeze(fixture, allow_missing=True)["path"], require_ready=False)
        records = {(item["qid"], item["budget"]): item for item in snapshot["attempt_inventory"]}
        self.assertEqual(set(records), {(qid, 16384) for qid in ("vsi590k_000001", "vsi590k_000002", "vsi590k_000003")})
        rejected = records[("vsi590k_000002", 16384)]
        self.assertFalse(rejected["selected"])
        self.assertTrue(any(item["source_path"] == str(fixture.raw_paths["vsi590k_000002"]) for item in rejected["files"]))
        self.assertEqual(records[("vsi590k_000003", 16384)]["disposition"], "partial")
        self.assertTrue(any("vsi590k_000003" in item["source_path"] for item in snapshot["missing"]))
        self.assertFalse(snapshot["runnable"])


class StrictInventoryTests(unittest.TestCase):
    def test_strict_succeeds_only_with_complete_authorities_and_pixel_proofs(self):
        fixture = Fixture(frame_scene="different_scene")
        frozen = source.freeze(fixture.workspace, fixture.run_root, fixture.census, fixture.clean / "strict",
                               fixture.membership, strict=True)
        snapshot = source.load_snapshot(fixture.workspace, frozen["path"])
        self.assertTrue(snapshot["runnable"])
        self.assertTrue(snapshot["rows"][0]["media"]["path_discrepancy_resolved_by_pixels"])
        self.assertEqual(snapshot["missing"], [])

    def test_strict_reports_all_missing_references_not_only_the_first(self):
        fixture = Fixture(budget=32768, frame_scene="different_scene")
        scene = source.read_json(fixture.workspace, fixture.scene_pin["path"])
        raw = source.read_json(fixture.workspace, fixture.raw_paths[fixture.qids[0]])
        specs = [scene["frames"][0], scene["frames"][1], scene["video"], scene["alignment"],
                 raw["run_receipt"]["source_contract"], fixture.pin(fixture.topup_paths[fixture.qids[0]])]
        mapping = fixture.save(fixture.root / "map.json", {"schema": "clean-vsi590k-source-map-v1", "files": {
            spec["path"]: str(fixture.root / (f"missing_{index}.json")) for index, spec in enumerate(specs)}})
        output = fixture.clean / "strict_snapshot"
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = converter.main(["snapshot", "--strict", "--workspace", str(fixture.workspace),
                                   "--run-root", str(fixture.run_root), "--census-root", str(fixture.census),
                                   "--membership", str(fixture.membership), "--source-map", mapping["path"],
                                   "--output", str(output)])
        self.assertEqual(code, 2)
        report = json.loads(stream.getvalue())
        self.assertFalse(report["runnable"])
        self.assertEqual(report["reason"], "requires_source_media")
        missing = {(item["source_path"], item["sha256"]) for item in report["missing"]}
        self.assertTrue({(spec["path"], spec["sha256"]) for spec in specs} <= missing)
        self.assertTrue(report["frame_path_discrepancies"])
        self.assertFalse((output / "snapshot.json").exists())

    def test_strict_and_allow_missing_are_mutually_exclusive(self):
        with redirect_stdout(io.StringIO()), patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as caught:
                converter.main(["snapshot", "--workspace", "/unused", "--run-root", "/unused",
                                "--census-root", "/unused", "--output", "/unused", "--strict", "--allow-missing"])
        self.assertEqual(caught.exception.code, 2)

    def test_strict_lists_missing_core_authorities_and_other_discoverable_media(self):
        fixture = Fixture()
        scene = source.read_json(fixture.workspace, fixture.scene_pin["path"])
        mapping = fixture.save(fixture.root / "map.json", {"schema": "clean-vsi590k-source-map-v1", "files": {
            str(fixture.census / "TOPUPS.json"): str(fixture.root / "missing_census_topups.json"),
            scene["frames"][0]["path"]: str(fixture.root / "missing_first_frame.png")}})
        with self.assertRaises(source.SnapshotIncomplete) as caught:
            source.freeze(fixture.workspace, fixture.run_root, fixture.census, fixture.clean / "strict",
                          fixture.membership, mapping["path"], strict=True)
        paths = {item["source_path"] for item in caught.exception.inventory["missing"]}
        self.assertIn(str(fixture.census / "TOPUPS.json"), paths)
        self.assertIn(scene["frames"][0]["path"], paths)

    def test_strict_staged_pilot_metadata_lists_the_known_scene_path_discrepancy(self):
        evidence_path = Path(os.environ.get("R1313_APPLICABILITY", str(Path(__file__).resolve().parents[3] / "inputs/r1313_applicability.json")))
        if not evidence_path.is_file():
            self.skipTest("requires_lane_staged_pilot_metadata: " + str(evidence_path))
        workspace = Path(os.environ["CLEAN_VSI590K_WORKSPACE"])
        evidence = source.read_json(workspace, evidence_path)
        def source_row(rows):
            rows[0].update(scene_name="104acbf7d2", video="scannetppv2/104acbf7d2.mp4")
        def scene_metadata(scene):
            scene.update(scene_name="104acbf7d2", runtime_scene_id=evidence["question_scene"], video=evidence["source_video"])
            for frame in scene["frames"]:
                frame["path"] = str(Path(evidence["trace_first_student_frame"]["path"]).parent / (frame["stem"] + ".png"))
                frame["timestamp_sec"] = frame["ordinal"] / evidence["source_video"]["fps"]
            scene["frames"][0] = evidence["trace_first_student_frame"]
            scene["alignment"] = {"path": str(evidence_path.parent / "missing_pilot_alignment.json"), "sha256": "0" * 64}
            scene["source_provenance"] = {"path": str(evidence_path.parent / "missing_pilot_provenance.json"), "sha256": "0" * 64}
        fixture = Fixture(qids=["vsi590k_094586"], source_patch=source_row, scene_patch=scene_metadata)
        with self.assertRaises(source.SnapshotIncomplete) as caught:
            source.freeze(fixture.workspace, fixture.run_root, fixture.census, fixture.clean / "strict",
                          fixture.membership, strict=True)
        report = caught.exception.inventory
        text = json.dumps(report)
        self.assertIn("scannetppv2__104acbf7d2", text)
        self.assertIn("scannetppv2__15b109bd584d", text)
        first = evidence["trace_first_student_frame"]
        self.assertTrue(any(item["source_path"] == first["path"] and item["sha256"] == first["sha256"]
                            for attempt in report["attempt_inventory"] for item in attempt["files"]))
        self.assertFalse(report["runnable"])
        self.assertTrue(report["undiscovered_dependencies"])
        fixture.save(fixture.root / "STRICT_PILOT_METADATA_INVENTORY.json", report)


if __name__ == "__main__":
    unittest.main()
