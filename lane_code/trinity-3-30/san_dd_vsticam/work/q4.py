# Q4: proxy head errors (gap head from routed object_abs_distance, camera head from routed camera_displacement at step 200) and a simulated routed form
import sys, json, re, math, random
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
U = {'feet': 0.3048, 'meters': 1.0, 'inches': 0.0254, 'centimeters': 0.01, None: 1.0}
A = K.routed(200, types=['object_abs_distance']); C = K.routed(200, types=['camera_displacement'])
gap = []; byroom = defaultdict(list); units = Counter()
for r in A:
    g = [c for c in r['calls'] if c['family'] == 'gap' and c['served']]
    if not g: continue
    m = re.search(r'distance ([\d.]+) m', g[0]['response'] or '')
    u = re.search(r'(centimeters|meters|feet|inches)', r['question']); u = u.group(1) if u else None
    units[u] += 1
    if not m: continue
    t = float(r['gt']) * U[u]; p = float(m.group(1))
    if t > 0 and p > 0:
        e = math.log(p / t); gap.append(e); byroom[r['room']].append(e)
cam = []
for r in C:
    g = [c for c in r['calls'] if c['family'] == 'move' and c['served']]
    m = re.search(r'distance = ([\d.]+) m', (g[0]['response'] or '') if g else '')
    if m and float(r['gt']) > 0 and float(m.group(1)) > 0:
        cam.append(math.log(float(m.group(1)) / float(r['gt'])))
print('gap items by question unit', dict(units))
for nm, e in (('gap', gap), ('camera move', cam)):
    a = np.array(e)
    print(nm, 'served n', len(a), 'median |ratio-1| %.3f' % np.median(np.abs(np.exp(a) - 1)), 'sd log %.3f' % a.std(),
          'share within 10pct %.2f, 25pct %.2f' % (np.mean(np.abs(np.exp(a) - 1) < 0.1), np.mean(np.abs(np.exp(a) - 1) < 0.25)), 'mean log %.3f' % a.mean())
grp = [v for v in byroom.values() if len(v) >= 2]
within = [x - np.mean(v) for v in grp for x in v]; allv = [x for v in grp for x in v]
print('gap rooms with >=2 served items', len(grp), 'items', len(allv), 'sd all %.3f, sd within room %.3f' % (np.std(allv), np.std(within)))
R = rows(); rng = np.random.default_rng(7)
def sim(fam, errs, mode, B=20):
    hits = 0; n = 0; errs = np.array(errs); w = np.array(within)
    for r in R[fam]:
        d = np.array(r['gv'])
        for _ in range(B):
            if mode == 'independent': e = rng.choice(errs, size=len(d))
            elif mode == 'shared': e = np.repeat(rng.choice(errs), len(d))
            else: e = np.repeat(rng.choice(errs), len(d)) + rng.choice(w, size=len(d))
            hits += int(np.argmin(d * np.exp(e)) == 0); n += 1
    return 100 * hits / n
for fam in CAM:
    print(fam[-2:], 'routed accuracy with gap-head errors: independent %.1f | one shared scale %.1f | shared + within-room residual %.1f' % (
        sim(fam, gap, 'independent'), sim(fam, gap, 'shared'), sim(fam, gap, 'mixed')),
        '| camera-head errors independent %.1f' % sim(fam, cam, 'independent'))
