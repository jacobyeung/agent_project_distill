"""CPU learning guard: 32 pose-bearing synthetic rows, no images or model weights."""
import json
import math
import time
import unittest

import numpy as np
import torch

from student_pilot.camera_head import CameraSupervision
from student_pilot.camera_targets import encode_cameras, rotation_from_xyzw
from student_pilot.decoupled_v import learning_rate
from student_pilot.decoupled_vc import VC_BATCH4H_RECIPE
from tests.test_decoupled_pose_fix import FIX, settings


def pose_fixture(all_frames=False):
    """32 rows x 32 raw poses -> 16 fused groups x 1152 frozen features.

    Each pair has the same pose. Two yaw trajectories each have 16 origins;
    rolling a trajectory preserves its frame features but changes its targets.
    Features encode absolute per-frame yaw, never the relative target or row ID.
    Targets use the production camera encoder, including anchor/origin direction.
    """
    generator = torch.Generator().manual_seed(29)
    projection = torch.randn(4, 1152, generator=generator)
    features, cameras, masks = [], [], []
    intrinsics = np.tile([[400., 0, 320.], [0, 500., 240.], [0, 0, 1.]], (32, 1, 1))
    for offset in (0., .12):
        yaw = torch.linspace(-1.4, 1.4, 16) + offset
        signal = torch.stack([yaw.sin(), yaw.cos(), (2*yaw).sin(), (2*yaw).cos()], -1) @ projection
        for origin in range(16):
            order = torch.roll(torch.arange(16), -origin)
            angles = yaw[order].repeat_interleave(2).numpy()
            if all_frames:
                angles[1::2] += .08
            poses = np.tile(np.eye(4), (32, 1, 1))
            for frame, angle in enumerate(angles):
                poses[frame, :3, :3] = rotation_from_xyzw([0, np.sin(angle/2), 0, np.cos(angle/2)])
            target, mask, _ = encode_cameras(poses, intrinsics, (480, 640), all_frames=all_frames)
            features.append(signal[order]); cameras.append(target); masks.append(mask)
    return (torch.stack(features), torch.tensor(np.stack(cameras), dtype=torch.float32),
            torch.tensor(np.stack(masks)))


class CpuOverfitTests(unittest.TestCase):
    def test_fixed_heads_overfit_32_rows_in_200_steps(self):
        # The production 1152-wide feature contract, projector, four trunk blocks,
        # four refinements and losses are retained; trunk width is reduced to 64.
        threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, threads)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(31)
            x, target, mask = pose_fixture()
            self.assertEqual(tuple(x.shape), (32, 16, 1152))
            self.assertFalse(x.requires_grad)
            head = CameraSupervision(1152, settings(**FIX)).cpu()
            optimizer = torch.optim.AdamW(head.parameters(), lr=1e-4, weight_decay=.01)

            def metrics():
                with torch.no_grad():
                    pred = head.predict(x)[-1]
                    q = torch.nn.functional.normalize(pred[..., 3:7], dim=-1)
                    error = 2*torch.acos((q*target[..., 3:7]).sum(-1).abs().clamp(max=1))*180/math.pi
                    return float(error.mean()), float(error.mean(-1).max())

            initial, _ = metrics()
            started = time.perf_counter()
            for step in range(1, 201):
                stages = head.predict(x)
                loss = .2*sum(.6**(3-i)*head.stage_loss(p, target, mask, torch.ones(32))
                              for i, p in enumerate(stages)).mean()/4
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(head.parameters(), 1.)
                for group in optimizer.param_groups:
                    group['lr'] = learning_rate(step, VC_BATCH4H_RECIPE)
                optimizer.step()
            final, worst_row = metrics()
            print(json.dumps(dict(rows=32, steps=200, features='synthetic_absolute_per_frame_yaw',
                initial_mean_rotation_deg=initial, final_mean_rotation_deg=final,
                worst_row_mean_rotation_deg=worst_row, seconds=time.perf_counter()-started)))
            self.assertGreater(initial, 30.)
            self.assertLess(final, 30.)
            self.assertLess(worst_row, 30.)
            self.assertLess(final, initial*.3)


if __name__ == '__main__':
    unittest.main()
