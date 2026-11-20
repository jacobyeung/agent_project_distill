"""Input-integrity checks and synthetic clean-room raster checks, not parity proof."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'builder_cr'))
import numpy as np
from preflight import ROOT, TARGETS, require_reproduction
from raycast_cr import first_hits


class Checks(unittest.TestCase):
    def test_reproduction_gate_rejects_missing_and_copied_gt(self):
        for records in ([], [dict(dataset=d, all_arrays_equal=True, independent_inputs=False) for d in TARGETS]):
            with self.assertRaises(RuntimeError):
                require_reproduction(records)

    def test_reproduction_gate_requires_all_three_datasets(self):
        records = [dict(dataset=d, all_arrays_equal=True, independent_inputs=True) for d in TARGETS]
        require_reproduction(records)
        with self.assertRaises(RuntimeError):
            require_reproduction(records[:-1])

    def test_staged_inputs_and_rgb_hashes(self):
        report = json.loads((ROOT / 'out/PREFLIGHT.json').read_text())
        self.assertTrue(report['stage_complete'])
        self.assertEqual(len(report['captures']), 22)
        self.assertEqual(len(report['references']), 38)
        for row in report['captures']:
            self.assertGreater(row['raw_files'], 0)
            self.assertEqual(row['missing_raw'], [])
            self.assertEqual(len(row['anchors']), 32)
            self.assertEqual([f['index'] for f in row['frames']], row['anchors'])
            self.assertTrue(all(f['verified'] for f in row['frames']))

    def test_existing_npz_raster_schema(self):
        report = json.loads((ROOT / 'out/PREFLIGHT.json').read_text())
        for ref in report['references']:
            s = ref['schema']
            self.assertEqual(s['depth']['dtype'], 'float32')
            self.assertEqual(s['inst']['dtype'], 'int32')
            self.assertIn(s['depth']['shape'], [[32, 240, 320], [32, 320, 240]])
            self.assertEqual(s['depth']['shape'], s['inst']['shape'])
            self.assertEqual(s['c2w']['shape'], [32, 4, 4])

    def test_first_hit_uses_nearest_positive_camera_z(self):
        vertices = np.array([[-10, -10, 4], [10, -10, 4], [0, 10, 4],
                             [-10, -10, 2], [10, -10, 2], [0, 10, 2]], float)
        depth, faces = first_hits(vertices, np.array([[0, 1, 2], [3, 4, 5]]),
                                  np.eye(4), np.eye(3), (1, 1))
        np.testing.assert_array_equal(depth, [[2.]])
        np.testing.assert_array_equal(faces, [[1]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
