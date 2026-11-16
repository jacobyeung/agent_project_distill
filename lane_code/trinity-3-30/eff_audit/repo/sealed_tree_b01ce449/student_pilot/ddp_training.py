import gc
import json
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .common import binding, configure_environment, digest_json, startup_event
from .ddp_config import (DEFAULTS, VERSION, allocator_settings, load_camera_config, load_run_control,
                         load_training_config, validate_camera_protocol, validate_run_control_protocol,
                         validate_training_protocol)
from .provisional import require_mode, tag, validate_label
from .storage import RunArtifacts, adapter_directory, localize_frames


def gather(value, world_size):
    import torch.distributed as dist

    values = [None] * world_size
    dist.all_gather_object(values, value)
    return values


def training_config_matches(training_config, student, settings, run_control, camera_config):
    """train()'s startup check: the launcher's training config normalizes to the frozen protocol's settings.

    A config without a camera block and arm U's disabled block both give camera_config None."""
    return (load_training_config(training_config, student) == settings
            and load_run_control(training_config) == run_control
            and load_camera_config(training_config) == camera_config)


def attach_targets(batch, row, tokenizer, audit):
    """Auxiliary and camera targets (and camera carriers) for one encoded row; other rows are untouched."""
    if '_auxiliary' not in row and '_camera' not in row:
        return batch
    from .auxiliary_targets import add_to_batch
    return add_to_batch(batch, row, tokenizer, audit)


def lm_row_scale(rows, indices):
    """Global batch / question rows: pose-only rows (Cambrian-P) leave the language-model row mean."""
    qa_rows = sum(1 for index in indices if rows[index].get("category") != "camera_pose_only")
    if qa_rows < 1:
        raise ValueError("A global batch without question rows has no language-model term")
    return len(indices) / qa_rows


def geometry_option(store):
    """Keyword for the batch and probe helpers: present only when a geometry store is configured."""
    return {} if store is None else {"geometry": store}


def geometry_batch(batch, row, store):
    """Add the row's geometry features (float16 [merged video tokens, 2 * feature_dim]) and optional G3T camera
    sidecar tensors when a store is configured."""
    if store is None:
        return batch
    frames = [frame["sha256"] for frame in row["student_input"]["frames"]]
    out = {**batch, "geometry_features": store.tokens(frames, batch["video_grid_thw"][0])}
    if store.has_camera_sidecar:
        out.update(store.camera_sidecar(frames))
    return out


def open_geometry_store(settings, rows, audits, world):
    """Every rank opens the pinned feature store; every admitted row needs features on its frozen processor grid."""
    from . import geometry_input
    from .orchard_paths import resolve_read

    store = report = failure = None
    try:
        store = geometry_input.FeatureStore(settings, resolve=resolve_read)
        missing, mismatched, files = [], [], set()
        for row in rows:
            try:
                frames = [frame["sha256"] for frame in row["student_input"]["frames"]]
                entry = store.row(frames)
                if store.has_camera_sidecar:
                    store.camera_row(frames)
            except ValueError:
                missing.append(row["qid"])
                continue
            files.add(entry["key"])
            height, width = geometry_input.store_grid(store.settings, audits[row["qid"]]["video_grid_thw"][0])
            if entry["shape"][1:3] != [height, width]:
                mismatched.append(row["qid"])
        report = {"schema": "geometry-store-coverage-v1", "store": settings["store"], "admitted_rows": len(rows),
                  "store_rows": len(store.rows), "feature_files_used": len(files), "missing_rows": len(missing),
                  "grid_mismatch_rows": len(mismatched),
                  **({"camera_rows": len(store.camera_rows)} if store.has_camera_sidecar else {})}
        if missing or mismatched:
            raise ValueError(f"{len(missing)} of {len(rows)} admitted rows have no store row and {len(mismatched)} differ "
                             f"from their processor grid (first qids: {(missing + mismatched)[:5]})")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    failures = sorted({item for item in gather(failure, world) if item is not None})
    if failures:
        raise ValueError("Geometry feature store refused: " + "; ".join(failures))
    return store, report


def attach_geometry(model, settings, seed):
    """Attach the zero-initialised geometry projector; its FP32 parameters train beside the LoRA allowlist."""
    import torch
    from . import geometry_input

    # A fixed seed gives every rank the same projector; the fork leaves the matched control's RNG stream untouched.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        module = geometry_input.attach(model, settings)
    module.to(device=next(model.parameters()).device, dtype=torch.float32)
    zero_start = settings["projector"].get("output_init") == "zeros"
    if (any(not parameter.requires_grad or parameter.dtype != torch.float32 for parameter in module.parameters())
            or zero_start and (module.projector.fc2.weight.count_nonzero() or module.projector.fc2.bias.count_nonzero())):
        raise ValueError("The geometry projector must be trainable FP32 (with a zero output layer when its design has one)")
    return module


def clip_gradients(lora_parameters, geometry_parameters, clip_norm):
    """Clip the LoRA tensors over themselves alone, exactly as a run without geometry, and the projector tensors
    separately to the same norm. Returns the LoRA norm before clipping and the projector's (None without one)."""
    import torch

    norm = torch.nn.utils.clip_grad_norm_(lora_parameters, clip_norm, error_if_nonfinite=True)
    if not geometry_parameters:
        return norm, None
    return norm, float(torch.nn.utils.clip_grad_norm_(geometry_parameters, clip_norm, error_if_nonfinite=True))


# The headcall block's per-rank state (headcall.rows): encoding counters and, in arm HC, the scheduled sampler that
# receives each micro-batch's single-row encodings. train() installs it; without the block both stay None.
HEADCALL = {"stats": None, "sampling": None}


def encode_microbatch(processor, rows, audits, indices, geometry=None):
    from .ddp_core import collate_rows
    from .pose_samples import encode_row as encode_training

    batches, used = [], []
    for index in indices:
        row = rows[index]
        batch, audit = encode_training(processor, row)
        if audit != audits[row["qid"]]:
            raise ValueError("Training preprocessing changed after the frozen input audit")
        if "_headcall" in row:
            # Queried depth points first in the depth targets, carriers forced, tool responses masked (headcall.rows).
            from headcall import rows as headcall_rows
            row = headcall_rows.prepare_row(row, HEADCALL["stats"])
            batch = attach_targets(batch, row, processor.tokenizer, audit)
            batch = headcall_rows.finish_encoding(batch, row, processor.tokenizer, HEADCALL["stats"])
        else:
            batch = attach_targets(batch, row, processor.tokenizer, audit)
        batch = geometry_batch(batch, row, geometry)
        batches.append(batch)
        used.append(row)
    collated = collate_rows(batches, processor.tokenizer.pad_token_id)
    if HEADCALL["sampling"] is not None:
        HEADCALL["sampling"].register(collated, used, batches, processor)
    return collated


def prefetched_batches(processor, rows, audits, slots, microbatch, geometry=None):
    chunks = [slots[start:start + microbatch] for start in range(0, len(slots), microbatch)]
    extra = () if geometry is None else (geometry,)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(encode_microbatch, processor, rows, audits, [index for index, _ in chunks[0]], *extra)
        for position, chunk in enumerate(chunks):
            batch = pending.result()
            if position + 1 < len(chunks):
                pending = executor.submit(encode_microbatch, processor, rows, audits,
                                          [index for index, _ in chunks[position + 1]], *extra)
            yield batch, chunk, position + 1 == len(chunks)


