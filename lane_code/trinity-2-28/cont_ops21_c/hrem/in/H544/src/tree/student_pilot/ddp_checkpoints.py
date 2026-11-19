import copy
import json
import math
import os
import random
import re
import shutil
import signal
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import torch
import torch.distributed as dist

from .common import binding, canonical_bytes, digest_json, load_json, sha256
from .ddp_config import DEFAULTS, frozen_groups
from .ddp_core import schedule_lr, select_microbatch
from .provisional import require_mode, source_path
from .storage import (RunArtifacts, code_provenance, contained, copy_new, ensure_free_space,
                      localize_frames, output_path, provisional_flags, publication_files)


SCHEMA = "student-ddp-checkpoint-v1"
STATE_FILES = {"adapters.pt", "optimizer.pt", "rng.pt", "scheduler.json"}
# Full fine-tuning checkpoints (format rank_sharded_v2): every rank's base shards and their optimizer state, plus the
# replicated attached modules and their optimizer state once (replicated.pt, written by rank 0).
FULL_FORMAT = "rank_sharded_v2"
FULL_STATE_FILES = {"rng.pt", "scheduler.json", "layout.json"}
REPLICATED_FILE = "replicated.pt"
REQUIRED_ARTIFACTS = {"config.json", "provenance.json", "run.json", "metrics.jsonl", "batch_plan.json"}
# Retention: milestone (every checkpoint_every_steps), final, signal (a graceful stop) and parent (the checkpoint a run
# resumed from) checkpoints are pinned in PINNED.jsonl and never pruned, so a run that ends, pauses or is cancelled
# always has its newest full checkpoint pinned. Rolling and epoch-end checkpoints form the rolling pool, which keeps its
# newest ROLLING_KEEP members that no PINNED.jsonl row names (rows appended by external tools count too).
PINNED_KINDS = ("milestone", "final", "signal", "parent")
POOL_KINDS = ("rolling", "epoch")
ROLLING_KEEP = 3
# Full fine-tuning: a full state (FP32 masters + AdamW, ~113 GB for Qwen3.5-9B) serves only to resume, so the rolling
# pool holds every rolling, epoch, milestone and final state and keeps the newest FULL_ROLLING_KEEP; a signal stop, a
# gate stop and a resumed run's parent stay pinned. Each milestone also pins a milestone export (MILESTONES.jsonl):
# the BF16 cast of the masters plus the FP32 attached modules (~21 GB), the files a publication carries.
FULL_PINNED_KINDS = ("signal", "scheduled", "parent")
FULL_POOL_KINDS = ("rolling", "epoch", "milestone", "final")
FULL_ROLLING_KEEP = 2
MILESTONE_LEDGER = "MILESTONES.jsonl"
MILESTONE_SCHEMA = "full-ft-milestone-export-v1"
STALE_TEMPORARY = re.compile(r"\.(step|milestone)_\d+_[0-9a-f]{32}\.tmp")
PINNED_LEDGER = "PINNED.jsonl"
ROLLING_LEDGER = "ROLLING.jsonl"
SAVING_MARKER = "SAVE_IN_PROGRESS.json"
STOP_MARKER = "STOPPED_ON_SIGNAL.json"
STOP_SIGNALS = (signal.SIGUSR1, signal.SIGTERM)


def targets_identity(settings):
    """A frozen-target or unfrozen-vision run records its target options; the default option stays implicit."""
    result = {"targets": settings["targets"]} if frozen_groups(settings) else {}
    if settings.get("unfreeze_vision_blocks"):
        result["unfreeze_vision_blocks"] = True
        result["vision_learning_rate"] = settings["vision_learning_rate"]
    if "head_learning_rate" in settings:
        result["head_learning_rate"] = settings["head_learning_rate"]
    if "full_ft" in settings:
        result["full_ft"] = settings["full_ft"]
    return result


def run_identity(header):
    return {"protocol_sha256": header["protocol"]["sha256"],
            "config_sha256": header["provenance"]["config_sha256"], "commit": header["provenance"]["commit"],
            "world_size": header["world_size"], "parallel": header["parallel"],
            **({"init_adapter_sha256": header["init_adapter_sha256"]} if "init_adapter_sha256" in header else {}),
            **targets_identity(header["settings"])}


def rng_state():
    numpy = np.random.get_state()
    return {"python": random.getstate(), "numpy": (numpy[0], torch.tensor(numpy[1].astype(np.int64)), *numpy[2:]),
            "torch": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []}


def restore_rng(state):
    numpy = state["numpy"]
    random.setstate(state["python"])
    np.random.set_state((numpy[0], numpy[1].numpy().astype(np.uint32), *numpy[2:]))
    torch.set_rng_state(state["torch"])
    devices = torch.cuda.device_count() if torch.cuda.is_initialized() else 0
    if len(state["cuda"]) != devices:
        raise ValueError("Checkpoint RNG CUDA device count changed")
    if devices:
        torch.cuda.set_rng_state_all(state["cuda"])


