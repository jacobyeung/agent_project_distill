"""Suffix-only LoRA for native Transformers 5.12.1 Qwen3.5 (including tiny fixtures).

Targets under model.language_model.layers.<i>: self_attn.{q,k,v,o}_proj;
linear_attn.{in_proj_qkv,in_proj_z,in_proj_b,in_proj_a,out_proj}.
All GDN input projections, including its two scalar gates, are adapted.

FP32 A/B tensors live in auxiliary_heads.mdg_lora, outside the LM FSDP units.
The existing use_orig_params=True wrapper ignores and broadcasts them alongside
the decoder heads; optimize_step averages their gradients and checkpoints them
in replicated.pt. Base names and the base full-weights export remain unchanged.
Forward hooks detach base tensor views only during a suffix call, after FSDP
unshards them. They preserve input gradients without accumulating base gradients
or changing any parameter's requires_grad flag. No hooks run during backward.
The suffix runs in eval mode, so activation checkpoint recomputation is disabled.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import math
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from .p3_provenance import file_pin, pinned


_MASK = ContextVar('mdg_suffix_mask', default=None)
ATTENTION = ('q_proj', 'k_proj', 'v_proj', 'o_proj')
GDN = ('in_proj_qkv', 'in_proj_z', 'in_proj_b', 'in_proj_a', 'out_proj')


def active_mask():
    return _MASK.get()


class Adapter(nn.Module):
    def __init__(self, inputs, outputs, rank, device):
        super().__init__()
        self.A = nn.Parameter(torch.empty(rank, inputs, dtype=torch.float32, device=device))
        self.B = nn.Parameter(torch.zeros(outputs, rank, dtype=torch.float32, device=device))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))

    def forward(self, x):
        with torch.autocast(device_type=x.device.type, enabled=False):
            return F.linear(F.linear(x.float(), self.A), self.B) * 2.


def _update(module, args, output):
    mask = _MASK.get()
    if mask is None:
        return output
    x = args[0]
    if x.shape[:-1] != mask.shape:
        raise ValueError('MDG adapter token mask differs from projection input')
    # Index before either projection: padding and inactive tokens never enter A/B.
    result = output.clone()
    result[mask] = output[mask] + module._mdg_adapter(x[mask]).to(output.dtype)
    return result


def _detach(module, args):
    if _MASK.get() is None:
        return
    saved = []
    # FSDP may install plain Tensor views in __dict__, rather than Parameters.
    for name in module._mdg_base_names:
        owner = module
        if '.' in name:
            parent, name = name.rsplit('.', 1)
            owner = module.get_submodule(parent)
        value = getattr(owner, name)
        if value is not None:
            # use_orig_params can retain the Parameter entry while shadowing it
            # with the active autograd view. Python reads __dict__ first.
            mapping = owner.__dict__ if name in owner.__dict__ else owner._parameters
            saved.append((mapping, name, value))
            mapping[name] = value.detach()
    module.__dict__['_mdg_saved_base'] = saved


def _restore(module, args, output):
    for mapping, name, value in module.__dict__.pop('_mdg_saved_base', ()):
        mapping[name] = value


def install(model, rank):
    if type(rank) is not int or rank < 0:
        raise ValueError('MDG LoRA rank must be a nonnegative integer')
    existing = getattr(model, 'mdg_lora_config', None)
    if existing is not None:
        if existing['rank'] != rank:
            raise ValueError('MDG LoRA rank differs from installed adapters')
        return
    if not rank:
        return
    adapters, targets = nn.ModuleDict(), []
    language = model.model.language_model
    for i, layer in enumerate(language.layers):
        family, names = ('self_attn', ATTENTION) if hasattr(layer, 'self_attn') else ('linear_attn', GDN)
        for name in names:
            module = getattr(getattr(layer, family), name)
            if not isinstance(module, nn.Linear):
                raise ValueError('MDG LoRA requires native linear projections')
            path = f'layers.{i}.{family}.{name}'
            key = path.replace('.', '__')
            adapters[key] = Adapter(module.in_features, module.out_features, rank, module.weight.device)
            # Avoid registering this reference under the base model a second time.
            module.__dict__['_mdg_adapter'] = adapters[key]
            module.register_forward_hook(_update)
            targets.append(path)
    for root in (language, model.lm_head):
        for module in root.modules():
            names = tuple(module._parameters)
            # Fused GDN kernels read conv weights directly, bypassing conv.forward.
            if type(module).__name__ == 'Qwen3_5GatedDeltaNet':
                names += ('conv1d.weight', 'conv1d.bias')
            if names:
                module.__dict__['_mdg_base_names'] = names
                module.register_forward_pre_hook(_detach)
                module.register_forward_hook(_restore, always_call=True)
    model.auxiliary_heads.mdg_lora = adapters
    model.mdg_lora_config = dict(rank=rank, alpha=2*rank, dropout=0., targets=targets,
                                 gate='mdg_suffix_tokens_v1', placement='replicated_fp32_heads')


@contextmanager
def suffix_mask(model, mask):
    if not hasattr(model, 'mdg_lora_config'):
        yield
        return
    if mask.dtype != torch.bool:
        raise ValueError('MDG suffix gate requires a boolean token mask')
    token = _MASK.set(mask if bool(mask.any()) else None)
    try:
        yield
    finally:
        _MASK.reset(token)


def export(directory, model, state):
    if not hasattr(model, 'mdg_lora_config'):
        return {}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'lora.pt').open('xb') as handle:
        torch.save({k.removeprefix('auxiliary_heads.mdg_lora.'): v.detach().float().cpu()
                    for k, v in state.items() if k.startswith('auxiliary_heads.mdg_lora.')}, handle)
    return dict(lora_config=model.mdg_lora_config, lora_weights=file_pin(directory/'lora.pt'))


def artifact_weights(directory, meta):
    """Authenticate relocated optional weights before admitting an artifact."""
    directory = Path(directory)
    config, weights = meta.get('lora_config'), meta.get('lora_weights')
    if config is None and weights is None:
        if (directory/'lora.pt').exists():
            raise ValueError('MDG LoRA weights require matching artifact metadata')
        return None
    if (not isinstance(config, dict) or not isinstance(weights, dict)
            or type(config.get('rank')) is not int or config['rank'] < 1
            or config.get('alpha') != 2*config['rank'] or config.get('dropout') != 0.
            or set(weights) != {'path', 'sha256'}):
        raise ValueError('Incomplete MDG LoRA artifact')
    return pinned(dict(path=str(directory/'lora.pt'), sha256=weights['sha256']))


def load(model, directory, meta):
    path = artifact_weights(directory, meta)
    if path is None:
        if hasattr(model, 'mdg_lora_config'):
            raise ValueError('MDG LoRA weights require matching artifact metadata')
        return
    config = meta['lora_config']
    install(model, config['rank'])
    if config.get('opener_tokens'):
        from .ground_tokens import install_rows
        install_rows(model, config['opener_tokens'])
    if model.mdg_lora_config != config:
        raise ValueError('MDG LoRA architecture differs from artifact')
    model.auxiliary_heads.mdg_lora.load_state_dict(torch.load(path, map_location='cpu', weights_only=True), strict=True)
