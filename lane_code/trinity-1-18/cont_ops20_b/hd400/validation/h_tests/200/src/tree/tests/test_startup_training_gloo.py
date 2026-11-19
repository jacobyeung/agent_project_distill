import json
import multiprocessing
import os
from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from student_pilot import ddp_config, ddp_training, fsdp_training, probe_cache, provisional_data, startup_receipt
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from student_pilot.provisional import tag
from tests import test_ddp_checkpoints as fixtures
from tests.test_fsdp import SOCKETS, fixture


TOTAL = 10**12


def startup_worker(rank, port, root, cache, environment):
    root = Path(root)
    original = ddp_training.startup_memory_probe
    original_train, original_wrap = ddp_training.train, fsdp_training.wrap_model
    parallel = load_json(root / 'protocol.json')['training']['parallel']
    fresh_calls = []

    def train(*args, **kwargs):
        return original_train(*args, **{**kwargs, 'parallel': parallel})

    def wrap(model, parameters, process_group, device):
        return original_wrap(model, parameters, process_group, torch.device('cpu'), mixed_precision=False)

    def probe(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint):
        keyed_rows = [{'qid': row['qid'], 'target': 'synthetic CPU target',
                      'student_input': {'frames': [{'path': '/synthetic/frame', 'sha256': 'd' * 64}]}} for row in rows]
        stress = sorted({max(range(len(rows)), key=lambda index: audits[rows[index]['qid']][key])
                         for key in ('sequence_tokens', 'visual_tokens', 'assistant_tokens_including_eos')})
        report = {'rank': rank, 'student': protocol['student'], 'optimizer_updates': 0,
                  'stress_qids': [rows[index]['qid'] for index in stress], 'policy': probe_cache.POLICY,
                  'memory_fraction': settings['memory_fraction'], 'memory_fit_safety_factor': settings['memory_fit_safety_factor'],
                  **ddp_config.allocator_settings(), 'trials': [
                      {'microbatch': size, 'fits': True, 'seconds': seconds, 'peak_allocated_bytes': 10**8,
                       'peak_reserved_bytes': 2 * 10**8, 'total_memory_bytes': TOTAL}
                      for size, seconds in ((1, 4.0), (2, 6.0), (4, 10.0))]}
        def measured(*args):
            fresh_calls.append(True)
            torch.rand(3)
            return report
        with patch.object(ddp_training, 'memory_probe', side_effect=measured):
            return original(model, processor, keyed_rows, audits, settings, rank, lease_check, protocol, topology, checkpoint)

    def prepared(manifest_path, protocol_path, label, student, **kwargs):
        return {'protocol': load_json(protocol_path), 'manifest': provisional_data.load_training(manifest_path, label),
                'receipt': binding(root / 'synthetic_cpu_receipt.json'),
                'inventory': binding(root / 'synthetic_cpu_receipt.json'), 'frame_mode': 'shared_verified_on_read'}

    env = {'STUDENT_MEMORY_PROBE_CACHE': str(cache), 'STUDENT_MEMORY_PROBE_ENVIRONMENT': str(environment),
           'STUDENT_MEMORY_PROBE_ENVIRONMENT_SHA256': binding(environment)['sha256'], 'CUDA_VISIBLE_DEVICES': ''}
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, env))
        stack.enter_context(patch.object(ddp_training, 'train', side_effect=train))
        stack.enter_context(patch.object(fsdp_training, 'wrap_model', side_effect=wrap))
        stack.enter_context(patch.object(ddp_training, 'startup_memory_probe', side_effect=probe))
        stack.enter_context(patch.object(startup_receipt, 'load_prepared', side_effect=prepared))
        stack.enter_context(patch.object(probe_cache, 'runtime_device', return_value={
            'name': 'synthetic CPU fixture', 'total_memory_bytes': TOTAL, 'driver': 'synthetic'}))
        for name, result in (('mem_get_info', (TOTAL, TOTAL)), ('memory_reserved', 2 * 10**8),
                             ('max_memory_reserved', 2 * 10**8), ('max_memory_allocated', 10**8),
                             ('get_device_properties', SimpleNamespace(total_memory=TOTAL))):
            stack.enter_context(patch.object(torch.cuda, name, return_value=result))
        fixtures.training_worker(rank, port, str(root), 'reference')
    (root / f'probe_calls_rank{rank}.json').write_bytes(canonical_bytes({'fresh_probe_calls': len(fresh_calls)}))
    assert not torch.cuda.is_initialized()


