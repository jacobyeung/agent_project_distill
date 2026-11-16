import ast
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from contextlib import ExitStack, redirect_stdout
from unittest.mock import patch

import torch
from peft import get_peft_model_state_dict
from safetensors.torch import load_file, save_file

from student_pilot import ddp_config, ddp_core, diagnostic_data, provisional_data, storage, warmstart
from student_pilot.common import REPO, binding, canonical_bytes, digest_json, load_json
from student_pilot.orchard_eval.contracts import MODEL_PINS
from student_pilot.provisional import adapter_directory, tag
from tests import test_ddp_models as native_fixtures
from tests import test_provisional as provisional_fixtures


BASE = "f5d970cfa2ff7de241f7f527356895242bd7888c"
RL = "76795f6f558d6ca1356013d4419c10df3573e5a9"
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


def reference_module(name, commit=BASE):
    source = subprocess.check_output(["git", "show", f"{commit}:student_pilot/{name}.py"], cwd=REPO, text=True)
    module = types.ModuleType(f"student_pilot._warmstart_reference_{name}")
    module.__package__ = "student_pilot"
    module.__file__ = str(REPO / "student_pilot" / f"{name}.py")
    exec(compile(source, f"{commit}:{name}", "exec"), module.__dict__)
    return module


class WarmstartTests(unittest.TestCase):
    document = provisional_fixtures.ProvisionalTests.document
    candidates = provisional_fixtures.ProvisionalTests.candidates
    index = provisional_fixtures.ProvisionalTests.index

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="sft_warmstart_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, STUDENT_ORCHARD="0", STUDENT_FRAME_ROOT_MAP=""))
        self.student = getattr(self, "student", "qwen35")
        self.model, self.groups, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
        self.targets = sorted({name.removeprefix("base_model.model.").__getattribute__("sp" "lit")(".lora_")[0]
                               for group in self.groups.values() for name, _ in group})
        self.settings = ddp_config.normalize_training_config({"world_size": 8, "epochs": 1, "lora_rank": 2,
                    "lora_alpha": 4, "lora_dropout": 0.0, "learning_rate": 5e-5}, self.student)
        self.base = self.make_base()
        self.parent = self.root / "r1813_synthetic" / "publication"
        self.parent.mkdir(parents=True)
        self.adapter = self.parent / adapter_directory(LABEL)
        with torch.no_grad():
            for index, parameter in enumerate(self.model.parameters()):
                if parameter.requires_grad:
                    parameter.fill_((index + 1) / 1000)
        self.model.peft_config["default"].base_model_name_or_path = MODEL_PINS[self.student]["repo_id"]
        self.model.save_pretrained(self.adapter, safe_serialization=True, save_embedding_layers=False)
        self.parent_protocol = tag({"schema": "provisional-student-diagnostic-protocol-v1", "student": self.student,
                "base": self.base, "base_sha256": digest_json(self.base), "training": self.settings,
                "protocol_version": ddp_config.VERSION, "selection_frozen_before_evaluation": True}, LABEL)
        self.receipt = tag({"schema": "student-publication-v1", "status": "TRAINED", "student": self.student,
                "base": {key: MODEL_PINS[self.student][key] for key in ("repo_id", "revision")},
                "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter",
                "published_path": str(self.parent), "local_path": str(self.root / "r1813_synthetic/train"),
                "adapter_directory": self.adapter.name, "provenance": {"commit": BASE, "dirty": False}}, LABEL)
        self.reseal()
        self.stack.enter_context(patch.object(storage, "SCRATCH_HOME", self.root))
        self.stack.enter_context(patch.object(storage, "ensure_free_space"))
        self.stack.enter_context(patch.object(storage, "code_provenance", side_effect=lambda value: {
            "commit": BASE, "dirty": False, "config_sha256": digest_json(value), "recorded_at": "synthetic CPU fixture"}))
        self.stack.enter_context(patch.object(diagnostic_data, "checkpoint_bindings", return_value=self.base))
        self.stack.enter_context(patch.object(diagnostic_data, "versions", return_value={"synthetic_cpu_fixture": True}))

    def make_base(self):
        root = self.root / "base" / MODEL_PINS[self.student]["revision"]
        root.mkdir(parents=True)
        (root / "config.json").write_text(self.model.config.to_json_string())
        for name in ("model.safetensors.index.json", "tokenizer.json", "tokenizer_config.json", "preprocessor_config.json",
                     "video_preprocessor_config.json", "processor_config.json", "chat_template.jinja"):
            (root / name).write_bytes(canonical_bytes({"synthetic": name}))
        shard = root / "model-00001-of-00001.safetensors"
        shard.write_bytes(b"synthetic base shard identity only")
        files = [binding(path) for path in sorted(root.iterdir()) if path != shard]
        return {"revision": root.name, "files": files, "weight_shards": [binding(shard)]}

    def reseal(self):
        path = self.parent / "protocol.json"
        path.write_bytes(canonical_bytes(self.parent_protocol))
        self.receipt["protocol"] = binding(path)
        self.receipt["adapter"] = {f"{kind}_sha256": binding(self.adapter / name)["sha256"]
                for kind, name in (("config", "adapter_config.json"), ("weights", "adapter_model.safetensors"))}
        (self.parent / "PUBLISHED.json").write_bytes(canonical_bytes(self.receipt))
        self.request = {"weights_sha256": self.receipt["adapter"]["weights_sha256"],
                        "published_sha256": binding(self.parent / "PUBLISHED.json")["sha256"],
                        "parent_run": "r1813_synthetic"}

    def identify(self, directory=None, settings=None, base=None, request=None):
        return warmstart.prepare_identity(directory or self.parent, self.student, settings or self.settings,
                                          base or self.base, LABEL, request or self.request)

    def protocol(self):
        identity = self.identify()
        return {"student": self.student, "training": self.settings, "base": self.base,
                "provisional_diagnostic": LABEL, "init_adapter_identity": identity,
                "init_adapter_sha256": digest_json(identity)}

    def test_publication_identity_reuses_rl_hash_scheme(self):
        source = subprocess.check_output(["git", "show", f"{RL}:student_pilot/rl_gspo.py"], cwd=REPO, text=True)
        node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
                    and node.name == "init_adapter_identity")
        namespace = {"__package__": "student_pilot", "Path": Path, "json": json}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "rl_reference", "exec"), namespace)
        self.assertEqual(warmstart.init_adapter_identity(self.parent, self.student),
                         namespace["init_adapter_identity"](self.parent, self.student))
        identity = self.identify()
        self.assertEqual(identity["sha256"], digest_json({"config": self.receipt["adapter"]["config_sha256"],
                                                         "weights": self.receipt["adapter"]["weights_sha256"]}))
        self.assertEqual(identity["training_receipt"], {"sha256": self.request["published_sha256"]})
        self.assertEqual(identity["parent_run"], self.request["parent_run"])

    def test_identity_is_stable_after_publication_and_base_relocation(self):
        expected = self.identify()
        relocated = self.root / "other_host" / "renamed_publication"
        shutil.copytree(self.parent, relocated)
        base = copy.deepcopy(self.base)
        for pin in base["files"] + base["weight_shards"]:
            pin["path"] = "/different/host/snapshot/" + Path(pin["path"]).name
        with patch.object(warmstart, "target_modules", return_value={"expected": self.targets, "modules": self.targets + ["lm_head"]}):
            actual = self.identify(relocated, base=base)
        self.assertEqual(canonical_bytes(expected), canonical_bytes(actual))
        self.assertNotIn(str(self.root), canonical_bytes(actual).decode())
        self.assertNotIn("path", canonical_bytes(actual).decode())

    def test_each_explicit_hash_and_parent_name_is_required_and_checked(self):
        for key in self.request:
            for replacement in (None, "wrong", "0" * 64):
                request = {**self.request, key: replacement}
                with self.subTest(key=key, replacement=replacement), self.assertRaises((ValueError, FileNotFoundError)):
                    self.identify(request=request)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                self.identify(request={name: value for name, value in self.request.items() if name != key})

    def test_corrupted_weights_config_receipt_and_protocol_are_refused(self):
        for name in ("adapter_model.safetensors", "adapter_config.json", "PUBLISHED.json", "protocol.json"):
            destination = self.root / ("corrupt_" + name)
            shutil.copytree(self.parent, destination)
            path = destination / (self.adapter.name if name.startswith("adapter_") else "") / name
            with path.open("ab") as stream:
                stream.write(b" ")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.identify(destination)

    def test_wrong_student_base_dirty_incomplete_and_escaping_publications_refuse(self):
        cases = (("student", "onethinker"), ("status", "SMOKE_COMPLETE"), ("schema", "other"),
                 ("base", {"repo_id": "other", "revision": "f" * 40}),
                 ("provenance", {"commit": BASE, "dirty": True}), ("adapter_directory", "../outside"))
        original = copy.deepcopy(self.receipt)
        for key, value in cases:
            self.receipt = {**original, key: value}
            self.reseal()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.identify()

    def test_lora_rank_alpha_dropout_targets_and_nonstandard_variants_refuse(self):
        path = self.adapter / "adapter_config.json"
        original = load_json(path)
        changes = {"r": 3, "lora_alpha": 8, "lora_dropout": 0.05,
                   "target_modules": self.targets[:-1], "rank_pattern": {self.targets[0]: 1},
                   "alpha_pattern": {self.targets[0]: 8}, "use_rslora": True, "use_dora": True,
                   "bias": "all", "modules_to_save": ["lm_head"], "fan_in_fan_out": True,
                   "lora_bias": True, "task_type": "SEQ_CLS"}
        for key, value in changes.items():
            path.write_bytes(canonical_bytes({**original, key: value}))
            self.reseal()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "LoRA|adapter|target"):
                self.identify()
        path.write_bytes(canonical_bytes({**original, "target_modules": [*self.targets, self.targets[0]]}))
        self.reseal()
        with self.assertRaisesRegex(ValueError, "target"):
            self.identify()

    def test_base_tokenizer_processor_and_weight_content_must_match(self):
        for field in ("files", "weight_shards"):
            for index, pin in enumerate(self.base[field]):
                base = copy.deepcopy(self.base)
                base[field][index]["sha256"] = "0" * 64
                with self.subTest(file=Path(pin["path"]).name), self.assertRaisesRegex(ValueError, "base|tokenizer|processor"):
                    self.identify(base=base)
        for key, value in (("revision", "f" * 40), ("files", self.base["files"][:-1])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.identify(base={**self.base, key: value})

    def test_parent_tensors_equal_after_load_and_optimizer_and_scheduler_are_fresh(self):
        protocol = self.protocol()
        child, groups, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
        parent_state = load_file(str(self.adapter / "adapter_model.safetensors"))
        report = {"targets": {"all": self.targets}, "trainable_parameters": sum(p.numel() for p in child.parameters() if p.requires_grad)}
        original_base = {name: parameter.detach().clone() for name, parameter in child.named_parameters() if not parameter.requires_grad}
        loaded = warmstart.initialize_adapters(child, report, protocol, self.root / "protocol.json", init_adapter=self.parent)
        actual = get_peft_model_state_dict(child, save_embedding_layers=False)
        self.assertEqual(set(actual), set(parent_state))
        for name, expected in parent_state.items():
            torch.testing.assert_close(actual[name], expected, rtol=0, atol=0)
        for name, value in child.named_parameters():
            if name in original_base:
                torch.testing.assert_close(value, original_base[name], rtol=0, atol=0)
        self.assertTrue(loaded["exact_tensor_equality"])
        self.assertTrue(loaded["initialization_applied"])
        optimizer = torch.optim.AdamW([p for p in child.parameters() if p.requires_grad], lr=self.settings["learning_rate"],
                                      betas=tuple(self.settings["betas"]), weight_decay=self.settings["weight_decay"], foreach=False)
        self.assertEqual(optimizer.state_dict()["state"], {})
        self.assertEqual(optimizer.param_groups[0]["lr"], 5e-5)
        self.assertEqual(ddp_core.schedule_lr(0, 100, self.settings), 5e-5 / 3)
        self.assertNotEqual(ddp_core.schedule_lr(0, 100, self.settings), ddp_core.schedule_lr(40, 100, self.settings))
        self.assertTrue(all(p.dtype == torch.float32 for p in child.parameters() if p.requires_grad))
        self.assertFalse(torch.cuda.is_initialized())

    def test_live_adapter_config_must_match_the_frozen_parent_before_loading(self):
        protocol = self.protocol()
        for key, value in (("lora_alpha", 8), ("lora_dropout", 0.2), ("use_rslora", True)):
            child, _, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
            setattr(child.peft_config["default"], key, value)
            before = copy.deepcopy(get_peft_model_state_dict(child, save_embedding_layers=False))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "LoRA"):
                warmstart.initialize_adapters(child, {"targets": {"all": self.targets}}, protocol,
                                              self.root / "protocol.json", init_adapter=self.parent)
            for name, tensor in get_peft_model_state_dict(child, save_embedding_layers=False).items():
                torch.testing.assert_close(tensor, before[name], rtol=0, atol=0)

    def test_tensor_payload_is_authenticated_again_at_the_load_boundary(self):
        protocol = self.protocol()
        child, _, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
        real_read = Path.read_bytes
        weights = self.adapter / "adapter_model.safetensors"

        def changed_payload(path):
            payload = real_read(path)
            return payload[:-1] + bytes([payload[-1] ^ 1]) if path == weights else payload

        with patch.object(Path, "read_bytes", changed_payload), self.assertRaisesRegex(ValueError, "tensor bytes changed"):
            warmstart.initialize_adapters(child, {"targets": {"all": self.targets}}, protocol,
                                          self.root / "protocol.json", init_adapter=self.parent)

    def test_resume_never_reads_or_applies_parent(self):
        protocol = self.protocol()
        report = {"targets": {"all": self.targets}}
        before = copy.deepcopy(get_peft_model_state_dict(self.model, save_embedding_layers=False))
        with patch.object(warmstart, "prepare_identity", side_effect=AssertionError("parent was reopened")):
            resumed = warmstart.initialize_adapters(self.model, report, protocol, self.root / "missing_protocol.json",
                                                    resume_from=self.root / "checkpoint", init_adapter=self.root / "missing_parent")
        self.assertFalse(resumed["initialization_applied"])
        for name, expected in before.items():
            torch.testing.assert_close(get_peft_model_state_dict(self.model, save_embedding_layers=False)[name], expected, rtol=0, atol=0)

    def test_tensor_name_shape_dtype_and_nonfinite_values_refuse(self):
        original = load_file(str(self.adapter / "adapter_model.safetensors"))
        name = next(iter(original))
        cases = ({key: value for key, value in original.items() if key != name},
                 {**original, "unexpected": torch.ones(1)},
                 {**original, name: torch.ones(1)},
                 {**original, name: original[name].bfloat16()},
                 {**original, name: torch.full_like(original[name], float("nan"))})
        for index, state in enumerate(cases):
            save_file(state, str(self.adapter / "adapter_model.safetensors"))
            self.reseal()
            protocol = self.protocol()
            child, _, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
            with self.subTest(case=index), self.assertRaisesRegex(ValueError, "tensor|dtype|shape|finite"):
                warmstart.initialize_adapters(child, {"targets": {"all": self.targets}}, protocol,
                                              self.root / "protocol.json", init_adapter=self.parent)

    def test_config_option_is_content_only_and_default_normalization_matches_base(self):
        original = reference_module("ddp_config")
        for world in (8, 16):
            config = {"world_size": world, "epochs": 1, "learning_rate": 5e-5, "parallel": "fsdp", "checkpoint_every_steps": 500}
            self.assertEqual(canonical_bytes(ddp_config.normalize_training_config(config, self.student)),
                             canonical_bytes(original.normalize_training_config(config, self.student)))
            self.assertEqual(ddp_config.normalize_training_config({**config, "init_adapter": self.request}, self.student),
                             ddp_config.normalize_training_config(config, self.student))
        with self.assertRaises(ValueError):
            ddp_config.normalize_training_config({"init_adapter": {**self.request, "publication": str(self.parent)}}, self.student)

    def test_prepare_cli_freezes_content_and_records_source_outside_protocol(self):
        from student_pilot import provisional_cli
        index, _ = self.candidates()
        config = self.document("config.json", self.settings)
        output = self.root / "prepared/protocol.json"
        with redirect_stdout(io.StringIO()):
            provisional_cli.main(["prepare-protocol", "--candidate-index", str(index), "--training-config", str(config),
                "--student", self.student, "--output", str(output), "--scratch-root", str(self.root),
                "--provisional-diagnostic", LABEL, "--init-adapter", str(self.parent),
                "--init-adapter-weights-sha256", self.request["weights_sha256"],
                "--init-adapter-published-sha256", self.request["published_sha256"],
                "--init-adapter-run-name", self.request["parent_run"]])
        protocol = provisional_data.load_protocol(output, LABEL)
        self.assertEqual(protocol["init_adapter_identity"], self.identify())
        self.assertEqual(protocol["init_adapter_sha256"], digest_json(self.identify()))
        self.assertNotIn(str(self.parent), output.read_text())
        source = load_json(output.with_suffix(".init_adapter.json"))
        self.assertEqual(source["publication"], str(self.parent))
        self.assertEqual(source["init_adapter_sha256"], protocol["init_adapter_sha256"])
        self.parent.rename(self.root / "_quarantine_parent")
        self.assertEqual(provisional_data.load_protocol(output, LABEL), protocol)

    def test_glue_config_option_uses_sidecar_without_changing_training_settings(self):
        index, _ = self.candidates()
        config = self.document("frozen/config.json", {**self.settings, "init_adapter": self.request})
        self.document("frozen/config.init_adapter.json", {"publication": str(self.parent)})
        output = self.root / "frozen/protocol.json"
        provisional_data.prepare_protocol(index, output, LABEL, self.student, training_config=config, scratch_root=self.root)
        protocol = provisional_data.load_protocol(output, LABEL)
        self.assertEqual(protocol["training"], self.settings)
        self.assertEqual(protocol["init_adapter_identity"], self.identify())
        fresh = copy.deepcopy(protocol)
        fresh.pop("init_adapter_identity")
        fresh.pop("init_adapter_sha256")
        self.assertNotEqual(digest_json(fresh), digest_json(protocol))

    def test_warmstart_training_uses_source_receipt_without_rereading_payloads(self):
        index, _ = self.candidates()
        config = self.document("frozen/config.json", {**self.settings, "init_adapter": self.request})
        self.document("frozen/config.init_adapter.json", {"publication": str(self.parent)})
        protocol_path = self.root / "frozen/protocol.json"
        training_path = self.root / "frozen/training.json"
        provisional_data.prepare_protocol(index, protocol_path, LABEL, self.student,
                                          training_config=config, scratch_root=self.root)
        protocol = provisional_data.load_protocol(protocol_path, LABEL)
        self.assertEqual(protocol["init_adapter_identity"], self.identify())

        def encode(processor, row):
            return {}, {"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 10,
                        "prompt_tokens": 20, "sequence_tokens": 32, "visual_tokens": 16}

        with patch("student_pilot.batches.load_processor", return_value=object()), \
                patch.object(diagnostic_data, "target_tokens", return_value=10), \
                patch.object(diagnostic_data, "encode_training", side_effect=encode):
            provisional_data.prepare_training(protocol_path, training_path, LABEL, self.root)
        full = provisional_data.load_training(training_path, LABEL, use_receipt=False)
        provisional_data.seal_source(training_path, provisional_data.source_receipt_path(training_path), LABEL, self.root)
        with patch.object(provisional_data, "source_rows", side_effect=AssertionError("candidate payloads re-read")), \
                patch("student_pilot.provisional._load_candidate_rows", side_effect=AssertionError("candidate payloads re-read")), \
                patch.object(provisional_data, "_verified_receipt", wraps=provisional_data._verified_receipt) as verified:
            self.assertEqual(provisional_data.load_training(training_path, LABEL), full)
            verified.assert_called_once()
            with self.assertRaisesRegex(AssertionError, "candidate payloads re-read"):
                provisional_data.load_training(training_path, LABEL, use_receipt=False)

    def test_identity_metadata_and_result_must_match_the_frozen_parent(self):
        protocol = self.protocol()
        warmstart.validate_identity(protocol)
        for key in ("init_adapter_identity", "init_adapter_sha256"):
            changed = copy.deepcopy(protocol)
            changed.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                warmstart.validate_identity(changed)
        changed = copy.deepcopy(protocol)
        changed["init_adapter_identity"]["parent_run"] = "another_parent"
        with self.assertRaises(ValueError):
            warmstart.validate_identity(changed)
        with self.assertRaises(ValueError):
            warmstart.validate_result({}, protocol)
        warmstart.validate_result({"init_adapter_identity": protocol["init_adapter_identity"],
                                    "init_adapter_sha256": protocol["init_adapter_sha256"]}, protocol)

    def test_default_prepare_protocol_bytes_equal_f5d970c(self):
        original = reference_module("provisional_data")
        index, _ = self.candidates()
        config = self.document("config.json", self.settings)
        reference = self.root / "reference/protocol.json"
        actual = self.root / "actual/protocol.json"
        with patch.object(original, "runtime_bindings", return_value=[]), patch.object(provisional_data, "runtime_bindings", return_value=[]), \
                patch.object(ddp_config, "runtime_bindings", return_value=[]):
            original.prepare_protocol(index, reference, LABEL, self.student, training_config=config, scratch_root=self.root)
            provisional_data.prepare_protocol(index, actual, LABEL, self.student, training_config=config, scratch_root=self.root)
        self.assertEqual(reference.read_bytes(), actual.read_bytes())
        protocol = load_json(actual)
        self.assertNotIn("init_adapter_identity", protocol)
        self.assertNotIn("init_adapter_sha256", protocol)
        self.assertFalse(actual.with_suffix(".init_adapter.json").exists())

    def test_warm_protocol_bytes_ignore_relocated_parent_paths(self):
        index, _ = self.candidates()
        config = self.document("config.json", self.settings)
        relocated = self.root / "remote_host/copied_parent"
        shutil.copytree(self.parent, relocated)
        outputs = [self.root / name / "protocol.json" for name in ("warm_a", "warm_b", "fresh")]
        for parent, output in zip((self.parent, relocated), outputs):
            provisional_data.prepare_protocol(index, output, LABEL, self.student, training_config=config, scratch_root=self.root,
                    init_adapter=parent, init_adapter_weights_sha256=self.request["weights_sha256"],
                    init_adapter_published_sha256=self.request["published_sha256"], init_adapter_run_name=self.request["parent_run"])
        provisional_data.prepare_protocol(index, outputs[2], LABEL, self.student, training_config=config, scratch_root=self.root)
        self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
        self.assertNotEqual(outputs[0].read_bytes(), outputs[2].read_bytes())
        self.assertNotEqual(outputs[0].with_suffix(".init_adapter.json").read_bytes(),
                            outputs[1].with_suffix(".init_adapter.json").read_bytes())

    def test_peft_suffix_selectors_are_resolved_against_the_exact_module_allowlist(self):
        layout = warmstart.target_modules(self.base, self.student)
        original = load_json(self.adapter / "adapter_config.json")
        suffixes = sorted({name.__getattribute__("sp" "lit")(".", 1)[-1] for name in self.targets})
        expected = warmstart.lora_identity(original, self.settings, layout)
        self.assertEqual(warmstart.lora_identity({**original, "target_modules": suffixes}, self.settings, layout), expected)
        with self.assertRaisesRegex(ValueError, "target"):
            warmstart.lora_identity({**original, "target_modules": [*suffixes, "lm_head"]}, self.settings, layout)

    def test_deployment_sidecar_supports_unchanged_prepare_glue(self):
        index, _ = self.candidates()
        config = self.document("frozen/config.json", {**self.settings, "init_adapter": self.request})
        deploy = self.root / "deployment"
        self.document("deployment/scripts/orchard/configs/qwen35.init_adapter.json", {"publication": str(self.parent)})
        output = self.root / "frozen/protocol.json"
        with patch.dict(os.environ, ORCH_DEPLOY=str(deploy)):
            provisional_data.prepare_protocol(index, output, LABEL, self.student, training_config=config, scratch_root=self.root)
        protocol = provisional_data.load_protocol(output, LABEL)
        self.assertEqual(protocol["init_adapter_identity"], self.identify())
        child, _, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(self.student)
        report = warmstart.initialize_adapters(child, {"targets": {"all": self.targets}}, protocol, output)
        self.assertTrue(report["exact_tensor_equality"])

    def test_changed_config_parent_is_refused_before_admission(self):
        from student_pilot import ddp_admission, ddp_training
        index, _ = self.candidates()
        config = self.document("config.json", {**self.settings, "init_adapter": self.request})
        self.document("config.init_adapter.json", {"publication": str(self.parent)})
        output = self.root / "frozen/protocol.json"
        provisional_data.prepare_protocol(index, output, LABEL, self.student, training_config=config, scratch_root=self.root)
        wrong = self.document("wrong_config.json", {**self.settings, "init_adapter": {**self.request, "parent_run": "another"}})
        with patch.object(ddp_admission, "request_identity") as admission, self.assertRaisesRegex(ValueError, "frozen parent"):
            ddp_training.train("unopened_manifest", output, self.root / "never_created", "unopened_lease",
                               student=self.student, provisional_diagnostic=LABEL, training_config=wrong)
        admission.assert_not_called()
        self.assertFalse((self.root / "never_created").exists())

    def test_cli_forwards_only_an_explicit_relocated_parent(self):
        from student_pilot import provisional_cli
        args = ["train-ddp", "--manifest", "unopened", "--protocol", "unopened", "--output", "unopened",
                "--lease", "unopened", "--student", self.student, "--provisional-diagnostic", LABEL, "--scratch-root", str(self.root)]
        with patch("student_pilot.ddp_training.train", return_value={}) as train, redirect_stdout(io.StringIO()):
            provisional_cli.main(args)
            self.assertNotIn("init_adapter", train.call_args.kwargs)
            provisional_cli.main([*args, "--init-adapter", "/relocated/parent"])
            self.assertEqual(train.call_args.kwargs["init_adapter"], "/relocated/parent")


