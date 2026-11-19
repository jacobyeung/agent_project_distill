import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from student_pilot import ddp_admission, orchard_paths, provisional_data, startup_receipt, storage
from student_pilot.common import binding, canonical_bytes, digest_json
from student_pilot.provisional import tag


LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


class StartupReceiptTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='startup_receipt_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.frozen = self.root / 'frozen'
        self.frozen.mkdir()
        self.frame = self.root / 'rgb.bin'
        self.frame.write_bytes(b'synthetic original RGB bytes')
        self.row = {'qid': 'synthetic', 'target': 'target', 'student_input': {'frames': [binding(self.frame)]}}
        self.protocol = tag({'student': 'qwen36_27b', 'runtime': [], 'versions': {},
                             'base': {'files': [], 'weight_shards': []}, 'candidate_source': binding(self.frame),
                             'training': {'world_size': 8}, 'PROVISIONAL_DIVISION_SHA': 'a' * 64}, LABEL)
        self.document('protocol.json', self.protocol)
        self.manifest = tag({'rows': [self.row], 'input_audits': [{'qid': 'synthetic'}],
                            'counts': {'training_rows': 1}, 'training_ready': True,
                            'protocol': binding(self.frozen / 'protocol.json'), 'pre_evaluation_drops': []}, LABEL)
        self.document('training.json', self.manifest)
        self.document('config.json', {'synthetic': True})
        self.document('launch_identity.json', {'synthetic': True})
        self.document('training.json.source_receipt.json', {'synthetic': True})
        self.request = {'student': 'qwen36_27b', 'world_size': 8,
                        'manifest': binding(self.frozen / 'training.json'), 'protocol': binding(self.frozen / 'protocol.json')}
        self.document('request.json', self.request)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '', 'STUDENT_ORCHARD': '1',
                                                        'STUDENT_FRAME_ROOT_MAP': ''}, clear=True))
        self.stack.enter_context(patch.object(orchard_paths, 'PROJECT', self.root))
        self.protocol_validator = self.stack.enter_context(patch.object(provisional_data, 'load_protocol', side_effect=lambda *a, **k: copy.deepcopy(self.protocol)))
        self.manifest_validator = self.stack.enter_context(patch.object(provisional_data, 'load_training', side_effect=lambda *a, **k: copy.deepcopy(self.manifest)))
        self.stack.enter_context(patch.object(provisional_data, '_verified_receipt'))
        self.stack.enter_context(patch.object(ddp_admission, 'checked_request', return_value=self.request))
        self.stack.enter_context(patch.object(storage, 'code_provenance', side_effect=lambda config: {'commit': 'b' * 40,
                                             'dirty': False, 'config_sha256': digest_json(config)}))

    def document(self, name, value):
        path = self.frozen / name
        path.write_bytes(canonical_bytes(value))
        return path

    def prepare(self):
        return startup_receipt.prepare(self.frozen, 'qwen36_27b', 8, LABEL)

    def enable(self, pin):
        self.stack.enter_context(patch.dict(os.environ, {'STUDENT_STARTUP_RECEIPT': pin['path'],
                                                        'STUDENT_STARTUP_RECEIPT_SHA256': pin['sha256']}))

    def load(self, weights=False):
        return startup_receipt.load_prepared(self.frozen / 'training.json', self.frozen / 'protocol.json',
                                             LABEL, 'qwen36_27b', weights=weights)

    def test_cpu_validation_is_reused_only_through_explicit_hash_pin(self):
        pin = self.prepare()
        self.assertEqual(self.manifest_validator.call_count, 1)
        self.assertIsNone(self.load())
        self.enable(pin)
        result = self.load(weights=True)
        self.assertEqual(result['manifest'], self.manifest)
        self.assertEqual(result['protocol'], self.protocol)
        self.assertEqual(result['receipt'], pin)
        self.assertEqual(result['frame_mode'], 'shared_verified_on_read')
        self.assertEqual(self.manifest_validator.call_count, 1)
        self.assertTrue(self.protocol_validator.call_args.kwargs['weights'])

    def test_missing_sha_and_corrupt_receipt_fail_closed(self):
        pin = self.prepare()
        with patch.dict(os.environ, {'STUDENT_STARTUP_RECEIPT': pin['path']}):
            with self.assertRaises(ValueError):
                self.load()
        self.enable(pin)
        Path(pin['path']).write_bytes(Path(pin['path']).read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Hash|hash'):
            self.load()

    def test_every_frozen_input_change_invalidates_the_cpu_result(self):
        pin = self.prepare()
        self.enable(pin)
        for name in ('protocol.json', 'training.json', 'config.json', 'launch_identity.json',
                     'training.json.source_receipt.json', 'request.json', 'shared_frames.json'):
            path = self.frozen / name
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.load()
            path.write_bytes(original)

    def test_corrupt_frame_is_rejected_on_cpu_before_receipt_exists(self):
        self.frame.write_bytes(b'changed frame')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.frozen / 'startup_receipt.json').exists())

    def test_shared_frames_keep_rows_and_use_existing_hash_before_decode(self):
        pin = self.prepare()
        self.enable(pin)
        prepared = self.load()
        store = unittest.mock.Mock()
        rows = startup_receipt.localize_shared(prepared, store, self.frozen / 'training.json')
        self.assertEqual(rows, self.manifest['rows'])
        self.assertEqual(store.write.call_args.args[0], 'input_manifest.json')
        self.frame.write_bytes(b'changed after CPU admission')
        with self.assertRaises(ValueError):
            binding(rows[0]['student_input']['frames'][0]['path'], rows[0]['student_input']['frames'][0]['sha256'])
        from student_pilot import batches
        self.assertIn('binding(frame["path"], frame["sha256"])', __import__('inspect').getsource(batches.load_rgb))

    def test_rejects_node_local_frames_and_changed_mapping_or_code(self):
        with patch.object(orchard_paths, 'PROJECT', self.frozen):
            with self.assertRaisesRegex(ValueError, 'shared'):
                self.prepare()
        pin = self.prepare()
        self.enable(pin)
        with patch.dict(os.environ, {'STUDENT_FRAME_ROOT_MAP': 'changed'}):
            with self.assertRaises(ValueError):
                self.load()
        with patch.object(storage, 'code_provenance', return_value={'commit': 'c' * 40, 'dirty': False}):
            with self.assertRaisesRegex(ValueError, 'code|commit'):
                self.load()

    def test_prepare_preserves_existing_artifacts_and_refuses_gpu_allocations(self):
        pin = self.prepare()
        original = Path(pin['path']).read_bytes()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(Path(pin['path']).read_bytes(), original)
        with patch.dict(os.environ, {'SLURM_JOB_GPUS': '0'}):
            with self.assertRaisesRegex(ValueError, 'CPU'):
                startup_receipt.prepare(self.root / 'new', 'qwen36_27b', 8, LABEL)

    def test_change_during_full_validation_never_gets_a_receipt(self):
        def mutate(*args, **kwargs):
            self.document('training.json', {**self.manifest, 'changed': True})
            return self.manifest
        self.manifest_validator.side_effect = mutate
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.frozen / 'startup_receipt.json').exists())

    def test_dropped_payload_hashes_are_rechecked_without_retokenizing(self):
        dropped = self.root / 'dropped.json'
        dropped.write_bytes(b'synthetic dropped row')
        with patch.object(startup_receipt, 'dropped_dependencies', return_value=[binding(dropped)]):
            pin = self.prepare()
        self.enable(pin)
        self.load()
        dropped.write_bytes(b'changed dropped row')
        with self.assertRaises(ValueError):
            self.load()


if __name__ == '__main__':
    unittest.main()
