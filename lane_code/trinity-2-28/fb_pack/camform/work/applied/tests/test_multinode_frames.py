import copy
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from student_pilot import ddp_training, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from tests.test_ddp_checkpoints import storage_patches


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class MultinodeFrameTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="multinode_frames_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.output = self.root / "train"
        self.source = self.root / "source.ppm"
        self.source.write_bytes(b"P6\n1 1\n255\n\x00\x00\xff")
        self.rows = [{"qid": "synthetic", "student_input": {"frames": [binding(self.source)] * 32}}]
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        storage_patches(self.stack, self.root)
        self.store = storage.RunArtifacts(self.output, {"provisional_diagnostic": LABEL, "PROVISIONAL_DIVISION_SHA": "a" * 64}, self.root)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_bytes(canonical_bytes({"synthetic": True}))
        self.localized = storage.localize_frames(self.rows, self.store, self.manifest, self.root, True)
        self.receipt = load_json(self.output / "frame_staging.json")
        self.pin = binding(self.output / "frame_staging.json")

    def mirror(self, receipt=None, rows=None):
        return ddp_training.mirror_staged_frames(receipt or self.receipt, self.pin, rows or self.localized,
                                               self.output, self.root, 1, LABEL)

    def test_mirror_copies_missing_frames_atomically_and_records_node_receipt(self):
        (self.output / "frames").rename(self.output / "retained_leader_frames")
        renames = []
        original = Path.rename
        def rename(path, target):
            self.assertIn('.partial.', path.name)
            self.assertEqual(binding(path)['sha256'], self.receipt['files'][0]['staged']['sha256'])
            renames.append((str(path), str(target)))
            return original(path, target)
        with patch.object(Path, 'rename', rename):
            pin = self.mirror()
        self.assertEqual(len(renames), 1)
        record = load_json(pin['path'])
        self.assertEqual(record['node_rank'], 1)
        self.assertEqual(record['source_receipt'], self.pin)
        self.assertTrue(Path(pin['path']).is_relative_to(self.output / 'runtime/node1'))
        for frame in self.localized[0]['student_input']['frames']:
            binding(frame['path'], frame['sha256'])

    def test_resume_reuses_verified_local_frames_and_keeps_receipts(self):
        with patch.object(storage, 'copy_new', side_effect=AssertionError('unchanged frame copied')):
            first, second = self.mirror(), self.mirror()
        self.assertNotEqual(first['path'], second['path'])
        self.assertTrue(Path(first['path']).is_file())

    def test_corrupt_source_and_existing_frame_refuse_before_use(self):
        destination = Path(self.receipt['files'][0]['staged']['path'])
        destination.rename(destination.with_name(destination.name + '.retained'))
        self.source.write_bytes(b'corrupt synthetic source')
        with self.assertRaises(ValueError):
            self.mirror()
        self.assertFalse(destination.exists())
        destination.write_bytes(b'corrupt synthetic staged frame')
        with self.assertRaises(ValueError):
            self.mirror()

    def test_receipt_mutation_wrong_path_and_incomplete_coverage_refuse(self):
        changed = copy.deepcopy(self.receipt)
        changed['files'][0]['source']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            self.mirror(changed)
        for section, field, value in (('staged', 'path', str(self.root / 'outside_train')), ('source', 'sha256', 'b' * 64)):
            changed = copy.deepcopy(self.receipt)
            changed['files'][0][section][field] = value
            pin = {**self.pin, 'sha256': digest_json(changed)}
            with self.assertRaises(ValueError):
                ddp_training.mirror_staged_frames(changed, pin, self.localized, self.output, self.root, 1, LABEL)
        with self.assertRaisesRegex(ValueError, 'exactly'):
            self.mirror(rows=[{'student_input': {'frames': []}}])


if __name__ == '__main__':
    unittest.main()
