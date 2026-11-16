"""Fixed programs for the GT ladder (copy-and-change of programs.py v3.6/SPEC behaviour; one switch per fix).

Fixes (names used in FIXES):
  frameidx  VSTI obj-obj 'frame N of M' = the N-th sampled frame with a valid pose (benchmark rule), not round(N*31/(M-1)).
  axes      VSTI up/down = camera +y (down), near/far = camera +z depth, as the label rule; not world z / Euclidean range.
  memory    an object that is absent or under the click threshold in the asked frame is taken from the other sampled
            frames (fused instance points, carried into the asked frame's camera by pose); only instances whose fused
            points project inside the asked frame count.
  extent    whole-object geometry: fuse each instance's mask points over every sampled frame, fit a minimal oriented
            box, and measure box-to-box / camera-to-box distance on the benchmark's 5 cm box grid; size = longest box
            side; direction and route use box centres.
  px1       visibility at any pixel (the benchmark's rule) instead of the 154-pixel click floor.
  v313      SPEC v3.13 distance rule as specified: best-frame gravity box fit, sampled_box_512 (for comparison).
  v313f     v3.13 distance rule with the box fit to the instance's points fused over all sampled frames.
  all32     the click programs look at all 32 sampled frames, not only the 16 even anchors.
  vocab     VSI-Bench category words pool the raw ScanNet labels the benchmark counts under them (GT-adapter rule).
  round     camera displacement printed on the label's 0.1 m grid (other metric types are biased, so rounding costs).
  merge     counting merges lifted clicks from all 32 frames into 3D clusters (1.5 m, one sighting per frame).
  identity  counting counts distinct instances seen in any sampled frame (GT identity; B rung) instead of the
            0.6 m floor-plane merge of clicks.
Levels: 'C' = GT clicks (largest-mask interior point / edge points) in the frames the SPEC scheme picks; 'B' = GT
instance masks on every sampled frame (>= MIN_PX pixels), GT depth and pose, fused per instance.
"""
import json
import math
import sys

import numpy as np

import programs as PR  # noqa: E402
import tplib as T  # noqa: E402
import common as C  # noqa: E402
import scene_gt as SG  # noqa: E402

MIN_PX = PR.MIN_PX
MEM_FRAC = 0.3


class PxGround(PR.GTGround):
    """GT grounding with its own minimum mask size ('px1': any visible pixel, the benchmark's visibility rule)."""

    def __init__(self, gt, min_px):
        super().__init__(gt)
        self.min_px = min_px

    def masks(self, obj, k):
        key = (obj, k)
        if key not in self.cache:
            inst = self.gt.inst[k - 1]
            out = [(i, inst == i) for i in self.instances(obj)]
            self.cache[key] = sorted([(i, m) for i, m in out if m.sum() >= self.min_px], key=lambda im: -im[1].sum())
        return self.cache[key]


class Fused:
    """Per-instance world points fused over the sampled frames from the GT instance raster, GT depth and GT pose."""

    def __init__(self, gt, min_px=MIN_PX, step=2, frames=None):
        self.gt, self.min_px = gt, min_px
        H, W = gt.depth.shape[1:]
        ys, xs = np.mgrid[0:H:step, 0:W:step]
        self.pix = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5, np.ones(xs.size)], 1) @ gt.Kinv.T
        self.yx = (ys.ravel(), xs.ravel())
        self.frames = frames if frames is not None else [k for k in range(1, len(gt.valid) + 1) if gt.has(k)]
        self.pts, self.px = {}, {}
        self._box = {}
        for k in self.frames:
            inst = gt.inst[k - 1]
            ids, cnt = np.unique(inst, return_counts=True)
            sub = inst[self.yx]
            d = gt.depth[k - 1][self.yx]
            R, t = gt.cam(k)
            for i, n in zip(ids, cnt):
                if i < 0:
                    continue
                self.px.setdefault(int(i), {})[k] = int(n)
                if n < min_px:
                    continue
                m = (sub == i) & (d > 0)
                if m.sum() < 3:
                    continue
                P = (self.pix[m] * d[m][:, None]) @ R.T + t
                self.pts.setdefault(int(i), []).append(P)

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
                self._box[i] = SG.minimal_obb(P)
        return self._box[i]

    def seen(self, i, min_px=None):
        mp = self.min_px if min_px is None else min_px
        return any(n >= mp for n in self.px.get(i, {}).values())


