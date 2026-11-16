import numpy as np
import selector_geom as PZ
from setlib import PFEATS
MAXPTS, REPROJ_D = 1500, 3.0

def geom_of(geom, masks):
    """masks {k(1-based): mask} -> (centre, extent, box lo, box hi, points sample) from tower lifting."""
    pts = [PZ.lift(geom, k, m) for k, m in masks.items() if k in geom.frames]
    pts = [x for x in pts if x is not None]
    if not pts:
        return None
    P = np.concatenate(pts)
    lo, hi = np.percentile(P, 10, 0), np.percentile(P, 90, 0)
    c = np.median(np.stack([np.median(x, 0) for x in pts]), 0)
    if len(P) > MAXPTS:
        P = P[np.random.default_rng(0).choice(len(P), MAXPTS, replace=False)]
    return c, float(np.max(hi-lo)), lo, hi, P

def box_iou(a, b):
    lo, hi = np.maximum(a[2], b[2]), np.minimum(a[3], b[3])
    inter = float(np.prod(np.clip(hi-lo, 0, None)))
    va, vb = float(np.prod(np.clip(a[3]-a[2], 1e-4, None))), float(np.prod(np.clip(b[3]-b[2], 1e-4, None)))
    return inter/(va+vb-inter), inter/min(va, vb)

def reproj(geom, P, masks):
    """Share of points P landing inside masks {k: mask} on visible pixels, averaged over frames with >= 20 hits in view."""
    vals = []
    for k, m in masks.items():
        if k not in geom.frames:
            continue
        x, y, z = geom.project(k, P)
        xi, yi = np.rint(x).astype(int), np.rint(y).astype(int)
        ok = (z > .1) & (xi >= 0) & (xi < PZ.W) & (yi >= 0) & (yi < PZ.H)
        if ok.sum() < 20:
            continue
        d = geom.depth(k)[yi[ok], xi[ok]]
        vis = (d <= 0) | (z[ok] <= d*1.05+.05)
        if vis.sum() < 20:
            continue
        vals.append(float(m[yi[ok][vis], xi[ok][vis]].mean()))
    return float(np.mean(vals)) if vals else 0.

def pair_features(ci, cj, mi, mj, gi, gj, geom):
    """ci, cj: table candidates; mi, mj: {k: mask}; gi, gj: geom_of results or None."""
    f = dict(peak_max=max(ci['features']['peak'], cj['features']['peak']), peak_min=min(ci['features']['peak'], cj['features']['peak']),
             logm_max=max(np.log1p(len(mi)), np.log1p(len(mj))), logm_min=min(np.log1p(len(mi)), np.log1p(len(mj))))
    if gi is not None and gj is not None:
        d = float(np.linalg.norm(gi[0]-gj[0]))
        iou3, ov3 = box_iou(gi, gj)
        f.update(has_c=1., d_c=d, d_rel=d/(.3+.5*max(gi[1], gj[1])), ext_max=max(gi[1], gj[1]), ext_min=min(gi[1], gj[1]),
                 box_iou3d=iou3, box_ov3d=ov3)
        if d < REPROJ_D:
            a, b = reproj(geom, gi[4], mj), reproj(geom, gj[4], mi)
            f.update(reproj_max=max(a, b), reproj_min=min(a, b))
    else:
        f.update(has_c=0., d_c=REPROJ_D*2, d_rel=10., ext_max=0., ext_min=0., box_iou3d=0., box_ov3d=0.)
    shared = sorted(set(mi) & set(mj))
    ious, ovs = [], []
    for k in shared:
        a, b = mi[k], mj[k]
        inter = float(np.logical_and(a, b).sum())
        ious.append(inter/max(float(np.logical_or(a, b).sum()), 1.))
        ovs.append(inter/max(min(float(a.sum()), float(b.sum())), 1.))
    f.update(n_shared=float(len(shared)), shared_frac=len(shared)/max(min(len(mi), len(mj)), 1), n_union=float(len(set(mi) | set(mj))),
             iou2d_max=max(ious, default=0.), iou2d_mean=float(np.mean(ious)) if ious else 0., ov2d_max=max(ovs, default=0.),
             ov2d_mean=float(np.mean(ovs)) if ovs else 0., n_disjoint=float(sum(o < .2 for o in ovs)),
             disjoint_frac=sum(o < .2 for o in ovs)/max(len(ovs), 1))
    f.setdefault('reproj_max', 0.)
    f.setdefault('reproj_min', 0.)
    return {k: float(f[k]) for k in PFEATS}
