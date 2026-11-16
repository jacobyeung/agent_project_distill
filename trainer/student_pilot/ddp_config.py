import math
import os
from copy import deepcopy

from .common import REPO, binding, digest_json
from .students import get_student
from .trace_contract import ANSWER_FORMAT_INSTRUCTION


VERSION = "vlm-lora-ddp-v2"
SEGMENT_LOSS_REDUCTION = "segment_normalized_answer_plus_0p5_trace_then_global_row_mean"
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
LOSS_REDUCTION_OPTIONS = (DEFAULTS["loss_reduction"], SEGMENT_LOSS_REDUCTION)
FIXED = ("version", "optimizer", "schedule", "precision", "adapter_dtype", "attention_implementation",
         "gradient_checkpointing", "microbatch_size", "max_target_tokens_including_eos",
         "max_sequence_tokens", "base_restart", "target_truncation", "shuffle", "padding", "loss_reduction", "targets")
# Global batch options. 32 is the default and keeps its earlier rule (a world above 8 must divide it); a scaled-out batch
# must divide by the world size, so every rank receives the same number of rows and no layout padding is needed.
BATCH_OPTIONS = (32, 64, 128, 256)
# Every targets option attaches the same exact LoRA allowlist; an option names the groups whose LoRA
# keeps its warm-start parent values (requires_grad=False, outside the optimizer).
VISION_FROZEN_TARGETS = "exact_text_attention_mlp_mergers_vision_frozen"
TARGET_OPTIONS = {DEFAULTS["targets"]: (), VISION_FROZEN_TARGETS: ("vision",)}
RUN_CONTROL_DEFAULTS = {"checkpoint_every_steps": 25}
RUN_CONTROL_KEYS = frozenset(RUN_CONTROL_DEFAULTS) | {'checkpoint_milestones'}


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


def frozen_groups(settings):
    return TARGET_OPTIONS[settings["targets"]]


def require_frozen_parent(protocol):
    """Frozen LoRA groups keep parent values, so a frozen-target protocol must pin a warm-start parent."""
    if frozen_groups(protocol["training"]) and "init_adapter_identity" not in protocol:
        raise ValueError("Frozen-target LoRA training requires a warm-start parent adapter")


