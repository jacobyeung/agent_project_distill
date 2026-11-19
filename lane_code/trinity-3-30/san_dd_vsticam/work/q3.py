# Q3 priors a trace could state truthfully (1,500 sampled rows per camera family) + Q4 margins + Q7 near-ties. numpy python.
import sys, json, random, math
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
R = rows(); drop = dropped(); counts = json.load(open(T + '/counts.json'))
def feats(r):
    labs = [x['label'] for x in r['inst']]; opts = [o.split('. ', 1)[1] for o in r['opts']]
    k = r['k']; fl = r['floor'] or 0.002; X = []
    fsr = sorted(r['fs'][o] for o in opts)
    for o in opts:
        f = r['fs'][o]; s = r['share'][o]; sz = size(o, False)[0]
        X.append([float(s >= fl), math.log(s + 1e-3), abs(f - k) / 32, float(f > k), float(f == k),
                  math.log(sz) if sz else 0.0, float(sz is None), fsr.index(f) / 3])
    return opts, np.array(X), opts.index(labs[0])
def fit(data, l2=1e-2, it=400, lr=0.5):
    w = np.zeros(data[0][0].shape[1])
    for _ in range(it):
        g = -l2 * w
        for X, y in data:
            z = X @ w; p = np.exp(z - z.max()); p /= p.sum(); g += X[y] - p @ X
        w += lr * g / len(data)
    return w
print('family | rule: covered / hits (pct)')
for fam in CAM:
    rs = R[fam][:]; random.Random(1500).shuffle(rs); rs = rs[:1500]
    c = Counter(); data = []
    for r in rs:
        opts, X, y = feats(r); n = len(opts); fl = r['floor'] or 0.002
        sh = [r['share'][o] for o in opts]; fs = [r['fs'][o] for o in opts]
        sz = [size(o, False)[0] for o in opts]
        if all(sz): c['large cov'] += 1; c['large hit'] += sz.index(max(sz)) == y
        c['share hit'] += sh.index(max(sh)) == y; c['share untied cov'] += sh.count(max(sh)) == 1
        c['share hit|untied'] += (sh.count(max(sh)) == 1 and sh.index(max(sh)) == y)
        iv = [j for j in range(n) if sh[j] >= fl]
        c['in-view count %d' % len(iv)] += 1
        if len(iv) == 1: c['only cov'] += 1; c['only hit'] += iv[0] == y
        dk = [abs(f - r['k']) for f in fs]; c['neark hit'] += dk.index(min(dk)) == y
        c['early hit'] += fs.index(min(fs)) == y
        cn = counts.get(r['scene'], {})
        if all(o.lower() in cn for o in opts): c['inst cov'] += 1
        c['kept'] += r['qid'] not in drop
        data.append((X, y))
    tr, te = data[0::2], data[1::2]
    w = fit(tr); hit = sum(int(np.argmax(X @ w) == y) for X, y in te)
    w2 = fit(te); hit2 = sum(int(np.argmax(X @ w2) == y) for X, y in tr)
    print(fam[-2:], 'n 1500 kept', c['kept'],
          '| largest(v7 medians) %d/%d' % (c['large hit'], c['large cov']),
          '| largest share %d/1500 (untied %d, hit %d)' % (c['share hit'], c['share untied cov'], c['share hit|untied']),
          '| only in view %d/%d' % (c['only hit'], c['only cov']),
          '| first-seen nearest k %d/1500' % c['neark hit'], '| earliest %d/1500' % c['early hit'],
          '| most instances: rows with counts for all candidates %d' % c['inst cov'],
          '| combo fit A->B %d/750, B->A %d/750' % (hit, hit2), '| in-view counts', {k2: v for k2, v in c.items() if k2.startswith('in-view')})
    print('   weights [inview, logshare, |f-k|, f>k, f==k, logsize, size_missing, fs_rank]', np.round(w, 2).tolist())
# Q4 margins and Q7 near-ties on all rows of each family
for fam in CAM:
    rat = []; near = 0; n = 0
    for r in R[fam]:
        g = r['gv']; rat.append(g[1] / g[0] if g[0] > 0 else float('inf')); near += g[0] < 0.5; n += 1
    print(fam[-2:], 'rows', n, 'ratio 2nd/1st under 1.05/1.1/1.25/1.5/2:', [sum(x < t for x in rat) for t in (1.05, 1.1, 1.25, 1.5, 2)],
          'nearest < 0.5 m', near, 'nearest == 0', sum(r['gv'][0] == 0 for r in R[fam]), 'median nearest %.2f' % sorted(r['gv'][0] for r in R[fam])[n // 2])