def project_frac(gt, k, P):
    """Fraction of points in front of camera k that land inside its image."""
    R, t = gt.cam(k)
    Pc = (P - t) @ R
    z = Pc[:, 2]
    ok = z > 0.1
    if not ok.any():
        return 0.0
    uv = (Pc[ok] / z[ok, None]) @ gt.K.T
    inside = (uv[:, 0] >= 0) & (uv[:, 0] < gt.W) & (uv[:, 1] >= 0) & (uv[:, 1] < gt.H)
    return float(inside.sum()) / len(P)


# b08_headrows patch: vocab file lost with trinity-2-18; only the GT-ground arm uses it. Fail loudly if used.
try:
    VOCAB = json.load(open('/scratch/jjyeung/orch_cd/gt_ceiling/work/tp/vsi_scannet_vocab.json'))
except FileNotFoundError:
    VOCAB = None


def use_vocab(ground):
    """'vocab': a VSI-Bench category word covers every raw ScanNet label the benchmark pools under it (table = table,
    desk, coffee table, end table, folded table; chair = chair, office chair, armchair, ...), learned from meta_info counts."""
    base = ground.instances

    def instances(obj):
        if VOCAB is None:
            raise RuntimeError('vsi_scannet_vocab.json unavailable (b08 patch)')
        h = T.head_noun(obj)
        if h in VOCAB:
            labs = set(VOCAB[h])
            return [i for l in ground.by_label if l in labs for i in ground.by_label[l]]
        return base(obj)
    ground.instances = instances


class Ctx:
    def __init__(self, gts, fixes, level):
        self.gt, self.fixes, self.level = gts, set(fixes), level
        self.ground = PR.GTGround(gts)
        mp = 1 if 'px1' in self.fixes else MIN_PX
        self.fused = Fused(gts, min_px=mp) if (level == 'B' or 'memory' in self.fixes or 'extent' in self.fixes) else None
        if 'px1' in self.fixes:
            self.ground = PxGround(gts, 1)
        if 'vocab' in self.fixes:
            use_vocab(self.ground)

    def ids(self, name):
        return self.ground.instances(name)


def valid_rank_frame(gt, n):
    v = [k for k in range(1, 33) if gt.has(k)]
    return v[n - 1] if 0 < n <= len(v) else None


# ------------------------------------------------------------------------------------------------ VSTI

def vsti_instances(ctx, name, k):
    """Instances of `name` usable in frame k: visible >= MIN_PX there; with 'memory', else those whose fused points
    project inside frame k (largest fraction first)."""
    gt, F = ctx.gt, ctx.fused
    vis = [i for i, _ in ctx.ground.masks(name, k)]
    if vis or 'memory' not in ctx.fixes:
        return vis, 'mask'
    cands = []
    for i in ctx.ids(name):
        P = F.points(i)
        if P is not None:
            f = project_frac(gt, k, P)
            if f > MEM_FRAC:
                cands.append((f, i))
    return [i for _, i in sorted(cands, reverse=True)], 'memory'


def vsti_obj_points(ctx, name, k):
    """World points for `name` in frame k: the click/mask points of frame k (C/B), or fused points under 'extent'/'memory'."""
    ids, how = vsti_instances(ctx, name, k)
    if not ids:
        return None, None
    i = ids[0]
    if 'extent' in ctx.fixes:
        b = ctx.fused.box(i)
        return (None, None) if b is None else (C.box_grid(b), b)
    if how == 'memory':
        return ctx.fused.points(i), None
    var = 'mask' if ctx.level == 'B' else 'pts'
    sc = PR.Scene(ctx.gt, ctx.ground, var, 'spec')
    Pw, _, _ = sc.points(name, 'point', frames=[k])
    return (Pw if len(Pw) else None), None


