"""Phase 1's real HeadSession (student_pilot.head_api) behind Phase1Heads, fed the GT encodings of a real scene:
its answers print exactly the GT responses the converters write (pose with roll and view, every frame 1..32)."""
import math
import os
import unittest

import numpy

import common  # noqa: F401  (puts the package on the path)
from headcall import phase1
from headcall.geometry import Reference
from headcall.heads import HeadContext, Phase1Heads
from headcall.protocol import POSE_FRAMES, Call, format_value

CALIB = os.path.join(os.environ.get("HEADCALL_CALIB_DIR", "/scratch/jjyeung/phase2_opus/calib"),
                     "scannet__scene0000_00.npz")


@unittest.skipUnless(os.path.exists(CALIB), "no calibration copy at %s" % CALIB)
class RealHeadSession(unittest.TestCase):
    def test_exact_heads_print_the_gt_responses(self):
        import torch
        from torch import nn
        targets, head_api = phase1.camera_targets(), phase1.head_api()
        calib = dict(numpy.load(CALIB))
        poses, intrinsics = calib["camera_poses"].astype(float), calib["intrinsics"].astype(float)
        hw = tuple(int(v) for v in calib["raster_hw"])
        camera, mask, scale = targets.encode_cameras(poses, intrinsics, hw)
        gravity, _ = targets.encode_gravity(poses)
        self.assertTrue(mask.all())

        class Exact(nn.Module):
            point_depth = None

            def __init__(self):
                super().__init__()
                self.projector = nn.Linear(4, 4)

            def predict_all(self, states):
                return ([torch.tensor(camera)[None]], [torch.tensor(gravity)[None]],
                        [torch.tensor([math.log(scale)])])
        session = head_api.HeadSession(Exact(), torch.zeros(16, 4))
        heads = Phase1Heads.from_session(session)
        heads.begin(HeadContext([]))
        reference = Reference(poses.tolist(), intrinsics=intrinsics.tolist(), calibration_hw=hw)
        for frame in POSE_FRAMES:
            head = heads.answer(Call("pose", frame, None))
            gt = reference.pose(frame)
            self.assertEqual(format_value("pose", head), format_value("pose", gt), frame)
            numpy.testing.assert_allclose(head.position, gt.position, atol=1e-5)  # float32 calibration
            for a, b in ((head.heading_deg, gt.heading_deg), (head.pitch_deg, gt.pitch_deg),
                         (head.roll_deg, gt.roll_deg)):
                self.assertLess(abs((a - b + 180.0) % 360.0 - 180.0), 1e-4, frame)
            if frame != 1:
                numpy.testing.assert_allclose(head.view_deg, gt.view_deg, atol=1e-6)
        with self.assertRaises(Exception):
            heads.answer(Call("depth", 2, (500, 500)))  # this session has no depth head: a refusal, never a value

    def test_provenance_names_this_tree(self):
        record = phase1.provenance()
        self.assertEqual(record["trainer"], phase1.ROOT)
        self.assertEqual(len(record["commit"] or ""), 40)
        self.assertTrue(all(record["files_sha256"].values()))

    def test_raw_quaternion_l1_is_vggts_convention(self):
        """Phase 1's pose loss is L1 on the raw predicted quaternion (VGGT's camera_loss_single, linear quat_act):
        deliberate, because its targets are unit quaternions with w >= 0 (VGGT's standardize_quaternion) and every
        use of a prediction normalizes it (rotation_from_xyzw here, VGGT's quat_to_mat divides by the squared norm)."""
        targets = phase1.camera_targets()
        rng = numpy.random.default_rng(11)
        for _ in range(20):
            q = rng.normal(size=4)
            rotation = targets.rotation_from_xyzw(q)
            numpy.testing.assert_allclose(targets.rotation_from_xyzw(3.7 * q), rotation, atol=1e-12)
            numpy.testing.assert_allclose(targets.rotation_from_xyzw(-q), rotation, atol=1e-12)
            unit = targets.quaternion_xyzw(rotation)
            self.assertAlmostEqual(float(numpy.linalg.norm(unit)), 1.0, places=12)
            self.assertGreaterEqual(float(unit[3]), 0.0)


if __name__ == "__main__":
    unittest.main()
