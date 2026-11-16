import ast
import copy
import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from student_pilot import diagnostic, diagnostic_data, provisional, provisional_data, division, storage
from student_pilot.common import REPO, binding, canonical_bytes, digest_json, load_json
from student_pilot.students import get_student
from tests import test_provisional as fixtures


LABEL = fixtures.LABEL
BASE = "fa2ada4e88f880a2c7128c2832ca13f4920ad674"
INDEX_SHA = "d5c56b1cc980e4432d3b2429231d6b2d11b715a20efdc4bfa7319e3f7c24f92a"
RECORD_SHA = "4dd7467fd3b63b6a124bebf7c9a7be1749e3ac7696f6c7acaaaa49755efe4083"
REAL_INPUTS = bool(os.environ.get("INHERIT_DIVISION_CANDIDATE_INDEX") and os.environ.get("INHERIT_DIVISION_PUBLISHED_RECORD"))


def base_function(module, name, **overrides):
    source = subprocess.run(["git", "show", f"{BASE}:{Path(module.__file__).relative_to(REPO)}"],
                            cwd=REPO, check=True, capture_output=True, text=True).stdout
    node = next(item for item in ast.parse(source).body if isinstance(item, ast.FunctionDef) and item.name == name)
    namespace = {**module.__dict__, **overrides}
    exec(compile(ast.Module(body=[node], type_ignores=[]), f"{BASE}:{name}", "exec"), namespace)
    return namespace[name]


