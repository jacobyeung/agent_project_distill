"""Tests of guard_read.py. Run: python -I -B tests/test_guard_read.py [-v]
GUARD_READ_PATH (env) selects the module under test (the mutant runner sets it)."""
import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
MODULE_PATH = Path(os.environ.get("GUARD_READ_PATH", KIT / "guard_read.py"))
spec = importlib.util.spec_from_file_location("guard_read_under_test", str(MODULE_PATH))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

FIX = HERE / "fixtures/R1_544_COMPACT.json"
LIST = KIT / "inputs/DISTANCE_LIST_DEVS1_150.jsonl"
TASKS = KIT / "inputs/TASKS.jsonl"
PARSER = KIT / "inputs/unit_from_question.py"
LIST_SHA = "028273ec3bfd1d3cd2d64f15c0fdab10fd8f905beb49fe09c3aa822a491a702e"
PARSER_SHA = "274f04a0d9590e2afbeada5d1f6003ab7d805c5e333b522ead22c23ff3396de5"
REAL_R1 = Path(os.environ.get("REAL_R1_544", KIT.parent.parent / "work/ret544/native/R1.json"))
CAND_ART = "c" * 64


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Fixture:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.base = json.loads(FIX.read_text())
        self.cand = copy.deepcopy(self.base)
        for row in self.cand["arms"]["unflagged"]:
            row["checkpoint_sha256"] = CAND_ART

    def rows(self, which="cand"):
        return {r["key"]: r for r in getattr(self, which)["arms"]["unflagged"]}

    def write(self, name, value):
        path = self.dir / name
        path.write_text(json.dumps(value))
        return path

    def run(self, list_path=LIST, list_sha=LIST_SHA, parser_sha=PARSER_SHA, draws=10000, fixed=True):
        c, b = self.write("cand.json", self.cand), self.write("base.json", self.base)
        return G.analyze(c, b, list_path, list_sha, TASKS, PARSER, parser_sha, draws, 20261115,
                         CAND_ART, G.STEP544_ARTIFACT, LIST if fixed else None, LIST_SHA if fixed else None)


def guard(result, name):
    return [g for g in result["guards"] if g["name"] == name][0]


def metre_keys():
    return ["devrows:" + json.loads(l)["question_id"] for l in LIST.read_text().splitlines()
            if l.strip() and json.loads(l)["metre"]]


class Bootstrap(unittest.TestCase):
    def test_constant_difference_interval_is_point(self):
        pairs = [("r%d" % (i % 7), 1.0, 0.5) for i in range(70)]
        c = G.paired_interval(pairs)
        self.assertAlmostEqual(c["difference"], 50.0)
        self.assertAlmostEqual(c["interval"][0], 50.0)
        self.assertAlmostEqual(c["interval"][1], 50.0)

    def test_two_rooms_known_quantiles(self):
        # Rooms A (diff -1) and B (diff +1), one item each: draws give -100 (p=.25), 0 (p=.5), +100 (p=.25).
        c = G.paired_interval([("A", 0.0, 1.0), ("B", 1.0, 0.0)])
        self.assertEqual(c["interval"], [-100.0, 100.0])
        self.assertEqual(c["difference"], 0.0)
        self.assertEqual(c["rooms"], 2)

    def test_item_weighting_and_cluster_by_room(self):
        # Room A: 3 items diff +1 each; room B: 1 item diff -1. Point = (3-1)/4 = 50.
        c = G.paired_interval([("A", 1, 0)] * 3 + [("B", 0, 1)])
        self.assertAlmostEqual(c["difference"], 50.0)
        self.assertEqual(c["interval"], [-100.0, 100.0])  # BB and AA draws, each p=.25

    def test_seed_and_draws_are_fixed(self):
        pairs = [("r%d" % (i % 9), float(i % 2), float(i % 3 == 0)) for i in range(90)]
        a, b = G.paired_interval(pairs), G.paired_interval(pairs, 10000, 20261115)
        self.assertEqual(a, b)
        self.assertEqual(G.DRAWS, 10000)
        self.assertEqual(G.SEED, 20261115)
        self.assertNotEqual(a["interval"], G.paired_interval(pairs, 10000, 1)["interval"])
        with self.assertRaises(G.Refusal):
            G.paired_interval(pairs, 9999)

    def test_independent_reimplementation(self):
        import random
        pairs = [("r%d" % (i % 11 if i < 80 else 0), float((i * 7) % 3 == 0), float((i * 5) % 4 == 0)) for i in range(121)]
        rooms = {}
        for r, a, b in pairs:
            rooms.setdefault(r, []).append(a - b)
        cl = [rooms[k] for k in sorted(rooms)]
        rng = random.Random(20261115)
        vals = sorted(100 * sum(sum(c) for c in ch) / sum(len(c) for c in ch)
                      for ch in (rng.choices(cl, k=len(cl)) for _ in range(10000)))
        lo = vals[249] + (vals[250] - vals[249]) * 0.975  # (10000-1)*.025 = 249.975
        hi = vals[9749] + (vals[9750] - vals[9749]) * 0.025
        c = G.paired_interval(pairs)
        self.assertAlmostEqual(c["interval"][0], lo, places=9)
        self.assertAlmostEqual(c["interval"][1], hi, places=9)


