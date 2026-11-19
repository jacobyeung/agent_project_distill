"""token_audit over the synthetic nested store of the dry run: the trainer's own encode and check_row pass
every planned row, a lowered ceiling flags the row instead of aborting the audit, and summarize grants
launch_ready only to complete, unique, single-run coverage (review sb_f64rev finding 2).
F64_WORK names a scratch directory these tests may write; they never write anywhere else."""
import hashlib
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

REVIEW_POSE_ROW = dict(stream='pose', index=0, tokens=9127, check_row='ok', over_ceiling=False, over_tripwire=False)


class TokenAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, setups = f64_dryrun.setup(CONFIG, ['a43'])
        cls.receipt, cls.processor, cls.rows = setups['a43']
        # The dry run has no bound r2_sampling table (f64_dryrun.STAND_INS); plan with the native sampler.
        cls.unbound = {k: v for k, v in cls.cfg.items() if k not in ('r2_identity', 'r2_sampling')}
        cls.recipe = cls.cfg['recipe']
        cls.items = token_audit.planned_rows(cls.unbound, cls.receipt, cls.recipe, 0, 1)
        cls.config_sha256 = token_audit.file_sha256(CONFIG)
        # Stand-in preparation pin: the camera/depth receipt the dry run reads.
        cls.preparation = file_pin(f64_dryrun.PREP)
        cls.tmp = Path(tempfile.mkdtemp(prefix='token_audit_', dir=WORK))
        identity = cls.identity()
        cls.shards = [cls.tmp / f'complete_{k}.jsonl' for k in range(2)]
        for k, path in enumerate(cls.shards):
            token_audit.write_shard(path, identity, k, cls.items[k::2], cls.real_audit)
        cls.records = {(r['stream'], r['index']): r for path in cls.shards
                       for r in map(json.loads, path.read_text().splitlines()[1:-1])}

    @classmethod
    def tearDownClass(cls):
        cls.rows.close()

    @classmethod
    def real_audit(cls, items, sink, recipe=None):
        token_audit.audit(cls.rows, recipe or cls.recipe, cls.receipt, items, sink)

    @classmethod
    def identity(cls, shards=2, end=1, run_end=1, preparation='bound', tripwire=token_audit.TRIPWIRE_TOKENS):
        return token_audit.identity_for(cls.config_sha256, cls.unbound, cls.receipt, cls.recipe, cls.items, 0, end,
                                        run_end, 16384, tripwire, shards,
                                        cls.preparation if preparation == 'bound' else preparation)

    def path(self, name):
        return Path(tempfile.mkdtemp(prefix=name + '_', dir=self.tmp)) / 'shard.jsonl'

    def replay(self, name, identity, shard, items, edit=None):
        """A shard written from the cached real records, optionally edited before the writer sees them."""
        path = self.path(name)
        def emit(part, sink):
            for key, _ in part:
                record = dict(self.records[key])
                sink(edit(record) if edit else record)
        token_audit.write_shard(path, identity, shard, items, emit)
        return path

    def summary(self, paths):
        return token_audit.summarize([str(p) for p in paths], self.config_sha256)

    def assert_blocked(self, summary, error):
        self.assertFalse(summary['launch_ready'])
        self.assertTrue(any(e.startswith(error) for e in summary['errors']), summary['errors'])

    def test_plan_covers_every_stream_once_per_row(self):
        streams = {stream for (stream, _), _ in self.items}
        self.assertEqual(streams, {'pose', 'vqa', 'routing', 'pointing'})
        self.assertEqual(len(self.items), len({key for key, _ in self.items}))

    def test_planned_rows_pass_at_64(self):
        for record in self.records.values():
            self.assertEqual(record['check_row'], 'ok', record)
            self.assertFalse(record['over_ceiling'])
            self.assertEqual(record['grid'][0][0], 64)
        self.assertTrue(all('suffix_tokens' in r for r in self.records.values() if r['stream'] == 'routing'))

    def test_lowered_ceiling_is_flagged(self):
        picked = [next(item for item in self.items if item[0][0] == 'vqa')]
        records = []
        self.real_audit(picked, records.append, {**self.recipe, 'max_row_tokens': 9000})
        self.assertTrue(records[0]['over_ceiling'])
        self.assertIn('exceed 9000', records[0]['check_row'])

    def test_complete_audit_is_launch_ready(self):
        summary = self.summary(self.shards)
        self.assertTrue(summary['launch_ready'], summary['errors'])
        self.assertEqual(summary['coverage'], dict(planned=len(self.items), audited=len(self.items), unique=len(self.items)))
        self.assertEqual(summary['identity']['preparation'], self.preparation)
        self.assertEqual(set(summary['longest']), {'pose', 'vqa', 'routing', 'pointing'})

    def test_reviewer_empty_shard(self):
        path = self.path('empty')
        path.write_text('')
        self.assert_blocked(self.summary([path]), 'shard_empty')

    def test_reviewer_single_pose_row(self):
        path = self.path('single_pose')
        path.write_text(json.dumps(REVIEW_POSE_ROW) + '\n')
        self.assert_blocked(self.summary([path]), 'shard_header_missing')

    def test_reviewer_duplicated_partial_shards(self):
        path = self.path('single_pose_twice')
        path.write_text(json.dumps(REVIEW_POSE_ROW) + '\n')
        summary = self.summary([path, path])
        self.assert_blocked(summary, 'shard_file_repeated')
        self.assert_blocked(summary, 'no_complete_shard')
        summary = self.summary([self.shards[0], self.shards[0]])
        self.assert_blocked(summary, 'shard_file_repeated')
        self.assert_blocked(summary, 'shards_missing:[1]')

    def test_duplicate_shard_index_from_another_file(self):
        copy = self.path('copy0')
        copy.write_text(self.shards[0].read_text())
        self.assert_blocked(self.summary([self.shards[0], copy, self.shards[1]]), 'shard_duplicate:0')

    def test_partial_and_missing_shards(self):
        lines = self.shards[0].read_text().splitlines(keepends=True)
        truncated = self.path('truncated')
        truncated.write_text(''.join(lines[:3]))
        self.assert_blocked(self.summary([truncated, self.shards[1]]), 'shard_incomplete')
        summary = self.summary([self.shards[0]])
        self.assert_blocked(summary, 'shards_missing:[1]')
        self.assert_blocked(summary, 'plan_not_covered')

    def test_mixed_runs(self):
        other = self.identity(tripwire=token_audit.TRIPWIRE_TOKENS + 1)
        path = self.replay('other_run', other, 1, self.items[1::2])
        self.assert_blocked(self.summary([self.shards[0], path]), 'mixed_runs')

    def test_record_missing_a_required_field(self):
        def drop(record):
            return {k: v for k, v in record.items() if k != 'tokens'} if record['stream'] == 'pose' else record
        path = self.replay('no_tokens', self.identity(), 1, self.items[1::2], drop)
        self.assert_blocked(self.summary([self.shards[0], path]), 'record_fields_missing')

    def test_record_outside_the_shard_plan(self):
        def move(record):
            return dict(record, index=record['index'] + 100) if record['stream'] == 'vqa' else record
        path = self.replay('moved', self.identity(), 1, self.items[1::2], move)
        self.assert_blocked(self.summary([self.shards[0], path]), 'shard_rows_differ_from_plan')

    def test_tampered_record_breaks_the_footer(self):
        lines = self.shards[1].read_text().splitlines(keepends=True)
        record = json.loads(lines[1])
        lines[1] = json.dumps(dict(record, tokens=1), sort_keys=True) + '\n'
        path = self.path('tampered')
        path.write_text(''.join(lines))
        self.assert_blocked(self.summary([self.shards[0], path]), 'shard_footer_differs')

    def test_short_horizon_wrong_config_and_unbound_preparation(self):
        short = self.identity(run_end=1000)
        paths = [self.replay(f'short{k}', short, k, self.items[k::2]) for k in range(2)]
        self.assert_blocked(self.summary(paths), 'horizon_short:1<1000')
        self.assert_blocked(token_audit.summarize([str(p) for p in self.shards], hashlib.sha256(b'x').hexdigest()),
                            'config_differs')
        unbound = self.identity(preparation=None)
        paths = [self.replay(f'unbound{k}', unbound, k, self.items[k::2]) for k in range(2)]
        self.assert_blocked(self.summary(paths), 'preparation_unbound')

    def test_failed_or_long_rows_block_launch(self):
        def fail(record):
            return dict(record, check_row='ValueError: x', over_tripwire=True) if record['stream'] == 'routing' else record
        path = self.replay('failed', self.identity(), 1, self.items[1::2], fail)
        summary = self.summary([self.shards[0], path])
        self.assertFalse(summary['launch_ready'])
        self.assertEqual(summary['errors'], [])
        self.assertTrue(summary['flagged'] and all(r['stream'] == 'routing' for r in summary['flagged']))

    def test_gpu_pilot_takes_the_longest_rows_of_a_complete_audit(self):
        summary_path = self.tmp / 'summary.json'
        summary_path.write_text(json.dumps(self.summary(self.shards)))
        audit = mem_pilot.check_audit(summary_path, CONFIG)
        from student_pilot.carrier_c1_data import mixed_indices
        counts = {k: v['count'] for k, v in self.receipt['streams'].items()}
        layout = next(mixed_indices(counts, 1, training_mode='final', mix=self.recipe['mix'], world=4))
        plan, tokens = mem_pilot.longest_plan(layout, audit['longest'], 4)
        self.assertEqual([s for s, _ in plan], [s for s, _ in layout])
        self.assertEqual(len(plan) * 4, self.recipe['global_batch'])
        first = {}
        for (stream, indices), values in zip(plan, tokens):
            first.setdefault(stream, (indices, values))
        for stream, (indices, values) in first.items():
            ranked = audit['longest'][stream]
            self.assertEqual(values, [r['tokens'] for r in ranked[:4]] if len(ranked) >= 4 else values)
            self.assertEqual(max(values), ranked[0]['tokens'])
        edited = json.loads(summary_path.read_text())
        edited['longest']['pose'] = edited['longest']['pose'][1:]
        tampered = self.tmp / 'summary_edited.json'
        tampered.write_text(json.dumps(edited))
        with self.assertRaisesRegex(ValueError, 'differs from its shards'):
            mem_pilot.check_audit(tampered, CONFIG)
        partial = self.tmp / 'summary_partial.json'
        partial.write_text(json.dumps(self.summary(self.shards[:1])))
        with self.assertRaisesRegex(ValueError, 'not complete coverage'):
            mem_pilot.check_audit(partial, CONFIG)


if __name__ == '__main__':
    unittest.main()
