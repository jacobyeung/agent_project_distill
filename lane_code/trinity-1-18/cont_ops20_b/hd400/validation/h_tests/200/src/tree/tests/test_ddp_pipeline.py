import copy
import io
import math
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import torch

from student_pilot import ddp_config, diagnostic, diagnostic_data, provisional, provisional_data, storage
from student_pilot.benchmark_eval import contracts
from student_pilot.common import binding, canonical_bytes, digest_json, load_json
from tests import test_benchmark_eval as benchmark_fixtures
from tests import test_provisional as fixtures
from tests import test_provisional_pipeline as pipeline_fixtures


LABEL = fixtures.LABEL
V2_PUBLICATION = Path("/data2/jjyeung/agent_project_data/devin_lane_out/trainer_provisional_path_v2_20260919_out/boundary_green_fixtures/provisional_pk_4kxh0/published/student/PUBLISHED.json")


class DDPProtocolTests(unittest.TestCase):
    setUp = fixtures.ProvisionalTests.setUp
    document = fixtures.ProvisionalTests.document
    candidates = fixtures.ProvisionalTests.candidates
    index = fixtures.ProvisionalTests.index
    prepare_pool = pipeline_fixtures.ProvisionalPipelineTests.prepare_pool

    def ddp_pool(self, student="onethinker", label=LABEL, config=None):
        self.prepare_pool(student)
        self.label = label
        self.config_path = self.document("training_config.json", {"world_size": 2, **(config or {})})
        self.protocol_path = self.root / "ddp_protocol.json"
        self.training_path = self.root / "ddp_training.json"
        self.heldout_path = self.root / "ddp_heldout.json"
        provisional_data.prepare_protocol(self.root / "candidate_index.jsonl", self.protocol_path, label,
                                         student, training_config=self.config_path)
        self.protocol = provisional_data.load_protocol(self.protocol_path, label)

        def encode(processor, row):
            return {}, {"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 10,
                        "prompt_tokens": 20, "sequence_tokens": 32, "visual_tokens": 16}

        with patch("student_pilot.batches.load_processor", return_value=object()), \
                patch.object(diagnostic_data, "target_tokens", return_value=10), \
                patch.object(diagnostic_data, "encode_training", side_effect=encode):
            provisional_data.prepare_training(self.protocol_path, self.training_path, label)
        provisional_data.prepare_heldout(self.protocol_path, self.heldout_path, label)
        return self.protocol

    def completed_run(self, student="onethinker", config=None):
        self.ddp_pool(student, config=config)
        source, _ = benchmark_fixtures.synthetic_adapter(self.root, student)
        settings = self.protocol["training"]
        manifest = load_json(self.training_path)
        count = manifest["counts"]["training_rows"]
        steps = math.ceil(count / settings["effective_batch_size"]) * settings["epochs"]
        config = provisional.tag({"student": student, "PROVISIONAL_DIVISION_SHA": self.protocol["PROVISIONAL_DIVISION_SHA"]}, LABEL)
        self.store = storage.RunArtifacts(self.root / "training_run", config, self.root)
        name = provisional.adapter_directory(LABEL)
        directory = self.store.root / name
        directory.mkdir()
        pins = {}
        for key, filename in (("config", "adapter_config.json"), ("weights", "adapter_model.safetensors")):
            storage.copy_new(source / filename, directory / filename, binding(source / filename)["sha256"])
            pins[key] = binding(directory / filename)
        self.store.write(f"{name}/provenance.json", {"adapter": pins, "protocol_version": ddp_config.VERSION})
        for step in range(1, steps + 1):
            self.store.write(f"steps/{step:04d}.json", {"step": step})
        self.store.write("throughput.json", {"synthetic": True, "world_size": settings["world_size"]})
        (self.store.root / "train.log").write_text(f"{LABEL} synthetic CPU publication fixture\n")
        (self.store.root / "metrics.jsonl").write_text("{}\n")
        result = {"schema": "completed-provisional-diagnostic-training-v1", "status": "TRAINED", "student": student,
                  "synthetic": True, "base": self.protocol["base"], "base_sha256": self.protocol["base_sha256"],
                  "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter", "protocol": binding(self.protocol_path),
                  "training_manifest": binding(self.training_path), "adapter": pins,
                  "adapter_parameters": settings["trainable_parameters"], "protocol_version": ddp_config.VERSION,
                  "training_sha256": self.protocol["training_sha256"], "settings": settings,
                  "run_control": self.protocol["run_control"], "run_control_sha256": self.protocol["run_control_sha256"],
                  "dataset_counts": manifest["counts"], "frozen_base_unchanged": True,
                  "completed_epochs": settings["epochs"],
                  "rank_checks": [{"rank": rank, "frozen_base_unchanged": True} for rank in range(settings["world_size"])],
                  "realized": {"optimizer_steps": steps, "training_rows": steps * 32,
                               "source_rows": count * settings["epochs"], "epoch_padding_rows": steps * 32 - count * settings["epochs"]}}
        self.store.write("training_result.json", result)
        self.store.write("run.json", result)
        self.store.write("input_manifest.json", {"rows": manifest["rows"]})
        self.publish = self.root / "published" / "ddp_student"
        return self.store.root

    def test_protocol_normalizes_and_hashes_v2_settings_and_full_runtime(self):
        protocol = self.ddp_pool()
        self.assertEqual(protocol["protocol_version"], ddp_config.VERSION)
        self.assertEqual(protocol["training_sha256"], digest_json(protocol["training"]))
        self.assertEqual(protocol["training"]["memory_fit_safety_factor"], 1.15)
        self.assertEqual(protocol["training_config_source"], binding(self.config_path))
        names = {Path(pin["path"]).name for pin in protocol["runtime"]}
        self.assertTrue({"ddp_config.py", "ddp_core.py", "ddp_admission.py", "ddp_training.py"} <= names)
        self.assertIn("ddp_config.py", {Path(pin["path"]).name for pin in contracts.runtime_bindings(LABEL)})
        with self.assertRaisesRegex(ValueError, "train-ddp"):
            provisional_data.load_single_training_protocol(self.protocol_path, LABEL)
        altered = copy.deepcopy(protocol)
        altered["training"]["learning_rate"] *= 2
        path = self.document("corrupt_protocol.json", altered)
        with self.assertRaisesRegex(ValueError, "hash changed"):
            provisional_data.load_protocol(path, LABEL)

    def test_all_accepted_labels_propagate_without_clean_admission(self):
        for label in provisional.LABELS:
            with self.subTest(label=label):
                self.root = Path(tempfile.mkdtemp(prefix="ddp_label_", dir=os.environ["LANE_TEST_OUTPUT"]))
                protocol = self.ddp_pool(label=label)
                for path, loader in ((self.protocol_path, provisional_data.load_protocol),
                                     (self.training_path, provisional_data.load_training),
                                     (self.heldout_path, provisional_data.load_heldout)):
                    value = loader(path, label)
                    self.assertEqual(value["provisional_diagnostic"], label)
                    self.assertEqual(value["PROVISIONAL_DIVISION_SHA"], protocol["PROVISIONAL_DIVISION_SHA"])
                    self.assertFalse(value["score_nomination_allowed"])
                    with self.assertRaises(ValueError):
                        provisional.require_mode(value, None)
                    with self.assertRaises(ValueError):
                        loader(path, next(other for other in provisional.LABELS if other != label))

    def test_config_file_rejects_duplicate_keys_and_nonfinite_values(self):
        for text in ('{"world_size": 2, "world_size": 4}', '{"learning_rate": NaN}'):
            path = self.root / "bad_training_config.json"
            path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                ddp_config.load_training_config(path, "onethinker")

    def test_finalize_retains_v2_schema_and_evaluation_accepts_ddp_receipt(self):
        run = self.completed_run()
        receipt = storage.finalize(run, self.publish, self.root, provisional_diagnostic=LABEL)
        self.assertEqual(receipt["schema"], "student-publication-v1")
        self.assertEqual(receipt["protocol_version"], ddp_config.VERSION)
        self.assertEqual(receipt["adapter_directory"], "adapter-" + LABEL)
        self.assertEqual(Path(receipt["training_result"]["path"]), self.publish / "training_result.json")
        if V2_PUBLICATION.is_file():
            fixture = load_json(V2_PUBLICATION)
            self.assertEqual(set(receipt), set(fixture) | {"protocol_version"})
            for key in fixture:
                self.assertIs(type(receipt[key]), type(fixture[key]))
        pin = contracts.validate_adapter("distilled", "onethinker", self.publish / receipt["adapter_directory"],
                                         self.publish / "PUBLISHED.json", contracts.DEFAULT_CONFIG,
                                         allow_synthetic=True, provisional_diagnostic=LABEL)
        self.assertEqual(pin["tensor_count"], 6)
        census = load_json(self.publish / "SHA256_MANIFEST.json")["files"]
        self.assertTrue({"throughput.json", "metrics.jsonl", "train.log"} <= census.keys())
        for name, expected in census.items():
            self.assertEqual(binding(self.publish / name)["sha256"], expected["sha256"])

    def test_publication_records_checkpoint_resume_without_changing_schema(self):
        run = self.completed_run()
        result = load_json(run / "training_result.json")
        resumed = {"path": "/scratch/synthetic/train/checkpoints/step_1", "step": 1,
                   "checkpoint_sha256": "c" * 64}
        result.update(resumed_from=resumed, resumed_from_step=1)
        (run / "training_result.json").write_bytes(canonical_bytes(result))
        receipt = storage.finalize(run, self.publish, self.root, provisional_diagnostic=LABEL)
        self.assertEqual(receipt["schema"], "student-publication-v1")
        self.assertEqual(receipt["resumed_from"], resumed)
        self.assertEqual(load_json(self.publish / "PUBLISHED.json")["resumed_from"], resumed)
        self.assertEqual(load_json(self.publish / "training_result.json")["resumed_from_step"], 1)
        self.assertEqual(load_json(self.publish / "publication_provenance.json")["config"]["resumed_from"], resumed)

    def test_ddp_adapter_admission_does_not_open_target_rows(self):
        run = self.completed_run("qwen35")
        targets = {self.training_path.resolve(), (run / "input_manifest.json").resolve(),
                   (self.root / "candidate_index.jsonl").resolve()}
        original_open = Path.open

        def checked_open(path, *args, **kwargs):
            if path.resolve() in targets:
                self.fail("Evaluation adapter admission read target-bearing rows")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", checked_open):
            pin = diagnostic.adapter_binding(run, self.protocol_path, "qwen35", LABEL)
        self.assertEqual(pin["training_result"], binding(run / "training_result.json"))

    def test_smoke_partial_training_or_missing_rank_proof_cannot_publish(self):
        run = self.completed_run()
        original = load_json(run / "training_result.json")
        variants = [{"status": "SMOKE_COMPLETE"}, {"completed_epochs": 2}, {"frozen_base_unchanged": False},
                    {"protocol_version": "wrong"}, {"rank_checks": original["rank_checks"][:1]},
                    {"realized": {**original["realized"], "source_rows": 1}}]
        for index, patch_value in enumerate(variants):
            (run / "training_result.json").write_bytes(canonical_bytes({**original, **patch_value}))
            with self.subTest(patch=patch_value), self.assertRaises(ValueError):
                storage.finalize(run, self.root / "published" / f"bad{index}", self.root, provisional_diagnostic=LABEL)
        protocol = copy.deepcopy(self.protocol)
        protocol["training"]["max_steps"] = 20
        protocol["training_sha256"] = digest_json(protocol["training"])
        smoke = {**original, "settings": protocol["training"], "training_sha256": protocol["training_sha256"]}
        with self.assertRaisesRegex(ValueError, "full-epoch"):
            ddp_config.validate_training_result(smoke, protocol, LABEL)

    def test_clean_and_wrong_label_publication_remain_refused(self):
        run = self.completed_run()
        for label in (None, provisional.LABELS[1]):
            with self.subTest(label=label), self.assertRaises(ValueError):
                storage.finalize(run, self.publish, self.root, provisional_diagnostic=label)
        with self.assertRaises(ValueError):
            provisional.tag({"schema": "clean-student-training-v1"}, LABEL)

    def test_all_rank_receipts_are_written_after_staging_before_model_loading(self):
        from student_pilot import ddp_admission, ddp_training
        from contextlib import ExitStack

        class ModelBoundary(Exception):
            pass

        self.ddp_pool()
        events = []
        leases = [provisional.tag({"rank": rank, "host": "fixture-host", "gpu_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}",
                   "admission_probe": {"cuda_device_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}", "compute_pids": [],
                                       "heartbeat_age_seconds": 1.0, "probed_at": "synthetic CPU probe"}}, LABEL)
                  for rank in range(2)]
        lease_path = self.document("ddp_leases.json", {"ranks": leases, "synthetic": True})
        output = self.root / "entry_run"
        real_stage = ddp_training.localize_frames

        def stage(*args, **kwargs):
            events.append("stage")
            return real_stage(*args, **kwargs)

        def entry(lease, label, request, fresh=True):
            events.append("fresh_entry" if fresh else "lease_check")
            return lease

        def probe(*args, **kwargs):
            events.append("live_probe")
            return leases[0]

        def collect(value, world):
            if "request_sha256" in value:
                return [value, {**value, "rank": 1}]
            return [{"lease": lease, "error": None} for lease in leases]

        def load(*args, **kwargs):
            events.append("model_boundary")
            raise ModelBoundary

        with ExitStack() as stack:
            stack.enter_context(patch.object(ddp_admission, "load_bundle", return_value={"ranks": leases}))
            stack.enter_context(patch.object(ddp_admission, "select_rank", return_value=(0, 2, "GPU-fixture-0,GPU-fixture-1")))
            stack.enter_context(patch.object(ddp_admission, "require_rank_lease", side_effect=entry))
            stack.enter_context(patch.object(ddp_admission, "admitted_rank", side_effect=probe))
            stack.enter_context(patch.object(ddp_training, "gather", side_effect=collect))
            stack.enter_context(patch.object(ddp_training, "localize_frames", side_effect=stage))
            stack.enter_context(patch.object(ddp_training, "configure_environment"))
            stack.enter_context(patch("student_pilot.batches.load_processor", return_value=object()))
            stack.enter_context(patch("student_pilot.runner.load_base", side_effect=load))
            stack.enter_context(patch("transformers.set_seed"))
            for method in ("init_process_group", "destroy_process_group", "broadcast_object_list", "barrier"):
                stack.enter_context(patch.object(torch.distributed, method))
            with self.assertRaises(ModelBoundary):
                ddp_training.train(self.training_path, self.protocol_path, output, lease_path,
                                   scratch_root=self.root, stage_frames=True, provisional_diagnostic=LABEL)
        self.assertEqual(events, ["fresh_entry", "stage", "live_probe", "model_boundary"])
        header = load_json(output / "run.json")
        self.assertEqual(header["lease"]["ranks"], leases)
        self.assertEqual(header["protocol_version"], ddp_config.VERSION)
        self.assertEqual(header["provisional_diagnostic"], LABEL)
        self.assertTrue((output / "frame_staging.json").is_file())
        self.assertFalse((output / "training_result.json").exists())

    def test_cli_dispatches_only_explicit_provisional_ddp(self):
        common = ["--manifest", "not-opened", "--protocol", "not-opened", "--output", "not-opened",
                  "--lease", "not-opened", "--scratch-root", "/scratch/jjyeung", "--training-config", "not-opened"]
        with patch("student_pilot.ddp_training.train", return_value={}) as train, redirect_stdout(io.StringIO()):
            diagnostic.main(["train-ddp", *common, "--provisional-diagnostic", LABEL])
            self.assertEqual(train.call_args.args[-2:], (LABEL, "not-opened"))
        with patch("student_pilot.ddp_training.train", return_value={}) as train, redirect_stdout(io.StringIO()):
            diagnostic.main(["train-ddp", *common, "--provisional-diagnostic", LABEL,
                             "--resume-from", "/scratch/synthetic/train/checkpoints/step_25"])
            self.assertEqual(train.call_args.kwargs["resume_from"], "/scratch/synthetic/train/checkpoints/step_25")
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
            diagnostic.main(["train-ddp", *common])


