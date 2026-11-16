"""Dry-run measurement: seconds per rollout and tokens per path, the reward table, budget hits,
tower errors, call counts, and the head-path call rate per type. Usage: measure.py RUN_DIR POOL REWARD.json"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, '/scratch/jjyeung/orch_n30/b09_rlkit')
from rlkit.common import read_jsonl  # noqa: E402
from rlkit.reward import DEFAULTS, score_group  # noqa: E402
from rlkit.store import DrawStore  # noqa: E402

run, pool, reward = Path(sys.argv[1]), read_jsonl(sys.argv[2]), json.load(open(sys.argv[3]))
head = json.loads((run / 'RUN_CONFIG.json').read_text())
st = DrawStore(run, head['config'])
groups = st.groups(pool, head['config']['sampling']['draws'], require_complete=False)
by_path, by_forced, by_type, budget, tower, n_draws = {}, {}, {}, 0, 0, 0
for p in pool:
    recs = groups.get(p['prompt_id']) or []
    if not recs:
        continue
    for rec, sc in zip(recs, score_group(p, recs, {**DEFAULTS, **reward})):
        n_draws += 1
        budget += rec['budget_hit']
        tower += rec.get('tower_error') is not None
        cost_path = 'head' if rec['calls'] else 'direct'  # timing by what the decoder did; reward by the gate's form
        cell = by_path.setdefault(cost_path, dict(seconds=[], own=[], calls=[]))
        forced = by_forced.setdefault(rec['path'], [])
        forced.append(rec['seconds'])
        cell['seconds'].append(rec['seconds'])
        cell['own'].append(rec['own_tokens'])
        cell['calls'].append(len(rec['calls']))
        t = by_type.setdefault(p['type'], dict(n=0, c=0., g=0, r=0., head=0, free_head=0, free=0))
        t['n'] += 1; t['c'] += sc['c']; t['g'] += sc['g']; t['r'] += sc['r']; t['head'] += sc['path'] == 'head'
        if rec['path'] == 'free':
            t['free'] += 1; t['free_head'] += sc['path'] == 'head'
summary = dict(draws=n_draws, budget_hits=budget, tower_errors=tower,
               paths={k: dict(n=len(v['seconds']), sec_mean=statistics.mean(v['seconds']),
                              sec_median=statistics.median(v['seconds']), own_tokens_median=statistics.median(v['own']),
                              calls_mean=statistics.mean(v['calls'])) for k, v in by_path.items()},
               forced={k: dict(n=len(v), sec_mean=statistics.mean(v)) for k, v in sorted(by_forced.items())},
               types={k: dict(n=v['n'], c=v['c'] / v['n'], g_rate=v['g'] / v['n'], r=v['r'] / v['n'],
                              head_share=v['head'] / v['n'], free_call_rate=v['free_head'] / max(1, v['free']))
                      for k, v in sorted(by_type.items())})
print(json.dumps(summary, indent=1, sort_keys=True))
