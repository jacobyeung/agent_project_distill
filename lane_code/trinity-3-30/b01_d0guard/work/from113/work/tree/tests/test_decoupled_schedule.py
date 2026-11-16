"""Fixed recipe admission and full-loop schedule endpoints on CPU stand-ins."""
import copy
from contextlib import ExitStack, nullcontext
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import Mock, patch

import torch

from student_pilot import decoupled_v_run as run
from student_pilot.decoupled_v import RECIPE, learning_rate
from student_pilot.decoupled_vc import VC_RECIPE, VC_BATCH4H_RECIPE


def config(recipe=VC_BATCH4H_RECIPE):
    return dict(schema='decoupled-v-run-v1', mode='decoupled_vc', recipe=copy.deepcopy(recipe),
                base_identity='fixture', init_heads=None, preparation=None, admission=None)


class ScheduleTests(unittest.TestCase):
    def test_only_explicit_recipes_and_identity(self):
        for recipe in (VC_RECIPE, VC_BATCH4H_RECIPE):
            run.validate(config(recipe))
        cfg = config()
        self.assertNotEqual(run.identity(cfg), run.identity(config(VC_RECIPE)))
        self.assertEqual(VC_RECIPE['steps'], 1600)
        self.assertEqual(RECIPE['milestones'], [200, 400, 800, 1600])
        for key, value in [('steps', 1250), ('warmup_ratio', .04), ('learning_rate', .001),
                           ('milestones', [200, 400, 800, 1600])]:
            bad = copy.deepcopy(cfg); bad['recipe'][key] = value
            self.assertNotEqual(run.identity(bad), run.identity(cfg))
            with self.assertRaisesRegex(ValueError, 'fixed recipe'):
                run.validate(bad)
        with self.assertRaisesRegex(ValueError, 'fixed recipe'):
            run.validate({**cfg, 'mode': 'decoupled_v'})
        with self.assertRaisesRegex(ValueError, 'fresh head'):
            run.validate({**cfg, 'init_heads': 'old'})

    def test_budget_and_both_cosines_finish(self):
        recipe = VC_BATCH4H_RECIPE
        self.assertLessEqual(recipe['steps']*10.5+240+120, .9*4*3600)
        self.assertEqual(math.ceil(recipe['steps']*recipe['warmup_ratio']), 36)
        for lr in (recipe['learning_rate'], recipe['encoder_learning_rate']):
            group = {**recipe, 'learning_rate': lr}
            self.assertAlmostEqual(learning_rate(1, group), lr/36)
            self.assertEqual(learning_rate(36, group), lr)
            self.assertGreater(learning_rate(1199, group), 0)
            self.assertEqual(learning_rate(1200, group), 0)

    def test_full_loop_stops_and_exports_selected_recipe(self):
        # Exercise the real 1200-iteration control flow; stand-ins replace only
        # RGB/model IO, model math and CUDA/DDP, with no checkpoint files.
        class Tiny(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.auxiliary_heads = torch.nn.Linear(1, 1, bias=False)
                self.model = torch.nn.Module()
                self.model.visual = torch.nn.Linear(1, 1, bias=False)
                self.config = SimpleNamespace(p3={'feature_backing': 'decoupled_vc'})

            def to(self, *args, **kwargs):
                return self

            def forward(self, *args):
                return self.auxiliary_heads.weight.square() + self.model.visual.weight.square()

        class Wrapped:
            def __init__(self, model, **kwargs): self.model = model
            def __call__(self, *args): return self.model(*args)
            def no_sync(self): return nullcontext()

        cfg = config()
        cfg['output'] = str(Path(os.environ['LANE_TEST_OUTPUT'])/uuid.uuid4().hex)
        receipt = dict(count=64, settings={}, model={}, database={'path': '/unused'})
        connection = Mock()
        connection.execute.return_value.fetchone.return_value = ('{}', '{}')
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, RANK='0', WORLD_SIZE='8', LOCAL_RANK='0',
                                          SLURM_JOB_ID='fixture', STAGE1_TRAINER_COMMIT='a'*40))
            stack.enter_context(patch.object(run, 'prepared', return_value=(receipt, {'root': '/unused'})))
            stack.enter_context(patch.object(run, 'load_vision', return_value=Tiny()))
            stack.enter_context(patch.object(run, 'processor_for', return_value=None))
            stack.enter_context(patch.object(run, 'row_workers', return_value=1))
            stack.enter_context(patch.object(run, 'encode', return_value={}))
            stack.enter_context(patch.object(run, 'target_tensors', return_value={}))
            stack.enter_context(patch.object(run.sqlite3, 'connect', return_value=connection))
            stack.enter_context(patch('torch.nn.parallel.DistributedDataParallel', Wrapped))
            stack.enter_context(patch.object(torch.cuda, 'set_device'))
            for name in ('init_process_group', 'destroy_process_group', 'barrier', 'all_reduce'):
                stack.enter_context(patch('torch.distributed.'+name))
            exported = stack.enter_context(patch.object(run, 'export_heads'))
            saved = stack.enter_context(patch.object(run.resume_state, 'save',
                side_effect=lambda output, step, model, optimizer, bound, export: export(output/f'step_{step}')))
            stack.enter_context(patch.object(run.resume_state, 'final_export',
                side_effect=lambda output, step, export: export(output/f'step_{step}')))
            run.train(cfg)
        self.assertEqual([call.args[1] for call in saved.call_args_list], [200, 400, 800])
        records = [json.loads(line) for line in (Path(cfg['output'])/'train/metrics.jsonl').read_text().splitlines()]
        self.assertEqual(len(records), 1200)
        self.assertEqual([call.args[2] for call in exported.call_args_list], [200, 400, 800, 1200])
        for call in exported.call_args_list:
            self.assertEqual(call.args[3]['recipe'], VC_BATCH4H_RECIPE)
            self.assertEqual(call.args[3]['config_sha256'], run.identity(cfg))
        for record in records:
            self.assertEqual(record['lr'], learning_rate(record['step'], VC_BATCH4H_RECIPE))
            self.assertEqual(record['lr'], record['group_lrs']['heads'])
        self.assertEqual(records[-1]['group_lrs'], {'heads': 0., 'encoder_copy': 0.})
        connection.close.assert_called_once()
