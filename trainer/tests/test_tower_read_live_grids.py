"""Live-gate regressions for the independent verifier's open grid comparison."""
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from tests.tower_live_grids import compare_auxiliary_grids


class LiveGrids(unittest.TestCase):
    def fixture(self):
        reference = dict(points_grid=np.ones((32, 51, 51, 3)),
                         depth_conf_grid=np.full((32, 51, 51), 2.))
        return SimpleNamespace(**{k: v.copy() for k, v in reference.items()}), reference

    def test_matching_grids_and_device_tolerances(self):
        state, reference = self.fixture()
        self.assertTrue(compare_auxiliary_grids(state, reference, .01)['auxiliary_grids_pass'])
        state.points_grid *= 1.02
        self.assertFalse(compare_auxiliary_grids(state, reference, .01)['auxiliary_grids_pass'])
        self.assertTrue(compare_auxiliary_grids(state, reference, .03)['auxiliary_grids_pass'])

    def test_world_frame_points_and_changed_confidence_refuse(self):
        state, reference = self.fixture()
        state.points_grid += [3., 0., 0.]
        self.assertFalse(compare_auxiliary_grids(state, reference, .03)['points_grid']['passed'])
        state, reference = self.fixture()
        state.depth_conf_grid *= .5
        self.assertFalse(compare_auxiliary_grids(state, reference, .03)['depth_conf_grid']['passed'])

    def test_shape_missing_and_finite_pattern_refuse(self):
        for mutation in ('missing', 'shape', 'nan'):
            state, reference = self.fixture()
            if mutation == 'missing':
                state.points_grid = None
            elif mutation == 'shape':
                state.points_grid = state.points_grid[:-1]
            else:
                state.depth_conf_grid[0] = np.nan
            with self.subTest(mutation=mutation):
                self.assertFalse(compare_auxiliary_grids(state, reference, .03)['auxiliary_grids_pass'])

    def test_live_gate_wiring_refuses_points_with_correct_cameras_and_depth(self):
        import hashlib, os, tempfile
        from pathlib import Path
        from student_pilot import tower_read as tower
        from tests import tower_live_parity as live
        root = Path(tempfile.mkdtemp(prefix='live-grid-gate-', dir=os.environ['LANE_TEST_OUTPUT']))
        state, reference = self.fixture()
        raw = np.zeros((64, 9)); raw[:, 6] = 1.; raw[:, 7:] = 1.
        slots = np.arange(0, 64, 2)
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        digest = hashlib.sha256(frame.tobytes()).digest()
        np.savez_compressed(root/'cache.npz', **reference, raw_pose=raw, depth_grid=np.ones((32, 51, 51)),
                            frame_indices=np.arange(64), anchor_slots=slots,
                            frame_identity=np.array([digest]*64, dtype='S32'), source_hw=[2, 2])
        np.savez_compressed(root/'own.npz', depth_grid=np.ones((32, 51, 51)))
        np.savez_compressed(root/'heads.npz', scale=1.)
        (root/'video.mp4').write_bytes(b'fixture')
        (root/'model.safetensors').write_bytes(b'fixture')
        state.raw_pose9, state.depth_grid, state.anchor_slots = raw, np.ones((32, 51, 51)), slots
        state.scaled_pose9 = lambda depth: (raw[slots], 1.)
        args = dict(tree=Path(__file__).resolve().parents[1], device='cpu', weights_dir=root,
                    video=root/'video.mp4', cache=root/'cache.npz', own=root/'own.npz', heads=root/'heads.npz')
        with mock.patch.object(live, 'decode', return_value=[frame]*64), \
             mock.patch.object(tower, '_hash', return_value=tower.WEIGHTS_SHA256), \
             mock.patch.object(tower, 'FrozenG3TTower') as frozen:
            frozen.return_value.run.return_value = state
            self.assertEqual(live.check(**args)['status'], 'PASS')
            state.points_grid += [3., 0., 0.]
            self.assertEqual(live.check(**args)['status'], 'FAIL')
