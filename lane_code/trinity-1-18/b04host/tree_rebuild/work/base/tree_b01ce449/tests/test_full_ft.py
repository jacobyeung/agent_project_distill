"""Full fine-tuning (full-ft-v1): config, groups and FP32 masters, the LoRA step-0 equality, one-step movement,
sharded clipping, rank-sharded checkpoints with bit-exact resume, retention, the BF16 export the evaluator loads,
the frozen-VLM alignment stage and its hand-off to stage 2."""
import copy
import hashlib
import io
import json
import multiprocessing
import os
import socket
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import torch
import torch.distributed as dist

from student_pilot import ddp_config, ddp_core, fsdp_training, full_ft, geometry_input
from student_pilot.common import canonical_bytes, digest_json, load_json, sha256
from tests.fullft_toys import bf16_batch, full_training_worker, source_rows, tiny_base
from tests.test_fsdp import SOCKETS
from tests.test_geometry_training import geometry_settings, make_protocol, run_pair, write_store


def output_root(prefix):
    return Path(tempfile.mkdtemp(prefix=prefix, dir=os.environ["LANE_TEST_OUTPUT"]))


ALL = {"llm": True, "vision_blocks": True, "merger": True}


class FullFTConfigTests(unittest.TestCase):
    def test_defaults_and_canonical_form(self):
        block = full_ft.normalize({})
        self.assertEqual(block["train"], {"llm": True, "vision_blocks": False, "merger": False})
        self.assertEqual(block["learning_rates"], {"llm": 1e-5, "geometry": 1e-4, "heads": 1e-4})
        self.assertEqual(block["init"], {"kind": "base"})
        self.assertFalse(full_ft.frozen_vlm(block))
        self.assertEqual(full_ft.normalize(block), block)
        both = full_ft.normalize({"train": ALL, "learning_rates": {"vision_blocks": 2e-6, "llm": 2e-5}})
        self.assertEqual(both["learning_rates"], {"llm": 2e-5, "vision_blocks": 2e-6, "merger": 1e-5, "geometry": 1e-4, "heads": 1e-4})
        frozen = full_ft.normalize({"train": {"llm": False}, "learning_rates": {"geometry": 1e-3}})
        self.assertTrue(full_ft.frozen_vlm(frozen))
        self.assertEqual(frozen["learning_rates"], {"geometry": 1e-3, "heads": 1e-4})

    def test_refusals(self):
        pin = {"path": "/x", "sha256": "a" * 64}
        for value in ({"extra": 1}, {"schema": "other"}, {"train": {"vision_blocks": True, "llm": False}},
                      {"train": {"llm": "yes"}}, {"learning_rates": {"vision_blocks": 1e-6}}, {"learning_rates": {"llm": 0}},
                      {"learning_rates": {"llm": 1.5}}, {"init": {"kind": "other"}},
                      {"train": {"llm": False}, "init": {"kind": "base_merged_init_adapter"}},
                      {"init_modules": {}}, {"init_modules": {"other": pin}}, {"init_modules": {"geometry": {"path": "/x"}}},
                      {"init_modules": {"geometry": {**pin, "sha256": "A" * 64}}}, {"master_dtype": "bfloat16"},
                      {"checkpoint": "full_state_dict"}, None, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                full_ft.normalize(value)

    def test_training_config_carries_the_block_and_lora_configs_are_unchanged(self):
        base = {"world_size": 32, "effective_batch_size": 256, "parallel": "fsdp", "lora_rank": 32, "lora_alpha": 64}
        plain = ddp_config.normalize_training_config(base, "qwen35")
        full = ddp_config.normalize_training_config({**base, "full_ft": {"train": ALL}}, "qwen35")
        self.assertNotIn("full_ft", plain)
        self.assertEqual({key: value for key, value in full.items() if key != "full_ft"}, plain)
        self.assertEqual(full["full_ft"], full_ft.normalize({"train": ALL}))
        self.assertEqual(ddp_config.normalize_training_config(json.loads(json.dumps(full)), "qwen35"), full)
        self.assertIn("full_ft.py", [Path(pin["path"]).name for pin in ddp_config.runtime_bindings()])
        with self.assertRaisesRegex(ValueError, "parallel=fsdp"):
            ddp_config.normalize_training_config({"world_size": 2, "full_ft": {}}, "qwen35")
        frozen = ddp_config.normalize_training_config({"world_size": 2, "full_ft": {"train": {"llm": False}}}, "qwen35")
        self.assertTrue(full_ft.frozen_vlm(frozen["full_ft"]))
        for extra in ({"unfreeze_vision_blocks": True}, {"head_learning_rate": 1e-4}):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "LoRA-path keys"):
                ddp_config.normalize_training_config({**base, **extra, "full_ft": {}}, "qwen35")

    def test_checkpoint_identity_names_the_block(self):
        from student_pilot.ddp_checkpoints import targets_identity
        full = ddp_config.normalize_training_config({"world_size": 2, "parallel": "fsdp", "full_ft": {}}, "qwen35")
        self.assertEqual(targets_identity(full)["full_ft"], full["full_ft"])
        self.assertNotIn("full_ft", targets_identity(ddp_config.normalize_training_config({"world_size": 2}, "qwen35")))