def normalize_training_config(value, student):
    if isinstance(value, dict) and "answer_format_instruction" in value:
        if value["answer_format_instruction"] != ANSWER_FORMAT_INSTRUCTION:
            raise ValueError("The fixed training answer-format instruction changed")
        value = {key: item for key, item in value.items() if key != "answer_format_instruction"}
    if isinstance(value, dict) and "init_adapter" in value:
        from .warmstart import normalize_request
        normalize_request(value["init_adapter"])
        value = {key: item for key, item in value.items() if key != "init_adapter"}
    auxiliary = None
    if isinstance(value, dict) and "auxiliary" in value:
        from .auxiliary_config import enabled as auxiliary_enabled, normalize as normalize_auxiliary
        normalized_auxiliary = normalize_auxiliary(value["auxiliary"])
        if auxiliary_enabled(normalized_auxiliary):
            auxiliary = normalized_auxiliary
        value = {key: item for key, item in value.items() if key != "auxiliary"}
    if isinstance(value, dict) and "camera" in value:
        from .camera_config import normalize as normalize_camera
        normalize_camera(value["camera"])
        value = {key: item for key, item in value.items() if key != "camera"}
    full = None
    if isinstance(value, dict) and "full_ft" in value:
        from .full_ft import normalize as normalize_full_ft
        full = normalize_full_ft(value["full_ft"])
        if any(key in value for key in ("unfreeze_vision_blocks", "vision_learning_rate", "head_learning_rate")):
            raise ValueError("full_ft sets its own vision and head learning rates; drop the LoRA-path keys")
        value = {key: item for key, item in value.items() if key != "full_ft"}
    frames = None
    if isinstance(value, dict) and "frames" in value:
        from .pose_samples import normalize_frames
        frames = normalize_frames(value["frames"])
        value = {key: item for key, item in value.items() if key != "frames"}
    headcall = None
    if isinstance(value, dict) and "headcall" in value:
        from headcall.rows import normalize as normalize_headcall
        headcall = normalize_headcall(value["headcall"])
        value = {key: item for key, item in value.items() if key != "headcall"}
    geometry = None
    if isinstance(value, dict) and "geometry" in value:
        from .geometry_input import normalize as normalize_geometry
        geometry = normalize_geometry(value["geometry"])
        value = {key: item for key, item in value.items() if key != "geometry"}
    if not isinstance(value, dict) or set(value) - (DEFAULTS.keys() | RUN_CONTROL_KEYS
                                                    | {"trainable_parameters", "group_parameters", "frozen_group_parameters",
                                                       "parallel", "sharding", "unfreeze_vision_blocks",
                                                       "vision_learning_rate", "head_learning_rate"}):
        raise ValueError("Training config contains unknown settings or is not an object")
    settings = {**deepcopy(DEFAULTS), **{key: item for key, item in value.items() if key not in RUN_CONTROL_KEYS}}
    unfreeze_vision = settings.pop("unfreeze_vision_blocks", None)
    vision_lr = settings.pop("vision_learning_rate", None)
    head_lr = settings.pop("head_learning_rate", None)
    if unfreeze_vision is not None and type(unfreeze_vision) is not bool:
        raise ValueError("unfreeze_vision_blocks must be a boolean")
    if vision_lr is not None:
        if not unfreeze_vision:
            raise ValueError("vision_learning_rate requires unfreeze_vision_blocks=True")
        if type(vision_lr) not in (int, float) or type(vision_lr) is bool:
            raise ValueError("vision_learning_rate must be a finite positive number")
        vision_lr = float(vision_lr)
        if not math.isfinite(vision_lr) or not 0 < vision_lr < 1:
            raise ValueError("vision_learning_rate must be finite and in (0, 1)")
    if head_lr is not None:
        if type(head_lr) not in (int, float) or type(head_lr) is bool:
            raise ValueError("head_learning_rate must be a finite positive number")
        head_lr = float(head_lr)
        if not math.isfinite(head_lr) or not 0 < head_lr < 1:
            raise ValueError("head_learning_rate must be finite and in (0, 1)")
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
        if key == "targets" and type(settings[key]) is str and settings[key] in TARGET_OPTIONS:
            continue
        if key == "loss_reduction" and type(settings[key]) is str and settings[key] in LOSS_REDUCTION_OPTIONS:
            continue
        if type(settings[key]) is not type(DEFAULTS[key]) or settings[key] != DEFAULTS[key]:
            raise ValueError(f"Unsupported DDP training setting: {key}")
    for key, low, high in (("world_size", 2, 64), ("epochs", 1, 100), ("lora_rank", 1, 256),
                           ("lora_alpha", 1, 1024), ("max_microbatch_size", 1, 32), ("seed", 0, 2**31 - 1)):
        if type(settings[key]) is not int or not low <= settings[key] <= high:
            raise ValueError(f"Invalid DDP integer setting: {key}")
    batch = settings["effective_batch_size"]
    if type(batch) is not int or batch not in BATCH_OPTIONS:
        raise ValueError(f"Unsupported DDP training setting: effective_batch_size (options {BATCH_OPTIONS})")
    if batch != DEFAULTS["effective_batch_size"] and batch % settings["world_size"]:
        raise ValueError("A scaled-out effective batch must divide by the world size")
    if settings["world_size"] > 8 and batch % settings["world_size"]:
        raise ValueError("Multi-node world size must divide the effective batch without layout padding")
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
    frozen = frozen_groups(settings)
    if unfreeze_vision and "vision" in frozen:
        raise ValueError("Cannot both freeze vision LoRA and unfreeze vision blocks")
    trainable = {group: count for group, count in counts.items() if group not in frozen}
    derived = [("group_parameters", trainable), ("trainable_parameters", sum(trainable.values()))]
    if frozen:
        derived.append(("frozen_group_parameters", {group: counts[group] for group in frozen}))
    elif "frozen_group_parameters" in value:
        raise ValueError("Only a frozen-target DDP config records frozen_group_parameters")
    for key, expected in derived:
        if key in value and value[key] != expected:
            raise ValueError(f"Architecture-derived DDP setting changed: {key}")
        settings[key] = expected
    if unfreeze_vision is True:
        settings["unfreeze_vision_blocks"] = True
        settings["vision_learning_rate"] = 2e-6 if vision_lr is None else vision_lr
    if head_lr is not None:
        settings["head_learning_rate"] = head_lr
    if auxiliary is not None:
        settings["auxiliary"] = auxiliary
    if geometry is not None:
        settings["geometry"] = geometry
    if frames is not None:
        settings["frames"] = frames
    if full is not None:
        from .full_ft import frozen_vlm
        if frozen_groups(settings):
            raise ValueError("full_ft does not combine with a frozen-LoRA targets option")
        if not frozen_vlm(full) and settings.get("parallel", "ddp") != "fsdp":
            raise ValueError("Full fine-tuning shards its FP32 masters and requires parallel=fsdp")
        settings["full_ft"] = full
    if headcall is not None:
        if full is None or frozen_groups(settings):
            raise ValueError("The headcall block trains through full fine-tuning")
        settings["headcall"] = headcall
    return settings


