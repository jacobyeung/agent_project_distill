import copy
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fixtures import fixture_root
from tools.gtmeasure.io import canonical
from tools.gtmeasure.room_corpus import replay
from tools.gtmeasure.room_labels import RoomLabelDeferred


class SelectiveReplayTests(unittest.TestCase):
    def setUp(self):
        self.root = fixture_root()
        self.nonroom = b'{ "qid": "n", "family": "gtm_object_count" }\r\n'
        self.room = {'qid': 'r', 'family': 'gtm_room_size', 'dataset': 'scannet', 'scene': 'scene0000_00'}
        (self.root / 'train.jsonl').write_bytes(self.nonroom + (canonical(self.room) + '\n').encode())
        (self.root / 'heldout.jsonl').write_bytes((canonical({**self.room, 'qid': 'h'}) + '\n').encode())
        self.repair = SimpleNamespace(manifest={'config': {'structure': 'v2'}}, conventions={}, labels=object())
        self.source = {'path': str(self.root / 'MANIFEST.json'), 'sha256': 'a' * 64}

    def test_preserves_noncanonical_bytes_and_defers_heldout(self):
        corrected = {**self.room, 'corrected': True}
        with patch('tools.gtmeasure.room_corpus.rewrite_room_row', return_value=corrected) as rewrite:
            sides, deferred, hashes = replay(self.repair, self.source, 'b' * 40)
        self.assertEqual(sides['train'][0], self.nonroom)
        self.assertEqual(json.loads(sides['train'][1]), corrected)
        self.assertEqual(sides['heldout'], [])
        self.assertEqual(deferred[0]['reason'], 'room_label_not_training')
        self.assertEqual(rewrite.call_count, 1)
        self.assertEqual(hashes['train']['rebuilt'], hashlib.sha256(self.nonroom).hexdigest())

    def test_missing_label_records_qid_and_reason(self):
        with patch('tools.gtmeasure.room_corpus.rewrite_room_row', side_effect=RoomLabelDeferred('room_label_missing')):
            sides, deferred, _ = replay(self.repair, self.source, 'b' * 40)
        self.assertEqual(sides['train'], [self.nonroom])
        self.assertEqual((deferred[0]['qid'], deferred[0]['reason']), ('r', 'room_label_missing'))

    def test_unexpected_repair_failure_is_not_a_deferral(self):
        with patch('tools.gtmeasure.room_corpus.rewrite_room_row', side_effect=ValueError('corrupt input')):
            with self.assertRaisesRegex(ValueError, 'corrupt input'):
                replay(self.repair, self.source, 'b' * 40)
