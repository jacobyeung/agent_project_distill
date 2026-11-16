import unittest
from types import SimpleNamespace
from unittest.mock import patch

import torch

from student_pilot import ddp_config, ddp_core, ddp_training
from tests.test_ddp import TinyAdapter, fixed_rows


class MemoryProbeTests(unittest.TestCase):
    def test_probe_chooses_fastest_common_safe_size(self):
        reports = [{"trials": [{"microbatch": 1, "fits": True, "seconds": 1.0},
                               {"microbatch": 2, "fits": True, "seconds": 1.3},
                               {"microbatch": 4, "fits": True, "seconds": 8.0}]},
                   {"trials": [{"microbatch": 1, "fits": True, "seconds": 1.1},
                               {"microbatch": 2, "fits": True, "seconds": 1.4},
                               {"microbatch": 4, "fits": False}]}]
        self.assertEqual(ddp_core.select_microbatch(reports, 2), 2)
        with self.assertRaisesRegex(ValueError, "at least one"):
            ddp_core.select_microbatch([{"trials": [{"microbatch": 1, "fits": False}]}] * 2, 2)
        with self.assertRaisesRegex(ValueError, "every rank"):
            ddp_core.select_microbatch(reports[:1], 2)

    def test_probe_handles_oom_without_optimizer_updates_or_cuda_execution(self):
        model = TinyAdapter()
        before = {name: parameter.detach().clone() for name, parameter in model.named_parameters()}
        rows = [{"qid": "a"}, {"qid": "b"}]
        audits = {row["qid"]: {"sequence_tokens": 10 + index, "visual_tokens": 2 - index,
                              "assistant_tokens_including_eos": index + 1} for index, row in enumerate(rows)}
        settings = ddp_config.normalize_training_config({"world_size": 2, "max_microbatch_size": 4}, "onethinker")
        processor = SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=0))
        checked = []
        with patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda processor, row:
                   (fixed_rows()[0], audits[row["qid"]])), patch.object(torch.cuda, "empty_cache"), \
                patch.object(ddp_training, "probe_candidate", side_effect=[
                    {"microbatch": 1, "fits": True, "seconds": 1.0}, torch.cuda.OutOfMemoryError("synthetic")]):
            report = ddp_training.memory_probe(model, processor, rows, audits, settings, 0, lambda: checked.append(True))
        self.assertEqual(report["optimizer_updates"], 0)
        self.assertEqual([item["microbatch"] for item in report["trials"]], [1, 2])
        self.assertEqual(report["trials"][-1]["reason"], "CUDA_OutOfMemory")
        self.assertEqual(len(checked), 2)
        self.assertEqual(set(report["stress_qids"]), {"a", "b"})
        for name, parameter in model.named_parameters():
            self.assertTrue(torch.equal(parameter, before[name]))


class NativeMultimodalBatchTests(unittest.TestCase):
    @staticmethod
    def fixture(student):
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import Qwen3VLConfig, Qwen3_5Config
        from student_pilot.adapters import discover_targets, trainable_groups
        from student_pilot.diagnostic import frozen_base_check
        from student_pilot.runner import group_gradients
        from student_pilot.students import model_class

        torch.manual_seed(17)
        text = {"vocab_size": 64, "hidden_size": 16, "intermediate_size": 32, "num_hidden_layers": 2,
                "num_attention_heads": 2, "num_key_value_heads": 1, "head_dim": 8, "use_cache": False,
                "pad_token_id": 0, "rope_parameters": {"rope_type": "default", "rope_theta": 10000.0,
                                                        "mrope_section": [1, 1, 2], "partial_rotary_factor": 1.0}}
        vision = {"depth": 1, "hidden_size": 16, "intermediate_size": 32, "num_heads": 2, "out_hidden_size": 16,
                  "num_position_embeddings": 16, "patch_size": 2, "temporal_patch_size": 2, "spatial_merge_size": 2,
                  "deepstack_visual_indexes": [0] if student == "onethinker" else []}
        if student == "qwen35":
            text.update(layer_types=["linear_attention", "full_attention"], linear_key_head_dim=4,
                        linear_value_head_dim=4, linear_num_key_heads=2, linear_num_value_heads=4)
        cls = Qwen3VLConfig if student == "onethinker" else Qwen3_5Config
        config = cls(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                     vision_start_token_id=62, vision_end_token_id=63)
        config._attn_implementation = "sdpa"
        config.text_config._attn_implementation = "sdpa"
        config.vision_config._attn_implementation = "sdpa"
        config.use_cache = False
        base = model_class(student)(config)
        base.requires_grad_(False)
        targets = discover_targets(base)
        model = get_peft_model(base, LoraConfig(task_type=TaskType.CAUSAL_LM, r=2, lora_alpha=4,
                              lora_dropout=0.0, bias="none", target_modules=[name for group in targets.values() for name in group]))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.train()
        groups = trainable_groups(model, targets)
        frozen = {name: parameter._version for name, parameter in model.named_parameters() if not parameter.requires_grad}
        rows = []
        for target_length in (2, 4):
            prompt = [1] + [62, 61, 63] * 16 + [2]
            ids = torch.tensor([prompt + list(range(3, 3 + target_length))])
            labels = ids.clone()
            labels[:, :len(prompt)] = -100
            rows.append({"input_ids": ids, "attention_mask": torch.ones_like(ids), "labels": labels,
                         "mm_token_type_ids": torch.where(ids == 61, 2, 0),
                         "pixel_values_videos": torch.randn(64, 24), "video_grid_thw": torch.tensor([[16, 2, 2]])})
        return model, groups, frozen, rows

    def check_student(self, student):
        from student_pilot.diagnostic import frozen_base_check
        from student_pilot.runner import group_gradients

        model, groups, frozen, rows = self.fixture(student)
        batch = ddp_core.collate_rows(rows, 0)
        actual = ddp_core.row_losses(model, batch)
        expected = torch.stack([ddp_core.row_losses(model, row)[0] for row in rows])
        torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-5)
        actual.mean().backward()
        gradients = group_gradients(groups)
        self.assertTrue(all(value["gradient_l2"] > 0 for value in gradients.values()))
        frozen_base_check(model, frozen)
        self.assertFalse(torch.cuda.is_initialized())

    def test_native_onethinker_family_batching_and_checkpointed_gradients(self):
        self.check_student("onethinker")

    def test_native_qwen35_family_batching_and_checkpointed_gradients(self):
        self.check_student("qwen35")


if __name__ == "__main__":
    unittest.main()
