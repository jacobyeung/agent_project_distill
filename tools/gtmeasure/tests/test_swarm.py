import copy
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import unittest
import uuid

from tools.gtmeasure.swarm import (
    AdmissionError, FAMILIES, Guard, check_answeronly, check_gt, check_rendered,
    make_trainer_split, materialize_row, select_balanced, verify_frames,
)
from tools.gtmeasure.targets import render_target


def rgb_input():
    return {
        'question': 'How many chairs are in this room?', 'options': [],
        'fps': 2.0, 'frame_indices': list(range(32)),
        'timestamps': [index / 2 for index in range(32)], 'total_num_frames': 32,
        'frames': [{'path': '/fixture/frame.png', 'sha256': 'a' * 64} for _ in range(32)],
    }


def count_row():
    observations = [
        'The chair instance 3 has center (1.00, 2.00, 3.00) meters in the camera0 frame.',
        'The chair instance 7 has center (4.00, 5.00, 6.00) meters in the camera0 frame.',
        'The scene contains 2 distinct chair instances.',
    ]
    return {
        'qid': 'gtmeasure_scannet__scene0000_02_00001', 'dataset': 'scannet',
        'scene': 'scene0000_02', 'category': 'object_counting',
        'family': 'gtm_object_count', 'source': 'gtmeasure_v1',
        'source_question_type': 'absolute_count', 'object_ids': [3, 7],
        'frame_index': None, 'generation_commit': 'b' * 40, 'config_sha256': 'c' * 64,
        'student_input': rgb_input(), 'observations': observations, 'derivations': [],
        'target': render_target(observations, '2'),
        'ground_truth': {'answer': '2', 'units': 'instances', 'value': 2,
                         'measurements': [{'rounded_value': '2', 'value_si': 2,
                                           'units': 'instances', 'object_ids': [3, 7]}]},
    }


def mc_row():
    row = count_row()
    labels = ['chair', 'table', 'lamp', 'desk']
    values = ['1.1', '0.8', '2.0', '3.0']
    row.update(family='gtm_object_distance', source_question_type='relative_distance_object',
               category='object_rel_distance', object_ids=[1, 2, 3, 4, 5])
    row['student_input'].update(
        question='Which object is closest to the door?\nOptions:\nA. chair\nB. table\nC. lamp\nD. desk',
        options=labels,
    )
    row['observations'] = [f'The closest-point distance from the door to the nearest {label} is {value} meters.'
                           for label, value in zip(labels, values)]
    row['derivations'] = ['The table has the smallest distance, so the answer is B.']
    row['ground_truth'] = {
        'answer': 'B', 'units': 'meters',
        'measurements': [{'label': label, 'rounded_value': value, 'units': 'meters',
                          'value_si': float(value), 'object_ids': [1, index + 2]}
                         for index, (label, value) in enumerate(zip(labels, values))],
    }
    row['target'] = render_target(row['observations'], 'B', row['derivations'])
    return row


def guard_for(*rows):
    return Guard(
        train_qids={row['qid'] for row in rows}, heldout_qids={'gtmeasure_heldout'},
        train_groups={'scannet/scene0000'}, heldout_groups={'scannet/scene0010'},
        forbidden_qids={'benchmark_qid'}, blocked_groups={('scannet', 'scene0123')},
    )


def rebuild(row):
    row['target'] = render_target(row['observations'], row['ground_truth']['answer'], row['derivations'])
    return row


