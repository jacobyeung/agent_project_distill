"""Real CPU media checks with no external decoder, installs or GPU access."""
import copy
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import av
import numpy as np
from PIL import Image

from student_pilot import a1_pipeline as a, recording_pose as rp
from tests.test_recording_pose import fixture, save


class DecoderTests(unittest.TestCase):
    def directory(self):
        return Path(tempfile.mkdtemp(prefix='decoder_', dir=os.environ['B2_TEST_OUTPUT']))

    def video(self, root, count):
        path = root / '017af04b.mp4'
        with av.open(str(path), 'w') as container:
            stream = container.add_stream('libx264rgb', rate=30)
            stream.width = stream.height = 16
            stream.pix_fmt = 'rgb24'
            stream.options = {'crf': '0', 'preset': 'ultrafast'}
            stream.thread_count = 1
            for number in range(count):
                rgb = np.full((16, 16, 3), [number % 256, number // 256, 23], dtype=np.uint8)
                for packet in stream.encode(av.VideoFrame.from_ndarray(rgb, format='rgb24')):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        return rp.pin(path)

    def shard_plan(self, root):
        request = fixture(root)
        request.update(variant='all_frames32', pool_size=96)
        for key, field in (('division', 'train_scenes'), ('admission_policy', 'allowed_groups')):
            authority = json.loads(rp.read_pin(request['authorities'][key]))
            authority[field] += ['arkitscenes/' + str(n) for n in range(101, 104)]
            request['authorities'][key] = save(root, key + '_multi.json', authority)
        source = json.loads(rp.read_pin(request['recordings']))['recordings'][0]
        video = self.video(root, 1000)
        sources = [dict(source, scene=str(n), video=video) for n in range(100, 104)]
        sources[2].update(sparse_poses=True, frame_numbers=list(range(0, 1000, 2)), pose_count=500)
        request['recordings'] = save(root, 'multi.json', {'recordings': sources})
        plan = rp.make_plan(request)
        return plan, save(root, 'multi_plan.json', plan)

    def test_parallel_stage_matches_serial_receipt_and_png_bytes(self):
        root = self.directory()
        plan, pp = self.shard_plan(root)
        with patch.object(rp, 'ProcessPoolExecutor', wraps=rp.ProcessPoolExecutor) as pool:
            parallel = rp.stage(plan, pp, root/'parallel', 0, 2, use_pyav=True, workers=16)
        self.assertEqual(pool.call_args.kwargs['max_workers'], 2)
        self.assertEqual([s['scene'] for s in parallel['scenes']], [s['scene'] for s in plan['scenes'][::2]])
        serial = rp.stage(plan, pp, root/'serial', 0, 2, use_pyav=True)
        normalized = copy.deepcopy(parallel)
        for actual, expected in zip(normalized['scenes'], serial['scenes']):
            for got, want in zip(actual['frames'], expected['frames']):
                self.assertEqual(Path(got['path']).read_bytes(), Path(want['path']).read_bytes())
                got['path'] = want['path']
        self.assertEqual(rp.payload(normalized), rp.payload(serial))
        self.assertEqual(rp.payload(parallel), rp.payload(rp.stage(plan, pp, root/'parallel', 0, 2,
                                                                use_pyav=True, workers=1)))

    def test_frames_allocation_workers_and_failed_scene_publish_no_receipt(self):
        root = self.directory()
        plan, pp = self.shard_plan(root)
        spec = dict(operation='frames', plan=pp, root=str(root/'frames'), shards=2,
                    output=str(root/'staged.json'), receipt=str(root/'receipt.json'))
        with patch.dict(os.environ, SLURM_JOB_ID='1', SLURMD_NODENAME='cpu-0001', SLURM_ARRAY_TASK_ID='0'):
            with patch.object(a.os, 'sched_getaffinity', return_value={10, 11, 12, 13}):
                result = a.run(spec)
            self.assertEqual(result['details']['workers'], 2)
            self.assertEqual(result['details']['scenes'], 2)
            with patch.object(a.os, 'sched_getaffinity', return_value={10}):
                single = a.run({**spec, 'output': str(root/'single.json'), 'receipt': str(root/'single_receipt.json')})
            self.assertEqual(single['details']['workers'], 1)
            self.assertEqual(Path(spec['output']).read_bytes(), (root/'single.json').read_bytes())
            plan['scenes'][2]['video'] = {**plan['scenes'][2]['video'], 'sha256': '0'*64}
            bad = {**spec, 'plan': save(root, 'bad_plan.json', plan),
                   'output': str(root/'bad_staged.json'), 'receipt': str(root/'bad_receipt.json')}
            with patch.object(a.os, 'sched_getaffinity', return_value={10, 11}), \
                    self.assertRaisesRegex(ValueError, 'Video source SHA-256 mismatch'):
                a.run(bad)
        self.assertFalse(Path(bad['output']).exists())
        self.assertFalse(Path(bad['receipt']).exists())

    def test_preflight_without_binaries_and_missing_pyav_refuses_all_phases(self):
        with patch.dict(os.environ, PATH=''):
            result = rp.pyav_preflight()
        self.assertEqual(result['backend'], 'pyav')
        self.assertIn('libavcodec', result['libraries'])
        with patch.dict(os.environ, SLURM_JOB_ID='1', SLURMD_NODENAME='cpu-0001'), \
                patch.dict(sys.modules, av=None):
            for operation in ('plan', 'frames', 'package'):
                with self.subTest(operation=operation), self.assertRaisesRegex(ValueError, 'CPU decoder unavailable'):
                    a.run({'operation': operation})

    def test_dense_and_sparse_ordinals_pixels_and_fail_closed(self):
        root = self.directory()
        source = dict(video=self.video(root, 6), pool=[0, 2, 5], total_num_frames=6,
                      pose_count=6, dataset='d1', scene='v123')
        sparse = dict(source, sparse_poses=True, frame_numbers=[0, 2, 5], pose_count=3)
        with patch.dict(os.environ, PATH=''), patch.object(rp.subprocess, 'Popen', side_effect=AssertionError('external tool')):
            for value in (source, sparse):
                receipt = rp.decode_pyav_pool(value, root / 'frames')
                self.assertEqual(receipt['decoded_frame_count'], 6)
                self.assertEqual([f['frame_number'] for f in receipt['frames']], [0, 2, 5])
                for frame in receipt['frames']:
                    self.assertEqual(rp.file_sha(frame['path']), frame['sha256'])
                    with Image.open(frame['path']) as image:
                        expected = np.full((16, 16, 3), [frame['frame_number'], 0, 23], dtype=np.uint8)
                        np.testing.assert_array_equal(np.asarray(image), expected)
            for changes in (dict(total_num_frames=7, pose_count=7), dict(pool=[0, 6]),
                            dict(pose_count=5), dict(video={**source['video'], 'sha256': '0'*64})):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    rp.decode_pyav_pool({**source, **changes}, root / 'bad')
            with self.assertRaisesRegex(ValueError, 'unposed'):
                rp.decode_pyav_pool({**sparse, 'pool': [0, 1]}, root / 'bad')

    def test_plan_frames_package_real_dispatch_with_pyav_only(self):
        root = self.directory()
        request = fixture(root)
        request.update(variant='all_frames32', pool_size=96)
        index = json.loads(rp.read_pin(request['recordings']))
        index['recordings'][0]['video'] = self.video(root, 1000)
        ip = save(root, 'index.json', index)
        spec = dict(operation='plan', request=save(root, 'request.json', request), index=ip,
                    output=str(root/'bound.json'), plan=str(root/'plan.json'), receipt=str(root/'plan_receipt.json'))
        with patch.dict(os.environ, PATH='', SLURM_JOB_ID='1', SLURMD_NODENAME='cpu-0001', SLURM_ARRAY_TASK_ID='0'), \
                patch.object(rp.subprocess, 'Popen', side_effect=AssertionError('external tool')), \
                patch.object(rp, 'decode_pool', side_effect=AssertionError('legacy decoder')):
            planned = a.run(spec)
            pp = rp.pin(root/'plan.json')
            plan = a.read(pp)
            framed = a.run(dict(operation='frames', plan=pp, root=str(root/'frames'), shards=1,
                                output=str(root/'staged.json'), receipt=str(root/'frame_receipt.json')))
            staged = a.read(rp.pin(root/'staged.json'))
            self.assertEqual(staged['plan'], pp)
            self.assertEqual(staged['scenes'][0]['video'], index['recordings'][0]['video'])
            numbers = [f['frame_number'] for f in staged['scenes'][0]['frames']]
            self.assertEqual(numbers, a.used_frames(plan['scenes'][0], plan))
            self.assertEqual(staged['scenes'][0]['decoded_frame_count'], 1000)
            packaged = a.run(dict(operation='package', plan=pp, staged=[rp.pin(root/'staged.json')],
                root=str(root), output=str(root/'frames.tar'), manifest=str(root/'manifest.json'),
                a0_manifest=None, a0_archive=None, a0=None, receipt=str(root/'package_receipt.json')))
        for result in (planned, framed, packaged):
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(result['details']['decoder']['backend'], 'pyav')
            for pin in result['outputs']:
                self.assertEqual(rp.pin(pin['path']), pin)
        with tarfile.open(root/'frames.tar') as archive:
            self.assertEqual(len(archive.getmembers()), len(numbers))
        for frame in staged['scenes'][0]['frames']:
            with Image.open(frame['path']) as image:
                number = frame['frame_number']
                self.assertEqual(image.getpixel((0, 0)), (number % 256, number // 256, 23))


if __name__ == '__main__':
    unittest.main()
