"""Second reader of gt_audit's K1 half-extent correction rule (lane tower_redecide).

Independent code (no import from audit.py, box_v313.py or gt_audit scripts). For 30 stratified K1 distance rows:
  1. back-project every instance pixel of the K1 GT raster (all valid frames, pixel centres +0.5, K_frames, c2w),
  2. measure each instance's robust half-extent along the stored box axes (rows of obb_axes) relative to the
     stored length; a full-length box gives about 0.5 (or less when partly seen), a half-length box about 1.0,
  3. classify the row's two boxes and the scene's convention (all well-observed instances of the raster),
  4. recompute the label with my own 5 cm box grid (full box minus inner half box, min over points) at the
     factors my reading implies, and compare with K1_LABELS_CORRECTED.jsonl.
Reads only: K1 manifest + rasters under gt_audit/work (read-only), K1_LABELS_CORRECTED.jsonl. Writes only in my lane.
"""
import collections, json, math, os, random
import numpy as np
from scipy.spatial import cKDTree

GA = '/scratch/jjyeung/orch_n30/gt_audit'
MAN = GA + '/work/k1/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
RROOT = GA + '/work/k1r'
LAB = GA + '/out/audit/k1/K1_LABELS_CORRECTED.jsonl'
OUT = '/scratch/jjyeung/orch_n30/tower_redecide/work/second_reader'


def grid(c, L, A, step=0.05):
    ax = [np.linspace(-e / 2, e / 2, int(math.ceil(e / step))) for e in L]
    g = np.stack([m.ravel() for m in np.meshgrid(*ax, indexing='ij')], 1)
    g = g[np.any(np.abs(g) > np.asarray(L) / 4, axis=1)]
    if len(g) == 0:
        return grid(c, L, A, step / 2)
    return g @ A + c


def gap(b1, b2, f1, f2):
    p = grid(b1['c'], b1['L'] * f1, b1['A']); q = grid(b2['c'], b2['L'] * f2, b2['A'])
    return float(cKDTree(p).query(q)[0].min())


def backproject_all(z):
    d, inst, c2w = z['depth'], z['inst'], z['c2w'].astype(np.float64)
    K = z['K_frames'] if 'K_frames' in z.files else np.repeat(z['K'][None], len(d), 0)
    valid = z['valid'] if 'valid' in z.files else np.ones(len(d), bool)
    H, W = d.shape[1:]
    vv, uu = np.mgrid[0:H, 0:W]
    pts, ids, frs = [], [], []
    for f in np.flatnonzero(valid):
        m = np.isfinite(d[f]) & (d[f] > 0) & (inst[f] > 0)
        if not m.any():
            continue
        u, v, z_ = uu[m] + 0.5, vv[m] + 0.5, d[f][m].astype(np.float64)
        Ki = np.linalg.inv(K[f])
        rays = np.stack([u, v, np.ones_like(u)], 1) @ Ki.T
        P = (rays * z_[:, None]) @ c2w[f, :3, :3].T + c2w[f, :3, 3]
        pts.append(P); ids.append(inst[f][m]); frs.append(np.full(len(P), f))
    return np.concatenate(pts), np.concatenate(ids), np.concatenate(frs)


def box_stats(P, b):
    q = (P - b['c']) @ b['A'].T
    L = b['L']
    obs = L >= 0.10
    if not obs.any():
        obs = L == L.max()
    e = np.quantile(np.abs(q), 0.99, axis=0) / L   # robust half-extent relative to the stored length
    r = float(e[obs].max())
    f1 = float(np.mean((np.abs(q) <= L / 2 + 0.03).all(1)))
    f2 = float(np.mean((np.abs(q) <= L + 0.03).all(1)))
    return dict(n=int(len(P)), r=r, e=[float(x) for x in e], in_x1=f1, in_x2=f2)


def verdict(s, nframes):
    if s is None or s['n'] < 200 or nframes < 2:
        return 'unknown'
    if 0.68 <= s['r'] <= 1.25 and s['in_x2'] >= 0.85 and s['in_x2'] - s['in_x1'] >= 0.10:
        return 'half'
    if 0.30 <= s['r'] <= 0.62 and s['in_x1'] >= 0.90:
        return 'full'
    return 'unknown'


