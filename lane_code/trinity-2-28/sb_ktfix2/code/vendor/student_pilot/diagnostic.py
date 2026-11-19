import argparse
import gc
import json
import random
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from .common import binding, configure_environment, digest_json, load_json
from .students import STUDENTS, get_student, training_parameters
from .storage import RunArtifacts, adapter_directory, finalize, localize_frames, provisional_flags, require_mode, tag
from .conversion import verify_pin
from .diagnostic_data import FLAGS, GENERATION, check_heldout_inputs, compare_scores, encode_prompt, encode_training, load_heldout, load_protocol, load_retry_plan, load_training, prepare_heldout, prepare_protocol, prepare_training, runtime_bindings, score_run
from .lease import require_lease


def execution_contract(label, manifest_path, protocol_path, student, mode, variant=None):
    if label is None:
        return require_lease, load_protocol, load_training if mode == "train" else load_heldout
    from . import provisional_data
    from .provisional import request_identity, require_lease as provisional_lease

    request = request_identity(mode, student, manifest_path, protocol_path, label, variant)
    check = partial(provisional_lease, label=label, expected_work=request["work_id"], protocol_sha256=request["protocol_sha256"])
    loader = provisional_data.load_training if mode == "train" else provisional_data.load_heldout
    protocol_loader = provisional_data.load_single_training_protocol if mode == "train" else provisional_data.load_protocol
    return check, partial(protocol_loader, label=label), partial(loader, label=label)


def admitted_device(lease_path, lease_check=None, provisional_diagnostic=None):
    import torch

    if provisional_diagnostic is not None:
        from uuid import UUID

        from .provisional import admission_probe

        lease = lease_check(lease_path, fresh=False)
        lease["admission_probe"] = admission_probe(lease)
    else:
        lease = (lease_check or require_lease)(lease_path)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise ValueError("Supervisor must expose exactly its leased BF16-capable CUDA device")
    torch.cuda.set_device(0)
    if provisional_diagnostic is not None:
        try:
            cuda_uuid = torch.cuda.get_device_properties(0).uuid
            cuda_uuid = "GPU-" + str(UUID(str(cuda_uuid).removeprefix("GPU-")))
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            raise ValueError("Admission probe cannot obtain CUDA device 0 physical UUID") from error
        probe = lease["admission_probe"]
        if cuda_uuid != lease["gpu_uuid"] or cuda_uuid != probe["nvidia_smi_gpu_uuid"]:
            raise ValueError("CUDA device 0 UUID does not match the bound lease and nvidia-smi probe UUID")
        probe["cuda_gpu_uuid"] = cuda_uuid
    torch.cuda.reset_peak_memory_stats()
    return lease


def frozen_base_check(model, versions):
    if any(parameter.requires_grad or parameter.grad is not None or parameter._version != versions[name]
           for name, parameter in model.named_parameters() if name in versions):
        raise ValueError("A frozen original base parameter changed or received a gradient")


