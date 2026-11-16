"""Sharded target storage: candidate rows inline in the index, targets as byte ranges of shared shard files."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from student_pilot import provisional, startup_receipt
from student_pilot.common import binding, canonical_bytes

LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class ShardedTargetTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ.get("LANE_TEST_OUTPUT") or tempfile.gettempdir())
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="sharded_", dir=root))
        frame = self.root / "frame.bin"
        frame.write_bytes(b"synthetic RGB fixture")
        self.frame = binding(frame)

    def rows(self, count=12):
        rows = []
        for index in range(count):
            rows.append({"qid": f"q{index:04d}", "dataset": "d1", "scene": f"v{index // 3:04d}",
                         "category": "object_counting", "answer": str(index % 5),
                         "target": f"<think>\nstep {index} with unicode ° and quotes \"x\"\n</think>\n\n{index % 5}",
                         "generation_commit": "a" * 40, "validation_commit": "b" * 40,
                         "student_input": {"question": "How many?", "options": [], "frames": [self.frame] * 32,
                                           "frame_indices": list(range(32)), "timestamps": [i / 2 for i in range(32)],
                                           "fps": 2.0, "total_num_frames": 32}})
        return rows

    def per_file(self, rows):
        entries = []
        for row in rows:
            path = self.root / "files" / (row["qid"] + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_bytes(row))
            pin = binding(path)
            entries.append({"qid": row["qid"], "pool": "p", "scene": row["scene"], "question_type": row["category"],
                            "dataset": row["dataset"], "answer": row["answer"], "target_path": str(path),
                            "sha256": pin["sha256"], "row_path": str(path), "row_sha256": pin["sha256"],
                            "generation_commit": row["generation_commit"], "validation_commit": row["validation_commit"]})
        return entries

    def sharded(self, rows, shards=2, newline=False):
        entries, blobs = [], [bytearray() for _ in range(shards)]
        spans = []
        for number, row in enumerate(rows):
            blob = blobs[number % shards]
            data = row["target"].encode() + (b"\n" if newline else b"")
            spans.append((number % shards, len(blob), len(data), hashlib.sha256(data).hexdigest()))
            blob.extend(data)
        paths = []
        for number, blob in enumerate(blobs):
            path = self.root / "shards" / f"s{number}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes(blob))
            paths.append(path)
        for row, (shard, offset, length, digest) in zip(rows, spans):
            entry = dict(row)
            entry.update({"pool": "p", "question_type": row["category"], "target_path": str(paths[shard]),
                          "target_offset": offset, "target_length": length, "sha256": digest})
            entries.append(entry)
        return entries

    def index(self, entries, name):
        path = self.root / name
        path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries))
        return path

    def load(self, entries, name, threads):
        with patch.dict(os.environ, {"STUDENT_IO_THREADS": str(threads)}):
            return provisional.load_provisional_candidates(self.index(entries, name), LABEL)

    @staticmethod
    def strip(rows):
        return [{k: v for k, v in row.items() if k != "candidate_provenance"} for row in rows]

    def test_sharded_rows_equal_per_file_rows(self):
        rows = self.rows()
        for threads in (1, 4):
            for newline in (False, True):
                with self.subTest(threads=threads, newline=newline):
                    expected = self.load(self.per_file(rows), f"file_{threads}.jsonl", threads)
                    loaded = self.load(self.sharded(rows, newline=newline), f"shard_{threads}_{newline}.jsonl", threads)
                    self.assertEqual(self.strip(loaded), self.strip(expected))
                    for row in loaded:
                        pin = row["candidate_provenance"]["target"]
                        self.assertEqual(sorted(pin), ["length", "offset", "path", "sha256"])
                        self.assertIsNone(row["candidate_provenance"]["row"])

    def test_whole_file_entries_keep_their_pins(self):
        rows = self.rows(3)
        for row in self.load(self.per_file(rows), "file_pins.jsonl", 1):
            self.assertEqual(sorted(row["candidate_provenance"]["target"]), ["path", "sha256"])

    def test_refusals(self):
        rows = self.rows(4)
        cases = {
            "wrong_sha": lambda e: e.update(sha256="0" * 64),
            "past_end": lambda e: e.update(target_offset=10 ** 6),
            "negative": lambda e: e.update(target_offset=-1),
            "zero_length": lambda e: e.update(target_length=0),
            "float_offset": lambda e: e.update(target_offset=1.0),
            "only_offset": lambda e: e.pop("target_length"),
            "row_file_too": lambda e: e.update(row_path=e["target_path"], row_sha256=e["sha256"]),
            "not_inline": lambda e: e.pop("student_input"),
            "other_text": lambda e: e.update(target_length=e["target_length"] - 1,
                                             sha256=hashlib.sha256(Path(e["target_path"]).read_bytes()[
                                                 e["target_offset"]:e["target_offset"] + e["target_length"] - 1]).hexdigest()),
        }
        for name, change in cases.items():
            for threads in (1, 4):
                with self.subTest(case=name, threads=threads):
                    entries = self.sharded(rows)
                    change(entries[1])
                    with self.assertRaises((ValueError, KeyError)):
                        self.load(entries, f"bad_{name}_{threads}.jsonl", threads)

    def test_dropped_dependency_pins_whole_shard(self):
        rows = self.rows(4)
        entries = self.sharded(rows, shards=1)
        index = self.index(entries, "dropped.jsonl")
        protocol = {"candidate_source": {"path": str(index)}}
        manifest = {"pre_evaluation_drops": [{"qid": rows[1]["qid"]}]}
        with patch("student_pilot.provisional_data._census_rows", return_value={}):
            pins = startup_receipt.dropped_dependencies(protocol, manifest, LABEL)
        shard = binding(Path(entries[1]["target_path"]))
        self.assertIn(shard, pins)
        self.assertNotIn(entries[1]["sha256"], [pin["sha256"] for pin in pins])


if __name__ == "__main__":
    unittest.main()
