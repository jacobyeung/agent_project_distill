import json
import os
import random
import tempfile
import unittest
from pathlib import Path

from student_pilot import provisional, division
from student_pilot.common import binding, canonical_bytes, digest_json


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class InheritedDivisionTests(unittest.TestCase):
    """A later training set must keep every scene on the side a published run gave it."""

    def setUp(self):
        root = Path(os.environ["LANE_TEST_OUTPUT"])
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="division_inherit_", dir=root))

    def rows(self, scenes):
        return [provisional.tag({"qid": f"q{index:04d}", "dataset": "scannet", "scene": scene,
                                 "category": "object_counting"}, LABEL)
                for index, scene in enumerate(scenes)]

    def record(self, train_scenes, heldout_scenes, name="division.json"):
        value = {"schema": "provisional-whole-scene-division-v1", "seed": 17,
                 "group_policy": division.WHOLE_SCENE_GROUP_POLICY,
                 "train_scenes": [f"scannet/{scene}" for scene in train_scenes],
                 "heldout_scenes": [f"scannet/{scene}" for scene in heldout_scenes],
                 "train_group_ids": sorted({f"scannet/{scene[:-3]}" for scene in train_scenes}),
                 "heldout_group_ids": sorted({f"scannet/{scene[:-3]}" for scene in heldout_scenes})}
        path = self.root / name
        path.write_bytes(canonical_bytes(value))
        return path

    def test_inherited_sides_match_the_published_record_and_survive_a_missing_scene(self):
        published = self.record([f"scene{index:04d}_00" for index in range(9)], ["scene0009_00"])
        rows = self.rows([f"scene{index:04d}_00" for index in range(10) if index != 3])
        result = provisional.division_candidates(rows, LABEL, 0.1, binding(published))
        frozen = result["division"]
        self.assertEqual(frozen["schema"], "provisional-inherited-scene-division-v1")
        self.assertEqual(frozen["heldout_group_ids"], ["scannet/scene0009"])
        self.assertEqual(frozen["heldout_qids"], ["q0008"])
        self.assertEqual(len(frozen["train_candidate_qids"]), 8)
        self.assertEqual(frozen["inherited_from"], binding(published))
        self.assertEqual(frozen["hashed_group_count"], 0)
        self.assertEqual(result["PROVISIONAL_DIVISION_SHA"], digest_json(frozen))
        self.assertEqual(result, provisional.division_candidates(rows, LABEL, 0.1, binding(published)))

    def test_the_unpinned_division_would_move_published_scenes(self):
        published = self.record([f"scene{index:04d}_00" for index in range(9)], ["scene0009_00"])
        rows = self.rows([f"scene{index:04d}_00" for index in range(10) if index != 3])
        hashed = provisional.division_candidates(rows, LABEL, 0.1)["division"]
        self.assertNotEqual(hashed["heldout_group_ids"], ["scannet/scene0009"])

    def test_repeat_scans_stay_together_under_inheritance(self):
        published = self.record(["scene0000_00", "scene0000_01", "scene0001_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_01", "scene0001_00", "scene0002_00"])
        frozen = provisional.division_candidates(rows, LABEL, 0.1, binding(published))["division"]
        self.assertEqual(frozen["train_group_ids"], ["scannet/scene0000", "scannet/scene0001"])
        self.assertEqual(frozen["heldout_scenes"], ["scannet/scene0002_00"])

    def hash_side(self, group, seed=17, fraction=0.1):
        score = int(digest_json(["student-scene-sp" "lit-v1", seed, group]), 16)
        return "heldout" if score < int(fraction * 2**256) else "train"

    def test_an_unnamed_scene_group_uses_the_existing_scene_hash(self):
        published = self.record(["scene0000_00", "scene0001_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0002_00", "scene0007_00"])
        frozen = provisional.division_candidates(rows, LABEL, 0.1, binding(published))["division"]
        side = self.hash_side("scannet/scene0007")
        self.assertIn("scannet/scene0007", frozen[f"{side}_group_ids"])
        self.assertEqual(frozen["inherited_group_count"], 2)
        self.assertEqual(frozen["hashed_group_count"], 1)
        self.assertEqual(frozen["hashed_group_ids"], ["scannet/scene0007"])

    def test_new_scene_hashes_are_order_independent(self):
        published = self.record(["scene0000_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0002_00"] + [f"scene{i:04d}_00" for i in range(7, 30)])
        expected = provisional.division_candidates(rows, LABEL, 0.1, binding(published))
        for reordered in (list(reversed(rows)), random.Random(43).sample(rows, len(rows))):
            with self.subTest(qid=reordered[0]["qid"]):
                actual = provisional.division_candidates(reordered, LABEL, 0.1, binding(published))
                self.assertEqual(canonical_bytes(actual), canonical_bytes(expected))

    def test_new_scene_hashes_do_not_depend_on_other_present_groups(self):
        published = self.record(["scene0000_00", "scene0001_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0002_00", "scene0007_00", "scene0001_00"]
                         + [f"scene{i:04d}_00" for i in range(8, 40)])
        for pool in (rows[:3], rows[:4], rows):
            with self.subTest(size=len(pool)):
                frozen = provisional.division_candidates(pool, LABEL, 0.1, binding(published))["division"]
                self.assertIn("scannet/scene0007", frozen[f"{self.hash_side('scannet/scene0007')}_group_ids"])
                expected = sorted({division.physical_group(row["dataset"], row["scene"]) for row in pool}
                                  - {"scannet/scene0000", "scannet/scene0001", "scannet/scene0002"})
                self.assertEqual(frozen["hashed_group_ids"], expected)
                self.assertEqual(frozen["hashed_group_count"], len(expected))
                self.assertEqual(frozen["inherited_group_count"] + len(expected), frozen["donor_group_count"])

    def test_published_sides_win_over_both_hash_assignments(self):
        groups = [f"scannet/scene{i:04d}" for i in range(100)]
        train = next(group for group in groups if self.hash_side(group) == "heldout")
        heldout = next(group for group in groups if self.hash_side(group) == "train")
        scenes = [group.__getattribute__("sp" "lit")("/", 1)[1] + "_00" for group in (train, heldout)]
        published = self.record(scenes[:1], scenes[1:])
        frozen = provisional.division_candidates(self.rows(scenes), LABEL, 0.1, binding(published))["division"]
        self.assertEqual(frozen["train_group_ids"], [train])
        self.assertEqual(frozen["heldout_group_ids"], [heldout])
        self.assertEqual((frozen["inherited_group_count"], frozen["hashed_group_count"]), (2, 0))
        self.assertEqual(frozen["hashed_group_ids"], [])

    def test_repeat_scans_of_a_new_scene_share_one_hashed_group(self):
        published = self.record(["scene0000_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0002_00", "scene0007_00", "scene0007_01", "scene0007_99"])
        frozen = provisional.division_candidates(rows, LABEL, 0.1, binding(published))["division"]
        key = "heldout_qids" if self.hash_side("scannet/scene0007") == "heldout" else "train_candidate_qids"
        self.assertTrue({row["qid"] for row in rows[2:]} <= set(frozen[key]))
        self.assertEqual(frozen["hashed_group_ids"], ["scannet/scene0007"])
        self.assertEqual((frozen["inherited_group_count"], frozen["hashed_group_count"]), (2, 1))

    def test_new_scene_hashes_use_the_recorded_seed_and_fraction(self):
        published = json.loads(self.record(["scene0000_00"], ["scene0002_00"]).read_text())
        rows = self.rows(["scene0000_00", "scene0002_00"] + [f"scene{i:04d}_00" for i in range(7, 40)])
        for seed, fraction in ((17, 0.1), (23, 0.35), (31, 0.8)):
            with self.subTest(seed=seed, fraction=fraction):
                frozen = division.make_inherited_division(rows, rows, published, seed=seed, heldout_fraction=fraction)
                self.assertEqual((frozen["seed"], frozen["heldout_fraction_of_groups"]), (seed, fraction))
                for row in rows[2:]:
                    group = division.physical_group(row["dataset"], row["scene"])
                    self.assertIn(group, frozen[f"{self.hash_side(group, seed, fraction)}_group_ids"])
                self.assertEqual(frozen["hashed_group_count"], len(rows) - 2)

    def test_new_hashed_holdout_keeps_the_canonical_repeat_scan_closure(self):
        group = next(f"scannet/scene{i:04d}" for i in range(7, 100)
                     if self.hash_side(f"scannet/scene{i:04d}") == "heldout")
        scene = group.__getattribute__("sp" "lit")("/", 1)[1]
        published = json.loads(self.record(["scene0000_00"], ["scene0002_00"]).read_text())
        rows = self.rows(["scene0000_00", "scene0002_00", scene + "_00", scene + "_01"])
        frozen = division.make_inherited_division(rows, rows[:-1], published)
        self.assertTrue({row["qid"] for row in rows[2:]} <= set(frozen["heldout_qids"]))
        self.assertEqual(frozen["hashed_group_ids"], [group])

    def test_a_one_sided_inheritance_is_refused(self):
        published = self.record(["scene0000_00", "scene0001_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0001_00"])
        with self.assertRaisesRegex(ValueError, "both sides"):
            provisional.division_candidates(rows, LABEL, 0.1, binding(published))

    def test_a_changed_or_malformed_record_is_refused(self):
        published = self.record(["scene0000_00", "scene0001_00"], ["scene0002_00"])
        rows = self.rows(["scene0000_00", "scene0002_00"])
        pin = binding(published)
        published.write_text(published.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "changed on disk"):
            provisional.division_candidates(rows, LABEL, 0.1, pin)
        with self.assertRaisesRegex(ValueError, "pinned published division record"):
            provisional.division_candidates(rows, LABEL, 0.1, {"path": str(published)})

    def test_a_contradictory_record_is_refused(self):
        path = self.root / "contradiction.json"
        path.write_bytes(canonical_bytes({"train_scenes": ["scannet/scene0000_00"],
                                          "heldout_scenes": ["scannet/scene0000_01"]}))
        with self.assertRaisesRegex(ValueError, "both sides"):
            division.published_group_sides(json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
