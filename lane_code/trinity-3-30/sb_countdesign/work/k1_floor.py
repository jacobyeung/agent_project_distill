"""Lane sb_countdesign, CPU pilot on K1: the per-frame maximum (n*) as a printed floor, with per-frame duplicate suppression.
For each joint-score threshold: MRA of n* against truth by truth bin, and how often n* exceeds truth (a floor violation).
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_floor.py   (writes K1_FLOOR.json)"""
import json, gzip, collections
import numpy as np
exec(open('k1_price.py').read().split("EST = {")[0])
N = np.load('K1_NMS.npz')['rows']
keep = {(int(r[0]), int(r[1]), int(r[2]), int(r[3])): (int(r[4]), float(r[5]), float(r[6])) for r in N}
miss = 0
for x in P:
    a = x['a']; kf = np.ones(len(a), bool)
    for i, d in enumerate(a):
        v = keep.get((int(d[0]), int(d[1]), int(d[2]), int(d[3])))
        if v is None: miss += 1
        else: kf[i] = bool(v[0])
    x['keep'] = kf
print('proposals without an NMS row', miss, 'suppressed share %.3f' % (1 - np.mean(np.concatenate([x['keep'] for x in P if len(x['keep'])]))))
def per_frame(a, t):
    m = a[a[:, 4] >= t]
    return collections.Counter(m[:, 2].astype(int)) if len(m) else collections.Counter()
def stat(a, t, kind):
    c = sorted(per_frame(a, t).values(), reverse=True)
    if not c: return 0
    if kind == 'max': return c[0]
    if kind == 'second': return c[1] if len(c) > 1 else c[0]     # second-largest frame: resists one frame of false positives
    raise ValueError(kind)
out = {}
print('%-22s %s' % ('rule', 'MRA by truth bin (all splits) | share of pairs with estimate above truth by bin | 5+: under/over, median ratio | heldout 5+ | scannetpp 5+'))
for nms in (0, 1):
    for kind in ('max', 'second'):
        for t in (0.35, 0.5, 0.6, 0.7, 0.8, 0.9):
            est = [stat(x['a'][x['keep']] if nms else x['a'], t, kind) for x in P]
            d = {}
            for b in ('1', '2', '3', '4', '5+'):
                ix = [i for i, x in enumerate(P) if tbin(x['T']) == b]
                d[b] = dict(n=len(ix), mra=round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1), over=round(float(np.mean([est[i] > P[i]['T'] for i in ix])), 3),
                            under=round(float(np.mean([est[i] < P[i]['T'] for i in ix])), 3))
            big = [i for i, x in enumerate(P) if x['T'] >= 5]
            for tag, sel in (('train', lambda x: x['split'] == 'train'), ('heldout', lambda x: x['split'] == 'heldout'), ('arkitscenes', lambda x: x['ds'] == 'arkitscenes'), ('scannet', lambda x: x['ds'] == 'scannet'), ('scannetpp', lambda x: x['ds'] == 'scannetpp')):
                ix = [i for i in big if sel(P[i])]
                d['5+|' + tag] = dict(n=len(ix), mra=round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1))
            d['5+_ratio_med'] = round(float(np.median([est[i] / P[i]['T'] for i in big])), 2)
            name = '%s_t%.2f_%s' % (kind, t, 'nms' if nms else 'raw'); out[name] = d
            print('%-22s' % name, ' '.join('%s %.1f' % (b, d[b]['mra']) for b in ('1', '2', '3', '4', '5+')), '| over', ' '.join('%.2f' % d[b]['over'] for b in ('1', '2', '3', '4', '5+')),
                  '| ratio %.2f under %.2f' % (d['5+_ratio_med'], d['5+']['under']), '| train %.1f heldout %.1f' % (d['5+|train']['mra'], d['5+|heldout']['mra']), '| ark %.1f sn %.1f spp %.1f' % (d['5+|arkitscenes']['mra'], d['5+|scannet']['mra'], d['5+|scannetpp']['mra']))
json.dump(out, open('K1_FLOOR.json', 'w'), indent=0)
