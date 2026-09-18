import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from torch.utils.data import DataLoader, Dataset

from dataset_builder_fixture import fixture_directory, make_fixture
from student_pilot.dataset_builder import DatasetBuildError, build_dataset
from student_pilot.dataset_loader import SmokeCollator, StudentDataset, dry_run


class ByteTokenizer:
    eos_token = "<|im_end|>"
    eos_token_id = 2
    pad_token_id = 0
    padding_side = "right"
    tokens = {"<|im_end|>": 2, "<|video_pad|>": 3}

    def encode(self, text, add_special_tokens=False):
        ids = []
        while text:
            marker = next((token for token in self.tokens if text.startswith(token)), None)
            if marker:
                ids.append(self.tokens[marker])
                text = text[len(marker):]
            else:
                ids.append(ord(text[0]) + 10)
                text = text[1:]
        return ids

    def decode(self, ids, skip_special_tokens=False):
        inverse = {value: key for key, value in self.tokens.items()}
        return "".join(inverse[int(item)] if int(item) in inverse else chr(int(item) - 10) for item in ids)


class VideoProcessor:
    def __init__(self):
        self.tokenizer = ByteTokenizer()
        self.video_processor = SimpleNamespace(temporal_patch_size=2, merge_size=2)
        self.video_token_id = 3
        self.observed = []

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        user = messages[0]["content"]
        prompt = "<user><|video_pad|>" + user[-1]["text"] + "</user><assistant>"
        return prompt if len(messages) == 1 else prompt + messages[1]["content"] + self.tokenizer.eos_token + "\n"

    def __call__(self, text, videos, video_metadata, do_sample_frames, size, return_tensors, return_metadata):
        self.observed.append((videos[0].shape, list(video_metadata[0].frames_indices), do_sample_frames))
        metadata = video_metadata[0]
        stamps = [(metadata.frames_indices[i] + metadata.frames_indices[i + 1]) / (2 * metadata.fps) for i in range(0, 32, 2)]
        media = "".join(f"<{stamp:.1f} seconds><|video_pad|>" for stamp in stamps)
        ids = torch.tensor([self.tokenizer.encode(text[0].replace("<|video_pad|>", media))])
        return {"input_ids": ids, "attention_mask": torch.ones_like(ids), "video_metadata": video_metadata,
                "video_grid_thw": torch.tensor([[16, 2, 2]]), "pixel_values_videos": torch.zeros(64, 1536),
                "mm_token_type_ids": torch.zeros_like(ids)}


class DatasetLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = fixture_directory("loader")
        fixture = make_fixture(cls.root / "sources")
        cls.admission_index = fixture["index"]
        cls.result = build_dataset(fixture["index"], cls.root / "dataset", workspace_root=cls.root,
                                   validation_fraction=0.1, shard_size=1)

    def dataset(self, **kwargs):
        return StudentDataset(self.result["manifest"], workspace_root=self.root, allow_fixtures=True, **kwargs)

    def test_is_torch_dataset_and_exposes_only_smoke_row_fields(self):
        dataset = self.dataset(split="all")
        self.assertIsInstance(dataset, Dataset)
        self.assertEqual(len(dataset), 3)
        row = dataset[0]
        self.assertEqual(set(row), {"qid", "student_input", "target"})
        self.assertEqual(len(row["student_input"]["frames"]), 32)
        self.assertEqual(set(row["student_input"]), {"question", "options", "frames", "frame_indices", "timestamps", "fps", "total_num_frames"})
        self.assertTrue(all(Path(f["path"]).is_relative_to(self.root) for f in row["student_input"]["frames"]))
        self.assertIsInstance(row["student_input"]["options"], list)

    def test_fixture_dataset_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(DatasetBuildError, "fixture"):
            StudentDataset(self.result["manifest"], workspace_root=self.root, split="all")

    def test_training_and_validation_loaders_match_written_proof(self):
        proof = json.loads((self.root / "dataset/split_proof.json").read_text())
        self.assertEqual(len(self.dataset(split="train")), proof["training_questions"])
        self.assertEqual(len(self.dataset(split="validation")), proof["heldout_questions"])

    def test_real_smoke_encoder_collation_masks_user_images_and_padding(self):
        dataset = self.dataset(split="all")
        processor = VideoProcessor()
        collator = SmokeCollator(processor)
        loader = DataLoader(dataset, batch_size=1, collate_fn=collator, num_workers=0)
        for batch in loader:
            self.assertEqual(set(batch), {"input_ids", "attention_mask", "mm_token_type_ids", "pixel_values_videos", "video_grid_thw", "labels"})
            audit = collator.last_audit
            prompt = audit["prompt_tokens"]
            self.assertTrue(torch.all(batch["labels"][:, :prompt] == -100))
            self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
            self.assertEqual(int((batch["labels"] != -100).sum()), audit["assistant_tokens_including_eos"])
            self.assertFalse(audit["target_truncated"])
            self.assertEqual(audit["frame_count"], 32)
            self.assertEqual(processor.observed[-1][0], (32, 32, 32, 3))
            self.assertFalse(processor.observed[-1][2])

    def test_collator_refuses_multiple_examples_and_overflow(self):
        dataset = self.dataset(split="all")
        collator = SmokeCollator(VideoProcessor())
        with self.assertRaises(ValueError):
            collator([dataset[0], dataset[1]])
        row = dataset[0]
        row["target"] = "Long explanation. " * 2000 + "<ANSWER>A</ANSWER>"
        with self.assertRaisesRegex(ValueError, "truncation is forbidden"):
            collator([row])

    def test_tokenizer_dry_run_explicitly_labels_both_models_as_mocks(self):
        report = dry_run(self.dataset(split="all"), num_examples=3, tokenizer_paths={
            "onethinker": "/data2/outside-scope-tokenizer", "qwen35": "/data2/outside-scope-tokenizer"})
        self.assertEqual(set(report["models"]), {"onethinker", "qwen35"})
        self.assertEqual(report["examples"], 3)
        for stats in report["models"].values():
            self.assertTrue(stats["mocked"])
            self.assertFalse(stats["visual_expansion_measured"])
            self.assertFalse(stats["model_token_lengths_verified"])
            self.assertIn("workspace", stats["reason"])
            self.assertGreater(stats["sequence_text_tokens"]["max"], 0)
            self.assertEqual(stats["sequence_text_tokens"]["count"], 3)

    def test_local_tokenizer_for_another_model_is_refused(self):
        from student_pilot.dataset_loader import load_offline_tokenizer

        local = self.root / "wrong_tokenizer"
        local.mkdir()
        for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"):
            with (local / name).open("x") as stream:
                stream.write("{}")
        with self.assertRaisesRegex(DatasetBuildError, "model config"):
            load_offline_tokenizer("onethinker", local, self.root)

    def test_missing_local_tokenizer_is_disclosed_as_a_mock(self):
        from student_pilot.dataset_loader import load_offline_tokenizer

        _, metadata = load_offline_tokenizer("qwen35", self.root / "absent_tokenizer", self.root)
        self.assertTrue(metadata["mocked"])
        self.assertIn("unavailable", metadata["reason"])

    def test_changed_shard_and_split_proof_are_rejected(self):
        for name in ("shard", "proof"):
            with self.subTest(name=name):
                result = build_dataset(self.admission_index, self.root / ("corrupt_" + name), self.root)
                manifest = json.loads(Path(result["manifest"]).read_text())
                member = manifest["shards"][0] if name == "shard" else manifest["split_proof"]
                with (Path(result["manifest"]).parent / member["path"]).open("ab") as stream:
                    stream.write(b"\n")
                with self.assertRaises(DatasetBuildError):
                    StudentDataset(result["manifest"], self.root, split="all", allow_fixtures=True)

    def test_shard_drift_after_dataset_initialization_is_rejected(self):
        result = build_dataset(self.admission_index, self.root / "late_shard_drift", self.root)
        dataset = StudentDataset(result["manifest"], self.root, split="all", allow_fixtures=True)
        path, offset, _ = dataset.locations[0]
        with path.open("r+b") as stream:
            stream.seek(offset)
            stream.write(b"!")
        with self.assertRaisesRegex(DatasetBuildError, "changed after"):
            dataset[0]

    def test_smoke_collator_rechecks_rgb_hashes(self):
        result = build_dataset(self.admission_index, self.root / "late_rgb_drift", self.root)
        dataset = StudentDataset(result["manifest"], self.root, split="all", allow_fixtures=True)
        row = dataset[0]
        with Path(row["student_input"]["frames"][0]["path"]).open("ab") as stream:
            stream.write(b"changed RGB bytes")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            SmokeCollator(VideoProcessor())([row])

    def test_tokenizer_dry_run_does_not_swallow_broken_real_template(self):
        tokenizer = ByteTokenizer()
        tokenizer.apply_chat_template = lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("broken template"))
        with patch("student_pilot.dataset_loader.load_offline_tokenizer", return_value=(tokenizer, {"mocked": False, "reason": None})):
            with self.assertRaisesRegex(ValueError, "broken template"):
                dry_run(self.dataset(split="all"), num_examples=1)


if __name__ == "__main__":
    unittest.main()
