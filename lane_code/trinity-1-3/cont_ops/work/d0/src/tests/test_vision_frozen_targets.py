"""CPU checks for the frozen-vision LoRA targets option; the default option keeps its bytes."""
import copy
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import torch
import torch.distributed as dist
from peft import get_peft_model_state_dict
from safetensors.torch import load_file

from student_pilot import ddp_checkpoints as checkpoints
from student_pilot import ddp_config, ddp_core, fsdp_training, provisional_data, storage, warmstart
from student_pilot.adapters import frozen_adapters, trainable_groups, trainable_targets
from student_pilot.common import canonical_bytes, digest_json, load_json
from student_pilot.provisional import tag
from tests import test_ddp_checkpoints as checkpoint_fixtures
from tests import test_ddp_models as native_fixtures
from tests import test_fsdp as fsdp_fixtures
from tests import test_sft_warmstart as warmstart_fixtures
from tests.test_ddp import TinyAdapter


BASELINE = "b4b2979d59b19bfc613fdf38b4fa1c6949b69ae3"
LABEL = warmstart_fixtures.LABEL
DEFAULT = ddp_config.DEFAULTS["targets"]
FROZEN = ddp_config.VISION_FROZEN_TARGETS
STUDENTS = ("onethinker", "qwen35", "qwen36_27b")
DERIVED = ("targets", "group_parameters", "trainable_parameters", "frozen_group_parameters")


def module_name(name):
    return name.removeprefix("base_model.model.").partition(".lora_")[0]


def freeze_vision(model, groups, seed=5):
    """Give every LoRA tensor parent-like values, then freeze vision as attach_ddp_adapters does."""
    generator = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for tensors in groups.values():
            for _, parameter in tensors:
                parameter.copy_(torch.randn(parameter.shape, generator=generator) * 0.05)
    for _, parameter in groups["vision"]:
        parameter.requires_grad_(False)
    return {"targets": {group: sorted({module_name(name) for name, _ in tensors}) for group, tensors in groups.items()},
            "frozen_group_parameters": {"vision": sum(parameter.numel() for _, parameter in groups["vision"])}}


