import ast
import copy
import json
import math
import random
import subprocess
import unittest
from unittest.mock import patch

from student_pilot import ddp_config, ddp_core, provisional_data
from student_pilot.common import REPO, canonical_bytes, digest_json, load_json
from tests import test_sft_warmstart as fixtures
from tests.test_fsdp import SOCKETS


class SeedConfigTests(unittest.TestCase):
    def test_default_seed_bytes_match_warmstart_baseline(self):
        baseline = fixtures.reference_module("ddp_config", "5b23b728c1a2b2b631777eab0c8862d2aa2d0dc3")
        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for parallel in ("ddp", "fsdp"):
                with self.subTest(student=student, parallel=parallel):
                    for value in ({}, {"seed": 17}, {"checkpoint_every_steps": 1},
                                  {"epochs": 1, "max_microbatch_size": 4}):
                        config = {**value, "parallel": parallel}
                        current = ddp_config.normalize_training_config(config, student)
                        self.assertEqual(current["seed"], 17)
                        self.assertEqual(canonical_bytes(current),
                                         canonical_bytes(baseline.normalize_training_config(config, student)))
                        self.assertEqual(current, ddp_config.normalize_training_config({**config, "seed": 17}, student))

    def test_seed18_and_integer_boundaries_are_normalized_and_hashed(self):
        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for parallel in ("ddp", "fsdp"):
                default = ddp_config.normalize_training_config({"parallel": parallel}, student)
                for seed in (0, 18, 19, 2**31 - 1):
                    with self.subTest(student=student, parallel=parallel, seed=seed):
                        settings = ddp_config.normalize_training_config({"parallel": parallel, "seed": seed}, student)
                        self.assertEqual(settings, {**default, "seed": seed})
                        self.assertEqual(settings, ddp_config.normalize_training_config(settings, student))
                        self.assertNotEqual(digest_json(settings), digest_json(default))

    def test_out_of_range_and_noninteger_seeds_are_refused(self):
        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for parallel in ("ddp", "fsdp"):
                for seed in (-1, 2**31, True, False, 17.0, 18.0, "18", None, [], {},
                             float("nan"), float("inf"), -float("inf")):
                    with self.subTest(student=student, parallel=parallel, seed=seed), self.assertRaisesRegex(ValueError, "seed"):
                        ddp_config.normalize_training_config({"parallel": parallel, "seed": seed}, student)

    def test_warmstart_protocol_records_seed18_without_changing_parent_or_division(self):
        fixture = fixtures.WarmstartTests()
        fixture.setUp()
        try:
            index, _ = fixture.candidates()
            protocols = []
            for seed in (17, 18):
                config = fixture.document(f"seed{seed}/config.json", {**fixture.settings, "parallel": "fsdp",
                                          "seed": seed, "init_adapter": fixture.request})
                fixture.document(f"seed{seed}/config.init_adapter.json", {"publication": str(fixture.parent)})
                output = fixture.root / f"seed{seed}/protocol.json"
                provisional_data.prepare_protocol(index, output, fixtures.LABEL, fixture.student,
                                                  training_config=config, scratch_root=fixture.root)
                protocol = provisional_data.load_protocol(output, fixtures.LABEL)
                self.assertEqual(protocol["training"]["seed"], seed)
                self.assertEqual(protocol["training_sha256"], digest_json(protocol["training"]))
                self.assertEqual(ddp_config.validate_training_protocol(protocol, fixtures.LABEL), protocol["training"])
                self.assertEqual(protocol["init_adapter_identity"], fixture.identify())
                protocols.append(protocol)
            for field in ("division", "PROVISIONAL_DIVISION_SHA", "init_adapter_identity", "init_adapter_sha256"):
                self.assertEqual(protocols[0][field], protocols[1][field], field)
            self.assertNotEqual(protocols[0]["training_sha256"], protocols[1]["training_sha256"])
            changed = copy.deepcopy(protocols[1])
            changed["training"]["seed"] = 17
            with self.assertRaisesRegex(ValueError, "training hash changed"):
                ddp_config.validate_training_protocol(changed, fixtures.LABEL)
        finally:
            fixture.doCleanups()


