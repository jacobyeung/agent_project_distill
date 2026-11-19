import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from student_pilot.p3_provenance import file_pin, write
from student_pilot.s1_admission import audit_frames


class OrchardAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="orchard_admission_", dir=os.environ["TMPDIR"]))
        self.frames = self.root / "frames"
        self.frames.mkdir()
        self.image = self.frames / "frame.png"
        self.image.write_bytes(b"fixed-image-bytes")
        self.image_pin = file_pin(self.image)

    def receipt(self, pins, indices=None):
        database = self.root / "rows.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)")
            for number, pin in enumerate(pins):
                row = dict(qid=str(number), student_input=dict(frames=[pin]))
                connection.execute("INSERT INTO rows VALUES (?,?,?)", (number, json.dumps(row), "{}"))
        value = dict(count=len(pins), database=file_pin(database))
        if indices is not None:
            write(self.root / "indices.json", indices)
            value.update(count=len(indices), indices=file_pin(self.root / "indices.json"))
        return dict(streams=dict(vqa=value))

    def audit(self, receipt, name="audit"):
        output = self.root / name
        output.mkdir()
        return audit_frames(receipt, [self.frames], output, sample_size=1)

    def test_all_retained_frames_exist_and_fixed_sample_is_authenticated(self):
        receipt = self.receipt([self.image_pin, self.image_pin])
        first = self.audit(receipt)
        second = self.audit(receipt, "second")
        self.assertTrue(first["all_retained_frames_exist"])
        self.assertEqual(first["sources"]["vqa"]["frame_references"], 2)
        self.assertEqual(first["sources"]["vqa"]["unique_frames"], 1)
        self.assertEqual(first["sources"]["vqa"]["hash_sample"], second["sources"]["vqa"]["hash_sample"])

    def test_removed_rows_do_not_enter_the_rgb_denominator(self):
        missing = dict(path=str(self.frames / "absent.png"), sha256="0"*64)
        receipt = self.receipt([missing, self.image_pin], indices=[1])
        report = self.audit(receipt)
        self.assertEqual(report["sources"]["vqa"]["rows"], 1)

    def test_missing_retained_frame_fails_closed(self):
        missing = dict(path=str(self.frames / "absent.png"), sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "absent"):
            self.audit(self.receipt([missing]))

    def test_changed_sample_and_conflicting_frame_hashes_fail_closed(self):
        receipt = self.receipt([self.image_pin])
        self.image.write_bytes(b"different-image-bytes")
        with self.assertRaisesRegex(ValueError, "hash sample differs"):
            self.audit(receipt)
        from student_pilot.s1_admission import FrameAudit
        output = self.root / "conflict"
        output.mkdir()
        audit = FrameAudit(output, [self.frames], sample_size=1)
        try:
            audit.keep(dict(student_input=dict(frames=[self.image_pin])), "vqa")
            with self.assertRaisesRegex(ValueError, "conflicting"):
                audit.keep(dict(student_input=dict(frames=[file_pin(self.image)])), "routing")
        finally:
            audit.close()

    def test_native_sql_stream_rebuild_iterator_is_read_only(self):
        from student_pilot.carrier_c1_data import _source_lines
        receipt = self.receipt([self.image_pin])["streams"]["vqa"]
        source = dict(schema="c1-stream-v1", stream="pointing", count=1, database=receipt["database"])
        write(self.root / "source.json", source)
        with _source_lines(file_pin(self.root / "source.json"), True, "pointing") as lines:
            self.assertEqual(len(list(lines)), 1)
        self.assertEqual(file_pin(self.root / "rows.sqlite"), receipt["database"])

    def test_legacy_dataset_aliases_use_the_label_list_identity(self):
        from student_pilot.ground_target_filter import pointing_key
        row = dict(dataset="d1", scene="scene0123_00", pointing=dict(frame=3, instance_id=8))
        self.assertEqual(pointing_key(row), "scannet/scene0123_00|2|8")
        row.update(dataset="d2", scene="capture")
        self.assertEqual(pointing_key(row), "scannetpp/capture|2|8")


if __name__ == "__main__":
    unittest.main()
