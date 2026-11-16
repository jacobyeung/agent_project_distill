import ast
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from student_pilot import diagnostic
from student_pilot.common import REPO, binding, canonical_bytes
from student_pilot.students import training_parameters


BASE = "835d48f9734aa85ec06902d2546223664a465945"


def base_source(relative):
    return subprocess.run(["git", "show", f"{BASE}:{relative}"], cwd=REPO, check=True, capture_output=True).stdout


def function_source(source, name):
    tree = ast.parse(source)
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(source, node)


class DDPIsolationTests(unittest.TestCase):
    def test_clean_admission_preprocessing_settings_and_single_gpu_launcher_are_byte_identical(self):
        paths = ("student_pilot/lease.py", "student_pilot/admission.py",
                 "student_pilot/diagnostic_data.py", "student_pilot/batches.py",
                 "student_pilot/students.py", "student_pilot/division.py", "student_pilot/common.py",
                 "student_pilot/conversion.py", "requirements.txt", "scripts/diagnostic_gpu_batch.sh")
        for relative in paths:
            with self.subTest(path=relative):
                before, after = base_source(relative), (REPO / relative).read_bytes()
                if relative == "student_pilot/batches.py":
                    source = after.decode()
                    after = source.replace(function_source(source, "training_text"),
                                           function_source(before.decode(), "training_text"), 1).encode()
                self.assertEqual(after, before)

        before = base_source("student_pilot/runner.py").decode()
        after = (REPO / "student_pilot/runner.py").read_text()
        for node in ast.parse(before).body:
            if isinstance(node, ast.FunctionDef) and node.name != "forward_loss":
                with self.subTest(path="student_pilot/runner.py", function=node.name):
                    self.assertEqual(function_source(before, node.name), function_source(after, node.name))

        before = base_source("student_pilot/provisional.py").decode()
        after = (REPO / "student_pilot/provisional.py").read_text()
        for node in ast.parse(before).body:
            if isinstance(node, ast.FunctionDef) and node.name not in ("gpu_uuid", "check_host_lease", "admission_probe"):
                with self.subTest(path="student_pilot/provisional.py", function=node.name):
                    self.assertEqual(function_source(before, node.name), function_source(after, node.name))

    def test_existing_training_evaluation_device_and_adapter_functions_are_byte_identical(self):
        modules = {"student_pilot/diagnostic.py": ("frozen_base_check", "train", "evaluate", "generation_config", "main"),
                   "student_pilot/adapters.py": ("discover_targets", "trainable_groups", "attach_adapters")}
        for relative, names in modules.items():
            before, after = base_source(relative).decode(), (REPO / relative).read_text()
            for name in names:
                with self.subTest(path=relative, function=name):
                    self.assertEqual(function_source(before, name), function_source(after, name))

    def test_single_gpu_admission_retains_reviewed_three_way_uuid_check(self):
        reviewed = subprocess.run(["git", "show", "0de12a5:student_pilot/diagnostic.py"],
                                  cwd=REPO, check=True, capture_output=True, text=True).stdout
        self.assertEqual(function_source(reviewed, "admitted_device"),
                         function_source((REPO / "student_pilot/diagnostic.py").read_text(), "admitted_device"))

    def test_clean_adapter_binding_returns_identical_bytes(self):
        root = Path(tempfile.mkdtemp(prefix="ddp_clean_binding_", dir=os.environ["LANE_TEST_OUTPUT"]))
        protocol = root / "protocol.json"
        training = root / "training.json"
        weights = root / "synthetic-weights.bin"
        config = root / "synthetic-config.json"
        for path in (protocol, training, config):
            path.write_bytes(canonical_bytes({"synthetic": True}))
        weights.write_bytes(b"synthetic CPU byte-identity fixture")
        result = {"schema": "completed-detailed-diagnostic-training-v1", "status": "TRAINED", "student": "onethinker",
                  "protocol": binding(protocol), "training_manifest": binding(training), "synthetic": True,
                  "adapter_parameters": training_parameters("onethinker"),
                  "adapter": {"config": binding(config), "weights": binding(weights)}}
        (root / "training_result.json").write_bytes(canonical_bytes(result))
        source = base_source("student_pilot/diagnostic.py").decode()
        node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "adapter_binding")
        namespace = dict(diagnostic.__dict__)
        exec(compile(ast.Module(body=[node], type_ignores=[]), "unchanged_clean_binding", "exec"), namespace)
        expected = namespace["adapter_binding"](root, protocol)
        actual = diagnostic.adapter_binding(root, protocol)
        self.assertEqual(canonical_bytes(actual), canonical_bytes(expected))


if __name__ == "__main__":
    unittest.main()
