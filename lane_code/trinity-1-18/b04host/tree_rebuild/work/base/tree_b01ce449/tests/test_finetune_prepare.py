import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from student_pilot.finetune_prepare import base_reference, gpu_check, summarize_division
from student_pilot.division import make_division


class FinetunePrepareTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="finetune_prepare_test_", dir=os.environ["LANE_TEST_OUTPUT"]))

    def test_base_table_uses_named_columns_and_census_counts(self):
        results = self.root / "RESULTS.md"
        results.write_text("| OneThinker-8B | vsibench_answerable500 | 1 | 16.93% | fixture: 20.00% | vsi-bank | /fixture/vsi |\n"
                           "| OneThinker-8B | vstibench_repr450_v2 | 1 | 11.33% | fixture: 10.00% | vsti-bank | /fixture/vsti |\n")
        census = {name: [{"qid": "1", "dataset": "fixture", "scene": "clip", "question_type": "fixture"}]
                  for name in ("vsibench_answerable500", "vstibench_repr450_v2")}
        reference = base_reference(results, census, "diagnostic, provisional")
        row = reference["benchmarks"]["vsibench_answerable500"]
        self.assertEqual(row["per_type"]["fixture"]["count"], 1)
        self.assertEqual(row["per_type"]["fixture"]["base_percent"], 20)
        self.assertIsNone(row["per_type"]["fixture"]["distilled_percent"])
        self.assertEqual(row["generation_run"], "/fixture/vsi")

    def test_overlap_is_reported_without_changing_membership(self):
        entries = [{"qid": str(index), "dataset": "fixture", "scene": str(index), "question_type": "fixture"}
                   for index in range(20)]
        identities = [{**row, "category": row["question_type"]} for row in entries]
        division = make_division(identities, identities, heldout_fraction=0.1)
        train = next(row for row in entries if row["qid"] in division["train_candidate_qids"])
        heldout = next(row for row in entries if row["qid"] in division["heldout_qids"])
        summary = summarize_division(entries, division, {"fixture_benchmark": [train, heldout]})
        self.assertEqual(summary["counts"]["train"]["rows"], 18)
        self.assertEqual(summary["counts"]["heldout"]["rows"], 2)
        self.assertEqual(summary["evaluation_overlap"]["fixture_benchmark"]["raw_scene_ids"], [train["scene"]])
        self.assertFalse(summary["evaluation_overlap"]["fixture_benchmark"]["division_filtered_on_overlap"])
        self.assertEqual(summary["physical_group_intersection"], [])

    def test_auto_gpu_needs_both_zero_processes_and_40000_free(self):
        params = self.root / "TRAIN_PARAMS.env"
        params.write_text("CANDIDATE_INDEX=/fixture\nGPUS=auto\nPUBLISH_ROOT=/data3/jjyeung/agent_project_data/fixture\n"
                          "ADMISSION_VERDICT=ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW\nSTUDENTS=onethinker\n")
        outputs = [SimpleNamespace(stdout="0, 100 MiB, 49140 MiB\n1, 20000 MiB, 49140 MiB\n2, 5 MiB, 49140 MiB\n", returncode=0),
                   SimpleNamespace(stdout="pid, used_gpu_memory [MiB]\n99, 10 MiB\n", stderr="", returncode=0),
                   SimpleNamespace(stdout="pid, used_gpu_memory [MiB]\n", stderr="", returncode=0),
                   SimpleNamespace(stdout="pid, used_gpu_memory [MiB]\n", stderr="", returncode=0)]
        with patch("student_pilot.finetune_prepare.subprocess.run", side_effect=outputs):
            self.assertEqual(gpu_check(params, self.root), 0)
        result = json.loads((self.root / "GPU_SELECTION.json").read_text())
        self.assertEqual(result["qualified_indices"], [2])
        self.assertFalse(result["allocated"])
        self.assertFalse(result["coordination_lease_acquired"])


if __name__ == "__main__":
    unittest.main()
