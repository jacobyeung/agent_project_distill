import copy
from collections import Counter
import json
import math
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

import numpy as np

from student.compact_targets import traceev_extract as extract
from tools.gtmeasure.io import digest


EXAMPLE = Path('/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/traceev_b1_20260925/inputs/example_trace_vsi590k_135758.json')


def rgb():
    return {'question': 'Source question', 'options': [],
            'frames': [{'path': f'/synthetic/frame{i}.png', 'sha256': f'{i:064x}'} for i in range(32)],
            'frame_indices': [i * 7 for i in range(32)], 'timestamps': [i * .7 for i in range(32)],
            'fps': 10., 'total_num_frames': 218}


def group(iid, label, center=(0., 0., 0.), half=(.6, .4, .375)):
    return {'id': iid, 'label': label, 'obb': {'centroid': list(center), 'axesLengths': list(half),
                                            'normalizedAxes': np.eye(3).ravel().tolist()}}


def fact(scene, serial, kind='traceev_size', count=None, source=None):
    qid = source or f'source_{scene}_{serial}'
    key = [scene, kind, [serial]]
    return {'qid': f'fact_{scene}_{serial}_{kind}', 'fact_key': key, 'scene': str(scene), 'dataset': 'scannet',
            'question_type': kind, 'question': 'Q', 'target': str(serial), 'source_qids': [qid],
            'source_traces': [{'path': '/' + qid, 'sha256': digest(qid)}],
            'evidence': {'owner_qid': qid, 'gt': {'values_unrounded': {'count': count}}}}


