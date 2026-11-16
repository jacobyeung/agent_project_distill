import gc
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import torch
from peft import PeftModel, get_peft_model_state_dict
from transformers import set_seed

from .adapters import attach_adapters, trainable_groups
from .batches import assistant_loss, encode_row, load_processor, prediction_positions
from .common import MODEL, MODEL_REVISION, binding, write_once
from .students import model_class, validate_snapshot


def load_base(student="onethinker", device="cuda:0"):
    model = model_class(student).from_pretrained(
        validate_snapshot(student), local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16,
        device_map={"": device}, attn_implementation="sdpa",
    )
    model.config.use_cache = False
    model.config.text_config.use_cache = False
    model.requires_grad_(False)
    return model


def load_adapter(model, adapter_path):
    from safetensors.torch import load_file

    adapter_dir = Path(adapter_path)
    vision_path = adapter_dir / "vision_blocks.safetensors"
    vision_report = {}
    if vision_path.is_file():
        from .adapters import load_vision_blocks
        vision_report = load_vision_blocks(model, vision_path)
    saved = load_file(str(adapter_dir / "adapter_model.safetensors"), device="cpu")
    model = PeftModel.from_pretrained(model, adapter_path, is_trainable=False, local_files_only=True,
                                     autocast_adapter_dtype=any(value.dtype == torch.float32 for value in saved.values()))
    restored = get_peft_model_state_dict(model)
    if set(restored) != set(saved) or any(value.dtype != saved[name].dtype or not torch.equal(value.detach().cpu(), saved[name])
                                        for name, value in restored.items()):
        raise ValueError("Reloaded PEFT tensors or dtypes differ from the saved adapter")
    return model, {"exact_tensor_equality": True, "exact_dtype_equality": True, "tensor_count": len(saved), **vision_report}


def supervised_logits(model, batch, positions, return_auxiliary=False):
    """Project only supervised hidden states while preserving PEFT/DDP forward hooks."""
    targets = batch["labels"][:, positions + 1]
    rows, columns = torch.where(targets != -100)
    unwrapped = model.module if isinstance(model, torch.nn.parallel.DistributedDataParallel) else model
    head = unwrapped.get_output_embeddings()
    if getattr(unwrapped, 'auxiliary_heads', None) is not None and not return_auxiliary and unwrapped.training:
        raise ValueError('Enabled auxiliary heads require targets on the training loss path')
    # Geometry features reach the vision tower's merged tokens through the attached module, never as a model input.
    geometry = getattr(unwrapped, "geometry_input", None)
    features = batch.get("geometry_features")
    if geometry is None and features is not None:
        raise ValueError("Geometry features supplied to a model without a geometry input")
    if geometry is not None and features is None:
        raise ValueError("A model with a geometry input requires geometry features for every batch")

    def select_hidden_states(module, args):
        hidden = args[0]
        if hidden.shape[:2] != targets.shape:
            raise ValueError("LM head hidden states do not align with selected causal positions")
        return (hidden[rows, columns], *args[1:])

    # Native Qwen forwards select the sequence positions before calling this head.
    # Pack the remaining batch dimension so mixed rows never project masked tokens.
    auxiliary_handle, auxiliary = None, []
    if return_auxiliary:
        from .auxiliary_losses import capture
        auxiliary_handle, auxiliary = capture(model, batch)
    handle = head.register_forward_pre_hook(select_hidden_states, prepend=True)
    try:
        if geometry is not None:
            calls = geometry.calls
            geometry.provide(features.to(next(geometry.parameters()).device))
        output = model(**{key: value for key, value in batch.items()
                          if key not in ("labels", "geometry_features") and not key.startswith("aux_")},
                       logits_to_keep=positions, use_cache=False, output_hidden_states=False, return_dict=True)
        if geometry is not None and (geometry.calls != calls + 1 or geometry._pending is not None):
            raise ValueError("Geometry features must be consumed by exactly one vision forward")
    finally:
        handle.remove()
        if auxiliary_handle is not None:
            auxiliary_handle.remove()
        if geometry is not None:
            geometry.clear()
    if output.logits.ndim != 2 or output.logits.shape[0] != rows.numel():
        raise ValueError("LM head must return exactly one logit vector per supervised token")
    if return_auxiliary:
        if len(auxiliary) != 1:
            raise ValueError('Auxiliary heads must execute exactly once per training forward')
        return output.logits, auxiliary[0]
    return output.logits