def train(manifest_path, protocol_path, output, lease_path, student="onethinker", scratch_root=None, stage_frames=False, provisional_diagnostic=None):
    lease_check, protocol_loader, manifest_loader = execution_contract(provisional_diagnostic, manifest_path, protocol_path, student, "train")
    lease_check(lease_path)
    protocol = protocol_loader(protocol_path, weights=True, student=student)
    manifest = manifest_loader(manifest_path)
    scope = provisional_flags(provisional_diagnostic)
    if provisional_diagnostic is not None:
        scope["PROVISIONAL_DIVISION_SHA"] = protocol["PROVISIONAL_DIVISION_SHA"]
    if manifest["protocol"] != binding(protocol_path) or not manifest["training_ready"] or not manifest["rows"]:
        raise ValueError("Training requires nonempty, accepted, token-fitting detailed targets under the frozen protocol")
    from .adapters import attach_adapters, trainable_groups
    from .batches import load_processor
    from .runner import adapter_snapshot, forward_loss, group_gradients, group_updates, load_base, memory_measurement
    import torch
    from transformers import set_seed

    config = {"mode": "train", "student": student, "manifest": binding(manifest_path), "protocol": binding(protocol_path), **scope,
              "settings": protocol["training"], "stage_frames": stage_frames, "scratch_root": str(scratch_root) if scratch_root else None}
    store = RunArtifacts(output, config, scratch_root)
    output = store.root
    configure_environment(output / "runtime")
    processor = load_processor(student)
    audits = {audit["qid"]: audit for audit in manifest["input_audits"]}
    order = localize_frames(manifest["rows"], store, manifest_path, scratch_root, stage_frames)
    random.Random(17).shuffle(order)
    lease = admitted_device(lease_path, lease_check, provisional_diagnostic)
    set_seed(17)
    header = {"schema": "one-pass-provisional-diagnostic-training-v1" if provisional_diagnostic is not None else "one-pass-detailed-diagnostic-training-v1", **FLAGS, "student": student,
              "protocol": binding(protocol_path), "training_manifest": binding(manifest_path),
              "base": protocol["base"], "base_sha256": protocol["base_sha256"], "settings": protocol["training"],
              "versions": protocol["versions"], "runtime": protocol["runtime"] if provisional_diagnostic is not None else runtime_bindings(), "lease": lease,
              "base_restart": "fresh_load_of_original_snapshot_no_smoke_adapter", "row_order": [row["qid"] for row in order],
              "device_name": torch.cuda.get_device_name(0), "base_dtype": "bfloat16", "attention_implementation": "sdpa",
              "started_at": datetime.now(timezone.utc).isoformat()}
    header = store.record(header)
    store.write(output / "run.json", header)
    model, report = attach_adapters(load_base(student))
    store.write(output / "adapters.json", report)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    checkpointing = {name: module.gradient_checkpointing for name, module in model.named_modules() if hasattr(module, "gradient_checkpointing")}
    if not checkpointing or not all(checkpointing.values()) or not any("visual" in name for name in checkpointing):
        raise ValueError("Non-reentrant gradient checkpointing must cover text and vision")
    store.write(output / "gradient_checkpointing.json", checkpointing)
    groups = trainable_groups(model, report["targets"])
    parameters = [parameter for group in groups.values() for _, parameter in group]
    frozen = {name: parameter._version for name, parameter in model.named_parameters() if not parameter.requires_grad}
    optimizer = torch.optim.AdamW(parameters, lr=1e-5, weight_decay=0.0)
    if {id(parameter) for group in optimizer.param_groups for parameter in group["params"]} != {id(parameter) for parameter in model.parameters() if parameter.requires_grad}:
        raise ValueError("Optimizer parameter set differs from the exact adapter allowlist")
    store.write(output / "optimizer.json", {"class": "AdamW", "defaults": optimizer.defaults,
               "loss_reduction": "mean assistant-token CE per row, then mean over each accumulation window"})
    model.train()
    realized = {"training_rows": 0, "frames": 0, "target_tokens_including_eos": 0, "prompt_tokens": 0, "optimizer_steps": 0}
    for start in range(0, len(order), 4):
        torch.cuda.synchronize()
        step_started = time.perf_counter()
        window = order[start:start + 4]
        optimizer.zero_grad(set_to_none=True)
        before = adapter_snapshot(groups)
        losses = []
        for row in window:
            lease_check(lease_path, fresh=False)
            cpu_batch, audit = encode_training(processor, row)
            if audit != audits[row["qid"]]:
                raise ValueError("Training preprocessing changed after the pre-evaluation admission receipt")
            batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
            loss, logits = forward_loss(model, batch)
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite diagnostic assistant loss")
            (loss / len(window)).backward()
            losses.append({"qid": row["qid"], "assistant_loss": loss.detach().item(),
                           "target_tokens_including_eos": audit["assistant_tokens_including_eos"], "frames": audit["frame_count"]})
            realized["training_rows"] += 1
            realized["frames"] += audit["frame_count"]
            realized["target_tokens_including_eos"] += audit["assistant_tokens_including_eos"]
            realized["prompt_tokens"] += audit["prompt_tokens"]
            del cpu_batch, batch, loss, logits
        gradients = group_gradients(groups)
        frozen_base_check(model, frozen)
        norm = torch.nn.utils.clip_grad_norm_(parameters, max_norm=1.0, error_if_nonfinite=True)
        optimizer.step()
        updates = group_updates(groups, before)
        frozen_base_check(model, frozen)
        realized["optimizer_steps"] += 1
        step = {"step": realized["optimizer_steps"], "rows": losses, "accumulation_rows": len(window),
                "gradient_norm_before_clip": float(norm), "groups": {key: {**gradients[key], **updates[key]} for key in groups},
                "frozen_base_unchanged": True, "memory": memory_measurement(), "step_seconds": time.perf_counter() - step_started}
        store.write(output / "steps" / f'{realized["optimizer_steps"]:04d}.json', step)
        print(json.dumps({"optimizer_step": realized["optimizer_steps"], "training_rows": realized["training_rows"], "scheduled_rows": len(order)}), flush=True)
        del before
    if any(realized[key] != manifest["counts"][key] for key in ("training_rows", "frames", "target_tokens_including_eos", "prompt_tokens")):
        raise ValueError("Realized one-pass rows/tokens/frames differ from the predeclared training manifest")
    optimizer.zero_grad(set_to_none=True)
    adapter_path = output / adapter_directory(provisional_diagnostic)
    model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False)
    adapter = {"weights": binding(adapter_path / "adapter_model.safetensors"), "config": binding(adapter_path / "adapter_config.json")}
    store.write(output / "adapter_bindings.json", adapter)
    store.write(adapter_path / "provenance.json", {"adapter": adapter})
    result = {**header, "schema": "completed-provisional-diagnostic-training-v1" if provisional_diagnostic is not None else "completed-detailed-diagnostic-training-v1", "status": "TRAINED",
              "adapter": adapter, "realized": realized, "training_scenes": manifest["counts"]["training_scenes"],
              "adapter_parameters": report["trainable_parameters"], "frozen_base_unchanged": True,
              "memory": memory_measurement(), "completed_at": datetime.now(timezone.utc).isoformat()}
    store.write(output / "training_result.json", result)
    return tag({"status": "TRAINED_NOT_EVALUATED", "realized": realized, "result": binding(output / "training_result.json")}, provisional_diagnostic)