class FrozenTargetsConfigTests(unittest.TestCase):
    def test_frozen_option_is_accepted_with_explicit_frozen_accounting(self):
        for student in STUDENTS:
            counts = ddp_config.parameter_counts(student, 32)
            for parallel in ("ddp", "fsdp"):
                with self.subTest(student=student, parallel=parallel):
                    default = ddp_config.normalize_training_config({"parallel": parallel}, student)
                    settings = ddp_config.normalize_training_config({"parallel": parallel, "targets": FROZEN}, student)
                    self.assertEqual(ddp_config.frozen_groups(settings), ("vision",))
                    self.assertEqual(settings["group_parameters"], {"text": counts["text"], "mergers": counts["mergers"]})
                    self.assertEqual(settings["frozen_group_parameters"], {"vision": counts["vision"]})
                    self.assertEqual(settings["trainable_parameters"], counts["text"] + counts["mergers"])
                    self.assertEqual(settings["trainable_parameters"] + counts["vision"], default["trainable_parameters"])
                    self.assertEqual({key: value for key, value in settings.items() if key not in DERIVED},
                                     {key: value for key, value in default.items() if key not in DERIVED})
                    self.assertEqual(settings, ddp_config.normalize_training_config(settings, student))
                    self.assertNotEqual(digest_json(settings), digest_json(default))

    def test_other_targets_and_inconsistent_accounting_are_refused(self):
        for value in ("exact_text_attention_mlp_mergers", "vision_frozen", FROZEN.upper(), "", None, 0,
                      [FROZEN], {FROZEN: True}):
            with self.subTest(targets=value), self.assertRaisesRegex(ValueError, "targets"):
                ddp_config.normalize_training_config({"targets": value}, "qwen35")
        frozen = ddp_config.normalize_training_config({"targets": FROZEN}, "qwen35")
        default = ddp_config.normalize_training_config({}, "qwen35")
        for key, value in (("group_parameters", default["group_parameters"]),
                           ("trainable_parameters", default["trainable_parameters"]),
                           ("frozen_group_parameters", {}), ("frozen_group_parameters", {"vision": 1})):
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, "Architecture-derived"):
                ddp_config.normalize_training_config({**frozen, key: value}, "qwen35")
        for value in ({**default, "frozen_group_parameters": frozen["frozen_group_parameters"]},
                      {**frozen, "targets": DEFAULT}):
            with self.subTest(value=value["targets"]), self.assertRaisesRegex(ValueError, "frozen_group_parameters"):
                ddp_config.normalize_training_config(value, "qwen35")

    def test_default_settings_bytes_and_digests_match_the_baseline_commit(self):
        baseline = warmstart_fixtures.reference_module("ddp_config", BASELINE)
        self.assertEqual(canonical_bytes(ddp_config.DEFAULTS), canonical_bytes(baseline.DEFAULTS))
        # The batch-options branch moves effective_batch_size out of FIXED (validated against BATCH_OPTIONS instead).
        self.assertEqual(ddp_config.FIXED, tuple(key for key in baseline.FIXED if key != "effective_batch_size"))
        for student in STUDENTS:
            for parallel in (None, "ddp", "fsdp"):
                for extra in ({}, {"targets": DEFAULT}, {"seed": 18, "checkpoint_every_steps": 1},
                              {"world_size": 16, "epochs": 1, "lora_rank": 128, "lora_alpha": 256, "max_steps": 3}):
                    value = {**extra, **({"parallel": parallel} if parallel else {})}
                    with self.subTest(student=student, value=value):
                        before = baseline.normalize_training_config(value, student)
                        after = ddp_config.normalize_training_config(value, student)
                        self.assertEqual(canonical_bytes(after), canonical_bytes(before))
                        self.assertEqual(digest_json(after), digest_json(before))
                        self.assertEqual(after, ddp_config.normalize_training_config(after, student))
            with self.assertRaisesRegex(ValueError, "targets"):
                baseline.normalize_training_config({"targets": FROZEN}, student)

    def test_frozen_protocol_requires_a_warm_start_parent(self):
        frozen = ddp_config.normalize_training_config({"targets": FROZEN}, "qwen35")
        default = ddp_config.normalize_training_config({}, "qwen35")
        with self.assertRaisesRegex(ValueError, "warm-start parent"):
            ddp_config.require_frozen_parent({"training": frozen})
        ddp_config.require_frozen_parent({"training": frozen, "init_adapter_identity": {}})
        ddp_config.require_frozen_parent({"training": default})
        protocol = tag({"student": "qwen35", "training": frozen, "training_sha256": digest_json(frozen),
                        "protocol_version": ddp_config.VERSION}, LABEL)
        with self.assertRaisesRegex(ValueError, "warm-start parent"):
            ddp_config.validate_training_protocol(protocol, LABEL)

    def test_publication_must_record_exactly_the_frozen_lora_parameters(self):
        control = ddp_config.normalize_run_control({})
        for targets in (FROZEN, DEFAULT):
            settings = ddp_config.normalize_training_config({"world_size": 2, "epochs": 1, "targets": targets}, "qwen35")
            result = tag({"protocol_version": ddp_config.VERSION, "training_sha256": digest_json(settings),
                          "settings": settings, "student": "qwen35", "adapter_parameters": settings["trainable_parameters"],
                          "schema": "completed-provisional-diagnostic-training-v1", "status": "TRAINED",
                          "frozen_base_unchanged": True, "completed_epochs": 1, "run_control": control,
                          "run_control_sha256": digest_json(control), "dataset_counts": {"training_rows": 64},
                          "realized": {"optimizer_steps": 2, "source_rows": 64, "training_rows": 64, "epoch_padding_rows": 0},
                          "rank_checks": [{"rank": rank, "frozen_base_unchanged": True} for rank in range(2)]}, LABEL)
            if targets == FROZEN:
                result["frozen_adapter_parameters"] = settings["frozen_group_parameters"]
            with patch.object(ddp_config, "validate_training_protocol", return_value=settings):
                self.assertEqual(ddp_config.validate_training_result(result, {"student": "qwen35"}, LABEL), settings)
                for value in ({}, {"vision": 1}, ddp_config.parameter_counts("qwen35", 32), None):
                    changed = {key: item for key, item in result.items() if key != "frozen_adapter_parameters"}
                    if value is not None:
                        changed["frozen_adapter_parameters"] = value
                    if changed == result:
                        continue
                    with self.subTest(targets=targets, value=value), self.assertRaisesRegex(ValueError, "frozen LoRA"):
                        ddp_config.validate_training_result(changed, {"student": "qwen35"}, LABEL)


