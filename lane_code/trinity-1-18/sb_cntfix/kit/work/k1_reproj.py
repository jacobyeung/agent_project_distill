"""Lane sb_countdesign, CPU pilot on K1: identity by the G3T tower's points. For two SAM 3 proposals of one name in different frames,
lift sampled mask pixels of one to 3D (G3T depth and pose x own-head scale), project them into the other frame, and measure the share
that is visible there (depth-consistent) and the share of those that land inside the other mask. These reprojection features are
added to the pair model of k1_lmerge.py; accept model, clustering rule and evaluation are unchanged.
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_reproj.py   (writes K1_REPROJ.json)"""
import json, gzip, collections, time, os
import numpy as np
exec(open('k1_lmerge.py').read().split("def pair_feats")[0])      # P with a, F, y, keep, pa; accept model
LABD = '/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1'; TEA = '/scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1'
GEO = '/scratch/jjyeung/n30_mirror/k1_ops3/run_convert_2'
DMAP = json.load(open('/scratch/jjyeung/orch_n30/b05_owngrd/work/k1map/DIR_TO_CAPTURE.json')); inv = {}
for k, v in DMAP.items():
    for c in (v['canonical'] or []): inv[c] = k
def rle_decode(r):
    h, w = r['size']; counts = r['counts']
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')
def bilinear(d, uv):
    n = len(d); x, y = np.clip(uv * ((n - 1) / 1000.0), 0, n - 1).T
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); x1, y1 = np.minimum(x0 + 1, n - 1), np.minimum(y0 + 1, n - 1); fx, fy = x - x0, y - y0
    return d[y0, x0] * (1 - fx) * (1 - fy) + d[y0, x1] * fx * (1 - fy) + d[y1, x0] * (1 - fx) * fy + d[y1, x1] * fx * fy
PA_MIN = 0.15; NS = 60
bycap = collections.defaultdict(list)
for x in P: bycap[x['p']['capture']].append(x)
t1 = time.time(); done = 0
for can, xs in bycap.items():
    g = np.load(os.path.join(GEO, inv[can], 'geometry.npz'), allow_pickle=True); scale = float(g['scale'])
    K = g['K'].astype(float); A = g['canvas_to_source'].astype(float); C = g['camera_to_world'].astype(float).copy(); C[:, :3, 3] *= scale; dg = g['depth_grid'].astype(float) * scale
    Kinv = np.linalg.inv(K); Ainv = np.linalg.inv(A)
    tea = json.load(gzip.open(os.path.join(TEA, can.replace('/', '__'), 'teacher.json.gz')))
    for x in xs:
        sel = np.flatnonzero(x['keep'] & (x['pa'] >= PA_MIN)); n = len(sel); x['sel'] = sel
        x['H'] = np.zeros((n, n), np.float32); x['V'] = np.zeros((n, n), np.float32)
        if n < 2: continue
        a = x['a'][sel]; fr = a[:, 2].astype(int); name = x['p']['name']
        masks = [rle_decode(tea['frames'][str(f)]['phrases'][name]['instances'][int(k)]['mask']) for f, k in zip(fr, a[:, 3].astype(int))]
        hh, ww = masks[0].shape
        pts = []
        for m, f in zip(masks, fr):
            idx = np.flatnonzero(m); s = idx[np.linspace(0, idx.size - 1, min(NS, idx.size)).astype(int)]
            r_, c_ = np.unravel_index(s, m.shape); src = np.column_stack((c_ + .5, r_ + .5, np.ones(len(s))))
            d = bilinear(dg[f], (src @ Ainv[f].T)[:, :2]); pc = (src @ Kinv[f].T) * d[:, None]
            pts.append(pc @ C[f, :3, :3].T + C[f, :3, 3])
        frames = sorted(set(fr)); members = {f: np.flatnonzero(fr == f) for f in frames}
        for i in range(n):
            Pw = pts[i]
            for f in frames:
                if f == fr[i]: continue
                pc = (Pw - C[f, :3, 3]) @ C[f, :3, :3]          # world -> camera f
                z = pc[:, 2]; ok = z > 0.1
                px = (pc / np.where(ok, z, 1.0)[:, None]) @ K[f].T
                xx, yy = px[:, 0], px[:, 1]; ok &= (xx >= 0) & (xx < ww) & (yy >= 0) & (yy < hh)
                if not ok.any(): continue
                src = np.column_stack((xx[ok], yy[ok], np.ones(int(ok.sum()))))
                dv = bilinear(dg[f], (src @ Ainv[f].T)[:, :2]); zz = z[ok]
                vis = np.abs(zz - dv) < np.maximum(0.15, 0.1 * zz)
                vfrac = float(vis.sum()) / len(Pw)
                if not vis.any():
                    for j in members[f]: x['V'][i, j] = vfrac
                    continue
                ci = np.clip(xx[ok][vis].astype(int), 0, ww - 1); ri = np.clip(yy[ok][vis].astype(int), 0, hh - 1)
                for j in members[f]:
                    x['V'][i, j] = vfrac; x['H'][i, j] = float(masks[j][ri, ci].mean())
    done += 1
    if done % 50 == 0: print('reproj', done, 'captures', '%.0fs' % (time.time() - t1), flush=True)
