import torch
from peft import LoraConfig, TaskType, get_peft_model

EXPECTED_COUNTS = {"text": 43_646_976, "vision": 3_849_984, "mergers": 573_440}
RANKS = {"text": 16, "vision": 8, "mergers": 8}


def discover_targets(model):
    config = model.config
    targets = {
        "text": [
            f"model.language_model.layers.{i}.{part}.{name}"
            for i in range(config.text_config.num_hidden_layers)
            for part, names in (("self_attn", ("q_proj", "k_proj", "v_proj", "o_proj")), ("mlp", ("gate_proj", "up_proj", "down_proj")))
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


def trainable_groups(model, targets):
    lookup = {name: group for group, names in targets.items() for name in names}
    groups = {group: [] for group in targets}
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        original = name.removeprefix("base_model.model.")
        module_name, separator, adapter_name = original.partition(".lora_")
        if not separator or module_name not in lookup or adapter_name not in ("A.default.weight", "B.default.weight"):
            raise ValueError(f"Unexpected trainable tensor: {name}")
        groups[lookup[module_name]].append((name, parameter))
    if any(len(groups[group]) != 2 * len(names) for group, names in targets.items()):
        raise ValueError("Each declared module must have exactly two trainable LoRA tensors")
    return groups


def attach_adapters(model):
    model.requires_grad_(False)
    targets = discover_targets(model)
    modules = dict(model.named_modules())
    counts = {
        group: sum(RANKS[group] * (modules[name].in_features + modules[name].out_features) for name in names)
        for group, names in targets.items()
    }
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"Architecture-discovered adapter counts differ: {counts}; expected {EXPECTED_COUNTS}")
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
        "targets": targets,
        "group_parameters": actual,
        "trainable_parameters": sum(actual.values()),
        "base_parameters_frozen": True,
        "lora_dropout": 0.0,
        "ranks": RANKS,
        "alphas": {"text": 32, "vision": 16, "mergers": 16},
    }
