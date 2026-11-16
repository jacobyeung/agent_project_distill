"""Full fine-tuning (schema full-ft-v1): the student's own weights train instead of a LoRA adapter.

A `full_ft` block in the training config turns LoRA off. The block names which base groups train:

- llm: every language-model parameter (decoder layers, embed_tokens, the final norm and lm_head);
- vision_blocks: the vision tower's transformer blocks;
- merger: the vision tower's patch merger (and DeepStack mergers where the architecture has them).

The vision tower's patch and position embeddings never train. A block whose groups are all false is the
frozen-VLM alignment stage: no base parameter trains, the base stays BF16, and only the attached modules
(the geometry adapter and the auxiliary heads) train, exactly as the LoRA path trains its replicated adapters.

When any base group trains, every base parameter is stored in FP32 (master weights) and FSDP shards all of
them, trainable or not, with BF16 compute (MixedPrecision param_dtype bfloat16) and FP32 gradient reduction.
Casting a BF16 checkpoint to FP32 and back is exact, so the step-0 forward equals the BF16 base forward.
Attached modules (geometry adapter, heads) stay outside FSDP: replicated FP32, their gradients averaged
explicitly, as in the LoRA path.

AdamW keeps one parameter group per trained group, each with its own base learning rate on the shared
warmup-cosine schedule. Gradient clipping is per family: the base groups together over their global
(all-rank) norm, the geometry adapter alone, the heads alone.

Checkpoints are rank-sharded: every rank writes its own trainable local shards and their optimizer state
(shards/rank<r>.pt), hashed while written. The replicated attached modules (identical on every rank) and their
optimizer state are written once, by rank 0 (replicated.pt); resume loads them on rank 0 and broadcasts them. Resume
requires the same world size and sharding layout and is bit-exact. Publication exports the BF16 cast of every base tensor in the Hugging Face layout (full_weights/),
which the evaluator loads over the pinned base snapshot.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path

import torch
import torch.distributed as dist

SCHEMA = "full-ft-v1"
TRAIN_GROUPS = ("llm", "vision_blocks", "merger")
ATTACHED_GROUPS = ("geometry", "heads")
DEFAULT_TRAIN = {"llm": True, "vision_blocks": False, "merger": False}
# Cambrian-P: LLM 1e-5, vision 2e-6, heads 1e-4; the merger follows the LLM; the adapter follows the heads.
DEFAULT_LEARNING_RATES = {"llm": 1e-5, "vision_blocks": 2e-6, "merger": 1e-5, "geometry": 1e-4, "heads": 1e-4}
INIT_KINDS = ("base", "base_merged_init_adapter", "full_export")
# full_export: start from a full fine-tuning export (BF16 full_weights/ of a milestone or a publication), pinned by the
# SHA-256 of its full_weights.json manifest; the manifest pins every shard (read_export). Its heads load through
# init_modules.heads.
FIXED = {"master_dtype": "float32", "compute_dtype": "bfloat16", "reduce_dtype": "float32",
         "wrap": "decoder_layers_vision_blocks_embed_tokens_lm_head", "checkpoint": "rank_sharded_v2",
         "clip": "base_groups_global_norm_then_geometry_then_heads"}
KEYS = {"schema", "train", "learning_rates", "init", "init_modules", *FIXED}
INIT_MODULE_KEYS = {"geometry", "heads"}
HEX64 = set("0123456789abcdef")
EXPORT_DIRECTORY = "full_weights"
EXPORT_MANIFEST = "full_weights.json"
EXPORT_SCHEMA = "full-ft-export-v1"
EXPORT_SHARD_BYTES = 4 * 1024**3
SHARD_SCHEMA = "full-ft-rank-shard-v2"
REPLICATED_SCHEMA = "full-ft-replicated-v1"
REPLICATED_FILE = "replicated.pt"


def _rate(value, what):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 1:
        raise ValueError(f"{what} must be a finite learning rate in (0, 1)")
    return float(value)


def _pin(value, what):
    if (not isinstance(value, dict) or set(value) != {"path", "sha256"} or not isinstance(value["path"], str)
            or not value["path"] or not isinstance(value["sha256"], str) or len(value["sha256"]) != 64
            or set(value["sha256"]) - HEX64):
        raise ValueError(f"{what} must be {{path, sha256}} with a lowercase sha256")
    return {"path": value["path"], "sha256": value["sha256"]}


def normalize(value):
    """Canonical full_ft block, or refuse it. Absent keys take their defaults; unknown keys refuse."""
    if not isinstance(value, dict) or set(value) - KEYS or value.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(f"full_ft keys must be a subset of {sorted(KEYS)} with schema {SCHEMA}")
    for key, fixed in FIXED.items():
        if value.get(key, fixed) != fixed:
            raise ValueError(f"full_ft {key} is fixed at {fixed}")
    train = value.get("train", DEFAULT_TRAIN)
    if not isinstance(train, dict) or set(train) - set(TRAIN_GROUPS) or any(type(v) is not bool for v in train.values()):
        raise ValueError(f"full_ft train must map {TRAIN_GROUPS} to booleans")
    train = {group: train.get(group, False) for group in TRAIN_GROUPS}
    if (train["vision_blocks"] or train["merger"]) and not train["llm"]:
        raise ValueError("full_ft trains vision groups only together with the LLM")
    rates = value.get("learning_rates", {})
    if not isinstance(rates, dict) or set(rates) - set(DEFAULT_LEARNING_RATES):
        raise ValueError(f"full_ft learning_rates keys must be a subset of {sorted(DEFAULT_LEARNING_RATES)}")
    for group in TRAIN_GROUPS:
        if group in rates and not train[group]:
            raise ValueError(f"full_ft learning rate for {group}, which does not train")
    rates = {group: _rate(rates.get(group, DEFAULT_LEARNING_RATES[group]), f"full_ft learning rate {group}")
             for group in DEFAULT_LEARNING_RATES if group in ATTACHED_GROUPS or train[group]}
    init = value.get("init", {"kind": "base"})
    if not isinstance(init, dict) or init.get("kind") not in INIT_KINDS:
        raise ValueError(f"full_ft init must be {{'kind': one of {INIT_KINDS}}}")
    if init["kind"] == "full_export":
        if set(init) != {"kind", "path", "sha256"}:
            raise ValueError("full_ft init full_export is {kind, path, sha256} of a full_weights.json manifest")
        init = {"kind": "full_export", **_pin({"path": init["path"], "sha256": init["sha256"]}, "full_ft init full_export")}
    elif set(init) != {"kind"}:
        raise ValueError(f"full_ft init must be {{'kind': one of {INIT_KINDS}}}")
    if init["kind"] == "base_merged_init_adapter" and not train["llm"]:
        raise ValueError("A warm start needs trainable FP32 masters (the frozen-VLM stage starts from base)")
    result = {"schema": SCHEMA, "train": train, "learning_rates": rates, "init": dict(init), **FIXED}
    if "init_modules" in value:
        modules = value["init_modules"]
        if not isinstance(modules, dict) or not modules or set(modules) - INIT_MODULE_KEYS:
            raise ValueError(f"full_ft init_modules keys must be a nonempty subset of {sorted(INIT_MODULE_KEYS)}")
        result["init_modules"] = {key: _pin(modules[key], f"full_ft init_modules {key}") for key in sorted(modules)}
    return json.loads(json.dumps(result, sort_keys=True))


def frozen_vlm(block):
    return not any(block["train"].values())


def frozen_attached_parameters(block, camera, heads=None, geometry=None):
    """Keep frozen FP32 attachments outside FSDP and require their pinned initialization."""
    frozen = [p for p in heads.parameters() if not p.requires_grad] if heads is not None else []
    pins = (block or {}).get('init_modules', {})
    if frozen and 'heads' not in pins:
        raise ValueError('Frozen camera modules require pinned full_ft init_modules.heads')
    if 'geometry' in (camera or {}).get('freeze_modules', []):
        if geometry is None or 'geometry' not in pins:
            raise ValueError('Frozen geometry requires an attached projector and pinned full_ft init_modules.geometry')
        geometry.projector.requires_grad_(False)
        frozen.extend(geometry.projector.parameters())
    return frozen


# ---------------------------------------------------------------------------------------------- parameter groups

def group_of(name):
    """The full_ft group of one base parameter name (Qwen3-VL / Qwen3.5 layout), or 'vision_frozen'."""
    name = name.removeprefix("base_model.model.")
    if name.startswith("model.language_model.") or name.startswith("lm_head."):
        return "llm"
    if name.startswith("model.visual.blocks."):
        return "vision_blocks"
    if name.startswith("model.visual.merger.") or name.startswith("model.visual.deepstack_merger_list."):
        return "merger"
    if name.startswith("model.visual.patch_embed.") or name.startswith("model.visual.pos_embed."):
        return "vision_frozen"
    raise ValueError(f"Unexpected base parameter outside the full_ft groups: {name}")


def base_parameters(model):
    """(name, parameter) of the base model: everything except attached modules."""
    return [(name, parameter) for name, parameter in model.named_parameters()
            if not name.startswith(("geometry_input.", "auxiliary_heads."))]


def prepare_model(model, block):
    """Set trainability and master dtype per the block; returns (groups, report). Call before attaching modules."""
    if any(name.startswith(("geometry_input.", "auxiliary_heads.")) or ".lora_" in name
           for name, _ in model.named_parameters()):
        raise ValueError("full_ft prepares the plain base before any adapter or attached module")
    found = {group: [] for group in (*TRAIN_GROUPS, "vision_frozen")}
    for name, parameter in base_parameters(model):
        found[group_of(name)].append((name, parameter))
    if not found["llm"] or not found["vision_blocks"] or not found["merger"]:
        raise ValueError("full_ft needs the language model, vision blocks and merger")
    trains = not frozen_vlm(block)
    model.requires_grad_(False)
    for name, parameter in base_parameters(model):
        if trains:
            parameter.data = parameter.data.to(torch.float32)
        if block["train"].get(group_of(name), False):
            parameter.requires_grad_(True)
    groups = {group: list(found[group]) for group in TRAIN_GROUPS if block["train"][group]}
    counts = {group: sum(parameter.numel() for _, parameter in found[group]) for group in found}
    report = {"schema": SCHEMA, "lora": None, "mode": "frozen_vlm" if not trains else "full",
              "train": block["train"], "learning_rates": block["learning_rates"],
              "group_parameters": {group: counts[group] for group in groups},
              "trainable_parameters": sum(counts[group] for group in groups),
              "base_parameters": sum(counts.values()), "frozen_base_parameters": sum(counts[g] for g in found if g not in groups),
              "master_dtype": "float32" if trains else None, "base_dtype": "float32" if trains else "bfloat16",
              "compute_dtype": "bfloat16"}
    return groups, report


def merge_init_adapter(model, settings, protocol, protocol_path, resume_from=None, init_adapter=None):
    """Warm start 'base_merged_init_adapter': attach the frozen parent's LoRA, load it, merge in FP32, drop PEFT."""
    from .adapters import attach_ddp_adapters
    from .warmstart import initialize_adapters

    for parameter in model.parameters():
        parameter.data = parameter.data.to(torch.float32)
    lora_settings = {key: value for key, value in settings.items() if key != "full_ft"}
    peft_model, report = attach_ddp_adapters(model, lora_settings)
    report = initialize_adapters(peft_model, report, protocol, protocol_path, resume_from=None, init_adapter=init_adapter)
    if not report.get("initialization_applied"):
        raise ValueError("The merged warm start did not load its parent adapter")
    merged = peft_model.merge_and_unload(safe_merge=True)
    if any(".lora_" in name for name, _ in merged.named_parameters()):
        raise ValueError("LoRA tensors survived the merge")
    merged.requires_grad_(False)
    return merged, {"merged_init_adapter": report["initialization"], "merge_dtype": "float32",
                    "initialization_source": report.get("initialization_source")}


