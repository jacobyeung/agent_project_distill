"""Byte-identical batches: the same admitted rows loaded from per-file targets and from a target shard encode to the
same tensors. Runs only where the pinned processor and the rows' frames are installed (code-aws preparation jobs, which
set STUDENT_MODEL_ROOT); elsewhere it skips."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sharded_equivalence_entries.jsonl"
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


@unittest.skipUnless(os.environ.get("STUDENT_MODEL_ROOT"), "needs the installed processor and frames")
class ShardedEquivalenceNative(unittest.TestCase):
    def test_batches_identical(self):
        import torch
        from student_pilot import provisional
        from student_pilot import diagnostic_data as clean
        from student_pilot.batches import load_processor

        root = Path(tempfile.mkdtemp(prefix="sharded_equiv_", dir=os.environ.get("LANE_TEST_OUTPUT") or None))
        per_file = root / "per_file.jsonl"
        per_file.write_bytes(FIXTURE.read_bytes())
        rows = provisional.load_provisional_candidates(per_file, LABEL)
        entries = {json.loads(line)["qid"]: json.loads(line) for line in FIXTURE.read_text().splitlines()}
        shard, blob, inline = root / "targets.txt", bytearray(), []
        for row in rows:
            data = row["target"].encode()
            entry = {key: row[key] for key in ("qid", "dataset", "scene", "category", "target", "student_input")}
            source = entries[row["qid"]]
            entry.update({"pool": source["pool"], "question_type": source["question_type"], "answer": source["answer"],
                          "generation_commit": source["generation_commit"],
                          "validation_commit": source["validation_commit"], "target_path": str(shard),
                          "target_offset": len(blob), "target_length": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(), "provisional_diagnostic": LABEL})
            blob.extend(data)
            inline.append(entry)
        shard.write_bytes(bytes(blob))
        index = root / "sharded.jsonl"
        index.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in inline))
        sharded = provisional.load_provisional_candidates(index, LABEL)
        self.assertEqual(len(rows), len(entries))
        processor = load_processor(bytes.fromhex(os.environ.get("R1_STUDENT_HEX") or "7177656e3335").decode())
        checked = 0
        for a, b in zip(rows, sharded):
            self.assertEqual({k: v for k, v in a.items() if k != "candidate_provenance"},
                             {k: v for k, v in b.items() if k != "candidate_provenance"})
            self.assertEqual(clean.target_tokens(processor, a), clean.target_tokens(processor, b))
            batch_a, audit_a = clean.encode_training(processor, a)
            batch_b, audit_b = clean.encode_training(processor, b)
            self.assertEqual(audit_a, audit_b)
            self.assertEqual(sorted(batch_a), sorted(batch_b))
            for key in batch_a:
                va, vb = batch_a[key], batch_b[key]
                if isinstance(va, torch.Tensor):
                    self.assertEqual(va.dtype, vb.dtype)
                    self.assertTrue(torch.equal(va, vb), key)
                else:
                    self.assertEqual(va, vb, key)
            checked += 1
        print(json.dumps({"sharded_equivalence_rows": checked, "identical": True}), flush=True)


if __name__ == "__main__":
    unittest.main()
