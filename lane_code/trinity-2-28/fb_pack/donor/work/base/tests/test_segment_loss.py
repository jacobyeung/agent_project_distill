"""Segment-normalized loss behind the loss_reduction gate, checked against the unmodified 9183 ddp_core."""
import copy
import hashlib
import importlib.util
import os
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests import cpu_stubs

cpu_stubs.install()

import torch
import torch.nn as nn
import torch.nn.functional as F

from student_pilot import ddp_config, ddp_core

# The unmodified 9183 tree sits next to this tree in the build directory; elsewhere name it explicitly.
BASELINE = Path(os.environ.get("RG2P_BASELINE_DDP_CORE",
                               Path(__file__).resolve().parents[2] / "trainer_9183/student_pilot/ddp_core.py"))
BASELINE_SHA256 = "9ed6f72f"
SEGMENT = ddp_config.SEGMENT_LOSS_REDUCTION
DEFAULT = ddp_config.DEFAULTS["loss_reduction"]
QWEN35 = {"think_start": 248068, "think_end": 248069, "im_end": 248046, "endoftext": 248044, "nl": 198, "dbl_nl": 271}
ONETHINKER = {"think_start": 151667, "think_end": 151668, "im_end": 151645, "endoftext": 151643, "nl": 198, "dbl_nl": 271}


def load_baseline():
    if not BASELINE.is_file():
        return None
    if not hashlib.sha256(BASELINE.read_bytes()).hexdigest().startswith(BASELINE_SHA256):
        raise AssertionError(f"{BASELINE} is not the 9183 ddp_core")
    spec = importlib.util.spec_from_file_location("student_pilot.ddp_core_9183", BASELINE)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "student_pilot"
    spec.loader.exec_module(module)
    return module


ORIGINAL = load_baseline()


class ToyCausalVLM(nn.Module):
    """A causal LM whose forward honours logits_to_keep and calls its output embedding like the native Qwen forward."""

    def __init__(self, vocab_size=250000, hidden_size=32, seed=17):
        super().__init__()
        generator = torch.Generator().manual_seed(seed)
        self.embed = nn.Embedding(vocab_size, hidden_size)
        self.proj = nn.Linear(hidden_size, hidden_size)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)
        with torch.no_grad():
            for weight in (self.embed.weight, self.proj.weight, self.lm_head.weight):
                weight.normal_(0.0, 0.02, generator=generator)
            self.proj.bias.zero_()

    def get_output_embeddings(self):
        return self.lm_head

    def forward(self, input_ids, attention_mask=None, logits_to_keep=None, **kwargs):
        hidden = torch.tanh(self.proj(self.embed(input_ids)))
        return SimpleNamespace(logits=self.lm_head(hidden[:, logits_to_keep, :]))


def row(prompt, target):
    ids = prompt + target
    return {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones((1, len(ids)), dtype=torch.long),
            "labels": torch.tensor([[-100] * len(prompt) + target])}


def prompt(tok, length):
    return [100 + index % 50 for index in range(length - 2)] + [tok["think_start"], tok["nl"]]


def direct(tok, length, answer):
    """<think>\\n\\n</think>\\n\\n<answer><|im_end|><|endoftext|> with the prompt ending in <think>\\n."""
    return row(prompt(tok, length), [tok["nl"], tok["think_end"], tok["dbl_nl"], *answer, tok["im_end"], tok["endoftext"]])


def traced(tok, length, trace, answer):
    return row(prompt(tok, length), [*trace, tok["nl"], tok["think_end"], tok["dbl_nl"], *answer, tok["im_end"], tok["endoftext"]])


def legacy(tok):
    return row([101, 102, 103, 104], [33, tok["im_end"], tok["endoftext"]])


def raw(tensor):
    return tensor.detach().contiguous().cpu().numpy().tobytes()


def mixed_rows(tok):
    return [direct(tok, 14, [33]), traced(tok, 15, list(range(501, 513)), [33]), direct(tok, 21, [17, 13, 20]),
            traced(tok, 18, list(range(600, 630)), [17, 13, 20]), legacy(tok),
            row(prompt(tok, 9), [tok["nl"], tok["dbl_nl"], tok["think_end"], 44, tok["im_end"]]),
            row(prompt(tok, 9), [77, 78, tok["nl"], tok["think_end"]])]


EXPECTED_SEGMENTS = {1: (14, 4), 3: (32, 6)}


