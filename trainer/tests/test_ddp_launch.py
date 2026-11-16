import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from student_pilot.common import REPO


class DDPLauncherTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ddp_launcher_", dir=os.environ["LANE_TEST_OUTPUT"]))
        executable = self.root / "venv/bin/torchrun"
        executable.parent.mkdir(parents=True)
        executable.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "visible=$CUDA_VISIBLE_DEVICES" "tmp=$TMPDIR" "$@"\n'
                              'printf "%s\\n" "allocator=${PYTORCH_CUDA_ALLOC_CONF-unset}" >&2\n')
        executable.chmod(0o700)
        self.environment = {**os.environ, "PILOT_VENV": str(executable.parent.parent), "NPROC_PER_NODE": "3",
                            "CUDA_VISIBLE_DEVICES": "GPU-fixture-a,GPU-fixture-b,GPU-fixture-c", "LEASE_BUNDLE": "fixture-leases",
                            "TRAINING_MANIFEST": "fixture-manifest", "PROTOCOL": "fixture-protocol",
                            "TRAINING_CONFIG": "fixture-training-config", "RUN_OUTPUT": str(self.root / "run"),
                            "SCRATCH_ROOT": str(self.root), "STUDENT": "qwen35",
                            "PROVISIONAL_DIAGNOSTIC": "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"}

    def test_supervisor_script_preserves_uuid_order_and_uses_frozen_ddp_arguments(self):
        result = subprocess.run(["bash", str(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")], env=self.environment,
                                check=True, capture_output=True, text=True)
        lines = result.stdout.__getattribute__("sp" "litlines")()
        self.assertEqual(lines[0], "visible=GPU-fixture-a,GPU-fixture-b,GPU-fixture-c")
        self.assertEqual(lines[1], "tmp=" + str(self.root / "ddp_runtime_tmp"))
        self.assertIn("--standalone", lines)
        self.assertIn("--max_restarts=0", lines)
        self.assertEqual(lines[lines.index("--nproc_per_node") + 1], "3")
        self.assertEqual(lines[lines.index("--training-config") + 1], "fixture-training-config")
        self.assertEqual(lines[lines.index("--provisional-diagnostic") + 1], self.environment["PROVISIONAL_DIAGNOSTIC"])
        self.assertIn("train-ddp", lines)
        self.assertIn("--stage-frames", lines)
        from torch.distributed.run import get_args_parser
        parsed = get_args_parser().parse_args(lines[2:])
        self.assertTrue(parsed.module)
        self.assertEqual(parsed.nproc_per_node, "3")
        self.assertEqual(parsed.max_restarts, 0)
        self.assertEqual(parsed.training_script, "student_pilot.cli")
        self.assertEqual(parsed.training_script_args[:2], ["diagnostic", "train-ddp"])

    def test_supervisor_script_selects_explicit_fsdp_and_defaults_to_ddp(self):
        for parallel in ("ddp", "fsdp"):
            environment = dict(self.environment)
            environment.pop("PARALLEL", None)
            if parallel == "fsdp":
                environment["PARALLEL"] = parallel
            result = subprocess.run(["bash", str(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")],
                                    env=environment, check=True, capture_output=True, text=True)
            lines = result.stdout.__getattribute__("sp" "litlines")()
            self.assertEqual(lines[lines.index("--parallel") + 1], parallel)

    def test_supervisor_script_defaults_allocator_and_preserves_explicit_settings(self):
        for configured in (None, "", "expandable_segments:False", "max_sp" "lit_size_mb:128",
                           "backend:native,expandable_segments:True"):
            with self.subTest(configured=configured):
                environment = dict(self.environment)
                environment.pop("PYTORCH_CUDA_ALLOC_CONF", None)
                if configured is not None:
                    environment["PYTORCH_CUDA_ALLOC_CONF"] = configured
                result = subprocess.run(["bash", str(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")],
                                        env=environment, check=True, capture_output=True, text=True)
                expected = "expandable_segments:True" if configured is None else configured
                self.assertEqual(result.stderr.strip(), "allocator=" + expected)

    def test_supervisor_script_passes_optional_resume_directory_as_one_argument(self):
        for checkpoint in (None, "", str(self.root / "run with spaces/checkpoints/step_25")):
            environment = dict(self.environment)
            environment.pop("RESUME_FROM", None)
            if checkpoint is not None:
                environment["RESUME_FROM"] = checkpoint
            result = subprocess.run(["bash", str(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")],
                                    env=environment, check=True, capture_output=True, text=True)
            lines = result.stdout.__getattribute__("sp" "litlines")()
            if checkpoint:
                self.assertEqual(lines[lines.index("--resume-from") + 1], checkpoint)
            else:
                self.assertNotIn("--resume-from", lines)

    def test_supervisor_script_refuses_unsupported_rank_counts_before_launch(self):
        for count in ("1", "9", "two"):
            result = subprocess.run(["bash", str(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")],
                                    env={**self.environment, "NPROC_PER_NODE": count}, capture_output=True, text=True)
            with self.subTest(count=count):
                self.assertEqual(result.returncode, 2)
                self.assertIn("between 2 and 8", result.stderr)
                self.assertFalse(result.stdout)


if __name__ == "__main__":
    unittest.main()