class FrozenTargetsAdapterTests(unittest.TestCase):
    def test_meta_students_freeze_vision_lora_and_the_optimizer_excludes_it(self):
        from accelerate import init_empty_weights
        from transformers import AutoConfig
        from student_pilot.adapters import attach_ddp_adapters
        from student_pilot.students import get_student, model_class

        for student in ("onethinker", "qwen35"):
            with self.subTest(student=student):
                config = AutoConfig.from_pretrained(get_student(student)["snapshot"], local_files_only=True)
                settings = ddp_config.normalize_training_config({"targets": FROZEN}, student)
                with init_empty_weights(include_buffers=True):
                    model, report = attach_ddp_adapters(model_class(student)(config), settings)
                self.assertEqual(set(report["targets"]), {"text", "vision", "mergers"})
                for key in ("group_parameters", "frozen_group_parameters", "trainable_parameters"):
                    self.assertEqual(report[key], settings[key])
                groups = trainable_groups(model, trainable_targets(report))
                self.assertEqual(set(groups), {"text", "mergers"})
                frozen = frozen_adapters(model, report)
                self.assertEqual(len(frozen), 2 * len(report["targets"]["vision"]))
                self.assertEqual({module_name(name) for name, _ in frozen}, set(report["targets"]["vision"]))
                self.assertEqual(sum(p.numel() for _, p in frozen), settings["frozen_group_parameters"]["vision"])
                self.assertTrue(all(not p.requires_grad and p.dtype == torch.float32 for _, p in frozen))
                parameters = [parameter for group in groups.values() for _, parameter in group]
                self.assertEqual(sum(p.numel() for p in parameters), settings["trainable_parameters"])
                optimizer = torch.optim.AdamW(parameters, lr=settings["learning_rate"], foreach=False)
                optimized = {id(p) for group in optimizer.param_groups for p in group["params"]}
                self.assertEqual(optimized, {id(p) for p in model.parameters() if p.requires_grad})
                self.assertFalse(optimized & {id(p) for _, p in frozen})
                # A raw-checkpoint loader that expects every group to train refuses instead of loading zeros.
                with self.assertRaisesRegex(ValueError, "exactly two trainable"):
                    trainable_groups(model, report["targets"])
                default = ddp_config.normalize_training_config({}, student)
                with init_empty_weights(include_buffers=True):
                    model, report = attach_ddp_adapters(model_class(student)(config), default)
                self.assertNotIn("frozen_group_parameters", report)
                self.assertEqual(trainable_targets(report), report["targets"])
                self.assertEqual(frozen_adapters(model, report), [])
                self.assertEqual(report["group_parameters"], default["group_parameters"])
                self.assertEqual(report["trainable_parameters"], default["trainable_parameters"])

    def test_wrap_ignores_frozen_adapters_only_when_given(self):
        model, groups, _ = fsdp_fixtures.fixture("qwen35")
        report = freeze_vision(model, groups)
        params = [p for group in trainable_groups(model, trainable_targets(report)).values() for _, p in group]
        frozen = [p for _, p in frozen_adapters(model, report)]
        with patch.object(fsdp_training, "FSDP", return_value=model) as wrapper, \
                patch.object(dist, "broadcast") as broadcast:
            fsdp_training.wrap_model(model, params, None, torch.device("cpu"), frozen_adapters=frozen)
        self.assertEqual([id(p) for p in wrapper.call_args.kwargs["ignored_states"]], [id(p) for p in params + frozen])
        self.assertEqual(broadcast.call_count, len(params) + len(frozen))
        with self.assertRaisesRegex(ValueError, "allowlist"):
            fsdp_training.wrap_model(model, params + frozen, None, torch.device("cpu"))
        frozen[0].requires_grad_(True)
        with self.assertRaisesRegex(ValueError, "must not require gradients"):
            fsdp_training.wrap_model(model, params + [frozen[0]], None, torch.device("cpu"), frozen_adapters=frozen)

    def test_fsdp_keeps_frozen_fp32_vision_lora_out_of_bf16_flat_parameters(self):
        import torch.testing._internal.distributed.fake_pg  # Registers the socket-free backend.
        dist.init_process_group("fake", store=dist.HashStore(), rank=0, world_size=1)
        try:
            for student in ("onethinker", "qwen35"):
                with self.subTest(student=student):
                    model, groups, rows = fsdp_fixtures.fixture(student, bf16=True)
                    report = freeze_vision(model, groups)
                    # Left to FSDP, the frozen FP32 vision LoRA would share a flat parameter with BF16 base weights.
                    clone = copy.deepcopy(model)
                    with self.assertRaisesRegex(ValueError, "uniform dtype"):
                        fsdp_training.wrap_model(clone, [p for p in clone.parameters() if p.requires_grad],
                                                 dist.group.WORLD, torch.device("cpu"))
                    reference = copy.deepcopy(model)
                    reference_parameters = dict(reference.named_parameters())
                    trainable = trainable_groups(model, trainable_targets(report))
                    params = [p for group in trainable.values() for _, p in group]
                    frozen = frozen_adapters(model, report)
                    before = {name: p.detach().clone() for name, p in frozen}
                    wrapped = fsdp_training.wrap_model(model, params, dist.group.WORLD, torch.device("cpu"),
                                                       frozen_adapters=[p for _, p in frozen])
                    # Publication gathers the ignored frozen LoRA unchanged in FP32 (before a size-one forward frees views).
                    state = fsdp_training.publication_state(wrapped)
                    for name, value in before.items():
                        self.assertEqual(state[name].dtype, torch.float32)
                        self.assertTrue(torch.equal(state[name], value))
                    fingerprints = fsdp_training.frozen_shard_fingerprints(wrapped)
                    recorded = {name: value for name, value in fingerprints.items() if ".lora_" in name}
                    self.assertEqual(len(recorded), len(frozen))
                    self.assertEqual(sorted(value[:2] for value in recorded.values()),
                                     sorted((tuple(p.shape), "torch.float32") for _, p in frozen))
                    self.assertTrue(all(value[1] == "torch.bfloat16" for name, value in fingerprints.items()
                                        if ".lora_" not in name))
                    context = lambda: torch.autocast("cpu", dtype=torch.bfloat16)
                    expected = ddp_core.backward_batch(reference, rows[0], [1], 1, 1, forward_context=context())
                    actual = ddp_core.backward_batch(wrapped, rows[0], [1], 1, 1, forward_context=context())
                    torch.testing.assert_close(actual, expected, rtol=0, atol=1e-5)
                    for group in trainable.values():
                        for name, parameter in group:
                            torch.testing.assert_close(parameter.grad, reference_parameters[name].grad, rtol=0, atol=1e-5)
                    torch.optim.AdamW(params, lr=0.01, foreach=False).step()
                    # A size-one group runs NO_SHARD and frees base views after forward; the ignored LoRA stays put.
                    after = fsdp_training.frozen_shard_fingerprints(wrapped)
                    self.assertEqual({name: value for name, value in after.items() if ".lora_" in name}, recorded)
                    for name, parameter in frozen:
                        self.assertIsNone(parameter.grad)
                        self.assertIsNone(reference_parameters[name].grad)
                        self.assertFalse(parameter.requires_grad)
                        self.assertTrue(torch.equal(parameter, before[name]))
        finally:
            dist.destroy_process_group()