def run_vsti(q, ctx):
    t, P = q['question_type'], T.parse_vsti(q)
    gt = ctx.gt
    if t in ('camera_displacement', 'camera_movement_direction'):
        sc = PR.Scene(gt, ctx.ground, 'pts', 'spec')
        return PR.run_vsti(q, sc), None
    if t.startswith('obj_obj') and 'frameidx' in ctx.fixes:
        k = valid_rank_frame(gt, P.get('k_raw', P['k']))
    else:
        k = P['k']
    if k is None or not gt.has(k):
        return None, 'no frame'
    R, c = gt.cam(k)
    if t == 'camera_obj_abs_dist' or t.startswith('camera_obj_rel_dist'):
        names = [P['obj']] if t == 'camera_obj_abs_dist' else P['cands']
        ds = []
        for n in names:
            A, _ = vsti_obj_points(ctx, n, k)
            ds.append(float(np.min(np.linalg.norm(A - c, axis=1))) if A is not None else np.inf)
        if t == 'camera_obj_abs_dist':
            return (ds[0] if np.isfinite(ds[0]) else None), None
        return (T.letter_of(q['options'], names[int(np.argmin(ds))]) if np.isfinite(ds).any() else None), None
    (A, ba), (B, bb) = vsti_obj_points(ctx, P['a'], k), vsti_obj_points(ctx, P['ref'], k)
    if A is None or B is None:
        return None, 'object missing'
    ca = (SG.box_corners(ba) if ba else A).mean(0) if 'extent' in ctx.fixes else np.median(A, 0)
    cb = (SG.box_corners(bb) if bb else B).mean(0) if 'extent' in ctx.fixes else np.median(B, 0)
    ac, bc = R.T @ (ca - c), R.T @ (cb - c)
    opts = {v.lower(): k_ for k_, v in T.option_texts(q['options']).items()}
    if t == 'obj_obj_relative_pos_lr':
        return opts.get('left' if ac[0] < bc[0] else 'right'), None
    if t == 'obj_obj_relative_pos_ud':
        up = ac[1] < bc[1] if 'axes' in ctx.fixes else ca[2] > cb[2]
        return opts.get('up' if up else 'down'), None
    near = ac[2] < bc[2] if 'axes' in ctx.fixes else np.linalg.norm(ca - c) < np.linalg.norm(cb - c)
    return opts.get('near' if near else 'far'), None


# ------------------------------------------------------------------------------------------------ VSI

MERGE_M = 1.5


def merge_count(ctx, name):
    """Clicks on every visible instance in all sampled frames, lifted; a sighting joins the nearest cluster whose mean
    lies within MERGE_M (3D) and that holds no sighting from the same frame, else starts a cluster (COMPOSED_TRACES
    'averaged centroid, 3D, 1.5 m' rule, all 32 frames instead of 16 anchors)."""
    clusters = []
    for k in range(1, len(ctx.gt.valid) + 1):
        if not ctx.gt.has(k):
            continue
        c = ctx.ground.get(name, k, 'all')
        if not c:
            continue
        Pw, _, _ = ctx.gt.lift(k, np.asarray(c, float))
        for p in Pw[np.isfinite(Pw).all(1)]:
            best = None
            for cl in clusters:
                d = np.linalg.norm(cl['s'] / cl['n'] - p)
                if d < MERGE_M and k not in cl['f'] and (best is None or d < best[0]):
                    best = (d, cl)
            if best:
                best[1]['s'] += p; best[1]['n'] += 1; best[1]['f'].add(k)
            else:
                clusters.append({'s': p.copy(), 'n': 1, 'f': {k}})
    return len(clusters)


def v313_box(ctx, name):
    """SPEC v3.13 '<ground mode=box>' with the frozen best-frame point fit: the frame with the largest mask of the
    name, its (2-px eroded) mask points lifted with depth and pose, a gravity-aligned box fit (programs.fit_gbox)."""
    best = None
    for k in range(1, len(ctx.gt.valid) + 1):
        if not ctx.gt.has(k):
            continue
        ms = ctx.ground.masks(name, k)
        if ms and (best is None or ms[0][1].sum() > best[1]):
            best = (k, ms[0][1].sum())
    if best is None:
        return None
    if 'v313f' in ctx.fixes:
        k = best[0]
        i = ctx.ground.masks(name, k)[0][0]
        Pf = ctx.fused.points(i)
        return PR.fit_gbox(Pf) if Pf is not None and len(Pf) >= 4 else None
    sc = PR.Scene(ctx.gt, ctx.ground, 'mask', 'spec')
    Pw, _, _ = sc.points(name, 'point', frames=[best[0]])
    return PR.fit_gbox(Pw) if len(Pw) >= 4 else None


def run_v313_distance(q, ctx, t, P):
    """v3.13 benchmark distance: sampled_box_512 between best-frame-fit boxes."""
    if t == 'object_abs_distance':
        a, b = v313_box(ctx, P['a']), v313_box(ctx, P['b'])
        return T.obb_closest([a], [b]) if a and b else None
    tg = v313_box(ctx, P['target'])
    ds = [T.obb_closest([tg], [o]) if tg and (o := v313_box(ctx, c)) else np.inf for c in P['cands']]
    return T.letter_of(q['options'], P['cands'][int(np.argmin(ds))]) if np.isfinite(ds).any() else None