def probe_candidate(model, parameters, cpu_rows, size, pad_token_id, memory_fraction,
                    memory_fit_safety_factor=DEFAULTS["memory_fit_safety_factor"], replicated=None):
    import torch
    from .ddp_core import collate_rows, row_losses

    memory_fraction = min(memory_fraction, 0.9)
    reserve = [torch.empty_like(parameter) for parameter in parameters for _ in range(3)]
    measurements = []
    batches = [[row] * size for row in cpu_rows]
    if size > 1 and len(cpu_rows) > 1:
        batches.append([cpu_rows[index % len(cpu_rows)] for index in range(size)])
    try:
        for rows in batches:
            model.zero_grad(set_to_none=True)
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            started = time.perf_counter()
            batch = {key: value.to("cuda:0") for key, value in collate_rows(rows, pad_token_id).items()}
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = row_losses(model, batch).mean()
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite loss during the measured memory probe")
            loss.backward()
            from torch.distributed.fsdp import FullyShardedDataParallel
            if isinstance(model, FullyShardedDataParallel):
                from .fsdp_training import average_adapter_gradients
                # FSDP reduces the gradients it owns; only replicated tensors are averaged here.
                average_adapter_gradients(parameters if replicated is None else replicated, model.process_group)
            torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
            torch.cuda.synchronize()
            measurements.append({"seconds": time.perf_counter() - started,
                                 "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                                 "peak_reserved_bytes": torch.cuda.max_memory_reserved()})
            del loss, batch
        total = torch.cuda.get_device_properties(0).total_memory
        limit = total * memory_fraction
        allocated = max(item["peak_allocated_bytes"] for item in measurements)
        reserved = max(item["peak_reserved_bytes"] for item in measurements)
        allocated_with_margin = allocated * memory_fit_safety_factor
        reserved_over_limit = reserved > limit
        allocator = allocator_settings()
        fits = allocated_with_margin <= limit and (allocator["expandable_segments"] or not reserved_over_limit)
        if allocator["expandable_segments"] and reserved_over_limit:
            logging.getLogger(__name__).warning(
                "Memory probe microbatch=%s reserved peak=%s exceeds limit=%s; reserved memory is advisory "
                "with expandable segments; allocated peak=%s safety_factor=%s adjusted=%s fits=%s",
                size, reserved, limit, allocated, memory_fit_safety_factor, allocated_with_margin, fits)
        return {"microbatch": size, "fits": fits, **allocator,
                "seconds": max(item["seconds"] for item in measurements), "measurements": measurements,
                "peak_allocated_bytes": allocated, "peak_reserved_bytes": reserved,
                "total_memory_bytes": total, "memory_limit_bytes": limit, "reserved_over_limit": reserved_over_limit,
                "memory_fit_safety_factor": memory_fit_safety_factor,
                "allocated_with_safety_factor_bytes": allocated_with_margin,
                "reserved_optimizer_and_communication_bytes": sum(t.numel() * t.element_size() for t in reserve)}
    finally:
        model.zero_grad(set_to_none=True)
        del reserve


def memory_probe(model, processor, rows, audits, settings, rank, lease_check, geometry=None):
    import torch
    from .pose_samples import encode_row as encode_training
    from .students import student_for_model

    student = student_for_model(model)
    memory_fraction = min(settings["memory_fraction"], 0.9)
    keys = ("sequence_tokens", "visual_tokens", "assistant_tokens_including_eos")
    stress = sorted({max(range(len(rows)), key=lambda index: audits[rows[index]["qid"]][key]) for key in keys})
    startup_event("probe_encoding_begin")
    cpu_rows = []
    for index in stress:
        batch, audit = encode_training(processor, rows[index])
        if audit != audits[rows[index]["qid"]]:
            raise ValueError("Memory probe preprocessing differs from the frozen row audit")
        row = rows[index]
        if '_camera' in row:
            # Probe the worst case: every stress row carries the 16 camera tokens and runs every camera loss.
            from .camera_targets import probe_record
            row = {**row, '_camera': probe_record(row['_camera'])}
        batch = attach_targets(batch, row, processor.tokenizer, audit)
        cpu_rows.append(geometry_batch(batch, rows[index], geometry))
    startup_event("probe_encoding_end")
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    replicated = None
    if settings.get("full_ft") is not None and settings.get("parallel", "ddp") == "fsdp":
        from .full_ft import clean_name
        replicated = [parameter for name, parameter in model.named_parameters() if parameter.requires_grad
                      and clean_name(name).startswith(("geometry_input.", "auxiliary_heads."))]
    sharded = settings.get("parallel", "ddp") == "fsdp"
    if sharded:
        from .fsdp_training import frozen_shard_fingerprints, check_frozen_shards
        frozen = frozen_shard_fingerprints(model)
    versions = {name: parameter._version for name, parameter in model.named_parameters()
                if not sharded or parameter.requires_grad}
    cap = min(settings["max_microbatch_size"], math.ceil(settings["effective_batch_size"] / settings["world_size"]))
    candidates = sorted({1, cap, *(2**power for power in range(6) if 2**power <= cap)})
    trials = []
    for size in candidates:
        startup_event(f"probe_microbatch_{size}_begin")
        lease_check()
        torch.cuda.empty_cache()
        try:
            trial = probe_candidate(model, parameters, cpu_rows, size, processor.tokenizer.pad_token_id, memory_fraction,
                                    memory_fit_safety_factor=settings["memory_fit_safety_factor"],
                                    **({"replicated": replicated} if replicated is not None else {}))
        except torch.cuda.OutOfMemoryError:
            if sharded:
                raise RuntimeError("FSDP probe OOM: stop all ranks; retry with a smaller frozen microbatch cap")
            trial = {"microbatch": size, "fits": False, "reason": "CUDA_OutOfMemory"}
        model.zero_grad(set_to_none=True)
        gc.collect()
        torch.cuda.empty_cache()
        if sharded:
            # Every rank must take the same next collective, even when only one
            # rank exceeds the measured memory budget.
            trial["fits"] = all(gather(trial["fits"], settings["world_size"]))
        trials.append(trial)
        startup_event(f"probe_microbatch_{size}_end")
        if not trial["fits"]:
            break
    if sharded:
        check_frozen_shards(model, frozen)
    if any(parameter._version != versions[name] for name, parameter in model.named_parameters() if name in versions):
        raise ValueError("The memory probe must never update model or adapter parameters")
    return {"rank": rank, "student": student, "trials": trials, "stress_qids": [rows[index]["qid"] for index in stress],
            "policy": "largest_sequence_visual_and_assistant_rows_plus_mixed_batch", **allocator_settings(),
            "memory_fraction": memory_fraction, "memory_fit_safety_factor": settings["memory_fit_safety_factor"],
            "optimizer_updates": 0}


def collective_startup(function, rank):
    import torch.distributed as dist

    result = [None]
    if rank == 0:
        try:
            result[0] = {"value": function()}
        except Exception as error:
            result[0] = {"error": f"{type(error).__name__}: {error}"}
    dist.broadcast_object_list(result, src=0)
    if "error" in result[0]:
        raise ValueError("Startup validation refused: " + result[0]["error"])
    return result[0]["value"]


def startup_memory_probe(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint,
                         geometry=None):
    import torch
    from . import probe_cache

    try:
        config = probe_cache.configuration()
        control = {"config": config, "error": None}
    except Exception as error:
        control = {"config": None, "error": str(error)}
    controls = gather(control, settings["world_size"])
    if any(item["error"] or item["config"] != controls[0]["config"] for item in controls):
        raise ValueError("Ranks disagree about probe cache configuration or cannot verify it")
    config = controls[0]["config"]
    if config is None or checkpoint is not None:
        return memory_probe(model, processor, rows, audits, settings, rank, lease_check, **geometry_option(geometry)), None
    startup_event("probe_cache_lookup_begin")
    try:
        device = {"device": probe_cache.runtime_device(), "error": None}
    except Exception as error:
        device = {"device": None, "error": str(error)}
    devices = gather(device, settings["world_size"])
    if any(item["error"] for item in devices):
        raise ValueError("Ranks cannot authenticate the probe cache hardware and runtime")
    identity = collective_startup(lambda: probe_cache.identity(protocol, rows, audits, settings, topology,
                                   [item["device"] for item in devices], config["environment_sha256"]), rank)
    cached = collective_startup(lambda: probe_cache.lookup(config["root"], identity), rank)
    if cached is not None:
        lease_check()
        free, _ = torch.cuda.mem_get_info()
        fits = probe_cache.available(cached["probes"][rank], cached["microbatch"], free,
                                     torch.cuda.memory_reserved(), settings)
        if not all(gather(fits, settings["world_size"])):
            cached = None
    startup_event("probe_cache_lookup_end")
    context = {"config": config, "identity": identity, "cache_hit": cached is not None,
               "source_receipt": cached["receipt"] if cached is not None else None}
    if cached is not None:
        startup_event("memory_probe_cache_hit")
        return {**cached["probes"][rank], "reused_calibration": cached["receipt"]}, context
    startup_event("memory_probe_cache_miss")
    return memory_probe(model, processor, rows, audits, settings, rank, lease_check, **geometry_option(geometry)), context


def startup_memory_guard(settings, rank, store, phase, additional_bytes=0):
    import torch
    from .probe_cache import memory_guard

    torch.cuda.synchronize()
    guard = memory_guard(rank, torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved(),
                         torch.cuda.get_device_properties(0).total_memory, settings, additional_bytes)
    guards = gather(guard, settings["world_size"])
    collective_startup(lambda: str(store.write(f"memory_guard_{phase}.json", {"ranks": guards})), rank)
    if not all(item["passed"] for item in guards):
        raise ValueError("First-step memory guard exceeded the frozen memory budget; no automatic batch change is allowed")
    return guards


def write_metric(store, metrics, log, value, total_steps, label):
    record = store.record(value)
    metrics.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    metrics.flush()
    line = (f"{datetime.now(timezone.utc).isoformat()} | {label} | step={value['step']}/{total_steps} "
            f"epoch={value['epoch']} loss={value['loss']:.6f} lr={value['lr']:.8g} rows={value['rows']} "
            f"tokens={value['tokens']} seconds={value['seconds']:.3f} training_rows={value['training_rows']}\n")
    log.write(line)
    log.flush()
    print(json.dumps({"optimizer_step": value["step"], "epoch": value["epoch"], "loss": value["loss"],
                      "lr": value["lr"], "training_rows": value["training_rows"], "scheduled_steps": total_steps,
                      "step_seconds": value["seconds"], "provisional_diagnostic": label}), flush=True)


def persist_admission(rank, probes, store, header):
    import torch.distributed as dist

    decision = [None]
    if rank == 0:
        errors = [item["error"] for item in probes if item["error"] is not None]
        if errors:
            decision[0] = {"admitted": False, "error": "; ".join(errors)}
        else:
            try:
                header["lease"]["ranks"] = [item["lease"] for item in probes]
                header = store.record(header)
                store.write("run.json", header)
                decision[0] = {"admitted": True}
            except Exception as error:
                decision[0] = {"admitted": False, "error": f"run.json persistence failed: {error}"}
    dist.broadcast_object_list(decision, src=0)
    if not decision[0]["admitted"]:
        raise ValueError(f"DDP admission refused: {decision[0]['error']}")
    dist.barrier()
    return header


def mirror_staged_frames(receipt, receipt_pin, rows, output, scratch_root, node_rank, label):
    from uuid import uuid4
    from .common import resolve_read
    from .storage import copy_new, ensure_free_space, output_path, write_new

    root = output_path(output, scratch_root)
    files = receipt.get("files", [])
    if receipt.get("schema") != "student-frame-staging-v1" or digest_json(receipt) != receipt_pin["sha256"]:
        raise ValueError("Node-local frame staging receipt changed")
    expected = {(frame["path"], frame["sha256"]) for row in rows if row.get("student_input") is not None
                for frame in row["student_input"]["frames"]}
    declared = {(item["staged"]["path"], item["staged"]["sha256"]) for item in files}
    if declared != expected or len(declared) != len(files) or receipt.get("unique_frames") != len(files):
        raise ValueError("Node-local mirror must cover exactly the admitted staged frames")
    for item in files:
        digest = item["staged"]["sha256"]
        destination = Path(item["staged"]["path"])
        if (len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest)
                or item["source"]["sha256"] != digest or destination != root / "frames" / digest[:2] / digest
                or destination.is_symlink() or destination.resolve() != destination
                or type(item["bytes"]) is not int or item["bytes"] < 0):
            raise ValueError("Node-local frame path, size, or source identity changed")
    ensure_free_space(root, sum(item["bytes"] for item in files if not Path(item["staged"]["path"]).exists()))
    for item in files:
        destination = Path(item["staged"]["path"])
        digest = item["staged"]["sha256"]
        if not destination.exists():
            source = resolve_read(item["source"]["path"])
            binding(source, digest)
            if source.stat().st_size != item["bytes"]:
                raise ValueError("Node-local frame source size changed")
            temporary = destination.with_name(destination.name + ".partial." + uuid4().hex)
            copy_new(source, temporary, digest)
            temporary.rename(destination)
        binding(destination, digest)
        if destination.stat().st_size != item["bytes"]:
            raise ValueError("Node-local staged frame size changed")
    record = tag({"schema": "provisional-ddp-node-frame-staging-v1", "node_rank": node_rank,
                  "source_receipt": receipt_pin, "files": files,
                  "verified_at": datetime.now(timezone.utc).isoformat()}, label)
    path = write_new(f"runtime/node{node_rank}/frame_staging-{uuid4().hex}.json", record, root)
    return binding(path)


def train(manifest_path, protocol_path, output, lease_path, student="onethinker", scratch_root=None,
          stage_frames=False, provisional_diagnostic=None, training_config=None, parallel="ddp", resume_from=None, init_adapter=None):
    from . import ddp_admission as admission
    from . import provisional_data as data
    from .provisional import load_json

    label = validate_label(provisional_diagnostic)
    started = time.perf_counter()
    manifest_path, protocol_path, lease_path = (admission.input_path(path)
                                                for path in (manifest_path, protocol_path, lease_path))
    if training_config is not None:
        training_config = admission.input_path(training_config)
    if resume_from is not None:
        resume_from = admission.input_path(resume_from)
    declared = require_mode(load_json(protocol_path), label)
    settings = validate_training_protocol(declared, label)
    if parallel not in ("ddp", "fsdp") or parallel != settings.get("parallel", "ddp"):
        raise ValueError("Parallel mode differs from the frozen protocol")
    run_control = validate_run_control_protocol(declared)
    camera_config = validate_camera_protocol(declared)
    if training_config is not None and not training_config_matches(training_config, student, settings, run_control,
                                                                    camera_config):
        raise ValueError("Training config differs from the frozen protocol")
    initialization = {key: declared[key] for key in ("init_adapter_identity", "init_adapter_sha256") if key in declared}
    configured = load_json(training_config).get("init_adapter") if training_config is not None else None
    if initialization or configured is not None or init_adapter is not None:
        from .warmstart import validate_identity, validate_request
        validate_identity(declared)
        if not initialization:
            raise ValueError("An initial adapter must be frozen at prepare time")
        if configured is not None:
            validate_request(configured, declared["init_adapter_identity"])
    startup_event("rank_admission_begin")
    request = admission.request_identity(manifest_path, protocol_path, label, student, settings["world_size"])
    bundle = admission.load_bundle(lease_path, request, label)
    rank, world, launcher_visibility = admission.select_rank(bundle)
    bound = bundle["ranks"][rank]
    topology = admission.rank_topology(bundle["ranks"])
    admission.require_rank_lease(bound, label, request["ranks"][rank], fresh=True)
    startup_event("rank_admission_end")

    import torch
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel
    from transformers import set_seed
    from .adapters import attach_ddp_adapters, frozen_adapters, trainable_groups, trainable_targets
    from .batches import load_processor
    from . import ddp_checkpoints as checkpoints
    from .ddp_core import backward_batch, build_optimizer, global_batches, question_order, rank_slots, schedule_lr
    from .diagnostic import frozen_base_check
    from .runner import adapter_snapshot, group_gradients, group_updates, load_base, memory_measurement
    from . import full_ft

    def make_batch_plan():
        batch_plan = {"microbatch_size": microbatch, "gradient_accumulation": accumulation,
                      "effective_batch_size": settings["effective_batch_size"], "world_size": world,
                      "compute_slots_per_step": world * microbatch * accumulation,
                      "padding": settings["padding"], "scheduler_steps": planned_steps, "optimizer_steps_planned": stop_steps,
                      "epoch_order_sha256": [digest_json([batch["indices"] for batch in global_batches(
                          len(rows), epoch, settings["effective_batch_size"], settings["seed"], pose_flags)])
                                             for epoch in range(settings["epochs"])]}
        if "full_ft" in settings:
            # The question rows' qids in epoch order (pose-only rows removed): a run with pose-only rows (CPD) and its
            # control without them (FT_A) record the same digest when their question rows match.
            batch_plan["question_order_sha256"] = [digest_json(question_order([row["qid"] for row in rows], epoch,
                                                                              settings["seed"], pose_flags))
                                                   for epoch in range(settings["epochs"])]
        return batch_plan

    store = metrics = log = None
    stop = checkpoints.StopRequest().install()
    dist.init_process_group("gloo", timeout=timedelta(minutes=60))
    try:
        identities = gather({"rank": rank, "host": bound["host"], "output": str(Path(output).resolve()),
                             "request_sha256": request["protocol_sha256"], "resume_from": str(resume_from)}, world)
        if (any(item["rank"] != index for index, item in enumerate(identities))
                or any(item["host"] != bundle["ranks"][index]["host"] or item["output"] != identities[0]["output"]
                       or item["request_sha256"] != request["protocol_sha256"]
                       or item["resume_from"] != identities[0]["resume_from"] for index, item in enumerate(identities))):
            raise ValueError("DDP ranks disagree about node, output, training identity, or checkpoint")
        payload = [None]
        if rank == 0:
            try:
                from .startup_receipt import load_prepared, localize_shared
                startup_event("prepared_startup_verify_begin")
                prepared = load_prepared(manifest_path, protocol_path, label, student, weights=True)
                startup_event("prepared_startup_verify_end")
                if prepared is None:
                    startup_event("protocol_weight_verify_begin")
                    protocol = data.load_protocol(protocol_path, label, weights=True, student=student)
                    startup_event("protocol_weight_verify_end")
                    startup_event("training_manifest_verify_begin")
                    manifest = data.load_training(manifest_path, label)
                    startup_event("training_manifest_verify_end")
                else:
                    protocol, manifest = prepared["protocol"], prepared["manifest"]
                if manifest["protocol"] != binding(protocol_path) or not manifest["training_ready"] or not manifest["rows"]:
                    raise ValueError("DDP requires nonempty admitted training rows under its frozen protocol")
                config = tag({"mode": "train-ddp", "student": student, "manifest": binding(manifest_path),
                              "protocol": binding(protocol_path), "settings": settings, "run_control": run_control,
                              "protocol_version": VERSION, "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"],
                              "stage_frames": stage_frames, "scratch_root": str(scratch_root), **initialization}, label)
                if prepared is not None:
                    config.update(startup_receipt=prepared["receipt"], frame_mode=prepared["frame_mode"])
                store = (checkpoints.ResumeArtifacts(output, config, scratch_root, resume_from, world, parallel)
                         if resume_from is not None else RunArtifacts(output, config, scratch_root))
                if resume_from is not None:
                    checkpoints.pin_parent(store, resume_from)
                log = (store.root / "train.log").open("a" if resume_from is not None else "x", buffering=1)
                log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | phase=stage_frames world_size={world}\n")
                localize = checkpoints.localize_resume_frames if resume_from is not None else localize_frames
                startup_event("frame_staging_begin")
                localized = (localize_shared(prepared, store, manifest_path) if prepared is not None
                             else localize(manifest["rows"], store, manifest_path, scratch_root, stage_frames))
                startup_event("frame_staging_end")
                payload[0] = {"protocol": protocol, "rows": localized, "audits": manifest["input_audits"], "counts": manifest["counts"],
                              "checkpoint": store.checkpoint if resume_from is not None else None,
                              "resumed_from": store.resumed_from if resume_from is not None else None,
                              "frame_mode": prepared["frame_mode"] if prepared is not None else "node_local"}
                if topology["nnodes"] > 1 and stage_frames and prepared is None:
                    payload[0].update(frame_staging=load_json(store.root / "frame_staging.json"),
                                      frame_staging_binding=binding(store.root / "frame_staging.json"))
            except Exception as error:
                payload[0] = {"error": f"{type(error).__name__}: {error}"}
        dist.broadcast_object_list(payload, src=0)
        shared = payload[0]
        if "error" in shared:
            raise ValueError("DDP run preparation refused: " + shared["error"])
        checkpoint = shared["checkpoint"]
        protocol, rows = shared["protocol"], shared["rows"]
        audits = {audit["qid"]: audit for audit in shared["audits"]}
        auxiliary_config = settings.get('auxiliary')
        auxiliary_heads = None
        if auxiliary_config is not None:
            from .auxiliary_targets import load_for_rows
            records = collective_startup(lambda: load_for_rows(rows, auxiliary_config), rank)
            if records is not None:
                rows = [{**row, '_auxiliary': record} for row, record in zip(rows, records)]
        if camera_config is not None:
            from .camera_targets import load_for_rows as load_camera_rows
            records = collective_startup(lambda: load_camera_rows(rows, camera_config), rank)
            if records is not None:
                rows = [{**row, '_camera': record} for row, record in zip(rows, records)]
        headcall_report = None
        HEADCALL.update(stats=None, sampling=None)
        if "headcall" in settings:
            # Head-call sidecar (headcall.rows): its entries bind to admitted rows by target and input hashes.
            from collections import Counter
            from headcall import rows as headcall_rows
            from .orchard_paths import resolve_read
            headcall_rows.check_camera(camera_config)
            joined, headcall_report = collective_startup(lambda: headcall_rows.join(rows, settings["headcall"],
                                                                                    resolve=resolve_read), rank)
            rows = headcall_rows.attach(rows, joined)
            HEADCALL["stats"] = Counter()
            if settings["headcall"]["scheduled_sampling"] is not None:
                HEADCALL["sampling"] = headcall_rows.Sampling(settings["headcall"]["scheduled_sampling"])
        from .pose_samples import configure_frames
        configure_frames(settings.get("frames"))
        pose_only_rows = any(row.get('category') == 'camera_pose_only' for row in rows)
        # Pose-only rows take seeded slots between the question rows, whose order stays that of the rows without them.
        pose_flags = [row.get('category') == 'camera_pose_only' for row in rows] if pose_only_rows else None
        if pose_only_rows and not any('_camera' in row for row in rows):
            raise ValueError('Pose-only rows require the camera head; without it they would train as answer rows')
        geometry_store = geometry_report = geometry = None
        if "geometry" in settings:
            startup_event("geometry_store_begin")
            geometry_store, geometry_report = open_geometry_store(settings["geometry"], rows, audits, world)
            startup_event("geometry_store_end")
        if camera_config is not None and camera_config.get("g3t_prior") and (geometry_store is None or not geometry_store.has_camera_sidecar):
            raise ValueError("Camera g3t_prior requires a geometry store with a pinned camera_manifest")
        if topology["nnodes"] > 1:
            failure = None
            if stage_frames and shared["frame_mode"] == "node_local" and rank > 0 and rank % topology["local_world_size"] == 0:
                try:
                    mirror_staged_frames(shared["frame_staging"], shared["frame_staging_binding"], rows, output,
                                         scratch_root, rank // topology["local_world_size"], label)
                except Exception as error:
                    failure = f"rank {rank}: {type(error).__name__}: {error}"
            failures = [item for item in gather(failure, world) if item is not None]
            if failures:
                raise ValueError("DDP node-local frame mirror refused: " + "; ".join(failures))
            dist.barrier()
        startup_event("processor_setup_begin")
        configure_environment(Path(output) / "runtime" / f"rank{rank}")
        processor = load_processor(student)
        startup_event("processor_setup_end")
        try:
            lease = admission.admitted_rank(bound, label, request["ranks"][rank])
            probe = {"lease": lease, "error": None}
        except Exception as error:
            probe = {"lease": None, "error": f"rank {rank}: {type(error).__name__}: {error}"}
        probes = gather(probe, world)
        header = {"schema": "provisional-ddp-training-run-v2", "student": student,
                  "protocol_version": VERSION, "training_sha256": protocol["training_sha256"],
                  "protocol": binding(protocol_path), "training_manifest": binding(manifest_path),
                  "base": protocol["base"], "base_sha256": protocol["base_sha256"], "settings": settings,
                  "run_control": run_control, "run_control_sha256": digest_json(run_control),
                  "versions": protocol["versions"], "runtime": protocol["runtime"], "dataset_counts": shared["counts"],
                  "lease": {"bundle": binding(lease_path), "ranks": []}, "world_size": world,
                  "parallel": parallel, "sharding": settings.get("sharding"),
                  "launcher_visible_devices": launcher_visibility,
                  "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter",
                  "base_dtype": "bfloat16", "attention_implementation": "sdpa", "detailed_distillation": True,
                  "future_clean_student_restarts_original_weights": True,
                  "started_at": datetime.now(timezone.utc).isoformat(), **initialization}
        if camera_config is not None:
            # Beside, never inside, "settings": evaluators normalize the plain training settings.
            header.update(camera=camera_config, camera_sha256=declared["camera_sha256"])
        if topology["nnodes"] > 1:
            header.update(topology)
        if checkpoint is not None:
            header.update(resumed_from=shared["resumed_from"], resumed_from_step=checkpoint["step"])
        header = persist_admission(rank, probes, store, header)
        if rank == 0:
            log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | phase=load_model admitted_ranks={world}\n")
        set_seed(settings["seed"])
        full_block = settings.get("full_ft")
        full = full_block is not None and not full_ft.frozen_vlm(full_block)
        # Full fine-tuning upcasts the base to FP32 masters on the CPU; FSDP then moves each unit's shard to the GPU.
        load_options = {"device": "cpu"} if (student == "qwen36_27b" and parallel == "fsdp") or full else {}
        startup_event("model_weights_begin")
        model = load_base(student, **load_options)
        startup_event("model_weights_end")
        startup_event("adapter_attach_begin")
        if full_block is not None:
            merge_report = {}
            if full_block["init"]["kind"] == "full_export":
                failure = None
                try:
                    from .orchard_paths import resolve_read
                    merge_report = {"init_export": full_ft.load_init_export(model, full_block, protocol["base_sha256"],
                                                                            resolve=resolve_read, base=protocol["base"],
                                                                            student=student)}
                except Exception as error:
                    failure = f"rank {rank}: {type(error).__name__}: {error}"
                failures = [item for item in gather(failure, world) if item is not None]
                if failures:
                    raise ValueError("Full-export warm start refused: " + "; ".join(failures))
            if full_block["init"]["kind"] == "base_merged_init_adapter":
                failure = None
                try:
                    model, merge_report = full_ft.merge_init_adapter(model, settings, protocol, protocol_path,
                                                                     init_adapter=init_adapter)
                except Exception as error:
                    failure = f"rank {rank}: {type(error).__name__}: {error}"
                failures = [item for item in gather(failure, world) if item is not None]
                if failures:
                    raise ValueError("Merged warm start refused: " + "; ".join(failures))
            full_groups, report = full_ft.prepare_model(model, full_block)
            report.update({key: value for key, value in merge_report.items() if key != "initialization_source"})
            if merge_report.get("initialization_source") is not None:
                report["initialization_source"] = merge_report["initialization_source"]
        else:
            model, report = attach_ddp_adapters(model, settings)
        startup_event("adapter_attach_end")
        if initialization and full_block is None:
            from .warmstart import initialize_adapters
            failure = None
            try:
                startup_event("initial_adapter_load_begin")
                report = initialize_adapters(model, report, protocol, protocol_path, resume_from=resume_from, init_adapter=init_adapter)
                startup_event("initial_adapter_load_end")
            except Exception as error:
                failure = f"rank {rank}: {type(error).__name__}: {error}"
            failures = [item for item in gather(failure, world) if item is not None]
            if failures:
                raise ValueError("Initial adapter loading refused: " + "; ".join(failures))
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        checkpointing = {name: module.gradient_checkpointing for name, module in model.named_modules()
                         if hasattr(module, "gradient_checkpointing")}
        if (not checkpointing or not all(checkpointing.values()) or not any("visual" in name for name in checkpointing)
                or not any("language_model" in name for name in checkpointing)):
            raise ValueError("Non-reentrant gradient checkpointing must cover text and vision")
        model.train()
        groups = trainable_groups(model, trainable_targets(report)) if full_block is None else {}
        adapters = {name: parameter for group in groups.values() for name, parameter in group}
        if auxiliary_config is not None or camera_config is not None:
            from .auxiliary_losses import attach
            auxiliary_heads = attach(model, auxiliary_config, processor.tokenizer, camera_config)
            if auxiliary_heads is not None:
                adapters.update({'auxiliary_heads.' + name: p for name, p in auxiliary_heads.named_parameters() if p.requires_grad})
                report['auxiliary_parameters'] = sum(p.numel() for p in auxiliary_heads.parameters() if p.requires_grad)
                report['auxiliary'] = auxiliary_heads.settings
        geometry_group = {}
        if geometry_store is not None:
            geometry = attach_geometry(model, settings["geometry"], settings["seed"])
        frozen_attached = full_ft.frozen_attached_parameters(full_block, camera_config, auxiliary_heads, geometry)
        if geometry is not None:
            geometry_named = [("geometry_input.projector." + name, parameter)
                              for name, parameter in geometry.projector.named_parameters() if parameter.requires_grad]
            geometry_group = {"geometry": geometry_named} if geometry_named else {}
            adapters.update(geometry_named)
            report["geometry_parameters"] = sum(parameter.numel() for parameter in geometry.projector.parameters() if parameter.requires_grad)
        parameters = list(adapters.values())
        geometry_parameters = [parameter for _, parameter in geometry_group.get("geometry", [])]
        head_named = [(name, parameter) for name, parameter in adapters.items() if name.startswith("auxiliary_heads.")]
        lora_parameters = parameters[:len(parameters) - len(geometry_parameters)]
        base_names = [name for name, _ in full_ft.base_parameters(model)] if full_block is not None else None
        init_modules = None
        if full_block is not None and "init_modules" in full_block:
            from .orchard_paths import resolve_read
            init_modules = full_ft.load_init_modules(full_block, geometry=geometry, heads=auxiliary_heads, resolve=resolve_read)
            report["init_modules"] = init_modules
        if full_block is not None and not parameters and not full:
            raise ValueError("The frozen-VLM stage needs an attached geometry adapter or heads to train")
        if parallel == "fsdp":
            from . import fsdp_training as fsdp
            startup_event("fsdp_wrap_begin")
            process_group = dist.new_group(backend="nccl", timeout=timedelta(minutes=30))
            if full:
                distributed = full_ft.wrap_full_model(model, [*parameters, *frozen_attached], process_group, torch.device("cuda:0"))
            else:
                frozen_lora = [p for _, p in frozen_adapters(model, report)] if full_block is None else []
                frozen_lora.extend(frozen_attached)
                distributed = fsdp.wrap_model(model, parameters, process_group, torch.device("cuda:0"),
                                              **({"frozen_adapters": frozen_lora} if frozen_lora else {}))
            startup_event("fsdp_wrap_end")
            startup_event("frozen_fingerprint_begin")
            frozen = fsdp.frozen_shard_fingerprints(distributed)
            startup_event("frozen_fingerprint_end")

        def lease_check():
            return admission.require_rank_lease(bound, label, request["ranks"][rank], fresh=False)

        if rank == 0:
            store.write("adapters.json", report)
            if "initialization_source" in report:
                store.write("init_adapter_source.json", report["initialization_source"])
            store.write("gradient_checkpointing.json", checkpointing)
            if geometry_report is not None:
                store.write("geometry_store.json", geometry_report)
            if headcall_report is not None:
                store.write("headcall_rows.json", headcall_report)
            log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | phase=memory_probe\n")
        startup_event("memory_probe_begin")
        probe, probe_context = startup_memory_probe(distributed if parallel == "fsdp" else model, processor,
                              rows, audits, settings, rank, lease_check, protocol, topology, checkpoint,
                              **geometry_option(geometry_store))
        startup_event("memory_probe_end")
        probes = gather(probe, world)
        if rank == 0:
            store.write("memory_probe.json", {"ranks": probes})
            if probe_context is not None:
                store.write("memory_probe_cache.json", probe_context)
        microbatch = checkpoints.resumed_microbatch(probes, world, settings["effective_batch_size"], checkpoint,
                                                    exact=topology["nnodes"] > 1)
        accumulation = math.ceil(settings["effective_batch_size"] / (world * microbatch))
        if topology["nnodes"] > 1 and (accumulation != 1 or world * microbatch != settings["effective_batch_size"]):
            raise ValueError("Multi-node training requires the exact batch with no gradient accumulation or layout padding")
        set_seed(settings["seed"] + rank)
        startup_event("distributed_optimizer_setup_begin")
        if parallel == "ddp":
            process_group = dist.new_group(backend="nccl", timeout=timedelta(minutes=30))
            distributed = DistributedDataParallel(model, device_ids=[0], output_device=0, process_group=process_group,
                                                 broadcast_buffers=False, find_unused_parameters=False,
                                                 gradient_as_bucket_view=True)
            frozen = {name: parameter._version for name, parameter in model.named_parameters() if not parameter.requires_grad}
        before = adapter_snapshot(groups) if rank == 0 else None
        geometry_before = adapter_snapshot(geometry_group) if rank == 0 and geometry_group else None
        sharded = full_ft.sharded_groups(distributed, full_block) if full else {}
        sharded_before = adapter_snapshot(sharded) if full else None
        if full_block is not None:
            optimizer = full_ft.build_optimizer(sharded, geometry_group, auxiliary_heads, full_block, settings)
        else:
            # Geometry tensors join the adapter group (the LoRA learning rate).
            optimizer = build_optimizer({**groups, **geometry_group}, auxiliary_heads, settings)
        if {id(p) for group in optimizer.param_groups for p in group["params"]} != {id(p) for p in model.parameters() if p.requires_grad}:
            raise ValueError("Optimizer parameter set differs from the exact adapter allowlist")
        trainables = dict(adapters)
        if full:
            trainables = {name: parameter for group in sharded.values() for name, parameter in group}
            trainables.update(adapters)
            layouts = gather(full_ft.shard_layout(list(trainables.items())), world)
            report["shard_layout_sha256"] = digest_json(layouts)
        startup_event("distributed_optimizer_setup_end")
        startup_event("batch_plan_setup_begin")
        steps_per_epoch = math.ceil(len(rows) / settings["effective_batch_size"])
        planned_steps = steps_per_epoch * settings["epochs"]
        if full_block is not None:
            planned_steps = full_ft.scheduler_steps(full_block, planned_steps, settings["max_steps"])
        stop_steps = min(planned_steps, settings["max_steps"] or planned_steps)
        realized = {"optimizer_steps": 0, "training_rows": 0, "source_rows": 0, "epoch_padding_rows": 0,
                    "layout_padding_rows": 0, "frames": 0, "target_tokens_including_eos": 0, "prompt_tokens": 0}
        batch_plan = collective_startup(make_batch_plan, rank)
        startup_event("batch_plan_setup_end")
        if checkpoint is not None:
            previous_plan = load_json(resume_from / "artifacts/batch_plan.json")
            if (checkpoint["state"]["row_count"] != len(rows)
                    or any(previous_plan.get(key) != value for key, value in batch_plan.items())):
                raise ValueError("Resume batch plan differs from the checkpoint")
        if rank == 0:
            store.write("batch_plan.json", batch_plan)
            store.write("optimizer.json", {"class": "AdamW", "defaults": optimizer.defaults,
                         "loss_reduction": settings["loss_reduction"], "ddp_rank_scale": world / settings["effective_batch_size"]})
            metrics = (store.root / "metrics.jsonl").open("a" if checkpoint is not None else "x", buffering=1)
        startup_event("loader_setup_begin")
        step_seconds = training_wall_before = total_wall_before = 0.0
        peak_per_rank = [0] * world
        start_epoch = start_batch = 0
        if checkpoint is not None:
            restored = (checkpoints.restore_full_checkpoint(resume_from, checkpoint, trainables, optimizer, rank, settings,
                                                            report["shard_layout_sha256"], process_group) if full
                        else checkpoints.restore_checkpoint(resume_from, checkpoint, adapters, optimizer, rank, settings))
            realized, step_seconds, peak_per_rank = restored["realized"], restored["step_seconds"], restored["peak_per_rank"]
            training_wall_before, total_wall_before = restored["training_wall_seconds"], restored["total_wall_seconds"]
            start_epoch, start_batch = checkpoint["epoch"], checkpoint["batch_plan_position"]["batch_index"]
        camera_gate = gate_stopped = None
        if camera_config is not None and camera_config['gate'] is not None:
            from .camera_gate import CameraGate
            camera_gate = CameraGate(camera_config['gate'])
            if camera_gate.config['check_step'] > stop_steps:
                raise ValueError('The camera gate would check after the run stops')
            if checkpoint is not None:
                with (Path(resume_from) / 'artifacts/metrics.jsonl').open() as history:
                    camera_gate.restore(json.loads(line) for line in history if line.strip())
        lm_gate = None
        if camera_config is not None and camera_config['lm_gate'] is not None:
            from .camera_gate import LMGate
            lm_gate = LMGate(camera_config['lm_gate'])
            if lm_gate.config['check_step'] > stop_steps:
                raise ValueError('The LM gate would check after the run stops')
            if auxiliary_heads is None:
                raise ValueError('The LM gate needs the auxiliary loss totals of an attached head')
            if checkpoint is not None:
                with (Path(resume_from) / 'artifacts/metrics.jsonl').open() as history:
                    lm_gate.restore(json.loads(line) for line in history if line.strip())
        startup_event("loader_setup_end")
        training_started = time.perf_counter()
        last_checkpoint_timing = None
        rolling = checkpoints.RollingClock()
        saved = {"durable": str(Path(resume_from).resolve()), "kind": "parent"} if checkpoint is not None else None
        stopping = checkpoints.agree(rank, stop)[0]
        for epoch in range(start_epoch, settings["epochs"]):
            if stopping:
                break
            for batch_index, window in enumerate(global_batches(len(rows), epoch, settings["effective_batch_size"], settings["seed"],
                                                                pose_flags)):
                if epoch == start_epoch and batch_index < start_batch:
                    continue
                if realized["optimizer_steps"] >= stop_steps:
                    break
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                step_started = time.perf_counter()
                # One schedule evaluation per parameter group; the logged lr is the adapter group's (the first).
                for group in optimizer.param_groups:
                    group["lr"] = schedule_lr(realized["optimizer_steps"], planned_steps, settings, group.get("base_lr"))
                lr = optimizer.param_groups[0]["lr"]
                optimizer.zero_grad(set_to_none=True)
                if auxiliary_heads is not None:
                    auxiliary_heads.set_step(realized['optimizer_steps'], planned_steps)
                slots = rank_slots(window["indices"], rank, world, microbatch)
                lm_scale = lm_row_scale(rows, window["indices"]) if pose_only_rows else None
                local_loss = torch.zeros((), device="cuda:0", dtype=torch.float64)
                local_tokens = local_prompt = 0
                from .auxiliary_losses import TERMS
                mixed_slot = len(TERMS)
                camera_rows_slot = mixed_slot + 2
                lm_sum_slot, lm_rows_slot = mixed_slot + 3, mixed_slot + 4
                from .auxiliary_losses import CAMERA_COMPONENTS
                component_slot = mixed_slot + 5
                depth_rows_slot = component_slot + len(CAMERA_COMPONENTS)
                auxiliary_totals = (torch.zeros(depth_rows_slot + 1, device='cuda:0', dtype=torch.float64)
                                    if auxiliary_heads is not None else None)
                mixing = auxiliary_heads is not None and auxiliary_heads.mixing(realized['optimizer_steps'], planned_steps)
                first_batch_pending = realized["optimizer_steps"] == 0
                if first_batch_pending:
                    startup_event("first_batch_loader_begin")
                for chunk_index, (cpu_batch, chunk, synchronize) in enumerate(prefetched_batches(
                        processor, rows, audits, slots, microbatch, **geometry_option(geometry_store))):
                    if first_batch_pending:
                        startup_event("first_batch_ready")
                        first_batch_pending = False
                    lease_check()
                    batch = {key: value.to("cuda:0", non_blocking=True) for key, value in cpu_batch.items()}
                    weights = [weight for _, weight in chunk]
                    if HEADCALL["sampling"] is not None:
                        # Scheduled sampling (headcall arm HC): GT responses of chosen calls become the student's own
                        # head answers before backward; FSDP ranks run matched session forwards.
                        from headcall import rows as headcall_rows
                        from .diagnostic_data import TRAINING as SEQUENCE_LIMITS
                        sampled_rows, encodings, sampled_processor = HEADCALL["sampling"].take(cpu_batch)
                        if HEADCALL["sampling"].sampler.schedule(realized["optimizer_steps"]) > 0:
                            batch = headcall_rows.scheduled_batch(
                                HEADCALL["sampling"], distributed, batch, sampled_rows, encodings, sampled_processor,
                                weights, realized["optimizer_steps"],
                                forward_context=torch.autocast("cuda", dtype=torch.bfloat16),
                                process_group=process_group, fsdp=parallel == "fsdp",
                                max_length=SEQUENCE_LIMITS["max_sequence_tokens"])
                    if mixing:
                        from .auxiliary_losses import mix_microbatch
                        batch, mixed = mix_microbatch(distributed if parallel == "fsdp" else model, auxiliary_heads, batch, weights,
                                                      f"{settings['seed']}:{realized['optimizer_steps']}:{rank}:{chunk_index}",
                                                      processor.tokenizer.pad_token_id, torch.autocast("cuda", dtype=torch.bfloat16),
                                                      collective=True)
                        auxiliary_totals[mixed_slot] += mixed["rows"]
                        auxiliary_totals[mixed_slot + 1] += mixed["queries"]
                    parts = {}
                    losses = backward_batch(distributed, batch, weights, world, settings["effective_batch_size"], synchronize or parallel == "fsdp",
                                            forward_context=torch.autocast("cuda", dtype=torch.bfloat16),
                                            loss_reduction=settings["loss_reduction"], parts=parts,
                                            **({"lm_scale": lm_scale} if lm_scale is not None else {}))
                    if auxiliary_totals is not None:
                        active = torch.tensor(weights, device=losses.device, dtype=torch.float64)
                        text_rows = active * batch['aux_lm_weight'].double() if 'aux_lm_weight' in batch else active
                        auxiliary_totals[lm_sum_slot] += (parts['lm'].double() * active).sum()
                        auxiliary_totals[lm_rows_slot] += text_rows.sum()
                    if auxiliary_heads is not None:
                        from .auxiliary_losses import TERMS
                        for term_index, term_name in enumerate(TERMS):
                            if term_name in auxiliary_heads.last_terms:
                                values = auxiliary_heads.last_terms[term_name]
                                auxiliary_totals[term_index] += (values * values.new_tensor(weights)).sum().double()
                    local_loss += (losses.double() * torch.tensor(weights, device=losses.device)).sum()
                    for index, weight in chunk:
                        if weight:
                            audit = audits[rows[index]["qid"]]
                            local_tokens += audit["assistant_tokens_including_eos"]
                            local_prompt += audit["prompt_tokens"]
                    if auxiliary_heads is not None and auxiliary_heads.has_camera:
                        supervised = batch['aux_camera_mask'].any(dim=1).double()
                        auxiliary_totals[camera_rows_slot] += (supervised * supervised.new_tensor(weights)).sum()
                        components = auxiliary_heads.camera.last_components
                        for offset, name in enumerate(CAMERA_COMPONENTS):
                            if name in components:
                                auxiliary_totals[component_slot + offset] += (components[name].double()
                                                                              * supervised.new_tensor(weights)).sum()
                        if 'aux_point_depth_mask' in batch:
                            labelled = batch['aux_point_depth_mask'].flatten(1).any(dim=1).double()
                            auxiliary_totals[depth_rows_slot] += (labelled * labelled.new_tensor(weights)).sum()
                    del cpu_batch, batch, losses
                if parallel == "fsdp":
                    fsdp.average_adapter_gradients(parameters, process_group)
                if realized["optimizer_steps"] == 0:
                    if full_block is not None:
                        gradients = full_ft.check_gradient_flow(sharded, report, process_group)
                        if auxiliary_heads is not None:
                            gradients["heads"] = group_gradients({"heads": head_named})["heads"]
                    else:
                        gradients = group_gradients(groups)
                    geometry_flow = {"geometry": group_gradients(geometry_group)["geometry"]} if geometry_group else {}
                    if rank == 0:
                        store.write("gradient_flow.json", {"groups": gradients, **geometry_flow})
                clip_norms = None
                if full_block is not None:
                    clip_norms = full_ft.clip_families(sharded, geometry_parameters, [p for _, p in head_named],
                                                       settings["clip_norm"], process_group)
                    norm, geometry_norm = next(iter(clip_norms.values())), clip_norms.get("geometry")
                else:
                    norm, geometry_norm = clip_gradients(lora_parameters, geometry_parameters, settings["clip_norm"])
                if realized["optimizer_steps"] == 0 and probe_context is not None:
                    startup_memory_guard(settings, rank, store, "before_optimizer",
                                         additional_bytes=3 * sum(parameter.numel() * parameter.element_size()
                                                                  for parameter in trainables.values()))
                optimizer.step()
                memory = memory_measurement()
                if realized["optimizer_steps"] == 0 and probe_context is not None:
                    guards = startup_memory_guard(settings, rank, store, "after_optimizer")
                    if not probe_context["cache_hit"]:
                        from .probe_cache import publish
                        calibration = collective_startup(lambda: publish(probe_context["config"]["root"],
                            probe_context["identity"], probes, microbatch, {"commit": store.provenance["commit"],
                            "config_sha256": store.provenance["config_sha256"], "run": binding(store.root / "run.json"),
                            "probe": binding(store.root / "memory_probe.json")}, guards), rank)
                        collective_startup(lambda: str(store.write("memory_probe_cache_written.json", {"receipt": calibration})), rank)
                elapsed = time.perf_counter() - step_started
                totals = torch.tensor([local_loss.item(), local_tokens, local_prompt], dtype=torch.float64)
                dist.all_reduce(totals)
                ranks = gather({"rank": rank, "seconds": elapsed, "memory": memory,
                                **({"headcall": {**dict(HEADCALL["stats"]), **(HEADCALL["sampling"].step_stats()
                                                                              if HEADCALL["sampling"] is not None else {})}}
                                   if HEADCALL["stats"] is not None else {})}, world)
                if HEADCALL["stats"] is not None:
                    HEADCALL["stats"].clear()
                elapsed = max(item["seconds"] for item in ranks)
                step_seconds += elapsed
                for item in ranks:
                    peak_per_rank[item["rank"]] = max(peak_per_rank[item["rank"]], item["memory"]["max_reserved_bytes"])
                realized["optimizer_steps"] += 1
                realized["training_rows"] += settings["effective_batch_size"]
                realized["source_rows"] += window["source_rows"]
                realized["epoch_padding_rows"] += window["padding_rows"]
                realized["layout_padding_rows"] += len(slots) * world - settings["effective_batch_size"]
                realized["frames"] += 32 * settings["effective_batch_size"]
                realized["target_tokens_including_eos"] += int(totals[1])
                realized["prompt_tokens"] += int(totals[2])
                if auxiliary_totals is not None:
                    auxiliary_totals = auxiliary_totals.cpu()
                    dist.all_reduce(auxiliary_totals)
                gate_record = None
                if camera_gate is not None:
                    gate_sample = {'step': realized['optimizer_steps'], 'loss_sum': float(auxiliary_totals[TERMS.index('camera')]),
                                   'rows': float(auxiliary_totals[camera_rows_slot])}
                    camera_gate.record(gate_sample['step'], gate_sample['loss_sum'], gate_sample['rows'])
                    gate_record = camera_gate.decide(realized['optimizer_steps'])
                lm_record = None
                if lm_gate is not None:
                    lm_sample = {'step': realized['optimizer_steps'], 'loss_sum': float(auxiliary_totals[lm_sum_slot]),
                                 'rows': float(auxiliary_totals[lm_rows_slot])}
                    lm_gate.record(lm_sample['step'], lm_sample['loss_sum'], lm_sample['rows'])
                    lm_record = lm_gate.decide(realized['optimizer_steps'])
                if rank == 0:
                    metric = {"step": realized["optimizer_steps"], "epoch": epoch + 1,
                              "loss": float(totals[0]) / settings["effective_batch_size"], "lr": lr,
                              "rows": settings["effective_batch_size"], "tokens": int(totals[1]), "prompt_tokens": int(totals[2]),
                              "source_rows": window["source_rows"], "epoch_padding_rows": window["padding_rows"],
                              "layout_padding_rows": len(slots) * world - settings["effective_batch_size"],
                              "training_rows": realized["training_rows"], "seconds": elapsed,
                              "gradient_norm_before_clip": float(norm), "peak_memory_per_rank": ranks,
                              "qids": [rows[index]["qid"] for index in window["indices"]]}
                    if geometry_norm is not None:
                        metric["geometry_gradient_norm_before_clip"] = geometry_norm
                    if HEADCALL["stats"] is not None:
                        # Summed over ranks; encoding counters follow the prefetching loader (one micro-batch ahead).
                        totals_headcall = {}
                        for item in ranks:
                            for key, value in item.get("headcall", {}).items():
                                totals_headcall[key] = totals_headcall.get(key, 0) + value
                        metric["headcall"] = dict(sorted(totals_headcall.items()))
                    if clip_norms is not None:
                        metric["clip_norms_before_clip"] = clip_norms
                        metric["learning_rates"] = {group.get("group_name", str(index)): group["lr"]
                                                    for index, group in enumerate(optimizer.param_groups)}
                    from .orchard_paths import enabled as orchard_enabled
                    if auxiliary_totals is not None:
                        from .auxiliary_losses import TERMS
                        metric['auxiliary'] = {f'{name}_row_mean': float(auxiliary_totals[index]) / settings['effective_batch_size']
                                               for index, name in enumerate(TERMS)
                                               if name in ('pose', 'depth') or auxiliary_heads.settings.get(name + '_weight')
                                               or (name == 'camera' and auxiliary_heads.has_camera)}
                        metric['auxiliary']['warmup_factor'] = auxiliary_heads.factor
                        if auxiliary_heads.has_camera:
                            metric['auxiliary']['camera_warmup_factor'] = auxiliary_heads.camera_factor
                            metric['auxiliary']['camera_backbone_gradient_scale'] = auxiliary_heads.camera.backbone_scale
                            metric['auxiliary']['camera_rows'] = int(auxiliary_totals[camera_rows_slot])
                            metric['auxiliary']['depth_rows'] = int(auxiliary_totals[depth_rows_slot])
                            # Unweighted per-term sums divided by the rows each term supervises (pose rows; depth rows).
                            metric['auxiliary']['camera_components'] = {
                                name: float(auxiliary_totals[component_slot + offset])
                                / max(1.0, float(auxiliary_totals[depth_rows_slot if name == 'point_depth' else camera_rows_slot]))
                                for offset, name in enumerate(CAMERA_COMPONENTS)
                                if name in auxiliary_heads.camera.last_components}
                        if auxiliary_heads.has_reason:
                            metric['auxiliary'].update(mixing=mixing, mixed_rows=int(auxiliary_totals[mixed_slot]),
                                                       mixed_queries=int(auxiliary_totals[mixed_slot + 1]))
                    if orchard_enabled() and last_checkpoint_timing is not None:
                        metric["previous_checkpoint"] = last_checkpoint_timing
                    if camera_gate is not None:
                        metric['auxiliary']['camera_gate_sample'] = gate_sample
                    if gate_record is not None:
                        metric['camera_gate'] = gate_record
                    if lm_gate is not None:
                        metric['auxiliary']['lm_gate_sample'] = lm_sample
                    if lm_record is not None:
                        metric['lm_gate'] = lm_record
                    if checkpoint is not None and realized["optimizer_steps"] == checkpoint["step"] + 1:
                        metric["resumed_from_step"] = checkpoint["step"]
                    store.write(f"steps/{realized['optimizer_steps']:04d}.json", metric)
                    write_metric(store, metrics, log, metric, stop_steps, label)
                    if gate_record is not None:
                        log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | camera_gate={gate_record['status']} "
                                  f"baseline_mean={gate_record['baseline_mean']} check_mean={gate_record['check_mean']} "
                                  f"relative_drop={gate_record['relative_drop']}\n")
                    if lm_record is not None:
                        log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | lm_gate={lm_record['status']} "
                                  f"reference_mean={lm_record['reference_mean']} check_mean={lm_record['check_mean']} "
                                  f"relative_increase={lm_record['relative_increase']}\n")
                stops = [record for record in (gate_record, lm_record) if record is not None and record['status'] == 'GATE_STOPPED']
                if stops:
                    gate_record = {**stops[0], 'reason': '; '.join(record['reason'] for record in stops),
                                   'camera_gate': gate_record, 'lm_gate': lm_record}
                    gate_stopped = gate_record
                    if rank == 0:
                        store.write('GATE_STOPPED.json', {**gate_record, 'schema': 'camera-gate-stop-v1',
                                    'optimizer_steps': realized['optimizer_steps'],
                                    'checkpoint': str(store.root / 'checkpoints' / f"step_{realized['optimizer_steps']}"),
                                    'stopped_at': datetime.now(timezone.utc).isoformat()})
                scheduled = checkpoints.due(realized["optimizer_steps"], batch_index, steps_per_epoch, stop_steps, run_control)
                stopping, rolling_due = checkpoints.agree(rank, stop, rolling)
                stopping = stopping and realized["optimizer_steps"] < stop_steps
                if gate_stopped is not None or scheduled or rolling_due or stopping:
                    state = {"realized": dict(realized), "row_count": len(rows), "microbatch_size": microbatch,
                             "planned_steps": planned_steps, "step_seconds": step_seconds, "peak_per_rank": list(peak_per_rank),
                             "training_wall_seconds": training_wall_before + time.perf_counter() - training_started,
                             "total_wall_seconds": total_wall_before + time.perf_counter() - started}
                    kind = ("scheduled" if gate_stopped is not None
                            else checkpoints.checkpoint_kind(realized["optimizer_steps"], stop_steps, run_control, scheduled, stopping))
                    # Full fine-tuning: a milestone pins a milestone export and sends its full state to the rolling pool;
                    # a stop on a milestone step still pins its full state.
                    milestone_export = full and kind == "milestone"
                    if milestone_export and stopping:
                        kind = "signal"
                    checkpoint_started = time.perf_counter()
                    saved = (checkpoints.save_full_checkpoint(store, header, trainables, optimizer, state,
                                                              report["shard_layout_sha256"], kind=kind) if full
                             else checkpoints.save_checkpoint(store, header, adapters, optimizer, state, distributed, kind=kind))
                    if milestone_export:
                        saved["milestone_export"] = checkpoints.save_milestone_export(
                            store, header, distributed, base_names, realized["optimizer_steps"],
                            {key: report[key] for key in ("mode", "train", "group_parameters", "trainable_parameters",
                                                          "base_parameters") if key in report},
                            geometry=geometry, auxiliary_heads=auxiliary_heads)
                    rolling.saved()
                    last_checkpoint_timing = {"step": realized["optimizer_steps"],
                                              "seconds": time.perf_counter() - checkpoint_started}
                    if rank == 0:
                        from .orchard_paths import enabled as orchard_enabled
                        if orchard_enabled():
                            with (store.root / "checkpoint_metrics.jsonl").open("a") as timings:
                                timings.write(json.dumps(last_checkpoint_timing) + "\n")
                    if not stopping and gate_stopped is None and realized["optimizer_steps"] < stop_steps:
                        # A request that arrived during the save stops here, on the checkpoint just written.
                        stopping = checkpoints.agree(rank, stop)[0]
                if gate_stopped is not None or stopping:
                    break
            if gate_stopped is not None or stopping or realized["optimizer_steps"] >= stop_steps:
                break
        if gate_stopped is not None:
            from .camera_gate import GATE_STOPPED_EXIT_CODE
            summary = None
            if rank == 0:
                log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | status=GATE_STOPPED optimizer_steps={realized['optimizer_steps']} "
                          f"reason={gate_stopped['reason']}\n")
                summary = tag({"status": "GATE_STOPPED", "exit_code": GATE_STOPPED_EXIT_CODE, "protocol_version": VERSION,
                               "realized": realized, "gate": binding(store.root / "GATE_STOPPED.json")}, label)
            outcome = [summary]
            dist.broadcast_object_list(outcome, src=0)
            return outcome[0]
        if stopping:
            reasons = gather(stop.reason, world)
            summary = None
            if rank == 0:
                # In the loop a stop always follows a save of the current step; before it, the parent holds the state.
                marker = checkpoints.write_stop_marker(store, realized["optimizer_steps"], reasons, saved)
                log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | status=STOPPED_ON_SIGNAL "
                          f"optimizer_steps={realized['optimizer_steps']} checkpoint={saved and saved['durable']}\n")
                summary = tag({"status": "STOPPED_ON_SIGNAL", "protocol_version": VERSION, "realized": realized,
                               "checkpoint": saved and saved["durable"], "marker": binding(marker)}, label)
            outcome = [summary]
            dist.broadcast_object_list(outcome, src=0)
            return outcome[0]
        optimizer.zero_grad(set_to_none=True)
        if parallel == "fsdp":
            fsdp.check_frozen_shards(distributed, frozen)
        else:
            frozen_base_check(model, frozen)
        checks = gather({"rank": rank, "frozen_base_unchanged": True}, world)
        # The frozen-VLM stage publishes only its attached modules: its base is the unchanged snapshot.
        state = (fsdp.publication_state(distributed) if parallel == "fsdp" and (full_block is None or full) else None)
        sharded_updates = full_ft.group_report(sharded, process_group, values=sharded_before) if full else {}
        summary = None
        if rank == 0:
            updates = group_updates(groups, before)
            if full:
                full_ft.check_updates(sharded_updates, report)
                updates.update(sharded_updates)
            geometry_updates = {"geometry": group_updates(geometry_group, geometry_before)["geometry"]} if geometry_group else {}
            store.write("adapter_updates.json", {"groups": updates, **geometry_updates})
            adapter_path = store.root / adapter_directory(label)
            if full_block is None:
                save_options = {"state_dict": state} if parallel == "fsdp" else {}
                model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False, **save_options)
                adapter = {"weights": binding(adapter_path / "adapter_model.safetensors"),
                           "config": binding(adapter_path / "adapter_config.json")}
            elif full:
                adapter_path.mkdir(exist_ok=False)
                export = full_ft.save_export(full_ft.export_tensors(state, base_names), adapter_path / full_ft.EXPORT_DIRECTORY,
                                             {"student": student, "base": protocol["base"], "base_sha256": protocol["base_sha256"]},
                                             {key: report[key] for key in ("mode", "train", "group_parameters", "trainable_parameters",
                                                                           "base_parameters") if key in report})
                adapter = {"full_weights": binding(adapter_path / full_ft.EXPORT_DIRECTORY / full_ft.EXPORT_MANIFEST),
                           "full_weights_bytes": export["bytes"], "full_weights_tensors": export["tensor_count"]}
            else:
                adapter_path.mkdir(exist_ok=False)
                adapter = {"frozen_vlm": True}
            if settings.get("unfreeze_vision_blocks"):
                from .adapters import save_vision_blocks
                vision_path = adapter_path / "vision_blocks.safetensors"
                save_vision_blocks(model, vision_path, state_dict=state)
                adapter["vision_blocks"] = binding(vision_path)
            if auxiliary_heads is not None:
                auxiliary_path = store.root / 'auxiliary_heads.pt'
                with auxiliary_path.open('xb') as handle:
                    torch.save({name: value.detach().cpu() for name, value in auxiliary_heads.state_dict().items()}, handle)
                store.write('auxiliary_heads.json', {'weights': binding(auxiliary_path), **auxiliary_heads.manifest()})
            store.write("adapter_bindings.json", adapter)
            store.write(adapter_path / "provenance.json", {"adapter": adapter, "protocol_version": VERSION})
            geometry_result = None
            if geometry is not None:
                from .geometry_input import MANIFEST_NAME, WEIGHTS_NAME, save as save_geometry
                geometry_path = store.root / "geometry"
                geometry_path.mkdir(exist_ok=True)
                if any((geometry_path / name).exists() for name in (WEIGHTS_NAME, MANIFEST_NAME)):
                    raise ValueError("Refusing to replace a written geometry projector")
                save_geometry(geometry, geometry_path)
                geometry_result = {"weights": binding(geometry_path / WEIGHTS_NAME), "manifest": binding(geometry_path / MANIFEST_NAME),
                                   "parameters": report["geometry_parameters"]}
            throughput = {"world_size": world, "microbatch_size": microbatch, "gradient_accumulation": accumulation,
                          "optimizer_steps": realized["optimizer_steps"], "optimization_step_seconds": step_seconds,
                          "training_wall_seconds": training_wall_before + time.perf_counter() - training_started,
                          "total_wall_seconds": total_wall_before + time.perf_counter() - started,
                          "rows_per_second": realized["training_rows"] / step_seconds,
                          "source_rows_per_second": realized["source_rows"] / step_seconds,
                          "assistant_tokens_per_second": realized["target_tokens_including_eos"] / step_seconds,
                          "peak_reserved_bytes_per_rank": peak_per_rank, "realized": realized,
                          "throughput_smoke": settings["max_steps"] is not None}
            if topology["nnodes"] > 1:
                throughput.update(topology)
            store.write("throughput.json", throughput)
            status = "SMOKE_COMPLETE" if settings["max_steps"] is not None else "TRAINED"
            result = {**header, "schema": "completed-provisional-diagnostic-training-v1", "status": status,
                      "adapter": adapter, "realized": realized, "training_scenes": shared["counts"]["training_scenes"],
                      "adapter_parameters": report["trainable_parameters"], "frozen_base_unchanged": True,
                      **({"full_ft": {key: report[key] for key in ("schema", "mode", "train", "learning_rates", "group_parameters",
                                                                     "trainable_parameters", "base_parameters", "init_modules",
                                                                     "merged_init_adapter", "init_export",
                                                                     "shard_layout_sha256") if key in report},
                          "auxiliary_heads": binding(store.root / "auxiliary_heads.pt") if auxiliary_heads is not None else None}
                         if full_block is not None else {}),
                      **({"frozen_adapter_parameters": report["frozen_group_parameters"]}
                         if "frozen_group_parameters" in report else {}),
                      **({"geometry": geometry_result} if geometry_result is not None else {}),
                      "rank_checks": checks, "completed_epochs": realized["optimizer_steps"] // steps_per_epoch,
                      "throughput": binding(store.root / "throughput.json"),
                      "completed_at": datetime.now(timezone.utc).isoformat()}
            if status == "TRAINED":
                from .ddp_config import validate_training_result
                validate_training_result(store.record(result), protocol, label)
            store.write("training_result.json", result)
            log.write(f"{datetime.now(timezone.utc).isoformat()} | {label} | status={status} optimizer_steps={realized['optimizer_steps']}\n")
            summary = tag({"status": status, "protocol_version": VERSION, "realized": realized,
                           "result": binding(store.root / "training_result.json")}, label)
        outcome = [summary]
        dist.broadcast_object_list(outcome, src=0)
        return outcome[0]
    finally:
        for stream in (metrics, log):
            if stream is not None:
                stream.close()
        dist.destroy_process_group()
        stop.restore()
