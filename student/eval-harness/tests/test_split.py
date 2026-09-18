import unittest

from student_pilot.split import make_split, physical_group


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.members = [
            {"qid": str(i), "dataset": "scannet", "scene": f"scene{i:04d}_00", "category": "object_counting"}
            for i in range(20)
        ]

    def test_deterministic_and_correctness_independent(self):
        first = make_split(self.members, self.members)
        poisoned = [{**row, "is_correct": False, "ground_truth": "unused"} for row in reversed(self.members)]
        self.assertEqual(first, make_split(poisoned, list(reversed(poisoned))))
        self.assertEqual(len(first["heldout_qids"]), 4)
        self.assertFalse(set(first["heldout_qids"]) & set(first["train_candidate_qids"]))

    def test_holdout_contains_all_canonical_repeated_scans(self):
        first = make_split(self.members, self.members)
        heldout_id = first["heldout_qids"][0]
        source = next(row for row in self.members if row["qid"] == heldout_id)
        extra = {**source, "qid": "100", "scene": source["scene"].replace("_00", "_01")}
        second = make_split(self.members + [extra], self.members)
        self.assertIn("100", second["heldout_qids"])
        self.assertEqual(first["heldout_group_ids"], second["heldout_group_ids"])

    def test_donor_identity_mismatch_is_rejected(self):
        bad = [{**self.members[0], "scene": "scene9999_00"}] + self.members[1:]
        with self.assertRaises(ValueError):
            make_split(self.members, bad)

    def test_group_only_identifiable_scans(self):
        self.assertEqual(physical_group("scannet", "scene0001_00"), physical_group("scannet", "scene0001_03"))
        self.assertNotEqual(physical_group("scannetpp", "abc"), physical_group("scannetpp", "def"))

    def test_duplicate_canonical_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            make_split(self.members + [self.members[0]], self.members)


if __name__ == "__main__":
    unittest.main()
