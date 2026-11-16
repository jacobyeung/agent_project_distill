"""CPU integration checks; all test artifacts remain under r0dev/test_*.

Run after python -B -m parity_kit.r0dev. No pytest cache or cleanup is used.
"""
import ast
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from parity_kit import r0dev as r0
from parity_kit import r0dev_constants as constants
from parity_kit.common import install, key, policy, read, rows, sha, tasks


class R0DevTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install()
        cls.settings = read(r0.DEFAULT_OUT / 'settings_r0dev.json')
        cls.tasks = rows(cls.settings['tasks'][0])
        cls.source = rows(r0.QUESTIONS)
        cls.frames = read(cls.settings['frames_json'])['captures']
        cls.dense = read(cls.settings['dense_manifest'])['captures']
        cls.receipt = read(r0.DEFAULT_OUT / 'BUILD_R0DEV.json')
        cls.run_dir = Path(tempfile.mkdtemp(prefix='test_', dir=r0.DEFAULT_OUT))

    def test_counts_keys_and_runner_selection(self):
        from parity_kit.run_parity import select
        self.assertEqual(len(self.tasks), 2169)
        self.assertEqual(len({key(t) for t in self.tasks}), 2169)
        self.assertEqual(Counter(t['question_type'] for t in self.tasks), r0.EXPECTED_COUNTS)
        self.assertEqual(len(self.frames), 98)
        self.assertEqual(sum(len(c['frames']) for c in self.frames.values()), 3136)
        self.assertEqual(tasks(self.settings), self.tasks)
        self.assertEqual(select(self.settings), self.tasks)
        keys = [key(self.tasks[0]), key(self.tasks[-1])]
        self.assertEqual([key(t) for t in select(self.settings, keys)], keys)
        request = read(self.settings['request'])
        self.assertEqual(request['keys'], [key(t) for t in self.tasks])
        self.assertEqual(request['decode_budget'], policy().DECODE_BUDGET)
        self.assertIsNone(request['prompt_flag'])
        self.assertEqual(request['arm'], 'unflagged')
        self.assertEqual(request['layout'], 'duplicate')
        base = read(r0.BASE_SETTINGS)
        changed = {'tasks', 'frames_json', 'dense_manifest', 'request', 'frames_root'}
        self.assertEqual({k: v for k, v in self.settings.items() if k not in changed},
                         {k: v for k, v in base.items() if k not in changed})

    def test_task_labels_and_source_order(self):
        scorers = {t['question_type']: t['scorer'] for t in rows(r0.TASKS[0])}
        scorers['obj_appearance_order'] = scorers['object_rel_distance']
        for source, task in zip(self.source, self.tasks):
            self.assertEqual(task['id'], source['qid'])
            for name in ('scene', 'dataset', 'question_type', 'question', 'answer',
                         'fps', 'total_num_frames'):
                self.assertEqual(task[name], source[name])
            options = source['options']
            self.assertEqual(task['options'], ast.literal_eval(options) if isinstance(options, str) else options)
            self.assertEqual(task['ground_truth'], source['answer'])
            self.assertIsNone(task['released_answer'])
            self.assertNotIn('released_answer_in_options', task)
            self.assertEqual(task['source_frame_indices'], source['frame_indices'])
            self.assertEqual(task['native'], 'r0dev/' + source['scene'])
            self.assertEqual(task['room'], task['native'])
            self.assertEqual(task['scorer'], scorers[task['question_type']])

    def test_every_manifest_hash_and_layout(self):
        index = read(r0.MANIFEST)['scenes']
        self.assertEqual(set(self.frames), set(self.dense))
        for native, capture in self.frames.items():
            scene = capture['scene']
            path = r0.SCENE_MANIFESTS / (scene + '.json')
            self.assertEqual(sha(path), index['scannetpp/' + scene]['manifest_sha256'])
            manifest = read(path)
            self.assertEqual(capture['anchor_indices'], manifest['layout_f32'])
            self.assertEqual(capture['timestamps'], [i / capture['fps'] for i in manifest['layout_f32']])
            dense = self.dense[native]
            self.assertEqual(dense['anchor_slots'], list(range(32)))
            self.assertEqual(capture['frames'], dense['frames'])
            self.assertEqual([f['index'] for f in capture['frames']], manifest['layout_f32'])
            for frame in capture['frames']:
                self.assertEqual(frame['sha256'], manifest['frames'][str(frame['index'])])
                self.assertEqual(frame['path'], f"scannetpp/{scene}/{frame['index']:06d}.png")
        for name, digest in self.receipt['output_sha256s'].items():
            self.assertEqual(sha(r0.DEFAULT_OUT / name), digest)
        for pin in (*self.receipt['inputs'].values(), *self.receipt['scene_manifests'].values()):
            self.assertEqual(sha(pin['path']), pin['sha256'])

    def test_twenty_png_hashes(self):
        frames = [f for c in self.frames.values() for f in c['frames']]
        indices = [i * (len(frames) - 1) // 19 for i in range(20)]
        self.assertEqual(len(set(indices)), 20)
        checked = []
        for i in indices:
            frame = frames[i]
            self.assertEqual(sha(r0.FRAMES_ROOT / frame['path']), frame['sha256'])
            checked.append(frame)
        r0.write_new(self.run_dir / 'PNG_CHECKS.json', r0.json_bytes(checked))

    def test_bind_three_items_unchanged(self):
        from PIL import Image
        from e2e_reader import parity
        selected = [self.tasks[i] for i in (0, len(self.tasks) // 2, len(self.tasks) - 1)]
        self.assertEqual(len({t['scene'] for t in selected}), 3)
        checks = []
        for task in selected:
            before, settings_before = deepcopy(task), deepcopy(self.settings)
            bound = parity.bind_item(task, self.settings, verify=True)
            self.assertEqual(task, before)
            self.assertEqual(self.settings, settings_before)
            self.assertEqual(bound['id'], key(task))
            student = bound['row']['student_input']
            self.assertEqual(student['question'], task['question'])
            self.assertEqual(student['options'], task['options'])
            self.assertEqual(student['frame_indices'], task['source_frame_indices'])
            self.assertEqual(student['fps'], task['fps'])
            self.assertEqual(student['total_num_frames'], task['total_num_frames'])
            self.assertEqual(bound['row']['qid'], task['id'])
            frames = bound['frames']
            self.assertEqual(frames['dense_indices'], task['source_frame_indices'])
            self.assertEqual(frames['anchor_indices'], task['source_frame_indices'])
            self.assertEqual(frames['anchor_slots'], list(range(32)))
            self.assertEqual(len(frames['native_frames']), 32)
            frame = self.frames[task['native']]['frames'][16]
            with Image.open(r0.FRAMES_ROOT / frame['path']) as original:
                rgb = original.convert('RGB')
                self.assertEqual(frames['native_frames'][16].size, (640, 480))
                self.assertEqual(frames['native_frames'][16].tobytes(), rgb.tobytes())
            checks.append(dict(key=key(task), verified_frames=32, image_compared=frame['path']))
            for im in frames['native_frames']:
                im.close()
        r0.write_new(self.run_dir / 'BIND_CHECKS.json', r0.json_bytes(checks))

    def test_all_nine_scorers(self):
        from e2e_reader import parity
        results = {}
        for kind in sorted(r0.EXPECTED_COUNTS):
            task = next(t for t in self.tasks if t['question_type'] == kind)
            wrong = (next(chr(65 + i) for i in range(len(task['options']))
                          if chr(65 + i) != task['answer']) if task['options']
                     else str(100 * abs(float(task['answer'])) + 100))
            correct = parity.score(task, dict(text='<think>x</think>' + task['answer'], finish='stop'))
            incorrect = parity.score(task, dict(text='<think>x</think>' + wrong, finish='stop'))
            self.assertEqual(correct, dict(answer=1.0, released_answer=None), kind)
            self.assertEqual(incorrect, dict(answer=0.0, released_answer=None), kind)
            results[kind] = dict(scorer=task['scorer'], right=correct, wrong=incorrect)
        r0.write_new(self.run_dir / 'SCORE_CHECKS.json', r0.json_bytes(dict(types=results, deferred=[])))

    def test_deterministic_build(self):
        out = self.run_dir / 'determinism'
        payloads = []
        for _ in range(2):
            captured = {}
            with patch.object(r0, 'write_new', side_effect=lambda p, b: captured.__setitem__(p.name, b)):
                r0.build(out)
            payloads.append(captured)
        self.assertEqual(payloads[0], payloads[1])
        for name in r0.OUTPUT_NAMES[:4]:
            self.assertEqual(payloads[0][name], (r0.DEFAULT_OUT / name).read_bytes())

    def test_refuse_overwrite(self):
        with self.assertRaises(FileExistsError):
            r0.build(r0.DEFAULT_OUT)

    def test_refuse_layout_missing_frame_and_manifest_mismatch(self):
        row = deepcopy(self.source[0])
        manifest = read(r0.SCENE_MANIFESTS / (row['scene'] + '.json'))
        row['frame_indices'][1] += 1
        with self.assertRaisesRegex(ValueError, 'layout_f32'):
            r0._validate_row(row, manifest)
        with patch.object(Path, 'is_file', return_value=False):
            with self.assertRaisesRegex(ValueError, 'missing frame:'):
                r0._capture(self.source[0], manifest)
        entry = dict(read(r0.MANIFEST)['scenes']['scannetpp/' + row['scene']], manifest_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'manifest sha256 mismatch'):
            r0._load_scene(row['scene'], entry)

    def _journal(self, name, entries):
        path = self.run_dir / name
        r0.write_new(path, ''.join(json.dumps(r) + '\n' for r in entries).encode())
        return path

    def test_constants_synthetic_partitions(self):
        entries = []
        for kind in sorted(r0.EXPECTED_COUNTS):
            selected = [t for t in self.tasks if t['question_type'] == kind][:3]
            entries.extend(dict(key=key(t), question_type=kind, arm='own_depth',
                                scores=dict(answer=s, released_answer=1.0))
                           for t, s in zip(selected, (1.0, 0.0, None)))
        journals = [self._journal('partition_a.jsonl', entries[::2]),
                    self._journal('partition_b.jsonl', entries[1::2])]
        result = constants.report(journals, self.settings['tasks'][0])
        self.assertEqual(result['coverage'], 'partial')
        self.assertEqual(result['n_completed'], 27)
        self.assertEqual(result['n_scored'], 18)
        self.assertEqual(len(result['missing_keys']), 2169 - 27)
        expected = read(r0.SUMMARY)['constants']
        for kind, row in result['per_type'].items():
            self.assertEqual(row['mean_score'], 0.5)
            self.assertEqual(row['n_scored'], 2)
            self.assertEqual(row['n_completed'], 3)
            self.assertEqual(row['n_unscored'], 1)
            self.assertEqual(row['n_missing'], r0.EXPECTED_COUNTS[kind] - 3)
            self.assertEqual(row['constant_dev_score'], expected[kind][row['constant_metric']] / 100)
        out = self.run_dir / 'constants'
        constants.save_report(result, out)
        self.assertEqual(read(out / 'REPORT.json'), result)
        self.assertEqual((out / 'TABLE.txt').read_text(), constants.table(result))
        with self.assertRaises(FileExistsError):
            constants.save_report(result, out)

    def test_constants_reject_duplicate_unknown_and_invalid_scores(self):
        task = self.tasks[0]
        entry = dict(key=key(task), scores=dict(answer=1.0))
        journal = self._journal('one.jsonl', [entry])
        with self.assertRaisesRegex(ValueError, 'duplicate journal key'):
            constants.report([journal, journal], self.settings['tasks'][0])
        for name, entry, message in (
            ('unknown', dict(key='devrows:missing', scores=dict(answer=0)), 'unknown journal key'),
            ('invalid', dict(key=key(task), scores=dict(answer=2)), 'invalid answer score'),
        ):
            journal = self._journal(name + '.jsonl', [entry])
            with self.assertRaisesRegex(ValueError, message):
                constants.report([journal], self.settings['tasks'][0])


class R0ConstantsStandaloneTests(unittest.TestCase):
    """Exercise journal reporting even when a source identity error blocks build."""

    @classmethod
    def setUpClass(cls):
        r0.DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
        cls.run_dir = Path(tempfile.mkdtemp(prefix='constants_test_', dir=r0.DEFAULT_OUT))
        source = rows(r0.QUESTIONS)
        cls.sample = []
        for kind in sorted(r0.EXPECTED_COUNTS):
            cls.sample.extend(dict(id=r['qid'], question_type=kind)
                              for r in [r for r in source if r['question_type'] == kind][:4])
        cls.tasks_path = cls.run_dir / 'synthetic_tasks.jsonl'
        r0.write_new(cls.tasks_path, ''.join(json.dumps(t) + '\n' for t in cls.sample).encode())

    def test_report_and_cli(self):
        from contextlib import redirect_stdout
        import io
        import sys
        entries = []
        for kind in sorted(r0.EXPECTED_COUNTS):
            selected = [t for t in self.sample if t['question_type'] == kind]
            entries.extend(dict(key=key(t), question_type=kind, arm='own_depth',
                                scores=dict(answer=s, released_answer=1.0))
                           for t, s in zip(selected, (1.0, 0.0, None)))
        journals = []
        for part in range(2):
            path = self.run_dir / f'items_{part}.jsonl'
            r0.write_new(path, ''.join(json.dumps(r) + '\n' for r in entries[part::2]).encode())
            journals.append(path)
        out = self.run_dir / 'report'
        argv = ['r0dev_constants', '--journals', *map(str, journals),
                '--tasks', str(self.tasks_path), '--out', str(out)]
        stdout = io.StringIO()
        with patch.object(sys, 'argv', argv), redirect_stdout(stdout):
            constants.main()
        result = read(out / 'REPORT.json')
        self.assertEqual((result['n_expected'], result['n_completed'], result['n_scored']), (36, 27, 18))
        self.assertEqual(len(result['missing_keys']), 9)
        expected = read(r0.SUMMARY)['constants']
        for kind, row in result['per_type'].items():
            self.assertEqual(row['mean_score'], 0.5)
            self.assertEqual((row['n_missing'], row['n_unscored']), (1, 1))
            self.assertEqual(row['constant_dev_score'], expected[kind][row['constant_metric']] / 100)
        self.assertEqual(stdout.getvalue(), (out / 'TABLE.txt').read_text())
        with self.assertRaises(FileExistsError):
            constants.save_report(result, out)

    def test_duplicate_unknown_and_invalid(self):
        entry = dict(key=key(self.sample[0]), scores=dict(answer=1.0))
        journal = self.run_dir / 'duplicate.jsonl'
        r0.write_new(journal, (json.dumps(entry) + '\n').encode())
        with self.assertRaisesRegex(ValueError, 'duplicate journal key'):
            constants.report([journal, journal], self.tasks_path)
        for name, bad, message in (
            ('unknown', dict(key='devrows:missing', scores=dict(answer=0)), 'unknown journal key'),
            ('invalid', dict(key=key(self.sample[0]), scores=dict(answer=2)), 'invalid answer score'),
        ):
            path = self.run_dir / (name + '.jsonl')
            r0.write_new(path, (json.dumps(bad) + '\n').encode())
            with self.assertRaisesRegex(ValueError, message):
                constants.report([path], self.tasks_path)


if __name__ == '__main__':
    unittest.main()
