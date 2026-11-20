"""Test the audit's transform direction, metric scale, and invariants on known poses."""
import unittest
import numpy as np
from analyze_round5 import FLIP, WORLD, alignment, converted, diagnostics


def rotation(axis, angle):
    u = np.asarray(axis,float); u /= np.linalg.norm(u)
    x,y,z = u; K = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K)


def fixture():
    rng = np.random.default_rng(55231)
    a = np.repeat(np.eye(4)[None], 32, axis=0)
    a[:,:3,3] = rng.normal(size=(32,3))
    for i in range(32):
        a[i,:3,:3] = rotation(rng.normal(size=3),rng.uniform(-2,2))
    T = np.eye(4);T[:3,:3] = rotation([1,2,3],.7);T[:3,3] = [2,-3,.5]
    return a,T


class CameraAuditTests(unittest.TestCase):
    def test_recovers_known_rigid_transform(self):
        a,T = fixture(); f = diagnostics(a,T@a)
        self.assertTrue(f['rigid']['accepted'])
        np.testing.assert_allclose(f['rigid']['reader_world_to_gt_world'],T,atol=1e-12)
        self.assertAlmostEqual(f['similarity_diagnostic']['scale'],1.)

    def test_direction_and_camera_axes(self):
        a,T = fixture();b = T@a
        representations = dict(c2w_cv=b,c2w_gl=b@FLIP,w2c_cv=np.linalg.inv(b),w2c_gl=np.linalg.inv(b@FLIP))
        for name,stored in representations.items():
            with self.subTest(name=name):
                np.testing.assert_allclose(converted(stored,name),b,atol=1e-12)
                self.assertTrue(alignment(a,converted(stored,name))['accepted'])
        self.assertFalse(alignment(a,representations['w2c_cv'])['accepted'])

    def test_similarity_never_rescales_rigid_acceptance(self):
        a,T = fixture();b = T@a
        b[:,:3,3] = 1.3*(a[:,:3,3]@T[:3,:3].T)+T[:3,3]
        f = diagnostics(a,b)
        self.assertFalse(f['rigid']['accepted'])
        self.assertFalse(f['rigid']['fit_scale'])
        self.assertAlmostEqual(f['similarity_diagnostic']['scale'],1.3)
        self.assertLess(f['similarity_diagnostic']['translation_rms_m'],1e-12)

    def test_world_up_cannot_repair_residuals(self):
        a,T = fixture();b = T@a;b[4,0,3] += .7
        base = alignment(a,b);world = alignment(a,WORLD@b)
        for field in ('translation_rms_m','rotation_rms_deg','rotation_max_deg'):
            self.assertAlmostEqual(base[field],world[field],places=7)
        self.assertEqual(base['accepted'],world['accepted'])

    def test_camera_flip_preserves_centers(self):
        a,T = fixture();b = T@a
        f = alignment(a,b);g = alignment(a,b@FLIP)
        self.assertAlmostEqual(f['translation_rms_m'],g['translation_rms_m'])
        self.assertGreater(g['rotation_max_deg'],179.99)

    def test_relative_rotation_detects_nonconstant_error(self):
        a,T = fixture();b = T@a
        b[7,:3,:3] = rotation([1,0,0],.8)@b[7,:3,:3]
        f = diagnostics(a,b)
        self.assertTrue(f['pairwise_rotation_invariant']['excludes_any_fixed_world_and_camera_axis_rotation'])
        g = diagnostics(a,WORLD@b@FLIP)
        self.assertAlmostEqual(f['pairwise_rotation_invariant']['max_relative_angle_disagreement_deg'],
                               g['pairwise_rotation_invariant']['max_relative_angle_disagreement_deg'])
        self.assertGreater(f['rotation_only_diagnostic']['rotation_max_deg'],5)


if __name__ == '__main__':
    unittest.main()
