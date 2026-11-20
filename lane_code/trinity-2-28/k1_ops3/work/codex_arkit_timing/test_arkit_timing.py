"""CPU metadata tests; fixtures stay in memory or in this build directory."""
import copy
import math
from pathlib import Path
import unittest
from unittest import mock
import uuid

import arkit_timing as timing


class TimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = timing.load_bundle()
        cls.reader = timing.load_module('k1_test_reader', timing.FINALIZER)
        cls.result, cls.report = timing.evaluate(cls.bundle, cls.reader)

    def test_all_87_exact_and_75_reader_checked(self):
        self.assertTrue(self.report['passed'], self.report['failures'])
        self.assertEqual(len(self.report['agreement']), 87)
        self.assertTrue(all(all(r['field_agreement'].values()) for r in self.report['agreement']))
        self.assertEqual(len(self.report['uncovered']), 75)
        self.assertTrue(all(r['reader_passed'] for r in self.report['uncovered']))
        self.assertEqual(self.result['k1_finalize']['timing']['source_counts'],
                         {'d12_mp4': 138, 'frame_rates_07ca49df': 87, 'derived_wa_validated': 75})

    def test_one_ulp_disagreement_blocks_all_and_never_writes(self):
        original = timing.derive
        target = self.report['agreement'][0]['canonical']
        visited = []

        def planted(capture, wa, plan):
            visited.append(capture['canonical'])
            value, diagnostics = original(capture, wa, plan)
            if capture['canonical'] == target:
                value['fps'] = math.nextafter(value['fps'], math.inf)
            return value, diagnostics

        path = timing.ROOT / ('blocked_'+uuid.uuid4().hex+'.json')
        with mock.patch.object(timing, 'derive', side_effect=planted), \
                mock.patch.object(timing, 'write_new') as writer:
            report = timing.publish(self.bundle, self.reader, path)
        self.assertFalse(report['passed'])
        self.assertEqual(len(report['failures']), 1)
        self.assertEqual(report['failures'][0]['canonical'], target)
        self.assertEqual(len(visited), 87)
        self.assertEqual(report['uncovered'], [])
        writer.assert_not_called()
        self.assertFalse(path.exists())

    def test_planted_gap_reports_excess_not_sparse_sampling(self):
        spans = timing.intervals([(0, 100.0), (10, 101.0), (20, 102.3)], 10.0)
        self.assertTrue(spans[0]['sample_spacing_over_1_5_periods'])
        self.assertFalse(spans[0]['missing_interval_over_1_5_periods'])
        self.assertTrue(spans[1]['missing_interval_over_1_5_periods'])
        self.assertAlmostEqual(spans[1]['excess_s'], 0.3)

    def test_gap_survives_full_derivation(self):
        capture = next(c for c in self.bundle['manifest']['captures']
                       if c['canonical'] == self.report['agreement'][0]['canonical'])
        token = self.report['agreement'][0]['token']
        wa = copy.deepcopy(next(r for r in self.bundle['wa'] if r['s'] == token))
        plan = copy.deepcopy(self.bundle['plan'][token])
        split = sorted(r[0] for r in wa['frames'])[32]
        for r in wa['frames']:
            if r[0] >= split:
                r[5] += 0.3
        for r in plan['need']:
            if r[0] >= split:
                r[1] += 0.3
        wa['last_ts'] += 0.3
        value, diagnostic = timing.derive(capture, wa, plan)
        self.assertEqual(value['fps'], 10.0)
        self.assertEqual(len(diagnostic['gaps']['wa_dense']), 1)
        self.assertEqual(len(diagnostic['gaps']['plan_dense']), 1)

    def test_no_extra_capture_fields_or_other_edits(self):
        timing.validate_changes(self.bundle['manifest'], self.result)
        bad = copy.deepcopy(self.result)
        bad['captures'][0]['timing_source'] = 'new_value'
        with self.assertRaisesRegex(ValueError, 'Unexpected capture edit'):
            timing.validate_changes(self.bundle['manifest'], bad)

    def test_archive_count_is_not_reader_count(self):
        for row in self.report['agreement']+self.report['uncovered']:
            self.assertEqual(row['derived']['total_num_frames'], max(row['diagnostics']['anchor_indices'])+1)
            self.assertNotEqual(row['derived']['total_num_frames'], row['diagnostics']['archive_n_members'])
            self.assertTrue(row['diagnostics']['total_num_frames_lower_bound'])

    def test_exclusive_creation_and_output_boundary(self):
        path = timing.ROOT / ('exclusive_test_'+uuid.uuid4().hex+'.txt')
        timing.write_new(path, 'first\n')
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            timing.write_new(path, 'second\n')
        self.assertEqual(path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'Output must'):
            timing.write_new(timing.ROOT.parent/'forbidden_test_output.json', {})

    def test_first_token_and_bad_receipt(self):
        self.assertEqual(timing.first_tokens([{'canonical': 'x', 's': 'first'},
                                              {'canonical': 'x', 's': 'second'}]), {'x': 'first'})
        row = self.report['agreement'][0]
        capture = next(c for c in self.bundle['manifest']['captures'] if c['canonical'] == row['canonical'])
        wa = copy.deepcopy(next(r for r in self.bundle['wa'] if r['s'] == row['token']))
        wa['frames'][0][4] += 10
        with self.assertRaisesRegex(ValueError, 'dt_ms'):
            timing.derive(capture, wa, self.bundle['plan'][row['token']])

    def test_noninteger_rate_and_nonmonotonic_time_refuse(self):
        with self.assertRaisesRegex(ValueError, '0.5%'):
            timing.nominal_rate([(0, 0.0), (19, 2.0)])
        with self.assertRaisesRegex(ValueError, 'increase'):
            timing.nominal_rate([(0, 0.0), (10, 0.0)])

    def test_actual_reader_rejects_corrupted_values(self):
        row = self.report['agreement'][0]
        capture = copy.deepcopy(next(c for c in self.bundle['manifest']['captures']
                                    if c['canonical'] == row['canonical']))
        capture['model_row']['student_input'].update(row['derived'])
        capture['model_row']['student_input']['timestamps'][0] += 0.1
        with self.assertRaisesRegex(ValueError, 'timestamps'):
            self.reader.resolve_timing(capture, row['token'], 10.0, None, 10.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
