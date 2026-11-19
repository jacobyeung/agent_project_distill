"""Length-reward floor n_min(type, path), set on held-out rollouts (USER ruling 2026-11-16).

    python -m rlkit.floor --run RUN_DIR --prompts HELDOUT.jsonl [--pool RL_POOL.jsonl] \
        [--reward-config R.json] [--delta 0.02] [--min-prompts 20] [--required-calls C.json] \
        --out FLOOR.json

Method, per question type and per path taken (head = the trace holds a tool response):
  1. Score every held-out rollout: base = c * g (reward.score_one; g includes the gate).
  2. Budget accuracy acc(L) = sum(base * [n <= L]) / N over all N rollouts of the cell:
     the accuracy the path keeps when every chain longer than L tokens counts as wrong.
     The denominator is fixed, so acc(L) rises monotonically to the path's full accuracy
     acc_full, and short chains on easy prompts cannot inflate it (the conditional
     accuracy over n <= L is printed beside it for reading, never used to choose).
  3. n_sweep = the shortest L with acc(L) >= acc_full - delta (delta absolute, default 0.02).
  4. Hard minimum: head path = tokens of the type's required head calls (median forced
     head-span tokens of the cell's forced draws x required calls, default 1 call);
     direct path = tokens of one Locate line (median forced direct-span tokens).
     n_min = max(n_sweep, hard_min, n_floor). Which bound set n_min is recorded.
  5. Stability: B prompt-level bootstrap resamples (seeded) give the 5th-95th percentile of
     n_sweep; a cell with fewer than min_prompts prompts or no right, valid rollout gets
     no n_min (the reward then falls back to the group's shortest right trace).
Held-out prompts must not overlap the RL pool (refused by prompt id and by scene).
"""
import argparse
import json
import statistics
from pathlib import Path

import numpy as np

from .common import atomic_write_bytes, atomic_write_json, read_jsonl, sha256_obj
from .reward import DEFAULTS as REWARD_DEFAULTS, score_one
from .store import DrawStore

FLOOR_SCHEMA = 'rlkit-floor-v1'
FLOOR_DEFAULTS = dict(delta=0.02, min_prompts=20, bootstrap=200, seed=17, n_floor=REWARD_DEFAULTS['n_floor'])


class FloorError(ValueError):
    pass


def check_heldout(heldout, pool):
    if not pool:
        raise FloorError('the RL pool is required: held-out prompts must be shown disjoint from it')
    ids = {p['prompt_id'] for p in pool}
    scenes = {p['scene_key'] for p in pool}
    bad = [p['prompt_id'] for p in heldout if p['prompt_id'] in ids or p['scene_key'] in scenes]
    if bad:
        raise FloorError(f'{len(bad)} held-out prompts share an id or scene with the RL pool, e.g. {bad[:3]}')


def budget_curve(n, base):
    """Unique lengths L (ascending) and acc(L), share(L), conditional acc(L)."""
    n, base = np.asarray(n, dtype=np.int64), np.asarray(base, dtype=np.float64)
    order = np.argsort(n, kind='stable')
    n_s, b_s = n[order], base[order]
    lengths = np.unique(n_s)
    idx = np.searchsorted(n_s, lengths, side='right')  # count of rollouts with n <= L
    cum = np.concatenate([[0.0], np.cumsum(b_s)])[idx]
    total = len(n_s)
    return dict(L=lengths, acc=cum / total, share=idx / total, cond=cum / idx)


def sweep_length(n, base, delta):
    """Shortest L whose budget accuracy is within delta of the full accuracy; None if no credit."""
    if not len(n) or float(np.sum(base)) <= 0:
        return None
    cur = budget_curve(n, base)
    full = cur['acc'][-1]
    k = int(np.argmax(cur['acc'] >= full - delta - 1e-12))
    return int(cur['L'][k])


def bootstrap_sweep(groups, delta, B, seed):
    """5th, 50th, 95th percentile of n_sweep over prompt-level resamples; groups = [(n list, base list)]."""
    if B <= 0 or not groups:
        return None
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(B):
        pick = rng.integers(0, len(groups), len(groups))
        n = [x for i in pick for x in groups[i][0]]
        b = [x for i in pick for x in groups[i][1]]
        v = sweep_length(n, b, delta)
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    return dict(p05=float(np.percentile(vals, 5)), p50=float(np.percentile(vals, 50)),
                p95=float(np.percentile(vals, 95)), resamples=len(vals))


