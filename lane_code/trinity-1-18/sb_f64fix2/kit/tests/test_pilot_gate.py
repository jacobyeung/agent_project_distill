"""mem_pilot.check_audit over complete audits of the dry run's 16 planned rows, encoded for real: a passing audit
and one whose rows exceed only the tripwire feed the pilot every row, while one check_row failure or one ceiling
violation refuses it, counted per stream over every audited row (review sb_f64rev2 finding 4).
F64_WORK names a scratch directory these tests may write; they never write anywhere else."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ['F64_WORK'])
sys.path[:0] = [str(KIT / 'scripts')]
CONFIG = KIT / 'configs' / 'r1_config_f64.json'

import f64_dryrun  # noqa: E402
import mem_pilot  # noqa: E402
import token_audit  # noqa: E402
from student_pilot.p3_provenance import file_pin  # noqa: E402

TRIPWIRE = 9200  # between the dry run's pose (9,127) and routing (9,303) rows


class PilotGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, setups = f64_dryrun.setup(CONFIG, ['a43'])
        cls.receipt, cls.processor, cls.rows = setups['a43']
        # The dry run has no bound r2_sampling table (f64_dryrun.STAND_INS); plan with the native sampler.
        cls.unbound = {k: v for k, v in cls.cfg.items() if k not in ('r2_identity', 'r2_sampling')}
        cls.recipe = cls.cfg['recipe']
        cls.items = token_audit.planned_rows(cls.unbound, cls.receipt, cls.recipe, 0, 1)
        cls.config_sha256 = token_audit.file_sha256(CONFIG)
        cls.preparation = file_pin(f64_dryrun.PREP)
        cls.tmp = Path(tempfile.mkdtemp(prefix='pilot_gate_', dir=WORK))
        records = []
        token_audit.audit(cls.rows, cls.recipe, cls.receipt, cls.items, records.append)
        cls.records = {(r['stream'], r['index']): r for r in records}

    @classmethod
    def tearDownClass(cls):
        cls.rows.close()

    def gate(self, name, edit=None, tripwire=token_audit.TRIPWIRE_TOKENS):
        """Summary and summary path of two complete shards of the cached real records, each passed through edit."""
        identity = token_audit.identity_for(self.config_sha256, self.unbound, self.receipt, self.recipe, self.items,
                                            0, 1, 1, 16384, tripwire, 2, self.preparation)
        folder = Path(tempfile.mkdtemp(prefix=name + '_', dir=self.tmp))
        paths = [str(folder / f'shard_{k}.jsonl') for k in range(2)]
        for k, path in enumerate(paths):
            def emit(part, sink):
                for key, _ in part:
                    record = dict(self.records[key])
                    sink(edit(record) if edit else record)
            token_audit.write_shard(path, identity, k, self.items[k::2], emit)
        summary = token_audit.summarize(paths, self.config_sha256)
        path = folder / 'summary.json'
        path.write_text(json.dumps(summary))
        return summary, path

    def first(self, stream):
        return min(key for key, _ in self.items if key[0] == stream)

    def refused(self, path):
        with self.assertRaisesRegex(ValueError, 'trainer refuses') as caught:
            mem_pilot.check_audit(path, CONFIG)
        message = str(caught.exception)
        return json.loads(message[message.index('{'):])

    def test_passing_audit_feeds_every_row_to_the_pilot(self):
        summary, path = self.gate('passing')
        self.assertTrue(summary['launch_ready'], summary['errors'])
        audit = mem_pilot.check_audit(path, CONFIG)
        self.assertEqual(sum(len(v) for v in audit['longest'].values()), len(self.items))

    def test_tripwire_only_rows_feed_the_pilot(self):
        summary, path = self.gate('tripwire_only', lambda r: dict(r, over_tripwire=r['tokens'] > TRIPWIRE), TRIPWIRE)
        tripped = sum(v['over_tripwire'] for v in summary['streams'].values())
        self.assertTrue(0 < tripped < len(self.items), tripped)
        self.assertFalse(summary['launch_ready'])
        self.assertEqual(summary['errors'], [])
        audit = mem_pilot.check_audit(path, CONFIG)
        self.assertEqual(sum(len(v) for v in audit['longest'].values()), len(self.items))
        self.assertGreater(max(r['tokens'] for v in audit['longest'].values() for r in v), TRIPWIRE)

    def test_failed_row_refuses_although_the_longest_rows_omit_it(self):
        fetch_fields = ('stream', 'index', 'first_step', 'rank', 'seconds')
        cases = (('check_row', 'routing', lambda r: dict(r, check_row='ValueError: injected failure (synthetic control)')),
                 ('fetch', 'pose', lambda r: dict({k: r[k] for k in fetch_fields}, check_row='FileNotFoundError: frame')))
        for name, stream, fail in cases:
            with self.subTest(name):
                key = self.first(stream)
                summary, path = self.gate('failed_' + name, lambda r: fail(r) if (r['stream'], r['index']) == key else r)
                self.assertEqual(summary['errors'], [])
                self.assertEqual(summary['streams'][stream]['failed'], 1)
                self.assertNotIn(key[1], [r['index'] for r in summary['longest'][stream]])
                refused = self.refused(path)
                self.assertEqual(list(refused), [stream])
                self.assertEqual(refused[stream]['failed'], 1)
                self.assertEqual(refused[stream]['omitted_from_longest'], 1)

    def test_ceiling_violation_refuses(self):
        key = self.first('vqa')
        lowered = []
        token_audit.audit(self.rows, {**self.recipe, 'max_row_tokens': 9000}, self.receipt,
                          [item for item in self.items if item[0] == key], lowered.append)
        self.assertTrue(lowered[0]['over_ceiling'])
        self.assertIn('exceed 9000', lowered[0]['check_row'])
        flag_key = self.first('pointing')
        cases = (('encoded', key, lambda r: lowered[0]), ('flag_only', flag_key, lambda r: dict(r, over_ceiling=True)))
        for name, target, edit in cases:
            with self.subTest(name):
                summary, path = self.gate('ceiling_' + name, lambda r: edit(r) if (r['stream'], r['index']) == target else r)
                self.assertEqual(summary['errors'], [])
                refused = self.refused(path)
                self.assertEqual(list(refused), [target[0]])
                self.assertEqual(refused[target[0]]['over_ceiling'], 1)


if __name__ == '__main__':
    unittest.main()
