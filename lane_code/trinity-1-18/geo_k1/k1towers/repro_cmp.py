"""Compare this lane's reference arms (GT, S4+G1, SO+G1; distance, room R0/R1) item by item with E3's per-capture rows.
Usage: python3 repro_cmp.py MY_CAPTURES_DIR E3_CAPTURES_DIR OUT.json"""
import json, sys, glob, os
mine, e3, out = sys.argv[1:4]
arms = {'GT', 'GT+R0', 'GT+R1', 'S4+G1', 'S4+G1+R0', 'S4+G1+R1', 'SO+G1', 'SO+G1+R0', 'SO+G1+R1'}
n = same = 0; diffs = []; missing_e3 = []
for p in sorted(glob.glob(mine + '/*.json')):
    q = os.path.join(e3, os.path.basename(p))
    if not os.path.isfile(q):
        missing_e3.append(os.path.basename(p)); continue
    a = {(r['row_id'], r['arm']): r for r in json.load(open(p))['items'] if r['arm'] in arms}
    b = {(r['row_id'], r['arm']): r for r in json.load(open(q))['items'] if r['arm'] in arms}
    for k in sorted(set(a) | set(b)):
        n += 1
        x, y = a.get(k), b.get(k)
        if x and y and x['pred'] == y['pred'] and x['mra'] == y['mra'] and x['refusal_code'] == y['refusal_code']:
            same += 1
        else:
            diffs.append(dict(key=k, mine=x and {f: x[f] for f in ('pred', 'mra', 'refusal_code')},
                              e3=y and {f: y[f] for f in ('pred', 'mra', 'refusal_code')}))
res = dict(captures=len(glob.glob(mine + '/*.json')), items_compared=n, identical=same, differing=len(diffs),
           missing_in_e3=missing_e3, first_diffs=diffs[:30], verdict='IDENTICAL' if n and same == n and not missing_e3 else 'DIFFERS')
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'first_diffs'}), json.dumps(diffs[:5]))
