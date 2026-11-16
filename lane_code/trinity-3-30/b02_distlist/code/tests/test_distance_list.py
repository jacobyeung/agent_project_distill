"""Tests for unit_from_question.py and build_lists.py (stdlib unittest; Python 3.6+).

Run: python3 -I code/tests/test_distance_list.py
Env: DL_TASKS (TASKS.jsonl), DL_R1 (R1.json or its extract), DL_OUT (frozen output dir),
     DL_SCRATCH (where the byte-stability rebuilds are written; never deleted).
"""
import hashlib
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(HERE)
LANE = os.path.dirname(CODE)
sys.path.insert(0, CODE)
import build_lists as bl  # noqa: E402
from unit_from_question import DISTANCE_TYPE, ROOM_TYPE, find_units, is_metre, parse_unit  # noqa: E402

TASKS = os.environ.get("DL_TASKS", os.path.join(LANE, "work/pull/x/TASKS.jsonl"))
R1 = os.environ.get("DL_R1", os.path.join(LANE, "work/pull/x/R1_EXTRACT_DIST_ROOM.json"))
OUT = os.environ.get("DL_OUT", os.path.join(LANE, "out/frozen"))
SCRATCH = os.environ.get("DL_SCRATCH", os.path.join(LANE, "out/test_runs/%d" % os.getpid()))

LIST_KEYS = {"question_id", "capture", "room", "unit", "unit_status", "metre"}
ARM_KEYS = {"question_id", "key", "unit", "metre", "score", "called", "call_count", "refusal",
            "no_answer", "capped", "final_answer"}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


class ParserCases(unittest.TestCase):
    def d(self, q):
        return parse_unit(q, DISTANCE_TYPE)

    def r(self, q):
        return parse_unit(q, ROOM_TYPE)

    def test_each_distance_unit(self):
        for q, u in [("How far apart, in meters?", "meters"), ("Distance in metres.", "meters"),
                     ("Gap measured in centimeters?", "centimeters"), ("in centimetres", "centimeters"),
                     ("in cm", "centimeters"), ("expressed in feet", "feet"), ("in ft", "feet"),
                     ("one foot or more", "feet"), ("in inches", "inches"), ("one inch", "inches")]:
            p = self.d(q)
            self.assertEqual((p["status"], p["unit"]), ("ok", u), q)
        self.assertTrue(is_metre(self.d("in meters"), DISTANCE_TYPE))
        self.assertFalse(is_metre(self.d("in centimeters"), DISTANCE_TYPE))

    def test_room_units(self):
        for q, u in [("What is the size of this room (in square meters)?", "square meters"),
                     ("in square metres", "square meters"), ("in m²", "square meters"),
                     ("in sq m", "square meters"), ("in square feet", "square feet"),
                     ("in sq ft", "square feet"), ("in ft^2", "square feet")]:
            p = self.r(q)
            self.assertEqual((p["status"], p["unit"]), ("ok", u), q)
        self.assertTrue(is_metre(self.r("in square meters"), ROOM_TYPE))
        self.assertFalse(is_metre(self.r("in square feet"), ROOM_TYPE))

    def test_square_not_double_counted(self):
        self.assertEqual(find_units("size (in square meters)? combined space"), ["square meters"])

    def test_preposition_in_is_not_inches(self):
        self.assertEqual(self.d("What is the distance in the kitchen?")["status"], "none")

    def test_no_unit_excluded(self):
        for q in ["How far apart are the chair and the table?", "Distance in m?"]:
            p = self.d(q)
            self.assertEqual((p["status"], p["unit"]), ("none", None), q)
            self.assertFalse(is_metre(p, DISTANCE_TYPE))

    def test_two_units_excluded(self):
        for q in ["Answer in feet or meters.", "In meters (about 300 centimeters)?"]:
            p = self.d(q)
            self.assertEqual((p["status"], p["unit"]), ("multiple", None), q)
            self.assertFalse(is_metre(p, DISTANCE_TYPE))
        self.assertEqual(self.d("in meters, i.e. meters")["status"], "ok")  # same unit twice

    def test_unsupported_excluded(self):
        self.assertEqual(self.d("in millimeters")["status"], "unsupported")
        self.assertEqual(self.d("in yards")["status"], "unsupported")
        self.assertEqual(self.r("room size in meters")["status"], "unsupported")
        self.assertEqual(self.d("in square meters")["status"], "unsupported")

    def test_bad_type(self):
        with self.assertRaises(ValueError):
            parse_unit("in meters", "object_counting")