class Scoring(unittest.TestCase):
    def test_refusals_and_nonanswers_score_zero(self):
        base = dict(key="k", stratum="primary", scores=dict(released_answer=1.0, answer=1.0), decode={})
        self.assertEqual(G.score(base), 1.0)
        for change in (dict(geometry_refusal=True), dict(no_answer=True), dict(parse_failed=True),
                       dict(decode=dict(finish="program_refusal")), dict(decode=dict(finish="call_limit")),
                       dict(decode=dict(strict_no_answer=True)), dict(decode=dict(text="no close"))):
            row = dict(base, **change)
            self.assertEqual(G.score(row), 0.0, change)
        self.assertEqual(G.score(dict(base, decode=dict(text="a</think>b"))), 1.0)

    def test_primary_label(self):
        row = dict(key="k", stratum="primary", scores=dict(released_answer=0.3, answer=0.9), decode={})
        self.assertEqual(G.score(row), 0.3)
        self.assertEqual(G.score(dict(row, stratum="secondary")), 0.9)

    def test_refused_item_stays_in_denominator(self):
        f = Fixture()
        key = sorted(k for k, r in f.rows().items() if r["question_type"] == "camera_rotation")[0]
        f.rows()[key]["geometry_refusal"] = True
        res = f.run()
        rot = res["comparisons"]["camera_rotation"]
        self.assertEqual(rot["items"], 150)
        base_score = G.score(f.rows("base")[key])
        self.assertAlmostEqual(rot["difference"], -100.0 * base_score / 150)


