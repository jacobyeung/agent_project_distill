"""Toy problems for the overfit and bimodal tests and examples/overfit.py (stub backbone, CPU)."""
import time

import torch

from .adapters import StubBackbone
from .policy import VLAPolicy
from .testing import STUB_QUERY_ID


def pairs(n=64, t=4, vocab=64, chunk=4, action_dim=7, proprio_dim=8, seed=0):
    """n distinct (token-sequence state, action chunk) pairs; actions in [-0.9, 0.9]. Each row ends
    with `chunk` query tokens (STUB_QUERY_ID), as the LIBERO prompt does."""
    g = torch.Generator().manual_seed(seed)
    ids = torch.randint(0, vocab - 1, (n, t), generator=g)
    ids[:, 0] = torch.arange(n) % (vocab - 1)  # distinct first two tokens per row
    ids[:, 1] = torch.arange(n) // (vocab - 1)
    ids = torch.cat([ids, torch.full((n, chunk), STUB_QUERY_ID)], 1)
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids),
                 actions=(torch.rand(n, chunk, action_dim, generator=g) * 1.8 - 0.9))
    if proprio_dim:
        batch['proprio'] = torch.rand(n, proprio_dim, generator=g) * 2 - 1
    return batch


def train(cfg, batch, steps, lr=3e-3, seed=0, sample_batch=None, max_seconds=120, vocab=64, codec=None):
    """Full-batch AdamW on a fresh stub policy. sample_batch(step) may resample targets each step."""
    torch.manual_seed(seed)
    pol = VLAPolicy(cfg, StubBackbone.for_config(cfg, vocab=vocab), codec=codec, query_token_id=STUB_QUERY_ID)
    opt = torch.optim.AdamW([p for p in pol.parameters() if p.requires_grad], lr=lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 50))
    start, losses = time.perf_counter(), []
    for step in range(steps):
        b = batch if sample_batch is None else sample_batch(step)
        loss = pol.loss(b)['loss']
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
        opt.step()
        sched.step()
        losses.append(loss.detach().item())
        if time.perf_counter() - start > max_seconds:
            break
    return pol.eval(), losses, time.perf_counter() - start


def bimodal(n=32, t=4, vocab=64, chunk=4, action_dim=2, seed=0, shared=True):
    """Each state's chunk is +m or -m (50/50, resampled every call), m a fixed pattern with |m| in
    [0.5, 0.9] (one pattern for every state when `shared`, else one per state). The conditional mean
    (0) is far from both modes: think of passing an obstacle on the left or on the right."""
    g = torch.Generator().manual_seed(seed)
    base = pairs(n, t, vocab, chunk, action_dim, 0, seed)
    rows = 1 if shared else n
    sign = torch.where(torch.rand(rows, chunk, action_dim, generator=g) > 0.5, 1.0, -1.0)
    mode = ((torch.rand(rows, chunk, action_dim, generator=g) * 0.4 + 0.5) * sign).expand(n, -1, -1)
    sg = torch.Generator().manual_seed(seed + 1)

    def sample(step=None):
        s = torch.where(torch.rand(n, 1, 1, generator=sg) > 0.5, 1.0, -1.0)
        return dict(base, actions=mode * s)
    return base, mode, sample


def mode_stats(pred, mode, tol=0.15):
    """pred [S, n, K, A] samples. Returns (fraction of samples within tol (max-abs) of a mode,
    mean over states of the minority-mode share, mean max-abs distance to the nearest mode)."""
    dp = (pred - mode[None]).abs().amax((-1, -2))
    dm = (pred + mode[None]).abs().amax((-1, -2))
    near = torch.minimum(dp, dm)
    plus = (dp < tol).float().mean(0)
    minus = (dm < tol).float().mean(0)
    return (near < tol).float().mean().item(), torch.minimum(plus, minus).mean().item(), near.mean().item()
