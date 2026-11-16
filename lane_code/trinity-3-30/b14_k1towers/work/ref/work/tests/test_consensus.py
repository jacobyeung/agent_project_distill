import unittest

import numpy as np

from geo_bakeoff.consensus import temporal_scales


class ConsensusTests(unittest.TestCase):
    def fixture(self, ratios):
        ratios = np.asarray(ratios, float)
        depth = np.ones((len(ratios), 64, 80), np.float32) * (2 * ratios[:, None, None])
        poses = np.repeat(np.eye(4)[None], len(ratios), 0)
        poses[:, 0, 3] = np.arange(len(ratios)) * .02
        intrinsics = np.repeat(np.array([[60., 0, 40], [0, 60, 32], [0, 0, 1]])[None], len(ratios), 0)
        return depth, poses, intrinsics

    def test_recovers_relative_scales_without_gt(self):
        ratios = np.array([.8, 1., 1.2, .9])
        scale, receipt = temporal_scales(*self.fixture(ratios))
        expected = np.exp(np.log(ratios).mean()) / ratios
        np.testing.assert_allclose(scale, expected, rtol=1e-3)
        self.assertAlmostEqual(float(np.log(scale).mean()), 0, places=8)
        self.assertGreater(receipt["pairs"], 0)
        self.assertFalse(receipt["gt_used"])

    def test_consistent_geometry_is_unchanged(self):
        scale, _ = temporal_scales(*self.fixture([1., 1., 1., 1.]))
        np.testing.assert_allclose(scale, 1., atol=1e-7)

    def test_missing_depth_cannot_drive_a_correction(self):
        depth, poses, intrinsics = self.fixture([1., 1., 1.])
        depth[:] = 0
        scale, receipt = temporal_scales(depth, poses, intrinsics)
        np.testing.assert_array_equal(scale, np.ones(3))
        self.assertEqual(receipt["pairs"], 0)

    def test_bad_pose_is_rejected(self):
        depth, poses, intrinsics = self.fixture([1., 1.])
        poses[1, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            temporal_scales(depth, poses, intrinsics)


if __name__ == "__main__":
    unittest.main()
