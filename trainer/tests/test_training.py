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
    def check_student(self, student, target_counts, group_counts):
        from accelerate import init_empty_weights
        from transformers import AutoConfig
        from student_pilot.students import get_student, model_class

        config = AutoConfig.from_pretrained(get_student(student)["snapshot"], local_files_only=True)
        with init_empty_weights(include_buffers=True):
            model = model_class(student)(config)
            targets = discover_targets(model)
            self.assertEqual({group: len(names) for group, names in targets.items()}, target_counts)
            model, report = attach_adapters(model)
        self.assertEqual(report["student"], student)
        self.assertEqual(report["trainable_parameters"], sum(group_counts.values()))
        self.assertEqual(report["group_parameters"], group_counts)
        groups = trainable_groups(model, targets)
        self.assertEqual(sum(p.numel() for group in groups.values() for _, p in group), sum(group_counts.values()))
        self.assertTrue(all(".lora_" in name for name, p in model.named_parameters() if p.requires_grad))
        self.assertEqual(report["ranks"], {"text": 16, "vision": 8, "mergers": 8})
        return targets

    def test_exact_architecture_targets_on_meta(self):
        with self.subTest(student="onethinker"):
            self.check_student("onethinker", {"text": 252, "vision": 108, "mergers": 8},
                               {"text": 43646976, "vision": 3849984, "mergers": 573440})
        with self.subTest(student="qwen35"):
            self.check_exact_qwen35_targets_on_meta()
        with self.subTest(condition="unknown_student"):
            self.check_registry_rejects_unknown_students()
        with self.subTest(condition="missing_projection"):
            self.check_discovery_refuses_missing_or_changed_projection()

    def check_exact_qwen35_targets_on_meta(self):
        targets = self.check_student("qwen35", {"text": 248, "vision": 108, "mergers": 2},
                                     {"text": 43278336, "vision": 3849984, "mergers": 143360})
        self.assertEqual(sum(".linear_attn." in name for name in targets["text"]), 120)
        self.assertEqual(sum(".self_attn." in name for name in targets["text"]), 32)
        self.assertEqual(sum(".mlp." in name for name in targets["text"]), 96)
        self.assertTrue(all("conv" not in name and "embed" not in name for names in targets.values() for name in names))

    def check_registry_rejects_unknown_students(self):
        from student_pilot.students import get_student

        with self.assertRaises(ValueError):
            get_student("not-a-student")

    def check_discovery_refuses_missing_or_changed_projection(self):
        from accelerate import init_empty_weights
        from transformers import AutoConfig
        from student_pilot.students import get_student, model_class

        config = AutoConfig.from_pretrained(get_student("qwen35")["snapshot"], local_files_only=True)
        with init_empty_weights(include_buffers=True):
            model = model_class("qwen35")(config)
            model.model.language_model.layers[0].linear_attn.in_proj_qkv = torch.nn.Identity()
            with self.assertRaisesRegex(ValueError, "Linear module is missing"):
                discover_targets(model)


class AdapterReloadTests(unittest.TestCase):
    def test_exact_peft_reload_preserves_fp32_and_bf16_archives(self):
        import json
        import tempfile
        from pathlib import Path
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from safetensors.torch import save_file
        from transformers import PretrainedConfig
        from student_pilot.common import ARTIFACTS
        from student_pilot.runner import load_adapter

        class TinyBase(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.q_proj = torch.nn.Linear(3, 3, bias=False, dtype=torch.bfloat16)
                self.config = PretrainedConfig()

        root = ARTIFACTS / "trainer_tests"
        root.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="adapter_dtype_", dir=root))
        for dtype in (torch.float32, torch.bfloat16):
            with self.subTest(saved_dtype=str(dtype)):
                path = root / str(dtype)
                path.mkdir()
                original = get_peft_model(TinyBase(), LoraConfig(r=1, lora_alpha=1, target_modules=["q_proj"]))
                config = original.peft_config["default"].to_dict()
                config = {key: sorted(value) if isinstance(value, set) else value for key, value in config.items()}
                (path / "adapter_config.json").write_text(json.dumps(config))
                saved = {name: (torch.arange(value.numel(), dtype=torch.float32).reshape(value.shape) + 0.1234567).to(dtype)
                         for name, value in get_peft_model_state_dict(original).items()}
                save_file(saved, str(path / "adapter_model.safetensors"))
                loaded, receipt = load_adapter(TinyBase(), path)
                restored = get_peft_model_state_dict(loaded)
                self.assertTrue(receipt["exact_tensor_equality"])
                self.assertTrue(receipt["exact_dtype_equality"])
                self.assertEqual(receipt["tensor_count"], len(saved))
                for name, value in restored.items():
                    self.assertEqual(value.dtype, saved[name].dtype)
                    self.assertTrue(torch.equal(value, saved[name]))


if __name__ == "__main__":
    unittest.main()
