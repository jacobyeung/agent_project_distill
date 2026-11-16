import math
import numpy as np
from scipy import ndimage
from compat import tower, cache

FORBIDDEN = ('on_target', 'gt_label', 'target', 'v3_slots', 'label', 'visible', 'adjudicated')

MAX_PIXELS = 300

def logit(p):
    p = min(max(float(p), 1e-6), 1-1e-6)
    return math.log(p/(1-p))

def box_iou(a, b):
    ix = max(0., min(a[2], b[2])-max(a[0], b[0]))
    iy = max(0., min(a[3], b[3])-max(a[1], b[1]))
    inter = ix*iy
    union = (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    return inter/union if union > 0 else 0.

def mask_box(m):
    """Mask bounding box in the 0..1000 frame convention of the V3 boxes and the heads."""
    r, c = np.nonzero(m)
    return [c.min()/W*1000, r.min()/H*1000, (c.max()+1)/W*1000, (r.max()+1)/H*1000]

def mask_uv(m, rng):
    er = ndimage.binary_erosion(m, structure=np.ones((3, 3)))
    r, c = np.nonzero(er if er.sum() >= 10 else m)
    if len(r) > MAX_PIXELS:
        keep = rng.choice(len(r), MAX_PIXELS, replace=False)
        r, c = r[keep], c[keep]
    uv = np.column_stack(((c+.5)/W*1000, (r+.5)/H*1000))
    return uv[((uv >= 20) & (uv <= 980)).all(1)]

def project(geo, k, X):
    """Inverse of PerFrameHeadSource.lift: world point -> (u, v, z) in frame k (1-based)."""
    g = k-1
    pc = (np.asarray(X, float)-geo.t[g])@geo.r[g]
    fh, fw = geo.fov[g]
    z = pc[..., 2]
    u = 500*(pc[..., 0]/z/math.tan(fw/2)+1)
    v = 500*(pc[..., 1]/z/math.tan(fh/2)+1)
    return u, v, z

def lift_member(geo, slot, m, rng):
    uv = mask_uv(m, rng)
    if not len(uv):
        return np.empty((0, 3))
    P, Pc, spread = geo.lift(slot+1, uv, mode='center')
    ok = np.isfinite(P).all(1) & (Pc[:, 2] > 0) & np.isfinite(spread) & (spread <= .25)
    return P[ok]

class Scene:
    """Per-scene caches: SAM 3 raw instances per (slot, phrase) and the tower heads."""

    def __init__(self, scene, raw_path):
        from rk.programs import load_heads
        self.raw = cache(raw_path)
        self.geo = load_heads(HEADS/(scene.replace('/', '__')+'.npz'))
        self._masks = {}

    def instances(self, slot, phrase):
        key = (slot, phrase)
        if key not in self._masks:
            rec = self.raw['frames'][str(slot)]['phrases'].get(phrase, {})
            self._masks[key] = [(float(i['score']), tower().rle_decode(i['mask'])) for i in rec.get('instances', [])]
        return self._masks[key]

    def sam_presence(self, slot, phrase):
        return float(self.raw['frames'][str(slot)]['phrases'].get(phrase, {}).get('presence', 0.))

def reprojection(sc, X, phrase, boxes_by_slot, own_slots):
    """Frames where the candidate's 3D centre is in view and unoccluded; SAM / model-box hits there."""
    vis = det = box_hit = 0
    hit_scores, other_vis = [], 0
    for k in range(32):
        u, v, z = project(sc.geo, k+1, X)
        if not (z > .1 and 20 <= u <= 980 and 20 <= v <= 980):
            continue
        d = float(sc.geo._depth(k, np.array([u]), np.array([v]))[0])
        if z > d*1.15+.3:
            continue
        vis += 1
        other_vis += k not in own_slots
        r, c = int(v/1000*H), int(u/1000*W)
        r0, r1, c0, c1 = max(r-6, 0), min(r+7, H), max(c-6, 0), min(c+7, W)
        hits = [s for s, m in sc.instances(k, phrase) if m[r0:r1, c0:c1].any()]
        if hits:
            det += 1
            hit_scores.append(max(hits))
        if any(b[0] <= u <= b[2] and b[1] <= v <= b[3] for b in boxes_by_slot.get(k, [])):
            box_hit += 1
    return dict(reproj_vis=vis, reproj_vis_other=other_vis, reproj_det=det, reproj_det_ratio=det/vis if vis else 0.,
                reproj_box=box_hit, reproj_box_ratio=box_hit/vis if vis else 0.,
                reproj_hit_score=float(np.mean(hit_scores)) if hit_scores else 0.)

def object_rows(g, sc, v1, v2, presence, boxes, rng):
    phrase = g['candidates'][0]['mask_ref']['phrase']
    oid = g['object_id']
    bslot = {k: boxes.get((oid, k), []) for k in range(32)}
    out, cents = [], {}
    for c in g['candidates']:
        mem = c.get('members') or [c]
        masks = [(m['slot'], tower().rle_decode(
            sc.raw['frames'][str(m['slot'])]['phrases'][m['mask_ref']['phrase']]['instances'][m['mask_ref']['instance_index']]['mask']))
            for m in mem]
        scores = [float(sc.raw['frames'][str(m['slot'])]['phrases'][m['mask_ref']['phrase']]['instances'][m['mask_ref']['instance_index']]['score'])
                  for m in mem]
        areas = [float(m.mean()) for _, m in masks]
        ious, pys = [], []
        for k, m in masks:
            mb = mask_box(m) if m.any() else None
            ious.append(max([box_iou(mb, b) for b in bslot[k]], default=0.) if mb else 0.)
            pys.append(presence[oid, k])
        pts = [lift_member(sc.geo, k, m, rng) for k, m in masks]
        meds = [np.median(p, 0) for p in pts if len(p) >= 5]
        allp = np.concatenate([p for p in pts if len(p)]) if any(len(p) for p in pts) else np.empty((0, 3))
        f = dict(peak=c['peak'], logit_peak=logit(c['peak']), cand_presence=c['presence'], support=c['support'],
                 n_members=len(mem), exclusivity_margin=c['exclusivity_margin'],
                 inst_score_mean=float(np.mean(scores)), inst_score_max=float(np.max(scores)),
                 log_area_mean=math.log(max(np.mean(areas), 1e-6)), log_area_max=math.log(max(np.max(areas), 1e-6)),
                 sam_presence_members=float(np.mean([sc.sam_presence(k, phrase) for k, _ in masks])),
                 model_pyes_members=float(np.mean(pys)), model_pyes_members_max=float(np.max(pys)),
                 box_iou_mean=float(np.mean(ious)), box_iou_max=float(np.max(ious)),
                 box_iou_weighted=float(np.dot(ious, pys)/max(sum(pys), 1e-6)))
        for ck in ('base', 't0'):
            p = v1[ck][oid, c['candidate_id']]
            f[f'v1_{ck}'] = p
            f[f'logit_v1_{ck}'] = logit(p)
            f[f'v2_{ck}'] = v2[ck][oid, c['candidate_id']]['prob'] if (oid, c['candidate_id']) in v2[ck] else 0.
        if meds:
            X = np.median(np.stack(meds), 0)
            spread = float(max(np.linalg.norm(m-X) for m in meds))
            ext = np.sort(np.percentile(allp, 90, 0)-np.percentile(allp, 10, 0))[::-1]
            f.update(has_3d=1., member_spread_m=spread if len(meds) > 1 else 0., multi_view_3d=float(len(meds) > 1),
                     log_extent_max=math.log(max(ext[0], 1e-2)), log_extent_mid=math.log(max(ext[1], 1e-2)),
                     **reprojection(sc, X, phrase, bslot, {k for k, _ in masks}))
            cents[c['candidate_id']] = X
        else:
            f.update(has_3d=0., member_spread_m=0., multi_view_3d=0., log_extent_max=0., log_extent_mid=0.,
                     reproj_vis=0, reproj_vis_other=0, reproj_det=0, reproj_det_ratio=0., reproj_box=0,
                     reproj_box_ratio=0., reproj_hit_score=0.)
        out.append(dict(object_id=oid, scene=g['scene'], name=g['name'], candidate_id=c['candidate_id'], features=f))
    top = max(g['candidates'], key=lambda c: (c['peak'], c['candidate_id']))['candidate_id']
    for r in out:
        X = cents.get(r['candidate_id'])
        others = [np.linalg.norm(X-Y) for cid, Y in cents.items() if cid != r['candidate_id']] if X is not None else []
        r['features']['dist_to_top_m'] = (float(np.linalg.norm(X-cents[top])) if X is not None and top in cents else 5.)
        r['features']['n_dupes_05m'] = float(sum(d < .5 for d in others))
        r['centre'] = X.tolist() if X is not None else None
    return out

def check(rows_):
    for r in rows_:
        bad = [k for k in r['features'] if any(t in k for t in FORBIDDEN)]
        if bad:
            raise ValueError(f'Label-like feature names {bad}')
        if not all(np.isfinite(v) for v in r['features'].values()):
            raise ValueError(f'Nonfinite feature in {r["object_id"]} {r["candidate_id"]}')
