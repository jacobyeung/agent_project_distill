import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from student.compact_targets import answer_fullpool as full
from student.compact_targets import compact_control as control
from student.compact_targets import compact_counted_v1 as compact
from student.compact_targets import traceev_build as build
from student.compact_targets import traceev_extract as extract

source = full.source


class TraceEvidenceBuildTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(os.environ['COMPACT_TEST_OUTPUT']) / ('traceev_build_' + uuid4().hex)
        self.root.mkdir(parents=True)
        self.frames = []
        for i in range(32):
            path = self.root / f'frame{i:02d}.png'
            path.write_bytes(f'synthetic RGB {i}'.encode())
            self.frames.append(source.pin(path))
        self.base = self.root / 'base'
        self.layout = self.root / 'base_trainer'
        self.base.mkdir()
        self.layout.mkdir()
        self.splitter, _ = full.trainer_modules(full.TRAINER)
        self.rows = [self.row('train_count', 'scene0001_00', 'object_counting', '1'),
                     self.row('train_other', 'scene0001_00', 'object_size_estimation', '2.00'),
                     self.row('held', 'scene0002_00', 'object_counting', '2')]
        self.entries = {}
        for row in self.rows:
            trace = self.root / (row['qid'] + '_trace.json')
            source.write_json(trace, {'qid': row['qid'], 'synthetic': True})
            row['sources'] = {'raw': source.pin(trace)}
            entry = {'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                     'question_type': row['category'], 'pool': 'synthetic', 'answer': row['target'],
                     'generation_commit': '1' * 40, 'validation_commit': '1' * 40,
                     'strict_accepted_trace': source.pin(trace)}
            self.entries[row['qid']] = control.copy_entry(entry, (json.dumps(row, indent=1) + '\n').encode(),
                                                         (row['target'] + '\n').encode(), self.layout)
        full.write_lines(self.layout / 'candidate_index.jsonl', self.entries.values())
        record = {'schema': 'provisional-whole-scene-split-v1', 'seed': 17,
                  'heldout_fraction_of_groups': 0.1, 'group_policy': self.splitter.WHOLE_SCENE_GROUP_POLICY,
                  'train_group_ids': ['scannet/scene0001'], 'heldout_group_ids': ['scannet/scene0002'],
                  'train_scenes': ['scannet/scene0001_00'], 'heldout_scenes': ['scannet/scene0002_00'],
                  'train_candidate_qids': ['train_count', 'train_other'], 'heldout_qids': ['held']}
        for root in (self.base, self.layout):
            source.write_json(root / 'split_trainer.json', record)
            source.write_json(root / 'split.json', {'train_qids': ['train_count', 'train_other'], 'heldout_qids': ['held']})
        for side, rows in (('train', self.rows[:2]), ('heldout', self.rows[2:])):
            (self.base / (side + '.jsonl')).write_bytes(b''.join((json.dumps(row, indent=None) + '\n').encode() for row in rows))
        benchmarks = {}
        for name in full.inherited.BENCHMARKS:
            path = self.root / (name + '.json')
            source.write_json(path, [{'id': 'benchmark', 'dataset': 'scannet', 'scene_name': 'scene9999_00'}])
            benchmarks[name] = {**source.pin(path), 'rows': 1}
        source.write_json(self.base / 'BUILD_INPUTS.json', {'benchmark_sources': benchmarks})
        source.write_json(self.base / 'MANIFEST.json', {'artifacts': {
            name: source.pin(self.base / name) for name in ('BUILD_INPUTS.json', 'train.jsonl', 'heldout.jsonl', 'split.json', 'split_trainer.json')}})
        source.write_json(self.layout / 'MATERIALIZATION.json', {'artifacts': {
            'candidate_index.jsonl': source.pin(self.layout / 'candidate_index.jsonl')}})
        self.evidence = self.root / 'evidence_rows.jsonl'
        self.merge_map = self.root / 'vsi_merge_map.json'
        self.instances = self.root / 'instances.json'
        source.write_json(self.merge_map, [['chair', 'armchair'], ['chair', 'office chair']])
        source.write_json(self.instances, {'segGroups': [{'id': 11, 'label': 'chair'}, {'id': 22, 'label': 'chair'}]})
        self.args = build.parser().parse_args(['build', '--base-mix', str(self.base), '--base-layout', str(self.layout),
            '--merge-map', str(self.merge_map), '--evidence', str(self.evidence), '--output-mix', str(self.root / 'mix'),
            '--output-layout', str(self.root / 'trainer'), '--audit', str(self.root / 'audit')])
        self.verify_args = build.parser().parse_args(['verify', '--output-mix', str(self.args.output_mix),
            '--output-layout', str(self.args.output_layout), '--audit', str(self.args.audit), '--replay-sample', '200'])
        self.pin_patch = patch.multiple(build, BASE_INDEX_SHA=source.sha(self.layout / 'candidate_index.jsonl'),
            BASE_SPLIT_SHA=source.sha(self.layout / 'split_trainer.json'), BASE_TRAIN=2, BASE_HELDOUT=1)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)
        self.provenance_patch = patch.object(build, 'provenance', side_effect=lambda config: {
            'repo_commit': '2' * 40, 'dirty': False, 'config_sha256': source.sha(config)})
        self.provenance_patch.start()
        self.addCleanup(self.provenance_patch.stop)
        self.replay_patch = patch.object(build, 'replay_evidence', side_effect=lambda row: row['target'])
        self.replay_patch.start()
        self.addCleanup(self.replay_patch.stop)
        self.fact = self.evidence_row()
        self.save_evidence()

    def row(self, qid, scene, category, target):
        return {'qid': qid, 'scene': scene, 'dataset': 'scannet', 'category': category, 'target': target,
                'student_input': {'question': 'How many chairs are in the video?', 'options': [],
                    'frames': copy.deepcopy(self.frames), 'frame_indices': list(range(32)),
                    'timestamps': [i / 10 for i in range(32)], 'fps': 10.0, 'total_num_frames': 32}}

    def evidence_row(self, kind='traceev_frames_all'):
        entry, row = self.entries['train_count'], self.rows[0]
        values = {'frames': [3, 7], 'unique': False}
        ids = []
        if kind == 'traceev_count_list':
            values, ids = {'first_frames': [[11, 3], [22, 7]], 'count': 2}, [11, 22]
        question, target = extract.render(kind, ['chair'], values)
        frame_sha = extract.digest(self.frames)
        key = [frame_sha, kind, 'chair' if kind.startswith('traceev_frames_') else ids]
        checks, counting = [], []
        if kind == 'traceev_count_list':
            checks, counting = extract.count_label_checks(entry, row, 'chair', 2, extract.counting_catalog([entry]))
        selected = {k: entry[k] for k in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256', 'strict_accepted_trace')}
        return {'qid': f"traceev__{row['scene']}__{kind}__{extract.digest(key)[:12]}", 'scene': row['scene'],
            'dataset': row['dataset'], 'question_type': kind, 'supports': extract.SUPPORTS[kind],
            'question': question, 'target': target, 'fact_key': key, 'source_qids': [row['qid']],
            'source_traces': [entry['strict_accepted_trace']], 'extractor_commit': '1' * 40,
            'student_input': {**copy.deepcopy(row['student_input']), 'question': question, 'options': []},
            'label_check': checks[0] if checks else None,
            'evidence': {'tool_calls': [], 'gt': {'instance_ids': ids, 'labels': ['chair'],
                'assets': {'instances': source.pin(self.instances),
                           'mesh': source.pin(self.root / 'train_count_trace.json')}, 'values_unrounded': values},
                'source_entry': selected, 'selected_frames_sha256': frame_sha,
                'v3_index_sha256': build.BASE_INDEX_SHA, 'v3_split_sha256': build.BASE_SPLIT_SHA,
                'label_checks': checks, 'counting_entries': counting, 'owner_qid': row['qid']}}

    def save_evidence(self, rows=None):
        full.write_lines(self.evidence, rows if rows is not None else [self.fact])

    def reseal(self, root, name):
        manifest = source.read_json(root / 'MANIFEST.json')
        manifest['artifacts'] = full.inventory(root)
        source.write_json(root / 'MANIFEST.json', manifest)
        summary = source.read_json(self.args.audit / 'BUILD_SUMMARY.json')
        summary['manifest'][name] = source.pin(root / 'MANIFEST.json')
        if name == 'trainer':
            summary['candidate_index'] = source.pin(root / 'candidate_index.jsonl')
        source.write_json(self.args.audit / 'BUILD_SUMMARY.json', summary)

    def test_carry_identity_sharded_evidence_and_native_loader(self):
        result = build.build(self.args)
        self.assertEqual(result['counts']['train']['total'], 3)
        self.assertEqual(result['counts']['heldout']['total'], 1)
        new = {entry['qid']: entry for entry in source.read_jsonl(self.args.output_layout / 'candidate_index.jsonl')}
        for qid, old in self.entries.items():
            self.assertEqual(control.bundle(old)[1:], control.bundle(new[qid])[1:])
        self.assertTrue((self.args.output_mix / 'train.jsonl').read_bytes().startswith((self.base / 'train.jsonl').read_bytes()))
        self.assertEqual((self.args.output_mix / 'heldout.jsonl').read_bytes(), (self.base / 'heldout.jsonl').read_bytes())
        relative = Path(new[self.fact['qid']]['row_path']).relative_to(self.args.output_layout)
        self.assertEqual(relative.parts[0], 'targets_traceev')
        self.assertEqual(len(relative.parts[1]), 2)
        self.verify_args.native_loader = True
        verification = build.verify(self.verify_args)
        self.assertTrue(verification['passed'])
        self.assertTrue(verification['checks']['native_loader']['passed'])
        self.assertEqual(verification['checks']['replay_sample']['rows'], 1)
        self.assertEqual(source.read_json(self.args.audit / 'VERIFICATION.json'), verification)

    def test_native_loader_report_preserves_core_verification(self):
        build.build(self.args)
        self.assertTrue(build.verify(self.verify_args)['passed'])
        core_report = (self.args.audit / 'VERIFICATION.json').read_bytes()
        args = build.parser().parse_args(['verify', '--output-mix', str(self.args.output_mix),
            '--output-layout', str(self.args.output_layout), '--audit', str(self.args.audit),
            '--native-loader', '--verification-name', 'NATIVE_VERIFICATION.json'])
        result = build.verify(args)
        self.assertTrue(result['checks']['native_loader']['passed'])
        self.assertEqual((self.args.audit / 'VERIFICATION.json').read_bytes(), core_report)
        self.assertEqual(source.read_json(self.args.audit / 'NATIVE_VERIFICATION.json'), result)

    def test_heldout_source_refused(self):
        self.fact.update(scene='scene0002_00', source_qids=['held'])
        self.save_evidence()
        with self.assertRaisesRegex(ValueError, 'heldout'):
            build.build(self.args)

    def test_benchmark_physical_group_refused(self):
        with patch.object(full, 'benchmark_groups', return_value=(set(), {'scannet/scene0001'})):
            with self.assertRaisesRegex(ValueError, 'benchmark'):
                build.build(self.args)

    def test_leakage_precision_and_invalid_frames_refused(self):
        cases = [('target', 'world 3'), ('target', '0.123'), ('target', '0, 33'),
                 ('question', self.fact['question'] + '\ninstance 17')]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                row = copy.deepcopy(self.fact)
                row[key] = value
                row['student_input']['question'] = row['question']
                self.save_evidence([row])
                self.args.audit = self.root / ('audit_bad_' + uuid4().hex)
                with self.assertRaises(ValueError):
                    build.build(self.args)

    def test_duplicate_fact_refused(self):
        self.save_evidence([self.fact, self.fact])
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            build.build(self.args)

    def test_new_frame_and_timing_refused(self):
        self.fact['student_input']['timestamps'][0] = 0.01
        self.save_evidence()
        with self.assertRaisesRegex(ValueError, 'student_input'):
            build.build(self.args)

    def test_count_disagreement_and_exclusions_preserve_heldout(self):
        self.fact = self.evidence_row('traceev_count_list')
        self.save_evidence()
        exclusions = self.root / 'exclude.txt'
        exclusions.write_text('train_count\nheld\n')
        self.args.exclude_base_qids = exclusions
        summary = build.build(self.args)
        self.assertEqual(summary['counts']['train']['total'], 2)
        index = {entry['qid']: entry for entry in source.read_jsonl(self.args.output_layout / 'candidate_index.jsonl')}
        self.assertNotIn('train_count', index)
        self.assertIn('held', index)
        row = control.bundle(index[self.fact['qid']])[0]
        self.assertEqual(row['label_check'], self.fact['label_check'])
        self.assertFalse(row['label_check']['agree'])
        composition = source.read_json(self.args.output_mix / 'COMPOSITION.json')
        self.assertEqual(composition['base_exclusions']['excluded_train'], 1)
        self.assertEqual(composition['label_checks']['scannet']['disagreement_percent'], 100)
        self.assertTrue(build.verify(self.verify_args)['passed'])

    def test_dirty_tree_and_existing_output_refused(self):
        with patch.object(build, 'provenance', return_value={'repo_commit': '2' * 40, 'dirty': True, 'config_sha256': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'dirty'):
                build.build(self.args)
        self.args.audit = self.root / 'audit_clean'
        build.build(self.args)
        with self.assertRaisesRegex(ValueError, 'output_exists'):
            build.build(self.args)

    def test_index_answer_mismatch_refused_even_with_refreshed_manifest(self):
        build.build(self.args)
        path = self.args.output_layout / 'candidate_index.jsonl'
        entries = list(source.read_jsonl(path))
        next(entry for entry in entries if entry['qid'] == self.fact['qid'])['answer'] = '31'
        full.write_lines(path, entries)
        materialization = source.read_json(self.args.output_layout / 'MATERIALIZATION.json')
        materialization['artifacts']['candidate_index.jsonl'] = source.pin(path)
        source.write_json(self.args.output_layout / 'MATERIALIZATION.json', materialization)
        self.reseal(self.args.output_layout, 'trainer')
        with self.assertRaisesRegex(ValueError, 'index_target'):
            build.verify(self.verify_args)
        self.assertFalse(source.read_json(self.args.audit / 'VERIFICATION.json')['passed'])

    def test_replay_mismatch_fails_closed(self):
        build.build(self.args)
        with patch.object(build, 'replay_evidence', return_value='wrong'):
            with self.assertRaisesRegex(ValueError, 'replay'):
                build.verify(self.verify_args)
        self.assertFalse(source.read_json(self.args.audit / 'VERIFICATION.json')['passed'])

    def test_manifest_corruption_refused(self):
        build.build(self.args)
        with (self.args.output_mix / 'train.jsonl').open('ab') as stream:
            stream.write(b'\n')
        with self.assertRaisesRegex(ValueError, 'manifest_hash'):
            build.verify(self.verify_args)

    def test_byte_drift_refused_even_with_refreshed_manifest(self):
        build.build(self.args)
        path = self.args.output_mix / 'heldout.jsonl'
        full.write_lines(path, self.rows[2:])
        self.reseal(self.args.output_mix, 'mix')
        with self.assertRaisesRegex(ValueError, 'base_mix_bytes'):
            build.verify(self.verify_args)

    def test_transfer_lists_are_complete_balanced_and_have_no_new_frames(self):
        build.build(self.args)
        args = build.parser().parse_args(['transfer', '--output-mix', str(self.args.output_mix),
            '--output-layout', str(self.args.output_layout), '--audit', str(self.args.audit),
            '--output-xfer', str(self.root / 'xfer')])
        result = build.transfer(args)
        self.assertEqual(result['new_frame_files'], 0)
        actual = []
        for pin in result['lists']['set']:
            actual.extend(Path(pin['path']).read_text().splitlines())
        expected = {str(path.relative_to('/data2')) for root in (self.args.output_mix, self.args.output_layout)
                    for path in root.rglob('*') if path.is_file()}
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(expected))
        counts = [pin['files'] for pin in result['lists']['set']]
        self.assertLessEqual(max(counts) - min(counts), 1)
        self.assertFalse(result['pull_executed'])
        for pin in result['lists']['frames']:
            self.assertEqual(Path(pin['path']).read_bytes(), b'')

    def test_merge_group_sibling_drop_is_audited_and_reverified(self):
        source.write_json(self.instances, {'segGroups': [{'id': 11, 'label': 'chair'}, {'id': 22, 'label': 'office chair'}]})
        self.fact['evidence']['gt']['assets']['instances'] = source.pin(self.instances)
        self.save_evidence()
        summary = build.build(self.args)
        self.assertEqual(summary['evidence_rows'], 0)
        self.assertEqual(summary['source_evidence_rows'], 1)
        self.assertEqual(summary['evidence_drops'], {'vsi_merge_group_sibling': 1})
        drops = list(source.read_jsonl(self.args.audit / 'EVIDENCE_DROPS.jsonl'))
        self.assertEqual(drops[0]['siblings'], {'chair': ['office chair']})
        result = build.verify(self.verify_args)
        self.assertTrue(result['passed'])
        self.assertEqual(result['checks']['vsi_merge_group_sibling']['dropped_rows'], 1)

    def test_merge_group_filter_authenticates_instance_bytes(self):
        source.write_json(self.instances, {'segGroups': [{'id': 11, 'label': 'office chair'}]})
        with self.assertRaisesRegex(ValueError, 'sha256_mismatch'):
            build.build(self.args)

    def test_carried_training_target_mismatch_is_never_exempt(self):
        row = self.rows[1]
        row['target'] = 'Context.\n2.00'
        self.entries[row['qid']] = control.copy_entry(self.entries[row['qid']], compact.canonical_bytes(row),
                                                     (row['target'] + '\n').encode(), self.root / 'training_context')
        full.write_lines(self.layout / 'candidate_index.jsonl', self.entries.values())
        full.write_lines(self.base / 'train.jsonl', self.rows[:2])
        source.write_json(self.layout / 'MATERIALIZATION.json', {'artifacts': {
            'candidate_index.jsonl': source.pin(self.layout / 'candidate_index.jsonl')}})
        manifest = source.read_json(self.base / 'MANIFEST.json')
        manifest['artifacts']['train.jsonl'] = source.pin(self.base / 'train.jsonl')
        source.write_json(self.base / 'MANIFEST.json', manifest)
        with patch.object(build, 'BASE_INDEX_SHA', source.sha(self.layout / 'candidate_index.jsonl')):
            self.fact['evidence']['v3_index_sha256'] = build.BASE_INDEX_SHA
            self.save_evidence()
            build.build(self.args)
            with self.assertRaisesRegex(ValueError, 'index_target_equality'):
                build.verify(self.verify_args)
        result = source.read_json(self.args.audit / 'VERIFICATION.json')
        self.assertEqual(result['checks']['index_target_equality']['exempt_heldout_count'], 0)
        self.assertEqual(result['checks']['index_target_equality']['mismatches'],
                         [{'qid': 'train_other', 'side': 'train', 'base_carried': True}])

    def test_carried_heldout_context_is_not_silently_rewritten(self):
        heldout = self.rows[2]
        heldout['target'] = 'Observations (1)\nTwo chairs are visible.\nEnd of reasoning.\n2'
        self.entries['held'] = control.copy_entry(self.entries['held'], compact.canonical_bytes(heldout),
                                                 (heldout['target'] + '\n').encode(), self.root / 'heldout_context')
        full.write_lines(self.layout / 'candidate_index.jsonl', self.entries.values())
        full.write_lines(self.base / 'heldout.jsonl', [heldout])
        source.write_json(self.layout / 'MATERIALIZATION.json', {'artifacts': {
            'candidate_index.jsonl': source.pin(self.layout / 'candidate_index.jsonl')}})
        manifest = source.read_json(self.base / 'MANIFEST.json')
        manifest['artifacts']['heldout.jsonl'] = source.pin(self.base / 'heldout.jsonl')
        source.write_json(self.base / 'MANIFEST.json', manifest)
        with patch.object(build, 'BASE_INDEX_SHA', source.sha(self.layout / 'candidate_index.jsonl')):
            self.fact['evidence']['v3_index_sha256'] = build.BASE_INDEX_SHA
            self.save_evidence()
            build.build(self.args)
            result = build.verify(self.verify_args)
            self.assertTrue(result['passed'])
            self.assertEqual(result['checks']['index_target_equality']['exempt_heldout_qids'], ['held'])
            self.assertEqual(result['checks']['index_target_equality']['exempt_heldout_count'], 1)
            self.assertEqual(result['checks']['index_target_equality']['mismatch_count'], 0)
            self.assertTrue(result['checks']['base_carried_bytes']['passed'])
            self.assertTrue(result['checks']['replay_sample']['passed'])
            path = self.args.output_layout / 'candidate_index.jsonl'
            entries = list(source.read_jsonl(path))
            next(entry for entry in entries if entry['qid'] == 'held')['answer'] = '3'
            full.write_lines(path, entries)
            materialization = source.read_json(self.args.output_layout / 'MATERIALIZATION.json')
            materialization['artifacts']['candidate_index.jsonl'] = source.pin(path)
            source.write_json(self.args.output_layout / 'MATERIALIZATION.json', materialization)
            self.reseal(self.args.output_layout, 'trainer')
            with self.assertRaisesRegex(ValueError, 'base_index_metadata_changed'):
                build.verify(self.verify_args)


if __name__ == '__main__':
    unittest.main()
