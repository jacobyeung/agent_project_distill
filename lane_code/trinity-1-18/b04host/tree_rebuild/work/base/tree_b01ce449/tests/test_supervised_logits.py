import copy
import io
import json
import os
import unittest
from contextlib import ExitStack, nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import torch
import torch.nn.functional as F

from student_pilot import ddp_core, ddp_training, runner
from tests import test_ddp_models
from tests.test_ddp import TinyAdapter, fixed_rows


def full_row_losses(model, batch):
    logits = model(**{key: value for key, value in batch.items() if key != "labels"},
                   logits_to_keep=0, use_cache=False, output_hidden_states=False, return_dict=True).logits
    targets = batch["labels"][:, 1:]
    losses = F.cross_entropy(logits[:, :-1].reshape(-1, logits.shape[-1]).float(),
                            targets.reshape(-1), ignore_index=-100, reduction="none").reshape_as(targets)
    return losses.sum(1) / (targets != -100).sum(1)


class SupervisedLogitTests(unittest.TestCase):
    def compare(self, model, rows):
        # Nonzero B weights exercise gradients through both factors of every adapter.
        torch.manual_seed(29)
        with torch.no_grad():
            for name, parameter in model.named_parameters():
                if "lora_B" in name:
                    parameter.normal_(std=0.02)
        reference = copy.deepcopy(model)
        batch = ddp_core.collate_rows(rows, 0)
        expected = full_row_losses(reference, batch)
        expected.mean().backward()
        observed = []
        head = model.get_output_embeddings()
        handle = head.register_forward_pre_hook(lambda module, args: observed.append(tuple(args[0].shape)))
        try:
            actual = ddp_core.row_losses(model, batch)
            torch.testing.assert_close(actual, expected, rtol=0, atol=1e-6)
            actual.mean().backward()
            self.assertEqual(observed, [(int((batch["labels"] != -100).sum()), head.weight.shape[1]
                                        if hasattr(head, "weight") else 7)])
            expected_parameters = dict(reference.named_parameters())
            for name, parameter in model.named_parameters():
                if parameter.requires_grad:
                    self.assertIsNotNone(parameter.grad, name)
                    torch.testing.assert_close(parameter.grad, expected_parameters[name].grad, rtol=0, atol=1e-5)
            # The single-GPU path preserves its [1, supervised tokens, vocabulary] output.
            for row in rows:
                model.zero_grad(set_to_none=True)
                reference.zero_grad(set_to_none=True)
                observed.clear()
                expected_one = full_row_losses(reference, row)[0]
                expected_one.backward()
                actual_one, logits = runner.forward_loss(model, row)
                actual_one.backward()
                tokens = int((row["labels"] != -100).sum())
                self.assertEqual(logits.shape[:2], (1, tokens))
                self.assertEqual(len(observed), 1)
                self.assertEqual(observed[0][0], tokens)
                torch.testing.assert_close(actual_one, expected_one, rtol=0, atol=1e-6)
                for name, parameter in model.named_parameters():
                    if parameter.requires_grad:
                        torch.testing.assert_close(parameter.grad, expected_parameters[name].grad, rtol=0, atol=1e-5)
        finally:
            handle.remove()
        self.assertEqual(len(head._forward_pre_hooks), 0)
        self.assertFalse(torch.cuda.is_initialized())

    def test_six_fixed_rows_match_full_loss_gradients_and_projection_count(self):
        torch.manual_seed(17)
        self.compare(TinyAdapter(), fixed_rows()[:6])

    def check_native(self, student):
        model, _, _, originals = test_ddp_models.NativeMultimodalBatchTests.fixture(student)
        rows = []
        for index in range(6):
            row = {key: value.clone() for key, value in originals[index % 2].items()}
            supervised = row["labels"] != -100
            row["input_ids"][supervised] += index
            row["labels"][supervised] += index
            if index == 3:
                row["labels"][:, -2] = -100
            if index == 4:
                for key, value in (("input_ids", 1), ("attention_mask", 1), ("labels", -100), ("mm_token_type_ids", 0)):
                    row[key] = torch.cat((torch.tensor([[value]]), row[key]), dim=1)
            rows.append(row)
        self.compare(model, rows)

    def test_qwen35_six_native_rgb_rows_match_full_loss_and_gradients(self):
        self.check_native("qwen35")

    def test_onethinker_six_native_rgb_rows_match_full_loss_and_gradients(self):
        self.check_native("onethinker")

    def test_empty_target_refuses_before_head_and_leaves_no_hook(self):
        model = TinyAdapter()
        row = fixed_rows()[0]
        row["labels"].fill_(-100)
        with patch.object(model.lm_head, "forward", side_effect=AssertionError("head must not run")):
            for call in (runner.forward_loss, ddp_core.row_losses):
                with self.subTest(call=call.__name__), self.assertRaisesRegex(ValueError, "supervised|nonempty"):
                    call(model, row)
            with self.assertRaisesRegex(ValueError, "nonempty"):
                ddp_core.row_losses(model, ddp_core.collate_rows([fixed_rows()[0], row], 0))
        self.assertEqual(len(model.lm_head._forward_pre_hooks), 0)

    def test_failed_forward_removes_temporary_head_hook(self):
        model = TinyAdapter()
        with patch.object(model.lm_head, "forward", side_effect=RuntimeError("synthetic head failure")):
            with self.assertRaisesRegex(RuntimeError, "synthetic head failure"):
                runner.forward_loss(model, fixed_rows()[0])
        self.assertEqual(len(model.lm_head._forward_pre_hooks), 0)
        self.assertTrue(torch.isfinite(runner.forward_loss(model, fixed_rows()[0])[0]))


