import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from student_pilot import carrier_c1_routing as routing, carrier_c1_run as run
from student_pilot.e2e_routing_rows import adapt_generated
from student_pilot.p3_provenance import load


ROOT = Path("/scratch/jjyeung/orch_cd/leg_s1_tree")
SAMPLES = Path(os.environ.get("S1_POOL_SAMPLES", ROOT / "inputs/pool_s1_samples.json"))


@unittest.skipUnless(SAMPLES.is_file(), "Requires the hash-authenticated POOL_S1 sample fixture")
class PoolRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mode = patch.dict(os.environ, S1_CPU_REHEARSAL="1")
        mode.start()
        cls.addClassCleanup(mode.stop)
        cls.samples = load(SAMPLES)["samples"]
        cls.inputs = load(ROOT / "work/fixture/assets/input.json")
        cls.receipt = load(ROOT / "work/fixture/kit_full_r6/preparation/receipt.json")
        cls.receipt = {key: value for key, value in cls.receipt.items() if key != "geometry_online"}
        cls.processor = run.processor_for_receipt(load(ROOT / "work/fixture/assets/model_v3.json"), cls.receipt)

    def test_all_real_types_adapt_and_encode_with_fixture_rgb(self):
        for sample in self.samples:
            if sample["kind"] != "packed":
                continue
            packed = sample["row"]
            with self.subTest(source=sample["set"], type=packed["question_type"], qid=packed["qid"]):
                source = {**packed["ground_record"], "suffix": packed["target"]}
                inputs = {**copy.deepcopy(self.inputs), "question": packed["question"],
                          "options": packed["options"]}
                row = adapt_generated(source, inputs, dataset="d1", scene="adapter_fixture")
                self.assertEqual(row["ground_build"]["training_admitted"], source["training_admitted"])
                self.assertEqual(row["routing"]["infrastructure_only"],
                                 not (source.get("training_admitted") is True and source.get("diagnostic_only") is False))
                batch, audit = routing.encode(self.processor, row, self.receipt["carrier_placement"],
                    self.receipt["training_mode"], self.receipt.get("frame_layout", "spread"), None)
                self.assertTrue(torch.isfinite(batch["pixel_values_videos"]).all())
                self.assertGreater(int((batch["labels"] != -100).sum()), 0)
                self.assertGreater(len(row["routing"]["tool_output_spans"]), 0)
                self.assertEqual(audit["qid"], packed["qid"])

    def test_packed_rows_keep_native_admission_and_binding(self):
        for sample in self.samples:
            if sample["kind"] != "packed":
                continue
            packed = sample["row"]
            with self.subTest(source=sample["set"], type=packed["question_type"]):
                routing.check_row(packed)
                ids = packed["provenance"]["frame_indices"]
                rgb = dict(frames=[{**frame, "source_index": index} for frame, index
                                   in zip(self.inputs["frames"], ids, strict=True)],
                           fps=self.inputs["fps"], total_num_frames=max(ids)+1)
                row = routing.c1_row(packed, rgb)
                self.assertEqual(row["routing"]["training_admitted"], packed["training_admitted"])
                self.assertEqual(row["target"], packed["target"])
                self.assertEqual(row["student_input"]["frame_indices"], ids)

    def test_unknown_revision_refuses(self):
        packed = next(sample["row"] for sample in self.samples if sample["kind"] == "packed")
        source = {**packed["ground_record"], "suffix": packed["target"], "spec_version": "3.99"}
        with self.assertRaisesRegex(ValueError, "revision"):
            adapt_generated(source, self.inputs, dataset="d1", scene="adapter_fixture")


if __name__ == "__main__":
    unittest.main()
