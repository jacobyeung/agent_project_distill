import copy
import gzip
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from student_pilot.p3_provenance import file_pin, load, pinned, write


class PoolAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        write(self.root / "dev.json", dict(schema="dev_s1_withhold_v1",
              canonical={"d1/scene0155_00": ["scannet/scene0155_00"]},
              natives=["d1/scene0155_00"], rooms=["d1/scene0155"],
              physical_groups=["scannet/scene0155"], aliases={"d1/scene0155_00": ["d1/vdev"]}))
        write(self.root / "benchmark.json", dict(schema="benchmark_scene_exclusions_v1",
              scenes=["d1/scene0000_00"], physical_groups=["scannet/scene0000"],
              rung1_tokens=[["d1", "vbench"]], other_corpora={}))
        lists = {}
        for name, text in (("dev_s1", "ROUTE_direct\tdev\n"), ("eval_rooms", "ROUTE_direct\tbench\n"),
                           ("room_release_gate", "T0_room\trelease\n")):
            path = self.root / (name+".tsv")
            path.write_text(text)
            pin = file_pin(path)
            lists[name] = dict(list=pin["path"], list_sha256=pin["sha256"], rows=1)
        for name, key, filename in (("dev_s1", "withhold", "dev.json"),
                                   ("eval_rooms", "v2", "benchmark.json")):
            pin = file_pin(self.root / filename)
            lists[name].update({key: pin["path"], key+"_sha256": pin["sha256"]})
        sets = [dict(name=name, status="final", files={}) for name in
                ("T0_room", "SCENE_room", "SCENE_room_sppK", "ROUTE_direct")]
        self.manifest = dict(schema="dose-pool-s1-manifest-v2", sets=sets, exclusions=lists)
        write(self.root / "manifest.json", self.manifest)
        self.pin = file_pin(self.root / "manifest.json")

    def test_release_qid_is_scoped_to_its_source(self):
        from student_pilot.s1_pool import Pool
        pool = Pool(self.pin)
        row = dict(qid="release", dataset="d1", scene="kept")
        self.assertIn("room_release_gate", pool.reasons("T0_room", row))
        self.assertEqual(pool.reasons("ROUTE_direct", row), set())

    def test_scene_rules_apply_even_without_a_listed_qid(self):
        from student_pilot.s1_pool import Pool
        pool = Pool(self.pin)
        self.assertIn("dev_s1", pool.reasons("ROUTE_direct", dict(qid="new", dataset="d1", scene="vdev")))
        self.assertIn("eval_rooms", pool.reasons("T0_room", dict(qid="new", canonical="scannet/scene0000_02")))
        self.assertIn("dev_s1", pool.reasons("ROUTE_direct", dict(qid="dev", dataset="d1", scene="kept")))

    def test_final_sppk_status_does_not_grant_authorization(self):
        from student_pilot.s1_pool import Pool
        pool = Pool(self.pin)
        self.assertIsNone(pool.deferred("T0_room"))
        self.assertIsNone(pool.deferred("SCENE_room"))
        self.assertEqual(pool.deferred("SCENE_room_sppK"), "room_set_not_authorized")

    def test_mutated_list_and_wrong_declared_count_refuse(self):
        from student_pilot.s1_pool import Pool
        (self.root / "room_release_gate.tsv").write_text("T0_room\tdifferent\n")
        with self.assertRaises(ValueError):
            Pool(self.pin)
        value = copy.deepcopy(self.manifest)
        value["exclusions"]["room_release_gate"]["list_sha256"] = file_pin(
            self.root / "room_release_gate.tsv")["sha256"]
        value["exclusions"]["room_release_gate"]["rows"] = 2
        write(self.root / "bad_count.json", value)
        with self.assertRaisesRegex(ValueError, "membership count"):
            Pool(file_pin(self.root / "bad_count.json"))

    def test_negative_zero_repacking_preserves_labels_flags_and_source(self):
        from student_pilot.s1_pool import normalize_room
        from student_pilot.ground_rows import validate
        from generator.derivgen_v7.derivgen.ground_v313_tokens import tokenizer_for_rows
        path = Path("/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/MANIFEST.json")
        if not path.exists():
            self.skipTest("The actual room source is not staged")
        source = None
        for entry in load(path)["sets"]:
            if entry["name"] not in ("T0_room", "T1H1_room", "SCENE_room"):
                continue
            pin = {key: entry["files"]["packed"][key] for key in ("path", "sha256")}
            with gzip.open(pinned(pin), "rt") as stream:
                source = next((json.loads(line) for line in stream if "floor height -0.00 m" in line), None)
            if source is not None:
                break
        self.assertIsNotNone(source)
        before = copy.deepcopy(source)
        tokenizer = tokenizer_for_rows("/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json")
        normalized, changed = normalize_room(source, tokenizer)
        self.assertTrue(changed)
        self.assertEqual(source, before)
        self.assertNotIn("floor height -0.00 m", normalized["target"])
        self.assertIn("floor height 0.00 m", normalized["target"])
        for key in ("answer", "gt_answer", "training_admitted", "provenance", "qid", "candidate_id"):
            self.assertEqual(normalized[key], source[key])
        validate(normalized)
        self.assertEqual(normalize_room(normalized, tokenizer), (normalized, False))

    def test_source_gate_defers_individually_and_rejects_selected_leak(self):
        from student_pilot.s1_pool import prepare, selected_rows
        manifest = copy.deepcopy(self.manifest)
        for entry in manifest["sets"]:
            names = (("dev", "vdev"), ("bench", "vbench"), ("kept", "kept")) if entry["name"] == "ROUTE_direct" else (
                (("release", "kept"),) if entry["name"] == "T0_room" else ())
            rows = [dict(qid=qid, dataset="d1", scene=scene, question_type="route_planning",
                         head_program=None, score_nomination_allowed=False, answer="A",
                         target="<think>\nA.\n</think>\n\nA") for qid, scene in names]
            path = self.root / (entry["name"]+".jsonl.gz")
            with gzip.open(path, "xt") as stream:
                for row in rows:
                    stream.write(json.dumps(row)+"\n")
            entry["files"] = dict(rows={**file_pin(path), "rows": len(rows), "bytes": path.stat().st_size})
        path = self.root / "broken.jsonl.gz"
        with gzip.open(path, "xt") as stream:
            stream.write("not-json\n")
        manifest["sets"].append(dict(name="BROKEN", status="final",
                                    files=dict(rows={**file_pin(path), "rows": 1})))
        write(self.root / "inputs.json", manifest)
        output = self.root / "prepared"
        report = prepare(file_pin(self.root / "inputs.json"), output)
        self.assertFalse(report["training_admission"])
        self.assertFalse(report["rgb_verified"])
        self.assertEqual(report["selected_rows"], 1)
        self.assertEqual(report["sources"]["BROKEN"]["status"], "DEFERRED")
        self.assertEqual(report["sources"]["SCENE_room_sppK"]["reason"], "room_set_not_authorized")
        self.assertEqual([row["qid"] for row in selected_rows(file_pin(output / "receipt.json"), "ROUTE_direct")],
                         ["kept"])
        changed = copy.deepcopy(report)
        write(self.root / "leaked_indices.json", [0, 2])
        changed["sources"]["ROUTE_direct"].update(selection=file_pin(self.root / "leaked_indices.json"), retained=2)
        write(self.root / "leaked_receipt.json", changed)
        with self.assertRaisesRegex(ValueError, "Excluded pool row"):
            list(selected_rows(file_pin(self.root / "leaked_receipt.json"), "ROUTE_direct"))

    def test_unknown_prefix_and_census_mismatch_block_the_whole_selection(self):
        from student_pilot.s1_exclusions import Exclusions
        from student_pilot.s1_pool import prepare, selected_rows
        for unknown in (True, False):
            with self.subTest(unknown=unknown):
                root = self.root / ("unknown" if unknown else "mismatch")
                root.mkdir()
                manifest = copy.deepcopy(self.manifest)
                for entry in manifest["sets"]:
                    names = {"ROUTE_direct": [("dev", "vdev"), ("bench", "vbench"), ("kept", "kept")],
                             "T0_room": [("release", "kept")], "SCENE_room": [("safe", "kept")]}.get(entry["name"], [])
                    path = root / (entry["name"]+".jsonl.gz")
                    with gzip.open(path, "xt") as stream:
                        for qid, scene in names:
                            row = dict(qid=qid, dataset="unknown" if unknown and qid == "kept" else "d1",
                                       scene=scene, question_type="route_planning", head_program=None,
                                       score_nomination_allowed=False, answer="A", target="<think>\nA.\n</think>\n\nA")
                            stream.write(json.dumps(row)+"\n")
                    entry["files"] = dict(rows={**file_pin(path), "rows": len(names)})
                write(root / "inputs.json", manifest)
                matched = Exclusions.matched

                def damaged(rule, keys):
                    value = matched(rule, keys)
                    if not unknown:
                        value["dev"] = False
                    return value

                with patch.object(Exclusions, "matched", damaged):
                    report = prepare(file_pin(root / "inputs.json"), root / "prepared")
                self.assertIn("ROUTE_direct", report["blockers"])
                self.assertEqual(report["sources"]["SCENE_room"]["status"], "ELIGIBLE")
                with self.assertRaisesRegex(ValueError, "Pool scene integrity"):
                    list(selected_rows(file_pin(root / "prepared/receipt.json"), "SCENE_room"))


if __name__ == "__main__":
    unittest.main()