def gbox_full(P, lo=0.0, hi=100.0):
    """Gravity-aligned box with configurable height percentiles (lo/hi = 0/100 keeps the full fused height)."""
    b = PR.fit_gbox(P)
    z0, z1 = np.percentile(P[:, 2], lo), np.percentile(P[:, 2], hi)
    c = np.asarray(b['centroid'], float).copy(); c[2] = (z0 + z1) / 2
    L = np.asarray(b['axesLengths'], float).copy(); L[2] = max(z1 - z0, 0.02)
    return {'centroid': c, 'axesLengths': L, 'normalizedAxes': np.asarray(b['normalizedAxes'], float)}


def boxes_of(ctx, name):
    ids = [i for i in ctx.ids(name) if ctx.fused.seen(i)]
    if 'gbox' in ctx.fixes or 'gbox0' in ctx.fixes:
        out = []
        for i in ids:
            P = ctx.fused.points(i)
            if P is None or len(P) < 4:
                continue
            if len(P) > 4000:
                P = P[np.random.default_rng(0).choice(len(P), 4000, replace=False)]
            out.append(gbox_full(P, 0, 100) if 'gbox0' in ctx.fixes else PR.fit_gbox(P))
        return out
    out = [ctx.fused.box(i) for i in ids]
    return [b for b in out if b is not None]


def samp512(A, B):
    """SPEC v3.13 sampled_box_512 min over all instance pairs."""
    rng_pts = []
    best = None
    for a in A:
        for b in B:
            rng = np.random.Generator(np.random.PCG64(0))
            pts = []
            for o in (a, b):
                u = rng.uniform(-1.0, 1.0, size=(512, 3))
                R = np.asarray(o['normalizedAxes'], float).reshape(3, 3)
                pts.append((u * (np.asarray(o['axesLengths'], float) / 2.0)) @ R + np.asarray(o['centroid'], float))
            from scipy.spatial.distance import cdist
            d = float(cdist(*pts).min())
            best = d if best is None or d < best else best
    return best


def bdist(ctx, A, B):
    return samp512(A, B) if 'samp512' in ctx.fixes else C.box_box_dist(A, B)


def run_vsi(q, ctx):
    t, P = q['question_type'], T.parse_vsi(q)
    fx = ctx.fixes
    if t == 'object_counting' and 'identity' in fx:
        return sum(1 for i in ctx.ids(P['cat']) if ctx.fused.seen(i)), None
    if t == 'object_counting' and 'merge' in fx:
        return merge_count(ctx, P['cat']), None
    if 'v313' in fx and t in ('object_abs_distance', 'object_rel_distance'):
        return run_v313_distance(q, ctx, t, P), None
    if 'extent' in fx:
        if t == 'object_size_estimation':
            bs = boxes_of(ctx, P['a'])
            return (round(max(max(b['axesLengths']) for b in bs) * 100) if bs else None), None
        if t == 'object_abs_distance':
            a, b = boxes_of(ctx, P['a']), boxes_of(ctx, P['b'])
            return (bdist(ctx, a, b) if a and b else None), None
        if t == 'object_rel_distance':
            tg = boxes_of(ctx, P['target'])
            ds = [bdist(ctx, tg, o) if tg and (o := boxes_of(ctx, c)) else np.inf for c in P['cands']]
            return (T.letter_of(q['options'], P['cands'][int(np.argmin(ds))]) if np.isfinite(ds).any() else None), None
        if t.startswith('object_rel_direction'):
            cs = []
            for key in ('stand', 'face', 'query'):
                bs = boxes_of(ctx, P[key])
                if not bs:
                    return None, 'missing'
                cs.append(np.asarray(bs[0]['centroid']))
            th, _, _ = T.floor_angle(*cs)
            return T.letter_of(q['options'], T.direction_label(t, th)), None
    var = 'mask' if ctx.level == 'B' else 'pts'
    sc = PR.Scene(ctx.gt, ctx.ground, var, 'spec' if ctx.level == 'C' else 'fused')
    if 'all32' in fx or (ctx.level == 'B' and len(ctx.gt.valid) != 32):
        sc.anchors = [k for k in range(1, len(ctx.gt.valid) + 1) if ctx.gt.has(k)]
    return PR.run_vsi(q, sc, None), None


ROUND1 = {'camera_displacement'}


def finalize(t, pred, fixes):
    """'round': print metric answers on the label's own grid (0.1 m), as the benchmark rounds its labels."""
    if 'round' in fixes and t in ROUND1 and isinstance(pred, (int, float)) and pred is not None and np.isfinite(pred):
        return round(float(pred), 1)
    return pred
