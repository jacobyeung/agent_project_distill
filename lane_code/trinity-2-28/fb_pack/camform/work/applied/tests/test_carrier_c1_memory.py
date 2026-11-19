"""CPU regressions for the OOM fallbacks; no GPU fit claims."""
from contextlib import ExitStack
from datetime import timedelta
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from student_pilot import carrier_c1_data as data, carrier_c1_run as run, full_ft
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.p3_provenance import file_pin
from tests.test_carrier_c1 import fixture
from tests.test_fsdp import SOCKETS


class PoseRows:
    def __init__(self, placement=data.C1_A):
        _, self.batch, self.target = fixture(4, placement=placement, training_mode='pose_only', depth_enabled=False)
        self.batch['labels'].fill_(-100)

    def get(self, stream, index):
        # Vary microbatches so dropping/duplicating one gradient cannot pass.
        batch = {**self.batch, 'pixel_values_videos': self.batch['pixel_values_videos'] * (1 + index / 10)}
        return batch, self.target, {}


def offload_worker(rank, root):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method='file://' + root + '/rendezvous', rank=rank,
                            world_size=2, timeout=timedelta(seconds=90))
    try:
        rows = PoseRows()
        plans = list(data.mixed_indices({'pose': 9}, 2, training_mode='pose_only'))
        reference = None
        for offload in (False, True):
            model, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
            # A CPU-only torch build cannot pin memory. Keep the actual FSDP
            # CPUOffload path, replacing only this allocator operation.
            with patch.dict(os.environ, C1_FSDP_CPU_OFFLOAD=str(int(offload))), \
                 patch.object(torch.Tensor, 'pin_memory', lambda tensor, *a, **kw: tensor):
                wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
                assert wrapped.cpu_offload.offload_params == offload
                optimizer = torch.optim.AdamW(parameter_groups(wrapped), weight_decay=.01)
                run.optimize_step(wrapped, optimizer, rows, plans[0], rank, torch.device('cpu'), 1, True)
                if not offload:
                    reference = {n: p.detach().clone() for n, p in full_ft.named_trainable(wrapped)}
                else:
                    for n, p in full_ft.named_trainable(wrapped):
                        torch.testing.assert_close(p, reference[n], rtol=0, atol=0)
                    pin = run.checkpoint(Path(root) / 'checkpoint', wrapped, optimizer, {'fixture': True}, 1)
                    run.optimize_step(wrapped, optimizer, rows, plans[1], rank, torch.device('cpu'), 2, True)
                    expected = {n: p.detach().clone() for n, p in full_ft.named_trainable(wrapped)}
                    assert run.restore(pin, wrapped, optimizer, {'fixture': True}) == 1
                    run.optimize_step(wrapped, optimizer, rows, plans[1], rank, torch.device('cpu'), 2, True)
                    for n, p in full_ft.named_trainable(wrapped):
                        torch.testing.assert_close(p, expected[n], rtol=0, atol=0)
                    run.export(Path(root) / 'export', wrapped, model, {'base_identity': 'fixture'}, 2)
                    if rank == 0:
                        fresh, batch, target = fixture(4, training_mode='pose_only', depth_enabled=False)
                        run.load_artifact(fresh, file_pin(Path(root) / 'export/artifact.json'))
                        assert fresh.eval().probe(batch, target)['finite']
    finally:
        dist.destroy_process_group()


