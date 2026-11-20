"""Small real-input score reproduction and room-exclusion checks."""
import importlib.util
from pathlib import Path
import statistics
import unittest

spec = importlib.util.spec_from_file_location('ledger', Path(__file__).with_name('ledger.py'))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class Reproduction(unittest.TestCase):
    def test_capture_scores_and_loro(self):
        rows, _, counts = ledger.capture_rows()
        self.assertEqual(counts, dict(T1=150, T2=150, dense64=150))
        self.assertAlmostEqual(statistics.mean(r['T1'] for r in rows), 58.6, places=10)
        ledger.fit_constants(rows)
        heldout = rows[0]['room']
        before = {r['item_id']: (r['class_constant_m'], r['global_constant_m'])
                  for r in rows if r['room'] == heldout}
        for r in rows:
            if r['room'] == heldout:
                r['truth_m'] = 9876.5
        ledger.fit_constants(rows)
        after = {r['item_id']: (r['class_constant_m'], r['global_constant_m'])
                 for r in rows if r['room'] == heldout}
        self.assertEqual(before, after)

    def test_four_index_reads(self):
        reads, checks, _ = ledger.load_corpus()
        self.assertEqual(len(checks), 4)
        self.assertEqual(sum(len(v) for v in checks.values()), 8)
        for rid, arms in checks.items():
            for arm, v in arms.items():
                self.assertTrue(v['match'], (rid, arm))
                self.assertAlmostEqual(v['actual']['mean_score'], v['expected']['mean_score'], places=12)
        for _, (_, direct) in ledger.READS.items():
            self.assertEqual(sum(r['type'] == 'object_abs_distance' for r in reads[direct]), 0)


if __name__ == '__main__':
    unittest.main()