class FullFTModelTests(unittest.TestCase):
    def test_groups_cover_every_base_parameter_and_trained_ones_become_fp32_masters(self):
        for student in ("qwen35", "onethinker"):
            model = tiny_base(student)
            names = {name for name, _ in model.named_parameters()}
            groups, report = full_ft.prepare_model(model, full_ft.normalize({"train": ALL}))
            grouped = {name for parameters in groups.values() for name, _ in parameters}
            frozen = {name for name, p in model.named_parameters() if not p.requires_grad}
            self.assertEqual(grouped | frozen, names)
            self.assertEqual(grouped & frozen, set())
            self.assertTrue(frozen and all(full_ft.group_of(name) == "vision_frozen" for name in frozen), student)
            self.assertTrue(all(p.dtype == torch.float32 for p in model.parameters()))
            self.assertEqual(report["trainable_parameters"], sum(p.numel() for p in model.parameters() if p.requires_grad))
            self.assertEqual(report["mode"], "full")

    def test_llm_only_and_frozen_vlm(self):
        model = tiny_base()
        groups, report = full_ft.prepare_model(model, full_ft.normalize({}))
        self.assertEqual(set(groups), {"llm"})
        self.assertTrue(all(p.requires_grad == (full_ft.group_of(n) == "llm") for n, p in model.named_parameters()))
        self.assertTrue(any(n.startswith("lm_head.") for n, _ in groups["llm"]))
        self.assertTrue(any("embed_tokens" in n for n, _ in groups["llm"]))
        frozen = tiny_base()
        groups, report = full_ft.prepare_model(frozen, full_ft.normalize({"train": {"llm": False}}))
        self.assertEqual(groups, {})
        self.assertEqual(report["mode"], "frozen_vlm")
        self.assertTrue(all(p.dtype == torch.bfloat16 and not p.requires_grad for p in frozen.parameters()))

    def test_unknown_names_and_peft_models_refuse(self):
        with self.assertRaisesRegex(ValueError, "Unexpected base parameter"):
            full_ft.group_of("model.other.weight")
        from tests.test_ddp_models import NativeMultimodalBatchTests
        peft_model = NativeMultimodalBatchTests.fixture("qwen35")[0]
        with self.assertRaisesRegex(ValueError, "plain base"):
            full_ft.prepare_model(peft_model, full_ft.normalize({}))

    def test_merged_warm_start_equals_the_lora_forward_in_fp32(self):
        from peft import LoraConfig, get_peft_model
        from student_pilot.adapters import discover_targets
        base = tiny_base(dtype=torch.float32)
        reference = copy.deepcopy(base)
        targets = [name for group in discover_targets(base).values() for name in group]

        def attach(model, settings):
            peft_model = get_peft_model(model, LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, target_modules=targets))
            torch.manual_seed(3)
            with torch.no_grad():
                for name, parameter in peft_model.named_parameters():
                    if ".lora_" in name:
                        parameter.normal_(std=0.05)
            return peft_model, {"targets": {}}

        with patch("student_pilot.adapters.attach_ddp_adapters", side_effect=attach), \
                patch("student_pilot.warmstart.initialize_adapters",
                      side_effect=lambda model, report, *a, **k: {**report, "initialization": {"parent": "fixture"},
                                                                    "initialization_applied": True}):
            lora_reference, _ = attach(reference, {})
            merged, merge_report = full_ft.merge_init_adapter(base, {}, {}, None)
        self.assertEqual(merge_report["merge_dtype"], "float32")
        self.assertFalse(any(".lora_" in name for name, _ in merged.named_parameters()))
        batch = bf16_batch(ddp_core.collate_rows(source_rows(), 0))
        batch = {k: v.float() if v.is_floating_point() else v for k, v in batch.items()}
        with torch.no_grad():
            expected = ddp_core.row_losses(lora_reference.eval(), batch)
            actual = ddp_core.row_losses(merged.eval(), batch)
        torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)

    def test_export_round_trip_is_exact_and_tampering_refuses(self):
        root = output_root("fullft_export_")
        trained = tiny_base(dtype=torch.float32, seed=5)
        names = [name for name, _ in full_ft.base_parameters(trained)]
        state = {name: parameter.detach() for name, parameter in trained.named_parameters()}
        tensors = full_ft.export_tensors(state, names)
        with patch.object(full_ft, "EXPORT_SHARD_BYTES", 4096):
            manifest = full_ft.save_export(tensors, root / "full_weights", {"student": "qwen35"}, {"mode": "full"})
        self.assertGreater(len(manifest["files"]), 1)
        self.assertEqual(manifest["tensor_count"], len(names))
        fresh = tiny_base(seed=99)
        evidence = full_ft.load_export(fresh, root / "full_weights")
        self.assertTrue(evidence["full_weights_exact_equality"])
        for name, parameter in fresh.named_parameters():
            self.assertTrue(torch.equal(parameter, state[name].to(torch.bfloat16)), name)
        with self.assertRaisesRegex(ValueError, "cover every base tensor"):
            full_ft.export_tensors({k: v for k, v in state.items() if k != names[0]}, names)
        victim = root / "full_weights" / manifest["files"][0]["name"]
        victim.write_bytes(victim.read_bytes()[:-1] + b"\x00")
        with self.assertRaisesRegex(ValueError, "differs from its manifest"):
            full_ft.load_export(tiny_base(), root / "full_weights")

    def test_hashing_writer_hashes_exactly_the_saved_bytes(self):
        root = output_root("fullft_writer_")
        with (root / "x.pt").open("xb") as handle:
            writer = full_ft.HashingWriter(handle)
            torch.save({"a": torch.arange(1000.0)}, writer)
        self.assertEqual(writer.digest.hexdigest(), sha256(root / "x.pt"))
        self.assertEqual(writer.bytes, (root / "x.pt").stat().st_size)


