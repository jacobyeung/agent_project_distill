import copy
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from student_pilot import carrier_c1_routing as routing
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.rehearsal import ENVIRONMENT
from student_pilot.s1_routing import DIRECT_RULE, Frames, build, direct_transform, frame_request


class RoutingMaterializationTests(unittest.TestCase):
    def row(self, think="The turns, in order, are Turn Left, Turn Right."):
        return dict(qid="fixture", question_type="route_planning", head_program=None, answer="B",
                    target=routing.THINK+think+"\n</think>\n\nB",
                    student_input=dict(options=["A. Turn Back", "B. Turn Left, Turn Right"]),
                    training_admitted=False, infrastructure_only=False, score_nomination_allowed=False)

    def test_only_the_authorized_think_field_changes(self):
        row = self.row()
        original = copy.deepcopy(row)
        result, changed = direct_transform(row)
        self.assertTrue(changed)
        self.assertEqual(row, original)
        self.assertEqual(result["target"], routing.THINK+"\n</think>\n\nB")
        self.assertEqual(result["provenance"]["direct_transform"], DIRECT_RULE)
        self.assertEqual(result["provenance"]["original_think"],
                         "The turns, in order, are Turn Left, Turn Right.")
        self.assertEqual({k: v for k, v in result.items() if k not in ("target", "provenance")},
                         {k: v for k, v in original.items() if k != "target"})

    def test_reasoning_and_wrong_option_restating_are_deferred(self):
        for think in ("The turns, in order, are Turn Left, Turn Right. I compare the two object positions.",
                      "First move to the desk, then turn left.", "The turn is Turn Back."):
            with self.subTest(think=think), self.assertRaises(ValueError):
                direct_transform(self.row(think))

    def test_the_transformation_is_idempotent(self):
        first, _ = direct_transform(self.row())
        second, changed = direct_transform(first)
        self.assertFalse(changed)
        self.assertEqual(first, second)


class NativeMaterializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lane = Path("/scratch/jjyeung/orch_cd/leg_s1_tree")
        samples = load(cls.lane / "inputs/pool_s1_samples.json")["samples"]
        cls.packed = next(sample["row"] for sample in samples
                          if sample["kind"] == "packed" and sample["row"]["question_type"] == "object_abs_distance")
        cls.direct = next(sample["row"] for sample in samples if sample["kind"] == "rows")
        proof = load(cls.lane / "out/R16_COMPATIBILITY.json")
        path = Path(proof["database"]["path"])
        connection = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
        try:
            for index in proof["types"]["camera_displacement"]["sample_indices"]:
                row = json.loads(connection.execute("SELECT row FROM rows WHERE i=?", (index,)).fetchone()[0])
                if row["dataset"] == frame_request(cls.packed)["d"]:
                    cls.legacy = row
                    break
            else:
                raise AssertionError("Native fixture lacks the matching dataset's frame rate")
        finally:
            connection.close()
        cls.base_model = file_pin(cls.lane / "work/fixture/assets/model_v3.json")
        cls.previous_mode = os.environ.get(ENVIRONMENT)
        os.environ[ENVIRONMENT] = "1"

    @classmethod
    def tearDownClass(cls):
        if cls.previous_mode is None:
            os.environ.pop(ENVIRONMENT, None)
        else:
            os.environ[ENVIRONMENT] = cls.previous_mode

    def setUp(self):
        from student_pilot.s1_pool import prepare
        self.root = Path(tempfile.mkdtemp(prefix="s1_routing_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.packed_row, self.direct_row = copy.deepcopy(self.packed), copy.deepcopy(self.direct)
        write(self.root / "dev.json", dict(schema="dev_s1_withhold_v1",
              canonical={"d1/scene9998_00": ["scannet/scene9998_00"]},
              natives=["d1/scene9998_00"], rooms=["d1/scene9998"],
              physical_groups=["scannet/scene9998"], aliases={"d1/scene9998_00": ["d1/vhelddev"]}))
        write(self.root / "benchmark.json", dict(schema="benchmark_scene_exclusions_v1",
              scenes=["d1/scene9999_00"], physical_groups=["scannet/scene9999"],
              rung1_tokens=[["d1", "vheldbenchmark"]], other_corpora={}))
        exclusions = {}
        for name in ("dev_s1", "eval_rooms", "room_release_gate"):
            path = self.root / (name+".tsv")
            path.write_text("")
            pin = file_pin(path)
            exclusions[name] = dict(list=pin["path"], list_sha256=pin["sha256"], rows=0)
        for name, key, filename in (("dev_s1", "withhold", "dev.json"), ("eval_rooms", "v2", "benchmark.json")):
            pin = file_pin(self.root / filename)
            exclusions[name].update({key: pin["path"], key+"_sha256": pin["sha256"]})
        (self.root / "remove.jsonl").write_text(json.dumps(dict(row_key="fixture_removed"))+"\n")
        sets = []
        for name, kind, row in (("POOL_native", "packed", self.packed_row),
                                ("ROUTE_direct", "rows", self.direct_row)):
            path = self.root / (name+".jsonl.gz")
            self.gzip(path, [row])
            sets.append(dict(name=name, status="final", rows_per_type={row["question_type"]: 1},
                             files={kind: {**file_pin(path), "rows": 1, "bytes": path.stat().st_size}}))
        write(self.root / "manifest.json", dict(schema="dose-pool-s1-manifest-v2",
                                              sets=sets, exclusions=exclusions))
        prepare(file_pin(self.root / "manifest.json"), self.root / "selected",
                [file_pin(self.root / "remove.jsonl")])
        selection = file_pin(self.root / "selected/receipt.json")
        catalog, staged = {}, self.root / "staged"
        staged.mkdir()
        for entry in sets:
            pin = next(iter(entry["files"].values()))
            destination = staged / (pin["sha256"]+".gz")
            shutil.copyfile(pin["path"], destination)
            catalog[pin["sha256"]] = str(destination)
            Path(pin["path"]).write_bytes(b"unusable-original-locator")
        map_rows, videos, scenes = {}, {}, set()
        for row in (self.packed_row, self.direct_row):
            pending = frame_request(row)
            scenes.add(pending["d"]+"/"+pending["s"])
            if pending["d"] != "d3":
                videos[pending["s"]] = dict(g=pending["d"], raw_n=max(pending["i"])+1)
            for index in pending["i"]:
                map_rows[pending["d"], pending["s"], index] = dict(
                    d=pending["d"], s=pending["s"], i=index, sha256="a"*64,
                    path="/data2/k6tk/aa/"+("a"*64)+".png")
        self.gzip(self.root / "map.jsonl.gz", map_rows.values())
        with gzip.open(self.root / "plan.json.gz", "xt") as stream:
            json.dump(dict(v=videos), stream)
        legacy = copy.deepcopy(self.legacy)
        duplicate = {**copy.deepcopy(legacy), "qid": self.packed_row["qid"]}
        removed = {**copy.deepcopy(legacy), "qid": "fixture_removed"}
        covered = {**copy.deepcopy(legacy), "qid": "fixture_covered"}
        covered["routing"]["question_type"] = self.packed_row["question_type"]
        native_rows = [legacy, duplicate, removed, covered]
        scenes.add(legacy["dataset"]+"/"+legacy["scene"])
        write(self.root / "division.json", dict(schema="diagnostic-whole-scene-division-v1",
              training_only=True, train_scenes=sorted(scenes), heldout_scenes=[]))
        self.division = file_pin(self.root / "division.json")
        database = self.root / "legacy.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)")
            connection.executemany("INSERT INTO rows VALUES (?,?,?)",
                                  [(index, json.dumps(row), "{}") for index, row in enumerate(native_rows)])
        write(self.root / "legacy.json", dict(schema=routing.ROUTING_SCHEMA, stream="routing",
              database=file_pin(database), count=len(native_rows), division=self.division,
              types=dict(Counter(row["routing"]["question_type"]+":route" for row in native_rows))))
        self.cfg = dict(streams=dict(routing=file_pin(self.root / "legacy.json")),
                        training_mode="final", trace_program_version="3.14",
                        s1_routing=dict(schema="s1-routing-inputs-v1", selection=selection, catalog=catalog,
                                        frame_map=file_pin(self.root / "map.jsonl.gz"),
                                        frame_plan=file_pin(self.root / "plan.json.gz")),
                        dev_scene_exclusions=file_pin(self.root / "dev.json"),
                        benchmark_scene_exclusions=file_pin(self.root / "benchmark.json"),
                        remove_files=[file_pin(self.root / "remove.jsonl")], recipe={},
                        route_table={self.packed_row["question_type"]: "route",
                                     legacy["routing"]["question_type"]: "route", "route_planning": "direct"})

    def gzip(self, path, rows):
        with gzip.open(path, "xt") as stream:
            for row in rows:
                stream.write(json.dumps(row)+"\n")

    def test_native_materializer_relocates_preserves_pool_precedence_and_filters(self):
        output = self.root / "routing"
        receipt = build(self.cfg, output, self.division, self.base_model)
        self.assertEqual(receipt["count"], 3)
        report = load(receipt["materialization"]["path"])
        self.assertEqual(report["status"], "PASS")
        camera = report["types"][self.legacy["routing"]["question_type"]]
        self.assertEqual(camera["r16_kept"], 1)
        self.assertEqual(camera["r16_dropped"], dict(label_removal=1, pool_qid_wins=1))
        self.assertEqual(report["types"][self.packed_row["question_type"]]["r16_dropped"],
                         dict(pool_type_wins=1))
        self.assertEqual(report["direct_rule_audit"]["ROUTE_direct"]["passed"], 1)
        self.assertEqual(report["fps_rule"], "S1-FPS1")
        dataset = frame_request(self.packed_row)["d"]
        self.assertEqual(report["frame_rate_sources"][dataset]["dataset_uniform"], 1)
        self.assertEqual(receipt["frame_rate_sources"], report["frame_rate_sources"])
        with sqlite3.connect(receipt["database"]["path"]) as connection:
            rows = [json.loads(value) for (value,) in connection.execute("SELECT row FROM rows ORDER BY i")]
            self.assertEqual([row["qid"] for row in rows],
                             [self.packed_row["qid"], self.direct_row["qid"], self.legacy["qid"]])
            plan = connection.execute("EXPLAIN QUERY PLAN SELECT row FROM rows WHERE i=1").fetchall()
            self.assertTrue(any("INTEGER PRIMARY KEY" in value[-1] for value in plan))
            plan = connection.execute("EXPLAIN QUERY PLAN SELECT k,qid,question_type,origin,row FROM candidates "
                                      "ORDER BY origin='legacy',k").fetchall()
            self.assertFalse(any("TEMP B-TREE" in value[-1] for value in plan))
        self.assertEqual(rows[0]["routing"]["training_admitted"], self.packed_row["training_admitted"])
        self.assertEqual(rows[1]["routing"]["answer"], self.direct_row["answer"])
        self.assertEqual(rows[1]["s1_source"]["provenance"]["direct_transform"], DIRECT_RULE)

    def test_frame_authority_missing_and_conflicting_rates_refuse(self):
        frames = Frames(self.cfg["s1_routing"]["frame_map"], self.cfg["s1_routing"]["frame_plan"])
        with self.assertRaisesRegex(ValueError, "frame rate"):
            frames.resolve(self.packed_row)
        key = frame_request(self.direct_row)
        frames.fps[key["d"]+"/"+key["s"]] = self.direct_row["student_input"]["fps"]+1
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            frames.resolve(self.direct_row)

    def test_real_processor_preserves_the_ground_answer_boundary(self):
        from student_pilot.batches import training_stop_token, training_text
        from student_pilot.carrier_c1_run import processor_for_receipt
        root = self.lane.parent / "orchard_cp2/work/rt/proc"
        if not (root / "tokenizer.json").is_file():
            self.skipTest("The real processor metadata is not local")
        processor = processor_for_receipt(dict(root=str(root)), self.cfg)
        target = self.packed_row["target"]
        question, options = self.packed_row["question"], self.packed_row["options"]
        prompt, suffix = training_text(processor, question, options, target)
        self.assertFalse(processor._s1_rehearsal)
        self.assertTrue((prompt+suffix).endswith(target+processor.tokenizer.eos_token+
                                                training_stop_token(processor)[0]))
        row = dict(student_input=dict(question=question, options=options))
        ids, mask, offsets = routing.suffix_tokens(processor, row, target, self.packed_row["tool_output_spans"])
        self.assertEqual(len(ids), len(mask))
        self.assertEqual(len(ids), len(offsets))
        self.assertFalse(all(mask))
        with self.assertRaisesRegex(ValueError, "assistant boundary"):
            training_text(processor, question, options, target+"  ")

    def test_dataset_uniform_authority_covers_missing_arkit_scenes(self):
        authority = self.root / "fps.json"
        write(authority, dict(schema="s1-fps-authority-v1", by_scene={"d3/authority_scene": 10.0}))
        frames = Frames(self.cfg["s1_routing"]["frame_map"], self.cfg["s1_routing"]["frame_plan"],
                        fps_authority=file_pin(authority))
        row = copy.deepcopy(self.packed_row)
        request = frame_request(row)
        row["frames_pending"] = dict(request, d="d3", s="fixture_arkit")
        frames.frames.update({("d3", "fixture_arkit", index): frames.frames[request["d"], request["s"], index]
                              for index in request["i"]})
        inputs, binding = frames.resolve(row)
        self.assertEqual(inputs["fps"], 10.0)
        self.assertEqual(inputs["timestamps"], [index/10 for index in request["i"]])
        self.assertEqual(binding["fps_source"], "dataset_uniform")
        self.assertEqual(binding["fps_rule"], "S1-FPS1")
        self.assertTrue(binding["total_num_frames_lower_bound"])

    def test_dataset_uniform_refuses_cross_authority_rate_disagreement(self):
        authority = self.root / "fps_conflict.json"
        write(authority, dict(schema="s1-fps-authority-v1",
                              by_scene={"d3/authority_scene": 10.0, "d3/other_scene": 30.0}))
        for native_rates in ({}, {"d3": {24.0}}):
            frames = Frames(self.cfg["s1_routing"]["frame_map"], self.cfg["s1_routing"]["frame_plan"],
                            fps_authority=file_pin(authority), fps_by_dataset=native_rates)
            row = copy.deepcopy(self.packed_row)
            request = frame_request(row)
            row["frames_pending"] = dict(request, d="d3", s="fixture_arkit")
            frames.frames.update({("d3", "fixture_arkit", index): frames.frames[request["d"], request["s"], index]
                                  for index in request["i"]})
            with self.subTest(native_rates=native_rates), self.assertRaisesRegex(ValueError, "frame rate"):
                frames.resolve(row)

    def test_frame_bindings_cannot_silently_replace_conflicting_source_metadata(self):
        source = self.cfg["s1_routing"]
        key = frame_request(self.direct_row)
        for field, value in (("frame_indices", list(reversed(key["i"]))),
                             ("timestamps", [0.0]*len(key["i"])),
                             ("frames", [dict(sha256="0"*64)]*len(key["i"]))):
            with self.subTest(field=field):
                frames = Frames(source["frame_map"], source["frame_plan"])
                row = copy.deepcopy(self.direct_row)
                row["student_input"][field] = value
                with self.assertRaisesRegex(ValueError, "Source.*conflict"):
                    frames.resolve(row)
        frames = Frames(source["frame_map"], source["frame_plan"])
        frames.authority = dict(by_scene={key["d"]+"/"+key["s"]: self.direct_row["student_input"]["fps"]+1})
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            frames.resolve(self.direct_row)

    def test_only_arkit_has_an_explicit_lower_bound_total(self):
        frames = Frames(self.cfg["s1_routing"]["frame_map"], self.cfg["s1_routing"]["frame_plan"],
                        fps_by_dataset={frame_request(self.packed_row)["d"]: {self.legacy["student_input"]["fps"]}})
        inputs, binding = frames.resolve(self.packed_row)
        self.assertFalse(binding["total_num_frames_lower_bound"])
        scene = frame_request(self.packed_row)["s"]
        frames.plan["v"].pop(scene)
        with self.assertRaisesRegex(ValueError, "full frame count"):
            frames.resolve(self.packed_row)
        row = copy.deepcopy(self.packed_row)
        request = frame_request(row)
        row["frames_pending"] = dict(request, d="d3", s="fixture_arkit")
        frames.frames.update({("d3", "fixture_arkit", index): frames.frames[request["d"], request["s"], index]
                              for index in request["i"]})
        frames.dataset_fps["d3"] = {10.0}
        inputs, binding = frames.resolve(row)
        self.assertTrue(binding["total_num_frames_lower_bound"])
        self.assertEqual(inputs["total_num_frames"], max(request["i"])+1)

    def test_changed_catalog_bytes_fail_closed(self):
        cfg = copy.deepcopy(self.cfg)
        selection = load(cfg["s1_routing"]["selection"]["path"])
        source = selection["sources"]["POOL_native"]["source"]
        cfg["s1_routing"]["catalog"][source["sha256"]] = str(self.root / "remove.jsonl")
        with self.assertRaisesRegex(ValueError, "changed pinned"):
            build(cfg, self.root / "wrong_catalog", self.division, self.base_model)

    def test_routing_policy_cannot_silently_admit_pool_programs(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["route_table"][self.packed_row["question_type"]] = "direct"
        output = self.root / "wrong_policy"
        with self.assertRaisesRegex(ValueError, "no_admitted_pool_program_rows"):
            build(cfg, output, self.division, self.base_model)
        report = load(output / "materialization.json")
        kind = report["types"][self.packed_row["question_type"]]
        self.assertEqual(kind["pool_deferred"]["route_policy_mismatch"], 1)
        self.assertEqual(kind["r16_dropped"]["pool_type_wins"], 1)

    def test_more_than_one_percent_bad_direct_rows_block_the_entire_receipt(self):
        from student_pilot.s1_pool import prepare
        manifest = load(self.root / "manifest.json")
        changed = copy.deepcopy(self.direct_row)
        changed["target"] = routing.THINK+"First identify the object, then compare its bearing.\n</think>\n\n"+changed["answer"]
        path = self.root / "reasoning.jsonl.gz"
        self.gzip(path, [changed])
        for entry in manifest["sets"]:
            kind = next(iter(entry["files"]))
            old = entry["files"][kind]
            if kind == "rows":
                entry["files"][kind] = {**file_pin(path), "rows": 1, "bytes": path.stat().st_size}
            else:
                old["path"] = self.cfg["s1_routing"]["catalog"][old["sha256"]]
        write(self.root / "reasoning_manifest.json", manifest)
        prepare(file_pin(self.root / "reasoning_manifest.json"), self.root / "reasoning_selection",
                self.cfg["remove_files"])
        cfg = copy.deepcopy(self.cfg)
        cfg["s1_routing"]["selection"] = file_pin(self.root / "reasoning_selection/receipt.json")
        output = self.root / "bad_direct"
        with self.assertRaisesRegex(ValueError, "direct_schema_failure_exceeds_one_percent"):
            build(cfg, output, self.division, self.base_model)
        report = load(output / "materialization.json")
        self.assertEqual(report["direct_rule_audit"]["ROUTE_direct"]["deferred"], 1)
        self.assertEqual(report["source_denominator"], 6)
        self.assertFalse(report["production_authorized"])

    def test_one_legacy_execution_disagreement_defers_the_whole_type(self):
        original = load(self.cfg["streams"]["routing"]["path"])
        source = sqlite3.connect(Path(original["database"]["path"]).as_uri()+"?mode=ro", uri=True)
        try:
            rows = [(index, json.loads(value)) for index, value in source.execute("SELECT i,row FROM rows ORDER BY i")]
        finally:
            source.close()
        rows[0][1]["target"] += "\ninvalid-native-output"
        path = self.root / "bad_legacy.sqlite"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)")
            connection.executemany("INSERT INTO rows VALUES (?,?,?)",
                                   [(index, json.dumps(row), "{}") for index, row in rows])
        write(self.root / "bad_legacy.json", {**original, "database": file_pin(path)})
        cfg = copy.deepcopy(self.cfg)
        cfg["streams"]["routing"] = file_pin(self.root / "bad_legacy.json")
        receipt = build(cfg, self.root / "bad_execution", self.division, self.base_model)
        report = load(receipt["materialization"]["path"])
        kind = self.legacy["routing"]["question_type"]
        self.assertEqual(report["legacy_compatibility"][kind]["tested"], 3)
        self.assertEqual(report["legacy_compatibility"][kind]["exact_execution_agreement"], 2)
        self.assertEqual(report["types"][kind]["r16_deferred"], dict(v314_execution_disagreement=3))
        self.assertEqual(receipt["count"], 2)


if __name__ == "__main__":
    unittest.main()
