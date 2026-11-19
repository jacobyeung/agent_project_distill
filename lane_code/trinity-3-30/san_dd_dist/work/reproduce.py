#!/scratch/jjyeung/envs/planner_local_v1/bin/python
"""Reproduce the five numbers REPORT.md rests on (read-only; caches a pickle under /tmp/san_dd_dist).
Run: python3 /scratch/jjyeung/orch_n30/san_dd_dist/work/reproduce.py  (re-executes itself with the planner python)."""
import os, sys
PY = '/scratch/jjyeung/envs/planner_local_v1/bin/python'
if os.path.realpath(sys.executable) != os.path.realpath(PY) and not os.environ.get('SAN_DD_REEXEC'):
    os.environ['SAN_DD_REEXEC'] = '1'; os.execv(PY, [PY] + sys.argv)
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.makedirs('/tmp/san_dd_dist', exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dist_items import *
import numpy as np
d = load(); R = build(d); ids = sorted(i for (s, i) in R if s == 200)
X = {i: R[(200, i)] for i in ids}; Y = {i: R[(544, i)] for i in ids}
assert all(abs(mra(x['ans'], x['gt']) - x['score']) < 1e-9 for x in R.values()), 'scored truth does not reproduce'
def cf(x, rule):
    y = Y[x['id']]
    if rule == 'a': g = x['gap'] if x['called'] else (y['gap'] if y['called'] else None)
    elif rule == 'd': g = None if x['called'] else (y['gap'] if y['called'] else None)
    else: g = x['gap'] if (x['unit'] == 'cm' and x['called'] and usage(x) == 'metres') else None
    return mra(round(g * x['F'], 2), x['gt']) if g is not None else x['score']
M = lambda v: round(100 * float(np.mean(v)), 2)
print('1. distance, step 200: observed MRA %.2f with %d/150 calls; (a) all call + right conversion %.2f' % (M([x['score'] for x in X.values()]), sum(x['called'] for x in X.values()), M([cf(x, 'a') for x in X.values()])))
print('2. distance, step 200: (c) centimetre conversions only %.2f; (d) no-call items only %.2f' % (M([cf(x, 'c') for x in X.values()]), M([cf(x, 'd') for x in X.values()])))
nc = [x for x in X.values() if not x['called']]
rk = lambda v: np.argsort(np.argsort(v))
a = np.array([x['ans'] / x['F'] for x in nc]); t = np.array([x['gt_m'] for x in nc])
hit = tot = 0
for x in nc:
    gm = {g['obj'].lower(): g for g in Y[x['id']]['grounds'] if g['frames']}
    for o, f in re.findall(r'find the ([^,.]+?), first seen in frame (\d+)', x['text']):
        g = gm.get(o.strip().lower())
        if g: tot += 1; hit += int(f) in g['frames']
print('3. no-call answers vs truth (metres): Spearman %.2f on %d items; frame claims inside the step-544 ground frame list %d of %d' % (np.corrcoef(rk(a), rk(t))[0, 1], len(nc), hit, tot))
B5 = [c for r in d[('B', 544)] for c in r['calls']]
print('4. room, step 544 (134 items): unserved calls %d of %d; capped items %d' % (sum(c['served'] is False for c in B5), len(B5), sum(r['finish'] == 'max_calls' for r in d[('B', 544)])))
B2 = [r for r in d[('B', 200)] if not re.search(r'square (?:feet|foot)', r['question'], re.I)]
print('5. room, step 200: MRA %.1f on 134; square-metre answers below truth %d of %d' % (100 * np.mean([r['score'] for r in d[('B', 200)]]), sum(num(r['answer']) < float(r['gt']) for r in B2), len(B2)))
