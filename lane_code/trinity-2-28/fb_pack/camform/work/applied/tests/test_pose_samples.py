"""Cambrian-P pose-only samples at 32 frames: sampling modes, GT targets, the camera head with fewer than 16 groups,
the LM row routing, augmentation determinism, and the N-frame encoder (equal to encode_arrays at 32 frames)."""
import collections
import os
import random
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np
import torch

from student_pilot import camera_targets, ddp_core, ddp_training, geometry_input, pose_samples
from tests.test_camera import SMALL, PIN, record_for, trajectory

PROCESSOR = Path("/scratch/jjyeung/fullft/inputs/qwen35_processor")


def output_root(prefix):
    return Path(tempfile.mkdtemp(prefix=prefix, dir=os.environ["LANE_TEST_OUTPUT"]))


class SamplingTests(unittest.TestCase):
    def test_two_modes_and_sizes_follow_cut3r(self):
        rng = random.Random(3)
        draws = [pose_samples.sample_order(rng) for _ in range(4000)]
        modes = collections.Counter(d[0] for d in draws)
        self.assertLess(abs(modes["temporal"] - modes["collection"]), 250)
        self.assertEqual({d[1] for d in draws}, set(pose_samples.SAMPLE_SIZES))
        for mode, size, order, stride, flipped in draws:
            self.assertEqual(len(order), size)
            self.assertEqual(len(set(order)), size)
            self.assertTrue(all(0 <= k < 32 for k in order))
            if mode == "temporal":
                forward = order[::-1] if flipped else order
                self.assertTrue(1 <= stride <= 32 // size)
                self.assertEqual(forward, [forward[0] + stride * k for k in range(size)])
        self.assertTrue(any(d[0] == "temporal" and d[4] for d in draws))

    def test_targets_equal_the_label_builder_on_the_natural_order(self):
        poses, intrinsics = trajectory(1)
        camera, mask, scale, gravity = pose_samples.encode_sample(poses, intrinsics, (480, 640), list(range(32)))
        reference, ref_mask, ref_scale = camera_targets.encode_cameras(poses, intrinsics, (480, 640))
        self.assertTrue(np.allclose(camera, reference) and (mask == ref_mask).all())
        self.assertAlmostEqual(scale, ref_scale)
        self.assertTrue(np.allclose(gravity, camera_targets.encode_gravity(poses)[0]))

    def test_targets_of_a_reversed_short_sample(self):
        poses, intrinsics = trajectory(2)
        order = [30, 27, 24, 21, 18, 15, 12, 9]
        camera, mask, scale, gravity = pose_samples.encode_sample(poses, intrinsics, (480, 640), order)
        self.assertEqual(mask.tolist(), [True] * 4 + [False] * 12)
        self.assertTrue(np.all(camera[4:] == 0))
        for g in range(4):
            relative = np.linalg.inv(poses[order[2 * g + 1]]) @ poses[order[0]]
            self.assertTrue(np.allclose(camera[g, :3], relative[:3, 3]))
        up = poses[30][:3, :3].T @ np.array([0.0, 0.0, 1.0])
        self.assertTrue(np.allclose(gravity, up / np.linalg.norm(up)))
        self.assertGreater(scale, 0)

    def test_rows_carry_validated_records_and_join_the_bank_loader(self):
        poses, intrinsics = trajectory(3)
        source = {"qid": "q", "dataset": "d1", "scene": "vabc", "student_input": {
            "question": "x", "options": [], "frames": [{"path": f"/f/{k}", "sha256": f"{k:064x}"} for k in range(32)],
            "frame_indices": list(range(0, 320, 10)), "timestamps": [k / 10 for k in range(0, 320, 10)], "fps": 10.0,
            "total_num_frames": 400}}
        rows = [pose_samples.build_row(source, {"c2w": poses, "intrinsics": intrinsics, "raster_hw": (480, 640)}, i, 17)
                for i in range(20)]
        self.assertEqual(len({row["qid"] for row in rows}), 20)
        again = pose_samples.build_row(source, {"c2w": poses, "intrinsics": intrinsics, "raster_hw": (480, 640)}, 3, 17)
        self.assertEqual(again, rows[3])
        for row in rows:
            record = pose_samples.check_sample(row)
            groups = row["pose_sample"]["frames"] // 2
            self.assertFalse(any(record["camera_mask"][groups:]))
            self.assertEqual(record["lm_weight"], 0.0)
            self.assertEqual(row["student_input"]["frame_indices"],
                             [source["student_input"]["frame_indices"][k] for k in row["pose_sample"]["positions"]])
        broken = {**rows[0], "pose_sample": {**rows[0]["pose_sample"], "frames": 6}}
        with self.assertRaises(ValueError):
            pose_samples.check_sample(broken)


class VariableGroupHeadTests(unittest.TestCase):
    def setUp(self):
        from student_pilot import camera_config
        from student_pilot.camera_head import CameraSupervision
        torch.manual_seed(0)
        self.head = CameraSupervision(16, camera_config.normalize({"weight": 1.0, **SMALL, "supervision": PIN}))

    def targets(self, rows):
        positions, target, mask, scale = [], [], [], []
        for groups, seed in rows:
            record = record_for(seed)
            row_mask = np.asarray(record["camera_mask"]) & (np.arange(16) < groups)
            positions.append([5 + 3 * g if g < groups else -1 for g in range(16)])
            target.append(record["camera"])
            mask.append(row_mask.tolist())
            scale.append(record["trajectory_scale"])
        return {"aux_camera_positions": torch.tensor(positions), "aux_camera_target": torch.tensor(target, dtype=torch.float32),
                "aux_camera_mask": torch.tensor(mask), "aux_camera_scale": torch.tensor(scale, dtype=torch.float32)}

    def test_full_rows_are_unchanged_and_padded_groups_are_invisible(self):
        hidden = torch.randn(2, 60, 16)
        full = self.head.loss(hidden[:1], self.targets([(16, 0)]))
        mixed = self.head.loss(hidden, self.targets([(16, 0), (4, 1)]))
        self.assertTrue(torch.allclose(mixed[0], full[0], atol=1e-6))
        alone = self.head.loss(hidden[1:], self.targets([(4, 1)]))
        changed = hidden.clone()
        changed[1, 0] += 5.0           # position 0 is what the padded slots read
        changed[1, 5 + 3 * 10] += 5.0  # a carrier position the short row does not own
        again = self.head.loss(changed[1:], self.targets([(4, 1)]))
        self.assertTrue(torch.allclose(alone, again, atol=1e-6))
        self.assertGreater(float(alone[0]), 0)

    def test_carriers_follow_the_row_group_count(self):
        ids = torch.tensor([[1] + [62, 61, 61, 63] * 4 + [2, 3, 4]])
        batch = {"input_ids": ids, "attention_mask": torch.ones_like(ids), "labels": torch.full_like(ids, -100)}
        batch["labels"][0, -2:] = ids[0, -2:]

        class Tok:
            def convert_tokens_to_ids(self, token):
                return {"<|fim_middle|>": 59, "<|video_pad|>": 61}[token]

            def encode(self, text, add_special_tokens=False):
                return [59]
        result = camera_targets.insert_carriers(batch, Tok())
        self.assertEqual(int((result["input_ids"] == 59).sum()), 4)
        positions = result["aux_camera_positions"][0].tolist()
        self.assertEqual(positions[4:], [-1] * 12)
        self.assertTrue(all(result["input_ids"][0, p] == 59 for p in positions[:4]))


class RoutingTests(unittest.TestCase):
    def test_pose_rows_leave_the_lm_mean_and_question_only_steps_are_unchanged(self):
        rows = [{"category": "camera_pose_only"}, {"category": "count"}, {"category": "count"}, {"category": "x"}]
        self.assertEqual(ddp_training.lm_row_scale(rows, [0, 1, 2, 3]), 4 / 3)
        self.assertEqual(ddp_training.lm_row_scale(rows, [1, 2, 3, 3]), 1.0)
        with self.assertRaises(ValueError):
            ddp_training.lm_row_scale(rows, [0, 0])

    def test_lm_scale_multiplies_only_the_language_model_term(self):
        from tests.test_ddp_models import NativeMultimodalBatchTests
        model, _, _, source = NativeMultimodalBatchTests.fixture("qwen35")
        batch = ddp_core.collate_rows(source, 0)
        base = ddp_core.row_losses(model, batch)
        scaled = ddp_core.row_losses(model, batch, lm_scale=1.5)
        self.assertTrue(torch.allclose(scaled, base * 1.5))
        self.assertTrue(torch.equal(ddp_core.row_losses(model, batch, lm_scale=1.0), base))


class QuestionOrderTests(unittest.TestCase):
    """CPD's question rows keep FT_A's exact order; the pose-only rows take seeded slots between them."""

    def real(self, row_count, epoch, flags, batch=64):
        return [index for window in ddp_core.global_batches(row_count, epoch, batch, 17, flags)
                for index in window["indices"][:window["source_rows"]]]

    def test_question_subsequence_equals_the_control_and_pose_rows_are_spread(self):
        questions = [{"qid": f"q{index}", "category": "count"} for index in range(1000)]
        poses = [{"qid": f"p{index}", "category": "camera_pose_only"} for index in range(90)]
        rng = random.Random(3)
        interleaved = list(questions)
        for row in poses:  # pose rows anywhere in the manifest; the question rows keep their relative order
            interleaved.insert(rng.randrange(len(interleaved) + 1), row)
        for cpd_rows in (questions + poses, interleaved):
            flags = [row["category"] == "camera_pose_only" for row in cpd_rows]
            for epoch in (0, 1):
                control = [questions[index]["qid"] for index in self.real(len(questions), epoch, None)]
                order = [cpd_rows[index]["qid"] for index in self.real(len(cpd_rows), epoch, flags)]
                self.assertEqual([qid for qid in order if qid.startswith("q")], control)
                self.assertEqual(sorted(qid for qid in order if qid.startswith("p")), sorted(row["qid"] for row in poses))
                self.assertEqual(ddp_core.question_order([row["qid"] for row in cpd_rows], epoch, 17, flags),
                                 ddp_core.question_order([row["qid"] for row in questions], epoch, 17))
                slots = [position for position, qid in enumerate(order) if qid.startswith("p")]
                self.assertLess(abs(sum(slots) / len(slots) - len(order) / 2), len(order) / 10)
                windows = list(ddp_core.global_batches(len(cpd_rows), epoch, 64, 17, flags))
                self.assertGreater(sum(any(flags[i] for i in w["indices"]) for w in windows), len(windows) * 3 // 4)
        epochs = [[cpd for cpd in self.real(len(interleaved), epoch, flags)] for epoch in (0, 1)]
        self.assertNotEqual(epochs[0], epochs[1])

    def test_without_pose_rows_the_order_is_the_plain_shuffle(self):
        for count, epoch, seed in ((1, 0, 17), (37, 2, 5), (1000, 1, 17)):
            order = list(range(count))
            random.Random(seed + epoch).shuffle(order)
            self.assertEqual(ddp_core.epoch_order(count, epoch, seed), order)
            self.assertEqual(ddp_core.epoch_order(count, epoch, seed, [False] * count), order)
            first = next(ddp_core.global_batches(count, epoch, 8, seed))
            self.assertEqual(first["indices"][:first["source_rows"]], order[:8])
        with self.assertRaises(ValueError):
            ddp_core.epoch_order(3, 0, 17, [True, True, True])
        with self.assertRaises(ValueError):
            ddp_core.epoch_order(3, 0, 17, [True, False])


@unittest.skipUnless(PROCESSOR.is_dir(), "needs the staged Qwen3.5 processor files")
class EncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        cls.processor = AutoProcessor.from_pretrained(str(PROCESSOR), local_files_only=True, trust_remote_code=False)
        cls.processor.tokenizer.padding_side = "right"

    def metadata(self, indices, fps=10.0):
        from transformers.video_utils import VideoMetadata
        return VideoMetadata(total_num_frames=400, fps=fps, frames_indices=list(indices), width=640, height=480)

    def test_32_frames_equal_encode_arrays_exactly(self):
        from student_pilot.batches import encode_arrays
        arrays = np.random.default_rng(0).integers(0, 255, (32, 480, 640, 3), dtype=np.uint8)
        indices = list(range(0, 320, 10))
        reference, ref_audit = encode_arrays(self.processor, "How many chairs?", ["A. 1", "B. 2"], arrays,
                                             self.metadata(indices), "<think>\n\n</think>\n\nB")
        batch, audit = pose_samples.encode_frames(self.processor, "How many chairs?", ["A. 1", "B. 2"], arrays,
                                                  self.metadata(indices), "<think>\n\n</think>\n\nB")
        self.assertEqual(batch.keys(), reference.keys())
        for key in reference:
            self.assertTrue(torch.equal(batch[key], reference[key]), key)
        self.assertEqual(audit, ref_audit)

    def test_short_reordered_samples_keep_the_per_frame_resolution(self):
        arrays = np.random.default_rng(1).integers(0, 255, (32, 480, 640, 3), dtype=np.uint8)
        full = pose_samples.encode_frames(self.processor, pose_samples.PROMPT, [], arrays, self.metadata(range(0, 320, 10)),
                                          pose_samples.TARGET)[1]
        order = [31, 3, 17, 8, 22, 0, 9, 14]
        short = pose_samples.encode_frames(self.processor, pose_samples.PROMPT, [], arrays[order],
                                           self.metadata([10 * k for k in order]), pose_samples.TARGET)[1]
        self.assertEqual(short["processed_height_width"], full["processed_height_width"])
        self.assertEqual(short["video_grid_thw"][0][0], 4)
        self.assertEqual(short["visual_tokens"] * 4, full["visual_tokens"])

    def test_augmentation_is_deterministic_per_row(self):
        arrays = np.random.default_rng(2).integers(0, 255, (8, 48, 64, 3), dtype=np.uint8)
        settings = {**pose_samples.AUGMENT, "seed": 5}
        first, second = pose_samples.augment(arrays, settings), pose_samples.augment(arrays, settings)
        self.assertTrue(np.array_equal(first, second))
        self.assertFalse(np.array_equal(first, arrays))
        self.assertEqual(first.dtype, np.uint8)


if __name__ == "__main__":
    unittest.main()


BASE_X = Path("/scratch/jjyeung/rung2_push/r2a_w32/config_w32.json")


class FrameSettingTests(unittest.TestCase):
    def test_knob_normalizes_and_the_default_keeps_the_old_encoder(self):
        from student_pilot import ddp_config
        self.assertEqual(pose_samples.normalize_frames(pose_samples.DEFAULT_FRAMES), pose_samples.DEFAULT_FRAMES)
        reduced = {"count": 64, "pixels_per_frame": [16384, 73728]}
        settings = ddp_config.normalize_training_config({"world_size": 2, "frames": reduced}, "qwen35")
        self.assertEqual(settings["frames"], reduced)
        self.assertNotIn("frames", ddp_config.normalize_training_config({"world_size": 2}, "qwen35"))
        for value in ({"count": 48, "pixels_per_frame": [1, 2]}, {"count": 32}, {"count": 32, "pixels_per_frame": [2, 1]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                pose_samples.normalize_frames(value)
        calls = []
        with unittest.mock.patch("student_pilot.diagnostic_data.encode_training", side_effect=lambda p, r: calls.append(r) or ("b", "a")):
            self.assertEqual(pose_samples.encode_row(None, {"qid": "q"}, pose_samples.DEFAULT_FRAMES), ("b", "a"))
            self.assertEqual(pose_samples.encode_row(None, {"qid": "q"}), ("b", "a"))
        self.assertEqual(len(calls), 2)


@unittest.skipUnless(PROCESSOR.is_dir(), "needs the staged Qwen3.5 processor files")
class SixtyFourFrameTests(unittest.TestCase):
    def test_64_frames_at_224x288_keep_their_resolution(self):
        from PIL import Image
        from transformers import AutoProcessor
        processor = AutoProcessor.from_pretrained(str(PROCESSOR), local_files_only=True, trust_remote_code=False)
        root = output_root("frames64_")
        frames = []
        for k in range(64):
            path = root / f"{k}.png"
            Image.new("RGB", (640, 480), (k * 3, 100, 200 - k)).save(path)
            import hashlib
            frames.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        row = {"qid": "q64", "target": "<think>\n\n</think>\n\nB", "student_input": {
            "question": "How many chairs?", "options": ["A. 1", "B. 2"], "frames": frames,
            "frame_indices": list(range(0, 640, 10)), "timestamps": [k / 10 for k in range(0, 640, 10)], "fps": 10.0,
            "total_num_frames": 700}}
        batch, audit = pose_samples.encode_row(processor, row, {"count": 64, "pixels_per_frame": [16384, 73728]})
        self.assertEqual(audit["frame_count"], 64)
        self.assertEqual(audit["video_grid_thw"][0][0], 32)
        self.assertEqual(audit["processed_height_width"], [224, 288])


@unittest.skipUnless(BASE_X.is_file(), "needs the pinned RG2P2_X config")
class ArmConfigTests(unittest.TestCase):
    def test_arms_carry_the_cited_recipes(self):
        from tools import fullft_arm_configs as arms
        base_x = arms.load_base(BASE_X, "X")
        base_a = arms.a_from_x(BASE_X.read_bytes())
        store = ("STORE/manifest.jsonl", "0" * 64)
        configs, pending = arms.arm_configs(base_a, base_x, ("/bank.npz", "1" * 64), {"stage1": store, "stage2": store})
        self.assertEqual(pending, ["PDG_S2", "GXS_S2", "GXS_X_S2"])
        cpd, s1, s2, control = configs["CPD"], configs["PDG_S1"], configs["PDG_S2"], configs["FT_A"]
        for config in configs.values():
            self.assertEqual((config["effective_batch_size"], config["epochs"], config["warmup_ratio"], config["weight_decay"]),
                             (256, 1, 0.03, 0.0))
            self.assertEqual(config["frames"], arms.FRAMES)
            self.assertNotIn("init_adapter", config)
        self.assertEqual(cpd["full_ft"]["learning_rates"], {"llm": 1e-5, "merger": 1e-5, "vision_blocks": 2e-6, "heads": 1e-4})
        self.assertEqual(cpd["camera"]["head_only_steps"], 51)
        from student_pilot import camera_config
        self.assertEqual(cpd["camera"]["row_routing"], camera_config.CAMBRIAN_P_ROUTING)
        self.assertNotIn("row_routing", s2["camera"])
        self.assertNotIn("row_routing", s1["camera"])
        self.assertEqual((cpd["camera"]["embed_dim"], cpd["camera"]["num_heads"], cpd["camera"]["trajectory_balance"]),
                         (2048, 16, False))
        self.assertEqual(s1["full_ft"]["train"], {"llm": False})
        self.assertEqual(s1["geometry"]["injection"], geometry_input.SPATIAL_INJECTION)
        self.assertEqual(s2["full_ft"]["learning_rates"]["geometry"], 1e-5)
        self.assertEqual({k: v for k, v in s2["full_ft"]["learning_rates"].items() if k != "geometry"},
                         {**control["full_ft"]["learning_rates"], "heads": 1e-4})
        self.assertNotIn("geometry", control)
        self.assertNotIn("camera", control)
        self.assertEqual(control["loss_reduction"], s2["loss_reduction"])
        self.assertEqual(configs["GXS_S2"]["full_ft"]["train"], {"llm": True, "vision_blocks": False, "merger": False})
        smokes = arms.smoke_configs(configs)
        self.assertEqual(set(smokes), {"SMOKE_CPD", "SMOKE_PDG_S1", "SMOKE_PDG_S2", "SMOKE_FT_A"})
        self.assertTrue(all(c["world_size"] == 8 and c["effective_batch_size"] == 64 for c in smokes.values()))


BANK = Path("/scratch/jjyeung/fullft/inputs/label_bank_1247_v2.npz")
POSE_ROWS = Path("/scratch/jjyeung/fullft/pose_rows_v1/pose_rows.jsonl")


@unittest.skipUnless(BANK.is_file() and POSE_ROWS.is_file(), "needs the label bank and the built pose rows")
class BankLoaderTests(unittest.TestCase):
    def test_pose_rows_use_their_inline_targets_and_question_rows_keep_the_bank(self):
        import json
        from student_pilot import camera_config
        from student_pilot.compact_label_bank import load_bank_for_rows
        with POSE_ROWS.open() as handle:
            pose = [json.loads(next(handle)) for _ in range(3)]
        cfg = camera_config.normalize({"weight": 1.0, "supervision": {"path": str(BANK), "sha256": "0" * 64},
                                       "point_depth": {"weight": 0.5}})
        records, audit = load_bank_for_rows(BANK, pose + [{"qid": "x", "dataset": "d9", "scene": "v0"}], cfg)
        self.assertEqual(audit["pose_only_samples"], 3)
        self.assertEqual(audit["scene_not_in_bank"], 1)
        for row, record in zip(pose, records):
            self.assertEqual(record["camera"], row["pose_sample"]["camera"])
            self.assertEqual(record["lm_weight"], 0.0)
            self.assertFalse(any(any(line) for line in record["point_depth"]["mask"]))


class CambrianRoutingTests(unittest.TestCase):
    """CPD (Cambrian-P): question rows train the next-token loss only; pose-only rows train the heads, with depth
    queries from the bank at their frames."""

    def test_routing_is_optional_and_checked(self):
        from student_pilot import camera_config
        base = {"weight": 1.0, "supervision": PIN}
        self.assertNotIn("row_routing", camera_config.normalize(base))
        routed = camera_config.normalize({**base, "row_routing": camera_config.CAMBRIAN_P_ROUTING})
        self.assertEqual(routed["row_routing"], camera_config.CAMBRIAN_P_ROUTING)
        self.assertEqual({k: v for k, v in routed.items() if k != "row_routing"}, camera_config.normalize(base))
        with self.assertRaises(ValueError):
            camera_config.normalize({**base, "row_routing": "all_rows"})

    def test_question_rows_keep_their_encoding(self):
        from tests.pd_toys import video_row
        from tests.auxiliary_toys import ToyTokenizer
        tokenizer = ToyTokenizer()
        _, batch = video_row(tokenizer)
        zero = {"camera": np.zeros((16, 9)).tolist(), "camera_mask": [False] * 16, "trajectory_scale": 0.0,
                "lm_weight": 1.0, "gravity": [0.0, 0.0, 0.0], "gravity_mask": False,
                "point_depth": {"uv": np.zeros((16, 8, 2)).tolist(), "depth": np.zeros((16, 8)).tolist(),
                                "mask": np.zeros((16, 8), bool).tolist()}}
        result = camera_targets.insert_tokens(batch, zero, tokenizer)
        self.assertTrue(torch.equal(result["input_ids"], batch["input_ids"]))
        self.assertEqual(result["aux_camera_positions"].tolist(), [[-1] * 16])
        self.assertEqual(float(result["aux_lm_weight"][0]), 1.0)

    def test_depth_runs_on_a_sample_with_fewer_groups(self):
        from student_pilot.auxiliary_targets import add_to_batch
        from tests.pd_toys import video_row
        from tests.test_pd_build2 import record, toy_heads
        tokenizer, model, heads = toy_heads()
        row, batch = video_row(tokenizer, groups=4)
        rec = record(0)
        rec["camera_mask"] = [g < 4 for g in range(16)]
        rec["point_depth"]["mask"] = [[g < 4] * 8 for g in range(16)]
        encoded = ddp_core.collate_rows([add_to_batch(batch, {**row, "_camera": rec}, tokenizer)], 0)
        losses = ddp_core.row_losses(model, encoded)
        depth = heads.camera.last_components["point_depth"]
        self.assertTrue(bool(torch.isfinite(losses).all()) and float(depth[0]) > 0)
        losses.sum().backward()
        self.assertTrue(any(p.grad is not None and float(p.grad.abs().sum()) > 0 for p in heads.camera.point_depth.parameters()))
        # A question row without heads (Cambrian-P routing) and the 4-group pose sample share one micro-batch.
        question, question_batch = video_row(tokenizer, qid="q", seed=1)
        zero = {"camera": np.zeros((16, 9)).tolist(), "camera_mask": [False] * 16, "trajectory_scale": 0.0, "lm_weight": 1.0,
                "gravity": [0.0, 0.0, 0.0], "gravity_mask": False,
                "point_depth": {"uv": np.zeros((16, 8, 2)).tolist(), "depth": np.zeros((16, 8)).tolist(),
                                "mask": np.zeros((16, 8), bool).tolist()}}
        mixed = ddp_core.collate_rows([add_to_batch(question_batch, {**question, "_camera": zero}, tokenizer),
                                       add_to_batch(batch, {**row, "_camera": rec}, tokenizer)], 0)
        both = ddp_core.row_losses(model, mixed)
        self.assertTrue(torch.allclose(both[1], losses[0], atol=1e-5))
        self.assertEqual(float(heads.camera.last_components["point_depth"][0]), 0.0)
        rec["point_depth"]["mask"][5] = [True] * 8
        encoded = ddp_core.collate_rows([add_to_batch(batch, {**row, "_camera": rec}, tokenizer)], 0)
        with self.assertRaisesRegex(ValueError, "beyond the row's temporal groups"):
            ddp_core.row_losses(model, encoded)

    @unittest.skipUnless(BANK.is_file() and POSE_ROWS.is_file(), "needs the label bank and the built pose rows")
    def test_bank_routing_on_the_built_rows(self):
        import json
        from student_pilot import camera_config
        from student_pilot.compact_label_bank import load_bank_for_rows, read_bank
        bank = read_bank(BANK)
        lookup = {key: i for i, key in enumerate(zip(bank["dataset_tokens"].tolist(), bank["scene_tokens"].tolist()))}
        with POSE_ROWS.open() as handle:
            pose = [json.loads(next(handle)) for _ in range(200)]
        questions = []
        for row in pose[::28]:
            index = lookup[(row["dataset"], row["scene"])]
            questions.append({"qid": "q" + row["qid"], "dataset": row["dataset"], "scene": row["scene"], "category": "count",
                              "student_input": {"frame_indices": [int(v) for v in bank["frame_indices"][index]]}})
        base = {"weight": 1.0, "supervision": {"path": str(BANK), "sha256": "0" * 64}, "point_depth": {"weight": 0.5}}
        plain, _ = load_bank_for_rows(BANK, questions, camera_config.normalize(base))
        self.assertTrue(all(any(record["camera_mask"]) for record in plain))  # the PD design: labelled rows train heads
        cfg = camera_config.normalize({**base, "row_routing": camera_config.CAMBRIAN_P_ROUTING})
        records, audit = load_bank_for_rows(BANK, questions + pose, cfg)
        self.assertEqual(audit["question_rows_lm_only"], len(questions))
        for record in records[:len(questions)]:
            self.assertFalse(any(record["camera_mask"]) or record["gravity_mask"]
                             or np.asarray(record["point_depth"]["mask"]).any())
            self.assertEqual(record["lm_weight"], 1.0)
        labelled = 0
        for row, record in zip(pose, records[len(questions):]):
            self.assertEqual(record["camera"], row["pose_sample"]["camera"])
            self.assertEqual(record["lm_weight"], 0.0)
            index, positions = lookup[(row["dataset"], row["scene"])], row["pose_sample"]["positions"]
            mask = np.asarray(record["point_depth"]["mask"])
            for group in range(16):
                position = positions[2 * group + 1] if group < len(positions) // 2 else None
                if position is not None and position % 2:
                    expected = bank["point_depth_mask"][index, position // 2, :mask.shape[1]]
                    self.assertTrue(np.array_equal(mask[group], expected))
                    self.assertEqual(record["point_depth"]["depth"][group],
                                     bank["point_depth_gt"][index, position // 2, :mask.shape[1]].astype(np.float32).tolist())
                    labelled += bool(expected.any())
                else:
                    self.assertFalse(mask[group].any())
        self.assertEqual(audit["pose_depth_groups"], labelled)
        self.assertGreater(labelled, 0)


class Stage1DevMetricTests(unittest.TestCase):
    def test_errors_and_the_growth_rule(self):
        from tools import stage1_dev_metrics as metrics
        rows = [{"qid": f"q{i}", "category": c, "answer": a} for i, (c, a) in enumerate(
            [("depth_at_pixel", "1.50"), ("nearer_pixel", "B"), ("camera_position_vs_frame1", "(1.00, 2.00, 0.00)"),
             ("camera_heading_vs_frame1", "-170.00")] * 10)]
        perfect = [{"qid": r["qid"], "prediction": "<think>\n\n</think>\n\n" + r["answer"]} for r in rows]
        self.assertEqual(metrics.aggregate(metrics.errors(rows, perfect))[0], 0.0)
        self.assertEqual(metrics.item_error("-170.00", "175.0", "camera_heading_vs_frame1"),
                         1.0 - metrics.mra(15.0, 170.0))
        self.assertEqual(metrics.item_error("1.50", "no number"), 1.0)
        empty = [{"qid": r["qid"], "prediction": ""} for r in rows]
        self.assertEqual(metrics.decide(rows, empty, perfect, reps=100)["decision"], "GROW")
        self.assertEqual(metrics.decide(rows, perfect, perfect, reps=100)["decision"], "STOP")
