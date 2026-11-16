"""(a) OFT-style parallel regression (design record 1.3).

K learnable action queries are appended to the LM input; the last tap at those K positions goes
through LayerNorm -> Linear(D -> H) [-> act] -> + proprio and where terms -> `reg_blocks` residual
blocks -> [LayerNorm] -> Linear(H -> A). L1 loss; one forward pass at inference.

- reg_block 'mlp2' (design default): x + Linear(act(Linear(LN(x)))).
- reg_block 'oft' (OpenVLA-OFT / StarVLA L1RegressionActionHead): x + act(Linear(LN(x))), with
  reg_input_act = reg_final_norm = true, reg_act = relu and reg_hidden = 2 D reproduces StarVLA's head.
Proprio (P -> H) and the where vector (E * 18 -> H) enter through zero-initialised linear maps;
G3T and readout cond tokens through a cross-attention whose output projection is zero-initialised.
So at step 0 every cond or proprio variant predicts exactly what the plain head predicts.
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
        self.n_queries = cfg.chunk
        self.queries = nn.Parameter(torch.randn(cfg.chunk, d) * 0.02)
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
                          if head_cond and cfg.cond in ('spatial_readouts', 'both') else None)
            self.cond_attn = None
            if head_cond and cfg.cond != 'none':
                self.cond_null = nn.Parameter(torch.zeros(1, 1, h))
                self.cond_proj = nn.Linear(cfg.cond_dim, h)
                self.cond_norm = nn.LayerNorm(h)
                self.cond_attn = Attention(h, cfg.reg_cond_heads)
                zero_(self.cond_attn.out)

    def query_embeds(self, batch, dtype, device):
        return self.queries.to(dtype=dtype, device=device)[None].expand(batch, -1, -1)

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
        return self.forward(inputs).clamp(-1, 1).to(inputs.lm_states.dtype)
