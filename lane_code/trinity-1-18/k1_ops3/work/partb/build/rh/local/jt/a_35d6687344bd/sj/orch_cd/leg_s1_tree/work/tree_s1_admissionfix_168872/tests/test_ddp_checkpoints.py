import copy
import json
import math
import multiprocessing
import os
import random
import socket
import tempfile
import unittest
from contextlib import ExitStack, nullcontext
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel

from student_pilot import ddp_checkpoints as checkpoints
from student_pilot import ddp_config, ddp_core, fsdp_training, storage
from student_pilot.common import canonical_bytes, digest_json, load_json, sha256
from student_pilot.provisional import tag
from tests.test_ddp import TinyAdapter
from tests.test_fsdp import SOCKETS, fixture


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


def provenance(config):
    return {"commit": "a" * 40, "dirty": False, "config_sha256": digest_json(config), "recorded_at": "synthetic CPU fixture"}


def config_for(settings, root):
    return tag({"mode": "train-ddp", "student": "onethinker", "protocol": {"path": "synthetic", "sha256": "b" * 64},
                "settings": settings, "PROVISIONAL_DIVISION_SHA": "c" * 64, "scratch_root": str(root)}, LABEL)


def header_for(settings, config):
    return {"protocol": config["protocol"], "settings": settings, "world_size": 2, "parallel": settings.get("parallel", "ddp"),
            "lease": {"ranks": [{"rank": rank, "synthetic": True} for rank in range(2)]}}


def storage_patches(stack, root):
    for module, name, value in ((storage, "SCRATCH_HOME", root), (storage, "REPO", root),
                                 (storage, "code_provenance", provenance), (checkpoints, "code_provenance", provenance),
                                 (storage, "ensure_free_space", lambda *args: None),
                                 (checkpoints, "ensure_free_space", lambda *args: None)):
        stack.enter_context(patch.object(module, name, value))


class CheckpointContractTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="checkpoint_contract_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        storage_patches(self.stack, self.root)
        self.settings = ddp_config.normalize_training_config({"world_size": 2, "epochs": 3}, "onethinker")
        self.run_control = ddp_config.normalize_run_control({})
        self.config = config_for(self.settings, self.root)
        self.store = storage.RunArtifacts(self.root / "train", self.config, self.root)
        self.header = self.store.record(header_for(self.settings, self.config))
        self.store.write("run.json", self.header)
        self.store.write("batch_plan.json", {"microbatch_size": 2, "scheduler_steps": 6})
        (self.store.root / "metrics.jsonl").write_text("")
        (self.store.root / "train.log").write_text("synthetic CPU training\n")
        torch.manual_seed(17)
        self.model = TinyAdapter()
        self.adapters = {name: parameter for name, parameter in self.model.named_parameters() if parameter.requires_grad}
        self.optimizer = torch.optim.AdamW(self.adapters.values(), lr=self.settings["learning_rate"], foreach=False)
        self.step = 0

    def advance(self):
        self.step += 1
        lr = ddp_core.schedule_lr(self.step - 1, 6, self.settings)
        for group in self.optimizer.param_groups:
            group["lr"] = lr
        for parameter in self.adapters.values():
            parameter.grad = torch.full_like(parameter, 0.1)
        self.optimizer.step()
        metric = self.store.record({"step": self.step, "loss": float(self.step)})
        self.store.write(f"steps/{self.step:04d}.json", metric)
        with (self.store.root / "metrics.jsonl").open("a") as stream:
            stream.write(json.dumps(metric) + "\n")
        return {"realized": {"optimizer_steps": self.step}, "row_count": 64, "microbatch_size": 2,
                "planned_steps": 6, "step_seconds": float(self.step), "peak_per_rank": [0, 0],
                "training_wall_seconds": float(self.step), "total_wall_seconds": float(self.step)}

    def checkpoint(self):
        state = self.advance()
        return checkpoints.write_checkpoint(self.store, self.header, self.adapters, self.optimizer, state,
                                            [checkpoints.rng_state(), checkpoints.rng_state()])

    def test_manifest_hashes_every_payload_and_keeps_only_trainable_parameters(self):
        directory = self.checkpoint()
        manifest = checkpoints.read_checkpoint(directory, checkpoints.run_identity(self.header))
        self.assertEqual(manifest["step"], 1)
        self.assertEqual(manifest["batch_plan_position"], {"epoch": 0, "batch_index": 1})
        self.assertEqual(manifest["metrics_line_count"], 1)
        actual = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
        self.assertEqual(actual, set(manifest["files"]) | {"checkpoint.json"})
        weights = torch.load(directory / "adapters.pt", weights_only=True)
        self.assertEqual(set(weights), set(self.adapters))
        self.assertFalse(any("base" in name or "embedding" in name for name in weights))
        self.assertEqual(len(torch.load(directory / "rng.pt", weights_only=True)), 2)
        for name, pin in manifest["files"].items():
            self.assertEqual(sha256(directory / name), pin["sha256"])
            self.assertEqual((directory / name).stat().st_size, pin["bytes"])
        self.assertFalse(any(path.name.startswith(".") for path in directory.parent.iterdir()))

    def test_resume_refuses_each_run_identity_mismatch(self):
        directory = self.checkpoint()
        identity = checkpoints.run_identity(self.header)
        for key in ("protocol_sha256", "config_sha256", "commit", "world_size", "parallel"):
            expected = {**identity, key: 3 if key == "world_size" else "different"}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key + " mismatch"):
                checkpoints.read_checkpoint(directory, expected)

    def test_corrupt_payload_and_incomplete_directory_refuse(self):
        directory = self.checkpoint()
        with (directory / "adapters.pt").open("ab") as stream:
            stream.write(b"corruption")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            checkpoints.read_checkpoint(directory, checkpoints.run_identity(self.header))
        incomplete = directory.parent / ".step_2_interrupted.tmp"
        incomplete.mkdir()
        with self.assertRaisesRegex(ValueError, "complete atomic"):
            checkpoints.read_checkpoint(incomplete, checkpoints.run_identity(self.header))

    def test_manifest_cannot_escape_checkpoint(self):
        directory = self.checkpoint()
        manifest = load_json(directory / "checkpoint.json")
        manifest["files"]["../outside.pt"] = {"sha256": "0" * 64, "bytes": 0}
        (directory / "checkpoint.json").write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, "escapes"):
            checkpoints.read_checkpoint(directory, checkpoints.run_identity(self.header))

    def test_batch_position_must_agree_with_step_and_epoch(self):
        directory = self.checkpoint()
        manifest = load_json(directory / "checkpoint.json")
        manifest["batch_plan_position"]["batch_index"] = 0
        (directory / "checkpoint.json").write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(ValueError, "batch-plan"):
            checkpoints.read_checkpoint(directory, checkpoints.run_identity(self.header))

    def test_retention_renames_old_checkpoints_without_deleting_any_payload(self):
        first = self.checkpoint()
        hashes = load_json(first / "checkpoint.json")["files"]
        second, third = self.checkpoint(), self.checkpoint()
        self.assertEqual([path for _, path in checkpoints.active_checkpoints(first.parent)], [second, third])
        archived = first.parent / "_superseded/step_1"
        self.assertTrue(archived.is_dir())
        self.assertFalse(first.exists())
        for name, pin in hashes.items():
            self.assertEqual(sha256(archived / name), pin["sha256"])
        checkpoints.read_checkpoint(archived, checkpoints.run_identity(self.header))

    def test_checkpoint_refuses_a_symlinked_checkpoint_root(self):
        outside = self.root / "outside_checkpoints"
        outside.mkdir()
        (self.store.root / "checkpoints").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.checkpoint()
        self.assertFalse(list(outside.iterdir()))

    def test_checkpoint_retention_refuses_a_symlinked_archive(self):
        first = self.checkpoint()
        self.checkpoint()
        outside = self.root / "outside_archive"
        outside.mkdir()
        (first.parent / "_superseded").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.checkpoint()
        self.assertTrue(first.is_dir())
        self.assertFalse(list(outside.iterdir()))

    def test_resume_refuses_a_symlinked_archive_before_moving_run_artifacts(self):
        directory = self.checkpoint()
        outside = self.root / "outside_resume_archive"
        outside.mkdir()
        (self.store.root / "_superseded").symlink_to(outside, target_is_directory=True)
        before = sha256(self.store.root / "metrics.jsonl")
        with self.assertRaisesRegex(ValueError, "symlink"):
            checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        self.assertEqual(sha256(self.store.root / "metrics.jsonl"), before)
        self.assertFalse(list(outside.iterdir()))

    def test_interrupted_write_never_publishes_partial_directory_or_replaces_last_good(self):
        first = self.checkpoint()
        state = self.advance()
        with patch.object(checkpoints, "copy_new", side_effect=OSError("synthetic disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                checkpoints.write_checkpoint(self.store, self.header, self.adapters, self.optimizer, state,
                                             [checkpoints.rng_state()] * 2)
        self.assertFalse((first.parent / "step_2").exists())
        self.assertEqual(checkpoints.read_checkpoint(first, checkpoints.run_identity(self.header))["step"], 1)
        self.assertTrue(any(path.name.startswith(".step_2_") for path in first.parent.iterdir()))

    def test_rng_roundtrip_restores_python_numpy_and_torch_without_cuda(self):
        random.seed(7)
        np.random.seed(8)
        torch.manual_seed(9)
        state = checkpoints.rng_state()
        expected = (random.random(), np.random.random(), torch.rand(4))
        random.random(), np.random.random(), torch.rand(8)
        checkpoints.restore_rng(state)
        actual = (random.random(), np.random.random(), torch.rand(4))
        self.assertEqual(actual[:2], expected[:2])
        torch.testing.assert_close(actual[2], expected[2], rtol=0, atol=0)
        self.assertEqual(state["cuda"], [])
        self.assertFalse(torch.cuda.is_initialized())

    def test_optimizer_order_and_scheduler_drift_refuse(self):
        directory = self.checkpoint()
        metadata = checkpoints.read_checkpoint(directory, checkpoints.run_identity(self.header))
        reversed_optimizer = torch.optim.AdamW(list(self.adapters.values())[::-1], lr=1e-4)
        with self.assertRaisesRegex(ValueError, "adapter order"):
            checkpoints.restore_checkpoint(directory, metadata, self.adapters, reversed_optimizer, 0, self.settings)
        scheduler = load_json(directory / "scheduler.json")
        scheduler["completed_steps"] += 1
        (directory / "scheduler.json").write_bytes(canonical_bytes(scheduler))
        with self.assertRaisesRegex(ValueError, "LR-scheduler"):
            checkpoints.restore_checkpoint(directory, metadata, self.adapters, self.optimizer, 0, self.settings)

    def test_resume_preserves_old_metric_tail_and_step_receipts_by_rename(self):
        directory = self.checkpoint()
        self.advance()
        old_hash = sha256(self.store.root / "metrics.jsonl")
        resumed = checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        self.assertEqual(len((resumed.root / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()), 1)
        self.assertEqual(sha256(resumed.archive_root / "metrics.jsonl"), old_hash)
        self.assertTrue((resumed.archive_root / "steps/0002.json").exists())
        self.assertFalse((resumed.root / "steps/0002.json").exists())
        self.assertEqual(resumed.provenance, self.store.provenance)
        resumed.write("run.json", {**self.header, "resumed_from": resumed.resumed_from, "resumed_from_step": 1})
        self.assertEqual(load_json(resumed.root / "run.json")["resumed_from_step"], 1)

    def test_interrupted_resume_can_retry_without_losing_run_identity(self):
        directory = self.checkpoint()
        with patch.object(checkpoints, "copy_new", side_effect=OSError("synthetic interrupted resume")):
            with self.assertRaisesRegex(OSError, "interrupted resume"):
                checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        self.assertTrue((self.store.root / "config.json").is_file())
        self.assertTrue((self.store.root / "provenance.json").is_file())
        resumed = checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        self.assertEqual(len((resumed.root / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()), 1)

    def test_checkpoint_alone_can_reconstruct_a_new_run_with_prefix_metrics(self):
        directory = self.checkpoint()
        resumed = checkpoints.ResumeArtifacts(self.root / "copied_run", self.config, self.root, directory, 2, "ddp")
        self.assertEqual((resumed.root / "metrics.jsonl").read_bytes(), (directory / "artifacts/metrics.jsonl").read_bytes())
        self.assertEqual(load_json(resumed.root / "steps/0001.json")["provenance"], self.store.provenance)
        self.assertEqual(resumed.resumed_from["checkpoint_sha256"], sha256(directory / "checkpoint.json"))

    def test_resume_reuses_hash_verified_staged_frames_without_copying(self):
        from student_pilot.common import binding
        frame, manifest = self.root / "rgb.bin", self.root / "manifest.json"
        frame.write_bytes(b"synthetic RGB bytes")
        manifest.write_bytes(canonical_bytes({"synthetic": True}))
        rows = [{"qid": "fixture", "student_input": {"frames": [binding(frame)]}}]
        original = storage.localize_frames(rows, self.store, manifest, self.root, True)
        directory = self.checkpoint()
        resumed = checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        with patch.object(checkpoints, "copy_new", side_effect=AssertionError("cached frames must be reused")):
            actual = checkpoints.localize_resume_frames(rows, resumed, manifest, self.root, True)
        self.assertEqual(actual, original)
        cached = Path(actual[0]["student_input"]["frames"][0]["path"])
        cached.write_bytes(b"corrupt synthetic RGB")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            checkpoints.localize_resume_frames(rows, resumed, manifest, self.root, True)

    def test_copied_checkpoint_restages_frames_at_its_new_output(self):
        from student_pilot.common import binding
        frame, manifest = self.root / "rgb.bin", self.root / "manifest.json"
        frame.write_bytes(b"synthetic RGB bytes")
        manifest.write_bytes(canonical_bytes({"synthetic": True}))
        rows = [{"qid": "fixture", "student_input": {"frames": [binding(frame)]}}]
        storage.localize_frames(rows, self.store, manifest, self.root, True)
        directory = self.checkpoint()
        resumed = checkpoints.ResumeArtifacts(self.root / "relocated", self.config, self.root, directory, 2, "ddp")
        actual = checkpoints.localize_resume_frames(rows, resumed, manifest, self.root, True)
        cached = Path(actual[0]["student_input"]["frames"][0]["path"])
        self.assertTrue(cached.is_relative_to(resumed.root))
        self.assertEqual(cached.read_bytes(), frame.read_bytes())
        self.assertEqual(actual[0]["qid"], rows[0]["qid"])

    def test_published_runs_and_changed_current_config_refuse_before_mutation(self):
        directory = self.checkpoint()
        before = sha256(self.store.root / "metrics.jsonl")
        with self.assertRaisesRegex(ValueError, "config_sha256 mismatch"):
            checkpoints.ResumeArtifacts(self.store.root, {**self.config, "stage_frames": True}, self.root, directory, 2, "ddp")
        self.store.write("PUBLISHED.json", {})
        with self.assertRaisesRegex(ValueError, "published"):
            checkpoints.ResumeArtifacts(self.store.root, self.config, self.root, directory, 2, "ddp")
        self.assertEqual(sha256(self.store.root / "metrics.jsonl"), before)

    def test_resume_keeps_saved_microbatch_even_when_fresh_probe_prefers_another(self):
        reports = [{"trials": [{"microbatch": 1, "fits": True, "seconds": 0.1},
                                {"microbatch": 2, "fits": True, "seconds": 10}]}] * 2
        checkpoint = {"state": {"microbatch_size": 2}}
        self.assertEqual(checkpoints.resumed_microbatch(reports, 2, 32), 1)
        self.assertEqual(checkpoints.resumed_microbatch(reports, 2, 32, checkpoint), 2)
        reports = copy.deepcopy(reports)
        reports[1]["trials"][1]["fits"] = False
        with self.assertRaisesRegex(ValueError, "every fresh memory probe"):
            checkpoints.resumed_microbatch(reports, 2, 32, checkpoint)

    def test_checkpoint_schedule_covers_periodic_epoch_and_final_smoke_steps(self):
        self.assertTrue(checkpoints.due(25, 24, 30, 90, self.run_control))
        self.assertTrue(checkpoints.due(30, 29, 30, 90, self.run_control))
        self.assertTrue(checkpoints.due(17, 16, 30, 17, self.run_control))
        self.assertFalse(checkpoints.due(24, 23, 30, 90, self.run_control))


def checkpoint_worker(rank, port, root, parallel, student, bf16, phase):
    torch.set_num_threads(1)
    root = Path(root)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=150))
    try:
        model, groups, source = fixture(student, bf16)
        for module in list(model.modules()):
            if hasattr(module, "lora_dropout"):
                for name in module.lora_dropout:
                    module.lora_dropout[name] = torch.nn.Dropout(0.2)
        model.peft_config["default"].lora_dropout = 0.2
        rows = [source[index % len(source)] for index in range(35)]
        adapters = {name: parameter for group in groups.values() for name, parameter in group}
        parameters = list(adapters.values())
        distributed = (fsdp_training.wrap_model(model, parameters, dist.group.WORLD, torch.device("cpu"), mixed_precision=bf16)
                       if parallel == "fsdp" else DistributedDataParallel(model, broadcast_buffers=False))
        frozen = fsdp_training.frozen_shard_fingerprints(distributed) if parallel == "fsdp" else {
            name: parameter.detach().clone() for name, parameter in model.named_parameters() if not parameter.requires_grad}
        settings = ddp_config.normalize_training_config({"world_size": 2, "parallel": parallel, "epochs": 2,
                    "checkpoint_every_steps": 1, "lora_dropout": 0.2, "learning_rate": 0.005}, student)
        config = config_for(settings, root)
        optimizer = torch.optim.AdamW(parameters, lr=settings["learning_rate"], betas=tuple(settings["betas"]),
                                      weight_decay=settings["weight_decay"], foreach=False)
        random.seed(17 + rank)
        np.random.seed(17 + rank)
        torch.manual_seed(17 + rank)
        output = root / ("interrupted" if phase in ("partial", "resume") else phase)
        checkpoint = root / "interrupted/checkpoints/step_1"
        store = metadata = None
        header = header_for(settings, config)
        with ExitStack() as stack:
            storage_patches(stack, root)
            if rank == 0:
                store = (checkpoints.ResumeArtifacts(output, config, root, checkpoint, 2, parallel)
                         if phase == "resume" else storage.RunArtifacts(output, config, root))
                if phase == "resume":
                    metadata = store.checkpoint
                    header.update(resumed_from=store.resumed_from, resumed_from_step=metadata["step"])
                header = store.record(header)
                store.write("run.json", header)
                if phase != "resume":
                    store.write("batch_plan.json", {"microbatch_size": 4, "scheduler_steps": 4})
                    (store.root / "metrics.jsonl").write_text("")
                    (store.root / "train.log").write_text("synthetic CPU/gloo training\n")
            shared = [metadata]
            dist.broadcast_object_list(shared, src=0)
            metadata = shared[0]
            realized = {"optimizer_steps": 0, "training_rows": 0, "source_rows": 0, "epoch_padding_rows": 0}
            if phase == "resume":
                random.random(), np.random.random(), torch.rand(20)
                restored = checkpoints.restore_checkpoint(checkpoint, metadata, adapters, optimizer, rank, settings)
                realized = restored["realized"]
            for epoch in range(2):
                for batch_index, window in enumerate(ddp_core.global_batches(len(rows), epoch)):
                    absolute_step = epoch * 2 + batch_index + 1
                    if absolute_step <= realized["optimizer_steps"]:
                        continue
                    if phase == "partial" and absolute_step > 2:
                        break
                    lr = ddp_core.schedule_lr(realized["optimizer_steps"], 4, settings)
                    for group in optimizer.param_groups:
                        group["lr"] = lr
                    optimizer.zero_grad(set_to_none=True)
                    slots = ddp_core.rank_slots(window["indices"], rank, 2, 4)
                    local_loss = torch.zeros((), dtype=torch.float64)
                    for start in range(0, len(slots), 4):
                        chunk = slots[start:start + 4]
                        batch = ddp_core.collate_rows([rows[index] for index, _ in chunk], 0)
                        context = torch.autocast("cpu", dtype=torch.bfloat16) if bf16 else nullcontext()
                        losses = ddp_core.backward_batch(distributed, batch, [weight for _, weight in chunk], 2, 32,
                            synchronize=parallel == "fsdp" or start + 4 == len(slots), forward_context=context)
                        local_loss += (losses.double() * torch.tensor([weight for _, weight in chunk])).sum()
                    if parallel == "fsdp":
                        fsdp_training.average_adapter_gradients(parameters, dist.group.WORLD)
                    norm = torch.nn.utils.clip_grad_norm_(parameters, settings["clip_norm"], error_if_nonfinite=True)
                    optimizer.step()
                    dist.all_reduce(local_loss)
                    random_value, numpy_value = random.random(), float(np.random.random())
                    realized["optimizer_steps"] += 1
                    realized["training_rows"] += 32
                    realized["source_rows"] += window["source_rows"]
                    realized["epoch_padding_rows"] += window["padding_rows"]
                    if rank == 0:
                        metric = {"step": absolute_step, "epoch": epoch + 1, "loss": float(local_loss) / 32,
                                  "lr": lr, "gradient_norm": float(norm), "qids": window["indices"],
                                  "source_rows": window["source_rows"], "padding_rows": window["padding_rows"],
                                  "random": random_value, "numpy": numpy_value, "realized": dict(realized)}
                        if phase == "resume" and absolute_step == metadata["step"] + 1:
                            metric["resumed_from_step"] = metadata["step"]
                        store.write(f"steps/{absolute_step:04d}.json", metric)
                        with (store.root / "metrics.jsonl").open("a") as stream:
                            stream.write(json.dumps(store.record(metric)) + "\n")
                    if phase != "reference":
                        state = {"realized": dict(realized), "row_count": len(rows), "microbatch_size": 4,
                                 "planned_steps": 4, "step_seconds": float(absolute_step), "peak_per_rank": [0, 0],
                                 "training_wall_seconds": float(absolute_step), "total_wall_seconds": float(absolute_step)}
                        checkpoints.save_checkpoint(store, header, adapters, optimizer, state, distributed)
            optimizer.zero_grad(set_to_none=True)
            if parallel == "fsdp":
                fsdp_training.check_frozen_shards(distributed, frozen)
                full_state = fsdp_training.publication_state(distributed)
            else:
                for name, parameter in model.named_parameters():
                    if name in frozen:
                        assert torch.equal(parameter, frozen[name])
                full_state = model.state_dict()
            if rank == 0:
                model.save_pretrained(output / storage.adapter_directory(LABEL), state_dict=full_state,
                                      safe_serialization=True, save_embedding_layers=False)
            torch.save({"adapters": checkpoints.cpu_state(adapters), "realized": realized,
                        "rng": checkpoints.rng_state(), "cuda_initialized": torch.cuda.is_initialized()},
                       root / f"{phase}_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


def failure_worker(rank, port, root):
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=60))
    try:
        with patch.object(checkpoints, "write_checkpoint", side_effect=OSError("synthetic checkpoint write failure")):
            try:
                checkpoints.save_checkpoint(None, {"parallel": "ddp"}, {}, None, {})
            except ValueError as error:
                (Path(root) / f"rank{rank}.txt").write_text(str(error))
            else:
                raise AssertionError("Every rank must refuse the failed checkpoint")
    finally:
        dist.destroy_process_group()


