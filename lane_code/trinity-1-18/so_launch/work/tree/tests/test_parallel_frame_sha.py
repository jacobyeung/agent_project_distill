import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
torch.set_num_threads(8)

spec = importlib.util.spec_from_file_location('frames', Path(__file__).resolve().parents[1] / 'launch_s1/b/f2.py')
frames = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frames)


class FrameHashTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='parallel-frames-', dir=os.environ['TEST_TMP_ROOT']))
        self.data = self.root / 'data'
        self.manifest = self.root / 'manifest.json'
        self.values, self.paths = [], []
        for number in range(19):
            raw = (str(number) + ':fixture').encode() * 300
            sha = hashlib.sha256(raw).hexdigest()
            relative = 'k3f8/' + sha[:2] + '/' + sha + '.png'
            path = self.data / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.paths.append(path)
            self.values.append(dict(path='/data2/' + relative, sha256=sha))

    def check(self, parallel):
        self.manifest.write_text(json.dumps(self.values))
        sha = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        with patch.dict(os.environ, {'TK_PARALLEL_FRAME_SHA': str(int(parallel))}):
            return frames.verify(self.manifest, self.data, sha)

    def test_parallel_and_default_counts_match(self):
        self.assertEqual(self.check(False), 19)
        self.assertEqual(self.check(True), 19)

    def test_default_does_not_construct_a_thread_pool(self):
        with patch('concurrent.futures.ThreadPoolExecutor', side_effect=AssertionError('default spawned workers')):
            self.assertEqual(self.check(False), 19)

    def test_late_corrupt_file_refuses_both_modes(self):
        self.paths[-1].write_bytes(b'corrupt')
        for parallel in (False, True):
            with self.subTest(parallel=parallel), self.assertRaisesRegex(ValueError, 'Frame differs'):
                self.check(parallel)

    def test_duplicate_and_wrong_path_refuse_both_modes(self):
        original = list(self.values)
        for values in (original + original[-1:], [dict(original[0], path='/data2/../escape')]):
            self.values = values
            for parallel in (False, True):
                with self.subTest(parallel=parallel), self.assertRaisesRegex(ValueError, 'Invalid frame identity'):
                    self.check(parallel)

    def test_manifest_digest_refuses(self):
        self.check(False)
        with patch.dict(os.environ, {'TK_PARALLEL_FRAME_SHA': '1'}), self.assertRaisesRegex(ValueError, 'manifest differs'):
            frames.verify(self.manifest, self.data, '0'*64)

    def test_missing_and_symlinked_files_refuse(self):
        moved = self.paths[0].with_suffix('.preserved')
        self.paths[0].rename(moved)
        with self.assertRaises(FileNotFoundError):
            self.check(True)
        self.paths[0].symlink_to(moved)
        with self.assertRaisesRegex(ValueError, 'leaves local store'):
            self.check(True)

    def test_worker_cap(self):
        for value in ('0', '9', '-1', 'bad'):
            with patch.dict(os.environ, {'TK_FRAME_SHA_WORKERS': value}), self.assertRaises(ValueError):
                self.check(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
