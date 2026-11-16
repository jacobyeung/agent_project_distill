"""Routing stream: exact derivgen rendering, fixed-layer conventions, masks, splice, schedule."""
import json
import math
import os
import unittest
from pathlib import Path

import numpy as np
import torch

from student_pilot import carrier_c1_routing as R
from student_pilot.camera_targets import quaternion_xyzw

POOL = Path(os.environ.get('P3_ROUTING_POOL', '/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl'))
PROCESSOR = Path(os.environ.get('P3_QWEN35_PROCESSOR', '/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor'))


def gt_level_basis(rotation):
    """derivgen geometry.level_basis: world z up."""
    down = np.array([0., 0., -1.])
    forward = rotation[:, 2].copy()
    forward[2] = 0
    forward /= np.linalg.norm(forward)
    return np.column_stack((np.cross(down, forward), down, forward))


def gt_pose(c2w, k):
    """derivgen GTScene.pose with origin frame 1."""
    basis, origin = gt_level_basis(c2w[0][:3, :3]), c2w[0][:3, 3]
    flip = np.diag([1., -1., 1.])
    R_, t = c2w[k - 1][:3, :3], c2w[k - 1][:3, 3]
    level = flip @ basis.T @ gt_level_basis(R_)
    return dict(camera_R_L1=flip @ basis.T @ R_, camera_t_L1=flip @ basis.T @ (t - origin), level_R_L1=level,
                yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))


def rotation(yaw, pitch, roll):
    cy, sy, cp, sp, cr, sr = (f(a) for a in (yaw, pitch, roll) for f in (math.cos, math.sin))
    # Camera looking along world +y (OpenCV: x right, y down, z forward), then yaw/pitch/roll.
    base = np.array([[1., 0., 0.], [0., 0., 1.], [0., -1., 0.]]).T
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    rc = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return rz @ base @ rx @ rc


class FixedLayerConventions(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(17)
        self.c2w = []
        for k in range(32):
            pose = np.eye(4)
            pose[:3, :3] = rotation(rng.uniform(-3, 3), rng.uniform(-.3, .3), rng.uniform(-.1, .1))
            pose[:3, 3] = rng.uniform(-2, 2, 3) + [0, 0, 1.4]
            self.c2w.append(pose)
        self.depth = rng.uniform(.8, 4., 32)
        self.fov = np.array([math.radians(45.), math.radians(58.)])
        pose9 = np.zeros((32, 9))
        for k in range(32):
            relative = np.linalg.inv(self.c2w[k]) @ self.c2w[0]
            pose9[k, :3], pose9[k, 3:7], pose9[k, 7:9] = relative[:3, 3], quaternion_xyzw(relative[:3, :3]), self.fov
        up = self.c2w[0][:3, :3].T @ np.array([0., 0., 1.])
        self.own = R.OwnGeometry(pose9, up, lambda k, uv: np.full(len(uv), self.depth[k - 1]))

    def test_pose_move_turn_and_click_match_gt_layer(self):
        for k in (1, 2, 7, 18, 32):
            expected, actual = gt_pose(self.c2w, k), self.own.pose(k)
            for key in ('camera_R_L1', 'camera_t_L1', 'level_R_L1'):
                np.testing.assert_allclose(actual[key], expected[key], atol=1e-6)
            self.assertEqual(actual['yaw_degree'], expected['yaw_degree'])
        for i, j in ((2, 8), (18, 8), (31, 4)):
            pi, pj = gt_pose(self.c2w, i), gt_pose(self.c2w, j)
            local = pi['level_R_L1'].T @ (pj['camera_t_L1'] - pi['camera_t_L1'])
            dist = float(np.linalg.norm(local))
            local[1] *= -1
            self.assertEqual(self.own.move_text(i, j),
                             f'dx = {R.s2(local[0])} m, dy = {R.s2(local[1])} m, dz = {R.s2(local[2])} m, distance = {R.f2(dist)} m')
            a, b = (gt_pose(self.c2w, k)['level_R_L1'][[0, 2], 2] for k in (i, j))
            turn = R.wrap(round(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0], float(a @ b)))))
            self.assertEqual(self.own.turn_text(i, j), f'turn = {turn:+d} deg')
        for k, uv in ((2, [767, 848]), (14, [148, 456]), (30, [500, 120])):
            d = self.depth[k - 1]
            pc = np.array([(uv[0]/500-1)*math.tan(self.fov[1]/2), (uv[1]/500-1)*math.tan(self.fov[0]/2), 1.]) * d
            p = gt_pose(self.c2w, k)
            f1 = p['camera_R_L1'] @ pc + p['camera_t_L1']
            cam, own_f1, spread = self.own.click(k, uv)
            np.testing.assert_allclose(cam, pc * [1, -1, 1], atol=.006)
            np.testing.assert_allclose(own_f1, f1, atol=.006)
            self.assertEqual(spread, 0.)
            # Public camera y is up: a click below the image centre has negative y.
            self.assertEqual(cam[1] < 0, uv[1] > 500)

    def test_invalid_head_outputs_refuse(self):
        bad = self.own.p.copy()
        bad[3, 7] = 0.
        with self.assertRaises(R.RenderError):
            R.OwnGeometry(bad, [0., -1., 0.], lambda k, uv: np.ones(len(uv))).click(4, [500, 500])
        with self.assertRaisesRegex(R.RenderError, 'gravity'):
            R.OwnGeometry(self.own.p, None, lambda k, uv: np.ones(len(uv)))


