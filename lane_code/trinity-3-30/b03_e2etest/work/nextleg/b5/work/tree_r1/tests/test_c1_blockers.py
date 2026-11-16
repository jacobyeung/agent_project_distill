"""CPU regressions for checkpoint transport, readouts and allocation boundaries."""
import copy
from contextlib import ExitStack, contextmanager
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import carrier_c1_run as run, carrier_c1_data as data, full_ft
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_sweep import capped_steps, recipe_for
from student_pilot.decoupled_resume import rng_state, restore_rng
from student_pilot.p3_provenance import file_pin
from tests.test_carrier_c1 import fixture, Tokenizer
from tests import test_carrier_c1_clip


@contextmanager
def transport(backend='gloo'):
    """No sockets or CUDA: emulate collective placement, retaining real tensors."""
    original_to = torch.Tensor.to
    transfers = []

    class DeviceTensor:
        is_cuda = True

        def __init__(self, value):
            self.value = value.clone()

        def cpu(self):
            return self.value

    def move(value, *args, **kwargs):
        device = kwargs.get('device', args[0] if args else None)
        if isinstance(device, (str, torch.device)) and torch.device(device).type == 'cuda':
            assert torch.device(device) == torch.device('cuda', 3)
            transfers.append(value.clone())
            return DeviceTensor(value)
        return original_to(value, *args, **kwargs)

    def broadcast(value, src, group=None):
        if backend == 'nccl' and not value.is_cuda:
            raise RuntimeError('NCCL cannot broadcast CPU tensors')

    def gather(out, value, **kwargs):
        out[0] = value

    with ExitStack() as stack:
        for name, replacement in (
            ('get_rank', lambda: 0), ('get_world_size', lambda: 1),
            ('get_backend', lambda group=None: backend), ('barrier', lambda: None),
            ('all_gather_object', gather), ('broadcast', broadcast),
            ('broadcast_object_list', lambda *a, **k: None)):
            stack.enter_context(patch.object(run.dist, name, replacement))
        stack.enter_context(patch.object(torch.cuda, 'current_device', return_value=3))
        stack.enter_context(patch.object(torch.Tensor, 'to', move))
        yield transfers