def init_base_matches(recorded, base_sha256, base=None, student=None):
    if recorded.get("base_sha256") == base_sha256:
        return True
    if student != "m8a9e" or base is None:
        return False
    from .common import digest_json
    from .students import STUDENTS, same_student

    if not same_student(recorded.get("student"), student) or digest_json(base) != base_sha256:
        return False
    from .warmstart import base_content

    original = STUDENTS["qwen35"]["snapshot"]
    parent = recorded.get("base")
    if (not isinstance(parent, dict) or digest_json(parent) != recorded.get("base_sha256")
            or base.get("revision") != original.name):
        return False
    try:
        return base_content(parent) == base_content(base)
    except (KeyError, TypeError, ValueError):
        return False


def load_init_export(model, block, base_sha256, resolve=None, *, base=None, student=None):
    """Warm start 'full_export': replace every base tensor of the loaded BF16 base with a pinned full fine-tuning export,
    exactly (load_export). prepare_model keeps a frozen VLM in BF16, or casts trainable masters to FP32
    (BF16 -> FP32 is exact). The export must name this run's base snapshot."""
    init = block["init"]
    if init["kind"] != "full_export":
        raise ValueError("load_init_export needs full_ft init kind full_export")
    resolve = resolve or (lambda path: Path(path))
    manifest_path = Path(resolve(init["path"]))
    if manifest_path.name != EXPORT_MANIFEST or sha256_file(manifest_path) != init["sha256"]:
        raise ValueError("The full_export init manifest differs from its pin")
    manifest = json.loads(manifest_path.read_text())
    if not init_base_matches(manifest.get("base", {}), base_sha256, base, student):
        raise ValueError("The full_export init was trained from another base snapshot")
    if any(parameter.dtype != torch.bfloat16 for _, parameter in base_parameters(model)):
        raise ValueError("The full_export init loads into the BF16 base before the FP32 master cast")
    evidence = load_export(model, manifest_path.parent)
    return {"kind": "full_export", "manifest_sha256": init["sha256"], "tensors": evidence["tensors"],
            "parameters": manifest["parameters"], "training": manifest.get("training")}


