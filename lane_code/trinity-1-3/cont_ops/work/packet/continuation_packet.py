import argparse
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import statistics
import types


ROOT = Path(__file__).resolve().parent
WORKSPACE = Path("/scratch/jjyeung/orch_cd/orchard_cp2")
LEDGERS = {
    "INPUTS.json": "899551f52cb14d228c78111ecde2c48064d9551f9218cbd1cafe953759ac609a",
    "ADDITIONAL_INPUTS.json": "17a64963ca3c56ba7cef027c6db35a1c62a8859fe1f9db86873d39449da115f5",
    "ADMISSION_INPUTS.json": "a691d01639109c35f32db97a7a14265cc74563023d3f8f8e921c60a45c25639f",
    "HELD_EVIDENCE.json": "f20d45373e69acf5c8845e63557a236afe3e7b47ae037bd288b77c759f54b7ed",
}
ARCHIVE_SHA = "22249bc7a3cb34117631e21db0132e9a4dc13f1ef85df4676c26ef1826c2c671"
MANIFEST_SHA = "0450e3a3c0265131175d4751329eba9f4605a5f391450a0c98b4e6fdefddc31c"
CONFIG_SHA = "84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb"
PREFIX_SHA = "607fc9f232a967bb28097829ad9a84914f62507a37b6cae7e983a43f41c3449f"
CHECKPOINT = "checkpoint_000544_16d2a80ac22a411f8442277a87b53738"
HEX = re.compile(r"[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def file_identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def read_local(name, limit=3_000_000):
    require(Path(name).name == name, "Only a local input basename is allowed")
    path = ROOT / name
    require(path.is_file() and not path.is_symlink(), "Input is not a regular local file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "Input exceeds its bounded read")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    require(len(raw) <= limit and file_identity(before) == file_identity(after) == file_identity(path.lstat()),
            "Input changed or exceeded its bound: " + name)
    return raw


def load_inputs():
    ledgers = {}
    for name, expected in LEDGERS.items():
        raw = read_local(name)
        require(sha(raw) == expected, "Input-ledger hash differs: " + name)
        ledgers[name] = json.loads(raw)
    primary = ledgers["INPUTS.json"]
    extra = ledgers["ADDITIONAL_INPUTS.json"]
    require(extra["parent_inputs_sha256"] == LEDGERS["INPUTS.json"], "Input ancestry differs")
    sources = {**primary["source_files"], **extra["files"]}
    admission = ledgers["ADMISSION_INPUTS.json"]["files"]
    evidence = ledgers["HELD_EVIDENCE.json"]["files"]
    raw_files = {}
    for pin in [*sources.values(), *admission.values(), *evidence.values()]:
        name = Path(pin["path"]).name
        raw = read_local(name)
        require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"], "Input pin differs: " + name)
        raw_files[name] = raw
    return primary, sources, admission, evidence, raw_files


def checkpoint_inventory(complete, binding):
    require(complete.get("schema") == "c1-checkpoint-v1", "Checkpoint schema differs")
    require(type(complete.get("step")) is int and complete["step"] == 544, "Saved step differs")
    require(type(binding.get("world_size")) is int and binding["world_size"] == 4, "World differs")
    require(complete.get("binding") == binding, "Checkpoint binding differs")
    require(len(complete.get("layouts", [])) == 4, "Layouts do not cover four ranks")
    expected = {"replicated.pt"} | {f"rng{k:03d}.pt" for k in range(4)}
    expected |= {f"shards/rank{k:03d}.pt" for k in range(4)}
    require(set(complete.get("files", {})) == expected, "Checkpoint payload set differs")
    result = []
    for name, pin in sorted(complete["files"].items()):
        require(type(pin.get("bytes")) is int and pin["bytes"] > 0, "Payload size differs")
        require(isinstance(pin.get("sha256"), str) and HEX.fullmatch(pin["sha256"]), "Payload hash differs")
        result.append({"member": f"{CHECKPOINT}/{name}", **pin})
    return result


def verify_slot(raw_slot, raw_sha, raw_complete, binding, reader, reconciliation):
    slot = json.loads(raw_slot)
    complete = json.loads(raw_complete)
    require(slot.get("slot") == "A" and slot.get("job") == "169097", "Slot identity differs")
    require(type(slot.get("step")) is int and slot["step"] == 544, "Slot step differs")
    require(slot.get("verified") is True and slot.get("content_check") == "c1-slot-check-v1",
            "Wrapper content verification is missing")
    require(slot.get("checkpoint") == CHECKPOINT, "Checkpoint basename differs")
    require(type(slot.get("bytes")) is int and slot["bytes"] == 112988477440, "Archive size differs")
    require(raw_sha.decode().strip() == slot.get("archive_sha256") == ARCHIVE_SHA, "Archive digest differs")
    require(sha(raw_complete) == slot.get("manifest_sha256") == MANIFEST_SHA, "Complete-marker digest differs")
    for name, raw in (("A.json", raw_slot), ("A.sha256", raw_sha)):
        record = reader["files"][name]
        require(record["status"] == "OK" and record["stable"] is True, "Terminal metadata was unstable")
        require(record["identity_before"] == record["identity_after"], "Terminal file changed")
        require(bytes.fromhex(record["raw"]["hex"]) == raw and record["raw"]["sha256"] == sha(raw),
                "Terminal raw metadata differs")
    archive = reader["archives"]["A.tar"]
    require(archive["status"] == "OK" and archive["identity"]["bytes"] == slot["bytes"],
            "Archive stat differs from its published index")
    require(all(reader["archives"][name]["status"] == "ABSENT"
                for name in ("A.tar.part", "B.tar", "B.tar.part")), "Unexpected retained slot history")
    require(reader["files"]["B.json"]["status"] == reader["files"]["B.sha256"]["status"] == "ABSENT",
            "Slot B was not absent at closeout")
    require(all(reconciliation["slot"].get(key) == value for key, value in slot.items()),
            "Terminal reconciliation differs")
    require(reconciliation["slot"]["metadata_reconciled"] is True, "Slot was not reconciled")
    baseline = reconciliation["baseline"]
    require(baseline["status"] == "PASS_SOURCE_MATCHED_PREFIX" and baseline["rows"] == 544
            and baseline["first_step"] == 1 and baseline["last_step"] == 544
            and baseline["ranks"] == [0, 1, 2, 3] and baseline["prefix_bytes_each"] == 86552359
            and baseline["prefix_sha256"] == PREFIX_SHA and baseline["prefix_equals_whole_observed_files"] is True,
            "Source-matched prefix evidence differs")
    return {
        "status": "PASS_HELD_METADATA_AGREEMENT",
        "slot": slot,
        "checkpoint_payload_inventory": checkpoint_inventory(complete, binding),
        "wrapper_record_scope": "Published A.json content-check record, A.sha256, archive stat and final copy log",
        "independent_archive_payload_rehash": False,
        "archive_header_inventory_performed": False,
        "production_state_restore_test": False,
    }


def native_functions():
    namespace = {
        "json": json, "os": os, "Path": Path,
        "sys": types.SimpleNamespace(executable="/__PILOT_VENV__/bin/python"),
    }
    selected = []
    for filename, functions in (
        ("source_b_i.py", {"allocation_gpus", "launcher", "pick", "identity"}),
        ("source_b_w.py", {"dispatch"}),
    ):
        for node in ast.parse(read_local(filename).decode(), filename=filename).body:
            if isinstance(node, ast.FunctionDef) and node.name in functions:
                selected.append(node)
            elif isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in ("ARMS", "GPU")
                                                     for target in node.targets):
                selected.append(node)
    exec(compile(ast.Module(body=selected, type_ignores=[]), "<pinned-native-argument-functions>", "exec"), namespace)
    return namespace


