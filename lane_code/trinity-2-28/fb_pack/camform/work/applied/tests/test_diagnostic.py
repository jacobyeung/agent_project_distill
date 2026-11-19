import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image

from student_pilot import diagnostic_data
from student_pilot.batches import encode_row, load_processor, training_text
from student_pilot.common import ARTIFACTS, binding


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = load_processor()
        root = ARTIFACTS / "trainer_tests"
        root.mkdir(parents=True, exist_ok=True)
        cls.fixture_root = Path(tempfile.mkdtemp(prefix="diagnostic_", dir=root))
        frames = []
        for index in range(32):
            path = cls.fixture_root / f"{index:02d}.png"
            Image.new("RGB", (128, 128), color=(index * 7, 64, 96)).save(path)
            frames.append(binding(path))
        cls.row = {"qid": "synthetic-cpu-fixture", "target": "SMOKE PLACEHOLDER: not a distillation target",
                   "student_input": {"question": "Describe this synthetic test clip.", "options": [], "frames": frames,
                                     "frame_indices": list(range(32)), "timestamps": [index / 2 for index in range(32)],
                                     "fps": 2.0, "total_num_frames": 32}}

    def test_answer_free_prompt_matches_proven_rgb_training_prefix(self):
        trained, audit = encode_row(self.processor, self.row)
        prompt, prompt_audit = diagnostic_data.encode_prompt(self.processor, self.row)
        length = audit["prompt_tokens"]
        self.assertNotIn("labels", prompt)
        torch.testing.assert_close(prompt["input_ids"], trained["input_ids"][:, :length])
        torch.testing.assert_close(prompt["pixel_values_videos"], trained["pixel_values_videos"])
        torch.testing.assert_close(prompt["video_grid_thw"], trained["video_grid_thw"])
        self.assertEqual(prompt_audit["frame_count"], 32)
        self.assertEqual(prompt_audit["original_timestamps_seconds"], audit["original_timestamps_seconds"])
        self.assertFalse(prompt_audit["answer_content_in_prompt"])

    def test_diagnostic_encoder_reuses_complete_assistant_masking(self):
        expected, expected_audit = encode_row(self.processor, self.row)
        actual, audit = diagnostic_data.encode_training(self.processor, self.row)
        for key in expected:
            torch.testing.assert_close(actual[key], expected[key])
        self.assertEqual(audit["assistant_tokens_including_eos"], expected_audit["assistant_tokens_including_eos"])
        self.assertFalse(audit["target_truncated"])
        with self.subTest(student="qwen35"):
            self.check_qwen35_native_assistant_suffix_and_answer_free_prompt()

    def check_qwen35_native_assistant_suffix_and_answer_free_prompt(self):
        processor = load_processor("qwen35")
        batch, audit = diagnostic_data.encode_training(processor, self.row)
        prompt, prompt_audit = diagnostic_data.encode_prompt(processor, self.row)
        length = audit["prompt_tokens"]
        torch.testing.assert_close(prompt["input_ids"], batch["input_ids"][:, :length])
        supervised = batch["input_ids"][batch["labels"] != -100].tolist()
        suffix = processor.tokenizer.decode(supervised, skip_special_tokens=False)
        self.assertEqual(suffix, "\n</think>\n\n" + self.row["target"] + processor.tokenizer.eos_token + "<|endoftext|>")
        self.assertEqual(supervised[-2:], [248046, 248044])
        self.assertFalse(prompt_audit["answer_content_in_prompt"])
        self.assertNotIn(self.row["target"], processor.tokenizer.decode(prompt["input_ids"][0]))
        self.assertFalse(audit["target_truncated"])
        self.assertEqual(diagnostic_data.target_tokens(processor, self.row), len(supervised))

    def test_single_terminal_lf_preserves_complete_target_and_mask_for_both_students(self):
        target = "Observations\nSynthetic CPU fixture only.\nAnswer\nfixture\n"
        row = {**self.row, "target": target}
        for student, processor in (("onethinker", self.processor), ("qwen35", load_processor("qwen35"))):
            with self.subTest(student=student):
                batch, audit = diagnostic_data.encode_training(processor, row)
                prompt, _ = diagnostic_data.encode_prompt(processor, row)
                length = audit["prompt_tokens"]
                torch.testing.assert_close(prompt["input_ids"], batch["input_ids"][:, :length])
                torch.testing.assert_close(prompt["pixel_values_videos"], batch["pixel_values_videos"])
                self.assertTrue(torch.all(batch["labels"][:, :length] == -100))
                self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
                supervised = batch["input_ids"][batch["labels"] != -100].tolist()
                suffix = processor.tokenizer.decode(supervised, skip_special_tokens=False)
                prefix = "\n</think>\n\n" if student == "qwen35" else ""
                stop = "<|endoftext|>" if student == "qwen35" else ""
                self.assertEqual(suffix, prefix + target + processor.tokenizer.eos_token + stop)
                self.assertEqual(supervised[-1], 248044 if student == "qwen35" else processor.tokenizer.eos_token_id)
                self.assertEqual(diagnostic_data.target_tokens(processor, row), len(supervised))
                self.assertEqual(row["target"], target)
                self.assertFalse(audit["target_truncated"])

    def test_qwen_single_lf_exception_refuses_template_drift(self):
        processor = load_processor("qwen35")
        native = processor.apply_chat_template
        target = "Observations\nSynthetic CPU fixture only.\nAnswer\nfixture\n"
        variants = {
            "assistant_marker": lambda text: text.replace("assistant\n<think>", "assistant_changed\n<think>", 1),
            "thinking_boundary": lambda text: text.replace("\n</think>\n\n", "\n</think>\n", 1),
            "target_content": lambda text: text.replace("Synthetic CPU fixture only.", "Changed fixture text.", 1),
            "end_of_turn": lambda text: text[:-len(processor.tokenizer.eos_token + "\n")],
            "extra_suffix": lambda text: text + " ",
        }
        for name, change in variants.items():
            def render(*args, **kwargs):
                text = native(*args, **kwargs)
                return text if kwargs.get("add_generation_prompt") else change(text)

            with self.subTest(drift=name), patch.object(processor, "apply_chat_template", side_effect=render):
                with self.assertRaisesRegex(ValueError, "Pinned chat-template assistant boundary changed"):
                    training_text(processor, self.row["student_input"]["question"], [], target)

    def test_qwen_single_lf_exception_does_not_allow_other_whitespace_or_controls(self):
        processor = load_processor("qwen35")
        target = "Observations\nSynthetic CPU fixture only.\nAnswer\nfixture"
        for changed in (target + "\n\n", target + " \n", target + "\t\n", target + "\r\n",
                        target + "\u00a0\n", " " + target + "\n", "\n" + target + "\n"):
            with self.subTest(target=repr(changed)), self.assertRaisesRegex(ValueError, "Pinned chat-template assistant boundary changed"):
                training_text(processor, self.row["student_input"]["question"], [], changed)
        for control in ("<|im_start|>", "<|im_end|>", "<|video_pad|>", "<|image_pad|>"):
            with self.subTest(control=control), self.assertRaisesRegex(ValueError, "conversation/media control tokens"):
                training_text(processor, self.row["student_input"]["question"], [], target + control + "\n")

    def check_requested_student_cannot_change_a_frozen_protocol(self):
        path = self.fixture_root / "qwen_protocol.json"
        path.write_text(json.dumps({"student": "qwen35"}))
        with self.assertRaisesRegex(ValueError, "Requested student differs"):
            diagnostic_data.load_protocol(path, student="onethinker")

    def check_student_specific_training_counts_preserve_other_settings(self):
        expected = {**diagnostic_data.TRAINING, "trainable_parameters": 47271680}
        self.assertEqual(diagnostic_data.training_settings("qwen35"), expected)
        self.assertEqual(diagnostic_data.training_settings("onethinker"), diagnostic_data.TRAINING)

    def test_predeclared_training_and_generation_are_fixed(self):
        self.check_student_specific_training_counts_preserve_other_settings()
        config = diagnostic_data.TRAINING
        self.assertEqual((config["seed"], config["epochs"], config["gradient_accumulation"], config["microbatch_size"]), (17, 1, 4, 1))
        self.assertEqual((config["learning_rate"], config["weight_decay"], config["clip_norm"]), (1e-5, 0.0, 1.0))
        self.assertFalse(diagnostic_data.GENERATION["do_sample"])
        self.assertEqual(diagnostic_data.GENERATION["initial_max_new_tokens"], 16384)
        self.assertEqual(diagnostic_data.GENERATION["retry_max_new_tokens"], 32768)

    def test_native_greedy_generation_configuration_preserves_eos(self):
        from transformers import GenerationConfig
        from student_pilot.common import MODEL
        from student_pilot.diagnostic import generation_config

        native = GenerationConfig.from_pretrained(MODEL, local_files_only=True)
        for budget in (16384, 32768):
            config = generation_config(native, self.processor, budget)
            self.assertFalse(config.do_sample)
            self.assertEqual(config.max_new_tokens, budget)
            self.assertEqual(config.eos_token_id, native.eos_token_id)
            self.assertTrue(config.use_cache)
        self.assertFalse(native.use_cache)

    def test_review_packets_and_smoke_are_not_diagnostic_training(self):
        self.check_requested_student_cannot_change_a_frozen_protocol()
        for schema in ("review-packets", "student-rgb-smoke-v1"):
            path = self.fixture_root / f"{schema}.json"
            path.write_text(json.dumps({"schema": schema, "infrastructure_only": True}))
            with self.assertRaises(ValueError):
                diagnostic_data.load_training(path)

    def test_missing_outputs_have_zero_credit_without_reducing_membership(self):
        records = [diagnostic_data.zero_record(str(qid), "object_counting") for qid in range(63)]
        self.assertEqual(len(records), 63)
        self.assertEqual(sum(record["MRA"] for record in records), 0)
        self.assertTrue(all(record["is_correct"] is False for record in records))

    def test_retry_requires_wrong_answer_and_recorded_initial_cap(self):
        self.assertTrue(diagnostic_data.retry_eligible("MAX_TOKENS", 16384, 16384, False))
        self.assertFalse(diagnostic_data.retry_eligible("MAX_TOKENS", 16384, 16384, True))
        self.assertFalse(diagnostic_data.retry_eligible("STOP", 16384, 16384, False))
        self.assertFalse(diagnostic_data.retry_eligible("MAX_TOKENS", 32768, 32768, False))
        self.assertFalse(diagnostic_data.retry_eligible("MAX_TOKENS", 17, 16384, False))


if __name__ == "__main__":
    unittest.main()
