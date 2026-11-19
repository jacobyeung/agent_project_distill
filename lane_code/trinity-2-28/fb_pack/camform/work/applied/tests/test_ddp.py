import copy
import json
import math
import multiprocessing
import os
import socket
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel

from student_pilot import ddp_config, ddp_core
from student_pilot.common import canonical_bytes, digest_json


class TinyHead(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.base = torch.nn.Linear(7, 19, bias=False)
        self.base.requires_grad_(False)
        self.lora_A = torch.nn.Parameter(torch.randn(3, 7) * 0.1)
        self.lora_B = torch.nn.Parameter(torch.zeros(19, 3))

    def forward(self, hidden):
        return self.base(hidden) + (hidden @ self.lora_A.T) @ self.lora_B.T


class TinyAdapter(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(model_type="qwen3_vl")
        self.embedding = torch.nn.Embedding(19, 7)
        self.embedding.requires_grad_(False)
        self.lm_head = TinyHead()

    def get_output_embeddings(self):
        return self.lm_head

    def forward(self, input_ids, attention_mask=None, logits_to_keep=0, use_cache=False,
                output_hidden_states=False, return_dict=True):
        hidden = self.embedding(input_ids)
        positions = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
        return SimpleNamespace(logits=self.lm_head(hidden[:, positions]))


def fixed_rows():
    rows = []
    for index in range(8):
        ids = torch.tensor([[1, 2] + [3 + (index + j) % 15 for j in range(1 + index % 4)]])
        labels = ids.clone()
        labels[:, :2] = -100
        rows.append({"input_ids": ids, "attention_mask": torch.ones_like(ids), "labels": labels})
    return rows


def equivalence_worker(rank, world_size, port, output, microbatch=2):
    torch.set_num_threads(1)
    torch.manual_seed(17)
    model = TinyAdapter()
    if world_size > 1:
        dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=rank,
                                world_size=world_size, timeout=timedelta(seconds=60))
        model = DistributedDataParallel(model)
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=0.01, weight_decay=0.0)
    rows = fixed_rows()
    losses = []
    try:
        for _ in range(2):
            optimizer.zero_grad(set_to_none=True)
            slots = ddp_core.rank_slots(list(range(8)), rank, world_size, microbatch)
            local_sum = 0.0
            for start in range(0, len(slots), microbatch):
                chunk = slots[start:start + microbatch]
                batch = ddp_core.collate_rows([rows[index] for index, _ in chunk], 0)
                row_loss = ddp_core.backward_batch(model, batch, [weight for _, weight in chunk],
                    world_size, 8, synchronize=start + microbatch == len(slots))
                local_sum += sum(float(value) * weight for value, (_, weight) in zip(row_loss, chunk))
            reduced = torch.tensor(local_sum, dtype=torch.float64)
            if world_size > 1:
                dist.all_reduce(reduced)
            losses.append(float(reduced) / 8)
            torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
            optimizer.step()
        state = model.module if world_size > 1 else model
        value = {"losses": losses, "adapter": {name: p.detach().tolist() for name, p in state.named_parameters()
                                               if p.requires_grad}}
        Path(output).write_bytes(canonical_bytes(value))
    finally:
        if world_size > 1:
            dist.destroy_process_group()


