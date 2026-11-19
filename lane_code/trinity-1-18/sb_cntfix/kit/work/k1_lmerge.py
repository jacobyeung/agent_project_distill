"""Lane sb_countdesign, CPU pilot on K1: a learned accept + learned pair merge for multi-instance counting, fitted on K1 train
(SAM 3 teacher proposals labelled with GT instance ids by lane b05_owngrd; G3T x own-scale 3D centroids), read on K1 held-out.
accept: P(proposal is an instance of the queried name); pair: P(two proposals of different frames are the same instance);
count = clusters (average linkage on 1 - P(same), same-frame pairs kept apart) whose best accept probability passes a threshold.
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_lmerge.py   (writes K1_LMERGE.json)"""
import json, gzip, collections, time
import numpy as np
exec(open('k1_price.py').read().split("EST = {")[0])
N = np.load('K1_NMS.npz')['rows']
nms = {(int(r[0]), int(r[1]), int(r[2]), int(r[3])): (int(r[4]), float(r[5]), float(r[6])) for r in N}
from sklearn.ensemble import HistGradientBoostingClassifier
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
t0 = time.time()
TMIN = 0.2
def prop_feats(x):
    a = x['a']
    if not len(a): return np.zeros((0, 14)), np.zeros(0), np.zeros(0, bool)
    fr = a[:, 2].astype(int); j = a[:, 4]
    keep = np.array([nms[(int(d[0]), int(d[1]), int(d[2]), int(d[3]))][0] for d in a], bool)
    mi = np.array([nms[(int(d[0]), int(d[1]), int(d[2]), int(d[3]))][1] for d in a]); mc = np.array([nms[(int(d[0]), int(d[1]), int(d[2]), int(d[3]))][2] for d in a])
    nf35 = collections.Counter(fr[j >= 0.35]); nf5 = collections.Counter(fr[j >= 0.5])
    rank = np.array([np.sum((fr == f) & (j > jj)) for f, jj in zip(fr, j)])
    xyz = a[:, 12:15]; ext = np.linalg.norm(a[:, 15:18], axis=1)
    D = np.linalg.norm(xyz[:, None] - xyz[None], axis=2); other = fr[:, None] != fr[None]
    sup5 = np.array([len(set(fr[(D[i] < 0.5) & other[i] & (j >= 0.35)])) for i in range(len(a))])
    supx = np.array([len(set(fr[(D[i] < max(0.5, ext[i])) & other[i] & (j >= 0.35)])) for i in range(len(a))])
    F = np.column_stack((j, a[:, 5], np.log(a[:, 11] + 1e-6), a[:, 18], ext, [nf35[f] for f in fr], [nf5[f] for f in fr], rank, np.full(len(a), j.max()), j / j.max(),
                         np.full(len(a), len(set(fr[j >= 0.5]))), sup5, supx, mc))
    y = ((a[:, 8] == 1) & (a[:, 9] >= 0.25)).astype(int)
    return F, y, keep
for x in P: x['F'], x['y'], x['keep'] = prop_feats(x)
tr = [x for x in P if x['split'] == 'train']; he = [x for x in P if x['split'] == 'heldout']
Xa = np.concatenate([x['F'] for x in tr]); ya = np.concatenate([x['y'] for x in tr])
acc = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=4, random_state=0).fit(Xa, ya)
from sklearn.metrics import roc_auc_score
Xh = np.concatenate([x['F'] for x in he]); yh = np.concatenate([x['y'] for x in he])
print('accept: train rows %d pos %.2f | heldout AUC %.3f (joint alone %.3f)' % (len(ya), ya.mean(), roc_auc_score(yh, acc.predict_proba(Xh)[:, 1]), roc_auc_score(yh, Xh[:, 0])), '%.0fs' % (time.time() - t0), flush=True)
for x in P: x['pa'] = acc.predict_proba(x['F'])[:, 1] if len(x['F']) else np.zeros(0)
def pair_feats(x, sel):
    a = x['a'][sel]; pa = x['pa'][sel]
    n = len(a); iu = np.triu_indices(n, 1)
    xyz = a[:, 12:15]; ext = np.linalg.norm(a[:, 15:18], axis=1); fr = a[:, 2]
    d = np.linalg.norm(xyz[iu[0]] - xyz[iu[1]], axis=1); e1, e2 = ext[iu[0]], ext[iu[1]]
    F = np.column_stack((d, d / (0.5 * (e1 + e2) + 1e-3), np.abs(np.log((e1 + 1e-3) / (e2 + 1e-3))), np.abs(a[iu[0], 11] - a[iu[1], 11]), np.abs(fr[iu[0]] - fr[iu[1]]),
                         np.minimum(pa[iu[0]], pa[iu[1]]), np.maximum(pa[iu[0]], pa[iu[1]]), np.abs(a[iu[0], 18] - a[iu[1], 18]), np.abs(xyz[iu[0], 2] - xyz[iu[1], 2]),
                         np.minimum(a[iu[0], 18], a[iu[1], 18])))
    same_frame = fr[iu[0]] == fr[iu[1]]
    true = (a[:, 8] == 1) & (a[:, 9] >= 0.25)
    y = (true[iu[0]] & true[iu[1]] & (a[iu[0], 7] == a[iu[1], 7])).astype(int)
    return F, y, same_frame, iu
