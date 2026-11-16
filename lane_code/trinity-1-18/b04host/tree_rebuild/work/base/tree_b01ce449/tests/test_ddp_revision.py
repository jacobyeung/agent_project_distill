"""Regressions for the three trainer-v4 admission review findings."""
import json
import multiprocessing
import os
import socket
import tempfile
import time
import unittest
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

import torch

from student_pilot import ddp_admission, ddp_training, provisional
from student_pilot.common import load_json
from tests import test_ddp_admission as admission_fixtures
from tests import test_ddp_pipeline as pipeline_fixtures

LABEL = admission_fixtures.LABEL
MALFORMED = ("GPU-fixture-2", "GPU-not-a-uuid", "GPU-deadbeef", "GPU----",
             "GPU-zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz")


class UUIDRegressionTests(unittest.TestCase):
    def test_gpu_prefixed_malformed_uuid_must_refuse(self):
        for value in MALFORMED:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UUID"):
                ddp_admission.cuda_uuid(value)

    def test_management_parser_rejects_malformed_uuid(self):
        for value in MALFORMED:
            with self.subTest(value=value), patch.object(provisional.subprocess, "run", return_value=SimpleNamespace(stdout=value)):
                with self.assertRaisesRegex(ValueError, "UUID"):
                    provisional.gpu_uuid(2)

    def test_matching_malformed_uuid_must_refuse(self):
        real_gpu_uuid = provisional.gpu_uuid
        fixture = admission_fixtures.RankAdmissionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for value in MALFORMED:
            fixture.lease["gpu_uuid"] = value
            fixture.properties.return_value.uuid = value
            def management_probe(command, **kwargs):
                return SimpleNamespace(stdout=value if "--query-gpu=uuid" in command else "")
            with self.subTest(value=value), patch.dict(os.environ, CUDA_VISIBLE_DEVICES=value), \
                    patch.object(provisional, "gpu_uuid", side_effect=real_gpu_uuid), \
                    patch.object(provisional.subprocess, "run", side_effect=management_probe):
                with self.assertRaisesRegex(ValueError, "UUID"):
                    fixture.admit()
                with self.assertRaisesRegex(ValueError, "UUID|identity"):
                    ddp_admission.validate_rank_list(fixture.bundle["ranks"], fixture.request, LABEL, fixture.coord)

    def test_normalization_preserves_every_identity_bit(self):
        expected = UUID("12345678-1234-1234-1234-123456789abc")
        for raw in (expected, expected.bytes, str(expected), expected.hex, "GPU-" + str(expected).upper()):
            with self.subTest(raw=raw):
                self.assertEqual(ddp_admission.cuda_uuid(raw), "GPU-" + str(expected))
        for bit in range(128):
            changed = UUID(int=expected.int ^ (1 << bit))
            self.assertNotEqual(ddp_admission.cuda_uuid(changed), "GPU-" + str(expected))

    def test_three_way_probe_mismatch_and_malformed_values_refuse(self):
        fixture = admission_fixtures.RankAdmissionTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        probe = provisional.admission_probe(fixture.lease)
        for value in (*MALFORMED, "GPU-ffffffff-ffff-ffff-ffff-ffffffffffff"):
            with self.subTest(value=value), patch.object(provisional, "admission_probe",
                    return_value={**probe, "nvidia_smi_gpu_uuid": value}):
                with self.assertRaisesRegex(ValueError, "UUID"):
                    fixture.admit()


class InputBoundaryTests(unittest.TestCase):
    def test_all_train_inputs_are_guarded_before_any_open(self):
        for argument in ("protocol_path", "manifest_path", "training_config", "lease_path"):
            for component in ("offline_labels", "answer_bank"):
                args = dict(manifest_path="unused", protocol_path="unused", output="unused", lease_path="unused",
                            training_config="unused", provisional_diagnostic=LABEL)
                args[argument] = Path(__file__).parent / component / "never-created.json"
                with self.subTest(argument=argument, component=component), \
                        patch.object(Path, "open", side_effect=AssertionError("input opened before validation")):
                    with self.assertRaisesRegex(ValueError, "Protected"):
                        ddp_training.train(**args)

    def test_request_inputs_are_guarded_before_any_open(self):
        for argument in ("protocol_path", "manifest_path"):
            for component in ("offline_labels", "answer_bank"):
                args = dict(manifest_path="unused", protocol_path="unused", label=LABEL, student="onethinker", world_size=2)
                args[argument] = Path(__file__).parent / component / "never-created.json"
                with self.subTest(argument=argument, component=component), \
                        patch.object(Path, "open", side_effect=AssertionError("input opened before validation")):
                    with self.assertRaisesRegex(ValueError, "Protected"):
                        ddp_admission.request_identity(**args)

    def test_allowed_roots_are_checked_before_any_open(self):
        for argument in ("protocol_path", "manifest_path", "training_config", "lease_path"):
            args = dict(manifest_path="unused", protocol_path="unused", output="unused", lease_path="unused",
                        provisional_diagnostic=LABEL)
            args[argument] = "/etc/never-created-ddp-input.json"
            with self.subTest(argument=argument), patch.object(Path, "open", side_effect=AssertionError("unexpected open")):
                with self.assertRaisesRegex(ValueError, "allowed roots"):
                    ddp_training.train(**args)

    def test_resolved_symlink_targets_are_guarded_before_open(self):
        root = Path(tempfile.mkdtemp(prefix="input_guard_", dir=os.environ["LANE_TEST_OUTPUT"]))
        for index, target in enumerate((root / "offline_labels" / "never-created.json",
                                        root / "answer_bank" / "never-created.json", Path("/etc/never-created-ddp.json"))):
            link = root / f"link{index}.json"
            link.symlink_to(target)
            with self.subTest(target=target), patch.object(Path, "open", side_effect=AssertionError("unexpected open")):
                with self.assertRaisesRegex(ValueError, "Protected|allowed roots"):
                    ddp_training.train(link, link, root / "unused", link, training_config=link, provisional_diagnostic=LABEL)


