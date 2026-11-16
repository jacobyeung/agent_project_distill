"""World-4 final mode with one pose stream and two VQA streams; site leg budget and warmup."""
import copy
import unittest

from student_pilot import carrier_c1_data as data
from student_pilot.carrier_c1 import RECIPE
from student_pilot.carrier_c1_sweep import recipe_for


def configuration(world=4, mix=('pose', 'vqa', 'vqa', 'pointing', 'routing'), **recipe):
    cfg = dict(schema='carrier-c1-run-v1', training_mode='final', depth_enabled=True,
        depth_fov_source='pose_head', frame_layout='duplicate', frame_markers=True,
        init='base', parallel='fsdp', all_frames=True, carrier_placement=data.C1_C,
        streams={s: {} for s in ('pose', 'vqa', 'pointing', 'routing')},
        mix=list(mix), world_size=world, reference_world_size=32,
        steps=1000, milestones=[50, 100, 200, 400, 600, 800, 1000], pose_lr_scale=.6, lm_lr_scale=.6,
        weights=dict(pointing=1., depth=.25, pose=1.5),
        scheduled_sampling=dict(seed=17, max_own_probability=0., pose_open_deg=20., pose_full_deg=10.,
            fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=None,
            exposure_from_step=None, exposure_probability=0.))
    if recipe:
        cfg['recipe'] = dict(recipe)
    cfg['recipe'] = recipe_for(cfg)
    return cfg


class SiteBudget(unittest.TestCase):
    def test_absent_keys_keep_the_recipe_defaults(self):
        cfg = configuration()
        for key in ('warmup_ratio', 'wall_seconds', 'stop_before_seconds', 'resume_every_seconds'):
            self.assertEqual(cfg['recipe'][key], RECIPE[key])
        again = copy.deepcopy(cfg)
        self.assertEqual(recipe_for(again), cfg['recipe'])

    def test_site_values_bind_and_survive_recomputation(self):
        cfg = configuration(warmup_ratio=.05, wall_seconds=84600, stop_before_seconds=3600, resume_every_seconds=3600)
        self.assertEqual((cfg['recipe']['warmup_ratio'], cfg['recipe']['wall_seconds'],
                          cfg['recipe']['stop_before_seconds'], cfg['recipe']['resume_every_seconds']),
                         (.05, 84600, 3600, 3600))
        self.assertEqual(recipe_for(copy.deepcopy(cfg)), cfg['recipe'])

    def test_out_of_range_values_refuse(self):
        for bad in (dict(warmup_ratio=-.1), dict(warmup_ratio=.6), dict(warmup_ratio=True),
                    dict(wall_seconds=600), dict(wall_seconds=90000), dict(wall_seconds=float('nan')),
                    dict(stop_before_seconds=100), dict(wall_seconds=7200, stop_before_seconds=3600)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                configuration(**bad)


class OnePoseTwoVqa(unittest.TestCase):
    def test_world_four_keeps_global_batch_160(self):
        cfg = configuration()
        self.assertEqual(cfg['recipe']['global_batch'], 160)
        self.assertEqual(len(cfg['recipe']['mix']), 40)
        self.assertEqual(cfg['recipe']['mix'].count('vqa'), 16)
        self.assertEqual(cfg['recipe']['mix'].count('pose'), 8)
        self.assertEqual(cfg['recipe']['reference_world_size'], 32)

    def test_without_reference_world_size_world_four_shrinks_the_batch(self):
        cfg = configuration()
        cfg.pop('reference_world_size'); cfg.pop('recipe')
        self.assertEqual(recipe_for(cfg)['global_batch'], 20)

    def test_both_vqa_slots_draw_distinct_rows_within_an_epoch(self):
        cfg = configuration()
        counts = dict(pose=1000, vqa=5000, pointing=800, routing=900)
        plans = list(data.mixed_indices(counts, 3, training_mode='final', mix=cfg['recipe']['mix'], world=4))
        for plan in plans:
            vqa = [i for stream, rows in plan if stream == 'vqa' for i in rows]
            self.assertEqual(len(vqa), 64)
            self.assertEqual(len(set(vqa)), 64)
        seen = [i for plan in plans for stream, rows in plan if stream == 'vqa' for i in rows]
        self.assertEqual(len(set(seen)), len(seen))

    def test_world_four_rows_equal_world_thirty_two_rows(self):
        counts = dict(pose=1000, vqa=5000, pointing=800, routing=900)
        flat = lambda plans: [[(s, i) for s, rows in p for i in rows] for p in plans]
        four, thirty_two = configuration(4), configuration(32)
        a = list(data.mixed_indices(counts, 4, training_mode='final', mix=four['recipe']['mix'], world=4))
        b = list(data.mixed_indices(counts, 4, training_mode='final', mix=thirty_two['recipe']['mix'], world=32))
        self.assertEqual([sorted(x) for x in flat(a)], [sorted(x) for x in flat(b)])


if __name__ == '__main__':
    unittest.main()


class ExportAtStop(unittest.TestCase):
    def test_flag_binds_and_refuses_non_booleans(self):
        self.assertNotIn('export_at_stop', configuration()['recipe'])
        cfg = configuration(export_at_stop=True)
        self.assertIs(cfg['recipe']['export_at_stop'], True)
        self.assertEqual(recipe_for(copy.deepcopy(cfg)), cfg['recipe'])
        for bad in (1, 'yes', None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                configuration(export_at_stop=bad)

    def test_budget_stop_exports_its_last_step_only_with_the_flag(self):
        import os, tempfile
        from pathlib import Path
        from unittest.mock import patch
        import torch
        from student_pilot import carrier_c1_run as run
        base = os.environ.get('LANE_TEST_OUTPUT') or tempfile.gettempdir()
        for flag in (None, True):
            extra = dict(wall_seconds=3600, stop_before_seconds=900)
            if flag is not None:
                extra['export_at_stop'] = flag
            cfg = configuration(**extra)
            cfg['schedule'] = dict(startup_seconds=0, p95_step_seconds=60, checkpoint_seconds=60, export_seconds=60)
            now = [0.]
            out = Path(tempfile.mkdtemp(prefix='eas_', dir=base)); cfg['output'] = str(out)
            def update(*args):
                now[0] += 600
                return {'wall_seconds': 600., 'head_metrics': {}}, None
            with patch.object(run, 'optimize_step', side_effect=update), \
                 patch.object(run, 'checkpoint') as save, patch.object(run, 'export') as export, \
                 patch.object(run.time, 'monotonic', side_effect=lambda: now[0]):
                report = run.run_steps(None, None, None, None, {'pose': 37, 'vqa': 37, 'pointing': 37, 'routing': 37},
                                       out, cfg, {}, torch.device('cpu'),
                                       started=0, distributed=False)
            with self.subTest(flag=flag):
                self.assertEqual(report['stop_reason'], 'budget_or_signal')
                self.assertLess(report['last_step'], 50)
                self.assertEqual(save.call_args.args[-1], report['last_step'])
                if flag:
                    self.assertEqual([c.args[-1] for c in export.call_args_list], [report['last_step']])
                else:
                    export.assert_not_called()