class AdmissionTests(unittest.TestCase):
    def test_count_copies_target_and_recomputes_roster(self):
        row = count_row()
        checks = check_gt(row, guard_for(row))
        self.assertEqual(checks['answer'], '2')
        self.assertEqual(checks['derivation'], 'distinct-instance-count')
        self.assertEqual(checks['target_bytes'], len(row['target'].encode()))

    def test_nearest_option_is_recomputed_from_displayed_measurements(self):
        row = mc_row()
        self.assertEqual(check_gt(row, guard_for(row))['derivation'], 'unique-displayed-minimum')

    def test_wrong_count_roster_is_refused(self):
        row = count_row()
        row['observations'][1] = row['observations'][0]
        rebuild(row)
        with self.assertRaisesRegex(AdmissionError, 'count_roster'):
            check_gt(row, guard_for(row))

    def test_target_fact_mutation_is_refused(self):
        row = count_row()
        row['target'] = row['target'].replace('(1.00,', '(9.00,')
        with self.assertRaisesRegex(AdmissionError, 'source_target'):
            check_gt(row, guard_for(row))

    def test_numeric_answer_must_match_exact_bytes(self):
        row = count_row()
        row['target'] = row['target'][:-1] + '2.0'
        with self.assertRaisesRegex(AdmissionError, 'source_target'):
            check_gt(row, guard_for(row))

    def test_marker_suffix_and_length_are_required(self):
        for transform in (lambda text: text.replace('End of reasoning.', 'Continue.'),
                          lambda text: text + '\n2', lambda text: text + '\n'):
            row = count_row()
            row['target'] = transform(row['target'])
            with self.assertRaises(AdmissionError):
                check_gt(row, guard_for(row))
        row = count_row()
        with self.assertRaisesRegex(AdmissionError, 'target_length'):
            check_gt(row, guard_for(row), max_bytes=50)

    def test_wrong_mc_derivation_is_refused(self):
        row = mc_row()
        row['derivations'] = ['The chair has the smallest distance, so the answer is B.']
        rebuild(row)
        with self.assertRaisesRegex(AdmissionError, 'mc_derivation'):
            check_gt(row, guard_for(row))

    def test_mc_rounding_tie_is_refused(self):
        row = mc_row()
        row['ground_truth']['measurements'][0]['rounded_value'] = '0.8'
        row['observations'][0] = row['observations'][0].replace('1.1', '0.8')
        rebuild(row)
        with self.assertRaisesRegex(AdmissionError, 'mc_tie'):
            check_gt(row, guard_for(row))

    def test_mc_option_mapping_drift_is_refused(self):
        row = mc_row()
        row['student_input']['options'][0] = 'sofa'
        with self.assertRaisesRegex(AdmissionError, 'mc_options'):
            check_gt(row, guard_for(row))

    def test_unsupported_numeric_derivation_is_refused(self):
        row = count_row()
        row['derivations'] = ['The coordinates imply 2 chairs.']
        rebuild(row)
        with self.assertRaisesRegex(AdmissionError, 'unsupported_derivation'):
            check_gt(row, guard_for(row))

    def test_room_area_is_an_observation_not_a_bounds_product(self):
        row = count_row()
        row.update(family='gtm_room_size', source_question_type='absolute_size_room',
                   category='room_size_estimation', object_ids=[9])
        row['observations'] = [
            'The floor bounds in camera0 XY are X [0.00, 4.00] meters and Y [0.00, 4.00] meters, with extents (4.00, 4.00) meters.',
            'The floor area is 8.0 square meters.',
        ]
        row['ground_truth'] = {'answer': '8.0', 'units': 'square meters',
                               'measurements': [{'rounded_value': '8.0', 'value_si': 8.0,
                                                 'units': 'square meters', 'object_ids': [9]}]}
        rebuild(row)
        self.assertEqual(check_gt(row, guard_for(row))['derivation'], 'measured-scalar-no-derivation')

    def test_unknown_and_published_heldout_qids_are_refused(self):
        row = count_row()
        guard = guard_for(row)
        for qid in ('unknown', 'gtmeasure_heldout', 'benchmark_qid'):
            bad = copy.deepcopy(row)
            bad['qid'] = qid
            with self.assertRaises(AdmissionError):
                check_gt(bad, guard)

    def test_heldout_scan_alias_and_benchmark_scene_are_refused(self):
        row = count_row()
        for scene in ('scene0010_99', 'scene0123_02', 'scene0999_00'):
            bad = copy.deepcopy(row)
            bad['scene'] = scene
            with self.assertRaises(AdmissionError):
                check_gt(bad, guard_for(bad))

    def test_heldout_mode_is_explicit_and_cannot_admit_training(self):
        row = count_row()
        with self.assertRaises(AdmissionError):
            check_gt(row, guard_for(row), side='heldout')

    def test_privileged_student_input_is_refused(self):
        row = count_row()
        row['student_input']['camera_poses'] = []
        with self.assertRaisesRegex(AdmissionError, 'rgb_schema'):
            check_gt(row, guard_for(row))

    def test_answeronly_keeps_control_bytes_and_uses_trainer_eos(self):
        row = count_row()
        row['target'] = '2'
        entry = {'qid': row['qid'], 'answer': '2'}
        checks = check_answeronly(row, entry, b'2\n', guard_for(row))
        self.assertEqual(checks['end_cue'], 'trainer-eos')
        with self.assertRaisesRegex(AdmissionError, 'answeronly_bytes'):
            check_answeronly(row, entry, b'2.0\n', guard_for(row))


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = Path(os.environ['H5_TEST_OUTPUT'])
        cls.root = base / uuid.uuid4().hex
        cls.root.mkdir(parents=True, exist_ok=False)

    def test_materialization_preserves_semantic_bytes_and_records_commit(self):
        row = count_row()
        entry = materialize_row(self.root / 'one', row, 'd' * 40, 'e' * 64, 'f' * 64)
        output = json.loads(Path(entry['row_path']).read_text())
        self.assertEqual(output['target'], row['target'])
        self.assertEqual(output['student_input'], row['student_input'])
        self.assertEqual(entry['answer'], row['ground_truth']['answer'])
        self.assertEqual(entry['validation_commit'], 'd' * 40)
        check_rendered(row, entry, 'd' * 40, 'e' * 64, 'f' * 64)

    def test_symmetric_row_and_target_mutation_is_refused_against_source(self):
        row = count_row()
        entry = materialize_row(self.root / 'mutated', row, 'd' * 40, 'e' * 64, 'f' * 64)
        target = row['target'].replace('(1.00,', '(9.00,')
        output = json.loads(Path(entry['row_path']).read_text())
        output['target'] = target
        Path(entry['row_path']).write_text(json.dumps(output))
        Path(entry['target_path']).write_text(target)
        entry['row_sha256'] = hashlib.sha256(Path(entry['row_path']).read_bytes()).hexdigest()
        entry['sha256'] = hashlib.sha256(target.encode()).hexdigest()
        with self.assertRaisesRegex(AdmissionError, 'rendered_fidelity'):
            check_rendered(row, entry, 'd' * 40, 'e' * 64, 'f' * 64)

    def test_candidate_source_metadata_drift_is_refused(self):
        row = count_row()
        entry = materialize_row(self.root / 'source_metadata', row, 'd' * 40, 'e' * 64, 'f' * 64)
        for field, value in (('pool', 'foreign'), ('source_index_sha256', '0' * 64)):
            bad = {**entry, field: value}
            with self.assertRaisesRegex(AdmissionError, 'rendered_source_metadata'):
                check_rendered(row, bad, 'd' * 40, 'e' * 64, 'f' * 64)

    def test_frame_hash_drift_is_refused(self):
        row = count_row()
        path = self.root / 'frame.png'
        path.write_bytes(b'fixture-image')
        frame = {'path': str(path), 'sha256': hashlib.sha256(b'fixture-image').hexdigest()}
        row['student_input']['frames'] = [frame] * 32
        verify_frames([row])
        path.write_bytes(b'changed-image')
        with self.assertRaisesRegex(AdmissionError, 'frame_hash'):
            verify_frames([row])

    def test_balanced_selection_is_order_independent(self):
        rows = [{'qid': f'{family}_{index}', 'family': family} for family in FAMILIES for index in range(5)]
        selected = select_balanced(rows, size=10, seed=17)
        self.assertEqual(Counter(row['family'] for row in selected), {family: 2 for family in FAMILIES})
        self.assertEqual(selected, select_balanced(list(reversed(rows)), size=10, seed=17))
        with self.assertRaisesRegex(AdmissionError, 'insufficient_family'):
            select_balanced(rows[:-4], size=10, seed=17)

    def test_split_keeps_heldout_context_out_of_training_index(self):
        row = count_row()
        held = copy.deepcopy(row)
        held.update(qid='gtmeasure_heldout', scene='scene0010_02')
        split = make_trainer_split([row], [held], [], 'd' * 40, 'e' * 64)
        self.assertEqual(split['schema'], 'provisional-whole-scene-split-v1')
        self.assertEqual(split['train_candidate_qids'], [row['qid']])
        self.assertEqual(split['heldout_qids'], [held['qid']])
        self.assertEqual(split['train_group_ids'], ['scannet/scene0000'])
        self.assertEqual(split['heldout_group_ids'], ['scannet/scene0010'])
        held['scene'] = 'scene0000_99'
        with self.assertRaisesRegex(AdmissionError, 'split_overlap'):
            make_trainer_split([row], [held], [], 'd' * 40, 'e' * 64)


if __name__ == '__main__':
    unittest.main()