def normalize_run_control(value):
    """Run control never shapes the weights, so it stays out of protocol["training"]."""
    if not isinstance(value, dict) or set(value) - RUN_CONTROL_KEYS:
        raise ValueError("Run control contains unknown settings or is not an object")
    run_control = {**deepcopy(RUN_CONTROL_DEFAULTS), **value}
    if type(run_control["checkpoint_every_steps"]) is not int or run_control["checkpoint_every_steps"] < 1:
        raise ValueError("checkpoint_every_steps must be a positive integer")
    if 'checkpoint_milestones' in run_control:
        steps = run_control['checkpoint_milestones']
        if (not isinstance(steps, list) or not steps or any(type(step) is not int or step < 1 for step in steps)
                or steps != sorted(set(steps))):
            raise ValueError('checkpoint_milestones must be increasing distinct positive steps')
    return run_control


def run_control_from_config(value):
    if not isinstance(value, dict):
        raise ValueError("Training config contains unknown settings or is not an object")
    return normalize_run_control({key: value[key] for key in RUN_CONTROL_KEYS if key in value})


def load_training_config(path, student):
    from .provisional import load_json, source_path

    return normalize_training_config(load_json(source_path(path)), student)


def load_run_control(path):
    from .provisional import load_json, source_path

    return run_control_from_config(load_json(source_path(path)))


def load_camera_config(path):
    """The enabled camera settings of a training config, or None (no camera block, or a disabled one)."""
    from .camera_config import from_training_config
    from .provisional import load_json, source_path

    return from_training_config(load_json(source_path(path)))


def camera_protocol_fields(value):
    """Camera supervision sits outside protocol["training"], so evaluators keep the training settings."""
    from .camera_config import from_training_config

    if not isinstance(value, dict):
        return {}
    camera = from_training_config(value)
    return {} if camera is None else {"camera": camera, "camera_sha256": digest_json(camera)}


def validate_camera_protocol(protocol):
    from .camera_config import enabled as camera_enabled, normalize as normalize_camera

    if "camera" not in protocol and "camera_sha256" not in protocol:
        return None
    camera = normalize_camera(protocol.get("camera"))
    if not camera_enabled(camera) or protocol.get("camera") != camera or protocol.get("camera_sha256") != digest_json(camera):
        raise ValueError("DDP camera supervision settings or hash changed")
    return camera


def runtime_bindings():
    return [binding(REPO / "student_pilot" / name)
            for name in ("trace_contract.py", "ddp_config.py", "ddp_core.py", "ddp_admission.py", "ddp_training.py",
                         "fsdp_training.py", "ddp_checkpoints.py", "probe_cache.py", "startup_receipt.py",
                         "auxiliary_config.py", "auxiliary_targets.py", "auxiliary_reason.py", "auxiliary_losses.py",
                         "camera_config.py", "camera_targets.py", "camera_head.py", "camera_gate.py",
                         "point_depth_head.py", "compact_label_bank.py", "adapters.py", "geometry_input.py",
                         "full_ft.py", "pose_samples.py")] + [
                binding(REPO / "headcall" / name)
                for name in ("__init__.py", "rows.py", "training.py", "protocol.py", "derive.py", "geometry.py", "heads.py",
                             "phase1.py")] + [
                binding(REPO / "scripts/diagnostic_ddp_gpu_batch.sh")]


def validate_run_control_protocol(protocol):
    """A protocol that records run control must record it normalized and hashed; silence means the defaults."""
    if "run_control" not in protocol:
        if "run_control_sha256" in protocol:
            raise ValueError("DDP run-control hash without its settings")
        return normalize_run_control({})
    run_control = normalize_run_control(protocol["run_control"])
    if protocol["run_control"] != run_control or protocol.get("run_control_sha256") != digest_json(run_control):
        raise ValueError("DDP run-control settings or their hash changed")
    return run_control


