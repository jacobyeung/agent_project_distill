"""Profile only the supplied small return journals; never load model weights."""
import collections
import csv
import hashlib
import json
import math
import statistics as st
from pathlib import Path

L = Path('/scratch/jjyeung/orch_n30/so_read')
BASE = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3')

def records(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def stats(xs):
    xs = sorted(xs)
    if not xs: return dict(n=0, mean=None, median=None, p90=None, total=0)
    pos = (len(xs)-1)*.9
    lo = math.floor(pos); hi = math.ceil(pos)
    return dict(n=len(xs), mean=st.mean(xs), median=st.median(xs),
                p90=xs[lo]+(xs[hi]-xs[lo])*(pos-lo), total=sum(xs))

report = {'evidence': 'Measured existing journals; p90 uses linear interpolation at (N-1)*0.9.', 'packages': {}}
flat = []
for package in ('A4', 'B5'):
    root = BASE/package/'ret/metadata/reads/0'
    summary = {'types': {}, 'journals': [], 'rows': 0}
    last_hits = last_misses = 0
    for t in (3, 0, 1, 2, 4):
        p = root/f'metadata/journals/{t}/0/items.jsonl'
        if not p.exists(): continue
        rows = records(p); outs = [r['output'] for r in rows]
        timing = records(p.parent/'timings.jsonl')
        env = json.loads((p.parent/'environment.json').read_text())
        memos = [o.get('perception_memo', {}) for o in outs]
        calls = [o['calls']['records'] for o in outs]
        fields = sorted(set().union(*(o.get('timings', {}) for o in outs)))
        d = dict(items=len(rows), source=str(p), source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            seconds=stats([r['seconds'] for r in rows]),
            output_seconds=stats([o['seconds'] for o in outs]),
            tokens_including_forced=stats([len(o['tokens']) for o in outs]),
            forced_tokens=stats([sum(c.get('forced_tokens',0) for c in cs) for cs in calls]),
            chosen_tokens=stats([len(o['tokens'])-sum(c.get('forced_tokens',0) for c in cs) for o,cs in zip(outs,calls)]),
            prompt_tokens=stats([o['prompt_tokens'] for o in outs]),
            calls=stats([len(cs) for cs in calls]),
            call_families=dict(collections.Counter(c['family'] for cs in calls for c in cs)),
            timings={f:stats([o['timings'].get(f,0) for o in outs]) for f in fields},
            timed_g3t_accesses=sum('g3t_s' in o['timings'] for o in outs),
            factory_load_s=sum(x['load_s'] for tr in timing for x in tr['loads']),
            journal_wall_s=sum(tr['seconds'] for tr in timing),
            outer_minus_core_s=stats([r['seconds']-o['timings']['total_s'] for r,o in zip(rows,outs)]),
            rooms=len(set(r['room_key'] for r in rows)),
            finishes=dict(collections.Counter(o['finish'] for o in outs)))
        end = memos[-1] if memos else {}
        d['memo'] = dict(hits=end.get('hits',0)-last_hits, misses=end.get('misses',0)-last_misses,
                         held_bytes=end.get('held_bytes'), requested=end.get('requested'),
                         events=sum(len(m.get('events',[])) for m in memos))
        last_hits, last_misses = end.get('hits',0), end.get('misses',0)
        d['journal_unattributed_s'] = d['journal_wall_s']-d['seconds']['total']-d['factory_load_s']
        summary['types'][rows[0]['type']] = d
        summary['journals'].append(str(p));summary['rows'] += len(rows)
        flat.append(dict(package=package, type=rows[0]['type'], items=len(rows),
                         seconds_mean=d['seconds']['mean'], seconds_median=d['seconds']['median'],
                         seconds_p90=d['seconds']['p90'], tokens_mean=d['tokens_including_forced']['mean'],
                         chosen_tokens_mean=d['chosen_tokens']['mean'], calls_mean=d['calls']['mean'],
                         g3t_seconds_mean=d['timings'].get('g3t_s',stats([]))['mean'],
                         prefill_seconds_mean=d['timings']['prefill_s']['mean'],
                         factory_load_seconds=d['factory_load_s'], memo_hits=d['memo']['hits'],
                         memo_misses=d['memo']['misses']))
    steps = records(root/'STEPS.jsonl') if (root/'STEPS.jsonl').exists() else []
    if steps:
        summary['worker_start_to_exit_s'] = steps[-1]['utc']-steps[0]['utc']
        summary['outside_type_timers_s'] = summary['worker_start_to_exit_s']-sum(d['journal_wall_s'] for d in summary['types'].values())
    report['packages'][package] = summary

(L/'out/profile.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
with (L/'out/profile.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
print((L/'out/profile.csv').read_text())
for name,s in report['packages'].items():
    print(name, 'wall', s.get('worker_start_to_exit_s'), 'outside timers',s.get('outside_type_timers_s'))
    for kind,d in s['types'].items():
        print(kind, 'timings', {k:round(v['mean'],4) for k,v in d['timings'].items()},
              'families',d['call_families'],'outer-core',round(d['outer_minus_core_s']['mean'],4),
              'unattributed',round(d['journal_unattributed_s'],4),'rooms',d['rooms'],'memo',d['memo'])
