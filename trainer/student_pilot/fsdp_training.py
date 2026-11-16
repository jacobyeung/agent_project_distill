"""Shard frozen weights while retaining the reviewed FP32 LoRA optimizer."""
import hashlib

import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP, FullStateDictConfig, MixedPrecision,
    ShardingStrategy, StateDictType,
)
from torch.distributed.fsdp.wrap import ModuleWrapPolicy


BLOCK_NAMES = frozenset({"Qwen3VLTextDecoderLayer", "Qwen3VLVisionBlock",
                         "Qwen3_5DecoderLayer", "Qwen3_5VisionBlock"})
SHARDING = {
    "strategy": "FULL_SHARD", "use_orig_params": True,
    "param_dtype": "bfloat16", "reduce_dtype": "bfloat16",
    "auto_wrap": sorted(BLOCK_NAMES), "backward_prefetch": None,
    "limit_all_gathers": True,
    "adapters": "replicated_float32_exact_allowlist",
    "adapter_gradient_reduction": "float32_sum_div_world_once_per_step",
    "publication": "full_state_dict_cpu_rank0_only",
}


def wrap_model(model, parameters, process_group, device, mixed_precision=True, frozen_adapters=()):
    """Exclude only the validated adapters; FSDP owns every frozen base parameter.

    Frozen FP32 LoRA tensors (a frozen-target run) stay replicated beside the trainable ones: FSDP
    cannot flatten them with their block's BF16 base weights, which require one dtype per flat parameter."""
    if {id(p) for p in parameters} != {id(p) for p in model.parameters() if p.requires_grad}:
        raise ValueError("FSDP requires the exact adapter allowlist")
    if any(p.requires_grad for p in frozen_adapters):
        raise ValueError("FSDP frozen adapters must not require gradients")
    ignored = [*parameters, *frozen_adapters] if frozen_adapters else parameters
    classes = {type(module) for module in model.modules()
               if type(module).__name__ in BLOCK_NAMES and any(not p.requires_grad for p in module.parameters())}
    if not classes:
        raise ValueError("FSDP requires supported decoder layers and vision blocks")
    for parameter in ignored:
        if parameter.device != device:
            parameter.data = parameter.data.to(device)
    wrapped = FSDP(model, process_group=process_group, device_id=device,
                   sharding_strategy=ShardingStrategy.FULL_SHARD, use_orig_params=True,
                   auto_wrap_policy=ModuleWrapPolicy(classes), ignored_states=ignored,
                   mixed_precision=MixedPrecision(param_dtype=torch.bfloat16, reduce_dtype=torch.bfloat16) if mixed_precision else None,
                   backward_prefetch=None, limit_all_gathers=True, sync_module_states=False)
    # All ranks load the same pinned base. Broadcast adapters explicitly because
    # ignored parameters do not participate in FSDP state synchronization.
    for parameter in ignored:
        dist.broadcast(parameter.data, src=0, group=process_group)
    return wrapped


def average_adapter_gradients(parameters, process_group):
    """Match DDP's mean reduction after accumulating the scaled row losses."""
    world = dist.get_world_size(process_group)
    for parameter in parameters:
        if parameter.grad is None:
            raise ValueError("An allowlisted FSDP adapter did not receive a gradient")
        dist.all_reduce(parameter.grad, group=process_group)
        parameter.grad.div_(world)


def frozen_shard_fingerprints(model):
    """Hash local shards, whose views may change without modifying their values."""
    result = {}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            continue
        if parameter.grad is not None:
            raise ValueError("A frozen FSDP base parameter received a gradient")
        raw = parameter.detach().cpu().contiguous().view(torch.uint8).numpy()
        result[name] = (tuple(parameter.shape), str(parameter.dtype), hashlib.sha256(raw.tobytes()).hexdigest())
    return result


def check_frozen_shards(model, before):
    if frozen_shard_fingerprints(model) != before:
        raise ValueError("A frozen FSDP base shard changed")


def publication_state(model):
    """Every rank participates; only rank zero receives the canonical full state."""
    with FSDP.state_dict_type(model, StateDictType.FULL_STATE_DICT,
                             FullStateDictConfig(offload_to_cpu=next(model.parameters()).device.type != "cpu",
                                                 rank0_only=True)):
        state = model.state_dict()
    if dist.get_rank(model.process_group) != 0:
        return {}
    for name, tensor in state.items():
        state[name] = tensor.cpu()
    return state
