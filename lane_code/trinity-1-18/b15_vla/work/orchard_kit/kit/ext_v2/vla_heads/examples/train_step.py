"""One optimizer step per head on the tiny native Qwen3.5 student (CPU), printing the loss parts
and the gradient norm per module group.

    source work/vla_heads/env.sh
    python work/vla_heads/examples/train_step.py --cond both
    python work/vla_heads/examples/train_step.py --heads flow --detach-backbone --lm-token-loss bins
"""
import argparse
import copy

import torch

from vla_heads.testing import build, full_batch, small_config, student_batch, tiny_qwen35


def grad_norm(params):
    norms = [p.grad.detach().float().norm() for p in params if p.grad is not None]
    return float(torch.stack(norms).norm()) if norms else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cond', default='both', choices=['none', 'g3t_tokens', 'spatial_readouts', 'both'])
    ap.add_argument('--train-mode', default='full', choices=['full', 'lora', 'frozen'])
    ap.add_argument('--detach-backbone', action='store_true')
    ap.add_argument('--lm-token-loss', default='none', choices=['none', 'bins', 'dct', 'fast'])
    ap.add_argument('--heads', default='regression,flow,tokens')
    args = ap.parse_args()
    base = tiny_qwen35()
    for head in args.heads.split(','):
        torch.manual_seed(0)
        kw = dict(cond=args.cond, train_mode=args.train_mode, lora_rank=4, lora_alpha=8)
        if head == 'flow':
            kw.update(detach_backbone=args.detach_backbone, lm_token_loss=args.lm_token_loss, tok_dct_scale=20.0)
        cfg = small_config(head, **kw)
        model = copy.deepcopy(base)
        pol = build(cfg, 'student', model)
        opt = torch.optim.AdamW([p for p in pol.parameters() if p.requires_grad], lr=1e-4)
        batch = full_batch(cfg, student_batch(model, b=2), 2)
        out = pol.loss(batch)
        opt.zero_grad(set_to_none=True)
        out['loss'].backward()
        norms = ' '.join(f'{k}={grad_norm(v):.3e}' for k, v in pol.module_groups().items())
        opt.step()
        parts = ' '.join(f'{k}={float(v):.4f}' for k, v in out['parts'].items())
        print(f'{head:10s} loss={out["loss"].detach().item():.4f} [{parts}] grad_norm: {norms}')
        print(f'{"":10s} predict -> {tuple(pol.eval().predict(batch).shape)}')


if __name__ == '__main__':
    main()
