"""E2E world-4 budgets, policy isolation, row limits and boundary exports."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_run as run, e2e_recipe
from student_pilot.carrier_c1_data import mixed_indices
from student_pilot.carrier_c1_sweep import recipe_for


def config(variant='E2E-1C'):
    return json.loads((Path(__file__).parents[1] / 'configs' / (variant + '.json')).read_text())


class Integrated(unittest.TestCase):
    def test_variants_validate_and_share_no_dormant_variant_keys(self):
        g, c = config('E2E-1G'), config()
        for cfg in (g, c):
            run.validate(cfg)
            self.assertNotIn('tool_mode_flag', json.dumps(cfg))
            self.assertNotIn('6db22ca7', json.dumps(cfg))
            self.assertEqual(cfg['recipe']['global_batch'], 160)
            self.assertEqual(cfg['mdg']['lora_rank'], 32)
            self.assertEqual(cfg['scheduled_sampling']['max_own_probability'], 0.)
            self.assertEqual(cfg['world_size'], 4)
            self.assertEqual(cfg['reference_world_size'], 32)
            self.assertNotIn('geometry_online', cfg)
            self.assertTrue(cfg['recipe']['export_at_stop'])
        self.assertEqual(set(g), set(c))
        self.assertEqual(set(g['mdg']), set(c['mdg']))
        self.assertEqual(g['recipe'], c['recipe'])
        self.assertEqual(g['mdg'], c['mdg'])
        # Stream insertion order assigns sampler RNGs; equal budgets must draw equal rows.
        plans = [list(mixed_indices(dict.fromkeys(cfg['streams'], 1000), 3,
                      training_mode='final', mix=recipe_for(cfg)['mix'], world=4)) for cfg in (g, c)]
        self.assertEqual(plans[0], plans[1])
        # Only routing source/form and policy differ; neither enters optimizer/forward settings.
        self.assertEqual(g['route_table']['object_rel_distance'], 'route')
        self.assertEqual(c['route_table']['object_rel_distance'], 'direct')
        self.assertEqual(g['route_table']['object_rel_direction_easy'], 'direct')
        self.assertEqual(g['route_table']['room_size_estimation'], 'direct')
        self.assertTrue(g['streams']['routing']['path'].endswith('routing_v3122_ground_flagfree/receipt.json'))
        self.assertTrue(c['streams']['routing']['sha256'].startswith('4835444b'))

    def test_exact_shares_atomic_reference_groups_and_world8_same_rows(self):
        cfg = config()
        recipe = recipe_for(cfg)
        expected = dict(pose=8, vqa=16, pointing=4, mdg=4, routing=8)
        self.assertEqual({s: recipe['mix'].count(s) for s in expected}, expected)
        counts = dict.fromkeys(expected, 1000)
        plans = list(mixed_indices(counts, 3, training_mode='final', mix=recipe['mix'], world=4))
        cfg8 = copy.deepcopy(cfg); cfg8['world_size'] = 8
        recipe8 = recipe_for(cfg8)
        other = list(mixed_indices(counts, 3, training_mode='final', mix=recipe8['mix'], world=8))
        flatten = lambda p: [(s, i) for s, ids in p for i in ids]
        self.assertEqual(list(map(flatten, plans)), list(map(flatten, other)))
        groups = list(e2e_recipe.plan_groups(recipe, plans[0]))
        self.assertEqual([len(group) * 4 for group in groups], [32, 32, 32, 16, 16, 32])
        seen = []
        def fetched(rows, stream, indices, model, **kwargs):
            seen.append((stream, len(indices)))
            return [('batch', None, dict(index=i)) for i in indices]
        with mock.patch.object(run, 'fetch_nominal', side_effect=fetched):
            result = list(run.fetch_plan(None, SimpleNamespace(recipe=recipe, training_mode='final'), plans[0], 0))
        self.assertEqual(len(result), 40)
        self.assertEqual(seen, [('pose', 8), ('vqa', 8), ('vqa', 8), ('pointing', 4), ('mdg', 4), ('routing', 8)])
        bad = copy.deepcopy(plans[0]); bad[0] = ('mdg', bad[0][1])
        with self.assertRaises(ValueError):
            list(e2e_recipe.plan_groups(recipe, bad))
        cfg['stream_rows_per_step']['mdg'] = 17
        with self.assertRaises(ValueError):
            recipe_for(cfg)

    def test_route_policy_only_filters_its_question_type(self):
        g, c = config('E2E-1G'), config()
        self.assertTrue(run.routed_type(dict(question_type='object_rel_distance'), g))
        self.assertFalse(run.routed_type(dict(question_type='object_rel_distance'), c))
        for qtype in ('camera_rotation', 'object_size_estimation', 'unknown'):
            self.assertEqual(run.routed_type(dict(question_type=qtype), g),
                             run.routed_type(dict(question_type=qtype), c))
        changed = copy.deepcopy(c)
        changed['route_table']['unused_question_type'] = 'route'
        self.assertEqual(recipe_for(changed), recipe_for(c))
        self.assertEqual(run.routed_type(dict(question_type='camera_rotation'), c),
                         run.routed_type(dict(question_type='camera_rotation'), changed))

    def test_complete_and_suffix_caps_fail_before_forward_without_truncation(self):
        recipe = recipe_for(config())
        model = SimpleNamespace(recipe=recipe)
        batch = dict(input_ids=torch.zeros(1, 10001, dtype=torch.long))
        with self.assertRaisesRegex(ValueError, '10001 tokens exceed 10000'):
            run.check_row(batch, None, 'routing', model)
        self.assertEqual(batch['input_ids'].shape[1], 10001)
        batch = dict(input_ids=torch.zeros(1, 9999, dtype=torch.long), aux_suffix_start=torch.tensor([4000]))
        with self.assertRaisesRegex(ValueError, '5999 routing suffix tokens exceed 5000'):
            run.check_row(batch, None, 'routing', model)

    def test_budget_signal_and_schedule_export_at_leg_end(self):
        import tempfile, os
        root = Path(tempfile.mkdtemp(prefix='e2e_boundary_', dir=os.environ['LANE_TEST_OUTPUT']))
        counts = dict(pose=9, vqa=9, pointing=9)
        cfg = config()
        cfg['gate_stop'] = False
        counts = dict.fromkeys(cfg['streams'], 9)
        with mock.patch.object(run, 'checkpoint'), mock.patch.object(run, 'export_resume_state') as export:
            report = run.run_steps(None, None, None, None, counts, root, cfg, {},
                                   torch.device('cpu'), stop=[True], distributed=False)
        self.assertEqual(report['last_step'], 0)
        self.assertEqual(export.call_args.args[-2], 0)
        root = Path(tempfile.mkdtemp(prefix='e2e_boundary_', dir=os.environ['LANE_TEST_OUTPUT']))
        clock = [0.]
        def update(*args):
            clock[0] += 2000.
            return dict(wall_seconds=2000., head_metrics={}), None
        with mock.patch.object(run.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(run, 'optimize_step', side_effect=update), \
                mock.patch.object(run, 'checkpoint'), mock.patch.object(run, 'export') as export:
            report = run.run_steps(None, None, None, None, counts, root, cfg, {},
                                   torch.device('cpu'), distributed=False)
        self.assertNotIn(report['last_step'], recipe_for(cfg)['milestones'])
        self.assertEqual(export.call_args.args[-1], report['last_step'])

    def test_native_optimizer_runs_all_five_streams_with_half_reference_groups(self):
        from student_pilot.carrier_c1 import parameter_groups
        from tests.test_mdg_features import small_layers
        from tools.e2e_cpu_first_batch import fixture_rows
        cfg = config()
        model, rows = fixture_rows(cfg, bf16=False)
        model.train()
        optimizer = torch.optim.AdamW(parameter_groups(model), weight_decay=.01)
        counts = dict.fromkeys(cfg['streams'], 1000)
        plan = next(mixed_indices(counts, 1, training_mode='final', mix=cfg['recipe']['mix'], world=4))
        with small_layers(), mock.patch.object(run, 'own_values', side_effect=lambda model, rows, batch, audit, *args: (batch, audit)):
            info, _ = run.optimize_step(model, optimizer, rows, plan, 0, torch.device('cpu'), 1)
        self.assertEqual(set(info['stream_means']), set(counts))
        self.assertEqual(len(info['shapes']), 40)
        self.assertFalse(info['skipped_microsteps'])
        self.assertGreater(info['gradient_norms']['mdg_lora'], 0.)
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in info['components'].values()))

    def test_mdg_limit_counts_the_longest_grounding_suffix(self):
        from tests.test_stageb_mdg import fixture
        model, batch, target = fixture()
        model.recipe = recipe_for(config())
        n = 9990
        batch['input_ids'] = torch.cat((batch['input_ids'], torch.zeros(1, n - batch['input_ids'].shape[1], dtype=torch.long)), 1)
        batch['attention_mask'] = torch.ones_like(batch['input_ids'])
        with self.assertRaisesRegex(ValueError, 'MDG prefix-plus-suffix tokens exceed 10000'):
            run.check_row(batch, target, 'mdg', model)
