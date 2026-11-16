"""Reward of one rollout and of a prompt's group.

  r = c * g - min(lambda * max(0, n - n_min(type, path)) / n_ref(type),  cap_frac * c * g)
  r = 0 when c * g = 0 (the length term applies only to a right, valid trace)

c: benchmark score (score.py); g: gate (gate.py); n: tokens the model generated (forced
first-span and sampled tokens; printed tool responses are free); path: the path taken,
read from the trace ('head' when it holds a tool response, else 'direct'), not the
forcing. n_min: the shortest valid trace of that path for the type (registered table from
validated SFT rows, floored at one Locate/Call line); when the table lacks the cell, the
shortest right and valid rollout of that path in the group. Deviation from the brief's formula: the
length term is capped at cap_frac of c*g (default 0.5), so a right answer always keeps
more than half its score and never falls to or below a wrong one (r = 0).
"""
from .gate import gate
from .score import score

DEFAULTS = dict(lam=0.2, cap_frac=0.5, n_floor=12, n_ref_default=256, allow_stated_option=False)


def path_taken(form):
    return 'head' if form == 'program' else 'direct'


def length_term(base, n, n_min, n_ref, lam, cap_frac):
    if base <= 0:
        return 0.0
    excess = max(0, n - n_min)
    return min(lam * excess / float(n_ref), cap_frac * base)


def score_one(prompt, rec, cfg):
    s = score(prompt, rec['text'])
    gt = gate(prompt, rec, s, allow_stated_option=cfg.get('allow_stated_option', False))
    return dict(prompt_id=rec['prompt_id'], draw=rec['draw'], forced=rec['path'], c=s['c'], answer=s['answer'],
                parse_failure=s['parse_failure'], g=gt['g'], form=gt['form'], recovery=gt['recovery'],
                reasons=gt['reasons'], provenance=gt['provenance'], n=rec['own_tokens'],
                path=path_taken(gt['form']), calls=len(rec.get('calls', [])))


def score_group(prompt, records, cfg=None):
    """Score every draw of one prompt; fill n_min, the length term and r."""
    cfg = {**DEFAULTS, **(cfg or {})}
    rows = [score_one(prompt, rec, cfg) for rec in records]
    table = (cfg.get('n_min') or {}).get(prompt['type'], {})
    n_ref = (cfg.get('n_ref') or {}).get(prompt['type'], cfg['n_ref_default'])
    for row in rows:
        base = row['c'] * row['g']
        n_min, source = table.get(row['path']), 'table'
        if n_min is None:
            valid = [o['n'] for o in rows if o['c'] * o['g'] > 0 and o['path'] == row['path']]
            n_min, source = (min(valid) if valid else row['n']), 'group'
        n_min = max(int(n_min), int(cfg['n_floor']))
        pen = length_term(base, row['n'], n_min, n_ref, cfg['lam'], cfg['cap_frac'])
        row.update(base=base, n_min=n_min, n_min_source=source, n_ref=n_ref, length_term=pen, r=base - pen)
    return rows