class FrozenTargetsWarmstartTests(unittest.TestCase):
    def setUp(self):
        self.fixture = warmstart_fixtures.WarmstartTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.raw = {key: self.fixture.settings[key] for key in
                    ("world_size", "epochs", "lora_rank", "lora_alpha", "lora_dropout", "learning_rate")}
        self.frozen = ddp_config.normalize_training_config({**self.raw, "targets": FROZEN}, self.fixture.student)

    def test_default_parent_initializes_a_frozen_child_and_resume_reloads_frozen_groups(self):
        fixture = self.fixture
        identity = warmstart.prepare_identity(fixture.parent, fixture.student, self.frozen, fixture.base, LABEL, fixture.request)
        self.assertEqual(identity, fixture.identify())
        protocol = {**fixture.protocol(), "training": self.frozen}
        parent_state = load_file(str(fixture.adapter / "adapter_model.safetensors"))
        child, groups, _, _ = native_fixtures.NativeMultimodalBatchTests.fixture(fixture.student)
        report = freeze_vision(child, groups)
        loaded = warmstart.initialize_adapters(child, report, protocol, fixture.root / "protocol.json", init_adapter=fixture.parent)
        self.assertTrue(loaded["initialization_applied"])
        for name, value in get_peft_model_state_dict(child, save_embedding_layers=False).items():
            torch.testing.assert_close(value, parent_state[name], rtol=0, atol=0)
        frozen = frozen_adapters(child, report)
        self.assertEqual({module_name(name) for name, p in child.named_parameters() if p.requires_grad},
                         set(report["targets"]["text"]) | set(report["targets"]["mergers"]))
        with torch.no_grad():
            for _, parameter in frozen:
                parameter.zero_()
        resumed = warmstart.initialize_adapters(child, report, protocol, fixture.root / "protocol.json",
                                                resume_from=fixture.root / "checkpoint", init_adapter=fixture.parent)
        self.assertFalse(resumed["initialization_applied"])
        self.assertEqual(resumed["frozen_groups_reloaded_from_parent"], ["vision"])
        for name, value in get_peft_model_state_dict(child, save_embedding_layers=False).items():
            torch.testing.assert_close(value, parent_state[name], rtol=0, atol=0)
        self.assertEqual(len(frozen_adapters(child, report)), len(frozen))

    def test_parent_with_an_unknown_targets_option_is_still_refused(self):
        fixture = self.fixture
        fixture.parent_protocol["training"] = {**fixture.parent_protocol["training"], "targets": "exact_text_attention_mlp_only"}
        fixture.reseal()
        for training in (fixture.settings, self.frozen):
            with self.subTest(targets=training["targets"]), self.assertRaisesRegex(ValueError, "LoRA training settings"):
                fixture.identify(settings=training)

    def test_prepare_refuses_a_frozen_config_without_a_parent(self):
        fixture = self.fixture
        index, _ = fixture.candidates()
        config = fixture.document("orphan/config.json", {**self.raw, "targets": FROZEN})
        with self.assertRaisesRegex(ValueError, "warm-start parent"):
            provisional_data.prepare_protocol(index, fixture.root / "orphan/protocol.json", LABEL, fixture.student,
                                              training_config=config, scratch_root=fixture.root)
        self.assertFalse((fixture.root / "orphan/protocol.json").exists())
        config = fixture.document("child/config.json", {**self.raw, "targets": FROZEN, "init_adapter": fixture.request})
        fixture.document("child/config.init_adapter.json", {"publication": str(fixture.parent)})
        output = fixture.root / "child/protocol.json"
        provisional_data.prepare_protocol(index, output, LABEL, fixture.student, training_config=config, scratch_root=fixture.root)
        protocol = provisional_data.load_protocol(output, LABEL)
        self.assertEqual(protocol["training"], self.frozen)
        self.assertEqual(protocol["init_adapter_identity"], fixture.identify())
        self.assertEqual(ddp_config.validate_training_protocol(protocol, LABEL), self.frozen)


