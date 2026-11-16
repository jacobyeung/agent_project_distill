"""Portable CPU tests; retain synthetic recordings and receipts under B2_TEST_OUTPUT."""
from collections import Counter
import copy
import io
import json
import os
from pathlib import Path
import random
import tempfile
import tarfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from student_pilot import pose_samples
from student_pilot import recording_pose as rp


def directory():
    root = Path(os.environ.get('B2_TEST_OUTPUT', 'artifacts/recording_pose_tests'))
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='fixture_', dir=root))


def save(root, name, value):
    path = root / name
    rp.write_new(path, rp.payload(value))
    return rp.pin(path)


def fixture(root):
    gate = json.loads(Path('configs/gate_heldout_scenes_v1.json').read_bytes())
    authority = {
        'gate': save(root, 'gate.json', gate),
        'vsti': save(root, 'vsti.json', {'scenes': [['scannet', 'scene0200_00']]}),
        'division': save(root, 'division.json', {'train_scenes': ['arkitscenes/100', 'scannet/scene0200_00',
            'scannet/scene0300_00', 'scannet/scene0400_00', 'scannetppv2/example'],
            'heldout_scenes': ['scannet/scene0400_01']}),
        'admission_policy': save(root, 'policy.json', {'allowed_groups': ['arkitscenes/100',
            'scannet/scene0200', 'scannet/scene0300', 'scannet/scene0400', 'scannetppv2/example'],
            'excluded_groups': ['scannetppv2/example']}), 'extra_benchmarks': []}
    vsi = root / 'scenes.tsv'
    rp.write_new(vsi, ''.join(f'arkitscenes\t{2000 + k}\n' for k in range(288)).encode())
    authority['vsi288'] = rp.pin(vsi)
    count = 1000
    c2w = np.repeat(np.eye(4)[None], count, axis=0)
    angle = np.arange(count) * .001
    c2w[:, 0, 0], c2w[:, 1, 1] = np.cos(angle), np.cos(angle)
    c2w[:, 1, 0], c2w[:, 0, 1] = np.sin(angle), -np.sin(angle)
    c2w[:, :3, 3] = np.stack([angle, angle**2, angle / 3], axis=-1)
    pose_path = root / 'source.npz'
    np.savez(pose_path, c2w=c2w, intrinsics=np.array([[4., 0, 2], [0, 4., 2], [0, 0, 1]]),
             raster_hw=np.array([4, 4]), frame_numbers=np.arange(count), world_up=np.array([0., 1., 0.]))
    source = {'dataset': 'arkitscenes', 'scene': '100', 'total_num_frames': count, 'pose_count': count,
              'coordinate_frame': rp.COORDINATES, 'fps': 30., 'poses': rp.pin(pose_path),
              'video': {'path': str(root / 'unopened.mp4'), 'sha256': 'a' * 64}}
    sources = [source]
    # Excluded source payload paths do not exist and must never be opened.
    for dataset, scene in [('scannet', 'scene0200_00'), ('arkitscenes', '2000'),
                           ('arkitscenes', 'outsider'), ('scannetppv2', 'example'),
                           ('scannet', 'scene0400_00')]:
        sources.append({**source, 'dataset': dataset, 'scene': scene})
    sources.append({**source, 'dataset': 'scannet', 'scene': 'scene0300_00', 'pose_count': 127})
    request = {'schema': 'recording-pose-request-v1', 'authorities': authority,
               'recordings': save(root, 'recordings.json', {'recordings': sources}), 'seed': 17, 'rows_per_scene': 80}
    return request


