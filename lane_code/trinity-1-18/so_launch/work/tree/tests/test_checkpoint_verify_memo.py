import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
torch.set_num_threads(8)

spec = importlib.util.spec_from_file_location('r8', Path(__file__).resolve().parents[1] / 'launch_s1/b/r8.py')
r8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r8)


class CheckpointMemoTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='checkpoint-memo-', dir=os.environ['TEST_TMP_ROOT']))
        self.directory = self.root / 'checkpoint_000200'
        self.directory.mkdir()
        (self.directory / 'shards').mkdir()
        self.binding = dict(world_size=2, config_sha256='a'*64)
        self.files = {}
        for name in ('replicated.pt', 'rng000.pt', 'rng001.pt', 'shards/rank000.pt', 'shards/rank001.pt'):
            path = self.directory / name
            path.write_bytes(b'fixture:' + name.encode())
            self.files[name] = dict(bytes=path.stat().st_size, sha256=r8.checksum(path))
        self.marker = self.directory / 'complete.json'
        self.marker.write_text(json.dumps(dict(schema='c1-checkpoint-v1', binding=self.binding, step=200, files=self.files)))
        self.env = patch.dict(os.environ, {'TK_CHECKPOINT_VERIFY_MEMO': '1', 'SLURM_JOB_ID': '172660', 'TK_JOB_START': '1795040434'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_only_first_same_job_check_reads_payloads(self):
        original = r8.complete_uncached
        with patch.object(r8, 'complete_uncached', wraps=original) as full:
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertEqual(full.call_count, 1)
        rows = [json.loads(line) for line in (self.root / '.checkpoint-verification/172660.events.jsonl').read_text().splitlines()]
        self.assertEqual([row['hit'] for row in rows], [False, True, True])
        self.assertTrue(all(row['valid'] and row['bytes'] > 0 for row in rows))

    def test_default_off_rehashes_and_writes_no_memo(self):
        with patch.dict(os.environ, {'TK_CHECKPOINT_VERIFY_MEMO': '0'}), patch.object(r8, 'complete_uncached', wraps=r8.complete_uncached) as full:
            for _ in range(2):
                self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertEqual(full.call_count, 2)
        self.assertFalse((self.root / '.checkpoint-verification').exists())

    def test_same_size_corruption_with_restored_mtime_refuses(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        path = self.directory / 'replicated.pt'
        before = path.stat()
        path.write_bytes(b'X' * before.st_size)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertFalse(r8.complete(self.marker, self.binding))

    def test_inode_replacement_even_with_same_size_and_mtime_refuses(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        path = self.directory / 'replicated.pt'
        before = path.stat()
        path.rename(path.with_suffix('.preserved'))
        path.write_bytes(b'Y' * before.st_size)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertFalse(r8.complete(self.marker, self.binding))

    def test_another_job_or_allocation_clock_rehashes(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        for change in ({'SLURM_JOB_ID': '172661'}, {'TK_JOB_START': '1795040435'}):
            with patch.dict(os.environ, change), patch.object(r8, 'complete_uncached', wraps=r8.complete_uncached) as full:
                self.assertTrue(r8.complete(self.marker, self.binding))
                self.assertEqual(full.call_count, 1)

    def test_marker_or_binding_change_cannot_hit(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        self.assertFalse(r8.complete(self.marker, dict(self.binding, world_size=4)))
        value = json.loads(self.marker.read_text())
        value['step'] = -1
        self.marker.write_text(json.dumps(value))
        self.assertFalse(r8.complete(self.marker, self.binding))

    def test_corrupt_memo_falls_back_to_full_hash(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        for path in (self.root / '.checkpoint-verification').glob('*.json'):
            path.write_text('{partial')
        with patch.object(r8, 'complete_uncached', wraps=r8.complete_uncached) as full:
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertEqual(full.call_count, 1)

    def test_purged_payload_refuses_resume(self):
        self.assertTrue(r8.complete(self.marker, self.binding))
        path = self.directory / 'rng000.pt'
        path.rename(self.root / 'purged-fixture.pt')
        self.assertFalse(r8.complete(self.marker, self.binding))

    def test_missing_allocation_identity_disables_memo(self):
        with patch.dict(os.environ, {'TK_JOB_START': ''}), patch.object(r8, 'complete_uncached', wraps=r8.complete_uncached) as full:
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertTrue(r8.complete(self.marker, self.binding))
            self.assertEqual(full.call_count, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