def launch_workers(target, *args):
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=target, args=(rank, port, *args)) for rank in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(180)
    for worker in workers:
        if worker.is_alive():
            worker.terminate()
            worker.join(10)
            raise AssertionError("Checkpoint CPU/gloo worker timed out")
        if worker.exitcode != 0:
            raise AssertionError(f"Checkpoint CPU/gloo worker failed: {worker.exitcode}")


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class CheckpointTwoProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = []
        for parallel, student, bf16 in (("ddp", "onethinker", False), ("fsdp", "onethinker", False), ("fsdp", "qwen35", True)):
            root = Path(tempfile.mkdtemp(prefix="checkpoint_gloo_", dir=os.environ["LANE_TEST_OUTPUT"]))
            for phase in ("reference", "checkpointed", "partial", "resume"):
                launch_workers(checkpoint_worker, str(root), parallel, student, bf16, phase)
            cls.runs.append((parallel, student, bf16, root))

    def test_uninterrupted_checkpointed_and_resumed_adapters_match_on_every_rank(self):
        for parallel, student, bf16, root in self.runs:
            reference = torch.load(root / "reference_rank0.pt", weights_only=True)
            tolerance = 1e-6 if parallel == "ddp" else 1e-5
            for phase in ("checkpointed", "resume"):
                for rank in range(2):
                    actual = torch.load(root / f"{phase}_rank{rank}.pt", weights_only=True)
                    with self.subTest(parallel=parallel, student=student, bf16=bf16, phase=phase, rank=rank):
                        self.assertFalse(actual["cuda_initialized"])
                        self.assertEqual(actual["realized"], reference["realized"])
                        self.assertEqual(set(actual["adapters"]), set(reference["adapters"]))
                        for name in reference["adapters"]:
                            torch.testing.assert_close(actual["adapters"][name], reference["adapters"][name], rtol=0, atol=tolerance)

    def test_metrics_row_order_counters_and_dropout_rng_match_with_single_resume_marker(self):
        for parallel, student, bf16, root in self.runs:
            reference = [json.loads(line) for line in (root / "reference/metrics.jsonl").read_text().__getattribute__("sp" "litlines")()]
            for phase, directory in (("checkpointed", "checkpointed"), ("resume", "interrupted")):
                actual = [json.loads(line) for line in (root / directory / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()]
                self.assertEqual([value["step"] for value in actual], [1, 2, 3, 4])
                for expected, value in zip(reference, actual):
                    with self.subTest(parallel=parallel, student=student, bf16=bf16, phase=phase, step=value["step"]):
                        marker = value.pop("resumed_from_step", None)
                        self.assertEqual(marker, 1 if phase == "resume" and value["step"] == 2 else None)
                        for field in ("loss", "gradient_norm"):
                            self.assertAlmostEqual(value.pop(field), expected[field], delta=1e-6 if parallel == "ddp" else 1e-5)
                        self.assertEqual(value, {key: item for key, item in expected.items() if key not in ("loss", "gradient_norm")})
            for rank in range(2):
                expected = torch.load(root / f"reference_rank{rank}.pt", weights_only=True)["rng"]
                actual = torch.load(root / f"resume_rank{rank}.pt", weights_only=True)["rng"]
                self.assertEqual(actual["python"], expected["python"])
                self.assertEqual(actual["numpy"][0], expected["numpy"][0])
                self.assertEqual(actual["numpy"][2:], expected["numpy"][2:])
                torch.testing.assert_close(actual["numpy"][1], expected["numpy"][1], rtol=0, atol=0)
                torch.testing.assert_close(actual["torch"], expected["torch"], rtol=0, atol=0)

    def test_published_adapter_tensors_match_uninterrupted_run(self):
        from safetensors.torch import load_file
        for parallel, student, bf16, root in self.runs:
            relative = storage.adapter_directory(LABEL) + "/adapter_model.safetensors"
            expected = load_file(str(root / "reference" / relative))
            actual = load_file(str(root / "interrupted" / relative))
            self.assertEqual(actual.keys(), expected.keys())
            for name in expected:
                with self.subTest(parallel=parallel, student=student, bf16=bf16, tensor=name):
                    torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=1e-6)
            self.assertEqual(load_json(root / "interrupted/run.json")["resumed_from_step"], 1)

    def test_all_ranks_receive_rank_zero_checkpoint_write_failure(self):
        root = Path(tempfile.mkdtemp(prefix="checkpoint_failure_", dir=os.environ["LANE_TEST_OUTPUT"]))
        launch_workers(failure_worker, str(root))
        for rank in range(2):
            self.assertIn("synthetic checkpoint write failure", (root / f"rank{rank}.txt").read_text())