@unittest.skipIf(ORIGINAL is None, f"baseline ddp_core not found at {BASELINE}")
class SegmentLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.model = ToyCausalVLM()
        cls.batches = {name: ddp_core.collate_rows(mixed_rows(tok), tok["endoftext"])
                       for name, tok in (("qwen35", QWEN35), ("onethinker", ONETHINKER))}

    def test_source_keeps_the_runner_import_without_a_fallback(self):
        source = Path(ddp_core.__file__).read_text()
        self.assertIn("    from .runner import supervised_logits\n", source)
        self.assertNotIn("fallback", source.lower())

    def test_gate_off_is_byte_identical_to_9183_for_losses_and_gradients(self):
        for name, batch in self.batches.items():
            for reduction in (None, DEFAULT, "any other string"):
                with self.subTest(student=name, reduction=reduction):
                    with torch.no_grad():
                        expected = ORIGINAL.row_losses(self.model, batch)
                        actual = ddp_core.row_losses(self.model, batch, reduction)
                    self.assertTrue(torch.equal(expected, actual))
                    self.assertEqual(raw(expected), raw(actual))
                    first, second = copy.deepcopy(self.model), copy.deepcopy(self.model)
                    weights = [1.0] * (batch["labels"].shape[0] - 1) + [0.0]
                    expected = ORIGINAL.backward_batch(first, batch, weights, 4, 32)
                    actual = ddp_core.backward_batch(second, batch, weights, 4, 32, loss_reduction=reduction)
                    self.assertEqual(raw(expected), raw(actual))
                    for left, right in zip(first.parameters(), second.parameters()):
                        self.assertEqual(raw(left.grad), raw(right.grad))

    def test_gate_on_applies_the_exact_segment_formula_and_keeps_direct_rows_bitwise(self):
        for name, batch in self.batches.items():
            with self.subTest(student=name), torch.no_grad():
                expected = ORIGINAL.row_losses(self.model, batch)
                actual = ddp_core.row_losses(self.model, batch, SEGMENT)
                for index in (0, 2, 4, 5, 6):
                    self.assertEqual(raw(expected[index]), raw(actual[index]), f"row {index} must keep the default")
                labels = batch["labels"]
                positions = torch.where((labels[:, 1:] != -100).any(dim=0))[0]
                targets = labels[:, positions + 1]
                supervised = targets != -100
                from student_pilot.runner import supervised_logits
                losses = F.cross_entropy(supervised_logits(self.model, batch, positions).float(), targets[supervised],
                                         reduction="none")
                rows = torch.where(supervised)[0]
                for index, (trace_count, answer_count) in EXPECTED_SEGMENTS.items():
                    values = losses[rows == index].double()
                    self.assertEqual(values.numel(), trace_count + answer_count)
                    formula = values[trace_count:].mean() + 0.5 * values[:trace_count].mean()
                    self.assertAlmostEqual(float(actual[index]), float(formula), delta=2e-6)
                    self.assertNotAlmostEqual(float(actual[index]), float(expected[index]), delta=1e-4)

    def test_segment_weights_are_one_over_answer_and_half_over_trace_tokens(self):
        batch = self.batches["qwen35"]
        labels = batch["labels"]
        positions = torch.where((labels[:, 1:] != -100).any(dim=0))[0]
        targets = labels[:, positions + 1]
        supervised = targets != -100
        counts = supervised.sum(dim=1)
        rows = torch.where(supervised)[0]
        losses = torch.rand(int(supervised.sum()), dtype=torch.float32, requires_grad=True)
        ddp_core.segment_row_losses(targets, supervised, losses, rows, counts).sum().backward()
        gradient = losses.grad
        for index, (trace_count, answer_count) in EXPECTED_SEGMENTS.items():
            values = gradient[rows == index]
            torch.testing.assert_close(values[:trace_count], torch.full((trace_count,), 0.5 / trace_count), rtol=0, atol=1e-7)
            torch.testing.assert_close(values[trace_count:], torch.full((answer_count,), 1.0 / answer_count), rtol=0, atol=1e-7)
            self.assertAlmostEqual(float(values[trace_count:].sum() / values[:trace_count].sum()), 2.0, delta=1e-5)
        for index in (0, 2, 4, 5, 6):
            values = gradient[rows == index]
            torch.testing.assert_close(values, torch.full_like(values, 1.0 / values.numel()), rtol=0, atol=1e-7)

    def test_backward_batch_threads_the_gate_into_row_losses(self):
        batch = self.batches["onethinker"]
        weights = [1.0] * batch["labels"].shape[0]
        with torch.no_grad():
            expected = ddp_core.row_losses(self.model, batch, SEGMENT)
        actual = ddp_core.backward_batch(copy.deepcopy(self.model), batch, weights, 2, 32, loss_reduction=SEGMENT)
        self.assertEqual(raw(expected), raw(actual.detach()))

    def test_direct_only_batch_with_gate_on_is_byte_identical_including_gradients(self):
        for tok in (QWEN35, ONETHINKER):
            batch = ddp_core.collate_rows([direct(tok, 14, [33]), direct(tok, 21, [17, 13, 20]), legacy(tok)],
                                          tok["endoftext"])
            first, second = copy.deepcopy(self.model), copy.deepcopy(self.model)
            expected = ORIGINAL.backward_batch(first, batch, [1.0, 1.0, 0.0], 4, 32)
            actual = ddp_core.backward_batch(second, batch, [1.0, 1.0, 0.0], 4, 32, loss_reduction=SEGMENT)
            self.assertEqual(raw(expected), raw(actual))
            for left, right in zip(first.parameters(), second.parameters()):
                self.assertEqual(raw(left.grad), raw(right.grad))


class LossReductionConfigTests(unittest.TestCase):
    def test_config_accepts_both_reductions_and_refuses_others(self):
        for value in (DEFAULT, SEGMENT):
            settings = ddp_config.normalize_training_config({"world_size": 2, "loss_reduction": value}, "onethinker")
            self.assertEqual(settings["loss_reduction"], value)
        self.assertEqual(ddp_config.normalize_training_config({"world_size": 2}, "onethinker")["loss_reduction"], DEFAULT)
        for value in ("segment_normalized", SEGMENT + " ", SEGMENT.upper(), None, 1, [SEGMENT]):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "loss_reduction"):
                ddp_config.normalize_training_config({"world_size": 2, "loss_reduction": value}, "onethinker")

    def test_other_fixed_settings_still_refuse_changes(self):
        for key, value in (("padding", "other"), ("shuffle", "other"), ("targets", "other")):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                ddp_config.normalize_training_config({"world_size": 2, key: value}, "onethinker")


if __name__ == "__main__":
    unittest.main()
