"""Exercise the owner-only scan on local synthetic files, never on /data*."""
import contextlib
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import ingest_read
import prove_kit_alias_ids as proof


class KitAliasProofTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='alias-proof-', dir=ingest_read.SCRATCH))
        (self.root / 'reads').mkdir()
        self.ids = list(proof.EXPECTED_COUNTS)
        self.assertEqual(len(self.ids), 6)
        self.counts = mock.patch.object(proof, 'EXPECTED_COUNTS', dict.fromkeys(self.ids, 2))
        self.counts.start()
        self.addCleanup(self.counts.stop)
        self.pause = mock.patch.object(proof.time, 'sleep')
        self.sleep = self.pause.start()
        self.addCleanup(self.pause.stop)
        for read_id in self.ids:
            self.write(read_id, ['q1', 'q2'])

    def write(self, read_id, item_ids):
        with gzip.open(self.root / 'reads' / (read_id + '.jsonl.gz'), 'wt') as stream:
            for item_id in item_ids:
                stream.write(json.dumps(dict(read_id=read_id, item_id=item_id)) + '\n')

    def run_scan(self):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = proof.main(['--corpus-root', str(self.root)])
        return code, output.getvalue(), error.getvalue()

    def test_scans_only_six_named_files_and_proves_absence(self):
        (self.root / 'reads' / 'unrelated.jsonl.gz').write_bytes(b'not gzip')
        code, output, error = self.run_scan()
        self.assertEqual(code, 0, error)
        self.assertIn('COMPLETE: files=6 items=12 devrows_item_ids=0', output)
        self.assertEqual(output.count('SCAN '), 6)
        self.assertTrue(self.sleep.called)

    def test_prefix_at_end_of_last_file_fails_proof(self):
        self.write(self.ids[-1], ['q1', 'devrows:q2'])
        code, output, error = self.run_scan()
        self.assertEqual(code, 1, error)
        self.assertIn('COMPLETE: files=6 items=12 devrows_item_ids=1', output)

    def test_missing_named_file_is_incomplete(self):
        empty_root = self.root / 'empty'
        empty_root.mkdir()
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = proof.main(['--corpus-root', str(empty_root)])
        self.assertEqual(code, 2)
        self.assertIn('INCOMPLETE:', error.getvalue())
        self.assertNotIn('COMPLETE:', output.getvalue())

    def test_corrupt_gzip_is_incomplete(self):
        (self.root / 'reads' / (self.ids[-1] + '.jsonl.gz')).write_bytes(b'bad gzip')
        code, output, error = self.run_scan()
        self.assertEqual(code, 2)
        self.assertIn('INCOMPLETE:', error)
        self.assertNotIn('COMPLETE:', output)

    def test_short_file_is_incomplete(self):
        self.write(self.ids[-1], ['q1'])
        code, output, error = self.run_scan()
        self.assertEqual(code, 2)
        self.assertIn('1 items != expected 2', error)
        self.assertNotIn('COMPLETE:', output)

    def test_damaged_deflate_or_json_is_incomplete(self):
        for data in [b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\x07',
                     gzip.compress(b'not JSON\n')]:
            with self.subTest(data=data):
                (self.root / 'reads' / (self.ids[0] + '.jsonl.gz')).write_bytes(data)
                code, output, error = self.run_scan()
                self.assertEqual(code, 2)
                self.assertIn('INCOMPLETE:', error)
                self.assertNotIn('COMPLETE:', output)

    def test_wrong_read_id_or_nonstring_item_is_incomplete(self):
        for row in [dict(read_id='another_read', item_id='q'),
                    dict(read_id=self.ids[0], item_id=None)]:
            with self.subTest(row=row):
                with gzip.open(self.root / 'reads' / (self.ids[0] + '.jsonl.gz'), 'wt') as stream:
                    stream.write(json.dumps(row) + '\n')
                code, output, error = self.run_scan()
                self.assertEqual(code, 2)
                self.assertIn('Invalid read_id/item_id', error)
                self.assertNotIn('COMPLETE:', output)

    def test_each_physical_read_is_bounded_and_paced_before_read(self):
        events = []
        class Source:
            def read(self, size):
                events.append(('read', size))
                return b'x' * size
        self.sleep.side_effect = lambda seconds: events.append(('sleep', seconds))
        paced = proof.PacedReader(Source())
        buffer = bytearray(2 * proof.CHUNK)
        self.assertEqual(paced.readinto(buffer), proof.CHUNK)
        self.assertEqual(paced.readinto(buffer), proof.CHUNK)
        self.assertEqual(events, [('sleep', proof.CHUNK / proof.BYTES_PER_SECOND),
                                  ('read', proof.CHUNK)] * 2)
        self.assertEqual(paced.bytes_read, 2 * proof.CHUNK)
