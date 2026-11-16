import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from student_pilot import rehearsal
from student_pilot.s1_first_step import report


class NativeFirstStepTests(unittest.TestCase):
    def records(self):
        return [dict(rank=rank, step=17, stream_means=dict(pose=1., mdg=2.),
                     components=dict(pose=1., mdg=2.), gradient_norms=dict(lm=.5, mdg=.4),
                     shapes=[dict(stream="pose"), dict(stream="mdg")],
                     skipped_microsteps=[], skip_totals=dict(skipped=0)) for rank in range(4)]

    def check(self, values):
        return report(values, dict(config_sha256="a"*64), dict(world_size=4, mix=["pose", "mdg"]),
                      17, "cpu" if rehearsal.enabled() else "cuda")

    def test_resume_allocation_checks_its_first_actual_optimizer_step(self):
        value = self.check(self.records())
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["step"], 17)
        self.assertFalse(value["production_authorized"])

    def test_each_rank_must_forward_every_stream_without_substitution(self):
        records = self.records()
        for change in (dict(shapes=[dict(stream="pose")]), dict(skipped_microsteps=[dict(stream="mdg")]),
                       dict(shapes=[dict(stream="pose"), dict(stream="mdg", substituted_from=12)])):
            values = copy.deepcopy(records)
            values[3].update(change)
            with self.subTest(change=change):
                self.assertEqual(self.check(values)["status"], "FAIL")

    def test_missing_rank_and_nonfinite_values_are_rejected(self):
        values = self.records()
        self.assertEqual(self.check(values[:-1])["status"], "FAIL")
        values[1]["components"]["mdg"] = float("nan")
        self.assertEqual(self.check(values)["status"], "FAIL")

    def test_microstep_multiplicity_must_match_the_recipe(self):
        records = self.records()
        records[2]["shapes"].append(dict(stream="pose"))
        self.assertEqual(self.check(records)["status"], "FAIL")
        recipe = dict(world_size=4, mix=["pose"]*16+["vqa"]*32+["mdg"]*8+["routing"]*16+["pointing"]*8)
        records = self.records()
        for item in records:
            item["shapes"] = [dict(stream=stream) for stream in recipe["mix"]]
            item["stream_means"] = {name: 1. for name in recipe["mix"]}
        device = "cpu" if rehearsal.enabled() else "cuda"
        self.assertEqual(report(records, {}, recipe, 17, device)["status"], "PASS")
        records[3]["shapes"].pop()
        self.assertEqual(report(records, {}, recipe, 17, device)["status"], "FAIL")

    def test_failed_first_step_cannot_checkpoint_or_export(self):
        from student_pilot import carrier_c1_run as run
        root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        recipe = dict(world_size=1, steps=1, mix=["pose", "mdg"], milestones=[1],
                      resume_every_seconds=1800, wall_seconds=7200, stop_before_seconds=3600)
        info = {**self.records()[0], "step": 1, "shapes": [], "wall_seconds": .01}
        cfg = dict(first_step_admission="all_rank_native_v1", output=str(root))
        with patch.object(run, "recipe_for", return_value=recipe), \
                patch.object(run.data, "mixed_indices", return_value=[[]]), \
                patch.object(run, "optimize_step", return_value=(info, None)), \
                patch.object(run, "checkpoint") as checkpoint, patch.object(run, "export") as export:
            with self.assertRaisesRegex(ValueError, "First native step failed admission"):
                run.run_steps(None, None, None, None, {}, root, cfg, {}, torch.device("cpu"), distributed=False)
        checkpoint.assert_not_called()
        export.assert_not_called()
        self.assertEqual(len(list((root / "inputs").glob("first_step_*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
