from .orchard_paths import resolve_read, enabled as orchard_enabled, owned as orchard_owned
import copy
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from itertools import groupby
from pathlib import Path

from .common import REPO, binding, canonical_bytes, digest_json, io_threads, load_json, memoize_io, ordered_io, sha256

SCRATCH_HOME = Path("/scratch/jjyeung")
PUBLISH_HOME = Path("/data3/jjyeung")
RESERVE_BYTES = 150 * 1024**3
MAX_DIRECTORY_FILES = 40_000
SMOKE_PURPOSE = "Infrastructure smoke only; not a distillation target or benchmark result"


def provisional_flags(label):
    if label is None:
        return {}
    from .provisional import flags
    return flags(label)


def require_mode(value, label):
    if label is None:
        if value.get("provisional_diagnostic") is not None:
            raise ValueError("Provisional artifacts require their explicit matching flag")
        return value
    from .provisional import require_mode as check
    return check(value, label)


def tag(value, label):
    if label is None:
        return require_mode(value, None)
    from .provisional import tag as label_artifact
    return label_artifact(value, label)


def adapter_directory(label):
    return "adapter" if label is None else "adapter-" + provisional_flags(label)["provisional_diagnostic"]


def scratch_directory(root):
    if root is None:
        raise ValueError("An explicit --scratch-root under /scratch/jjyeung is required")
    root = Path(root).resolve()
    if (not root.is_relative_to(SCRATCH_HOME) and not (orchard_enabled() and root.is_relative_to(Path("/tmp/jjyeung")))) or not root.is_dir():
        raise ValueError("Scratch root must be an existing directory under /scratch/jjyeung")
    return root


def output_path(path, scratch_root=None, new=False):
    path = Path(path).resolve()
    root = scratch_directory(scratch_root) if scratch_root is not None else REPO
    if not path.is_relative_to(root) or path == root or (scratch_root is None and path.is_relative_to(SCRATCH_HOME)):
        raise ValueError("Output must stay inside the repository or the explicit node-local scratch root")
    if new and path.exists():
        raise ValueError(f"Use a new output path; existing artifacts remain immutable: {path}")
    return path


def ensure_free_space(path, additional_bytes=0):
    existing = Path(path)
    while not existing.exists():
        existing = existing.parent
    if shutil.disk_usage(existing).free - additional_bytes < RESERVE_BYTES:
        raise ValueError("Node-local storage must retain at least 150 GiB free")


def directory_capacity(path):
    with os.scandir(path) as entries:
        if sum(1 for _ in entries) >= MAX_DIRECTORY_FILES:
            raise ValueError("The directory file limit would be exceeded")


def contained(root, path):
    root = Path(root).resolve()
    path = Path(path)
    path = (path if path.is_absolute() else root / path).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError("Artifact path escapes its output directory")
    return path


def write_new(path, value, root):
    path = contained(root, path)
    if path.exists():
        raise ValueError(f"Refusing to replace an existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    directory_capacity(path.parent)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
    return path


def code_provenance(config):
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, capture_output=True,
                            text=True, env=environment).stdout.strip()
    status = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=normal"],
                            check=True, capture_output=True, text=True, env=environment).stdout.strip()
    if status:
        raise ValueError("Training, evaluation, and publication require a clean committed worktree")
    return {"commit": commit, "dirty": False, "config_sha256": digest_json(config),
            "recorded_at": datetime.now(timezone.utc).isoformat()}


