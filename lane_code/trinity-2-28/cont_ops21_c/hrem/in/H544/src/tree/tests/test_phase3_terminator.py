from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch
from transformers.video_utils import VideoMetadata

from student_pilot import batches


class Phase3TerminatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = batches.load_processor("qwen35")

    def test_both_arms_supervise_the_generation_stop_after_the_turn_end(self):
        for arm in ("candidate", "F_control"):
            for target in ("synthetic target", "synthetic target\n"):
                with self.subTest(arm=arm, target=target):
                    prompt, suffix = batches.training_text(self.processor, "Synthetic rendering check", [], target)
                    ids = self.processor.tokenizer.encode(suffix, add_special_tokens=False)
                    self.assertEqual(ids[-2:], [248046, 248044])
                    self.assertEqual(ids.count(248044), 1)
                    self.assertTrue(suffix.endswith(target + "<|im_end|><|endoftext|>"))
                    from student_pilot.trace_contract import ANSWER_FORMAT_INSTRUCTION
                    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": "Synthetic rendering check\n\n" + ANSWER_FORMAT_INSTRUCTION}]}]
                    self.assertEqual(prompt, self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
                    self.assertEqual(self.processor.tokenizer.eos_token_id, 248046)

    def test_an_unsupported_assistant_boundary_still_refuses(self):
        with self.assertRaisesRegex(ValueError, "assistant boundary changed"):
            batches.training_text(self.processor, "Synthetic rendering check", [], "synthetic target\n\n")

    def test_injected_generation_or_conversation_stops_are_not_teacher_targets(self):
        for token in ("<|endoftext|>", "<|im_end|>", "<|im_start|>"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                batches.training_text(self.processor, "Synthetic rendering check", [], "synthetic" + token + "target")

    def test_a_changed_generation_stop_token_mapping_refuses(self):
        encode = self.processor.tokenizer.encode
        def changed(text, *args, **kwargs):
            return [1] if text == "<|endoftext|>" else encode(text, *args, **kwargs)
        with mock.patch.object(self.processor.tokenizer, "encode", side_effect=changed), self.assertRaises(ValueError):
            batches.training_text(self.processor, "Synthetic rendering check", [], "synthetic target")

    def test_the_other_tokenizer_contract_is_unchanged(self):
        tokenizer = SimpleNamespace(eos_token="<|im_end|>", eos_token_id=151645)
        processor = SimpleNamespace(tokenizer=tokenizer)
        processor.apply_chat_template = lambda messages, tokenize, add_generation_prompt: "synthetic prompt" if add_generation_prompt else "synthetic prompt" + messages[-1]["content"] + tokenizer.eos_token + "\n"
        self.assertEqual(batches.training_text(processor, "synthetic question", [], "synthetic target"), ("synthetic prompt", "synthetic target<|im_end|>"))
        processor._student_pilot_student = "qwen36_27b"
        processor.tokenizer.eos_token_id = 248046
        self.assertEqual(batches.training_text(processor, "synthetic question", [], "synthetic target"), ("synthetic prompt", "synthetic target<|im_end|>"))

    def test_real_rgb_encoding_masks_both_stops_and_refuses_truncation(self):
        frames = np.zeros((32, 32, 32, 3), dtype=np.uint8)
        metadata = VideoMetadata(total_num_frames=64, fps=30.0, frames_indices=list(range(0, 64, 2)), width=32, height=32)
        batch, audit = batches.encode_arrays(self.processor, "Synthetic rendering check", [], frames, metadata, "synthetic target")
        positions = torch.where(batch["labels"][0] != -100)[0]
        self.assertEqual(batch["labels"][0, positions][-2:].tolist(), [248046, 248044])
        self.assertEqual(batch["input_ids"][0, positions][-2:].tolist(), [248046, 248044])
        self.assertEqual(len(positions), audit["assistant_tokens_including_eos"])
        self.assertTrue(torch.all(batch["labels"][0, :audit["prompt_tokens"]] == -100))
        self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
        self.assertEqual((audit["frame_count"], audit["original_frame_indices"]), (32, list(range(0, 64, 2))))
        self.assertFalse(audit["target_truncated"])
        causal = batches.prediction_positions(batch["labels"])
        self.assertEqual(batch["labels"][0, causal + 1][-2:].tolist(), [248046, 248044])
        with self.assertRaisesRegex(ValueError, "truncation is forbidden"):
            batches.encode_arrays(self.processor, "Synthetic rendering check", [], frames, metadata, "synthetic target", max_length=audit["sequence_tokens"] - 1)
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
