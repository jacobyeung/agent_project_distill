"""Small shared modules: masked attention, MLPs, sinusoidal time features, zero initialisation."""
import math

import torch
from torch import nn
from torch.nn import functional as F

ACTS = {'gelu': nn.GELU, 'relu': nn.ReLU, 'silu': nn.SiLU}


def zero_(module):
    """Zero every parameter of `module` in place and return it."""
    with torch.no_grad():
        for p in module.parameters():
            p.zero_()
    return module


def mlp(dims, act='gelu', zero_last=False):
    act = ACTS[act] if isinstance(act, str) else act
    layers = []
    for i, (a, b) in enumerate(zip(dims[:-1], dims[1:])):
        layers.append(nn.Linear(a, b))
        if i < len(dims) - 2:
            layers.append(act())
    if zero_last:
        zero_(layers[-1])
    return nn.Sequential(*layers)


class Attention(nn.Module):
    """Multi-head attention with a boolean key mask (True = attend). Callers keep at least one valid
    key per row (a learned null token)."""

    def __init__(self, dim, heads, kv_dim=None, dropout=0.0):
        super().__init__()
        self.heads, self.dropout = heads, dropout
        self.q = nn.Linear(dim, dim)
        self.kv = nn.Linear(kv_dim or dim, 2 * dim)
        self.out = nn.Linear(dim, dim)

    def forward(self, x, context=None, key_mask=None):
        context = x if context is None else context
        b, n, d = x.shape
        split = lambda t: t.reshape(b, t.shape[1], self.heads, d // self.heads).transpose(1, 2)
        q = split(self.q(x))
        k, v = (split(t) for t in self.kv(context).chunk(2, dim=-1))
        mask = None if key_mask is None else key_mask[:, None, None, :].to(device=x.device)
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask,
                                           dropout_p=self.dropout if self.training else 0.0)
        return self.out(y.transpose(1, 2).reshape(b, n, d))


def time_features(t, dim, min_period=4e-3, max_period=4.0):
    """openpi's sinusoidal embedding of t in [0, 1] (periods from min_period to max_period), fp32.
    [B] -> [B, dim]."""
    half = dim // 2
    fraction = torch.linspace(0.0, 1.0, half, device=t.device, dtype=torch.float32)
    period = min_period * (max_period / min_period) ** fraction
    args = 2 * math.pi * t.float()[:, None] / period[None]
    out = torch.cat([args.sin(), args.cos()], dim=-1)
    return F.pad(out, (0, dim - 2 * half))


def positions_1d(n, dim, device):
    pos = torch.arange(n, device=device, dtype=torch.float32) / max(n, 1)
    return time_features(pos, dim)
