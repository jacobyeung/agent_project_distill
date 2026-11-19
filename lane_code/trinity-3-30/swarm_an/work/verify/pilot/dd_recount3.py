import sys, re, json, collections
sys.dont_write_bytecode = True
sys.path.insert(0, "/scratch/jjyeung/orch_n30/swarm_an/kit")
import san_kit as K
import numpy as np
def mra(p, g):
    e = abs(p - g) / abs(g); return sum(e < 1 - t for t in np.arange(.50, 1., .05)) / 10.0
S = K._scorer().scorers
for step in (544, 200):
    rows = K.routed(step, types=['object_abs_distance']); base = []; ceil = []; mb = []; mc = []
    for r in rows:
        vals = [S.printed(c) for c in r['calls'] if c['family'] == 'gap']; vals = [v['distance'] for v in vals if v]
        t = float(r['gt']) / S.unit_factor(r['question']); metre = abs(S.unit_factor(r['question']) - 1.0) < 1e-9
        fs = [re.search(r'frames ([\d,]+) \(best', c['response'] or '') for c in r['calls'] if c['family'] == 'ground']
        if vals and len(fs) == 2 and all(fs):
            b = mra(vals[-1], t); rare = min(len(m.group(1).split(',')) for m in fs); c = 1.0 if rare < 3 else b
        else:
            b = c = r['score']
        base.append(b); ceil.append(c)
        if metre: mb.append(b); mc.append(c)
    print(step, 'all 150: measurement baseline %.2f, truth on flagged %.2f | metre items %d: %.2f -> %.2f | observed %.2f' % (100 * np.mean(base), 100 * np.mean(ceil), len(mb), 100 * np.mean(mb), 100 * np.mean(mc), 100 * np.mean([r['score'] for r in rows])))
