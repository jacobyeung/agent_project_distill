import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from fixtures import fixture_root, make_room_labels, make_scene
from test_contracts import authorities
from tools.gtmeasure.assets import load_scene
from tools.gtmeasure.blocking import EXPECTED_GROUPS, benchmark_blocking
from tools.gtmeasure.conventions import FAMILIES
from tools.gtmeasure.formats import harvest
from tools.gtmeasure.generate import load_authority_samples, process_scene
from tools.gtmeasure.io import canonical, new_output, pin, write_json
from tools.gtmeasure.mix import mix_rows, mix_training
from tools.gtmeasure.questions import generate_scene
from tools.gtmeasure.split import SplitPolicy
from tools.gtmeasure.targets import STUDENT_KEYS, validate_student_input, validate_target


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_root()
        cls.scene = make_scene(cls.root / 'scene')
        cls.formats = harvest(authorities())
        cls.room_labels = make_room_labels(cls.root, cls.scene)
        cls.rows, cls.coverage = generate_scene(cls.scene, cls.formats, density=30, config_sha='a' * 64, commit='b' * 40,
                                               room_labels=cls.room_labels)

    def test_all_families_use_rgb_only_inputs_and_grounded_compact_targets(self):
        self.assertEqual(len(self.rows), 30)
        self.assertEqual({row['family'] for row in self.rows}, set(FAMILIES))
        self.assertEqual(self.coverage['by_family']['gtm_room_size'], 1)
        self.assertTrue(all(count >= 6 for family, count in self.coverage['by_family'].items() if family != 'gtm_room_size'))
        self.assertEqual(len({canonical(row['student_input']) for row in self.rows}), 30)
        for row in self.rows:
            self.assertEqual(set(row['student_input']), STUDENT_KEYS)
            self.assertTrue(validate_student_input(row['student_input']))
            self.assertTrue(validate_target(row['target'])['numeric_tokens'])
            self.assertRegex(row['qid'], r'^gtmeasure_scannet__scene0000_00_\d{5}$')
            self.assertEqual(row['source'], 'gtmeasure_v1')
            self.assertEqual(bool(row['object_ids']), row['family'] != 'gtm_room_size')
            if row['source_question_type'] == 'absolute_count' and 'chair' in row['student_input']['question']:
                self.assertEqual(row['ground_truth']['answer'], '2')

    def test_seed_repeats_exact_row_bytes_and_changes_selection(self):
        repeated, _ = generate_scene(self.scene, self.formats, density=30, config_sha='a' * 64, commit='b' * 40,
                                     room_labels=self.room_labels)
        changed, _ = generate_scene(self.scene, self.formats, seed=18, density=30, config_sha='a' * 64, commit='b' * 40,
                                    room_labels=self.room_labels)
        self.assertEqual(canonical(self.rows), canonical(repeated))
        self.assertNotEqual([row['student_input']['question'] for row in self.rows], [row['student_input']['question'] for row in changed])

    def test_mc_distractors_are_real_copresent_objects_in_pool_order(self):
        selected = [row for row in self.rows if row['source_question_type'] == 'relative_distance_object']
        self.assertTrue(selected)
        labels = {obj['label'] for obj in self.scene.objects}
        for row in selected:
            options = row['student_input']['options']
            measurements = row['ground_truth']['measurements']
            self.assertEqual(len(options), 4)
            self.assertEqual(len(set(options)), 4)
            self.assertTrue(set(options) <= labels)
            self.assertEqual(options, [value['label'] for value in measurements])
            for letter, label in zip('ABCD', options):
                self.assertIn(f'{letter}. {label}', row['student_input']['question'])
            values = [float(item['rounded_value']) for item in measurements]
            self.assertEqual(row['ground_truth']['answer'], 'ABCD'[values.index(min(values))])
            visible = {obj['label'] for obj in self.scene.observations(row['provenance']['visibility_witness_frame'])}
            self.assertTrue(set(options) <= visible)

    def test_blocking_happens_before_assets_are_opened(self):
        policy = SplitPolicy({'seed': 17, 'validation_fraction': .1, 'heldout_scenes': [], 'train_scenes': []})
        with patch('tools.gtmeasure.generate.load_scene', side_effect=AssertionError('assets must stay closed')):
            rows, coverage = process_scene({'dataset': 'scannet', 'scene_name': 'scene0123_09'}, {}, {}, '', [],
                                           {('scannet', 'scene0123')}, policy)
        self.assertEqual(rows, [])
        self.assertEqual(coverage['status'], 'deferred_benchmark_scene_group')

    def test_benchmark_authorities_require_exact_group_censuses(self):
        specs = {}
        for index, (name, count) in enumerate(EXPECTED_GROUPS.items()):
            path = self.root / f'{name}.json'
            rows = [{'dataset': 'scannet', 'scene_name': f'scene{i + 1000 * index:04d}_00'} for i in range(count)]
            write_json(path, rows)
            specs[name] = {**pin(path), 'rows': count, 'scene_groups': count}
        _, blocked = benchmark_blocking(specs)
        self.assertEqual(len(blocked), sum(EXPECTED_GROUPS.values()))
        specs['vsibench_full']['scene_groups'] -= 1
        with self.assertRaisesRegex(ValueError, 'census'):
            benchmark_blocking(specs)

    def test_asset_pin_drift_is_rejected(self):
        scene = make_scene(self.root / 'tampered')
        Path(scene.receipt['frames'][0]['path']).write_bytes(b'changed synthetic RGB')
        with self.assertRaisesRegex(ValueError, 'drifted|digest'):
            load_scene(scene.receipt_path)

    def test_cached_wording_requires_its_pin_and_the_original_authorities(self):
        specs = {}
        for name in ('vsi', 'vsti', 'vsibench'):
            path = self.root / (name + '_authority.json')
            write_json(path, {'fixture': name})
            specs[name] = pin(path)
        manifest = {'source': specs['vsi'], 'benchmark_blocking': {'eval_files': {
            'vstibench_full': specs['vsti'], 'vsibench_full': specs['vsibench']}}}
        cache = self.root / 'authority_cache.json'
        samples = {name: {'authority': spec} for name, spec in specs.items()}
        write_json(cache, samples)
        cache_pin = pin(cache)
        self.assertEqual(load_authority_samples(cache, cache_pin['sha256'], manifest), samples)
        with self.assertRaisesRegex(ValueError, 'require'):
            load_authority_samples(cache, None, manifest)
        with self.assertRaisesRegex(ValueError, 'digest'):
            load_authority_samples(cache, '0' * 64, manifest)
        changed = copy.deepcopy(manifest)
        changed['source'] = specs['vsti']
        with self.assertRaisesRegex(ValueError, 'foreign'):
            load_authority_samples(cache, cache_pin['sha256'], changed)

    def test_output_guard_rejects_home(self):
        with self.assertRaisesRegex(ValueError, 'outputs must live'):
            new_output('/home/gtmeasure-must-not-be-created')


