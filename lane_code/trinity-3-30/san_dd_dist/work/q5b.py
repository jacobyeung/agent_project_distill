# Q5b: does disagreement between the step-200 direct estimate and the step-544 head gap flag head failures? (57 no-call items)
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
import numpy as np
d = load(); R = build(d); ids = sorted(i for (s, i) in R if s == 200)
P = [(R[(200, i)], R[(544, i)]) for i in ids if not R[(200, i)]['called'] and R[(544, i)]['gap'] is not None and R[(200, i)]['ans']]
print('items', len(P))
g = np.array([y['gap'] for x, y in P]); a = np.array([x['ans'] / x['F'] for x, y in P]); t = np.array([x['gt_m'] for x, y in P])
hm = np.array([mra(gg, tt) for gg, tt in zip(g, t)]); am = np.array([mra(aa, tt) for aa, tt in zip(a, t)])
ratio = np.abs(np.log(np.maximum(g, 0.01) / a))
print('head MRA %.1f, direct MRA %.1f, geometric mean MRA %.1f, oracle-best-of-two %.1f' % (100 * hm.mean(), 100 * am.mean(), 100 * np.mean([mra(np.sqrt(max(gg, .01) * aa), tt) for gg, aa, tt in zip(g, a, t)]), 100 * np.maximum(hm, am).mean()))
for thr in (np.log(1.5), np.log(2), np.log(3)):
    dis = ratio > thr
    rule = np.where(dis, am, hm)
    print('disagree > x%.1f: %d items; head MRA on them %.1f vs direct %.1f; on agreeing %d items head %.1f; rule (direct when disagree) %.1f' % (np.exp(thr), dis.sum(), 100 * hm[dis].mean() if dis.any() else 0, 100 * am[dis].mean() if dis.any() else 0, (~dis).sum(), 100 * hm[~dis].mean(), 100 * rule.mean()))
bad = hm == 0
print('head MRA=0 items %d: median |log ratio| %.2f vs others %.2f' % (bad.sum(), np.median(ratio[bad]), np.median(ratio[~bad])))
# gap-size rule on step-200 callers
xs = [R[(200, i)] for i in ids if R[(200, i)]['called'] and R[(200, i)]['gap'] is not None]
for c in (0.5, 1.0):
    lo = [x for x in xs if x['gap'] < c]
    print('step-200 callers with gap < %.1f m: %d; head MRA on them %.1f; head-MRA-0 among them %d of %d head-MRA-0 overall' % (c, len(lo), 100 * np.mean([mra(x['gap'], x['gt_m']) for x in lo]), sum(mra(x['gap'], x['gt_m']) == 0 for x in lo), sum(mra(x['gap'], x['gt_m']) == 0 for x in xs)))