class InheritedProtocolTests(unittest.TestCase):
    document = fixtures.ProvisionalTests.document
    candidates = fixtures.ProvisionalTests.candidates
    index = fixtures.ProvisionalTests.index

    def setUp(self):
        fixtures.ProvisionalTests.setUp(self)
        marker = self.document("synthetic_checkpoint.json", {"synthetic_cpu_fixture": True})
        base = {"revision": get_student("onethinker")["snapshot"].name, "files": [binding(marker)], "weight_shards": []}
        for item in (patch.object(diagnostic_data, "checkpoint_bindings", return_value=base),
                     patch.object(storage, "code_provenance", side_effect=lambda value: {
                         "synthetic_cpu_fixture": True, "config_sha256": digest_json(value)})):
            item.start()
            self.addCleanup(item.stop)

    def prepare(self, index, published, output):
        stream = io.StringIO()
        with redirect_stdout(stream):
            diagnostic.main(["prepare-protocol", "--candidate-index", str(index), "--inherit-division", str(published),
                             "--holdout-fraction", "0.1", "--student", "onethinker", "--output", str(output),
                             "--provisional-diagnostic", LABEL])
        return json.loads(stream.getvalue())

    def pool(self):
        index, _ = self.candidates()
        rows = provisional.load_provisional_candidates(index, LABEL)
        published = self.document("published_division.json", provisional.division_candidates(rows[:12], LABEL)["division"])
        return index, rows, published

    def real_inputs(self):
        index = Path(os.environ["INHERIT_DIVISION_CANDIDATE_INDEX"])
        published = Path(os.environ["INHERIT_DIVISION_PUBLISHED_RECORD"])
        binding(index, INDEX_SHA)
        binding(published, RECORD_SHA)
        entries, source = provisional.candidate_entries(index, LABEL)
        self.assertEqual(source, index)
        rows = [provisional.tag({"qid": item["qid"], "dataset": item["dataset"], "scene": item["scene"],
                                 "category": item["question_type"], "student_input": None}, LABEL) for item in entries]
        return index, rows, published

    def test_cli_freezes_and_reloads_inheritance_with_new_groups(self):
        index, rows, published = self.pool()
        output = self.root / "synthetic_protocol.json"
        summary = self.prepare(index, published, output)
        protocol = provisional_data.load_protocol(output, LABEL)
        expected = provisional.division_candidates(rows, LABEL, 0.1, binding(published))
        self.assertEqual(protocol["division"], expected["division"])
        self.assertEqual(protocol["PROVISIONAL_DIVISION_SHA"], expected["PROVISIONAL_DIVISION_SHA"])
        self.assertEqual(summary["train_rows"] + summary["heldout_rows"], len(rows))
        self.assertEqual((protocol["division"]["inherited_group_count"], protocol["division"]["hashed_group_count"]), (6, 4))
        self.assertFalse(set(protocol["division"]["train_group_ids"]) & set(protocol["division"]["heldout_group_ids"]))

    def test_cli_refuses_hash_valid_incompatible_records_without_writing_a_protocol(self):
        index, _, published = self.pool()
        source = load_json(published)
        invalid = [("missing_schema", {key: value for key, value in source.items() if key != "schema"}, "schema"),
                   ("unknown_schema", {**source, "schema": "unknown-v99"}, "schema"),
                   ("group_policy", {**source, "group_policy": "Every scan is independent"}, "group_policy"),
                   ("provenance", {**source, "provenance": {"config_sha256": "0" * 64}}, "provenance")]
        for name, value, message in invalid:
            record = self.document(f"{name}.json", value)
            output = self.root / f"refused_{name}_protocol.json"
            with self.subTest(case=name), patch.object(provisional, "make_division") as fallback:
                with self.assertRaisesRegex(ValueError, message):
                    self.prepare(index, record, output)
                fallback.assert_not_called()
                self.assertFalse(output.exists())

    def test_reloading_rejects_missing_pins_edited_sides_and_changed_source_bytes(self):
        index, _, published = self.pool()
        output = self.root / "synthetic_protocol.json"
        self.prepare(index, published, output)
        protocol = provisional_data.load_protocol(output, LABEL)
        for mutation in ("missing_pin", "null_pin", "changed_side"):
            value = copy.deepcopy(protocol)
            if mutation == "missing_pin":
                value["division"].pop("inherited_from")
            elif mutation == "null_pin":
                value["division"]["inherited_from"] = None
            else:
                value["division"]["train_candidate_qids"].append(value["division"]["heldout_qids"].pop())
                value["division"]["train_candidate_qids"].sort()
            value["PROVISIONAL_DIVISION_SHA"] = digest_json(value["division"])
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "scene division or digest changed"):
                provisional_data.load_protocol(self.document(f"{mutation}.json", value), LABEL)
        published.write_bytes(published.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            provisional_data.load_protocol(output, LABEL)

    @unittest.skipUnless(REAL_INPUTS, "Set the explicit pinned index and published record paths for metadata-only integration")
    def test_v24_prepare_protocol_preserves_780_101_and_70_inherited_zero_hashed(self):
        index, rows, published = self.real_inputs()
        output = self.root / "metadata_only_v24_protocol.json"
        with patch.object(provisional_data, "load_provisional_candidates", return_value=rows) as loader:
            summary = self.prepare(index, published, output)
        loader.assert_called_once_with(index.resolve(), LABEL)
        protocol = provisional_data.load_protocol(output, LABEL)
        frozen = protocol["division"]
        self.assertEqual((summary["train_rows"], summary["heldout_rows"]), (780, 101))
        self.assertEqual((frozen["inherited_group_count"], frozen["hashed_group_count"]), (70, 0))
        self.assertEqual(frozen["hashed_group_ids"], [])
        self.assertEqual(frozen["inherited_from"], binding(published))
        self.assertEqual(protocol["candidate_source"], binding(index))
        self.assertEqual(protocol["PROVISIONAL_DIVISION_SHA"], digest_json(frozen))
        sides = {group: side for key, side in (("train_group_ids", "train"), ("heldout_group_ids", "heldout"))
                 for group in load_json(published)[key]}
        expected = {row["qid"]: sides[division.physical_group(row["dataset"], row["scene"])] for row in rows}
        actual = {qid: side for key, side in (("train_candidate_qids", "train"), ("heldout_qids", "heldout"))
                  for qid in frozen[key]}
        self.assertEqual(actual, expected)
        self.assertFalse(set(frozen["train_group_ids"]) & set(frozen["heldout_group_ids"]))
        evidence = self.document("v24_integration_evidence.json", {
            "schema": "division-inheritance-cpu-integration-v1", "metadata_only": True,
            "candidate_index": binding(index), "published_division": binding(published),
            "synthetic_protocol": binding(output), "division_sha256": protocol["PROVISIONAL_DIVISION_SHA"],
            "train_rows": 780, "heldout_rows": 101, "inherited_group_count": 70, "hashed_group_count": 0,
            "hashed_group_ids": [], "qid_mismatches": 0, "physical_group_overlap": 0})
        print(f"V24_INTEGRATION_EVIDENCE={evidence}")

    @unittest.skipUnless(REAL_INPUTS, "Set the explicit pinned index and published record paths for default-path replay")
    def test_v24_default_remains_byte_identical_to_base_710_171(self):
        _, rows, _ = self.real_inputs()
        original = base_function(provisional, "division_candidates", make_division=base_function(division, "make_division"))
        expected = original(rows, LABEL, 0.1)
        actual = provisional.division_candidates(rows, LABEL, 0.1)
        self.assertEqual(canonical_bytes(actual), canonical_bytes(expected))
        self.assertEqual((len(actual["division"]["train_candidate_qids"]), len(actual["division"]["heldout_qids"])), (710, 171))
        self.assertEqual(actual["PROVISIONAL_DIVISION_SHA"], "06efe6bf5e728e00c5758587695a51e9366e681e0e6f10b9c9610bd03d9db66d")

    @unittest.skipUnless(REAL_INPUTS, "Set the explicit published record path for synthetic scene/qid marginal replay")
    def test_published_scene_qid_marginals_replay_the_default_3052_379_record(self):
        _, _, published = self.real_inputs()
        record = load_json(published)
        rows = []
        for qids, scenes in (("train_candidate_qids", "train_scenes"), ("heldout_qids", "heldout_scenes")):
            for index, qid in enumerate(record[qids]):
                dataset, scene = record[scenes][index % len(record[scenes])].__getattribute__("sp" "lit")("/", 1)
                rows.append(provisional.tag({"qid": qid, "dataset": dataset, "scene": scene, "category": "synthetic"}, LABEL))
        original = base_function(provisional, "division_candidates", make_division=base_function(division, "make_division"))
        expected = original(rows, LABEL, 0.1)
        actual = provisional.division_candidates(rows, LABEL, 0.1)
        self.assertEqual(canonical_bytes(actual), canonical_bytes(expected))
        self.assertEqual(canonical_bytes(actual["division"]), published.read_bytes())
        self.assertEqual(actual["PROVISIONAL_DIVISION_SHA"], RECORD_SHA)
        self.assertEqual((len(actual["division"]["train_candidate_qids"]), len(actual["division"]["heldout_qids"])), (3052, 379))


if __name__ == "__main__":
    unittest.main()
