"""Reproduce the review's metadata probes and check bounded frame work."""
import importlib
import os
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

TREE = Path(sys.argv.pop(1)).resolve()
sys.path[:0] = [str(TREE / 'tests'), str(TREE)]
memo = importlib.import_module('test_checkpoint_verify_memo')
frame = importlib.import_module('test_parallel_frame_sha')


class ReviewProbes(unittest.TestCase):
    def checkpoint(self):
        fixture = memo.CheckpointMemoTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_chmod_invalidates_memo(self):
        f = self.checkpoint()
        with patch.object(memo.r8, 'complete_uncached', wraps=memo.r8.complete_uncached) as full:
            self.assertTrue(memo.r8.complete(f.marker, f.binding))
            self.assertTrue(memo.r8.complete(f.marker, f.binding))
            payload = f.directory / 'replicated.pt'
            payload.chmod(payload.stat().st_mode ^ 0o100)
            self.assertTrue(memo.r8.complete(f.marker, f.binding))
            self.assertEqual(full.call_count, 2)

    def test_write_during_hash_refuses_and_cannot_publish_hit(self):
        f = self.checkpoint()
        original = memo.r8.complete_uncached
        def changed(path, binding):
            valid = original(path, binding)
            (f.directory / 'replicated.pt').write_bytes(b'changed-after-full-hash')
            return valid
        with patch.object(memo.r8, 'complete_uncached', changed):
            self.assertFalse(memo.r8.complete(f.marker, f.binding))
        self.assertFalse(memo.r8.complete(f.marker, f.binding))

    def test_symlinked_parent_falls_back_without_events(self):
        f = self.checkpoint()
        link = f.root / 'alias'
        link.symlink_to(f.directory, target_is_directory=True)
        with patch.object(memo.r8, 'complete_uncached', wraps=memo.r8.complete_uncached) as full:
            self.assertTrue(memo.r8.complete(link / 'complete.json', f.binding))
            self.assertTrue(memo.r8.complete(link / 'complete.json', f.binding))
            self.assertEqual(full.call_count, 2)
        self.assertFalse((f.root / '.checkpoint-verification/172660.events.jsonl').exists())

    def test_frame_inflight_limit_and_worker_error_propagation(self):
        from concurrent.futures import ThreadPoolExecutor
        f = frame.FrameHashTests()
        f.setUp()
        for workers in (1, 4, 8):
            counts = {'pending': 0, 'peak': 0}
            class Pool:
                def __init__(self, max_workers):
                    self.pool = ThreadPoolExecutor(max_workers=max_workers)
                    self.assert_workers = max_workers
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    self.pool.shutdown(wait=True)
                def submit(self, fn, item):
                    future = self.pool.submit(fn, item)
                    counts['pending'] += 1
                    counts['peak'] = max(counts['peak'], counts['pending'])
                    class Result:
                        def result(self):
                            try:
                                return future.result()
                            finally:
                                counts['pending'] -= 1
                    return Result()
            with patch.dict(os.environ, {'TK_FRAME_SHA_WORKERS':str(workers)}), \
                    patch('concurrent.futures.ThreadPoolExecutor', Pool):
                self.assertEqual(f.check(True), 19)
            self.assertLessEqual(counts['peak'], 2 * workers)
            self.assertEqual(counts['pending'], 0)

    def test_randomized_serial_parallel_verdict_and_count(self):
        rng = random.Random(172660)
        for case in range(12):
            f = frame.FrameHashTests()
            f.setUp()
            rng.shuffle(f.values)
            if case % 3 == 1:
                f.paths[rng.randrange(len(f.paths))].write_bytes(b'corrupt')
            elif case % 3 == 2:
                path = f.paths[rng.randrange(len(f.paths))]
                path.rename(path.with_suffix('.retained'))
            values = []
            for parallel in (False, True):
                try:
                    values.append(('PASS', f.check(parallel)))
                except (OSError, ValueError) as error:
                    values.append(('REFUSE', type(error).__name__))
            self.assertEqual(values[0], values[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