def validate_training_protocol(protocol, label):
    from .provisional import require_mode, validate_label

    validate_label(label)
    require_mode(protocol, label)
    settings = normalize_training_config(protocol.get("training"), protocol.get("student"))
    if (protocol.get("protocol_version") != VERSION or protocol["training"] != settings
            or protocol.get("training_sha256") != digest_json(settings)):
        raise ValueError("DDP protocol version, normalized settings, or training hash changed")
    require_frozen_parent(protocol)
    validate_run_control_protocol(protocol)
    validate_camera_protocol(protocol)
    return settings


def validate_training_result(result, protocol, label):
    from .provisional import require_mode

    require_mode(result, label)
    settings = validate_training_protocol(protocol, label)
    camera = validate_camera_protocol(protocol)
    if camera is not None and (result.get("camera") != camera or result.get("camera_sha256") != digest_json(camera)):
        raise ValueError("DDP publication requires the protocol's camera supervision settings and hash")
    if camera is None and ("camera" in result or "camera_sha256" in result):
        raise ValueError("DDP result records camera supervision not present in the protocol")
    if any(key in value for value in (protocol, result) for key in ("init_adapter_identity", "init_adapter_sha256")):
        from .warmstart import validate_result
        validate_result(result, protocol)
    run_control = validate_run_control_protocol(protocol)
    if result.get("run_control") != run_control or result.get("run_control_sha256") != digest_json(run_control):
        raise ValueError("DDP publication requires the protocol's run-control settings and hash")
    count = result.get("dataset_counts", {}).get("training_rows")
    if type(count) is not int or count < 1:
        raise ValueError("DDP result lacks its complete dataset row count")
    steps = math.ceil(count / settings["effective_batch_size"]) * settings["epochs"]
    realized = result.get("realized", {})
    checks = result.get("rank_checks", [])
    if (result.get("protocol_version") != VERSION or result.get("training_sha256") != digest_json(settings)
            or result.get("settings") != settings or result.get("student") != protocol["student"]
            or result.get("adapter_parameters") != (settings["trainable_parameters"] if "full_ft" not in settings
                                                    else result.get("full_ft", {}).get("trainable_parameters"))
            or result.get("schema") != "completed-provisional-diagnostic-training-v1"
            or result.get("status") != "TRAINED" or settings["max_steps"] is not None
            or result.get("frozen_base_unchanged") is not True or result.get("completed_epochs") != settings["epochs"]
            or realized.get("optimizer_steps") != steps or realized.get("source_rows") != count * settings["epochs"]
            or realized.get("training_rows") != steps * settings["effective_batch_size"]
            or realized.get("epoch_padding_rows") != steps * settings["effective_batch_size"] - count * settings["epochs"]
            or not isinstance(checks, list) or [check.get("rank") for check in checks] != list(range(settings["world_size"]))
            or any(check.get("frozen_base_unchanged") is not True for check in checks)):
        raise ValueError("DDP publication requires complete full-epoch training, matching settings, and frozen bases on every rank")
    if result.get("frozen_adapter_parameters") != settings.get("frozen_group_parameters"):
        raise ValueError("DDP publication must record exactly the frozen LoRA parameters of its targets option")
    if ("geometry" in settings) != (result.get("geometry") is not None):
        raise ValueError("A geometry-input run must publish its projector, and no other run may")
    if "full_ft" in settings:
        from .full_ft import frozen_vlm
        full = result.get("full_ft")
        adapter = result.get("adapter", {})
        if (not isinstance(full, dict) or full.get("train") != settings["full_ft"]["train"]
                or full.get("learning_rates") != settings["full_ft"]["learning_rates"]
                or (frozen_vlm(settings["full_ft"]) != (adapter == {"frozen_vlm": True}))
                or (not frozen_vlm(settings["full_ft"]) and "full_weights" not in adapter)
                or ("init_modules" in settings["full_ft"]) != ("init_modules" in full)):
            raise ValueError("A full fine-tuning run must publish its full weights (or its frozen-VLM modules) and settings")
    elif "full_ft" in result:
        raise ValueError("A LoRA run cannot record full fine-tuning")
    return settings
