import copy
import hashlib
import json
import unittest
from pathlib import Path

from dataset_builder_fixture import SENTENCES, SOURCES, canonical, fixture_directory, make_fixture, revised_fixture, save
from student_pilot.dataset_builder import DatasetBuildError, build_dataset, render_target, scene_partition, validate_prompt


class DatasetBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_directory("builder")
        cls.fixture = make_fixture(cls.root / "sources")

    def setUp(self):
        self.output = fixture_directory(self._testMethodName)

    def build(self, index=None, name="dataset", **kwargs):
        return build_dataset(index or self.fixture["index"], self.output / name,
                             workspace_root=self.root.parent, validation_fraction=0.1, **kwargs)

    def manifest(self, result):
        return json.loads(Path(result["manifest"]).read_text())

    def test_fixture_sources_are_three_supplied_request_projections(self):
        sources = json.loads(SOURCES.read_text())["source_requests"]
        self.assertEqual([s["identity"]["qid"] for s in sources], ["3919", "1600", "2544"])
        self.assertEqual(len({s["request_sha256"] for s in sources}), 3)
        self.assertEqual([len(s["evidence_layout"]) for s in sources], [42, 21, 16])

    def test_manifest_authenticates_all_student_and_target_bytes(self):
        result = self.build(shard_size=1)
        manifest = self.manifest(result)
        self.assertEqual(manifest["example_count"], 3)
        self.assertTrue(manifest["fixture_only"])
        self.assertFalse(manifest["training_eligible"])
        base = Path(result["manifest"]).parent
        for row in manifest["examples"]:
            original = next(b for b in self.fixture["bindings"] if b["qid"] == row["qid"])
            self.assertEqual(row["question_sha256"], hashlib.sha256(original["student_input"]["question"].encode()).hexdigest())
            self.assertEqual(row["options_sha256"], hashlib.sha256(canonical(original["student_input"]["options"])).hexdigest())
            self.assertEqual(len(row["frames"]), 32)
            self.assertEqual(row["frame_order_sha256"], hashlib.sha256(canonical(row["frame_order"])).hexdigest())
            self.assertEqual(row["target"]["sha256"], hashlib.sha256(Path(row["target"]["path"]).read_bytes()).hexdigest())
            for frame in row["frames"]:
                self.assertEqual(frame["sha256"], hashlib.sha256((base / frame["path"]).read_bytes()).hexdigest())
            for position, frame in enumerate(row["frame_order"]):
                self.assertEqual(frame["position"], position)
                self.assertEqual(frame["sha256"], original["student_input"]["frames"][position]["sha256"])
        for shard in manifest["shards"]:
            self.assertEqual(shard["sha256"], hashlib.sha256((base / shard["path"]).read_bytes()).hexdigest())

    def test_records_contain_only_32_images_question_options_and_prose(self):
        result = self.build()
        manifest = self.manifest(result)
        base = Path(result["manifest"]).parent
        records = [json.loads(line) for shard in manifest["shards"] for line in (base / shard["path"]).read_text().splitlines()]
        for record in records:
            original = next(b for b in self.fixture["bindings"] if b["qid"] == record["qid"])
            messages = record["messages"]
            self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
            content = messages[0]["content"]
            self.assertEqual([item["type"] for item in content], ["image"] * 32 + ["text"])
            options = original["student_input"]["options"] or []
            expected = original["student_input"]["question"] + ("\n" + "\n".join(options) if options else "")
            self.assertEqual(content[-1]["text"], expected)
            self.assertEqual(messages[1]["content"], "\n\n".join(SENTENCES) + "\n\n<ANSWER>" + original["native_answer"] + "</ANSWER>")
            user_json = json.dumps(messages[0])
            for forbidden in ("planner", "execute_python_code", "e9000", "e9001", "987.654", "(1.25, -2.0, 3e2)", "native_answer", "citations"):
                self.assertNotIn(forbidden, user_json)
            self.assertEqual(set(content[0]), {"type", "image"})

    def test_prompt_lexicon_refuses_tools_planner_coordinates_evidence_and_controls(self):
        for fragment in ("execute_python_code", "find_frames_with_object", "SAM3", "planner", "Planner",
                         "predict_2d_points", "verify_plan_post_execution", "(1.25, -2.0, 3e2)",
                         "[.1, -.2, +.3]", "x=1 y=2 z=3", "e0017", "evidence_id", "<|im_start|>", "<ANSWER>A</ANSWER>"):
            with self.subTest(fragment=fragment), self.assertRaises(DatasetBuildError):
                validate_prompt("What is " + fragment + "?", [])
        with self.assertRaises(DatasetBuildError):
            validate_prompt("Safe question?", ["A. planner"])
        validate_prompt("What is the distance in meters?", ["A. 1", "B. 2"])

    def test_scene_split_is_disjoint_repeat_scan_aware_and_input_order_independent(self):
        result = self.build()
        base = Path(result["manifest"]).parent
        proof = json.loads((base / "split_proof.json").read_text())
        self.assertFalse(set(proof["training_groups"]) & set(proof["heldout_groups"]))
        self.assertEqual(proof["scene_intersection"], [])
        self.assertEqual(proof["qid_intersection"], [])
        self.assertEqual(proof["training_questions"], 2)
        self.assertEqual(proof["heldout_questions"], 1)
        self.assertTrue(proof["assignment_independent_of_admission_order"])
        self.assertEqual(scene_partition("scannet/scene0643_00", 17, 0.5), scene_partition("scannet/scene0643_02", 17, 0.5))
        self.assertEqual(scene_partition("scannet/scannet__scene0643_00", 17, 0.5), scene_partition("scannet/scene0643_02", 17, 0.5))
        shuffled = save(self.output / "shuffled.json", list(reversed(self.fixture["entries"])))
        reversed_result = self.build(Path(shuffled["path"]), name="reversed")
        reversed_proof = json.loads((Path(reversed_result["manifest"]).parent / "split_proof.json").read_text())
        for key in ("training_groups", "heldout_groups", "training_qids", "heldout_qids"):
            self.assertEqual(proof[key], reversed_proof[key])

    def test_dedup_uses_question_and_physical_scene_and_keeps_audit(self):
        entries = self.fixture["entries"] + [copy.deepcopy(self.fixture["entries"][0])]
        index = save(self.output / "duplicates.json", entries)
        manifest = self.manifest(self.build(Path(index["path"])))
        self.assertEqual(manifest["example_count"], 3)
        self.assertEqual(manifest["admitted_count"], 4)
        self.assertEqual(len(manifest["duplicates"]), 1)
        self.assertEqual(manifest["duplicates"][0]["kept_qid"], "3919")

    def test_dedup_normalizes_question_text_across_repeat_scans_and_qids(self):
        from dataset_builder_fixture import cloned_entry

        extra = cloned_entry(self.fixture, self.output / "repeat")
        index = save(self.output / "repeated.json", self.fixture["entries"] + [extra])
        manifest = self.manifest(self.build(Path(index["path"])))
        self.assertEqual(manifest["example_count"], 3)
        self.assertEqual(manifest["duplicates"][0]["dropped_qid"], "3919_repeat")
        self.assertEqual(manifest["duplicates"][0]["kept_qid"], "3919")

    def test_same_question_in_another_physical_scene_is_not_deduplicated(self):
        from dataset_builder_fixture import cloned_entry

        extra = cloned_entry(self.fixture, self.output / "different", scene="scene7777_00")
        index = save(self.output / "different_scene.json", self.fixture["entries"] + [extra])
        manifest = self.manifest(self.build(Path(index["path"])))
        self.assertEqual(manifest["example_count"], 4)
        self.assertFalse(manifest["duplicates"])

    def test_conflicting_duplicate_options_or_native_answers_are_rejected(self):
        from dataset_builder_fixture import cloned_entry

        for name, changes in (("options", {"change_options": True}), ("answer", {"answer": "B"})):
            with self.subTest(name=name):
                extra = cloned_entry(self.fixture, self.output / name, **changes)
                index = save(self.output / (name + ".json"), self.fixture["entries"] + [extra])
                with self.assertRaisesRegex(DatasetBuildError, "conflicting options or native answers"):
                    self.build(Path(index["path"]), name=name + "_refused")

    def test_rendering_and_output_shards_are_byte_stable(self):
        first, second = self.build(name="first"), self.build(name="second")
        for target in self.fixture["targets"]:
            expected = ("\n\n".join(SENTENCES) + "\n\n<ANSWER>" + target["answer"] + "</ANSWER>").encode()
            self.assertEqual(render_target(target).encode(), expected)
            self.assertEqual(render_target(target), render_target(json.loads(json.dumps(target))))
        one, two = self.manifest(first), self.manifest(second)
        self.assertEqual(one, two)
        for shard in one["shards"]:
            self.assertEqual((Path(first["manifest"]).parent / shard["path"]).read_bytes(),
                             (Path(second["manifest"]).parent / shard["path"]).read_bytes())

    def test_answer_body_whitespace_case_and_precision_are_never_normalized(self):
        target = copy.deepcopy(self.fixture["targets"][1])
        target["answer"] = " 0.5100 \n"
        target.pop("target")
        target.pop("target_sha256")
        self.assertTrue(render_target(target).endswith("<ANSWER> 0.5100 \n</ANSWER>"))
        self.assertTrue(render_target(target, answer_tag="answer").endswith("<answer> 0.5100 \n</answer>"))

    def test_refuses_wrong_frame_count_missing_or_wrapped_answer_and_native_disagreement(self):
        cases = [
            ("frame_count", lambda b: b["student_input"]["frames"].pop(), None),
            ("missing_answer", None, lambda t: t.pop("answer")),
            ("wrapped_answer", None, lambda t: t.update(answer="<ANSWER>C</ANSWER>")),
            ("native_disagreement", lambda b: b.update(native_answer="WRONG"), None),
            ("target_disagreement", None, lambda t: t.update(answer="WRONG")),
            ("empty_answer", None, lambda t: t.update(answer="")),
            ("whitespace_answer", None, lambda t: t.update(answer=" \n")),
        ]
        for name, binding_update, target_update in cases:
            with self.subTest(name=name):
                index = revised_fixture(self.fixture, self.output / name, binding_update=binding_update, target_update=target_update)
                with self.assertRaises(DatasetBuildError):
                    self.build(index, name=name + "_refused")
                self.assertFalse((self.output / (name + "_refused") / "manifest.json").exists())

    def test_refuses_unadmitted_or_unreviewed_targets(self):
        for name, entry_update, review_update in (
            ("unadmitted", lambda e: e.update(admitted=False), None),
            ("missing_review", lambda e: e.pop("review"), None),
            ("dependent_review", None, lambda r: r.update(independent_of_converter=False)),
            ("missing_claim", None, lambda r: r["supported_claim_ids"].pop()),
        ):
            with self.subTest(name=name):
                index = revised_fixture(self.fixture, self.output / name, entry_update=entry_update, review_update=review_update)
                with self.assertRaises(DatasetBuildError):
                    self.build(index, name=name + "_refused")

    def test_refuses_stale_target_binding_frame_and_citation_hashes(self):
        for name, binding_update, target_update, entry_update in (
            ("frame", lambda b: b["student_input"]["frames"][0].update(sha256="0" * 64), None, None),
            ("target", None, None, lambda e: e["target"].update(sha256="0" * 64)),
            ("binding", None, None, lambda e: e["binding"].update(sha256="0" * 64)),
            ("citation", None, lambda t: t["claims"][0]["citations"][0].update(start=1), None),
            ("claim_text", None, lambda t: t["claims"][0].update(text="Modified claim."), None),
            ("answer_only", None, lambda t: t.update(explanation=t["explanation"][:1]), None),
        ):
            with self.subTest(name=name):
                index = revised_fixture(self.fixture, self.output / name, binding_update=binding_update,
                                        target_update=target_update, entry_update=entry_update)
                with self.assertRaises(DatasetBuildError):
                    self.build(index, name=name + "_refused")

    def test_refuses_external_paths_before_reading_them(self):
        index = revised_fixture(self.fixture, self.output / "external",
                                binding_update=lambda b: b["student_input"]["frames"][0].update(path="/data2/never-read-dataset-fixture.png"))
        with self.assertRaisesRegex(DatasetBuildError, "workspace"):
            self.build(index)

    def test_refuses_existing_output_without_modifying_it(self):
        result = self.build()
        before = Path(result["manifest"]).read_bytes()
        with self.assertRaises(DatasetBuildError):
            self.build()
        self.assertEqual(Path(result["manifest"]).read_bytes(), before)

    def test_refuses_invalid_rgb_and_original_timing(self):
        from PIL import Image

        grey = self.output / "grey.png"
        Image.new("L", (32, 32), 10).save(grey)
        broken = save(self.output / "broken.png", b"not image bytes")
        grey_pin = {"path": str(grey), "sha256": hashlib.sha256(grey.read_bytes()).hexdigest()}
        cases = (
            ("grey", lambda b: b["student_input"]["frames"].__setitem__(0, grey_pin)),
            ("broken", lambda b: b["student_input"]["frames"].__setitem__(0, broken)),
            ("fps", lambda b: b["student_input"].update(fps=0)),
            ("repeated_index", lambda b: b["student_input"]["frame_indices"].__setitem__(1, 0)),
            ("timestamp", lambda b: b["student_input"]["timestamps"].__setitem__(0, 99)),
            ("teacher_extra", lambda b: b["student_input"].update(measurements="987.654 meters")),
        )
        for name, update in cases:
            with self.subTest(name=name):
                index = revised_fixture(self.fixture, self.output / name, binding_update=update)
                with self.assertRaises(DatasetBuildError):
                    self.build(index, name=name + "_refused")

    def test_bad_duplicate_cannot_hide_behind_an_admitted_keeper(self):
        entries = copy.deepcopy(self.fixture["entries"])
        bad = copy.deepcopy(entries[0])
        bad["target"]["sha256"] = "0" * 64
        index = save(self.output / "bad_duplicate.json", entries + [bad])
        with self.assertRaises(DatasetBuildError):
            self.build(Path(index["path"]))

    def test_reused_authenticated_frames_are_decoded_once_per_build(self):
        from PIL import Image
        from unittest.mock import patch

        index = save(self.output / "reused.json", self.fixture["entries"] + [self.fixture["entries"][0]])
        with patch("student_pilot.dataset_builder.Image.open", wraps=Image.open) as opened:
            self.build(Path(index["path"]))
        self.assertEqual(opened.call_count, 96)

    def test_duplicate_json_keys_are_rejected(self):
        pin = save(self.output / "ambiguous.json", b'{"schema":"student-admission-index-v1","rows":[],"rows":[]}')
        with self.assertRaisesRegex(DatasetBuildError, "Duplicate JSON key"):
            self.build(Path(pin["path"]))

    def test_empty_admissions_and_invalid_build_parameters_refuse(self):
        pin = save(self.output / "empty.json", [])
        with self.assertRaises(DatasetBuildError):
            self.build(Path(pin["path"]))
        for fraction in (0, 1, -0.5, float("nan"), float("inf"), True):
            with self.subTest(fraction=fraction), self.assertRaises(DatasetBuildError):
                scene_partition("scannet/scene0001", validation_fraction=fraction)
        with self.assertRaises(DatasetBuildError):
            self.build(shard_size=0)

    def test_entrypoint_paths_are_relative_to_current_directory(self):
        from unittest.mock import patch

        with patch("student_pilot.dataset_builder.Path.cwd", return_value=self.root):
            result = build_dataset(self.fixture["index"].relative_to(self.root),
                                   Path("..") / self.output.name / "relative", self.root.parent)
        self.assertEqual(result["example_count"], 3)
        self.assertTrue((self.output / "relative/manifest.json").is_file())

    def test_split_is_stable_when_new_scenes_arrive(self):
        for group in ("scannet/scene0001", "scannet/scene9999", "scannetpp/example"):
            before = scene_partition(group, seed=17, validation_fraction=0.1)
            for other in ("scannet/scene2222", "scannetpp/another"):
                scene_partition(other, seed=17, validation_fraction=0.1)
            self.assertEqual(before, scene_partition(group, seed=17, validation_fraction=0.1))


if __name__ == "__main__":
    unittest.main()