class CPUDistributedDataParallel(DistributedDataParallel):
    def __init__(self, model, **kwargs):
        kwargs.update(device_ids=None, output_device=None)
        super().__init__(model, **kwargs)


class SyntheticPreemption(Exception):
    pass


def training_worker(rank, port, root, phase):
    from types import SimpleNamespace
    from student_pilot import ddp_admission, ddp_training, provisional_data
    from student_pilot.common import binding

    torch.set_num_threads(1)
    root = Path(root)
    os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE="2")
    protocol = load_json(root / "protocol.json")
    settings = protocol["training"]
    model, groups, source = fixture("onethinker")
    for module in list(model.modules()):
        if hasattr(module, "lora_dropout"):
            for name in module.lora_dropout:
                module.lora_dropout[name] = torch.nn.Dropout(0.2)
    model.peft_config["default"].lora_dropout = 0.2
    rows = [{"qid": str(index)} for index in range(35)]
    audits = {}
    for row in rows:
        batch = source[int(row["qid"]) % len(source)]
        target = int((batch["labels"] != -100).sum())
        sequence = batch["labels"].numel()
        audits[row["qid"]] = {"qid": row["qid"], "assistant_tokens_including_eos": target,
                               "prompt_tokens": sequence - target, "sequence_tokens": sequence, "visual_tokens": 16}
    manifest = {"protocol": binding(root / "protocol.json"), "training_ready": True, "rows": rows,
                "input_audits": list(audits.values()), "counts": {"training_rows": 35, "training_scenes": 2}}
    leases = [{"rank": index, "host": "synthetic-cpu-host", "attempt": phase,
               "admission_probe": {"synthetic": True}} for index in range(2)]
    events = []
    original_to, original_zeros, original_group = torch.Tensor.to, torch.zeros, dist.new_group
    original_save = checkpoints.save_checkpoint

    def cpu_to(tensor, *args, **kwargs):
        if args and isinstance(args[0], (str, torch.device)) and str(args[0]).startswith("cuda"):
            args = ("cpu", *args[1:])
        if str(kwargs.get("device", "")).startswith("cuda"):
            kwargs["device"] = "cpu"
        return original_to(tensor, *args, **kwargs)

    def cpu_zeros(*args, **kwargs):
        if str(kwargs.get("device", "")).startswith("cuda"):
            kwargs["device"] = "cpu"
        return original_zeros(*args, **kwargs)

    def lease_check(*args, fresh=True, **kwargs):
        events.append("fresh_lease" if fresh else "step_lease")
        return leases[rank]

    def live_probe(*args):
        events.append("live_probe")
        if phase == "resume_refused" and rank == 1:
            raise ValueError("synthetic expired live ownership")
        return leases[rank]

    def load_model(*args):
        events.append("load_model")
        return model

    def localize(values, store, manifest_path, *args):
        store.write("input_manifest.json", {"source_manifest": binding(manifest_path), "rows": values})
        return values

    def save(*args, **kwargs):
        result = original_save(*args, **kwargs)
        if phase == "partial" and args[4]["realized"]["optimizer_steps"] == 1:
            raise SyntheticPreemption
        return result

    output = root / ("reference" if phase == "reference" else "interrupted")
    resume = root / "interrupted/checkpoints/step_1" if phase.startswith("resume") else None
    with ExitStack() as stack:
        storage_patches(stack, root)
        stack.enter_context(patch.object(storage, "PUBLISH_HOME", root / "published"))
        for target, name, replacement in (
            (ddp_admission, "request_identity", lambda *a: {"ranks": [{"rank": 0}, {"rank": 1}], "protocol_sha256": "fixture"}),
            (ddp_admission, "load_bundle", lambda *a: {"ranks": leases}),
            (ddp_admission, "select_rank", lambda *a: (rank, 2, "synthetic-rank-0,synthetic-rank-1")),
            (ddp_admission, "require_rank_lease", lease_check), (ddp_admission, "admitted_rank", live_probe),
            (provisional_data, "load_protocol", lambda *a, **k: protocol),
            (provisional_data, "load_training", lambda *a: manifest),
            (ddp_training, "configure_environment", lambda *a: None),
            (ddp_training, "localize_frames", localize), (checkpoints, "localize_resume_frames", localize),
            (ddp_training, "memory_probe", lambda *a: {"rank": rank, "trials": [{"microbatch": 4, "fits": True, "seconds": 1.0}]}),
            (checkpoints, "save_checkpoint", save), (torch.Tensor, "to", cpu_to), (torch, "zeros", cpu_zeros),
            (torch, "autocast", lambda *a, **k: nullcontext()),
            (torch.nn.parallel, "DistributedDataParallel", CPUDistributedDataParallel),
            (dist, "new_group", lambda **k: original_group(backend="gloo", timeout=timedelta(seconds=90)))):
            stack.enter_context(patch.object(target, name, replacement))
        stack.enter_context(patch("student_pilot.batches.load_processor", return_value=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))))
        stack.enter_context(patch("student_pilot.runner.load_base", side_effect=load_model))
        stack.enter_context(patch("student_pilot.adapters.attach_ddp_adapters", return_value=(model, {
            "targets": {}, "trainable_parameters": settings["trainable_parameters"]})))
        stack.enter_context(patch("student_pilot.adapters.trainable_groups", return_value=groups))
        stack.enter_context(patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda processor, row:
            (source[int(row["qid"]) % len(source)], audits[row["qid"]])))
        stack.enter_context(patch("student_pilot.runner.memory_measurement", return_value={"max_reserved_bytes": 0}))
        for name in ("synchronize", "reset_peak_memory_stats"):
            stack.enter_context(patch.object(torch.cuda, name))
        if phase == "reference":
            stack.enter_context(patch.object(checkpoints, "due", return_value=False))
        try:
            outcome = ddp_training.train(root / "manifest.json", root / "protocol.json", output, root / f"{phase}_lease.json",
                                        scratch_root=root, stage_frames=True, provisional_diagnostic=LABEL, resume_from=resume)
        except SyntheticPreemption:
            assert phase == "partial"
            outcome = {"preempted": True}
        except ValueError as error:
            assert phase == "resume_refused", str(error)
            assert "load_model" not in events
            outcome = {"refused": str(error)}
        else:
            assert phase in ("reference", "resume")
            if rank == 0:
                receipt = storage.finalize(output, root / "published" / phase, root, provisional_diagnostic=LABEL)
                outcome["publication"] = receipt
        (root / f"{phase}_outcome_rank{rank}.json").write_bytes(canonical_bytes({"outcome": outcome, "events": events}))
        torch.save({name: parameter.detach().clone() for group in groups.values() for name, parameter in group},
                   root / f"{phase}_actual_rank{rank}.pt")
        assert not torch.cuda.is_initialized()


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class TrainerResumeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="trainer_resume_gloo_", dir=os.environ["LANE_TEST_OUTPUT"]))
        settings = ddp_config.normalize_training_config({"world_size": 2, "epochs": 2, "checkpoint_every_steps": 1,
                                                        "lora_dropout": 0.2, "learning_rate": 0.005}, "onethinker")
        run_control = ddp_config.normalize_run_control({"checkpoint_every_steps": 1})
        protocol = tag({"training": settings, "training_sha256": digest_json(settings), "protocol_version": ddp_config.VERSION,
                        "run_control": run_control, "run_control_sha256": digest_json(run_control),
                        "student": "onethinker", "base": {}, "base_sha256": "synthetic", "versions": {}, "runtime": [],
                        "PROVISIONAL_DIVISION_SHA": "synthetic", "rgb": {"synthetic": True},
                        "division": {"training_qids": [str(index) for index in range(35)], "heldout_qids": ["heldout"]}}, LABEL)
        (cls.root / "protocol.json").write_bytes(canonical_bytes(protocol))
        (cls.root / "manifest.json").write_bytes(canonical_bytes({"synthetic": True}))
        for phase in ("reference", "partial", "resume_refused", "resume"):
            (cls.root / f"{phase}_lease.json").write_bytes(canonical_bytes({"attempt": phase, "synthetic": True}))
            launch_workers(training_worker, str(cls.root), phase)

    def test_actual_train_loop_restores_adapters_scheduler_and_scientific_metrics(self):
        expected = torch.load(self.root / "reference_actual_rank0.pt", weights_only=True)
        for rank in range(2):
            actual = torch.load(self.root / f"resume_actual_rank{rank}.pt", weights_only=True)
            for name in expected:
                torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=1e-6)
        metrics = [[json.loads(line) for line in (self.root / directory / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()]
                   for directory in ("reference", "interrupted")]
        self.assertEqual([row["step"] for row in metrics[1]], [1, 2, 3, 4])
        fields = ("step", "epoch", "lr", "rows", "tokens", "prompt_tokens", "source_rows", "epoch_padding_rows",
                  "layout_padding_rows", "training_rows", "qids")
        for expected, actual in zip(*metrics):
            self.assertEqual({key: expected[key] for key in fields}, {key: actual[key] for key in fields})
            self.assertAlmostEqual(actual["loss"], expected["loss"], delta=1e-6)
            self.assertAlmostEqual(actual["gradient_norm_before_clip"], expected["gradient_norm_before_clip"], delta=1e-6)
            self.assertEqual(actual.get("resumed_from_step"), 1 if actual["step"] == 2 else None)
        results = [load_json(self.root / directory / "training_result.json") for directory in ("reference", "interrupted")]
        self.assertEqual(results[0]["realized"], results[1]["realized"])
        self.assertEqual(results[1]["completed_epochs"], 2)
        self.assertEqual(results[1]["status"], "TRAINED")

    def test_resume_requires_fresh_leases_and_collective_admission_before_model_load(self):
        for rank in range(2):
            refused = load_json(self.root / f"resume_refused_outcome_rank{rank}.json")
            self.assertIn("expired live ownership", refused["outcome"]["refused"])
            self.assertEqual(refused["events"], ["fresh_lease", "live_probe"])
            resumed = load_json(self.root / f"resume_outcome_rank{rank}.json")
            self.assertEqual(resumed["events"][:3], ["fresh_lease", "live_probe", "load_model"])
            self.assertIn("step_lease", resumed["events"])
        header = load_json(self.root / "interrupted/run.json")
        self.assertEqual(Path(header["lease"]["bundle"]["path"]).name, "resume_lease.json")
        self.assertEqual(header["resumed_from_step"], 1)
        self.assertEqual(header["provenance"], load_json(self.root / "reference/run.json")["provenance"])

    def test_actual_finalization_publishes_complete_prefix_and_resume_provenance(self):
        from safetensors.torch import load_file
        published = self.root / "published/resume"
        receipt = load_json(published / "PUBLISHED.json")
        self.assertEqual(receipt["schema"], "student-publication-v1")
        self.assertEqual(receipt["resumed_from"]["step"], 1)
        self.assertEqual(len((published / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()), 4)
        for step in range(1, 5):
            self.assertEqual(load_json(published / f"steps/{step:04d}.json")["step"], step)
        relative = storage.adapter_directory(LABEL) + "/adapter_model.safetensors"
        expected = load_file(str(self.root / "published/reference" / relative))
        actual = load_file(str(published / relative))
        for name in expected:
            torch.testing.assert_close(actual[name], expected[name], rtol=0, atol=1e-6)


if __name__ == "__main__":
    unittest.main()
