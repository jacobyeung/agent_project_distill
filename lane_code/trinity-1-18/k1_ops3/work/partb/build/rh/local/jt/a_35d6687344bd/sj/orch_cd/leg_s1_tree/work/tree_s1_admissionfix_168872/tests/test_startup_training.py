import copy
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from student_pilot import ddp_training, probe_cache
from tests.test_probe_cache import fixture_identity, fixture_probes


class StartupTrainingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='startup_training_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.protocol, self.rows, self.audits, self.settings, self.devices, self.identity = fixture_identity()
        self.reports = fixture_probes(self.identity)
        self.config = {'root': str(self.root), 'environment_sha256': 'e' * 64}
        source = {'commit': 'f' * 40, 'config_sha256': '1' * 64,
                  'run': {'path': '/prior/run.json', 'sha256': '2' * 64},
                  'probe': {'path': '/prior/probe.json', 'sha256': '3' * 64}}
        guards = [{'rank': rank, 'allocated_bytes': 4000, 'reserved_bytes': 5000,
                   'total_memory_bytes': 10000, 'passed': True} for rank in range(2)]
        self.pin = probe_cache.publish(self.root, self.identity, self.reports, 4, source, guards)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(probe_cache, 'configuration', return_value=self.config))
        self.stack.enter_context(patch.object(probe_cache, 'runtime_device', return_value=self.devices[0]))
        self.stack.enter_context(patch.object(ddp_training, 'gather', side_effect=lambda value, world: [copy.deepcopy(value) for _ in range(world)]))
        self.stack.enter_context(patch.object(ddp_training, 'collective_startup', side_effect=lambda function, rank: function()))
        self.stack.enter_context(patch('torch.cuda.mem_get_info', return_value=(6000, 10000)))
        self.stack.enter_context(patch('torch.cuda.memory_reserved', return_value=1000))
        self.fresh = self.stack.enter_context(patch.object(ddp_training, 'memory_probe', return_value=self.reports[0]))
        self.lease = Mock()

    def probe(self, checkpoint=None):
        return ddp_training.startup_memory_probe(object(), object(), self.rows, self.audits, self.settings, 0,
                                                 self.lease, self.protocol, {'nnodes': 1, 'local_world_size': 2}, checkpoint)

    def test_matching_calibration_skips_all_probe_forward_backward_work(self):
        report, context = self.probe()
        self.fresh.assert_not_called()
        self.lease.assert_called_once()
        self.assertTrue(context['cache_hit'])
        self.assertEqual(report['reused_calibration'], self.pin)
        self.assertEqual(report['trials'], self.reports[0]['trials'])

    def test_new_configuration_and_resume_always_probe(self):
        self.settings = {**self.settings, 'max_microbatch_size': 2}
        report, context = self.probe()
        self.fresh.assert_called_once()
        self.assertFalse(context['cache_hit'])
        self.fresh.reset_mock()
        report, context = self.probe(checkpoint={'step': 25})
        self.fresh.assert_called_once()
        self.assertIsNone(context)

    def test_one_rank_capacity_miss_makes_every_rank_probe(self):
        original = ddp_training.gather.side_effect
        def gather(value, world):
            return [True, False] if isinstance(value, bool) else original(value, world)
        with patch.object(ddp_training, 'gather', side_effect=gather):
            report, context = self.probe()
        self.fresh.assert_called_once()
        self.assertFalse(context['cache_hit'])

    def test_mismatched_rank_cache_configuration_fails_collectively(self):
        def gather(value, world):
            changed = copy.deepcopy(value)
            changed['config'] = None
            return [value, changed]
        with patch.object(ddp_training, 'gather', side_effect=gather), self.assertRaisesRegex(ValueError, 'configuration'):
            self.probe()
        self.fresh.assert_not_called()

    def test_disabled_cache_uses_original_probe_without_device_fingerprinting(self):
        with patch.object(probe_cache, 'configuration', return_value=None), patch.object(probe_cache, 'runtime_device') as device:
            report, context = self.probe()
        self.fresh.assert_called_once()
        device.assert_not_called()
        self.assertIsNone(context)

    def test_first_step_memory_guard_refuses_before_optimizer_update(self):
        with patch('torch.cuda.synchronize'), patch('torch.cuda.max_memory_allocated', return_value=8000), \
                patch('torch.cuda.max_memory_reserved', return_value=8000), \
                patch('torch.cuda.get_device_properties', return_value=Mock(total_memory=10000)):
            store = Mock()
            with self.assertRaisesRegex(ValueError, 'memory guard'):
                ddp_training.startup_memory_guard(self.settings, 0, store, 'before_optimizer', additional_bytes=1000)
            self.assertEqual(store.write.call_args.args[0], 'memory_guard_before_optimizer.json')


if __name__ == '__main__':
    unittest.main()
