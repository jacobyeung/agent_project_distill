"""Synthetic fixtures exercise the real census parser without reading real labels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


TOOL = Path(__file__).resolve().parents[1] / "numeric_tolerance_tiers.py"
spec = importlib.util.spec_from_file_location("numeric_tolerance_tiers", TOOL)
tiers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tiers)
CENSUS = tiers.import_census(tiers.DEFAULT_REPO)
PROVENANCE = {"tool_git_commit": None, "tool_base_git_commit": "synthetic",
              "tool_sha256": "synthetic"}


class NumericToleranceTests(unittest.TestCase):
    def setUp(self):
        # Preserve fixtures: this project forbids deleting files, including cleanup.
        root = TOOL.parents[1] / "out" / "test_fixtures"
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="numeric_", dir=root))
        self.rows, self.labels, self.decisions = [], {}, []

    def add(self, identity, answer, *, gold="100", kind="object_size_estimation",
            accepted=False, complete=True, evidence=True, options=None):
        self.rows.append({"id": identity, "question_type": kind, "question": "Size in meters?",
                          "options": options, "option_letters": ["A", "B"]})
        self.labels[identity] = gold
        trace = {"question_id": identity, "question_type": kind, "pred": answer,
                 "trace": [{"role": "assistant", "provenance": "provider",
                            "content": f"<ANSWER>{answer}</ANSWER>"}] if answer is not None else []}
        path = self.root / f"trace_{identity}.json"
        path.write_text(json.dumps(trace))
        self.decisions.append({"id": identity, "accepted": accepted, "answer_correct": accepted,
            "reason": "numeric_mra_1.0", "trace_path": str(path),
            "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mechanically_complete": complete, "has_perceptual_evidence": evidence})

    def write_census(self):
        (self.root / "DECISIONS.json").write_text(json.dumps(self.decisions))
        (self.root / "SUMMARY.json").write_text(json.dumps({
            "distinct_finalized": len(self.decisions),
            "distinct_accepted": sum(d["accepted"] for d in self.decisions)}))

    def run_tool(self):
        self.write_census()
        return tiers.run(self.root, CENSUS, PROVENANCE,
                         label_loader=lambda *_: (self.rows, self.labels))

    def test_strict_and_cumulative_tiers_and_non_numeric_skip(self):
        self.add("strict", "103", accepted=True)
        self.add("seven", "107")
        self.add("twenty", "120")
        self.add("option", "A", gold="A", kind="object_rel_distance",
                 accepted=True, options=["near", "far"])
        result = self.run_tool()
        records = {r["id"]: r for r in result["records"]}
        self.assertTrue(records["strict"]["strict_accepted"])
        self.assertNotIn("option", records)
        self.assertAlmostEqual(records["seven"]["relative_error"], .07)
        # Seven percent first enters at 10%; cumulative wider tiers also include it.
        self.assertEqual([records["seven"][f"within_{t}pct"] for t in tiers.TIERS], [True]*3)
        self.assertEqual([records["twenty"][f"within_{t}pct"] for t in tiers.TIERS], [False, False, True])
        self.assertEqual([result["blended"][f"{t}pct"]["accepted"] for t in tiers.TIERS], [3, 3, 4])
        self.assertEqual(result["blended"]["10pct"]["acceptance_rate"], .75)
        self.assertEqual(result["decisions_sha256"], tiers.digest((self.root / "DECISIONS.json").read_bytes()))
        allowed = {"id", "question_type", "strict_accepted", "relative_error", "within_10pct",
                   "within_15pct", "within_25pct", "mechanically_complete", "has_perceptual_evidence"}
        self.assertTrue(all(set(r) == allowed for r in records.values()))

    def test_conditions_exclude_incomplete_and_unobserved(self):
        self.add("incomplete", "107", complete=False)
        self.add("unobserved", "107", evidence=False)
        result = self.run_tool()
        self.assertTrue(all(r["within_10pct"] for r in result["records"]))
        self.assertEqual(result["blended"]["25pct"]["accepted"], 0)

    def test_units_missing_invalid_zero_and_integer_rules(self):
        cases = [("107 m", "100", "object_size_estimation", .07),
                 ("107 cm", "100", "object_size_estimation", None),
                 ("-1", "100", "object_size_estimation", None),
                 ("1e999", "100", "object_size_estimation", None),
                 ("about 107", "100", "object_size_estimation", None),
                 (None, "100", "object_size_estimation", None),
                 ("0", "0", "object_counting", None),
                 ("12", "10", "object_counting", .2),
                 ("12.5", "10", "object_counting", None),
                 ("12", "10.5", "object_counting", None),
                 ("12 objects", "10", "object_counting", None)]
        for answer, gold, kind, expected in cases:
            row = {"question_type": kind, "question": "Size in meters?"}
            actual = tiers.relative_error(CENSUS, row, gold, answer)
            self.assertEqual(actual, expected)

    def test_numeric_type_is_not_a_hardcoded_allowlist(self):
        self.add("future", "107", kind="another_numeric_type")
        result = self.run_tool()
        self.assertEqual(result["records"][0]["question_type"], "another_numeric_type")

    def test_existing_output_refused_before_label_loading(self):
        for name in tiers.OUTPUT_NAMES:
            with self.subTest(name=name):
                path = self.root / name
                path.write_text("sentinel")
                with self.assertRaises(FileExistsError):
                    tiers.run(self.root, CENSUS, PROVENANCE,
                              label_loader=lambda *_: self.fail("loaded labels before refusing"))
                self.assertEqual(path.read_text(), "sentinel")
                self.setUp()

    def test_forbidden_output_paths_and_symlink_refused(self):
        for part in ("training", "conversion", "targets", "train_set", "converted"):
            with self.subTest(part=part), self.assertRaises(ValueError):
                tiers.validate_destination(self.root / part, self.root / part)
        forbidden = self.root / "training"
        forbidden.mkdir()
        link = self.root / "apparently_safe"
        link.symlink_to(forbidden, target_is_directory=True)
        with self.assertRaises(ValueError):
            tiers.validate_destination(link, link)
        authorized = tiers.CENSUS_ROOT / "123456789"
        self.assertEqual(tiers.validate_destination(authorized, authorized), authorized)
        with self.assertRaises(ValueError):
            tiers.validate_destination(authorized / "targets", authorized / "targets")

    def test_trace_drift_refused(self):
        self.add("drift", "107")
        self.decisions[0]["trace_sha256"] = "wrong"
        with self.assertRaises(ValueError):
            self.run_tool()
        self.assertFalse((self.root / tiers.OUTPUT_NAMES[0]).exists())

    def test_profile_is_restored(self):
        previous = sys.getprofile()
        tiers.relative_error(CENSUS, {"question_type": "object_counting"}, "10", "11")
        self.assertIs(sys.getprofile(), previous)

    def test_sanctioned_inline_loader_stops_before_census_writes(self):
        labels = self.root / "synthetic_labels.jsonl"
        labels.write_text(json.dumps({"id": "synthetic", "ground_truth": "100"}) + "\n")
        rows = [{"id": "synthetic", "question_type": "object_counting"}]
        previous = sys.gettrace()
        with patch.object(CENSUS, "LABELS", labels), \
             patch.object(CENSUS, "LABELS_SHA", tiers.digest(labels.read_bytes())), \
             patch.object(CENSUS, "teacher_rows", return_value=rows), \
             patch.object(CENSUS, "require_data_path", side_effect=lambda path: path), \
             patch.object(CENSUS, "baseline_annotations", side_effect=AssertionError("past loader")):
            loaded_rows, gold = tiers.load_census_inputs(CENSUS, self.root)
        self.assertEqual(loaded_rows, rows)
        self.assertEqual(gold, {"synthetic": "100"})
        self.assertIs(sys.gettrace(), previous)
        self.assertFalse((self.root / "SUMMARY.json").exists())


if __name__ == "__main__":
    unittest.main()
