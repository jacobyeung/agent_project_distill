import sys, re, json, collections
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import numpy as np
def mra(p, g):
    e = abs(p - g) / abs(g); return sum(e <= 1 - t + 1e-9 for t in [0.5 + 0.05 * i for i in range(10)]) / 10.0
def auc(y, x):
    y = np.asarray(y, bool); x = np.asarray(x, float); p = x[y]; n = x[~y]
    return float(np.mean((p[:, None] > n[None, :]) + 0.5 * (p[:, None] == n[None, :])))
UNIT = [('centimeter', 100.0), ('centimetre', 100.0), ('feet', 3.28084), ('foot', 3.28084), ('inch', 39.3701), ('yard', 1.09361), ('meter', 1.0), ('metre', 1.0)]
def factor_old(q):
    m = re.search(r'\(in ([a-z]+)\)', q.lower()) or re.search(r'in (meters|metres|feet|inches|centimeters|centimetres|yards)', q.lower())
    w = m.group(1) if m else 'meter'
    for k, f in UNIT:
        if w.startswith(k[:4]): return f
    return 1.0
S = K._scorer().scorers
factor = S.unit_factor
first = True
for step in (544, 200):
    rows = K.routed(step, types=['object_abs_distance'])
    if first:
        r = rows[0]; print('keys', sorted(r.keys())); print('call keys', sorted(r['calls'][0].keys()) if r['calls'] else None); first = False
    ncall = sum(1 for r in rows if r['calls'])
    G = []
    for r in rows:
        gaps = [c for c in r['calls'] if c['family'] == 'gap']
        vals = []
        for c in gaps:
            m = re.search(r'(-?\d+(?:\.\d+)?)\s*m\b', c['response'] or '')
            v = S.printed(c)
            if v: vals.append((v['distance'], m.group(1) if m else None))
        if not vals: continue
        g = vals[-1][0]; t = float(r['gt']) / factor(r['question'])
        fs = [re.search(r'frames ([\d,]+) \(best', c['response'] or '') for c in r['calls'] if c['family'] == 'ground']
        rare = min(len(m.group(1).split(',')) for m in fs if m) if any(fs) else None
        G.append(dict(id=r['id'], g=g, t=t, err=abs(g - t) / t, rare=rare, n_ground=len(fs), q=r['question']))
    print('step', step, 'items', len(rows), 'callers', ncall, 'numeric gaps', len(G), 'wrong>.25', sum(x['err'] > .25 for x in G), 'wrong>.5', sum(x['err'] > .5 for x in G),
          'gap MRA %.2f' % (100 * np.mean([mra(x['g'], x['t']) for x in G])), 'unit factors', collections.Counter(round(factor(x['q']), 2) for x in G))
    R = [x for x in G if x['rare'] is not None]
    fl = [x for x in R if x['rare'] < 3]
    print('   rarer<3 flagged', len(fl), 'of', len(R), 'wrong .25', sum(x['err'] > .25 for x in fl), 'wrong .5', sum(x['err'] > .5 for x in fl),
          '| AUC(-gap) .25 %.3f .5 %.3f' % (auc([x['err'] > .25 for x in G], [-x['g'] for x in G]), auc([x['err'] > .5 for x in G], [-x['g'] for x in G])),
          '| AUC(-rare) .25 %.3f' % auc([x['err'] > .25 for x in R], [-x['rare'] for x in R]))
    for x in G:
        if x['id'] == 'vsi590k_161799': print('   cited', x)
n = sparse = 0; adm = collections.Counter()
for line in open('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/units/packed.jsonl'):
    r = json.loads(line); n += 1
    c = [len(f.split(',')) for f in re.findall(r'frames ([\d,]+) \(best', r['target'])]
    sparse += (min(c) < 3) if c else 0; adm[str(r.get('training_admitted'))] += 1
print('unit rows', n, 'sparse', sparse, 'training_admitted', dict(adm))
