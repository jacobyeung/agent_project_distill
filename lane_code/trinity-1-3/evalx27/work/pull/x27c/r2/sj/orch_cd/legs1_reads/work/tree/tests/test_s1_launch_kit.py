import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.rehearsal import ENVIRONMENT


class LaunchKitTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=os.environ["LANE_TEST_OUTPUT"]))
        self.kit = Path(__file__).resolve().parents[1] / "launch_s1"

    def choose(self):
        return subprocess.run([sys.executable, "-I", str(self.kit / "b/r8.py"), str(self.root)],
                              capture_output=True, text=True, timeout=15)

    def test_new_run_chooses_training(self):
        result = self.choose()
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "t"))

    def test_parseable_but_incomplete_checkpoint_never_restarts_cold(self):
        checkpoint = self.root / "checkpoint_incomplete"
        checkpoint.mkdir()
        write(checkpoint / "complete.json", {})
        self.assertNotEqual(self.choose().returncode, 0)

    def test_resume_requires_matching_binding_and_complete_payload_inventory(self):
        binding = dict(config_sha256="a"*64, preparation=dict(path="/fixture", sha256="b"*64),
                       trainer_commit="c"*40, world_size=2)
        write(self.root / "binding.json", binding)
        checkpoint = self.root / "checkpoint_complete"
        checkpoint.mkdir()
        (checkpoint / "shards").mkdir()
        files = {}
        for name in ("replicated.pt", "rng000.pt", "rng001.pt", "shards/rank000.pt", "shards/rank001.pt"):
            path = checkpoint / name
            path.write_bytes(b"fixture")
            files[name] = dict(bytes=path.stat().st_size, sha256=file_pin(path)["sha256"])
        value = dict(schema="c1-checkpoint-v1", binding=binding, step=1, files=files)
        write(checkpoint / "complete.json", value)
        result = self.choose()
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "u"))
        value["binding"] = {**binding, "config_sha256": "d"*64}
        (checkpoint / "complete.json").write_text(json.dumps(value))
        self.assertNotEqual(self.choose().returncode, 0)

    def guard(self):
        spec = importlib.util.spec_from_file_location("s1_test_guard", self.kit / "b/sg.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def gate(self):
        spec = importlib.util.spec_from_file_location("s1_test_gate", self.kit / "b/g.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def local(self, name, value):
        path = self.root / "k" / name
        path.write_text(json.dumps(value))
        return dict(file="k/"+name, sha256=file_pin(path)["sha256"])

    def ready(self, sealed=False, world=8):
        gate = self.gate()
        (self.root / "k").mkdir()
        commit = "c"*40
        if sealed:
            files = {"unit.py": "a"*64}
            tree_sha = gate.digest(files)
            commit = "sha256:"+tree_sha
            archive = dict(path="/fixture/tree.tar", sha256="e"*64)
            code = self.local("7.json", dict(schema="c1-sealed-source-v1", commit=commit,
                              tree_sha256=tree_sha, files=files, archive=archive))
        else:
            code = self.local("7.json", dict(clean=True, commit=commit))
        cfg = dict(world_size=world, recipe=dict(world_size=world, wall_seconds=86400,
                                             stop_before_seconds=3600 if world == 4 else 900,
                                             mix=["pose", "vqa", "pointing", "routing", "mdg"]),
                   trace_program_version="3.14", tool_mode_flag=None,
                   preparation=dict(path="/fixture/receipt.json", sha256="a"*64), streams=dict(vqa="fixture"),
                   code=dict(path="/fixture/7.json", sha256=code["sha256"]))
        review = self.local("review.json", dict(verdict="PASS", reviewer="synthetic-unit-review",
                            config_sha256=gate.identity(cfg), preparation=cfg["preparation"]))
        cfg["admission"] = dict(path="/fixture/review.json", sha256=review["sha256"])
        config_sha = gate.identity(cfg)
        report = self.local("first.json", dict(schema="c1-first-batch-check-v1", ranks=list(range(world)), device="cpu",
                            records=[dict(rank=rank, stream=stream, finite=True)
                                     for rank in range(world) for stream in cfg["recipe"]["mix"]]))
        batch = self.local("batch.json", dict(schema="s1-first-batch-binding-v1", config_sha256=config_sha,
                           source_revision=commit, preparation=cfg["preparation"], streams=cfg["streams"],
                           real_rgb_verified=True, native_full_forward=True, report=report))
        staging = self.local("staging.json", dict(status="PASS", source_revision=commit, config_sha256=config_sha,
                             missing=[], project_community_write_bytes=0))
        if sealed:
            record = self.local("tree.json", dict(trees=dict(trainer=dict(files=files))))
            self.local("0.json", dict(commit=commit, trainer=dict(file="/fixture/tree.tar", sha256=archive["sha256"]),
                                     record=dict(file="/fixture/tree.json", sha256=record["sha256"])))
        else:
            self.local("0.json", dict(commit=commit))
        self.local("4.json", dict(allow_until_utc="2099-11-22T00:00:00Z", source_revision=commit,
                                 modes=["p", "t", "u", "x"]))
        launch = dict(schema="s1-orchard-launch-v1", rehearsal_environment=ENVIRONMENT,
                      status="READY", production_authorized=True, source_revision=commit,
                      config=self.local("config.json", cfg), review=review, first_batch=batch, staging=staging,
                      run_directory="/tmp/jjyeung/okit_fixture/runs/fixture")
        if world == 4:
            launch["persistent_run_root"] = str(self.root / "persistent")
        if sealed:
            value = dict(schema="s1-run-seal-v1", tree_sha256=tree_sha, config_sha256=config_sha, archive=archive)
            launch["source_seal"] = {**value, "sha256": gate.digest(value)}
            launch["archive"] = self.local("archive.json", dict(status="ARCHIVED", durable=True,
                sha256=archive["sha256"], tree_sha256=tree_sha, location="/project/community/unit/tree.tar"))
        self.local("launch.json", launch)
        return gate, launch, cfg

    def test_real_entry_refuses_cpu_mode_and_fixture_rgb(self):
        gate, launch, _ = self.ready()
        gate.check(self.root, {})
        with self.assertRaisesRegex(ValueError, "refuses CPU rehearsal"):
            gate.check(self.root, {ENVIRONMENT: "1"})
        batch = json.loads((self.root / "k/batch.json").read_text())
        batch["real_rgb_verified"] = False
        launch["first_batch"] = self.local("batch.json", batch)
        self.local("launch.json", launch)
        with self.assertRaisesRegex(ValueError, "fixture RGB"):
            gate.check(self.root, {})

    def test_all_eight_ranks_and_native_configuration_binding_are_required(self):
        gate, launch, cfg = self.ready()
        native = __import__("student_pilot.carrier_c1_run", fromlist=["identity"])
        self.assertEqual(gate.identity(cfg), native.identity(cfg))
        report = json.loads((self.root / "k/first.json").read_text())
        report["records"] = [row for row in report["records"] if row["rank"] != 7]
        batch = json.loads((self.root / "k/batch.json").read_text())
        batch["report"] = self.local("first.json", report)
        launch["first_batch"] = self.local("batch.json", batch)
        self.local("launch.json", launch)
        with self.assertRaisesRegex(ValueError, "Every rank"):
            gate.check(self.root, {})

    def test_preparation_authorization_does_not_authorize_training(self):
        gate, launch, _ = self.ready()
        launch.update(status="PREPARATION_ONLY", production_authorized=False)
        self.local("launch.json", launch)
        gate.check(self.root, {}, "p")
        with self.assertRaisesRegex(ValueError, "Launch is blocked"):
            gate.check(self.root, {}, "t")

    def test_world_four_gate_requires_the_checkpoint_transfer_reserve(self):
        gate, launch, cfg = self.ready(sealed=True, world=4)
        gate.check(self.root, {"SLURM_JOB_ID": "100"})
        cfg["recipe"]["stop_before_seconds"] = 900
        launch["config"] = self.local("config.json", cfg)
        self.local("launch.json", launch)
        with self.assertRaisesRegex(ValueError, "slot resources"):
            gate.check(self.root, {})

    def test_world_four_direct_entry_cannot_restart_a_prior_leg(self):
        gate, _, _ = self.ready(sealed=True, world=4)
        gate.check(self.root, {"SLURM_JOB_ID": "100"})
        for mode in ("p", "t", "u"):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "cold restart"):
                gate.check(self.root, {"SLURM_JOB_ID": "101"}, mode)

    def test_sealed_source_requires_its_off_scratch_archive_attestation(self):
        gate, launch, _ = self.ready(sealed=True)
        gate.check(self.root, {})
        archived = json.loads((self.root / "k/archive.json").read_text())
        archived["durable"] = False
        launch["archive"] = self.local("archive.json", archived)
        self.local("launch.json", launch)
        with self.assertRaisesRegex(ValueError, "Off-scratch"):
            gate.check(self.root, {})

    def test_slot_script_is_self_contained_and_syntax_valid(self):
        text = (self.kit / "job.sh").read_text()
        for token in ("--partition=advanced", "--gpus-per-node=4", "--cpus-per-task=48", "--mem=800G", "--time=24:00:00",
                      "--no-requeue", "--signal=B:USR1@3600"):
            self.assertIn(token, text)
        self.assertNotIn("ulimit -f", text)
        self.assertNotIn("PILOT_VENV", text)
        for path in (self.kit / "job.sh", self.kit / "b/r.sh", self.kit / "b/c.sh"):
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_packaged_templates_validate_but_do_not_authorize_execution(self):
        from launch_s1.build import build
        from student_pilot import carrier_c1_run as run
        lane = Path("/scratch/jjyeung/orch_cd/leg_s1_tree")
        pool = Path(os.environ.get("S1_POOL_RECEIPT", lane / "out/pool_admission_audit_v8/receipt.json"))
        if not pool.is_file():
            self.skipTest("The authenticated pool selection is not staged")
        output = self.root / "kit"
        result = build(lane.parent / "orchard_cp2/work/okit_v13", output, file_pin(pool))
        self.assertEqual(result["status"], "BLOCKED")
        key = load(output / "k/1.json")["0"]
        for name in (key+".json", "candidate_1.json", "candidate_2.json"):
            run.validate(load(output / "k" / name))
        inventory = subprocess.run([sys.executable, "-B", str(output / "b/a.py"), str(output), "--build-only"],
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        production = subprocess.run([sys.executable, "-B", str(output / "b/a.py"), str(output)],
                                    capture_output=True, text=True, timeout=30)
        self.assertNotEqual(production.returncode, 0)
        self.assertFalse(load(output / "k/4.json")["modes"])
        with (output / "job.sh").open("a") as stream:
            stream.write("\n")
        changed = subprocess.run([sys.executable, "-B", str(output / "b/a.py"), str(output), "--build-only"],
                                 capture_output=True, text=True, timeout=30)
        self.assertNotEqual(changed.returncode, 0)
        self.assertIn("Kit differs", changed.stderr)

    def test_guard_preserves_success_and_checks_progress_files(self):
        guard = self.guard()
        before = guard.activity(self.root)
        write(self.root / "progress.json", dict(step=1))
        self.assertNotEqual(before, guard.activity(self.root))
        child = subprocess.Popen([sys.executable, "-I", "-c", "pass"], start_new_session=True)
        self.assertEqual(guard.supervise(child, self.root, lambda pid: None), 0)

    def test_invalid_guard_settings_refuse_before_a_child_is_needed(self):
        guard = self.guard()
        for settings in (False, [], dict(idle_seconds=0), dict(checkpoint_grace_seconds=float("inf")),
                         dict(unknown=1)):
            with self.assertRaises(ValueError):
                guard.normalize(settings)

    def test_startup_and_steady_state_have_separate_budgets(self):
        self.assertEqual(self.guard().normalize(), (3600, 1200, 600, 10))

    def test_ordinary_startup_files_do_not_activate_the_short_idle_limit(self):
        guard = self.guard()
        program = ("import sys,time;from pathlib import Path;"
                   "time.sleep(.05);Path(sys.argv[1]).write_text('{}');time.sleep(.2)")
        child = subprocess.Popen([sys.executable, "-I", "-c", program, str(self.root / "binding.json")],
                                 start_new_session=True)
        called = []
        try:
            result = guard.supervise(child, self.root, called.append,
                dict(startup_seconds=2, idle_seconds=.05, checkpoint_grace_seconds=.1, poll_seconds=.02))
            self.assertEqual(result, 0)
            self.assertEqual(called, [])
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=15)

    def test_native_attempt_marker_activates_the_steady_state_limit(self):
        guard = self.guard()
        program = ("import sys,time;from pathlib import Path;"
                   "time.sleep(.05);Path(sys.argv[1]).write_text('{}');time.sleep(300)")
        child = subprocess.Popen([sys.executable, "-I", "-c", program, str(self.root / "attempt_unit.json")],
                                 start_new_session=True)
        called = []
        try:
            result = guard.supervise(child, self.root, called.append,
                dict(startup_seconds=5, idle_seconds=.1, checkpoint_grace_seconds=.1, poll_seconds=.02))
            self.assertEqual(result, 124)
            self.assertEqual(called, [child.pid])
            self.assertIsNotNone(child.poll())
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=15)

    def test_guard_requests_checkpoint_then_stops_only_its_child(self):
        guard = self.guard()
        child = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(300)"],
                                 start_new_session=True)
        called = []
        try:
            result = guard.supervise(child, self.root, called.append,
                                     dict(startup_seconds=.1, idle_seconds=.1,
                                          checkpoint_grace_seconds=.1, poll_seconds=.05))
            self.assertEqual(result, 124)
            self.assertEqual(called, [child.pid])
            self.assertIsNotNone(child.poll())
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=15)


if __name__ == "__main__":
    unittest.main()
