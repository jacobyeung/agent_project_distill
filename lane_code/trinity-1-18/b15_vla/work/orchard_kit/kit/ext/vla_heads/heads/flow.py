"""(b) Flow-matching action expert (design record 1.4), with DDPM/DDIM behind the objective flag.

Context: each configured LM tap -> LayerNorm -> Linear(D -> W) + a learned tap embedding (masked),
plus a learned null token, the projected cond tokens (Linear(cond_dim -> W)) and one token per where
entity (MLP(18 -> W), masked by validity). Expert: `flow_layers` blocks of self-attention over
[proprio token, K action tokens], cross-attention to the context and a 4x MLP (pre-LN residual).

Time conditioning (`flow_time_cond`):
- concat (pi0): action token = MLP([W_a x_tau ; phi(tau)]) with openpi's sinusoidal phi;
- adaln: adaLN scale / shift / gate per block from an MLP of phi(tau).

Objectives (`flow_objective`):
- flow, openpi's convention: x_tau = tau * eps + (1 - tau) * a with tau = 1 pure noise; the expert
  predicts v ~ u = eps - a under masked MSE; tau = 0.001 + 0.999 * Beta(1.5, 1) (`beta`, pi0 and
  GR00T), or uniform, or logit-normal. Inference integrates `flow_steps` Euler steps from tau = 1:
  x <- x - v / steps.
- ddpm: epsilon prediction (or x0 with `ddpm_prediction = sample`) under the cosine schedule over
  `ddpm_train_steps`; deterministic DDIM (eta = 0) with `flow_steps` <= `ddpm_train_steps` steps, x0
  clipped to [-1, 1] when `ddpm_clip_sample`. Epsilon prediction recovers x0 as
  (x - sqrt(1 - ab) eps) / sqrt(ab), which multiplies the eps error by 1 / sqrt(ab) (about 2000 at
  the last cosine step), so its rare large errors come from the high-noise steps.

`detach_backbone` stops every gradient from the expert into the LM (knowledge insulation); the LM
then learns from `lm_token_loss` (the policy adds the codec token loss on the same chunk).
"""
import math

import torch
from torch import nn

from ..cond import rng_neutral
from ..interface import ActionHead, expand_mask, masked_mean
from ..layers import Attention, mlp, positions_1d, time_features, zero_


class _Block(nn.Module):
    def __init__(self, width, heads, mlp_ratio, dropout, adaln):
        super().__init__()
        affine = not adaln
        self.n1 = nn.LayerNorm(width, elementwise_affine=affine)
        self.n2 = nn.LayerNorm(width, elementwise_affine=affine)
        self.n3 = nn.LayerNorm(width, elementwise_affine=affine)
        self.nc = nn.LayerNorm(width)
        self.self_attn = Attention(width, heads, dropout=dropout)
        self.cross_attn = Attention(width, heads, dropout=dropout)
        self.ff = mlp([width, int(width * mlp_ratio), width])
        self.ada = None
        if adaln:
            self.ada = zero_(nn.Linear(width, 9 * width))
            with torch.no_grad():  # gates start at 1, so the context gets gradient at step 0
                for i in (2, 5, 8):
                    self.ada.bias[i * width:(i + 1) * width] = 1.0

    def forward(self, x, temb, ctx, ctx_mask):
        if self.ada is None:
            x = x + self.self_attn(self.n1(x))
            x = x + self.cross_attn(self.n2(x), self.nc(ctx), ctx_mask)
            return x + self.ff(self.n3(x))
        s1, b1, g1, s2, b2, g2, s3, b3, g3 = self.ada(temb)[:, None].chunk(9, dim=-1)
        x = x + g1 * self.self_attn(self.n1(x) * (1 + s1) + b1)
        x = x + g2 * self.cross_attn(self.n2(x) * (1 + s2) + b2, self.nc(ctx), ctx_mask)
        return x + g3 * self.ff(self.n3(x) * (1 + s3) + b3)


def cosine_alpha_bar(steps, s=0.008):
    """alpha_bar at integer steps 0..T (index 0 = clean), clipped like improved DDPM."""
    t = torch.arange(steps + 1, dtype=torch.float64) / steps
    f = torch.cos((t + s) / (1 + s) * math.pi / 2) ** 2
    alpha_bar = f / f[0]
    betas = (1 - alpha_bar[1:] / alpha_bar[:-1]).clamp(max=0.999)
    return torch.cat([torch.ones(1, dtype=torch.float64), torch.cumprod(1 - betas, 0)]).float()


