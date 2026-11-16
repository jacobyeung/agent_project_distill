import importlib.util
import os
from pathlib import Path
import socket
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import torch
import torch.distributed as dist

from student_pilot import carrier_c1_run as run
from student_pilot import full_ft
from student_pilot.p3_provenance import digest


class TinyBufferedModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.lm = torch.nn.Linear(2, 2)
        self.auxiliary_heads = torch.nn.ModuleDict({"mdg": torch.nn.BatchNorm1d(2)})
        self.trace_program_version = "3.14"

    def forward(self, value):
        return self.auxiliary_heads["mdg"](self.lm(value))


class CheckpointBufferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=0, world_size=1)

    @classmethod
    def tearDownClass(cls):
        dist.destroy_process_group()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="s1-buffers-", dir=os.environ["TMPDIR"]))
        torch.manual_seed(17)
        self.model = TinyBufferedModel()
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        value = torch.arange(16, dtype=torch.float32).reshape(8, 2)
        self.model(value).square().mean().backward()
        self.optimizer.step()

    def test_checkpoint_restore_preserves_running_statistics(self):
        bound = {"world_size": 1, "test": "native-buffer-roundtrip"}
        pin = run.checkpoint(self.root / "checkpoint", self.model, self.optimizer, bound, 1)
        restored = TinyBufferedModel()
        optimizer = torch.optim.AdamW(restored.parameters(), lr=1e-3)
        self.assertEqual(run.restore(pin, restored, optimizer, bound), 1)
        expected, actual = dict(self.model.named_buffers()), dict(restored.named_buffers())
        self.assertEqual(expected.keys(), actual.keys())
        for name in expected:
            torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=0, msg=name)

    def test_buffers_are_rank_private(self):
        named = full_ft.named_trainable(self.model)
        layout = digest(full_ft.shard_layout(named))
        first = full_ft.write_rank_shard(self.root, 0, named, self.optimizer, layout,
                                        buffers=full_ft.named_buffers(self.model))
        self.model.auxiliary_heads["mdg"].running_mean.add_(3.)
        second = full_ft.write_rank_shard(self.root, 1, named, self.optimizer, layout,
                                         buffers=full_ft.named_buffers(self.model))
        a = torch.load(self.root / first["shard"]["name"], weights_only=True)
        b = torch.load(self.root / second["shard"]["name"], weights_only=True)
        key = "auxiliary_heads.mdg.running_mean"
        torch.testing.assert_close(b["buffers"][key]-a["buffers"][key], torch.full((2,), 3.))
        shared = torch.load(self.root / first["replicated"]["name"], weights_only=True)
        self.assertNotIn("buffers", shared)

    def test_legacy_shard_cannot_initialize_mutable_buffers(self):
        named = full_ft.named_trainable(self.model)
        layout = digest(full_ft.shard_layout(named))
        written = full_ft.write_rank_shard(self.root, 0, named, self.optimizer, layout)
        pins = {value["name"]: {key: entry for key, entry in value.items() if key != "name"}
                for value in written.values()}
        with self.assertRaisesRegex(ValueError, "buffer"):
            full_ft.read_rank_shard(self.root, 0, pins, named, self.optimizer, layout,
                                    buffers=full_ft.named_buffers(self.model))

    def test_disk_headroom_is_checked_before_any_checkpoint_payload(self):
        destination = self.root / "no_space"
        with patch("os.statvfs", return_value=SimpleNamespace(f_bavail=0, f_frsize=4096)):
            with self.assertRaisesRegex(ValueError, "checkpoint disk"):
                run.checkpoint(destination, self.model, self.optimizer, {"world_size": 1}, 1)
        self.assertFalse(destination.exists())

    def test_two_hour_plan_counts_early_signal_and_weight_exports(self):
        from student_pilot.checkpoint_space import plan
        recipe = dict(wall_seconds=86400, stop_before_seconds=3600, resume_every_seconds=7200,
                      milestones=[100, 200], export_at_stop=True)
        self.assertEqual(plan(recipe), dict(reserve_bytes=200_000_000_000, planned_full_states=14,
                                           extra_full_states=2, planned_weight_exports=3))

    def test_whole_leg_guard_does_not_admit_space_for_only_one_state(self):
        policy = dict(reserve_bytes=0, planned_full_states=14, extra_full_states=2, planned_weight_exports=3)
        destination = self.root / "one_state_only"
        with patch("os.statvfs", return_value=SimpleNamespace(f_bavail=200*1024**2, f_frsize=1)):
            with self.assertRaisesRegex(ValueError, "Insufficient checkpoint disk space"):
                run.checkpoint(destination, self.model, self.optimizer, {"world_size": 1}, 1, disk_guard=policy)
        self.assertFalse(destination.exists())

    def test_whole_leg_budget_counts_measured_states_and_exports(self):
        from student_pilot.checkpoint_space import Budget, check
        policy = dict(reserve_bytes=123, planned_full_states=2, extra_full_states=2, planned_weight_exports=3)
        budget = Budget(policy)
        measured = check(self.root, full_ft.named_trainable(self.model), self.optimizer,
                         full_ft.named_buffers(self.model), 0, 1, budget)
        self.assertEqual(measured["required_bytes"], 4*measured["state_bytes"]+3*measured["export_bytes"]+123)
        self.assertEqual(measured["remaining_full_states"], 4)
        self.assertEqual(measured["remaining_weight_exports"], 3)
        self.assertGreater(measured["state_tensor_bytes"], 0)
        self.assertGreater(measured["export_tensor_bytes"], 0)
        marker = run.checkpoint(self.root / "budgeted", self.model, self.optimizer, {"world_size": 1}, 1,
                                disk_guard=budget)
        from student_pilot.p3_provenance import load, pinned
        complete = load(pinned(marker))
        self.assertEqual(complete["disk_guard"]["serialized_state_bytes"],
                         sum(value["bytes"] for value in complete["files"].values()))
        later = check(self.root, full_ft.named_trainable(self.model), self.optimizer,
                      full_ft.named_buffers(self.model), 0, 1, budget)
        self.assertEqual(later["remaining_full_states"], 3)
        self.assertEqual(policy, dict(reserve_bytes=123, planned_full_states=2,
                                     extra_full_states=2, planned_weight_exports=3))

    def test_export_disk_guard_precedes_publication_and_payloads(self):
        destination = self.root / "export_without_space"
        with patch("os.statvfs", return_value=SimpleNamespace(f_bavail=0, f_frsize=4096)):
            with patch("student_pilot.fsdp_training.publication_state") as publication:
                with self.assertRaisesRegex(ValueError, "Insufficient export disk space"):
                    run.export(destination, self.model, self.model, {"trace_program_version": "3.14"}, 1,
                               optimizer=self.optimizer)
                publication.assert_not_called()
        self.assertFalse(destination.exists())

    def test_default_stall_budget_covers_native_startup(self):
        path = Path(__file__).resolve().parents[1] / "launch_s1/b/sg.py"
        spec = importlib.util.spec_from_file_location("s1_startup_guard", path)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        self.assertGreaterEqual(guard.normalize()[0], 3600)


if __name__ == "__main__":
    unittest.main()
