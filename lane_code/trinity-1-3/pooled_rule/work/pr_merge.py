"""Merge pr_sim.py outputs: estimated false-stop probability and power of the pooled rule (three variants) and of the
card's dev-S1 rule on the same pseudo-reads.  usage: pr_merge.py ARM OUT.json"""
import sys, json, glob, math
import numpy as np
ARM = sys.argv[1]
F = sorted(glob.glob('sim_%s_seed1??.npz' % ARM))
Z = [np.load(f) for f in F]
cat = lambda k: np.concatenate([z[k] for z in Z])
ub, est, mub, mest, sub, sest, smub, smest = [cat(k) for k in ('ub', 'est', 'mub', 'mest', 'sub', 'sest', 'smub', 'smest')]
n = len(ub)
T8 = ('counting', 'direction_easy', 'direction_medium', 'direction_hard', 'rel_distance', 'object_size', 'route_planning(dev-S1 only)',
      'appearance_order(R0-dev only)')
TS = ('counting', 'direction_easy', 'direction_medium', 'direction_hard', 'rel_distance', 'object_size', 'route_planning')
V = ('item', 'equal', 'unstrat')
WI = Z[0]['W_item']
W = {'item': WI, 'equal': np.full(6, 0.5), 'unstrat': WI}


def rate(x):
    p = float(np.mean(x))
    return [round(p, 4), round(math.sqrt(max(p * (1 - p), 1e-12) / len(x)), 4)]


def pack(U, m, t=None):
    ty = U < 0
    d = dict(H1=rate(ty.any(1)), H2=rate(m < 0), stop=rate(ty.any(1) | (m < 0)))
    if t is not None:
        d['type_alone'] = rate(ty[:, t])
    return d


LOOK = {'step200': (0, 0), 'later': (1, 1)}       # (type level index, mean level index)
out = dict(arm=ARM, files=F, outer=n, inner=int(Z[0]['INN']), rooms=[int(Z[0]['KS']), int(Z[0]['KR'])],
           item_weights_devS1=[round(float(x), 4) for x in WI], types=T8,
           observed_delta_pp=dict(devS1=dict(zip(TS, (100 * Z[0]['deltaS']).round(2).tolist())),
                                  R0dev=dict(zip(T8[:6] + T8[7:], (100 * Z[0]['deltaR']).round(2).tolist()))),
           pooled_mean_score=dict(devS1=Z[0]['pmS'].round(4).tolist(), R0dev=Z[0]['pmR'].round(4).tolist()))
res = {}
for v, name in enumerate(V):
    w = W[name]
    r = {}
    for look, (L, ml) in LOOK.items():
        q = {}
        X = ub[:, v, 1, :, L]
        C = ub[:, v, 0, :, L]
        q['no change (exchange)'] = pack(X, mub[:, v, 1, ml])
        q['no change (exchange) per type'] = [rate(X[:, t] < 0)[0] for t in range(8)]
        q['no change (centred, D0 noise)'] = pack(C, mub[:, v, 0, ml])
        # (a) D0's size loss: dev-S1 -9.5, R0-dev -4.3
        U = X.copy(); U[:, 5] = ub[:, v, 6, 5, L]
        q['a: size loss dev-S1 9.5 + R0-dev 4.3 (flips)'] = pack(U, mub[:, v, 11, ml], 5)
        sh = -(w[5] * 0.095 + (1 - w[5]) * 0.043)
        for nm, base, mb in (('exchange', X, mub[:, v, 1, ml]), ('centred, D0 noise', C, mub[:, v, 0, ml])):
            U = base.copy(); U[:, 5] += sh
            q['a: size loss dev-S1 9.5 + R0-dev 4.3 (shift on %s)' % nm] = pack(U, mb + sh / 8, 5)
        # (b) 9.5 on one type, both sets
        for t in range(8):
            U = X.copy(); U[:, t] = ub[:, v, 2, t, L]
            q['b: loss 9.5 on %s (flips)' % T8[t]] = pack(U, mub[:, v, 2 + t, ml], t)
        for t in range(6):
            U = X.copy(); U[:, t] = ub[:, v, 3, t, L]
            q['dilution: loss 9.5 on %s, dev-S1 only (flips)' % T8[t]] = pack(U, mub[:, v, 12 + t, ml], t)
            U = X.copy(); U[:, t] = ub[:, v, 4, t, L]
            q['dilution: loss 9.5 on %s, R0-dev only (flips)' % T8[t]] = pack(U, mub[:, v, 18 + t, ml], t)
        # (c) uniform 2
        q['c: uniform loss 2 (flips)'] = pack(ub[:, v, 5, :, L], mub[:, v, 10, ml])
        q['c: uniform loss 2 (shift on exchange)'] = pack(X - 0.02, mub[:, v, 1, ml] - 0.02)
        for c in (0.03, 0.04):
            q['uniform loss %d, H2 alone (shift on exchange)' % round(100 * c)] = rate(mub[:, v, 1, ml] - c < 0)
        for c in (0.03, 0.06):
            for nm, base in (('exchange', X), ('centred', C)):
                q['size drift %d on both sets, size test alone (shift on %s)' % (round(100 * c), nm)] = rate(base[:, 5] - c < 0)
        r[look] = q
    r['null_sd_pp'] = (100 * est[:, v, 1].std(0)).round(2).tolist()
    r['null_mean8_sd_pp'] = round(float(100 * mest[:, v, 1].std()), 3)
    r['realised a: size estimate mean/sd pp'] = [round(float(100 * est[:, v, 6, 5].mean()), 2), round(float(100 * est[:, v, 6, 5].std()), 2)]
    res['pooled_' + name] = r