@unittest.skipUnless(POOL.exists(), 'derivgen review pool not on this host')
class DerivgenRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in POOL.open()]

    def test_every_row_renders_and_replays_byte_identically(self):
        for row in self.rows:
            target, spans = R.check_row(row)
            replay, replay_spans, _ = R.rerender(row, R.RecordedGeometry(row))
            self.assertEqual(replay, target, row['qid'])
            self.assertEqual([(s['start'], s['end']) for s in replay_spans], [(s['start'], s['end']) for s in spans])

    def test_own_rerender_changes_only_tool_spans(self):
        own = R.OwnGeometry(np.tile([0., 0., 0., 0., 0., 0., 1., .8, 1.], (32, 1)), None,
                            lambda k, uv: np.full(len(uv), 1.5), require_up=False)
        done = 0
        for row in self.rows:
            try:
                target, spans, _ = R.rerender(row, own)
            except R.RenderError:
                continue
            gt, gt_spans = R.render(row['events'], row['answer'])
            strip = lambda text, ss: ''.join(text[a['end']:b['start']] for a, b in zip([{'end': 0}] + ss, ss + [{'start': len(text)}]))
            self.assertEqual(strip(target, spans), strip(gt, gt_spans), row['qid'])
            done += 1
        self.assertGreater(done, 100)

    @unittest.skipUnless(PROCESSOR.exists(), 'Qwen3.5 processor fixture absent')
    def test_masks_cover_exactly_the_tool_outputs(self):
        from student_pilot.decoupled_v_run import processor_for
        processor = processor_for(PROCESSOR)
        for row in self.rows[::25]:
            target, spans = R.render(row['events'], row['answer'])
            c1 = {'student_input': {'question': row['question'], 'options': row.get('options') or []}, 'routing': row}
            ids, train, offsets = R.suffix_tokens(processor, c1, target, spans)
            self.assertTrue(train[0])
            self.assertEqual(len(ids), len(train))
            masked = [i for i, keep in zip(ids, train) if not keep]
            self.assertEqual(masked.count(processor.tokenizer.convert_tokens_to_ids('<tool_response>')), len(spans))