class SeedBatchTests(unittest.TestCase):
    def test_configured_seed_changes_epoch_order_and_preserves_padding(self):
        for seed in (17, 18, 19):
            settings = ddp_config.normalize_training_config({"seed": seed}, "qwen35")
            for epoch in range(settings["epochs"]):
                with self.subTest(seed=seed, epoch=epoch):
                    batches = list(ddp_core.global_batches(67, epoch, settings["effective_batch_size"], settings["seed"]))
                    order = [index for batch in batches for index in batch["indices"][:batch["source_rows"]]]
                    expected = list(range(67))
                    random.Random(seed + epoch).shuffle(expected)
                    self.assertEqual(order, expected)
                    self.assertEqual(batches[-1]["indices"][3:], expected[:29])
                    if seed != 17:
                        self.assertNotEqual(batches, list(ddp_core.global_batches(67, epoch)))

    def test_saved_batch_plan_hashes_configured_seed_and_preserves_default_bytes(self):
        source = (REPO / "student_pilot/ddp_training.py").read_text()
        baseline = subprocess.check_output(["git", "show",
            "5b23b728c1a2b2b631777eab0c8862d2aa2d0dc3:student_pilot/ddp_training.py"], cwd=REPO, text=True)

        def plan(text, settings, row_count):
            node = next(node.value for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "batch_plan" for target in node.targets))
            steps = math.ceil(row_count / settings["effective_batch_size"]) * settings["epochs"]
            namespace = {"settings": settings, "rows": range(row_count), "world": settings["world_size"],
                         "microbatch": 1, "accumulation": math.ceil(settings["effective_batch_size"] / settings["world_size"]),
                         "planned_steps": steps, "stop_steps": steps, "digest_json": digest_json,
                         "global_batches": ddp_core.global_batches}
            return eval(compile(ast.Expression(node), "saved_batch_plan", "eval"), namespace)

        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for parallel in ("ddp", "fsdp"):
                default = ddp_config.normalize_training_config({"parallel": parallel}, student)
                for row_count in (1, 35, 67):
                    with self.subTest(student=student, parallel=parallel, row_count=row_count):
                        self.assertEqual(canonical_bytes(plan(source, default, row_count)),
                                         canonical_bytes(plan(baseline, default, row_count)))
                        for seed in (0, 18, 19, 2**31 - 1):
                            settings = {**default, "seed": seed}
                            expected = [digest_json([batch["indices"] for batch in ddp_core.global_batches(
                                row_count, epoch, settings["effective_batch_size"], settings["seed"])])
                                for epoch in range(settings["epochs"])]
                            self.assertEqual(plan(source, settings, row_count)["epoch_order_sha256"], expected)
                            if row_count > 1:
                                self.assertNotEqual(expected, plan(baseline, settings, row_count)["epoch_order_sha256"])

    def test_training_rng_controls_lora_initialization_and_rank_dropout(self):
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import set_seed

        tree = ast.parse((REPO / "student_pilot/ddp_training.py").read_text())
        train = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "train")
        calls = [node for node in ast.walk(train) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        seed_calls = sorted((node for node in calls if node.func.id == "set_seed"), key=lambda node: node.lineno)
        self.assertEqual(len(seed_calls), 2)
        attach_line = next(node.lineno for node in calls if node.func.id == "attach_ddp_adapters")
        probe_line = next(node.lineno for node in calls if node.func.id in ("memory_probe", "startup_memory_probe"))
        self.assertLess(seed_calls[0].lineno, attach_line)
        self.assertLess(attach_line, probe_line)
        self.assertLess(probe_line, seed_calls[1].lineno)
        expressions = [compile(ast.Expression(node.args[0]), "training_seed", "eval") for node in seed_calls]

        def sample(seed, rank):
            settings = ddp_config.normalize_training_config({"seed": seed}, "qwen35")
            namespace = {"settings": settings, "rank": rank}
            self.assertEqual([eval(expression, namespace) for expression in expressions], [seed, seed + rank])
            set_seed(eval(expressions[0], namespace))
            model = get_peft_model(torch.nn.Sequential(torch.nn.Linear(16, 16, bias=False)),
                LoraConfig(r=settings["lora_rank"], lora_alpha=settings["lora_alpha"],
                           lora_dropout=settings["lora_dropout"], target_modules=["0"]))
            layer = next(module for module in model.modules() if hasattr(module, "lora_A"))
            initialized = layer.lora_A["default"].weight.detach().clone()
            set_seed(eval(expressions[1], namespace))
            return initialized, layer.lora_dropout["default"](torch.ones(128, 16))

        samples = {}
        for seed in (0, 17, 18, 19, 2**31 - 1):
            with self.subTest(seed=seed):
                first, repeated, other_rank = sample(seed, 0), sample(seed, 0), sample(seed, 7)
                for actual, expected in zip(first, repeated):
                    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
                torch.testing.assert_close(first[0], other_rank[0], rtol=0, atol=0)
                self.assertFalse(torch.equal(first[1], other_rank[1]))
                samples[seed] = first
        for seed in (18, 19):
            for actual, default in zip(samples[seed], samples[17]):
                self.assertFalse(torch.equal(actual, default))


@unittest.skipUnless(SOCKETS, "requires local CPU/gloo sockets")
class SeedBatchPlanTests(unittest.TestCase):
    def check_plan(self, parallel):
        from tests import test_sft_warmstart_training as training_fixtures

        original_normalize = ddp_config.normalize_training_config

        def normalize(value, student):
            if isinstance(value, dict) and value.get("world_size") == 2 and "seed" not in value:
                value = {**value, "seed": 18}
            return original_normalize(value, student)

        fixture = type("Seed18Fixture", (training_fixtures.WarmstartResumeIntegrationTests,), {"parallel": parallel})
        with patch.object(ddp_config, "normalize_training_config", side_effect=normalize):
            fixture.setUpClass()
        root = fixture.root
        protocol = load_json(root / "protocol.json")
        settings = protocol["training"]
        self.assertEqual(settings["seed"], 18)
        self.assertEqual(protocol["training_sha256"], digest_json(settings))
        expected_batches = [[batch["indices"] for batch in ddp_core.global_batches(
            35, epoch, settings["effective_batch_size"], settings["seed"])] for epoch in range(settings["epochs"])]
        expected = [digest_json(batches) for batches in expected_batches]
        legacy = [digest_json([batch["indices"] for batch in ddp_core.global_batches(35, epoch)])
                  for epoch in range(settings["epochs"])]
        self.assertNotEqual(expected, legacy)
        executed = {}
        for name in ("reference", "interrupted"):
            metrics = [json.loads(line) for line in (root / name / "metrics.jsonl").read_text().__getattribute__("sp" "litlines")()]
            self.assertEqual([metric["step"] for metric in metrics], [1, 2, 3, 4])
            batches = [[[int(qid) for qid in metric["qids"]] for metric in metrics if metric["epoch"] == epoch + 1]
                       for epoch in range(settings["epochs"])]
            self.assertEqual(batches, expected_batches)
            executed[name] = [digest_json(order) for order in batches]
            self.assertEqual(executed[name], expected)
        plans = {name: load_json(root / name)["epoch_order_sha256"] for name in (
            "reference/batch_plan.json", "interrupted/batch_plan.json",
            "interrupted/checkpoints/_superseded/step_1/artifacts/batch_plan.json",
            "interrupted/checkpoints/step_4/artifacts/batch_plan.json",
            "published/reference/batch_plan.json", "published/resume/batch_plan.json")}
        (root / "seed_batch_plan.json").write_bytes(canonical_bytes({
            "parallel": parallel, "seed": settings["seed"], "training_sha256": protocol["training_sha256"],
            "observed_training_orders": executed, "default_seed17_orders": legacy, "saved_orders": plans,
            "saved_orders_match_executed_seed18": all(value == expected for value in plans.values()),
            "cpu_only": True, "synthetic": True, "grants_training_admission": False}))
        for name, saved in plans.items():
            self.assertEqual(saved, expected, f"{parallel}: {name} hashes a different seed from the executed training order")

    def test_ddp_saved_orders_match_executed_seed(self):
        self.check_plan("ddp")

    def test_fsdp_saved_orders_match_executed_seed(self):
        self.check_plan("fsdp")


if __name__ == "__main__":
    unittest.main()