MILESTONE_SCHEMA = "full-ft-milestone-export-v1"


def read_milestone(directory):
    """Verify a milestone export (ddp_checkpoints.save_milestone_export: milestone_<step>/ with MILESTONE.json, full_weights/,
    auxiliary_heads.pt/.json and optionally geometry/) file by file against MILESTONE.json; returns (manifest, pins) with
    pins {"full_weights": {path, sha256} of full_weights.json, "heads": {path, sha256} of auxiliary_heads.pt or None}."""
    directory = Path(directory)
    manifest = json.loads((directory / "MILESTONE.json").read_text())
    if manifest.get("schema") != MILESTONE_SCHEMA or not isinstance(manifest.get("files"), dict):
        raise ValueError("Not a full fine-tuning milestone export")
    for name, pin in manifest["files"].items():
        path = directory / name
        if ".." in Path(name).parts or path.stat().st_size != pin["bytes"] or sha256_file(path) != pin["sha256"]:
            raise ValueError(f"Milestone file differs from MILESTONE.json: {name}")
    weights = f"{EXPORT_DIRECTORY}/{EXPORT_MANIFEST}"
    if weights not in manifest["files"]:
        raise ValueError("The milestone export has no full weights")
    read_export(directory / EXPORT_DIRECTORY)
    pins = {"full_weights": {"path": str((directory / weights).resolve()), "sha256": manifest["files"][weights]["sha256"]},
            "heads": ({"path": str((directory / "auxiliary_heads.pt").resolve()),
                       "sha256": manifest["files"]["auxiliary_heads.pt"]["sha256"]}
                      if "auxiliary_heads.pt" in manifest["files"] else None)}
    return manifest, pins


