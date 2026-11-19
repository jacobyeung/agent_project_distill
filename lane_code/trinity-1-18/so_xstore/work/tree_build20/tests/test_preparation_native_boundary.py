"""Native dependency/format evidence and CPU-entry tests, not an adoption proof."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from student_pilot import mdg_parent, preparation_cpu
from student_pilot.p3_provenance import file_pin, load, write
from student_pilot.preparation_reads import Recorder, UnkeyedRead
from student_pilot.s1_admission import FrameAudit


class NativeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="native_boundary_", dir=os.environ["LANE_TEST_OUTPUT"]))
        env = patch.dict(os.environ, {"TK_XSTORE_EXPERIMENT": "1", "TK_NATIVE_CPU_PREPARE": "1",
                         "CUDA_VISIBLE_DEVICES": "", "C1_INIT_LOCAL": "", "STUDENT_FRAME_ROOT_MAP": "",
                         "SLURM_GPUS_ON_NODE": "", "SLURM_GPUS": "", "SLURM_JOB_GPUS": "",
                         "SLURM_GPUS_PER_NODE": ""})
        env.start()
        self.addCleanup(env.stop)

    def put(self, name, value):
        path = self.root / name
        write(path, value)
        return file_pin(path)

    def parent(self):
        architecture = self.put("model/config.json", {"text_config": {"hidden_size": 4}})
        base = self.put("base.json", {"root": str(self.root / "model"), "base_identity": "tiny",
                        "files": {"config.json": architecture["sha256"]}})
        pose = self.put("pose.json", {"model": base})
        index = self.put("weights/model.safetensors.index.json",
                         {"weight_map": {"model.embed_tokens.weight": "missing-shard.safetensors"}})
        weights = self.put("weights/manifest.json", {"schema": run.full_ft.EXPORT_SCHEMA,
                           "index": {"name": "model.safetensors.index.json", "sha256": index["sha256"]},
                           "files": [{"name": "missing-shard.safetensors", "sha256": "a" * 64, "bytes": 8}]})
        parent = self.put("artifact.json", {"schema": "carrier-c1-artifact-v1", "base_identity": "tiny",
                          "full_weights": weights, "heads": {"path": "/not-read/heads.json", "sha256": "b" * 64}})
        cfg = {"streams": {"pose": pose}, "base_identity": "tiny", "init_artifact": {"lm": "full", "artifact": parent}}
        return cfg

    def test_no_mdg_native_parent_still_requires_export_artifact(self):
        cfg = self.parent()
        cfg["init_artifact"]["artifact"] = {"path": str(self.root / "future-step-600.json"), "sha256": "c" * 64}
        with self.assertRaisesRegex(ValueError, "Missing or changed pinned input"):
            mdg_parent.bind(cfg, self.root / "out")

    def test_no_mdg_native_parent_still_requires_export_manifest(self):
        cfg = self.parent()
        (self.root / "weights/manifest.json").rename(self.root / "retained-manifest.json")
        with self.assertRaisesRegex(ValueError, "Missing or changed pinned input"):
            mdg_parent.bind(cfg, self.root / "out")

    def test_no_mdg_native_parent_still_requires_export_index(self):
        cfg = self.parent()
        (self.root / "weights/model.safetensors.index.json").rename(self.root / "retained-index.json")
        with self.assertRaisesRegex(ValueError, "Missing or changed pinned input"):
            mdg_parent.bind(cfg, self.root / "out")

    def test_no_mdg_native_parent_reads_metadata_without_weight_payload(self):
        cfg = self.parent()
        with patch.object(torch.cuda, "_lazy_init", side_effect=AssertionError("CUDA initialization forbidden")):
            proof = mdg_parent.bind(cfg, self.root / "out")
        self.assertEqual(proof["mdg"], "absent")
        self.assertFalse(proof["parent_weight_payloads_verified"])
        self.assertFalse((self.root / "weights/missing-shard.safetensors").exists())

    def test_native_identity_changes_with_output_and_preparation_output(self):
        cfg = {"output": "/run/a", "preparation_output": "/run/a/prep", "seed": 17}
        baseline = run.identity(cfg)
        for key in ("output", "preparation_output"):
            value = {**cfg, key: "/run/b"}
            self.assertNotEqual(baseline, run.identity(value))

    def test_actual_native_identity_refuses_excluded_reads_under_recorder(self):
        cfg = Recorder({"output": "/run/a", "preparation_output": "/run/a/prep", "seed": 17})
        with self.assertRaisesRegex(UnkeyedRead, "Run-specific"):
            run.identity(cfg.config)

    def test_native_frame_audit_contains_physical_paths_and_differs_between_dirs(self):
        outputs = []
        for name in ("a", "b"):
            root = self.root / name
            root.mkdir()
            frame = root / "frame.bin"
            frame.write_bytes(b"same frame")
            output = root / "audit"
            output.mkdir()
            audit = FrameAudit(output, [root], sample_size=1)
            try:
                audit.keep({"student_input": {"frames": [file_pin(frame)]}}, "vqa")
                outputs.append(audit.finish())
            finally:
                audit.close()
        self.assertNotEqual(outputs[0]["inventory"]["sha256"], outputs[1]["inventory"]["sha256"])
        self.assertNotEqual(outputs[0]["roots"], outputs[1]["roots"])

    def test_cpu_entry_defaults_off_and_rejects_allocated_gpus(self):
        with patch.dict(os.environ, {"TK_NATIVE_CPU_PREPARE": "0"}):
            with self.assertRaisesRegex(ValueError, "TK_NATIVE_CPU_PREPARE"):
                preparation_cpu.resources(8, 30, 60)
        for name in ("SLURM_GPUS_ON_NODE", "SLURM_GPUS", "SLURM_JOB_GPUS", "SLURM_GPUS_PER_NODE"):
            with patch.dict(os.environ, {name: "4"}):
                with self.assertRaisesRegex(ValueError, "GPU allocation"):
                    preparation_cpu.resources(8, 30, 60)

    def test_cpu_entry_forwards_exact_native_arguments_and_separates_telemetry(self):
        from student_pilot import s1_admission
        pin = self.put("config.json", {"output": "native-output"})
        out = self.root / "native"
        result = {"schema": "test-native-return", "status": "PREPARED"}
        def native(config, output, roots, **kwargs):
            self.assertEqual(config, pin)
            self.assertEqual(roots, [str(self.root)])
            self.assertTrue(kwargs["prepare_only"])
            self.assertEqual(kwargs["threads"], 8)
            self.assertEqual(kwargs["memory_gib"], 30)
            write(output / "data_receipt.json", result)
            return result
        # This spy tests forwarding, not a native end-to-end preparation proof.
        with patch.object(s1_admission, "admit", side_effect=native) as called:
            got = preparation_cpu.prepare(pin["path"], pin["sha256"], out, [str(self.root)], max_seconds=60)
        called.assert_called_once()
        self.assertEqual(got, result)
        self.assertEqual(load(out / "data_receipt.json"), result)
        telemetry = load(next(out.glob("cpu_telemetry_*.json")))
        self.assertFalse(telemetry["cross_run_adoptable"])
        self.assertFalse(telemetry["store_published"])
        self.assertEqual(telemetry["status"], "PREPARED")

    def test_cpu_entry_keeps_native_failure_and_partial_journal(self):
        from student_pilot import s1_admission
        pin = self.put("config.json", {})
        out = self.root / "partial"
        out.mkdir()
        marker = out / "phase_prepare.complete.json"
        marker.write_bytes(b"existing native journal")
        with patch.object(s1_admission, "admit", side_effect=ValueError("native refusal")):
            with self.assertRaisesRegex(ValueError, "native refusal"):
                preparation_cpu.prepare(pin["path"], pin["sha256"], out, [str(self.root)], resume=True)
        self.assertEqual(marker.read_bytes(), b"existing native journal")
        self.assertEqual(load(next(out.glob("cpu_telemetry_*.json")))["status"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
