import os
from pathlib import Path
import tempfile
import unittest

from student_pilot import mdg_inputs
from student_pilot.p3_provenance import file_pin, write


class MDGInputTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="mdg_inputs_", dir=os.environ["TMPDIR"]))

    def test_two_clip_sources_are_pinned_without_concatenation(self):
        clips = []
        for number in range(2):
            directory = self.root / str(number)
            directory.mkdir()
            write(directory / "a.jsonl", dict(scene="scene", qid=str(number)))
            clips.append(file_pin(directory / "a.jsonl"))
        write(self.root / "clips.json", dict(schema="s1-mdg-clips-v1", clips=clips))
        manifest = file_pin(self.root / "clips.json")
        self.assertEqual(mdg_inputs.clip_sources(manifest), clips)
        with Path(clips[1]["path"]).open("ab") as handle:
            handle.write(b" ")
        with self.assertRaises(ValueError):
            mdg_inputs.clip_sources(manifest)

    def test_directory_manifest_cannot_escape_its_root(self):
        write(self.root / "r.json", dict(schema="s1-mdg-raster-inputs-v1", count=1,
              files=[dict(destination="../outside.npz", bytes=3, sha256="a"*64)]))
        source = dict(rasters=str(self.root), raster_manifest=file_pin(self.root / "r.json"))
        with self.assertRaisesRegex(ValueError, "raster member"):
            mdg_inputs.raster_manifest(source)

    def test_initialization_binds_both_metadata_and_weight_bytes(self):
        write(self.root / "mdg.json", dict(schema="mdg-head-v1"))
        (self.root / "mdg.pt").write_bytes(b"fixture-not-a-model")
        values = {key: file_pin(self.root / key) for key in ("mdg.json", "mdg.pt")}
        self.assertEqual(mdg_inputs.artifact(values), values)
        with (self.root / "mdg.pt").open("ab") as handle:
            handle.write(b"changed")
        with self.assertRaises(ValueError):
            mdg_inputs.artifact(values)

    def test_resized_frame_root_does_not_change_legacy_rgb_mapping(self):
        sha = "a"*64
        clip = dict(qid="1", scene="scene", frame_indices=list(range(32)), frame_sha256=[sha]*32)
        before = os.environ.get("STUDENT_FRAME_ROOT_MAP")
        bound = mdg_inputs.explicit_frames(clip, self.root / "resized")
        self.assertEqual(os.environ.get("STUDENT_FRAME_ROOT_MAP"), before)
        self.assertEqual(bound["student_input"]["frames"][0],
                         dict(path=str(self.root / "resized/k8pd/aa" / (sha+".png")), sha256=sha))
        self.assertNotIn("student_input", clip)

    def test_frame_manifest_uses_resized_not_original_hashes(self):
        original, resized = "a"*64, "b"*64
        write(self.root / "f.json", dict(complete=True, checked=1, errors={},
              frames={original: dict(name=f"k8pd/bb/{resized}.png", sha256=resized)}))
        values = mdg_inputs.frame_hashes(dict(frame_manifest=file_pin(self.root / "f.json")))
        self.assertEqual(values, {resized})


if __name__ == "__main__":
    unittest.main()
