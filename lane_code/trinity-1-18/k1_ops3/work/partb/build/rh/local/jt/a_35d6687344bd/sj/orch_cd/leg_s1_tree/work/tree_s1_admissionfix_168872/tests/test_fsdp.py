"""CPU contract checks; real two-process equivalence requires local sockets."""
import copy
import json
import multiprocessing
import os
import socket
import tempfile
import unittest
from contextlib import nullcontext
from datetime import timedelta
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

import torch
import torch.distributed as dist
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.nn.parallel import DistributedDataParallel as DDP

from student_pilot import ddp_config, ddp_core, ddp_training, fsdp_training
from student_pilot.common import digest_json
from student_pilot.runner import adapter_snapshot, group_gradients
from tests import test_ddp_models


def sockets_available():
    try:
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
        return True
    except OSError:
        return False


SOCKETS = sockets_available()


def fixture(student, bf16=False):
    model, groups, _, source = test_ddp_models.NativeMultimodalBatchTests.fixture(student)
    if bf16:
        for parameter in model.parameters():
            if not parameter.requires_grad:
                parameter.data = parameter.data.bfloat16()
    # Eight fixed RGB rows retain mixed target lengths and all three adapter groups.
    rows = [copy.deepcopy(source[index % 2]) for index in range(8)]
    return model, groups, rows


def equivalence_worker(rank, port, root, parallel, student, bf16):
    torch.set_num_threads(1)
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank,
                            world_size=2, timeout=timedelta(seconds=90))
    try:
        model, groups, rows = fixture(student, bf16)
        parameters = [p for group in groups.values() for _, p in group]
        frozen_full = {name: p.detach().clone() for name, p in model.named_parameters() if not p.requires_grad}
        distributed = (fsdp_training.wrap_model(model, parameters, dist.group.WORLD, torch.device("cpu"),
                                               mixed_precision=bf16)
                       if parallel == "fsdp" else DDP(model, broadcast_buffers=False))
        if parallel == "fsdp":
            before = fsdp_training.frozen_shard_fingerprints(distributed)
            owned = sum(p.numel() for p in distributed.parameters() if not p.requires_grad)
            assert owned < sum(p.numel() for p in frozen_full.values()), "Frozen base was not sharded"
        optimizer = torch.optim.AdamW(parameters, lr=0.01, weight_decay=0.0, foreach=False)
        assert {id(p) for g in optimizer.param_groups for p in g["params"]} == {
            id(p) for p in distributed.parameters() if p.requires_grad}
        losses = []
        for _ in range(2):
            optimizer.zero_grad(set_to_none=True)
            slots = ddp_core.rank_slots(list(range(8)), rank, 2, 1)
            local = torch.zeros((), dtype=torch.float64)
            for index, (row, weight) in enumerate(slots):
                context = torch.autocast("cpu", dtype=torch.bfloat16) if bf16 else nullcontext()
                value = ddp_core.backward_batch(distributed, rows[row], [weight], 2, 8,
                    synchronize=parallel == "fsdp" or index == len(slots) - 1, forward_context=context)
                local += value.double().sum()
            if parallel == "fsdp":
                fsdp_training.average_adapter_gradients(parameters, dist.group.WORLD)
            group_gradients(groups)
            torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
            optimizer.step()
            dist.all_reduce(local)
            losses.append(local.item() / 8)
        optimizer.zero_grad(set_to_none=True)
        if parallel == "fsdp":
            fsdp_training.check_frozen_shards(distributed, before)
            state = fsdp_training.publication_state(distributed)
            assert rank == 0 or not state
        else:
            state = model.state_dict()
        if rank == 0:
            for name, value in frozen_full.items():
                assert torch.equal(state[name], value), name
            adapter_path = Path(root) / parallel
            model.save_pretrained(adapter_path, state_dict=state, safe_serialization=True, save_embedding_layers=False)
        result = {"losses": losses, "adapter": adapter_snapshot(groups),
                  "frozen_unchanged": True, "optimizer_allowlist": True}
        torch.save(result, Path(root) / f"{parallel}_rank{rank}.pt")
    finally:
        dist.destroy_process_group()


