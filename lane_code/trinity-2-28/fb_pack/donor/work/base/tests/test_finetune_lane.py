import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from student_pilot.finetune_lane import gate_candidates, parse_params, validate_student_input
from student_pilot.division import make_division


class FinetuneLaneTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="finetune_gate_test_", dir=os.environ["LANE_TEST_OUTPUT"]))
        frame = self.root / "frame.bin"
        frame.write_bytes(b"synthetic schema fixture; not model input")
        self.frame = {"path": str(frame), "sha256": hashlib.sha256(frame.read_bytes()).hexdigest()}
        self.inputs = {"question": "Synthetic question", "options": None,
                       "frames": [self.frame.copy() for _ in range(32)],
                       "frame_indices": list(range(32)), "timestamps": [index / 2 for index in range(32)],
                       "fps": 2.0, "total_num_frames": 32}

    def candidate(self, qid="fixture-1", inputs=None):
        row = {"qid": qid, "dataset": "scannet", "scene": "scene0001_00", "category": "fixture",
               "target": "Synthetic schema target", "student_input": inputs or self.inputs,
               "generation_commit": "a" * 40, "validation_commit": "a" * 40}
        row_path = self.root / f"{qid}.json"
        row_path.write_text(json.dumps(row))
        target = self.root / f"{qid}.txt"
        target.write_text(row["target"] + "\n")
        return {"qid": qid, "pool": "fixture", "dataset": row["dataset"], "scene": row["scene"],
                "question_type": row["category"], "answer": "fixture", "row_path": str(row_path),
                "row_sha256": hashlib.sha256(row_path.read_bytes()).hexdigest(), "target_path": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "generation_commit": row["generation_commit"], "validation_commit": row["validation_commit"]}

    def gate(self, rows):
        index = self.root / "candidate_index.jsonl"
        index.write_text("".join(json.dumps(row) + "\n" for row in rows))
        return gate_candidates(index)

    def test_valid_rows_keep_exact_target_and_null_options(self):
        report, candidates = self.gate([self.candidate()])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["passed"], report["failed"]), (1, 0))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["unique_frame_files_verified"], 1)

    def test_target_hash_mismatch_is_a_failure(self):
        row = self.candidate()
        row["sha256"] = "0" * 64
        report, candidates = self.gate([row])
        self.assertEqual(report["status"], "STOP")
        self.assertEqual(report["failures"][0]["qid"], row["qid"])
        self.assertIn("SHA256 mismatch", report["failures"][0]["reason"])
        self.assertFalse(candidates)

    def test_frame_hash_mismatch_is_a_failure(self):
        inputs = {**self.inputs, "frames": [{**self.frame, "sha256": "0" * 64}] * 32}
        report, _ = self.gate([self.candidate(inputs=inputs)])
        self.assertEqual(report["failed"], 1)

    def test_schema_rejects_wrong_counts_and_invalid_timing(self):
        for changes in ({"frames": []}, {"frame_indices": [0]}, {"timestamps": [0]},
                        {"fps": 0}, {"fps": float("nan")}, {"options": "A"},
                        {"question": ""}, {"timestamps": [-1] * 32}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_student_input({**self.inputs, **changes})

    def test_threshold_is_strictly_greater_than_one_percent(self):
        rows = [self.candidate(f"fixture-{index}") for index in range(100)]
        rows[-1]["sha256"] = "0" * 64
        report, candidates = self.gate(rows)
        self.assertEqual(report["status"], "PASS_WITH_DROPS")
        self.assertEqual(len(candidates), 99)
        rows[-2]["sha256"] = "0" * 64
        index = self.root / "candidate_index_second.jsonl"
        index.write_text("".join(json.dumps(row) + "\n" for row in rows))
        report, _ = gate_candidates(index)
        self.assertEqual(report["status"], "STOP")

    def test_duplicate_qids_fail_all_duplicate_rows(self):
        row = self.candidate()
        report, candidates = self.gate([row, row])
        self.assertEqual(report["failed"], 2)
        self.assertFalse(candidates)

    def test_missing_required_params_and_invalid_verdict_fail_closed(self):
        params = self.root / "TRAIN_PARAMS.env"
        params.write_text("CANDIDATE_INDEX=/fixture\nGPUS=auto\n")
        with self.assertRaises(ValueError):
            parse_params(params)
        params.write_text("CANDIDATE_INDEX=/fixture\nGPUS=auto\nPUBLISH_ROOT=/data3/jjyeung/agent_project_data/fixture\nADMISSION_VERDICT=REJECT\n")
        with self.assertRaises(ValueError):
            parse_params(params)

    def test_explicit_diagnostic_marker_and_student_selection(self):
        params = self.root / "TRAIN_PARAMS.env"
        params.write_text("CANDIDATE_INDEX=/fixture\nGPUS=auto\nPUBLISH_ROOT=/data3/jjyeung/agent_project_data/fixture\nADMISSION_VERDICT=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW\nSTUDENTS=onethinker\n")
        parsed = parse_params(params)
        self.assertEqual(parsed["label"], "diagnostic, provisional")
        self.assertEqual(parsed["STUDENTS"], "onethinker")

    def test_publication_path_cannot_escape_the_owned_data_root(self):
        params = self.root / "TRAIN_PARAMS.env"
        params.write_text("CANDIDATE_INDEX=/fixture\nGPUS=auto\nPUBLISH_ROOT=/data3/jjyeung/agent_project_data/../../escape\nADMISSION_VERDICT=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW\n")
        with self.assertRaises(ValueError):
            parse_params(params)

    def test_ten_percent_division_is_repeat_scan_disjoint(self):
        rows = [{"qid": str(index), "dataset": "scannet", "scene": f"scene{index // 2:04d}_0{index % 2}",
                 "category": "fixture"} for index in range(40)]
        division = make_division(rows, rows, seed=17, heldout_fraction=0.1)
        self.assertEqual(len(division["heldout_group_ids"]), 2)
        self.assertEqual(len(division["heldout_qids"]), 4)
        self.assertFalse(set(division["heldout_group_ids"]) & set(division["train_group_ids"]))
        self.assertEqual(division, make_division(list(reversed(rows)), list(reversed(rows)), seed=17, heldout_fraction=0.1))

    def test_division_rejects_invalid_fraction(self):
        rows = [{"qid": str(index), "dataset": "fixture", "scene": str(index), "category": "fixture"}
                for index in range(10)]
        for fraction in (0, 1, -0.1, float("nan")):
            with self.subTest(fraction=fraction), self.assertRaises(ValueError):
                make_division(rows, rows, heldout_fraction=fraction)


if __name__ == "__main__":
    unittest.main()