def load_init_modules(block, geometry=None, heads=None, resolve=None):
    """Load stage-1 geometry and head weights pinned in init_modules; exact names, shapes, dtypes and values."""
    from safetensors.torch import load as load_safetensors

    pins = block.get("init_modules", {})
    resolve = resolve or (lambda path: Path(path))
    loaded = {}
    for key, module in (("geometry", geometry), ("heads", heads)):
        if key not in pins:
            continue
        if module is None:
            raise ValueError(f"full_ft init_modules names {key}, which this run does not attach")
        payload = Path(resolve(pins[key]["path"])).read_bytes()
        if hashlib.sha256(payload).hexdigest() != pins[key]["sha256"]:
            raise ValueError(f"full_ft init module {key} differs from its pinned sha256")
        if key == "geometry":
            saved = load_safetensors(payload)
            target = module.projector
        else:
            saved = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
            target = module
        expected = target.state_dict()
        if set(saved) != set(expected) or any(tuple(saved[name].shape) != tuple(value.shape) or saved[name].dtype != value.dtype
                                              for name, value in expected.items()):
            raise ValueError(f"full_ft init module {key} tensors differ from the live module")
        target.load_state_dict({name: value.to(expected[name].device) for name, value in saved.items()}, strict=True)
        if any(not torch.equal(value.detach().cpu(), saved[name]) for name, value in target.state_dict().items()):
            raise ValueError(f"full_ft init module {key} did not reload exactly")
        loaded[key] = {"sha256": pins[key]["sha256"], "tensors": len(saved)}
    if set(pins) - set(loaded):
        raise ValueError("full_ft init_modules were not all loaded")
    return loaded


# ---------------------------------------------------------------------------------------------- FSDP

def wrap_full_model(model, replicated, process_group, device, mixed_precision=True, cpu_offload=False, frozen_base=False):
    """FSDP owns every base parameter (FP32 masters); attached modules stay replicated beside it."""
    from torch.distributed.fsdp import FullyShardedDataParallel as FSDP, MixedPrecision, ShardingStrategy, CPUOffload
    from torch.distributed.fsdp.wrap import CustomPolicy
    from .fsdp_training import BLOCK_NAMES

    replicated = list(replicated)
    replicated_ids = {id(parameter) for parameter in replicated}
    base = base_parameters(model)
    if any(id(parameter) in replicated_ids for _, parameter in base):
        raise ValueError("A base parameter cannot be replicated")
    if {id(p) for p in model.parameters()} != {id(p) for _, p in base} | replicated_ids:
        raise ValueError("Every parameter is either an FSDP base parameter or a replicated attached parameter")
    if frozen_base:
        if any(p.requires_grad or p.dtype not in (torch.float32, torch.bfloat16) for _, p in base):
            raise ValueError("Frozen-base FSDP requires frozen FP32/BF16 base tensors")
    elif any(parameter.dtype != torch.float32 for _, parameter in base):
        raise ValueError("Full fine-tuning keeps every base parameter as an FP32 master")
    embed, head = model.get_input_embeddings(), model.get_output_embeddings()
    blocks = [module for module in model.modules() if type(module).__name__ in BLOCK_NAMES]
    if not blocks or embed is None or head is None:
        raise ValueError("Full fine-tuning needs decoder layers, vision blocks, embed_tokens and lm_head")
    policy = CustomPolicy(lambda module: type(module).__name__ in BLOCK_NAMES or module is embed or module is head)
    for parameter in replicated:
        if parameter.device != device:
            parameter.data = parameter.data.to(device)
    precision = MixedPrecision(param_dtype=torch.bfloat16, reduce_dtype=torch.float32) if mixed_precision else None
    wrapped = FSDP(model, process_group=process_group, device_id=device, sharding_strategy=ShardingStrategy.FULL_SHARD,
                   use_orig_params=True, auto_wrap_policy=policy, ignored_states=replicated or None,
                   cpu_offload=CPUOffload(offload_params=True) if cpu_offload else None,
                   mixed_precision=precision, backward_prefetch=None, limit_all_gathers=True, sync_module_states=False)
    for parameter in replicated:
        dist.broadcast(parameter.data, src=0, group=process_group)
    return wrapped