def hard_minimum(cell_rows, path, required_calls):
    """Required head calls (head) or one Locate line (direct), in forced-span tokens."""
    spans = [r['forced_prefix_tokens'] for r in cell_rows if r['forced'] == path and r['forced_prefix_tokens'] > 0]
    if not spans:
        return None, 'no forced draws of this path'
    one = int(statistics.median(spans))
    if path == 'head':
        return one * int(required_calls), f'{required_calls} head call(s) x median forced head span {one}'
    return one, f'one Locate line = median forced direct span {one}'


def fit_floor(rows, *, delta=0.02, min_prompts=20, bootstrap=200, seed=17, n_floor=12, required_calls=None):
    """rows: scored rollouts with type, path, forced, forced_prefix_tokens, n, c, g, prompt_id."""
    required_calls = required_calls or {}
    cells = {}
    for r in rows:
        cells.setdefault((r['type'], r['path']), []).append(r)
    table, report = {}, {}
    for (qtype, path), cell in sorted(cells.items()):
        by_prompt = {}
        for r in cell:
            g = by_prompt.setdefault(r['prompt_id'], ([], []))
            g[0].append(int(r['n']))
            g[1].append(float(r['c']) * float(r['g']))
        n = [x for g in by_prompt.values() for x in g[0]]
        base = [x for g in by_prompt.values() for x in g[1]]
        cur = budget_curve(n, base)
        hmin, hwhy = hard_minimum(cell, path, required_calls.get(qtype, 1))
        entry = dict(rollouts=len(n), prompts=len(by_prompt), acc_full=float(cur['acc'][-1]),
                     right_valid=int(sum(b > 0 for b in base)), hard_min=hmin, hard_min_rule=hwhy,
                     n_median=float(np.median(n)), delta=delta)
        if len(by_prompt) < min_prompts or entry['right_valid'] == 0:
            entry.update(n_min=None, set_by='insufficient: %d prompts, %d right and valid' % (len(by_prompt), entry['right_valid']))
        else:
            n_sweep = sweep_length(n, base, delta)
            bounds = dict(sweep=n_sweep, hard_min=hmin or 0, n_floor=n_floor)
            n_min = max(bounds.values())
            entry.update(n_sweep=n_sweep, n_min=int(n_min), set_by=max(bounds, key=lambda k: bounds[k]),
                         acc_at_n_min=float(cur['acc'][np.searchsorted(cur['L'], n_min, side='right') - 1])
                         if n_min >= cur['L'][0] else 0.0,
                         bootstrap=bootstrap_sweep(list(by_prompt.values()), delta, bootstrap, seed))
            table.setdefault(qtype, {})[path] = int(n_min)
        entry['curve'] = curve_points(cur, entry.get('n_min'))
        report.setdefault(qtype, {})[path] = entry
    right_n = {}
    for r in rows:
        if float(r['c']) * float(r['g']) > 0:
            right_n.setdefault(r['type'], []).append(int(r['n']))
    n_ref = {t: max(1, int(statistics.median(v))) for t, v in sorted(right_n.items())}
    return dict(n_min=table, n_ref=n_ref, cells=report)


def curve_points(cur, mark, k=12):
    """Up to k quantile points of the curve plus the chosen n_min, for the printed table."""
    L = cur['L']
    picks = sorted(set(np.unique(np.quantile(np.arange(len(L)), np.linspace(0, 1, min(k, len(L))))
                                 .round().astype(int)).tolist()))
    if mark is not None:
        j = int(np.searchsorted(L, mark, side='right')) - 1
        if j >= 0:
            picks = sorted(set(picks) | {j})
    return [dict(L=int(L[i]), acc=round(float(cur['acc'][i]), 4), share=round(float(cur['share'][i]), 4),
                 cond=round(float(cur['cond'][i]), 4), chosen=bool(mark is not None and L[i] == mark)) for i in picks]