def adapter_binding(training_run, protocol_path, student="onethinker", provisional_diagnostic=None):
    if training_run is None:
        return None
    path = Path(training_run).resolve() / "training_result.json"
    result = require_mode(load_json(path), provisional_diagnostic)
    schema = "completed-provisional-diagnostic-training-v1" if provisional_diagnostic is not None else "completed-detailed-diagnostic-training-v1"
    expected_parameters = training_parameters(student)
    if provisional_diagnostic is not None and result.get("protocol_version") is not None:
        from .ddp_config import validate_training_result
        from .provisional_data import load_protocol as load_provisional_protocol
        protocol = load_provisional_protocol(protocol_path, provisional_diagnostic, student=student)
        expected_parameters = validate_training_result(result, protocol, provisional_diagnostic)["trainable_parameters"]
    if result.get("schema") != schema or result.get("status") != "TRAINED" or result.get("protocol") != binding(protocol_path) or result.get("student", "onethinker") != student or result.get("adapter_parameters") != expected_parameters:
        raise ValueError("Adapter must come from the complete original-restart detailed diagnostic, never the infrastructure smoke")
    if provisional_diagnostic is None:
        verify_pin(result["training_manifest"])
    for pin in result["adapter"].values():
        verify_pin(pin)
    return {**result["adapter"], "training_result": binding(path)}


def generation_config(native_config, processor, budget):
    config = deepcopy(native_config)
    config.do_sample = False
    config.num_beams = 1
    config.num_return_sequences = 1
    config.max_new_tokens = budget
    config.temperature = None
    config.top_p = None
    config.top_k = None
    config.use_cache = True
    config.pad_token_id = processor.tokenizer.pad_token_id
    config.return_dict_in_generate = True
    config.output_scores = False
    config.output_logits = False
    config.validate()
    return config