def cpu_state(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_state(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(cpu_state(item) for item in value)
    return value


def optimizer_names(adapters, optimizer):
    names = {id(parameter): name for name, parameter in adapters.items()}
    parameters = [parameter for group in optimizer.param_groups for parameter in group["params"]]
    if (not names or len(names) != len(adapters) or len(parameters) != len(names)
            or {id(parameter) for parameter in parameters} != set(names)
            or any(not parameter.requires_grad for parameter in parameters)):
        raise ValueError("Checkpoint optimizer must contain only the exact trainable adapter allowlist")
    return [[names[id(parameter)] for parameter in group["params"]] for group in optimizer.param_groups]


def resumed_microbatch(reports, world_size, batch_size, checkpoint=None, exact=False):
    if exact:
        # Multi-node training takes the exact batch with no accumulation, so the only usable microbatch is
        # batch / world; the timing heuristic must not pick a smaller size that the exact-batch rule then refuses.
        size = batch_size // world_size
        if (batch_size % world_size or len(reports) != world_size
                or any(not any(trial["microbatch"] == size and trial["fits"] for trial in report["trials"])
                       for report in reports)):
            raise ValueError("Multi-node training requires the exact per-rank microbatch to fit on every leased GPU")
        if checkpoint is not None and checkpoint["state"]["microbatch_size"] != size:
            raise ValueError("Resume requires the checkpoint microbatch to equal the exact multi-node microbatch")
        return size
    selected = select_microbatch(reports, world_size, batch_size)
    if checkpoint is None:
        return selected
    saved = checkpoint["state"]["microbatch_size"]
    if any(not any(trial["microbatch"] == saved and trial["fits"] for trial in report["trials"]) for report in reports):
        raise ValueError("Resume requires the checkpoint microbatch to pass every fresh memory probe")
    return saved


def due(step, batch_index, steps_per_epoch, stop_steps, run_control):
    return milestone_due(step, run_control) or batch_index + 1 == steps_per_epoch or step == stop_steps


def milestone_due(step, run_control):
    if 'checkpoint_milestones' in run_control:
        return step in run_control['checkpoint_milestones']
    return step % run_control['checkpoint_every_steps'] == 0


def validate_progress(checkpoint, settings):
    state = checkpoint["state"]
    step = checkpoint["step"]
    rows, microbatch = state["row_count"], state["microbatch_size"]
    if type(rows) is not int or rows < 1 or type(microbatch) is not int or not 1 <= microbatch <= settings["max_microbatch_size"]:
        raise ValueError("Invalid checkpoint row count or microbatch")
    per_epoch = math.ceil(rows / settings["effective_batch_size"])
    planned = per_epoch * settings["epochs"]
    if 'full_ft' in settings:
        from .full_ft import scheduler_steps
        planned = scheduler_steps(settings['full_ft'], planned, settings['max_steps'])
    if (type(step) is not int or not 1 <= step <= min(planned, settings["max_steps"] or planned)
            or state["planned_steps"] != planned or state["realized"]["optimizer_steps"] != step
            or checkpoint["metrics_line_count"] != step
            or checkpoint["batch_plan_position"] != {"epoch": step // per_epoch, "batch_index": step % per_epoch}
            or checkpoint["epoch"] != step // per_epoch):
        raise ValueError("Checkpoint counters differ from the deterministic batch-plan position")
    return per_epoch


def validate_metrics(path, header, count):
    actual = 0
    with Path(path).open() as stream:
        for actual, line in enumerate(stream, 1):
            record = json.loads(line)
            if record.get("step") != actual or record.get("provenance") != header["provenance"]:
                raise ValueError("Checkpoint metric coverage or provenance changed")
    if actual != count:
        raise ValueError("Checkpoint metrics line count differs from the completed optimizer steps")


def archive(path, destination):
    path, destination = Path(path), Path(destination)
    if destination.exists() or destination.is_symlink():
        destination = destination.with_name(destination.name + "_" + uuid4().hex)
    destination.parent.mkdir(parents=True, exist_ok=True)
    path.rename(destination)
    return destination


def active_checkpoints(root):
    if root.is_symlink() or (root / "_superseded").is_symlink():
        raise ValueError("Checkpoint storage directories must not be symlinks")
    if not root.exists():
        return []
    result = []
    for path in root.iterdir():
        match = re.fullmatch(r"step_([0-9]+)", path.name)
        if match:
            if path.is_symlink() or not path.is_dir():
                raise ValueError("Checkpoint entries must be real directories")
            result.append((int(match[1]), path))
    return sorted(result)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_checkpoint(store, header, adapters, optimizer, state, rank_rng, full_state=None, archive_older=True):
    step = state["realized"]["optimizer_steps"]
    settings = header["settings"]
    per_epoch = math.ceil(state["row_count"] / settings["effective_batch_size"])
    position = {"epoch": step // per_epoch, "batch_index": step % per_epoch}
    metadata = {"schema": SCHEMA, "identity": run_identity(header), "step": step, "epoch": position["epoch"],
                "batch_plan_position": position, "metrics_line_count": step, "state": state,
                "optimizer_parameters": optimizer_names(adapters, optimizer)}
    validate_progress(metadata, settings)
    if len(rank_rng) != header["world_size"]:
        raise ValueError("Checkpoint requires RNG state from every rank")
    root = store.root / "checkpoints"
    previous = active_checkpoints(root)
    weights = {name: cpu_state(full_state[name] if full_state is not None else parameter)
               for name, parameter in adapters.items()}
    optimizer_state = cpu_state(optimizer.state_dict())
    ensure_free_space(store.root, sum(tensor.numel() * tensor.element_size() for tensor in weights.values()) * 4)
    root.mkdir(exist_ok=True)
    final = root / f"step_{step}"
    if final.exists() or final.is_symlink():
        raise ValueError("Refusing to replace an existing checkpoint")
    temporary = root / f".step_{step}_{uuid4().hex}.tmp"
    temporary.mkdir()
    for name, value in (("adapters.pt", weights), ("optimizer.pt", optimizer_state), ("rng.pt", rank_rng)):
        with (temporary / name).open("xb") as stream:
            torch.save(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
    scheduler = {"completed_steps": step, "total_steps": state["planned_steps"], "settings_sha256": digest_json(settings),
                 "last_lr": [group["lr"] for group in optimizer.param_groups]}
    (temporary / "scheduler.json").write_bytes(canonical_bytes(scheduler))
    artifacts = publication_files(store.root, store.provisional_diagnostic)
    if not REQUIRED_ARTIFACTS <= artifacts.keys():
        raise ValueError("Checkpoint is missing its run header, provenance, batch plan, or metrics")
    names = set(STATE_FILES)
    for name, path in artifacts.items():
        relative = "artifacts/" + name
        copy_new(path, temporary / relative, sha256(path))
        names.add(relative)
    validate_metrics(temporary / "artifacts/metrics.jsonl", header, step)
    metadata["files"] = {}
    for name in sorted(names):
        path = temporary / name
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
        metadata["files"][name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    with (temporary / "checkpoint.json").open("xb") as stream:
        stream.write(canonical_bytes(metadata))
        stream.flush()
        os.fsync(stream.fileno())
    for directory in sorted({(temporary / name).parent for name in names}, key=lambda path: len(path.parts), reverse=True):
        sync_directory(directory)
    sync_directory(temporary)
    temporary.rename(final)
    sync_directory(root)
    if archive_older:
        for _, older in sorted([*previous, (step, final)])[:-2]:
            archive(older, root / "_superseded" / older.name)
    return final


def durable_root(store):
    """Where resume looks for checkpoints: the Orchard/code-aws published root, else the run's own checkpoints."""
    from .orchard_paths import enabled
    return Path(os.environ["ORCHARD_CHECKPOINT_ROOT"]).resolve() if enabled() else store.root / "checkpoints"


def ledger_directory(store):
    """PINNED.jsonl and ROLLING.jsonl live in the published run root (the parent of ORCHARD_CHECKPOINT_ROOT); a local
    run keeps them inside its checkpoints directory, outside the artifacts that checkpoints and publications copy."""
    from .orchard_paths import enabled
    root = durable_root(store)
    return root.parent if enabled() else root


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_ledger(path, strict=True):
    """The ledger's JSON rows. strict=False skips lines that are not a JSON object instead of raising."""
    try:
        with Path(path).open() as stream:
            lines = [line for line in stream if line.strip()]
    except FileNotFoundError:
        return []
    rows = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            if strict:
                raise
            continue
        if isinstance(row, dict):
            rows.append(row)
        elif strict:
            raise ValueError(f"{path} has a row that is not a JSON object")
    return rows


def pinned_ledgers(store):
    """Every PINNED.jsonl that can protect this run's checkpoints: the trainer's own ledger and the run root's (the
    parent of the durable checkpoint root, where external pin tools append), which coincide on Orchard and code-aws."""
    return list(dict.fromkeys((ledger_directory(store) / PINNED_LEDGER,
                               durable_root(store).resolve().parent / PINNED_LEDGER)))


def pinned_set(store):
    """(resolved checkpoint directories, checkpoint.json sha256s) named by any PINNED.jsonl row. A relative row path
    is read against the ledger's directory; the sha256 also protects a checkpoint whose row names it by another path.
    Rows may carry any other keys (an external tool's rows have no "kind"); only "path" and "sha256" are read."""
    paths, digests = set(), set()
    for ledger in pinned_ledgers(store):
        for row in read_ledger(ledger):
            if isinstance(row.get("path"), str) and row["path"]:
                paths.add((ledger.parent / row["path"]).resolve())
            if isinstance(row.get("sha256"), str) and row["sha256"]:
                digests.add(row["sha256"])
    return paths, digests


def is_pinned(store, path, pinned=None):
    paths, digests = pinned if pinned is not None else pinned_set(store)
    local = store.root / "checkpoints" / path.name
    if {path.resolve(), local.resolve()} & paths:
        return True
    manifest = path / "checkpoint.json"
    return manifest.is_file() and sha256(manifest) in digests


def append_ledger(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def checkpoint_bytes(directory):
    return sum(path.stat().st_size for path in Path(directory).rglob("*") if path.is_file() and not path.is_symlink())


def pin_record(directory, kind):
    """One PINNED.jsonl line: sha256 is the SHA-256 of the checkpoint's checkpoint.json, which pins every file's bytes."""
    directory = Path(directory)
    manifest = load_json(directory / "checkpoint.json")
    return {"path": str(directory), "step": manifest["step"], "bytes": checkpoint_bytes(directory),
            "sha256": sha256(directory / "checkpoint.json"), "kind": kind, "utc": utc_now()}


def pin_parent(store, directory):
    """Pin the checkpoint a resumed run starts from, so that its own rolling retention can never prune it."""
    directory = Path(directory).resolve()
    ledger = ledger_directory(store) / PINNED_LEDGER
    rows = read_ledger(ledger, strict=False)
    if all(not isinstance(row.get("path"), str) or (ledger.parent / row["path"]).resolve() != directory
           for row in rows):
        append_ledger(ledger, pin_record(directory, "parent"))
    return directory


def checkpoint_kind(step, stop_steps, run_control, scheduled, stopping):
    if step == stop_steps:
        return "final"
    if milestone_due(step, run_control):
        return "milestone"
    return "signal" if stopping else "epoch" if scheduled else "rolling"


def remove_checkpoint(directory):
    hidden = directory.with_name(f".pruned_{directory.name}_{uuid4().hex}")
    directory.rename(hidden)
    shutil.rmtree(hidden)


def prune_rolling(store, step, keep=ROLLING_KEEP, kinds=POOL_KINDS):
    """Remove unpinned rolling-pool checkpoints beyond the newest `keep` unpinned ones: only ROLLING.jsonl members,
    never one that a PINNED.jsonl row names (by resolved durable or node-local directory, or by checkpoint.json
    sha256). PINNED.jsonl is re-read here and again before each removal, so a row an external tool appended since the
    last save protects its checkpoint; an unreadable PINNED.jsonl stops the prune (it raises)."""
    root, ledger = durable_root(store).resolve(), ledger_directory(store)
    pinned = pinned_set(store)
    pool = {}
    for entry in read_ledger(ledger / ROLLING_LEDGER):
        path = Path(entry["path"])
        if (entry.get("event") == "written" and entry["kind"] in kinds and entry["step"] <= step
                and path.parent == root and path.name == f"step_{entry['step']}"):
            pool[entry["step"]] = path
    live = [(number, path) for number, path in sorted(pool.items())
            if path.is_dir() and not path.is_symlink() and not is_pinned(store, path, pinned)]
    removed = []
    for number, path in live[:-keep] if keep > 0 else live:
        if is_pinned(store, path):
            continue  # pinned while this prune ran
        local = store.root / "checkpoints" / path.name
        for directory in dict.fromkeys((path, local)):
            if directory.is_dir() and not directory.is_symlink():
                remove_checkpoint(directory)
                removed.append(str(directory))
        append_ledger(ledger / ROLLING_LEDGER, {"event": "pruned", "step": number, "path": str(path), "utc": utc_now()})
    return removed


@contextmanager
def saving_marker(store, step, kind):
    """SAVE_IN_PROGRESS.json in the durable checkpoint root while rank 0 writes; the GPU sidecar skips idle samples."""
    root = durable_root(store)
    root.mkdir(parents=True, exist_ok=True)
    marker = root / SAVING_MARKER
    marker.write_text(json.dumps({"step": step, "kind": kind, "pid": os.getpid(), "utc": utc_now()}) + "\n")
    try:
        yield
    finally:
        try:
            marker.unlink()
        except FileNotFoundError:
            pass


def retain(store, header, local, kind):
    """Publish, verify with the resume reader, record, then prune: nothing is pruned unless the new one verifies."""
    from .orchard_paths import enabled
    durable = local
    if enabled():
        from .orchard_checkpoints import publish
        durable = publish(local)
    durable = Path(durable).resolve()
    read_checkpoint(durable, run_identity(header))
    ledger = ledger_directory(store)
    step = load_json(durable / "checkpoint.json")["step"]
    if kind in PINNED_KINDS:
        append_ledger(ledger / PINNED_LEDGER, pin_record(durable, kind))
    else:
        append_ledger(ledger / ROLLING_LEDGER, {"event": "written", "step": step, "kind": kind,
                                                 "path": str(durable), "utc": utc_now()})
    try:
        removed = prune_rolling(store, step)
    except Exception as error:
        print(f"ROLLING_PRUNE_FAILED step={step} {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        removed = []
    return durable, removed


def save_checkpoint(store, header, adapters, optimizer, state, distributed=None, kind=None):
    """kind=None keeps the original retention (archive all but the newest two); a training-loop kind applies the
    pinned/rolling retention of retain()."""
    rank = dist.get_rank()
    local_rng = rng_state()
    rank_rng = [None] * dist.get_world_size() if rank == 0 else None
    dist.gather_object(local_rng, rank_rng, dst=0)
    outcome = [None]
    try:
        full_state = None
        # The frozen-VLM stage's trainables are replicated attached modules: no sharded state to gather.
        if header["parallel"] == "fsdp" and "full_ft" not in header["settings"]:
            from .fsdp_training import publication_state
            full_state = publication_state(distributed)
        if rank == 0:
            try:
                if kind is None:
                    path = write_checkpoint(store, header, adapters, optimizer, state, rank_rng, full_state)
                    from .orchard_paths import enabled
                    if enabled():
                        from .orchard_checkpoints import publish
                        publish(path)
                    outcome[0] = {"path": str(path)}
                else:
                    with saving_marker(store, state["realized"]["optimizer_steps"], kind):
                        path = write_checkpoint(store, header, adapters, optimizer, state, rank_rng, full_state,
                                                archive_older=False)
                        durable, removed = retain(store, header, path, kind)
                    outcome[0] = {"path": str(path), "durable": str(durable), "kind": kind, "pruned": removed}
            except Exception as error:
                outcome[0] = {"error": f"{type(error).__name__}: {error}"}
        dist.broadcast_object_list(outcome, src=0)
        if "error" in outcome[0]:
            raise ValueError("Checkpoint failed: " + outcome[0]["error"])
        return outcome[0]["path"] if kind is None else outcome[0]
    finally:
        restore_rng(local_rng)


def save_full_checkpoint(store, header, trainables, optimizer, state, layout_sha256, kind):
    """Full fine-tuning: every rank writes its shard straight into the durable root; rank 0 seals the directory.

    The durable root (ORCHARD_CHECKPOINT_ROOT on code-aws, else the run's checkpoints/) must be visible to every
    rank. Retention is retain_full()'s rule, without a copy: the checkpoint is written where it stays."""
    from .full_ft import is_replicated, write_rank_shard
    rank, world = dist.get_rank(), dist.get_world_size()
    local_rng = rng_state()
    rank_rng = [None] * world if rank == 0 else None
    dist.gather_object(local_rng, rank_rng, dst=0)
    step = state["realized"]["optimizer_steps"]
    target = [None]
    if rank == 0:
        try:
            root = durable_root(store)
            root.mkdir(parents=True, exist_ok=True)
            final = root / f"step_{step}"
            if final.exists() or final.is_symlink():
                raise ValueError("Refusing to replace an existing checkpoint")
            remove_stale_temporaries(root)
            local_bytes = sum(parameter.numel() * 4 for name, parameter in trainables.items() if not is_replicated(name))
            replicated_bytes = sum(parameter.numel() * 4 for name, parameter in trainables.items() if is_replicated(name))
            ensure_free_space(root, 3 * (local_bytes * world + replicated_bytes))
            temporary = root / f".step_{step}_{uuid4().hex}.tmp"
            temporary.mkdir()
            target[0] = {"temporary": str(temporary), "final": str(final)}
        except Exception as error:
            target[0] = {"error": f"{type(error).__name__}: {error}"}
    dist.broadcast_object_list(target, src=0)
    if "error" in target[0]:
        raise ValueError("Checkpoint failed: " + target[0]["error"])
    temporary, final = Path(target[0]["temporary"]), Path(target[0]["final"])
    outcome = [None]
    try:
        try:
            pin = write_rank_shard(temporary, rank, list(trainables.items()), optimizer, layout_sha256)
        except Exception as error:
            pin = {"error": f"rank {rank}: {type(error).__name__}: {error}"}
        pins = [None] * world if rank == 0 else None
        dist.gather_object(pin, pins, dst=0)
        if rank == 0:
            try:
                errors = [item["error"] for item in pins if "error" in item]
                if errors:
                    raise ValueError("; ".join(errors))
                with saving_marker(store, step, kind):
                    path = seal_full_checkpoint(store, header, trainables, optimizer, state, rank_rng, pins,
                                                layout_sha256, temporary, final)
                    durable, removed = retain_full(store, header, path, kind)
                outcome[0] = {"path": str(path), "durable": str(durable), "kind": kind, "pruned": removed,
                              "bytes": checkpoint_bytes(durable)}
            except Exception as error:
                outcome[0] = {"error": f"{type(error).__name__}: {error}"}
        dist.broadcast_object_list(outcome, src=0)
        if "error" in outcome[0]:
            raise ValueError("Checkpoint failed: " + outcome[0]["error"])
        return outcome[0]
    finally:
        restore_rng(local_rng)


def seal_full_checkpoint(store, header, trainables, optimizer, state, rank_rng, pins, layout_sha256, temporary, final):
    step = state["realized"]["optimizer_steps"]
    settings = header["settings"]
    per_epoch = math.ceil(state["row_count"] / settings["effective_batch_size"])
    position = {"epoch": step // per_epoch, "batch_index": step % per_epoch}
    metadata = {"schema": SCHEMA, "format": FULL_FORMAT, "identity": run_identity(header), "step": step,
                "epoch": position["epoch"], "batch_plan_position": position, "metrics_line_count": step, "state": state,
                "optimizer_parameters": optimizer_names(trainables, optimizer), "shard_layout_sha256": layout_sha256}
    validate_progress(metadata, settings)
    if len(rank_rng) != header["world_size"] or len(pins) != header["world_size"]:
        raise ValueError("Checkpoint requires RNG state and a shard from every rank")
    replicated = [name for name in trainables if name.startswith(("geometry_input.", "auxiliary_heads."))]
    if bool(replicated) != ("replicated" in pins[0]) or any("replicated" in pin for pin in pins[1:]):
        raise ValueError("Rank 0 alone writes the replicated modules, exactly when the run has them")
    with (temporary / "rng.pt").open("xb") as stream:
        torch.save(rank_rng, stream)
        stream.flush()
        os.fsync(stream.fileno())
    scheduler = {"completed_steps": step, "total_steps": state["planned_steps"], "settings_sha256": digest_json(settings),
                 "last_lr": [group["lr"] for group in optimizer.param_groups]}
    (temporary / "scheduler.json").write_bytes(canonical_bytes(scheduler))
    (temporary / "layout.json").write_bytes(canonical_bytes({"shard_layout_sha256": layout_sha256, "world_size": len(pins)}))
    artifacts = publication_files(store.root, store.provisional_diagnostic)
    if not REQUIRED_ARTIFACTS <= artifacts.keys():
        raise ValueError("Checkpoint is missing its run header, provenance, batch plan, or metrics")
    names = set(FULL_STATE_FILES)
    for name, path in artifacts.items():
        relative = "artifacts/" + name
        copy_new(path, temporary / relative, sha256(path))
        names.add(relative)
    validate_metrics(temporary / "artifacts/metrics.jsonl", header, step)
    metadata["files"] = {}
    for name in sorted(names):
        path = temporary / name
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
        metadata["files"][name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    for rank, pin in enumerate(pins):
        for item in (pin["shard"], *([pin["replicated"]] if "replicated" in pin else [])):
            expected = f"shards/rank{rank:03d}.pt" if item is pin["shard"] else REPLICATED_FILE
            if item["name"] != expected or (temporary / item["name"]).stat().st_size != item["bytes"]:
                raise ValueError(f"Rank {rank} checkpoint file {expected} is missing or truncated")
            metadata["files"][item["name"]] = {"sha256": item["sha256"], "bytes": item["bytes"]}
    with (temporary / "checkpoint.json").open("xb") as stream:
        stream.write(canonical_bytes(metadata))
        stream.flush()
        os.fsync(stream.fileno())
    for directory in sorted({(temporary / name).parent for name in metadata["files"]}, key=lambda path: len(path.parts),
                            reverse=True):
        sync_directory(directory)
    sync_directory(temporary)
    temporary.rename(final)
    sync_directory(final.parent)
    return final


def retain_full(store, header, path, kind):
    """retain() for a checkpoint already in the durable root: verify, record, then prune the rolling pool (the full
    fine-tuning rule: FULL_PINNED_KINDS pinned, every other full state in the pool of FULL_ROLLING_KEEP)."""
    durable = Path(path).resolve()
    read_checkpoint(durable, run_identity(header))
    ledger = ledger_directory(store)
    step = load_json(durable / "checkpoint.json")["step"]
    if kind in FULL_PINNED_KINDS:
        append_ledger(ledger / PINNED_LEDGER, pin_record(durable, kind))
    elif kind in FULL_POOL_KINDS:
        append_ledger(ledger / ROLLING_LEDGER, {"event": "written", "step": step, "kind": kind,
                                                 "path": str(durable), "utc": utc_now()})
    else:
        raise ValueError(f"Unknown full fine-tuning checkpoint kind: {kind}")
    try:
        removed = prune_rolling(store, step, keep=FULL_ROLLING_KEEP, kinds=FULL_POOL_KINDS)
    except Exception as error:
        print(f"ROLLING_PRUNE_FAILED step={step} {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        removed = []
    return durable, removed


def remove_stale_temporaries(root):
    """Remove the temporary directories of saves that an earlier attempt of this run left unfinished. Saves are
    serialized and only rank 0 creates temporaries, so any temporary present when a new save starts is stale."""
    removed = []
    for path in sorted(Path(root).iterdir()):
        if STALE_TEMPORARY.fullmatch(path.name) and path.is_dir() and not path.is_symlink():
            remove_checkpoint(path)
            removed.append(path.name)
    if removed:
        print(f"REMOVED_STALE_CHECKPOINT_TEMPORARIES {removed}", file=sys.stderr, flush=True)
    return removed


def save_milestone_export(store, header, distributed, base_names, step, report, geometry=None, auxiliary_heads=None):
    """A full fine-tuning milestone export: every rank joins the FULL_STATE_DICT gather; rank 0 writes the BF16 export of
    the masters (full_weights/), the geometry adapter (geometry/) and the heads (auxiliary_heads.pt), all FP32 as
    published, into durable_root/milestone_<step>/ atomically, and pins it in MILESTONES.jsonl."""
    from . import full_ft
    from .fsdp_training import publication_state
    rank = dist.get_rank()
    state = publication_state(distributed)
    outcome = [None]
    if rank == 0:
        try:
            root = durable_root(store)
            final = root / f"milestone_{step}"
            if final.exists() or final.is_symlink():
                raise ValueError("Refusing to replace an existing milestone export")
            remove_stale_temporaries(root)
            tensors = full_ft.export_tensors(state, base_names)
            ensure_free_space(root, 2 * sum(tensor.numel() * tensor.element_size() for tensor in tensors.values()))
            temporary = root / f".milestone_{step}_{uuid4().hex}.tmp"
            temporary.mkdir()
            export = full_ft.save_export(tensors, temporary / full_ft.EXPORT_DIRECTORY,
                                         {"student": header["student"], "base": header["base"], "base_sha256": header["base_sha256"]},
                                         report)
            del tensors
            files = {f"{full_ft.EXPORT_DIRECTORY}/{item['name']}": {"sha256": item["sha256"], "bytes": item["bytes"]}
                     for item in export["files"]}
            for name in (export["index"]["name"], full_ft.EXPORT_MANIFEST):
                path = temporary / full_ft.EXPORT_DIRECTORY / name
                files[f"{full_ft.EXPORT_DIRECTORY}/{name}"] = {"sha256": sha256(path), "bytes": path.stat().st_size}
            if geometry is not None:
                from .geometry_input import MANIFEST_NAME, WEIGHTS_NAME, save as save_geometry
                (temporary / "geometry").mkdir()
                save_geometry(geometry, temporary / "geometry")
                for name in (WEIGHTS_NAME, MANIFEST_NAME):
                    files[f"geometry/{name}"] = {"sha256": sha256(temporary / "geometry" / name),
                                                 "bytes": (temporary / "geometry" / name).stat().st_size}
            if auxiliary_heads is not None:
                with (temporary / "auxiliary_heads.pt").open("xb") as handle:
                    torch.save({name: value.detach().cpu() for name, value in auxiliary_heads.state_dict().items()}, handle)
                files["auxiliary_heads.pt"] = {"sha256": sha256(temporary / "auxiliary_heads.pt"),
                                               "bytes": (temporary / "auxiliary_heads.pt").stat().st_size}
                (temporary / "auxiliary_heads.json").write_bytes(canonical_bytes(auxiliary_heads.manifest()))
                files["auxiliary_heads.json"] = {"sha256": sha256(temporary / "auxiliary_heads.json"),
                                                 "bytes": (temporary / "auxiliary_heads.json").stat().st_size}
            manifest = {"schema": MILESTONE_SCHEMA, "step": step, "identity": run_identity(header), "files": files}
            with (temporary / "MILESTONE.json").open("xb") as stream:
                stream.write(canonical_bytes(manifest))
                stream.flush()
                os.fsync(stream.fileno())
            for directory in sorted({(temporary / name).parent for name in files}, key=lambda path: len(path.parts), reverse=True):
                sync_directory(directory)
            sync_directory(temporary)
            temporary.rename(final)
            sync_directory(final.parent)
            record = {"path": str(final.resolve()), "step": step, "bytes": checkpoint_bytes(final),
                      "sha256": sha256(final / "MILESTONE.json"), "kind": "milestone_export", "utc": utc_now()}
            append_ledger(ledger_directory(store) / MILESTONE_LEDGER, record)
            outcome[0] = record
        except Exception as error:
            outcome[0] = {"error": f"{type(error).__name__}: {error}"}
    del state
    dist.broadcast_object_list(outcome, src=0)
    if "error" in outcome[0]:
        raise ValueError("Milestone export failed: " + outcome[0]["error"])
    return outcome[0]


def restore_full_checkpoint(directory, checkpoint, trainables, optimizer, rank, settings, layout_sha256, process_group=None):
    """Each rank verifies and loads its own shard, rank 0 the replicated modules (then broadcast over process_group); the
    scheduler, RNG and layout must match this run exactly."""
    from .full_ft import read_rank_shard
    directory = Path(directory)
    if checkpoint.get("format") != FULL_FORMAT or checkpoint.get("shard_layout_sha256") != layout_sha256:
        raise ValueError("Resume requires a rank-sharded checkpoint with this run's sharding layout")
    if optimizer_names(trainables, optimizer) != checkpoint["optimizer_parameters"]:
        raise ValueError("Checkpoint optimizer parameter order changed")
    scheduler = load_json(directory / "scheduler.json")
    step, planned = checkpoint["step"], checkpoint["state"]["planned_steps"]
    expected = {"completed_steps": step, "total_steps": planned, "settings_sha256": digest_json(settings),
                "last_lr": [schedule_lr(step - 1, planned, settings, group.get("base_lr")) for group in optimizer.param_groups]}
    if scheduler != expected:
        raise ValueError("Checkpoint LR-scheduler state differs from its frozen plan")
    if load_json(directory / "layout.json") != {"shard_layout_sha256": layout_sha256, "world_size": checkpoint["identity"]["world_size"]}:
        raise ValueError("Checkpoint sharding layout differs from this run")
    read_rank_shard(directory, rank, checkpoint["files"], list(trainables.items()), optimizer, layout_sha256, process_group)
    if [group["lr"] for group in optimizer.param_groups] != expected["last_lr"]:
        raise ValueError("Restored optimizer learning rates differ from the frozen plan")
    rank_rng = torch.load(directory / "rng.pt", map_location="cpu", weights_only=True)
    if len(rank_rng) != checkpoint["identity"]["world_size"]:
        raise ValueError("Checkpoint rank RNG coverage changed")
    restore_rng(rank_rng[rank])
    return copy.deepcopy(checkpoint["state"])


class StopRequest:
    """A stop request: SIGUSR1 or SIGTERM to this rank, or the file R1_STOP_FILE existing.

    The handler only records the request, so a signal that lands during a checkpoint write lets the write finish.
    """

    def __init__(self, path=None):
        self.path = path if path is not None else os.environ.get("R1_STOP_FILE") or None
        self.reason = None
        self.previous = {}

    def handle(self, signum, frame):
        if self.reason is None:
            self.reason = signal.Signals(signum).name

    def install(self):
        for number in STOP_SIGNALS:
            self.previous[number] = signal.signal(number, self.handle)
        return self

    def restore(self):
        for number, handler in self.previous.items():
            signal.signal(number, handler)
        self.previous = {}

    def requested(self):
        if self.reason is None and self.path and os.path.exists(self.path):
            self.reason = "stop_file"
        return self.reason is not None


def rolling_interval():
    """Seconds between rolling checkpoints (R1_ROLLING_MINUTES, default 30; 0 turns rolling saves off)."""
    minutes = float(os.environ.get("R1_ROLLING_MINUTES", "30"))
    if not math.isfinite(minutes) or minutes < 0:
        raise ValueError("R1_ROLLING_MINUTES must be a finite number of minutes, at least 0")
    return minutes * 60


class RollingClock:
    """Rank 0's wall-clock timer; agree() makes every rank take its decision at the same optimizer step."""

    def __init__(self, interval=None):
        self.interval = rolling_interval() if interval is None else interval
        self.last = time.monotonic()

    def due(self):
        return self.interval > 0 and time.monotonic() - self.last >= self.interval

    def saved(self):
        self.last = time.monotonic()


def agree(rank, stop, rolling=None):
    """(stop, rolling save) for this optimizer step: any rank's stop request, rank 0's rolling timer."""
    flags = torch.tensor([int(stop.requested()), int(rank == 0 and rolling is not None and rolling.due())],
                         dtype=torch.int64)
    dist.all_reduce(flags, op=dist.ReduceOp.MAX)
    return bool(flags[0]), bool(flags[1])


def write_stop_marker(store, step, reasons, saved):
    record = {"schema": "student-ddp-signal-stop-v1", "step": step, "reasons": reasons,
              "checkpoint": saved.get("durable") if saved else None, "kind": saved.get("kind") if saved else None,
              "checkpoint_sha256": sha256(Path(saved["durable"]) / "checkpoint.json") if saved else None,
              "utc": utc_now()}
    return store.write(STOP_MARKER, record)


def read_checkpoint(directory, expected_identity):
    directory = source_path(directory).resolve()
    manifest = directory / "checkpoint.json"
    if manifest.is_symlink() or not manifest.is_file() or directory.name.startswith("."):
        raise ValueError("Resume requires a complete atomic checkpoint directory")
    checkpoint = load_json(manifest)
    if checkpoint.get("schema") != SCHEMA:
        raise ValueError("Unsupported checkpoint schema")
    if (checkpoint.get("identity", {}).get("targets", DEFAULTS["targets"])
            != expected_identity.get("targets", DEFAULTS["targets"])):
        raise ValueError("Resume across a change of the LoRA targets option (frozen groups) is refused")
    for key, expected in expected_identity.items():
        if checkpoint.get("identity", {}).get(key) != expected:
            raise ValueError(f"Resume {key} mismatch")
    files = checkpoint.get("files", {})
    full = checkpoint.get("format") == FULL_FORMAT
    state_files = (FULL_STATE_FILES | ({REPLICATED_FILE} & files.keys())) if full else STATE_FILES
    shards = {f"shards/rank{rank:03d}.pt" for rank in range(checkpoint.get("identity", {}).get("world_size", 0))} if full else set()
    if not state_files | shards | {"artifacts/" + name for name in REQUIRED_ARTIFACTS} <= files.keys():
        raise ValueError("Checkpoint file manifest is incomplete")
    for name, pin in files.items():
        relative = Path(name)
        path = source_path(directory / relative)
        if (relative.is_absolute() or ".." in relative.parts or str(relative) != name or path.is_symlink()
                or not path.resolve().is_relative_to(directory)
                or (name not in state_files and name not in shards and not name.startswith("artifacts/"))):
            raise ValueError("Checkpoint file escapes its sealed directory")
        if not path.is_file() or path.stat().st_size != pin["bytes"]:
            raise ValueError(f"Checkpoint SHA256 or size mismatch: {name}")
        # Each rank verifies its own shard's sha256 when it restores (restore_full_checkpoint), in parallel.
        if name not in shards and sha256(path) != pin["sha256"]:
            raise ValueError(f"Checkpoint SHA256 or size mismatch: {name}")
    header = load_json(directory / "artifacts/run.json")
    config = load_json(directory / "artifacts/config.json")
    if (run_identity(header) != checkpoint["identity"] or header["provenance"].get("dirty") is not False
            or digest_json(config["config"]) != checkpoint["identity"]["config_sha256"]
            or config["provenance"] != header["provenance"]
            or load_json(directory / "artifacts/provenance.json")["provenance"] != header["provenance"]):
        raise ValueError("Checkpoint run header or config identity changed")
    validate_progress(checkpoint, header["settings"])
    validate_metrics(directory / "artifacts/metrics.jsonl", header, checkpoint["metrics_line_count"])
    for step in range(1, checkpoint["step"] + 1):
        name = f"artifacts/steps/{step:04d}.json"
        if name not in files:
            raise ValueError("Checkpoint is missing its immutable optimizer-step receipts")
        metric = load_json(directory / name)
        if metric.get("step") != step or metric.get("provenance") != header["provenance"]:
            raise ValueError("Checkpoint optimizer-step provenance changed")
    return checkpoint


def restore_checkpoint(directory, checkpoint, adapters, optimizer, rank, settings):
    directory = Path(directory)
    if optimizer_names(adapters, optimizer) != checkpoint["optimizer_parameters"]:
        raise ValueError("Checkpoint optimizer adapter order changed")
    weights = torch.load(directory / "adapters.pt", map_location="cpu", weights_only=True)
    optimizer_state = torch.load(directory / "optimizer.pt", map_location="cpu", weights_only=True)
    rank_rng = torch.load(directory / "rng.pt", map_location="cpu", weights_only=True)
    scheduler = load_json(directory / "scheduler.json")
    step, planned = checkpoint["step"], checkpoint["state"]["planned_steps"]
    expected = {"completed_steps": step, "total_steps": planned, "settings_sha256": digest_json(settings),
                "last_lr": [schedule_lr(step - 1, planned, settings, group.get("base_lr")) for group in optimizer.param_groups]}
    if scheduler != expected or [group["lr"] for group in optimizer_state["param_groups"]] != expected["last_lr"]:
        raise ValueError("Checkpoint LR-scheduler state differs from its frozen plan")
    if set(weights) != set(adapters) or len(rank_rng) != checkpoint["identity"]["world_size"]:
        raise ValueError("Checkpoint adapter or rank RNG coverage changed")
    for name, parameter in adapters.items():
        if weights[name].shape != parameter.shape or weights[name].dtype != parameter.dtype:
            raise ValueError(f"Checkpoint adapter shape or dtype changed: {name}")
    with torch.no_grad():
        for name, parameter in adapters.items():
            parameter.copy_(weights[name])
    optimizer.load_state_dict(optimizer_state)
    restore_rng(rank_rng[rank])
    return copy.deepcopy(checkpoint["state"])


class ResumeArtifacts(RunArtifacts):
    def __init__(self, output, config, scratch_root, directory, world_size, parallel):
        directory = source_path(directory).resolve()
        current = code_provenance(config)
        expected = {"protocol_sha256": config["protocol"]["sha256"], "config_sha256": current["config_sha256"],
                    "commit": current["commit"], "world_size": world_size, "parallel": parallel,
                    **({"init_adapter_sha256": config["init_adapter_sha256"]} if "init_adapter_sha256" in config else {}),
                    **targets_identity(config["settings"])}
        self.checkpoint = read_checkpoint(directory, expected)
        header = require_mode(load_json(directory / "artifacts/run.json"), config["provisional_diagnostic"])
        if load_json(directory / "artifacts/config.json")["config"] != config:
            raise ValueError("Resume configuration changed")
        self.root = output_path(output, scratch_root)
        if self.root == directory or self.root.is_relative_to(directory):
            raise ValueError("Resume output must not lie inside its checkpoint")
        self.provenance = header["provenance"]
        self.provisional_diagnostic = config["provisional_diagnostic"]
        self.flags = {"infrastructure_only": False, "benchmark_improvement_claim": False, "score_nomination_allowed": False,
                      **provisional_flags(self.provisional_diagnostic), "PROVISIONAL_DIVISION_SHA": config["PROVISIONAL_DIVISION_SHA"]}
        self.resumed_from = {"path": str(directory), "step": self.checkpoint["step"], "checkpoint_sha256": sha256(directory / "checkpoint.json")}
        if (self.root / "PUBLISHED.json").exists():
            raise ValueError("A published run cannot be resumed")
        if self.root.exists() and any(self.root.iterdir()):
            if not (self.root / "config.json").is_file() or load_json(self.root / "config.json")["provenance"] != self.provenance:
                raise ValueError("Resume output belongs to a different run")
        stable = {"config.json", "provenance.json"}
        for name in stable:
            if (self.root / name).exists():
                binding(self.root / name, self.checkpoint["files"]["artifacts/" + name]["sha256"])
        previous = active_checkpoints(self.root / "checkpoints")
        if (self.root / "_superseded").is_symlink():
            raise ValueError("Resume archive directory must not be a symlink")
        ensure_free_space(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.archive_root = self.root / "_superseded" / f"resume_step_{self.checkpoint['step']}_{uuid4().hex}"
        for name, path in publication_files(self.root, self.provisional_diagnostic).items():
            if name not in stable:
                archive(path, self.archive_root / name)
        for step, path in previous:
            if step > self.checkpoint["step"]:
                archive(path, self.root / "checkpoints/_superseded" / path.name)
        for name, pin in self.checkpoint["files"].items():
            if name.startswith("artifacts/"):
                relative = name.removeprefix("artifacts/")
                if relative not in stable or not (self.root / relative).exists():
                    copy_new(directory / name, self.root / relative, pin["sha256"])

    def write(self, path, value):
        path = contained(self.root, path)
        if path.exists():
            archive(path, self.archive_root / path.relative_to(self.root))
        return super().write(path, value)


def localize_resume_frames(rows, store, manifest_path, scratch_root, stage):
    if not stage or not (store.root / "frames").is_dir():
        return localize_frames(rows, store, manifest_path, scratch_root, stage)
    localized = copy.deepcopy(rows)
    for row in localized:
        if row.get("student_input") is not None:
            row["student_input"]["frames"] = [binding(store.root / "frames" / frame["sha256"][:2] / frame["sha256"], frame["sha256"])
                                                for frame in row["student_input"]["frames"]]
    receipt = load_json(store.root / "frame_staging.json")
    for item in receipt["files"]:
        digest = item["staged"]["sha256"]
        item["staged"] = binding(store.root / "frames" / digest[:2] / digest, digest)
    store.write("frame_staging.json", receipt)
    store.write("frames/provenance.json", {"frame_staging": binding(store.root / "frame_staging.json")})
    store.write("input_manifest.json", {"source_manifest": binding(manifest_path), "rows": localized})
    return localized
