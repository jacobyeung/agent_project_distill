import torch

from .students import get_student, student_for_model

EXPECTED_COUNTS = get_student("onethinker")["group_parameters"]
RANKS = {"text": 16, "vision": 8, "mergers": 8}
ATTENTION = {
    "full_attention": ("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")),
    "linear_attention": ("linear_attn", ("in_proj_qkv", "in_proj_z", "in_proj_b", "in_proj_a", "out_proj")),
}


def discover_targets(model):
    config = model.config
    layer_types = getattr(config.text_config, "layer_types", None)
    if layer_types is None:
        layer_types = ["full_attention"] * config.text_config.num_hidden_layers
    if len(layer_types) != config.text_config.num_hidden_layers or set(layer_types) - ATTENTION.keys():
        raise ValueError("Unexpected student attention layer layout")
    targets = {
        "text": [
            f"model.language_model.layers.{i}.{part}.{name}"
            for i, layer_type in enumerate(layer_types)
            for part, names in (ATTENTION[layer_type], ("mlp", ("gate_proj", "up_proj", "down_proj")))
            for name in names
        ],
        "vision": [
            f"model.visual.blocks.{i}.{part}.{name}"
            for i in range(config.vision_config.depth)
            for part, names in (("attn", ("qkv", "proj")), ("mlp", ("linear_fc1", "linear_fc2")))
            for name in names
        ],
        "mergers": [
            f"model.visual.{merger}.{name}"
            for merger in ["merger"] + [f"deepstack_merger_list.{i}" for i in range(len(config.vision_config.deepstack_visual_indexes))]
            for name in ("linear_fc1", "linear_fc2")
        ],
    }
    modules = dict(model.named_modules())
    for names in targets.values():
        for name in names:
            if not isinstance(modules.get(name), torch.nn.Linear):
                raise ValueError(f"Expected exact Linear module is missing: {name}")
    return targets


VISION_BLOCK_SUFFIXES = (
    "norm1.weight", "norm1.bias", "norm2.weight", "norm2.bias",
    "attn.qkv.weight", "attn.qkv.bias", "attn.proj.weight", "attn.proj.bias",
    "mlp.linear_fc1.weight", "mlp.linear_fc1.bias", "mlp.linear_fc2.weight", "mlp.linear_fc2.bias",
)


def canonical_vision_block_name(name):
    return name.removeprefix("base_model.model.").replace(".base_layer.", ".")


def discover_vision_block_parameters(model):
    depth = model.config.vision_config.depth
    expected = {f"model.visual.blocks.{i}.{suffix}" for i in range(depth) for suffix in VISION_BLOCK_SUFFIXES}
    found = []
    seen = set()
    for name, parameter in model.named_parameters():
        if ".lora_" in name:
            continue
        canonical = canonical_vision_block_name(name)
        if canonical.startswith("model.visual.blocks."):
            if canonical not in expected or canonical in seen:
                raise ValueError(f"Unexpected or duplicate vision block parameter: {name}")
            seen.add(canonical)
            found.append((name, parameter))
    if seen != expected:
        raise ValueError(f"Missing expected vision block parameters: {len(seen)} != {len(expected)}")
    return found


VISION_MASTER_DTYPE = torch.float32
VISION_EXPORT_DTYPE = torch.bfloat16


def unfreeze_vision_blocks(model):
    """Make the vision blocks' base parameters trainable FP32 master weights; returns them.

    The forward still computes in BF16 under the trainer's autocast (each matmul casts the FP32
    weight), so step 0 is unchanged, while AdamW's 2e-6 updates accumulate in FP32 instead of
    rounding away against BF16's 8-bit mantissa. LayerNorm weights and biases are included."""
    found = discover_vision_block_parameters(model)
    for _, parameter in found:
        parameter.data = parameter.data.to(VISION_MASTER_DTYPE)
        parameter.requires_grad_(True)
    model._unfrozen_vision_blocks = True
    return found


def save_vision_blocks(model, path, state_dict=None, dtype=VISION_EXPORT_DTYPE):
    """Export the vision blocks for evaluators: the FP32 masters cast to the evaluator's BF16 base dtype."""
    from pathlib import Path
    from safetensors.torch import save_file

    tensors = {}
    for name, parameter in discover_vision_block_parameters(model):
        source = state_dict[name] if state_dict is not None and name in state_dict else parameter
        tensors[canonical_vision_block_name(name)] = source.detach().to(device='cpu', dtype=dtype).contiguous()
    save_file(tensors, str(Path(path)))
    return tensors