def render(result):
    """Markdown table that shows how each floor was set."""
    out = ['# Length-reward floor n_min(type, path) on held-out rollouts', '',
           'acc(L) = sum(c*g * [n <= L]) / N (chains longer than L count wrong); n_sweep = shortest L with '
           'acc(L) >= acc_full - delta; n_min = max(n_sweep, hard minimum, n_floor).', '',
           '| type | path | prompts | rollouts | acc_full | n_median | n_sweep [p05, p95] | hard min | n_min | set by | acc(n_min) |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for qtype, paths in result['cells'].items():
        for path, e in paths.items():
            bs = e.get('bootstrap')
            ci = f' [{bs["p05"]:.0f}, {bs["p95"]:.0f}]' if bs else ''
            out.append(f'| {qtype} | {path} | {e["prompts"]} | {e["rollouts"]} | {e["acc_full"]:.3f} | {e["n_median"]:.0f} | '
                       f'{e.get("n_sweep", "-")}{ci} | {e["hard_min"]} | {e["n_min"]} | {e["set_by"]} | '
                       f'{e.get("acc_at_n_min", float("nan")):.3f} |')
    out += ['', '## Curves (L: budget acc / share of rollouts with n <= L / conditional acc; * = n_min)']
    for qtype, paths in result['cells'].items():
        for path, e in paths.items():
            pts = '  '.join(f'{"*" if p["chosen"] else ""}{p["L"]}: {p["acc"]:.3f}/{p["share"]:.2f}/{p["cond"]:.3f}'
                            for p in e['curve'])
            out.append(f'- {qtype} / {path} (rule: {e["hard_min_rule"]}): {pts}')
    return '\n'.join(out) + '\n'


def score_run(run_dir, prompts, reward_cfg):
    head = json.loads((Path(run_dir) / 'RUN_CONFIG.json').read_text())
    store = DrawStore(run_dir, head['config'])
    draws = head['config']['sampling']['draws']
    cfg = {**REWARD_DEFAULTS, **(reward_cfg or {})}
    rows = []
    by_id = {p['prompt_id']: p for p in prompts}
    for pid, recs in store.groups(prompts, draws, require_complete=False).items():
        for rec in recs:
            row = score_one(by_id[pid], rec, cfg)
            row.update(type=by_id[pid]['type'], forced_prefix_tokens=rec['forced_prefix_tokens'])
            rows.append(row)
    return rows, head['config_hash']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--pool', required=True)
    ap.add_argument('--reward-config')
    ap.add_argument('--required-calls')
    ap.add_argument('--delta', type=float, default=FLOOR_DEFAULTS['delta'])
    ap.add_argument('--min-prompts', type=int, default=FLOOR_DEFAULTS['min_prompts'])
    ap.add_argument('--bootstrap', type=int, default=FLOOR_DEFAULTS['bootstrap'])
    ap.add_argument('--seed', type=int, default=FLOOR_DEFAULTS['seed'])
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    from .common import sha256_file
    from .sampler import check_prompts
    prompts = read_jsonl(a.prompts)
    check_prompts(prompts, {})
    check_heldout(prompts, read_jsonl(a.pool))
    reward_cfg = json.loads(Path(a.reward_config).read_text()) if a.reward_config else {}
    required = json.loads(Path(a.required_calls).read_text()) if a.required_calls else {}
    rows, run_hash = score_run(a.run, prompts, reward_cfg)
    params = dict(delta=a.delta, min_prompts=a.min_prompts, bootstrap=a.bootstrap, seed=a.seed,
                  n_floor=reward_cfg.get('n_floor', FLOOR_DEFAULTS['n_floor']), required_calls=required)
    result = fit_floor(rows, **params)
    result.update(schema=FLOOR_SCHEMA, params=params, run_config_hash=run_hash, heldout_prompts=len(prompts),
                  heldout_sha256=sha256_file(a.prompts), pool_sha256=sha256_file(a.pool),
                  reward_config_sha256=sha256_obj(reward_cfg))
    atomic_write_json(a.out, result)
    text = render(result)
    atomic_write_bytes(str(Path(a.out).with_suffix('.md')), text.encode())
    print(text)


if __name__ == '__main__':
    main()