def named_trainable(distributed):
    """(clean name, parameter) for every trainable parameter of the wrapped model, in module order."""
    result = []
    for name, parameter in distributed.named_parameters():
        if parameter.requires_grad:
            result.append((clean_name(name), parameter))
    return result


def named_buffers(distributed):
    result, seen = [], set()
    for prefix, module in distributed.named_modules():
        for name, value in module.named_buffers(recurse=False):
            if name not in module._non_persistent_buffers_set and id(value) not in seen:
                result.append((clean_name(f'{prefix}.{name}' if prefix else name), value))
                seen.add(id(value))
    return result


def clean_name(name):
    return name.replace("_fsdp_wrapped_module.", "").replace("_checkpoint_wrapped_module.", "")


def sharded_groups(distributed, block):
    """Trainable base parameters of the wrapped model by group: their local shards (use_orig_params views)."""
    groups = {group: [] for group in TRAIN_GROUPS if block["train"][group]}
    for name, parameter in named_trainable(distributed):
        if name.startswith(("geometry_input.", "auxiliary_heads.")):
            continue
        group = group_of(name)
        if group not in groups:
            raise ValueError(f"Trainable base parameter outside the trained groups: {name}")
        groups[group].append((name, parameter))
    return groups


def global_norm(parameters, process_group=None, sharded=True):
    """L2 norm of the gradients; local sums are all-reduced when the tensors are shards."""
    device = next((p.grad.device for p in parameters if p.grad is not None), torch.device("cpu"))
    total = torch.zeros((), dtype=torch.float64, device=device)
    for parameter in parameters:
        if parameter.grad is not None and parameter.grad.numel():
            total += parameter.grad.detach().double().square().sum()
    if sharded:
        # NCCL cannot reduce the CPU scalar produced by offloaded shards.
        wire = total.to(torch.device('cuda', torch.cuda.current_device())) if (
            total.device.type == 'cpu' and dist.get_backend(process_group) == 'nccl') else total
        dist.all_reduce(wire, group=process_group)
        total = wire.to(total.device)
    return total.sqrt()


def clip_sharded(parameters, max_norm, process_group=None):
    """torch.nn.utils.clip_grad_norm_ semantics over shards: one global norm, one coefficient for every shard."""
    parameters = list(parameters)
    norm = global_norm(parameters, process_group)
    if not torch.isfinite(norm):
        raise RuntimeError(f"The total norm of order 2.0 for gradients from {len(parameters)} shards is non-finite")
    coefficient = torch.clamp(max_norm / (norm + 1e-6), max=1.0)
    for parameter in parameters:
        if parameter.grad is not None and parameter.grad.numel():
            parameter.grad.detach().mul_(coefficient.to(parameter.grad.device, parameter.grad.dtype))
    return norm.float()


def group_report(groups, process_group=None, values=None):
    """Global per-group L2 norms of gradients (values None) or of value differences."""
    report = {}
    for group, parameters in groups.items():
        device = parameters[0][1].device if parameters else torch.device("cpu")
        total = torch.zeros((), dtype=torch.float64, device=device)
        count = torch.zeros((), dtype=torch.float64, device=device)
        for name, parameter in parameters:
            tensor = parameter.grad if values is None else parameter.detach() - values[name].to(parameter.device)
            if tensor is not None and tensor.numel():
                total += tensor.detach().double().square().sum()
                count += float(tensor.numel())
        dist.all_reduce(total, group=process_group)
        dist.all_reduce(count, group=process_group)
        report[group] = {"l2": float(total.sqrt()), "elements": int(count), "tensors": len(parameters)}
    return report


def build_optimizer(sharded, geometry_group, auxiliary_heads, block, settings):
    """AdamW with one group per trained family, each with its own base LR on the shared schedule (weight decay 0)."""
    rates = block["learning_rates"]
    groups = [{"params": [p for _, p in sharded[group]], "lr": rates[group], "base_lr": rates[group], "group_name": group}
              for group in TRAIN_GROUPS if group in sharded]
    if geometry_group.get("geometry"):
        groups.append({"params": [p for _, p in geometry_group["geometry"]], "lr": rates["geometry"],
                       "base_lr": rates["geometry"], "group_name": "geometry"})
    if auxiliary_heads is not None:
        heads = [p for p in auxiliary_heads.parameters() if p.requires_grad]
        if heads:
            groups.append({"params": heads, "lr": rates["heads"], "base_lr": rates["heads"], "group_name": "heads"})
    if not groups:
        raise ValueError("full_ft has nothing to train")
    return torch.optim.AdamW(groups, lr=groups[0]["lr"], weight_decay=settings["weight_decay"],
                             betas=tuple(settings["betas"]), foreach=False)


def scheduler_steps(block, epoch_steps, max_steps):
    """The frozen-export heads run completes its cosine schedule at the explicit step cap."""
    if frozen_vlm(block) and block["init"]["kind"] == "full_export" and max_steps is not None:
        return min(epoch_steps, max_steps)
    return epoch_steps