# the card's dev-S1 rule
r = {}
for look, (L, ml) in LOOK.items():
    q = {}
    X = sub[:, 1, :, L]
    C = sub[:, 0, :, L]
    q['no change (exchange)'] = pack(X, smub[:, 1, ml])
    q['no change (exchange) per type'] = [rate(X[:, t] < 0)[0] for t in range(7)]
    q['no change (centred, D0 noise)'] = pack(C, smub[:, 0, ml])
    for t in range(7):
        U = X.copy(); U[:, t] = sub[:, 2, t, L]
        key = 'a: size loss dev-S1 9.5 + R0-dev 4.3 (flips)' if t == 5 else 'b: loss 9.5 on %s (flips)' % TS[t]
        q[key] = pack(U, smub[:, 2 + t, ml], t)
    for nm, base, mb in (('exchange', X, smub[:, 1, ml]), ('centred, D0 noise', C, smub[:, 0, ml])):
        U = base.copy(); U[:, 5] -= 0.095
        q['a: size loss dev-S1 9.5 + R0-dev 4.3 (shift on %s)' % nm] = pack(U, mb - 0.095 / 7, 5)
    q['b: loss 9.5 on appearance_order(R0-dev only) (flips)'] = pack(X, smub[:, 1, ml])
    q['dilution: any loss on R0-dev only'] = pack(X, smub[:, 1, ml])
    q['c: uniform loss 2 (flips)'] = pack(sub[:, 3, :, L], smub[:, 9, ml])
    q['c: uniform loss 2 (shift on exchange)'] = pack(X - 0.02, smub[:, 1, ml] - 0.02)
    for c in (0.03, 0.04):
        q['uniform loss %d, H2 alone (shift on exchange)' % round(100 * c)] = rate(smub[:, 1, ml] - c < 0)
    for c in (0.03, 0.06):
        for nm, base in (('exchange', X), ('centred', C)):
            q['size drift %d on both sets, size test alone (shift on %s)' % (round(100 * c), nm)] = rate(base[:, 5] - c < 0)
    r[look] = q
r['null_sd_pp'] = (100 * sest[:, 1].std(0)).round(2).tolist()
r['null_mean7_sd_pp'] = round(float(100 * smest[:, 1].std()), 3)
res['devS1_rule'] = r
out['results'] = res
json.dump(out, open(sys.argv[2], 'w'), indent=1)
# compact table
keys = [k for k in res['pooled_item']['step200'] if not k.endswith('per type')]
for look in LOOK:
    print('==', look, '| stop probability [estimate, MC se]: devS1_rule | pooled_item | pooled_equal | pooled_unstrat')
    for k in keys:
        row = []
        for nm in ('devS1_rule', 'pooled_item', 'pooled_equal', 'pooled_unstrat'):
            x = res[nm][look].get(k)
            row.append('-' if x is None else ('%.3f' % x['stop'][0] if isinstance(x, dict) else '%.3f' % x[0]))
        print('%-78s %s' % (k[:78], '  '.join(row)))
for nm in res:
    print(nm, 'null sd pp', res[nm]['null_sd_pp'], 'H1/H2 null step200', res[nm]['step200']['no change (exchange)'],
          'later', res[nm]['later']['no change (exchange)'])