class ReceiptBoundaryTests(unittest.TestCase):
    def test_nonzero_rank_waits_for_persisted_receipt_and_barrier(self):
        fixture = pipeline_fixtures.DDPProtocolTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.ddp_pool()
        manifest = load_json(fixture.training_path)
        leases = [{"rank": rank, "host": "fixture-host", "gpu_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}",
                   "admission_probe": {"cuda_device_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}"}}
                  for rank in range(2)]
        lease_path = fixture.document("reviewer_leases.json", {"ranks": leases})
        output = fixture.root / "nonzero_entry"
        shared = {"protocol": fixture.protocol, "rows": manifest["rows"], "audits": manifest["input_audits"], "counts": manifest["counts"],
                  "checkpoint": None, "resumed_from": None}
        events = []
        def collect(value, world):
            if "request_sha256" in value:
                return [{**value, "rank": rank} for rank in range(world)]
            return [{"lease": lease, "error": None} for lease in leases]
        def broadcast(payload, src):
            if not events:
                payload[0] = shared
                events.append("staged")
            else:
                self.assertFalse((output / "run.json").exists())
                output.mkdir()
                (output / "run.json").write_text(json.dumps({"lease": {"ranks": leases}}))
                events.append("persisted")
                payload[0] = {"admitted": True}
        def barrier():
            self.assertTrue((output / "run.json").is_file())
            events.append("barrier")
        class ModelBoundary(Exception):
            pass
        def boundary(*args):
            self.assertEqual(events, ["staged", "persisted", "barrier"])
            self.assertEqual(load_json(output / "run.json")["lease"]["ranks"], leases)
            raise ModelBoundary
        with ExitStack() as stack:
            for target, name, replacement in (
                (ddp_admission, "load_bundle", lambda *a, **k: {"ranks": leases}),
                (ddp_admission, "select_rank", lambda *a: (1, 2, "2,3")),
                (ddp_admission, "require_rank_lease", lambda *a, **k: leases[1]),
                (ddp_admission, "admitted_rank", lambda *a, **k: leases[1]),
                (ddp_training, "gather", collect),
                (ddp_training, "configure_environment", lambda *a: None),
                (torch.distributed, "init_process_group", lambda *a, **k: None),
                (torch.distributed, "destroy_process_group", lambda *a, **k: None),
                (torch.distributed, "broadcast_object_list", broadcast),
                (torch.distributed, "barrier", barrier)):
                stack.enter_context(patch.object(target, name, side_effect=replacement))
            stack.enter_context(patch("student_pilot.batches.load_processor", return_value=object()))
            stack.enter_context(patch("student_pilot.runner.load_base", side_effect=boundary))
            stack.enter_context(patch("transformers.set_seed"))
            with self.assertRaises(ModelBoundary):
                ddp_training.train(fixture.training_path, fixture.protocol_path, output, lease_path,
                    scratch_root=fixture.root, stage_frames=True, provisional_diagnostic=LABEL)


class AdmissionDecisionTests(unittest.TestCase):
    def test_receipt_failure_is_broadcast_and_no_rank_passes_barrier(self):
        self.check_refusal("write failure")

    def test_probe_failure_is_broadcast_and_no_rank_passes_barrier(self):
        self.check_refusal("probe failure")

    def check_refusal(self, failure):
        from unittest.mock import Mock

        probes = [{"lease": {"rank": rank}, "error": None} for rank in range(2)]
        store = Mock()
        store.record.side_effect = lambda value: value
        if failure == "write failure":
            store.write.side_effect = OSError("synthetic write failure")
        else:
            probes[1] = {"lease": None, "error": "rank 1: synthetic probe failure"}
        decisions = []
        def broadcast(value, src):
            if not decisions:
                decisions.append(value[0])
            else:
                value[0] = decisions[0]
        with patch.object(torch.distributed, "broadcast_object_list", side_effect=broadcast), \
                patch.object(torch.distributed, "barrier") as barrier:
            for rank in range(2):
                with self.subTest(rank=rank), self.assertRaisesRegex(ValueError, "DDP admission refused"):
                    ddp_training.persist_admission(rank, probes, store if rank == 0 else None, {"lease": {"ranks": []}})
            barrier.assert_not_called()
        self.assertIs(decisions[0]["admitted"], False)
        if failure == "probe failure":
            store.write.assert_not_called()


