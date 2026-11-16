import copy
import os
from pathlib import Path
import tempfile
import unittest

from student_pilot.first_batch_progress import PhaseJournal, RankJournal
from student_pilot.p3_provenance import file_pin, load, write


class FirstBatchProgressTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="first_batch_progress_", dir=os.environ["TMPDIR"]))
        self.plans = [[("pose", [0, 1]), ("mdg", [2, 3])]]
        self.binding = dict(config_sha256="a"*64, steps=1, device="cpu", cpu_threads=4)
        self.journal = RankJournal(self.root, self.binding, self.plans)
        self.records = [dict(step=1, microstep=number, rank=0, stream=stream, index=indices[0],
                             finite=True, seconds=.1, qid="fixture", loss=.1, components=dict(loss=.1),
                             tokens=10, effective_tokens=10)
                        for number, (stream, indices) in enumerate(self.plans[0])]

    def save(self):
        return self.journal.save(0, self.records, dict(seconds=.2, peak_rss_kib=100, cpu_threads=4))

    def test_completed_rank_is_authenticated_and_reused(self):
        self.assertIsNone(self.journal.load(0))
        saved = self.save()
        before = file_pin(self.root / "rank_000.complete.json")
        self.assertEqual(self.journal.load(0), saved)
        self.assertEqual(file_pin(self.root / "rank_000.complete.json"), before)
        self.assertIsNone(self.journal.load(1))

    def test_foreign_binding_cannot_reuse_a_rank(self):
        self.save()
        journal = RankJournal(self.root, {**self.binding, "config_sha256": "b"*64}, self.plans)
        with self.assertRaisesRegex(ValueError, "binding"):
            journal.load(0)

    def test_changed_rank_payload_is_rejected(self):
        self.save()
        marker = load(self.root / "rank_000.complete.json")
        with Path(marker["payload"]["path"]).open("ab") as handle:
            handle.write(b" ")
        with self.assertRaises(ValueError):
            self.journal.load(0)

    def test_partial_duplicate_nonfinite_and_wrong_row_do_not_complete(self):
        variants = [self.records[:1], self.records+self.records[:1]]
        for key, value in (("finite", False), ("index", 77), ("rank", 1), ("loss", float("inf"))):
            changed = copy.deepcopy(self.records)
            changed[0][key] = value
            variants.append(changed)
        for records in variants:
            with self.subTest(records=records):
                with self.assertRaises(ValueError):
                    self.journal.save(0, records, dict(seconds=.2))
        self.assertFalse((self.root / "rank_000.complete.json").exists())

    def test_completed_preparation_phase_is_not_rebuilt(self):
        phases = PhaseJournal(self.root, self.binding)
        calls = []

        def action(directory):
            calls.append(directory)
            write(directory / "receipt.json", dict(count=2))
            return dict(outputs=[file_pin(directory / "receipt.json")])

        first, reused = phases.run("prepare", action)
        self.assertFalse(reused)
        second, reused = phases.run("prepare", action)
        self.assertTrue(reused)
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)
        with Path(first["outputs"][0]["path"]).open("ab") as handle:
            handle.write(b" ")
        with self.assertRaises(ValueError):
            phases.run("prepare", action)

    def test_failed_phase_never_publishes_completion(self):
        phases = PhaseJournal(self.root, self.binding)

        def fail(directory):
            write(directory / "partial.json", dict(partial=True))
            raise ValueError("intentional incomplete phase")

        with self.assertRaisesRegex(ValueError, "intentional"):
            phases.run("prepare", fail)
        self.assertFalse((self.root / "phase_prepare.complete.json").exists())


if __name__ == "__main__":
    unittest.main()
