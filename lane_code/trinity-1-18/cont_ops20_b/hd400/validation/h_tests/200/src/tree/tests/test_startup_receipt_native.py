import os
from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import patch

from student_pilot import ddp_admission, diagnostic_data, orchard_paths, provisional_data, startup_receipt, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from student_pilot.students import get_student
from tests import test_provisional as fixtures


LABEL = fixtures.LABEL


class NativeStartupReceiptTests(unittest.TestCase):
    document = fixtures.ProvisionalTests.document
    candidates = fixtures.ProvisionalTests.candidates
    index = fixtures.ProvisionalTests.index

    def setUp(self):
        fixtures.ProvisionalTests.setUp(self)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '', 'STUDENT_ORCHARD': '1',
            'STUDENT_FRAME_ROOT_MAP': '', 'STUDENT_MODEL_ROOT': str(self.root / 'models')}, clear=True))
        self.stack.enter_context(patch.object(orchard_paths, 'PROJECT', self.root))
        self.stack.enter_context(patch.object(storage, 'code_provenance', side_effect=lambda config: {
            'commit': 'c' * 40, 'dirty': False, 'config_sha256': digest_json(config)}))
        index, self.entries = self.candidates()
        self.marker = self.document('checkpoint.json', {'synthetic_cpu_fixture': True})
        self.base = {'revision': get_student('onethinker')['snapshot'].name, 'files': [binding(self.marker)],
                     'weight_shards': [binding(self.marker)]}
        self.stack.enter_context(patch.object(diagnostic_data, 'checkpoint_bindings', return_value=self.base))
        self.config = self.document('config.json', {'world_size': 2})
        self.document('launch_identity.json', {'synthetic_cpu_fixture': True})
        self.protocol_path, self.manifest_path = self.root / 'protocol.json', self.root / 'training.json'
        provisional_data.prepare_protocol(index, self.protocol_path, LABEL, training_config=self.config)
        self.protocol = provisional_data.load_protocol(self.protocol_path, LABEL)
        self.dropped = self.protocol['division']['train_candidate_qids'][0]
        self.stack.enter_context(patch('student_pilot.batches.load_processor', return_value=object()))
        self.tokens = self.stack.enter_context(patch.object(diagnostic_data, 'target_tokens',
            side_effect=lambda processor, row: 1000000 if row['qid'] == self.dropped else 10))
        self.stack.enter_context(patch.object(diagnostic_data, 'encode_training', side_effect=lambda processor, row: ({}, {
            'qid': row['qid'], 'frame_count': 32, 'assistant_tokens_including_eos': 10, 'prompt_tokens': 20})))
        provisional_data.prepare_training(self.protocol_path, self.manifest_path, LABEL)
        provisional_data.seal_source(self.manifest_path, provisional_data.source_receipt_path(self.manifest_path), LABEL)
        self.document('request.json', ddp_admission.request_identity(self.manifest_path, self.protocol_path, LABEL, 'onethinker', 2))

    def prepare(self):
        pin = startup_receipt.prepare(self.root, 'onethinker', 2, LABEL)
        self.stack.enter_context(patch.dict(os.environ, {'STUDENT_STARTUP_RECEIPT': pin['path'],
                                                       'STUDENT_STARTUP_RECEIPT_SHA256': pin['sha256']}))
        return pin

    def load(self):
        return startup_receipt.load_prepared(self.manifest_path, self.protocol_path, LABEL, 'onethinker', weights=True)

    def test_native_seal_and_dropped_row_admission_match_cached_inputs(self):
        expected = provisional_data.load_training(self.manifest_path, LABEL)
        self.prepare()
        self.tokens.reset_mock()
        with patch.object(provisional_data, 'load_training', side_effect=AssertionError('full semantic validation repeated')):
            actual = self.load()['manifest']
        self.tokens.assert_not_called()
        self.assertEqual(expected, actual)
        self.assertEqual([row['qid'] for row in expected['pre_evaluation_drops']], [self.dropped])

    def test_changed_dropped_target_is_refused_by_a_fresh_byte_hash(self):
        self.prepare()
        entry = next(item for item in self.entries if item['qid'] == self.dropped)
        Path(entry['target_path']).write_bytes(b'changed after CPU validation')
        with self.assertRaisesRegex(ValueError, 'Hash|hash'):
            self.load()

    def test_changed_base_weight_is_still_refused_on_gpu_startup_path(self):
        self.prepare()
        self.marker.write_bytes(b'changed pinned model bytes')
        with self.assertRaises(ValueError):
            self.load()

    def test_changed_kept_row_and_inventory_cannot_inherit_cpu_admission(self):
        self.prepare()
        manifest = load_json(self.manifest_path)
        manifest['rows'][0]['target'] = 'unadmitted target'
        self.manifest_path.write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.load()

    def test_shared_inventory_preserves_all_original_rgb_pins(self):
        self.prepare()
        prepared = self.load()
        inventory = load_json(self.root / 'shared_frames.json')
        expected = startup_receipt.frame_references(prepared['manifest']['rows'])
        actual = [{key: pin[key] for key in ('path', 'sha256')} for pin in inventory['files']]
        self.assertEqual(expected, actual)
        self.assertEqual(inventory['unique_paths'], 1)
        dropped_pins = load_json(self.root / 'startup_receipt.json')['dropped_dependencies']
        target = next(item['target_path'] for item in self.entries if item['qid'] == self.dropped)
        self.assertIn(binding(target), dropped_pins)


if __name__ == '__main__':
    unittest.main()
