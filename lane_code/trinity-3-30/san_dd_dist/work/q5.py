# Q5: can the response text separate failed/implausible head outputs from good ones? Features vs head error, both steps.
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
from collections import defaultdict
import numpy as np
d = load(); R = build(d)
cls = defaultdict(list)
for (s, i), x in R.items():
    for g in x['grounds']:
        if g['size']: cls[g['obj'].lower()].append((s, i, max(g['size'])))
def feats(x):
    a, b = x['grounds']; sa, sb = np.array(a['size']), np.array(b['size']); ca, cb = np.array(a['centre']), np.array(b['centre'])
    dc = float(np.linalg.norm(ca - cb)); lo = dc - (np.linalg.norm(sa) + np.linalg.norm(sb)) / 2
    def plaus(g):
        o = [m for (s, i, m) in cls[g['obj'].lower()] if (s, i) != (x['step'], x['id'])]
        return max(g['size']) / np.median(o) if len(o) >= 3 else np.nan
    pa, pb = plaus(a), plaus(b)
    return dict(nfr_min=min(len(a['frames']), len(b['frames'])), nfr_sum=len(a['frames']) + len(b['frames']),
                maxdim_min=min(sa.max(), sb.max()), vol_min=min(sa.prod(), sb.prod()), gap=x['gap'], gap_small=float(x['gap'] < 0.1),
                centre_dist=dc, gap_over_centre=x['gap'] / dc if dc else np.nan, gap_below_lowerbound=float(x['gap'] < lo - 0.05),
                gap_above_centre=float(x['gap'] > dc + 0.05), size_vs_class=np.nanmax([abs(np.log(pa)) if pa == pa else np.nan, abs(np.log(pb)) if pb == pb else np.nan]),
                best_gap=abs(a['best'] - b['best']), scale=x['scale'] or np.nan, overlap_frames=len(set(a['frames']) & set(b['frames'])))
def auc(pos, neg):
    pos = [p for p in pos if p == p]; neg = [n for n in neg if n == n]
    if not pos or not neg: return np.nan
    return np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg])
for step in (200, 544):
    xs = [x for (s, i), x in sorted(R.items()) if s == step and x['called'] and x['gap'] is not None and all(g['size'] for g in x['grounds'])]
    for x in xs: x['herr'] = abs(x['gap'] - x['gt_m']) / x['gt_m']; x['hmra'] = mra(x['gap'], x['gt_m']); x['f'] = feats(x)
    xs.sort(key=lambda x: x['herr']); best, worst = xs[:20], xs[-20:]
    bad = [x for x in xs if x['hmra'] == 0]; good = [x for x in xs if x['hmra'] >= 0.8]
    print('== step %d: callers with numeric gap and two boxes %d; head MRA %.1f; head MRA=0: %d; >=0.8: %d' % (step, len(xs), 100 * np.mean([x['hmra'] for x in xs]), len(bad), len(good)))
    print('   %-20s %10s %10s %8s %8s' % ('feature', 'best20', 'worst20', 'AUC b/g', 'rho_err'))
    for k in xs[0]['f']:
        e = np.array([x['herr'] for x in xs]); v = np.array([x['f'][k] for x in xs], float); ok = ~np.isnan(v)
        rk = lambda z: np.argsort(np.argsort(z))
        rho = np.corrcoef(rk(v[ok]), rk(e[ok]))[0, 1] if ok.sum() > 3 and np.std(v[ok]) > 0 else np.nan
        print('   %-20s %10.3f %10.3f %8.2f %8.2f' % (k, np.nanmean([x['f'][k] for x in best]), np.nanmean([x['f'][k] for x in worst]), auc([x['f'][k] for x in bad], [x['f'][k] for x in good]), rho))
    sgn = [np.sign(x['gap'] - x['gt_m']) for x in worst]; print('   worst-20 direction: over %d under %d; worst-20 truth_m mean %.2f vs best-20 %.2f' % (sum(s > 0 for s in sgn), sum(s < 0 for s in sgn), np.mean([x['gt_m'] for x in worst]), np.mean([x['gt_m'] for x in best])))
    if step == 200:
        print('   worst 20 (id, objs, truth_m, gap, ratio, frames a/b, maxdim a/b, centre_dist):')
        for x in worst[::-1]:
            a, b = x['grounds']; print('     %s %s t=%.2f g=%.2f r=%.2f fr=%d/%d dim=%.2f/%.2f dc=%.2f' % (x['id'][-6:], '/'.join(x['objs']), x['gt_m'], x['gap'], x['gap'] / x['gt_m'], len(a['frames']), len(b['frames']), max(a['size']), max(b['size']), x['f']['centre_dist']))
        print('   best 20:')
        for x in best:
            a, b = x['grounds']; print('     %s %s t=%.2f g=%.2f r=%.2f fr=%d/%d dim=%.2f/%.2f dc=%.2f' % (x['id'][-6:], '/'.join(x['objs']), x['gt_m'], x['gap'], x['gap'] / x['gt_m'], len(a['frames']), len(b['frames']), max(a['size']), max(b['size']), x['f']['centre_dist']))
# number of boxes per ground
print('boxes per successful ground:', {s: dict(__import__('collections').Counter(g['nboxes'] for (st, i), x in R.items() if st == s for g in x['grounds'] if not g['not_seen'])) for s in (200, 544)})
