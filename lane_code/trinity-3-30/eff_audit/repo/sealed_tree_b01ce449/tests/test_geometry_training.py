"""Geometry input (geometry-input-v1) in the DDP/FSDP trainer: config, batches, zero-init identity, refusals, and
CPU/gloo training through ddp_training.train with checkpoint, resume and publication."""
import copy
import hashlib
import json
import multiprocessing
import os
import socket
import tempfile
import unittest
from contextlib import ExitStack, nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch
import torch.distributed as dist

from student_pilot import ddp_checkpoints as checkpoints
from student_pilot import ddp_config, ddp_core, ddp_training, fsdp_training, geometry_input, storage
from student_pilot.common import canonical_bytes, digest_json, load_json, sha256
from student_pilot.provisional import tag
from tests import test_ddp_models
from tests.test_ddp_checkpoints import CPUDistributedDataParallel, SyntheticPreemption, storage_patches
from tests.test_fsdp import SOCKETS

LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
# The shared module must stay byte-identical to the evaluator's copy (this branch's orchard_eval imports it).
MODULE_SHA256 = "e3fbcaacd836fe1491b197cf7d91b8bf7af68bfb18b1e7897fb9414b4e06e2c7"
FEATURE_DIM = 8
ENCODER = {"name": "g3t", "repository": "fixture", "revision": "fixture", "source_sha256": "0" * 64,
           "input": "square_pad_518", "pooling": "roi_align_valid_region"}
VIDEOS = 5
ROWS = 35
GRADIENT_SCALE = 1e4


def frames_for(video):
    return [hashlib.sha256(f"video{video}:frame{index}".encode()).hexdigest() for index in range(32)]


