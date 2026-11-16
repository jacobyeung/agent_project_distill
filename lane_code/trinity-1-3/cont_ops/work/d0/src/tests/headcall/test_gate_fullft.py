"""The gate on a full fine-tuning checkpoint: a milestone export (CPD's init layout, ddp_checkpoints.save_milestone_export)
loads exactly (BF16 full weights over the base, heads strict), and its heads answer held-out probe rows' calls through
the trainer's prompt encoder and carriers."""
import hashlib
import json
import os
import tempfile
import unittest
from unittest import mock

from common import CACHE, TINY  # noqa: F401  (puts the tree on the path)
from headcall import gate_eval, phase1
from rows_fixture import direction_row, distance_row

STUDENT = "qwen35"


def tiny_camera_model(seed):
    """The tiny Qwen3.5 asset (4-block ViT) in BF16 with the trainer's camera, gravity, scale and point-depth heads."""
    import torch
    from transformers import AutoConfig, AutoModelForImageTextToText, AutoTokenizer
    config = AutoConfig.from_pretrained(TINY)
    config.vision_config.depth = 4
    torch.manual_seed(seed)
    model = AutoModelForImageTextToText.from_config(config).to(torch.bfloat16).eval()
    model.requires_grad_(False)
    settings = phase1._module("camera_config").normalize({
        "weight": 1.0, "weight_gravity": 0.5, "weight_scale": 0.2, "embed_dim": 16, "num_heads": 2, "trunk_depth": 2,
        "refine_iterations": 2, "supervision": {"path": "/fixture/bank.npz", "sha256": "0" * 64},
        "point_depth": {"weight": 0.5, "d_proj": 16, "mlp_hidden": 16, "num_heads": 2, "context_depth": 1,
                        "vit_layers": [1, 2, 4], "num_points_per_frame": 8}})
    return model, settings, AutoTokenizer.from_pretrained(TINY)


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def write_milestone(root, step=20):
    """milestone_<step>/ in save_milestone_export's layout: full_weights/ (BF16 export), auxiliary_heads.pt/.json and
    MILESTONE.json pinning every file. Returns (directory, trained model, heads state)."""
    import torch
    full_ft = phase1._module("full_ft")
    attach = phase1.auxiliary_losses().attach
    model, settings, tokenizer = tiny_camera_model(seed=3)
    heads = attach(model, None, tokenizer, settings)
    with torch.no_grad():
        heads.camera.tokens.normal_(0.0, 0.5)
        heads.camera.head.pose_branch.fc2.bias[7:9] += 1.0
    directory = os.path.join(root, "milestone_%d" % step)
    os.makedirs(directory)
    names = [name for name, _ in full_ft.base_parameters(model)]
    state = {name: parameter.detach() for name, parameter in model.named_parameters()}
    with mock.patch.object(full_ft, "EXPORT_SHARD_BYTES", 16 * 1024 ** 2):
        export = full_ft.save_export(full_ft.export_tensors(state, names), os.path.join(directory, full_ft.EXPORT_DIRECTORY),
                                     {"student": STUDENT, "base": {"fixture": True}, "base_sha256": "b" * 64},
                                     {"mode": "full"})
    heads_state = {name: value.detach().cpu() for name, value in heads.state_dict().items()}
    torch.save(heads_state, os.path.join(directory, "auxiliary_heads.pt"))
    with open(os.path.join(directory, "auxiliary_heads.json"), "w") as handle:
        json.dump(heads.manifest(), handle, sort_keys=True)
    files = {}
    for name in [item["name"] for item in export["files"]] + [export["index"]["name"], full_ft.EXPORT_MANIFEST]:
        path = os.path.join(directory, full_ft.EXPORT_DIRECTORY, name)
        files["%s/%s" % (full_ft.EXPORT_DIRECTORY, name)] = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
    for name in ("auxiliary_heads.pt", "auxiliary_heads.json"):
        path = os.path.join(directory, name)
        files[name] = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
    with open(os.path.join(directory, "MILESTONE.json"), "w") as handle:
        json.dump({"schema": "full-ft-milestone-export-v1", "step": step, "identity": {"fixture": True}, "files": files},
                  handle, sort_keys=True)
    return directory, model, heads_state


def frames(root):
    import numpy
    from PIL import Image
    rng = numpy.random.RandomState(7)
    result = []
    for k in range(32):
        path = os.path.join(root, "f%02d.png" % k)
        Image.fromarray((rng.rand(64, 64, 3) * 255).astype(numpy.uint8), "RGB").save(path)
        result.append({"path": path, "sha256": sha256(path)})
    return result