# ---------------------------------------------------------------------------------------------- distributed

def pair(target, *args):
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
    context = multiprocessing.get_context("spawn")
    workers = [context.Process(target=target, args=(rank, port, *args)) for rank in range(2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(240)
        if worker.is_alive():
            worker.terminate()
            raise AssertionError("CPU/gloo worker timed out")
        if worker.exitcode != 0:
            raise AssertionError(f"CPU/gloo worker failed: {worker.exitcode}")


def equality_worker(rank, port, root):
    """Step 0 and an LR-0 step: FSDP LoRA (B = 0) against FSDP full fine-tuning on the same BF16 base."""
    from peft import LoraConfig, get_peft_model
    from student_pilot.adapters import discover_targets
    torch.set_num_threads(1)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=90))
    try:
        batch = ddp_core.collate_rows(source_rows(), 0)
        results = {}
        for kind in ("lora", "full"):
            model = tiny_base()
            if kind == "lora":
                targets = [name for group in discover_targets(model).values() for name in group]
                model = get_peft_model(model, LoraConfig(r=2, lora_alpha=4, lora_dropout=0.05, target_modules=targets),
                                       autocast_adapter_dtype=True)
                parameters = [p for p in model.parameters() if p.requires_grad]
                wrapped = fsdp_training.wrap_model(model, parameters, dist.group.WORLD, torch.device("cpu"))
            else:
                full_ft.prepare_model(model, full_ft.normalize({"train": ALL}))
                wrapped = full_ft.wrap_full_model(model, [], dist.group.WORLD, torch.device("cpu"))
                parameters = [p for _, p in full_ft.named_trainable(wrapped)]
            model.train()
            optimizer = torch.optim.AdamW(parameters, lr=0.0, weight_decay=0.0, foreach=False)
            losses = []
            for _ in range(2):
                optimizer.zero_grad(set_to_none=True)
                torch.manual_seed(11)
                loss = ddp_core.row_losses(wrapped, batch)
                loss.mean().backward()
                optimizer.step()
                losses.append(loss.detach().clone())
            results[kind] = losses
        torch.save(results, Path(root) / f"equality_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


def movement_worker(rank, port, root):
    """One AdamW step at 1e-3 on FSDP full fine-tuning: every trained element with a gradient moves, nothing else."""
    torch.set_num_threads(1)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=90))
    try:
        model = tiny_base()
        block = full_ft.normalize({"train": ALL})
        _, report = full_ft.prepare_model(model, block)
        wrapped = full_ft.wrap_full_model(model, [], dist.group.WORLD, torch.device("cpu"))
        sharded = full_ft.sharded_groups(wrapped, block)
        optimizer = full_ft.build_optimizer(sharded, {}, None, full_ft.normalize({"train": ALL, "learning_rates": {
            "llm": 1e-3, "vision_blocks": 1e-3, "merger": 1e-3}}), {"weight_decay": 0.0, "betas": [0.9, 0.999]})
        named = full_ft.named_trainable(wrapped)
        frozen_before = {n: p.detach().clone() for n, p in wrapped.named_parameters() if not p.requires_grad}
        before = {name: parameter.detach().clone() for name, parameter in named}
        loss = ddp_core.row_losses(wrapped, ddp_core.collate_rows(source_rows(), 0))
        loss.mean().backward()
        flow = full_ft.check_gradient_flow(sharded, report)
        grads = {name: (parameter.grad.detach().clone() if parameter.grad is not None else None) for name, parameter in named}
        global_full = full_ft.global_norm([p for _, p in named])
        norms = full_ft.clip_families(sharded, [], [], 1e9)
        optimizer.step()
        after = {name: parameter.detach().clone() for name, parameter in named}
        frozen_after = {n: p.detach().clone() for n, p in wrapped.named_parameters() if not p.requires_grad}
        updates = full_ft.group_report(sharded, values=before)
        torch.save({"before": before, "after": after, "grads": grads, "flow": flow, "updates": updates,
                    "norm": float(global_full), "clip_norms": norms, "report": report,
                    "frozen_unchanged": all(torch.equal(frozen_before[n], frozen_after[n]) for n in frozen_before),
                    "dtypes": sorted({str(p.dtype) for _, p in named})}, Path(root) / f"movement_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class FullFTDistributedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = output_root("fullft_distributed_")
        pair(equality_worker, str(cls.root))
        pair(movement_worker, str(cls.root))

    def test_step0_and_lr0_step_equal_the_lora_recipe_bit_for_bit(self):
        for rank in range(2):
            result = torch.load(self.root / f"equality_rank{rank}.pt", weights_only=True)
            for step in range(2):
                self.assertTrue(torch.equal(result["full"][step], result["lora"][step]), (rank, step))
            self.assertTrue(torch.equal(result["full"][0], result["full"][1]))

    def test_one_step_moves_every_trained_element_that_has_a_gradient(self):
        totals = {}
        for rank in range(2):
            result = torch.load(self.root / f"movement_rank{rank}.pt", weights_only=True)
            self.assertEqual(result["dtypes"], ["torch.float32"])
            self.assertTrue(result["frozen_unchanged"])
            for name, before in result["before"].items():
                grad = result["grads"][name]
                moved = result["after"][name] != before
                expected = (grad != 0) if grad is not None else torch.zeros_like(before, dtype=torch.bool)
                self.assertTrue(torch.equal(moved, expected), name)
                totals[name] = totals.get(name, 0) + int(moved.sum())
            for group, item in result["updates"].items():
                self.assertEqual(item["elements"], result["report"]["group_parameters"][group])
                self.assertGreater(item["l2"], 0)
            self.assertAlmostEqual(result["clip_norms"]["base"], result["norm"], places=5)
        # Every trained tensor moved somewhere across the two shards.
        self.assertTrue(all(count > 0 for count in totals.values()), [n for n, c in totals.items() if not c])

    def test_sharded_clip_matches_torch_clip_on_the_full_gradient(self):
        torch.manual_seed(4)
        full = [torch.nn.Parameter(torch.zeros(10)) for _ in range(3)]
        for parameter in full:
            parameter.grad = torch.randn(10) * 5
        reference = [torch.nn.Parameter(torch.zeros(10)) for _ in range(3)]
        for parameter, source in zip(reference, full):
            parameter.grad = source.grad.clone()
        expected = torch.nn.utils.clip_grad_norm_(reference, 1.0)
        with patch.object(dist, "all_reduce", lambda tensor, group=None: tensor):
            actual = full_ft.clip_sharded(full, 1.0)
        torch.testing.assert_close(actual, expected.float(), rtol=1e-6, atol=0)
        for parameter, other in zip(full, reference):
            torch.testing.assert_close(parameter.grad, other.grad, rtol=1e-6, atol=1e-7)


# ---------------------------------------------------------------------------------------------- train()

def full_protocol(root, extra, epochs=2, every=1):
    base = {"world_size": 2, "epochs": epochs, "learning_rate": 0.005, "parallel": "fsdp"}
    make_protocol(root, ddp_config.normalize_training_config({**base, **extra}, "onethinker"))
    if every != 1:
        # make_protocol pins checkpoint_every_steps 1; this run's milestone cadence replaces it.
        protocol = load_json(root / "protocol.json")
        run_control = ddp_config.normalize_run_control({"checkpoint_every_steps": every})
        protocol.update(run_control=run_control, run_control_sha256=digest_json(run_control))
        (root / "protocol.json").write_bytes(canonical_bytes(protocol))


def run_phases(root, phases, interrupt_step=1):
    for phase in phases:
        (root / f"{phase}_lease.json").write_bytes(canonical_bytes({"attempt": phase}))
        run_pair(full_training_worker, str(root), phase, interrupt_step)


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class FullFTTrainingTests(unittest.TestCase):
    """ddp_training.train end to end: reference, a run stopped after its step-1 checkpoint, and its resume."""

    @classmethod
    def setUpClass(cls):
        cls.root = output_root("fullft_training_")
        cls.block = {"train": ALL, "learning_rates": {"llm": 1e-3, "vision_blocks": 2e-4, "merger": 1e-3}}
        full_protocol(cls.root / "full", {"full_ft": cls.block})
        run_phases(cls.root / "full", ("reference", "partial", "resume"))
        with patch.dict(os.environ, {"FULLFT_TEST_ROLLING_MINUTES": "0.00001"}):
            full_protocol(cls.root / "rolling", {"full_ft": cls.block}, epochs=4, every=4)
            run_phases(cls.root / "rolling", ("reference",))

    def result(self, directory, phase, rank=0):
        return torch.load(self.root / directory / f"{phase}_rank{rank}.pt", weights_only=True)

    def test_resume_from_a_rank_sharded_checkpoint_is_bit_exact(self):
        for rank in range(2):
            reference, resumed = self.result("full", "reference", rank), self.result("full", "resume", rank)
            self.assertTrue(resumed["restored"])
            self.assertEqual(reference["trainables"].keys(), resumed["trainables"].keys())
            for name, tensor in reference["trainables"].items():
                self.assertTrue(torch.equal(resumed["trainables"][name], tensor), (rank, name))
        for step in range(1, 5):
            reference = load_json(self.root / "full/reference/steps" / f"{step:04d}.json")
            resumed = load_json(self.root / "full/interrupted/steps" / f"{step:04d}.json")
            self.assertEqual((reference["loss"], reference["qids"], reference["lr"]), (resumed["loss"], resumed["qids"], resumed["lr"]))
            self.assertEqual(reference["clip_norms_before_clip"], resumed["clip_norms_before_clip"])
        self.assertEqual(load_json(self.root / "full/interrupted/steps/0002.json")["resumed_from_step"], 1)

    def test_checkpoint_holds_one_shard_per_rank_and_the_trainer_metadata(self):
        directory = self.root / "full/interrupted/checkpoints/step_1"
        manifest = load_json(directory / "checkpoint.json")
        self.assertEqual(manifest["format"], "rank_sharded_v2")
        for rank in range(2):
            name = f"shards/rank{rank:03d}.pt"
            self.assertEqual(manifest["files"][name]["sha256"], sha256(directory / name))
            shard = torch.load(directory / name, weights_only=True)
            self.assertEqual(shard["rank"], rank)
            self.assertTrue(all(t.dtype == torch.float32 for t in shard["tensors"].values()))
            self.assertTrue(shard["optimizer"]["state"])
        self.assertNotIn("adapters.pt", manifest["files"])
        self.assertNotIn("replicated.pt", manifest["files"])  # this run attaches no modules
        rolling = [json.loads(line) for line in (self.root / "full/interrupted/checkpoints/ROLLING.jsonl").read_text().splitlines()]
        self.assertTrue(any(row.get("kind") == "milestone" and row["step"] == 1 for row in rolling))
        pinned = [json.loads(line) for line in (self.root / "full/interrupted/checkpoints/PINNED.jsonl").read_text().splitlines()]
        self.assertEqual([(row["kind"], row["step"]) for row in pinned], [("parent", 1)])

    def test_rolling_pool_keeps_two_full_states_and_milestones_pin_exports(self):
        root = self.root / "rolling/reference/checkpoints"
        live = sorted(int(path.name.removeprefix("step_")) for path in root.iterdir() if path.name.startswith("step_"))
        ledger = [json.loads(line) for line in (root / "ROLLING.jsonl").read_text().splitlines()]
        written = {row["step"]: row["kind"] for row in ledger if row["event"] == "written"}
        pruned = sorted(row["step"] for row in ledger if row["event"] == "pruned")
        self.assertFalse((root / "PINNED.jsonl").exists())
        self.assertEqual(written, {**{step: "rolling" for step in range(1, 8)}, 2: "epoch", 4: "milestone", 6: "epoch",
                                   8: "final"})
        self.assertEqual(live, [7, 8])
        self.assertEqual(pruned, list(range(1, 7)))
        milestones = [json.loads(line) for line in (root / "MILESTONES.jsonl").read_text().splitlines()]
        self.assertEqual([(row["step"], row["kind"]) for row in milestones], [(4, "milestone_export")])
        export = root / "milestone_4"
        manifest = load_json(export / "MILESTONE.json")
        self.assertEqual(milestones[0]["sha256"], sha256(export / "MILESTONE.json"))
        for name, pin in manifest["files"].items():
            self.assertEqual((sha256(export / name), (export / name).stat().st_size), (pin["sha256"], pin["bytes"]), name)
        self.assertFalse((export / "shards").exists())
        model = tiny_base(seed=123)
        self.assertTrue(full_ft.load_export(model, export / full_ft.EXPORT_DIRECTORY)["full_weights_exact_equality"])
        final = tiny_base(seed=123)
        from student_pilot.storage import adapter_directory
        from tests.test_geometry_training import LABEL
        full_ft.load_export(final, self.root / "rolling/reference" / adapter_directory(LABEL) / full_ft.EXPORT_DIRECTORY)
        self.assertFalse(all(torch.equal(a, b) for a, b in zip(model.parameters(), final.parameters())))

    def test_publication_exports_bf16_full_weights_that_load_exactly(self):
        from student_pilot.storage import adapter_directory
        from tests.test_geometry_training import LABEL
        result = load_json(self.root / "full/reference/training_result.json")
        self.assertEqual(result["full_ft"]["mode"], "full")
        self.assertEqual(result["adapter_parameters"], result["full_ft"]["trainable_parameters"])
        export = self.root / "full/reference" / adapter_directory(LABEL) / full_ft.EXPORT_DIRECTORY
        model = tiny_base(seed=123)
        self.assertTrue(full_ft.load_export(model, export)["full_weights_exact_equality"])
        # The export is the BF16 cast of the trained FP32 masters: rebuild them from both ranks' shards.
        live = dict(model.named_parameters())
        shards = [self.result("full", "reference", rank)["trainables"] for rank in range(2)]
        for name, parameter in live.items():
            if full_ft.group_of(name) == "vision_frozen":
                self.assertTrue(torch.equal(parameter, tiny_base().state_dict()[name]), name)
                continue
            flat = torch.cat([shard[name].flatten() for shard in shards])[:parameter.numel()]
            self.assertTrue(torch.equal(parameter.flatten(), flat.to(torch.bfloat16)), name)
        resumed = self.root / "full/interrupted" / adapter_directory(LABEL) / full_ft.EXPORT_DIRECTORY
        self.assertEqual(load_json(export / full_ft.EXPORT_MANIFEST)["files"], load_json(resumed / full_ft.EXPORT_MANIFEST)["files"])
        published = self.root / "full/published/reference" / adapter_directory(LABEL) / full_ft.EXPORT_DIRECTORY
        self.assertTrue(full_ft.read_export(published))


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class SignalStopTests(unittest.TestCase):
    """The full fine-tuning graceful stop: SIGUSR1 on one rank after step 2 saves and pins that step on every rank; the
    resumed run is bit-exact with the uninterrupted one, and a stale temporary from a killed save is removed."""

    @classmethod
    def setUpClass(cls):
        cls.root = output_root("fullft_signal_")
        block = {"train": ALL, "learning_rates": {"llm": 1e-3, "vision_blocks": 2e-4, "merger": 1e-3}}
        full_protocol(cls.root, {"full_ft": block}, every=4)
        run_phases(cls.root, ("reference", "signal"), interrupt_step=2)
        cls.stale = cls.root / "signalled/checkpoints" / f".step_3_{'ab' * 16}.tmp"
        cls.stale.mkdir()
        (cls.stale / "shards").mkdir()
        (cls.stale / "shards/rank000.pt").write_bytes(b"partial")
        cls.pinned_before_resume = (cls.root / "signalled/checkpoints/PINNED.jsonl").read_text()
        cls.marker = load_json(cls.root / "signalled/STOPPED_ON_SIGNAL.json")  # the resume moves it to _superseded/
        run_phases(cls.root, ("signal_resume",), interrupt_step=2)

    def result(self, phase, rank=0):
        return torch.load(self.root / f"{phase}_rank{rank}.pt", weights_only=True)

    def test_the_signal_saves_and_pins_the_current_step(self):
        for rank in range(2):
            outcome = self.result("signal", rank)["outcome"]
            self.assertEqual(outcome["status"], "STOPPED_ON_SIGNAL")
            self.assertEqual(outcome["realized"]["optimizer_steps"], 2)
        marker = self.marker
        self.assertEqual(marker["reasons"], [None, "SIGUSR1"])
        self.assertEqual((marker["step"], marker["kind"]), (2, "signal"))
        pinned = [json.loads(line) for line in self.pinned_before_resume.splitlines()]
        self.assertEqual([(row["kind"], row["step"]) for row in pinned], [("signal", 2)])
        self.assertEqual(pinned[0]["sha256"], marker["checkpoint_sha256"])

    def test_resume_from_the_signal_checkpoint_is_bit_exact(self):
        for rank in range(2):
            reference, resumed = self.result("reference", rank), self.result("signal_resume", rank)
            self.assertTrue(resumed["restored"])
            self.assertEqual(reference["trainables"].keys(), resumed["trainables"].keys())
            for name, tensor in reference["trainables"].items():
                self.assertTrue(torch.equal(resumed["trainables"][name], tensor), (rank, name))
        for step in range(1, 5):
            reference = load_json(self.root / "reference/steps" / f"{step:04d}.json")
            resumed = load_json(self.root / "signalled/steps" / f"{step:04d}.json")
            self.assertEqual((reference["loss"], reference["qids"], reference["lr"], reference["clip_norms_before_clip"]),
                             (resumed["loss"], resumed["qids"], resumed["lr"], resumed["clip_norms_before_clip"]))
        self.assertEqual(load_json(self.root / "signalled/steps/0003.json")["resumed_from_step"], 2)

    def test_a_tampered_shard_stops_every_rank(self):
        import shutil
        from tests.test_geometry_training import run_pair
        copy = self.root / "tampered_checkpoint/step_2"
        shutil.copytree(self.root / "signalled/checkpoints/step_2", copy)
        shard = copy / "shards/rank001.pt"
        payload = bytearray(shard.read_bytes())
        payload[-1] ^= 1  # same size: only rank 1's own sha256 check can see it
        shard.chmod(0o644)
        shard.write_bytes(bytes(payload))
        (self.root / "tampered_resume_lease.json").write_bytes(canonical_bytes({"attempt": "tampered_resume"}))
        with self.assertRaisesRegex(ValueError, "Checkpoint restore refused: rank 1"):
            run_pair(full_training_worker, str(self.root), "tampered_resume", 2)

    def test_a_stale_temporary_is_removed_and_the_signal_state_stays_pinned(self):
        self.assertFalse(self.stale.exists())
        root = self.root / "signalled/checkpoints"
        self.assertTrue((root / "step_2").is_dir())
        self.assertFalse(any(path.name.startswith((".step_", ".pruned_")) for path in root.iterdir()))


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class TwoStageTrainingTests(unittest.TestCase):
    """Stage 1 trains only the geometry adapter on a frozen BF16 VLM; stage 2 loads it and fine-tunes everything."""

    @classmethod
    def setUpClass(cls):
        cls.root = output_root("fullft_two_stage_")
        manifest = write_store(cls.root / "store")
        cls.geometry = geometry_settings(manifest, geometry_input.CROSS_INJECTION)
        full_protocol(cls.root / "stage1", {"full_ft": {"train": {"llm": False}, "learning_rates": {"geometry": 1e-2}},
                                            "geometry": cls.geometry})
        run_phases(cls.root / "stage1", ("reference", "partial", "resume"))
        weights = cls.root / "stage1/reference/geometry" / geometry_input.WEIGHTS_NAME
        cls.pin = {"path": str(weights), "sha256": sha256(weights)}
        full_protocol(cls.root / "stage2", {"full_ft": {"train": ALL, "init_modules": {"geometry": cls.pin}},
                                            "geometry": cls.geometry})
        run_phases(cls.root / "stage2", ("reference", "partial", "resume"))

    def test_stage1_trains_only_the_adapter_and_keeps_the_base(self):
        result = load_json(self.root / "stage1/reference/training_result.json")
        self.assertEqual(result["adapter"], {"frozen_vlm": True})
        self.assertEqual(result["full_ft"]["mode"], "frozen_vlm")
        self.assertTrue(result["frozen_base_unchanged"])
        self.assertIsNotNone(result["geometry"])
        trainables = self.result("stage1", "reference")["trainables"]
        self.assertTrue(trainables and all(name.startswith("geometry_input.") for name in trainables))
        start = geometry_input.GeometryCrossAttention(8, 16)
        self.assertGreater(float(trainables["geometry_input.projector.o.weight"].abs().sum()), 0)
        self.assertEqual(start.o.weight.count_nonzero(), 0)
        for rank in range(2):
            reference, resumed = self.result("stage1", "reference", rank), self.result("stage1", "resume", rank)
            for name, tensor in reference["geometry"].items():
                self.assertTrue(torch.equal(resumed["geometry"][name], tensor), name)

    def test_stage2_starts_from_the_stage1_adapter_exactly(self):
        result = load_json(self.root / "stage2/reference/training_result.json")
        self.assertEqual(result["full_ft"]["init_modules"]["geometry"]["sha256"], self.pin["sha256"])
        report = load_json(self.root / "stage2/reference/adapters.json")
        self.assertEqual(report["init_modules"]["geometry"]["sha256"], self.pin["sha256"])
        first = load_json(self.root / "stage2/reference/steps/0001.json")
        self.assertIn("geometry", first["clip_norms_before_clip"])
        self.assertIn("base", first["clip_norms_before_clip"])
        self.assertEqual(set(first["learning_rates"]), {"llm", "vision_blocks", "merger", "geometry"})

    def test_rank0_alone_saves_the_replicated_adapter_and_resume_is_bit_exact(self):
        directory = self.root / "stage2/interrupted/checkpoints/step_1"
        manifest = load_json(directory / "checkpoint.json")
        self.assertEqual(manifest["files"]["replicated.pt"]["sha256"], sha256(directory / "replicated.pt"))
        replicated = torch.load(directory / "replicated.pt", weights_only=True)
        names = sorted(replicated["tensors"])
        self.assertTrue(names and all(name.startswith("geometry_input.") for name in names))
        self.assertEqual(len(replicated["optimizer_state"]), len(names))
        for rank in range(2):
            shard = torch.load(directory / f"shards/rank{rank:03d}.pt", weights_only=True)
            self.assertFalse(any(name.startswith("geometry_input.") for name in shard["tensors"]))
            self.assertTrue(set(shard["optimizer"]["state"]).isdisjoint(replicated["optimizer_state"]))
            reference, resumed = self.result("stage2", "reference", rank), self.result("stage2", "resume", rank)
            self.assertTrue(resumed["restored"])
            for name, tensor in reference["trainables"].items():
                self.assertTrue(torch.equal(resumed["trainables"][name], tensor), (rank, name))
            for name, tensor in reference["geometry"].items():
                self.assertTrue(torch.equal(resumed["geometry"][name], tensor), (rank, name))
        # Milestone exports carry the adapter beside the BF16 export.
        milestones = [json.loads(line) for line in
                      (self.root / "stage2/reference/checkpoints/MILESTONES.jsonl").read_text().splitlines()]
        self.assertEqual([row["step"] for row in milestones], [1, 2, 3])
        export = self.root / "stage2/reference/checkpoints/milestone_3"
        self.assertIn("geometry/" + geometry_input.WEIGHTS_NAME, load_json(export / "MILESTONE.json")["files"])

    def test_a_wrong_stage1_pin_refuses(self):
        block = full_ft.normalize({"train": ALL, "init_modules": {"geometry": {**self.pin, "sha256": "0" * 64}}})
        module = geometry_input.GeometryInput(geometry_input.normalize(self.geometry), 16)
        with self.assertRaisesRegex(ValueError, "pinned sha256"):
            full_ft.load_init_modules(block, geometry=module)
        good = full_ft.normalize({"train": ALL, "init_modules": {"geometry": self.pin}})
        self.assertEqual(full_ft.load_init_modules(good, geometry=module)["geometry"]["sha256"], self.pin["sha256"])
        with self.assertRaisesRegex(ValueError, "does not attach"):
            full_ft.load_init_modules(good)

    def result(self, directory, phase, rank=0):
        return torch.load(self.root / directory / f"{phase}_rank{rank}.pt", weights_only=True)


class SpatialMLLMConnectorTests(unittest.TestCase):
    """The G3T adapter of GXS and PDG: Spatial-MLLM's mlp_add connector over 2x2 x 2-frame patch-grid cells."""

    def test_patch_tokens_follow_spatial_mllm_order(self):
        rng = torch.Generator().manual_seed(1)
        array = torch.randn(32, 4, 6, 3, generator=rng).numpy().astype("float16")
        tokens = geometry_input.patch_tokens(array, (16, 4, 6))
        self.assertEqual(tuple(tokens.shape), (16 * 2 * 3, 4 * 3 * 2))
        # Spatial-MLLM: view(t, 2, D, h, 2, w, 2).permute(t, h, w, 2, 2, D, 2) on a (frame, channel, row, col) tensor.
        reference = torch.from_numpy(array).permute(0, 3, 1, 2).reshape(16, 2, 3, 2, 2, 3, 2)
        reference = reference.permute(0, 3, 5, 4, 6, 2, 1).reshape(16 * 2 * 3, -1)
        self.assertTrue(torch.equal(tokens, reference))
        with self.assertRaisesRegex(ValueError, "patch grid"):
            geometry_input.patch_tokens(array[:, :2], (16, 4, 6))

    def test_connector_matches_the_source_layers_and_adds_to_the_merged_tokens(self):
        settings = geometry_input.normalize({**geometry_settings(write_store(output_root("spatial_store_") / "s", cells=(2, 2)),
                                                                 geometry_input.SPATIAL_INJECTION)})
        module = geometry_input.GeometryInput(settings, 16)
        connector = module.projector
        self.assertIsInstance(connector, geometry_input.SpatialMLLMConnector)
        width = 2 * 2 * 2 * 8
        self.assertEqual([tuple(p.shape) for p in connector.parameters()],
                         [(width,), (width, width), (width,), (16, width), (16,)])
        self.assertEqual(geometry_input.token_width(settings), width)
        features = torch.randn(5, width)
        x = features.float()
        normed = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + 1e-6)
        expected = connector.mlp[2](torch.nn.functional.gelu(connector.mlp[0](normed)))
        self.assertTrue(torch.allclose(connector(features), expected, atol=1e-6))
        self.assertGreater(float(connector(features).abs().sum()), 0)  # no zero start, as in the source
        self.assertEqual(geometry_input.store_grid(settings, (16, 4, 4)), (4, 4))
        self.assertEqual(geometry_input.store_grid(geometry_input.normalize(geometry_settings(
            write_store(output_root("merged_store_") / "s"))), (16, 4, 4)), (2, 2))

    def test_connector_init_is_the_source_hf_init(self):
        # Spatial-MLLM: from_pretrained fills the missing connector with Qwen2.5-VL's _init_weights (normal 0.02, zero
        # bias); the RMSNorm keeps its ones.
        connector = geometry_input.SpatialMLLMConnector(256, 96)
        self.assertEqual(geometry_input.SPATIAL_MLLM["init"], "hf_init_weights_normal_0.02_bias_0_norm_1")
        self.assertTrue(torch.equal(connector.ln_q.weight, torch.ones(2048)))
        for layer in (connector.fc1, connector.fc2):
            self.assertEqual(layer.bias.count_nonzero(), 0)
            weight = layer.weight.double()
            self.assertLess(abs(float(weight.mean())), 2e-4)
            self.assertAlmostEqual(float(weight.std()), 0.02, delta=2e-4)