PA_MIN = 0.15
rng = np.random.default_rng(0); XP = []; YP = []
for x in tr:
    sel = x['keep'] & (x['pa'] >= PA_MIN)
    if sel.sum() < 2: continue
    F, y, sf, iu = pair_feats(x, sel)
    F, y = F[~sf], y[~sf]
    if len(y) > 400:
        ix = rng.choice(len(y), 400, replace=False); F, y = F[ix], y[ix]
    XP.append(F); YP.append(y)
XP = np.concatenate(XP); YP = np.concatenate(YP)
pm = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=4, random_state=0).fit(XP, YP)
print('pair: train rows %d pos %.2f' % (len(YP), YP.mean()), '%.0fs' % (time.time() - t0), flush=True)
def clusters(x, theta):
    sel = x['keep'] & (x['pa'] >= PA_MIN)
    n = int(sel.sum())
    if n == 0: return []
    pa = x['pa'][sel]
    if n == 1: return [float(pa[0])]
    F, y, sf, iu = pair_feats(x, sel)
    ps = pm.predict_proba(F)[:, 1]; dist = 1 - ps; dist[sf] = 3.0
    Z = linkage(dist, method='average'); lab = fcluster(Z, t=theta, criterion='distance')
    return [float(pa[lab == c].max()) for c in np.unique(lab)]
res = {}
cache = {}
for theta in (0.4, 0.5, 0.6, 0.7, 0.8):
    for i, x in enumerate(P): cache[(i, theta)] = clusters(x, theta)
    for tau in (0.3, 0.4, 0.5, 0.6):
        est = [sum(1 for v in cache[(i, theta)] if v >= tau) for i in range(len(P))]
        d = {}
        for split in ('train', 'heldout'):
            for b in ('1', '2', '3', '4', '5+'):
                ix = [i for i, x in enumerate(P) if x['split'] == split and tbin(x['T']) == b]
                d['%s|%s' % (split, b)] = round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1)
        for dsn in ('arkitscenes', 'scannet', 'scannetpp'):
            ix = [i for i, x in enumerate(P) if x['split'] == 'heldout' and x['T'] >= 5 and x['ds'] == dsn]
            d['heldout|5+|' + dsn] = [len(ix), round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1) if ix else None]
        big = [i for i, x in enumerate(P) if x['split'] == 'heldout' and x['T'] >= 5]
        d['heldout_5+_ratio_med'] = round(float(np.median([est[i] / P[i]['T'] for i in big])), 2)
        res['theta%.1f_tau%.1f' % (theta, tau)] = dict(bins=d, est=est)
    print('theta', theta, '%.0fs' % (time.time() - t0), flush=True)
def bal(d, s): return float(np.mean([d['%s|%s' % (s, b)] for b in ('2', '3', '4', '5+')]))
print('\n== learned accept + merge: sorted by train balanced (2,3,4,5+) ==')
for n in sorted(res, key=lambda n: -bal(res[n]['bins'], 'train'))[:8]:
    d = res[n]['bins']; print('%-18s train bal %.1f:' % (n, bal(d, 'train')), ' '.join('%s %.1f' % (b, d['train|' + b]) for b in ('1', '2', '3', '4', '5+')), '| heldout bal %.1f:' % bal(d, 'heldout'), ' '.join('%s %.1f' % (b, d['heldout|' + b]) for b in ('1', '2', '3', '4', '5+')), '| ho 5+ ratio %.2f' % d['heldout_5+_ratio_med'], d['heldout|5+|arkitscenes'], d['heldout|5+|scannet'], d['heldout|5+|scannetpp'])
print('\n== sorted by train 5+ ==')
for n in sorted(res, key=lambda n: -res[n]['bins']['train|5+'])[:5]:
    d = res[n]['bins']; print('%-18s' % n, ' '.join('%s %.1f' % (b, d['train|' + b]) for b in ('1', '2', '3', '4', '5+')), '| heldout', ' '.join('%s %.1f' % (b, d['heldout|' + b]) for b in ('1', '2', '3', '4', '5+')))
json.dump({n: dict(bins=res[n]['bins'], est=[int(v) for v in res[n]['est']]) for n in res}, open('K1_LMERGE.json', 'w'))
