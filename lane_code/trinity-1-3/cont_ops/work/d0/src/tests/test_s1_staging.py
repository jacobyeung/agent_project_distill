import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest


class PinnedStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "launch_s1/b/s.py"
        spec = importlib.util.spec_from_file_location("s1_staging_test", path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="s1_staging_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.kit = self.root / "kit"
        self.kit.mkdir()
        self.stage = self.module.Stage(self.kit, self.root / "node")

    def archive(self, *, name=None, content=b"fixture-frame", link=False, wrong_member_hash=False):
        digest = hashlib.sha256(content).hexdigest()
        filename = name or digest[:2]+"/"+digest+".png"
        if wrong_member_hash:
            filename = "aa/"+("a"*64)+".png"
        path = self.root / "frames.tar"
        with tarfile.open(path, "x") as archive:
            member = tarfile.TarInfo(filename)
            member.size = len(content)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = "/tmp/unowned"
                member.size = 0
            archive.addfile(member, None if link else io.BytesIO(content))
        return dict(source=str(path), sha256=self.module.sha256(path), bytes=path.stat().st_size,
                    destination="data2root/k6tk", members=1), filename

    def test_streamed_archive_and_cached_sample_are_verified(self):
        entry, name = self.archive()
        first = self.stage.archive(entry)
        self.assertFalse(first["reused"])
        self.assertEqual(self.stage.destination("data2root/k6tk/"+name).read_bytes(), b"fixture-frame")
        self.assertTrue(self.stage.archive(entry)["reused"])
        path = self.stage.destination("data2root/k6tk/"+name)
        path.chmod(0o600)
        path.write_bytes(b"changed-frame")
        with self.assertRaisesRegex(ValueError, "hash sample"):
            self.stage.archive(entry)

    def test_wrong_full_archive_digest_never_creates_completion_marker(self):
        entry, _ = self.archive()
        entry["sha256"] = "b"*64
        with self.assertRaisesRegex(ValueError, "archive digest"):
            self.stage.archive(entry)
        self.assertEqual(list(self.stage.state.iterdir()), [])

    def test_member_hash_is_checked_during_streaming(self):
        entry, _ = self.archive(wrong_member_hash=True)
        with self.assertRaisesRegex(ValueError, "payload differs"):
            self.stage.archive(entry)
        self.assertEqual(list(self.stage.state.iterdir()), [])

    def test_parent_traversal_and_links_are_rejected(self):
        entry, _ = self.archive(name="../outside.png")
        with self.assertRaisesRegex(ValueError, "Unsafe archive"):
            self.stage.archive(entry)

    def test_symbolic_link_member_is_rejected(self):
        entry, _ = self.archive(link=True)
        with self.assertRaisesRegex(ValueError, "Unsafe archive"):
            self.stage.archive(entry)

    def test_destination_traversal_and_symlinks_are_rejected(self):
        with self.assertRaises(ValueError):
            self.stage.destination("u/../outside")
        outside = self.root / "outside"
        outside.mkdir()
        root = self.stage.roots["u"]
        root.mkdir(parents=True)
        (root / "escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.stage.destination("u/escape/payload")

    def test_files_and_each_raster_are_bound_without_deleting_sources(self):
        source_root = self.root / "source"
        source = source_root / "u/token/c/fixture.npz"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"raster-fixture")
        record = dict(destination="u/token/c/fixture.npz",
                      sha256=self.module.sha256(source), bytes=source.stat().st_size)
        manifest = self.kit / "rasters.json"
        manifest.write_text(json.dumps(dict(schema="s1-mdg-raster-inputs-v1", files=[record],
                                           count=1, bytes=record["bytes"])))
        plan = dict(schema="s1-staged-inputs-v1", files=[], archives=[],
                    directories=[dict(source_root=str(source_root),
                                      manifest=dict(file="rasters.json", sha256=self.module.sha256(manifest)))])
        result = self.stage.run(plan)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["production_authorized"])
        self.assertTrue(source.is_file())
        self.assertEqual(self.stage.destination(record["destination"]).read_bytes(), source.read_bytes())
        self.assertEqual(self.stage.run(plan), result)

    def test_payload_package_verifies_members_and_retains_duplicate_role_pins(self):
        path = self.root / "payload.tar"
        data = b"packed-source"
        record = dict(name="opaque.jsonl.gz", sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        with tarfile.open(path, "x") as archive:
            for name, body in (("opaque.jsonl.gz", data), ("opaque.jsonl.gz", data),
                               ("SHA256SUMS", b"inventory\n")):
                member = tarfile.TarInfo(name)
                member.size = len(body)
                archive.addfile(member, io.BytesIO(body))
        entry = dict(source=str(path), sha256=self.module.sha256(path), bytes=path.stat().st_size,
                     inventory=[record, record], members=1, destination="u/opaque")
        self.assertEqual(self.stage.archive(entry)["members"], 1)
        self.assertEqual(self.stage.destination("u/opaque/opaque.jsonl.gz").read_bytes(), data)
        self.assertTrue(self.stage.archive(entry)["reused"])


if __name__ == "__main__":
    unittest.main()
