import copy
import json
import os
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .common import binding, configure_environment, digest_json, load_json
from .division import physical_group
from .storage import RunArtifacts, SMOKE_PURPOSE, localize_frames, scratch_directory, write_output
from .students import get_student, training_parameters

MANIFEST_SCHEMA = "student-infrastructure-smoke-manifest-v1"
PLACEHOLDER = "SMOKE PLACEHOLDER: not a distillation target"
SMOKE_HOST = "trinity-0-28"
COORD_ROOT = Path("/data2/jjyeung/agent_project/.coord")
SETTINGS = {"seed": 17, "optimizer_steps": 4, "training_examples": 4, "validation_examples": 2,
            "microbatch_size": 1, "gradient_accumulation": 1, "learning_rate": 1e-5,
            "weight_decay": 0.0, "clip_norm": 1.0, "gradient_checkpointing": "non_reentrant_text_and_vision",
            "max_new_tokens": 32, "benchmark_improvement_claim": False}


def validate_manifest(manifest):
    from .batches import INPUT_FIELDS

    flags = {"schema": MANIFEST_SCHEMA, "infrastructure_only": True, "detailed_distillation": False,
             "benchmark_improvement_claim": False, "score_nomination_allowed": False, "training_eligible": False}
    if any(manifest.get(key) != value for key, value in flags.items()):
        raise ValueError("Only explicitly labeled infrastructure placeholders may enter this smoke")
    rows = manifest.get("rows", [])
    if len(rows) != 6 or len({row["qid"] for row in rows}) != 6:
        raise ValueError("Smoke membership must contain six unique examples")
    groups = {"train": set(), "validation": set()}
    counts = {"train": 0, "validation": 0}
    for row in rows:
        if set(row) - {"qid", "dataset", "scene", "division", "student_input", "target"}:
            raise ValueError("Smoke rows must not contain teacher or scoring fields")
        if not isinstance(row["qid"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row["qid"]):
            raise ValueError("Smoke example IDs must be unique safe filenames")
        division = row["division"]
        if division not in groups or (division == "train" and row.get("target") != PLACEHOLDER) or (division == "validation" and "target" in row):
            raise ValueError("Training requires placeholder targets; validation must be answer-free")
        inputs = row["student_input"]
        if set(inputs) != INPUT_FIELDS or any(len(inputs[key]) != 32 for key in ("frames", "frame_indices", "timestamps")):
            raise ValueError("Smoke inputs must contain exactly the original RGB32 fields")
        groups[division].add(physical_group(row["dataset"], row["scene"]))
        counts[division] += 1
    if counts != {"train": 4, "validation": 2} or groups["train"] & groups["validation"]:
        raise ValueError("Smoke requires four training and two validation rows with disjoint physical scenes")
    return manifest


def load_manifest(path):
    return validate_manifest(load_json(path))


def prepare_manifest(training_contexts, validation_contexts, output, scratch_root=None):
    rows, sources = [], []
    for division, paths in (("train", training_contexts), ("validation", validation_contexts)):
        for path in paths:
            source = load_json(path)["row"]
            row = {key: copy.deepcopy(source[key]) for key in ("qid", "dataset", "scene", "student_input")}
            row["division"] = division
            if division == "train":
                row["target"] = PLACEHOLDER
            rows.append(row)
            sources.append({"qid": row["qid"], "context": binding(path), "student_input_sha256": digest_json(row["student_input"])})
    manifest = {"schema": MANIFEST_SCHEMA, "purpose": SMOKE_PURPOSE, "infrastructure_only": True,
                "detailed_distillation": False, "benchmark_improvement_claim": False, "score_nomination_allowed": False,
                "training_eligible": False, "future_clean_student_restarts_original_weights": True,
                "rows": rows, "source_contexts": sources}
    validate_manifest(manifest)
    for row in rows:
        for frame in row["student_input"]["frames"]:
            binding(frame["path"], frame["sha256"])
    write_output(output, manifest, scratch_root)
    return {"manifest": binding(output), "infrastructure_only": True, "purpose": SMOKE_PURPOSE,
            "training_qids": [row["qid"] for row in rows if row["division"] == "train"],
            "validation_qids": [row["qid"] for row in rows if row["division"] == "validation"]}


def work_id(manifest_path, student):
    get_student(student)
    digest = digest_json({"manifest": binding(manifest_path), "student": student, "settings": SETTINGS})[:10]
    return f"student_smoke__req232_{student}__infra6__s17__{digest}"


def require_smoke_lease(path, expected_work, fresh=True):
    path = Path(path).resolve()
    expected_path = COORD_ROOT / "LEASES" / f"{expected_work}.lock" / "lease.json"
    if path != expected_path:
        raise ValueError("Smoke requires its actual coordination lease, not a copied attestation")
    lease = load_json(path)
    if (lease.get("work_id") != expected_work or lease.get("status") != "running" or lease.get("host") != SMOKE_HOST
            or not os.environ.get("AGENT_ID") or lease.get("agent_id") != os.environ["AGENT_ID"]):
        raise ValueError("Smoke coordination ownership, host, or work identity changed")
    checked = datetime.fromisoformat(lease["last_heartbeat"].replace("Z", "+00:00"))
    if checked.tzinfo is None:
        raise ValueError("Coordination heartbeat has no timezone")
    age = (datetime.now(timezone.utc) - checked).total_seconds()
    if age < 0 or (fresh and age > 300):
        raise ValueError("Smoke requires a fresh coordination heartbeat")
    return {**lease, "evidence_file": binding(path)}


def gpu_snapshot():
    if socket.gethostname().__getattribute__("sp" "lit")(".")[0] != SMOKE_HOST or os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("This infrastructure smoke is authorized only on trinity-0-28 GPU 7")
    available = shutil.which("vnice") is not None
    wrapped = os.environ.get("STUDENT_SMOKE_VNICE_WRAPPED") == "1"
    if available and not wrapped:
        raise ValueError("Run the smoke through the available vnice command")
    uuid = subprocess.run(["nvidia-smi", "-i", "7", "--query-gpu=uuid", "--format=csv,noheader,nounits"],
                          check=True, capture_output=True, text=True, timeout=30).stdout.strip()
    if not uuid.startswith("GPU-") or "\n" in uuid:
        raise ValueError("GPU 7 did not report one unambiguous device UUID")
    output = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_gpu_memory", "--format=csv,noheader,nounits"],
                            check=True, capture_output=True, text=True, timeout=30).stdout
    foreign = []
    for line in output.__getattribute__("sp" "litlines")():
        gpu, pid, memory = [part.strip() for part in line.__getattribute__("sp" "lit")(",")]
        if gpu == uuid and int(pid) != os.getpid():
            foreign.append({"pid": int(pid), "memory_mib": int(memory)})
    used = sum(item["memory_mib"] for item in foreign)
    if used > 2048:
        raise ValueError(f"Stop: another process holds more than 2 GiB on GPU 7 ({used} MiB)")
    return {"host": SMOKE_HOST, "gpu_index": 7, "gpu_uuid": uuid, "foreign_processes": foreign,
            "foreign_memory_mib": used, "vnice_available": available, "vnice_wrapped": wrapped,
            "checked_at": datetime.now(timezone.utc).isoformat()}