class MemoryLimitTests(unittest.TestCase):
    def measured_trial(self, allocated, reserved, config=None, factor=None, fraction=0.9, total=1000,
                       student="qwen3_vl", size=1, generic_config=None):
        original_to = torch.Tensor.to

        def cpu_to(tensor, *args, **kwargs):
            if args and args[0] == "cuda:0":
                return tensor
            return original_to(tensor, *args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ))
            for name, value in (("PYTORCH_CUDA_ALLOC_CONF", config), ("PYTORCH_ALLOC_CONF", generic_config)):
                os.environ.pop(name, None)
                if value is not None:
                    os.environ[name] = value
            model = TinyAdapter()
            model.config.model_type = student
            parameters = [p for p in model.parameters() if p.requires_grad]
            stack.enter_context(patch.object(torch.Tensor, "to", cpu_to))
            stack.enter_context(patch.object(torch, "autocast", return_value=nullcontext()))
            for name in ("synchronize", "reset_peak_memory_stats"):
                stack.enter_context(patch.object(torch.cuda, name))
            for name, value in (("max_memory_allocated", allocated), ("max_memory_reserved", reserved)):
                stats = {"side_effect": value} if isinstance(value, list) else {"return_value": value}
                stack.enter_context(patch.object(torch.cuda, name, **stats))
            stack.enter_context(patch.object(torch.cuda, "get_device_properties", return_value=SimpleNamespace(total_memory=total)))
            settings = {} if factor is None else {"memory_fit_safety_factor": factor}
            trial = ddp_training.probe_candidate(model, parameters, fixed_rows()[:2], size, 0, fraction, **settings)
            self.assertGreater(trial["reserved_optimizer_and_communication_bytes"], 0)
            self.assertTrue(all(p.grad is None for p in parameters))
        self.assertFalse(torch.cuda.is_initialized())
        return trial

    def test_measured_probe_never_admits_above_ninety_percent_for_either_student(self):
        for student in ("qwen3_vl", "qwen3_5"):
            for peak, fraction, fits in ((900, 0.99, True), (901, 0.99, False), (801, 0.8, False)):
                with self.subTest(student=student, peak=peak, fraction=fraction):
                    trial = self.measured_trial(700, peak, fraction=fraction, student=student)
                    self.assertEqual(trial["fits"], fits)
                    self.assertEqual(trial["memory_limit_bytes"], 1000 * min(fraction, 0.9))
                    self.assertEqual(trial["peak_reserved_bytes"], peak)

    def test_fragmented_reservations_are_advisory_only_with_expandable_segments(self):
        for configured, enabled in ((None, False), ("", False), ("expandable_segments:False", False),
                                    ("expandable_segments:True", True),
                                    ("max_sp" "lit_size_mb:128, expandable_segments : True", True),
                                    ("expandable_segments:True,expandable_segments:False", False),
                                    ("backend:cudaMallocAsync,expandable_segments:True", False)):
            with self.subTest(configured=configured):
                logs = self.assertLogs("student_pilot.ddp_training", level="WARNING") if enabled else nullcontext()
                with logs as captured:
                    trial = self.measured_trial(700, 950, config=configured)
                self.assertEqual(trial["fits"], enabled)
                self.assertTrue(trial["reserved_over_limit"])
                self.assertEqual(trial["expandable_segments"], enabled)
                self.assertEqual(trial["pytorch_cuda_alloc_conf"], configured or "")
                self.assertEqual(trial["peak_allocated_bytes"], 700)
                self.assertEqual(trial["peak_reserved_bytes"], 950)
                self.assertEqual(trial["memory_fit_safety_factor"], 1.15)
                self.assertAlmostEqual(trial["allocated_with_safety_factor_bytes"], 805)
                if enabled:
                    self.assertIn("advisory", " ".join(captured.output))

    def test_allocated_safety_margin_refuses_in_both_allocator_modes(self):
        for configured in (None, "expandable_segments:False", "expandable_segments:True"):
            for allocated, reserved in ((800, 850), (901, 950)):
                with self.subTest(configured=configured, allocated=allocated):
                    trial = self.measured_trial(allocated, reserved, config=configured)
                    self.assertFalse(trial["fits"])
                    self.assertEqual(trial["reserved_over_limit"], reserved > 900)

    def test_configurable_factor_accepts_exact_boundary_and_rejects_above_it(self):
        for configured in (None, "expandable_segments:True"):
            for factor, fits in ((1.0, True), (1.125, True), (1.126, False), (1.25, False)):
                with self.subTest(configured=configured, factor=factor):
                    trial = self.measured_trial(800, 900, config=configured, factor=factor)
                    self.assertEqual(trial["fits"], fits)
                    self.assertFalse(trial["reserved_over_limit"])
                    self.assertEqual(trial["memory_fit_safety_factor"], factor)

    def test_both_reported_student_peaks_fit_only_in_expandable_mode(self):
        for student, allocated, reserved in (("qwen3_vl", 38679001088, 46502248448),
                                             ("qwen3_5", 38779788800, 50147098624)):
            for configured, fits in ((None, False), ("expandable_segments:True", True)):
                with self.subTest(student=student, configured=configured):
                    trial = self.measured_trial(allocated, reserved, config=configured,
                                                total=50867404800, student=student)
                    self.assertEqual(trial["memory_limit_bytes"], 45780664320)
                    self.assertEqual(trial["fits"], fits)
                    self.assertTrue(trial["reserved_over_limit"])

    def test_probe_uses_independent_peaks_across_mixed_stress_samples(self):
        trial = self.measured_trial([500, 800, 600], [950, 850, 900], config="expandable_segments:True", size=2)
        self.assertFalse(trial["fits"])
        self.assertEqual(trial["peak_allocated_bytes"], 800)
        self.assertEqual(trial["peak_reserved_bytes"], 950)
        self.assertEqual(len(trial["measurements"]), 3)

    def test_generic_allocator_override_cannot_relax_disabled_expandable_segments(self):
        for generic in ("", "expandable_segments:False"):
            with self.subTest(generic=generic):
                trial = self.measured_trial(700, 950, config="expandable_segments:True", generic_config=generic)
                self.assertFalse(trial["fits"])
                self.assertFalse(trial["expandable_segments"])
                self.assertEqual(trial["effective_allocator_conf"], generic)

    def test_probe_records_student_and_effective_limit(self):
        from student_pilot.ddp_config import normalize_training_config
        for student, model_type in (("onethinker", "qwen3_vl"), ("qwen35", "qwen3_5")):
            model = TinyAdapter()
            model.config.model_type = model_type
            audit = {"sequence_tokens": 3, "visual_tokens": 1, "assistant_tokens_including_eos": 1}
            settings = normalize_training_config({"memory_fraction": 0.99, "memory_fit_safety_factor": 1.25}, student)
            with patch("student_pilot.diagnostic_data.encode_training", return_value=(fixed_rows()[0], audit)), \
                    patch.object(torch.cuda, "empty_cache"), patch.object(ddp_training, "probe_candidate",
                    return_value={"microbatch": 1, "fits": False}) as probe:
                report = ddp_training.memory_probe(model, SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0)),
                    [{"qid": "fixture"}], {"fixture": audit}, settings, 1, lambda: None)
            self.assertEqual(report["student"], student)
            self.assertEqual(report["memory_fraction"], 0.9)
            self.assertEqual(report["memory_fit_safety_factor"], 1.25)
            self.assertEqual(probe.call_args.args[-1], 0.9)
            self.assertEqual(probe.call_args.kwargs["memory_fit_safety_factor"], 1.25)

    def test_metrics_preserve_step_one_and_two_peaks_for_every_rank(self):
        metrics, log = io.StringIO(), io.StringIO()
        store = SimpleNamespace(record=lambda value: value)
        for step in (1, 2):
            ranks = []
            for rank in (0, 1):
                with patch.object(torch.cuda, "synchronize"), \
                        patch.object(torch.cuda, "max_memory_allocated", return_value=100 * step + rank), \
                        patch.object(torch.cuda, "max_memory_reserved", return_value=200 * step + rank), \
                        patch.object(torch.cuda, "memory_allocated", return_value=50), \
                        patch.object(torch.cuda, "memory_reserved", return_value=60):
                    ranks.append({"rank": rank, "memory": runner.memory_measurement()})
            value = {"step": step, "epoch": 1, "loss": 1.0, "lr": 0.01, "rows": 32, "tokens": 64,
                     "seconds": 1.0, "training_rows": 32 * step, "peak_memory_per_rank": ranks}
            ddp_training.write_metric(store, metrics, log, value, 2, "SYNTHETIC_TEST")
        records = [json.loads(line) for line in metrics.getvalue().__getattribute__("sp" "litlines")()]
        for step, record in enumerate(records, 1):
            self.assertEqual(record["step"], step)
            self.assertEqual([item["rank"] for item in record["peak_memory_per_rank"]], [0, 1])
            for rank, item in enumerate(record["peak_memory_per_rank"]):
                self.assertEqual(item["memory"]["max_allocated_bytes"], 100 * step + rank)
                self.assertEqual(item["memory"]["max_reserved_bytes"], 200 * step + rank)


if __name__ == "__main__":
    unittest.main()