class HybridAndSegments(unittest.TestCase):
    @unittest.skipUnless(POOL.exists(), 'derivgen review pool not on this host')
    def test_value_source_per_head(self):
        rows = [json.loads(line) for line in POOL.open()]
        depth_only = next(r for r in rows if r['question_type'] == 'absolute_count')
        with_pose = next(r for r in rows if r['question_type'] == 'absolute_distance_object')
        pose9 = torch.tensor(np.tile([0., 0., 0., 0., 0., 0., 1., .8, 1.], (1, 32, 1)))
        queries = R.depth_queries(depth_only)
        uv, index = R.query_tensor(queries)
        readout = dict(pose=pose9, gravity=torch.tensor([[0., -1., 0.]]), depth=torch.full(tuple(uv.shape[:2]), 2.))
        self.assertEqual(R.row_geometry(with_pose, readout, [], [], True, False)[1], 'pose_gate_closed')
        self.assertEqual(R.row_geometry(depth_only, readout, queries, index, True, False)[1], 'gt_pose_missing')
        gt = {**depth_only, 'gt_pose9': pose9[0].tolist(), 'gt_up': [0., -1., 0.]}
        geometry, source = R.row_geometry(gt, readout, queries, index, True, False)
        self.assertEqual(source, 'own_depth_gt_pose')
        geometry, source = R.row_geometry(depth_only, readout, queries, index, False, True)
        self.assertEqual(source, 'own_pose_gt_depth')
        target, _, _ = R.rerender(depth_only, geometry)
        first = next(e for e in depth_only['events'] if e['kind'] == 'tool_response')['points'][0]
        self.assertIn(f"{first['label']}: cam{first['actual_frame']} {R.vec(first['camera'])} m", target)

    @unittest.skipUnless(POOL.exists() and PROCESSOR.exists(), 'pool or processor fixture absent')
    def test_segments_tag_openers_arguments_and_answer(self):
        from student_pilot.decoupled_v_run import processor_for
        processor = processor_for(PROCESSOR)
        tokens = R.add_routing_tokens(processor)
        row = json.loads(next(iter(POOL.open())))
        target, spans, segments = R.render_full(row['events'], row['answer'])
        c1 = {'student_input': {'question': row['question'], 'options': []}, 'routing': row}
        ids, train, offsets = R.suffix_tokens(processor, c1, target, spans)
        tags = R.segment_ids(offsets, segments)
        opener = tokens['ids']['<depth_at']
        self.assertTrue(all(R.SEGMENTS[t] == 'opener' for i, t in zip(ids, tags) if i == opener))
        self.assertGreater(sum(i == opener for i in ids), 0)
        self.assertTrue(all(R.SEGMENTS[t] == 'tool' for t, keep in zip(tags, train) if not keep))
        self.assertEqual(R.SEGMENTS[tags[-1]], 'answer')
        batch = dict(input_ids=torch.tensor([[1, 2] + ids]), labels=torch.tensor([[-100, -100] + ids]))
        own, _ = R.finish({k: v.clone() for k, v in batch.items()}, ids, train, c1, target, spans, 'own', offsets)
        cut = spans[0]['end'] - len(R.THINK)
        trained = [a < cut for (a, _), lab in zip(offsets, own['labels'][0, 2:].tolist()) if lab != -100]
        self.assertTrue(all(trained) and trained)


