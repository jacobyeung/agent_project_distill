import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import patch

import torch
from peft import get_peft_model_state_dict
from safetensors.torch import load_file

from student_pilot import ddp_checkpoints, ddp_config, ddp_core, ddp_training, diagnostic_data, fsdp_training, warmstart
from student_pilot.common import REPO, canonical_bytes, digest_json, load_json
from student_pilot.orchard_eval.contracts import MODEL_PINS
from student_pilot.provisional import tag
from tests import test_ddp_checkpoints as checkpoint_fixtures
from tests.test_fsdp import SOCKETS
from tests import test_sft_warmstart as fixtures
from tests.version_pin import REASON as PIN_REASON, on_trainer_pin


LABEL = fixtures.LABEL
HARNESS_SHA = "13069649488ea33d823bef53f39f6d2fac30fa59"


def warmstart_worker(rank, port, root, phase):
    root = Path(root)
    events = {"initializations": [], "optimizers": [], "scheduler_steps": []}
    original_initialize = warmstart.initialize_adapters
    original_optimizer = torch.optim.AdamW
    original_schedule = ddp_core.schedule_lr
    original_persist = ddp_training.persist_admission
    original_train = ddp_training.train
    original_wrap = fsdp_training.wrap_model
    parallel = load_json(root / "protocol.json")["training"].get("parallel", "ddp")

    def train(*args, **kwargs):
        return original_train(*args, **{**kwargs, "parallel": parallel})

    def wrap(model, parameters, process_group, device):
        assert len(events["initializations"]) == 1
        assert not events["optimizers"]
        return original_wrap(model, parameters, process_group, torch.device("cpu"), mixed_precision=False)

    def initialize(model, report, protocol, protocol_path, **kwargs):
        targets = sorted({name.removeprefix("base_model.model.").__getattribute__("sp" "lit")(".lora_")[0]
                          for name, parameter in model.named_parameters() if parameter.requires_grad})
        model.peft_config["default"].base_model_name_or_path = MODEL_PINS[protocol["student"]]["repo_id"]
        result = original_initialize(model, {**report, "targets": {"all": targets}}, protocol, protocol_path, **kwargs)
        if kwargs["resume_from"] is None:
            expected = load_file(str(root / "r1813_synthetic/publication" / ("adapter-" + LABEL) / "adapter_model.safetensors"))
            actual = get_peft_model_state_dict(model, save_embedding_layers=False)
            assert set(expected) == set(actual)
            assert all(torch.equal(expected[name], actual[name]) for name in expected)
        events["initializations"].append({"applied": result["initialization_applied"],
                                           "identity": result["initialization"], "before_optimizer": not events["optimizers"]})
        return result

    def optimizer(*args, **kwargs):
        result = original_optimizer(*args, **kwargs)
        events["optimizers"].append({"state_empty": not result.state, "lr": result.param_groups[0]["lr"]})
        return result

    def schedule(step, total_steps, settings, base_lr=None):
        events["scheduler_steps"].append(step)
        return original_schedule(step, total_steps, settings, base_lr)

    def persist(rank, probes, store, header):
        return original_persist(rank, probes, store, {**header, "synthetic": True})

    with ExitStack() as stack:
        stack.enter_context(patch.object(ddp_training, "train", side_effect=train))
        stack.enter_context(patch.object(fsdp_training, "wrap_model", side_effect=wrap))
        stack.enter_context(patch.object(warmstart, "initialize_adapters", side_effect=initialize))
        stack.enter_context(patch.object(torch.optim, "AdamW", side_effect=optimizer))
        stack.enter_context(patch.object(ddp_core, "schedule_lr", side_effect=schedule))
        stack.enter_context(patch.object(ddp_training, "persist_admission", side_effect=persist))
        if phase.startswith("resume"):
            stack.enter_context(patch.object(warmstart, "prepare_identity", side_effect=AssertionError("Resume reopened parent")))
        checkpoint_fixtures.training_worker(rank, port, root, phase)
    (root / f"warmstart_{phase}_rank{rank}.json").write_bytes(canonical_bytes(events))


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
@unittest.skipUnless(on_trainer_pin(), PIN_REASON)
class WarmstartResumeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = fixtures.WarmstartTests()
        fixture.student = "onethinker"
        fixture.setUp()
        try:
            cls.root = fixture.root
            cls.settings = ddp_config.normalize_training_config({"world_size": 2, "epochs": 2, "lora_rank": 2,
                        "lora_alpha": 4, "lora_dropout": 0.2, "learning_rate": 5e-5,
                        "parallel": getattr(cls, "parallel", "ddp")}, "onethinker")
            fixture.settings = cls.settings
            fixture.model.peft_config["default"].lora_dropout = 0.2
            fixture.parent_protocol["training"] = cls.settings
            fixture.model.save_pretrained(fixture.adapter, safe_serialization=True, save_embedding_layers=False)
            fixture.reseal()
            cls.identity = fixture.identify()
            division = tag({"schema": "provisional-whole-scene-division-v1", "train_candidate_qids": [str(index) for index in range(35)],
                         "heldout_qids": ["heldout"], "synthetic": True}, LABEL)
            control = ddp_config.normalize_run_control({"checkpoint_every_steps": 1})
            protocol = tag({"schema": "provisional-student-diagnostic-protocol-v1", "training": cls.settings,
                    "training_sha256": digest_json(cls.settings), "protocol_version": ddp_config.VERSION,
                    "run_control": control, "run_control_sha256": digest_json(control), "student": fixture.student,
                    "base": fixture.base, "base_sha256": digest_json(fixture.base), "versions": {}, "runtime": [],
                    "PROVISIONAL_DIVISION_SHA": digest_json(division), "rgb": diagnostic_data.RGB, "division": division,
                    "selection_frozen_before_evaluation": True, "init_adapter_identity": cls.identity,
                    "init_adapter_sha256": digest_json(cls.identity)}, LABEL)
            (cls.root / "protocol.json").write_bytes(canonical_bytes(protocol))
            (cls.root / "protocol.init_adapter.json").write_bytes(canonical_bytes({"publication": str(fixture.parent),
                                                           "init_adapter_sha256": digest_json(cls.identity)}))
            (cls.root / "manifest.json").write_bytes(canonical_bytes({"synthetic": True}))
            torch.save({"parent_optimizer_must_not_load": True}, fixture.parent / "optimizer.pt")
        finally:
            fixture.doCleanups()
        for phase in ("reference", "partial", "resume_refused", "resume"):
            if phase == "resume_refused":
                quarantine = cls.root / "_quarantine"
                quarantine.mkdir()
                (cls.root / "r1813_synthetic/publication").rename(quarantine / "parent_publication")
            (cls.root / f"{phase}_lease.json").write_bytes(canonical_bytes({"attempt": phase, "synthetic": True}))
            checkpoint_fixtures.launch_workers(warmstart_worker, str(cls.root), phase)

    test_actual_train_loop_restores_adapters_scheduler_and_scientific_metrics = (
        checkpoint_fixtures.TrainerResumeIntegrationTests.test_actual_train_loop_restores_adapters_scheduler_and_scientific_metrics)
    test_resume_requires_fresh_leases_before_model_load = (
        checkpoint_fixtures.TrainerResumeIntegrationTests.test_resume_requires_fresh_leases_and_collective_admission_before_model_load)

    def test_parent_is_loaded_before_fresh_optimizer_and_schedule_step_zero(self):
        for rank in range(2):
            for phase in ("reference", "partial"):
                events = load_json(self.root / f"warmstart_{phase}_rank{rank}.json")
                self.assertEqual(events["initializations"], [{"applied": True, "identity": self.identity, "before_optimizer": True}])
                self.assertEqual(events["optimizers"], [{"state_empty": True, "lr": 5e-5}])
                self.assertEqual(events["scheduler_steps"][0], 0)
            events = load_json(self.root / f"warmstart_resume_rank{rank}.json")
            self.assertEqual(events["initializations"], [{"applied": False, "identity": self.identity, "before_optimizer": True}])
            self.assertEqual(events["scheduler_steps"], [1, 2, 3])
        self.assertFalse((self.root / "r1813_synthetic/publication").exists())

    def test_checkpoint_and_publication_preserve_parent_and_refuse_another_parent(self):
        expected_hash = digest_json(self.identity)
        for name in ("reference/run.json", "interrupted/run.json", "interrupted/training_result.json",
                     "published/reference/PUBLISHED.json", "published/resume/PUBLISHED.json", "published/resume/protocol.json"):
            value = load_json(self.root / name)
            self.assertEqual(value["init_adapter_identity"], self.identity)
            self.assertEqual(value["init_adapter_sha256"], expected_hash)
        header = load_json(self.root / "interrupted/run.json")
        checkpoint = self.root / "interrupted/checkpoints/step_4"
        identity = ddp_checkpoints.run_identity(header)
        self.assertEqual(identity["init_adapter_sha256"], expected_hash)
        self.assertEqual(ddp_checkpoints.read_checkpoint(checkpoint, identity)["step"], 4)
        with self.assertRaisesRegex(ValueError, "init_adapter_sha256 mismatch"):
            ddp_checkpoints.read_checkpoint(checkpoint, {**identity, "init_adapter_sha256": "f" * 64})
        census = load_json(self.root / "published/resume/SHA256_MANIFEST.json")["files"]
        self.assertIn("init_adapter_source.json", census)
        receipt = load_json(self.root / "published/resume/PUBLISHED.json")
        self.assertEqual(receipt["resumed_from"]["step"], 1)
        self.assertTrue(receipt["synthetic"])

    def test_unmodified_harness_validates_publication_and_matching_base(self):
        harness = Path(os.environ.get("WARMSTART_HARNESS_ROOT", REPO / "artifacts/warmstart_harness_1306964"))
        if not (harness / "student_pilot/orchard_eval/contracts.py").is_file():
            self.skipTest("set WARMSTART_HARNESS_ROOT to the unchanged 1306964 harness checkout")
        self.assertEqual(subprocess.check_output(["git", "-C", str(harness), "rev-parse", "HEAD"], text=True).strip(), HARNESS_SHA)
        program = '''
import copy, json, sys
from pathlib import Path
from student_pilot.orchard_eval import contracts, pairing, protocol
root = Path(sys.argv[1])
label = sys.argv[2]
receipt = contracts.load_json(root / "PUBLISHED.json")
adapter = contracts.validate_adapter("distilled", "onethinker", root / receipt["adapter_directory"],
    root / "PUBLISHED.json", contracts.DEFAULT_CONFIG, allow_synthetic=True, provisional_diagnostic=label)
assert contracts.validate_adapter("base", "onethinker", None, None, contracts.DEFAULT_CONFIG,
    provisional_diagnostic=label) is None
assert receipt["init_adapter_identity"]["parent_run"] == "r1813_synthetic"
manifest = contracts.binding(root.parent.parent / "manifest.json")
runtime = [contracts.binding(Path.cwd() / name) for name in (*protocol.SOURCE_CLOSURE, *protocol.AUXILIARY_FILES)]
base = {"variant": "base", "adapter": None, "benchmark": "vsibench_answerable500", "paper_cell": False,
        "mock": True, "ordered_ids": ["synthetic"], "config": contracts.DEFAULT_CONFIG,
        "model_identity": dict(receipt["base"]), "model_snapshot": {"synthetic": True, **receipt["base"]},
        "decoding": {}, "effective_generation_config": {"do_sample": False}, "eos_token_ids": [2], "versions": {},
        "input_audits_sha256": "a" * 64, "runtime": [*runtime, manifest], "generation_manifest": manifest,
        "answer_format_instruction": "synthetic pairing fixture", "config_sha256": contracts.digest(contracts.DEFAULT_CONFIG),
        "decode_execution": {"batch_size": 1, "mode": "single", "identity_certificate": None, "protocol_controls": {}},
        **contracts.provisional_flags(label)}
distilled = copy.deepcopy(base)
distilled.update(variant="distilled", adapter=adapter)
distilled["model_identity"]["adapter_manifest_sha256"] = contracts.digest({key: adapter[key]["sha256"] for key in ("config", "weights")})
paired = pairing.require_pair(base, distilled, label)
assert paired["base"]["protocol_sha256"] == paired["distilled"]["protocol_sha256"]
wrong_base = copy.deepcopy(base)
wrong_base["model_identity"]["revision"] = "f" * 40
try:
    pairing.require_pair(wrong_base, distilled, label)
except ValueError:
    pass
else:
    raise AssertionError("Different base was paired")
print(json.dumps({"status": "WARMSTART_PUBLICATION_ACCEPTED", "tensor_count": adapter["tensor_count"],
                  "parent_identity_sha256": receipt["init_adapter_sha256"], "base_validated": True,
                  "paired_protocol_sha256": paired["base"]["protocol_sha256"], "wrong_base_refused": True}))
'''
        result = subprocess.run([sys.executable, "-B", "-c", program, str(self.root / "published/resume"), LABEL],
                                cwd=harness, env={**os.environ, "PYTHONPATH": str(harness), "STUDENT_ORCHARD": "0"},
                                capture_output=True, text=True, timeout=300)
        (self.root / "harness_validation.stdout").write_text(result.stdout)
        (self.root / "harness_validation.stderr").write_text(result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "WARMSTART_PUBLICATION_ACCEPTED")


class WarmstartFSDPResumeIntegrationTests(WarmstartResumeIntegrationTests):
    parallel = "fsdp"


if __name__ == "__main__":
    unittest.main()