class WarmstartProductionLayoutTests(unittest.TestCase):
    def test_meta_qwen_world8_and_world16_accept_peft_compressed_target_selectors(self):
        from accelerate import init_empty_weights
        from student_pilot.adapters import attach_ddp_adapters
        from student_pilot.students import get_student, model_class

        for student, world, parameters in (("qwen35", 8, 102530048), ("qwen36_27b", 16, 249461760)):
            with self.subTest(student=student, world=world), patch.dict(os.environ, STUDENT_ORCHARD="0"):
                spec = get_student(student)
                config_pin = binding(spec["snapshot"] / "config.json", spec["config_sha256"])
                layout = warmstart.target_modules({"files": [config_pin]}, student)
                self.assertEqual(len(layout["expected"]), sum(spec["target_counts"].values()))
                settings = ddp_config.normalize_training_config({"world_size": world, "parallel": "fsdp",
                            "epochs": 1, "learning_rate": 5e-5, "checkpoint_every_steps": 500}, student)
                cls = model_class(student)
                with init_empty_weights(include_buffers=True):
                    model, report = attach_ddp_adapters(cls(cls.config_class.from_dict(load_json(config_pin["path"]))), settings)
                config = model.peft_config["default"].to_dict()
                config["target_modules"] = sorted(config["target_modules"])
                self.assertLess(len(config["target_modules"]), len(layout["expected"]))
                identity = warmstart.lora_identity(config, settings, layout)
                self.assertEqual(identity["target_modules_sha256"], digest_json(layout["expected"]))
                self.assertEqual(report["trainable_parameters"], parameters)
                self.assertEqual(settings["world_size"], world)
                self.assertEqual(settings["learning_rate"], 5e-5)
                self.assertEqual(settings["warmup_ratio"], 0.03)
                self.assertEqual(ddp_config.normalize_run_control({"checkpoint_every_steps": 500})["checkpoint_every_steps"], 500)
                self.assertTrue(all(parameter.device.type == "meta" for parameter in model.parameters()))
                self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
