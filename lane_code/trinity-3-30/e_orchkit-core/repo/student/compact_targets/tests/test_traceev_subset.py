from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

from student.compact_targets import traceev_subset as subset


SUPPORTS = {'traceev_count_list': ['object_counting'],
            'traceev_abs_distance': ['object_abs_distance'],
            'traceev_size': ['object_size_estimation'],
            'traceev_frames_all': ['obj_appearance_order', 'object_counting'],
            'traceev_frames_first': ['obj_appearance_order'],
            'traceev_frames_some': ['grounding'],
            'traceev_rel_quadrant': ['object_rel_direction_hard']}


class TraceEvidenceSubsetTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['COMPACT_TEST_OUTPUT']) / ('traceev_subset_' + uuid4().hex)
        self.root.mkdir(parents=True)
        self.serial = 0

    def entries(self, kind, count, scenes=200, prefix='scene', agree=None):
        result = []
        for ordinal in range(count):
            self.serial += 1
            result.append(subset.Entry(self.serial, 0, 0, '', f'{kind}_{self.serial}', kind,
                ('scannet', f'{prefix}{ordinal % scenes:04d}'), tuple(SUPPORTS[kind]), agree is False))
        return result

    def choose(self, entries, budget=1000, seed=20260925):
        selected, attempts = subset.select_entries(entries, budget, seed)
        counts = Counter(entry.kind for entry in selected)
        scenes = Counter(entry.scene for entry in selected)
        self.assertLessEqual(len(selected), budget)
        self.assertLessEqual(5 * sum(counts[kind] for kind in subset.FRAME_KINDS), len(selected))
        self.assertLessEqual(10 * counts['traceev_rel_quadrant'], len(selected))
        self.assertLessEqual(100 * max(scenes.values(), default=0), len(selected))
        self.assertEqual(len({entry.line for entry in selected}), len(selected))
        self.assertTrue(set(selected) <= set(entries))
        self.assertEqual(selected, sorted(selected, key=lambda entry: entry.line))
        self.assertEqual(attempts[-1]['selected'], len(selected))
        return selected

    def write_rows(self, entries, name='evidence_rows.jsonl', mixed_bytes=False):
        path = self.root / name
        with path.open('xb') as stream:
            for ordinal, entry in enumerate(entries):
                row = {'qid': entry.qid, 'question_type': entry.kind, 'dataset': entry.scene[0],
                       'scene': entry.scene[1], 'supports': list(entry.supports),
                       'source_qids': [f'source_{entry.line}'], 'source_traces': [],
                       'fact_key': [entry.scene[1], entry.kind, entry.line],
                       'question': 'These are frames of a video.\nSynthetic question?',
                       'target': '1.20, 0.80, 0.75', 'student_input': {'frames': [], 'options': []},
                       'evidence': {'synthetic': True, 'text': 'café'}, 'extractor_commit': '1' * 40,
                       'label_check': {'agree': False} if entry.disagreement else None}
                line = json.dumps(row, ensure_ascii=not mixed_bytes,
                                  separators=(', ', ': ') if ordinal % 2 else (',', ':')).encode()
                ending = b'\r\n' if mixed_bytes and ordinal % 2 else b'\n'
                if mixed_bytes and ordinal == len(entries) - 1:
                    ending = b''
                stream.write(line + ending)
        return path

    def test_weighted_quota_arithmetic_and_remainders(self):
        available = dict.fromkeys(subset.PRIMARY_KINDS, 50000)
        self.assertEqual(subset.priority_quotas(available, 25000), {
            'traceev_count_list': 10000, 'traceev_abs_distance': 7500, 'traceev_size': 7500})
        self.assertEqual(subset.priority_quotas(available, 1001), {
            'traceev_count_list': 401, 'traceev_abs_distance': 300, 'traceev_size': 300})
        for budget in range(101):
            quotas = subset.priority_quotas(available, budget)
            self.assertEqual(sum(quotas.values()), budget)
            for kind, weight in subset.PRIMARY_WEIGHTS.items():
                self.assertLess(abs(quotas[kind] - budget * weight / 10), 1)

    def test_quota_leftovers_redistribute_without_replacement(self):
        available = {'traceev_count_list': 100, 'traceev_abs_distance': 2000, 'traceev_size': 2000}
        self.assertEqual(subset.priority_quotas(available, 1000), {
            'traceev_count_list': 100, 'traceev_abs_distance': 450, 'traceev_size': 450})
        available['traceev_abs_distance'] = 50
        self.assertEqual(subset.priority_quotas(available, 1000), {
            'traceev_count_list': 100, 'traceev_abs_distance': 50, 'traceev_size': 850})
        self.assertEqual(subset.priority_quotas({'traceev_size': 20}, 1000), {
            'traceev_count_list': 0, 'traceev_abs_distance': 0, 'traceev_size': 20})

    def test_full_25000_row_budget(self):
        rows = sum((self.entries(kind, 15000) for kind in subset.PRIMARY_KINDS), [])
        rows += self.entries('traceev_frames_all', 5000)
        selected = self.choose(rows, budget=25000)
        self.assertEqual(len(selected), 25000)
        self.assertEqual(Counter(entry.kind for entry in selected), {
            'traceev_count_list': 10000, 'traceev_abs_distance': 7500, 'traceev_size': 7500})

    def test_quota_totals_and_availability_for_small_pools(self):
        for count in range(8):
            for distance in range(8):
                for size in range(8):
                    available = dict(zip(subset.PRIMARY_KINDS, (count, distance, size)))
                    for budget in (0, 1, 3, 10, 25):
                        quotas = subset.priority_quotas(available, budget)
                        self.assertEqual(sum(quotas.values()), min(budget, sum(available.values())))
                        for kind in subset.PRIMARY_KINDS:
                            self.assertLessEqual(quotas[kind], available[kind])
                            self.assertGreaterEqual(quotas[kind], 0)

    def test_oversubscribed_priority_kinds_split_40_30_30(self):
        rows = sum((self.entries(kind, 2000) for kind in subset.PRIMARY_KINDS), [])
        rows += self.entries('traceev_frames_all', 1000)
        selected = self.choose(rows)
        self.assertEqual(Counter(entry.kind for entry in selected), {
            'traceev_count_list': 400, 'traceev_abs_distance': 300, 'traceev_size': 300})

    def test_all_priority_rows_fit_and_frame_kinds_fill_in_order(self):
        primary = self.entries('traceev_count_list', 300) + self.entries('traceev_abs_distance', 200)
        primary += self.entries('traceev_size', 200)
        rows = primary + self.entries('traceev_frames_all', 100)
        rows += self.entries('traceev_frames_first', 500) + self.entries('traceev_frames_some', 500)
        rows += self.entries('traceev_rel_quadrant', 500)
        selected = self.choose(rows)
        self.assertTrue(set(primary) <= set(selected))
        self.assertEqual(Counter(entry.kind for entry in selected), {
            'traceev_count_list': 300, 'traceev_abs_distance': 200, 'traceev_size': 200,
            'traceev_frames_all': 100, 'traceev_frames_first': 100, 'traceev_rel_quadrant': 100})

    def test_frames_all_exhausts_frame_cap_before_other_frames(self):
        rows = self.entries('traceev_size', 800)
        rows += sum((self.entries(kind, 600) for kind in subset.FRAME_KINDS), [])
        counts = Counter(entry.kind for entry in self.choose(rows))
        self.assertEqual(counts, {'traceev_size': 800, 'traceev_frames_all': 200})

    def test_frames_some_fills_only_after_all_and_first(self):
        rows = self.entries('traceev_size', 800) + self.entries('traceev_frames_all', 50)
        rows += self.entries('traceev_frames_first', 50) + self.entries('traceev_frames_some', 1000)
        counts = Counter(entry.kind for entry in self.choose(rows))
        self.assertEqual(counts, {'traceev_size': 800, 'traceev_frames_all': 50,
                                  'traceev_frames_first': 50, 'traceev_frames_some': 100})

    def test_frame_cap_uses_actual_subset_size(self):
        rows = self.entries('traceev_size', 400) + self.entries('traceev_frames_all', 2000)
        selected = self.choose(rows, budget=25000)
        self.assertEqual(Counter(entry.kind for entry in selected), {
            'traceev_size': 400, 'traceev_frames_all': 100})

    def test_quadrant_cap_uses_actual_subset_size(self):
        rows = self.entries('traceev_size', 900) + self.entries('traceev_rel_quadrant', 3000)
        selected = self.choose(rows, budget=25000)
        self.assertEqual(Counter(entry.kind for entry in selected), {
            'traceev_size': 900, 'traceev_rel_quadrant': 100})

    def test_round_robin_balances_scenes_within_a_kind(self):
        rows = self.entries('traceev_size', 5000)
        selected = self.choose(rows, budget=400)
        self.assertEqual(set(Counter(entry.scene for entry in selected).values()), {2})

    def test_global_scene_cap_and_small_input_fixed_point(self):
        rows = self.entries('traceev_count_list', 1000, scenes=1, prefix='dominant')
        rows += self.entries('traceev_size', 1000)
        selected = self.choose(rows)
        self.assertEqual(len(selected), 1000)
        self.assertEqual(sum(entry.scene[1] == 'dominant0000' for entry in selected), 10)
        rows = self.entries('traceev_size', 9999, scenes=100)
        self.assertEqual(len(self.choose(rows, budget=25000)), 9900)

    def test_insufficient_scene_diversity_and_empty_input_are_reportable(self):
        self.assertEqual(self.choose(self.entries('traceev_size', 1000, scenes=99)), [])
        self.assertEqual(self.choose([], budget=25000), [])
        self.assertEqual(self.choose(self.entries('traceev_size', 200), budget=99), [])
        rows = self.entries('traceev_frames_all', 1000) + self.entries('traceev_rel_quadrant', 1000)
        self.assertEqual(self.choose(rows), [])

    def test_corrected_counts_precede_agreeing_and_uncompared_counts(self):
        ordinary = self.entries('traceev_count_list', 2000, agree=True)
        corrected = self.entries('traceev_count_list', 200, agree=False)
        selected = self.choose(ordinary + corrected, budget=400)
        self.assertTrue(set(corrected) <= set(selected))
        self.assertEqual(len(selected), 400)
        self.assertEqual(set(Counter(entry.scene for entry in selected).values()), {2})

    def test_seed_is_deterministic_and_changes_membership(self):
        rows = self.entries('traceev_size', 5000)
        first = self.choose(rows, budget=1000, seed=20260925)
        self.assertEqual(first, self.choose(rows, budget=1000, seed=20260925))
        self.assertNotEqual(first, self.choose(rows, budget=1000, seed=20260926))

    def test_subset_bytes_index_hashes_counts_and_room_size(self):
        rows = self.entries('traceev_size', 800) + self.entries('traceev_frames_all', 800)
        source = self.write_rows(rows, mixed_bytes=True)
        out = self.root / 'subset' / 'rows.jsonl'
        report = subset.select_file(source, out, max_rows=1000)
        original = source.read_bytes().splitlines(keepends=True)
        actual = out.read_bytes().splitlines(keepends=True)
        self.assertFalse(Counter(actual) - Counter(original))
        self.assertEqual(len(actual), 1000)
        self.assertEqual(report['input']['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(report['output']['sha256'], hashlib.sha256(out.read_bytes()).hexdigest())
        index_path = Path(str(out) + '.INDEX.jsonl')
        self.assertEqual(report['index']['sha256'], hashlib.sha256(index_path.read_bytes()).hexdigest())
        index = [json.loads(line) for line in index_path.read_bytes().splitlines()]
        self.assertEqual([entry['output_line'] for entry in index], list(range(1, 1001)))
        for entry, line in zip(index, actual):
            self.assertEqual(line, original[entry['input_line'] - 1])
            self.assertEqual(entry['sha256'], hashlib.sha256(line).hexdigest())
            self.assertEqual(entry['qid'], json.loads(line)['qid'])
            self.assertEqual(entry['input_bytes'], len(line))
        self.assertEqual(report['per_kind']['before']['traceev_frames_all'], 800)
        self.assertEqual(report['per_kind']['after']['traceev_frames_all'], 200)
        self.assertEqual(report['per_supported_type']['after']['object_counting'], 200)
        self.assertEqual(report['per_supported_type']['after']['obj_appearance_order'], 200)
        self.assertEqual(report['per_supported_type']['after']['room_size_estimation'], 0)
        self.assertIsNone(report['room_size']['evidence_kind'])
        self.assertLessEqual(report['scenes']['after']['max_share'], .01)
        self.assertEqual(json.loads(Path(str(out) + '.SELECTION.json').read_text()), report)

    def test_complete_selection_keeps_missing_final_newline(self):
        source = self.write_rows(self.entries('traceev_size', 101), mixed_bytes=True)
        out = self.root / 'subset.jsonl'
        subset.select_file(source, out)
        self.assertEqual(out.read_bytes(), source.read_bytes())
        self.assertFalse(out.read_bytes().endswith(b'\n'))

    def test_duplicate_input_lines_are_not_multiplied(self):
        source = self.write_rows(self.entries('traceev_size', 200))
        with source.open('ab') as stream:
            stream.write(source.read_bytes().splitlines(keepends=True)[0])
        out = self.root / 'subset.jsonl'
        subset.select_file(source, out)
        self.assertFalse(Counter(out.read_bytes().splitlines(keepends=True)) -
                         Counter(source.read_bytes().splitlines(keepends=True)))

    def test_cli_and_repeated_seed_produce_identical_rows_and_index(self):
        source = self.write_rows(self.entries('traceev_size', 1000))
        outputs = [self.root / f'cli_{i}.jsonl' for i in range(2)]
        for out in outputs:
            result = subprocess.run([sys.executable, '-B', '-m', 'student.compact_targets.traceev_subset',
                '--evidence', str(source), '--out', str(out), '--max-rows', '500', '--seed', '20260925'],
                check=True, capture_output=True, text=True, env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
            self.assertEqual(json.loads(result.stdout)['output']['rows'], 500)
        self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
        self.assertEqual(Path(str(outputs[0]) + '.INDEX.jsonl').read_bytes(),
                         Path(str(outputs[1]) + '.INDEX.jsonl').read_bytes())

    def test_invalid_budgets_and_metadata_fail_before_publication(self):
        for budget in (-1, 0, 25001):
            with self.subTest(budget=budget), self.assertRaisesRegex(ValueError, 'max_rows'):
                subset.select_entries([], budget, 20260925)
        for ordinal, row in enumerate(({'question_type': 'unknown'}, {'question_type': 'traceev_size'}, [])):
            path = self.root / f'invalid_{ordinal}.jsonl'
            path.write_text(json.dumps(row) + '\n')
            out = self.root / f'invalid_out_{ordinal}.jsonl'
            with self.subTest(row=row), self.assertRaises(ValueError):
                subset.select_file(path, out)
            self.assertFalse(out.exists())

    def test_existing_output_and_input_alias_are_never_overwritten(self):
        source = self.write_rows(self.entries('traceev_size', 200))
        original = source.read_bytes()
        with self.assertRaisesRegex(ValueError, 'input_output_alias'):
            subset.select_file(source, source)
        out = self.root / 'existing.jsonl'
        out.write_bytes(b'preserve me\n')
        with self.assertRaises(FileExistsError):
            subset.select_file(source, out)
        self.assertEqual(out.read_bytes(), b'preserve me\n')
        self.assertEqual(source.read_bytes(), original)

    def test_input_changes_do_not_publish_success_manifest(self):
        source = self.write_rows(self.entries('traceev_size', 200))
        select_entries = subset.select_entries
        def mutate(entries, max_rows, seed):
            selected = select_entries(entries, max_rows, seed)
            with source.open('ab') as stream:
                stream.write(b'\n')
            return selected
        out = self.root / 'changed.jsonl'
        with patch.object(subset, 'select_entries', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'input_changed'):
                subset.select_file(source, out)
        self.assertFalse(Path(str(out) + '.SELECTION.json').exists())


if __name__ == '__main__':
    unittest.main()
