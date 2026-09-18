import argparse
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def source_manifest():
    return {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for directory in ("student_pilot", "scripts", "tests") for path in sorted((REPO / directory).glob("*.py"))}


def integration_dependencies(test):
    class_id, method = test.id().rsplit(".", 1)
    shared, specific = {"files": [], "modules": []}, {"files": [], "modules": []}
    if class_id == "test_conversion.ConversionTests":
        from student_pilot import admission, conversion
        shared["files"] = [conversion.DEFAULT_AUDIT / "audit_report.json", conversion.DEFAULT_AUDIT / "review_packets.json",
                           admission.SPLIT_PATH, admission.CONTRACT, admission.MEMBERSHIP, admission.REGISTRY]
        shared["modules"] = ["av"]
        if method == "test_prepared_first_three_job_revalidates_without_network":
            specific["files"] = [REPO / "artifacts/data/conversion_first3_v2/job.json"]
    elif class_id == "test_diagnostic.DiagnosticTests":
        from student_pilot.common import ARTIFACTS, MODEL
        shared["files"] = [ARTIFACTS / "data/smoke.json", MODEL / "config.json", MODEL / "tokenizer_config.json",
                           MODEL / "tokenizer.json"]
        shared["any_files"] = [(MODEL / "processor_config.json", MODEL / "preprocessor_config.json")]
        shared["modules"] = ["torch", "transformers", "PIL", "av"]
        if method == "test_native_greedy_generation_configuration_preserves_eos":
            specific["files"] = [MODEL / "generation_config.json"]
        elif method == "test_review_packets_and_smoke_are_not_diagnostic_training":
            specific["files"] = [ARTIFACTS / "data/detailed_audit_v1/review_packets.json"]
        elif method == "test_missing_outputs_have_zero_credit_without_reducing_membership":
            specific["files"] = [ARTIFACTS / "data/split.json"]
    elif class_id == "test_training.AdapterTests":
        from student_pilot.common import MODEL
        shared = {"files": [MODEL / "config.json"], "modules": ["torch", "accelerate", "transformers", "peft"]}
    return shared, specific


def missing_dependencies(spec, workspace):
    workspace = Path(os.path.abspath(workspace))

    def present(path):
        path = Path(os.path.abspath(path))
        return path.is_relative_to(workspace) and path.is_file()

    missing = ["fixture:" + str(path) for path in spec.get("files", []) if not present(path)]
    for alternatives in spec.get("any_files", []):
        if not any(present(path) for path in alternatives):
            missing.append("fixture:any_of(" + ",".join(map(str, alternatives)) + ")")
    for module in spec.get("modules", []):
        try:
            available = importlib.util.find_spec(module) is not None
        except ModuleNotFoundError:
            available = False
        if not available:
            missing.append("module:" + module)
    return missing


def condition_integration_tests(tests, workspace):
    blocked = {}
    for test in tests:
        shared, specific = integration_dependencies(test)
        shared_missing = missing_dependencies(shared, workspace)
        specific_missing = missing_dependencies(specific, workspace)
        cls = type(test)
        if shared_missing:
            cls.__unittest_skip__ = True
            cls.__unittest_skip_why__ = "conditional_dependency_skip: " + "; ".join(shared_missing)
            cls._clean_dependency_skip = True
        elif cls.__dict__.get("_clean_dependency_skip"):
            cls.__unittest_skip__ = False
            cls._clean_dependency_skip = False
        if shared_missing or specific_missing:
            reason = "conditional_dependency_skip: " + "; ".join(shared_missing + specific_missing)
            blocked[test.id()] = reason
            if not shared_missing:
                method = getattr(test, test._testMethodName)
                setattr(test, test._testMethodName, unittest.skip(reason)(method))
    return blocked


