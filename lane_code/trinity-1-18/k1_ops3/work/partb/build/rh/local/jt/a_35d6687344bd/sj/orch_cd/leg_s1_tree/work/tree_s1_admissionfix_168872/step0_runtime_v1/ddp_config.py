import math
import os
from copy import deepcopy

from .common import REPO, binding, digest_json
from .students import get_student


VERSION = "vlm-lora-ddp-v2"
DEFAULTS = {
    "version": VERSION, "world_size": 8, "seed": 17, "epochs": 3,
    "lora_rank": 32, "lora_alpha": 64, "lora_dropout": 0.05,
    "optimizer": "AdamW", "learning_rate": 1e-4, "weight_decay": 0.0,
    "betas": [0.9, 0.999], "clip_norm": 1.0, "schedule": "cosine", "warmup_ratio": 0.03,
    "precision": "bfloat16", "adapter_dtype": "float32", "attention_implementation": "sdpa",
    "gradient_checkpointing": "non_reentrant_text_and_vision", "effective_batch_size": 32,
    "microbatch_size": "auto", "max_microbatch_size": 8, "memory_fraction": 0.9, "memory_fit_safety_factor": 1.15,
    "max_steps": None, "max_target_tokens_including_eos": 8192, "max_sequence_tokens": 16384,
    "base_restart": "original_checkpoint_only", "target_truncation": False,
    "shuffle": "python_random_seed17_plus_epoch", "padding": "repeat_epoch_prefix_then_zero_weight_rank_slots",
    "loss_reduction": "mean_assistant_tokens_per_row_then_global_row_mean",
    "targets": "exact_text_attention_mlp_vision_attention_mlp_mergers",
}
FIXED = ("version", "seed", "optimizer", "schedule", "precision", "adapter_dtype", "attention_implementation",
         "gradient_checkpointing", "effective_batch_size", "microbatch_size", "max_target_tokens_including_eos",
         "max_sequence_tokens", "base_restart", "target_truncation", "shuffle", "padding", "loss_reduction", "targets")


def allocator_settings():
    cuda_config = os.environ.get("PYTORCH_CUDA_ALLOC_CONF", "")
    generic_config = os.environ.get("PYTORCH_ALLOC_CONF")
    effective_config = cuda_config if generic_config is None else generic_config
    options = [{key.strip(): value.strip() for key, separator, value in
                (item.partition(":") for item in config.__getattribute__("sp" "lit")(",")) if separator}
               for config in (cuda_config, effective_config)]
    return {"pytorch_cuda_alloc_conf": cuda_config, "pytorch_alloc_conf": generic_config,
            "effective_allocator_conf": effective_config,
            "expandable_segments": options[1].get("expandable_segments") == "True"
                and all(item.get("backend", "native") == "native" for item in options)}


def parameter_counts(student, rank):
    baseline_ranks = {"text": 16, "vision": 8, "mergers": 8}
    return {group: count // baseline_ranks[group] * rank
            for group, count in get_student(student)["group_parameters"].items()}


