import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student_pilot import provisional, division
from student_pilot.common import binding, canonical_bytes, digest_json


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class InheritedRecordValidationTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ["LANE_TEST_OUTPUT"])
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="inherited_record_", dir=root))
        self.rows = [provisional.tag({"qid": str(index), "dataset": "scannet", "scene": scene,
                                      "category": "object_counting"}, LABEL)
                     for index, scene in enumerate(("scene0000_00", "scene0010_00"))]
        self.record = provisional.division_candidates(self.rows, LABEL)["division"]

    def document(self, name, value):
        path = self.root / name
        path.write_bytes(canonical_bytes(value))
        return path

    def review_fixture(self, name, mutate):
        directory = os.environ.get("INHERIT_DIVISION_REVIEW_FIXTURES")
        if directory:
            source = Path(directory) / name
            path = self.root / name
            path.write_bytes(source.read_bytes())
            self.assertEqual(binding(path)["sha256"], binding(source)["sha256"])
            return path
        value = dict(self.record)
        mutate(value)
        return self.document(name, value)

    def assert_fixture_refused(self, name, message, mutate):
        pin = binding(self.review_fixture(name, mutate))
        for name, operation in (("loader", lambda: provisional.load_inherited_record(pin)),
                                ("division", lambda: provisional.division_candidates(self.rows, LABEL, 0.1, pin))):
            with self.subTest(operation=name), patch.object(provisional, "make_division") as fallback:
                with self.assertRaisesRegex(ValueError, message):
                    operation()
                fallback.assert_not_called()

    def test_missing_schema_fixture_is_refused(self):
        self.assert_fixture_refused("missing_schema.json", "schema", lambda value: value.pop("schema"))

    def test_unknown_schema_fixture_is_refused(self):
        self.assert_fixture_refused("unknown_schema.json", "schema",
                                    lambda value: value.update(schema="incompatible-unrelated-schema-v99"))

    def test_different_group_policy_fixture_is_refused(self):
        self.assert_fixture_refused("different_group_policy.json", "grouping|group_policy",
                                    lambda value: value.update(group_policy="Each scan is an independent group; never merge scan suffixes."))

    def test_wrong_embedded_provenance_fixture_is_refused(self):
        self.assert_fixture_refused("wrong_embedded_provenance.json", "provenance",
                                    lambda value: value.update(provenance={"commit": "0" * 40, "dirty": True,
                                                                         "config_sha256": "0" * 64}))

    def test_wrong_embedded_division_digest_fixture_is_refused(self):
        self.assert_fixture_refused("wrong_embedded_division_digest.json", "PROVISIONAL_DIVISION_SHA|division digest",
                                    lambda value: value.update(PROVISIONAL_DIVISION_SHA="0" * 64))

    def test_missing_group_policy_and_unknown_schema_versions_are_refused(self):
        malformed = [{key: value for key, value in self.record.items() if key != "group_policy"}]
        malformed += [{**self.record, "schema": schema} for schema in
                      ("provisional-whole-scene-division-v2", "diagnostic-whole-scene-division-v99", None, [])]
        for index, value in enumerate(malformed):
            with self.subTest(value=value.get("schema")), self.assertRaisesRegex(ValueError, "schema|grouping|group_policy"):
                provisional.load_inherited_record(binding(self.document(f"malformed_{index}.json", value)))

    def test_absent_and_content_matched_provenance_are_accepted(self):
        for index, digest_key in enumerate((None, "PROVISIONAL_DIVISION_SHA", "DIVISION_SHA")):
            value = dict(self.record)
            if digest_key:
                value[digest_key] = digest_json(value)
            for declared in (False, True):
                if declared:
                    value["provenance"] = {"commit": "a" * 40, "dirty": False, "config_sha256": digest_json(value)}
                with self.subTest(digest_key=digest_key, provenance=declared):
                    pin = binding(self.document(f"valid_{index}_{declared}.json", value))
                    self.assertEqual(provisional.load_inherited_record(pin), value)

    def test_malformed_or_stale_embedded_provenance_is_refused_after_repinning(self):
        for index, provenance in enumerate((None, [], {}, {"config_sha256": "0" * 64})):
            value = {**self.record, "provenance": provenance}
            with self.subTest(provenance=provenance), self.assertRaisesRegex(ValueError, "provenance"):
                provisional.load_inherited_record(binding(self.document(f"bad_provenance_{index}.json", value)))
        value = {**self.record, "provenance": {"config_sha256": digest_json(self.record)}}
        value["donor_scene_count"] += 1
        with self.assertRaisesRegex(ValueError, "provenance"):
            provisional.load_inherited_record(binding(self.document("repinned_content.json", value)))

    def test_newly_derived_inherited_records_can_be_inherited_again(self):
        source = binding(self.document("source.json", self.record))
        inherited = provisional.division_candidates(self.rows, LABEL, 0.1, source)["division"]
        pin = binding(self.document("derived.json", inherited))
        reloaded = provisional.load_inherited_record(pin)
        self.assertEqual(reloaded, inherited)
        result = provisional.division_candidates(self.rows, LABEL, 0.1, pin)["division"]
        for key in ("train_candidate_qids", "heldout_qids", "train_group_ids", "heldout_group_ids"):
            self.assertEqual(result[key], inherited[key])

    def test_known_v1_schemas_keep_their_declared_grouping_contract(self):
        legacy = ("Every scene group keeps the side the pinned published division record gave it;"
                  " groups that record does not name are refused, never hashed here."
                  " ScanNet sceneNNNN scan suffixes share a group.")
        for prefix in ("diagnostic", "provisional"):
            for kind, policies in (("whole", (division.WHOLE_SCENE_GROUP_POLICY,)),
                                   ("inherited", (division.INHERITED_GROUP_POLICY, legacy))):
                for index, policy in enumerate(policies):
                    value = {**self.record, "schema": f"{prefix}-{kind}-scene-division-v1", "group_policy": policy}
                    with self.subTest(schema=value["schema"], policy=index):
                        pin = binding(self.document(f"{prefix}_{kind}_{index}.json", value))
                        self.assertEqual(provisional.load_inherited_record(pin), value)
                    value["group_policy"] = "Each scan is an independent group."
                    with self.assertRaisesRegex(ValueError, "group_policy"):
                        provisional.load_inherited_record(binding(self.document(f"bad_{prefix}_{kind}_{index}.json", value)))

    def test_external_byte_pin_still_precedes_semantic_validation(self):
        path = self.document("wrong_pin.json", {"schema": "unknown"})
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            provisional.load_inherited_record({"path": str(path), "sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()