def forward_loss(model, batch):
    labels = batch["labels"]
    positions = prediction_positions(labels)
    logits = supervised_logits(model, batch, positions).unsqueeze(0)
    return assistant_loss(logits, labels, positions), logits


def group_gradients(groups):
    report = {}
    for group, parameters in groups.items():
        gradients = [parameter.grad for _, parameter in parameters]
        if any(gradient is None for gradient in gradients):
            missing = [name for name, parameter in parameters if parameter.grad is None]
            raise ValueError(f"Missing gradients in {group}: {missing}")
        norm = torch.stack([gradient.detach().float().square().sum() for gradient in gradients]).sum().sqrt().item()
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError(f"Nonfinite or zero {group} gradient norm: {norm}")
        report[group] = {"gradient_l2": norm, "gradient_tensors": len(gradients)}
    return report


def adapter_snapshot(groups):
    return {name: parameter.detach().cpu().clone() for parameters in groups.values() for name, parameter in parameters}


def group_updates(groups, before):
    report = {}
    for group, parameters in groups.items():
        squared_norm, changed = 0.0, 0
        for name, parameter in parameters:
            difference = parameter.detach().cpu().float() - before[name].float()
            squared_norm += difference.double().square().sum().item()
            changed += int(torch.count_nonzero(difference).item() > 0)
        norm = math.sqrt(squared_norm)
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError(f"Nonfinite or zero {group} parameter update: {norm}")
        report[group] = {"update_l2": norm, "updated_tensors": changed, "adapter_tensors": len(parameters)}
    return report


def memory_measurement():
    torch.cuda.synchronize()
    return {
        "max_allocated_bytes": torch.cuda.max_memory_allocated(),
        "max_reserved_bytes": torch.cuda.max_memory_reserved(),
        "allocated_bytes": torch.cuda.memory_allocated(),
        "reserved_bytes": torch.cuda.memory_reserved(),
    }


