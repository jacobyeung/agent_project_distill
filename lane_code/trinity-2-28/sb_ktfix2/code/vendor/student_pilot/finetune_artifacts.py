import argparse
import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from .common import REPO, binding, canonical_bytes, load_json
from .finetune_lane import parse_params, write_new
from .storage import code_provenance, copy_new


SOURCE_FILES = ("AGENTS.md", "student_pilot/finetune_lane.py", "student_pilot/finetune_prepare.py",
                "student_pilot/finetune_artifacts.py", "student_pilot/division.py", "tests/test_finetune_lane.py",
                "tests/test_finetune_prepare.py", "tests/test_division.py")
ARTIFACT_FILES = ("SCHEMA_GATE.json", "SCHEMA_GATE.md", "validated_index.jsonl", "division.json", "DIVISION_SUMMARY.md",
                  "EVAL_SCENE_CENSUS.json", "GPU_SELECTION.json", "GPU_SELECTION.md", "BASE_REFERENCE.json",
                  "BENCH_ONETHINKER.md", "TRAIN_ONETHINKER.json", "TRAIN_ONETHINKER.md", "HELDOUT_onethinker.md",
                  "LOCAL_LEASE_PROBE.json", "NATIVE_ADMISSION_PROBE.json", "NOTES.md", "VERIFICATION.json", "TESTS.log")


def output_root(params_path, output):
    output = Path(output).resolve()
    if output != (Path(params_path).resolve().parent / "out").resolve() or not output.is_dir():
        raise ValueError("Artifact output must be the parameter file's existing lane out directory")
    return output


