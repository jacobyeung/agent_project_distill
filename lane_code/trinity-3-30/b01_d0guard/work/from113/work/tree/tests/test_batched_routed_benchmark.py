"""Benchmark selection strips labels, enforces coverage and detects mismatches."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from student_pilot import carrier_c1_batch_benchmark as B


class BenchmarkTests(unittest.TestCase):
    def rows(self):
        return [dict(qid=f'{kind}-{i}', type=kind, ground_truth='SECRET', target='SECRET',
                     student_input=dict(frames=[dict(path='/fixture', sha256='a'*64)]*32,
                                        frame_indices=list(range(32)), timestamps=list(range(32)),
                                        fps=1, total_num_frames=32, question='Question', options=['A. option'],
                                        answer='SECRET')) for kind in B.TYPES for i in range(8)]

    def source(self, rows):
        path = Path(tempfile.mkdtemp()) / 'rows.jsonl'
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        return path

    def test_exact_balanced_selection_strips_answers(self):
        selected = B.select_rows(self.source(self.rows()))
        self.assertEqual(len(selected), 32)
        self.assertEqual([r['question_type'] for r in selected[:4]], list(B.TYPES))
        self.assertNotIn('SECRET', json.dumps(selected))
        with self.assertRaisesRegex(ValueError, 'eight'):
            B.select_rows(self.source(self.rows()[:-1]))
        rows = self.rows(); rows[1]['qid'] = rows[0]['qid']
        with self.assertRaisesRegex(ValueError, 'distinct'):
            B.select_rows(self.source(rows))

    def test_comparison_detects_lengths_values_calls_and_finish(self):
        row = dict(tokens=[1, 2], text='ab', calls=[], finish='eos')
        bad = dict(tokens=[1], text='a', calls=[{}], finish='call_limit')
        check = B.compare_records([row], [bad])[0]
        self.assertEqual(check['first_differing_token'], 1)
        self.assertFalse(any(check[k] for k in ('tokens_equal', 'text_equal', 'calls_equal', 'finish_equal')))
        self.assertEqual(B.compare_records([row], [{**row, 'tokens': [9, 2]}])[0]['first_differing_token'], 0)

    def test_report_times_both_arms_and_refuses_no_route(self):
        selected = B.select_rows(self.source(self.rows()))
        sizes = []
        def generate(model, processor, batch, **kwargs):
            def record(row):
                return dict(tokens=[len(row['qid']), 1], text=row['qid'],
                            calls=[dict(kind='ground')], finish='eos')
            sizes.append(len(batch) if isinstance(batch, list) else 1)
            return [record(row) for row in batch] if isinstance(batch, list) else record(batch)
        with mock.patch.object(B.decode, 'generate', side_effect=generate), \
             mock.patch('student_pilot.carrier_c1_run.move', side_effect=lambda batch, device: batch):
            report, outputs = B.benchmark(None, None, selected, lambda r: r, device='cpu')
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(len(outputs[4]), 32)
        self.assertEqual(sizes.count(4), 9)  # Eight timed groups plus one warmup.
        self.assertGreater(report['arms']['4']['items_per_hour'], 0.)
        def direct(model, processor, batch, **kwargs):
            row = dict(tokens=[1], text='', calls=[], finish='eos')
            return [row]*len(batch) if isinstance(batch, list) else row
        with mock.patch.object(B.decode, 'generate', side_effect=direct), \
             mock.patch('student_pilot.carrier_c1_run.move', side_effect=lambda batch, device: batch):
            report, _ = B.benchmark(None, None, selected, lambda r: r, device='cpu')
        self.assertEqual(report['status'], 'FAIL')
        self.assertTrue(report['tokens_and_calls_equal'])
        self.assertFalse(report['eight_routed_per_type'])


if __name__ == '__main__':
    unittest.main()
