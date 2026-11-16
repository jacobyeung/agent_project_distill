"""The patch-grid G3T store tool: roi pooling onto the unmerged patch grid, the selection lists and the sealed manifest
that the trainer's and evaluator's FeatureStore read."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from student_pilot import geometry_input
from tools import fullft_arm_configs as arms
from tools import g3t_patch_grid_store as tool


def output_root():
    return Path(tempfile.mkdtemp(prefix="g3t_store_", dir=os.environ.get("LANE_TEST_OUTPUT") or None))


def frame_shas(video):
    return [hashlib.sha256(f"video{video}:frame{index}".encode()).hexdigest() for index in range(32)]


class PoolingTests(unittest.TestCase):
    def ramp(self, side=37, channels=3):
        """Feature map linear in the 518-px pixel position of each patch centre: channel c = c + 0.01 x + 0.02 y."""
        centres = (torch.arange(side, dtype=torch.float64) + 0.5) * tool.PATCH
        y, x = torch.meshgrid(centres, centres, indexing="ij")
        grid = torch.stack([c + 0.01 * x + 0.02 * y for c in range(channels)], dim=-1)
        return grid.reshape(1, side * side, channels).expand(32, -1, -1).float(), lambda px, py: [c + 0.01 * px + 0.02 * py
                                                                                                    for c in range(channels)]

    def test_cells_sit_on_the_student_patch_grid_inside_the_valid_region(self):
        tokens, value = self.ramp()
        coords = torch.tensor([[100.0, 150.0, 900.0, 850.0, 1024, 1024]] * 32)  # valid region in the 1024-px square
        pooled = tool.pool_patch_grid(tokens, coords, (16, 8, 10))
        self.assertEqual(tuple(pooled.shape), (32, 8, 10, 3))
        x1, y1, x2, y2 = (float(v) * 518 / 1024 for v in coords[0, :4])
        for i, j in ((0, 0), (3, 7), (7, 9)):
            centre = (x1 + (j + 0.5) * (x2 - x1) / 10, y1 + (i + 0.5) * (y2 - y1) / 8)
            self.assertTrue(np.allclose(pooled[5, i, j].numpy(), value(*centre), atol=1e-4))
        # The merged-grid extractor's cells are the 2x2 means of these cells (exact for a linear field).
        from torchvision.ops import roi_align
        grid = tokens.reshape(32, 37, 37, 3).permute(0, 3, 1, 2)
        boxes = torch.cat((torch.arange(32.0)[:, None], coords[:, :4] * 518 / 1024), 1)
        merged = roi_align(grid, boxes, output_size=(4, 5), spatial_scale=1 / 14, sampling_ratio=2, aligned=True).permute(0, 2, 3, 1)
        means = pooled.reshape(32, 4, 2, 5, 2, 3).mean(dim=(2, 4))
        self.assertTrue(torch.allclose(means, merged, atol=1e-4))

    def test_grids_must_be_32_frame_and_mergeable(self):
        tokens, _ = self.ramp()
        for grid in ((15, 8, 10), (16, 7, 10), (16, 8, 9)):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                tool.pool_patch_grid(tokens, torch.zeros(32, 6), grid)
        with self.assertRaisesRegex(ValueError, "patch-token shape"):
            tool.pool_patch_grid(tokens[:, :1000], torch.zeros(32, 6), (16, 8, 10))
        self.assertEqual(tool.ENCODER, arms.G3T_ENCODER)
        self.assertEqual(tool.store_bytes((16, 20, 26)), 32 * 20 * 26 * 2048 * 2 + 128)  # 68.2 MB at 320 x 416


class ListsAndSealTests(unittest.TestCase):
    def setUp(self):
        self.root = output_root()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return str(path)

    def fixture(self):
        rows, audits = [], []
        for index, video in enumerate((0, 0, 1)):
            frames = [{"path": f"/remote/frames/{video}/{k}.png", "sha256": sha} for k, sha in enumerate(frame_shas(video))]
            rows.append({"qid": f"q{index}", "student_input": {"frames": frames}})
            audits.append({"qid": f"q{index}", "video_grid_thw": [[16, 4, 6]]})
        training = self.write("training.json", {"rows": rows, "input_audits": audits})
        receipt = self.write("eval/receipt.json", {"frames": [{"png": {"sha256": sha, "path": f"/remote/eval/{k}.png"}}
                                                              for k, sha in enumerate(frame_shas(7))]})
        media = self.write("eval/media.json", {"v7": {"frame_receipt": {"path": receipt}}})
        manifest = self.write("eval/manifest.json", {"media": {"path": media}})
        cell = self.root / "cell"
        self.write("cell/preflight/preflight.json", {"manifest": {"path": manifest}})
        (cell / "preflight/input_audits.jsonl").write_text("".join(
            json.dumps({"qid": f"e{k}", "frame_hashes": frame_shas(7), "video_grid_thw": [[16, 4, 6]]}) + "\n" for k in range(2)))
        return training, cell

    def store_rows(self, sets, store, shape=(32, 4, 6, 2048)):
        rng = np.random.default_rng(0)
        with (store / "m_0.jsonl").open("w") as stream:
            for entry in sets:
                relative = Path("f") / entry["key"][:2] / f"{entry['key']}.npy"
                (store / relative).parent.mkdir(parents=True, exist_ok=True)
                np.save(store / relative, rng.standard_normal(shape).astype(np.float16), allow_pickle=False)
                stream.write(json.dumps({"key": entry["key"], "frames": entry["frames"], "file": str(relative),
                                         "sha256": tool.sha(store / relative), "shape": list(shape), "dtype": "float16",
                                         "layer": tool.LAYER, "encoder": tool.ENCODER}) + "\n")

    def test_lists_seal_and_the_trainer_store_reads_the_result(self):
        training, cell = self.fixture()
        report = tool.build_lists([("RG2P2_A", training)], [("vsi", str(cell))], [], self.root / "lists")
        self.assertEqual((report["train"]["selections"], report["eval"]["selections"]), (2, 1))
        train = [json.loads(line) for line in (self.root / "lists/train_sets.jsonl").read_text().splitlines()]
        self.assertEqual(sorted(entry["rows"]["RG2P2_A"] for entry in train), [1, 2])
        evaluation = [json.loads(line) for line in (self.root / "lists/eval_sets.jsonl").read_text().splitlines()]
        self.assertEqual((evaluation[0]["items"], evaluation[0]["video_id"]), (2, "v7"))
        store = self.root / "store"
        store.mkdir()
        self.store_rows(train, store)
        receipt = tool.seal(self.root / "lists/train_sets.jsonl", store)
        self.assertEqual(receipt["selections"], 2)
        self.assertEqual(receipt["manifest"]["sha256"], tool.sha(store / "manifest.jsonl"))
        settings = arms.geometry_block(str(store / "manifest.jsonl"), receipt["manifest"]["sha256"])
        features = geometry_input.FeatureStore(settings)
        tokens = features.tokens(train[0]["frames"], (16, 4, 6))
        self.assertEqual(tuple(tokens.shape), (16 * 2 * 3, 8 * 2048))
        self.assertEqual(geometry_input.store_grid(settings, (16, 4, 6)), (4, 6))

    def test_seal_refuses_missing_foreign_or_misshapen_rows(self):
        training, cell = self.fixture()
        tool.build_lists([("RG2P2_A", training)], [], [], self.root / "lists")
        train = [json.loads(line) for line in (self.root / "lists/train_sets.jsonl").read_text().splitlines()]
        for name, rows, shape in (("missing", train[:1], (32, 4, 6, 2048)), ("merged_grid", train, (32, 2, 3, 2048))):
            with self.subTest(name=name):
                store = self.root / name
                store.mkdir()
                self.store_rows(rows, store, shape)
                with self.assertRaises(ValueError):
                    tool.seal(self.root / "lists/train_sets.jsonl", store)
                self.assertFalse((store / "manifest.jsonl").exists())
        with self.assertRaisesRegex(ValueError, "both the training and the eval"):
            tool.build_lists([("A", training)], [("leak", str(self.leak()))], [], self.root / "overlap")

    def leak(self):
        """An eval cell whose items show a training selection (video 0)."""
        receipt = self.write("leak/receipt.json", {"frames": [{"png": {"sha256": sha, "path": f"/x/{k}.png"}}
                                                              for k, sha in enumerate(frame_shas(0))]})
        media = self.write("leak/media.json", {"v0": {"frame_receipt": {"path": receipt}}})
        manifest = self.write("leak/manifest.json", {"media": {"path": media}})
        self.write("leakcell/preflight/preflight.json", {"manifest": {"path": manifest}})
        (self.root / "leakcell/preflight/input_audits.jsonl").write_text(
            json.dumps({"qid": "e", "frame_hashes": frame_shas(0), "video_grid_thw": [[16, 4, 6]]}) + "\n")
        return self.root / "leakcell"


if __name__ == "__main__":
    unittest.main()