class FrozenTargetsCheckpointTests(unittest.TestCase):
    advance = checkpoint_fixtures.CheckpointContractTests.advance
    checkpoint = checkpoint_fixtures.CheckpointContractTests.checkpoint

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="frozen_targets_checkpoint_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        checkpoint_fixtures.storage_patches(self.stack, self.root)

    def run_for(self, targets, name):
        self.settings = ddp_config.normalize_training_config({"world_size": 2, "epochs": 3, "targets": targets}, "onethinker")
        self.config = checkpoint_fixtures.config_for(self.settings, self.root)
        self.store = storage.RunArtifacts(self.root / name, self.config, self.root)
        self.header = self.store.record(checkpoint_fixtures.header_for(self.settings, self.config))
        self.store.write("run.json", self.header)
        self.store.write("batch_plan.json", {"microbatch_size": 2, "scheduler_steps": 6})
        (self.store.root / "metrics.jsonl").write_text("")
        (self.store.root / "train.log").write_text("synthetic CPU training\n")
        torch.manual_seed(17)
        model = TinyAdapter()
        self.adapters = {key: parameter for key, parameter in model.named_parameters() if parameter.requires_grad}
        self.optimizer = torch.optim.AdamW(self.adapters.values(), lr=self.settings["learning_rate"], foreach=False)
        self.step = 0
        return self.checkpoint(), self.header

    def test_checkpoint_records_the_option_and_resume_refuses_a_change(self):
        frozen_directory, frozen_header = self.run_for(FROZEN, "frozen")
        default_directory, default_header = self.run_for(DEFAULT, "default")
        frozen_identity = checkpoints.run_identity(frozen_header)
        default_identity = checkpoints.run_identity(default_header)
        baseline = warmstart_fixtures.reference_module("ddp_checkpoints", BASELINE)
        self.assertEqual(canonical_bytes(default_identity), canonical_bytes(baseline.run_identity(default_header)))
        self.assertNotIn("targets", default_identity)
        self.assertEqual(frozen_identity["targets"], FROZEN)
        self.assertEqual(load_json(frozen_directory / "checkpoint.json")["identity"], frozen_identity)
        self.assertEqual(checkpoints.read_checkpoint(frozen_directory, frozen_identity)["step"], 1)
        self.assertEqual(checkpoints.read_checkpoint(default_directory, default_identity)["step"], 1)
        for directory, identity in ((frozen_directory, default_identity), (default_directory, frozen_identity)):
            with self.subTest(directory=directory.name), self.assertRaisesRegex(ValueError, "targets option"):
                checkpoints.read_checkpoint(directory, identity)


if __name__ == "__main__":
    unittest.main()