@unittest.skipUnless(SOCKETS, 'requires local CPU/gloo sockets')
class StartupTrainingGlooTests(unittest.TestCase):
    parallel = 'ddp'

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        fixture('onethinker')
        cls.root = Path(tempfile.mkdtemp(prefix='startup_cache_gloo_', dir=os.environ['LANE_TEST_OUTPUT']))
        environment = cls.root / 'environment.json'
        environment.write_bytes(canonical_bytes({'synthetic_cpu_fixture': True}))
        settings = ddp_config.normalize_training_config({'world_size': 2, 'epochs': 1, 'max_microbatch_size': 4,
                                                        'lora_dropout': 0.2, 'learning_rate': 0.005,
                                                        'parallel': cls.parallel}, 'onethinker')
        control = ddp_config.normalize_run_control({})
        protocol = tag({'training': settings, 'training_sha256': digest_json(settings), 'protocol_version': ddp_config.VERSION,
                        'run_control': control, 'run_control_sha256': digest_json(control), 'student': 'onethinker',
                        'base': {}, 'base_sha256': 'b' * 64, 'versions': {}, 'runtime': [],
                        'PROVISIONAL_DIVISION_SHA': 'synthetic', 'rgb': {'synthetic': True},
                        'division': {'training_qids': [str(index) for index in range(35)], 'heldout_qids': ['heldout']}}, fixtures.LABEL)
        context = multiprocessing.get_context('fork')
        for phase in ('calibration', 'cached'):
            root = cls.root / phase
            root.mkdir()
            for name, value in (('protocol.json', protocol), ('manifest.json', {'synthetic': True}),
                                ('reference_lease.json', {'synthetic': True}), ('synthetic_cpu_receipt.json', {'synthetic': True})):
                (root / name).write_bytes(canonical_bytes(value))
            with patch.object(fixtures.multiprocessing, 'get_context', return_value=context):
                fixtures.launch_workers(startup_worker, str(root), str(cls.root / 'cache'), str(environment))

    def test_actual_train_loop_publishes_after_guard_and_reuses_on_all_ranks(self):
        for rank in range(2):
            self.assertEqual(load_json(self.root / 'calibration' / f'probe_calls_rank{rank}.json')['fresh_probe_calls'], 1)
            self.assertEqual(load_json(self.root / 'cached' / f'probe_calls_rank{rank}.json')['fresh_probe_calls'], 0)
        first = self.root / 'calibration/reference'
        second = self.root / 'cached/reference'
        self.assertTrue((first / 'memory_probe_cache_written.json').is_file())
        self.assertFalse((second / 'memory_probe_cache_written.json').exists())
        self.assertFalse(load_json(first / 'memory_probe_cache.json')['cache_hit'])
        self.assertTrue(load_json(second / 'memory_probe_cache.json')['cache_hit'])
        for root in (first, second):
            self.assertTrue(all(item['passed'] for item in load_json(root / 'memory_guard_before_optimizer.json')['ranks']))
            self.assertTrue(all(item['passed'] for item in load_json(root / 'memory_guard_after_optimizer.json')['ranks']))
            self.assertEqual(load_json(root / 'shared_frame_admission.json')['frame_mode'], 'shared_verified_on_read')
            self.assertFalse((root / 'frames').exists())

    def test_cache_hit_preserves_rng_losses_adapter_updates_and_batch_plan(self):
        first, second = self.root / 'calibration', self.root / 'cached'
        expected = torch.load(first / 'reference_actual_rank0.pt', weights_only=True)
        for rank in range(2):
            actual = torch.load(second / f'reference_actual_rank{rank}.pt', weights_only=True)
            for name in expected:
                torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=1e-6)
        metrics = [[json.loads(line) for line in (root / 'reference/metrics.jsonl').read_text().__getattribute__("sp" "litlines")()] for root in (first, second)]
        for a, b in zip(*metrics):
            self.assertAlmostEqual(a['loss'], b['loss'], delta=1e-6)
            self.assertEqual(a['qids'], b['qids'])
            self.assertEqual(a['lr'], b['lr'])
        plans = [load_json(root / 'reference/batch_plan.json') for root in (first, second)]
        for key in ('microbatch_size', 'gradient_accumulation', 'epoch_order_sha256'):
            self.assertEqual(plans[0][key], plans[1][key])


class FSDPStartupTrainingGlooTests(StartupTrainingGlooTests):
    parallel = 'fsdp'


def failure_worker(rank, port, root):
    from datetime import timedelta
    import torch.distributed as dist

    root = Path(root)
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=2,
                            timeout=timedelta(seconds=30))
    errors = []
    settings = ddp_config.normalize_training_config({'world_size': 2}, 'onethinker')
    def write(name, value):
        path = root / name
        path.write_bytes(canonical_bytes(value))
        return path
    def fail():
        raise ValueError('synthetic cache I/O failure')
    try:
        with patch('torch.cuda.synchronize'), patch('torch.cuda.max_memory_allocated', return_value=TOTAL * (0.95 if rank else 0.1)), \
                patch('torch.cuda.max_memory_reserved', return_value=TOTAL * 0.2), \
                patch('torch.cuda.get_device_properties', return_value=SimpleNamespace(total_memory=TOTAL)):
            try:
                ddp_training.startup_memory_guard(settings, rank, SimpleNamespace(write=write), 'before_optimizer')
            except ValueError as error:
                errors.append(str(error))
        try:
            ddp_training.collective_startup(fail, rank)
        except ValueError as error:
            errors.append(str(error))
        (root / f'errors_rank{rank}.json').write_bytes(canonical_bytes(errors))
        assert not torch.cuda.is_initialized()
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(SOCKETS, 'requires local CPU/gloo sockets')
class CollectiveStartupFailureTests(unittest.TestCase):
    def test_memory_guard_and_rank_zero_io_failures_reach_every_rank(self):
        root = Path(tempfile.mkdtemp(prefix='startup_failure_gloo_', dir=os.environ['LANE_TEST_OUTPUT']))
        context = multiprocessing.get_context('fork')
        with patch.object(fixtures.multiprocessing, 'get_context', return_value=context):
            fixtures.launch_workers(failure_worker, str(root))
        errors = [load_json(root / f'errors_rank{rank}.json') for rank in range(2)]
        self.assertEqual(errors[0], errors[1])
        self.assertIn('memory guard', errors[0][0])
        self.assertIn('synthetic cache I/O failure', errors[0][1])


if __name__ == '__main__':
    unittest.main()
