"""Sparse posed-frame opt-in; production media and GPUs are never opened."""
import copy
import io
import json
import random
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from student_pilot import recording_pose as rp
from tests.test_recording_pose import directory, fixture, save, staged_fixture


def sparse_fixture():
    root = directory()
    request = fixture(root)
    source = json.loads(rp.read_pin(request['recordings']))['recordings'][0]
    numbers = list(range(0, 1000, 3))
    with np.load(source['poses']['path']) as data:
        arrays = {key: data[key] for key in data.files}
    arrays['c2w'] = arrays['c2w'][numbers]
    arrays['frame_numbers'] = np.array(numbers)
    path = root / 'sparse.npz'
    np.savez(path, **arrays)
    source.update(sparse_poses=True, frame_numbers=numbers, pose_count=len(numbers), poses=rp.pin(path))
    request['recordings'] = save(root, 'sparse_index.json', {'recordings': [source]})
    return root, request, source


class SparseTests(unittest.TestCase):
    def test_pyav_sparse_decode_counts_raw_frames_and_keeps_only_posed_pool(self):
        import av
        root, _, source = sparse_fixture()
        video = root / 'synthetic.mp4'
        video.write_bytes(b'Synthetic PyAV fixture')
        source.update(video=rp.pin(video), pool=[0, 30, 999], dataset='d3')
        container = MagicMock()
        container.__enter__.return_value = container
        def frames(count):
            return (av.VideoFrame.from_ndarray(np.full((4, 4, 3), n % 256, dtype=np.uint8), format='rgb24')
                    for n in range(count))
        container.decode.side_effect = lambda stream: frames(1000)
        with patch.object(av, 'open', return_value=container), patch.object(rp.subprocess, 'run') as ffprobe:
            receipt = rp.decode_pool(source, root / 'pyav_frames')
            self.assertEqual(receipt['decoded_frame_count'], 1000)
            self.assertEqual(receipt['pose_count'], 334)
            self.assertEqual([f['frame_number'] for f in receipt['frames']], [0, 30, 999])
            ffprobe.assert_not_called()
            container.decode.side_effect = lambda stream: frames(999)
            with self.assertRaisesRegex(ValueError, 'Decoded frame count'):
                rp.decode_pool(source, root / 'short_pyav_frames')
            source['pool'] = [1]
            with self.assertRaisesRegex(ValueError, 'unposed'):
                rp.decode_pool(source, root / 'unposed_pyav_frames')

    def test_opt_in_and_ordinal_validation(self):
        root, request, source = sparse_fixture()
        plan = rp.make_plan(request)
        rp.validate_plan(plan)
        self.assertTrue(set(plan['scenes'][0]['pool']) <= set(source['frame_numbers']))
        off = {**source, 'sparse_poses': False}
        request['recordings'] = save(root, 'no_opt_in.json', {'recordings': [off]})
        self.assertEqual(rp.make_plan(request)['deferred'][0]['reason'], 'sparse_pose_count')
        for numbers in ([0, 0], [3, 0], [-1, 3], [0, 3.0], [0, 1000], [0, 3]):
            with self.subTest(numbers=numbers), self.assertRaises(ValueError):
                rp.sparse_frames({**source, 'frame_numbers': numbers})
        corrupt = copy.deepcopy(plan)
        corrupt['scenes'][0]['pool'][0] = 1
        with self.assertRaisesRegex(ValueError, 'unposed'):
            rp.validate_plan(corrupt)
        wrong = {**source, 'frame_numbers': [f + 1 for f in source['frame_numbers'][:-1]] + [999]}
        with self.assertRaises(ValueError):
            rp.load_poses(wrong, {})

    def test_nearest_targets_bounds_and_probabilities_on_irregular_poses(self):
        numbers = sorted({round(k * 3.03) for k in range(1000)})
        numbers = [f for i, f in enumerate(numbers) if i % 23 != 10]
        pool, sizes = rp.make_sparse_pool(numbers, random.Random(17), 96)
        sampler = rp.SparsePoolSampler(pool, sizes)
        self.assertTrue(sampler.ready())
        rng, video, fixed = random.Random(91), 0, 0
        for _ in range(3000):
            mode, kind, order = sampler.draw(rng, 'd3')
            self.assertTrue(set(order) <= set(numbers))
            self.assertEqual(len(set(order)), len(order))
            if mode != 'video':
                continue
            video += 1
            fixed += kind == 'fixed'
            self.assertTrue(all(30 <= b - a <= 100 for a, b in zip(order, order[1:])))
            for i, (previous, actual, target) in enumerate(zip(order, order[1:], sampler.target_frame_numbers[1:]), 1):
                choices = [f for f in sampler.next[previous] if sampler.depth[f] >= len(order) - i]
                self.assertEqual(actual, min(choices, key=lambda f: (abs(f - target), f)))
        self.assertAlmostEqual(video / 3000, .8, delta=.035)
        self.assertAlmostEqual(fixed / video, .5, delta=.035)
        with self.assertRaisesRegex(ValueError, 'cannot support'):
            rp.SparsePoolSampler(list(range(0, 1200, 101)))

    def test_sparse_build_maps_raw_ordinals_to_pose_rows(self):
        root, request, source = sparse_fixture()
        plan = rp.make_plan(request)
        source = plan['scenes'][0]
        pin = save(root, 'sparse_plan.json', plan)
        receipt, _ = staged_fixture(root, plan, pin)
        receipt['scenes'][0]['decoded_frame_count'] = source['total_num_frames']
        receipt_pin = save(root, 'sparse_receipt.json', receipt)
        audit = rp.build(plan, pin, [receipt_pin], root / 'sparse_built')
        self.assertEqual(audit['rows'], 80)
        rows = [json.loads(line) for line in (root / 'sparse_built/pose_rows.jsonl').read_text().splitlines()]
        poses = rp.load_poses(source, {})
        staged = receipt['scenes'][0]
        for i, row in enumerate(rows):
            order = row['student_input']['frame_indices']
            record = row['pose_sample']['recording']
            self.assertTrue(set(order) <= set(source['frame_numbers']))
            self.assertEqual(record['effective_intervals'], [b - a for a, b in zip(order, order[1:])])
            # The existing encoder sees pose-row positions; RGB metadata retains raw ordinals.
            dense_source = {k: v for k, v in source.items() if k not in ('sparse_poses', 'frame_numbers')}
            indices = [source['frame_numbers'].index(f) for f in order]
            class Draw:
                def draw(self, rng, dataset):
                    # Match the RNG state consumed by the sparse sampler before augmentation.
                    rp.sampler_for(source, rp.sampling_settings({}), 17).draw(rng, dataset)
                    return row['pose_sample']['mode'], record['interval_mode'], indices
            dense_source['pool'] = [source['frame_numbers'].index(f) for f in source['pool']]
            dense_staged = {'frames': [{**f, 'frame_number': source['frame_numbers'].index(f['frame_number'])}
                                       for f in staged['frames']]}
            expected = rp.build_row(dense_source, poses, dense_staged, Draw(), i, 17)
            self.assertEqual(row['pose_sample']['camera'], expected['pose_sample']['camera'])
            self.assertEqual(row['pose_sample']['gravity'], expected['pose_sample']['gravity'])
        broken = copy.deepcopy(receipt)
        broken['scenes'][0]['decoded_frame_count'] -= 1
        broken_pin = save(root, 'bad_sparse_receipt.json', broken)
        with self.assertRaisesRegex(ValueError, 'Staging count'):
            rp.build(plan, pin, [broken_pin], root / 'bad_sparse_built')

    def test_full_pose_rows_remain_byte_identical(self):
        root = directory()
        plan = rp.make_plan(fixture(root))
        source = plan['scenes'][0]
        poses = rp.load_poses(source, {})
        staged = {'frames': [{'frame_number': f, 'path': f'/fixture/{f}.png', 'sha256': str(f).zfill(64)}
                             for f in source['pool']]}
        sampler = rp.sampler_for(source, rp.sampling_settings({}), 17)
        rows = [rp.build_row(source, poses, staged, sampler, i, 17) for i in range(80)]
        # Captured before the sparse change from source SHA 5fb8806a3ce10a1b... .
        self.assertEqual(rp.digest(rp.payload(rows)), 'a16c0e5ce95c0ecd94880d27a7cb70122a8593f949fb391537fb7ff3cfe8daf6')


if __name__ == '__main__':
    unittest.main()