def load_vision_blocks(model, path):
    from pathlib import Path
    from safetensors.torch import load_file

    saved = load_file(str(Path(path)), device="cpu")
    vision_params = discover_vision_block_parameters(model)
    by_canonical = {canonical_vision_block_name(name): parameter for name, parameter in vision_params}
    if set(saved) != set(by_canonical):
        raise ValueError("Saved vision_blocks.safetensors tensor names differ from model.visual.blocks")
    with torch.no_grad():
        for canonical, parameter in by_canonical.items():
            tensor = saved[canonical]
            if tensor.shape != parameter.shape or tensor.dtype != parameter.dtype:
                raise ValueError(f"Vision block shape or dtype mismatch for {canonical}")
            parameter.copy_(tensor.to(device=parameter.device, dtype=parameter.dtype))
            if not torch.equal(parameter.detach().cpu(), tensor):
                raise ValueError(f"Vision block parameter did not reload exactly: {canonical}")
    return {"vision_blocks_exact_equality": True, "vision_block_tensors": len(saved)}


def trainable_groups(model, targets):
    lookup = {name: group for group, names in targets.items() for name in names}
    groups = {group: [] for group in targets}
    unfrozen_vision = bool(getattr(model, "_unfrozen_vision_blocks", False))
    vision_lookup = {name for name, _ in discover_vision_block_parameters(model)} if unfrozen_vision else set()
    if unfrozen_vision:
        groups["vision_blocks"] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if unfrozen_vision and name in vision_lookup:
            groups["vision_blocks"].append((name, parameter))
            continue
        original = name.removeprefix("base_model.model.")
        module_name, separator, adapter_name = original.partition(".lora_")
        if not separator or module_name not in lookup or adapter_name not in ("A.default.weight", "B.default.weight"):
            raise ValueError(f"Unexpected trainable tensor: {name}")
        groups[lookup[module_name]].append((name, parameter))
    if any(len(groups[group]) != 2 * len(names) for group, names in targets.items()):
        raise ValueError("Each declared module must have exactly two trainable LoRA tensors")
    if unfrozen_vision and len(groups["vision_blocks"]) != len(vision_lookup):
        raise ValueError("Each declared vision block must have all base parameters trainable when unfrozen")
    return groups


def trainable_targets(report):
    """The declared targets whose LoRA trains; a frozen group keeps its warm-start parent values."""
    frozen = report.get("frozen_group_parameters", {})
    return {group: names for group, names in report["targets"].items() if group not in frozen}


def frozen_adapters(model, report):
    """Exactly two frozen FP32 LoRA tensors per module of each frozen group, recorded in the report."""
    frozen = report.get("frozen_group_parameters", {})
    lookup = {name: group for group in frozen for name in report["targets"][group]}
    counts = {group: 0 for group in frozen}
    result = []
    for name, parameter in model.named_parameters():
        module_name, separator, adapter_name = name.removeprefix("base_model.model.").partition(".lora_")
        if separator and module_name in lookup:
            if (parameter.requires_grad or parameter.dtype != torch.float32
                    or adapter_name not in ("A.default.weight", "B.default.weight")):
                raise ValueError(f"Unexpected frozen LoRA tensor: {name}")
            counts[lookup[module_name]] += parameter.numel()
            result.append((name, parameter))
    if len(result) != 2 * len(lookup) or counts != frozen:
        raise ValueError("Each frozen module must keep exactly two frozen LoRA tensors")
    return result


