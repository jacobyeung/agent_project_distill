import unittest

import torch

from student_pilot.batches import assistant_labels, assistant_loss, prediction_positions
from student_pilot.adapters import discover_targets, attach_adapters, trainable_groups


class MaskTests(unittest.TestCase):
    def test_only_assistant_and_eos_are_supervised(self):
        ids = torch.tensor([[11, 12, 13, 21, 22, 99, 0, 0]])
        attention = torch.tensor([[1, 1, 1, 1, 1, 1, 0, 0]])
        labels = assistant_labels(ids, attention, 3, 3)
        self.assertEqual(labels.tolist(), [[-100, -100, -100, 21, 22, 99, -100, -100]])
        self.assertEqual(prediction_positions(labels).tolist(), [2, 3, 4])

    def test_selected_logits_equal_full_masked_causal_ce(self):
        torch.manual_seed(17)
        ids = torch.tensor([[1, 2, 3, 4, 5, 0]])
        attention = torch.tensor([[1, 1, 1, 1, 1, 0]])
        labels = assistant_labels(ids, attention, 3, 2)
        logits = torch.randn(1, 6, 7, requires_grad=True)
        positions = prediction_positions(labels)
        selected = assistant_loss(logits[:, positions], labels, positions)
        full = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 7), labels[:, 1:].reshape(-1))
        torch.testing.assert_close(selected, full)
        selected.backward()
        self.assertEqual(torch.count_nonzero(logits.grad[:, [0, 1, 4, 5]]).item(), 0)

    def test_empty_target_and_unattended_target_are_rejected(self):
        ids = torch.tensor([[1, 2, 3, 0]])
        attention = torch.tensor([[1, 1, 1, 0]])
        for prompt, answer in ((3, 0), (2, 2), (0, 2)):
            with self.assertRaises(ValueError):
                assistant_labels(ids, attention, prompt, answer)


class AdapterTests(unittest.TestCase):
    def test_exact_architecture_targets_on_meta(self):
        from accelerate import init_empty_weights
        from transformers import Qwen3VLConfig, Qwen3VLForConditionalGeneration
        from student_pilot.common import MODEL

        with init_empty_weights(include_buffers=True):
            model = Qwen3VLForConditionalGeneration(Qwen3VLConfig.from_pretrained(MODEL, local_files_only=True))
            targets = discover_targets(model)
            self.assertEqual({group: len(names) for group, names in targets.items()}, {"text": 252, "vision": 108, "mergers": 8})
            model, report = attach_adapters(model)
        self.assertEqual(report["trainable_parameters"], 48070400)
        self.assertEqual(report["group_parameters"], {"text": 43646976, "vision": 3849984, "mergers": 573440})
        groups = trainable_groups(model, targets)
        self.assertEqual(sum(p.numel() for group in groups.values() for _, p in group), 48070400)
        self.assertTrue(all(".lora_" in name for name, p in model.named_parameters() if p.requires_grad))


if __name__ == "__main__":
    unittest.main()
