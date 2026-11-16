"""The one interface every action head implements (HeadInputs v2, VLA_SCHEMA.md sections 1-3).

Shapes (batch first): B batch, T LM context length, D LM width (4096), n taps, N cond tokens,
Dc cond width (1024), E where entities (2: target, place; 18 numbers each), P proprio width (8),
K chunk length (8), A action width (7).

`HeadInputs`
- lm_states [B, T, D] and lm_mask [B, T] (bool, True = real token; the processor left-pads): the
  last configured tap over all positions (prompt, images and any LM-injected cond or proprio tokens).
- tap_states [n, B, T, D] or None: every configured tap, in config order (flow head).
- query_states [B, K, D] or None: tap -1 at the prompt's K query tokens (regression), or at the
  positions that predict each codec token (tokens head).
- cond_tokens [B, N, Dc] and cond_mask [B, N] or None: projected G3T / readout tokens (`cond.py`).
- where [B, 2, 18] and where_mask [B, 2] or None: the where records after dropout (schema 5);
  where_mask = valid AND NOT withheld.
- proprio [B, 8] or None: normalised proprioception (schema 7).
- decoder: tokens head at inference only, a stateful callable supplied by the policy:
  decoder(None) -> state [B, D] at the last prefix position; decoder(ids [B]) appends one token and
  returns the state that predicts the next one.
The backbone runs under bf16 autocast; heads cast their inputs to fp32 at their first LayerNorm and
compute the loss in fp32.

Every head implements
- kind: 'regression' | 'flow' | 'tokens'
- loss(inputs, actions [B, K, A] fp32, action_mask [B, K] (or [B, K, A]) in {0, 1} or None)
  -> {'loss': fp32 scalar, 'parts': {name: detached}}; the loss averages over unmasked entries.
- predict(inputs) -> fp32 actions [B, K, A] in the normalised action space, clipped to [-1, 1].
"""
from dataclasses import dataclass, replace
from typing import Callable, Optional

import torch
from torch import nn


@dataclass
class HeadInputs:
    lm_states: torch.Tensor
    lm_mask: torch.Tensor
    query_states: Optional[torch.Tensor] = None
    cond_tokens: Optional[torch.Tensor] = None
    cond_mask: Optional[torch.Tensor] = None
    proprio: Optional[torch.Tensor] = None
    decoder: Optional[Callable] = None
    tap_states: Optional[torch.Tensor] = None
    where: Optional[torch.Tensor] = None
    where_mask: Optional[torch.Tensor] = None

    def __post_init__(self):
        b, t, _ = self.lm_states.shape
        if self.lm_mask.shape != (b, t):
            raise ValueError(f'lm_mask must be [{b}, {t}], got {tuple(self.lm_mask.shape)}')
        self.lm_mask = self.lm_mask.bool()
        if self.tap_states is not None and (self.tap_states.ndim != 4 or self.tap_states.shape[1:3] != (b, t)):
            raise ValueError('tap_states must be [n_taps, B, T, D]')
        for tokens, name in ((self.cond_tokens, 'cond'), (self.where, 'where')):
            if tokens is None:
                continue
            if tokens.ndim != 3 or tokens.shape[0] != b:
                raise ValueError(f'{name} tokens must be [B, N, F]')
            mask = getattr(self, name + '_mask')
            mask = torch.ones(tokens.shape[:2], dtype=torch.bool, device=tokens.device) if mask is None else mask.bool()
            setattr(self, name + '_mask', mask)
        if self.proprio is not None and (self.proprio.ndim != 2 or self.proprio.shape[0] != b):
            raise ValueError('proprio must be [B, P]')

    @property
    def batch(self):
        return self.lm_states.shape[0]

    def detached(self):
        """Knowledge insulation: the head sees the same values, but no gradient reaches the LM."""
        d = lambda x: None if x is None else x.detach()
        return replace(self, lm_states=self.lm_states.detach(), query_states=d(self.query_states),
                       tap_states=d(self.tap_states))


def expand_mask(action_mask, actions):
    """[B, K] or [B, K, A] or None -> float [B, K, A] weights."""
    if action_mask is None:
        return torch.ones_like(actions, dtype=torch.float32)
    mask = action_mask.to(device=actions.device, dtype=torch.float32)
    if mask.ndim == 2:
        mask = mask[..., None].expand_as(actions)
    if mask.shape != actions.shape:
        raise ValueError(f'action_mask {tuple(action_mask.shape)} does not match actions {tuple(actions.shape)}')
    return mask


def masked_mean(values, weights):
    return (values.float() * weights).sum() / weights.sum().clamp(min=1.0)


class ActionHead(nn.Module):
    kind = None

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg

    def check(self, inputs, actions=None):
        if actions is not None and tuple(actions.shape[1:]) != (self.cfg.chunk, self.cfg.action_dim):
            raise ValueError(f'actions must be [B, {self.cfg.chunk}, {self.cfg.action_dim}], got {tuple(actions.shape)}')
        if self.cfg.proprio_inject == 'head' and self.cfg.proprio_dim and inputs.proprio is None:
            raise ValueError('This head expects proprio [B, P]')
        if self.cfg.cond_inject == 'head':
            if self.cfg.cond in ('g3t_tokens', 'both') and inputs.cond_tokens is None:
                raise ValueError(f'cond={self.cfg.cond} needs cond_tokens')
            if self.cfg.where_vector and self.cfg.cond in ('spatial_readouts', 'both') and inputs.where is None:
                raise ValueError(f'cond={self.cfg.cond} needs where [B, E, 18]')

    def loss(self, inputs, actions, action_mask=None):
        raise NotImplementedError

    def predict(self, inputs):
        raise NotImplementedError
