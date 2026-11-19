"""Q5: can one 2-D layout satisfy every stated relation of a room?  Fits object positions to (truth | step-200 answers | step-544 answers | random answers)
for all R0-dev direction items (toward and away) of a room.  Run with /scratch/jjyeung/envs/planner_local_v1/bin/python."""
import sys, re, collections, json, math
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import *
QA = re.compile(r"standing by the (.+?) and facing (away from )?the (.+?), is the (.+?) to (?:the |my )", re.I)
IV = {'left': [(0, 180)], 'right': [(-180, 0)]}
IVM = {'left': [(0, 135)], 'right': [(-135, 0)], 'back': [(135, 180), (-180, -135)]}
IVH = {'front-left': [(0, 90)], 'front-right': [(-90, 0)], 'back-left': [(90, 180)], 'back-right': [(-180, -90)]}
def ivs(lv, rel): return (IV if lv == 'easy' else IVM if lv == 'medium' else IVH)[rel]
def items_by_room(st=200):
    D = {s: {r['id']: r for r in K.direct(run, s, 'R0-dev', types=T)} for run, s in (('S1', 544), ('R1', 100), ('R1', 200))}
    R = collections.defaultdict(list)
    for i, r in D[200].items():
        m = QA.search(r['question'])
        if not m: continue
        R[r['room']].append(dict(id=i, lv=LV[r['type']], away=bool(m.group(2)), o=m.group(1).lower(), f=m.group(3).lower(), t=m.group(4).lower(),
                                 truth=opt(r, r['gt']), a200=opt(r, r['pred']), a100=opt(D[100][i], D[100][i]['pred']), a544=opt(D[544][i], D[544][i]['pred']),
                                 opts=[x.split('.', 1)[1].strip().lower() for x in r['options']], sub=r['subtype']))
    return R
def viol(P, its, rels, idx):
    tot = 0.0; per = []
    for it, rel in zip(its, rels):
        A, B, C = P[idx[it['o']]], P[idx[it['f']]], P[idx[it['t']]]
        h = (A - B) if it['away'] else (B - A); v = C - A
        th = math.degrees(math.atan2(h[0] * v[1] - h[1] * v[0], h[0] * v[0] + h[1] * v[1]))
        d = min((0 if lo + 2 <= th <= hi - 2 else min(abs(th - lo - 2), abs(th - hi + 2))) for lo, hi in ivs(it['lv'], rel))
        per.append(d); tot += d
    return tot, per
def fit(its, rels, restarts=40, steps=1500, seed=0):
    names = sorted({n for it in its for n in (it['o'], it['f'], it['t'])}); idx = {n: k for k, n in enumerate(names)}
    rng = np.random.default_rng(seed); best = None
    for _ in range(restarts):
        P = rng.normal(size=(len(names), 2)) * 3; L, per = viol(P, its, rels, idx)
        for s in range(steps):
            if L == 0: break
            k = rng.integers(len(names)); Q = P.copy(); Q[k] += rng.normal(size=2) * (1.5 if s < steps // 2 else 0.4)
            L2, per2 = viol(Q, its, rels, idx)
            if L2 <= L: P, L, per = Q, L2, per2
        sat = sum(1 for d in per if d == 0)
        if best is None or sat > best[0]: best = (sat, L)
        if L == 0: break
    return best[0]
if __name__ == '__main__':
    R = items_by_room(); rooms = sys.argv[1:] or None
    out = {}
    for room, its in sorted(R.items()):
        if rooms and not any(room.startswith(x) for x in rooms): continue
        n = len(its); res = {}
        for k in ('truth', 'a200', 'a544'):
            res[k] = fit(its, [it[k] for it in its])
        rng = np.random.default_rng(3); rs = []
        for b in range(8):
            rels = [it['opts'][rng.integers(len(it['opts']))] for it in its]; rs.append(fit(its, rels, restarts=15, steps=1000, seed=b))
        res['random_all_sat'] = sum(1 for x in rs if x == n); res['n'] = n
        res['wrong200'] = sum(it['a200'] != it['truth'] for it in its); res['wrong544'] = sum(it['a544'] != it['truth'] for it in its)
        out[room] = res
        print(room[:6], json.dumps(res), flush=True)
    json.dump(out, open('layout_fit.json' if not rooms else 'layout_fit_top.json', 'w'))
