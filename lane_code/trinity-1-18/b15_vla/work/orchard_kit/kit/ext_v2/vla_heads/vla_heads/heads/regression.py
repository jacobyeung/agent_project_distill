"""(a) OFT-style parallel regression, the default head (schema 1, design record 1.3).

The last tap (-1) at the prompt's K query tokens (`query_states`, gathered by the policy; v1 learns
no query embeddings) goes through LayerNorm -> Linear(D -> H) [-> act] -> + proprio and where terms
-> `reg_blocks` residual blocks -> [LayerNorm] -> Linear(H -> A). L1 loss over unmasked steps and
dimensions; one forward pass at inference. The head computes in fp32 (inputs cast at its first
LayerNorm) and returns fp32 normalised actions.

- reg_arch 'starvla_oft_985c2238' (default): StarVLA's L1RegressionActionHead, blocks
  x + ReLU(Linear(LN(x))), ReLU after the first projection, LayerNorm before the output, H = 8192 at
  D = 4096 (about 0.17B parameters). tests/test_parity_starvla.py pins the layout to StarVLA's code.
- reg_arch 'custom': any of reg_block ('oft' | 'mlp2' = x + Linear(act(Linear(LN(x))))), reg_act,
  reg_input_act, reg_final_norm, reg_hidden (for example the 1024-wide variant).
Proprio Linear(P -> H) and where Linear(E * 18 -> H) (the two records flattened in entity order,
multiplied by where_mask) are zero-initialised and added after the first projection; G3T and readout
cond tokens enter through a cross-attention whose output projection is zero-initialised. At step 0
every cond or proprio variant therefore predicts exactly what the plain head predicts.
"""
import torch
from torch import nn

from ..cond import rng_neutral
from ..interface import ActionHead, expand_mask, masked_mean
from ..layers import ACTS, Attention, zero_


class _Block(nn.Module):
    def __init__(self, dim, kind, act):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, dim)
        self.act = ACTS[act]()
        self.fc2 = nn.Linear(dim, dim) if kind == 'mlp2' else None

    def forward(self, x):
        h = self.act(self.fc1(self.norm(x)))
        return x + (h if self.fc2 is None else self.fc2(h))


class RegressionHead(ActionHead):
    kind = 'regression'

    def __init__(self, cfg):
        super().__init__(cfg)
        d, h = cfg.hidden_size, cfg.reg_hidden
        self.norm = nn.LayerNorm(d)
        self.inp = nn.Linear(d, h)
        self.inp_act = ACTS[cfg.reg_act]() if cfg.reg_input_act else nn.Identity()
        self.blocks = nn.ModuleList([_Block(h, cfg.reg_block, cfg.reg_act) for _ in range(cfg.reg_blocks)])
        self.final_norm = nn.LayerNorm(h) if cfg.reg_final_norm else nn.Identity()
        self.out = nn.Linear(h, cfg.action_dim)
        with rng_neutral():
            head_cond = cfg.cond_inject == 'head'
            self.proprio = (zero_(nn.Linear(cfg.proprio_dim, h)) if cfg.proprio_dim and cfg.proprio_inject == 'head'
                            else None)
            self.where = (zero_(nn.Linear(cfg.where_entities * cfg.where_features, h))
                          if head_cond and cfg.where_vector and cfg.cond in ('spatial_readouts', 'both') else None)
            self.cond_attn = None
            if head_cond and cfg.cond in ('g3t_tokens', 'both'):
                self.cond_null = nn.Parameter(torch.zeros(1, 1, h))
                self.cond_proj = nn.Linear(cfg.cond_dim, h)
                self.cond_norm = nn.LayerNorm(h)
                self.cond_attn = Attention(h, cfg.reg_cond_heads)
                zero_(self.cond_attn.out)

    def forward(self, inputs):
        self.check(inputs)
        q = inputs.query_states
        if q is None or q.shape[1] != self.cfg.chunk:
            raise ValueError(f'The regression head needs query_states [B, {self.cfg.chunk}, D]')
        dtype = self.inp.weight.dtype
        x = self.inp_act(self.inp(self.norm(q.to(dtype))))
        if self.proprio is not None:
            x = x + self.proprio(inputs.proprio.to(dtype))[:, None]
        if self.where is not None:
            w = inputs.where * inputs.where_mask[..., None]
            x = x + self.where(w.flatten(1).to(dtype))[:, None]
        if self.cond_attn is not None and inputs.cond_tokens is not None:
            ctx = self.cond_proj(inputs.cond_tokens.to(dtype))
            ctx = torch.cat([self.cond_null.expand(len(ctx), -1, -1).to(dtype), ctx], 1)
            mask = torch.cat([torch.ones_like(inputs.cond_mask[:, :1]), inputs.cond_mask], 1)
            x = x + self.cond_attn(self.cond_norm(x), self.cond_norm(ctx), mask)
        for block in self.blocks:
            x = block(x)
        return self.out(self.final_norm(x))

    def loss(self, inputs, actions, action_mask=None):
        self.check(inputs, actions)
        pred = self.forward(inputs).float()
        loss = masked_mean((pred - actions.float()).abs(), expand_mask(action_mask, actions))
        return {'loss': loss, 'parts': {'l1': loss.detach()}}

    @torch.no_grad()
    def predict(self, inputs):
        """fp32 [B, K, A] normalised actions, clipped to [-1, 1] (schema 7: evaluation clips)."""
        return self.forward(inputs).float().clamp(-1, 1)