class MixerTests(unittest.TestCase):
    def setUp(self):
        self.published = {'seed': 17, 'validation_fraction': .1, 'heldout_scenes': ['scannet/scene0010'],
                          'train_scenes': ['scannet/scene0000']}
        self.arm_pin = {'path': '/published/arm-c', 'sha256': 'c' * 64}
        self.policy = SplitPolicy(self.published, inherited_pin=self.arm_pin)
        self.compact = [{'qid': f'compact_{i}', 'dataset': 'scannet', 'scene': 'scene0000_00', 'category': 'object_counting'} for i in range(12)]
        self.gt = [{'qid': f'gt_{i}', 'dataset': 'scannet', 'scene': 'scene0000_01', 'category': 'object_size_estimation',
                    'family': 'gtm_object_size', 'source': 'gtmeasure_v1'} for i in range(8)]
        self.compact.append({'qid': 'held_base', 'dataset': 'scannet', 'scene': 'scene0010_09', 'category': 'object_counting'})
        self.gt.append({'qid': 'held_gt', 'dataset': 'scannet', 'scene': 'scene0010_03', 'category': 'object_counting',
                        'family': 'gtm_object_count', 'source': 'gtmeasure_v1'})

    def test_mixer_inherits_split_and_keeps_every_holdout_out_of_training(self):
        train, held, split, selection = mix_rows(self.compact, self.gt, self.policy, .25)
        self.assertEqual(len(train), 16)
        self.assertEqual(selection['selected'], {'compact': 12, 'gtmeasure_v1': 4})
        self.assertEqual({row['qid'] for row in held}, {'held_base', 'held_gt'})
        self.assertEqual(split['heldout_scenes'], self.published['heldout_scenes'])
        self.assertEqual(split['inherited_split'], self.arm_pin)
        self.policy.assert_train(train)
        self.assertEqual(canonical((train, held, split, selection)), canonical(mix_rows(self.compact, self.gt, self.policy, .25)))
        self.assertEqual(len({row['qid'] for row in train}), len(train))

    def test_ratio_downsamples_without_replacement_and_handles_endpoints(self):
        base, gt = self.compact[:-1], self.gt[:-1]
        mixed, selected = mix_training(base, gt, .5)
        self.assertEqual(len(mixed), 16)
        self.assertEqual(selected['selected'], {'compact': 8, 'gtmeasure_v1': 8})
        self.assertEqual(len(mix_training(base, gt, 0)[0]), 12)
        self.assertEqual(len(mix_training(base, gt, 1)[0]), 8)
        with self.assertRaises(ValueError):
            mix_training(base, gt, float('nan'))
        with self.assertRaises(ValueError):
            mix_training(base, gt, -1)

    def test_duplicate_source_qids_are_refused(self):
        changed = copy.deepcopy(self.gt)
        changed[0]['qid'] = self.compact[0]['qid']
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            mix_rows(self.compact, changed, self.policy, .5)


if __name__ == '__main__':
    unittest.main()