class SpliceAndSchedule(unittest.TestCase):
    def test_splice_preserves_prefix_and_relabels_suffix(self):
        ids = torch.tensor([[5, 6, 7, 8, 9, 10, 0, 0]])
        batch = dict(input_ids=ids, attention_mask=(ids != 0).long(), mm_token_type_ids=torch.zeros_like(ids),
                     labels=torch.tensor([[-100, -100, -100, 8, 9, 10, -100, -100]]), aux_suffix_start=torch.tensor([3]),
                     aux_video_prefix_end=torch.tensor([1]))
        out = R.splice(batch, [11, 12, 13, 14, 15, 16], 0)
        self.assertEqual(out['input_ids'][0, :3].tolist(), [5, 6, 7])
        self.assertEqual(out['input_ids'].shape[1] % 8, 0)
        self.assertEqual(out['labels'][0, 3:9].tolist(), [11, 12, 13, 14, 15, 16])
        self.assertEqual(int(out['attention_mask'].sum()), 9)
        prefix = R.prefix_batch(batch)
        self.assertEqual(prefix['input_ids'].tolist(), [[5, 6]])
        self.assertNotIn('labels', prefix)

    def test_gates_open_per_head_and_force_for_the_test_run(self):
        schedule = dict(seed=17, max_own_probability=.5, pose_open_deg=45., pose_full_deg=25., fov_open_deg=2.,
                        depth_open_absrel=.25, ema_steps=100, force_from_step=None,
                        exposure_from_step=None, exposure_probability=0.)
        gates = R.Gates(schedule, stage1_depth=True)
        self.assertEqual(gates.state(1)['p_depth'], 0.)
        gates.update(dict(rotation_deg=80., fov_deg=1.5, depth_absrel=None))
        self.assertEqual(gates.state(2)['p_depth'], 0.)
        gates.update(dict(depth_absrel=.16))
        state = gates.state(2)
        self.assertEqual((state['p_depth'], state['p_pose']), (.5, 0.))
        gates.ema['rotation_deg'] = 35.
        self.assertAlmostEqual(gates.state(3)['p_pose'], .25)
        gates.ema['rotation_deg'] = 20.
        self.assertEqual(gates.state(3)['p_pose'], .5)
        unfit = R.Gates(schedule, stage1_depth=False, ema=dict(fov_deg=.1, depth_absrel=.4))
        self.assertEqual(unfit.state(5)['p_depth'], 0.)
        forced = R.Gates({**schedule, 'force_from_step': 100}, stage1_depth=False)
        self.assertEqual(forced.state(99)['p_pose'], 0.)
        self.assertEqual((forced.state(100)['p_depth'], forced.state(100)['p_pose']), (.5, .5))
        draws = [forced.decide(s, m) for s in range(100, 400) for m in (4, 5)]
        self.assertEqual(draws, [forced.decide(s, m) for s in range(100, 400) for m in (4, 5)])
        self.assertTrue(.4 < sum(d for d, _ in draws) / len(draws) < .6)
        exposed = R.Gates({**schedule, 'exposure_from_step': 300, 'exposure_probability': .25}, stage1_depth=False,
                          ema=dict(rotation_deg=60.))
        self.assertEqual((exposed.state(299)['p_pose'], exposed.state(300)['p_pose'], exposed.state(300)['p_depth']),
                         (0., .25, .25))
        with self.assertRaises(ValueError):
            R.validate_schedule({**schedule, 'pose_full_deg': 50.})

    def test_query_tensor_indexes_each_click_stencil(self):
        queries = [(2, [767., 848.]), (2, [100., 200.]), (14, [148., 456.])]
        uv, index = R.query_tensor(queries)
        self.assertEqual(tuple(uv.shape), (32, 50, 2))
        self.assertEqual(index, [(2, 0), (2, 25), (14, 0)])
        self.assertEqual(uv[1, 25 + 12].tolist(), [100., 200.])
        depth = torch.arange(32 * 50, dtype=torch.float64).reshape(32, 50) + 1
        geometry = R.own_geometry(dict(pose=torch.tensor(np.tile([0, 0, 0, 0, 0, 0, 1, .8, 1.], (1, 32, 1))),
                                       depth=depth), queries, index, require_up=False)
        self.assertEqual(geometry.depth(2, np.clip(np.array([100., 200.])[None] + R.STENCIL, 0, 999.9)).tolist(),
                         depth[1, 25:50].tolist())


