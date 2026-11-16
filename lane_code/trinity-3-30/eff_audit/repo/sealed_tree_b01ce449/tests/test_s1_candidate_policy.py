from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
from scipy import ndimage

from student_pilot.candidate_policy import Policy, depth_cut, disjoint, merge, predict
from student_pilot.ground_sources import MaskBatch, MaskProvider
from student_pilot.p3_provenance import file_pin
from student_pilot.routed_features import Geometry, pair_features, rle, select_instances
from student_pilot.routed_candidates import small_rle, SHAPE


class PlaneGeometry:
    def has(self, frame):
        return 1 <= frame <= 32

    def cam(self, frame):
        return np.eye(3), np.zeros(3)

    def fov_of(self, frame):
        return np.pi/2, np.pi/2

    def _depth(self, slot, u, v):
        return np.full(np.asarray(u).shape, 2.)

    def lift(self, frame, uv, mode="center"):
        uv = np.asarray(uv)
        points = np.column_stack(((uv[:, 0]/500-1)*2, (uv[:, 1]/500-1)*2, np.full(len(uv), 2.)))
        return points, points.copy(), np.zeros(len(uv))


class FrameMap:
    source_indices = tuple(range(0, 64, 2))

    def require(self, indices):
        if tuple(indices) != self.source_indices:
            raise ValueError("frame identity differs")


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(name="routed_default_v1", weights=file_pin(
            Path(__file__).parents[1] / "student_pilot/assets/routed_policy_v1.json"))

    def test_rle_preserves_native_small_mask_sampling(self):
        mask = np.zeros((480, 640), bool)
        mask[80:170, 100:300] = True
        expected = ndimage.zoom(mask, (SHAPE[0]/480, SHAPE[1]/640), order=0, prefilter=False)
        np.testing.assert_array_equal(small_rle(rle(mask)), expected)

    def test_depth_cut_and_disjoint_block(self):
        mask = np.zeros((40, 50), bool)
        mask[4:36, 4:46] = True
        depth = np.full(mask.shape, 2.)
        depth[4:7] = 5.
        cut = depth_cut(mask, depth)
        self.assertLess(cut.sum(), mask.sum())
        self.assertTrue(disjoint({1: mask}, {1: ~mask}))
        self.assertFalse(disjoint({1: mask}, {2: ~mask}))
        self.assertEqual(merge(["a", "b"], lambda a, b: .99, lambda a, b: True), [["a"], ["b"]])

    def test_policy_rejects_missing_or_nonfinite_features(self):
        policy = Policy(self.config, "object_abs_distance")
        features = dict(zip(policy.weights["accept"]["features"], policy.weights["accept"]["mean"], strict=True))
        self.assertTrue(0 <= predict(policy.weights["accept"], features) <= 1)
        with self.assertRaisesRegex(ValueError, "lacks features"):
            predict(policy.weights["accept"], {})
        features["peak"] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            predict(policy.weights["accept"], features)

    def test_native_candidates_features_and_unique_policy(self):
        frames = FrameMap()
        def masks(name):
            values = np.zeros((32, 480, 640), bool)
            left = 100 if name == "chair" else 360
            values[:, 160:300, left:left+100] = True
            return MaskBatch(values, np.full(32, .9), frames.source_indices, .5)
        source = MaskProvider(masks, "cpu-geometric-fixture", names=("chair", "table"))
        owner = SimpleNamespace(config=dict(candidate_universe=source.names), source=source,
                                scene=SimpleNamespace(frames=frames), geometry_error=None,
                                candidate_policy=Policy(self.config, "object_abs_distance"))
        result, audit = select_instances(owner, "chair", PlaneGeometry())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["masks"].shape, (32, 240, 320))
        self.assertTrue(result[0]["masks"].any())
        self.assertTrue(result[0]["depth_cut_applied"])
        self.assertTrue(audit["interior_depth_cut"])
        self.assertEqual(audit["candidate_universe"], ["chair", "table"])
        candidates = owner._routed_candidate_cache["candidates"]
        first, second = candidates["chair"][0], candidates["table"][0]
        self.assertEqual(set(first["features"]), set(owner.candidate_policy.weights["accept"]["features"]))
        pair = pair_features(first, second, Geometry(PlaneGeometry()))
        self.assertEqual(set(pair), set(owner.candidate_policy.weights["pair"]["features"]))
        self.assertTrue(all(np.isfinite(value) for value in pair.values()))
        self.assertGreater(pair["d_c"], 0.)

    def test_universe_is_required(self):
        owner = SimpleNamespace(config=dict(candidate_universe=[]), geometry_error=None)
        with self.assertRaisesRegex(ValueError, "fixed named"):
            select_instances(owner, "chair", PlaneGeometry())


if __name__ == "__main__":
    unittest.main()