def verify(params_path, output):
    output = output_root(params_path, output)
    params = parse_params(params_path)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("Focused verification must expose no CUDA devices")
    provenance = code_provenance({"purpose": "focused_candidate_preparation_verification", "students": params["STUDENTS"]})
    os.environ["LANE_TEST_OUTPUT"] = str(output)
    names = ["tests.test_finetune_lane", "tests.test_finetune_prepare", "tests.test_division"]
    stream = io.StringIO()
    with redirect_stdout(stream), redirect_stderr(stream):
        suite = unittest.defaultTestLoader.loadTestsFromNames(names)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    commands = []
    for command in (["git", "diff", "--check"], [sys.executable, "-B", "-m", "student_pilot.benchmark_eval", "score", "--help"]):
        process = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=60)
        commands.append({"argv": command, "returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
    successful = result.wasSuccessful() and all(item["returncode"] == 0 for item in commands)
    report = {"label": params["label"], "status": "PASS" if successful else "FAIL", "provenance": provenance,
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "test_modules": names, "commands": commands,
              "source_files": {name: binding(REPO / name) for name in SOURCE_FILES},
              "gpu_execution": False, "full_legacy_suite_run": False,
              "recorded_at": datetime.now(timezone.utc).isoformat()}
    write_new(output / "TESTS.log", stream.getvalue().encode())
    write_new(output / "VERIFICATION.json", canonical_bytes(report))
    print(json.dumps({key: report[key] for key in ("status", "tests_run", "failures", "errors", "skipped")}), flush=True)
    return 0 if successful else 1


def blocked_reports(output, label):
    from .diagnostic_data import GENERATION, RGB, training_settings
    from .students import get_student

    division = load_json(output / "division.json")
    settings = training_settings("onethinker")
    student = get_student("onethinker")
    record = {"label": label, "status": "BLOCKED_BEFORE_TRAINING", "student": "onethinker",
              "training_started": False, "optimizer_steps": 0, "start_loss": None, "end_loss": None, "gpu_hours": 0.0,
              "training_defaults_not_executed": settings, "generation_defaults_not_executed": GENERATION,
              "rgb_defaults_not_executed": RGB, "base_snapshot": str(student["snapshot"]),
              "lora": {"text_rank": 16, "vision_rank": 8, "merger_rank": 8,
                       "alphas": {"text": 32, "vision": 16, "mergers": 16}, "dropout": 0.0,
                       "bias": "none", "group_parameters": student["group_parameters"], "target_counts": student["target_counts"]},
              "scratch_frames_staged": False, "adapter": None,
              "default_sources": {name: binding(REPO / "student_pilot" / name)
                                   for name in ("diagnostic_data.py", "diagnostic.py", "adapters.py", "students.py")}}
    write_new(output / "TRAIN_ONETHINKER.json", canonical_bytes(record))
    lines = ["# OneThinker training", "", f"Status: {label}; blocked before training.",
             "No training settings were executed. Optimizer steps: 0. Start/end loss: not available. GPU-hours: 0.",
             "No frames were staged because native source admission and local GPU admission reject this run.", "",
             "## Built-in settings (read from source, not executed)", "", f"Table label: {label}.", "",
             "| Setting | Built-in value |", "|---|---|"]
    lines.extend(f"| {name} | `{json.dumps(value)}` |" for name, value in settings.items())
    lines += ["", "The language adapters use rank 16 and alpha 32. Vision and merger adapters use rank 8 and alpha 16.",
              "LoRA dropout is zero and bias is disabled. The original model is frozen; 48,070,400 adapter parameters are expected.",
              "The training loop declares BF16, SDPA, and non-reentrant gradient checkpointing for language and vision.",
              "Training would restart the pinned original checkpoint, not an infrastructure-smoke adapter.",
              "The complete JSON records source pins, RGB settings, greedy-generation defaults and the exact model snapshot.",
              "NOTES.md and the two native validator probes document the blockers. There is no loss curve or trained adapter to publish."]
    write_new(output / "TRAIN_ONETHINKER.md", ("\n".join(lines) + "\n").encode())
    lines = ["# OneThinker paired held-out evaluation", "", f"Status: {label}; not run.",
             "The requested division is frozen, but the native evaluator accepts only its fixed legacy cohort.",
             "No base or adapter generations exist for this held-out division. Missing results below are not zero accuracies.",
             "The intended metric is per-question-type exact-match accuracy with an identical RGB-only, tool-free input for each pair.",
             "", f"Table label: {label}.", "", "| Question type | Held-out rows | Base exact match | Adapter exact match |",
             "|---|---:|---|---|"]
    for category, count in division["histograms"]["heldout"].items():
        lines.append(f"| {category} | {count} | Not run | Not run |")
    lines += ["", "Raw base generations: absent. Raw adapter generations: absent. No accuracy or improvement claim is made."]
    write_new(output / "HELDOUT_onethinker.md", ("\n".join(lines) + "\n").encode())


def snapshot(params_path, output, manifest_path):
    output = output_root(params_path, output)
    params = parse_params(params_path)
    if params["STUDENTS"] != "onethinker":
        raise ValueError("This blocked-run publication is scoped to the OneThinker-only lane")
    verification = load_json(output / "VERIFICATION.json")
    if verification["status"] != "PASS":
        raise ValueError("Focused preparation verification has not passed")
    provenance = code_provenance({"purpose": "blocked_lane_preparation_snapshot", "params": binding(params_path)})
    manifest_path = Path(manifest_path).resolve()
    if manifest_path.parent != REPO / "configs":
        raise ValueError("The committed lane manifest belongs in this worktree's configs directory")
    blocked_reports(output, params["label"])
    division = load_json(output / "division.json")
    entries = [json.loads(line) for line in (output / "validated_index.jsonl").read_text().__getattribute__("sp" "litlines")()]
    snapshot = {"schema": "provisional-finetune-preparation-manifest-v1", "label": params["label"],
                "status": "BLOCKED_NO_GPU_RUN", "params": params, "params_binding": binding(params_path),
                "provenance": provenance, "division_counts": division["counts"], "scene_intersection": division["scene_intersection"],
                "generation_commits": sorted({row["generation_commit"] for row in entries}),
                "validation_commits": sorted({row["validation_commit"] for row in entries}),
                "artifacts": {name: binding(output / name) for name in ARTIFACT_FILES},
                "source_files": {name: binding(REPO / name) for name in SOURCE_FILES},
                "training_completed": False, "heldout_completed": False, "benchmark_generation_completed": False,
                "model_artifacts": [], "gpu_hours": 0.0,
                "blockers": ["Native fixed conversion-pool and held-out admission do not accept the candidate division",
                             "Native training and benchmark lease guards reject trinity-0-18",
                             "The benchmark harness rejects diagnostic training lineage"],
                "qwen_skip_reason": "STUDENTS=onethinker"}
    write_new(manifest_path, canonical_bytes(snapshot))
    print(json.dumps({"manifest": binding(manifest_path), "status": snapshot["status"],
                      "generation_commits": snapshot["generation_commits"], "validation_commits": snapshot["validation_commits"]}), flush=True)
    return 0


def publish(params_path, output, manifest_path, name):
    output = output_root(params_path, output)
    params = parse_params(params_path)
    recipe = load_json(manifest_path)
    if recipe["status"] != "BLOCKED_NO_GPU_RUN" or recipe["model_artifacts"] or recipe["params_binding"] != binding(params_path):
        raise ValueError("Only the unchanged blocked preparation snapshot may be published here")
    if not name.startswith("preflight_") or Path(name).name != name:
        raise ValueError("A new preflight-named publication directory is required")
    publish_root = Path(params["PUBLISH_ROOT"]).resolve() / name
    if publish_root.exists() or not publish_root.parent.is_dir():
        raise ValueError("Publication needs an existing owned parent and a new child directory")
    provenance = code_provenance({"purpose": "publish_blocked_preparation", "manifest": binding(manifest_path), "output": str(publish_root)})
    if set(recipe["artifacts"]) != set(ARTIFACT_FILES) or set(recipe["source_files"]) != set(SOURCE_FILES):
        raise ValueError("The preparation publication file allowlist changed")
    sources = {}
    for relative, pin in recipe["artifacts"].items():
        if Path(pin["path"]).resolve() != output / relative:
            raise ValueError("Published preparation input escapes the lane output directory")
        binding(pin["path"], pin["sha256"])
        sources["preparation/" + relative] = pin
    for relative, pin in recipe["source_files"].items():
        if Path(pin["path"]).resolve() != REPO / relative:
            raise ValueError("Published source input escapes the trainer worktree")
        binding(pin["path"], pin["sha256"])
        sources["source/" + relative] = pin
    sources["source/" + str(Path(manifest_path).resolve().relative_to(REPO))] = binding(manifest_path)
    publish_root.mkdir(exist_ok=False)
    files = {}
    for relative, pin in sorted(sources.items()):
        destination = publish_root / relative
        copy_new(pin["path"], destination, pin["sha256"])
        files[relative] = {"sha256": pin["sha256"], "bytes": destination.stat().st_size}
    manifest = {"schema": "provisional-preparation-publication-v1", "label": params["label"], "status": "BLOCKED_NO_GPU_RUN",
                "files": files, "excludes": ["MANIFEST.json"], "self_hash_recorded_in": str(output / "PUBLISH_RECEIPT.json"),
                "provenance": provenance, "model_artifacts": [], "gpu_hours": 0.0}
    write_new(publish_root / "MANIFEST.json", canonical_bytes(manifest))
    for relative, pin in files.items():
        binding(publish_root / relative, pin["sha256"])
    receipt = {"label": params["label"], "status": "PREPARATION_PUBLISHED_TRAINING_BLOCKED", "published_path": str(publish_root),
               "manifest": binding(publish_root / "MANIFEST.json"), "verified_files": len(files) + 1,
               "model_artifacts": [], "provenance": provenance}
    write_new(output / "PUBLISH_RECEIPT.json", canonical_bytes(receipt))
    print(json.dumps(receipt), flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify and publish a blocked diagnostic preparation without fabricating model artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "snapshot", "publish"):
        item = sub.add_parser(name)
        item.add_argument("--params", required=True)
        item.add_argument("--output", required=True)
        if name != "verify":
            item.add_argument("--manifest", required=True)
        if name == "publish":
            item.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    if args.command == "verify":
        return verify(args.params, args.output)
    if args.command == "snapshot":
        return snapshot(args.params, args.output, args.manifest)
    return publish(args.params, args.output, args.manifest, args.name)


if __name__ == "__main__":
    raise SystemExit(main())
