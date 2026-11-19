# Q1: per unit and per wording at both steps: items, calls, gap printed, conversion written/right, answer follows, MRA.
import sys, json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
from collections import Counter, defaultdict
d = load(); R = build(d)
def conv_ok(x):
    """(written, right): a 'Converting to' line exists; right = line's g equals printed gap, factor within 0.1%, product within 0.011, answer = product."""
    if not x['conv']: return False, False
    u, gw, fw, yw = x['conv'][-1]
    try: gw, fw, yw = float(gw), float(fw), float(yw)
    except ValueError: return True, False
    ok = x['gap'] is not None and abs(gw - x['gap']) <= 0.005 and abs(fw / x['F'] - 1) < 1e-3 and abs(yw - gw * fw) <= max(0.011, 5e-4 * abs(yw)) and x['ans'] is not None and abs(x['ans'] - yw) <= 0.011
    return True, ok
def exact_place(x):
    e = [sc.signature(c) for c in expected_calls(x['q'], 'object_abs_distance')]
    return [sc.signature(c) for c in x['calls']] == e
def row(xs):
    n = len(xs); c = [x for x in xs if x['called']]; g = [x for x in c if x['gap'] is not None]
    nm = [x for x in g if x['unit'] != 'm']
    cw = sum(conv_written(x) for x in nm); cr = sum(conv_right(x) for x in nm)
    silent = sum(usage(x) == 'follows' and not conv_written(x) for x in nm)
    fol = sum(usage(x) == 'follows' for x in g)
    return dict(n=n, calls=len(c), exact=sum(exact_place(x) for x in c), gap=len(g), nonm_gap=len(nm), conv_written=cw, conv_right=cr,
                silent=silent, follows=fol, metres=sum(usage(x) == 'metres' for x in g), other=sum(usage(x) == 'other' for x in g),
                mra=round(100 * sum(x['score'] for x in xs) / n, 1) if n else None)
out = {}
for key in ('unit', 'tmpl'):
    for step in (544, 200):
        groups = defaultdict(list)
        for (s, i), x in R.items():
            if s == step: groups[x[key]].append(x)
        out[(key, step)] = {k: row(v) for k, v in groups.items()}
        out[(key, step)]['ALL'] = row([x for (s, i), x in R.items() if s == step])
hdr = 'n calls exact gap nonm_gap conv_written conv_right silent follows metres other mra'.split()
for step in (544, 200):
    print('== step', step, 'by unit:', ' '.join(hdr))
    for u in ('m', 'ft', 'in', 'cm', 'ALL'): print(' ', u, [out[('unit', step)][u][h] for h in hdr])
T = sorted(out[('tmpl', 200)], key=lambda t: -out[('tmpl', 200)][t]['n'])
print('== by wording (544 | 200): n, calls, gap, follows, mra')
for t in T:
    if t == 'ALL': continue
    a, b = out[('tmpl', 544)][t], out[('tmpl', 200)][t]
    us = Counter(x['unit'] for (s, i), x in R.items() if s == 200 and x['tmpl'] == t)
    print('%-3d 544[%d %d %d %5.1f] 200[%d %d %d %5.1f] %s | %s' % (a['n'], a['calls'], a['gap'], a['follows'], a['mra'], b['calls'], b['gap'], b['follows'], b['mra'], dict(us), t[:70]))
json.dump({'%s|%s' % k: v for k, v in out.items()}, open('/scratch/jjyeung/orch_n30/san_dd_dist/work/q1_tables.json', 'w'), indent=0)