@unittest.skipUnless(os.path.exists(TASKS), "TASKS.jsonl not present")
class ParserCountsOnFixedList(unittest.TestCase):
    def test_reviewed_counts(self):
        self.assertEqual(sha(TASKS), bl.TASKS_SHA)
        dist, room = {}, {}
        for line in open(TASKS, encoding="utf-8"):
            t = json.loads(line)
            if t["question_type"] == DISTANCE_TYPE:
                p = parse_unit(t["question"], DISTANCE_TYPE)
                dist[p["unit"] or p["status"]] = dist.get(p["unit"] or p["status"], 0) + 1
            elif t["question_type"] == ROOM_TYPE:
                p = parse_unit(t["question"], ROOM_TYPE)
                room[p["unit"] or p["status"]] = room.get(p["unit"] or p["status"], 0) + 1
        self.assertEqual(dist, {"meters": 43, "centimeters": 28, "feet": 46, "inches": 33})
        self.assertEqual(room, {"square meters": 29, "square feet": 7})


@unittest.skipUnless(os.path.isdir(OUT), "frozen output dir not present")
class FrozenFiles(unittest.TestCase):
    def load(self, name):
        raw = open(os.path.join(OUT, name), "rb").read()
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))
        raw.decode("ascii")
        return [json.loads(l) for l in raw.decode("ascii").split("\n") if l]

    def test_list_schema(self):
        rows = self.load(bl.LIST_NAME)
        self.assertEqual(len(rows), 150)
        ids = [r["question_id"] for r in rows]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(set(ids)), 150)
        for r in rows:
            self.assertEqual(set(r), LIST_KEYS)
            self.assertIsInstance(r["metre"], bool)
            self.assertIn(r["unit_status"], ("ok", "none", "multiple", "unsupported"))
            self.assertEqual(r["metre"], r["unit"] == "meters" and r["unit_status"] == "ok")
            if r["unit_status"] != "ok":
                self.assertIsNone(r["unit"])
            self.assertTrue(r["room"].split("/")[0] == r["capture"].split("/")[0])
        self.assertEqual(sum(r["metre"] for r in rows), 43)

    def test_list_sha_file(self):
        line = open(os.path.join(OUT, "LIST_150.sha256"), "rb").read().decode("ascii")
        digest, name = line.rstrip("\n").split("  ")
        self.assertEqual(name, bl.LIST_NAME)
        self.assertEqual(digest, sha(os.path.join(OUT, bl.LIST_NAME)))

    def test_arm_schema_and_means(self):
        rows = self.load(bl.ARM_NAME)
        lst = self.load(bl.LIST_NAME)
        self.assertEqual([r["question_id"] for r in rows], [r["question_id"] for r in lst])
        for a, l in zip(rows, lst):
            self.assertEqual(set(a), ARM_KEYS)
            self.assertEqual((a["unit"], a["metre"]), (l["unit"], l["metre"]))
            self.assertEqual(a["key"], "devrows:" + a["question_id"])
            self.assertTrue(0.0 <= a["score"] <= 1.0)
            self.assertAlmostEqual(a["score"] * 10, round(a["score"] * 10), places=9)
            if a["refusal"] is not None or a["no_answer"]:
                self.assertEqual(a["score"], 0.0)
        metre = [a["score"] for a in rows if a["metre"]]
        self.assertEqual(len(metre), 43)
        self.assertEqual(round(100 * sum(metre) / len(metre), 3), 61.628)
        self.assertEqual(round(100 * sum(a["score"] for a in rows) / len(rows), 3), 29.867)

    def test_arm_sha_file(self):
        line = open(os.path.join(OUT, "STEP544_ARM_150.sha256"), "rb").read().decode("ascii")
        digest, name = line.rstrip("\n").split("  ")
        self.assertEqual(digest, sha(os.path.join(OUT, bl.ARM_NAME)))


@unittest.skipUnless(os.path.exists(TASKS) and os.path.exists(R1), "inputs not present")
class ByteStable(unittest.TestCase):
    def test_two_builds_same_bytes(self):
        a, b = os.path.join(SCRATCH, "a"), os.path.join(SCRATCH, "b")
        ra, rb = bl.build(TASKS, R1, a), bl.build(TASKS, R1, b)
        self.assertEqual(ra["status"], "PASS", ra["failures"])
        for name in (bl.LIST_NAME, bl.ARM_NAME, "LIST_150.sha256", "STEP544_ARM_150.sha256", "BUILD_CHECKS.json"):
            self.assertEqual(sha(os.path.join(a, name)), sha(os.path.join(b, name)), name)
        if os.path.isdir(OUT):
            for name in (bl.LIST_NAME, bl.ARM_NAME):
                self.assertEqual(sha(os.path.join(a, name)), sha(os.path.join(OUT, name)), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