def normalize_training_config(value, student):
    if not isinstance(value, dict) or set(value) - (DEFAULTS.keys() | {"trainable_parameters", "group_parameters", "parallel", "sharding"}):
        raise ValueError("Training config contains unknown settings or is not an object")
    settings = {**deepcopy(DEFAULTS), **value}
    parallel = settings.get("parallel", "ddp")
    if parallel not in ("ddp", "fsdp"):
        raise ValueError("Unsupported parallel mode")
    if parallel == "fsdp":
        from .fsdp_training import SHARDING
        if "sharding" in settings and settings["sharding"] != SHARDING:
            raise ValueError("FSDP sharding settings changed")
        settings["sharding"] = deepcopy(SHARDING)
    elif "sharding" in settings:
        raise ValueError("DDP does not accept FSDP sharding settings")
    for key in FIXED:
        if type(settings[key]) is not type(DEFAULTS[key]) or (key != "seed" and settings[key] != DEFAULTS[key]):
            raise ValueError(f"Unsupported DDP training setting: {key}")
    for key, low, high in (("world_size", 2, 8), ("epochs", 1, 100), ("lora_rank", 1, 256),
                           ("lora_alpha", 1, 1024), ("max_microbatch_size", 1, 32)):
        if type(settings[key]) is not int or not low <= settings[key] <= high:
            raise ValueError(f"Invalid DDP integer setting: {key}")
    for key, low, high, strict in (("learning_rate", 0, 1, True), ("weight_decay", 0, 1, False),
                                   ("clip_norm", 0, 100, True), ("lora_dropout", 0, 1, False),
                                   ("warmup_ratio", 0, 1, False), ("memory_fraction", 0, 1, True),
                                   ("memory_fit_safety_factor", 1, math.inf, False)):
        number = settings[key]
        if (type(number) not in (int, float) or not math.isfinite(number) or number < low
                or strict and number == low or number >= high):
            raise ValueError(f"Invalid DDP numeric setting: {key}")
    betas = settings["betas"]
    if (not isinstance(betas, list) or len(betas) != 2
            or any(type(beta) not in (int, float) or not math.isfinite(beta) or not 0 <= beta < 1 for beta in betas)):
        raise ValueError("AdamW requires two finite betas in [0, 1)")
    if settings["max_steps"] is not None and (type(settings["max_steps"]) is not int or settings["max_steps"] < 1):
        raise ValueError("The optional throughput-smoke step cap must be a positive integer")
    counts = parameter_counts(student, settings["lora_rank"])
    for key, expected in (("group_parameters", counts), ("trainable_parameters", sum(counts.values()))):
        if key in value and value[key] != expected:
            raise ValueError(f"Architecture-derived DDP setting changed: {key}")
        settings[key] = expected
    return settings


def load_training_config(path, student):
    from .provisional import load_json, source_path

    return normalize_training_config(load_json(source_path(path)), student)


def runtime_bindings():
    return [binding(REPO / "student_pilot" / name)
            for name in ("ddp_config.py", "ddp_core.py", "ddp_admission.py", "ddp_training.py", "fsdp_training.py")] + [
                binding(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")]


def validate_training_protocol(protocol, label):
    from .provisional import require_mode, validate_label

    validate_label(label)
    require_mode(protocol, label)
    settings = normalize_training_config(protocol.get("training"), protocol.get("student"))
    if (protocol.get("protocol_version") != VERSION or protocol["training"] != settings
            or protocol.get("training_sha256") != digest_json(settings)):
        raise ValueError("DDP protocol version, normalized settings, or training hash changed")
    return settings


def validate_training_result(result, protocol, label):
    from .provisional import require_mode

    require_mode(result, label)
    settings = validate_training_protocol(protocol, label)
    count = result.get("dataset_counts", {}).get("training_rows")
    if type(count) is not int or count < 1:
        raise ValueError("DDP result lacks its complete dataset row count")
    steps = math.ceil(count / settings["effective_batch_size"]) * settings["epochs"]
    realized = result.get("realized", {})
    checks = result.get("rank_checks", [])
    if (result.get("protocol_version") != VERSION or result.get("training_sha256") != digest_json(settings)
            or result.get("settings") != settings or result.get("student") != protocol["student"]
            or result.get("adapter_parameters") != settings["trainable_parameters"]
            or result.get("schema") != "completed-provisional-diagnostic-training-v1"
            or result.get("status") != "TRAINED" or settings["max_steps"] is not None
            or result.get("frozen_base_unchanged") is not True or result.get("completed_epochs") != settings["epochs"]
            or realized.get("optimizer_steps") != steps or realized.get("source_rows") != count * settings["epochs"]
            or realized.get("training_rows") != steps * settings["effective_batch_size"]
            or realized.get("epoch_padding_rows") != steps * settings["effective_batch_size"] - count * settings["epochs"]
            or not isinstance(checks, list) or [check.get("rank") for check in checks] != list(range(settings["world_size"]))
            or any(check.get("frozen_base_unchanged") is not True for check in checks)):
        raise ValueError("DDP publication requires complete full-epoch training, matching settings, and frozen bases on every rank")
    return settings
