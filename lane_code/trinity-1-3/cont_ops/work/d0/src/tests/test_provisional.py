import ast
import copy
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import Mock, patch

from student_pilot import conversion, lease, division, storage
from student_pilot.common import REPO, binding, canonical_bytes, digest_json, load_json
from student_pilot import provisional


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


class ProvisionalTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ["LANE_TEST_OUTPUT"])
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="provisional_", dir=root))

    def document(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(value))
        return path

    def candidates(self, count=20):
        frame = self.root / "frame.bin"
        frame.write_bytes(b"synthetic RGB fixture")
        entries = []
        for index in range(count):
            qid = f"candidate_{index:04d}"
            row = {"qid": qid, "dataset": "scannet", "scene": f"scene{index // 2:04d}_{index % 2:02d}",
                   "category": "object_counting", "target": "Synthetic evidence. <answer>2</answer>",
                   "generation_commit": "a" * 40, "validation_commit": "b" * 40,
                   "student_input": {"question": "Synthetic count?", "options": None,
                                     "frames": [binding(frame)] * 32, "frame_indices": list(range(32)),
                                     "timestamps": [i / 2 for i in range(32)], "fps": 2.0, "total_num_frames": 32}}
            row_path = self.document(f"{qid}/row.json", row)
            target = row_path.with_name("target.txt")
            target.write_text(row["target"] + "\n")
            entries.append({"qid": qid, "dataset": row["dataset"], "scene": row["scene"],
                            "question_type": row["category"], "answer": "2", "pool": "synthetic",
                            "target_path": str(target), "sha256": binding(target)["sha256"],
                            "row_path": str(row_path), "row_sha256": binding(row_path)["sha256"],
                            "generation_commit": row["generation_commit"], "validation_commit": row["validation_commit"]})
        return self.index(entries), entries

    def index(self, entries, name="candidate_index.jsonl"):
        path = self.root / name
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in entries))
        return path

    def test_loader_preserves_target_and_labels_index_and_container(self):
        index, entries = self.candidates()
        rows = provisional.load_provisional_candidates(index, LABEL)
        container = self.document("manifest.json", {"schema": "zero-call-diagnostic-candidates-v3",
                                  "admission_verdict": LABEL, "candidate_index": binding(index), "candidate_rows": entries})
        self.assertEqual(rows, provisional.load_provisional_candidates(container, LABEL))
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(row["provisional_diagnostic"] == LABEL for row in rows))
        self.assertIsNone(rows[0]["student_input"]["options"])
        self.assertEqual(rows[0]["target"], load_json(entries[0]["row_path"])["target"])

    def test_loader_rejects_hash_drift_malformed_rows_and_label_drift(self):
        index, entries = self.candidates(2)
        for field in ("sha256", "row_sha256"):
            bad = copy.deepcopy(entries)
            bad[0][field] = "0" * 64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "[Hh]ash|SHA256"):
                provisional.load_provisional_candidates(self.index(bad, field + ".jsonl"), LABEL)
        row = load_json(entries[0]["row_path"])
        row["student_input"]["frames"] = row["student_input"]["frames"][:31]
        self.document("bad-row.json", row)
        bad = copy.deepcopy(entries)
        bad[0].update(row_path=str(self.root / "bad-row.json"), row_sha256=binding(self.root / "bad-row.json")["sha256"])
        with self.assertRaises(ValueError):
            provisional.load_provisional_candidates(self.index(bad, "bad.jsonl"), LABEL)
        with self.assertRaises(ValueError):
            provisional.load_provisional_candidates(index, "UNREVIEWED")
        container = self.document("wrong-label.json", {"schema": "zero-call-diagnostic-candidates-v3",
                                  "admission_verdict": provisional.LABELS[1], "candidate_index": binding(index)})
        with self.assertRaises(ValueError):
            provisional.load_provisional_candidates(container, LABEL)

    def test_external_row_label_mismatch_is_refused(self):
        _, entries = self.candidates(2)
        original = load_json(entries[0]["row_path"])
        for declared in provisional.LABELS:
            row = {**original, "provisional_diagnostic": declared}
            path = self.document(f"row_{declared}.json", row)
            for requested in provisional.LABELS:
                entry = {**entries[0], "row_path": str(path), "row_sha256": binding(path)["sha256"],
                         "provisional_diagnostic": requested}
                index = self.index([entry], f"index_{declared}_{requested}.jsonl")
                with self.subTest(declared=declared, requested=requested):
                    if declared == requested:
                        loaded = provisional.load_provisional_candidates(index, requested)
                        self.assertEqual(loaded[0]["provisional_diagnostic"], declared)
                        self.assertEqual(loaded[0]["target"], original["target"])
                    else:
                        with self.assertRaisesRegex(ValueError, "label") as refused:
                            provisional.load_provisional_candidates(index, requested)
                        self.assertEqual(type(refused.exception).__name__, "ProvisionalLabelMismatchError")

    def test_loader_rejects_input_extras_duplicate_ids_and_temporal_drift(self):
        index, entries = self.candidates(2)
        with self.assertRaises(ValueError):
            provisional.load_provisional_candidates(self.index(entries + [entries[0]], "duplicates.jsonl"), LABEL)
        original = load_json(entries[0]["row_path"])
        for name, value in (("target", "leaked"), ("total_num_frames", 4), ("timestamps", [0] * 32)):
            row = copy.deepcopy(original)
            row["student_input"][name] = value
            path = self.document(name + ".json", row)
            bad = [{**entries[0], "row_path": str(path), "row_sha256": binding(path)["sha256"]}]
            with self.subTest(field=name), self.assertRaises(ValueError):
                provisional.load_provisional_candidates(self.index(bad, name + ".jsonl"), LABEL)

    def baseline_function(self, module, name):
        source = subprocess.run(["git", "show", f"a633dc6:{Path(module.__file__).relative_to(REPO)}"],
                                cwd=REPO, check=True, capture_output=True, text=True).stdout
        function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name)
        namespace = dict(module.__dict__)
        exec(compile(ast.Module(body=[function], type_ignores=[]), "clean_baseline", "exec"), namespace)
        return namespace[name]

    def test_clean_manifest_and_fixed_lease_are_byte_identical(self):
        run = self.document("clean/run.json", {"fixture": "run"})
        review = self.document("clean/review.json", {"fixture": "review"})
        manifest = {"schema": "accepted-grounded-detailed-targets-v1", "run": binding(run), "review": binding(review),
                    "rows": [{"qid": "clean-fixture", "target": "accepted fixture"}]}
        path = self.document("clean/accepted.json", manifest)
        with patch.object(conversion, "accepted_manifest", return_value=manifest):
            original = self.baseline_function(conversion, "load_accepted")
            self.assertEqual(canonical_bytes(original(path)), canonical_bytes(conversion.load_accepted(path)))
        now = datetime.now(timezone.utc)
        fixed = {"host": "trinity-1-8", "gpu_index": 1, "owner": "fixture", "work_id": "fixture",
                 "ownership_check_passed": True, "coordination_lease_passed": True, "vnice_wrapped": True,
                 "coordination_lease_evidence": "fixture", "ownership_checked_at": now.isoformat(),
                 "expires_at": (now + timedelta(minutes=10)).isoformat()}
        original = self.baseline_function(lease, "check_lease")
        self.assertEqual(canonical_bytes(original(fixed, "trinity-1-8", "1", now)),
                         canonical_bytes(lease.check_lease(fixed, "trinity-1-8", "1", now)))
        for hostname, device in (("trinity-0-18", "1"), ("trinity-1-8", "3")):
            for check in (original, lease.check_lease):
                with self.assertRaises(ValueError):
                    check(fixed, hostname, device, now)
        index, _ = self.candidates()
        rows = provisional.load_provisional_candidates(index, LABEL)
        original_division = self.baseline_function(division, "make_division")
        self.assertEqual(canonical_bytes(original_division(rows, rows)), canonical_bytes(division.make_division(rows, rows)))

    def test_provisional_division_keeps_repeat_scans_together_and_records_digest(self):
        index, _ = self.candidates()
        rows = provisional.load_provisional_candidates(index, LABEL)
        for fraction, expected in ((0.1, 1), (0.3, 3)):
            result = provisional.division_candidates(rows, LABEL, fraction)
            frozen = result["division"]
            self.assertEqual(len(frozen["heldout_group_ids"]), expected)
            self.assertFalse(set(frozen["heldout_group_ids"]) & set(frozen["train_group_ids"]))
            self.assertFalse(set(frozen["heldout_qids"]) & set(frozen["train_candidate_qids"]))
            self.assertEqual(result["PROVISIONAL_DIVISION_SHA"], digest_json(frozen))
            self.assertNotIn("DIVISION_SHA", result)
            self.assertEqual(result, provisional.division_candidates(rows, LABEL, fraction))

    def test_mode_cannot_emit_or_accept_clean_receipts(self):
        with self.assertRaisesRegex(ValueError, "clean"):
            provisional.tag({"schema": "clean-student-training-v1"}, LABEL)
        with self.assertRaisesRegex(ValueError, "clean"):
            provisional.require_mode({"schema": "clean-student-training-v1", **provisional.flags(LABEL)}, LABEL)
        value = provisional.tag({"schema": "student-publication-v1"}, LABEL)
        with self.assertRaises(ValueError):
            provisional.require_mode(value, None)
        with self.assertRaises(ValueError):
            provisional.require_mode(value, provisional.LABELS[1])
        self.assertEqual(provisional.require_mode(value, LABEL), value)
        self.assertEqual(provisional.tag({"unchanged": True}, None), {"unchanged": True})

    def test_provisional_lease_records_real_host_uuid_and_rechecks_both(self):
        now = datetime.now(timezone.utc)
        coord = self.root / "coord"
        evidence = self.document("coord/LEASES/test-work.lock/lease.json", {
            "work_id": "test-work", "status": "running", "agent_id": "fixture", "host": "trinity-0-18",
            "last_heartbeat": now.isoformat()})
        lease_path = self.document("supervisor.json", {
            "host": "trinity-0-18", "gpu_index": 3, "owner": "fixture", "work_id": "test-work",
            "protocol_sha256": "c" * 64, "ownership_check_passed": True, "coordination_lease_passed": True,
            "vnice_wrapped": True, "coordination_lease_evidence": str(evidence),
            "ownership_checked_at": now.isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat()})
        output = self.root / "bound-lease.json"
        with patch.object(provisional.socket, "gethostname", return_value="trinity-0-18.example"), \
                patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}), \
                patch.object(provisional.subprocess, "run", return_value=type("Probe", (), {"stdout": "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa\n"})()) as probe:
            provisional.bind_lease(lease_path, output, LABEL, "test-work", "c" * 64, coord)
            bound = load_json(output)
            self.assertEqual((bound["host"], bound["gpu_uuid"]), ("trinity-0-18", "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
            self.assertIn("3", probe.call_args.args[0])
            provisional.require_lease(output, LABEL, "test-work", "c" * 64, coord_root=coord)
            from student_pilot.benchmark_eval import contracts
            admission = contracts.authenticate_lease(output, "test-work", "c" * 64, coord, provisional_diagnostic=LABEL)
            self.assertEqual((admission["host"], admission["gpu_index"], admission["gpu_uuid"]),
                             ("trinity-0-18", 3, "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
            self.assertEqual(admission["provisional_diagnostic"], LABEL)
            with self.assertRaisesRegex(ValueError, "identity overrides"):
                contracts.authenticate_lease(output, "test-work", "c" * 64, coord, hostname="forged",
                                             provisional_diagnostic=LABEL)
            with patch.object(provisional.socket, "gethostname", return_value="trinity-1-13"), self.assertRaises(ValueError):
                provisional.require_lease(output, LABEL, "test-work", "c" * 64, coord_root=coord)
            probe.return_value.stdout = "GPU-foreign\n"
            with self.assertRaisesRegex(ValueError, "UUID"):
                provisional.require_lease(output, LABEL, "test-work", "c" * 64, coord_root=coord)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        from student_pilot import diagnostic
        import torch

        self.diagnostic = diagnostic
        self.root = Path(tempfile.mkdtemp(prefix="admission_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.now = datetime.now(timezone.utc)
        coord = self.root / "coord"
        self.evidence = coord / "LEASES/test-work.lock/lease.json"
        self.evidence.parent.mkdir(parents=True)
        self.evidence.write_bytes(canonical_bytes({
            "work_id": "test-work", "status": "running", "agent_id": "fixture", "host": "trinity-0-18",
            "last_heartbeat": self.now.isoformat()}))
        self.lease = provisional.tag({
            "host": "trinity-0-18", "gpu_index": 3, "gpu_uuid": "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "owner": "fixture",
            "work_id": "test-work", "protocol_sha256": "c" * 64, "ownership_check_passed": True,
            "coordination_lease_passed": True, "vnice_wrapped": True, "coordination_root": str(coord),
            "coordination_lease_evidence": str(self.evidence),
            "ownership_checked_at": (self.now - timedelta(seconds=600)).isoformat(),
            "expires_at": (self.now + timedelta(minutes=10)).isoformat()}, LABEL)
        self.path = self.root / "lease.json"
        self.path.write_bytes(canonical_bytes(self.lease))
        self.check = Mock(wraps=partial(provisional.require_lease, label=LABEL, expected_work="test-work",
                                       protocol_sha256="c" * 64, coord_root=coord))
        patches = [patch.object(provisional.socket, "gethostname", return_value="trinity-0-18.example"),
                   patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "3"}),
                   patch.object(provisional, "gpu_uuid", return_value="GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                   patch.object(provisional.subprocess, "run", return_value=Mock(stdout="")),
                   patch.object(torch, "cuda", Mock(is_available=Mock(return_value=True),
                                                    device_count=Mock(return_value=1),
                                                    is_bf16_supported=Mock(return_value=True),
                                                    get_device_properties=Mock(return_value=SimpleNamespace(
                                                        uuid=self.lease["gpu_uuid"]))))]
        _, _, self.uuid, self.compute, self.cuda = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)

    def admit(self):
        return self.diagnostic.admitted_device(self.path, self.check, LABEL)

    def test_stale_supervisor_timestamp_admits_with_live_probe(self):
        for stdout, pids in (("", []), (f"{os.getpid()}, 12 MiB\n", [os.getpid()])):
            with self.subTest(stdout=stdout):
                self.compute.return_value.stdout = stdout
                admitted = self.admit()
                probe = admitted["admission_probe"]
                self.assertEqual(probe["gpu_uuid"], "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
                self.assertEqual(probe["compute_pids"], pids)
                self.assertGreaterEqual(datetime.fromisoformat(probe["probed_at"]), self.now)
                self.assertTrue(0 <= probe["heartbeat_age_seconds"] <= 300)
                self.check.assert_called_with(self.path, fresh=False)
                self.uuid.assert_called_with(3)
                self.compute.assert_called_with(
                    ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader", "--id=GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"],
                    check=True, capture_output=True, text=True, timeout=20)
        self.assertNotIn("admission_probe", load_json(self.path))

    def test_cuda_uuid_matches_lease_and_management_uuid(self):
        expected = self.lease["gpu_uuid"]
        for raw in (expected, expected.removeprefix("GPU-"), expected.upper(), UUID(expected[4:])):
            with self.subTest(raw=raw):
                self.cuda.get_device_properties.return_value.uuid = raw
                self.cuda.get_device_properties.side_effect = lambda index: (
                    self.cuda.set_device.assert_called_with(0) or SimpleNamespace(uuid=raw))
                probe = self.admit()["admission_probe"]
                for key in ("gpu_uuid", "lease_gpu_uuid", "nvidia_smi_gpu_uuid", "cuda_gpu_uuid"):
                    self.assertEqual(probe[key], expected)
                self.cuda.get_device_properties.assert_called_with(0)

    def test_reordered_cuda_device_uuid_refuses(self):
        self.cuda.get_device_properties.return_value.uuid = "GPU-bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        with self.assertRaisesRegex(ValueError, "CUDA device 0 UUID.*bound lease"):
            self.admit()
        self.cuda.reset_peak_memory_stats.assert_not_called()

    def test_missing_cuda_uuid_refuses(self):
        self.cuda.get_device_properties.return_value = SimpleNamespace()
        with self.assertRaisesRegex(ValueError, "cannot obtain CUDA device 0 physical UUID"):
            self.admit()
        self.cuda.reset_peak_memory_stats.assert_not_called()

    def test_none_cuda_uuid_refuses(self):
        self.cuda.get_device_properties.return_value.uuid = None
        with self.assertRaisesRegex(ValueError, "cannot obtain CUDA device 0 physical UUID"):
            self.admit()
        self.cuda.reset_peak_memory_stats.assert_not_called()

    def test_unavailable_or_invalid_cuda_uuid_refuses(self):
        for value in (RuntimeError("CUDA properties unavailable"), SimpleNamespace(uuid=""),
                      SimpleNamespace(uuid="not-a-uuid")):
            with self.subTest(value=value):
                self.cuda.get_device_properties.side_effect = [value]
                with self.assertRaisesRegex(ValueError, "cannot obtain CUDA device 0 physical UUID"):
                    self.admit()
        self.cuda.reset_peak_memory_stats.assert_not_called()

    def test_compute_probe_uuid_differs_from_cuda_uuid_refuses(self):
        probe = provisional.admission_probe(self.lease)
        probe["nvidia_smi_gpu_uuid"] = "GPU-bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        with patch.object(provisional, "admission_probe", return_value=probe):
            with self.assertRaisesRegex(ValueError, "CUDA device 0 UUID.*nvidia-smi"):
                self.admit()
        self.cuda.reset_peak_memory_stats.assert_not_called()

    def test_foreign_compute_pid_refuses_before_cuda(self):
        self.compute.return_value.stdout = f"{os.getpid()}, 12 MiB\n{os.getpid() + 1}, 1 MiB\n"
        with self.assertRaisesRegex(ValueError, "foreign compute PID"):
            self.admit()
        self.cuda.set_device.assert_not_called()

    def test_uuid_mismatch_refuses_before_compute_probe(self):
        self.uuid.return_value = "GPU-other"
        with self.assertRaisesRegex(ValueError, "UUID"):
            self.admit()
        self.compute.assert_not_called()
        self.cuda.set_device.assert_not_called()

    def test_stale_coordination_heartbeat_refuses(self):
        evidence = load_json(self.evidence)
        evidence["last_heartbeat"] = (self.now - timedelta(seconds=600)).isoformat()
        self.evidence.write_bytes(canonical_bytes(evidence))
        with self.assertRaisesRegex(ValueError, "heartbeat"):
            self.admit()
        self.compute.assert_not_called()

    def test_expired_lease_refuses(self):
        self.lease["expires_at"] = (self.now - timedelta(seconds=1)).isoformat()
        self.path.write_bytes(canonical_bytes(self.lease))
        with self.assertRaisesRegex(ValueError, "expired"):
            self.admit()
        self.compute.assert_not_called()

    def test_heartbeat_and_expiry_are_rechecked_after_compute_probe(self):
        for seconds, message in ((301, "heartbeat"), (601, "expired")):
            with self.subTest(seconds=seconds):
                def probe(*args, **kwargs):
                    clock.now.return_value = self.now + timedelta(seconds=seconds)
                    if seconds == 601:
                        evidence = load_json(self.evidence)
                        evidence["last_heartbeat"] = clock.now.return_value.isoformat()
                        self.evidence.write_bytes(canonical_bytes(evidence))
                    return Mock(stdout="")

                with patch.object(provisional, "datetime", wraps=datetime) as clock:
                    clock.now.return_value = self.now
                    self.compute.side_effect = probe
                    with self.assertRaisesRegex(ValueError, message):
                        self.admit()
        self.cuda.set_device.assert_not_called()

    def test_failed_or_malformed_compute_probe_refuses(self):
        for result in (subprocess.TimeoutExpired("nvidia-smi", 20),
                       subprocess.CalledProcessError(1, "nvidia-smi"), Mock(stdout="unparseable\n")):
            with self.subTest(result=result):
                self.compute.side_effect = [result]
                with self.assertRaises((subprocess.SubprocessError, ValueError)):
                    self.admit()
        self.cuda.set_device.assert_not_called()

    def test_train_and_evaluate_entry_still_require_fresh_supervisor_timestamp(self):
        protocol_loader, manifest_loader = Mock(), Mock()
        with patch.object(self.diagnostic, "execution_contract", return_value=(self.check, protocol_loader, manifest_loader)):
            for operation, extra in ((self.diagnostic.train, {}), (self.diagnostic.evaluate, {"variant": "original"})):
                with self.subTest(operation=operation.__name__), self.assertRaisesRegex(ValueError, "older than five minutes"):
                    operation("manifest", "protocol", "output", self.path, provisional_diagnostic=LABEL, **extra)
                self.check.assert_called_with(self.path)
        protocol_loader.assert_not_called()
        manifest_loader.assert_not_called()
        self.compute.assert_not_called()

    def test_clean_admission_keeps_fresh_check_and_does_not_probe(self):
        lease_check = Mock(return_value={"clean": True})
        with patch.object(provisional, "admission_probe") as probe:
            result = self.diagnostic.admitted_device(self.path, lease_check)
        self.assertEqual(result, {"clean": True})
        lease_check.assert_called_once_with(self.path)
        probe.assert_not_called()
        self.cuda.get_device_properties.assert_not_called()
        self.compute.assert_not_called()
        self.cuda.set_device.assert_called_once_with(0)
        self.cuda.reset_peak_memory_stats.assert_called_once_with()

    def test_train_and_evaluate_record_probe_after_slow_staging(self):
        protocol = {"PROVISIONAL_DIVISION_SHA": "d" * 64, "training": {}, "base": {},
                    "base_sha256": "e" * 64, "versions": {}, "runtime": []}
        protocol_path = self.root / "protocol.json"
        protocol_path.write_bytes(canonical_bytes(protocol))
        rows = [{"qid": "fixture", "student_input": None}]
        manifest = {"protocol": binding(protocol_path), "training_ready": True, "rows": rows,
                    "input_audits": [{"qid": "fixture"}], "heldout_qids": ["fixture"]}
        manifest_path = self.root / "manifest.json"
        manifest_path.write_bytes(canonical_bytes(manifest))
        self.lease.update(ownership_checked_at=self.now.isoformat(),
                          expires_at=(self.now + timedelta(hours=1)).isoformat())
        self.path.write_bytes(canonical_bytes(self.lease))
        self.cuda.get_device_name.return_value = "CPU fixture"

        class ModelBoundary(Exception):
            pass

        for operation, extra in ((self.diagnostic.train, {}), (self.diagnostic.evaluate, {"variant": "original"})):
            with self.subTest(operation=operation.__name__), ExitStack() as stack:
                clock = stack.enter_context(patch.object(provisional, "datetime", wraps=datetime))
                clock.now.return_value = self.now
                evidence = load_json(self.evidence)
                evidence["last_heartbeat"] = self.now.isoformat()
                self.evidence.write_bytes(canonical_bytes(evidence))

                def stage(*args):
                    clock.now.return_value = self.now + timedelta(seconds=600)
                    evidence["last_heartbeat"] = clock.now.return_value.isoformat()
                    self.evidence.write_bytes(canonical_bytes(evidence))
                    return rows

                stack.enter_context(patch.object(self.diagnostic, "execution_contract",
                                                return_value=(self.check, Mock(return_value=protocol), Mock(return_value=manifest))))
                stack.enter_context(patch.object(self.diagnostic, "localize_frames", side_effect=stage))
                stack.enter_context(patch.object(self.diagnostic, "configure_environment"))
                stack.enter_context(patch.object(storage, "SCRATCH_HOME", self.root))
                stack.enter_context(patch.object(storage, "ensure_free_space"))
                stack.enter_context(patch.object(storage, "code_provenance", return_value={"commit": "f" * 40, "dirty": False}))
                stack.enter_context(patch("student_pilot.batches.load_processor", return_value=object()))
                stack.enter_context(patch("student_pilot.runner.load_base", side_effect=ModelBoundary))
                stack.enter_context(patch("transformers.set_seed"))
                output = self.root / operation.__name__
                self.check.reset_mock()
                with self.assertRaises(ModelBoundary):
                    operation(manifest_path, protocol_path, output, self.path, scratch_root=self.root,
                              stage_frames=True, provisional_diagnostic=LABEL, **extra)
                self.assertEqual([call.kwargs for call in self.check.call_args_list], [{}, {"fresh": False}])
                recorded = load_json(output / "run.json")["lease"]["admission_probe"]
                self.assertEqual(recorded["probed_at"], clock.now.return_value.isoformat())
                self.assertEqual(recorded["gpu_uuid"], "GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
                for key in ("lease_gpu_uuid", "nvidia_smi_gpu_uuid", "cuda_gpu_uuid"):
                    self.assertEqual(recorded[key], self.lease["gpu_uuid"])
                self.assertEqual(recorded["compute_pids"], [])
                self.assertEqual(recorded["heartbeat_age_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
