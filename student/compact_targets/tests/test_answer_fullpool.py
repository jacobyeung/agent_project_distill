"""Synthetic fixtures stay under the explicitly supplied lane temporary root."""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from student.compact_targets import answer_fullpool as full
from student.compact_targets import answer_fullpool_sources as source
from student.compact_targets import answer_fullpool_ingest as ingest
from student.compact_targets import compact_counted_v1 as compact
from student.compact_targets import compact_control as control


class FullpoolTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['COMPACT_TEST_OUTPUT']) / ('fullpool_' + uuid4().hex)
        self.root.mkdir(parents=True)
        self.frames = []
        for i in range(32):
            p = self.root / f'frame{i:02d}.png'
            p.write_bytes(f'synthetic RGB frame {i}'.encode())
            self.frames.append(source.pin(p))
        self.base = self.root / 'source'
        self.base_layout = self.root / 'source_trainer'
        self.base.mkdir()
        self.base_layout.mkdir()
        self.root_a = self.root / 'root_a'
        self.root_a.mkdir()
        self.run_a = self.root / 'run_a'
        self.run_b = self.root / 'run_b'
        (self.run_b / 'terminals').mkdir(parents=True)
        self.split, self.provisional = full.trainer_modules(full.TRAINER)
        self.train = [self.row('base_train', 'scene0001_00')]
        self.heldout = [self.row('base_heldout', 'scene0002_00', target='Context\n<answer>A</answer>')]
        record = {'schema': 'provisional-whole-scene-split-v1', 'seed': 17,
                  'heldout_fraction_of_groups': 0.1, 'group_policy': self.split.WHOLE_SCENE_GROUP_POLICY,
                  'train_group_ids': ['scannet/scene0001'], 'heldout_group_ids': ['scannet/scene0002'],
                  'train_scenes': ['scannet/scene0001_00'], 'heldout_scenes': ['scannet/scene0002_00'],
                  'train_candidate_qids': ['base_train'], 'heldout_qids': ['base_heldout']}
        source.write_json(self.base / 'split_trainer.json', record)
        source.write_json(self.base / 'split.json', {'train_qids': ['base_train'], 'heldout_qids': ['base_heldout']})
        for side, rows in [('train', self.train), ('heldout', self.heldout)]:
            # Deliberately noncanonical whitespace: copying must retain exact line bytes.
            (self.base / (side + '.jsonl')).write_bytes(b''.join((json.dumps(r) + '\n').encode() for r in rows))
        base_entries = [self.entry(r, self.base_layout) for r in self.train + self.heldout]
        full.write_lines(self.base_layout / 'candidate_index.jsonl', base_entries)
        source.write_json(self.base_layout / 'MATERIALIZATION.json', {
            'artifacts': {'candidate_index.jsonl': source.pin(self.base_layout / 'candidate_index.jsonl')}})
        benchmarks = {}
        for name in full.inherited.BENCHMARKS:
            p = self.root / (name + '.json')
            source.write_json(p, [{'id': 'bench', 'dataset': 'scannet', 'scene_name': 'scene9999_00'}])
            benchmarks[name] = {**source.pin(p), 'rows': 1}
        source.write_json(self.base / 'MANIFEST.json', {'artifacts': {
            side + '.jsonl': source.pin(self.base / (side + '.jsonl')) for side in ('train', 'heldout')},
            'benchmark_sources': benchmarks})
        self.a_rows = [self.row('base_train', 'scene0001_00'),
                       self.row('new_train', 'scene0001_01'),
                       self.row('new_heldout', 'scene0002_01'),
                       self.row('new_scene', 'scene0088_00'),
                       self.row('blocked', 'scene9999_01'),
                       self.row('missing', 'scene0001_00'),
                       self.row('room_wrong', 'scene0001_00', category='room_size_estimation', target='22'),
                       self.row('wrong_gold', 'scene0001_00')]
        self.a_rows[5]['student_input']['frames'][0] = {'path': str(self.root / 'absent.png'), 'sha256': '0' * 64}
        self.decisions = []
        a_entries = []
        for row in self.a_rows:
            trace = {'path': str(self.run_a / 'attempts' / row['qid'] / 'trace.json'), 'sha256': 'f' * 64}
            row['sources'] = {'raw': trace}
            self.decisions.append({'id': row['qid'], 'accepted': True, 'answer_correct': True,
                'mechanically_complete': True, 'has_perceptual_evidence': True,
                'trace_path': trace['path'], 'trace_sha256': trace['sha256']})
            a_entries.append(self.entry(row, self.root_a))
        source.write_json(self.root_a / 'ACCEPTED_combined_r3_r4.json', self.decisions)
        full.write_lines(self.root_a / 'candidate_index.jsonl', a_entries)
        members = [{'id': r['qid'], 'dataset': r['dataset'], 'scene_name': r['scene'],
                    'question_type': r['category'], 'question': r['student_input']['question'],
                    'options': r['student_input']['options'], 'option_letters': ['A', 'B'] if r['student_input']['options'] else []}
                   for r in self.a_rows]
        self.members = self.root / 'members.jsonl'
        self.gold = self.root / 'gold.jsonl'
        full.write_lines(self.members, members)
        full.write_lines(self.gold, [{'id': r['qid'], 'ground_truth': 'B' if r['qid'] == 'wrong_gold' else r['target']} for r in self.a_rows])
        self.room = self.root / 'rooms.jsonl'
        full.write_lines(self.room, [{'question_type': 'absolute_size_room', 'video': 'scannet/scene0001_00.mp4',
            'conversations': [{'from': 'human', 'value': 'Room area in square meters?'}, {'from': 'gpt', 'value': '20'}]}])
        argv = ['build', '--output-mix', str(self.root / 'output'), '--output-layout', str(self.root / 'trainer'),
                '--out', str(self.root / 'audit'), '--source-mix', str(self.base), '--source-layout', str(self.base_layout),
                '--root-a', str(self.root_a), '--root-a-run', str(self.run_a), '--root-b-run', str(self.run_b),
                '--root-a-members', str(self.members), '--root-a-labels', str(self.gold),
                '--root-a-members-sha', source.sha(self.members), '--root-a-labels-sha', source.sha(self.gold),
                '--members', str(self.members), '--labels', str(self.gold), '--room-labels', str(self.room),
                '--members-sha', source.sha(self.members), '--labels-sha', source.sha(self.gold), '--room-sha', source.sha(self.room),
                '--split-sha', source.sha(self.base / 'split.json'), '--native-split-sha', source.sha(self.base / 'split_trainer.json'),
                '--expected-train', '1', '--expected-root-a', str(len(self.a_rows))]
        self.args = full.parser().parse_args(argv)
        # Root B is a different authority, not a superset of Root A's membership.
        self.args.members = self.root / 'b_members.jsonl'
        self.args.labels = self.root / 'b_gold.jsonl'
        full.write_lines(self.args.members, [])
        full.write_lines(self.args.labels, [])
        self.args.members_sha = source.sha(self.args.members)
        self.args.labels_sha = source.sha(self.args.labels)
        self.verify_args = full.parser().parse_args(['verify', '--output-mix', str(self.args.output_mix),
                '--output-layout', str(self.args.output_layout), '--out', str(self.args.out)])

    def row(self, qid, scene, category='object_rel_distance', target='A'):
        answer = target if category == 'room_size_estimation' else 'A'
        return {'qid': qid, 'dataset': 'scannet', 'scene': scene, 'category': category,
                'target': target, 'generation_commit': '1' * 40, 'validation_commit': '1' * 40,
                'native_answer_archive': {'native_answer_block': '<ANSWER>' + answer + '</ANSWER>',
                                           'target': '<answer>' + answer + '</answer>'},
                'student_input': {'question': 'Room area in square meters?' if category == 'room_size_estimation' else 'Which object is nearer?',
                    'options': [] if category == 'room_size_estimation' else ['chair', 'table'],
                    'frames': copy.deepcopy(self.frames), 'frame_indices': list(range(32)),
                    'timestamps': [i / 10 for i in range(32)], 'fps': 10.0, 'total_num_frames': 32}}

    def entry(self, row, layout):
        entry = {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                 'question_type': row['category'], 'pool': 'synthetic',
                 'answer': full.native_answer(row, 'bare')[0], 'generation_commit': '1' * 40, 'validation_commit': '1' * 40}
        return control.copy_entry(entry, compact.canonical_bytes(row), (row['target'] + '\n').encode(), layout)

    def test_build_verify_superset_split_drops_and_native_loader(self):
        summary = full.build(self.args)
        self.verify_args.native_loader = True
        result = full.verify(self.verify_args)
        self.assertTrue(result['out0_full_superset'])
        self.assertTrue(result['native_loader_passed'])
        self.assertEqual(summary['dropped_by_reason']['duplicate'], 1)
        for reason in ('benchmark_overlap', 'missing_frames', 'room_label_mismatch', 'ingest_refusal'):
            self.assertEqual(summary['dropped_by_reason'][reason], 1)
        train = {r['qid'] for r in source.read_jsonl(self.args.output_mix / 'train.jsonl')}
        held = {r['qid'] for r in source.read_jsonl(self.args.output_mix / 'heldout.jsonl')}
        self.assertIn('new_train', train)
        self.assertIn('new_heldout', held)
        self.assertEqual(summary['newly_hashed_group_count'], 1)
        self.assertTrue((self.args.output_mix / 'train.jsonl').read_bytes().startswith((self.base / 'train.jsonl').read_bytes()))
        for pin in summary['manifest'].values():
            self.assertEqual(source.sha(pin['path']), pin['sha256'])

    def test_manifest_corruption_is_rejected(self):
        full.build(self.args)
        with (self.args.output_mix / 'train.jsonl').open('ab') as stream:
            stream.write(b'\n')
        with self.assertRaisesRegex(ValueError, 'manifest_hash_mismatch'):
            full.verify(self.verify_args)

    def test_tolerated_numeric_estimate_uses_ground_truth_target(self):
        row = next(r for r in self.a_rows if r['qid'] == 'new_train')
        row.update(category='object_abs_distance', target='33')
        row['student_input'].update(question='Distance between the objects in meters?', options=[])
        row['native_answer_archive'] = {'native_answer_block': '<ANSWER>33</ANSWER>',
                                       'target': '<answer>33</answer>'}
        entries = list(source.read_jsonl(self.root_a / 'candidate_index.jsonl'))
        full.write_lines(self.root_a / 'candidate_index.jsonl',
                         [self.entry(row, self.root / 'numeric_source') if e['qid'] == row['qid'] else e for e in entries])
        members = list(source.read_jsonl(self.members))
        member = next(r for r in members if r['id'] == row['qid'])
        member.update(question_type=row['category'], question=row['student_input']['question'],
                      options=[], option_letters=[])
        full.write_lines(self.members, members)
        labels = list(source.read_jsonl(self.gold))
        next(r for r in labels if r['id'] == row['qid'])['ground_truth'] = '31.5'
        full.write_lines(self.gold, labels)
        self.args.root_a_members_sha = source.sha(self.members)
        self.args.root_a_labels_sha = source.sha(self.gold)
        self.assertTrue(source.census.grade(member, '31.5', '33')[0])
        full.build(self.args)
        path = self.args.output_mix / 'train.jsonl'
        rows = list(source.read_jsonl(path))
        built = next(r for r in rows if r['qid'] == row['qid'])
        self.assertEqual(built['target'], '31.5')
        self.assertEqual(built['target_provenance']['source'], 'ground_truth')
        self.assertEqual(built['native_answer_archive'], row['native_answer_archive'])
        index = {e['qid']: e for e in source.read_jsonl(self.args.output_layout / 'candidate_index.jsonl')}
        self.assertEqual(index[row['qid']]['answer'], '31.5')
        self.verify_args.native_loader = True
        self.assertTrue(full.verify(self.verify_args)['passed'])
        built['target'] = '33'
        path.write_bytes(b''.join(full.inherited.line_bytes(built) if json.loads(line)['qid'] == row['qid']
                                  else line for line in path.read_bytes().splitlines(keepends=True)))
        self.refresh_output_manifest(self.args.output_mix, 'mix')
        with self.assertRaisesRegex(ValueError, 'new_target_ground_truth_mismatch'):
            full.verify(self.verify_args)

    def refresh_output_manifest(self, root, name):
        manifest = source.read_json(root / 'MANIFEST.json')
        manifest['artifacts'] = full.inventory(root)
        source.write_json(root / 'MANIFEST.json', manifest)
        summary = source.read_json(self.args.out / 'BUILD_SUMMARY.json')
        summary['manifest'][name] = source.pin(root / 'MANIFEST.json')
        source.write_json(self.args.out / 'BUILD_SUMMARY.json', summary)

    def test_verify_rejects_out0_byte_changes_after_repin(self):
        full.build(self.args)
        path = self.args.output_mix / 'train.jsonl'
        lines = path.read_bytes().splitlines(keepends=True)
        row = json.loads(lines[0])
        lines[0] = full.inherited.line_bytes(row)
        path.write_bytes(b''.join(lines))
        self.refresh_output_manifest(self.args.output_mix, 'mix')
        with self.assertRaisesRegex(ValueError, 'OUT0_superset_byte_identity'):
            full.verify(self.verify_args)

    def test_dropped_qids_are_unique_across_roots(self):
        decision = next(d for d in self.decisions if d['id'] == 'base_train')
        with patch.object(source, 'root_b_decisions', return_value=iter([(decision, None)])):
            full.build(self.args)
        drops = list(source.read_jsonl(self.args.out / 'DROPPED_ROWS.jsonl'))
        self.assertEqual(len(drops), len({r['qid'] for r in drops}))
        duplicate = next(r for r in drops if r['qid'] == 'base_train')
        self.assertEqual(len(duplicate['occurrences']), 2)

    def test_frame_change_and_missing_are_rejected(self):
        frames = source.Frames()
        frames.check(self.frames[0])
        Path(self.frames[0]['path']).write_bytes(b'corrupt different bytes')
        with self.assertRaisesRegex(source.FrameError, 'frame_hash_mismatch'):
            frames.check(self.frames[0])
        with self.assertRaisesRegex(source.FrameError, 'missing_frames'):
            frames.check({'path': str(self.root / 'no-file'), 'sha256': '0' * 64})

    def test_room_requires_exact_fixed_label_and_scan(self):
        labels = source.room_labels(self.room, source.sha(self.room))
        row = self.row('room', 'scene0001_00', 'room_size_estimation', '20')
        source.check_room(row, '20', labels)
        for answer in ('20.5', '22', '20 square feet'):
            with self.assertRaises(ValueError):
                source.check_room(row, answer, labels)
        row['scene'] = 'scene0001_01'
        with self.assertRaises(ValueError):
            source.check_room(row, '20', labels)

    def test_root_b_snapshot_excludes_later_terminals_and_detects_drift(self):
        def terminal(qid):
            adir = self.run_b / 'attempts' / qid / 'b16384'
            path = self.run_b / 'terminals' / (qid + '__b16384.json')
            source.write_json(path, {'question_id': qid, 'budget': 16384, 'output': str(adir)})
            return path
        first = terminal('one')
        snap = source.snapshot_terminals(self.run_b, 1, self.root / 'snapshot.json')
        terminal('two')
        self.assertEqual(snap['selected_qids'], ['one'])
        first.write_bytes(first.read_bytes() + b'\n')
        result = list(source.root_b_decisions(snap, {'one': {}}, {'one': 'A'}))
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0][0]['accepted'])
        self.assertIn('snapshot_terminal_changed', result[0][0]['detail'])

    def test_light_census_calls_existing_strict_rule(self):
        qid = 'teacher'
        adir = self.run_b / 'attempts' / qid / 'b16384'
        trace_path = adir / 'finalized' / qid / f'trace_{qid}.json'
        source.write_json(trace_path, {'question_id': qid, 'run_receipt': {'round': 1313, 'fixture_only': False},
            'trace': [{'role': 'ai', 'provenance': 'provider', 'content': '<ANSWER>A</ANSWER>'}],
            'budget_terminal': False, 'tool_vlm_responses': []})
        (adir / 'archive').mkdir()
        for name in ('journal.jsonl', 'artifact_refs.jsonl'):
            (adir / 'archive' / name).write_text('')
        source.write_json(self.run_b / 'terminals' / f'{qid}__b16384.json',
                          {'question_id': qid, 'budget': 16384, 'output': str(adir)})
        snap = source.snapshot_terminals(self.run_b, 0, self.root / 'snapshot.json')
        member = {'question_type': 'object_rel_distance', 'options': ['x', 'y'], 'option_letters': ['A', 'B']}
        with patch.object(source.census, 'mechanically_complete', return_value=True), \
             patch.object(source.census, 'perceptual_evidence', return_value=[{'tool': 'fixture'}]):
            decision, payload = list(source.root_b_decisions(snap, {qid: member}, {qid: 'A'}))[0]
            self.assertTrue(decision['accepted'])
            self.assertEqual(decision['reason'], 'exact_option')
            wrong, _ = list(source.root_b_decisions(snap, {qid: member}, {qid: 'B'}))[0]
            self.assertFalse(wrong['accepted'])
            self.assertTrue(payload)

    def test_native_formats_and_parameterized_path_guard(self):
        row = self.row('q', 'scene0001_00')
        self.assertEqual(full.native_answer(row, 'bare'), ('A', 'A'))
        self.assertEqual(full.native_answer(row, 'native-block'), ('A', '<answer>A</answer>'))
        path = self.run_b / 'attempts/q/trace.json'
        self.assertEqual(ingest.allowed_path(path, self.run_b, str(path)), path)
        with self.assertRaises(ValueError):
            ingest.allowed_path(path, self.run_b)

    def test_fresh_root_b_reuses_native_authentication_and_rgb_sampling(self):
        qid = 'fresh_b'
        member = {'id': qid, 'dataset': 'scannet', 'scene_name': 'scannet__scene0001_00',
                  'source_scene_name': 'scene0001_00', 'question_type': 'object_rel_distance',
                  'question': 'Which object is nearer?', 'options': ['chair', 'table']}
        usage = {'input_tokens': 10, 'output_tokens': 3, 'total_tokens': 13}
        metadata = {'finish_reason': 'STOP', 'model_name': ingest.MODEL}
        call = {'id': 'call-1', 'name': 'find_frames_with_object'}
        def ai(content, calls):
            raw = {'content': content, 'response_metadata': metadata, 'tool_calls': calls,
                   'usage_metadata': usage}
            return {'role': 'ai', 'provenance': 'provider', 'content': content,
                    'response_metadata': metadata, 'tool_calls': calls,
                    'usage_metadata': usage, 'raw_response': raw}
        scene_frames = [{**frame, 'ordinal': i, 'timestamp_sec': i / 10}
                        for i, frame in enumerate(self.frames)]
        receipt_path = self.root / 'scene_receipt.json'
        source.write_json(receipt_path, {'frames': scene_frames,
            'video': {'fps': 10.0, 'decoded_frame_count': 32}})
        receipt_pin = source.pin(receipt_path)
        raw = {'question_id': qid, 'scene_name': member['scene_name'],
               'question_type': member['question_type'], 'question': member['question'],
               'run_receipt': {'schema': 'r1313-training-episode-v1', 'round': 1313, 'fixture_only': False,
                   'input_rows': [member], 'planner_output_budget_tokens': 16384,
                   'membership_sha256': 'a' * 64, 'selected_frames_sha256': receipt_pin['sha256'],
                   'scene_receipt': receipt_pin,
                   'student_inputs': {'modality': 'question_and_RGB_only', 'frames': scene_frames}},
               'trace': [ai('Inspect the object.', [call]),
                         {'role': 'tool', 'tool_call_id': call['id'], 'name': call['name'], 'content': 'frame 1'},
                         ai('<ANSWER>A</ANSWER>', [])]}
        payload = compact.canonical_bytes(raw)
        decision = {'id': qid, 'trace_sha256': compact.sha256_bytes(payload),
                    'trace_path': str(self.run_b / 'attempts' / qid / 'b16384/finalized' / qid / ('trace_' + qid + '.json')),
                    'accepted': True, 'answer_correct': True, 'mechanically_complete': True,
                    'has_perceptual_evidence': True, 'chosen_budget': 16384,
                    'perceptual_evidence': [{'tool_call_id': call['id'], 'tool': call['name']}]}
        row = source.fresh_row(decision, payload, self.run_b, source.Frames(), '1' * 40, '2' * 64)
        self.assertEqual(row['student_input'], self.row(qid, 'scene0001_00')['student_input'])
        self.assertEqual(full.native_answer(row, 'bare'), ('A', 'A'))
        broken = copy.deepcopy(raw)
        broken['run_receipt']['fixture_only'] = True
        payload = compact.canonical_bytes(broken)
        decision['trace_sha256'] = compact.sha256_bytes(payload)
        with self.assertRaisesRegex(ValueError, 'ingest_native_provenance'):
            source.fresh_row(decision, payload, self.run_b, source.Frames(), '1' * 40, '2' * 64)

    def test_split_inheritance_resists_pool_expansion(self):
        old = source.read_json(self.base / 'split_trainer.json')
        before = self.split.make_inherited_split(self.train + self.heldout, self.train + self.heldout, old)
        extra = [self.row('new_scan', 'scene0002_03'), self.row('unseen', 'scene0200_00')]
        rows = self.train + self.heldout + extra
        after = self.split.make_inherited_split(rows, rows, old)
        self.assertTrue(set(before['train_candidate_qids']) <= set(after['train_candidate_qids']))
        self.assertIn('new_scan', after['heldout_qids'])
        self.assertEqual(after['hashed_group_ids'], ['scannet/scene0200'])

    def test_no_overwrite_or_source_output_overlap(self):
        self.args.output_mix = self.base
        with self.assertRaisesRegex(ValueError, 'output_source_overlap'):
            full.build(self.args)


if __name__ == '__main__':
    unittest.main()
