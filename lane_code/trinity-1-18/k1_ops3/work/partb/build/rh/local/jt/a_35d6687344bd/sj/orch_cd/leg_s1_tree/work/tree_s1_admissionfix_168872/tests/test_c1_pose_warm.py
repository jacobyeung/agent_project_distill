"""Warm-started pose-only runs: init from a C1 milestone, an own LR horizon/milestones, and a sampler offset
that continues the donor's row order. Absent keys keep the fixed C1 pose-only recipe byte-identical."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from student_pilot import carrier_c1_run as run, carrier_c1_data as data
from student_pilot.carrier_c1 import RECIPE
from student_pilot.carrier_c1_sweep import capped_steps, recipe_for
from tests.test_c1_blockers import transport
from tests.test_carrier_c1 import fixture

SCHEDULE = dict(startup_seconds=900, p95_step_seconds=40, checkpoint_seconds=300, export_seconds=300)
PIN = {'path': '/fixture/m800/artifact.json', 'sha256': 'a' * 64}


def pose_cfg(**extra):
    cfg = dict(schema='carrier-c1-run-v1', training_mode='pose_only', depth_enabled=False, init='base',
               parallel='fsdp', all_frames=True, frame_layout='duplicate',
               carrier_placement='append_after_temporal_group_video_tokens_v1', base_identity='fixture',
               streams={'pose': {'path': '/fixture/receipt.json', 'sha256': 'b' * 64}}, schedule=dict(SCHEDULE),
               skip_unsupervised_lm=False, output='/fixture/out', preparation_output='/fixture/prep')
    cfg.update(extra)
    cfg['recipe'] = recipe_for(cfg)
    return cfg


def warm(**extra):
    return pose_cfg(init_artifact={'artifact': dict(PIN), 'lm': 'full', 'heads': ['pose']}, steps=300,
                    milestones=[100, 200, 300], row_start_step=800, **extra)


class Recipe(unittest.TestCase):
    def test_default_pose_only_recipe_is_unchanged(self):
        recipe = pose_cfg()['recipe']
        self.assertEqual((recipe['steps'], recipe['milestones'], recipe['mix']), (800, [100, 200, 400, 800], ['pose'] * 4))
        self.assertEqual({k: v for k, v in recipe.items() if k not in ('mix', 'weights')},
                         {k: v for k, v in RECIPE.items() if k not in ('mix', 'weights')})
        self.assertEqual(capped_steps(SCHEDULE), capped_steps(SCHEDULE, total_steps=800, milestones=[100, 200, 400, 800]))

    def test_warm_recipe_horizon_and_milestones(self):
        cfg = warm()
        self.assertEqual((cfg['recipe']['steps'], cfg['recipe']['milestones']), (300, [100, 200, 300]))
        run.validate(cfg)
        # The cap counts the run's own horizon and milestones: all 300 updates fit one allocation at 30 s/update,
        # 255 at 40 s/update (a resume leg finishes), never the fixed recipe's 800.
        self.assertEqual(capped_steps(dict(SCHEDULE, p95_step_seconds=30), total_steps=300, milestones=[100, 200, 300]), 300)
        self.assertEqual(capped_steps(SCHEDULE, total_steps=300, milestones=[100, 200, 300]), 255)
        for bad in (dict(steps=900, milestones=[100]), dict(steps=300, milestones=[200, 100]),
                    dict(steps=300, milestones=[400]), dict(steps='300', milestones=[100])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                pose_cfg(init_artifact={'artifact': dict(PIN), 'lm': 'full', 'heads': ['pose']}, **bad)

    def test_validation_scopes_the_warm_levers(self):
        with self.assertRaisesRegex(ValueError, 'need init_artifact'):
            run.validate(pose_cfg(steps=300, milestones=[100]))
        with self.assertRaisesRegex(ValueError, 'need init_artifact'):
            run.validate(pose_cfg(row_start_step=800))
        cfg = warm()
        for bad in (-1, 1.5, '800'):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'row_start_step'):
                run.validate({**cfg, 'row_start_step': bad})
        # The other final-mode levers stay refused in pose-only mode.
        with self.assertRaisesRegex(ValueError, 'final-mode levers'):
            run.validate({**cfg, 'camera_overrides': {'weight_focal': 2.0}})
        with self.assertRaisesRegex(ValueError, 'init_artifact needs'):
            run.validate({**cfg, 'init_artifact': {'artifact': dict(PIN), 'lm': 'full', 'heads': ['depth']}})


class Offset(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix='psw_', dir=os.environ['LANE_TEST_OUTPUT']))

    def test_steps_read_the_donor_order_after_its_last_step_and_resume_exactly(self):
        cfg = warm(schedule=dict(SCHEDULE, p95_step_seconds=10))
        counts = {'pose': 997}
        donor = list(data.mixed_indices(counts, 1200, training_mode='pose_only'))
        root = self.root(); start = 0; plans = []; exports = []; now = [0.]

        def update(model, optimizer, rows, plan, rank, device, step, distributed, gates=None):
            plans.append((step, plan))
            now[0] += 10.
            return {'wall_seconds': 10.}, None
        with patch.object(run, 'optimize_step', side_effect=update), \
             patch.object(run, 'checkpoint'), patch.object(run, 'export', side_effect=lambda *a: exports.append(a[-1])), \
             patch.object(run.time, 'monotonic', side_effect=lambda: now[0]):
            # A first allocation stops early (budget), a second resumes at its last step.
            first = run.run_steps(None, None, None, None, counts, root, cfg, {}, torch.device('cpu'),
                                  started=-12500., distributed=False)
            self.assertTrue(first['stopped_for_resume'])
            start = first['last_step']
            now[0] = 0.
            with patch.dict(os.environ, SLURM_JOB_ID='2'):
                second = run.run_steps(None, None, None, None, counts, root, cfg, {}, torch.device('cpu'),
                                       start_step=start, started=0., distributed=False)
        self.assertEqual(second['last_step'], 300)
        self.assertFalse(second['stopped_for_resume'])
        self.assertEqual([s for s, _ in plans], list(range(1, 301)))
        self.assertEqual([p for _, p in plans], donor[800:1100])
        self.assertEqual(exports, [100, 200, 300])

    def test_dryrun_plan_uses_the_offset(self):
        counts = {'pose': 997}
        expected = list(data.mixed_indices(counts, 801, training_mode='pose_only'))[800]
        self.assertEqual(next(data.mixed_indices(counts, 801, start_step=800, training_mode='pose_only')), expected)


class WarmStart(unittest.TestCase):
    def test_pose_only_receiver_equals_the_exported_donor(self):
        donor, batch, target = fixture(16, training_mode='pose_only', depth_enabled=False)
        with torch.no_grad():
            for p in donor.parameters():
                p.add_(0.01 * torch.randn_like(p))
        receiver, _, _ = fixture(16, training_mode='pose_only', depth_enabled=False)
        cfg = {'base_identity': 'fixture'}
        root = Path(tempfile.mkdtemp(prefix='psw_init_', dir=os.environ['LANE_TEST_OUTPUT']))
        with transport(), patch('student_pilot.fsdp_training.publication_state',
                                side_effect=lambda model: model.state_dict()):
            run.export(root/'m800', donor, donor, cfg, 800)
        pin = run.file_pin(root/'m800/artifact.json')
        spec = {'artifact': pin, 'lm': 'full', 'heads': ['pose']}
        receipt = {'training_mode': 'pose_only', 'init_artifact': spec}
        calls = []
        native = run.init_from_artifact

        def spy(model, value, verify=True, part='heads'):
            calls.append(part)
            return native(model, value, verify=verify, part=part)
        with patch.object(run, 'init_from_artifact', side_effect=spy):
            # load_model's warm-start branch, after the base load (stubbed by the fixture model).
            with patch('transformers.Qwen3_5ForConditionalGeneration.from_pretrained', return_value=None), \
                 patch.object(run, 'CarrierC1', return_value=receiver), \
                 patch('student_pilot.camera_targets.carrier_id', return_value=5):
                model = run.load_model({'root': str(root), 'files': {}},
                                       {**receipt, 'camera': {}, 'depth': None, 'carrier_placement': receiver.carrier_placement,
                                        'depth_enabled': False, 'recipe': RECIPE},
                                       type('P', (), {'tokenizer': None})())
        self.assertIs(model, receiver)
        self.assertEqual(calls, ['lm', 'heads'])
        live = dict(receiver.named_parameters())
        for name, value in donor.named_parameters():
            expected = value if name.startswith('auxiliary_heads.') else value.to(torch.bfloat16).float()
            torch.testing.assert_close(live[name], expected, rtol=0, atol=0, msg=name)
        receiver.eval(); donor.eval()
        with torch.no_grad():
            a = receiver(copy.deepcopy(batch), target)['components']['pose']
        self.assertTrue(torch.isfinite(a))


if __name__ == '__main__':
    unittest.main()
