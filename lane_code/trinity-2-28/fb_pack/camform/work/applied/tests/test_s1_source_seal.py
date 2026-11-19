import copy
import os
from pathlib import Path
import tempfile
import unittest

from student_pilot import source_seal
from student_pilot.p3_provenance import sha256


class SourceSealTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="source_seal_", dir=os.environ["TMPDIR"]))
        self.root = self.directory / "tree"
        self.root.mkdir()
        (self.root / "module.py").write_text("value = 1\n")
        self.files = source_seal.inventory(self.root)
        self.archive = self.directory / "tree.tar"
        source_seal.archive(self.root, self.archive, self.files)
        self.seal = source_seal.create(self.root, self.archive, self.files, {})

    def test_seal_binds_tree_archive_and_configuration_without_a_git_sha(self):
        revision = source_seal.verify(self.seal, self.root, self.files)
        self.assertEqual(revision, "sha256:"+self.seal["tree_sha256"])
        self.assertNotEqual(len(revision), 40)
        first = source_seal.binding(self.seal, "a"*64)
        second = source_seal.binding(self.seal, "b"*64)
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual(first["archive"], self.seal["archive"])
        source_seal.check_binding(first, self.seal, "a"*64)
        with self.assertRaises(ValueError):
            source_seal.check_binding(first, self.seal, "b"*64)

    def test_mutated_source_and_archive_are_rejected(self):
        (self.root / "module.py").write_text("value = 2\n")
        with self.assertRaisesRegex(ValueError, "Source"):
            source_seal.verify(self.seal, self.root, self.files)
        (self.root / "module.py").write_text("value = 1\n")
        with self.archive.open("ab") as handle:
            handle.write(b"unexpected")
        with self.assertRaises(ValueError):
            source_seal.verify(self.seal, self.root, self.files)

    def test_rehashed_foreign_archive_does_not_prove_the_tree(self):
        foreign = self.directory / "foreign"
        foreign.mkdir()
        (foreign / "module.py").write_text("value = 8\n")
        path = self.directory / "foreign.tar"
        source_seal.archive(foreign, path, source_seal.inventory(foreign))
        changed = copy.deepcopy(self.seal)
        changed["archive"] = dict(path=str(path), sha256=sha256(path))
        with self.assertRaisesRegex(ValueError, "Archive"):
            source_seal.verify(changed, self.root, self.files)

    def test_links_are_not_source_files(self):
        (self.root / "linked").symlink_to(self.archive)
        with self.assertRaisesRegex(ValueError, "link"):
            source_seal.inventory(self.root)

    def test_export_retains_training_and_export_configuration_seals(self):
        training = source_seal.binding(self.seal, "a"*64)
        exported = source_seal.binding(self.seal, "b"*64)
        artifact = dict(source_seal=exported, training_source_seal=training, config_sha256="b"*64)
        source_seal.check_export(dict(source_seal=training), artifact)
        artifact["config_sha256"] = "c"*64
        with self.assertRaisesRegex(ValueError, "lineage"):
            source_seal.check_export(dict(source_seal=training), artifact)
        with self.assertRaisesRegex(ValueError, "lacks"):
            source_seal.check_export(dict(source_seal=training), {})


if __name__ == "__main__":
    unittest.main()