def probe_rows(root, scene):
    student_input = {"question": "How far apart are the chair and the lamp, in meters?", "options": [],
                     "frames": frames(root), "frame_indices": list(range(0, 64, 2)),
                     "timestamps": [i / 2.0 for i in range(0, 64, 2)], "fps": 2.0, "total_num_frames": 64}
    rows = []
    for make in (distance_row, direction_row):
        row = make(qid="p_" + make.__name__)
        row["dataset"], row["scene"] = scene
        row["student_input"] = dict(student_input)
        rows.append(row)
    return rows


class FullFTGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        os.makedirs(CACHE, exist_ok=True)
        cls.root = tempfile.mkdtemp(prefix="gate_fullft_", dir=CACHE)
        cls.directory, cls.trained, cls.heads_state = write_milestone(cls.root)
        processor = AutoProcessor.from_pretrained(TINY)
        processor.tokenizer.padding_side = "right"
        cls.processor = processor
        fresh, _, _ = tiny_camera_model(seed=11)  # the "pinned base": other values, replaced by the export
        with mock.patch.object(phase1._module("runner"), "load_base", return_value=fresh), \
                mock.patch.object(phase1._module("batches"), "load_processor", return_value=processor):
            full_weights, heads_json, heads_pt, cls.milestone = gate_eval.milestone_paths(cls.directory)
            cls.backend = gate_eval.FullFTCheckpointHeads(STUDENT, full_weights, heads_json, heads_pt, device="cpu")

    def test_milestone_loads_exactly(self):
        import torch
        full_ft = phase1._module("full_ft")
        live = dict(full_ft.base_parameters(self.backend.model))
        for name, parameter in full_ft.base_parameters(self.trained):
            self.assertTrue(torch.equal(live[name], parameter), name)
        loaded = self.backend.model.auxiliary_heads.state_dict()
        self.assertEqual(set(loaded), set(self.heads_state))
        self.assertTrue(all(torch.equal(loaded[name].cpu(), value) for name, value in self.heads_state.items()))
        self.assertTrue(self.backend.load_report["full_weights"]["full_weights_exact_equality"])
        self.assertEqual(self.milestone["step"], 20)
        self.assertEqual(self.backend.load_report["heads_sha256"], self.milestone["pins"]["heads"]["sha256"])

    def test_heads_answer_probe_rows(self):
        import numpy
        scene = phase1.heldout_scenes()[0]
        rows = probe_rows(tempfile.mkdtemp(prefix="frames_", dir=self.root), scene)
        report = gate_eval.evaluate(rows, self.backend.heads, phase1.heldout_scenes(), [])
        self.assertEqual(len(report["per_row"]), len(rows))
        self.assertIn("call_refusals", report["checks"])
        self.assertGreater(report["summary"]["depth_points"], 0)  # the depth head answered the probe points
        # The session is the checkpoint's own: the heads on the encoded prompt with carriers, one forward.
        encode_prompt = phase1._module("diagnostic_data").encode_prompt
        batch = phase1.insert_carriers(encode_prompt(self.processor, rows[0])[0], self.processor.tokenizer)
        reference = phase1.head_api().HeadSession.from_forward(self.backend.model, batch)
        self.backend.heads.begin(gate_eval.HeadContext([], key=rows[0]["qid"], row=rows[0]))
        numpy.testing.assert_allclose(self.backend.heads.session.raw_pose, reference.raw_pose, atol=1e-6)

    def test_tampered_milestone_and_cli_refusals(self):
        import shutil
        copy = os.path.join(self.root, "tampered")
        shutil.copytree(self.directory, copy)
        with open(os.path.join(copy, "auxiliary_heads.json"), "a") as handle:
            handle.write(" ")
        with self.assertRaises(ValueError):
            gate_eval.milestone_paths(copy)
        common = ["--rows", self.root, "--training-scenes", "unused.json", "--out", os.path.join(self.root, "never.json"),
                  "--student", STUDENT]
        for extra in (["--milestone", self.directory, "--heads-json", "h.json"],
                      ["--milestone", self.directory, "--full-weights", "w"],
                      ["--full-weights", "w"]):
            with self.subTest(extra=extra), self.assertRaises(SystemExit), mock.patch("sys.stderr"):
                gate_eval.main(common + extra)


if __name__ == "__main__":
    unittest.main()
