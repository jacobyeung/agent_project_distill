"""Forecast of the NF-A job from job 171253's own per-read timings (return c82cb20f)."""
import json, statistics, sys
from pathlib import Path
ret = Path(sys.argv[1]); items = json.load(open(sys.argv[2])); out = Path(sys.argv[3])
J0 = ret/'metadata/reads/0/metadata/journals'; J1 = ret/'metadata/reads/1/metadata/journals'
mapping = {r['id']: r for r in json.load(open(J0/'3/0/item_mapping.json'))['items']}
cap = lambda i: (mapping[i]['native'], tuple(mapping[i]['anchor_indices']))
rows = {}
for t in range(5):
    for l in open(J0/f'{t}/0/items.jsonl'):
        r = json.loads(l); rows[(0, r['id'])] = r
for l in open(J1/'3/0/items.jsonl'):
    r = json.loads(l); rows[(1, r['id'])] = r
fresh = {}
for (rd, i), r in rows.items():
    g = r['output']['timings'].get('g3t_s', 0.0)
    if g > 1.0: fresh.setdefault(cap(i), []).append(g)
hit = statistics.median(r['output']['timings'].get('g3t_s', 0.0) for r in rows.values() if r['output']['timings'].get('g3t_s', 0.0) <= 1.0)
first0 = json.loads(open(J0/'3/0/items.jsonl').readline())
warm = first0['seconds'] - statistics.median(rows[(1, i)]['seconds'] for i in items['forward_ids'] if (1, i) in rows)
def base(i):
    # distance runs best candidate: read 1 timings; camera: read 0 timings
    r = rows[(1, i)] if (1, i) in rows else rows[(0, i)]
    return r['seconds'] - r['output']['timings'].get('g3t_s', 0.0)
def order_seconds(ids):
    seen, total = set(), 0.0
    for i in ids:
        c = cap(i)
        total += base(i) + (statistics.median(fresh[c]) if c not in seen else hit)
        seen.add(c)
    return total, len(seen)
f, nf = order_seconds(items['forward_ids']); r, nr = order_seconds(items['reverse_ids'])
staging, load, publish = 378.0, 100.0, 30.0
reads = f + r + 2 * (load + warm)
job = staging + reads + publish
limit = staging + 1.5 * reads + 1800 + publish
value = dict(forward_read_seconds=f, reverse_read_seconds=r, captures=nf, warmup_seconds=warm,
             load_seconds=load, staging_seconds=staging, publish_seconds=publish, hit_g3t_seconds=hit,
             expected_job_seconds=job, expected_h100_hours=job/3600,
             limit_seconds_at_1_5_plus_stop_margin=limit,
             basis='171253 per-read seconds: camera from read 0 (memo on), distance from read 1 (best candidate); '
                   'G3T fresh cost per capture from its own fresh calls; staging 378 s and load 100 s as measured in 171253')
out.write_text(json.dumps(value, indent=1) + '\n'); print(json.dumps(value, indent=1))
