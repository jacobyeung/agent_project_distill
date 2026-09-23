import copy
from decimal import Decimal
import hashlib
import unittest

import numpy as np

from fixtures import fixture_root, make_scene
from test_contracts import authorities
from tools.gtmeasure.formats import harvest
from tools.gtmeasure.io import pin, write_jsonl
from tools.gtmeasure.questions import generate_scene, rewrite_room_row
from tools.gtmeasure.split import SplitPolicy


def source_room(answer='20.0', unit='square meters', video='scannet/scene0000_00.mp4'):
    return {'question_type': 'absolute_size_room', 'video': video, 'conversations': [
        {'from': 'human', 'value': f'<image>\nWhat is the room size in {unit}?'},
        {'from': 'gpt', 'value': answer}]}


class RoomLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_root()
        cls.scene = make_scene(cls.root / 'scene')
        samples = authorities()
        samples['vsi']['samples']['absolute_size_room'].append({
            'line': 12, 'question': 'What is the room area in square feet?', 'answer': '100'})
        cls.conventions = harvest(samples, structure='v2')
        cls.policy = SplitPolicy({'seed': 17, 'validation_fraction': .1,
                                 'train_scenes': ['scannet/scene0000'], 'heldout_scenes': ['scannet/scene0010']})

    def labels(self, rows=None, identities=None, blocked=(), policy=None):
        from tools.gtmeasure.room_labels import RoomLabels

        path = fixture_root() / 'vsi590k.jsonl'
        write_jsonl(path, [source_room()] if rows is None else rows)
        return RoomLabels(pin(path), identities or [('scannet', 'scene0000_00')],
                          policy or self.policy, set(blocked))

    def room_rows(self, labels, scene=None):
        rows, coverage = generate_scene(scene or self.scene, self.conventions, density=30,
                                        structure='v2', room_labels=labels)
        return [row for row in rows if row['family'] == 'gtm_room_size'], coverage

    def test_missing_authenticated_source_defers_instead_of_using_floor_area(self):
        rows, coverage = generate_scene(self.scene, self.conventions, density=30, structure='v2')
        self.assertFalse([row for row in rows if row['family'] == 'gtm_room_size'])
        self.assertEqual(coverage['rejections']['room_label_unavailable'], 1)

    def test_holes_and_occluders_keep_the_full_room_label(self):
        labels = self.labels()

        def rectangle(x0, y0, x1, y1):
            return [[[x0, y0, 0.], [x1, y0, 0.], [x1, y1, 0.]],
                    [[x0, y0, 0.], [x1, y1, 0.], [x0, y1, 0.]]]

        ring = rectangle(0., 0., 4., 1.) + rectangle(0., 3., 4., 4.) + rectangle(0., 1., 1., 3.) + rectangle(3., 1., 4., 3.)
        for triangles in (np.array(ring), np.array([[[0., 0., 0.], [4., 0., 0.], [0., 4., 0.]]])):
            scene = copy.deepcopy(self.scene)
            next(obj for obj in scene.objects if obj['label'] == 'floor')['triangles'] = triangles
            rows, _ = self.room_rows(labels, scene)
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(row['ground_truth']['measurements'][0]['value_si'], 20.0)
                self.assertEqual(row['object_ids'], [])
                self.assertFalse(any('bounds' in line or 'floor' in line for line in row['observations']))

    def test_absent_floor_geometry_does_not_discard_a_valid_room_label(self):
        scene = copy.deepcopy(self.scene)
        scene.objects = [obj for obj in scene.objects if obj['label'] != 'floor']
        rows, _ = self.room_rows(self.labels(), scene)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row['ground_truth']['measurements'][0]['value_si'] == 20 for row in rows))

    def test_square_feet_source_converts_once_to_each_declared_unit(self):
        rows, _ = self.room_rows(self.labels([source_room('100', 'square feet')]))
        by_unit = {row['ground_truth']['units']: row for row in rows}
        self.assertEqual(by_unit['square feet']['ground_truth']['answer'], '100')
        self.assertEqual(by_unit['square meters']['ground_truth']['answer'], '9.3')
        for row in rows:
            self.assertEqual(Decimal(str(row['ground_truth']['measurements'][0]['value_si'])), Decimal('9.290304'))
            self.assertEqual(row['observations'][0], 'The same-scene full-room label is 100 square feet.')
            self.assertIn(f'The full-room area is {row["ground_truth"]["answer"]} {row["ground_truth"]["units"]}.', row['observations'])

    def test_square_meters_source_converts_to_square_feet(self):
        rows, _ = self.room_rows(self.labels([source_room('9.290304')]))
        feet, = [row for row in rows if row['ground_truth']['units'] == 'square feet']
        self.assertEqual(feet['ground_truth']['answer'], '100')
        self.assertEqual(feet['provenance']['room_label']['answer'], '9.290304')

    def test_missing_same_scan_label_defers(self):
        rows, coverage = self.room_rows(self.labels([source_room(video='scannet/scene0000_01.mp4')]))
        self.assertEqual(rows, [])
        self.assertEqual(coverage['rejections']['room_label_missing'], 1)

    def test_dataset_identity_never_falls_back_to_a_matching_scan_name(self):
        rows, coverage = self.room_rows(self.labels([source_room(video='scannetppv2/scene0000_00.mp4')]))
        self.assertEqual(rows, [])
        self.assertEqual(coverage['rejections']['room_label_missing'], 1)

    def test_heldout_and_benchmark_scene_labels_are_never_admitted(self):
        from tools.gtmeasure.room_labels import RoomLabelDeferred

        labels = self.labels([source_room(video='scannet/scene0010_00.mp4')],
                             identities=[('scannet', 'scene0010_00')])
        with self.assertRaisesRegex(RoomLabelDeferred, 'not_training'):
            labels.lookup('scannet', 'scene0010_00')
        rows, coverage = self.room_rows(self.labels(blocked=[('scannet', 'scene0000')]))
        self.assertEqual(rows, [])
        self.assertEqual(coverage['rejections']['room_label_benchmark_scene'], 1)

    def test_invalid_or_ambiguous_labels_defer(self):
        cases = [source_room(value) for value in ('nan', 'inf', '0', '-1', '4.4 square meters', '', '1' + '0' * 400)]
        cases += [source_room(unit='meters'), source_room(unit='square meters or square feet')]
        malformed = source_room()
        malformed['conversations'].append({'from': 'gpt', 'value': '30'})
        cases.append(malformed)
        for row in cases:
            with self.subTest(source=row):
                rows, coverage = self.room_rows(self.labels([row]))
                self.assertEqual(rows, [])
                self.assertEqual(coverage['rejections']['room_label_invalid'], 1)

    def test_conflicting_labels_defer_without_averaging_or_selecting_a_fit(self):
        rows, coverage = self.room_rows(self.labels([source_room('20.0'), source_room('20.1')]))
        self.assertEqual(rows, [])
        self.assertEqual(coverage['rejections']['room_label_conflict'], 1)

    def test_equivalent_labels_keep_the_first_exact_source_line(self):
        labels = self.labels([source_room('100', 'square feet'), source_room('9.290304')])
        label = labels.lookup('scannet', 'scene0000_00')
        self.assertEqual(label['source_line'], 1)
        self.assertEqual(label['answer'], '100')
        self.assertEqual(label['agreeing_source_lines'], [1, 2])
        self.assertEqual(label['value_si_decimal'], '9.29030400')

    def test_provenance_pins_file_line_bytes_and_the_exact_scene(self):
        source = source_room('20.0')
        labels = self.labels([{'question_type': 'unrelated'}, source])
        label = labels.lookup('scannet', 'scene0000_00')
        from tools.gtmeasure.io import canonical

        self.assertEqual(label['source_line'], 2)
        self.assertEqual(label['source_line_sha256'], hashlib.sha256((canonical(source) + '\n').encode()).hexdigest())
        self.assertEqual(label['source']['sha256'], labels.authority['sha256'])
        self.assertEqual((label['dataset'], label['scene']), ('scannet', 'scene0000_00'))
        label['answer'] = '999'
        self.assertEqual(labels.lookup('scannet', 'scene0000_00')['answer'], '20.0')

    def test_source_hash_drift_refuses_the_index(self):
        from tools.gtmeasure.room_labels import RoomLabels

        path = fixture_root() / 'vsi590k.jsonl'
        write_jsonl(path, [source_room()])
        spec = pin(path)
        spec['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'digest'):
            RoomLabels(spec, [('scannet', 'scene0000_00')], self.policy, set())

    def test_rewrite_preserves_qid_rgb_question_units_and_original_row(self):
        rows, _ = self.room_rows(self.labels([source_room('8.0')]))
        row, = [row for row in rows if row['ground_truth']['units'] == 'square meters']
        original = copy.deepcopy(row)
        repaired = rewrite_room_row(row, self.conventions, self.labels(), commit='c' * 40, config_sha='d' * 64)
        self.assertEqual(row, original)
        for key in ('qid', 'dataset', 'scene', 'student_input', 'source_question_type', 'family'):
            self.assertEqual(row[key], repaired[key])
        self.assertEqual(repaired['ground_truth']['units'], row['ground_truth']['units'])
        self.assertEqual(repaired['ground_truth']['answer'], '20.0')
        self.assertEqual(repaired['generation_commit'], 'c' * 40)
        self.assertEqual(repaired['config_sha256'], 'd' * 64)
        self.assertEqual(repaired['observations'], ['The same-scene full-room label is 20.0 square meters.',
                                                  'The full-room area is 20.0 square meters.'])

    def test_rewrite_missing_label_and_unit_disagreement_fail_closed(self):
        from tools.gtmeasure.room_labels import RoomLabelDeferred

        rows, _ = self.room_rows(self.labels())
        row = rows[0]
        with self.assertRaisesRegex(RoomLabelDeferred, 'missing'):
            rewrite_room_row(row, self.conventions, self.labels([]), commit='c' * 40, config_sha='d' * 64)
        changed = copy.deepcopy(row)
        changed['ground_truth']['units'] = 'square feet' if row['ground_truth']['units'] == 'square meters' else 'square meters'
        with self.assertRaisesRegex(ValueError, 'unit disagree'):
            rewrite_room_row(changed, self.conventions, self.labels(), commit='c' * 40, config_sha='d' * 64)

    def test_rewrite_refuses_non_room_rows(self):
        rows, _ = generate_scene(self.scene, self.conventions, density=30, structure='v2')
        with self.assertRaisesRegex(ValueError, 'requires a room'):
            rewrite_room_row(rows[0], self.conventions, self.labels(), commit='c' * 40, config_sha='d' * 64)

    def test_exact_midpoint_conversion_defers_instead_of_guessing_rounding(self):
        rows, coverage = self.room_rows(self.labels([source_room('20.05')]))
        self.assertFalse([row for row in rows if row['ground_truth']['units'] == 'square meters'])
        self.assertEqual(coverage['rejections']['rounding_midpoint_not_specified_by_authority'], 1)

    def test_corrected_conventions_align_the_quantity_and_keep_other_measures(self):
        from tools.gtmeasure.conventions import MEASURES
        from tools.gtmeasure.room_repair import corrected_conventions

        original = copy.deepcopy(self.conventions)
        original['measurements'] = {'gtm_room_size': {'measure': 'floor union', 'formula': 'floor geometry'},
                                    'gtm_object_size': {'measure': 'unchanged object convention'}}
        corrected = corrected_conventions(original)
        self.assertEqual(original['measurements']['gtm_room_size']['measure'], 'floor union')
        self.assertEqual(corrected['measurements']['gtm_object_size'], original['measurements']['gtm_object_size'])
        for key, value in MEASURES['gtm_room_size'].items():
            self.assertEqual(corrected['measurements']['gtm_room_size'][key], value)
        self.assertEqual(corrected['measurements']['gtm_room_size']['value_authority'], original['authorities']['vsi'])
        self.assertNotIn('floor_bounds', corrected['observation_templates'])

    def test_swarm_admission_checks_label_identity_conversion_and_observation(self):
        from tools.gtmeasure.io import canonical
        from tools.gtmeasure.split import group_id
        from tools.gtmeasure.swarm import AdmissionError, Guard, check_gt
        from tools.gtmeasure.targets import render_target, validate_target

        rows, _ = self.room_rows(self.labels())
        row = rows[0]
        before = canonical(row)
        guard = Guard({row['qid']}, set(), {group_id(row['dataset'], row['scene'])}, set(), set(), set())
        self.assertEqual(check_gt(row, guard, conventions=self.conventions)['answer'], row['ground_truth']['answer'])
        for field, value, reason in [('scene', 'scene0000_01', 'exact_scene'),
                                     ('value_si_decimal', '999', 'conversion'), ('split_side', 'heldout', 'training_authority')]:
            changed = copy.deepcopy(row)
            changed['provenance']['room_label'][field] = value
            with self.assertRaisesRegex(AdmissionError, reason):
                check_gt(changed, guard, conventions=self.conventions)
        changed = copy.deepcopy(row)
        changed['observations'][0] = 'The floor area is 1 square meters.'
        changed['target'] = render_target(changed['observations'], changed['ground_truth']['answer'])
        changed['checks'] = validate_target(changed['target'])
        with self.assertRaisesRegex(AdmissionError, 'observations'):
            check_gt(changed, guard, conventions=self.conventions)
        self.assertEqual(canonical(row), before)

    def test_outside_the_requested_training_membership_defers(self):
        from tools.gtmeasure.room_labels import RoomLabelDeferred

        labels = self.labels()
        with self.assertRaisesRegex(RoomLabelDeferred, 'unrequested'):
            labels.lookup('scannet', 'scene0000_01')


if __name__ == '__main__':
    unittest.main()