def check_gradient_flow(sharded, report, process_group=None):
    """Step 1: every trained base group has a finite nonzero global gradient covering all of its elements."""
    flow = group_report(sharded, process_group)
    for group, item in flow.items():
        if not math.isfinite(item["l2"]) or item["l2"] <= 0:
            raise ValueError(f"Nonfinite or zero {group} gradient norm: {item['l2']}")
        if item["elements"] != report["group_parameters"][group]:
            raise ValueError(f"{group} gradients cover {item['elements']} of {report['group_parameters'][group]} elements")
    return {group: {"gradient_l2": item["l2"], "gradient_elements": item["elements"], "gradient_tensors": item["tensors"]}
            for group, item in flow.items()}


def check_updates(updates, report):
    for group, item in updates.items():
        if not math.isfinite(item["l2"]) or item["l2"] <= 0 or item["elements"] != report["group_parameters"][group]:
            raise ValueError(f"Nonfinite, zero or partial {group} parameter update: {item}")


def clip_families(sharded, geometry_parameters, head_parameters, clip_norm, process_group=None):
    """Clip the base groups over their global norm, the geometry adapter alone, the heads alone; returns the norms."""
    norms = {}
    base = [parameter for group in sharded.values() for _, parameter in group]
    if base:
        norms["base"] = float(clip_sharded(base, clip_norm, process_group))
    if geometry_parameters:
        norms["geometry"] = float(torch.nn.utils.clip_grad_norm_(geometry_parameters, clip_norm, error_if_nonfinite=True))
    if head_parameters:
        norms["heads"] = float(torch.nn.utils.clip_grad_norm_(head_parameters, clip_norm, error_if_nonfinite=True))
    if not norms:
        raise ValueError("full_ft clipped no parameters")
    return norms


def shard_layout(named):
    """The local shard layout: names, local shapes and element counts in optimizer order."""
    return [[name, list(parameter.shape), int(parameter.numel()), str(parameter.dtype)] for name, parameter in named]


# ---------------------------------------------------------------------------------------------- checkpoints

class HashingWriter:
    """File-like writer that hashes the exact bytes it writes."""

    def __init__(self, handle):
        self.handle, self.digest, self.bytes = handle, hashlib.sha256(), 0

    def write(self, data):
        view = memoryview(data).cast("B")
        self.digest.update(view)
        self.bytes += len(view)
        return self.handle.write(view)

    def flush(self):
        self.handle.flush()


def is_replicated(name):
    """Attached modules (geometry adapter, heads) are replicated on every rank; base parameters are FSDP shards."""
    return name.startswith(("geometry_input.", "auxiliary_heads."))


def optimizer_indices(named, optimizer):
    """{name: index} of each trainable tensor in the optimizer state dict (param_groups order)."""
    names = {id(parameter): name for name, parameter in named}
    return {names[id(parameter)]: index for index, parameter in
            enumerate(parameter for group in optimizer.param_groups for parameter in group["params"])}


