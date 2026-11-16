"""Overfit 64 synthetic (state, action-chunk) pairs with each head on the stub backbone (CPU), and
run the bimodal toy that separates the flow expert from the regression head.

    source work/vla_heads/env.sh
    python work/vla_heads/examples/overfit.py                       # every head, then the bimodal toy
    python work/vla_heads/examples/overfit.py --heads flow --objective ddpm
    python work/vla_heads/examples/overfit.py --heads tokens --codec fast
"""
import argparse

import torch

from vla_heads import FastCodec
from vla_heads.testing import small_config, synthetic_cond
from vla_heads.toy import bimodal, mode_stats, pairs, train

TOY = dict(hidden_size=64, reg_hidden=64, flow_width=64, flow_layers=2)
STEPS = dict(regression=400, flow=1500, tokens=500)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--heads', default='regression,flow,tokens')
    ap.add_argument('--objective', default='flow', choices=['flow', 'ddpm'])
    ap.add_argument('--codec', default='bins', choices=['bins', 'dct', 'fast'])
    ap.add_argument('--cond', default='none')
    ap.add_argument('--no-bimodal', action='store_true')
    args = ap.parse_args()
    for head in args.heads.split(','):
        cfg = small_config(head, **TOY, cond=args.cond, flow_objective=args.objective, flow_steps=10,
                           tok_codec=args.codec, tok_dct_scale=20.0)
        batch = pairs(64, chunk=cfg.chunk)
        if cfg.cond != 'none':
            batch['cond'] = synthetic_cond(cfg, 64, patch=False)
        codec = None
        if head == 'tokens' and args.codec == 'fast':
            codec = FastCodec(cfg.chunk, cfg.action_dim, cfg.tok_vocab, cfg.tok_dct_scale).fit(batch['actions'])
        lr = 2e-3 if head == 'flow' else 3e-3
        pol, losses, sec = train(cfg, batch, STEPS[head], lr, max_seconds=300, codec=codec)
        torch.manual_seed(0)
        err = (pol.predict(batch) - batch['actions']).abs()
        curve = ' '.join(f'{losses[i]:.4f}' for i in range(0, len(losses), max(1, len(losses) // 8)))
        print(f'{head:10s} steps={len(losses)} {sec:5.1f}s loss curve: {curve} -> {losses[-1]:.4f}; '
              f'|err| mean={err.mean():.4f} max={err.max():.4f}')
    if args.no_bimodal:
        return
    for head, steps in (('regression', 600), ('flow', 1500)):
        cfg = small_config(head, **TOY, action_dim=2, proprio_dim=0, flow_steps=10, flow_time_dist='uniform')
        base, mode, sample = bimodal(32, chunk=cfg.chunk)
        pol, losses, sec = train(cfg, base, steps, 2e-3, sample_batch=sample, max_seconds=300)
        torch.manual_seed(0)
        pred = torch.stack([pol.predict(base) for _ in range(32)])
        near, minority, dist = mode_stats(pred, mode)
        print(f'bimodal {head:10s}: within 0.15 of a mode {near:.3f}, minority-mode share {minority:.3f}, '
              f'mean distance to nearest mode {dist:.3f} ({sec:.1f}s)')


if __name__ == '__main__':
    main()