def staged_fixture(root, plan, plan_pin):
    source = plan['scenes'][0]
    frames = []
    for n in source['pool']:
        output = io.BytesIO()
        Image.new('RGB', (4, 4), (n % 256, n // 256, 0)).save(output, format='PNG')
        raw = output.getvalue()
        sha = rp.digest(raw)
        path = root / sha[:2] / (sha + '.png')
        path.parent.mkdir(exist_ok=True)
        if not path.exists():
            rp.write_new(path, raw)
        frames.append({'frame_number': n, 'path': str(path), 'sha256': sha, 'raster_hw': [4, 4]})
    scene = {'dataset': source['dataset'], 'scene': source['scene'], 'pose_count': source['pose_count'],
             'decoded_frame_count': source['pose_count'], 'video': source['video'], 'frames': frames}
    receipt = {'schema': 'recording-pose-staged-v1', 'plan': plan_pin, 'shard': 0, 'shards': 1, 'scenes': [scene]}
    return receipt, save(root, 'staged.json', receipt)


class SamplingTests(unittest.TestCase):
    def test_probabilities_integer_intervals_and_sizes(self):
        sampler = rp.PoolSampler(list(range(0, 2880, 30)))
        self.assertTrue(sampler.ready())
        for dataset, (p_video, p_fix) in rp.PROBABILITIES.items():
            rng, counts, sizes = random.Random(18), Counter(), Counter()
            for _ in range(10000):
                mode, kind, order = sampler.draw(rng, dataset)
                counts[mode] += 1
                counts[kind] += 1
                sizes[len(order)] += 1
                self.assertEqual(len(set(order)), len(order))
                self.assertTrue(all(type(f) is int and f in sampler.pool for f in order))
                if mode == 'video':
                    gaps = np.diff(order)
                    self.assertTrue(((30 <= gaps) & (gaps <= 100)).all())
                    if kind == 'fixed':
                        self.assertEqual(len(set(gaps)), 1)
            self.assertAlmostEqual(counts['video'] / 10000, p_video, delta=.02)
            self.assertAlmostEqual(counts['fixed'] / counts['video'], p_fix, delta=.025)
            for n in (8, 16, 24, 32):
                self.assertAlmostEqual(sizes[n] / 10000, .25, delta=.025)

    def test_pool_spans_recording_is_bounded_and_has_all_paths(self):
        for count in (211, 451, 691, 930, 931, 966, 8637, 20000):
            pool = rp.make_pool(count, random.Random(count))
            self.assertEqual(len(pool), 96)
            self.assertEqual(pool, sorted(set(pool)))
            self.assertTrue(all(type(f) is int and 0 <= f < count for f in pool))
            self.assertEqual(len({min(15, f * 16 // count) for f in pool}), 16)
            sampler = rp.PoolSampler(pool, rp.sizes_for(count))
            self.assertTrue(sampler.ready())
            for _ in range(20):
                self.assertIn(len(sampler.draw(random.Random(_), 'd3')[2]), rp.sizes_for(count))
            self.assertEqual(pool, rp.make_pool(count, random.Random(count)))
        with self.assertRaisesRegex(ValueError, 'too short'):
            rp.make_pool(210, random.Random(1))
        for pool in ([0., 30.], [True, 30], [0, 0], [30, 0], [-1, 30]):
            with self.subTest(pool=pool), self.assertRaises(ValueError):
                rp.PoolSampler(pool)

    def test_no_nearest_frame_or_mode_fallback(self):
        sampler = rp.PoolSampler([i * 101 for i in range(96)])
        self.assertFalse(sampler.ready())
        with self.assertRaisesRegex(ValueError, 'pool path'):
            sampler.draw(random.Random(3), 'd2')


class BuilderTests(unittest.TestCase):
    def test_real_encoding_schema_audit_and_augmentation(self):
        root = directory()
        request = fixture(root)
        plan = rp.make_plan(request)
        self.assertEqual(len(plan['scenes']), 1)
        self.assertEqual(len(plan['excluded']), 5)
        self.assertEqual(plan['deferred'][0]['reason'], 'sparse_pose_count')
        plan_pin = save(root, 'plan.json', plan)
        receipt, staged_pin = staged_fixture(root, plan, plan_pin)
        audit = rp.build(plan, plan_pin, [staged_pin], root / 'built')
        rows = [json.loads(line) for line in (root / 'built/pose_rows.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 80)
        self.assertEqual(audit['datasets']['d3']['rows'], 80)
        self.assertEqual(audit['scenes'], 1)
        self.assertFalse(audit['depth_labels_built'])
        self.assertEqual(audit['authorities'], request['authorities'])
        self.assertTrue(audit['target_sanity']['finite_translation'])
        self.assertLess(audit['target_sanity']['max_quaternion_norm_error'], 1e-12)
        self.assertLess(audit['target_sanity']['max_gravity_norm_error'], 1e-12)
        self.assertEqual(audit['pool_coverage'][0]['occupied_sixteenths'], 16)
        self.assertEqual(sum(audit['N_histogram'].values()), 80)
        self.assertEqual(len({r['qid'] for r in rows}), 80)
        poses = rp.load_poses(plan['scenes'][0], {})
        for row in rows:
            numbers = row['pose_sample']['recording']['raw_frame_numbers']
            positions = row['pose_sample']['recording']['pool_positions']
            self.assertEqual(numbers, [plan['scenes'][0]['pool'][i] for i in positions])
            self.assertEqual(numbers, row['student_input']['frame_indices'])
            self.assertTrue(all(type(f) is int for f in numbers))
            camera, mask, scale, gravity = pose_samples.encode_sample(
                poses['c2w'], poses['intrinsics'], poses['raster_hw'], numbers, poses['world_up'])
            np.testing.assert_array_equal(row['pose_sample']['camera'], camera)
            np.testing.assert_array_equal(row['pose_sample']['camera_mask'], mask)
            np.testing.assert_array_equal(row['pose_sample']['gravity'], gravity)
            self.assertEqual(row['pose_sample']['trajectory_scale'], scale)
            self.assertEqual({k: v for k, v in row['pose_sample']['augment'].items() if k != 'seed'}, pose_samples.AUGMENT)
            self.assertEqual(pose_samples.check_sample(row)['lm_weight'], 0.)
            self.assertNotIn('depth', row)
        with self.assertRaises(FileExistsError):
            rp.build(plan, plan_pin, [staged_pin], root / 'built')

    def test_authorities_fail_closed_and_apply_before_payload_reads(self):
        root = directory()
        request = fixture(root)
        plan = rp.make_plan(request)
        reasons = {s['scene']: s['reasons'] for s in plan['excluded']}
        self.assertIn('vsti', reasons['scene0200_00'])
        self.assertIn('vsi288', reasons['2000'])
        self.assertIn('outside_frozen_training_division', reasons['outsider'])
        self.assertIn('admission_policy', reasons['example'])
        self.assertIn('division_heldout', reasons['scene0400_00'])
        for excluded in plan['excluded']:
            self.assertEqual(set(excluded['sources']), set(excluded['reasons']))
            self.assertTrue(all(len(s['sha256']) == 64 for pins in excluded['sources'].values() for s in pins))
        for key in request['authorities']:
            broken = copy.deepcopy(request)
            broken['authorities'].pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                rp.make_plan(broken)
        broken = copy.deepcopy(request)
        broken['authorities']['vsti']['path'] = str(root / 'missing.json')
        with self.assertRaises(FileNotFoundError):
            rp.make_plan(broken)
        broken = copy.deepcopy(request)
        broken['authorities']['division']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            rp.make_plan(broken)

    def test_opaque_gate_token_blocks_repeat_scans(self):
        root = directory()
        request = fixture(root)
        gate = json.loads(rp.read_pin(request['authorities']['gate']))
        gate['scenes'][0] = ['d1', rp.token('d1', 'scene0300_01')]
        request['authorities']['gate'] = save(root, 'gate2.json', gate)
        plan = rp.make_plan(request)
        self.assertTrue(any(s['scene'] == 'scene0300_00' and 'gate' in s['reasons'] for s in plan['excluded']))

    def test_missing_extra_authority_and_changed_staging_rejected(self):
        root = directory()
        request = fixture(root)
        policy = json.loads(rp.read_pin(request['authorities']['admission_policy']))
        policy['required_exclusion_lists'] = [{'path': '/missing', 'sha256': '0' * 64}]
        broken = copy.deepcopy(request)
        broken['authorities']['admission_policy'] = save(root, 'policy2.json', policy)
        with self.assertRaisesRegex(ValueError, 'additional'):
            rp.make_plan(broken)
        plan = rp.make_plan(request)
        plan_pin = save(root, 'plan.json', plan)
        receipt, _ = staged_fixture(root, plan, plan_pin)
        for kind in ('count', 'frame', 'hash', 'plan', 'shards'):
            changed = copy.deepcopy(receipt)
            if kind == 'count':
                changed['scenes'][0]['decoded_frame_count'] -= 1
            elif kind == 'frame':
                changed['scenes'][0]['frames'][0]['frame_number'] += 1
            elif kind == 'hash':
                changed['scenes'][0]['frames'][0]['sha256'] = '0' * 64
            elif kind == 'plan':
                changed['plan']['sha256'] = '0' * 64
            else:
                changed['shards'] = 2
            source = save(root, 'changed_' + kind + '.json', changed)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                rp.build(plan, plan_pin, [source], root / ('bad_' + kind))

    def test_npz_indices_are_raw_integer_ordinals(self):
        root = directory()
        request = fixture(root)
        plan = rp.make_plan(request)
        source = plan['scenes'][0]
        with np.load(source['poses']['path'], allow_pickle=False) as data:
            arrays = dict(data)
        for kind, indices in [('float', np.arange(1000, dtype=float)), ('sparse', np.arange(1000) * 2)]:
            path = root / (kind + '.npz')
            np.savez(path, **{**arrays, 'frame_numbers': indices})
            bad = {**source, 'poses': rp.pin(path)}
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                rp.load_poses(bad, {})

    def test_pinned_archive_member_and_missing_authority_recheck(self):
        root = directory()
        request = fixture(root)
        plan = rp.make_plan(request)
        source = plan['scenes'][0]
        raw = Path(source['poses']['path']).read_bytes()
        path = root / 'poses.tar'
        with tarfile.open(path, 'w') as archive:
            member = tarfile.TarInfo('abcd1234.npz')
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
        spec = {**rp.pin(path), 'member': 'abcd1234.npz', 'member_sha256': rp.digest(raw)}
        cache = {}
        try:
            loaded = rp.load_poses({**source, 'poses': spec}, cache)
            self.assertEqual(len(loaded['c2w']), 1000)
            with self.assertRaisesRegex(ValueError, 'member SHA-256'):
                rp.load_poses({**source, 'poses': {**spec, 'member_sha256': '0' * 64}}, cache)
        finally:
            for key, value in cache.items():
                if key[0] == 'archive':
                    value.close()
        plan['authorities']['gate']['path'] = str(root / 'missing_gate.json')
        with self.assertRaises(FileNotFoundError), patch.object(rp, 'decode_pool') as decode:
            rp.stage(plan, {'path': '/unused', 'sha256': '0' * 64}, root / 'frames', 0, 1)
        decode.assert_not_called()

    def test_frozen_depth_loader_accepts_pool_rows_and_preserves_unfrozen_guard(self):
        from student_pilot import compact_label_bank
        from student_pilot.camera_config import CAMBRIAN_P_ROUTING
        root = directory()
        plan = rp.make_plan(fixture(root))
        plan_pin = save(root, 'plan.json', plan)
        receipt, _ = staged_fixture(root, plan, plan_pin)
        source = plan['scenes'][0]
        row = rp.build_row(source, rp.load_poses(source, {}), receipt['scenes'][0],
                           rp.PoolSampler(source['pool']), 0, plan['seed'])
        bank = {'dataset_tokens': np.array(['d3']), 'scene_tokens': np.array([source['scene']]),
                'point_depth_uv': np.zeros((1, 16, 2, 2)), 'frame_indices': np.arange(32)[None]}
        cfg = {'row_routing': CAMBRIAN_P_ROUTING, 'point_depth': {'weight': .1, 'num_points_per_frame': 2},
               'freeze_modules': ['point_depth']}
        with patch.object(compact_label_bank, 'read_bank', return_value=bank):
            entries, audit = compact_label_bank.load_bank_for_rows('/unused.npz', [row], cfg)
            self.assertEqual(entries[0]['camera'], row['pose_sample']['camera'])
            self.assertFalse(np.asarray(entries[0]['point_depth']['mask']).any())
            self.assertEqual(audit['depth_rows'], 0)
            with self.assertRaisesRegex(ValueError, 'differ from'):
                compact_label_bank.load_bank_for_rows('/unused.npz', [row], {**cfg, 'freeze_modules': []})
        absent = {**bank, 'dataset_tokens': np.array(['d1']), 'scene_tokens': np.array(['v_other'])}
        with patch.object(compact_label_bank, 'read_bank', return_value=absent):
            entries, _ = compact_label_bank.load_bank_for_rows('/unused.npz', [row], cfg)
            self.assertEqual(entries[0]['camera'], row['pose_sample']['camera'])
            with self.assertRaisesRegex(ValueError, 'no bank entry'):
                compact_label_bank.load_bank_for_rows('/unused.npz', [row], {**cfg, 'freeze_modules': []})


class StageTests(unittest.TestCase):
    def test_serial_stage_keeps_receipt_and_rejects_invalid_workers(self):
        root = directory()
        plan = rp.make_plan(fixture(root))
        pp = save(root, 'plan.json', plan)
        scene = {'synthetic': True}
        with patch.object(rp, 'decode_pool', return_value=scene) as decoder, \
                patch.object(rp, 'ProcessPoolExecutor', side_effect=AssertionError('serial pool')):
            expected = dict(schema='recording-pose-staged-v1', plan=pp, shard=0, shards=1, scenes=[scene])
            self.assertEqual(rp.payload(rp.stage(plan, pp, root/'frames', 0, 1)), rp.payload(expected))
            decoder.assert_called_once_with(plan['scenes'][0], root/'frames')
            self.assertEqual(rp.stage(plan, pp, root/'empty', 1, 2, workers=8)['scenes'], [])
            for workers in (0, -1, True, 1.5, '2'):
                with self.subTest(workers=workers), self.assertRaisesRegex(ValueError, 'Workers'):
                    rp.stage(plan, pp, root/'invalid', 0, 1, workers=workers)

    def test_decoder_materializes_only_pool_and_checks_full_count(self):
        root = directory()
        video = root / 'synthetic.mp4'
        rp.write_new(video, b'CPU decoder fixture; no media source read')
        source = {'video': rp.pin(video), 'pool': [0, 30], 'pose_count': 31, 'total_num_frames': 31,
                  'dataset': 'd1', 'scene': 'v123'}
        process = unittest.mock.MagicMock()
        process.__enter__.return_value = process
        ppm = b'P6\n2 1\n255\n' + bytes([255, 0, 0, 0, 0, 255])
        process.stdout = io.BytesIO(ppm * 2)
        process.wait.return_value = 0
        with patch.object(rp.subprocess, 'run') as probe, patch.object(rp.subprocess, 'Popen', return_value=process) as decode:
            probe.return_value.stdout = b'{"streams":[{"nb_read_frames":"31"}]}'
            receipt = rp.decode_pool(source, root / 'frames')
            self.assertEqual([f['frame_number'] for f in receipt['frames']], [0, 30])
            self.assertEqual(receipt['decoded_frame_count'], 31)
            command = decode.call_args.args[0]
            self.assertIn('select=eq(n\\,0)+eq(n\\,30)', command)
            self.assertNotIn('-r', command)
            self.assertNotIn('-ss', command)
            for frame in receipt['frames']:
                self.assertEqual(rp.file_sha(frame['path']), frame['sha256'])
                self.assertEqual(Path(frame['path']).stem, frame['sha256'])
                with Image.open(frame['path']) as image:
                    self.assertEqual(image.mode, 'RGB')
            probe.return_value.stdout = b'{"streams":[{"nb_read_frames":"32"}]}'
            with self.assertRaisesRegex(ValueError, 'pose count'):
                rp.decode_pool(source, root / 'rejected')
            self.assertEqual(decode.call_count, 1)

    def test_cli_plan_jobs_and_opaque_job_resources(self):
        root = directory()
        request = fixture(root)
        source = save(root, 'request.json', request)
        plan_path = root / 'plan.json'
        rp.main(['plan', '--request', source['path'], '--output', str(plan_path)])
        plan_pin = rp.pin(plan_path)
        # Deployments and input paths supplied to AWS must themselves be opaque.
        opaque = {'path': '/store/abcd1234/abcd.json', 'sha256': plan_pin['sha256']}
        spec, script = rp.job_files(opaque, '/store/abcd1234/f', '/store/abcd1234/o', '/store/abcd1234/c', 7)
        self.assertRegex(spec['job_name'], r'^a15_cot_ap[0-9a-f]+$')
        self.assertEqual(spec['partition'], 'cpu')
        self.assertEqual(spec['qos'], 'cpu-normal')
        self.assertEqual(spec['time'], '01:30:00')
        self.assertEqual(spec['array'], '0-6%4')
        self.assertEqual(spec['gpus'], 0)
        self.assertNotIn('sbatch ', script)
        self.assertIn('CUDA_VISIBLE_DEVICES=""', script)
        self.assertIn('--plan-sha256 ' + plan_pin['sha256'], script)
        rp.write_new(root / (spec['job_name'] + '.sh'), script.encode())
        rp.write_new(root / (spec['job_name'] + '.json'), rp.payload(spec))


if __name__ == '__main__':
    unittest.main()