def evaluate(manifest_path, protocol_path, output, lease_path, variant, training_run=None, retry_plan_path=None, student="onethinker", scratch_root=None, stage_frames=False, provisional_diagnostic=None):
    if provisional_diagnostic is not None and retry_plan_path is not None:
        raise ValueError("Provisional evaluation permits one heldout pass, not the fixed-cohort retry policy")
    lease_check, protocol_loader, manifest_loader = execution_contract(provisional_diagnostic, manifest_path, protocol_path, student, "evaluate", variant)
    lease_check(lease_path)
    protocol = protocol_loader(protocol_path, weights=True, student=student)
    manifest = manifest_loader(manifest_path)
    scope = provisional_flags(provisional_diagnostic)
    if provisional_diagnostic is not None:
        scope["PROVISIONAL_DIVISION_SHA"] = protocol["PROVISIONAL_DIVISION_SHA"]
    cohort_size = len(manifest["heldout_qids"]) if provisional_diagnostic is not None else 63
    if manifest["protocol"] != binding(protocol_path) or (variant == "adapter") != (training_run is not None):
        raise ValueError("Evaluation variant and frozen protocol/adapter identity disagree")
    adapter = adapter_binding(training_run, protocol_path, student, provisional_diagnostic)
    retry_plan = load_retry_plan(retry_plan_path, manifest_path, protocol_path, variant, adapter) if retry_plan_path else None
    qids = [item["qid"] for item in retry_plan["entries"]] if retry_plan else manifest["heldout_qids"]
    if not qids:
        raise ValueError("No recorded-cap wrong-answer reruns are required; do not allocate a GPU")
    budget = 32768 if retry_plan else 16384
    from .batches import load_processor
    from .runner import load_adapter, load_base, memory_measurement
    import torch
    from transformers import set_seed

    configuration = {"mode": "evaluate", "student": student, "variant": variant, "manifest": binding(manifest_path), **scope,
                     "protocol": binding(protocol_path), "adapter": adapter, "budget": budget,
                     "stage_frames": stage_frames, "scratch_root": str(scratch_root) if scratch_root else None}
    store = RunArtifacts(output, configuration, scratch_root)
    output = store.root
    configure_environment(output / "runtime")
    original_inputs = {row["qid"]: digest_json(row["student_input"]) for row in manifest["rows"]}
    local_rows = localize_frames(manifest["rows"], store, manifest_path, scratch_root, stage_frames)
    processor = load_processor(student)
    lease = admitted_device(lease_path, lease_check, provisional_diagnostic)
    set_seed(17)
    header = {"schema": "provisional-student-generation-run-v1" if provisional_diagnostic is not None else "fixed63-student-generation-run-v1", **FLAGS, "variant": variant, "student": student,
              "protocol": binding(protocol_path), "evaluation_manifest": binding(manifest_path),
              "base": protocol["base"], "base_sha256": protocol["base_sha256"], "adapter": adapter,
              "generation": GENERATION, "output_budget": budget, "attempt_qids": qids, "cohort_size": cohort_size,
              "original_run": retry_plan["original_run"] if retry_plan else None,
              "retry_plan": binding(retry_plan_path) if retry_plan_path else None,
              "versions": protocol["versions"], "runtime": protocol["runtime"] if provisional_diagnostic is not None else runtime_bindings(), "lease": lease,
              "device_name": torch.cuda.get_device_name(0), "attention_implementation": "sdpa",
              "base_dtype": "bfloat16", "answers_available_to_inference": False,
              "started_at": datetime.now(timezone.utc).isoformat()}
    header = store.record(header)
    store.write(output / "run.json", header)
    model = load_base(student)
    if adapter:
        model, reload_report = load_adapter(model, Path(adapter["config"]["path"]).parent)
        store.write(output / "adapter_reload.json", {**reload_report, "adapter": adapter})
    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    model.config.text_config.use_cache = True
    config = generation_config(model.generation_config, processor, budget)
    store.write(output / "effective_generation_config.json", config.to_dict())
    eos_ids = config.eos_token_id if isinstance(config.eos_token_id, list) else [config.eos_token_id]
    if not eos_ids or any(type(value) is not int for value in eos_ids):
        raise ValueError("The pinned model must have explicit native EOS token IDs")
    rows = {row["qid"]: row for row in local_rows}
    successes, failures = 0, 0
    for qid in qids:
        lease_check(lease_path, fresh=False)
        row = rows[qid]
        trace = {"qid": qid, "question_id": qid, "variant": variant, "budget": budget,
                 "run_sha256": digest_json(header), "input_sha256": original_inputs[qid],
                 "trace": {"messages": []}, "budget_terminal": False}
        batch = generated = cpu_batch = None
        try:
            if row["student_input"] is None:
                raise ValueError("Original_RGB_source_admission_failed")
            cpu_batch, audit = encode_prompt(processor, row)
            batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
            with torch.inference_mode():
                generated = model.generate(**batch, generation_config=config)
            tokens = generated.sequences[0, audit["prompt_tokens"]:].detach().cpu().tolist()
            finish = "STOP" if tokens and tokens[-1] in eos_ids else "MAX_TOKENS" if len(tokens) == budget else "UNEXPECTED_STOP"
            if finish == "UNEXPECTED_STOP":
                raise ValueError("Generation_ended_without_EOS_or_recorded_cap")
            text = processor.tokenizer.decode(tokens, skip_special_tokens=True)
            trace.update(status="ok", budget_terminal=finish == "MAX_TOKENS", input_audit=audit,
                         generation={"generated_token_ids": tokens, "generated_tokens": len(tokens),
                                     "raw_decoded_text": processor.tokenizer.decode(tokens, skip_special_tokens=False),
                                     "finish_reason": finish, "eos_token_ids": eos_ids,
                                     "effective_config": binding(output / "effective_generation_config.json")},
                         trace={"messages": [{"role": "ai", "content": text, "tool_calls": [],
                                               "provenance": "local_original_rgb_model_generation",
                                               "response_metadata": {"finish_reason": finish, "model_name": str(get_student(student)["snapshot"]), "variant": variant}}]})
            successes += 1
        except (ValueError, OSError, RuntimeError) as error:
            trace.update(status="error", error_type=type(error).__name__, source_media_failure=row.get("media_failure"),
                         missing_output_counts_as_failure=True)
            failures += 1
        store.write(output / "traces" / f"{qid}.json", trace)
        print(json.dumps({"qid": qid, "variant": variant, "budget": budget, "status": trace["status"], "attempted": successes + failures, "scheduled": len(qids)}), flush=True)
        del batch, generated, cpu_batch
        gc.collect()
        if trace["status"] == "error":
            torch.cuda.empty_cache()
    completion = {"schema": "provisional-generation-completion-v1" if provisional_diagnostic is not None else "fixed63-generation-completion-v1", "run": binding(output / "run.json"),
                  "attempted_qids": qids, "successful_outputs": successes, "failed_outputs": failures,
                  "cohort_size": cohort_size, "offline_scoring_performed": False, "memory": memory_measurement(),
                  "completed_at": datetime.now(timezone.utc).isoformat()}
    store.write(output / "completion.json", completion)
    return tag({"status": "INFERENCE_ATTEMPTS_RECORDED_NOT_SCORED", "successful_outputs": successes, "failed_outputs": failures,
                "completion": binding(output / "completion.json")}, provisional_diagnostic)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if any(value == "--provisional-diagnostic" or value.startswith("--provisional-diagnostic=") for value in arguments):
        from .provisional_cli import main as provisional_main
        return provisional_main(arguments)
    parser = argparse.ArgumentParser(description="Benchmark-trained diagnostic only; paid/GPU work requires supervisor admission")
    sub = parser.add_subparsers(dest="command", required=True)
    fixture = sub.add_parser("prepare-infrastructure-smoke")
    fixture.add_argument("--training-contexts", nargs=4, required=True)
    fixture.add_argument("--validation-contexts", nargs=2, required=True)
    fixture.add_argument("--output", required=True)
    fixture.add_argument("--scratch-root")
    protocol = sub.add_parser("prepare-protocol")
    protocol.add_argument("--output", required=True)
    protocol.add_argument("--student", choices=tuple(STUDENTS), default="onethinker")
    train_data = sub.add_parser("prepare-training")
    train_data.add_argument("--accepted", nargs=2, required=True)
    train_data.add_argument("--protocol", required=True)
    train_data.add_argument("--output", required=True)
    eval_data = sub.add_parser("prepare-heldout")
    eval_data.add_argument("--protocol", required=True)
    eval_data.add_argument("--output", required=True)
    cpu = sub.add_parser("cpu-check-heldout")
    cpu.add_argument("--manifest", required=True)
    cpu.add_argument("--output", required=True)
    for name in ("train", "evaluate"):
        item = sub.add_parser(name)
        item.add_argument("--manifest", required=True)
        item.add_argument("--protocol")
        item.add_argument("--infrastructure-smoke", action="store_true")
        item.add_argument("--output", required=True)
        item.add_argument("--lease", required=True)
        item.add_argument("--student", choices=tuple(STUDENTS), default="onethinker")
        item.add_argument("--scratch-root")
        item.add_argument("--stage-frames", action="store_true")
        if name == "evaluate":
            item.add_argument("--variant", choices=("original", "adapter"), required=True)
            item.add_argument("--training-run")
            item.add_argument("--retry-plan")
    publish = sub.add_parser("finalize")
    publish.add_argument("--training-run", required=True)
    publish.add_argument("--evaluation-run")
    publish.add_argument("--scratch-root", required=True)
    publish.add_argument("--publish-root", required=True)
    for item in (protocol, train_data, eval_data, cpu):
        item.add_argument("--scratch-root")
    score = sub.add_parser("score")
    score.add_argument("--original-run", required=True)
    score.add_argument("--retry-run")
    score.add_argument("--output", required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("--original-score", required=True)
    compare.add_argument("--adapter-score", required=True)
    compare.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command in ("train", "evaluate"):
        if not args.infrastructure_smoke and not args.protocol:
            parser.error("--protocol is required outside the isolated infrastructure smoke")
        if args.infrastructure_smoke and (args.protocol or getattr(args, "retry_plan", None)):
            parser.error("Infrastructure smoke cannot use a benchmark protocol or scoring retry plan")
    if args.command not in ("train", "evaluate", "finalize"):
        configure_environment()
    if args.command == "prepare-infrastructure-smoke":
        from .infrastructure_smoke import prepare_manifest
        result = prepare_manifest(args.training_contexts, args.validation_contexts, args.output, args.scratch_root)
    elif args.command == "prepare-protocol":
        result = prepare_protocol(args.output, args.student, args.scratch_root)
    elif args.command == "prepare-training":
        result = prepare_training(args.accepted, args.protocol, args.output, args.scratch_root)
    elif args.command == "prepare-heldout":
        result = prepare_heldout(args.protocol, args.output, args.scratch_root)
    elif args.command == "cpu-check-heldout":
        result = check_heldout_inputs(args.manifest, args.output, args.scratch_root)
    elif args.command in ("train", "evaluate") and args.infrastructure_smoke:
        from . import infrastructure_smoke
        if args.command == "train":
            result = infrastructure_smoke.train(args.manifest, args.output, args.lease, args.student, args.scratch_root, args.stage_frames)
        else:
            result = infrastructure_smoke.evaluate(args.manifest, args.output, args.lease, args.student, args.scratch_root, args.training_run, args.variant)
    elif args.command == "train":
        result = train(args.manifest, args.protocol, args.output, args.lease, args.student, args.scratch_root, args.stage_frames)
    elif args.command == "evaluate":
        result = evaluate(args.manifest, args.protocol, args.output, args.lease, args.variant, args.training_run, args.retry_plan, args.student, args.scratch_root, args.stage_frames)
    elif args.command == "finalize":
        result = finalize(args.training_run, args.publish_root, args.scratch_root, args.evaluation_run)
    elif args.command == "score":
        result = score_run(args.original_run, args.output, args.retry_run)
    else:
        result = compare_scores(args.original_score, args.adapter_score, args.output)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError, KeyError) as error:
        print(f"BLOCKED: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
