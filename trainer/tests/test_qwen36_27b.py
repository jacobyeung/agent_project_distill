import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import torch
from transformers import AutoConfig, Qwen3VLProcessor
from transformers.video_utils import VideoMetadata

from student_pilot import adapters, batches, ddp_config, fsdp_training, runner, students


REVISION = "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"
SNAPSHOT = Path(os.environ.get("QWEN36_27B_SNAPSHOT", "/data2/jjyeung/cache/huggingface/hub/models--Qwen--Qwen3.6-27B/snapshots/" + REVISION))
CONFIG_PATH = Path(os.environ.get("QWEN36_27B_TRAINING_CONFIG", str(Path(__file__).resolve().parents[3] / "out/config_qwen36_27b.json")))
BASELINE_CONFIG = Path("/data3/jjyeung/ddp_qwen35_c_qwen_20260920T0800Z_r1/config.json")
BASELINE_COUNTS = {"text": 116727808, "vision": 3849984, "mergers": 151552}
RANK32_COUNTS = {"text": 233455616, "vision": 15399936, "mergers": 606208}
TARGET_COUNTS = {"text": 496, "vision": 108, "mergers": 2}


class Qwen36Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import Qwen3_5ForConditionalGeneration

        if torch.cuda.is_initialized():
            raise AssertionError("This regression must not initialize CUDA")
        config = AutoConfig.from_pretrained(SNAPSHOT, local_files_only=True, trust_remote_code=False)
        config._name_or_path = ""
        with patch.object(Qwen3_5ForConditionalGeneration, "from_pretrained", side_effect=AssertionError("Weights must not load")):
            with torch.device("meta"):
                cls.model = Qwen3_5ForConditionalGeneration(config)

    def test_registry_and_snapshot_revision(self):
        spec = students.get_student("qwen36_27b")
        self.assertEqual(spec["snapshot"], SNAPSHOT)
        self.assertEqual(students.validate_snapshot("qwen36_27b").name, REVISION)
        self.assertEqual(spec["architecture"], "Qwen3_5ForConditionalGeneration")
        self.assertEqual(spec["processor"], "Qwen3VLProcessor")
        self.assertEqual(spec["model_type"], "qwen3_5")
        self.assertEqual(spec["config_sha256"], "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c")
        self.assertEqual(spec["group_parameters"], BASELINE_COUNTS)
        self.assertEqual(spec["target_counts"], TARGET_COUNTS)
        for basename, succeeds in ((REVISION, True), ("renamed-snapshot", False)):
            override = "/scratch/jjyeung/staged/" + basename
            command = "from student_pilot.students import get_student; print(get_student('qwen36_27b')['snapshot'])"
            result = subprocess.run([sys.executable, "-B", "-c", command], capture_output=True, text=True,
                                    env={**os.environ, "QWEN36_27B_SNAPSHOT": override, "CUDA_VISIBLE_DEVICES": ""})
            self.assertEqual(result.returncode == 0, succeeds, result.stderr)
            if succeeds:
                self.assertEqual(result.stdout.strip(), override)
            else:
                self.assertIn("snapshot directory", result.stderr)

    def test_shared_model_type_uses_structure_not_name(self):
        self.assertEqual(self.model.name_or_path, "")
        self.assertEqual(students.student_for_model(self.model), "qwen36_27b")
        for student in ("qwen35", "onethinker"):
            config = AutoConfig.from_pretrained(students.get_student(student)["snapshot"], local_files_only=True)
            for misleading_name in ("", "Qwen/Qwen3.6-27B"):
                with self.subTest(student=student, name=misleading_name):
                    model = SimpleNamespace(config=config, name_or_path=misleading_name)
                    self.assertEqual(students.student_for_model(model), student)
        for layers, hidden in ((64, 4096), (32, 5120), (63, 5120)):
            config = SimpleNamespace(model_type="qwen3_5", text_config=SimpleNamespace(num_hidden_layers=layers, hidden_size=hidden))
            with self.subTest(layers=layers, hidden=hidden), self.assertRaisesRegex(ValueError, "Unsupported student"):
                students.student_for_model(SimpleNamespace(config=config, name_or_path=str(SNAPSHOT)))

    def test_real_meta_module_names_counts_and_rank32_adapters(self):
        self.assertTrue(all(parameter.is_meta for parameter in self.model.parameters()))
        with patch.object(adapters, "student_for_model", return_value="qwen36_27b"):
            targets = adapters.discover_targets(self.model)
        modules = dict(self.model.named_modules())
        measured = {group: sum(adapters.RANKS[group] * (modules[name].in_features + modules[name].out_features)
                               for name in names) for group, names in targets.items()}
        rank32 = {group: sum(32 * (modules[name].in_features + modules[name].out_features)
                             for name in names) for group, names in targets.items()}
        self.assertEqual({group: len(names) for group, names in targets.items()}, TARGET_COUNTS)
        self.assertEqual(measured, BASELINE_COUNTS)
        self.assertEqual(rank32, RANK32_COUNTS)
        self.assertEqual(sum(rank32.values()), 249461760)
        self.assertEqual(sum(".linear_attn." in name for name in targets["text"]), 240)
        self.assertEqual(sum(".self_attn." in name for name in targets["text"]), 64)
        self.assertEqual(sum(".mlp." in name for name in targets["text"]), 192)
        self.assertEqual(targets["mergers"], ["model.visual.merger.linear_fc1", "model.visual.merger.linear_fc2"])
        self.assertTrue(all(isinstance(modules[name], torch.nn.Linear) for names in targets.values() for name in names))
        with SNAPSHOT.joinpath("model.safetensors.index.json").open() as stream:
            index = json.load(stream)
        self.assertTrue(all(name + ".weight" in index["weight_map"] for names in targets.values() for name in names))
        base_parameters = sum(parameter.numel() for parameter in self.model.parameters())
        with torch.device("meta"):
            attached, report = adapters.attach_ddp_adapters(self.model, {"world_size": 3, "parallel": "fsdp"})
        self.assertEqual(report["group_parameters"], rank32)
        self.assertEqual(students.student_for_model(attached), "qwen36_27b")
        self.assertTrue(all(parameter.is_meta for parameter in attached.parameters()))
        print(json.dumps({"student": "qwen36_27b", "target_counts": TARGET_COUNTS,
                          "baseline_parameters": measured, "rank32_parameters": rank32,
                          "trainable_parameters": sum(rank32.values()), "base_parameters": base_parameters,
                          "base_bf16_bytes": 2 * base_parameters, "cuda_initialized": torch.cuda.is_initialized()}, sort_keys=True))

    def test_arm_c_config_is_exact_settings_derivative(self):
        with BASELINE_CONFIG.open() as stream:
            expected = json.load(stream)["config"]["settings"]
        expected.pop("sharding", None)
        expected.update(parallel="fsdp", world_size=3, max_microbatch_size=1, checkpoint_every_steps=25,
                        group_parameters=RANK32_COUNTS, trainable_parameters=249461760)
        with CONFIG_PATH.open() as stream:
            supplied = json.load(stream)
        self.assertEqual(supplied, expected)
        self.assertNotIn("sharding", supplied)
        with CONFIG_PATH.open() as stream:
            normalized = ddp_config.normalize_training_config(json.load(stream), "qwen36_27b")
        self.assertEqual(normalized["sharding"], fsdp_training.SHARDING)
        self.assertEqual(ddp_config.run_control_from_config(supplied), {"checkpoint_every_steps": 25})
        for key in ddp_config.FIXED:
            self.assertEqual(normalized[key], ddp_config.DEFAULTS[key])
        capped = ddp_config.normalize_training_config({**supplied, "max_steps": 3}, "qwen36_27b")
        self.assertEqual(capped["max_steps"], 3)

    def test_real_processor_boundary_verbatim_suffix_and_mask(self):
        processor = batches.load_processor("qwen36_27b")
        self.assertIsInstance(processor, Qwen3VLProcessor)
        target = "Observations\nSynthetic CPU fixture only.\nAnswer\nfixture"
        metadata = VideoMetadata(total_num_frames=32, fps=2.0, frames_indices=list(range(32)), width=128, height=128)
        for ending in ("", "\n"):
            with self.subTest(ending=repr(ending)):
                value = target + ending
                prompt, suffix = batches.training_text(processor, "Synthetic boundary check, not a benchmark question.", [], value)
                self.assertTrue(prompt.endswith("<|im_start|>assistant\n<think>\n"))
                self.assertEqual(suffix, "\n</think>\n\n" + value + processor.tokenizer.eos_token)
                batch, audit = batches.encode_arrays(processor, "Synthetic boundary check, not a benchmark question.", [],
                                                     np.zeros((32, 128, 128, 3), dtype=np.uint8), metadata, value)
                supervised = batch["input_ids"][batch["labels"] != -100].tolist()
                self.assertEqual(processor.tokenizer.decode(supervised, skip_special_tokens=False), suffix)
                self.assertEqual(supervised[-1], processor.tokenizer.eos_token_id)
                self.assertTrue(torch.all(batch["labels"][:, :audit["prompt_tokens"]] == -100))
                self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
                self.assertFalse(audit["target_truncated"])
        for ending in ("\n\n", " \n", "\t\n", "\r\n"):
            with self.subTest(refused=repr(ending)), self.assertRaisesRegex(ValueError, "assistant boundary"):
                batches.training_text(processor, "Synthetic boundary check.", [], target + ending)
        self.assertFalse(torch.cuda.is_initialized())

    def test_cpu_base_loading_preserves_legacy_defaults(self):
        for student, options, device in (("qwen36_27b", {"device": "cpu"}, "cpu"),
                                         ("qwen35", {}, "cuda:0"), ("onethinker", {}, "cuda:0")):
            with self.subTest(student=student), patch.object(runner, "model_class") as factory, \
                    patch.object(runner, "validate_snapshot", return_value=SNAPSHOT):
                model = runner.load_base(student, **options)
                factory.assert_called_once_with(student)
                factory.return_value.from_pretrained.assert_called_once_with(
                    SNAPSHOT, local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16,
                    device_map={"": device}, attn_implementation="sdpa")
                self.assertFalse(model.config.use_cache)
                self.assertFalse(model.config.text_config.use_cache)
                model.requires_grad_.assert_called_once_with(False)

    def test_fsdp_moves_only_cpu_adapters_before_wrapping(self):
        device = torch.device("cuda:0")
        for origin in ("cpu", "cuda:0"):
            parameter = Mock(requires_grad=True, device=torch.device(origin))
            original_data = parameter.data
            model = Mock()
            model.parameters.return_value = [parameter]
            model.modules.return_value = [type("Qwen3_5DecoderLayer", (torch.nn.Module,), {})()]
            with self.subTest(origin=origin), patch.object(fsdp_training, "FSDP") as wrapper, \
                    patch.object(fsdp_training.dist, "broadcast") as broadcast:
                self.assertIs(fsdp_training.wrap_model(model, [parameter], "synthetic-group", device), wrapper.return_value)
                if origin == "cpu":
                    original_data.to.assert_called_once_with(device)
                    self.assertIs(parameter.data, original_data.to.return_value)
                else:
                    original_data.to.assert_not_called()
                broadcast.assert_called_once_with(parameter.data, src=0, group="synthetic-group")
                model.to.assert_not_called()
        self.assertFalse(torch.cuda.is_initialized())


