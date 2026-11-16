"""Save, load and resume: trainable weights, optimizer, scheduler, RNG streams, step and config.

`trainable_only=True` (default) stores only parameters with requires_grad plus the head, cond and
injection modules' buffers, which keeps a 9B full fine-tune checkpoint as large as its trainable
set and a frozen or LoRA run small. Resume with the same config and the same base weights.
"""
import json
import random

import numpy as np
import torch


def rng_state():
    state = dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state())
    if torch.cuda.is_available():
        state['cuda'] = torch.cuda.get_rng_state_all()
    return state


def set_rng_state(state):
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'])
    if 'cuda' in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state['cuda'])


def _weights(policy, trainable_only):
    full = policy.state_dict()
    if not trainable_only:
        return full
    keep = {n for n, p in policy.named_parameters() if p.requires_grad}
    keep |= {n for n in full if not n.startswith('backbone.')}
    return {n: v for n, v in full.items() if n in keep}


def save_checkpoint(path, policy, optimizer=None, scheduler=None, step=0, extra=None, trainable_only=True):
    payload = dict(format='vla_heads_ckpt_v1', step=int(step), config=policy.cfg.to_dict(),
                   config_sha256=policy.cfg.sha256(), weights=_weights(policy, trainable_only),
                   trainable_only=trainable_only, rng=rng_state(), extra=extra or {})
    if optimizer is not None:
        payload['optimizer'] = optimizer.state_dict()
    if scheduler is not None:
        payload['scheduler'] = scheduler.state_dict()
    torch.save(payload, path)
    return path


def load_checkpoint(path, policy, optimizer=None, scheduler=None, restore_rng=True, map_location='cpu'):
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if payload.get('format') != 'vla_heads_ckpt_v1':
        raise ValueError('Not a vla_heads checkpoint')
    if payload['config_sha256'] != policy.cfg.sha256():
        diff = {k: (v, policy.cfg.to_dict().get(k)) for k, v in payload['config'].items()
                if policy.cfg.to_dict().get(k) != v}
        raise ValueError('Checkpoint config differs: ' + json.dumps(diff, default=str))
    missing, unexpected = policy.load_state_dict(payload['weights'], strict=False)
    if unexpected:
        raise ValueError(f'Unexpected checkpoint tensors: {unexpected[:5]}')
    if payload['trainable_only']:
        need = {n for n, p in policy.named_parameters() if p.requires_grad}
        lost = need & set(missing)
        if lost:
            raise ValueError(f'Checkpoint lacks trainable tensors: {sorted(lost)[:5]}')
    elif missing:
        raise ValueError(f'Checkpoint lacks tensors: {missing[:5]}')
    if optimizer is not None:
        optimizer.load_state_dict(payload['optimizer'])
    if scheduler is not None and 'scheduler' in payload:
        scheduler.load_state_dict(payload['scheduler'])
    if restore_rng:
        set_rng_state(payload['rng'])
    return payload