class DDPArchitectureTests(unittest.TestCase):
    def test_both_students_attach_exact_rank32_text_vision_and_merger_targets(self):
        from accelerate import init_empty_weights
        from transformers import AutoConfig
        from student_pilot.adapters import attach_ddp_adapters, trainable_groups
        from student_pilot.students import get_student, model_class

        for student in ("onethinker", "qwen35"):
            with self.subTest(student=student):
                config = AutoConfig.from_pretrained(get_student(student)["snapshot"], local_files_only=True)
                settings = ddp_config.normalize_training_config({}, student)
                with init_empty_weights(include_buffers=True):
                    model = model_class(student)(config)
                    model, report = attach_ddp_adapters(model, settings)
                self.assertEqual(report["trainable_parameters"], settings["trainable_parameters"])
                self.assertEqual(report["group_parameters"], settings["group_parameters"])
                self.assertEqual(report["ranks"], {"text": 32, "vision": 32, "mergers": 32})
                self.assertEqual(report["alphas"], {"text": 64, "vision": 64, "mergers": 64})
                self.assertEqual(report["lora_dropout"], 0.05)
                groups = trainable_groups(model, report["targets"])
                self.assertTrue(all(p.dtype == torch.float32 for group in groups.values() for _, p in group))
                if student == "qwen35":
                    self.assertEqual(sum(".linear_attn." in name for name in report["targets"]["text"]), 120)


if __name__ == "__main__":
    unittest.main()