def admission_worker(rank, port, root, scenario):
    """Run the real train entrypoint and CPU collectives with synthetic device probes."""
    from student_pilot import ddp_config, provisional_data
    from student_pilot.common import binding, digest_json

    root = Path(root)
    os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE="2")
    settings = ddp_config.normalize_training_config({"world_size": 2}, "onethinker")
    protocol = provisional.tag({"training": settings, "protocol_version": ddp_config.VERSION,
        "training_sha256": digest_json(settings), "student": "onethinker", "base": {}, "base_sha256": "synthetic",
        "versions": {}, "runtime": {}, "PROVISIONAL_DIVISION_SHA": "synthetic"}, LABEL)
    leases = [{"rank": i, "host": "fixture-host", "admission_probe": {"synthetic": True}} for i in range(2)]
    manifest = {"protocol": binding(root / "protocol.json"), "training_ready": True, "rows": [{"qid": "fixture"}],
                "input_audits": [{"qid": "fixture"}], "counts": {"training_rows": 1}}
    class Store:
        def __init__(self, *args):
            self.root = root
        def record(self, header):
            return header
        def write(self, name, header):
            if scenario == "write_failure":
                raise OSError("synthetic receipt write failure")
            time.sleep(0.3)
            (root / name).write_text(json.dumps(header))
    class ModelBoundary(Exception):
        pass
    def probe(*args, **kwargs):
        if scenario == "probe_failure" and rank == 1:
            raise ValueError("synthetic UUID probe failure")
        return leases[rank]
    def model_boundary(*args):
        header = load_json(root / "run.json")
        assert [lease["rank"] for lease in header["lease"]["ranks"]] == [0, 1]
        (root / f"model_boundary_rank{rank}.json").write_text(json.dumps(header))
        raise ModelBoundary
    with ExitStack() as stack:
        for target, name, replacement in (
            (ddp_admission, "request_identity", lambda *a: {"ranks": [{"rank": 0}, {"rank": 1}], "protocol_sha256": "synthetic"}),
            (ddp_admission, "load_bundle", lambda *a: {"ranks": leases}),
            (ddp_admission, "select_rank", lambda *a: (rank, 2, "2,3")),
            (ddp_admission, "require_rank_lease", lambda *a, **k: leases[rank]),
            (ddp_admission, "admitted_rank", probe),
            (provisional, "load_json", lambda *a: protocol),
            (provisional_data, "load_protocol", lambda *a, **k: protocol),
            (provisional_data, "load_training", lambda *a: manifest),
            (ddp_training, "localize_frames", lambda rows, *a: rows),
            (ddp_training, "configure_environment", lambda *a: None)):
            stack.enter_context(patch.object(target, name, side_effect=replacement))
        stack.enter_context(patch.object(ddp_training, "RunArtifacts", Store))
        stack.enter_context(patch("student_pilot.batches.load_processor", return_value=object()))
        stack.enter_context(patch("student_pilot.runner.load_base", side_effect=model_boundary))
        optimizer = stack.enter_context(patch.object(torch.optim, "AdamW", side_effect=AssertionError("optimizer reached")))
        try:
            ddp_training.train(root / "manifest.json", root / "protocol.json", root, root / "leases.json",
                               provisional_diagnostic=LABEL)
        except ModelBoundary:
            assert scenario == "delayed_write"
        except ValueError as error:
            (root / f"refused_rank{rank}.txt").write_text(str(error))
            raise SystemExit(1)
        finally:
            optimizer.assert_not_called()


class DistributedAdmissionTests(unittest.TestCase):
    def run_case(self, scenario):
        root = Path(tempfile.mkdtemp(prefix=f"ddp_{scenario}_", dir=os.environ["LANE_TEST_OUTPUT"]))
        for name in ("manifest.json", "protocol.json", "leases.json"):
            (root / name).write_text("{}")
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
        (root / "endpoint.txt").write_text(f"MASTER_ADDR=127.0.0.1 MASTER_PORT={port}\n")
        context = multiprocessing.get_context("spawn")
        workers = [context.Process(target=admission_worker, args=(rank, port, str(root), scenario)) for rank in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(45)
            if worker.is_alive():
                worker.terminate()
                worker.join(5)
                self.fail("CPU admission worker timed out")
            self.assertEqual(worker.exitcode, 0 if scenario == "delayed_write" else 1)
        for rank in range(2):
            self.assertEqual((root / f"model_boundary_rank{rank}.json").exists(), scenario == "delayed_write")
            self.assertEqual((root / f"refused_rank{rank}.txt").exists(), scenario != "delayed_write")
        self.assertEqual((root / "run.json").exists(), scenario == "delayed_write")

    def test_delayed_rank_zero_write_precedes_every_model_boundary(self):
        self.run_case("delayed_write")

    def test_write_failure_refuses_every_rank_before_model_work(self):
        self.run_case("write_failure")

    def test_one_failed_probe_exits_whole_job_nonzero(self):
        self.run_case("probe_failure")