@unittest.skipUnless(POOL.exists() and PROCESSOR.exists(), 'pool or processor fixture absent')
class StreamBuild(unittest.TestCase):
    def test_builder_writes_c1_rows_with_relocated_frames_and_refusals(self):
        import sqlite3
        import tempfile
        from student_pilot.p3_provenance import file_pin
        rows = [json.loads(line) for line in POOL.open()][:40]
        root = Path(tempfile.mkdtemp(dir=os.environ.get('TMPDIR', '/tmp')))
        manifests = {}
        for row in rows:
            pin = row['provenance']['rgb_manifest']
            if pin['sha256'] in manifests:
                continue
            body = dict(frames=[dict(path=f'/old/{i}.jpg', sha256='0'*64, source_index=k)
                                for i, k in enumerate(row['provenance']['frame_indices'])],
                        fps=24.0, total_num_frames=5000)
            path = root / f'{len(manifests)}.json'
            path.write_text(json.dumps(body))
            manifests[pin['sha256']] = str(path)
        # Manifest pins in rows name the producer's bytes; rebind them to the synthetic copies.
        for row in rows:
            old = row['provenance']['rgb_manifest']['sha256']
            row['provenance']['rgb_manifest'] = file_pin(Path(manifests[old]))
        index = dict(manifests={file_pin(Path(p))['sha256']: p for p in manifests.values()}, path_map={'/old/': '/new/'})
        (root / 'index.json').write_text(json.dumps(index))
        source = root / 'rows.jsonl'
        source.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        scenes = sorted({r['provenance']['alias'] for r in rows})
        for r in rows:
            self.assertEqual(R.alias_of(r['provenance']['canonical']), r['provenance']['alias'])
        division = dict(schema='diagnostic-whole-scene-division-v1', training_only=True,
                        train_scenes=scenes[1:], heldout_scenes=[])
        (root / 'division.json').write_text(json.dumps(division))
        receipt = R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                         root / 'out', PROCESSOR, max_suffix_tokens=4000, verify_frames=False,
                                         allow_paired_anchor=True)
        held = sum(r['provenance']['alias'] == scenes[0] for r in rows)
        group = next(r['provenance']['physical_group'] for r in rows if r['provenance']['alias'] == scenes[-1])
        (root / 'bench.json').write_text(json.dumps({'schema': 'benchmark_scene_exclusions_v1', 'scenes': [],
                                                     'physical_groups': [group]}))
        bench = R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                       root / 'bench', PROCESSOR, max_suffix_tokens=4000, verify_frames=False,
                                       allow_paired_anchor=True, exclusions=file_pin(root / 'bench.json'))
        self.assertEqual(bench['refused'].get('benchmark_scene'),
                         sum(r['provenance']['physical_group'] == group for r in rows))
        shipped = R.shippable_exclusions(root / 'bench.json', root / 'bench_alias.json')
        alias = R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                       root / 'bench_alias', PROCESSOR, max_suffix_tokens=4000, verify_frames=False,
                                       allow_paired_anchor=True, exclusions=file_pin(root / 'bench_alias.json'))
        self.assertEqual(alias['refused'].get('benchmark_scene'), bench['refused'].get('benchmark_scene'))
        self.assertNotIn('scannet', (root / 'bench_alias.json').read_text())
        counted = R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                         root / 'bench_report', PROCESSOR, max_suffix_tokens=4000, verify_frames=False,
                                         allow_paired_anchor=True, report_exclusions=file_pin(root / 'bench_alias.json'))
        self.assertNotIn('benchmark_scene', counted['refused'])
        # Overlap counts admitted rows only; benchmark refusals happen before the policy check.
        self.assertLessEqual(sum(counted['reported_overlap_rows'].values()), bench['refused'].get('benchmark_scene'))
        self.assertEqual(receipt['refused'].get('scene_outside_training_division', 0), held)
        self.assertEqual(receipt['policy_version'], R.POLICY_VERSION)
        self.assertTrue(all(k.split(':')[1] == 'route' for k in receipt['types']))
        last = next(r['provenance']['canonical'] for r in rows if r['provenance']['alias'] == scenes[-1])
        direct = [dict(qid=f'd{i}', question_type=t, canonical=last, answer='B',
                       target=R.THINK + '\n</think>\n\nB',
                       student_input=dict(frames=[dict(path=f'/x/{k}.jpg', sha256='0'*64) for k in range(32)],
                                          frame_indices=list(range(0, 64, 2)), fps=30., total_num_frames=900,
                                          question='Which is longer?', options=['A. sofa', 'B. table']))
                  for i, t in enumerate(('relative_size_object', 'camera_displacement'))]
        (root / 'direct.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in direct))
        mixed = R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                       root / 'mixed', PROCESSOR, max_suffix_tokens=4000, verify_frames=False,
                                       allow_paired_anchor=True, direct_source=file_pin(root / 'direct.jsonl'))
        self.assertEqual(mixed['types'].get('relative_size_object:direct'), 1)
        self.assertEqual(mixed['refused'].get('direct:direct_row_for_route_type'), 1)
        with sqlite3.connect(root / 'mixed' / 'rows.sqlite') as conn:
            last = json.loads(conn.execute('SELECT row FROM rows ORDER BY i DESC LIMIT 1').fetchone()[0])
        self.assertEqual(R.render(last['routing']['events'], last['routing']['answer'])[0], last['target'])
        self.assertEqual(last['student_input']['timestamps'][1], 2 / 30.)
        with self.assertRaisesRegex(ValueError, 'Empty routing stream'):
            # Pool v1 is paired_anchor; production builds admit only per_frame route rows.
            R.build_routing_stream(file_pin(source), file_pin(root / 'index.json'), file_pin(root / 'division.json'),
                                   root / 'strict', PROCESSOR, max_suffix_tokens=4000, verify_frames=False)
        self.assertEqual(receipt['count'] + sum(receipt['refused'].values()), len(rows))
        with sqlite3.connect(root / 'out' / 'rows.sqlite') as conn:
            first = json.loads(conn.execute('SELECT row FROM rows WHERE i=0').fetchone()[0])
        self.assertTrue(first['student_input']['frames'][0]['path'].startswith('/new/'))
        self.assertEqual(first['student_input']['timestamps'][3], first['student_input']['frame_indices'][3] / 24.0)
        self.assertEqual(R.render(first['routing']['events'], first['routing']['answer'])[0], first['target'])


if __name__ == '__main__':
    unittest.main()
