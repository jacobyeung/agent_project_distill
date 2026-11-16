"""Parameter counts per head at a given LM width, computed on the meta device (no weights).

`python -m vla_heads.params` prints the README table for Qwen3.5-9B (hidden 4096).
"""
import torch

from .cond import CondProjector
from .config import VLAConfig
from .heads import make_head
from .utils import ProprioEncoder


def count(module):
    return sum(p.numel() for p in module.parameters()) if module is not None else 0


def symbols(cfg, codec):
    """Codec symbols (+1 end symbol for variable-length codecs) without fitting anything."""
    if codec == 'bins':
        return cfg.tok_bins
    if codec == 'dct':
        return 2 * cfg.tok_dct_clip + 1
    if codec == 'fast':
        return cfg.tok_vocab + 1
    return 0


def head_params(cfg):
    """{'head', 'cond_proj', 'lm_inject', 'lm_rows'}: head modules, cond projector, cond/proprio -> LM
    projections, and appended LM embedding + output rows for the LM-written codec ('append' ids)."""
    with torch.device('meta'):
        head = None if cfg.head == 'tokens' else make_head(cfg)
        cond = CondProjector(cfg)
        inject = 0
        if cfg.cond_inject == 'lm' and cfg.cond in ('g3t_tokens', 'both'):
            inject += cfg.cond_dim * cfg.hidden_size + cfg.hidden_size
        if cfg.cond_inject == 'lm' and cfg.cond in ('spatial_readouts', 'both'):
            inject += cfg.where_features * cfg.hidden_size + cfg.hidden_size
        if cfg.proprio_dim and cfg.proprio_inject == 'lm':
            inject += count(ProprioEncoder(cfg.proprio_dim, cfg.hidden_size))
    codec = cfg.token_codec
    rows = 2 * symbols(cfg, codec) * cfg.hidden_size if codec and cfg.tok_ids == 'append' else 0
    return dict(head=count(head), cond_proj=count(cond), lm_inject=inject, lm_rows=rows)


VARIANTS = [
    ('(a) regression, StarVLA OFT H 8192 (default)', dict(head='regression')),
    ('(a) regression, OFT H 1024', dict(head='regression', reg_hidden=1024)),
    ('(b) flow, 8 x 1024, taps 16+32', dict(head='flow')),
    ('(b) flow, 8 x 1024, + FAST LM loss', dict(head='flow', detach_backbone=True, lm_token_loss='fast')),
    ('(b) flow, 16 x 1024 (large)', dict(head='flow', flow_layers=16)),
    ('(c) tokens, FAST 1024', dict(head='tokens', tok_codec='fast')),
    ('(c) tokens, 256 bins', dict(head='tokens', tok_codec='bins')),
]


def table(hidden_size=4096, conds=('none', 'spatial_readouts', 'g3t_tokens', 'both'), **overrides):
    out = []
    for name, kw in VARIANTS:
        for cond in conds:
            cfg = VLAConfig(hidden_size=hidden_size, cond=cond, **{**kw, **overrides})
            out.append(dict(name=name, cond=cond, **head_params(cfg)))
    return out


def markdown(rows):
    lines = ['| Head | cond | head | cond projector | LM injection | new LM rows | total new |',
             '|---|---|---:|---:|---:|---:|---:|']
    for r in rows:
        total = r['head'] + r['cond_proj'] + r['lm_inject'] + r['lm_rows']
        lines.append(f"| {r['name']} | {r['cond']} | {r['head']:,} | {r['cond_proj']:,} | {r['lm_inject']:,} | "
                     f"{r['lm_rows']:,} | {total:,} |")
    return '\n'.join(lines)


if __name__ == '__main__':
    print(markdown(table()))
