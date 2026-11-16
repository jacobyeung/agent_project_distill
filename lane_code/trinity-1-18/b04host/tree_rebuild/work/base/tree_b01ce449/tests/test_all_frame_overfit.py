"""CPU guard for the production all-frame query expansion and pose head."""
import json
import math
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from student_pilot.decoupled_v import head_settings, learning_rate
from student_pilot.decoupled_vc import VC_BATCH4H_RECIPE
from student_pilot.p3_heads import P3Heads, PrefixCapture
from tests.test_decoupled_overfit import pose_fixture
from tests.test_decoupled_pose_fix import settings
from student_pilot.decoupled_v_run import SPATIAL_CAMERA


class AllFrameOverfitTests(unittest.TestCase):
    def test_32_rows_32_poses_in_200_steps(self):
        threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, threads)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(31)
            x, target, mask = pose_fixture(all_frames=True)
            self.assertEqual(tuple(x.shape), (32, 16, 1152))
            self.assertEqual(tuple(target.shape), (32, 32, 9))
            self.assertTrue(mask.all())
            camera = settings(**SPATIAL_CAMERA, point_depth=dict(weight=.1, d_proj=16,
                mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1, 2, 3]))
            cfg = SimpleNamespace(p3=head_settings(camera, 'fixture', 'a'*64, all_frames=True),
                text_config=SimpleNamespace(num_hidden_layers=4),
                vision_config=SimpleNamespace(hidden_size=1152, depth=3, spatial_merge_size=2))
            cfg.p3['feature_backing'] = 'decoupled_vc'
            heads = P3Heads(cfg)
            self.assertEqual(tuple(heads.frame_queries.shape), (32, 1152))
            model = SimpleNamespace(config=cfg, auxiliary_heads=heads)
            # Synthetic frozen ViT grids replace only the encoder output. Native
            # PrefixCapture and pose_inputs select fused spatial grids and frame queries.
            grids = [row[:, None, None, :].expand(-1, 2, 2, -1) for row in x]

            def predict():
                capture = PrefixCapture(model, {'video_grid_thw': torch.tensor([[16, 4, 4]]*32)})
                capture.vit = dict.fromkeys((1, 2, 3))
                with patch('student_pilot.p3_heads.vit_grids_by_row', return_value=grids):
                    capture.finish()
                return heads.camera.predict(capture.states, **capture.pose_inputs())

            parameters = list(heads.parameters())
            optimizer = torch.optim.AdamW(parameters, lr=1e-4, weight_decay=.01)

            def metrics():
                with torch.no_grad():
                    pred = predict()[-1]
                    self.assertEqual(tuple(pred.shape), (32, 32, 9))
                    q = torch.nn.functional.normalize(pred[..., 3:7], dim=-1)
                    error = 2*torch.acos((q*target[..., 3:7]).sum(-1).abs().clamp(max=1))*180/math.pi
                    return float(error.mean()), float(error.mean(-1).max())

            initial, _ = metrics()
            started = time.perf_counter()
            for step in range(1, 201):
                stages = predict()
                loss = .2*sum(.6**(3-i)*heads.camera.stage_loss(p, target, mask, torch.ones(32))
                              for i, p in enumerate(stages)).mean()/4
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                self.assertTrue(torch.isfinite(heads.frame_queries.grad).all())
                self.assertGreater(float(heads.frame_queries.grad.norm()), 0.)
                torch.nn.utils.clip_grad_norm_(parameters, 1.)
                for group in optimizer.param_groups:
                    group['lr'] = learning_rate(step, VC_BATCH4H_RECIPE)
                optimizer.step()
            final, worst = metrics()
            print(json.dumps(dict(rows=32, poses=32, queries_per_group=2, steps=200,
                pose_input='spatial_tokens_v1',
                initial_mean_rotation_deg=initial, final_mean_rotation_deg=final,
                worst_row_mean_rotation_deg=worst, seconds=time.perf_counter()-started)))
            self.assertGreater(initial, 30.)
            self.assertLess(final, 30.)
            self.assertLess(worst, 30.)
            self.assertLess(final, initial*.3)
            self.assertLess(worst, initial*.3)


if __name__ == '__main__':
    unittest.main()
