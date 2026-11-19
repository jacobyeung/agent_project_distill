import sys, json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import defaultdict
def table(old, new, label):
    out = {}
    m = {r['id']: r for r in old}
    by = defaultdict(list)
    for r in new: by[r['type']].append(r)
    for t, rs in sorted(by.items()):
        n = len(rs); s2 = sum(r['score'] for r in rs) / n * 100
        os_ = [m[r['id']] for r in rs if r['id'] in m]
        s5 = sum(o['score'] for o in os_) / len(os_) * 100 if os_ else None
        wrong = sum(1 for r in rs if r['score'] < 1); lost = sum(1 - r['score'] for r in rs) / n * 100
        fc = [r for r in rs if r['forced_close']]; fcl = sum(1 - r['score'] for r in fc) / n * 100
        rw = sum(1 for r in rs if r['id'] in m and m[r['id']]['score'] >= 1 and r['score'] < 1)
        wr = sum(1 for r in rs if r['id'] in m and m[r['id']]['score'] < 1 and r['score'] >= 1)
        out[t] = dict(n=n, s544=None if s5 is None else round(s5, 2), s200=round(s2, 2), wrong200=wrong, lost_pts=round(lost, 2),
                      forced=len(fc), forced_lost_pts=round(fcl, 2), right_to_wrong=rw, wrong_to_right=wr)
        print('%-9s %-30s n=%3d 544=%6s 200=%6.2f d=%+6.2f wrong=%3d forced=%3d(cost %5.2f) R>W=%3d W>R=%3d' % (label, t, n, '%.2f' % s5 if s5 is not None else '-', s2, (s2 - s5) if s5 is not None else 0, wrong, len(fc), fcl, rw, wr))
    return out
res = {}
res['dev-S1'] = table(K.direct('S1', 544, 'dev-S1'), K.direct('R1', 200, 'dev-S1'), 'dev-S1')
res['R0-dev'] = table(K.direct('S1', 544, 'R0-dev'), K.direct('R1', 200, 'R0-dev'), 'R0-dev')
for tw in ('away', 'forward'):
    res[tw] = table(K.facing('S1', 544, tw), K.facing('R1', 200, tw), tw)
res['vsti'] = table(K.vsti('S1', 544), K.vsti('R1', 200), 'vsti')
json.dump(res, open('OVERVIEW_m200.json', 'w'), indent=1)
# subtype split on R0-dev
new = K.direct('R1', 200, 'R0-dev'); old = {r['id']: r for r in K.direct('S1', 544, 'R0-dev')}
d = defaultdict(lambda: [0, 0.0, 0.0])
for r in new:
    x = d[(r['type'], r['subtype'])]; x[0] += 1; x[1] += r['score']; x[2] += old[r['id']]['score']
for k, v in sorted(d.items()): print('R0-dev', k, v[0], '544=%.1f 200=%.1f' % (100 * v[2] / v[0], 100 * v[1] / v[0]))
