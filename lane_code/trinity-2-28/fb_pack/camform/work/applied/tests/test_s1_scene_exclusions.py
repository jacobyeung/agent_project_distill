import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from student_pilot.p3_provenance import file_pin, load, write


class SceneExclusionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        manifest = dict(schema="dev_s1_withhold_v1", canonical={"d1/scene0155_00": ["scannet/scene0155_00"]},
                        natives=["scannet/scene0155_00"], rooms=["d1/scene0155"],
                        physical_groups=["scannet/scene0155"],
                        aliases={"d1/scene0155_00": ["d1/scene0155_00", "d1/vfixture"]})
        write(self.root / "withhold.json", manifest)
        self.pin = file_pin(self.root / "withhold.json")
        self.rows = [dict(dataset="d1", scene="vfixture"), dict(dataset="d1", scene="kept")]
        database = self.root / "rows.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE rows(i INTEGER PRIMARY KEY, row TEXT, target TEXT)")
            connection.executemany("INSERT INTO rows VALUES(?,?,?)",
                                   [(i, json.dumps(row), "{}") for i, row in enumerate(self.rows)])
        self.source = dict(database=file_pin(database), count=2, source_count=2,
                           receipt=self.pin)

    def test_canonical_alias_room_and_physical_group_match(self):
        from student_pilot.s1_exclusions import Exclusions
        rule = Exclusions(self.pin)
        for row in (self.rows[0], dict(dataset="scannet", scene="scene0155_00"),
                    dict(dataset="d1", scene="scene0155_99"),
                    dict(dataset="d1", scene="opaque", physical_group="scannet/scene0155"),
                    dict(scene="scannet/scene0155_00")):
            self.assertTrue(rule.excluded(row), row)
        self.assertFalse(rule.excluded(self.rows[1]))
        with self.assertRaises(ValueError):
            rule.excluded(dict(scene="opaque"))

    def test_every_database_stream_filters_and_authenticates(self):
        from student_pilot.s1_exclusions import apply, verify
        streams = {name: dict(self.source) for name in ("pose", "vqa", "pointing", "routing")}
        selected, report = apply(streams, self.pin, self.root)
        for name, value in selected.items():
            self.assertEqual(load(value["indices"]["path"]), [1])
            self.assertEqual(value["count"], 1)
            self.assertEqual(report["sources"][name]["removed"], 1)
            self.assertEqual(value["scene_source"], streams[name])
        receipt = dict(streams=selected, dev_scene_exclusions=self.pin, scene_filter_report=report)
        verify(receipt, dict(dev_scene_exclusions=self.pin))
        altered = copy.deepcopy(receipt)
        write(self.root / "leaked.json", [0, 1])
        altered["streams"]["routing"].update(indices=file_pin(self.root / "leaked.json"), count=2)
        with self.assertRaisesRegex(ValueError, "Scene selection"):
            verify(altered, dict(dev_scene_exclusions=self.pin))

    def test_pose_mix_preserves_source_addressing_and_order(self):
        from student_pilot.s1_exclusions import apply, verify
        write(self.root / "order.json", [[0, 0], [1, 0], [0, 1], [1, 1]])
        source = dict(kind="mix", sources=[dict(kind="rows", **self.source),
                                          dict(kind="rows", **self.source)],
                      order=file_pin(self.root / "order.json"), count=4, receipt=self.pin)
        streams, report = apply(dict(pose=source), self.pin, self.root)
        self.assertEqual(load(streams["pose"]["order"]["path"]), [[0, 1], [1, 1]])
        self.assertEqual([part["count"] for part in streams["pose"]["sources"]], [2, 2])
        self.assertEqual(report["sources"]["pose/0"]["removed"], 1)
        self.assertEqual(report["sources"]["pose/1"]["removed"], 1)
        verify(dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report),
               dict(dev_scene_exclusions=self.pin))

    def test_mdg_filters_training_and_calibration_scenes(self):
        from student_pilot.s1_exclusions import apply, verify
        index = {name: copy.deepcopy(self.rows) for name in ("train", "tau", "val")}
        index["vocab"] = ["chair"]
        write(self.root / "mdg.json", index)
        source = dict(kind="mdg", count=2, index=file_pin(self.root / "mdg.json"),
                      receipt=self.pin)
        streams, report = apply(dict(mdg=source), self.pin, self.root)
        result = load(streams["mdg"]["index"]["path"])
        self.assertEqual(result["vocab"], ["chair"])
        for split in ("train", "tau", "val"):
            self.assertEqual(result[split], self.rows[1:])
            self.assertEqual(report["sources"]["mdg/"+split]["removed"], 1)
        verify(dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report),
               dict(dev_scene_exclusions=self.pin))

    def test_changed_or_unbound_exclusion_list_refuses(self):
        from student_pilot.s1_exclusions import apply, verify
        streams, report = apply(dict(vqa=self.source), self.pin, self.root)
        receipt = dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report)
        with self.assertRaisesRegex(ValueError, "Scene exclusion"):
            verify(receipt, {})
        changed = load(self.pin["path"])
        changed["rooms"] = []
        Path(self.pin["path"]).write_text(json.dumps(changed))
        with self.assertRaises(ValueError):
            verify(receipt, dict(dev_scene_exclusions=self.pin))

    def test_native_mdg_clip_reference_is_not_a_source_receipt(self):
        from student_pilot.s1_exclusions import apply, verify
        clips = self.root / "clips.jsonl"
        clips.write_text("".join(json.dumps(row)+"\n" for row in self.rows))
        write(self.root / "mdg_index.json", dict(train=self.rows, tau=self.rows, val=self.rows))
        for index, reference in enumerate((str(clips), file_pin(clips))):
            with self.subTest(reference=reference):
                source = dict(kind="mdg", receipt=reference, count=2,
                              index=file_pin(self.root / "mdg_index.json"))
                streams, report = apply(dict(mdg=source), self.pin, self.root / str(index))
                self.assertEqual(streams["mdg"]["count"], 1)
                self.assertNotIn("upstream", report)
                verify(dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report),
                       dict(dev_scene_exclusions=self.pin))

    def test_real_dev_manifest_schema_and_alias_membership(self):
        from student_pilot.s1_exclusions import Exclusions
        source = Path("/scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/WITHHOLD_SCENES.json")
        if not source.exists():
            self.skipTest("The supplied dev-S1 manifest is not staged")
        value = load(source)
        rule = Exclusions(file_pin(source))
        for aliases in value["aliases"].values():
            for alias in aliases:
                self.assertTrue(rule.excluded(dict(scene=alias)), alias)
        for names in value["canonical"].values():
            for name in names:
                self.assertTrue(rule.excluded(dict(scene=name)), name)

    def test_known_dataset_spellings_cannot_bypass_scene_exclusions(self):
        from student_pilot.s1_exclusions import Exclusions
        benchmark = dict(schema="benchmark_scene_exclusions_v1",
                         scenes=["d3/held", "d2/held"], other_corpora={"3rscan": ["held"]})
        write(self.root / "spellings.json", benchmark)
        rule = Exclusions(self.pin, file_pin(self.root / "spellings.json"))
        for dataset in ("ARKitScenes", "scannet++", "ScanNetPP", "3RScan"):
            with self.subTest(dataset=dataset):
                self.assertTrue(rule.excluded(dict(dataset=dataset, scene="held")))
        for row in (dict(dataset="scannnet", scene="scene0155_00"),
                    dict(dataset="unknown", scene="d1/scene0155_00"),
                    dict(scene="unknown/held", provenance=dict(canonical="d1/scene0155_00"))):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "Unknown scene dataset"):
                rule.excluded(row)

    def coverage(self, withheld=1):
        reference = dict(schema="dev_s1_manifest_v1", withhold_file=self.pin,
                         withheld_training_rows={"unit": dict(rows_total=self.source["count"], rows_withheld=withheld,
                                                               path=self.source["database"]["path"])})
        write(self.root / "reference.json", reference)
        return dict(schema="s1-scene-coverage-v1", reference=file_pin(self.root / "reference.json"),
                    source_map={"vqa": [dict(source="unit")]})

    def test_partial_scene_filter_failure_disagrees_with_independent_census(self):
        from student_pilot.s1_exclusions import Exclusions, apply
        database = Path(self.source["database"]["path"])
        with sqlite3.connect(database) as connection:
            connection.execute("INSERT INTO rows VALUES(?,?,?)",
                               (2, json.dumps(dict(dataset="d1", scene="scene0155_00")), "{}"))
        self.source.update(database=file_pin(database), count=3, source_count=3)
        matched = Exclusions.matched

        def missed(rule, keys):
            return dict(dev=False, benchmark=False) if "d1/scene0155_00" in keys else matched(rule, keys)

        with patch.object(Exclusions, "matched", missed):
            with self.assertRaisesRegex(ValueError, "independent scene census"):
                apply(dict(vqa=self.source), self.pin, self.root, coverage=self.coverage(2))

    def test_clean_selection_has_an_independently_verified_zero(self):
        from student_pilot.s1_exclusions import apply, verify
        write(self.root / "clean_indices.json", [1])
        source = {**self.source, "count": 1, "indices": file_pin(self.root / "clean_indices.json")}
        cfg = dict(dev_scene_exclusions=self.pin, scene_coverage=self.coverage())
        streams, report = apply(dict(vqa=source), self.pin, self.root, coverage=cfg["scene_coverage"])
        self.assertEqual(report["expected"]["vqa"]["counts"]["dev_matches"], 0)
        self.assertEqual(report["sources"]["vqa"]["dev_matches"], 0)
        receipt = dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report)
        verify(receipt, cfg)

    def test_raw_reference_totals_do_not_claim_a_passed_population_comparison(self):
        from student_pilot.s1_exclusions import apply
        _, report = apply(dict(vqa=self.source), self.pin, self.root, coverage=self.coverage(2))
        coverage = report["coverage"]
        self.assertEqual(coverage["status"], "PASS")
        self.assertEqual(coverage["scope"], "admitted-population-census")
        self.assertEqual(coverage["raw_reference_status"], "NOT_COMPARED")
        self.assertEqual(report["comparisons"], {"vqa": "PASS"})
        self.assertEqual(coverage["sources"]["vqa"]["reference_comparison"], "NOT_COMPARED")
        self.assertEqual(coverage["sources"]["vqa"]["reference_dev_rows"], 2)
        self.assertEqual(coverage["sources"]["vqa"]["observed_dev_matches"], 1)

    def test_upstream_removals_cover_an_already_filtered_selection(self):
        from student_pilot.s1_exclusions import Exclusions, apply, verify
        rule = Exclusions(self.pin)
        rule.expect("vqa", self.rows)
        for row in self.rows:
            rule.keep(row, "vqa")
        write(self.root / "upstream.json", dict(source_scene_exclusions=rule.report()))
        write(self.root / "clean_indices.json", [1])
        source = {**self.source, "count": 1, "indices": file_pin(self.root / "clean_indices.json"),
                  "receipt": file_pin(self.root / "upstream.json")}
        policy = self.coverage()
        streams, report = apply(dict(vqa=source), self.pin, self.root, coverage=policy)
        self.assertEqual(report["sources"]["vqa"]["removed"], 0)
        self.assertEqual(report["coverage"]["sources"]["vqa"]["upstream"]["dev_matches"], 1)
        self.assertEqual(report["coverage"]["sources"]["vqa"]["reference_dev_rows"], 1)
        verify(dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report),
               dict(dev_scene_exclusions=self.pin, scene_coverage=policy))

    def test_benchmark_rooms_filter_every_source_and_pin_both_lists(self):
        from student_pilot.s1_exclusions import Exclusions, apply, verify
        benchmark = dict(schema="benchmark_scene_exclusions_v1", scenes=["d1/kept"],
                         physical_groups=["scannet/scene9999"], rung1_tokens=[["d1", "vfixture"]],
                         other_corpora={"3rscan": ["held-id"]})
        write(self.root / "benchmark.json", benchmark)
        pin = file_pin(self.root / "benchmark.json")
        rule = Exclusions(self.pin, pin)
        for row in (dict(dataset="d1", scene="scene9999_02"),
                    dict(dataset="3rscan", scene="held-id")):
            self.assertTrue(rule.excluded(row))
        streams, report = apply(dict(vqa=self.source), self.pin, self.root, pin)
        self.assertEqual(load(streams["vqa"]["indices"]["path"]), [])
        self.assertEqual(report["sources"]["vqa"],
                         dict(seen=2, removed=2, retained=0, dev_matches=1,
                              benchmark_matches=2, overlap_matches=1))
        receipt = dict(streams=streams, dev_scene_exclusions=self.pin,
                       benchmark_scene_exclusions=pin, scene_filter_report=report)
        verify(receipt, dict(dev_scene_exclusions=self.pin, benchmark_scene_exclusions=pin))
        with self.assertRaisesRegex(ValueError, "Scene exclusion"):
            verify(receipt, dict(dev_scene_exclusions=self.pin))

    def test_clip_sources_keep_native_indices_and_source_count(self):
        from student_pilot.c1r_clips import fingerprint
        from student_pilot.s1_exclusions import apply, verify
        scenes = [dict(row, fps=2., total_num_frames=32, pose_count=32,
                       frame_numbers=list(range(32))) for row in self.rows]
        write(self.root / "a1.json", dict(schema="recording-pose-plan-v1", scenes=scenes))
        write(self.root / "dense.json", dict(a1_plan=file_pin(self.root / "a1.json")))
        clips = self.root / "clips.jsonl"
        clips.write_text("".join(json.dumps(dict(i=i, recording_fingerprint=fingerprint(row)))+"\n"
                                 for i, row in enumerate(scenes)))
        write(self.root / "clips_order.json", [[0, 0], [0, 1]])
        part = dict(kind="c1r_clips", count=2, clips_plan=file_pin(clips),
                    dense_plan=file_pin(self.root / "dense.json"))
        source = dict(kind="mix", count=2, teacher_rows=2, sources=[part],
                      order=file_pin(self.root / "clips_order.json"))
        streams, report = apply(dict(pose=source), self.pin, self.root)
        self.assertEqual(load(streams["pose"]["order"]["path"]), [[0, 1]])
        self.assertEqual(streams["pose"]["sources"][0]["count"], 2)
        self.assertEqual(streams["pose"]["teacher_rows"], 1)
        verify(dict(streams=streams, dev_scene_exclusions=self.pin, scene_filter_report=report),
               dict(dev_scene_exclusions=self.pin))


if __name__ == "__main__":
    unittest.main()