def _write_payload(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        writer = HashingWriter(handle)
        torch.save(payload, writer)
        handle.flush()
        os.fsync(handle.fileno())
    return {"sha256": writer.digest.hexdigest(), "bytes": writer.bytes}


def write_rank_shard(directory, rank, named, optimizer, layout_sha256, *, buffers=None):
    """Write this rank's local base shards and their optimizer state; rank 0 also writes the replicated attached
    modules and their optimizer state, once. Returns {"shard": pin, "replicated": pin (rank 0 with modules)}."""
    from .ddp_checkpoints import cpu_state
    indices = optimizer_indices(named, optimizer)
    packed = optimizer.state_dict()  # references to the live state; only this rank's entries are copied below
    sharded = [(name, parameter) for name, parameter in named if not is_replicated(name)]
    replicated = [(name, parameter) for name, parameter in named if is_replicated(name)]
    own = {indices[name] for name, _ in sharded}
    relative = f"shards/rank{rank:03d}.pt"
    payload = {"schema": SHARD_SCHEMA, "rank": rank, "layout_sha256": layout_sha256,
               "tensors": {name: parameter.detach().cpu().clone() for name, parameter in sharded},
               "optimizer": {"state": {index: cpu_state(value) for index, value in packed["state"].items() if index in own},
                             "param_groups": cpu_state(packed["param_groups"])}}
    if buffers is not None:
        payload["buffers"] = {name: value.detach().cpu().clone() for name, value in buffers}
    pins = {"shard": {"name": relative, **_write_payload(Path(directory) / relative, payload)}}
    del payload
    if rank == 0 and replicated:
        shared = {indices[name] for name, _ in replicated}
        payload = {"schema": REPLICATED_SCHEMA, "layout_sha256": layout_sha256,
                   "tensors": {name: parameter.detach().cpu().clone() for name, parameter in replicated},
                   "optimizer_state": {index: cpu_state(value) for index, value in packed["state"].items() if index in shared}}
        pins["replicated"] = {"name": REPLICATED_FILE, **_write_payload(Path(directory) / REPLICATED_FILE, payload)}
    return pins


def _verified_load(path, pin, what):
    payload = Path(path).read_bytes()
    if len(payload) != pin["bytes"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
        raise ValueError(f"{what} checkpoint file size or sha256 changed")
    return torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)


def _copy_exact(named, tensors, what):
    if list(tensors) != [name for name, _ in named]:
        raise ValueError(f"{what} tensor names or order differ from this run")
    with torch.no_grad():
        for name, parameter in named:
            value = tensors[name]
            if value.shape != parameter.shape or value.dtype != parameter.dtype:
                raise ValueError(f"Checkpoint tensor shape or dtype changed: {name}")
            parameter.copy_(value.to(parameter.device))


def _broadcast(tensor, process_group):
    """Use the selected group without moving AdamW's CPU counters permanently."""
    if not tensor.is_cuda and dist.get_backend(process_group) == 'nccl':
        # The default group can itself be NCCL. Its wire tensors must be CUDA,
        # even though non-capturable AdamW keeps its scalar step on the CPU.
        wire = tensor.to(torch.device('cuda', torch.cuda.current_device()))
        dist.broadcast(wire, src=0, group=process_group)
        tensor.copy_(wire.cpu())
    else:
        dist.broadcast(tensor, src=0, group=process_group)


def read_rank_shard(directory, rank, pins, named, optimizer, layout_sha256, process_group=None, *, buffers=None):
    """Verify and restore this rank's shard; rank 0 restores the replicated modules and their optimizer state, then
    broadcasts them to every rank. pins: the checkpoint's file pins by name."""
    directory = Path(directory)
    sharded = [(name, parameter) for name, parameter in named if not is_replicated(name)]
    replicated = [(name, parameter) for name, parameter in named if is_replicated(name)]
    # Every rank's local reads finish (or fail) before any rank enters a collective, so a refusal on one rank stops
    # all of them instead of leaving the others blocked in the broadcast.
    failure, layout, saved, state = None, [None], None, {}
    try:
        saved = _verified_load(directory / f"shards/rank{rank:03d}.pt", pins[f"shards/rank{rank:03d}.pt"], f"Rank {rank}")
        if saved.get("schema") != SHARD_SCHEMA or saved.get("rank") != rank or saved.get("layout_sha256") != layout_sha256:
            raise ValueError("Checkpoint shard schema, rank or sharding layout differs from this run")
        _copy_exact(sharded, saved["tensors"], "Checkpoint shard")
        if buffers is not None:
            if buffers and "buffers" not in saved:
                raise ValueError("Checkpoint omits persistent rank-local buffers")
            _copy_exact(buffers, saved.get("buffers", {}), "Checkpoint buffers")
        indices = optimizer_indices(named, optimizer)
        if set(saved["optimizer"]["state"]) - {indices[name] for name, _ in sharded}:
            raise ValueError("A rank shard holds optimizer state outside its own tensors")
        state = dict(saved["optimizer"]["state"])
        if replicated and rank == 0:
            if REPLICATED_FILE not in pins:
                raise ValueError("The checkpoint lacks the replicated modules")
            shared = _verified_load(directory / REPLICATED_FILE, pins[REPLICATED_FILE], "Replicated")
            if shared.get("schema") != REPLICATED_SCHEMA or shared.get("layout_sha256") != layout_sha256:
                raise ValueError("Replicated checkpoint schema or sharding layout differs from this run")
            _copy_exact(replicated, shared["tensors"], "Replicated checkpoint")
            if set(shared["optimizer_state"]) - {indices[name] for name, _ in replicated}:
                raise ValueError("The replicated file holds optimizer state outside the replicated modules")
            state.update(shared["optimizer_state"])
            layout[0] = {index: {key: ("tensor", tuple(value.shape), value.dtype) if torch.is_tensor(value) else ("value", value)
                                 for key, value in entry.items()} for index, entry in shared["optimizer_state"].items()}
            del shared
    except Exception as error:
        failure = f"rank {rank}: {type(error).__name__}: {error}"
    failures = [None] * dist.get_world_size()
    dist.all_gather_object(failures, failure)
    if any(item is not None for item in failures):
        raise ValueError("Checkpoint restore refused: " + "; ".join(item for item in failures if item is not None))
    if replicated:
        dist.broadcast_object_list(layout, src=0)
        if rank != 0:
            # Placeholders of the right structure; rank 0's values arrive by broadcast below.
            state.update({index: {key: torch.zeros(spec[1], dtype=spec[2]) if spec[0] == "tensor" else spec[1]
                                  for key, spec in entry.items()} for index, entry in layout[0].items()})
    optimizer.load_state_dict({"state": state, "param_groups": saved["optimizer"]["param_groups"]})
    for _, parameter in replicated:
        _broadcast(parameter.data, process_group)
        entry = optimizer.state.get(parameter, {})
        for key in sorted(entry):
            if torch.is_tensor(entry[key]):
                _broadcast(entry[key], process_group)
    return len(saved["tensors"]) + len(replicated)


# ---------------------------------------------------------------------------------------------- export

def export_tensors(state, base_names):
    """BF16 cast of exactly the base tensors of a full state dict (rank 0's FULL_STATE_DICT)."""
    names = [name for name in state if clean_name(name) in base_names]
    if {clean_name(name) for name in names} != set(base_names):
        raise ValueError("The full state dict does not cover every base tensor exactly once")
    return {clean_name(name): state[name].detach().to("cpu", torch.bfloat16).contiguous() for name in names}


def save_export(tensors, directory, base_pin, report):
    """Write BF16 tensors in the Hugging Face sharded layout plus a manifest that pins every file."""
    from safetensors.torch import save_file

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    shards, current, size = [], {}, 0
    for name in sorted(tensors):
        tensor = tensors[name]
        nbytes = tensor.numel() * tensor.element_size()
        if current and size + nbytes > EXPORT_SHARD_BYTES:
            shards.append(current)
            current, size = {}, 0
        current[name] = tensor
        size += nbytes
    if current:
        shards.append(current)
    files, weight_map = [], {}
    for index, shard in enumerate(shards, 1):
        filename = f"model-{index:05d}-of-{len(shards):05d}.safetensors"
        save_file(shard, str(directory / filename), metadata={"format": "pt"})
        files.append({"name": filename, "sha256": sha256_file(directory / filename),
                      "bytes": (directory / filename).stat().st_size, "tensors": len(shard)})
        weight_map.update({name: filename for name in shard})
    index = {"metadata": {"total_size": sum(t.numel() * t.element_size() for t in tensors.values())},
             "weight_map": dict(sorted(weight_map.items()))}
    (directory / "model.safetensors.index.json").write_text(json.dumps(index, indent=1, sort_keys=True) + "\n")
    manifest = {"schema": EXPORT_SCHEMA, "dtype": "bfloat16", "cast": "fp32_master_to_bf16_round_nearest_even",
                "tensor_count": len(tensors), "parameters": sum(t.numel() for t in tensors.values()),
                "bytes": sum(item["bytes"] for item in files), "files": files,
                "index": {"name": "model.safetensors.index.json", "sha256": sha256_file(directory / "model.safetensors.index.json")},
                "base": base_pin, "training": report}
    (directory / EXPORT_MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def read_export(directory):
    """Verify a full-weights export against its manifest; returns (manifest, {name: path})."""
    directory = Path(directory)
    manifest = json.loads((directory / EXPORT_MANIFEST).read_text())
    if manifest.get("schema") != EXPORT_SCHEMA or manifest.get("dtype") != "bfloat16":
        raise ValueError("Unsupported full-weights export")
    index_pin = manifest["index"]
    if sha256_file(directory / index_pin["name"]) != index_pin["sha256"]:
        raise ValueError("Full-weights index differs from its manifest")
    for item in manifest["files"]:
        path = directory / item["name"]
        if Path(item["name"]).name != item["name"] or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"Full-weights file differs from its manifest: {item['name']}")
    index = json.loads((directory / index_pin["name"]).read_text())
    files = {item["name"] for item in manifest["files"]}
    if set(index["weight_map"].values()) != files or len(index["weight_map"]) != manifest["tensor_count"]:
        raise ValueError("Full-weights index and manifest disagree")
    return manifest, index["weight_map"]


def load_export(model, directory):
    """Evaluator side: replace every base tensor of a loaded BF16 base with the export, exactly."""
    from safetensors.torch import load_file

    directory = Path(directory)
    manifest, weight_map = read_export(directory)
    live = dict(base_parameters(model))
    buffers = dict(model.named_buffers())
    if set(weight_map) != set(live):
        missing, extra = sorted(set(live) - set(weight_map))[:5], sorted(set(weight_map) - set(live))[:5]
        raise ValueError(f"Full-weights tensors differ from the model (missing {missing}, extra {extra})")
    loaded = 0
    for item in manifest["files"]:
        tensors = load_file(str(directory / item["name"]), device="cpu")
        expected = {name for name, shard in weight_map.items() if shard == item["name"]}
        if set(tensors) != expected:
            raise ValueError("Full-weights shard membership differs from index: " + item["name"])
        with torch.no_grad():
            for name, value in tensors.items():
                parameter = live[name]
                if value.shape != parameter.shape or value.dtype != torch.bfloat16 or parameter.dtype != torch.bfloat16:
                    raise ValueError(f"Full-weights tensor shape or dtype differs: {name}")
                parameter.copy_(value.to(parameter.device))
                if not torch.equal(parameter.detach().cpu(), value):
                    raise ValueError(f"Full-weights tensor did not load exactly: {name}")
                loaded += 1
    if loaded != len(live):
        raise ValueError("Full-weights load did not cover every base tensor")
    return {"full_weights_exact_equality": True, "tensors": loaded, "buffers_unchanged": len(buffers),
            "manifest_sha256": sha256_file(directory / EXPORT_MANIFEST)}