def main():
    parser = argparse.ArgumentParser(description="Run every available offline fixture without external data access, network calls, GPUs or cleanup")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path)
    parser.add_argument("--suite", choices=("all", "clean", "preexisting"), default="all")
    parser.add_argument("--test", action="append", default=[], help="Run only matching fully qualified test or class prefixes")
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    output = args.output.absolute()
    if not output.is_relative_to(workspace):
        raise ValueError("Test outputs must stay inside the workspace")
    output.mkdir(parents=True, exist_ok=True)
    for key, name in (("TMPDIR", "tmp"), ("XDG_CACHE_HOME", "cache"), ("HF_HOME", "huggingface"),
                      ("TORCH_HOME", "torch"), ("TRITON_CACHE_DIR", "triton"), ("TORCHINDUCTOR_CACHE_DIR", "inductor"),
                      ("PYTHONPYCACHEPREFIX", "bytecode")):
        path = output / name
        path.mkdir(exist_ok=True)
        os.environ[key] = str(path)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      HF_HUB_DISABLE_TELEMETRY="1", TOKENIZERS_PARALLELISM="false", WANDB_DISABLED="true",
                      CLEAN_VSI590K_WORKSPACE=str(workspace), CLEAN_VSI590K_TEST_ROOT=str(output / "fixtures"))
    if args.staged_root:
        os.environ["R1313_STAGED_ROOT"] = str(args.staged_root)
    sys.dont_write_bytecode = True
    tempfile.tempdir = str(output / "tmp")

    class RetainedTemporaryDirectory(tempfile.TemporaryDirectory):
        def cleanup(self):
            self._finalizer.detach()

        @classmethod
        def _cleanup(cls, *positional, **keywords):
            return None

    tempfile.TemporaryDirectory = RetainedTemporaryDirectory
    sys.path[:0] = [str(REPO), str(REPO / "tests")]
    runtime_roots = [Path(sys.prefix), Path(sys.base_prefix)]
    denied = []

    def allowed_read(path):
        return path.is_relative_to(workspace) or any(path.is_relative_to(root) for root in runtime_roots)

    def guard(event, values):
        if event in ("socket.connect", "socket.getaddrinfo", "os.remove", "os.rmdir", "shutil.rmtree"):
            denied.append(event)
            raise PermissionError("Offline fixture guard forbids network calls and deletion")
        if event == "open" and isinstance(values[0], (str, bytes)):
            path = Path(os.fsdecode(values[0])).absolute()
            mode, flags = values[1:3]
            writing = isinstance(mode, str) and any(c in mode for c in "wax+") or isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not path.is_relative_to(output):
                denied.append("external_write")
                raise PermissionError("Offline fixture write outside the test output")
            if str(path).startswith(("/data2/", "/home/")) and not allowed_read(path):
                denied.append("external_data_read")
                raise PermissionError("Offline fixture external data access is forbidden")

    original_resolve = Path.resolve

    def guarded_resolve(path, *positional, **keywords):
        absolute = Path(os.path.abspath(path))
        if str(absolute).startswith(("/data2/", "/home/")) and not allowed_read(absolute):
            return absolute
        return original_resolve(path, *positional, **keywords)

    Path.resolve = guarded_resolve
    sys.addaudithook(guard)
    tested_sources = source_manifest()
    pattern = "test_clean*.py" if args.suite == "clean" else "test_*.py"
    print("Discovering offline test modules with workspace-only caches and retained temporary files", flush=True)
    suite = unittest.defaultTestLoader.discover(str(REPO / "tests"), pattern=pattern)
    flattened = []

    def visit(node):
        if isinstance(node, unittest.TestSuite):
            for child in node:
                visit(child)
        elif (args.suite != "preexisting" or not node.id().startswith("test_clean")) and (
                not args.test or any(node.id() == name or node.id().startswith(name + ".") for name in args.test)):
            flattened.append(node)

    visit(suite)
    if not flattened:
        raise ValueError("No offline tests matched the requested suite/filter")
    blocked = condition_integration_tests(flattened, workspace)
    pytest_available = importlib.util.find_spec("pytest") is not None
    log = (output / "tests.log").open("x")

    class Tee(io.TextIOBase):
        def write(self, value):
            log.write(value)
            log.flush()
            sys.stdout.write(value)
            sys.stdout.flush()
            return len(value)

        def flush(self):
            if not log.closed:
                log.flush()
            sys.stdout.flush()

    stream = Tee()
    stream.write("Interpreter: " + sys.executable + "\n")
    stream.write("Pytest available: " + str(pytest_available) + "; runner: unittest (fixtures are pytest-compatible)\n")
    stream.write("Missing diagnostic integrations are reported explicitly, not replaced with synthetic benchmark evidence.\n")
    for test in flattened:
        stream.write(("CONDITIONAL_SKIP " + test.id() + ": " + blocked[test.id()] if test.id() in blocked
                      else "SELECTED " + test.id()) + "\n")
    class RecordingResult(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.started_ids = []

        def startTest(self, test):
            self.started_ids.append(test.id())
            super().startTest(test)

    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult).run(unittest.TestSuite(flattened))
    skipped_ids = {test.id() for test, _ in result.skipped}
    executed = [test_id for test_id in result.started_ids if test_id not in skipped_ids]
    source_unchanged = tested_sources == source_manifest()
    for test_id in executed:
        stream.write("EXECUTED " + test_id + "\n")
    for test, reason in result.skipped:
        stream.write("CONDITIONAL_SKIP " + test.id() + ": " + reason + "\n")
    stream.write(f"Execution summary: selected={len(flattened)} executed={len(executed)} "
                 f"dependency_gate_skips={len(blocked)} skipped_total={len(result.skipped)} "
                 f"failures={len(result.failures)} errors={len(result.errors)} source_unchanged={source_unchanged}\n")
    summary = {"schema": "clean-vsi590k-offline-test-results-v1", "interpreter": sys.executable,
               "runner": "unittest", "pytest_available": pytest_available, "selected_tests": len(flattened),
               "tests_run": result.testsRun, "tests_executed": len(executed), "executed_test_ids": executed,
               "failures": len(result.failures), "errors": len(result.errors),
               "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
               "blocked_preexisting": blocked, "executed_tests_successful": result.wasSuccessful() and source_unchanged,
               "tested_source_sha256": tested_sources, "source_unchanged": source_unchanged,
               "full_requested_verification": result.wasSuccessful() and source_unchanged and not result.skipped,
               "clean_tests_selected": sum(t.id().startswith("test_clean") for t in flattened),
               "preexisting_tests_selected": sum(not t.id().startswith("test_clean") for t in flattened),
               "boundary_guard_denials": denied, "network_calls": 0, "gpu_runs": 0}
    with (output / "TEST_RESULTS.json").open("x") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    log.close()
    return 0 if result.wasSuccessful() and source_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