class RunArtifacts:
    def __init__(self, output, config, scratch_root=None):
        self.root = output_path(output, scratch_root, new=True)
        self.provenance = code_provenance(config)
        self.provisional_diagnostic = config.get("provisional_diagnostic")
        self.flags = {"infrastructure_only": bool(config.get("infrastructure_only", False)),
                      "benchmark_improvement_claim": False, "score_nomination_allowed": False,
                      **provisional_flags(self.provisional_diagnostic)}
        if self.provisional_diagnostic is not None:
            self.flags["PROVISIONAL_DIVISION_SHA"] = config["PROVISIONAL_DIVISION_SHA"]
        if self.flags["infrastructure_only"]:
            self.flags.update(detailed_distillation=False, purpose=SMOKE_PURPOSE)
        if scratch_root is not None:
            ensure_free_space(self.root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.write("provenance.json", {})
        self.write("config.json", {"config": config})

    def record(self, value):
        return {**tag(value, self.provisional_diagnostic), **self.flags, "provenance": self.provenance}

    def write(self, path, value):
        return write_new(path, self.record(value), self.root)


def copy_new(source, destination, expected_sha256, *, read_path=None):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    directory_capacity(destination.parent)
    with Path(source).open("rb") as reader, destination.open("xb") as writer:
        shutil.copyfileobj(reader, writer, length=8 * 1024 * 1024)
    if read_path is None:
        binding(destination, expected_sha256)
    else:
        return binding(destination, expected_sha256, read_path=read_path)


def stage_frames(rows, output, scratch_root):
    workers = io_threads()
    if workers != 1:
        return _stage_frames_parallel(rows, output, scratch_root, workers)
    output = output_path(output, scratch_directory(scratch_root), new=True)
    sources = {}
    for row in rows:
        if row.get("student_input") is None:
            continue
        for frame in row["student_input"]["frames"]:
            if not re.fullmatch(r"[0-9a-f]{64}", frame["sha256"]):
                raise ValueError("Frame staging requires a complete SHA256 digest")
            source = resolve_read(frame["path"])
            if frame["path"] not in sources:
                binding(source, frame["sha256"])
                sources[frame["path"]] = {**frame, "bytes": source.stat().st_size}
    unique = {frame["sha256"]: frame for frame in sources.values()}
    ensure_free_space(output, sum(frame["bytes"] for frame in unique.values()))
    output.mkdir(parents=True, exist_ok=False)
    files, destinations = [], {}
    for digest, frame in sorted(unique.items()):
        destination = output / digest[:2] / digest
        copy_new(resolve_read(frame["path"]), destination, digest)
        destinations[digest] = binding(destination)
        files.append({"source": {key: frame[key] for key in ("path", "sha256")},
                      "staged": destinations[digest], "bytes": frame["bytes"]})
    staged = copy.deepcopy(rows)
    for row in staged:
        if row.get("student_input") is not None:
            row["student_input"]["frames"] = [destinations[frame["sha256"]].copy() for frame in row["student_input"]["frames"]]
    return staged, {"schema": "student-frame-staging-v1", "files": files, "source_references": list(sources.values()),
                    "unique_frames": len(files), "staged_bytes": sum(item["bytes"] for item in files),
                    "scratch_root": str(scratch_directory(scratch_root)), "rows": len(rows),
                    **({"orchard_path_map": os.environ.get(("Q_E4" if "Q_E4" in os.environ else "STUDENT_FRAME_ROOT_MAP"))} if orchard_enabled() else {})}


def _stage_frames_parallel(rows, output, scratch_root, workers):
    output = output_path(output, scratch_directory(scratch_root), new=True)
    resolved = memoize_io(Path.resolve)
    read_path = memoize_io(lambda path: resolve_read(path, resolve=resolved), uncached=resolve_read)

    def source_frames():
        seen = set()
        for row in rows:
            if row.get("student_input") is None:
                continue
            for frame in row["student_input"]["frames"]:
                if not re.fullmatch(r"[0-9a-f]{64}", frame["sha256"]):
                    raise ValueError("Frame staging requires a complete SHA256 digest")
                source = read_path(frame["path"])
                if frame["path"] not in seen:
                    seen.add(frame["path"])
                    yield source, frame

    def verify_source(item):
        source, frame = item
        binding(source, frame["sha256"], read_path=read_path)
        return {**frame, "bytes": source.stat().st_size}

    def verify_fresh_source(frame):
        if binding(frame["path"], read_path=read_path)["sha256"] != frame["sha256"]:
            raise ValueError(f"SHA256 mismatch: {frame['path']}")

    def copy_group(items):
        files = []
        for digest, frame in items:
            destination = output / digest[:2] / digest
            copy_new(read_path(frame["path"]), destination, digest, read_path=read_path)
            staged = binding(destination, digest, read_path=read_path)
            files.append({"source": {key: frame[key] for key in ("path", "sha256")},
                          "staged": staged, "bytes": frame["bytes"]})
        return files

    with ThreadPoolExecutor(max_workers=workers) as pool:
        sources = {frame["path"]: frame for frame in ordered_io(pool, verify_source, source_frames(), workers * 2)}
        unique = {frame["sha256"]: frame for frame in sources.values()}
        ensure_free_space(output, sum(frame["bytes"] for frame in unique.values()))
        output.mkdir(parents=True, exist_ok=False)
        groups = (list(group) for _, group in groupby(sorted(unique.items()), key=lambda item: item[0][:2]))
        files = [item for group in ordered_io(pool, copy_group, groups, workers * 2) for item in group]
        destinations = {item["staged"]["sha256"]: item["staged"] for item in files}
        inputs = {id(row["student_input"]): row["student_input"] for row in rows if row.get("student_input") is not None}
        memo = {identity: {} for identity in inputs}
        for identity, value in inputs.items():
            memo[identity].update((key, [destinations[frame["sha256"]].copy() for frame in item] if key == "frames"
                                   else copy.deepcopy(item, memo)) for key, item in value.items())
        staged = copy.deepcopy(rows, memo)
        for cached in (read_path, resolved):
            cached.verify(pool, workers * 2)
        for _ in ordered_io(pool, verify_fresh_source, sources.values(), workers * 2):
            pass
    return staged, {"schema": "student-frame-staging-v1", "files": files, "source_references": list(sources.values()),
                    "unique_frames": len(files), "staged_bytes": sum(item["bytes"] for item in files),
                    "scratch_root": str(scratch_directory(scratch_root)), "rows": len(rows),
                    **({"orchard_path_map": os.environ.get(("Q_E4" if "Q_E4" in os.environ else "STUDENT_FRAME_ROOT_MAP"))} if orchard_enabled() else {})}


def localize_frames(rows, store, manifest_path, scratch_root=None, stage=False):
    if stage:
        rows, receipt = stage_frames(rows, store.root / "frames", scratch_root)
        store.write("frame_staging.json", receipt)
        store.write("frames/provenance.json", {"frame_staging": binding(store.root / "frame_staging.json")})
    elif scratch_root is not None:
        root = scratch_directory(scratch_root)
        if any(not Path(frame["path"]).resolve().is_relative_to(root)
               for row in rows if row.get("student_input") is not None for frame in row["student_input"]["frames"]):
            raise ValueError("Use --stage-frames before training or evaluating with non-local RGB frames")
    store.write("input_manifest.json", {"source_manifest": binding(manifest_path), "rows": rows})
    return rows


def write_output(path, value, scratch_root=None):
    path = output_path(path, scratch_root, new=True)
    provenance = code_provenance(value)
    if scratch_root is not None:
        ensure_free_space(path)
    return write_new(path, {**value, "provenance": provenance}, path.parent)


def publication_files(root, provisional_diagnostic=None):
    root = Path(root).resolve()
    candidates = [path for path in root.iterdir() if path.is_file()
                  and (path.suffix in (".json", ".jsonl", ".log", ".safetensors") or path.name == "auxiliary_heads.pt")
                  and path.name not in ("PUBLISHED.json", "SHA256_MANIFEST.json")]
    for name in (adapter_directory(provisional_diagnostic), "steps", "traces", "geometry"):
        directory = root / name
        if directory.is_symlink():
            raise ValueError("Publication refuses symlinked artifact directories")
        if directory.is_dir():
            candidates.extend(directory.rglob("*"))
    files = {}
    for path in sorted(candidates):
        if path.is_symlink():
            raise ValueError("Publication refuses symlinked artifacts")
        if path.is_file():
            contained(root, path)
            files[str(path.relative_to(root))] = path
    return files


def finalize(training_run, publish_root, scratch_root, evaluation_run=None, provisional_diagnostic=None):
    scratch_root = scratch_directory(scratch_root)
    training_run = output_path(training_run, scratch_root)
    publish_root = Path(publish_root).resolve()
    from .orchard_paths import PROJECT
    publish_home = PROJECT / "runs" if orchard_enabled() else PUBLISH_HOME
    if not publish_root.is_relative_to(publish_home) or publish_root == publish_home or publish_root.exists():
        raise ValueError("Publication requires a new directory under /data3/jjyeung")
    if (training_run / "PUBLISHED.json").exists():
        raise ValueError("This local run has already been published")
    result_path = training_run / "training_result.json"
    result = require_mode(load_json(result_path), provisional_diagnostic)
    if provisional_diagnostic is not None:
        if result.get("schema") != "completed-provisional-diagnostic-training-v1":
            raise ValueError("Provisional publication requires a completed provisional training run")
        from .provisional_data import load_protocol
        verify = result["protocol"]
        binding(verify["path"], verify["sha256"])
        protocol = load_protocol(verify["path"], provisional_diagnostic, student=result["student"])
        if result.get("PROVISIONAL_DIVISION_SHA") != protocol["PROVISIONAL_DIVISION_SHA"]:
            raise ValueError("Publication changed the provisional division")
        if result.get("protocol_version") is not None or protocol.get("protocol_version") is not None:
            from .ddp_config import validate_training_result
            validate_training_result(result, protocol, provisional_diagnostic)
    if result.get("status") != "TRAINED" or result.get("provenance", {}).get("dirty") is not False:
        raise ValueError("Only completed, clean-commit training runs may be published")
    adapter_files = [("weights", "adapter_model.safetensors"), ("config", "adapter_config.json")]
    if "vision_blocks" in result.get("adapter", {}):
        adapter_files.append(("vision_blocks", "vision_blocks.safetensors"))
    if "full_weights" in result.get("adapter", {}) or result.get("adapter") == {"frozen_vlm": True}:
        # Full fine-tuning publishes its BF16 export (or, in the frozen-VLM stage, only the attached modules).
        adapter_files = []
        if "full_weights" in result["adapter"]:
            from .full_ft import EXPORT_DIRECTORY, EXPORT_MANIFEST, read_export
            pin = result["adapter"]["full_weights"]
            expected = training_run / adapter_directory(provisional_diagnostic) / EXPORT_DIRECTORY / EXPORT_MANIFEST
            if Path(pin["path"]).resolve() != expected:
                raise ValueError("Full-weights identity escapes its training run")
            binding(pin["path"], pin["sha256"])
            read_export(expected.parent)
    for key, filename in adapter_files:
        pin = result["adapter"][key]
        if Path(pin["path"]).resolve() != training_run / adapter_directory(provisional_diagnostic) / filename:
            raise ValueError("Adapter identity escapes its training run")
        binding(pin["path"], pin["sha256"])
    if result.get("geometry") is not None:
        # The trained geometry projector publishes beside the unchanged LoRA adapter, under geometry/.
        for key, filename in (("weights", "geometry_projector.safetensors"), ("manifest", "geometry_input.json")):
            pin = result["geometry"][key]
            if Path(pin["path"]).resolve() != training_run / "geometry" / filename:
                raise ValueError("Geometry projector identity escapes its training run")
            binding(pin["path"], pin["sha256"])
    steps = result["realized"]["optimizer_steps"]
    if type(steps) is not int or steps < 1:
        raise ValueError("Training did not complete an optimizer step")
    for index in range(1, steps + 1):
        step = require_mode(load_json(training_run / "steps" / f"{index:04d}.json"), provisional_diagnostic)
        if step.get("step") != index or step.get("provenance") != result["provenance"]:
            raise ValueError("Optimizer step coverage or provenance changed")
    files = publication_files(training_run, provisional_diagnostic)
    if provisional_diagnostic is not None:
        files["protocol.json"] = Path(result["protocol"]["path"])
    evaluation_path = None
    if result.get("infrastructure_only") and evaluation_run is None:
        raise ValueError("Infrastructure smoke publication requires its successful reload evaluation")
    if evaluation_run is not None:
        evaluation_path = output_path(evaluation_run, scratch_root)
        completion = require_mode(load_json(evaluation_path / "completion.json"), provisional_diagnostic)
        reload_check = require_mode(load_json(evaluation_path / "adapter_reload.json"), provisional_diagnostic)
        if (reload_check.get("exact_tensor_equality") is not True
                or reload_check.get("adapter", {}).get("training_result") != binding(result_path)
                or completion.get("failed_outputs") != 0
                or completion.get("student", result.get("student")) != result.get("student")
                or completion.get("provenance", {}).get("commit") != result["provenance"]["commit"]):
            raise ValueError("Publication requires the matching successful adapter reload evaluation")
        qids = completion["attempted_qids"]
        if provisional_diagnostic is not None and (qids != protocol["division"]["heldout_qids"]
                or completion.get("PROVISIONAL_DIVISION_SHA") != protocol["PROVISIONAL_DIVISION_SHA"]
                or completion.get("cohort_size") != len(qids)):
            raise ValueError("Provisional publication requires the complete frozen heldout cohort")
        if len(set(qids)) != len(qids) or completion["successful_outputs"] != len(qids) or not qids:
            raise ValueError("Evaluation coverage is incomplete")
        for qid in qids:
            trace = require_mode(load_json(contained(evaluation_path, f"traces/{qid}.json")), provisional_diagnostic)
            if trace.get("qid") != qid or trace.get("status") != "ok":
                raise ValueError("Evaluation trace coverage is incomplete")
        files.update({"evaluation/" + name: path for name, path in publication_files(evaluation_path, provisional_diagnostic).items()})
    config = {"training_result": binding(result_path), "evaluation_run": str(evaluation_path) if evaluation_path else None,
              "publish_root": str(publish_root), "infrastructure_only": result.get("infrastructure_only", False),
              **provisional_flags(provisional_diagnostic)}
    if provisional_diagnostic is not None:
        config["PROVISIONAL_DIVISION_SHA"] = result["PROVISIONAL_DIVISION_SHA"]
    if result.get("resumed_from") is not None:
        config["resumed_from"] = result["resumed_from"]
    if "init_adapter_identity" in result:
        config.update(init_adapter_identity=result["init_adapter_identity"], init_adapter_sha256=result["init_adapter_sha256"])
    provenance = code_provenance(config)
    manifest = {name: {"sha256": sha256(path), "bytes": path.stat().st_size} for name, path in files.items()}
    publish_root.mkdir(parents=True, exist_ok=False)
    for name, path in files.items():
        copy_new(path, contained(publish_root, name), manifest[name]["sha256"])
    flags = {"infrastructure_only": config["infrastructure_only"], "benchmark_improvement_claim": False,
             "score_nomination_allowed": False, **provisional_flags(provisional_diagnostic)}
    if provisional_diagnostic is not None:
        flags["PROVISIONAL_DIVISION_SHA"] = result["PROVISIONAL_DIVISION_SHA"]
    if flags["infrastructure_only"]:
        flags["purpose"] = SMOKE_PURPOSE
    if provisional_diagnostic is not None:
        division_path = write_new("division.json", protocol["division"], publish_root)
        manifest[division_path.name] = {"sha256": sha256(division_path), "bytes": division_path.stat().st_size}
    publication = write_new("publication_provenance.json", {"config": config, "provenance": provenance, **flags}, publish_root)
    manifest[publication.name] = {"sha256": sha256(publication), "bytes": publication.stat().st_size}
    manifest_path = write_new("SHA256_MANIFEST.json", {"schema": "student-publication-sha256-v1", "files": manifest,
                              "excludes": ["SHA256_MANIFEST.json", "PUBLISHED.json"], "provenance": provenance, **flags}, publish_root)
    receipt = {"schema": "student-publication-v1", "local_path": str(training_run), "published_path": str(publish_root),
               "evaluation_path": str(evaluation_path) if evaluation_path else None, "sha256_manifest": binding(manifest_path),
               "training_result": binding(result_path), "file_count": len(manifest), "provenance": provenance, **flags}
    if provisional_diagnostic is not None:
        from .benchmark_eval.contracts import MODEL_PINS
        if orchard_enabled():
            from .orchard_eval.contracts import MODEL_PINS
        model = MODEL_PINS[result["student"]]
        if "full_weights" in result["adapter"]:
            adapter_receipt = {"full_weights_manifest_sha256": result["adapter"]["full_weights"]["sha256"]}
        elif result["adapter"] == {"frozen_vlm": True}:
            adapter_receipt = {"frozen_vlm": True}
        else:
            adapter_receipt = {"config_sha256": result["adapter"]["config"]["sha256"],
                               "weights_sha256": result["adapter"]["weights"]["sha256"]}
        if "vision_blocks" in result["adapter"]:
            adapter_receipt["vision_blocks_sha256"] = result["adapter"]["vision_blocks"]["sha256"]
        if result.get("geometry") is not None:
            adapter_receipt["geometry_weights_sha256"] = result["geometry"]["weights"]["sha256"]
        receipt.update(status="TRAINED", student=result["student"], base={key: model[key] for key in ("repo_id", "revision")},
                       base_restart=result["base_restart"], preprocessing=protocol["rgb"],
                       trained_module_families=(["vision", "merger", "language"] if "full_ft" not in result
                                                else [group for group, on in result["full_ft"]["train"].items() if on]),
                       adapter=adapter_receipt,
                       adapter_directory=adapter_directory(provisional_diagnostic),
                       training_data_sha256=result["training_manifest"]["sha256"],
                       protocol=binding(publish_root / "protocol.json"), division=binding(publish_root / "division.json"),
                       local_training_result=receipt["training_result"], training_result=binding(publish_root / "training_result.json"))
        if result.get("protocol_version") is not None:
            receipt["protocol_version"] = result["protocol_version"]
        if result.get("synthetic") is True:
            receipt["synthetic"] = True
    if result.get("resumed_from") is not None:
        receipt["resumed_from"] = result["resumed_from"]
    if "init_adapter_identity" in result:
        receipt.update(init_adapter_identity=result["init_adapter_identity"], init_adapter_sha256=result["init_adapter_sha256"])
    write_new("PUBLISHED.json", tag(receipt, provisional_diagnostic), publish_root)
    write_new("PUBLISHED.json", tag(receipt, provisional_diagnostic), training_run)
    return receipt
