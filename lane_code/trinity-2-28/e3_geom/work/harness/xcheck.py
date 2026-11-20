"""Compare integrated-run per-capture items (out/captures) with shard items (out_tr, out_ho)."""
import json, glob, os
n = same = 0; diffs = []
for p in sorted(glob.glob('out/captures/*.json')):
    name = os.path.basename(p)
    q = next((d + '/' + name for d in ('out_tr', 'out_ho') if os.path.exists(d + '/' + name)), None)
    if q is None: diffs.append((name, 'no shard file')); continue
    a = {(r['row_id'], r['arm']): (r['pred'], r['refusal_code']) for r in json.load(open(p))['items']}
    b = {(r['row_id'], r['arm']): (r['pred'], r['refusal_code']) for r in json.load(open(q))['items']}
    n += 1
    if a == b: same += 1
    else: diffs.append((name, sum(1 for k in a if a.get(k) != b.get(k)), len(a)))
print(f'captures compared {n}, identical {same}'); print(diffs[:10])