def attach_adapters(model):
    from peft import LoraConfig, TaskType, get_peft_model

    model.requires_grad_(False)
    targets = discover_targets(model)
    modules = dict(model.named_modules())
    counts = {
        group: sum(RANKS[group] * (modules[name].in_features + modules[name].out_features) for name in names)
        for group, names in targets.items()
    }
    student = student_for_model(model)
    expected = get_student(student)
    if counts != expected["group_parameters"] or {group: len(names) for group, names in targets.items()} != expected["target_counts"]:
        raise ValueError(f"Architecture-discovered adapter counts differ for {student}: {counts}")
    visual_names = targets["vision"] + targets["mergers"]
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        target_modules=[name for names in targets.values() for name in names],
        rank_pattern={name: 8 for name in visual_names},
        alpha_pattern={name: 16 for name in visual_names},
        init_lora_weights=True,
        base_model_name_or_path=str(model.name_or_path),
    )
    model = get_peft_model(model, config)
    groups = trainable_groups(model, targets)
    actual = {group: sum(p.numel() for _, p in parameters) for group, parameters in groups.items()}
    if actual != counts:
        raise ValueError(f"PEFT attached incorrect ranks: {actual} != {counts}")
    attached = {name.removeprefix("base_model.model.") for name, module in model.named_modules() if hasattr(module, "lora_A")}
    if attached != set(name for names in targets.values() for name in names):
        raise ValueError("PEFT attached to a module outside the exact allowlist")
    return model, {
        "student": student,
        "targets": targets,
        "group_parameters": actual,
        "trainable_parameters": sum(actual.values()),
        "base_parameters_frozen": True,
        "lora_dropout": 0.0,
        "ranks": RANKS,
        "alphas": {"text": 32, "vision": 16, "mergers": 16},
    }


def attach_ddp_adapters(model, training):
    from peft import LoraConfig, TaskType, get_peft_model
    from .ddp_config import frozen_groups, normalize_training_config

    student = student_for_model(model)
    settings = normalize_training_config(training, student)
    frozen = frozen_groups(settings)
    model.requires_grad_(False)
    targets = discover_targets(model)
    modules = dict(model.named_modules())
    counts = {group: sum(settings["lora_rank"] * (modules[name].in_features + modules[name].out_features)
                         for name in names) for group, names in targets.items()}
    if (counts != {**settings["group_parameters"], **settings.get("frozen_group_parameters", {})}
            or {group: len(names) for group, names in targets.items()} != get_student(student)["target_counts"]):
        raise ValueError("Architecture-discovered DDP adapter counts changed")
    names = [name for group in targets.values() for name in group]
    config = LoraConfig(task_type=TaskType.CAUSAL_LM, r=settings["lora_rank"], lora_alpha=settings["lora_alpha"],
                        lora_dropout=settings["lora_dropout"], bias="none", target_modules=names,
                        init_lora_weights=True, base_model_name_or_path=str(model.name_or_path))
    model = get_peft_model(model, config, autocast_adapter_dtype=True)
    groups = trainable_groups(model, targets)
    actual = {group: sum(parameter.numel() for _, parameter in parameters) for group, parameters in groups.items()}
    attached = {name.removeprefix("base_model.model.") for name, module in model.named_modules() if hasattr(module, "lora_A")}
    if actual != counts or attached != set(names):
        raise ValueError("PEFT changed the exact DDP adapter ranks or allowlist")
    if any(parameter.dtype != torch.float32 for parameters in groups.values() for _, parameter in parameters):
        raise ValueError("DDP LoRA parameters and AdamW states must use FP32")
    for group in frozen:
        for _, parameter in groups[group]:
            parameter.requires_grad_(False)
    trainable = {group: count for group, count in actual.items() if group not in frozen}
    report = {"student": student, "protocol_version": settings["version"], "targets": targets,
              "group_parameters": trainable, "trainable_parameters": sum(trainable.values()),
              "base_parameters_frozen": True, "lora_dropout": settings["lora_dropout"],
              "ranks": {group: settings["lora_rank"] for group in targets},
              "alphas": {group: settings["lora_alpha"] for group in targets}, "adapter_dtype": "float32"}
    if frozen:
        report["frozen_group_parameters"] = {group: actual[group] for group in frozen}
        trainable_groups(model, trainable_targets(report))
        frozen_adapters(model, report)
    if settings.get("unfreeze_vision_blocks"):
        vision_params = unfreeze_vision_blocks(model)
        trainable_groups(model, trainable_targets(report))
        report["unfreeze_vision_blocks"] = True
        report["vision_block_count"] = model.config.vision_config.depth
        report["vision_block_parameters"] = sum(parameter.numel() for _, parameter in vision_params)
        report["vision_learning_rate"] = settings["vision_learning_rate"]
        report["vision_master_dtype"] = "float32"
        report["vision_export_dtype"] = "bfloat16"
    return model, report