class ConfigTests(unittest.TestCase):
    def test_standard_defaults_and_counts_for_both_students(self):
        for student, expected in (("onethinker", 104987648), ("qwen35", 102530048)):
            config = ddp_config.normalize_training_config({}, student)
            self.assertEqual(config["version"], "vlm-lora-ddp-v2")
            self.assertEqual((config["lora_rank"], config["lora_alpha"], config["lora_dropout"]), (32, 64, 0.05))
            self.assertEqual((config["effective_batch_size"], config["epochs"], config["seed"]), (32, 3, 17))
            self.assertEqual(config["learning_rate"], 1e-4)
            self.assertEqual(config["betas"], [0.9, 0.999])
            self.assertEqual(config["trainable_parameters"], expected)
            self.assertEqual(config, ddp_config.normalize_training_config(config, student))

    def test_checkpoint_interval_is_run_control_and_leaves_the_training_hash(self):
        for student in ("onethinker", "qwen35"):
            default = ddp_config.normalize_training_config({}, student)
            changed = ddp_config.normalize_training_config({"checkpoint_every_steps": 1}, student)
            self.assertNotIn("checkpoint_every_steps", default)
            self.assertEqual(digest_json(default), digest_json(changed))
            self.assertEqual(ddp_config.run_control_from_config({})["checkpoint_every_steps"], 25)
            self.assertEqual(ddp_config.run_control_from_config({"checkpoint_every_steps": 1}), {"checkpoint_every_steps": 1})
            self.assertNotEqual(digest_json(ddp_config.normalize_run_control({})),
                                digest_json(ddp_config.normalize_run_control({"checkpoint_every_steps": 1})))
            for interval in (0, -1, True, 2.5, "25", None):
                with self.subTest(interval=interval), self.assertRaisesRegex(ValueError, "checkpoint_every_steps"):
                    ddp_config.run_control_from_config({"checkpoint_every_steps": interval})
            with self.assertRaisesRegex(ValueError, "Run control contains unknown settings"):
                ddp_config.normalize_run_control({"learning_rate": 0.1})

    def test_memory_fit_safety_factor_normalizes_and_hashes_default(self):
        for student in ("onethinker", "qwen35"):
            with self.subTest(student=student):
                default = ddp_config.normalize_training_config({}, student)
                explicit = ddp_config.normalize_training_config({"memory_fit_safety_factor": 1.15}, student)
                self.assertEqual(default["memory_fit_safety_factor"], 1.15)
                self.assertEqual(digest_json(default), digest_json(explicit))
                for factor in (1.0, 1.25):
                    changed = ddp_config.normalize_training_config({"memory_fit_safety_factor": factor}, student)
                    self.assertEqual(changed["memory_fit_safety_factor"], factor)
                    self.assertEqual(changed, ddp_config.normalize_training_config(changed, student))
                    self.assertNotEqual(digest_json(default), digest_json(changed))

    def test_invalid_memory_fit_safety_factors_refuse(self):
        for factor in (0, -1, 0.99, True, None, "1.15", float("nan"), float("inf"), -float("inf")):
            with self.subTest(factor=factor), self.assertRaisesRegex(ValueError, "memory_fit_safety_factor"):
                ddp_config.normalize_training_config({"memory_fit_safety_factor": factor}, "onethinker")

    def test_invalid_or_unimplemented_settings_refuse(self):
        for patch in ({"world_size": 1}, {"world_size": 9}, {"lora_rank": 0}, {"learning_rate": float("nan")},
                      {"lora_dropout": 1.0}, {"betas": [0.9, 1.0]}, {"seed": -1}, {"max_microbatch_size": 0},
                      {"version": "clean"}, {"precision": "float16"}, {"unknown": True},
                      {"trainable_parameters": 1}, {"max_steps": True}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                ddp_config.normalize_training_config(patch, "onethinker")

    def test_scheduler_warms_up_then_decays_to_zero(self):
        settings = ddp_config.normalize_training_config({"warmup_ratio": 0.1}, "onethinker")
        rates = [ddp_core.schedule_lr(step, 100, settings) for step in range(100)]
        self.assertAlmostEqual(rates[0], 1e-5)
        self.assertAlmostEqual(rates[9], 1e-4)
        self.assertTrue(all(a < b for a, b in zip(rates[:9], rates[1:10])))
        self.assertTrue(all(a >= b for a, b in zip(rates[9:], rates[10:])))
        self.assertAlmostEqual(rates[-1], 0.0)
        self.assertTrue(all(math.isfinite(value) for value in rates))

    def test_hash_changes_with_frozen_training_settings(self):
        config = ddp_config.normalize_training_config({}, "onethinker")
        changed = ddp_config.normalize_training_config({"world_size": 4}, "onethinker")
        self.assertNotEqual(digest_json(config), digest_json(changed))
        self.assertEqual(digest_json(config), digest_json(copy.deepcopy(config)))


class BatchTests(unittest.TestCase):
    def test_epoch_shuffle_and_last_batch_padding_are_deterministic(self):
        first = list(ddp_core.global_batches(35, 0))
        self.assertEqual(first, list(ddp_core.global_batches(35, 0)))
        self.assertNotEqual(first, list(ddp_core.global_batches(35, 1)))
        self.assertEqual([row["source_rows"] for row in first], [32, 3])
        self.assertEqual([row["padding_rows"] for row in first], [0, 29])
        self.assertEqual(first[-1]["indices"][3:], first[0]["indices"][:29])
        actual = [index for batch in first for index in batch["indices"][:batch["source_rows"]]]
        self.assertEqual(sorted(actual), list(range(35)))
        self.assertEqual(len(list(ddp_core.global_batches(1, 0))[0]["indices"]), 32)

    def test_equal_rank_slots_preserve_exact_global_weight_for_two_to_eight_ranks(self):
        for world in range(2, 9):
            for micro in (1, 2, 4):
                ranks = [ddp_core.rank_slots(list(range(32)), rank, world, micro) for rank in range(world)]
                with self.subTest(world=world, micro=micro):
                    self.assertEqual(len({len(slots) for slots in ranks}), 1)
                    self.assertEqual(len(ranks[0]) % micro, 0)
                    active = [index for slots in ranks for index, weight in slots if weight]
                    self.assertEqual(sorted(active), list(range(32)))
                    self.assertEqual(sum(weight for slots in ranks for _, weight in slots), 32)

    def test_collation_keeps_assistant_mask_and_original_multimodal_rows(self):
        rows = fixed_rows()[:2]
        for i, row in enumerate(rows):
            row["mm_token_type_ids"] = torch.zeros_like(row["input_ids"])
            row["pixel_values_videos"] = torch.full((2 + i, 3), float(i))
            row["video_grid_thw"] = torch.tensor([[1, 2 + i, 1]])
        batch = ddp_core.collate_rows(rows, 0)
        self.assertEqual(batch["input_ids"].shape, (2, 4))
        self.assertEqual(batch["labels"][0, -1].item(), -100)
        self.assertEqual(batch["attention_mask"][0, -1].item(), 0)
        self.assertEqual(batch["video_grid_thw"].tolist(), [[1, 2, 1], [1, 3, 1]])
        self.assertTrue(torch.equal(batch["pixel_values_videos"], torch.cat([row["pixel_values_videos"] for row in rows])))

    def test_batched_loss_is_mean_per_row_not_mean_per_token(self):
        torch.manual_seed(17)
        model = TinyAdapter()
        rows = fixed_rows()
        actual = ddp_core.row_losses(model, ddp_core.collate_rows(rows, 0))
        expected = torch.stack([ddp_core.row_losses(model, row)[0] for row in rows])
        torch.testing.assert_close(actual, expected, rtol=1e-6, atol=1e-6)
        tokens = torch.tensor([int((row["labels"] != -100).sum()) for row in rows])
        self.assertGreater(abs(float((actual.mean() - (actual * tokens).sum() / tokens.sum()).detach())), 1e-4)

    def test_two_process_gloo_matches_single_process_loss_and_adapter_updates(self):
        root = Path(tempfile.mkdtemp(prefix="ddp_equivalence_", dir=os.environ["LANE_TEST_OUTPUT"]))
        equivalence_worker(0, 1, 0, root / "single.json")
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
        context = multiprocessing.get_context("spawn")
        workers = [context.Process(target=equivalence_worker, args=(rank, 2, port, str(root / f"rank{rank}.json")))
                   for rank in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(150)
            self.assertFalse(worker.is_alive(), "Gloo CPU worker timed out")
            self.assertEqual(worker.exitcode, 0)
        reference = json.loads((root / "single.json").read_text())
        for rank in range(2):
            actual = json.loads((root / f"rank{rank}.json").read_text())
            torch.testing.assert_close(torch.tensor(actual["losses"]), torch.tensor(reference["losses"]), rtol=0, atol=1e-5)
            for name, value in reference["adapter"].items():
                torch.testing.assert_close(torch.tensor(actual["adapter"][name]), torch.tensor(value), rtol=0, atol=1e-5)


if __name__ == "__main__":
    unittest.main()