@unittest.skipUnless(SOCKETS, "requires local sockets: sandbox denies 127.0.0.1 bind")
class FSDPTwoProcessTests(unittest.TestCase):
    """Socket-required acceptance tests (a)-(d), using genuine CPU/gloo."""
    @classmethod
    def setUpClass(cls):
        cls.runs = []
        for student, bf16 in (("onethinker", False), ("qwen35", False), ("qwen35", True)):
            root = Path(tempfile.mkdtemp(prefix="fsdp_gloo_", dir=os.environ["LANE_TEST_OUTPUT"]))
            for parallel in ("ddp", "fsdp"):
                with socket.socket() as server:
                    server.bind(("127.0.0.1", 0))
                    port = server.getsockname()[1]
                context = multiprocessing.get_context("spawn")
                workers = [context.Process(target=equivalence_worker,
                            args=(rank, port, str(root), parallel, student, bf16)) for rank in range(2)]
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(120)
                for worker in workers:
                    if worker.is_alive():
                        worker.terminate()
                        worker.join(10)
                        raise AssertionError("CPU/gloo worker timed out")
                    if worker.exitcode != 0:
                        raise AssertionError(f"CPU/gloo worker failed: {worker.exitcode}")
            cls.runs.append((student, bf16, root))

    def test_a_two_process_loss_and_adapter_updates_match_ddp(self):
        for student, bf16, root in self.runs:
            reference = torch.load(root / "ddp_rank0.pt", weights_only=True)
            for rank in range(2):
                actual = torch.load(root / f"fsdp_rank{rank}.pt", weights_only=True)
                with self.subTest(student=student, bf16=bf16, rank=rank):
                    torch.testing.assert_close(torch.tensor(actual["losses"]), torch.tensor(reference["losses"]),
                                               rtol=0, atol=1e-5)
                    self.assertEqual(actual["adapter"].keys(), reference["adapter"].keys())
                    for name, value in reference["adapter"].items():
                        torch.testing.assert_close(actual["adapter"][name], value, rtol=0, atol=1e-5)

    def test_b_published_adapter_keys_and_values_match_ddp(self):
        from safetensors.torch import load_file
        for student, bf16, root in self.runs:
            with self.subTest(student=student, bf16=bf16):
                reference = load_file(str(root / "ddp/adapter_model.safetensors"))
                actual = load_file(str(root / "fsdp/adapter_model.safetensors"))
                self.assertEqual(actual.keys(), reference.keys())
                for name, value in reference.items():
                    self.assertEqual(actual[name].dtype, torch.float32)
                    torch.testing.assert_close(actual[name], value, rtol=0, atol=1e-6)
                configs = [json.loads((root / parallel / "adapter_config.json").read_text())
                           for parallel in ("ddp", "fsdp")]
                for config in configs:
                    config["target_modules"].sort()
                self.assertEqual(*configs)

    def test_c_frozen_base_parameters_unchanged_after_steps(self):
        for _, _, root in self.runs:
            for rank in range(2):
                self.assertTrue(torch.load(root / f"fsdp_rank{rank}.pt", weights_only=True)["frozen_unchanged"])

    def test_d_optimizer_parameters_equal_adapter_allowlist(self):
        for _, _, root in self.runs:
            for rank in range(2):
                self.assertTrue(torch.load(root / f"fsdp_rank{rank}.pt", weights_only=True)["optimizer_allowlist"])