def sample_tau(dist, b, device):
    """Training noise level tau in (0, 1], tau = 1 pure noise."""
    if dist == 'uniform':
        return torch.rand(b, device=device) * 0.999 + 0.001
    if dist == 'logit_normal':
        return torch.sigmoid(torch.randn(b, device=device)) * 0.999 + 0.001
    # Beta(1.5, 1) has CDF x^1.5, so inverse-CDF sampling is exact: u^(2/3).
    return 0.001 + 0.999 * torch.rand(b, device=device) ** (2.0 / 3.0)


class FlowExpert(ActionHead):
    kind = 'flow'

    def __init__(self, cfg):
        super().__init__(cfg)
        w, d = cfg.flow_width, cfg.hidden_size
        adaln = cfg.flow_time_cond == 'adaln'
        self.n_taps = len(cfg.taps)
        self.tap_norm = nn.ModuleList([nn.LayerNorm(d) for _ in range(self.n_taps)])
        self.tap_proj = nn.ModuleList([nn.Linear(d, w) for _ in range(self.n_taps)])
        self.tap_embed = nn.Parameter(torch.zeros(self.n_taps, w))
        self.null = nn.Parameter(torch.zeros(1, 1, w))
        self.act_in = nn.Linear(cfg.action_dim, w)
        self.register_buffer('pos', positions_1d(cfg.chunk, w, 'cpu'), persistent=False)
        if adaln:
            self.time = mlp([w, w, w], act='silu')
        else:
            self.time_mix = mlp([2 * w, w, w], act='silu')
        self.blocks = nn.ModuleList([_Block(w, cfg.flow_heads, cfg.flow_mlp_ratio, cfg.flow_dropout, adaln)
                                     for _ in range(cfg.flow_layers)])
        self.out_norm = nn.LayerNorm(w)
        self.out = nn.Linear(w, cfg.action_dim)
        with rng_neutral():
            head_cond = cfg.cond_inject == 'head'
            self.proprio = (nn.Linear(cfg.proprio_dim, w) if cfg.proprio_dim and cfg.proprio_inject == 'head'
                            else None)
            self.cond_proj = (nn.Linear(cfg.cond_dim, w)
                              if head_cond and cfg.cond in ('g3t_tokens', 'both') else None)
            self.where = (mlp([cfg.where_features, w, w], act='silu')
                          if head_cond and cfg.cond in ('spatial_readouts', 'both') else None)
            self.cond_type = nn.Parameter(torch.zeros(2, w)) if head_cond and cfg.cond != 'none' else None
        if cfg.flow_objective == 'ddpm':
            self.register_buffer('alpha_bar', cosine_alpha_bar(cfg.ddpm_train_steps), persistent=False)

    # context -----------------------------------------------------------------------------------
    def context(self, inputs):
        if self.cfg.detach_backbone:
            inputs = inputs.detached()
        self.check(inputs)
        dtype = self.act_in.weight.dtype
        b, device = inputs.batch, inputs.lm_states.device
        taps = inputs.tap_states if inputs.tap_states is not None else inputs.lm_states[None]
        if taps.shape[0] != self.n_taps:
            raise ValueError(f'The flow head reads {self.n_taps} taps, got {taps.shape[0]}')
        parts = [self.null.to(dtype).expand(b, -1, -1)]
        masks = [torch.ones(b, 1, dtype=torch.bool, device=device)]
        for i in range(self.n_taps):
            parts.append(self.tap_proj[i](self.tap_norm[i](taps[i].to(dtype))) + self.tap_embed[i].to(dtype))
            masks.append(inputs.lm_mask)
        if self.cond_proj is not None and inputs.cond_tokens is not None:
            parts.append(self.cond_proj(inputs.cond_tokens.to(dtype)) + self.cond_type[0].to(dtype))
            masks.append(inputs.cond_mask)
        if self.where is not None:
            parts.append(self.where(inputs.where.to(dtype)) + self.cond_type[1].to(dtype))
            masks.append(inputs.where_mask)
        prop = None if self.proprio is None else self.proprio(inputs.proprio.to(dtype))[:, None]
        return torch.cat(parts, 1), torch.cat(masks, 1), prop

    def denoise(self, x, tau, ctx, ctx_mask, prop):
        """x [B, K, A] noisy actions, tau [B] (1 = noise) -> velocity (flow) or epsilon (ddpm)."""
        dtype = self.act_in.weight.dtype
        phi = time_features(tau, self.cfg.flow_width).to(dtype)
        h = self.act_in(x.to(dtype))
        temb = None
        if self.cfg.flow_time_cond == 'adaln':
            temb = self.time(phi)
        else:
            h = self.time_mix(torch.cat([h, phi[:, None].expand_as(h)], -1))
        h = h + self.pos.to(device=x.device, dtype=dtype)[None]
        if prop is not None:
            h = torch.cat([prop, h], 1)
        for block in self.blocks:
            h = block(h, temb, ctx, ctx_mask)
        if prop is not None:
            h = h[:, 1:]
        return self.out(self.out_norm(h))

    # training ----------------------------------------------------------------------------------
    def loss(self, inputs, actions, action_mask=None):
        self.check(inputs, actions)
        ctx, ctx_mask, prop = self.context(inputs)
        a = actions.float()
        b, device = a.shape[0], a.device
        eps = torch.randn_like(a)
        if self.cfg.flow_objective == 'flow':
            tau = sample_tau(self.cfg.flow_time_dist, b, device)
            xt = tau[:, None, None] * eps + (1 - tau[:, None, None]) * a
            target = eps - a
        else:
            steps = self.cfg.ddpm_train_steps
            k = torch.randint(1, steps + 1, (b,), device=device)
            ab = self.alpha_bar.to(device)[k][:, None, None]
            xt = ab.sqrt() * a + (1 - ab).sqrt() * eps
            tau = k.float() / steps
            target = eps if self.cfg.ddpm_prediction == 'epsilon' else a
        pred = self.denoise(xt, tau, ctx, ctx_mask, prop).float()
        loss = masked_mean((pred - target) ** 2, expand_mask(action_mask, actions))
        return {'loss': loss, 'parts': {'mse_' + self.cfg.flow_objective: loss.detach()}}

    # sampling ----------------------------------------------------------------------------------
    @torch.no_grad()
    def predict(self, inputs, noise=None, steps=None):
        ctx, ctx_mask, prop = self.context(inputs)
        b, device = inputs.batch, inputs.lm_states.device
        shape = (b, self.cfg.chunk, self.cfg.action_dim)
        x = torch.randn(shape, device=device) if noise is None else noise.float().to(device)
        steps = steps or self.cfg.flow_steps
        if self.cfg.flow_objective == 'flow':
            x = euler(lambda xt, tau: self.denoise(xt, tau, ctx, ctx_mask, prop).float(), x, steps)
        else:
            total = self.cfg.ddpm_train_steps
            if steps > total:
                raise ValueError(f'DDIM steps={steps} exceed ddpm_train_steps={total}')
            ab = self.alpha_bar.to(device)
            ks = torch.linspace(total, 0, steps + 1).round().long().tolist()  # strictly decreasing
            for k, k_next in zip(ks[:-1], ks[1:]):
                tau = torch.full((b,), k / total, device=device)
                out = self.denoise(x, tau, ctx, ctx_mask, prop).float()
                if self.cfg.ddpm_prediction == 'epsilon':
                    e, x0 = out, (x - (1 - ab[k]).sqrt() * out) / ab[k].sqrt()
                else:
                    e, x0 = None, out
                if self.cfg.ddpm_clip_sample:
                    x0 = x0.clamp(-1, 1)
                if e is None or self.cfg.ddpm_clip_sample:
                    e = (x - ab[k].sqrt() * x0) / (1 - ab[k]).sqrt()
                x = ab[k_next].sqrt() * x0 + (1 - ab[k_next]).sqrt() * e
        return x.clamp(-1, 1).to(inputs.lm_states.dtype)


def euler(velocity, x, steps):
    """Integrate dx/dtau = v from tau = 1 (noise) to tau = 0 (data): x <- x - v / steps."""
    dt = 1.0 / steps
    for i in range(steps):
        tau = torch.full((x.shape[0],), 1.0 - i * dt, device=x.device)
        x = x - dt * velocity(x, tau)
    return x