class Guards(unittest.TestCase):
    def test_self_pair_zero_and_pass(self):
        f = Fixture()
        res = f.run()
        self.assertEqual(res["verdict"], "PASS")
        for c in list(res["comparisons"].values()) + list(res["printed_only"].values()):
            self.assertEqual(c["difference"], 0.0)
            self.assertEqual(c["interval"], [0.0, 0.0])

    def test_camera_call_rate_one_uncalled_fails(self):
        f = Fixture()
        key = sorted(k for k, r in f.rows().items() if r["question_type"] == "camera_displacement")[0]
        f.rows()[key]["called"] = False
        res = f.run()
        self.assertFalse(guard(res, "camera_call_rate")["pass"])
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn(key, guard(res, "camera_call_rate")["value"])

    def test_camera_interval_below_zero_fails(self):
        f = Fixture()
        for k, r in f.rows().items():
            if r["question_type"] == "camera_rotation":
                r["scores"] = dict(released_answer=0.0, answer=0.0)
        res = f.run()
        self.assertFalse(guard(res, "interval_camera_rotation")["pass"])
        self.assertTrue(guard(res, "interval_camera_displacement")["pass"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_interval_touching_zero_passes(self):
        self.assertFalse(G.wholly_below_zero(dict(interval=[-5.0, 0.0])))
        self.assertTrue(G.wholly_below_zero(dict(interval=[-5.0, -0.001])))
        self.assertFalse(G.wholly_below_zero(dict(interval=[-5.0, 3.0])))

    def test_lower_bound_below_zero_alone_passes(self):
        f = Fixture()
        rows = f.rows()
        keys = sorted(k for k, r in rows.items() if r["question_type"] == "camera_displacement")
        for k in keys[:20]:  # a few items worse: point below zero, interval straddles zero
            if G.score(f.rows("base")[k]) > 0:
                rows[k]["scores"] = dict(released_answer=0.0, answer=0.0)
                break
        res = f.run()
        c = res["comparisons"]["camera_displacement"]
        self.assertLess(c["interval"][0], 0)
        self.assertGreaterEqual(c["interval"][1], 0)
        self.assertTrue(guard(res, "interval_camera_displacement")["pass"])

    def test_metre_interval_below_zero_fails(self):
        f = Fixture()
        rows = f.rows()
        for k in metre_keys():
            rows[k]["scores"] = dict(released_answer=0.0, answer=0.0)
        res = f.run()
        self.assertFalse(guard(res, "interval_distance_metre")["pass"])

    def _metre_list(self, f, n=20):
        keep, kept = [], 0
        for line in LIST.read_text().splitlines():
            row = json.loads(line)
            if row["metre"] and kept < n:
                keep.append(line); kept += 1
            elif not row["metre"]:
                keep.append(line)
        path = f.dir / "list20.jsonl"
        path.write_text("\n".join(keep) + "\n")
        return path, sha(path), ["devrows:" + json.loads(l)["question_id"] for l in keep if json.loads(l)["metre"]]

    def test_metre_call_rate_boundary(self):
        f = Fixture()
        path, digest, keys = self._metre_list(f)
        self.assertEqual(len(keys), 20)
        f.rows()[keys[0]]["called"] = False  # 19 of 20 = 95%: passes
        res = f.run(path, digest)
        self.assertTrue(guard(res, "distance_metre_call_rate")["pass"])
        f.rows()[keys[1]]["called"] = False  # 18 of 20 = 90%: fails
        res = f.run(path, digest)
        self.assertFalse(guard(res, "distance_metre_call_rate")["pass"])
        self.assertEqual(res["verdict"], "FAIL")

    def test_room_and_non_metre_decide_nothing(self):
        f = Fixture()
        metre = set(metre_keys())
        for k, r in f.rows().items():
            if r["question_type"] == "room_size_estimation" or (r["question_type"] == "object_abs_distance" and k not in metre):
                r["scores"] = dict(released_answer=0.0, answer=0.0)
                r["called"] = False
        res = f.run()
        self.assertEqual(res["verdict"], "PASS")
        self.assertLess(res["printed_only"]["room_all"]["difference"], 0)
        self.assertLess(res["printed_only"]["distance_non_metre"]["difference"], 0)

    def test_six_guards(self):
        res = Fixture().run()
        self.assertEqual([g["name"] for g in res["guards"]],
                         ["interval_camera_displacement", "interval_camera_movement_direction",
                          "interval_camera_rotation", "camera_call_rate", "interval_distance_metre",
                          "distance_metre_call_rate"])


class Units(unittest.TestCase):
    def test_parser_counts_on_fixed_list(self):
        parser = G.load_parser(PARSER, PARSER_SHA)
        tasks = {json.loads(l)["id"]: json.loads(l) for l in TASKS.read_text().splitlines() if l.strip()}
        ids = [json.loads(l)["question_id"] for l in LIST.read_text().splitlines() if l.strip()]
        counts = {}
        for i in ids:
            u = parser.parse_unit(tasks[i]["question"], "object_abs_distance")["unit"]
            counts[u] = counts.get(u, 0) + 1
        self.assertEqual(counts, {"meters": 43, "centimeters": 28, "feet": 46, "inches": 33})
        rooms = [t for t in tasks.values() if t["question_type"] == "room_size_estimation"]
        rc = {}
        for t in rooms:
            u = parser.parse_unit(t["question"], "room_size_estimation")["unit"]
            rc[u] = rc.get(u, 0) + 1
        self.assertEqual(rc, {"square meters": 29, "square feet": 7})

    def test_report_unit_groups(self):
        res = Fixture().run()
        self.assertEqual(res["distance_list"]["metre_items"], 43)
        p = res["printed_only"]
        self.assertEqual((p["distance_centimeters"]["items"], p["distance_feet"]["items"], p["distance_inches"]["items"]), (28, 46, 33))
        self.assertEqual((p["room_square_meters"]["items"], p["room_square_feet"]["items"]), (29, 7))


class Refusals(unittest.TestCase):
    def test_missing_candidate_item_refuses(self):
        f = Fixture()
        f.cand["arms"]["unflagged"] = f.cand["arms"]["unflagged"][1:]
        with self.assertRaises(G.Refusal):
            f.run()

    def test_list_sha_mismatch_refuses(self):
        with self.assertRaises(G.Refusal):
            Fixture().run(list_sha="0" * 64)

    def test_parser_sha_mismatch_refuses(self):
        with self.assertRaises(G.Refusal):
            Fixture().run(parser_sha="0" * 64)

    def test_wrong_baseline_refuses(self):
        f = Fixture()
        for r in f.base["arms"]["unflagged"]:
            r["checkpoint_sha256"] = "d" * 64
        with self.assertRaises(G.Refusal):
            f.run()

    def test_mixed_candidate_identity_refuses(self):
        f = Fixture()
        f.cand["arms"]["unflagged"][0]["checkpoint_sha256"] = "e" * 64
        with self.assertRaises(G.Refusal):
            f.run()

    def test_list_unit_disagreeing_with_question_refuses(self):
        f = Fixture()
        lines = LIST.read_text().splitlines()
        row = json.loads(lines[0])
        row["unit"], row["metre"] = ("feet", False) if row["metre"] else ("meters", True)
        lines[0] = json.dumps(row, sort_keys=True)
        path = f.dir / "bad_list.jsonl"
        path.write_text("\n".join(lines) + "\n")
        with self.assertRaises(G.Refusal):
            f.run(path, sha(path))

    def test_room_mismatch_refuses(self):
        f = Fixture()
        f.cand["arms"]["unflagged"][5]["room"] = "d9/elsewhere"
        with self.assertRaises(G.Refusal):
            f.run()

    def test_cli_exit_codes(self):
        f = Fixture()
        c, b = f.write("c.json", f.cand), f.write("b.json", f.base)
        paths = ["--list", str(LIST), "--fixed-list", str(LIST), "--tasks", str(TASKS), "--parser", str(PARSER)]
        self.assertEqual(G.main(["--candidate", str(c), "--step544", str(b), "--out", str(f.dir / "o"),
                                 "--candidate-artifact", CAND_ART] + paths), 0)
        self.assertTrue((f.dir / "o/GUARD_READ.md").read_text().startswith("INTERNAL INSTRUMENT, NOT A CLAIMED RESULT"))
        self.assertEqual(G.main(["--candidate", str(c), "--step544", str(b), "--out", str(f.dir / "o2"),
                                 "--candidate-artifact", "f" * 64] + paths), 3)


@unittest.skipUnless(REAL_R1.is_file(), "real R1.json of job 170056 not present")
class RealReturn(unittest.TestCase):
    def test_170056_against_itself(self):
        res = G.analyze(REAL_R1, REAL_R1, LIST, LIST_SHA, TASKS, PARSER, PARSER_SHA, 10000, 20261115,
                        G.STEP544_ARTIFACT, G.STEP544_ARTIFACT, LIST, LIST_SHA)
        self.assertEqual(res["verdict"], "PASS")
        expect = dict(camera_displacement=82.333, camera_movement_direction=94.667, camera_rotation=75.667,
                      distance_metre=61.628)
        for name, value in expect.items():
            self.assertAlmostEqual(res["comparisons"][name]["step544"], value, places=3)
        self.assertAlmostEqual(res["printed_only"]["distance_all"]["step544"], 29.867, places=3)
        self.assertAlmostEqual(res["printed_only"]["room_all"]["step544"], 53.889, places=3)
        for c in list(res["comparisons"].values()) + list(res["printed_only"].values()):
            self.assertEqual(c["difference"], 0.0)
            self.assertEqual(c["interval"], [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
