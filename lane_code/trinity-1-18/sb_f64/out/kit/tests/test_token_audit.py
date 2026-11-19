"""token_audit over the synthetic nested store of the dry run: the trainer's own encode and check_row
pass every planned row, and a lowered ceiling flags the row instead of aborting the audit."""
import json
import sys
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT / 'scripts')]
CONFIG = KIT / 'configs' / 'r1_config_f64.json'

import f64_dryrun  # noqa: E402
import token_audit  # noqa: E402


class TokenAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, setups = f64_dryrun.setup(CONFIG, ['a43'])
        cls.receipt, cls.processor, cls.rows = setups['a43']
        # The dry run has no bound r2_sampling table (f64_dryrun.STAND_INS); plan with the native sampler.
        unbound = {k: v for k, v in cls.cfg.items() if k not in ('r2_identity', 'r2_sampling')}
        cls.items = token_audit.planned_rows(unbound, cls.receipt, cls.cfg['recipe'], 1)

    @classmethod
    def tearDownClass(cls):
        cls.rows.close()

    def run_audit(self, recipe, items):
        records = []
        token_audit.audit(self.rows, recipe, self.receipt, items, records.append)
        return records

    def test_plan_covers_every_stream_once_per_row(self):
        streams = {stream for (stream, _), _ in self.items}
        self.assertEqual(streams, {'pose', 'vqa', 'routing', 'pointing'})
        self.assertEqual(len(self.items), len({key for key, _ in self.items}))

    def test_planned_rows_pass_at_64(self):
        picked = [next(item for item in self.items if item[0][0] == s) for s in ('pose', 'routing')]
        records = self.run_audit(self.cfg['recipe'], picked)
        for record in records:
            self.assertEqual(record['check_row'], 'ok', record)
            self.assertFalse(record['over_ceiling'])
            self.assertEqual(record['grid'][0][0], 64)
        self.assertIn('suffix_tokens', records[1])

    def test_lowered_ceiling_is_flagged(self):
        picked = [next(item for item in self.items if item[0][0] == 'vqa')]
        record = self.run_audit({**self.cfg['recipe'], 'max_row_tokens': 9000}, picked)[0]
        self.assertTrue(record['over_ceiling'])
        self.assertIn('exceed 9000', record['check_row'])

    def test_summarize_marks_launch_blockers(self):
        tmp = Path(f64_dryrun.WORK) / 'token_audit_test'
        tmp.mkdir(parents=True, exist_ok=True)
        shard = tmp / f'shard_{id(self)}.jsonl'
        shard.write_text(''.join(json.dumps(r) + '\n' for r in (
            dict(stream='routing', index=0, tokens=17000, over_ceiling=True, over_tripwire=True, check_row='ValueError: x'),
            dict(stream='pose', index=1, tokens=9127, over_ceiling=False, over_tripwire=False, check_row='ok'))))
        out = tmp / f'summary_{id(self)}.json'
        token_audit.summarize(type('A', (), dict(shards=[shard], out=out))())
        summary = json.loads(out.read_text())
        self.assertFalse(summary['launch_ready'])
        self.assertEqual(summary['streams']['routing']['over_ceiling'], 1)
        self.assertEqual(summary['flagged'][0]['tokens'], 17000)


if __name__ == '__main__':
    unittest.main()