def run_smoke(manifest_path, output_path, lease_path, learning_rate=1e-5):
    from .admission import load_admitted_manifest
    from .lease import require_lease

    lease = require_lease(lease_path)
    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("Learning rate must be finite and positive")
    manifest = load_admitted_manifest(manifest_path)
    output_path = Path(output_path).resolve()
    if not output_path.is_relative_to(Path("/data2")):
        raise ValueError("Run outputs must remain under /data2")
    output_path.mkdir(parents=True, exist_ok=False)
    processor = load_processor()
    prepared = [encode_row(processor, row) for row in manifest["rows"]]
    write_once(output_path / "input_audit.json", [audit for _, audit in prepared])
    lease = require_lease(lease_path)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError("Supervisor must expose exactly its leased CUDA device")
    if not torch.cuda.is_bf16_supported():
        raise ValueError("The pinned smoke requires BF16 support")
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    set_seed(17)
    header = {
        "schema": "student-rgb-two-step-smoke-v1",
        "infrastructure_only": True,
        "detailed_distillation": False,
        "benchmark_trained_diagnostic": True,
        "benchmark_improvement_claim": False,
        "future_clean_student_restarts_original_weights": True,
        "model_path": str(MODEL), "model_revision": MODEL_REVISION,
        "model_config": binding(MODEL / "config.json"),
        "checkpoint_index": binding(MODEL / "model.safetensors.index.json"),
        "output_directory": str(output_path),
        "manifest": binding(manifest_path), "lease": lease,
        "device_name": torch.cuda.get_device_name(0),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "seed": 17, "optimizer": "AdamW", "learning_rate": learning_rate,
        "weight_decay": 0.0, "microbatch_size": 1, "steps_required": 2,
        "attention_implementation": "sdpa", "base_dtype": "bfloat16",
    }
    write_once(output_path / "run.json", header)
    model, adapter_report = attach_adapters(load_base())
    write_once(output_path / "adapters.json", adapter_report)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    checkpointing = {name: module.gradient_checkpointing for name, module in model.named_modules() if hasattr(module, "gradient_checkpointing")}
    if not checkpointing or not all(checkpointing.values()) or not any("visual" in name for name in checkpointing):
        raise ValueError("Non-reentrant gradient checkpointing must cover text and vision")
    write_once(output_path / "gradient_checkpointing.json", checkpointing)
    groups = trainable_groups(model, adapter_report["targets"])
    trainable = [parameter for parameters in groups.values() for _, parameter in parameters]
    base_versions = {name: parameter._version for name, parameter in model.named_parameters() if not parameter.requires_grad}
    optimizer = torch.optim.AdamW(trainable, lr=learning_rate, weight_decay=0.0)
    if {id(p) for group in optimizer.param_groups for p in group["params"]} != {id(p) for p in model.parameters() if p.requires_grad}:
        raise ValueError("Optimizer parameter set differs from the adapter allowlist")
    steps = []
    model.train()
    for step in range(2):
        require_lease(lease_path, fresh=False)
        cpu_batch, audit = prepared[step % len(prepared)]
        batch = {key: value.to("cuda:0") for key, value in cpu_batch.items()}
        before = adapter_snapshot(groups)
        optimizer.zero_grad(set_to_none=True)
        loss, logits = forward_loss(model, batch)
        if not torch.isfinite(loss):
            raise ValueError(f"Nonfinite loss at step {step + 1}")
        loss.backward()
        gradients = group_gradients(groups)
        if any(parameter.grad is not None or parameter.requires_grad or parameter._version != base_versions[name]
               for name, parameter in model.named_parameters() if name in base_versions):
            raise ValueError("A frozen base parameter changed or received a gradient")
        torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0, error_if_nonfinite=True)
        optimizer.step()
        updates = group_updates(groups, before)
        if any(parameter._version != base_versions[name] for name, parameter in model.named_parameters() if name in base_versions):
            raise ValueError("Optimizer modified a frozen base parameter")
        record = {
            "step": step + 1, "qid": audit["qid"], "loss": loss.detach().item(),
            "groups": {group: {**gradients[group], **updates[group]} for group in groups},
            "frozen_base_versions_unchanged": True,
            "memory": memory_measurement(),
        }
        steps.append(record)
        write_once(output_path / f"step_{step + 1}.json", record)
        print(json.dumps(record, allow_nan=False), flush=True)
        del before, batch, loss, logits
    optimizer.zero_grad(set_to_none=True)
    model.eval()
    reference_batch = {key: value.to("cuda:0") for key, value in prepared[0][0].items()}
    with torch.no_grad():
        reference_loss, reference_logits = forward_loss(model, reference_batch)
    reference_loss = reference_loss.item()
    reference_logits = reference_logits.detach().cpu().clone()
    saved_state = {name: value.detach().cpu().clone() for name, value in get_peft_model_state_dict(model).items()}
    adapter_path = output_path / "adapter"
    model.save_pretrained(adapter_path, safe_serialization=True, save_embedding_layers=False)
    write_once(output_path / "adapter_bindings.json", {
        "weights": binding(adapter_path / "adapter_model.safetensors"),
        "config": binding(adapter_path / "adapter_config.json"),
    })
    del optimizer, trainable, groups, model, reference_batch
    gc.collect()
    torch.cuda.empty_cache()
    require_lease(lease_path, fresh=False)
    reloaded = PeftModel.from_pretrained(load_base(), adapter_path, is_trainable=False, local_files_only=True)
    reloaded.eval()
    restored = get_peft_model_state_dict(reloaded)
    if set(restored) != set(saved_state):
        raise ValueError("Reloaded adapter tensor names changed")
    for name, value in restored.items():
        if not torch.equal(value.detach().cpu(), saved_state[name]):
            raise ValueError(f"Adapter reload changed tensor: {name}")
    batch = {key: value.to("cuda:0") for key, value in prepared[0][0].items()}
    with torch.no_grad():
        restored_loss, restored_logits = forward_loss(reloaded, batch)
    restored_logits = restored_logits.detach().cpu()
    torch.testing.assert_close(restored_logits, reference_logits, rtol=1e-4, atol=1e-4)
    if not math.isclose(reference_loss, restored_loss.item(), rel_tol=1e-5, abs_tol=1e-5):
        raise ValueError("Adapter reload changed the fixed RGB example's loss")
    result = {
        **header, "status": "PASS", "steps": steps,
        "trainable_parameters": adapter_report["trainable_parameters"],
        "group_parameters": adapter_report["group_parameters"],
        "adapter_save_reload": {
            "tensor_equality": True, "tensor_count": len(saved_state),
            "reference_loss": reference_loss, "reloaded_loss": restored_loss.item(),
            "max_absolute_logit_difference": (restored_logits.float() - reference_logits.float()).abs().max().item(),
            "logit_rtol": 1e-4, "logit_atol": 1e-4,
        },
        "memory": memory_measurement(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    write_once(output_path / "smoke_result.json", result)
    print(json.dumps(result, allow_nan=False), flush=True)
    return result