class ContractTests(unittest.TestCase):
    def test_one_based_mapping_and_path_sha_equality(self):
        student = rgb()
        receipt = {'frames': [{**frame, 'ordinal': ordinal} for frame, ordinal in
                              zip(student['frames'], student['frame_indices'])]}
        mapping = extract.frame_mapping(receipt, student)
        self.assertEqual(mapping[1], student['frames'][0])
        self.assertEqual(mapping[32], student['frames'][31])
        self.assertNotIn(0, mapping)
        receipt['frames'][0]['path'] = '/different/path.png'
        with self.assertRaisesRegex(ValueError, 'frame_path_sha_mismatch'):
            extract.frame_mapping(receipt, student)

    def test_parallel_tool_responses_follow_ids(self):
        trace = {'trace': [{'tool_calls': [{'id': 'a', 'name': 'one', 'args': {}},
                                         {'id': 'b', 'name': 'two', 'args': {}}]},
                           {'tool_calls': None, 'tool_call_id': 'b', 'name': 'two', 'content': '[2]'},
                           {'tool_call_id': 'a', 'name': 'one', 'content': '[1]'}]}
        pairs = extract.tool_pairs(trace)
        self.assertEqual([(p['name'], p['response']) for p in pairs], [('two', [2]), ('one', [1])])
        trace['trace'][1]['name'] = 'one'
        with self.assertRaisesRegex(ValueError, 'tool_name_mismatch'):
            extract.tool_pairs(trace)

    def test_uniqueness_uses_complete_gt_census(self):
        objects = {obj['id']: obj for obj in [group(1, 'chair'), group(2, 'chair'), group(3, 'table')]}
        self.assertEqual(extract.unique_ids(objects, {1, 3}), [3])

    def test_numeric_targets_have_two_decimals(self):
        question, target = extract.render('traceev_size', ['table'], {'dimensions': [1.2, .8, .75]})
        self.assertEqual(target, '1.20, 0.80, 0.75')
        self.assertNotIn('numbered', question)
        self.assertEqual(extract.format_number(-.00001), '0.00')
        self.assertEqual(extract.format_number(1.235), '1.24')
        self.assertEqual(extract.render('traceev_abs_distance', ['table', 'door'], {'distance': 1.5})[1], '1.50')

    def test_frame_modes_and_nonunique_wording(self):
        question, target = extract.render('traceev_frames_all', ['chair'], {'frames': [1, 7, 32], 'unique': False})
        self.assertIn('at least one chair', question)
        self.assertIn('32 frames, numbered 1 to 32', question)
        self.assertEqual(target, '1, 7, 32')
        for frames in ([0], [33], [2, 2], [True]):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                extract.render('traceev_frames_all', ['chair'], {'frames': frames, 'unique': True})

    def test_no_leakage_with_only_literal_template_exception(self):
        question, target = extract.render('traceev_count_list', ['chair'], {'first_frames': [[8, 3], [9, 11]], 'count': 2})
        extract.validate_text(question, target)
        self.assertEqual(target, 'chair 1: frame 3\nchair 2: frame 11\ncount: 2')
        for text in ('x=1', '(1, 2)', 'camera', 'pose', 'centroid', 'instance 42', 'world', '/mask.npy',
                     'predict_2d_segmentation_masks'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                extract.validate_text(question, text)
        with self.assertRaises(ValueError):
            extract.render('traceev_size', ['camera'], {'dimensions': [1., 1., 1.]})

    def test_quadrant_margin_and_agreement(self):
        a, b = group(1, 'table'), group(2, 'door', (1., 0., 0.))
        for center, side, answer in [((1., 1., 8.), 'left', 'front-left'),
                                     ((-1., -1., 0.), 'right', 'back-right')]:
            self.assertEqual(extract.quadrant(a, b, group(3, 'chair', center), side)[0], answer)
        c = group(3, 'chair', (1., math.tan(math.radians(15)), 0.))
        with self.assertRaisesRegex(ValueError, 'quadrant_axis_margin'):
            extract.quadrant(a, b, c, 'left')
        with self.assertRaisesRegex(ValueError, 'quadrant_left_right_disagreement'):
            extract.quadrant(a, b, group(3, 'chair', (1., 1., 0.)), 'right')

    def test_count_one_cap_is_exact(self):
        rows = [fact(i, i, 'traceev_count_list', 2) for i in range(17)]
        rows += [fact(i + 30, i + 30, 'traceev_count_list', 1) for i in range(20)]
        selected, dropped = extract.limit_count_one(rows)
        self.assertEqual(len(selected), 20)
        self.assertEqual(sum(r['evidence']['gt']['values_unrounded']['count'] == 1 for r in selected), 3)
        self.assertEqual(dropped, 17)
        self.assertEqual(extract.limit_count_one(rows[17:])[0], [])

    def test_count_one_cap_preserves_disagreements(self):
        disagreement = fact(1, 1, 'traceev_count_list', 1)
        disagreement['label_check'] = {'v3_qid': 'v3_count', 'v3_label': '2', 'gt_count': 1, 'agree': False}
        ordinary = fact(2, 2, 'traceev_count_list', 1)
        kept, dropped = extract.limit_count_one([ordinary, disagreement])
        self.assertEqual(kept, [disagreement])
        self.assertEqual(dropped, 1)
        rows = [fact(scene, 0) for scene in range(250)] + [disagreement]
        kept, _ = extract.select_budget(rows)
        self.assertIn(disagreement, kept)

    def test_counting_category_is_exact_not_substring(self):
        self.assertTrue(extract.counting_category_matches('How many chair(s) do we have?', 'chair'))
        self.assertTrue(extract.counting_category_matches('Tell me how many smoke detector(s) are located here.', 'smoke detector'))
        self.assertTrue(extract.counting_category_matches('How many chairs are visible?', 'chair'))
        self.assertTrue(extract.counting_category_matches('Could you give me the number of heater(s) in this space?', 'heater'))
        self.assertTrue(extract.counting_category_matches("What's the number of bookshelf(s) present in this room?", 'bookshelf'))
        self.assertTrue(extract.counting_category_matches("What's the exact quantity of monitor(s) in this room?", 'monitor'))
        self.assertFalse(extract.counting_category_matches('How many armchair(s) do we have?', 'chair'))
        self.assertFalse(extract.counting_category_matches('How many chair(s) are beside the table?', 'table'))

    def test_complete_tool_count_census_requires_all_slots(self):
        objects = {1: group(1, 'chair'), 2: group(2, 'chair'), 3: group(3, 'table')}
        calls = [{'name': 'find_frames_with_object', 'args': {'object_label': 'chair', 'num_frames': 'all'},
                  'call_id': 'all', 'response': [3, 9]},
                 {'name': 'predict_2d_segmentation_masks_video',
                  'args': {'object_label': 'chair', 'frame_indices': [3, 9]}, 'call_id': 'video',
                  'response': {'frames': {'3': [{'instance_id': 1}], '9': [{'instance_id': 1}, {'instance_id': 2}]}}}]
        first, witnesses = extract.complete_tool_visibility(calls, objects, 'chair')
        self.assertEqual(first, {1: 3, 2: 9})
        self.assertEqual(len(witnesses), 2)
        self.assertIsNone(extract.complete_tool_visibility(calls[1:], objects, 'chair'))
        calls[1]['response']['frames'].pop('9')
        self.assertIsNone(extract.complete_tool_visibility(calls, objects, 'chair'))

    def test_distance_uses_complete_triangle_surfaces(self):
        triangle = np.asarray([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])
        cache = object.__new__(extract.SceneCache)
        cache.distances = {}
        cache.mesh_objects = {1: {'triangles': triangle}, 2: {'triangles': triangle + [0., 0., 1.53]}}
        with patch.object(cache, 'scene', return_value=None):
            self.assertAlmostEqual(cache.distance(1, 2), 1.53)
            self.assertEqual(cache.distance(2, 1), cache.distance(1, 2))
        self.assertEqual(len(cache.distances), 1)

    def test_label_disagreement_report_uses_per_dataset_denominators(self):
        rows = [fact(i, i, 'traceev_count_list', 2) for i in range(3)]
        for row, agree in zip(rows[:2], (False, True)):
            row['label_check'] = {'v3_qid': row['qid'], 'v3_label': '2' if agree else '1', 'gt_count': 2, 'agree': agree}
            row['evidence']['label_checks'] = [row['label_check']]
        summary = extract.label_check_summary(rows)['scannet']
        self.assertEqual(summary['count_rows'], 3)
        self.assertEqual(summary['compared_rows'], 2)
        self.assertEqual(summary['disagreement_rows'], 1)
        self.assertEqual(summary['disagreement_percent'], 50.)
        self.assertEqual(summary['label_disagreement_percent'], 50.)

    def test_visibility_failure_never_caches_an_incomplete_census(self):
        cache = object.__new__(extract.SceneCache)
        cache.first = cache.visible_frames = None
        with patch.object(cache, 'scene') as scene:
            scene.return_value.observations.side_effect = [[{'id': 1}], ValueError('broken visibility')]
            with self.assertRaisesRegex(ValueError, 'broken visibility'):
                cache.visibility()
            self.assertIsNone(cache.first)
            scene.return_value.observations.side_effect = [[{'id': 1}]] * 32
            self.assertEqual(cache.visibility(), {1: 1})
            self.assertEqual(cache.visible_frames[1], list(range(1, 33)))

    def test_dedupe_merges_sources_without_adding_facts(self):
        first = fact(1, 1)
        second = copy.deepcopy(first)
        second['source_qids'] = ['another']
        second['source_traces'] = [{'path': '/another', 'sha256': 'b' * 64}]
        rows, drops = extract.dedupe_rows([first, second])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['source_qids'], ['another', 'source_1_1'])
        self.assertEqual(len(rows[0]['source_traces']), 2)
        self.assertEqual(drops['duplicate_fact'], 1)
        second['target'] = 'different'
        rows, drops = extract.dedupe_rows([first, second])
        self.assertEqual(drops['dedupe_conflicting_render'], 1)

    def test_budget_scene_and_trace_caps(self):
        rows = [fact(scene, i, source=f'source_{scene}') for scene in range(250) for i in range(10)]
        kept, drops = extract.select_budget(rows, budget=40000)
        self.assertEqual(len(kept), 1000)
        self.assertLessEqual(max(Counter(r['scene'] for r in kept).values()), len(kept) * .005)
        self.assertLessEqual(max(Counter(r['evidence']['owner_qid'] for r in kept).values()), 4)
        self.assertEqual(extract.select_budget(rows[:100])[0], [])

    def test_example_trace_program_roles_are_grounded(self):
        trace = json.loads(EXAMPLE.read_text())
        calls = extract.tool_pairs(trace)
        objects = {72: group(72, 'whiteboard'), 12: group(12, 'blanket'), 141: group(141, 'laptop')}
        grounded, labels, lifts = extract.grounding(calls, objects, trace['scene_name'])
        self.assertEqual(set(grounded), {72, 12, 141})
        roles, side, program = extract.program_viewpoint(calls, lifts)
        self.assertEqual(roles, (72, 12, 141))
        self.assertEqual(side, 'right')
        self.assertEqual(program['name'], 'execute_python_code')

    def test_manual_cross_program_and_no_execution(self):
        code = 'a = [0.,0.,0.]\nb = [1.,0.,0.]\nc = [1.,1.,0.]\nf = [b[0]-a[0],b[1]-a[1]]\nt = [c[0]-a[0],c[1]-a[1]]\nz = f[0]*t[1]-f[1]*t[0]\nprint("left")'
        call = {'name': 'execute_python_code', 'args': {'code': code}, 'call_id': 'p', 'response': 'left\n'}
        lifts = {1: [{'centroid': [0., 0., 0.]}], 2: [{'centroid': [1., 0., 0.]}], 3: [{'centroid': [1., 1., 0.]}]}
        self.assertEqual(extract.program_viewpoint([call], lifts)[:2], ((1, 2, 3), 'left'))
        call['args']['code'] = 'open("/forbidden", "w").write("x")'
        with self.assertRaisesRegex(ValueError, 'quadrant_program_unresolved'):
            extract.program_viewpoint([call], lifts)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['COMPACT_TEST_OUTPUT']) / ('traceev_' + uuid4().hex)
        self.root.mkdir(parents=True)
        self.inputs = rgb()
        self.objects = [group(1, 'table')]
        instances = self.save('instances.json', {'segGroups': self.objects})
        annotations = self.save('annotations.json', {'instances': [{'instance_id': 1, 'label': 'table'}]})
        mesh = self.save('mesh.json', {'synthetic': True})
        self.receipt = {'dataset': 'scannet', 'scene_name': 'scene0000_00', 'runtime_scene_id': 'scannet__scene0000_00',
                        'coordinate_frame': 'source_world_meters_opencv_camera_to_world', 'gravity_up': [0, 0, 1],
                        'frames': [{**f, 'ordinal': i} for f, i in zip(self.inputs['frames'], self.inputs['frame_indices'])],
                        'instances': instances, 'annotations': annotations, 'instance_mesh': mesh,
                        'dense': mesh, 'calibration': mesh, 'alignment': mesh}
        receipt_pin = self.save('scene_receipt.json', self.receipt)
        calls = [{'id': 'seg', 'name': 'predict_2d_segmentation_masks',
                  'args': {'scene_id': self.receipt['runtime_scene_id'], 'frame_index': 1, 'object_label': 'table'}},
                 {'id': 'frames', 'name': 'find_frames_with_object',
                  'args': {'scene_id': self.receipt['runtime_scene_id'], 'object_label': 'table', 'num_frames': 'all'}}]
        self.trace = {'question_id': 'vsi590k_fixture', 'scene_name': self.receipt['runtime_scene_id'],
                      'question_type': 'object_size_estimation', 'question': 'How big is the table?',
                      'run_receipt': {'scene_receipt': receipt_pin},
                      'trace': [{'tool_calls': calls},
                                {'name': calls[0]['name'], 'tool_call_id': 'seg', 'content': '[{"instance_id": 1}]'},
                                {'name': calls[1]['name'], 'tool_call_id': 'frames', 'content': '[1, 7, 32]'}]}
        trace_pin = self.save('trace.json', self.trace)
        row = {'qid': 'vsi590k_fixture', 'dataset': 'scannet', 'scene': 'scene0000_00', 'target': '1.20',
               'student_input': self.inputs, 'sources': {'raw': trace_pin}}
        row_pin = self.save('row.json', row)
        self.entry = {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                      'question_type': 'object_size_estimation', 'row_path': row_pin['path'], 'row_sha256': row_pin['sha256'],
                      'strict_accepted_trace': trace_pin}

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return {'path': str(path), 'sha256': extract.sha(path)}

    def test_replay_equality_and_student_input_copy(self):
        rows, stats = extract.extract_entry(self.entry, {}, 'a' * 40, kinds={'traceev_size', 'traceev_frames_all'})
        self.assertEqual({r['question_type'] for r in rows}, {'traceev_size', 'traceev_frames_all'})
        for row in rows:
            self.assertEqual(extract.replay(row), row['target'])
            expected = {**self.inputs, 'question': row['question'], 'options': []}
            self.assertEqual(row['student_input'], expected)
        bad = copy.deepcopy(rows[0])
        bad['target'] = '999.99'
        with self.assertRaises(ValueError):
            extract.replay(bad)

    def counting_entry(self, qid, label, target, frames=None):
        inputs = {**self.inputs, 'question': f'How many {label}(s) do we have?'}
        if frames is not None:
            inputs['frames'] = frames
        row = {'qid': qid, 'dataset': 'scannet', 'scene': 'scene0000_00',
               'student_input': inputs, 'target': target}
        pin = self.save(qid + '.json', row)
        return {**self.entry, 'qid': qid, 'question_type': 'object_counting',
                'row_path': pin['path'], 'row_sha256': pin['sha256']}

    def test_count_disagreement_keeps_gt_and_replays_label_check(self):
        counting = self.counting_entry(self.entry['qid'], 'table', '2')
        with patch.object(extract.SceneCache, 'visibility', return_value={1: 3}):
            rows, stats = extract.extract_entry(counting, {}, 'a' * 40, kinds={'traceev_count_list'})
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['target'], 'table 1: frame 3\ncount: 1')
            self.assertEqual(row['label_check'], {'v3_qid': counting['qid'], 'v3_label': '2', 'gt_count': 1, 'agree': False})
            self.assertNotIn('count_question_gt_mismatch', stats['drops'])
            self.assertEqual(extract.replay(row), row['target'])
            changed = copy.deepcopy(row)
            changed['label_check']['agree'] = True
            with self.assertRaisesRegex(ValueError, 'label_check'):
                extract.replay(changed)

    def test_count_checks_every_matching_v3_category_and_frame_set(self):
        same = self.counting_entry('other_count', 'table', '3')
        agreeing = self.counting_entry('agreeing_count', 'table', '1')
        foreign_label = self.counting_entry('chair_count', 'chair', '5')
        foreign_frames = self.counting_entry('other_frames', 'table', '4', list(reversed(self.inputs['frames'])))
        catalog = extract.counting_catalog([same, agreeing, foreign_label, foreign_frames])
        with patch.object(extract.SceneCache, 'visibility', return_value={1: 1}):
            rows, _ = extract.extract_entry(self.entry, {}, 'a' * 40, kinds={'traceev_count_list'}, counting=catalog)
            row, = rows
            self.assertEqual(row['label_check']['v3_qid'], 'other_count')
            self.assertFalse(row['label_check']['agree'])
            self.assertEqual({item['v3_qid'] for item in row['evidence']['label_checks']}, {'other_count', 'agreeing_count'})
            self.assertEqual(extract.replay(row), row['target'])
        no_labels, _ = extract.extract_entry(self.entry, {}, 'a' * 40, kinds={'traceev_size'})
        self.assertIsNone(no_labels[0]['label_check'])

    def test_count_census_includes_only_instances_visible_in_video(self):
        cache = extract.SceneCache(self.trace['run_receipt']['scene_receipt'], self.receipt)
        cache.objects[2] = group(2, 'table')
        cache.labels['table'].append(2)
        cache.first = {1: 2}
        key = (cache.receipt_pin['path'], cache.receipt_pin['sha256'])
        rows, _ = extract.extract_entry(self.entry, {key: cache}, 'a' * 40, kinds={'traceev_count_list'})
        row, = rows
        self.assertEqual(row['evidence']['gt']['instance_ids'], [1])
        self.assertEqual(row['target'], 'table 1: frame 2\ncount: 1')

    def test_runner_retains_complete_shards_and_reports_source_failures(self):
        bad = {**self.entry, 'qid': 'vsi590k_missing', 'row_path': str(self.root / 'absent.json')}
        out = self.root / 'runner'
        args = extract.parser().parse_args(['extract', '--v3-layout', str(self.root), '--out', str(out), '--workers', '1'])
        with patch.object(extract, 'v3_sources', return_value=([self.entry, bad], Counter())), \
             patch.object(extract, 'source_commit', return_value='a' * 40):
            summary = extract.extract(args)
        self.assertEqual(summary['traces_processed'], 2)
        self.assertEqual(summary['scene_shards'], 1)
        self.assertEqual(summary['rows'], 0)
        self.assertEqual(summary['drops']['FileNotFoundError'], 1)
        self.assertEqual(summary['sha256'], extract.sha(out / 'evidence_rows.jsonl'))
        self.assertTrue((out / 'COMPOSITION.md').is_file())
        self.assertTrue((out / 'DROPS.json').is_file())
        shard = out / 'shards' / 'scannet__scene0000_00.jsonl'
        self.assertGreater(json.loads(shard.with_suffix('.done.json').read_text())['rows'], 0)
        audit_args = extract.parser().parse_args(['audit', '--out', str(out), '--workers', '1'])
        with patch.object(extract, 'v3_sources', return_value=([self.entry, bad], Counter())):
            audited = extract.audit(audit_args)
        self.assertEqual(audited['status'], 'PASS')
        self.assertEqual(audited['traces_reconciled'], 2)
        self.assertEqual(audited['replayed_by_kind'], {'traceev_size': 1, 'traceev_frames_all': 1})
        with (out / 'evidence_rows.jsonl').open('a') as stream:
            stream.write('{}\n')
        with patch.object(extract, 'v3_sources', return_value=([self.entry, bad], Counter())), \
             self.assertRaisesRegex(ValueError, 'audit_published_bytes'):
            extract.audit(audit_args)

    def test_replay_reauthenticates_trace(self):
        rows, _ = extract.extract_entry(self.entry, {}, 'a' * 40, kinds={'traceev_size'})
        with Path(self.entry['strict_accepted_trace']['path']).open('a') as stream:
            stream.write(' ')
        with self.assertRaisesRegex(ValueError, 'sha256_mismatch'):
            extract.replay(rows[0])

    def test_replay_reauthenticates_gt(self):
        rows, _ = extract.extract_entry(self.entry, {}, 'a' * 40, kinds={'traceev_size'})
        with Path(self.receipt['instances']['path']).open('a') as stream:
            stream.write(' ')
        with self.assertRaisesRegex(ValueError, 'sha256_mismatch'):
            extract.replay(rows[0])


if __name__ == '__main__':
    unittest.main()
