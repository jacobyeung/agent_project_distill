import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from student_pilot import storage
from student_pilot.common import ARTIFACTS, binding, digest_json, load_json


class StorageTests(unittest.TestCase):
    def setUp(self):
        root = ARTIFACTS / "trainer_tests"
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="storage_", dir=root))
        self.scratch = self.root / "scratch"
        self.publish = self.root / "publish"
        self.scratch.mkdir()
        self.publish.mkdir()
        self.config = {"student": "onethinker", "infrastructure_only": True, "purpose": "synthetic CPU storage fixture"}
        self.real_provenance = storage.code_provenance
        self.patches = [patch.object(storage, "SCRATCH_HOME", self.scratch),
                        patch.object(storage, "PUBLISH_HOME", self.publish),
                        patch.object(storage, "code_provenance", side_effect=lambda config: {
                            "commit": "a" * 40, "dirty": False, "config_sha256": digest_json(config)}),
                        patch.object(storage.shutil, "disk_usage", return_value=SimpleNamespace(free=2**50))]
        for item in self.patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in reversed(self.patches)])

    def run_fixture(self, name="train"):
        store = storage.RunArtifacts(self.scratch / name, self.config, self.scratch)
        adapter = store.root / "adapter"
        adapter.mkdir()
        (adapter / "adapter_model.safetensors").write_bytes(b"synthetic CPU fixture, not model weights")
        (adapter / "adapter_config.json").write_text('{"peft_type": "LORA"}')
        store.write("adapter/provenance.json", {"infrastructure_only": True})
        for step in range(1, 5):
            store.write(f"steps/{step:04d}.json", {"step": step})
        store.write("training_result.json", {
            "schema": "student-infrastructure-training-v1", "student": "onethinker", "status": "TRAINED",
            "realized": {"optimizer_steps": 4},
            "adapter": {"weights": binding(adapter / "adapter_model.safetensors"), "config": binding(adapter / "adapter_config.json")},
        })
        store.write("run.json", {"student": "onethinker"})
        return store

    def evaluation_fixture(self, training):
        store = storage.RunArtifacts(self.scratch / "evaluate", self.config, self.scratch)
        result = binding(training.root / "training_result.json")
        store.write("adapter_reload.json", {"exact_tensor_equality": True, "tensor_count": 8, "adapter": {"training_result": result}})
        for qid in ("v0", "v1"):
            store.write(f"traces/{qid}.json", {"qid": qid, "status": "ok"})
        store.write("completion.json", {"student": "onethinker", "attempted_qids": ["v0", "v1"],
                                        "successful_outputs": 2, "failed_outputs": 0, "training_result": result})
        return store

    def test_output_requires_an_explicit_contained_scratch_root(self):
        self.assertEqual(storage.output_path(self.scratch / "run", self.scratch), self.scratch / "run")
        with self.assertRaises(ValueError):
            storage.output_path(self.scratch / "run")
        with self.assertRaises(ValueError):
            storage.output_path(self.scratch / "../outside", self.scratch)
        with self.assertRaises(ValueError):
            storage.output_path(self.scratch / "run", self.root)

    def test_symlink_escape_is_rejected(self):
        (self.scratch / "escape").symlink_to(self.publish, target_is_directory=True)
        with self.assertRaises(ValueError):
            storage.output_path(self.scratch / "escape/run", self.scratch)

    def test_low_space_and_directory_cap_fail_closed(self):
        with patch.object(storage.shutil, "disk_usage", return_value=SimpleNamespace(free=149 * 1024**3)):
            with self.assertRaisesRegex(ValueError, "150 GiB"):
                storage.ensure_free_space(self.scratch)
        store = storage.RunArtifacts(self.scratch / "cap", self.config, self.scratch)
        with patch.object(storage, "MAX_DIRECTORY_FILES", 2):
            with self.assertRaisesRegex(ValueError, "directory"):
                store.write("extra.json", {})

    def test_run_and_artifact_paths_are_immutable_and_have_provenance(self):
        store = storage.RunArtifacts(self.scratch / "run", self.config, self.scratch)
        store.write("step.json", {"step": 1})
        document = load_json(store.root / "step.json")
        self.assertTrue(document["infrastructure_only"])
        self.assertFalse(document["benchmark_improvement_claim"])
        self.assertEqual(document["provenance"]["config_sha256"], digest_json(self.config))
        with self.assertRaises(ValueError):
            store.write("step.json", {"step": 2})
        with self.assertRaises(ValueError):
            storage.RunArtifacts(store.root, self.config, self.scratch)
        with self.assertRaises(ValueError):
            store.write("../escape.json", {})

    def test_code_provenance_refuses_a_dirty_tree(self):
        with patch.object(storage.subprocess, "run", side_effect=[SimpleNamespace(stdout="a" * 40 + "\n"), SimpleNamespace(stdout=" M student_pilot/diagnostic.py\n")]):
            with self.assertRaisesRegex(ValueError, "clean"):
                self.real_provenance(self.config)

    def test_code_provenance_records_commit_and_configuration_hash(self):
        with patch.object(storage.subprocess, "run", side_effect=[SimpleNamespace(stdout="b" * 40 + "\n"), SimpleNamespace(stdout="")]):
            provenance = self.real_provenance(self.config)
        self.assertEqual(provenance["commit"], "b" * 40)
        self.assertFalse(provenance["dirty"])
        self.assertEqual(provenance["config_sha256"], digest_json(self.config))

    def test_frames_are_hashed_deduplicated_and_only_paths_change(self):
        source = self.root / "real-frame-fixture.png"
        source.write_bytes(b"retained synthetic CPU frame bytes")
        rows = [{"qid": str(index), "target": "SMOKE PLACEHOLDER: not a distillation target",
                 "student_input": {"frames": [binding(source)], "question": "CPU fixture"}} for index in range(2)]
        before = copy.deepcopy(rows)
        staged, receipt = storage.stage_frames(rows, self.scratch / "frames", self.scratch)
        self.assertEqual(rows, before)
        self.assertEqual(len(receipt["files"]), 1)
        frame = staged[0]["student_input"]["frames"][0]
        self.assertTrue(Path(frame["path"]).is_relative_to(self.scratch))
        self.assertEqual(binding(frame["path"])["sha256"], before[0]["student_input"]["frames"][0]["sha256"])
        self.assertEqual(staged[0]["student_input"]["frames"], staged[1]["student_input"]["frames"])
        self.assertEqual(staged[0]["target"], before[0]["target"])
        with self.assertRaises(ValueError):
            storage.stage_frames(rows, self.scratch / "frames", self.scratch)

    def test_frame_drift_refuses_staging(self):
        source = self.root / "frame.png"
        source.write_bytes(b"before")
        frame = binding(source)
        source.write_bytes(b"after")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            storage.stage_frames([{"student_input": {"frames": [frame]}}], self.scratch / "frames", self.scratch)

    def test_finalize_checks_every_copy_and_preserves_local_files(self):
        training = self.run_fixture()
        evaluation = self.evaluation_fixture(training)
        destination = self.publish / "onethinker"
        result = storage.finalize(training.root, destination, self.scratch, evaluation.root)
        self.assertEqual(result["local_path"], str(training.root))
        self.assertEqual(result["published_path"], str(destination))
        self.assertTrue((training.root / "adapter/adapter_model.safetensors").is_file())
        manifest = load_json(destination / "SHA256_MANIFEST.json")
        self.assertIn("adapter/adapter_model.safetensors", manifest["files"])
        self.assertIn("steps/0004.json", manifest["files"])
        self.assertIn("evaluation/adapter_reload.json", manifest["files"])
        for relative, expected in manifest["files"].items():
            self.assertEqual(binding(destination / relative)["sha256"], expected["sha256"])
        self.assertEqual(load_json(training.root / "PUBLISHED.json"), load_json(destination / "PUBLISHED.json"))
        with self.assertRaises(ValueError):
            storage.finalize(training.root, destination, self.scratch, evaluation.root)

    def test_finalize_rejects_foreign_or_existing_publish_paths(self):
        training = self.run_fixture()
        for destination in (self.root / "outside", self.publish):
            with self.assertRaises(ValueError):
                storage.finalize(training.root, destination, self.scratch)

    def test_finalize_refuses_missing_steps_or_changed_adapter(self):
        training = self.run_fixture()
        (training.root / "adapter/adapter_model.safetensors").write_bytes(b"corrupted fixture")
        with self.assertRaises(ValueError):
            storage.finalize(training.root, self.publish / "bad", self.scratch)
        self.assertFalse((self.publish / "bad").exists())

    def test_smoke_publication_requires_successful_adapter_reload(self):
        training = self.run_fixture()
        with self.assertRaisesRegex(ValueError, "evaluation"):
            storage.finalize(training.root, self.publish / "missing_eval", self.scratch)
        self.assertFalse((self.publish / "missing_eval").exists())

    def test_finalize_refuses_invalid_reload_and_step_coverage(self):
        training = self.run_fixture()
        evaluation = self.evaluation_fixture(training)
        path = evaluation.root / "adapter_reload.json"
        document = load_json(path)
        document["exact_tensor_equality"] = False
        path.write_bytes(storage.canonical_bytes(document))
        with self.assertRaisesRegex(ValueError, "reload"):
            storage.finalize(training.root, self.publish / "invalid_reload", self.scratch, evaluation.root)
        step = training.root / "steps/0002.json"
        document = load_json(step)
        document["step"] = 99
        step.write_bytes(storage.canonical_bytes(document))
        with self.assertRaisesRegex(ValueError, "step coverage"):
            storage.finalize(training.root, self.publish / "invalid_step", self.scratch, evaluation.root)

    def test_local_training_requires_staging_nonlocal_frames(self):
        source = self.root / "source.png"
        source.write_bytes(b"synthetic RGB storage fixture")
        rows = [{"qid": "fixture", "student_input": {"frames": [binding(source)]}}]
        manifest = self.root / "manifest.json"
        manifest.write_bytes(storage.canonical_bytes({"rows": rows}))
        store = storage.RunArtifacts(self.scratch / "localize", self.config, self.scratch)
        with self.assertRaisesRegex(ValueError, "stage-frames"):
            storage.localize_frames(rows, store, manifest, self.scratch)
        staged = storage.localize_frames(rows, store, manifest, self.scratch, stage=True)
        self.assertEqual(load_json(store.root / "input_manifest.json")["rows"], staged)
        self.assertEqual(load_json(store.root / "frame_staging.json")["provenance"], store.provenance)

    def test_generation_header_hash_includes_written_provenance(self):
        store = storage.RunArtifacts(self.scratch / "header", self.config, self.scratch)
        header = store.record({"schema": "test-run"})
        store.write("run.json", header)
        self.assertEqual(digest_json(header), digest_json(load_json(store.root / "run.json")))

    def test_runtime_caches_are_local_without_replacing_the_hf_cache(self):
        from student_pilot.common import configure_environment

        runtime = self.root / "runtime"
        with patch.dict(storage.os.environ, {"HF_HOME": "/data2/jjyeung/cache/huggingface"}), \
                patch("student_pilot.common.REPO", self.root):
            configure_environment(runtime)
            self.assertEqual(storage.os.environ["HF_HOME"], "/data2/jjyeung/cache/huggingface")
            self.assertEqual(storage.os.environ["HF_HUB_OFFLINE"], "1")
            for key in ("TMPDIR", "XDG_CACHE_HOME", "CUDA_CACHE_PATH", "TRITON_CACHE_DIR", "TORCHINDUCTOR_CACHE_DIR"):
                self.assertTrue(Path(storage.os.environ[key]).is_relative_to(runtime))
        with self.assertRaises(ValueError):
            configure_environment("/tmp/forbidden-runtime")

    def test_launcher_honors_explicit_venv_and_visible_device(self):
        from student_pilot.common import REPO

        interpreter = self.root / "custom_venv/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "gpu=$CUDA_VISIBLE_DEVICES" "$@"\n')
        interpreter.chmod(0o700)
        result = storage.subprocess.run(["bash", str(REPO / "scripts/diagnostic_gpu_batch.sh"), "train", "fixture_lease.json", "--student", "qwen35"],
                                        env={**storage.os.environ, "PILOT_VENV": str(interpreter.parent.parent), "CUDA_VISIBLE_DEVICES": "7"},
                                        text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.__getattribute__("sp" "litlines")()[:6], ["gpu=7", "-B", "-u", "-m", "student_pilot.cli", "diagnostic"])
        self.assertIn("qwen35", result.stdout)

    def test_launcher_reports_an_unusable_explicit_venv(self):
        from student_pilot.common import REPO

        result = storage.subprocess.run(["bash", str(REPO / "scripts/diagnostic_gpu_batch.sh"), "train", "fixture_lease.json"],
                                        env={**storage.os.environ, "PILOT_VENV": str(self.root / "absent")}, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PILOT_VENV has no executable interpreter", result.stderr)


if __name__ == "__main__":
    unittest.main()
