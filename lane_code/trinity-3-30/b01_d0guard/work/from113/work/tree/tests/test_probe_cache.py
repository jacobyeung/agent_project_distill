import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import ddp_config, probe_cache
from student_pilot.common import canonical_bytes, digest_json


def fixture_identity():
    settings = ddp_config.normalize_training_config({'world_size': 2, 'max_microbatch_size': 4}, 'qwen36_27b')
    protocol = {'student': 'qwen36_27b', 'base_sha256': 'a' * 64, 'rgb': {'frame_count': 32},
                'base': {'revision': 'snapshot', 'files': [], 'weight_shards': []},
                'runtime': [{'path': '/code/ddp_training.py', 'sha256': 'b' * 64}],
                'versions': {'torch': 'synthetic'}, 'init_adapter_sha256': 'c' * 64}
    rows = [{'qid': 'fixture', 'target': 'synthetic target',
             'student_input': {'frames': [{'path': '/run-one/frame', 'sha256': 'd' * 64}], 'question': 'synthetic'}}]
    audits = {'fixture': {'qid': 'fixture', 'sequence_tokens': 16, 'visual_tokens': 8, 'assistant_tokens_including_eos': 2}}
    devices = [{'name': 'synthetic', 'total_memory_bytes': 10000, 'driver': 'test'}] * 2
    identity = probe_cache.identity(protocol, rows, audits, settings, {'nnodes': 1, 'local_world_size': 2}, devices, 'e' * 64)
    return protocol, rows, audits, settings, devices, identity


def fixture_probes(identity):
    reports = []
    for rank in range(2):
        trials = [{'microbatch': size, 'fits': True, 'seconds': seconds,
                   'peak_allocated_bytes': 4000, 'peak_reserved_bytes': 5000,
                   'total_memory_bytes': 10000, 'memory_fit_safety_factor': 1.15}
                  for size, seconds in ((1, 4.0), (2, 6.0), (4, 10.0))]
        reports.append({'rank': rank, 'student': 'qwen36_27b', 'trials': trials,
                        'stress_qids': ['fixture'], 'optimizer_updates': 0,
                        'memory_fraction': 0.9, 'memory_fit_safety_factor': 1.15,
                        'policy': probe_cache.POLICY, **identity['allocator']})
    return reports


class ProbeCacheTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='probe_cache_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.protocol, self.rows, self.audits, self.settings, self.devices, self.identity = fixture_identity()
        self.reports = fixture_probes(self.identity)
        self.source = {'commit': 'f' * 40, 'config_sha256': '1' * 64,
                       'run': {'path': '/prior/run.json', 'sha256': '2' * 64},
                       'probe': {'path': '/prior/memory_probe.json', 'sha256': '3' * 64}}
        self.guards = [{'rank': rank, 'allocated_bytes': 4000, 'reserved_bytes': 5000,
                        'total_memory_bytes': 10000, 'passed': True} for rank in range(2)]

    def publish(self):
        return probe_cache.publish(self.root, self.identity, self.reports, 4, self.source, self.guards)

    def test_miss_then_hash_pinned_reuse_of_identical_calibration(self):
        self.assertIsNone(probe_cache.lookup(self.root, self.identity))
        pin = self.publish()
        entry = probe_cache.lookup(self.root, self.identity)
        self.assertEqual(entry['receipt'], pin)
        self.assertEqual(entry['probes'], self.reports)
        self.assertEqual(entry['microbatch'], 4)
        self.assertEqual(entry['identity'], self.identity)

    def test_reuse_ignores_only_run_local_frame_locations(self):
        self.publish()
        rows = copy.deepcopy(self.rows)
        rows[0]['student_input']['frames'][0]['path'] = '/run-two/frame'
        identity = probe_cache.identity(self.protocol, rows, self.audits, self.settings,
                                        {'nnodes': 1, 'local_world_size': 2}, self.devices, 'e' * 64)
        self.assertEqual(identity, self.identity)
        self.assertIsNotNone(probe_cache.lookup(self.root, identity))

    def test_input_configuration_and_runtime_changes_force_fresh_probe(self):
        self.publish()
        changes = [lambda p, r, a, s, d: p.update(base_sha256='9' * 64),
                   lambda p, r, a, s, d: p.update(init_adapter_sha256='9' * 64),
                   lambda p, r, a, s, d: p['rgb'].update(frame_count=64),
                   lambda p, r, a, s, d: p['versions'].update(torch='changed'),
                   lambda p, r, a, s, d: p['runtime'][0].update(sha256='9' * 64),
                   lambda p, r, a, s, d: s.update(max_microbatch_size=2),
                   lambda p, r, a, s, d: s.update(max_sequence_tokens=32768),
                   lambda p, r, a, s, d: s.update(world_size=4),
                   lambda p, r, a, s, d: s.update(memory_fraction=0.8),
                   lambda p, r, a, s, d: r[0].update(target='other target'),
                   lambda p, r, a, s, d: r[0]['student_input']['frames'][0].update(sha256='9' * 64),
                   lambda p, r, a, s, d: a['fixture'].update(sequence_tokens=17),
                   lambda p, r, a, s, d: d[0].update(driver='changed')]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                values = copy.deepcopy((self.protocol, self.rows, self.audits, self.settings, self.devices))
                change(*values)
                p, r, a, s, d = values
                identity = probe_cache.identity(p, r, a, s, {'nnodes': 1, 'local_world_size': 2}, d, 'e' * 64)
                self.assertIsNone(probe_cache.lookup(self.root, identity))
        with patch.dict(os.environ, {'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True', 'PYTORCH_ALLOC_CONF': ''}):
            changed = probe_cache.identity(self.protocol, self.rows, self.audits, self.settings,
                                          {'nnodes': 1, 'local_world_size': 2}, self.devices, 'e' * 64)
            self.assertNotEqual(changed, self.identity)

    def test_environment_receipt_is_mandatory_and_byte_pinned(self):
        with patch.dict(os.environ, {'STUDENT_MEMORY_PROBE_CACHE': str(self.root)}, clear=True):
            with self.assertRaisesRegex(ValueError, 'environment'):
                probe_cache.configuration()
            env = self.root / 'environment.json'
            env.write_bytes(b'{}')
            from student_pilot.common import binding
            with patch.dict(os.environ, {'STUDENT_MEMORY_PROBE_ENVIRONMENT': str(env),
                                        'STUDENT_MEMORY_PROBE_ENVIRONMENT_SHA256': binding(env)['sha256']}):
                config = probe_cache.configuration()
                self.assertEqual(config['environment_sha256'], binding(env)['sha256'])
                env.write_bytes(b'{ }')
                with self.assertRaises(ValueError):
                    probe_cache.configuration()
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(probe_cache.configuration())

    def test_corruption_and_symlink_receipts_never_skip_the_probe(self):
        pin = self.publish()
        path = Path(pin['path'])
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'hash|Hash'):
            probe_cache.lookup(self.root, self.identity)
        path.rename(path.with_suffix('.retained'))
        path.symlink_to(path.with_suffix('.retained'))
        with self.assertRaisesRegex(ValueError, 'symlink'):
            probe_cache.lookup(self.root, self.identity)

    def test_rejects_unverified_ranks_timing_and_guard_results(self):
        cases = [(self.reports[:1], self.guards),
                 (self.reports, self.guards[:1])]
        for reports, guards in cases:
            with self.subTest(reports=len(reports), guards=len(guards)), self.assertRaises(ValueError):
                probe_cache.publish(self.root, self.identity, reports, 4, self.source, guards)
        for field, value in (('seconds', float('nan')), ('peak_allocated_bytes', 9500), ('fits', False)):
            reports = copy.deepcopy(self.reports)
            reports[0]['trials'][-1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe_cache.publish(self.root, self.identity, reports, 4, self.source, self.guards)
        guards = copy.deepcopy(self.guards)
        guards[1]['passed'] = False
        with self.assertRaises(ValueError):
            probe_cache.publish(self.root, self.identity, self.reports, 4, self.source, guards)

    def test_private_cache_and_immutable_first_writer(self):
        self.root.chmod(0o770)
        with self.assertRaisesRegex(ValueError, 'private'):
            self.publish()
        self.root.chmod(0o700)
        pin = self.publish()
        before = Path(pin['path']).read_bytes()
        self.assertEqual(self.publish(), pin)
        self.assertEqual(before, Path(pin['path']).read_bytes())

    def test_live_capacity_and_first_step_guard_keep_the_safety_margin(self):
        report = self.reports[0]
        self.assertTrue(probe_cache.available(report, 4, 5000, 1000, self.settings))
        self.assertFalse(probe_cache.available(report, 4, 3000, 1000, self.settings))
        guard = probe_cache.memory_guard(0, 6000, 7000, 10000, self.settings, additional_bytes=1000)
        self.assertTrue(guard['passed'])
        self.assertFalse(probe_cache.memory_guard(0, 8000, 8000, 10000, self.settings, additional_bytes=1000)['passed'])
        self.assertFalse(probe_cache.memory_guard(0, 6000, 9500, 10000, self.settings)['passed'])

    def test_runtime_fingerprint_pins_driver_kernel_tag_and_backend_flags(self):
        from types import SimpleNamespace
        import torch

        device = SimpleNamespace(name='synthetic', total_memory=10000, major=9, minor=0)
        with patch('torch.cuda.get_device_properties', return_value=device), \
                patch.object(probe_cache.subprocess, 'check_output', return_value='575.57.08\n575.57.08\n'), \
                patch.dict(os.environ, {'STUDENT_KERNEL_CACHE_TAG': 'pinned-environment'}):
            first = probe_cache.runtime_device()
            with patch.dict(os.environ, {'STUDENT_KERNEL_CACHE_TAG': 'different-environment'}):
                second = probe_cache.runtime_device()
        self.assertEqual(first['driver'], '575.57.08')
        self.assertEqual(first['compute_capability'], [9, 0])
        self.assertEqual(first['kernel_cache_tag'], 'pinned-environment')
        self.assertNotEqual(first, second)
        self.assertEqual(set(first['sdpa']), {'flash', 'math', 'memory_efficient'})
        self.assertFalse(torch.cuda.is_initialized())

    def test_identity_is_canonical_and_does_not_accept_nonfinite_values(self):
        self.assertEqual(digest_json(self.identity), digest_json(json.loads(canonical_bytes(self.identity))))
        changed = copy.deepcopy(self.settings)
        changed['memory_fraction'] = float('nan')
        with self.assertRaises(ValueError):
            probe_cache.identity(self.protocol, self.rows, self.audits, changed,
                                 {'nnodes': 1, 'local_world_size': 2}, self.devices, 'e' * 64)


if __name__ == '__main__':
    unittest.main()
