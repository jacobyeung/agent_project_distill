import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np

from student_pilot.p3_provenance import file_pin
from student_pilot.row_removals import Removals


class TargetFilterTests(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix="s1_targets_", dir=os.environ["TMPDIR"]))

    def test_defect_restriction_keeps_extent_only(self):
        path = self.root() / "remove.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in (
            dict(row_key="extent", defect="extent"),
            dict(row_key="combo", defect="identity|extent")))+"\n")
        rules = Removals([{**file_pin(path), "defects": ["identity", "absent", "merged"]}])
        self.assertTrue(rules.keep(dict(row_key="extent")))
        self.assertFalse(rules.keep(dict(row_key="combo")))
        report = rules.report()[0]
        self.assertEqual((report["source_listed"], report["listed"], report["retained_by_filter"]), (2, 1, 1))

    def test_scaled_area_and_component_boundary(self):
        from student_pilot.ground_target_filter import mask_quality
        mask = np.zeros((120, 160), bool)
        mask[2:5, 2:15] = True
        self.assertTrue(mask_quality(mask)["accepted"])
        mask[2, 2] = False
        self.assertEqual(mask_quality(mask)["reason"], "area_below_runtime_floor")
        mask = np.zeros((240, 320), bool)
        mask[2:12, 2:14] = True
        mask[30:40, 30:38] = True
        self.assertTrue(mask_quality(mask)["accepted"])
        mask[2, 2] = False
        self.assertEqual(mask_quality(mask)["reason"], "fragmented_mask")

    def test_removed_and_bad_shapes_are_unknown_not_absent(self):
        from student_pilot.ground_target_filter import TargetFilter
        from student_pilot.mdg_targets import mdg_units_for_clip, to_tensors
        root = self.root()
        inst = np.full((32, 240, 320), -1, np.int16)
        inst[:, 10:30, 10:30] = 1
        inst[1] = -1
        inst[1, 10:20, 10:20] = 1
        inst[1, 40:50, 40:50] = 1
        inst[0, 80:100, 80:100] = 2
        path = root / "raster.npz"
        np.savez_compressed(path, inst=inst, used=np.ones(32, bool),
                            ids=np.array([1, 2]), labels=np.array(["chair", "table"]))
        removed = root / "remove.jsonl"
        removed.write_text("\n".join(json.dumps(dict(row_key=key, defect="identity"))
                                     for key in ("scannet/scene_test|0|1", "scannet/scene_test|0|2"))+"\n")
        source = dict(path=str(path), scene="scene_test", dataset="scannet",
                      qid="fixture", rgb_wh=[320, 240], sha256=file_pin(path)["sha256"])
        filtered = TargetFilter([file_pin(removed)], shape_filter=True).clip(source)
        units = mdg_units_for_clip(filtered, ["chair", "table", "lamp"],
                                   {"chair": ["table"]}, seed_key="fixture")
        self.assertNotIn("table", units.labels)
        index = units.labels.index("chair")
        self.assertTrue(np.isnan(units.frame_presence[index, :2]).all())
        self.assertEqual(units.frame_presence[index, 2], 1)
        self.assertFalse(to_tensors(units)["frame_valid"][index, :2].any())
        self.assertEqual(len(filtered["ignored_targets"]), 3)


if __name__ == "__main__":
    unittest.main()