def native_selector():
    path = ROOT / "source_b_r8.py"
    spec = importlib.util.spec_from_file_location("bound_native_resume_selector", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocalKit:
    def __truediv__(self, name):
        require(name == "k/0.json", "Unexpected native argument-test file access")
        return ROOT / "source_k_0.json"


def prove_arguments(base, derived, auth, arm_map, launch, binding, contract):
    functions = native_functions()
    require(arm_map == {"0": "b02e4385"} and launch["config"]["file"] == "k/b02e4385.json",
            "Native arm selection differs")
    require(launch["kit_key"] == "07ca49df" and launch["run_key"] == "469ddece", "Kit/run identity differs")
    require(launch["run_directory"] == "/tmp/jjyeung/okit_8865619b/runs/469ddece"
            and launch["persistent_run_root"] == "/home/jjyeung/okit/r/5da50f2b", "Resume location differs")
    require(functions["identity"](derived) == binding["config_sha256"] == CONFIG_SHA,
            "Effective training identity differs")
    expected = copy.deepcopy(base)
    for stream in ("pointing", "routing", "vqa"):
        expected["streams"][stream] = derived["streams"][stream]
    expected["preparation"] = binding["preparation"]
    expected["preparation_output"] = str(Path(binding["preparation"]["path"]).parent)
    expected.pop("admission", None)
    require(derived == expected, "Derived admission changed an unrelated training setting")
    recipe = derived["recipe"]
    require(recipe == base["recipe"] and sha(canonical(recipe)) == contract["training_identity"]["recipe_sha256"],
            "Recipe identity differs")
    require(recipe["steps"] == derived["steps"] == 1000 and recipe["world_size"] == derived["world_size"] == 4,
            "Global schedule or world was reset")
    require(recipe["seed"] == 17 and recipe["resume_every_seconds"] == 7200
            and recipe["wall_seconds"] == 86400 and recipe["stop_before_seconds"] == 3600,
            "Cadence, seed or wall rule differs")
    require(derived.get("row_start_step", 0) == 0 and derived["gate_stop"] is False,
            "Sampler offset or milestone-stop rule differs")
    require(auth["resume"] == "latest" and "u" in auth["modes"] and auth["new_gpus"]["u"] == 4,
            "Native resume permission/configuration differs")
    require(auth["production_go_granted"] is False and auth["production_go_required_separately"] is True,
            "Configuration permission was confused with a new GO")
    require(contract["training_identity"]["binding"] == binding, "Checker training binding differs")
    calls = []
    trainer = types.SimpleNamespace(train=lambda cfg, **kwargs: calls.append((copy.deepcopy(cfg), kwargs)))
    functions["dispatch"](LocalKit(), "u", "0", auth, copy.deepcopy(derived), trainer, Path("/__UNUSED_OUTPUT__"), "990001")
    require(len(calls) == 1 and calls[0][1] == {"smoke_steps": None, "resume_pin": "latest"},
            "Native dispatch did not select the uninterrupted resume path")
    argv = functions["launcher"](Path("/__NODE_LOCAL_KIT__"), "u", "0", derived)
    require("--nproc-per-node=4" in argv and argv[-2:] == ["u", "0"], "Native launcher arguments differ")
    return {
        "status": "PASS_NATIVE_ARGUMENT_BINDING_NO_TRAINING",
        "mode": "u", "arm": "0", "resume_pin": "latest", "smoke_steps": None,
        "saved_step": 544, "first_step": 545, "target_step": 1000, "remaining_steps": 456,
        "effective_config_sha256": CONFIG_SHA, "recipe_sha256": sha(canonical(recipe)),
        "launcher_argv_with_symbolic_paths": argv,
        "scope": "Pinned native argument functions with a stub trainer; symbolic node-local paths; zero optimizer updates",
        "wrapper_reused": True, "job_sh_reused": True, "new_resume_flags": [],
        "first_step_admission": derived["first_step_admission"],
        "save_rule": "First admitted resumed update, 7200-second cadence, and final/guarded stop",
        "milestone_export_steps": [600, 800, 1000],
        "milestones_alone_force_full_checkpoint": False,
        "expected_effective_config_rechecked_in_future_job": True,
    }


def input_inventory(admission_records, admission_pins, logical_root):
    root = PurePosixPath(logical_root)
    pins = {}

    def add(path, digest, size=None):
        relative = PurePosixPath(path).relative_to(root)
        require(relative.parts and ".." not in relative.parts, "Input path escapes the run")
        require(isinstance(digest, str) and HEX.fullmatch(digest), "Input hash is malformed")
        name = str(relative)
        require(name not in pins or pins[name]["sha256"] == digest, "Conflicting input pins")
        value = {"member": "inputs/" + name, "sha256": digest}
        if size is not None:
            value["bytes"] = size
        pins[name] = {**pins.get(name, {}), **value}

    def visit(value):
        if isinstance(value, dict):
            path = value.get("path")
            if isinstance(path, str) and path.startswith(str(root) + "/") and "sha256" in value:
                add(path, value["sha256"], value.get("bytes"))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for name, pin in admission_pins.items():
        add(str(root / name), pin["sha256"], pin["bytes"])
    for record in admission_records.values():
        visit(record)
    return {
        "scope": "Expected hash-pinned run-input paths in held metadata; not an archive-header or staged-filesystem inventory",
        "members": [pins[key] for key in sorted(pins)],
        "preserve_entire_inputs_directory": True,
        "other_regular_inputs_not_enumerated": True,
        "staged_inputs_presence_verified_now": False,
    }


def timing_projection(snapshot, audit, reconciliation, derived):
    metrics = snapshot["metrics"]["metrics_169097.jsonl"]
    require(metrics["stable_read"] is True and not metrics.get("integrity_error"), "Metric snapshot is not validated")
    recent = metrics["summary"]["last_three_step_seconds"]
    require(len(recent) == 3 and all(type(value) in (int, float) and math.isfinite(value) and value > 0
                                    for value in recent), "Timing sample differs")
    first = json.loads(metrics["first_line"])
    first_step = max(rank["wall_seconds"] for rank in first["ranks"])
    model_export = max(rank["export_seconds"] for rank in first["ranks"])
    save = next(value["seconds"] for value in metrics["summary"]["recent_saves"] if value["step"] == 544)
    slot = reconciliation["slot"]
    start_line = next(line for line in snapshot["logs"]["169097.w.steps"]["tail"].splitlines()
                      if "wrapper start on " in line)
    start = datetime.datetime.fromisoformat(start_line.split(" | ")[0].replace("Z", "+00:00"))
    attempt = audit["metadata"]["native_attempt"]["identity"]["ctime_ns"] / 1e9
    startup = attempt - start.timestamp()
    uploads = []
    for line in snapshot["logs"]["gcs.log"]["tail"].splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (record.get("gcsput") == "split" and "/469ddece_" in record.get("name", "")
                and record.get("uploaded") == 4 and record.get("failed") == 0):
            uploads.append(record["seconds"])
    require(len(uploads) == 6, "Completed upload timing inventory differs")
    steady = statistics.mean(recent)
    restore = slot["bytes"] / 163_000_000
    end_slot = slot["wrapper_write_seconds"] + max(slot["wrapper_verify_seconds"], restore) + 120
    step_work = first_step + 455 * steady
    save_allowance = 12 * save
    export_allowance = 3 * (max(model_export, derived["schedule"]["export_seconds"]) + 300 + max(uploads))
    total = startup + restore + step_work + save_allowance + export_allowance + end_slot
    free = snapshot["project_free_bytes"]
    return {
        "scope": "Conditional arithmetic scenario, not a measured resume or completion guarantee",
        "recent_validated_step_seconds": recent, "recent_sample_count": 3, "recent_mean_seconds": steady,
        "raw_456_steps_seconds": 456 * steady, "cold_first_step_seconds": first_step,
        "cold_wrapper_to_attempt_seconds": startup, "steps_with_cold_first_step_allowance_seconds": step_work,
        "cold_first_export_seconds": model_export, "completed_upload_seconds": uploads,
        "latest_save_four_rank_max_seconds": save, "save_count_allowance": 12,
        "save_allowance_seconds": save_allowance,
        "restore_measured": False, "restore_io_scenario_seconds": restore,
        "restore_io_basis": "112988477440 bytes / 163 MB/s; excludes unmeasured extraction and state loading",
        "observed_slot_write_seconds": slot["wrapper_write_seconds"],
        "observed_slot_verify_seconds": slot["wrapper_verify_seconds"],
        "end_slot_scenario_seconds": end_slot, "slot_setup_allowance_seconds": 120,
        "native_export_allowance_each_seconds": max(model_export, derived["schedule"]["export_seconds"]),
        "tar_pack_allowance_each_seconds": 300, "three_exports_allowance_seconds": export_allowance,
        "upload_budget_uses_whole_four_part_durations": True,
        "advanced_allocation_scenario_total_seconds": total,
        "remaining_to_24_hours_seconds": 86400 - total,
        "remaining_after_one_hour_reserve_seconds": 86400 - 3600 - total,
        "separate_real_cpu_checker_charged_to_advanced_clock": False,
        "additional_unmeasured_work": [
            "Cold extraction and node-local checksum passes",
            "Production optimizer/state deserialization beyond the cold-start allowance",
            "Preparation reuse or rebuild, shared-load variation and transfer retries",
        ],
        "native_guard_settings_changed": False, "completion_guaranteed": False,
        "space_sample_at": snapshot["checked_at"], "space_sample_free_bytes": free,
        "slot_B_reference_bytes": slot["bytes"], "reference_free_after_B_bytes": free - slot["bytes"],
        "reference_slot_guard_bytes": slot["bytes"] + 20_000_000_000,
        "fresh_project_space_gate_passed": False, "slot_A_preserved_while_B_is_written": True,
    }


def evaluate():
    primary, sources, admission_pins, evidence_pins, raw_files = load_inputs()

    def record(pin):
        return json.loads(raw_files[Path(pin["path"]).name])

    evidence = {key: record(pin) for key, pin in evidence_pins.items()
                if key not in ("slot_sha_record", "terminal_accounting")}
    admission = {key: record(pin) for key, pin in admission_pins.items()}
    source = {key: record(pin) for key, pin in sources.items() if Path(pin["path"]).suffix == ".json"}
    binding = evidence["native_binding"]
    config_name = "prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json"
    preparation_name = "prepare_dd26bb95f37a43789206c6e4d4cd94bd/prepared/s1_receipt.json"
    require(admission_pins[preparation_name]["sha256"] == binding["preparation"]["sha256"],
            "Held preparation does not match the saved native binding")
    data = admission["data_receipt.json"]
    require(data["config"]["sha256"] == admission_pins[config_name]["sha256"],
            "Admission did not bind the held derived configuration")
    require(evidence["native_attempt"]["binding"] == binding, "Original attempt binding differs")
    slot = verify_slot(raw_files[Path(evidence_pins["slot_record"]["path"]).name],
                       raw_files[Path(evidence_pins["slot_sha_record"]["path"]).name],
                       raw_files[Path(evidence_pins["native_complete"]["path"]).name],
                       binding, evidence["terminal_reader_result"], evidence["reconciliation"])
    arguments = prove_arguments(source["k/b02e4385.json"], admission[config_name], source["k/4.json"],
                                source["k/1.json"], source["k/launch.json"], binding, source["canary_contract"])
    inventory = input_inventory(admission, admission_pins,
                                source["k/launch.json"]["in_job_admission"]["directory"])
    timing = timing_projection(evidence["terminal_snapshot"], evidence["native_audit"],
                               evidence["reconciliation"], admission[config_name])
    return {
        "schema": "orchard-continuation-build-proof-v1",
        "status": "PASS_CPU_METADATA_AND_ARGUMENT_PROOFS_ONLY",
        "kit": "07ca49df", "run": "469ddece", "slot": slot, "arguments": arguments,
        "resume_input_inventory": inventory, "timing": timing,
        "reused_installed_files": primary["reused_installed_files"],
        "installed_wrapper_sha256": sources["installed_wrapper"]["sha256"],
        "installed_job_sh_sha256": sources["job.sh"]["sha256"],
        "new_installed_wrapper_or_job_script_required_by_native_resume": False,
        "early_loss_observer_and_stop_integration_ready": False,
        "staged_input_declarations": [sources["k/0.json"], sources["k/staging.json"]],
        "checker_contract": sources["canary_contract"],
        "input_ledgers": LEDGERS,
        "unexecuted_submission_example": "cd /home/jjyeung/okit && env -u TK_JOB_START sbatch /home/jjyeung/okit/j/07ca49df.sh",
        "submission_example_is_authority": False,
        "build_only": True, "launch_authorized": False, "reservation_authorized": False,
        "native_calls": 0, "state_payload_reads": 0, "optimizer_updates": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(output.is_absolute() and output.parent == ROOT, "Output must be a new file in the isolated build directory")
    result = evaluate()
    with output.open("xb") as stream:
        stream.write(json_bytes(result))
    print(result["status"], sha(output.read_bytes()), str(output))


if __name__ == "__main__":
    main()