def write_store(root, videos=range(VIDEOS), cells=(1, 1)):
    """A sealed feature store for the fixture videos; the fixture grid (16, 2, 2) merges to one cell per frame."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    generator = np.random.default_rng(5)
    lines = []
    for video in videos:
        frames = frames_for(video)
        array = generator.standard_normal((32, *cells, FEATURE_DIM)).astype(np.float16)
        np.save(root / f"v{video}.npy", array)
        lines.append(json.dumps({"key": geometry_input.frame_key(frames), "frames": frames, "file": f"v{video}.npy",
                                 "sha256": geometry_input.file_sha256(root / f"v{video}.npy"),
                                 "shape": [32, *cells, FEATURE_DIM], "dtype": "float16", "layer": 23, "encoder": ENCODER}))
    (root / "manifest.jsonl").write_text("\n".join(lines) + "\n")
    return root / "manifest.jsonl"


# The zero-initialised output layer of each injection's module.
OUTPUT_LAYER = {geometry_input.INJECTION: "fc2", geometry_input.CROSS_INJECTION: "o"}


def geometry_settings(manifest, injection=geometry_input.INJECTION):
    return {"schema": geometry_input.SCHEMA, "injection": injection, "layer": 23, "feature_dim": FEATURE_DIM,
            "frames_per_token": 2, "projector": dict(geometry_input.INJECTIONS[injection]), "encoder": dict(ENCODER),
            "store": {"manifest": str(manifest), "manifest_sha256": geometry_input.file_sha256(manifest)}}


def student_row(index):
    return {"qid": str(index), "student_input": {"frames": [{"path": f"/fixture/{sha}", "sha256": sha}
                                                            for sha in frames_for(index % VIDEOS)]}}


def output_root(prefix):
    return Path(tempfile.mkdtemp(prefix=prefix, dir=os.environ["LANE_TEST_OUTPUT"]))


class GeometryConfigTests(unittest.TestCase):
    def setUp(self):
        self.root = output_root("geometry_config_")
        self.block = geometry_settings(write_store(self.root / "store"))

    def test_module_is_the_shared_byte_identical_copy(self):
        self.assertEqual(sha256(Path(geometry_input.__file__)), MODULE_SHA256)

    def test_block_normalizes_into_settings_and_absence_is_unchanged(self):
        base = {"world_size": 32, "effective_batch_size": 256, "parallel": "fsdp", "lora_rank": 32, "lora_alpha": 64}
        plain = ddp_config.normalize_training_config(base, "qwen35")
        settings = ddp_config.normalize_training_config({**base, "geometry": self.block}, "qwen35")
        self.assertNotIn("geometry", plain)
        self.assertEqual(settings["geometry"], geometry_input.normalize(self.block))
        self.assertEqual({key: value for key, value in settings.items() if key != "geometry"}, plain)
        # A frozen protocol stores the normalized settings and re-normalizes them identically.
        self.assertEqual(ddp_config.normalize_training_config(json.loads(json.dumps(settings)), "qwen35"), settings)
        names = [Path(pin["path"]).name for pin in ddp_config.runtime_bindings()]
        self.assertIn("geometry_input.py", names)

    def test_unknown_or_malformed_blocks_refuse(self):
        base = {"world_size": 2}
        for block in ({**self.block, "extra": 1}, {key: value for key, value in self.block.items() if key != "store"},
                      {**self.block, "projector": {**geometry_input.PROJECTOR, "hidden": 512}},
                      {**self.block, "layer": 24}, {**self.block, "feature_dim": 0},
                      {**self.block, "store": {**self.block["store"], "manifest_sha256": "A" * 64}}, None, []):
            with self.subTest(block=block), self.assertRaises(ValueError):
                ddp_config.normalize_training_config({**base, "geometry": block}, "onethinker")


class GeometryModelTests(unittest.TestCase):
    def setUp(self):
        self.root = output_root("geometry_model_")
        self.manifest = write_store(self.root / "store")
        self.block = ddp_config.normalize_training_config({"world_size": 2, "geometry": geometry_settings(self.manifest)},
                                                          "onethinker")["geometry"]
        self.store = geometry_input.FeatureStore(self.block)
        self.model, self.groups, _, self.rows = test_ddp_models.NativeMultimodalBatchTests.fixture("qwen35")
        torch.manual_seed(29)
        with torch.no_grad():
            for name, parameter in self.model.named_parameters():
                if "lora_B" in name:
                    parameter.normal_(std=0.02)

    def feature_batch(self, videos=(0, 1)):
        rows = [ddp_training.geometry_batch(row, student_row(video), self.store) for row, video in zip(self.rows, videos)]
        return ddp_core.collate_rows(rows, 0)

    def test_features_follow_the_merged_token_order_and_concatenate_in_row_order(self):
        batch = self.feature_batch((3, 1))
        expected = [geometry_input.tokens(np.load(self.manifest.parent / f"v{video}.npy"), (16, 2, 2)) for video in (3, 1)]
        self.assertEqual(batch["geometry_features"].dtype, torch.float16)
        self.assertEqual(tuple(batch["geometry_features"].shape), (32, 2 * FEATURE_DIM))
        self.assertTrue(torch.equal(batch["geometry_features"], torch.cat(expected)))
        array = np.load(self.manifest.parent / "v3.npy")
        # Token t pairs frames 2t and 2t+1 in frame order.
        self.assertTrue(torch.equal(batch["geometry_features"][5], torch.from_numpy(np.concatenate([array[10, 0, 0], array[11, 0, 0]]))))

    def test_zero_initialized_projector_keeps_losses_and_lora_gradients_and_trains_its_output_layer(self):
        reference = copy.deepcopy(self.model)
        plain = ddp_core.collate_rows(self.rows, 0)
        expected = ddp_core.row_losses(reference, plain)
        expected.mean().backward()
        state = torch.get_rng_state()
        geometry = ddp_training.attach_geometry(self.model, self.block, 17)
        self.assertTrue(torch.equal(torch.get_rng_state(), state), "projector init must not move the training RNG")
        twin = ddp_training.attach_geometry(copy.deepcopy(reference), self.block, 17)
        for (name, value), (_, other) in zip(geometry.state_dict().items(), twin.state_dict().items()):
            self.assertTrue(torch.equal(value, other), name)
        actual = ddp_core.row_losses(self.model, self.feature_batch())
        actual.mean().backward()
        self.assertTrue(torch.equal(actual, expected))
        reference_parameters = dict(reference.named_parameters())
        for name, parameter in self.model.named_parameters():
            if name.startswith("geometry_input."):
                continue
            if parameter.requires_grad:
                self.assertTrue(torch.equal(parameter.grad, reference_parameters[name].grad), name)
        # One hook call per forward: non-reentrant checkpointing recomputes vision blocks, never the tower's merger output.
        self.assertEqual(geometry.calls, 1)
        self.assertGreater(float(geometry.projector.fc2.weight.grad.abs().sum()), 0)
        self.assertIsNotNone(geometry.projector.fc1.weight.grad)
        self.assertEqual(sum(p.numel() for p in geometry.projector.parameters()),
                         2 * 2 * FEATURE_DIM + 2 * FEATURE_DIM * 1024 + 1024 + 1024 * 16 + 16)

    def test_zero_initialized_cross_attention_keeps_losses_and_lora_gradients(self):
        block = geometry_input.normalize({**self.block, "injection": geometry_input.CROSS_INJECTION,
                                          "projector": geometry_input.CROSS_ATTENTION})
        reference = copy.deepcopy(self.model)
        expected = ddp_core.row_losses(reference, ddp_core.collate_rows(self.rows, 0))
        expected.mean().backward()
        state = torch.get_rng_state()
        geometry = ddp_training.attach_geometry(self.model, block, 17)
        self.assertIsInstance(geometry.projector, geometry_input.GeometryCrossAttention)
        self.assertTrue(torch.equal(torch.get_rng_state(), state))
        actual = ddp_core.row_losses(self.model, self.feature_batch())
        actual.mean().backward()
        self.assertTrue(torch.equal(actual, expected))
        reference_parameters = dict(reference.named_parameters())
        for name, parameter in self.model.named_parameters():
            if parameter.requires_grad and not name.startswith("geometry_input."):
                self.assertTrue(torch.equal(parameter.grad, reference_parameters[name].grad), name)
        self.assertEqual(geometry.calls, 1)
        self.assertGreater(float(geometry.projector.o.weight.grad.abs().sum()), 0)
        self.assertTrue(all(parameter.grad is not None for parameter in geometry.projector.parameters()))

    def test_refusals_leave_no_pending_features(self):
        with self.assertRaisesRegex(ValueError, "without a geometry input"):
            ddp_core.row_losses(self.model, self.feature_batch())
        geometry = ddp_training.attach_geometry(self.model, self.block, 17)
        with self.assertRaisesRegex(ValueError, "requires geometry features"):
            ddp_core.row_losses(self.model, ddp_core.collate_rows(self.rows, 0))
        batch = self.feature_batch()
        wrong = {**batch, "geometry_features": batch["geometry_features"][:-1]}
        with self.assertRaisesRegex(ValueError, "Geometry features cover"):
            ddp_core.row_losses(self.model, wrong)
        self.assertIsNone(geometry._pending)
        ddp_core.row_losses(self.model, batch)
        self.assertEqual(geometry.calls, 1)
        with self.assertRaisesRegex(ValueError, "do not match the student grid"):
            ddp_training.geometry_batch({**self.rows[0], "video_grid_thw": torch.tensor([[16, 4, 2]])}, student_row(0), self.store)
        unknown = {"qid": "x", "student_input": {"frames": [{"sha256": sha} for sha in frames_for(99)]}}
        with self.assertRaisesRegex(ValueError, "No geometry features"):
            ddp_training.geometry_batch(self.rows[0], unknown, self.store)

    def test_startup_coverage_refuses_missing_rows_and_grid_mismatch(self):
        audits = {str(index): {"video_grid_thw": [[16, 2, 2]]} for index in range(8)}
        rows = [student_row(index) for index in range(8)]
        with patch.object(ddp_training, "gather", side_effect=lambda value, world: [value] * world):
            store, report = ddp_training.open_geometry_store(self.block, rows, audits, 2)
            self.assertEqual(report["missing_rows"] + report["grid_mismatch_rows"], 0)
            self.assertEqual((report["admitted_rows"], report["feature_files_used"]), (8, VIDEOS))
            partial = write_store(self.root / "partial", videos=range(VIDEOS - 1))
            with self.assertRaisesRegex(ValueError, r"1 of 8 admitted rows have no store row"):
                ddp_training.open_geometry_store(geometry_input.normalize(geometry_settings(partial)), rows, audits, 2)
            with self.assertRaisesRegex(ValueError, "differ from their processor grid"):
                ddp_training.open_geometry_store(self.block, rows, {**audits, "3": {"video_grid_thw": [[16, 4, 2]]}}, 2)
            moved = {**self.block, "store": {**self.block["store"], "manifest_sha256": "f" * 64}}
            with self.assertRaisesRegex(ValueError, "pinned sha256"):
                ddp_training.open_geometry_store(moved, rows, audits, 2)

    def test_memory_probe_and_training_batches_carry_the_features(self):
        rows = [student_row(index) for index in range(4)]
        audits = {row["qid"]: {"qid": row["qid"], "sequence_tokens": 60 + index, "visual_tokens": 16,
                               "assistant_tokens_including_eos": 2 + index} for index, row in enumerate(rows)}
        settings = ddp_config.normalize_training_config({"world_size": 2, "max_microbatch_size": 2}, "onethinker")
        processor = SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))
        seen = []

        def candidate(model, parameters, cpu_rows, size, *args, **kwargs):
            seen.append(cpu_rows)
            return {"microbatch": size, "fits": True, "seconds": 1.0}

        with patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda processor, row:
                   (self.rows[int(row["qid"]) % 2], audits[row["qid"]])), \
                patch("student_pilot.students.student_for_model", return_value="qwen35"), \
                patch.object(torch.cuda, "empty_cache"), patch.object(ddp_training, "probe_candidate", side_effect=candidate):
            ddp_training.memory_probe(self.model, processor, rows, audits, settings, 0, lambda: None, self.store)
            batch = ddp_training.encode_microbatch(processor, rows, audits, [2, 0], self.store)
        self.assertTrue(seen and all("geometry_features" in row for cpu_rows in seen for row in cpu_rows))
        self.assertEqual(tuple(seen[0][0]["geometry_features"].shape), (16, 2 * FEATURE_DIM))
        expected = torch.cat([self.store.tokens(frames_for(index), (16, 2, 2)) for index in (2, 0)])
        self.assertTrue(torch.equal(batch["geometry_features"], expected))


def with_grad(grad):
    parameter = torch.nn.Parameter(torch.zeros_like(grad))
    parameter.grad = grad.clone()
    return parameter


class GeometryClipTests(unittest.TestCase):
    def test_lora_clip_ignores_the_projector_and_the_projector_clips_to_the_same_norm(self):
        torch.manual_seed(3)
        grads = [torch.randn(5, 7) * 3 for _ in range(3)]
        control = [with_grad(grad) for grad in grads]
        expected_norm = torch.nn.utils.clip_grad_norm_(control, 1.0, error_if_nonfinite=True)
        for scale in (1e-3, 1.0, 1e6):
            lora = [with_grad(grad) for grad in grads]
            projector = [with_grad(torch.randn(4, 4) * scale), with_grad(torch.randn(4) * scale)]
            before = float(torch.stack([parameter.grad.norm() for parameter in projector]).norm())
            norm, geometry_norm = ddp_training.clip_gradients(lora, projector, 1.0)
            self.assertTrue(torch.equal(norm, expected_norm))
            for parameter, reference in zip(lora, control):
                self.assertTrue(torch.equal(parameter.grad, reference.grad))
            self.assertAlmostEqual(geometry_norm, before, delta=before * 1e-6)
            after = float(torch.stack([parameter.grad.norm() for parameter in projector]).norm())
            self.assertAlmostEqual(after, min(before, 1.0), delta=1e-5)
        lora = [with_grad(grad) for grad in grads]
        norm, geometry_norm = ddp_training.clip_gradients(lora, [], 1.0)
        self.assertTrue(torch.equal(norm, expected_norm))
        self.assertIsNone(geometry_norm)


# CPU/gloo training through the real ddp_training.train: rank 0 runs in this process and rank 1 in one child, so a
# run never holds more than two processes.

def run_pair(target, *args):
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
    child = multiprocessing.get_context("spawn").Process(target=target, args=(1, port, *args))
    child.start()
    try:
        target(0, port, *args)
    finally:
        child.join(300)
        if child.is_alive():
            child.terminate()
            child.join(10)
            raise AssertionError("Geometry CPU/gloo rank 1 timed out")
    if child.exitcode != 0:
        raise AssertionError(f"Geometry CPU/gloo rank 1 failed: {child.exitcode}")


def training_worker(rank, port, root, phase):
    from student_pilot import ddp_admission, provisional_data
    from student_pilot.common import binding

    torch.set_num_threads(1)
    root = Path(root)
    protocol = load_json(root / "protocol.json")
    settings = protocol["training"]
    parallel = settings.get("parallel", "ddp")
    model, groups, _, source = test_ddp_models.NativeMultimodalBatchTests.fixture("qwen35")
    for module in list(model.modules()):
        if hasattr(module, "lora_dropout"):
            for name in module.lora_dropout:
                module.lora_dropout[name] = torch.nn.Dropout(0.2)
    model.peft_config["default"].lora_dropout = 0.2
    rows = [student_row(index) for index in range(ROWS)]
    audits = {}
    for row in rows:
        batch = source[int(row["qid"]) % len(source)]
        target = int((batch["labels"] != -100).sum())
        sequence = batch["labels"].numel()
        audits[row["qid"]] = {"qid": row["qid"], "assistant_tokens_including_eos": target, "prompt_tokens": sequence - target,
                              "sequence_tokens": sequence, "visual_tokens": 16, "video_grid_thw": [[16, 2, 2]]}
    manifest = {"protocol": binding(root / "protocol.json"), "training_ready": True, "rows": rows,
                "input_audits": list(audits.values()), "counts": {"training_rows": ROWS, "training_scenes": 2}}
    leases = [{"rank": index, "host": "synthetic-cpu-host", "attempt": phase, "admission_probe": {"synthetic": True}}
              for index in range(2)]
    events = {"forwards": 0, "restored": None, "clips": []}
    original_to, original_zeros, original_group = torch.Tensor.to, torch.zeros, dist.new_group
    original_save, original_restore = checkpoints.save_checkpoint, checkpoints.restore_checkpoint
    original_losses, original_wrap = ddp_core.row_losses, fsdp_training.wrap_model
    original_attach, original_clip = ddp_training.attach_geometry, torch.nn.utils.clip_grad_norm_
    lora_ids = {id(parameter) for group in groups.values() for _, parameter in group}

    def attach(*args, **kwargs):
        module = original_attach(*args, **kwargs)
        # A projector gradient 1e4 times its natural size: the LoRA path must not notice it.
        for parameter in module.projector.parameters():
            parameter.register_hook(lambda grad: grad * GRADIENT_SCALE)
        return module

    def clip(parameters, *args, **kwargs):
        parameters = list(parameters)
        result = original_clip(parameters, *args, **kwargs)
        geometry = getattr(model, "geometry_input", None)
        ids = {id(parameter) for parameter in parameters}
        kind = ("lora" if ids == lora_ids else
                "geometry" if geometry is not None and ids == {id(parameter) for parameter in geometry.projector.parameters()}
                else "other")
        events["clips"].append([kind, float(result)])
        return result

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

    def save(*args, **kwargs):
        result = original_save(*args, **kwargs)
        if phase == "partial" and args[4]["realized"]["optimizer_steps"] == 1:
            raise SyntheticPreemption
        return result

    def restore(directory, checkpoint, adapters, *args, **kwargs):
        result = original_restore(directory, checkpoint, adapters, *args, **kwargs)
        events["restored"] = {name: value.detach().clone() for name, value in adapters.items() if name.startswith("geometry_input.")}
        return result

    def losses(*args, **kwargs):
        events["forwards"] += 1
        return original_losses(*args, **kwargs)

    def wrap(model, parameters, process_group, device, **kwargs):
        return original_wrap(model, parameters, process_group, torch.device("cpu"), mixed_precision=True, **kwargs)

    output = root / ("interrupted" if phase in ("partial", "resume") else phase)
    resume = root / "interrupted/checkpoints/step_1" if phase == "resume" else None
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, {"MASTER_ADDR": "127.0.0.1", "MASTER_PORT": str(port), "RANK": str(rank),
                                                    "WORLD_SIZE": "2"}))
        storage_patches(stack, root)
        stack.enter_context(patch.object(storage, "PUBLISH_HOME", root / "published"))
        for target, name, replacement in (
            (ddp_admission, "request_identity", lambda *a: {"ranks": [{"rank": 0}, {"rank": 1}], "protocol_sha256": "fixture"}),
            (ddp_admission, "load_bundle", lambda *a: {"ranks": leases}),
            (ddp_admission, "select_rank", lambda *a: (rank, 2, "synthetic-rank-0,synthetic-rank-1")),
            (ddp_admission, "require_rank_lease", lambda *a, **k: leases[rank]),
            (ddp_admission, "admitted_rank", lambda *a: leases[rank]),
            (provisional_data, "load_protocol", lambda *a, **k: protocol),
            (provisional_data, "load_training", lambda *a: manifest),
            (ddp_training, "configure_environment", lambda *a: None),
            (ddp_training, "localize_frames", lambda values, store, path, *a: (store.write("input_manifest.json", {
                "source_manifest": binding(path), "rows": values}), values)[1]),
            (checkpoints, "localize_resume_frames", lambda values, store, path, *a: values),
            (ddp_training, "memory_probe", lambda *a, **k: {"rank": rank, "probed_geometry": "geometry" in k,
                                                              "trials": [{"microbatch": 4, "fits": True, "seconds": 1.0}]}),
            (checkpoints, "save_checkpoint", save), (checkpoints, "restore_checkpoint", restore),
            (ddp_core, "row_losses", losses), (fsdp_training, "wrap_model", wrap),
            (ddp_training, "attach_geometry", attach), (torch.nn.utils, "clip_grad_norm_", clip),
            (torch.Tensor, "to", cpu_to), (torch, "zeros", cpu_zeros),
            (torch, "autocast", lambda *a, **k: nullcontext()),
            (torch.nn.parallel, "DistributedDataParallel", CPUDistributedDataParallel),
            (dist, "new_group", lambda **k: original_group(backend="gloo", timeout=timedelta(seconds=90)))):
            stack.enter_context(patch.object(target, name, replacement))
        stack.enter_context(patch("student_pilot.batches.load_processor", return_value=SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))))
        stack.enter_context(patch("student_pilot.runner.load_base", return_value=model))
        stack.enter_context(patch("student_pilot.adapters.attach_ddp_adapters", return_value=(model, {
            "targets": {}, "trainable_parameters": settings["trainable_parameters"]})))
        stack.enter_context(patch("student_pilot.adapters.trainable_groups", return_value=groups))
        stack.enter_context(patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda processor, row:
            (source[int(row["qid"]) % len(source)], audits[row["qid"]])))
        stack.enter_context(patch("student_pilot.runner.memory_measurement", return_value={"max_reserved_bytes": 0}))
        for name in ("synchronize", "reset_peak_memory_stats"):
            stack.enter_context(patch.object(torch.cuda, name))
        try:
            outcome = ddp_training.train(root / "manifest.json", root / "protocol.json", output, root / f"{phase}_lease.json",
                                         scratch_root=root, stage_frames=True, provisional_diagnostic=LABEL,
                                         resume_from=resume, parallel=parallel)
        except SyntheticPreemption:
            assert phase == "partial"
            outcome = {"preempted": True}
        else:
            if rank == 0:
                outcome["publication"] = storage.finalize(output, root / "published" / phase, root, provisional_diagnostic=LABEL)
    geometry = getattr(model, "geometry_input", None)
    torch.save({"lora": {name: parameter.detach().clone() for group in groups.values() for name, parameter in group},
                "geometry": None if geometry is None else {name: value.detach().clone() for name, value in geometry.projector.state_dict().items()},
                "calls": None if geometry is None else geometry.calls, "forwards": events["forwards"], "restored": events["restored"],
                "clips": events["clips"],
                "outcome": json.loads(canonical_bytes(outcome))}, root / f"{phase}_rank{rank}.pt")
    assert not torch.cuda.is_initialized()


def make_protocol(root, settings):
    run_control = ddp_config.normalize_run_control({"checkpoint_every_steps": 1})
    protocol = tag({"training": settings, "training_sha256": digest_json(settings), "protocol_version": ddp_config.VERSION,
                    "run_control": run_control, "run_control_sha256": digest_json(run_control),
                    "student": "onethinker", "base": {}, "base_sha256": "synthetic", "versions": {}, "runtime": [],
                    "PROVISIONAL_DIVISION_SHA": "synthetic", "rgb": {"synthetic": True},
                    "division": {"training_qids": [str(index) for index in range(ROWS)], "heldout_qids": ["heldout"]}}, LABEL)
    root.mkdir(parents=True, exist_ok=True)
    (root / "protocol.json").write_bytes(canonical_bytes(protocol))
    (root / "manifest.json").write_bytes(canonical_bytes({"synthetic": True}))


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class GeometryTrainingTests(unittest.TestCase):
    parallel = "ddp"
    injection = geometry_input.INJECTION

    @classmethod
    def setUpClass(cls):
        cls.root = output_root(f"geometry_training_{OUTPUT_LAYER[cls.injection]}_{cls.parallel}_")
        base = {"world_size": 2, "epochs": 2, "checkpoint_every_steps": 1, "lora_dropout": 0.2, "learning_rate": 0.005,
                "parallel": cls.parallel}
        cls.block = geometry_settings(write_store(cls.root / "store"), cls.injection)
        make_protocol(cls.root / "control", ddp_config.normalize_training_config(base, "onethinker"))
        make_protocol(cls.root / "geometry", ddp_config.normalize_training_config({**base, "geometry": cls.block}, "onethinker"))
        for directory, phases in (("control", ("reference", "partial")), ("geometry", ("reference", "partial", "resume"))):
            for phase in phases:
                (cls.root / directory / f"{phase}_lease.json").write_bytes(canonical_bytes({"attempt": phase}))
                run_pair(training_worker, str(cls.root / directory), phase)

    def result(self, directory, phase, rank=0):
        return torch.load(self.root / directory / f"{phase}_rank{rank}.pt", weights_only=True)

    def test_first_step_matches_the_control_exactly(self):
        control, geometry = (load_json(self.root / name / "reference/steps/0001.json") for name in ("control", "geometry"))
        self.assertEqual(control["loss"], geometry["loss"])
        self.assertEqual(control["qids"], geometry["qids"])
        self.assertNotIn("geometry_gradient_norm_before_clip", control)
        self.assertGreater(geometry["geometry_gradient_norm_before_clip"], 0)
        flows = [load_json(self.root / name / "reference/gradient_flow.json") for name in ("control", "geometry")]
        self.assertEqual(flows[0]["groups"], flows[1]["groups"])
        self.assertNotIn("geometry", flows[0])
        self.assertGreater(flows[1]["geometry"]["gradient_l2"], 0)
        self.assertEqual(flows[1]["geometry"]["gradient_tensors"], len(self.result("geometry", "reference")["geometry"]))
        self.assertEqual(len(self.result("geometry", "reference")["geometry"]),
                         {geometry_input.INJECTION: 6, geometry_input.CROSS_INJECTION: 13}[self.injection])

    def test_lora_updates_and_clip_ignore_a_large_projector_gradient(self):
        # Step 1: the zero-initialised projector leaves the forward unchanged, so the LoRA update equals the control's
        # bit for bit although the projector gradient is forced 1e4 times larger.
        for rank in range(2):
            control, geometry = self.result("control", "partial", rank), self.result("geometry", "partial", rank)
            self.assertEqual(control["lora"].keys(), geometry["lora"].keys())
            for name, tensor in control["lora"].items():
                self.assertTrue(torch.equal(geometry["lora"][name], tensor), name)
        # Milestone checkpoints are pinned (9467aac5 retention), so step_1 stays in checkpoints/ for both runs.
        saved = [torch.load(self.root / name / "interrupted/checkpoints/step_1/adapters.pt", weights_only=True)
                 for name in ("control", "geometry")]
        lora = [name for name in saved[0]]
        self.assertTrue(lora and all(torch.equal(saved[0][name], saved[1][name]) for name in lora))
        first = [load_json(self.root / name / "reference/steps/0001.json") for name in ("control", "geometry")]
        self.assertEqual(first[0]["gradient_norm_before_clip"], first[1]["gradient_norm_before_clip"])
        self.assertGreater(first[1]["geometry_gradient_norm_before_clip"], 100 * first[1]["gradient_norm_before_clip"])
        # Every step: one clip over exactly the LoRA tensors (the logged norm) and one over exactly the projector.
        for name, kinds in (("control", ["lora"]), ("geometry", ["lora", "geometry"])):
            for rank in range(2):
                clips = self.result(name, "reference", rank)["clips"]
                self.assertEqual([kind for kind, _ in clips], kinds * 4, (name, rank))
            clips = self.result(name, "reference")["clips"]
            for step in range(1, 5):
                metric = load_json(self.root / name / f"reference/steps/{step:04d}.json")
                self.assertEqual(metric["gradient_norm_before_clip"], clips[(step - 1) * len(kinds)][1])
                if name == "geometry":
                    self.assertEqual(metric["geometry_gradient_norm_before_clip"], clips[(step - 1) * 2 + 1][1])
        # From step 2 on the trained projector adds a nonzero term to the video tokens, so the LoRA gradients (and
        # updates) legitimately differ from the control; only their clipping stays independent of the projector.
        second = [load_json(self.root / name / "reference/steps/0002.json") for name in ("control", "geometry")]
        self.assertNotEqual(second[0]["loss"], second[1]["loss"])

    def test_hook_runs_once_per_forward_and_the_projector_trains(self):
        for phase in ("reference", "partial", "resume"):
            for rank in range(2):
                value = self.result("geometry", phase, rank)
                self.assertGreater(value["forwards"], 0)
                self.assertEqual(value["calls"], value["forwards"], (phase, rank))
        final = self.result("geometry", "reference")["geometry"]
        self.assertGreater(float(final[OUTPUT_LAYER[self.injection] + ".weight"].abs().sum()), 0)
        other = self.result("geometry", "reference", 1)["geometry"]
        for name, tensor in final.items():
            self.assertTrue(torch.equal(tensor, other[name]), name)
        probes = [load_json(self.root / name / "reference/memory_probe.json")["ranks"] for name in ("control", "geometry")]
        self.assertEqual([[rank["probed_geometry"] for rank in ranks] for ranks in probes], [[False, False], [True, True]])
        adapters = load_json(self.root / "geometry/reference/adapters.json")
        self.assertEqual(adapters["geometry_parameters"], sum(tensor.numel() for tensor in final.values()))
        self.assertEqual(load_json(self.root / "geometry/reference/geometry_store.json")["missing_rows"], 0)
        updates = load_json(self.root / "geometry/reference/adapter_updates.json")
        self.assertGreater(updates["geometry"]["update_l2"], 0)
        self.assertNotIn("geometry", load_json(self.root / "control/reference/adapter_updates.json"))

    def test_checkpoint_and_resume_restore_the_projector_exactly(self):
        checkpoint = self.root / "geometry/interrupted/checkpoints/_superseded/step_1"
        if not checkpoint.is_dir():
            checkpoint = self.root / "geometry/interrupted/checkpoints/step_1"
        saved = torch.load(checkpoint / "adapters.pt", weights_only=True)
        partial = self.result("geometry", "partial")["geometry"]
        for name, tensor in partial.items():
            self.assertTrue(torch.equal(saved["geometry_input.projector." + name], tensor), name)
        names = load_json(checkpoint / "checkpoint.json")["optimizer_parameters"]
        self.assertIn(f"geometry_input.projector.{OUTPUT_LAYER[self.injection]}.weight", names[0])
        for rank in range(2):
            restored = self.result("geometry", "resume", rank)["restored"]
            self.assertEqual(set(restored), {"geometry_input.projector." + name for name in partial})
            for name, tensor in partial.items():
                self.assertTrue(torch.equal(restored["geometry_input.projector." + name], tensor), name)
            reference, resumed = self.result("geometry", "reference", rank), self.result("geometry", "resume", rank)
            for kind in ("geometry", "lora"):
                for name, tensor in reference[kind].items():
                    torch.testing.assert_close(resumed[kind][name], tensor, rtol=0, atol=1e-6)

    def test_publication_carries_a_loadable_projector_beside_the_unchanged_adapter(self):
        from safetensors.torch import load_file

        for phase in ("reference", "resume"):
            published = self.root / "geometry/published" / phase
            files = load_json(published / "SHA256_MANIFEST.json")["files"]
            for name in ("geometry/geometry_projector.safetensors", "geometry/geometry_input.json"):
                self.assertIn(name, files)
                self.assertEqual(sha256(published / name), files[name]["sha256"])
            adapter = load_file(str(published / storage.adapter_directory(LABEL) / "adapter_model.safetensors"))
            pairs = [{name.replace(f".lora_{side}.", ".") for name in adapter if f".lora_{side}." in name} for side in "AB"]
            self.assertTrue(pairs[0] and pairs[0] == pairs[1] and len(adapter) == 2 * len(pairs[0]))
            result = load_json(published / "training_result.json")
            self.assertEqual(result["geometry"]["weights"]["sha256"], files["geometry/geometry_projector.safetensors"]["sha256"])
            self.assertEqual(result["settings"]["geometry"], geometry_input.normalize(self.block))
            model, _, _, _ = test_ddp_models.NativeMultimodalBatchTests.fixture("qwen35")
            module = geometry_input.load(model, published / "geometry", self.block)
            self.assertEqual(module.cross, self.injection == geometry_input.CROSS_INJECTION)
            trained = self.result("geometry", "reference" if phase == "reference" else "resume")["geometry"]
            for name, tensor in module.projector.state_dict().items():
                self.assertTrue(torch.equal(tensor, trained[name]), name)
        control = self.root / "control/published/reference"
        self.assertFalse((control / "geometry").exists())
        self.assertNotIn("geometry", load_json(control / "training_result.json"))


class GeometryFSDPTrainingTests(GeometryTrainingTests):
    parallel = "fsdp"


class GeometryCrossAttentionTrainingTests(GeometryTrainingTests):
    injection = geometry_input.CROSS_INJECTION


class GeometryCrossAttentionFSDPTrainingTests(GeometryTrainingTests):
    injection = geometry_input.CROSS_INJECTION
    parallel = "fsdp"


if __name__ == "__main__":
    unittest.main()
