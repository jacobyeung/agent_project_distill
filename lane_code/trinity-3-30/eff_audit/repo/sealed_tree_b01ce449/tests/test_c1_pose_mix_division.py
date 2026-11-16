"""Division-pinned pose mix: rows-only (A3-style) sources, parent-division admission and row drops."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from student_pilot import c1_pose_mix as mix
from student_pilot.p3_provenance import sha256

A1_ROWS = 'A1 all_frames32 pose-only rows; every slot carries depth'


def pin(path):
    return {'path': str(path), 'sha256': sha256(path)}


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')
    return pin(path)


def dense(dataset, scene, a1_schema=True):
    sample = dict(recording=dict(sampling=dict(variant='all_frames32')))
    if a1_schema:
        sample.update(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames')
    row = dict(category='camera_pose_only', dataset=dataset, scene=scene, pose_sample=sample,
               student_input=dict(frames=[dict(path=f'/data2/k8pd/{i}.png', sha256='0' * 40) for i in range(32)]))
    target = dict(camera=[[0.] * 9] * 32, camera_mask=[True] * 32)
    return row, target


def database(path, rows):
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT NOT NULL, target TEXT NOT NULL)')
        conn.executemany('INSERT INTO rows VALUES (?,?,?)', [(i, json.dumps(r), json.dumps(t)) for i, (r, t) in enumerate(rows)])
    return pin(path)


class PoseMixDivisionTest(unittest.TestCase):
    def setUp(self):
        base = os.environ.get('LANE_TEST_OUTPUT')
        self.tmp = Path(tempfile.mkdtemp(prefix='posemix_div_', dir=base))
        division = lambda train, held, **extra: dict(schema=mix.DIVISION_SCHEMA, training_only=True, seed=17,
                                                    train_scenes=train, heldout_scenes=held, **extra)
        self.parent = dump(self.tmp / 'parent.json', division(['d1/a', 'd1/b'], ['d1/h']))
        self.child = dump(self.tmp / 'child.json', division(['d1/a', 'd1/b', 'd3/c'], ['d1/h', 'd3/g'],
                                                          parent_division=self.parent))
        self.model = dump(self.tmp / 'model.json', {'kind': 'base'})
        self.a1_receipt = dict(
            schema='pose-stream-a2-v1', count=2, model=self.model,
            database=database(self.tmp / 'a1.sqlite', [dense('d1', 'a'), dense('d1', 'b')]),
            settings=dict(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames', camera={}),
            inputs=dict(division=self.parent))
        self.a1 = dump(self.tmp / 'a1.json', self.a1_receipt)
        self.a3_receipt = dict(schema='pose-stream-a3-v1', row_schema=A1_ROWS, test_scene_hits_in_rows=0, count=2,
                               database=database(self.tmp / 'a3.sqlite', [dense('d3', 'c'), dense('d3', 'c')]))
        self.a3 = dump(self.tmp / 'a3.json', self.a3_receipt)
        self.n = 0

    def spec(self, sources, division=True, counts=None):
        value = dict(schema=mix.SCHEMA, sources=[dict(kind='rows', receipt=r, frame_prefix=None) for r in sources])
        for source, count in zip(value['sources'], counts or []):
            source['count'] = count
        if division:
            value['division'] = self.child
        self.n += 1
        return dump(self.tmp / f'spec{self.n}.json', value)

    def run_prepare(self, spec, excluded=lambda row, b, r: (False, 0), check=None):
        out = self.tmp / f'out{self.n}'
        out.mkdir()
        return mix.prepare(spec, out, set(), set(), excluded, check)

    def with_rows(self, name, receipt, rows):
        return dump(self.tmp / f'{name}.json', {**receipt, 'count': len(rows),
                                                'database': database(self.tmp / f'{name}.sqlite', rows)})

    def test_division_pinned_mix_admits_parent_and_rows_only_sources(self):
        entry, settings = self.run_prepare(self.spec([self.a1, self.a3], counts=[2, 2]))
        self.assertEqual([s['count'] for s in entry['sources']], [2, 2])
        self.assertEqual((entry['count'], entry['division']), (4, self.child))
        self.assertEqual(settings['inputs']['division'], self.child)
        self.assertEqual(settings['model'], self.model)
        order = json.loads(Path(entry['order']['path']).read_text())
        self.assertEqual(order, [[0, 0], [0, 1], [1, 0], [1, 1]])

    def test_rows_outside_the_division_train_scenes_are_refused(self):
        for name, receipt, scene in (('a1x', self.a1_receipt, ('d1', 'x')), ('a3g', self.a3_receipt, ('d3', 'g'))):
            source = self.with_rows(name, receipt, [dense('d3', 'c'), dense(*scene)])
            other = self.a3 if receipt is self.a1_receipt else self.a1
            sources = [source, other] if receipt is self.a1_receipt else [other, source]
            with self.assertRaisesRegex(ValueError, '1 selected rows outside the mix division'):
                self.run_prepare(self.spec(sources))

    def test_spec_counts_must_match_before_benchmark_exclusion(self):
        hit = lambda row, b, r: (row['scene'] == 'b', 1 if row['scene'] == 'c' else 0)
        entry, _ = self.run_prepare(self.spec([self.a1, self.a3], counts=[2, 2]), excluded=hit)
        self.assertEqual([s['benchmark_rows_dropped'] for s in entry['sources']], [1, 0])
        with self.assertRaisesRegex(ValueError, 'the spec expects 3'):
            self.run_prepare(self.spec([self.a1, self.a3], counts=[2, 3]))

    def test_row_check_runs_on_every_selected_row_and_records_the_uv_span(self):
        seen = []
        def check(row, target):
            seen.append(row['scene'])
            return (1.0, 990.0) if row['scene'] == 'c' else (2.0, 500.0)
        entry, _ = self.run_prepare(self.spec([self.a1, self.a3]), check=check)
        self.assertEqual(seen, ['a', 'b', 'c', 'c'])
        self.assertEqual([s['uv_range'] for s in entry['sources']], [[2.0, 500.0], [1.0, 990.0]])
        def bad(row, target):
            raise ValueError('layout differs')
        with self.assertRaisesRegex(ValueError, 'row 0 fails the training row check: layout differs'):
            self.run_prepare(self.spec([self.a1, self.a3]), check=bad)

    def test_benchmark_exclusion_still_drops_train_scene_rows(self):
        hit = lambda row, b, r: (row['scene'] == 'b', 1 if row['scene'] == 'c' else 0)
        entry, _ = self.run_prepare(self.spec([self.a1, self.a3]), excluded=hit)
        order = json.loads(Path(entry['order']['path']).read_text())
        self.assertEqual(order, [[0, 0], [1, 0], [1, 1]])
        self.assertEqual((entry['benchmark_rows_dropped'], entry['reported_overlap_rows']), (1, 2))

    def test_mix_without_division_is_unchanged(self):
        entry, settings = self.run_prepare(self.spec([self.a1], division=False))
        self.assertEqual(entry['count'], 2)
        self.assertNotIn('division', entry)
        self.assertEqual(set(entry['sources'][0]), {'kind', 'receipt', 'database', 'frame_prefix', 'count'})
        self.assertEqual(settings['inputs']['division'], self.parent)

    def test_rows_only_source_needs_the_mix_division(self):
        with self.assertRaisesRegex(ValueError, 'needs the pose mix division'):
            self.run_prepare(self.spec([self.a1, self.a3], division=False))

    def test_rows_only_source_alone_has_no_settings(self):
        with self.assertRaisesRegex(ValueError, 'one A1-schema row source'):
            self.run_prepare(self.spec([self.a3]))

    def test_rows_only_receipt_and_rows_must_be_a1_schema(self):
        for change in (dict(row_schema='other'), dict(test_scene_hits_in_rows=1), dict(count=4)):
            receipt = dump(self.tmp / f'bad{len(change)}{list(change)[0]}.json', {**self.a3_receipt, **change})
            with self.assertRaises(ValueError):
                self.run_prepare(self.spec([self.a1, receipt]))
        rows = database(self.tmp / 'a3old.sqlite', [dense('d3', 'c', a1_schema=False)])
        receipt = dump(self.tmp / 'a3old.json', {**self.a3_receipt, 'count': 1, 'database': rows})
        with self.assertRaisesRegex(ValueError, 'not an all-frame A1-schema row'):
            self.run_prepare(self.spec([self.a1, receipt]))

    def test_unrelated_or_widening_parent_division_is_refused(self):
        other = dump(self.tmp / 'other.json', dict(schema=mix.DIVISION_SCHEMA, training_only=True,
                                                   train_scenes=['d1/a'], heldout_scenes=['d1/z']))
        receipt = json.loads(Path(self.a1['path']).read_text())
        receipt['inputs']['division'] = other
        foreign = dump(self.tmp / 'a1_other.json', receipt)
        with self.assertRaisesRegex(ValueError, 'admitted parent'):
            self.run_prepare(self.spec([foreign, self.a3]))
        # A parent whose held-out scene the child trains on is not admitted.
        leaky = dump(self.tmp / 'leaky_parent.json', dict(schema=mix.DIVISION_SCHEMA, training_only=True,
                                                          train_scenes=['d1/a'], heldout_scenes=['d1/b']))
        child = json.loads(Path(self.child['path']).read_text())
        child['parent_division'] = leaky
        self.child = dump(self.tmp / 'child_leaky.json', child)
        receipt['inputs']['division'] = leaky
        leaky_a1 = dump(self.tmp / 'a1_leaky.json', receipt)
        with self.assertRaisesRegex(ValueError, 'admitted parent'):
            self.run_prepare(self.spec([leaky_a1, self.a3]))

    def test_division_must_be_training_only_and_disjoint(self):
        child = json.loads(Path(self.child['path']).read_text())
        child['heldout_scenes'] = child['heldout_scenes'] + ['d1/a']
        self.child = dump(self.tmp / 'child_overlap.json', child)
        with self.assertRaisesRegex(ValueError, 'overlap'):
            self.run_prepare(self.spec([self.a1, self.a3]))

    def clip_spec(self, scenes, fingerprints):
        from student_pilot.c1r_clips import fingerprint
        census = [dict(dataset=d, scene=sc, fps=10.0, total_num_frames=40, pose_count=40) for d, sc in scenes]
        a1_plan = dump(self.tmp / f'a1plan{self.n}.json', dict(schema='recording-pose-plan-v1', scenes=census))
        dense_plan = dump(self.tmp / f'dense{self.n}.json', dict(schema='c1r-dense-plan-v2', a1_plan=a1_plan))
        prints = [fingerprint(census[j]) if j is not None else 'f' * 64 for j in fingerprints]
        plan = self.tmp / f'clips{self.n}.jsonl'
        plan.write_text(''.join(json.dumps(dict(i=i, layout='duplicate', recording_fingerprint=f)) + '\n'
                                for i, f in enumerate(prints)))
        spec = json.loads(Path(self.spec([self.a1])['path']).read_text())
        spec['sources'].insert(0, dict(kind='c1r_clips', clips_plan=pin(plan), dense_plan=dense_plan, teacher=self.model,
                                       cache_root=str(self.tmp), model=self.model, layout='duplicate', count=len(prints)))
        return dump(self.tmp / f'spec_clip{self.n}.json', spec)

    def test_division_pinned_mix_admits_clips_whose_scenes_are_train_scenes(self):
        entry, _ = self.run_prepare(self.clip_spec([('d1', 'a'), ('d1', 'b')], [0, 1, 0]))
        self.assertEqual(entry['teacher_rows'], 3)
        self.assertEqual(entry['count'], 3 + 2)

    def test_division_pinned_mix_refuses_a_clip_from_a_non_train_scene(self):
        for scenes, prints in ((([('d1', 'a'), ('d1', 'h')]), [0, 1]), ((['d1', 'a'],), [0, None]),
                               (([('d1', 'a'), ('d3', 'g')]), [1])):
            scenes = [tuple(s) for s in scenes]
            with self.assertRaisesRegex(ValueError, 'outside the pose mix division train scenes'):
                self.run_prepare(self.clip_spec(scenes, prints))

    def test_a4_rows_only_schemas_are_admitted_with_their_row_schema(self):
        for schema, row_schema in (('pose-stream-a4-v1', A1_ROWS),
                                   ('pose-stream-a4m-v1', 'A1 all_frames32 pose-only rows; A3 layout; MP3D rooms')):
            a4 = self.with_rows(schema, {**self.a3_receipt, 'schema': schema, 'row_schema': row_schema},
                                [dense('d3', 'c')])
            entry, _ = self.run_prepare(self.spec([self.a1, a4]))
            self.assertEqual(entry['count'], 3)
            wrong = self.with_rows(schema + 'x', {**self.a3_receipt, 'schema': schema, 'row_schema': 'other'},
                                   [dense('d3', 'c')])
            with self.assertRaisesRegex(ValueError, 'all-frame A1-schema stream'):
                self.run_prepare(self.spec([self.a1, wrong]))

    def test_ancestor_division_is_admitted_only_along_a_consistent_chain(self):
        division = lambda train, held, **extra: dict(schema=mix.DIVISION_SCHEMA, training_only=True, seed=17,
                                                    train_scenes=train, heldout_scenes=held, **extra)
        grandchild = dump(self.tmp / 'grand.json', division(['d1/a', 'd1/b', 'd3/c', 'd4/m'], ['d1/h', 'd3/g', 'd4/v'],
                                                            parent_division=self.child))
        self.assertTrue(mix.ancestor_admits(grandchild, self.parent))
        self.assertTrue(mix.ancestor_admits(grandchild, self.child))
        self.assertFalse(mix.ancestor_admits(self.parent, grandchild))
        widened = dump(self.tmp / 'widen.json', division(['d1/a', 'd3/c'], ['d1/h', 'd1/b'], parent_division=self.child))
        self.assertFalse(mix.ancestor_admits(widened, self.parent))
        from student_pilot import carrier_c1_run as run
        self.assertTrue(run.division_admits(self.parent, grandchild))
        self.assertFalse(run.division_admits(widened, grandchild))

    def test_spec_fields_are_closed(self):
        rows = [dict(kind='rows', receipt=self.a1, frame_prefix=None)]
        mix.validate_spec(dict(schema=mix.SCHEMA, sources=rows, note='legacy metadata'))
        with self.assertRaisesRegex(ValueError, 'spec fields differ'):
            mix.validate_spec(dict(schema=mix.SCHEMA, sources=rows, division=self.child, extra=1))
        with self.assertRaisesRegex(ValueError, 'spec fields differ'):
            mix.validate_spec(dict(schema=mix.SCHEMA, sources=[dict(kind='rows', receipt=self.a1, frame_prefix=None)],
                                   division='not a pin'))


class PoseRowCheckTest(unittest.TestCase):
    def test_augmentation_settings_are_required(self):
        from unittest.mock import patch
        import torch
        from student_pilot import carrier_c1_run as run
        augment = dict(seed=3, brightness=.3, contrast=.3, saturation=.3, hue=.05, grayscale_p=.05, blur_p=.1,
                       blur_kernel=5, blur_sigma=[.1, 2.])
        tensors = dict(aux_point_depth_mask=torch.tensor([[[True, False]]]),
                       aux_point_depth_uv=torch.tensor([[[[3., 4.], [0., 0.]]]]))
        with patch.object(run.data, 'layout_inputs'), patch('student_pilot.pose_samples.check_sample'), \
                patch('student_pilot.decoupled_v.target_tensors', return_value=tensors):
            self.assertEqual(run.pose_row_check({}, {'pose_sample': {'augment': augment}}, {}), (3., 4.))
            for bad in ({}, {**augment, 'seed': 1.5}, {k: v for k, v in augment.items() if k != 'hue'}):
                with self.assertRaisesRegex(ValueError, 'augmentation settings'):
                    run.pose_row_check({}, {'pose_sample': {'augment': bad}}, {})


if __name__ == '__main__':
    unittest.main()