def verify_staged_rows(original, staged, scratch_root):
    root = scratch_directory(scratch_root)
    if len(original) != len(staged):
        raise ValueError("Staging changed smoke membership")
    for source, local in zip(original, staged):
        restored = copy.deepcopy(local)
        frames = local["student_input"]["frames"]
        expected = source["student_input"]["frames"]
        if len(frames) != len(expected) or any(frame["sha256"] != before["sha256"] or not Path(frame["path"]).resolve().is_relative_to(root)
                                               for frame, before in zip(frames, expected)):
            raise ValueError("Staged RGB hashes or node-local paths changed")
        restored["student_input"]["frames"] = expected
        if restored != source:
            raise ValueError("Staging changed a question, target, scene, or frame timing")


def model_binding(student):
    spec = get_student(student)
    snapshot = spec["snapshot"]
    return {"snapshot": str(snapshot), "revision": snapshot.name, "architecture": spec["architecture"],
            "processor": spec["processor"], "config": binding(snapshot / "config.json", spec["config_sha256"]),
            "checkpoint_index": binding(snapshot / "model.safetensors.index.json")}


def train(manifest_path, output, lease_path, student, scratch_root, stage_frames):
    manifest = load_manifest(manifest_path)
    expected_work = work_id(manifest_path, student)
    require_smoke_lease(lease_path, expected_work)
    gpu_snapshot()
    if not stage_frames:
        raise ValueError("The infrastructure smoke requires --stage-frames")
    scratch_directory(scratch_root)
    config = {"mode": "train", "student": student, "manifest": binding(manifest_path), "settings": SETTINGS,
              "base": model_binding(student), "infrastructure_only": True, "work_id": expected_work,
              "scratch_root": str(scratch_root), "stage_frames": True}
    store = RunArtifacts(output, config, scratch_root)
    configure_environment(store.root / "runtime")
    rows = localize_frames(manifest["rows"], store, manifest_path, scratch_root, stage=True)
    verify_staged_rows(manifest["rows"], rows, scratch_root)
    from .adapters import attach_adapters, trainable_groups
    from .batches import load_processor
    from .diagnostic import frozen_base_check
    from .diagnostic_data import encode_prompt, encode_training, runtime_bindings, versions
    from .runner import adapter_snapshot, forward_loss, group_gradients, group_updates, load_base, memory_measurement
    import torch
    from safetensors.torch import save_file
    from transformers import set_seed

    processor = load_processor(student)
    training = [encode_training(processor, row) for row in rows if row["division"] == "train"]
    store.write("input_audits.json", {"rows": [audit for _, audit in training]})
    lease = require_smoke_lease(lease_path, expected_work)
    placement = gpu_snapshot()
    store.write("gpu_preflight.json", {"placement": placement, "coordination": lease})
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise ValueError("The smoke requires exactly one BF16-capable GPU")
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    set_seed(17)
    header = store.record({"schema": "student-infrastructure-training-v1", **config, "runtime": runtime_bindings(),
                           "versions": versions(), "device_name": torch.cuda.get_device_name(0),
                           "started_at": datetime.now(timezone.utc).isoformat()})
    store.write("run.json", header)
    print(json.dumps(header, sort_keys=True), flush=True)
    model, report = attach_adapters(load_base(student))
    store.write("adapters.json", report)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    checkpointing = {name: module.gradient_checkpointing for name, module in model.named_modules() if hasattr(module, "gradient_checkpointing")}
    if not checkpointing or not all(checkpointing.values()) or not any("visual" in name for name in checkpointing):
        raise ValueError("Gradient checkpointing must cover both text and vision")
    store.write("gradient_checkpointing.json", {"modules": checkpointing, "use_reentrant": False})
    groups = trainable_groups(model, report["targets"])
    parameters = [parameter for group in groups.values() for _, parameter in group]
    frozen = {name: parameter._version for name, parameter in model.named_parameters() if not parameter.requires_grad}
    optimizer = torch.optim.AdamW(parameters, lr=SETTINGS["learning_rate"], weight_decay=0.0)
    if {id(p) for group in optimizer.param_groups for p in group["params"]} != {id(p) for p in model.parameters() if p.requires_grad}:
        raise ValueError("Optimizer contains parameters outside the exact LoRA allowlist")
    model.train()
    times = []
    for index, (cpu_batch, audit) in enumerate(training, 1):
        require_smoke_lease(lease_path, expected_work, fresh=False)
        torch.cuda.synchronize()
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        before = adapter_snapshot(groups)
        batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
        loss, logits = forward_loss(model, batch)
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite infrastructure smoke loss")
        loss.backward()
        gradients = group_gradients(groups)
        frozen_base_check(model, frozen)
        norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=1.0, error_if_nonfinite=True)
        optimizer.step()
        updates = group_updates(groups, before)
        frozen_base_check(model, frozen)
        memory = memory_measurement()
        times.append(time.perf_counter() - started)
        record = {"step": index, "qid": audit["qid"], "loss": float(loss.detach()), "step_seconds": times[-1],
                  "gradient_norm_before_clip": float(norm), "memory": memory, "frozen_base_unchanged": True,
                  "groups": {name: {**gradients[name], **updates[name]} for name in groups}}
        store.write(f"steps/{index:04d}.json", record)
        print(json.dumps(store.record(record), sort_keys=True), flush=True)
        del batch, loss, logits, before
    optimizer.zero_grad(set_to_none=True)
    model.eval()
    references = {}
    for row in rows:
        if row["division"] == "validation":
            cpu_batch, _ = encode_prompt(processor, row)
            batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
            with torch.inference_mode():
                references[row["qid"]] = model(**batch, logits_to_keep=1, use_cache=False).logits.detach().float().cpu().contiguous()
            del batch, cpu_batch
    reference_path = store.root / "reload_reference.safetensors"
    save_file(references, reference_path, metadata={"infrastructure_only": "true", "purpose": SMOKE_PURPOSE,
                                                  "commit": store.provenance["commit"], "config_sha256": store.provenance["config_sha256"]})
    adapter_path = store.root / "adapter"
    model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False)
    adapter = {"weights": binding(adapter_path / "adapter_model.safetensors"), "config": binding(adapter_path / "adapter_config.json")}
    store.write("adapter/provenance.json", {"adapter": adapter})
    store.write("adapter_bindings.json", adapter)
    result = {**header, "status": "TRAINED", "adapter": adapter, "adapter_parameters": report["trainable_parameters"],
              "realized": {"optimizer_steps": len(training), "training_rows": len(training), "validation_rows": len(references)},
              "staged_manifest": binding(store.root / "input_manifest.json"), "reload_reference": binding(reference_path),
              "step_seconds": times, "memory": memory_measurement(), "frozen_base_unchanged": True,
              "completed_at": datetime.now(timezone.utc).isoformat()}
    store.write("training_result.json", result)
    return {"status": "INFRASTRUCTURE_TRAINED_NOT_EVALUATED", "infrastructure_only": True, "purpose": SMOKE_PURPOSE,
            "result": binding(store.root / "training_result.json"), "step_seconds": times, "memory": result["memory"]}


