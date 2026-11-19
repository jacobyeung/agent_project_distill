import gzip
import json
from pathlib import Path
import unittest

from student_pilot.live_trace313 import AuditSession, replay


RECORD = Path("/scratch/jjyeung/orch_cd/leg_s1_tree/out/native_programs_r9/00.json.gz")


class NativeReplayTests(unittest.TestCase):
    @unittest.skipUnless(RECORD.is_file(), "Requires retained native tiny-model decode")
    def test_explicit_predicted_geometry_replays_native_calls(self):
        with gzip.open(RECORD, "rt") as handle:
            record = json.load(handle)["decode"]
        for query in record["heads"]["ground_queries"]:
            self.assertEqual(query["geometry_source"], "same_checkpoint_own")
            query["geometry_mode"] = "predicted"
        result = replay(record)
        self.assertTrue(result["byte_equal"], result)

    def test_mixed_geometry_modes_refuse(self):
        with self.assertRaisesRegex(ValueError, "geometry_mode"):
            AuditSession([dict(geometry_mode="sensor"), dict(geometry_mode="predicted")], "3.14")


if __name__ == "__main__":
    unittest.main()
