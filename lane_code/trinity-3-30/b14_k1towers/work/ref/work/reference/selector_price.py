"""Priced outcome: the fixed programs (gt_ceiling prog_v2, read-only, imported) on masks from each grounding arm,
with GT depth and pose and with the tower's (vcd heads) depth and pose, on identical items.

Masks per arm (instances of each named object; frames = sampled slots 0..31):
  gt            GT masks of prog_v2's own resolution (parity: GT geometry must reproduce gt_ceiling 'none')
  gt_prop       GT masks only on frames where a raw SAM 3 proposal matches that instance (IoU > 0.5)
  sam_gtid      the matching SAM 3 proposals themselves, GT identity (same frames as gt_prop: extent only)
  oracle        linked candidates the scoring label accepts (y = 1), type-aware identity (below)
  sel           the set selector's accepted candidates (frozen DEPLOY model, tau 0.5), type-aware identity
  sel_t03       the same at tau 0.3
  native        the deployed selector's per-frame masks; sam3_top: SAM 3's top linked candidate
  sel_e1, sel_e2   sel with masks eroded 1 / 2 px before lifting; sel_edge: sel minus depth-edge pixels
  *_dc          masks cut to the depth range of their interior before lifting (P10 - 0.15 m .. P90 + 0.15 m)
  *_ppdc        propagation, then the depth-range cut on every mask
  *_pp          the arm plus propagation: each instance's fused 3D points projected (z-buffered against the frame's
                depth) into frames where it has no mask; a projected mask of >= 154 px joins the instance
Type-aware identity (label-free): counting merges accepted candidates into 3D instances (centre distance below
0.3 m + 0.5 x the larger extent, no two disjoint masks on one frame); every other VSI-Bench type names a unique
object, so its accepted candidates form one instance.
usage: price.py --set vsi --probs data/probs/probs.json --key 'DEPLOY|portable|logistic' --out ../../out/price_vsi"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path[:0] = ['/scratch/jjyeung/orch_cd/grd_selector/work/setsel', '/scratch/jjyeung/orch_cd/grd_selector/work/vk',
                '/scratch/jjyeung/orch_cd/gt_ceiling/work/tp', '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl']
import setlib as L  # noqa: E402
import cands as CD  # noqa: E402

GTNPZ = '/scratch/jjyeung/orch_cd/toolprog/work/gt/scannet/%s.npz'
VCD = '/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd/scannet__%s.npz'
VSI_FIX = 'frameidx,axes,memory,extent,identity,round,vocab,gbox0'.split(',')
H, W, STEP, MIN_PX = 240, 320, 2, 154
ARGS = None
SUFFIX = ('e1', 'e2', 'edge', 'dc', 'pp', 'ppdc')
ARMS = ['gt', 'gt_prop', 'sam_gtid', 'oracle', 'oracle_obj', 'sel', 'sel_t03', 'native', 'sam3_top', 'sel_e1', 'sel_e2',
        'sel_edge', 'sel_pp', 'oracle_pp', 'gt_prop_pp', 'native_pp']


# ------------------------------------------------------------------------------------------------ geometry

class GeomGT:
    def __init__(self, gt):
        self.gt = gt
        ys, xs = np.mgrid[0:H, 0:W]
        self._rays = np.stack([xs + .5, ys + .5, np.ones_like(xs, float)], -1) @ gt.Kinv.T
        self.frames = [k for k in range(1, 33) if gt.has(k)]

    def depth(self, k):
        return self.gt.depth[k-1]

    def rays(self, k):
        return self._rays

    def cam(self, k):
        return self.gt.cam(k)

    def project(self, k, P):
        R, t = self.cam(k)
        Pc = (P - t) @ R
        z = Pc[:, 2]
        uv = (Pc / np.maximum(z, 1e-6)[:, None]) @ self.gt.K.T
        return uv[:, 0] - .5, uv[:, 1] - .5, z


class GeomTower:
    def __init__(self, path):
        import programs as PR
        self.h = PR.load_heads(path)
        assert self.h.grid is not None
        ys, xs = np.mgrid[0:H, 0:W]
        self.u, self.v = (xs + .5) / W * 1000, (ys + .5) / H * 1000
        self.frames = list(range(1, 33))
        self._d = {}

    def depth(self, k):
        if k not in self._d:
            self._d[k] = self.h._depth(k-1, self.u.ravel(), self.v.ravel()).reshape(H, W).astype(np.float32)
        return self._d[k]

    def rays(self, k):
        fh, fw = self.h.fov[k-1]
        return np.stack([(self.u/500-1)*math.tan(fw/2), (self.v/500-1)*math.tan(fh/2), np.ones_like(self.u)], -1)

    def cam(self, k):
        return self.h.cam(k)

    def project(self, k, P):
        R, t = self.cam(k)
        Pc = (P - t) @ R
        z = Pc[:, 2]
        fh, fw = self.h.fov[k-1]
        u = 500*(Pc[:, 0]/np.maximum(z, 1e-6)/math.tan(fw/2)+1)
        v = 500*(Pc[:, 1]/np.maximum(z, 1e-6)/math.tan(fh/2)+1)
        return u/1000*W - .5, v/1000*H - .5, z


def edge_mask(D):
    """Pixels whose depth departs from the 5 x 5 median by more than 5 cm + 3%: mixed-depth boundary pixels."""
    med = ndimage.median_filter(D, size=5)
    return np.abs(D - med) > .05 + .03*med


def depth_consistent(m, D):
    """Drop mask pixels whose depth leaves the interior's depth range (P10 - 0.15 m, P90 + 0.15 m): background
    bleed behind the object and occluders in front; interior = the mask eroded 3 px."""
    inner = ndimage.binary_erosion(m, iterations=3)
    if inner.sum() < 20:
        inner = m
    d = D[inner]
    d = d[d > 0]
    if len(d) < 10:
        return m
    lo, hi = np.percentile(d, 10)-.15, np.percentile(d, 90)+.15
    keep = m & (D >= lo) & (D <= hi)
    return keep if keep.sum() >= 8 else m


def lift(geom, k, m, mode=None):
    """World points of mask m on frame k (stride-2 grid as prog_v2.Fused), optional erosion / depth-edge drop."""
    if mode in ('e1', 'e2'):
        er = ndimage.binary_erosion(m, ndimage.generate_binary_structure(2, 1), iterations=int(mode[1]))
        m = er if er.sum() >= 8 else m
    D = geom.depth(k)
    if mode == 'edge':
        keep = m & ~edge_mask(D)
        m = keep if keep.sum() >= 8 else m
    if mode == 'dc':
        m = depth_consistent(m, D)
    sub = m[::STEP, ::STEP] & (D[::STEP, ::STEP] > 0)
    if sub.sum() < 3:
        return None
    d = D[::STEP, ::STEP][sub]
    R, t = geom.cam(k)
    return (geom.rays(k)[::STEP, ::STEP][sub] * d[:, None]) @ R.T + t


class PredFused:
    """prog_v2.Fused over per-instance mask dicts {iid: {k: mask}} (masks may overlap across names)."""

    def __init__(self, geom, insts, min_px=MIN_PX, mode=None):
        import scene_gt as SG
        self.SG, self.min_px = SG, min_px
        self.pts, self.px, self._box = {}, {}, {}
        for i, fr in insts.items():
            for k, m in fr.items():
                n = int(m.sum())
                self.px.setdefault(i, {})[k] = n
                if n < min_px or k not in geom.frames:
                    continue
                P = lift(geom, k, m, mode)
                if P is not None:
                    self.pts.setdefault(i, []).append(P)

    def points(self, i):
        p = self.pts.get(i)
        return np.concatenate(p) if p else None

    def box(self, i):
        if i not in self._box:
            P = self.points(i)
            if P is None:
                self._box[i] = None
            else:
                if len(P) > 4000:
                    P = P[np.random.default_rng(0).choice(len(P), 4000, replace=False)]
                self._box[i] = self.SG.minimal_obb(P)
        return self._box[i]

    def seen(self, i, min_px=None):
        mp = self.min_px if min_px is None else min_px
        return any(n >= mp for n in self.px.get(i, {}).values())


class PredCtx:
    def __init__(self, geom, insts, name2ids, mode=None):
        self.gt, self.fixes, self.level = geom, set(VSI_FIX), 'B'
        self.fused = PredFused(geom, insts, mode=mode)
        self.name2ids = name2ids

    def ids(self, name):
        return self.name2ids.get(name.lower(), [])


# ------------------------------------------------------------------------------------------------ masks per arm

def iou(a, b):
    i = np.logical_and(a, b).sum()
    return float(i/np.logical_or(a, b).sum()) if i else 0.


def propagate(geom, fr, mode=None):
    """Project an instance's fused points into frames without a mask; z-buffer against the frame depth."""
    pts = [lift(geom, k, m, mode) for k, m in fr.items() if m.sum() >= MIN_PX and k in geom.frames]
    pts = [p for p in pts if p is not None]
    if not pts:
        return {}
    P = np.concatenate(pts)
    if len(P) > 20000:
        P = P[np.random.default_rng(0).choice(len(P), 20000, replace=False)]
    out = {}
    for k in geom.frames:
        if k in fr:
            continue
        x, y, z = geom.project(k, P)
        xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
        ok = (z > .1) & (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        if ok.sum() < 20:
            continue
        D = geom.depth(k)
        d = D[yi[ok], xi[ok]]
        vis = (d <= 0) | (z[ok] <= d*1.05 + .05)
        if vis.sum() < 20:
            continue
        m = np.zeros((H, W), bool)
        m[yi[ok][vis], xi[ok][vis]] = True
        m = ndimage.binary_fill_holes(ndimage.binary_closing(ndimage.binary_dilation(m, iterations=1), iterations=2))
        if m.sum() >= MIN_PX:
            out[k] = m
    return out


def merge_masks(acc, p, centres, exts):
    """Counting identity: union-find over accepted candidates; acc = [(cid, {k: mask})]."""
    n = len(acc)
    groups = {i: {i} for i in range(n)}
    root = list(range(n))

    def find(i):
        while root[i] != i:
            i = root[i]
        return i
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            if centres[i] is None or centres[j] is None:
                continue
            d = float(np.linalg.norm(centres[i]-centres[j]))
            if d < .3 + .5*max(exts[i], exts[j]):
                pairs.append((d, i, j))
    for d, i, j in sorted(pairs):
        ri, rj = find(i), find(j)
        if ri == rj:
            continue
        bad = False
        for a in groups[ri]:
            for b in groups[rj]:
                for k in set(acc[a][1]) & set(acc[b][1]):
                    ma, mb = acc[a][1][k], acc[b][1][k]
                    if np.logical_and(ma, mb).sum() < .2*min(ma.sum(), mb.sum()):
                        bad = True
        if not bad:
            root[rj] = ri
            groups[ri] |= groups.pop(rj)
    return [sorted(g, key=lambda i: -p[acc[i][0]]) for g in groups.values()]


def union(parts, p):
    """One instance from accepted candidates: per frame the union of members (candidate order by p)."""
    fr = {}
    for cid, masks in sorted(parts, key=lambda t: -p[t[0]]):
        for k, m in masks.items():
            fr[k] = fr[k] | m if k in fr else m
    return fr


def centre_ext(geom, masks):
    pts = [lift(geom, k, m) for k, m in masks.items() if k in geom.frames]
    pts = [x for x in pts if x is not None]
    if not pts:
        return None, 0.
    P = np.concatenate(pts)
    meds = [np.median(x, 0) for x in pts]
    ext = float(np.max(np.percentile(P, 90, 0)-np.percentile(P, 10, 0)))
    return np.median(np.stack(meds), 0), ext


def scene_job(job):
    import programs as PR
    import prog_v2 as V
    import common as C
    from verifykit.io import cache, tower
    scene, qs, objs, cands = job
    a = ARGS
    gt = PR.GTSource(GTNPZ % scene)
    geoms = dict(gtgeo=GeomGT(gt), tower=GeomTower(VCD % scene))
    raw = cache(str(CD.RAW[a.set]/f'scannet__{scene}.npz'))
    probs = a.probs_d

    def dec(phrase, k, ii):
        return tower().rle_decode(raw['frames'][str(k)]['phrases'][phrase]['instances'][ii]['mask'])[::2, ::2]
    base = V.Ctx(gt, VSI_FIX, 'B')
    names = sorted({n for q in qs for n in CD.item_names(V.T.parse_vsi(q))})
    # arm -> name -> list of (label, {k(1-based): mask}) ; one entry per instance
    arms, arms_m = defaultdict(dict), defaultdict(dict)
    mstats = []
    for n in names:
        gids = base.ids(n)
        arms['gt'][n] = [{k: gt.inst[k-1] == i for k in range(1, 33) if (gt.inst[k-1] == i).any()} for i in gids]
        oid = f'scannet/{scene}::{n}'
        obj = objs.get(oid)
        if obj is None:
            continue
        cs = cands.get(oid, [])
        ph = obj['phrase']
        p = {c['candidate_id']: probs.get(f"{oid}|{c['candidate_id']}", 0.) for c in cs}
        cm = {c['candidate_id']: {m['slot']+1: dec(ph, m['slot'], m['ii']) for m in c['members']} for c in cs}
        # proposals matched to GT instances of the category (prog resolution) -> gt_prop / sam_gtid
        gp, sg = defaultdict(dict), defaultdict(dict)
        for k in range(1, 33):
            gms = [(i, gt.inst[k-1] == i) for i in gids]
            gms = [(i, m) for i, m in gms if m.any()]
            if not gms:
                continue
            ni = len(raw['frames'][str(k-1)]['phrases'][ph]['instances'])
            props = [dec(ph, k-1, j) for j in range(ni)]
            pairs = sorted(((iou(g, q), i, j, g) for i, g in gms for j, q in enumerate(props)), key=lambda t: -t[0])
            ug, up = set(), set()
            for v, i, j, g in pairs:
                if v > .5 and i not in ug and j not in up:
                    ug.add(i); up.add(j)
                    gp[i][k], sg[i][k] = g, props[j]
        arms['gt_prop'][n] = list(gp.values())
        arms['sam_gtid'][n] = list(sg.values())
        counting = obj['_counting']
        top = [c for c in cs if c['candidate_id'] == obj['sam3_top']]
        arms['sam3_top'][n] = [union([(c['candidate_id'], cm[c['candidate_id']]) for c in top], defaultdict(float))] if top else []
        arms['native'][n] = [{s+1: dec(ph, s, ii) for s, ii in ((x['slot'], x['ii']) for x in obj['native'])}] if obj['native'] else []
        yobj = {c['candidate_id']: float(np.mean([m['iou'] > .1 for m in c['members']]) >= .5) for c in cs}
        for arm, chosen, pp in (('oracle', [c for c in cs if c['y']], {c['candidate_id']: c['y']+1e-3*c['features']['peak'] for c in cs}),
                                ('oracle_obj', [c for c in cs if yobj[c['candidate_id']]], {c['candidate_id']: yobj[c['candidate_id']]+1e-3*c['features']['peak'] for c in cs}),
                                ('sel', L.accept(cs, p, .5), p), ('sel_t03', L.accept(cs, p, .3), p),
                                ('sel_top1', L.accept(cs, p, 2.), p)):
            parts = [(c['candidate_id'], cm[c['candidate_id']]) for c in chosen]
            if not parts:
                arms[arm][n] = []
                continue
            arms[arm][n] = [union(parts, pp)]
            if counting:
                ce = [centre_ext(geoms['tower'], m) for _, m in parts]
                groups = merge_masks(parts, pp, [x[0] for x in ce], [x[1] for x in ce])
                arms_m[arm][n] = [union([parts[i] for i in g], pp) for g in groups]
        # mask extent statistics vs GT on frames where a kept mask matches a GT instance
        for arm in ('sel', 'native', 'sam3_top'):
            for fr in arms[arm][n]:
                for k, m in fr.items():
                    best = max(((iou(m, gt.inst[k-1] == i), i) for i in gids), default=(0., -1))
                    if best[0] <= .5:
                        continue
                    g = gt.inst[k-1] == best[1]
                    row = dict(scene=scene, name=n, arm=arm, k=k, gt_px=int(g.sum()), iou=best[0])
                    for mode in (None, 'e1', 'e2', 'edge'):
                        mm = m
                        if mode in ('e1', 'e2'):
                            er = ndimage.binary_erosion(m, ndimage.generate_binary_structure(2, 1), iterations=int(mode[1]))
                            mm = er if er.sum() >= 8 else m
                        elif mode == 'edge':
                            for gname, geom in geoms.items():
                                keep = m & ~edge_mask(geom.depth(k))
                                mk = keep if keep.sum() >= 8 else m
                                row[f'bleed_edge_{gname}'] = float((mk & ~g).sum()/max(mk.sum(), 1))
                                row[f'under_edge_{gname}'] = float((g & ~mk).sum()/g.sum())
                            continue
                        tag = mode or 'raw'
                        row[f'bleed_{tag}'] = float((mm & ~g).sum()/max(mm.sum(), 1))
                        row[f'under_{tag}'] = float((g & ~mm).sum()/g.sum())
                    mstats.append(row)
    # programs
    rows, recall = [], []
    D = a.direct
    contexts = {}
    has_count = any(q['question_type'] == 'object_counting' for q in qs)
    for gname, geom in geoms.items():
        for arm, ident in [(x, i) for x in a.arms for i in (('u', 'm') if has_count else ('u',))]:
            src, _, suf = arm.rpartition('_')
            if suf not in SUFFIX:
                src, suf = arm, None
            mode = suf if suf in ('e1', 'e2', 'edge', 'dc') else 'dc' if suf == 'ppdc' else None
            if ident == 'm' and src not in arms_m:
                contexts[(gname, arm, 'm')] = contexts[(gname, arm, 'u')]
                continue
            insts, name2ids, nid = {}, {}, 0
            for n, lst in (arms[src] | arms_m[src] if ident == 'm' else arms[src]).items():
                ids = []
                for fr in lst:
                    if suf in ('pp', 'ppdc'):
                        fr = {**fr, **propagate(geom, fr)}
                    insts[nid] = fr
                    ids.append(nid)
                    nid += 1
                name2ids[n] = ids
            if ident == 'u' and (gname == 'gtgeo' or suf in ('pp', 'ppdc')):
                for n, ids in name2ids.items():
                    gids = base.ids(n)
                    for k in range(1, 33):
                        gm = [gt.inst[k-1] == i for i in gids]
                        gm = [m for m in gm if m.sum() >= MIN_PX]
                        pm = [insts[i][k] for i in ids if k in insts[i]]
                        if not gm and not pm:
                            continue
                        pairs = sorted(((iou(g, q), x, y) for x, g in enumerate(gm) for y, q in enumerate(pm)), reverse=True)
                        ux, uy = set(), set()
                        for v, x, y in pairs:
                            if v > .5 and x not in ux and y not in uy:
                                ux.add(x); uy.add(y)
                        recall.append(dict(scene=scene, name=n, geom=gname, arm=arm, k=k, gt=len(gm), pred=len(pm), tp=len(ux)))
            contexts[(gname, arm, ident)] = PredCtx(geom, insts, name2ids, mode)
    for q in qs:
        d = D.get(str(q['id']))
        want = 'm' if q['question_type'] == 'object_counting' else 'u'
        for (gname, arm, ident), ctx in contexts.items():
            if ident != want:
                continue
            try:
                if any(n not in ctx.name2ids for n in CD.item_names(V.T.parse_vsi(q))):
                    pred = None  # a named object without a re-cache phrase or candidates: no program answer
                else:
                    pred, _ = V.run_vsi(q, ctx)
                    pred = V.finalize(q['question_type'], pred, ctx.fixes)
            except Exception:  # noqa: BLE001 - scored as no answer
                pred = None
            s = C.score(q['question_type'], pred, q['ground_truth'])
            rows.append(dict(id=str(q['id']), type=q['question_type'], scene=scene, geom=gname, arm=arm, pred=pred, score=s,
                             none=pred is None, fb=(d if pred is None and d is not None else s)))
    return rows, recall, mstats


def init(a):
    global ARGS
    ARGS = a


def main():
    import common as C
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--set', default='vsi')
    ap.add_argument('--table', default='/scratch/jjyeung/orch_cd/grd_selector/work/setsel/data/vsi_tab.jsonl')
    ap.add_argument('--probs', required=True)
    ap.add_argument('--key', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--scenes', nargs='*')
    ap.add_argument('--arms', default=','.join(ARMS))
    a = ap.parse_args()
    a.arms = a.arms.split(',')
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    a.probs_d = json.load(open(a.probs))[a.key]
    objs, cands = L.load(a.table)
    qs = [q for q in C.vsi_items() if q['dataset'] == 'scannet' and q['question_type'] in CD.PROG_TYPES
          and (CD.RAW[a.set]/f"scannet__{q['scene_name']}.npz").exists()]
    if a.scenes:
        qs = [q for q in qs if q['scene_name'] in a.scenes]
    import tplib as T
    counting = {f"scannet/{q['scene_name']}::{n}" for q in qs if q['question_type'] == 'object_counting' for n in CD.item_names(T.parse_vsi(q))}
    for oid, o in objs.items():
        o['_counting'] = oid in counting
    a.direct = {}
    for l in open(C.D_VSI):
        r = json.loads(l)
        a.direct[str(r['raw_id'])] = r['score']
    by = defaultdict(list)
    for q in qs:
        by[q['scene_name']].append(q)
    jobs = []
    for s, qq in sorted(by.items(), key=lambda kv: -len(kv[1])):
        so = {k: v for k, v in objs.items() if v['scene'] == f'scannet/{s}'}
        jobs.append((s, qq, so, {k: cands.get(k, []) for k in so}))
    rows, recall, mstats = [], [], []
    with Pool(a.workers, initializer=init, initargs=(a,)) as p:
        for i, (r, rc, ms) in enumerate(p.imap_unordered(scene_job, jobs), 1):
            rows += r; recall += rc; mstats += ms
            print('SCENE', i, len(jobs), flush=True)
    for name, v in (('rows', rows), ('recall', recall), ('mask_stats', mstats)):
        with open(out/f'{name}.jsonl', 'w') as f:
            for r in v:
                f.write(json.dumps(r, default=float)+'\n')
    print(json.dumps(dict(rows=len(rows), recall=len(recall), mask_stats=len(mstats))))


if __name__ == '__main__':
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    main()