class MemoryTests(unittest.TestCase):
    def test_skip_unsupervised_lm_defaults_off_in_both_training_modes(self):
        for mode in ('mixed', 'pose_only'):
            model, batch, target = fixture(4, training_mode=mode, depth_enabled=False)
            self.assertIs(model.skip_unsupervised_lm, False)
            batch['labels'].fill_(-100)
            with patch.object(model.lm_head, 'forward', wraps=model.lm_head.forward) as head:
                model(batch, target)['loss'].backward()
                head.assert_called_once()
            self.assertIsNotNone(model.lm_head.weight.grad)

    def test_skip_lm_preserves_pose_loss_states_gradients_and_updates_for_every_arm(self):
        for placement in data.PLACEMENTS:
            old, batch, target = fixture(4, placement=placement, training_mode='pose_only', depth_enabled=False)
            new, _, _ = fixture(4, placement=placement, training_mode='pose_only', depth_enabled=False)
            old.skip_unsupervised_lm = False
            new.skip_unsupervised_lm = True
            batch['labels'].fill_(-100)
            calls = []
            hook = new.lm_head.register_forward_hook(lambda *args: calls.append(True))
            before = new.lm_head.weight.detach().clone()
            a, b = old(batch, target, return_states=True), new(batch, target, return_states=True)
            self.assertTrue(torch.equal(a['loss'], b['loss']))
            self.assertTrue(torch.equal(a['states'], b['states']))
            a['loss'].backward(); b['loss'].backward()
            self.assertEqual(calls, [])
            hook.remove()
            self.assertIsNone(new.lm_head.weight.grad)
            for (name, p), (_, q) in zip(old.named_parameters(), new.named_parameters()):
                if name == 'lm_head.weight':
                    self.assertEqual(float(p.grad.abs().sum()), 0.)
                elif p.grad is not None:
                    self.assertTrue(torch.equal(p.grad, q.grad), name)
                else:
                    self.assertIsNone(q.grad)
            optimizers = [torch.optim.AdamW(parameter_groups(m), weight_decay=.01) for m in (old, new)]
            for optimizer in optimizers:
                optimizer.step()
            self.assertTrue(torch.equal(before, new.lm_head.weight))
            self.assertFalse(torch.equal(before, old.lm_head.weight))
            self.assertNotIn(new.lm_head.weight, optimizers[1].state)
            for (name, p), (_, q) in zip(old.named_parameters(), new.named_parameters()):
                if name != 'lm_head.weight':
                    self.assertTrue(torch.equal(p, q), name)

    def test_supervised_labels_and_mixed_mode_keep_head_path(self):
        for mode in ('mixed', 'pose_only'):
            model, batch, target = fixture(4, training_mode=mode, depth_enabled=False)
            with patch.object(model.lm_head, 'forward', wraps=model.lm_head.forward) as head:
                model(batch, target)
                head.assert_called_once()
        model, batch, target = fixture(4, training_mode='mixed', depth_enabled=False)
        model.skip_unsupervised_lm = True
        with patch.object(model.lm_head, 'forward', wraps=model.lm_head.forward) as head:
            model(batch, None, stream='vqa')['loss'].backward()
            head.assert_called_once()
            self.assertGreater(float(model.lm_head.weight.grad.norm()), 0)

    def test_cpu_metrics_never_call_cuda(self):
        model, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        plan = next(data.mixed_indices({'pose': 9}, 1, training_mode='pose_only'))
        with ExitStack() as stack:
            probes = [stack.enter_context(patch.object(torch.cuda, name)) for name in (
                'reset_peak_memory_stats', 'memory_allocated', 'memory_reserved',
                'max_memory_allocated', 'max_memory_reserved', 'synchronize')]
            info, _ = run.optimize_step(model, optimizer, PoseRows(), plan, 0, torch.device('cpu'), 1)
        self.assertTrue(all(not probe.called for probe in probes))
        self.assertEqual(len(info['memory']['microbatches']), 4)
        self.assertEqual(info['memory']['after_optimizer_step'], dict(allocated_bytes=0, reserved_bytes=0))
        for micro in info['memory']['microbatches']:
            self.assertEqual(micro['after_forward'], micro['after_backward'])
            self.assertEqual(micro['peak_allocated_bytes'], 0)

    def test_cuda_metrics_reset_each_microbatch_and_keep_step_maximum(self):
        model, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
        optimizer = torch.optim.AdamW(parameter_groups(model))
        plan = next(data.mixed_indices({'pose': 9}, 1, training_mode='pose_only'))
        with patch.object(run, 'move', side_effect=lambda value, device: value), \
             ExitStack() as stack:
            cuda = SimpleNamespace(**{name: stack.enter_context(patch.object(torch.cuda, name)) for name in (
                'reset_peak_memory_stats', 'memory_allocated', 'memory_reserved',
                'max_memory_allocated', 'max_memory_reserved', 'synchronize')})
            cuda.memory_allocated.side_effect = range(10, 19)
            cuda.memory_reserved.side_effect = range(20, 29)
            cuda.max_memory_allocated.side_effect = [50, 40, 30, 20, 25]
            cuda.max_memory_reserved.side_effect = [60, 50, 40, 30, 35]
            native_tensor, native_zeros = torch.tensor, torch.zeros
            def cpu_tensor(*args, **kwargs):
                if torch.device(kwargs.get('device', 'cpu')).type == 'cuda':
                    kwargs['device'] = 'cpu'
                return native_tensor(*args, **kwargs)
            def cpu_zeros(*args, **kwargs):
                if torch.device(kwargs.get('device', 'cpu')).type == 'cuda':
                    kwargs['device'] = 'cpu'
                return native_zeros(*args, **kwargs)
            with patch.object(torch, 'tensor', side_effect=cpu_tensor), patch.object(torch, 'zeros', side_effect=cpu_zeros):
                info, _ = run.optimize_step(model, optimizer, PoseRows(), plan, 0, torch.device('cuda'), 1)
        self.assertEqual(cuda.reset_peak_memory_stats.call_count, 4)
        self.assertEqual(info['peak_allocated_bytes'], 50)
        self.assertEqual(info['peak_reserved_bytes'], 60)
        self.assertEqual(info['memory']['microbatches'][0]['after_forward']['allocated_bytes'], 10)
        self.assertEqual(info['memory']['microbatches'][0]['after_backward']['allocated_bytes'], 11)
        self.assertEqual(info['memory']['after_optimizer_step']['allocated_bytes'], 18)

    def test_offload_env_validation_and_wrapper_forwarding(self):
        from torch.distributed.fsdp import MixedPrecision
        model, _, _ = fixture(4)
        for value in ('0', '1'):
            wrapped = SimpleNamespace(mixed_precision=MixedPrecision())
            with patch.dict(os.environ, C1_FSDP_CPU_OFFLOAD=value), \
                 patch.object(full_ft, 'wrap_full_model', return_value=wrapped) as wrapper:
                run.wrap_model(model, torch.device('cpu'))
            self.assertEqual(wrapper.call_args.kwargs['cpu_offload'], value == '1')
        with patch.dict(os.environ, C1_FSDP_CPU_OFFLOAD='yes'), self.assertRaisesRegex(ValueError, 'must be 0 or 1'):
            run.wrap_model(model, torch.device('cpu'))

    def test_full_wrapper_passes_cpuoffload_and_preserves_sharding_policy(self):
        from torch.distributed.fsdp import ShardingStrategy
        model, _, _ = fixture(4)
        for offload in (False, True):
            with patch('torch.distributed.fsdp.FullyShardedDataParallel') as fsdp, patch.object(dist, 'broadcast'):
                full_ft.wrap_full_model(model, list(model.auxiliary_heads.parameters()), None,
                                       torch.device('cpu'), cpu_offload=offload)
            options = fsdp.call_args.kwargs
            self.assertEqual(options['sharding_strategy'], ShardingStrategy.FULL_SHARD)
            self.assertTrue(options['use_orig_params'])
            self.assertTrue(options['limit_all_gathers'])
            self.assertEqual(options['cpu_offload'].offload_params if offload else options['cpu_offload'],
                             True if offload else None)

    def test_cpu_accumulation_and_checkpoint_resume_without_sockets(self):
        root = Path(tempfile.mkdtemp(prefix='c1_offload_local_', dir=os.environ['LANE_TEST_OUTPUT']))
        rows = PoseRows()
        plans = list(data.mixed_indices({'pose': 9}, 2, training_mode='pose_only'))
        reference, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
        model, _, _ = fixture(4, training_mode='pose_only', depth_enabled=False)
        model.c1_cpu_offload = True
        optimizer = torch.optim.AdamW(parameter_groups(model))
        ref_optimizer = torch.optim.AdamW(parameter_groups(reference))
        run.optimize_step(reference, ref_optimizer, rows, plans[0], 0, torch.device('cpu'), 1)
        run.optimize_step(model, optimizer, rows, plans[0], 0, torch.device('cpu'), 1)
        for (name, p), (_, q) in zip(model.named_parameters(), reference.named_parameters()):
            self.assertTrue(torch.equal(p, q), name)
        def gather(out, value, *args, **kwargs):
            out[0] = value
        with patch.object(dist, 'get_rank', return_value=0), patch.object(dist, 'get_world_size', return_value=1), \
             patch.object(dist, 'barrier'), patch.object(dist, 'all_gather_object', side_effect=gather), \
             patch.object(dist, 'broadcast'), patch.object(dist, 'broadcast_object_list'), \
             patch.object(dist, 'get_backend', return_value='gloo'):
            pin = run.checkpoint(root / 'checkpoint', model, optimizer, {'fixture': True}, 1)
            run.optimize_step(model, optimizer, rows, plans[1], 0, torch.device('cpu'), 2)
            expected = {n: p.detach().clone() for n, p in full_ft.named_trainable(model)}
            self.assertEqual(run.restore(pin, model, optimizer, {'fixture': True}), 1)
            run.optimize_step(model, optimizer, rows, plans[1], 0, torch.device('cpu'), 2)
            for n, p in full_ft.named_trainable(model):
                self.assertTrue(torch.equal(p, expected[n]), n)
            with patch('student_pilot.fsdp_training.publication_state', return_value=model.state_dict()):
                run.export(root / 'export', model, model, {'base_identity': 'fixture'}, 2)
        fresh, batch, target = fixture(4, training_mode='pose_only', depth_enabled=False)
        run.load_artifact(fresh, file_pin(root / 'export/artifact.json'))
        self.assertTrue(fresh.eval().probe(batch, target)['finite'])

    def test_nccl_norm_stages_only_scalar_for_cpu_shards(self):
        parameter = torch.nn.Parameter(torch.ones(3))
        parameter.grad = torch.tensor([3., 4., 0.])
        original_to = torch.Tensor.to
        transfers = []
        def to(tensor, *args, **kwargs):
            if args and isinstance(args[0], torch.device) and args[0].type == 'cuda':
                transfers.append(tensor.numel())
                return tensor.clone()
            return original_to(tensor, *args, **kwargs)
        with patch.object(dist, 'get_backend', return_value='nccl'), \
             patch.object(torch.cuda, 'current_device', return_value=0), \
             patch.object(torch.Tensor, 'to', to), \
             patch.object(dist, 'all_reduce', side_effect=lambda tensor, **kw: tensor.mul_(4)):
            self.assertEqual(float(full_ft.clip_sharded([parameter], 1.)), 10.)
        self.assertEqual(transfers, [1])
        torch.testing.assert_close(parameter.grad, torch.tensor([.3, .4, 0.]))

    @unittest.skipUnless(SOCKETS, 'Local sockets unavailable; parent CPU job must run Gloo')
    def test_offload_gloo_accumulation_resume_export(self):
        root = tempfile.mkdtemp(prefix='c1_offload_', dir=os.environ['LANE_TEST_OUTPUT'])
        mp.start_processes(offload_worker, args=(root,), nprocs=2, join=True, start_method='fork')
