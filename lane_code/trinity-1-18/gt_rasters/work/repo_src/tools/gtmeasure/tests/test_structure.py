import copy
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from fixtures import fixture_root, make_room_labels, make_scene
from test_contracts import authorities
from collector.frame_alignment import canonical_geometry
from tools.gtmeasure import conventions, formats, generate, questions
from tools.gtmeasure.io import canonical, digest, read_json, write_json
from tools.gtmeasure.split import SplitPolicy
from tools.gtmeasure.targets import validate_target
from tools.gtmeasure.verify import verify_dataset


class StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_root()
        cls.scene = make_scene(cls.root / 'scene')
        cls.legacy = formats.harvest(authorities())
        cls.room_labels = make_room_labels(cls.root, cls.scene)
        cls.default_rows, cls.coverage = questions.generate_scene(
            cls.scene, cls.legacy, density=30, config_sha='a' * 64, commit='b' * 40, room_labels=cls.room_labels)

    def v2_rows(self, scene=None, conventions=None):
        return questions.generate_scene(
            scene or self.scene, conventions or formats.harvest(authorities(), structure='v2'),
            density=30, config_sha='a' * 64, commit='b' * 40, structure='v2', room_labels=self.room_labels)[0]

    def test_default_matches_full_room_label_semantic_bytes(self):
        semantic = [{key: value for key, value in row.items() if key not in ('student_input', 'provenance')}
                    | {'question': row['student_input']['question'], 'options': row['student_input']['options']}
                    for row in self.default_rows]
        self.assertEqual(digest(semantic), '4025872fb06324b628ec7a8bf3694a1d39290b5beb5848fc2873bc4e78b8aa62')
        self.assertEqual(digest(self.legacy), '46cf6982780b1a79aa1a710898ce15dd699940814fbc6a34914fb869d5403b71')

    def test_default_and_explicit_v1_preserve_every_row_byte(self):
        rows, coverage = questions.generate_scene(
            self.scene, formats.harvest(authorities(), structure='v1'), density=30,
            config_sha='a' * 64, commit='b' * 40, structure='v1', room_labels=self.room_labels)
        self.assertEqual(canonical(rows), canonical(self.default_rows))
        self.assertEqual(coverage, self.coverage)

    def test_v2_keeps_answers_inputs_measurements_and_final_lines_byte_identical(self):
        rows = self.v2_rows()
        self.assertEqual(len(rows), len(self.default_rows))
        for old, new in zip(self.default_rows, rows):
            with self.subTest(qid=old['qid']):
                self.assertEqual(new['target'].rsplit('\n', 1)[1].encode(), old['target'].rsplit('\n', 1)[1].encode())
                self.assertEqual(new['observations'][-len(old['observations']):], old['observations'])
                self.assertGreater(len(new['observations']), len(old['observations']))
                keys = set(old) - {'target', 'observations', 'checks'}
                self.assertEqual(canonical({key: old[key] for key in keys}), canonical({key: new[key] for key in keys}))
                self.assertEqual(validate_target(new['target'])['observation_count'], len(new['observations']))
        self.assertEqual(canonical(rows), canonical(self.v2_rows()))

    def test_object_size_uses_full_oriented_box_sides_in_stored_axis_order(self):
        scene = copy.deepcopy(self.scene)
        obj = next(obj for obj in scene.objects if obj['id'] == 2)
        obj['obb']['axesLengths'] = [1.125, .75, .375]
        obj['obb']['normalizedAxes'] = [0., 1., 0., -1., 0., 0., 0., 0., 1.]
        obj['corners'] = conventions.box_corners(obj['obb'])
        selected = [row for row in self.v2_rows(scene) if row['family'] == 'gtm_object_size' and row['object_ids'] == [2]]
        self.assertTrue(selected)
        for row in selected:
            self.assertEqual(row['observations'][0], "The table's official-box extents (length, width, height) are (2.25, 1.50, 0.75) meters.")
            self.assertEqual(row['ground_truth']['measurements'][0]['value_si'], 2.25)
            self.assertEqual(row['checks']['observation_count'], 2)

    def object_line(self, iid, label):
        return (f'The {label} (instance {iid}) has center ({-6 + iid * 2:.2f}, 0.00, 8.00) meters in the camera0 frame '
                'and official-box extents (length, width, height) of (1.00, 1.00, 0.00) meters.')

    def test_object_distance_lists_both_gt_centers_and_extents(self):
        labels = {obj['id']: obj['label'] for obj in self.scene.objects}
        selected = [row for row in self.v2_rows() if row['source_question_type'] == 'absolute_distance_object']
        self.assertTrue(selected)
        for row in selected:
            self.assertEqual(row['observations'][:2], [self.object_line(iid, labels[iid]) for iid in row['object_ids']])
            self.assertEqual(row['checks']['observation_count'], 3)

    def test_mc_distance_lists_every_candidate_instance_before_unchanged_distances(self):
        labels = {obj['id']: obj['label'] for obj in self.scene.objects}
        selected = [row for row in self.v2_rows() if row['source_question_type'] == 'relative_distance_object']
        self.assertTrue(selected)
        self.assertTrue(any({0, 1} <= set(row['object_ids']) for row in selected))
        for row in selected:
            self.assertEqual(row['observations'][:-4], [self.object_line(iid, labels[iid]) for iid in row['object_ids']])
            self.assertEqual(row['checks']['observation_count'], len(row['object_ids']) + 4)
            self.assertEqual(row['checks']['derivation_count'], 1)

    def test_camera_distance_lists_queried_camera_and_gt_object(self):
        labels = {obj['id']: obj['label'] for obj in self.scene.objects}
        selected = [row for row in self.v2_rows() if row['family'] == 'gtm_camera_object_distance']
        self.assertTrue(selected)
        for row in selected:
            iid, = row['object_ids']
            self.assertEqual(row['observations'][:2], [
                f'In frame {row["frame_index"]}, the camera position is (0.00, 0.00, 0.00) meters in the camera0 frame.',
                self.object_line(iid, labels[iid])])
            self.assertEqual(row['checks']['observation_count'], 3)

    def test_room_size_observations_keep_the_full_label_when_floor_support_is_partial(self):
        scene = copy.deepcopy(self.scene)
        floor = next(obj for obj in scene.objects if obj['label'] == 'floor')
        floor['triangles'] = np.array([[[0., 0., 0.], [4., 0., 0.], [0., 4., 0.]]])
        row, = [row for row in self.v2_rows(scene) if row['family'] == 'gtm_room_size']
        self.assertEqual(row['observations'], [
            'The same-scene full-room label is 16.0 square meters.',
            'The full-room area is 16.0 square meters.'])
        self.assertEqual(row['ground_truth']['measurements'][0]['value_si'], 16.0)
        self.assertEqual(row['checks']['observation_count'], 2)

    def test_count_lists_each_official_instance_once(self):
        row, = [row for row in self.v2_rows() if row['family'] == 'gtm_object_count' and row['object_ids'] == [0, 1]]
        self.assertEqual(row['observations'], [
            'The chair instance 0 has center (-6.00, 0.00, 8.00) meters in the camera0 frame.',
            'The chair instance 1 has center (-4.00, 0.00, 8.00) meters in the camera0 frame.',
            'The scene contains 2 distinct chair instances.'])
        self.assertEqual(row['checks']['observation_count'], 3)

    def test_camera0_matches_teacher_heading_gravity_and_one_based_frame(self):
        scene = copy.deepcopy(self.scene)
        poses = scene.arrays['camera_poses']
        poses[:, :3, :3] = [[0., -.6, .8], [-1., 0., 0.], [0., -.8, -.6]]
        poses[:, :3, 3] = [10., 20., 3.]
        poses[1, :3, 3] = [11., 18., 4.]
        obj = next(obj for obj in scene.objects if obj['id'] == 2)
        obj['obb']['centroid'] = [13., 16., 8.]
        actual = conventions.camera0_points([obj['obb']['centroid']], poses, scene.receipt['gravity_up'])
        teacher = canonical_geometry({'pts3d_world': [obj['obb']['centroid']], 'camera_poses': poses}, [0, 0, 1])
        np.testing.assert_array_equal(actual, teacher['pts3d_world'])
        np.testing.assert_array_equal(actual, [[4., 3., 5.]])
        lines = questions.intermediate_observations(scene, formats.harvest(authorities(), structure='v2'),
                                                   'gtm_camera_object_distance', [2], 2)
        self.assertEqual(lines[0], 'In frame 2, the camera position is (2.00, 1.00, 1.00) meters in the camera0 frame.')
        self.assertIn('center (4.00, 3.00, 5.00) meters in the camera0 frame', lines[1])
        self.assertFalse(np.allclose(actual, conventions.camera_points([obj['obb']['centroid']], poses[0])))

    def test_camera0_uses_teacher_vertical_view_fallback(self):
        poses = self.scene.arrays['camera_poses'].copy()
        poses[:, :3, 3] = [1., 1., 1.]
        np.testing.assert_array_equal(conventions.camera0_points([[3., 4., 5.]], poses, [0, 0, 1]), [[2., 3., 4.]])

    def test_v2_wording_is_pinned_and_separate_from_harvested_authority(self):
        extended = formats.harvest(authorities(), structure='v2')
        self.assertEqual({key: extended[key] for key in self.legacy}, self.legacy)
        self.assertEqual(set(extended) - set(self.legacy), {'observation_templates', 'structure_v2'})
        self.assertEqual(len(extended['observation_templates']), 5)
        for name, spec in extended['observation_templates'].items():
            self.assertEqual(spec['origin'], 'lane_authored')
            author = 'swarm_h05_gtmonly_room_label_20260923' if name == 'room_label' else 'gt_measurement_v2_20260922T0735Z'
            self.assertEqual(spec['authored_by'], author)
            self.assertNotIn('source_line', spec)
        extended['observation_templates']['instance_center']['template'] = 'Pinned {target} {instance_id}: ({x}, {y}, {z}) meters.'
        selected = [row for row in self.v2_rows(conventions=extended) if row['family'] == 'gtm_object_count']
        self.assertTrue(all(row['observations'][0].startswith('Pinned ') for row in selected))

    def test_signed_observation_precision_normalizes_zero_without_deferring_ties(self):
        for value, expected in [(-1.235, '-1.24'), (1.225, '1.22'), (-.0001, '0.00'), (0., '0.00'), (2., '2.00')]:
            self.assertEqual(formats.format_observation_value(value), expected)
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                formats.format_observation_value(value)

    def test_unknown_structure_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'structure'):
            formats.harvest(authorities(), structure='v3')
        with self.assertRaisesRegex(ValueError, 'structure'):
            questions.generate_scene(self.scene, self.legacy, structure='v3')


class GeneratorStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_root()
        cls.scene = make_scene(cls.root / 'scene')
        cls.split_record = {'seed': 17, 'validation_fraction': .1, 'heldout_scenes': [], 'train_scenes': ['scannet/scene0000']}
        cls.samples = authorities()
        cls.samples['vsi']['authority'] = make_room_labels(cls.root, cls.scene).authority
        write_json(cls.root / 'prepared.json', [{'dataset': 'scannet', 'scene_name': 'scene0000_00'}])
        write_json(cls.root / 'manifest.json', {'benchmark_blocking': {'eval_files': {}}})
        write_json(cls.root / 'split.json', cls.split_record)

    def run_fixture(self, name, structure=None):
        args = SimpleNamespace(prepared_scenes=self.root / 'prepared.json', v3_manifest=self.root / 'manifest.json',
                               split=self.root / 'split.json', authorities=None, authorities_sha256=None, job_root=[],
                               scene=[], limit=None, seed=17, density=8, output=self.root / name)
        if structure is not None:
            args.structure = structure
        with ExitStack() as stack:
            for name, value in [('source_commit', 'b' * 40), ('sources', {'fixture': 'c' * 64}),
                                ('benchmark_blocking', ({}, set())), ('overlap', {'any': 0}),
                                ('load_split', SplitPolicy(self.split_record)), ('collect', self.samples),
                                ('receipt_candidates', [self.scene.receipt_path])]:
                stack.enter_context(patch('tools.gtmeasure.generate.' + name, return_value=value))
            stack.enter_context(redirect_stdout(StringIO()))
            self.assertEqual(generate.run(args), 0)
        return args.output

    def test_default_and_v1_config_conventions_and_row_files_are_byte_identical(self):
        default, explicit = self.run_fixture('default'), self.run_fixture('v1', 'v1')
        for name in ('CONFIG.json', 'CONVENTIONS.json', 'train.jsonl', 'heldout.jsonl'):
            self.assertEqual((default / name).read_bytes(), (explicit / name).read_bytes())
        config = read_json(default / 'CONFIG.json')['config']
        self.assertEqual(set(config), {'schema', 'seed', 'density', 'conventions_sha256', 'source_sha256',
                                      'dependencies', 'selection', 'visibility', 'output_schema', 'room_label_policy'})
        self.assertNotIn('observation_templates', read_json(default / 'CONVENTIONS.json'))

    def test_v2_config_selects_structured_geometry_during_replay(self):
        output = self.run_fixture('v2', 'v2')
        self.assertEqual(read_json(output / 'CONFIG.json')['config']['structure'], 'v2')
        with patch('tools.gtmeasure.verify.benchmark_blocking', return_value=({}, set())), \
                patch('tools.gtmeasure.verify.overlap', return_value={'any': 0}), \
                patch('tools.gtmeasure.verify.load_split', return_value=SplitPolicy(self.split_record)):
            summary, rows, _ = verify_dataset(output, recompute=True)
        self.assertEqual(summary['replayed_scenes'], 1)
        self.assertTrue(all(row['checks']['observation_count'] > 1 for row in rows))
        saved = read_json(output / 'CONVENTIONS.json')
        self.assertEqual(saved['measurements']['gtm_room_size']['measure'], conventions.MEASURES['gtm_room_size']['measure'])
        self.assertEqual(saved['measurements']['gtm_room_size']['value_authority'], self.samples['vsi']['authority'])
        self.assertIn('room_label', saved['observation_templates'])
        self.assertNotIn('floor_bounds', saved['observation_templates'])
        room, = [row for row in rows if row['family'] == 'gtm_room_size']
        self.assertEqual(room['ground_truth']['answer'], '16.0')
        self.assertEqual(room['provenance']['room_label']['source_line'], 1)

    def test_cli_defaults_to_v1_and_accepts_v2(self):
        for flags, expected in [([], 'v1'), (['--structure', 'v1'], 'v1'), (['--structure', 'v2'], 'v2')]:
            with patch('sys.argv', ['generate', '--output', str(self.root / 'unused'), *flags]), patch.object(generate, 'run', return_value=0) as run:
                self.assertEqual(generate.main(), 0)
                self.assertEqual(run.call_args.args[0].structure, expected)

    def test_v2_provenance_pins_the_teacher_coordinate_implementation(self):
        self.assertNotIn('collector/frame_alignment.py', generate.sources())
        self.assertIn('collector/frame_alignment.py', generate.sources('v2'))


if __name__ == '__main__':
    unittest.main()
