import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class PersistentResumeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="persistent_resume_", dir=os.environ["TMPDIR"]))
        self.run = self.root / "run"
        self.persistent = self.root / "persistent"
        self.kit = self.root / "kit"
        for directory in (self.run, self.persistent, self.kit / "k"):
            directory.mkdir(parents=True)
        self.put(self.kit / "k/launch.json",
                 dict(run_directory=str(self.run), persistent_run_root=str(self.persistent)))
        self.chooser = Path(__file__).resolve().parents[1] / "launch_s1/b/r8.py"
        self.binding = dict(world_size=4, config_sha256="a"*64, trainer_commit="b"*40)

    def put(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True))

    def marker(self, job="100", run="run"):
        self.put(self.persistent / "RUN.json",
                 dict(run=run, first_job=job, started_utc="2026-11-12T00:00:00Z"))

    def checkpoint(self, step=3):
        self.put(self.run / "binding.json", self.binding)
        checkpoint = self.run / f"checkpoint_{step:06d}"
        (checkpoint / "shards").mkdir(parents=True)
        names = ["replicated.pt", *[f"rng{rank:03d}.pt" for rank in range(4)],
                 *[f"shards/rank{rank:03d}.pt" for rank in range(4)]]
        files = {}
        for name in names:
            payload = (name+" unit fixture").encode()
            (checkpoint / name).write_bytes(payload)
            files[name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        self.put(checkpoint / "complete.json",
                 dict(schema="c1-checkpoint-v1", binding=self.binding, step=step, files=files))
        return checkpoint

    def slot(self, step=3, verified=True):
        payload = b"unit slot attestation fixture"
        (self.persistent / "A.tar").write_bytes(payload)
        (self.persistent / "A.sha256").write_text(hashlib.sha256(payload).hexdigest()+"  A.tar\n")
        self.put(self.persistent / "A.json",
                 dict(slot="A", step=step, verified=verified, job="100", bytes=len(payload)))
        self.put(self.persistent / "binding.json", self.binding)
        digest = hashlib.sha256((self.persistent / "binding.json").read_bytes()).hexdigest()
        (self.persistent / "binding.json.sha256").write_text(digest+"\n")

    def choose(self, job="101"):
        return subprocess.run([sys.executable, "-I", str(self.chooser), str(self.run),
                               "--kit", str(self.kit)],
                              env={**os.environ, "SLURM_JOB_ID": job},
                              capture_output=True, text=True, timeout=15)

    def test_new_job_with_prior_marker_refuses_cold_start(self):
        self.marker()
        result = self.choose()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cold restart", result.stderr)

    def test_first_job_claims_marker_and_may_start(self):
        result = self.choose("100")
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "t"), result.stderr)
        marker = json.loads((self.persistent / "RUN.json").read_text())
        self.assertEqual((marker["run"], marker["first_job"]), ("run", "100"))
        self.assertEqual(self.choose("100").returncode, 0)
        self.assertNotEqual(self.choose("101").returncode, 0)

    def test_unmarked_persistent_binding_refuses_a_new_first_leg(self):
        self.put(self.persistent / "binding.json", self.binding)
        self.assertNotEqual(self.choose("100").returncode, 0)

    def test_foreign_run_marker_refuses(self):
        self.marker(run="another_run")
        self.assertNotEqual(self.choose("100").returncode, 0)

    def test_restored_native_state_and_verified_slot_resume(self):
        self.marker()
        self.checkpoint()
        self.slot()
        result = self.choose()
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "u"), result.stderr)

    def test_verified_slot_without_restored_state_refuses(self):
        self.marker()
        self.slot()
        self.assertNotEqual(self.choose().returncode, 0)

    def test_unverified_slot_does_not_admit_a_later_job(self):
        self.marker()
        self.checkpoint()
        self.slot(verified=False)
        self.assertNotEqual(self.choose().returncode, 0)

    def test_changed_binding_mirror_refuses(self):
        self.marker()
        self.checkpoint()
        self.slot()
        self.put(self.persistent / "binding.json", {**self.binding, "config_sha256": "c"*64})
        self.assertNotEqual(self.choose().returncode, 0)

    def test_valid_but_foreign_binding_mirror_refuses(self):
        self.marker()
        self.checkpoint()
        self.slot()
        self.put(self.persistent / "binding.json", {**self.binding, "config_sha256": "c"*64})
        digest = hashlib.sha256((self.persistent / "binding.json").read_bytes()).hexdigest()
        (self.persistent / "binding.json.sha256").write_text(digest+"\n")
        self.assertNotEqual(self.choose().returncode, 0)

    def test_stale_local_checkpoint_refuses(self):
        self.marker()
        self.checkpoint(step=2)
        self.slot(step=3)
        self.assertNotEqual(self.choose().returncode, 0)

    def test_corrupt_restored_payload_refuses(self):
        self.marker()
        checkpoint = self.checkpoint()
        self.slot()
        (checkpoint / "rng000.pt").write_bytes(b"changed")
        self.assertNotEqual(self.choose().returncode, 0)

    def test_missing_slurm_identity_refuses_persistent_mode(self):
        self.assertNotEqual(self.choose("").returncode, 0)


if __name__ == "__main__":
    unittest.main()
