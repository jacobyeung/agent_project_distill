"""Independent rigid-gap and gravity-refit controls; no verdict reads."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import devpose2 as r
import numpy as np
import unittest
from scipy.spatial.transform import Rotation


class RigidTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r.d.dependencies(r.d.arguments([]).gbuild)

    def box(self, center, lengths=(1., 1., 1.)):
        return dict(center=np.array(center, float), axes=np.eye(3), full_lengths=np.array(lengths))

    def test_identity_camera_L1_equals_L2_exactly(self):
        a, b = (r.original_box(self.box(c)) for c in ([0, 0, 0], [4, 2, 1]))
        rotation, offset = r.rigid_map(np.eye(4), np.eye(4))
        self.assertEqual(r.exact_gap(a, b), r.exact_gap(r.rigid_box(a, rotation, offset), r.rigid_box(b, rotation, offset)))
        self.assertEqual(r.d.score(r.exact_gap(a, b), r.exact_gap(a, b)), 100.)

    def test_axis_aligned_closed_box_gaps_and_contact(self):
        a = r.original_box(self.box([0, 0, 0]))
        for center, expected in (([4, 2, 1], np.sqrt(10)), ([1, 0, 0], 0.), ([.2, .2, .2], 0.)):
            self.assertAlmostEqual(r.exact_gap(a, r.original_box(self.box(center))), expected, places=12)
        self.assertEqual(r.exact_gap(a, r.original_box(self.box([0, 0, 0], (.1, .1, .1)))), 0.)

    def test_shared_tilt_and_translation_preserve_exact_gap(self):
        rng = np.random.default_rng(20261120)
        for _ in range(30):
            a = r.original_box(self.box(rng.normal(size=3), rng.uniform(.2, 2., 3)))
            b = r.original_box(self.box(rng.normal(size=3)*3, rng.uniform(.2, 2., 3)))
            a['axes'] = Rotation.random(random_state=rng).as_matrix()
            b['axes'] = Rotation.random(random_state=rng).as_matrix()
            rotation = Rotation.random(random_state=rng).as_matrix(); offset = rng.normal(size=3)*10
            self.assertAlmostEqual(r.exact_gap(a, b), r.exact_gap(r.rigid_box(a, rotation, offset), r.rigid_box(b, rotation, offset)), places=10)

    def test_known_one_anchor_rotation(self):
        a, b = (r.original_box(self.box(c)) for c in ([2, 0, 0], [5, 0, 0]))
        turn = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        self.assertAlmostEqual(r.exact_gap(a, b), 2., places=12)
        self.assertAlmostEqual(r.exact_gap(a, r.rigid_box(b, turn, np.zeros(3))), np.sqrt(17), places=12)

    def test_gravity_fit_identity_is_reader_L2(self):
        a, b = self.box([.2, .4, .3], (1.13, .77, 1.26)), self.box([4.2, 2.1, .8], (.64, 1.36, .83))
        expected = r.d.gap(r.d.refit(r.d.corners(a)), r.d.refit(r.d.corners(b)))
        actual = r.d.gap(r.gravity_refit(a, np.eye(3), np.zeros(3)), r.gravity_refit(b, np.eye(3), np.zeros(3)))
        self.assertEqual(actual, expected)

    def test_gravity_fit_tilt_preserves_common_world(self):
        a, b = self.box([.2, .4, .3], (1.13, .77, 1.26)), self.box([4.2, 2.1, .8], (.64, 1.36, .83))
        rotation = Rotation.from_euler('xyz', [41, -32, 27], degrees=True).as_matrix()
        offset = np.array([3., -2., 7.])
        expected = r.d.gap(r.d.refit(r.d.corners(a)), r.d.refit(r.d.corners(b)))
        actual = r.d.gap(r.gravity_refit(a, rotation, offset), r.gravity_refit(b, rotation, offset))
        self.assertAlmostEqual(actual, expected, places=10)
        fitted = r.gravity_refit(a, rotation, offset)
        np.testing.assert_allclose(fitted['centre'], np.array(a['center'])@rotation.T+offset, atol=1e-12)

    def test_up_alignment_including_antiparallel(self):
        for up in ([0., 0., 1.], [0., 0., -1.], [.2, .4, .9]):
            up = np.array(up); up /= np.linalg.norm(up)
            turn = r.up_to_z(up)
            np.testing.assert_allclose(turn@up, [0, 0, 1], atol=1e-12)
            np.testing.assert_allclose(turn@turn.T, np.eye(3), atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(turn), 1.)


if __name__ == '__main__':
    unittest.main(verbosity=2)