class BlockerTests(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix='b34_', dir=os.environ['LANE_TEST_OUTPUT']))

    def test_restore_cpu_adam_steps_with_gloo_and_nccl_transport(self):
        for backend in ('gloo', 'nccl'):
            with self.subTest(backend=backend), transport(backend) as transfers:
                root = self.root()
                model, batch, target = fixture(4, training_mode='pose_only', depth_enabled=False)
                optimizer = torch.optim.AdamW(parameter_groups(model))
                rows = SimpleNamespace(get=lambda *a: (batch, target, {}))
                plans = list(data.mixed_indices({'pose': 3}, 2, training_mode='pose_only'))
                run.optimize_step(model, optimizer, rows, plans[0], 0, torch.device('cpu'), 1)
                pin = run.checkpoint(root/'checkpoint', model, optimizer, {'fixture': 1}, 1)
                run.optimize_step(model, optimizer, rows, plans[1], 0, torch.device('cpu'), 2)
                expected = copy.deepcopy(model.state_dict())
                self.assertEqual(run.restore(pin, model, optimizer, {'fixture': 1}), 1)
                self.assertTrue(all(s['step'].device.type == 'cpu' and s['step'].item() == 1
                                    for s in optimizer.state.values()))
                run.optimize_step(model, optimizer, rows, plans[1], 0, torch.device('cpu'), 2)
                for name, value in model.state_dict().items():
                    torch.testing.assert_close(value, expected[name], rtol=0, atol=0)
                if backend == 'nccl':
                    self.assertTrue(any(v.ndim == 0 for v in transfers))

    def test_pose_only_sparse_readout_with_optional_depth(self):
        from student_pilot import all_frame_readout as scoring
        for depth in (False, True):
            model, batch, _ = fixture(training_mode='pose_only', depth_enabled=depth)
            for slots in (16, 32):
                values = model.readout(batch, np.zeros((slots, 2, 2)))
                self.assertEqual(np.shape(values['raw_pose']), (32, 9))
                self.assertIsNone(values['gravity_up'])
                self.assertIsNone(values['trajectory_step_m'])
                self.assertEqual(values['point_depth'] is not None, depth)
                if depth:
                    self.assertEqual(len(values['point_depth']), slots)
                camera = np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.], (32,1))
                camera[:,0] = np.linspace(0,1,32)
                record = dict(dataset='d',scene='s',gt=dict(camera=camera,camera_mask=np.ones(32,bool),
                    gravity=[0.,-1.,0.],gravity_mask=True),pred=dict(camera=values['raw_pose'],
                    gravity=values['gravity_up'],trajectory_step_m=values['trajectory_step_m']))
                with self.assertRaisesRegex(ValueError, 'no authenticated R2 bank adapter'):
                    scoring.evaluate([record], {'pose'}, [('d','s')], [])
                with_gravity = copy.deepcopy(record)
                with_gravity['pred']['gravity'] = [0.,-1.,0.]
                with self.assertRaisesRegex(ValueError, 'no authenticated R2 bank adapter'):
                    scoring.evaluate([with_gravity], {'pose','gravity'}, [('d','s')], [])

    def test_cpu_counter_receiver_copies_back_and_honors_selected_group(self):
        group = object()
        for backend in ('gloo', 'nccl'):
            counter = torch.tensor(0.)
            def receive(wire, src, group):
                (wire.cpu() if wire.is_cuda else wire).fill_(37)
            with transport(backend), patch.object(run.dist, 'broadcast', side_effect=receive) as broadcast:
                full_ft._broadcast(counter, group)
                self.assertIs(broadcast.call_args.kwargs['group'], group)
                self.assertEqual(counter.item(), 37)
                self.assertEqual(counter.device.type, 'cpu')

    def test_built_clips_reach_native_encoder_with_stable_unique_qids(self):
        from student_pilot import carrier_c1_clip as clip
        _, cfg, _ = test_carrier_c1_clip.ClipTests().fixture()
        document = clip.build_clips(cfg)
        _, batch, _ = fixture()
        keep = batch['input_ids'][0] != 5
        raw = {k: (v[:, keep] if k in ('input_ids', 'labels', 'attention_mask', 'mm_token_type_ids') else v)
               for k, v in batch.items() if not k.startswith('aux_')}
        processor = SimpleNamespace(tokenizer=Tokenizer(), video_processor=SimpleNamespace(merge_size=2))
        ids = []
        for row in document['clips']:
            # Only pixel loading/tokenization are fixtures; both native row encoders run.
            with patch('student_pilot.diagnostic_data.rgb_arrays',
                       return_value=(row['student_input'], [], [[4, 4]]*32, None)), \
                 patch('student_pilot.batches.encode_arrays', return_value=(raw, {})):
                encoded, _, audit = data.encode(processor, {**row, 'target': data.READOUT_TARGET}, {}, 'vqa')
            ids.append(audit['qid'])
            self.assertEqual(int((encoded['aux_camera_positions'] >= 0).sum()), 32)
        self.assertEqual(len(set(ids)), 38)
        cfg['output'] = str(Path(cfg['output']).with_name('clips_again.json'))
        self.assertEqual(ids, [r['qid'] for r in clip.build_clips(cfg)['clips']])

    def test_allocation_resume_across_m200_keeps_model_optimizer_rng_and_schedule(self):
        cfg = dict(training_mode='pose_only', depth_enabled=False, base_identity='fixture',
                   schedule=dict(startup_seconds=0, p95_step_seconds=1,
                                 checkpoint_seconds=10, export_seconds=10))
        recipe = recipe_for(cfg)
        self.assertEqual(recipe['steps'], 800)
        self.assertEqual(recipe['milestones'], [100, 200, 400, 800])
        root = self.root()
        reference, batch, target = fixture(4, training_mode='pose_only', depth_enabled=False)
        reference.recipe = recipe
        rows = SimpleNamespace(get=lambda *a: (batch, target, {}))
        optimizer = torch.optim.AdamW(parameter_groups(reference))
        initial_model = copy.deepcopy(reference.state_dict())
        initial_rng = rng_state()
        bound = dict(config_sha256=run.identity(cfg))
        exports = []
        native_export = run.export

        def publish(directory, wrapped, model, config, step):
            exports.append(step)
            native_export(directory, wrapped, model, config, step)

        (root/'reference').mkdir(); (root/'resumed').mkdir()
        for output in (root/'reference', root/'resumed'):
            run.bind_output(output, bound)
        with transport(), patch.object(run.time, 'monotonic', return_value=0), \
             patch.object(run, 'export', side_effect=publish), \
             patch('student_pilot.fsdp_training.publication_state', side_effect=lambda model: model.state_dict()):
            # 25 seconds fit steps 198..202, one final save and the m200 export.
            expected_report = run.run_steps(reference, reference, optimizer, rows, {'pose': 37},
                root/'reference', cfg, bound, torch.device('cpu'), start_step=197,
                started=-13475, distributed=False)
            self.assertEqual(expected_report['last_step'], 202)
            expected_optimizer = copy.deepcopy(optimizer.state_dict())
            expected_rng = rng_state()
            resumed, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
            resumed.recipe = recipe
            resumed.load_state_dict(initial_model)
            opt = torch.optim.AdamW(parameter_groups(resumed))
            restore_rng(initial_rng)
            first = run.run_steps(resumed, resumed, opt, rows, {'pose': 37}, root/'resumed', cfg, bound,
                torch.device('cpu'), start_step=197, started=-13478, distributed=False)
            self.assertEqual(first['last_step'], 199)
            self.assertTrue(first['stopped_for_resume'])
            random.random(); np.random.rand(); torch.rand(7)
            start = run.restore(run.latest_resume(root/'resumed', bound), resumed, opt, bound)
            with patch.dict(os.environ, SLURM_JOB_ID='2'):
                second = run.run_steps(resumed, resumed, opt, rows, {'pose': 37}, root/'resumed', cfg, bound,
                    torch.device('cpu'), start_step=start, started=-13477, distributed=False)
            self.assertEqual(second['last_step'], 202)
            self.assertEqual(exports, [200, 200])
            for name, value in resumed.state_dict().items():
                torch.testing.assert_close(value, reference.state_dict()[name], rtol=0, atol=0)
            actual_optimizer = opt.state_dict()
            self.assertEqual(actual_optimizer['param_groups'], expected_optimizer['param_groups'])
            for key, state in actual_optimizer['state'].items():
                for field, value in state.items():
                    torch.testing.assert_close(value, expected_optimizer['state'][key][field], rtol=0, atol=0)
            actual_rng = rng_state()
            self.assertEqual(actual_rng['python'], expected_rng['python'])
            np.testing.assert_array_equal(actual_rng['numpy'][1], expected_rng['numpy'][1])
            torch.testing.assert_close(actual_rng['torch'], expected_rng['torch'], rtol=0, atol=0)

    def test_allocations_reach_all_gates_without_repeating_dense_rows(self):
        cfg = dict(training_mode='pose_only', depth_enabled=False, schedule=dict(
            startup_seconds=1800, p95_step_seconds=60, checkpoint_seconds=300, export_seconds=600))
        self.assertEqual(recipe_for(cfg)['steps'], 800)
        self.assertEqual(capped_steps(cfg['schedule']), 155)
        root = self.root(); start = 0; plans = []; saves = []; exports = []; ends = []
        def update(model, optimizer, rows, plan, rank, device, step, distributed, gates=None):
            plans.append(plan)
            return {'wall_seconds': 60.}, None
        with patch.object(run, 'optimize_step', side_effect=update), \
             patch.object(run, 'checkpoint', side_effect=lambda *a, **kw: saves.append(a[-1])), \
             patch.object(run, 'export', side_effect=lambda *a: exports.append(a[-1])), \
             patch.object(run.time, 'monotonic', return_value=0):
            for attempt in range(10):
                with patch.dict(os.environ, SLURM_JOB_ID=str(attempt)):
                    report = run.run_steps(None, None, None, None, {'pose': 37}, root, cfg, {},
                        torch.device('cpu'), start_step=start, distributed=False)
                self.assertGreater(report['last_step'], start)
                start = report['last_step']; ends.append(start)
                self.assertIn(start, saves)
                if start == 400:
                    self.assertEqual(report['stop_reason'], 'm400_gate')
                if start == 800:
                    self.assertFalse(report['stopped_for_resume'])
                    break
        self.assertEqual(start, 800)
        self.assertGreater(len(ends), 4)
        self.assertEqual(exports, [100, 200, 400, 800])
        self.assertEqual(plans, list(data.mixed_indices({'pose': 37}, 800, training_mode='pose_only')))

    def test_budget_overrun_signal_and_exhausted_start_save_cleanly(self):
        cfg = dict(training_mode='pose_only', depth_enabled=False, schedule=dict(
            startup_seconds=0, p95_step_seconds=60, checkpoint_seconds=300, export_seconds=600))
        for reason in ('overrun', 'signal', 'startup'):
            root = self.root(); stop = [False]; now = [13499. if reason == 'startup' else 0.]
            def update(*args):
                now[0] += 5000 if reason == 'overrun' else 60
                stop[0] = reason == 'signal'
                return {'wall_seconds': 5000. if reason == 'overrun' else 60.}, None
            with patch.object(run, 'optimize_step', side_effect=update), \
                 patch.object(run, 'checkpoint') as save, patch.object(run, 'export') as export, \
                 patch.object(run.time, 'monotonic', side_effect=lambda: now[0]):
                report = run.run_steps(None, None, None, None, {'pose': 37}, root, cfg, {},
                    torch.device('cpu'), started=0, stop=stop, distributed=False)
            self.assertEqual(report['last_step'], {'overrun': 2, 'signal': 1, 'startup': 0}[reason])
            self.assertEqual(save.call_args.args[-1], report['last_step'])
            self.assertEqual(report['stop_reason'], 'budget_or_signal')
            self.assertTrue(report['stopped_for_resume'])
            self.assertLess(now[0]+cfg['schedule']['checkpoint_seconds'], 14400)
            export.assert_not_called()

    def test_ranks_agree_on_shortest_allocation_before_updates(self):
        cfg = dict(training_mode='pose_only', depth_enabled=False, schedule=dict(
            startup_seconds=1800, p95_step_seconds=60, checkpoint_seconds=300, export_seconds=600))
        def reduce(value, op):
            if op == run.dist.ReduceOp.MIN:
                value.fill_(140)
        with transport(), patch.object(run.dist, 'all_reduce', side_effect=reduce), \
             patch.object(run, 'optimize_step', return_value=({'wall_seconds': 60.}, None)), \
             patch.object(run, 'checkpoint') as save, patch.object(run, 'export'), \
             patch.object(run.time, 'monotonic', return_value=0):
            report = run.run_steps(None, None, None, None, {'pose': 37}, self.root(), cfg, {},
                                  torch.device('cpu'), distributed=True)
        self.assertEqual(report['last_step'], 140)
        self.assertEqual(save.call_args.args[-1], 140)
        self.assertEqual(report['stop_reason'], 'budget_or_signal')

    def test_exhausted_resume_saves_the_same_step_under_each_attempt(self):
        cfg = dict(training_mode='pose_only', depth_enabled=False, schedule=dict(
            startup_seconds=0, p95_step_seconds=60, checkpoint_seconds=300, export_seconds=600))
        root = self.root()
        model, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        run.bind_output(root, {})
        with transport(), patch.object(run, 'optimize_step', side_effect=AssertionError('No budget for an update')), \
             patch.object(run, 'checkpoint', wraps=run.checkpoint) as save, \
             patch.object(run.time, 'monotonic', return_value=13499):
            for attempt in ('1', '2'):
                with patch.dict(os.environ, SLURM_JOB_ID=attempt):
                    report = run.run_steps(model, model, optimizer, None, {'pose': 37}, root, cfg, {},
                        torch.device('cpu'), start_step=199, started=0, distributed=False)
                self.assertEqual(report['last_step'], 199)
                self.assertEqual(report['steps'], [])
                self.assertTrue(report['stopped_for_resume'])
        self.assertEqual(len(run.complete_states(root, {})), 2)
        self.assertEqual(save.call_count, 2)
        self.assertTrue(all(call.kwargs == {'rotate': True} for call in save.call_args_list))


if __name__ == '__main__':
    unittest.main()