class LaunchArtifactTests(unittest.TestCase):
    @staticmethod
    def embedded(script, delimiter):
        lines = script.read_text().__getattribute__("sp" "litlines")()
        start = next(index for index, line in enumerate(lines) if "<<'" + delimiter + "'" in line) + 1
        return "\n".join(lines[start:lines.index(delimiter, start)]) + "\n"

    def test_shell_and_embedded_python_syntax_without_launching(self):
        scripts = {"run_qwen36_27b.sh": ("PY_CONFIG", "PY_PROTOCOL", "PY_LEASES", "PY_SYNC"),
                   "smoke_qwen36_27b.sh": ("PY_MEMORY",)}
        for name, delimiters in scripts.items():
            path = CONFIG_PATH.parent / name
            with self.subTest(script=name):
                subprocess.run(["bash", "-n", str(path)], check=True, capture_output=True, text=True)
                for delimiter in delimiters:
                    ast.parse(self.embedded(path, delimiter), filename=str(path) + ":" + delimiter)
        launcher = (CONFIG_PATH.parent / "run_qwen36_27b.sh").read_text()
        self.assertIn('bash /data3/shared/scripts/vnice/vnice.sh bash "$TRAINER/scripts/diagnostic_ddp_gpu_batch.sh"', launcher)
        self.assertIn('--inherit-division "$DIVISION_PATH"', launcher)
        self.assertIn('"--bwlimit=60000"', launcher)
        self.assertNotIn("torchrun", launcher)
        for command in ("prepare-protocol", "prepare-training", "lease-request-ddp", "bind-lease-ddp", "finalize"):
            self.assertIn("diagnostic " + command, launcher)

    def test_memory_summary_uses_each_rank_and_refuses_incomplete_smokes(self):
        source = self.embedded(CONFIG_PATH.parent / "smoke_qwen36_27b.sh", "PY_MEMORY")
        code = compile(source, "smoke_qwen36_27b.sh:PY_MEMORY", "exec")
        for case in ("complete", "oom", "short", "missing_rank", "missing_receipt", "no_memory"):
            root = Path(tempfile.mkdtemp(prefix="qwen36_synthetic_memory_" + case + "_", dir=CONFIG_PATH.parent))
            probe = {"ranks": [{"rank": rank, "trials": [{"peak_allocated_bytes": 1000 + rank,
                                                       "peak_reserved_bytes": 5000 + rank}]} for rank in range(3)]}
            metrics = [{"step": step, "loss": 1.0, "peak_memory_per_rank": [
                {"rank": rank, "memory": {"max_allocated_bytes": 2000 + step * 100 + rank,
                                          "max_reserved_bytes": 4000 + step * 100 + rank}} for rank in range(3)]}
                for step in (1, 2, 3)]
            result = {"status": "SMOKE_COMPLETE", "realized": {"optimizer_steps": 3}, "settings": {"max_steps": 3},
                      "world_size": 3, "parallel": "fsdp", "frozen_base_unchanged": True}
            if case == "oom":
                probe["ranks"][1]["trials"][0]["reason"] = "CUDA_OutOfMemory"
            if case == "short":
                metrics = metrics[:2]
            if case == "missing_rank":
                metrics[0]["peak_memory_per_rank"] = metrics[0]["peak_memory_per_rank"][:2]
            if case != "no_memory":
                (root / "memory_probe.json").write_text(json.dumps(probe))
                (root / "metrics.jsonl").write_text("".join(json.dumps(metric) + "\n" for metric in metrics))
            if case != "missing_receipt":
                (root / "training_result.json").write_text(json.dumps(result))
            output = io.StringIO()
            with self.subTest(case=case), patch.object(sys, "argv", ["memory-check", str(root), "3"]), redirect_stdout(output):
                if case == "complete":
                    exec(code, {"__name__": "__main__"})
                else:
                    with self.assertRaises(SystemExit):
                        exec(code, {"__name__": "__main__"})
            if case == "complete":
                for rank in range(3):
                    self.assertIn(f"rank={rank} peak_allocated_bytes={2300 + rank} peak_reserved_bytes={5000 + rank}", output.getvalue())
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == "__main__":
    unittest.main()
