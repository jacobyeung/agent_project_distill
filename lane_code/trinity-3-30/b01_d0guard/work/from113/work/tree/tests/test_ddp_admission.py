import copy
import os
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch

from student_pilot import ddp_admission, ddp_config, provisional, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class RankAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ddp_admission_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.coord = self.root / "coord"
        self.now = datetime.now(timezone.utc)
        settings = ddp_config.normalize_training_config({"world_size": 2}, "onethinker")
        self.protocol = self.document("protocol.json", provisional.tag({"student": "onethinker", "training": settings,
            "protocol_version": ddp_config.VERSION, "training_sha256": digest_json(settings)}, LABEL))
        self.manifest = self.document("training.json", provisional.tag({"protocol": binding(self.protocol)}, LABEL))
        self.request = ddp_admission.request_identity(self.manifest, self.protocol, LABEL, "onethinker", 2)
        self.request_path = self.document("request.json", self.request)
        self.paths = []
        self.evidence = []
        for rank, request in enumerate(self.request["ranks"]):
            evidence = self.document(f"coord/LEASES/{request['work_id']}.lock/lease.json", {
                "work_id": request["work_id"], "status": "running", "agent_id": "fixture", "host": "trinity-0-18",
                "last_heartbeat": self.now.isoformat()})
            self.evidence.append(evidence)
            self.paths.append(self.document(f"supervisor{rank}.json", {
                "host": "trinity-0-18", "gpu_index": rank + 2, "owner": "fixture", "work_id": request["work_id"],
                "protocol_sha256": request["protocol_sha256"], "ownership_check_passed": True,
                "coordination_lease_passed": True, "vnice_wrapped": True, "coordination_lease_evidence": str(evidence),
                "ownership_checked_at": self.now.isoformat(), "expires_at": (self.now + timedelta(hours=1)).isoformat()}))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(provisional.socket, "gethostname", return_value="trinity-0-18.example"))
        self.stack.enter_context(patch.object(provisional, "gpu_uuid", side_effect=lambda index: f"GPU-00000000-0000-0000-0000-{index:012x}"))
        self.stack.enter_context(patch.object(storage, "code_provenance", return_value={"commit": "c" * 40, "dirty": False,
                                                                                     "config_sha256": "a" * 64}))
        self.bundle_path = self.root / "leases.json"
        ddp_admission.bind_leases(self.paths, self.request_path, self.bundle_path, LABEL, coord_root=self.coord)
        self.bundle = ddp_admission.load_bundle(self.bundle_path, self.request, LABEL, self.coord)
        self.lease = self.bundle["ranks"][0]
        self.stack.enter_context(patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": self.lease["gpu_uuid"]}))
        self.stack.enter_context(patch.object(torch.cuda, "is_available", return_value=True))
        self.stack.enter_context(patch.object(torch.cuda, "device_count", return_value=1))
        self.stack.enter_context(patch.object(torch.cuda, "is_bf16_supported", return_value=True))
        self.properties = self.stack.enter_context(patch.object(torch.cuda, "get_device_properties",
                                                               return_value=SimpleNamespace(uuid=self.lease["gpu_uuid"])))
        self.select = self.stack.enter_context(patch.object(torch.cuda, "set_device"))
        self.stack.enter_context(patch.object(torch.cuda, "reset_peak_memory_stats"))
        self.compute = self.stack.enter_context(patch.object(provisional.subprocess, "run", return_value=SimpleNamespace(stdout="")))

    def document(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(value))
        return path

    def admit(self):
        return ddp_admission.admitted_rank(self.lease, LABEL, self.request["ranks"][0], self.coord)

    def change_evidence(self, **values):
        value = load_json(self.evidence[0])
        self.evidence[0].write_bytes(canonical_bytes({**value, **values}))

    def test_actual_cuda_uuid_and_live_probe_are_recorded_per_rank(self):
        for rank in range(2):
            self.lease = self.bundle["ranks"][rank]
            self.properties.return_value.uuid = self.lease["gpu_uuid"]
            with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": self.lease["gpu_uuid"]}):
                result = ddp_admission.admitted_rank(self.lease, LABEL, self.request["ranks"][rank], self.coord)
            probe = result["admission_probe"]
            self.assertEqual(probe["cuda_device_uuid"], result["gpu_uuid"])
            self.assertEqual(probe["cuda_device_ordinal"], 0)
            self.assertEqual(probe["compute_pids"], [])
            self.assertLess(probe["heartbeat_age_seconds"], 300)
            self.assertIn("probed_at", probe)
            self.assertNotIn("admission_probe", self.bundle["ranks"][rank])

    def test_effective_allocator_setting_is_persisted_in_run_json_per_rank(self):
        from student_pilot import ddp_training

        for index, configured in enumerate((None, "", "expandable_segments:True", "expandable_segments:False,max_sp" "lit_size_mb:128")):
            with self.subTest(configured=configured), patch.dict(os.environ):
                os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)
                if configured is not None:
                    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = configured
                probes = []
                for rank, lease in enumerate(self.bundle["ranks"]):
                    self.properties.return_value.uuid = lease["gpu_uuid"]
                    with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=lease["gpu_uuid"]):
                        admitted = ddp_admission.admitted_rank(lease, LABEL, self.request["ranks"][rank], self.coord)
                    probes.append({"lease": admitted, "error": None})
                store = SimpleNamespace(record=lambda value: value,
                    write=lambda name, value: self.document(f"allocator_run{index}/{name}", value))
                with patch.object(torch.distributed, "broadcast_object_list"), patch.object(torch.distributed, "barrier"):
                    ddp_training.persist_admission(0, probes, store, {"lease": {"ranks": []}})
                header = load_json(self.root / f"allocator_run{index}/run.json")
                for lease in header["lease"]["ranks"]:
                    self.assertEqual(lease["admission_probe"]["pytorch_cuda_alloc_conf"], configured or "")
                    self.assertEqual(lease["admission_probe"]["cuda_visible_devices"], lease["gpu_uuid"])

    def test_torch_cuda_uuid_objects_are_normalized(self):
        class TorchUUID:
            def __init__(self, value):
                self.value = value

            def __str__(self):
                return self.value

        expected = self.lease["gpu_uuid"]
        for raw in (expected, expected.removeprefix("GPU-")):
            value = TorchUUID(raw)
            self.properties.return_value.uuid = value
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "^Physical GPU UUID is missing or malformed$"):
                    provisional.physical_uuid(value)
                self.assertEqual(self.admit()["admission_probe"]["cuda_device_uuid"], expected)

    def test_cuda_management_enumeration_mismatch_refuses(self):
        self.properties.return_value.uuid = "GPU-different-CUDA-order"
        with self.assertRaisesRegex(ValueError, "CUDA-visible device UUID"):
            self.admit()
        self.select.assert_not_called()

    def test_missing_or_malformed_cuda_uuid_refuses_without_index_fallback(self):
        for properties in (SimpleNamespace(), SimpleNamespace(uuid=None), SimpleNamespace(uuid=""),
                           SimpleNamespace(uuid="garbage")):
            self.properties.return_value = properties
            with self.subTest(properties=properties), self.assertRaisesRegex(ValueError,
                    "^CUDA-visible device UUID is missing or malformed$"):
                self.admit()
        self.select.assert_not_called()

    def test_foreign_compute_pid_refuses(self):
        self.compute.return_value.stdout = f"{os.getpid() + 1000000}, 1024\n"
        with self.assertRaisesRegex(ValueError, "foreign compute PID"):
            self.admit()
        self.select.assert_not_called()

    def test_current_process_is_the_only_permitted_compute_pid(self):
        self.compute.return_value.stdout = f"{os.getpid()}, 32\n"
        self.assertEqual(self.admit()["admission_probe"]["compute_pids"], [os.getpid()])

    def test_stale_or_future_coordination_heartbeat_refuses(self):
        for seconds in (-301, 600):
            self.change_evidence(last_heartbeat=(self.now + timedelta(seconds=seconds)).isoformat())
            with self.subTest(seconds=seconds), self.assertRaisesRegex(ValueError, "heartbeat"):
                self.admit()

    def test_expired_lease_refuses(self):
        self.lease["expires_at"] = (self.now - timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError, "expired"):
            self.admit()

    def test_fresh_entry_remains_strict_but_post_staging_probe_can_be_late(self):
        self.lease["ownership_checked_at"] = (self.now - timedelta(seconds=600)).isoformat()
        with self.assertRaisesRegex(ValueError, "older than five minutes"):
            ddp_admission.require_rank_lease(self.lease, LABEL, self.request["ranks"][0], coord_root=self.coord)
        self.assertEqual(self.admit()["admission_probe"]["gpu_uuid"], self.lease["gpu_uuid"])

    def test_heartbeat_and_owner_are_rechecked_after_the_live_probe(self):
        def stale(*args, **kwargs):
            self.change_evidence(last_heartbeat=(self.now - timedelta(seconds=600)).isoformat())
            return SimpleNamespace(stdout="")
        self.compute.side_effect = stale
        with self.assertRaisesRegex(ValueError, "heartbeat"):
            self.admit()
        self.change_evidence(last_heartbeat=self.now.isoformat())
        def moved(*args, **kwargs):
            self.change_evidence(agent_id="foreign-owner")
            return SimpleNamespace(stdout="")
        self.compute.side_effect = moved
        with self.assertRaisesRegex(ValueError, "owner/state/host"):
            self.admit()

    def test_supplied_or_prior_successful_probe_cannot_bypass_new_occupancy(self):
        self.lease["admission_probe"] = {"gpu_uuid": "forged", "compute_pids": []}
        self.assertEqual(self.admit()["admission_probe"]["gpu_uuid"], self.lease["gpu_uuid"])
        self.compute.return_value.stdout = "123456789, 256\n"
        with self.assertRaisesRegex(ValueError, "foreign compute PID"):
            self.admit()

    def test_duplicate_gpu_and_cross_rank_work_identity_refuse(self):
        for key in ("gpu_uuid", "gpu_index", "work_id", "protocol_sha256"):
            ranks = copy.deepcopy(self.bundle["ranks"])
            ranks[1][key] = ranks[0][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                ddp_admission.validate_rank_list(ranks, self.request, LABEL, self.coord)

    def test_torchrun_selects_the_rank_uuid_before_cuda_initialization(self):
        environment = {"RANK": "1", "LOCAL_RANK": "1", "WORLD_SIZE": "2", "LOCAL_WORLD_SIZE": "2",
                       "GROUP_RANK": "0", "TORCHELASTIC_RESTART_COUNT": "0", "CUDA_VISIBLE_DEVICES": "2,3"}
        with patch.dict(os.environ, environment), patch.object(torch.cuda, "is_initialized", return_value=False):
            self.assertEqual(ddp_admission.select_rank(self.bundle), (1, 2, "2,3"))
            self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "GPU-00000000-0000-0000-0000-000000000003")
        with patch.dict(os.environ, environment), patch.object(torch.cuda, "is_initialized", return_value=True):
            with self.assertRaisesRegex(ValueError, "before CUDA"):
                ddp_admission.select_rank(self.bundle)
        for values in ({"LOCAL_WORLD_SIZE": "1"}, {"CUDA_VISIBLE_DEVICES": "3,2"}, {"TORCHELASTIC_RESTART_COUNT": "1"}):
            with patch.dict(os.environ, {**environment, **values}), self.assertRaises(ValueError):
                ddp_admission.select_rank(self.bundle)

    def test_changed_protocol_and_mixed_labels_refuse(self):
        changed = copy.deepcopy(self.request)
        changed["protocol_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            ddp_admission.load_bundle(self.bundle_path, changed, LABEL, self.coord)
        for label in (None, provisional.LABELS[1]):
            with self.subTest(label=label), self.assertRaises(ValueError):
                ddp_admission.load_bundle(self.bundle_path, self.request, label, self.coord)

    def test_probe_failures_and_malformed_pid_output_fail_closed(self):
        self.compute.side_effect = OSError("synthetic probe unavailable")
        with self.assertRaises(OSError):
            self.admit()
        self.compute.side_effect = None
        for text in ("not-a-pid, 100\n", "1, 2, 3\n"):
            self.compute.return_value.stdout = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.admit()


if __name__ == "__main__":
    unittest.main()
