import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ProductionImportTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="production_import_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.source = Path(__file__).resolve().parents[1]
        self.root = self.base / "kit"
        shutil.copytree(self.source / "launch_s1/b", self.root / "b")
        self.closure = self.base / "closure"
        shutil.copytree(self.root / "b/sa", self.closure / "site_alias")
        for name in ("kit/k", "kit/o", "empty", "np", "fla", "epochs/fixture"):
            (self.base / name).mkdir(parents=True, exist_ok=True)
        pin = dict(path="/unavailable/input", sha256="a"*64)
        cfg = dict(training_mode="final", world_size=4, recipe=dict(world_size=4),
                   streams={key: pin for key in ("pose", "vqa", "pointing", "routing")},
                   depth_init=pin, preparation=pin)
        auth = dict(arm=["0"], source_revision="fixture", modes=["p", "t", "u"],
                    allow_until_utc="2099-11-26T00:00:00Z", new_gpus=dict(p=0, t=4, u=4),
                    other_running_and_pending_gpus=0, gpu_cap=4, resume="latest")
        for name, value in (("0", dict(commit="fixture")), ("1", {"0": "config"}),
                            ("4", auth), ("config", cfg)):
            (self.root / "k" / (name+".json")).write_text(json.dumps(value))
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(("PYTHON", "S1_", "SLURM_"))}
        self.environment.update(PYTHONPATH=":".join(map(str, (self.root / "b", self.closure,
                                                           self.closure / "site_alias"))),
                                PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                                CUDA_VISIBLE_DEVICES="", SLURM_JOB_ID="123456",
                                SLURM_JOB_NUM_NODES="1", SLURM_GPUS_ON_NODE="4",
                                TRAINER=str(self.base / "epochs/fixture"))

    def run_python(self, arguments, environment=None, cwd=None):
        return subprocess.run([sys.executable, "-B", *arguments], capture_output=True, text=True,
                              cwd=cwd or self.base / "empty", env=environment or self.environment, timeout=30)

    def test_authorize_all_production_modes_without_importing_the_trainer(self):
        for mode in ("p", "t", "u"):
            for overlays in (False, True):
                with self.subTest(mode=mode, overlays=overlays):
                    env = dict(self.environment)
                    if overlays:
                        env["PYTHONPATH"] = ":".join((str(self.base / "fla"), str(self.base / "np"),
                                                    env["PYTHONPATH"]))
                    code = ("import importlib.util,pathlib,sys; "
                            "assert importlib.util.find_spec('student_pilot') is None; "
                            "from i import authorize; "
                            "authorize(pathlib.Path(sys.argv[1]),sys.argv[2],'0'); "
                            "assert 'student_pilot' not in sys.modules")
                    result = self.run_python(["-c", code, str(self.root), mode], env)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_supervisor_reaches_worker_tree_boundary_without_rehearsal_import(self):
        result = self.run_python([str(self.root / "b/i.py"), str(self.root), "p", "0"])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("No module named 'student_pilot'", result.stderr)
        self.assertIn("KeyError: 'record'", result.stderr)

    def test_worker_reaches_tree_boundary_from_neutral_and_kit_directories(self):
        for cwd in (self.base / "empty", self.root):
            with self.subTest(cwd=str(cwd)):
                result = self.run_python([str(self.root / "b/w.py"), str(self.root), "p", "0"], cwd=cwd)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("No module named 'student_pilot'", result.stderr)
                self.assertIn("KeyError: 'record'", result.stderr)

    def test_invalid_switch_refuses_without_importing_the_trainer(self):
        env = {**self.environment, "S1_CPU_REHEARSAL": "invalid"}
        result = self.run_python([str(self.root / "b/i.py"), str(self.root), "p", "0"], env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("S1_CPU_REHEARSAL must be 0 or 1", result.stderr)
        self.assertNotIn("No module named 'student_pilot'", result.stderr)

    def test_production_gate_refuses_the_rehearsal_switch_without_a_trainer(self):
        launch = dict(schema="s1-orchard-launch-v1", rehearsal_environment="S1_CPU_REHEARSAL")
        (self.root / "k/launch.json").write_text(json.dumps(launch))
        result = self.run_python([str(self.root / "b/g.py"), str(self.root), "p"],
                                 {**self.environment, "S1_CPU_REHEARSAL": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refuses CPU rehearsal", result.stderr)

    def test_supervisor_refuses_non_numeric_allocation_without_a_trainer(self):
        result = self.run_python([str(self.root / "b/i.py"), str(self.root), "p", "0"],
                                 {**self.environment, "SLURM_JOB_ID": "not-an-allocation"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Allocation absent", result.stderr)

    def test_metadata_preflight_runs_native_authorization_without_persistent_state(self):
        result = self.run_python([str(self.root / "b/p0.py"), str(self.root), "p", "--metadata-only"])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.root / "o/123456.preflight.metadata.p.json").read_text())
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["trainer_initially_visible"])
        self.assertFalse(report["persistent_marker_written"])
        self.assertFalse(report["training_executed"])
        self.assertFalse(any(self.base.rglob("RUN*.json")))
        self.assertFalse(any(name.startswith("student_pilot") for name in report["module_origins"]))

    def test_metadata_preflight_refuses_a_source_directory_that_hides_import_errors(self):
        foreign = self.base / "foreign"
        (foreign / "student_pilot").mkdir(parents=True)
        (foreign / "student_pilot/__init__.py").write_text("raise AssertionError('must not execute')\n")
        env = {**self.environment, "PYTHONPATH": str(foreign)+":"+self.environment["PYTHONPATH"]}
        result = self.run_python([str(self.root / "b/p0.py"), str(self.root), "p", "--metadata-only"], env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("visible before source authentication", result.stderr)
        self.assertNotIn("must not execute", result.stderr)

    def test_metadata_preflight_refuses_rehearsal_without_bulk_staging(self):
        env = {**self.environment, "S1_CPU_REHEARSAL": "1"}
        result = self.run_python([str(self.root / "b/p0.py"), str(self.root), "p", "--metadata-only"], env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Production preflight refuses CPU rehearsal", result.stderr)

    def test_preflight_cannot_be_selected_through_a_worker_cli_argument(self):
        for script in ("i.py", "w.py"):
            result = self.run_python([str(self.root / "b" / script), str(self.root), "p", "0", "--preflight"])
            self.assertNotEqual(result.returncode, 0, script)
            self.assertNotIn("KeyError: 'record'", result.stderr)

    def test_preflight_precedes_persistent_state_and_bulk_payloads(self):
        for name in ("job.sh", "job8.sh"):
            script = (self.source / "launch_s1" / name).read_text()
            self.assertLess(script.index('b/p0.sh'), script.index('b/g.py'))
            self.assertLess(script.index('b/p0.sh'), script.index('b/r8.py'))
        stage = (self.source / "launch_s1/b/c.sh").read_text().split("tk_stage() {", 1)[1]
        self.assertLess(stage.index('"$mode" == preflight'), stage.index("\n    tk_stage_model"))
        self.assertLess(stage.index('"$mode" == preflight'), stage.index("\n    tk_stage_extra"))
        result = subprocess.run(["/bin/bash", "-n", str(self.source / "launch_s1/b/p0.sh")],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
