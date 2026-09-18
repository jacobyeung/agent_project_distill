import hashlib
import unittest
from student_pilot import conversion

class LandingTests(unittest.TestCase):
    def test_tool_observation_keeps_return_and_call_binding(self):
        raw = {"trace": [{"tool_calls": [{"id": "t1", "name": "get_3d_points_in_mask", "args": {"frame": 7}}]},
                         {"role": "tool", "tool_call_id": "t1", "content": "centroid: (1, 2, 3)"}]}
        item, = conversion.tool_observations(raw)
        self.assertEqual(item["text"], raw["trace"][1]["content"])
        self.assertEqual(item["source_pointer"], "/trace/1/content")
        self.assertEqual(item["tool_name"], "get_3d_points_in_mask")
        self.assertIn('"frame": 7', item["argument_summary"])
        raw["trace"][1]["content"] = "x" * 2001
        item, = conversion.tool_observations(raw)
        self.assertEqual(item["text"], "x" * 2000 + "\n[TRUNCATED after 2000 characters]")

    def test_all_v2_requests_use_32k(self):
        self.assertEqual(conversion.request_config("v2")["max_output_tokens"], 32768)

    def test_clean_request_rejects_aliases_in_each_source_text_channel(self):
        import copy
        from student_pilot import clean_conversion
        from test_conversion_v2 import synthetic_payload
        payload = synthetic_payload()
        payload["frame_metadata"] = {"frame_indices": [], "timestamps": [], "fps": 1, "total_num_frames": 32,
            "selected_frame_positions": [], "spatial_reference_policy": "Only archived conventions."}
        for alias in ("ground_truth_answer", "correct_answer", "evaluation_qid"):
            for channel in ("question", "options", "native_final_provenance", "evidence"):
                value = copy.deepcopy(payload)
                text = alias + ": FORBIDDEN_SENTINEL"
                if channel == "evidence":
                    value["evidence"][0]["text"] = text
                    value["evidence"][0]["text_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                elif channel == "options": value[channel] = [text]
                else: value[channel] = text
                with self.subTest(alias=alias, channel=channel), self.assertRaises(ValueError):
                    clean_conversion.request_boundary(conversion.make_request(value))

    def test_perception_confidence_is_distinct_from_offline_task_score(self):
        from student_pilot.clean_conversion import check_no_selection_fields
        check_no_selection_fields({"kind": "tool_observation", "tool_name": "predict_2d_segmentation_masks",
                                   "text": '{"score": 1.0}', "argument_summary": '{"object_label": "bed"}'})
        for text in ('{"score": "OFFLINE_SENTINEL"}', '{"ground_truth_answer": "A"}', '{"correct_answer": "A"}'):
            with self.assertRaises(ValueError):
                check_no_selection_fields({"kind": "tool_observation", "tool_name": "predict_2d_segmentation_masks", "text": text})

    def test_topup_uses_collector_selection_schema_and_initial_hash(self):
        from clean_r1313_fixture import Fixture
        from student_pilot import clean_source
        fixture = Fixture(budget=32768)
        snapshot = clean_source.read_json(fixture.workspace, fixture.freeze()["path"])
        self.assertTrue(snapshot["rows"][0]["selection"]["topup_authority_verified"])

    def test_parallel_source_recheck_propagates_hash_drift(self):
        import os,json
        from pathlib import Path
        from uuid import uuid4
        from student_pilot import clean_source
        root = Path(os.environ["CLEAN_VSI590K_TEST_ROOT"]) / uuid4().hex
        root.mkdir(parents=True)
        path = root / "source.json"
        path.write_text("{}")
        pin = clean_source.pin(root, path)
        clean_source.verify_pins(root, [pin, pin])
        path.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, "Source-hash drift"):
            clean_source.verify_pins(root, [pin, pin])
