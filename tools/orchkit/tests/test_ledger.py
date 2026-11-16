"""Tests for orchkit.ledger: append, lookup, live jobs and import of the old schemas."""
import json
import os
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import ledger  # noqa: E402

TOKEN = '0123456789abcdef'


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='orchkit_ledger_')
        self.path = os.path.join(self.tmp, 'L.jsonl')

    def test_append_and_lookup(self):
        row = ledger.make_row('minted', TOKEN, lane='x', partition='general', gpus=1)
        ledger.append(row, self.path)
        ledger.append(ledger.make_row('submitted', TOKEN, job_id=12, partition='general'), self.path)
        rows = ledger.lookup('a15_cot_ap' + TOKEN, self.path)
        self.assertEqual([r['event'] for r in rows], ['minted', 'submitted'])
        self.assertEqual(rows[0]['job_name'], 'a15_cot_ap' + TOKEN)
        self.assertEqual(sorted(rows[0]), sorted(ledger.FIELDS))

    def test_strict_validation(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.append(ledger.make_row('minted', 'abc'), self.path)
        bad = ledger.make_row('minted', TOKEN)
        bad['job_name'] = 'other'
        with self.assertRaises(ledger.LedgerError):
            ledger.append(bad, self.path)
        big = ledger.make_row('minted', TOKEN, meaning='m' * 2000)
        with self.assertRaises(ledger.LedgerError):
            ledger.append(big, self.path)
        with self.assertRaises(ledger.LedgerError):
            ledger.make_row('minted', TOKEN, bogus=1)
        self.assertFalse(os.path.exists(self.path))

    def test_live_jobs_by_partition(self):
        other = 'fedcba9876543210'
        ledger.append(ledger.make_row('submitted', TOKEN, job_id=1, partition='general'), self.path)
        ledger.append(ledger.make_row('submitted', other, job_id=2, partition='advanced'), self.path)
        self.assertEqual([r['token'] for r in ledger.live(self.path, ['general'])], [TOKEN])
        ledger.append(ledger.make_row('ended', TOKEN, job_id=1, state='COMPLETED'), self.path)
        self.assertEqual(ledger.live(self.path, ['general']), [])
        self.assertEqual([r['token'] for r in ledger.live(self.path)], [other])

    def test_env_default_path(self):
        old = os.environ.get('ORCHKIT_LEDGER')
        os.environ['ORCHKIT_LEDGER'] = self.path
        try:
            self.assertEqual(ledger.ledger_path(), self.path)
        finally:
            if old is None:
                del os.environ['ORCHKIT_LEDGER']
            else:
                os.environ['ORCHKIT_LEDGER'] = old

    def test_import_the_five_schemas(self):
        old = [
            {'utc': '2026-11-15T18:11:03Z', 'token': 'a15_cot_ap989d2aa9', 'meaning': 'test-only run'},
            {'utc': '2026-11-16T04:36:40Z', 'token': 'd36acca73f', 'object': 'gs://b/o.tar',
             'meaning': 'upload'},
            {'token': 'a50b808269080', 'job_name': 'a15_cot_apa50b808269080',
             'meaning': {'step': 100}, 'pool': '/p/pool', 'gcs': 'gs://b/q',
             'destination': '/x/evidence/test_1/prepared'},
            {'utc': '2026-11-15T18:42:11Z', 'token': 'pb59bef09f3', 'job_name': 'a15_cot_appb59bef09f3',
             'meaning': 'proof', 'partition': 'general', 'gpus': 1, 'kit_sha256': 'a' * 64,
             'plan_sha256': 'b' * 64, 'pool': '/p/x', 'gcs': 'gs://b/x', 'time': '02:00:00'},
            {'allocation_seconds': 10800, 'token': 'b7e31d84a90c62f5', 'pool': '/p/k',
             'cloud': 'gs://b/k', 'purpose': 'prepare only', 'submitted': False},
            {'utc': '2026-11-16T09:21:00Z', 'job_id': 170193, 'status': 'FAILED', 'token': 'c0ffee'},
            {'tokens': ['t1', 't2'], 'job_name': None, 'status': 'pending', 'cloud': 'gs://b/z'},
        ]
        source = os.path.join(self.tmp, 'old.jsonl')
        with open(source, 'w') as handle:
            for row in old:
                handle.write(json.dumps(row) + '\n')
            handle.write('{broken\n')
        out = os.path.join(self.tmp, 'imported.jsonl')
        self.assertEqual(ledger.main(['import', '--from', source, '--lane', 'lane_a', '--out', out]), 0)
        self.assertEqual(ledger.main(['import', '--from', source, '--lane', 'lane_a', '--out', out]), 0)
        rows = ledger.read_rows(out)
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(sorted(r) == sorted(ledger.FIELDS) and r['lane'] == 'lane_a' for r in rows))
        self.assertEqual(rows[0]['token'], '989d2aa9')
        self.assertEqual(rows[1]['gcs'], 'gs://b/o.tar')
        self.assertEqual(rows[2]['state'], 'test-prepare')
        self.assertIn('kit_sha256', rows[3]['meaning'])
        self.assertEqual(rows[3]['time_limit_s'], 7200)
        self.assertEqual(rows[4]['time_limit_s'], 10800)
        self.assertEqual((rows[5]['event'], rows[5]['job_id']), ('ended', 170193))
        self.assertEqual([r['token'] for r in rows[6:]], ['t1', 't2'])

    def test_import_refuses_production_path(self):
        self.assertEqual(ledger.main(['import', '--from', self.path, '--lane', 'x',
                                      '--out', ledger.PRODUCTION]), 2)


if __name__ == '__main__':
    unittest.main()