class CarrierTokenizer:
    """The tiny base's ids for the camera carrier and the video pad token."""
    ids = {"<|fim_middle|>": 59, "<|video_pad|>": 61}
    pad_token_id = 0

    def convert_tokens_to_ids(self, token):
        return self.ids[token]

    def encode(self, text, add_special_tokens=False):
        return [self.ids[text]] if text in self.ids else [5]


def pdg_worker(rank, port, root, mode):
    """PDG's composition on the tiny native Qwen3.5: camera head + carriers + video-context G3T adapter, under full
    FSDP (mode 'full') or the frozen-VLM stage (mode 'frozen')."""
    from student_pilot import auxiliary_losses, camera_config
    from student_pilot.camera_targets import insert_tokens
    from student_pilot.ddp_training import attach_geometry, geometry_batch
    from tests.test_camera import PIN, SMALL, record_for
    from tests.test_geometry_training import student_row
    torch.set_num_threads(1)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank, world_size=2,
                            timeout=timedelta(seconds=90))
    try:
        model = tiny_base()
        block = full_ft.normalize({"train": ALL} if mode == "full" else {"train": {"llm": False}})
        _, report = full_ft.prepare_model(model, block)
        tokenizer = CarrierTokenizer()
        heads = auxiliary_losses.attach(model, None, tokenizer, camera_config.normalize({"weight": 1.0, **SMALL, "supervision": PIN}))
        manifest = Path(root) / "store/manifest.jsonl"
        settings = geometry_input.normalize(geometry_settings(manifest, geometry_input.SPATIAL_INJECTION))
        geometry = attach_geometry(model, settings, 17)
        store = geometry_input.FeatureStore(settings)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
        replicated = list(heads.parameters()) + list(geometry.projector.parameters())
        wrapped = (full_ft.wrap_full_model(model, replicated, dist.group.WORLD, torch.device("cpu")) if mode == "full"
                   else fsdp_training.wrap_model(model, replicated, dist.group.WORLD, torch.device("cpu")))
        rows = [geometry_batch(insert_tokens(row, record_for(index), tokenizer), student_row(index), store)
                for index, row in enumerate(source_rows())]
        batch = ddp_core.collate_rows(rows, 0)
        losses = ddp_core.row_losses(wrapped, batch)
        losses.sum().backward()
        fsdp_training.average_adapter_gradients(replicated, dist.group.WORLD)
        result = {"losses": losses.detach(), "camera": heads.last_terms["camera"].detach(),
                  "carriers": int((batch["input_ids"] == 59).sum()), "geometry_calls": geometry.calls,
                  "head_grads": all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in heads.parameters()),
                  "carrier_token_grad": float(heads.camera.tokens.grad.abs().sum()),
                  "geometry_output_grad": float(geometry.projector.fc2.weight.grad.abs().sum())}
        if mode == "full":
            result["flow"] = full_ft.check_gradient_flow(full_ft.sharded_groups(wrapped, block), report)
        torch.save(result, Path(root) / f"pdg_{mode}_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class PDGCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = output_root("fullft_pdg_")
        write_store(cls.root / "store", cells=(2, 2))
        for mode in ("full", "frozen"):
            pair(pdg_worker, str(cls.root), mode)

    def test_heads_carriers_and_adapter_train_under_both_stages(self):
        for rank in range(2):
            full = torch.load(self.root / f"pdg_full_rank{rank}.pt", weights_only=True)
            frozen = torch.load(self.root / f"pdg_frozen_rank{rank}.pt", weights_only=True)
            # The same adapter (seeded) and the same BF16 compute: both stages see the same step-0 losses.
            self.assertTrue(torch.equal(full["losses"], frozen["losses"]))
            self.assertTrue(torch.equal(full["camera"], frozen["camera"]))
            for result in (full, frozen):
                self.assertEqual(result["carriers"], 32)
                self.assertEqual(result["geometry_calls"], 1)
                self.assertTrue(result["head_grads"])
                self.assertGreater(result["carrier_token_grad"], 0)
                self.assertGreater(result["geometry_output_grad"], 0)
                self.assertTrue(bool((result["camera"] > 0).all()))
            self.assertEqual(set(full["flow"]), {"llm", "vision_blocks", "merger"})


if __name__ == "__main__":
    unittest.main()