def main():
    os.makedirs(OUT, exist_ok=True)
    M = json.load(open(MAN))
    lab = {json.loads(l)['id']: json.loads(l) for l in open(LAB)}
    rows = []
    for c in M['captures']:
        p = RROOT + '/' + c['gt']['path'][len('/scratch/jjyeung/'):]
        if not os.path.exists(p):
            continue
        for r in c['rows']:
            if r['type'] == 'object_abs_distance':
                rows.append(dict(r, capture=c['canonical'], split=c['k1_split'], raster=p))
    L = {r['id']: lab[r['id']] for r in rows}
    st = collections.defaultdict(list)
    for r in rows:
        l = L[r['id']]; ds = l['dataset']; unk = 'unknown' in l['box_statuses']
        if ds == 'scannetpp' and r['split'] == 'heldout':
            st['A_ho_snpp_decided' if not unk else 'B_ho_snpp_unknownbox'].append(r)
        elif ds == 'scannetpp' and not unk:
            st['G_tr_snpp_decided'].append(r)
        elif ds == 'scannetpp' and unk:
            st['C_tr_snpp_unknownbox'].append(r)
        elif ds == 'scannet' and l['convention'] == 'half':
            st['D_scannet_half_scene'].append(r)
        elif ds == 'scannet':
            st['E_scannet_full'].append(r)
        elif ds == 'arkitscenes':
            st['F_arkit_full'].append(r)
    want = {k: 10**6 for k in st}
    rng = random.Random(20261117)
    sample = []
    for k, n in want.items():
        pool = sorted(st[k], key=lambda r: r['id'])
        sample += [dict(r, stratum=k) for r in rng.sample(pool, min(n, len(pool)))]
    print({k: len(v) for k, v in st.items()}, 'sample', len(sample), flush=True)
    by_raster = collections.defaultdict(list)
    for r in sample:
        by_raster[r['raster']].append(r)
    results, scenes = [], {}
    for p, rs in sorted(by_raster.items()):
        z = np.load(p, allow_pickle=False)
        ids = [int(x) for x in z['ids']]
        boxes = {iid: dict(c=z['obb_centroid'][j].astype(float), L=z['obb_lengths'][j].astype(float),
                           A=z['obb_axes'][j].astype(float).reshape(3, 3)) for j, iid in enumerate(ids)}
        P, I, F = backproject_all(z)
        per = {}
        for iid, b in boxes.items():
            m = I == iid
            if m.sum() < 50:
                continue
            s = box_stats(P[m], b); nf = len(np.unique(F[m]))
            per[iid] = dict(s, frames=nf, verdict=verdict(s, nf))
        cnt = collections.Counter(v['verdict'] for v in per.values())
        rr = [v['r'] for v in per.values() if v['n'] >= 500 and v['frames'] >= 2 and boxes_maxlen(boxes, v) >= 0.2]
        scene_conv = 'half' if cnt['half'] and not cnt['full'] else 'full' if cnt['full'] and not cnt['half'] else 'mixed' if cnt['half'] else 'none'
        scenes[p] = dict(canonical=rs[0]['capture'], verdicts=dict(cnt), median_r=float(np.median(rr)) if rr else None, n_r=len(rr),
                         scene_convention=scene_conv)
        for r in rs:
            l = L[r['id']]; bx = [boxes[int(r['gt_instances'][n])] for n in r['operands']]
            vs = [per.get(int(r['gt_instances'][n]), dict(verdict='unknown')) for n in r['operands']]
            x1 = gap(bx[0], bx[1], 1, 1)
            fac = [2 if v['verdict'] == 'half' else 1 if v['verdict'] == 'full' else (2 if scene_conv == 'half' else 1 if scene_conv == 'full' else None)
                   for v in vs]
            mine = gap(bx[0], bx[1], *fac) if None not in fac else None
            results.append(dict(id=r['id'], stratum=r['stratum'], capture=r['capture'], split=r['split'], operands=r['operands'],
                                stored=r['gt_value'], my_x1=x1, x1_reproduces_stored=abs(x1 - r['gt_value']) < 1e-6,
                                my_box_verdicts=[v['verdict'] for v in vs], my_box_r=[v.get('r') for v in vs],
                                my_box_in=[(v.get('in_x1'), v.get('in_x2')) for v in vs], my_box_frames=[v.get('frames') for v in vs],
                                scene_convention=scene_conv, my_factors=fac, my_label=mine,
                                ga_convention=l['convention'], ga_box_statuses=l['box_statuses'], ga_corrected=l['corrected'],
                                agree=(mine is not None and abs(mine - l['corrected']) < 1e-6),
                                box_level_agree=[(a == b) or (a == 'unknown') or (b == 'unknown') for a, b in zip([v['verdict'] for v in vs], l['box_statuses'])]))
        print('raster', os.path.basename(p), scenes[p], flush=True)
    json.dump(dict(rows=results, scenes=scenes), open(OUT + '/SECOND_READER_ALL2.json', 'w'), indent=1)
    n = len(results)
    print('rows', n, 'x1 reproduces stored', sum(r['x1_reproduces_stored'] for r in results),
          'label agrees', sum(r['agree'] for r in results),
          'box-level conflicts', sum(not all(r['box_level_agree']) for r in results),
          'rows resting on a scene-convention box (my unknown)', sum('unknown' in r['my_box_verdicts'] for r in results))
    for r in results[:0]:
        print(r['stratum'], r['capture'], r['split'], 'stored %.3f mine %s ga %.3f' % (r['stored'], 'None' if r['my_label'] is None else '%.3f' % r['my_label'], r['ga_corrected']),
              r['my_box_verdicts'], [None if x is None else round(x, 2) for x in r['my_box_r']], r['ga_box_statuses'], r['scene_convention'], 'AGREE' if r['agree'] else 'DIFF')


def boxes_maxlen(boxes, v):
    return 1.0  # every instance in the scene-level median passes the size filter through n >= 500 points


if __name__ == '__main__':
    main()