class FSDPContractTests(unittest.TestCase):
    def test_default_ddp_config_stays_unchanged_and_fsdp_settings_are_pinned(self):
        ddp = ddp_config.normalize_training_config({}, "qwen35")
        self.assertNotIn("parallel", ddp)
        fsdp = ddp_config.normalize_training_config({"parallel": "fsdp"}, "qwen35")
        self.assertEqual(fsdp["sharding"], fsdp_training.SHARDING)
        self.assertEqual(fsdp, ddp_config.normalize_training_config(fsdp, "qwen35"))
        self.assertNotEqual(digest_json(ddp), digest_json(fsdp))
        for value in ({"parallel": "other"}, {"sharding": {}}, {"parallel": "fsdp", "sharding": {}}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ddp_config.normalize_training_config(value, "qwen35")

    def test_mismatched_cli_mode_refuses_before_lease_or_model_loading(self):
        settings = ddp_config.normalize_training_config({"parallel": "fsdp"}, "qwen35")
        with patch("student_pilot.ddp_admission.input_path", side_effect=lambda p: p), \
                patch("student_pilot.provisional.load_json", return_value={}), \
                patch.object(ddp_training, "require_mode"), \
                patch.object(ddp_training, "validate_training_protocol", return_value=settings), \
                patch("student_pilot.ddp_admission.request_identity") as request:
            with self.assertRaisesRegex(ValueError, "Parallel mode"):
                ddp_training.train("unused", "unused", "unused", "unused", student="qwen35",
                                   provisional_diagnostic="ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW")
            request.assert_not_called()

    def test_wrap_policy_covers_decoder_and_vision_and_preserves_adapter_identity(self):
        for student in ("onethinker", "qwen35"):
            model, groups, _ = fixture(student)
            params = [p for group in groups.values() for _, p in group]
            with patch.object(fsdp_training, "FSDP", return_value=model) as wrapper, \
                    patch.object(dist, "broadcast") as broadcast:
                fsdp_training.wrap_model(model, params, None, torch.device("cpu"))
            options = wrapper.call_args.kwargs
            classes = {cls.__name__ for cls in options["auto_wrap_policy"]._module_classes}
            self.assertEqual(len(classes), 2)
            self.assertTrue(any("DecoderLayer" in name for name in classes))
            self.assertTrue(any("VisionBlock" in name for name in classes))
            self.assertIs(options["ignored_states"], params)
            self.assertTrue(options["use_orig_params"])
            self.assertEqual(options["mixed_precision"].param_dtype, torch.bfloat16)
            self.assertEqual(options["mixed_precision"].reduce_dtype, torch.bfloat16)
            self.assertEqual(broadcast.call_count, len(params))
            with self.assertRaisesRegex(ValueError, "allowlist"):
                fsdp_training.wrap_model(model, params[:-1], None, torch.device("cpu"))

    def test_adapter_gradient_average_matches_mean_and_rejects_missing_gradients(self):
        parameter = torch.nn.Parameter(torch.tensor([1.0]))
        parameter.grad = torch.tensor([4.0])
        with patch.object(dist, "get_world_size", return_value=2), \
                patch.object(dist, "all_reduce", side_effect=lambda tensor, **kwargs: tensor.add_(8)):
            fsdp_training.average_adapter_gradients([parameter], None)
        self.assertEqual(parameter.grad.item(), 6.0)
        parameter.grad = None
        with patch.object(dist, "get_world_size", return_value=2), self.assertRaisesRegex(ValueError, "gradient"):
            fsdp_training.average_adapter_gradients([parameter], None)

    def test_publication_gathers_every_rank_and_returns_cpu_state_only_on_rank_zero(self):
        for device in ("cpu", "cuda"):
            for rank in (0, 1):
                with self.subTest(device=device, rank=rank):
                    state = torch.nn.Linear(2, 2).state_dict()
                    metadata = state._metadata
                    adapter = Mock(spec=torch.Tensor)
                    adapter.cpu.return_value = torch.ones(2, dtype=torch.float32)
                    state["adapter"] = adapter
                    model = SimpleNamespace(process_group=object(), state_dict=Mock(return_value=state),
                        parameters=lambda: iter([SimpleNamespace(device=torch.device(device))]))
                    with patch.object(FSDP, "state_dict_type", return_value=nullcontext()) as context, \
                            patch.object(dist, "get_rank", return_value=rank) as get_rank:
                        actual = fsdp_training.publication_state(model)
                    model.state_dict.assert_called_once_with()
                    get_rank.assert_called_once_with(model.process_group)
                    context.assert_called_once()
                    self.assertIs(context.call_args.args[0], model)
                    self.assertEqual(context.call_args.args[1], fsdp_training.StateDictType.FULL_STATE_DICT)
                    config = context.call_args.args[2]
                    self.assertTrue(config.rank0_only)
                    self.assertEqual(config.offload_to_cpu, device != "cpu")
                    if rank == 0:
                        self.assertIs(actual, state)
                        self.assertIs(actual._metadata, metadata)
                        self.assertEqual(set(actual), {"weight", "bias", "adapter"})
                        self.assertTrue(all(tensor.device.type == "cpu" for tensor in actual.values()))
                        self.assertIs(actual["adapter"], adapter.cpu.return_value)
                        adapter.cpu.assert_called_once_with()
                    else:
                        self.assertEqual(actual, {})
                        adapter.cpu.assert_not_called()

    def test_sharded_probe_coordinates_fit_and_treats_oom_as_job_failure(self):
        from tests.test_ddp import TinyAdapter, fixed_rows
        model = TinyAdapter()
        rows = [{"qid": "fixture"}]
        audit = {"sequence_tokens": 5, "visual_tokens": 1, "assistant_tokens_including_eos": 2}
        settings = ddp_config.normalize_training_config({"parallel": "fsdp", "world_size": 2}, "qwen35")
        processor = SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))
        with patch("student_pilot.diagnostic_data.encode_training", return_value=(fixed_rows()[0], audit)), \
                patch.object(torch.cuda, "empty_cache"), \
                patch.object(ddp_training, "gather", return_value=[True, False]) as gather, \
                patch.object(ddp_training, "probe_candidate", return_value={"microbatch": 1, "fits": True}) as probe:
            report = ddp_training.memory_probe(model, processor, rows, {"fixture": audit}, settings, 0, lambda: None)
            self.assertFalse(report["trials"][0]["fits"])
            self.assertEqual(len(report["trials"]), 1)
            self.assertIs(probe.call_args.args[0], model)
            gather.assert_called_once_with(True, 2)
            probe.side_effect = torch.cuda.OutOfMemoryError("synthetic")
            with self.assertRaisesRegex(RuntimeError, "FSDP probe OOM"):
                ddp_training.memory_probe(model, processor, rows, {"fixture": audit}, settings, 0, lambda: None)

    def test_native_fsdp_wrapper_forward_gradients_and_frozen_values_without_sockets(self):
        # A size-one fake group performs no communication. This verifies FSDP
        # hooks and native checkpointing, not FULL_SHARD or distributed parity.
        import torch.testing._internal.distributed.fake_pg  # Registers the socket-free backend.
        dist.init_process_group("fake", store=dist.HashStore(), rank=0, world_size=1)
        try:
            for student in ("onethinker", "qwen35"):
                for bf16 in (False, True):
                    with self.subTest(student=student, bf16=bf16):
                        model, groups, rows = fixture(student, bf16)
                        reference = copy.deepcopy(model)
                        reference_parameters = dict(reference.named_parameters())
                        params = [p for group in groups.values() for _, p in group]
                        frozen = [(p, p.detach().clone()) for p in model.parameters() if not p.requires_grad]
                        wrapped = fsdp_training.wrap_model(model, params, dist.group.WORLD,
                                                           torch.device("cpu"), mixed_precision=bf16)
                        self.assertEqual(len(FSDP.fsdp_modules(wrapped)), 4)
                        context = lambda: torch.autocast("cpu", dtype=torch.bfloat16) if bf16 else nullcontext()
                        expected = ddp_core.backward_batch(reference, rows[0], [1], 1, 1, forward_context=context())
                        actual = ddp_core.backward_batch(wrapped, rows[0], [1], 1, 1, forward_context=context())
                        torch.testing.assert_close(actual, expected, rtol=0, atol=1e-5)
                        for group in groups.values():
                            for name, parameter in group:
                                torch.testing.assert_close(parameter.grad, reference_parameters[name].grad,
                                                           rtol=0, atol=1e-5)
                        torch.optim.AdamW(params, lr=0.01).step()
                        for parameter, before in frozen:
                            self.assertFalse(parameter.requires_grad)
                            self.assertIsNone(parameter.grad)
                            self.assertTrue(torch.equal(parameter, before))
        finally:
            dist.destroy_process_group()

    def test_frozen_fingerprints_detect_value_changes_and_missing_parameters(self):
        model = torch.nn.Linear(3, 2).requires_grad_(False)
        before = fsdp_training.frozen_shard_fingerprints(model)
        fsdp_training.check_frozen_shards(model, before)
        with torch.no_grad():
            model.weight.add_(1)
        with self.assertRaisesRegex(ValueError, "changed"):
            fsdp_training.check_frozen_shards(model, before)


if __name__ == "__main__":
    unittest.main()