def pair_feats(x):
    sel = x['sel']; a = x['a'][sel]; pa = x['pa'][sel]; n = len(a); iu = np.triu_indices(n, 1)
    xyz = a[:, 12:15]; ext = np.linalg.norm(a[:, 15:18], axis=1); fr = a[:, 2]
    d = np.linalg.norm(xyz[iu[0]] - xyz[iu[1]], axis=1); e1, e2 = ext[iu[0]], ext[iu[1]]
    hij, hji = x['H'][iu[0], iu[1]], x['H'][iu[1], iu[0]]; vij, vji = x['V'][iu[0], iu[1]], x['V'][iu[1], iu[0]]
    F = np.column_stack((d, d / (0.5 * (e1 + e2) + 1e-3), np.abs(np.log((e1 + 1e-3) / (e2 + 1e-3))), np.abs(a[iu[0], 11] - a[iu[1], 11]), np.abs(fr[iu[0]] - fr[iu[1]]),
                         np.minimum(pa[iu[0]], pa[iu[1]]), np.maximum(pa[iu[0]], pa[iu[1]]), np.abs(a[iu[0], 18] - a[iu[1], 18]), np.abs(xyz[iu[0], 2] - xyz[iu[1], 2]), np.minimum(a[iu[0], 18], a[iu[1], 18]),
                         np.maximum(hij, hji), np.minimum(hij, hji), np.maximum(vij, vji), np.minimum(vij, vji), np.maximum(vij, vji) * (1 - np.maximum(hij, hji))))
    sf = fr[iu[0]] == fr[iu[1]]; true = (a[:, 8] == 1) & (a[:, 9] >= 0.25)
    y = (true[iu[0]] & true[iu[1]] & (a[iu[0], 7] == a[iu[1], 7])).astype(int)
    return F, y, sf
rng = np.random.default_rng(0); XP = []; YP = []
for x in P:
    if x['split'] != 'train' or len(x['sel']) < 2: continue
    F, y, sf = pair_feats(x); F, y = F[~sf], y[~sf]
    if len(y) > 400:
        ix = rng.choice(len(y), 400, replace=False); F, y = F[ix], y[ix]
    XP.append(F); YP.append(y)
XP = np.concatenate(XP); YP = np.concatenate(YP)
from sklearn.metrics import roc_auc_score
pm = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, max_depth=4, random_state=0).fit(XP, YP)
pm0 = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.08, max_depth=4, random_state=0).fit(XP[:, :10], YP)
XH = []; YH = []
for x in P:
    if x['split'] != 'heldout' or len(x['sel']) < 2: continue
    F, y, sf = pair_feats(x); XH.append(F[~sf]); YH.append(y[~sf])
XH = np.concatenate(XH); YH = np.concatenate(YH)
print('pair model heldout AUC: with reprojection %.3f, centroid features only %.3f (pairs %d, same-instance share %.2f)' % (roc_auc_score(YH, pm.predict_proba(XH)[:, 1]), roc_auc_score(YH, pm0.predict_proba(XH[:, :10])[:, 1]), len(YH), YH.mean()), flush=True)
def clusters(x, theta):
    sel = x['sel']; n = len(sel)
    if n == 0: return []
    pa = x['pa'][sel]
    if n == 1: return [float(pa[0])]
    F, y, sf = pair_feats(x); dist = 1 - pm.predict_proba(F)[:, 1]; dist[sf] = 3.0
    lab = fcluster(linkage(dist, method='average'), t=theta, criterion='distance')
    return [float(pa[lab == c].max()) for c in np.unique(lab)]
from scipy.stats import spearmanr
res = {}
for theta in (0.5, 0.6, 0.7, 0.8, 0.9):
    cl = [clusters(x, theta) for x in P]
    for tau in (0.4, 0.5):
        est = [sum(1 for v in c if v >= tau) for c in cl]; d = {}
        for split in ('train', 'heldout'):
            for b in ('1', '2', '3', '4', '5+'):
                ix = [i for i, x in enumerate(P) if x['split'] == split and tbin(x['T']) == b]; d['%s|%s' % (split, b)] = round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1)
        big = [i for i, x in enumerate(P) if x['T'] >= 5]; bh = [i for i in big if P[i]['split'] == 'heldout']
        d['rho_5+'] = round(float(spearmanr([est[i] for i in big], [P[i]['T'] for i in big]).correlation), 2); d['rho_5+_heldout'] = round(float(spearmanr([est[i] for i in bh], [P[i]['T'] for i in bh]).correlation), 2)
        d['ratio_5+_heldout'] = round(float(np.median([est[i] / P[i]['T'] for i in bh])), 2)
        for dsn in ('arkitscenes', 'scannetpp'):
            ix = [i for i in bh if P[i]['ds'] == dsn]; d['heldout|5+|' + dsn] = [len(ix), round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1)]
        res['theta%.1f_tau%.1f' % (theta, tau)] = dict(bins=d, est=[int(v) for v in est])
print('\n== learned accept + merge WITH reprojection features ==')
for n in sorted(res, key=lambda n: -np.mean([res[n]['bins']['train|' + b] for b in ('2', '3', '4', '5+')])):
    d = res[n]['bins']; print('%-16s train' % n, ' '.join('%s %.1f' % (b, d['train|' + b]) for b in ('1', '2', '3', '4', '5+')), '| heldout', ' '.join('%s %.1f' % (b, d['heldout|' + b]) for b in ('1', '2', '3', '4', '5+')),
                              '| rho 5+ %.2f (heldout %.2f) ratio %.2f' % (d['rho_5+'], d['rho_5+_heldout'], d['ratio_5+_heldout']), d['heldout|5+|arkitscenes'], d['heldout|5+|scannetpp'])
json.dump(res, open('K1_REPROJ.json', 'w'))
print('total %.0fs' % (time.time() - t0))