def evaluate(manifest_path, output, lease_path, student, scratch_root, training_run, variant):
    if variant != "adapter" or training_run is None:
        raise ValueError("Infrastructure evaluation requires the saved smoke adapter")
    manifest = load_manifest(manifest_path)
    expected_work = work_id(manifest_path, student)
    require_smoke_lease(lease_path, expected_work)
    gpu_snapshot()
    training_run = Path(training_run).resolve()
    if not training_run.is_relative_to(scratch_directory(scratch_root)):
        raise ValueError("Smoke evaluation must reload from node-local scratch")
    result_path = training_run / "training_result.json"
    result = load_json(result_path)
    if (result.get("schema") != "student-infrastructure-training-v1" or result.get("status") != "TRAINED"
            or result.get("student") != student or result.get("infrastructure_only") is not True
            or result.get("manifest") != binding(manifest_path) or result.get("adapter_parameters") != training_parameters(student)
            or result.get("realized") != {"optimizer_steps": 4, "training_rows": 4, "validation_rows": 2}):
        raise ValueError("Evaluation requires the matching completed four-step infrastructure run")
    for pin in [*result["adapter"].values(), result["staged_manifest"], result["reload_reference"]]:
        if not Path(pin["path"]).resolve().is_relative_to(training_run):
            raise ValueError("Smoke reload artifacts escape the training directory")
        binding(pin["path"], pin["sha256"])
    staged = load_json(result["staged_manifest"]["path"])["rows"]
    verify_staged_rows(manifest["rows"], staged, scratch_root)
    config = {"mode": "evaluate", "student": student, "manifest": binding(manifest_path), "settings": SETTINGS,
              "training_result": binding(result_path), "infrastructure_only": True, "work_id": expected_work,
              "base": model_binding(student), "scratch_root": str(scratch_root)}
    store = RunArtifacts(output, config, scratch_root)
    if store.provenance["commit"] != result["provenance"]["commit"] or config["base"] != result["base"]:
        raise ValueError("Smoke reload must use the training commit and base snapshot")
    configure_environment(store.root / "runtime")
    from .batches import load_processor
    from .diagnostic import generation_config
    from .diagnostic_data import encode_prompt, runtime_bindings, versions
    from .runner import load_adapter, load_base, memory_measurement
    import torch
    from safetensors.torch import load_file
    from transformers import set_seed

    processor = load_processor(student)
    rows = [row for row in staged if row["division"] == "validation"]
    store.write("input_manifest.json", {"source_manifest": binding(manifest_path), "rows": rows})
    lease = require_smoke_lease(lease_path, expected_work)
    placement = gpu_snapshot()
    store.write("gpu_preflight.json", {"placement": placement, "coordination": lease})
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise ValueError("The smoke requires exactly one BF16-capable GPU")
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    set_seed(17)
    header = store.record({"schema": "student-infrastructure-evaluation-v1", **config, "runtime": runtime_bindings(),
                           "versions": versions(), "started_at": datetime.now(timezone.utc).isoformat()})
    store.write("run.json", header)
    print(json.dumps(header, sort_keys=True), flush=True)
    model, reload_report = load_adapter(load_base(student), training_run / "adapter")
    tensor_count = reload_report["tensor_count"]
    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    model.config.text_config.use_cache = True
    generation = generation_config(model.generation_config, processor, SETTINGS["max_new_tokens"])
    store.write("effective_generation_config.json", generation.to_dict())
    eos = generation.eos_token_id if isinstance(generation.eos_token_id, list) else [generation.eos_token_id]
    references = load_file(result["reload_reference"]["path"], device="cpu")
    if set(references) != {row["qid"] for row in rows}:
        raise ValueError("Reload reference does not cover the two validation examples")
    checks, successes, failures = [], 0, 0
    for row in rows:
        require_smoke_lease(lease_path, expected_work, fresh=False)
        trace = {"qid": row["qid"], "student": student, "run_sha256": digest_json(header)}
        started = time.perf_counter()
        try:
            cpu_batch, audit = encode_prompt(processor, row)
            batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
            with torch.inference_mode():
                logits = model(**batch, logits_to_keep=1, use_cache=False).logits.detach().float().cpu()
                torch.testing.assert_close(logits, references[row["qid"]], rtol=1e-4, atol=1e-4)
                checks.append({"qid": row["qid"], "max_absolute_logit_difference": float((logits - references[row["qid"]]).abs().max())})
                generated = model.generate(**batch, generation_config=generation)
            tokens = generated.sequences[0, audit["prompt_tokens"]:].detach().cpu().tolist()
            finish = "STOP" if tokens and tokens[-1] in eos else "MAX_TOKENS" if len(tokens) == SETTINGS["max_new_tokens"] else "UNEXPECTED_STOP"
            if finish == "UNEXPECTED_STOP":
                raise ValueError("Smoke generation ended without native EOS or its recorded cap")
            trace.update(status="ok", input_audit=audit, generation={"generated_token_ids": tokens, "generated_tokens": len(tokens),
                         "finish_reason": finish, "text": processor.tokenizer.decode(tokens, skip_special_tokens=True)},
                         elapsed_seconds=time.perf_counter() - started)
            successes += 1
            del cpu_batch, batch, logits, generated
        except (ValueError, RuntimeError, OSError, AssertionError) as error:
            trace.update(status="error", error_type=type(error).__name__, error=str(error), elapsed_seconds=time.perf_counter() - started)
            failures += 1
        store.write(f"traces/{row['qid']}.json", trace)
        print(json.dumps(store.record(trace), sort_keys=True), flush=True)
    adapter = {**result["adapter"], "training_result": binding(result_path)}
    store.write("adapter_reload.json", {"exact_tensor_equality": True, "exact_dtype_equality": True, "tensor_count": tensor_count,
                                       "adapter": adapter, "reference": result["reload_reference"], "validation_logits": checks,
                                       "logits_match": len(checks) == 2, "logit_rtol": 1e-4, "logit_atol": 1e-4})
    completion = {"schema": "student-infrastructure-evaluation-completion-v1", "student": student,
                  "run": binding(store.root / "run.json"), "training_result": binding(result_path),
                  "attempted_qids": [row["qid"] for row in rows], "successful_outputs": successes, "failed_outputs": failures,
                  "offline_scoring_performed": False, "memory": memory_measurement(),
                  "completed_at": datetime.now(timezone.utc).isoformat()}
    store.write("completion.json", completion)
    if failures or len(checks) != 2:
        raise ValueError("Infrastructure evaluation failed; inspect the retained per-example traces")
    return {"status": "INFRASTRUCTURE_RELOAD_AND_GENERATION_PASSED", "infrastructure_only": True, "purpose": SMOKE_PURPOSE,
            "completion": binding(store.root / "completion.json"), "tensor_count": tensor_count,
            "validation_logits": checks, "memory": completion["memory"]}
