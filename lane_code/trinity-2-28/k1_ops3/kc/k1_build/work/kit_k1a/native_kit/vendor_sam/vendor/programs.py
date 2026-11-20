"""toolprog executor: run every program under one condition (geometry source x grounding source).

Geometry sources (both give a z-up metric world W):
  heads  f17 readouts (work/heads/<ds>__<scene>.npz): W = frame-1 gravity reference; anchors 2..32 only.
  gt     ScanNet mesh raster (work/gt/scannet/<scene>.npz): W = raw ScanNet world; all 32 frames with a valid pose.
Grounding sources: gt (clicks/boxes from the GT instance raster), f17 / base (parsed LM outputs).
Variants: pts (clicks + depth_at) and box (box lifting + fitted gravity-aligned boxes).
Odd frames use anchor k+1 for head geometry (printed head gap); GT geometry uses the frame itself.
"""
import json
import math
import os
import re
import sys
from collections import defaultdict

import numpy as np

import tplib as T

W0 = '/scratch/jjyeung/orch_cd/toolprog/work'
MIN_PX = 154          # 0.2% of the 320x240 raster
PATCH = 10.0          # +-10 grid units
OUTLIER_M = 1.5


# ----------------------------------------------------------------------------------------------- geometry sources

class HeadSource:
    kind = 'heads'

    def __init__(self, path):
        z = np.load(path)
        self.r, self.t, self.fov = z['r_grav'], z['t_grav'], z['fov_hw']
        self.grid = z['depth_grid'].astype(np.float32)
        self.uv = z['grid_uv']
        self.G = self.grid.shape[1]

    def frame_of(self, k):
        """Anchor frame used for frame k (1-based)."""
        return k if k % 2 == 0 else min(k + 1, 32)

    def has(self, k):
        return True

    def _depth(self, g, u, v):
        s = (self.G - 1) / 1000.0
        x, y = np.clip(u * s, 0, self.G - 1), np.clip(v * s, 0, self.G - 1)
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        x1, y1 = np.minimum(x0 + 1, self.G - 1), np.minimum(y0 + 1, self.G - 1)
        fx, fy = x - x0, y - y0
        D = self.grid[g]
        return (D[y0, x0] * (1 - fx) * (1 - fy) + D[y0, x1] * fx * (1 - fy) + D[y1, x0] * (1 - fx) * fy + D[y1, x1] * fx * fy)

    def cam(self, k):
        g = self.frame_of(k) // 2 - 1
        return self.r[g], self.t[g]

    def lift(self, k, uv, mode='p30'):
        """uv [n,2] on the 0-1000 grid -> (P_W [n,3], P_cam [n,3], spread [n])."""
        g = self.frame_of(k) // 2 - 1
        uv = np.asarray(uv, float).reshape(-1, 2)
        offs = np.array([(dx, dy) for dx in np.linspace(-PATCH, PATCH, 5) for dy in np.linspace(-PATCH, PATCH, 5)])
        pu = np.clip(uv[:, None, 0] + offs[None, :, 0], 0, 1000)
        pv = np.clip(uv[:, None, 1] + offs[None, :, 1], 0, 1000)
        dp = self._depth(g, pu.ravel(), pv.ravel()).reshape(len(uv), -1)
        p20, p30, p50, p80 = (np.percentile(dp, q, axis=1) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / np.maximum(p50, 1e-3)
        d = p30 if mode == 'p30' else self._depth(g, uv[:, 0], uv[:, 1])
        fh, fw = self.fov[g]
        ray = np.stack([(uv[:, 0] / 500 - 1) * math.tan(fw / 2), (uv[:, 1] / 500 - 1) * math.tan(fh / 2), np.ones(len(uv))], 1)
        Pc = ray * d[:, None]
        return Pc @ self.r[g].T + self.t[g], Pc, spread

    def dense(self, k, step=4):
        g = self.frame_of(k) // 2 - 1
        idx = np.arange(0, self.G, step)
        u, v = np.meshgrid(self.uv[idx], self.uv[idx])
        return self.lift(k, np.stack([u.ravel(), v.ravel()], 1), mode='center')[0]

    def fov_of(self, k):
        return self.fov[self.frame_of(k) // 2 - 1]


class PerFrameHeadSource(HeadSource):
    """C1 per-frame carriers: one pose code per viewpoint 1..32 (layout 'per_frame'), so no odd-frame gap.
    Converted by c1_to_heads.py; W = viewpoint-1 gravity reference (own or GT gravity, recorded in 'gravity_source').
    depth_grid is optional (pose-only arms have no depth head; use the SW-gtdepth conditions)."""

    def __init__(self, path):
        z = np.load(path)
        self.r, self.t, self.fov = z['r_grav'], z['t_grav'], z['fov_hw']
        self.gravity_source = str(z['gravity_source'])
        self.grid = z['depth_grid'].astype(np.float32) if 'depth_grid' in z.files else None
        self.uv = z['grid_uv'] if 'grid_uv' in z.files else None
        self.G = None if self.grid is None else self.grid.shape[1]

    def frame_of(self, k):
        return k

    def _g(self, k):
        return k - 1

    def cam(self, k):
        return self.r[k - 1], self.t[k - 1]

    def fov_of(self, k):
        return self.fov[k - 1]

    def lift(self, k, uv, mode='p30'):
        if self.grid is None:
            raise ValueError('no own depth head in this export')
        g = k - 1
        uv = np.asarray(uv, float).reshape(-1, 2)
        offs = np.array([(dx, dy) for dx in np.linspace(-PATCH, PATCH, 5) for dy in np.linspace(-PATCH, PATCH, 5)])
        pu = np.clip(uv[:, None, 0] + offs[None, :, 0], 0, 1000)
        pv = np.clip(uv[:, None, 1] + offs[None, :, 1], 0, 1000)
        dp = self._depth(g, pu.ravel(), pv.ravel()).reshape(len(uv), -1)
        p20, p30, p50, p80 = (np.percentile(dp, q, axis=1) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / np.maximum(p50, 1e-3)
        d = p30 if mode == 'p30' else self._depth(g, uv[:, 0], uv[:, 1])
        fh, fw = self.fov[g]
        ray = np.stack([(uv[:, 0] / 500 - 1) * math.tan(fw / 2), (uv[:, 1] / 500 - 1) * math.tan(fh / 2), np.ones(len(uv))], 1)
        Pc = ray * d[:, None]
        return Pc @ self.r[g].T + self.t[g], Pc, spread

    def dense(self, k, step=4):
        idx = np.arange(0, self.G, step)
        u, v = np.meshgrid(self.uv[idx], self.uv[idx])
        return self.lift(k, np.stack([u.ravel(), v.ravel()], 1), mode='center')[0]


def load_heads(path):
    """f17 anchor exports (16 slots) or C1 per-frame exports (layout key 'per_frame')."""
    with np.load(path) as z:
        per_frame = 'layout' in z.files and str(z['layout']) == 'per_frame'
    return PerFrameHeadSource(path) if per_frame else HeadSource(path)


class GTSource:
    kind = 'gt'

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.depth, self.inst, self.K, self.c2w, self.valid = z['depth'], z['inst'], z['K'], z['c2w'], z['valid']
        self.ids, self.labels = z['ids'], [str(x) for x in z['labels']]
        self.obb = {int(i): {'centroid': c, 'axesLengths': l, 'normalizedAxes': a}
                    for i, c, l, a in zip(z['ids'], z['obb_centroid'], z['obb_lengths'], z['obb_axes'])}
        self.H, self.W = self.depth.shape[1:]
        self.Kinv = np.linalg.inv(self.K)

    def frame_of(self, k):
        return k

    def has(self, k):
        return bool(self.valid[k - 1])

    def cam(self, k):
        T4 = self.c2w[k - 1]
        return T4[:3, :3], T4[:3, 3]

    def px(self, uv):
        uv = np.asarray(uv, float).reshape(-1, 2)
        return (np.clip((uv[:, 0] / 1000.0 * self.W).astype(int), 0, self.W - 1),
                np.clip((uv[:, 1] / 1000.0 * self.H).astype(int), 0, self.H - 1))

    def lift(self, k, uv, mode='p30'):
        uv = np.asarray(uv, float).reshape(-1, 2)
        D = self.depth[k - 1]
        offs = np.array([(dx, dy) for dx in np.linspace(-PATCH, PATCH, 5) for dy in np.linspace(-PATCH, PATCH, 5)])
        pu = np.clip(uv[:, None, 0] + offs[None, :, 0], 0, 999.9)
        pv = np.clip(uv[:, None, 1] + offs[None, :, 1], 0, 999.9)
        xs, ys = self.px(np.stack([pu.ravel(), pv.ravel()], 1))
        dp = D[ys, xs].reshape(len(uv), -1).astype(float)
        dp[dp <= 0] = np.nan
        with np.errstate(all='ignore'):
            p20, p30, p50, p80 = (np.nanpercentile(dp, q, axis=1) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / np.maximum(p50, 1e-3)
        x, y = self.px(uv)
        dc = D[y, x].astype(float)
        d = p30 if mode == 'p30' else np.where(dc > 0, dc, np.nan)
        pix = np.stack([(x + 0.5), (y + 0.5), np.ones(len(x))], 1)
        Pc = (pix @ self.Kinv.T) * d[:, None]
        R, t = self.cam(k)
        return Pc @ R.T + t, Pc, spread

    def dense(self, k, step=4):
        D = self.depth[k - 1][::step, ::step]
        ys, xs = np.nonzero(D > 0)
        pix = np.stack([(xs * step + 0.5), (ys * step + 0.5), np.ones(len(xs))], 1)
        Pc = (pix @ self.Kinv.T) * D[ys, xs][:, None]
        R, t = self.cam(k)
        return Pc @ R.T + t


# ----------------------------------------------------------------------------------------------- grounding

def parse_points(text):
    """[[x, y], ...] from an LM reply (JSON point_2d objects or bare pairs); [] for null/none."""
    if text is None:
        return []
    pts = []
    for m in re.finditer(r'"point_2d"\s*:\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', text):
        pts.append([float(m.group(1)), float(m.group(2))])
    return [p for p in pts if 0 <= p[0] <= 1000 and 0 <= p[1] <= 1000 and max(p) > 10]


def parse_box(text):
    if text is None:
        return None
    m = re.search(r'"bbox_2d"\s*:\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', text)
    if not m:
        return None
    b = [float(g) for g in m.groups()]
    x1, y1, x2, y2 = min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3])
    if max(b) <= 10 or x2 - x1 < 1 or y2 - y1 < 1 or min(b) < 0 or max(b) > 1000:
        return None
    return [x1, y1, x2, y2]


SIZE_FIX = False  # run_conditions sets True for '-fix' conditions


class LMGround:
    def __init__(self, items_by_key, outputs):
        self.items, self.out = items_by_key, outputs

    def get(self, obj, k, kind, other=None):
        it = self.items.get((obj.lower(), k, kind, (other or '').lower()))
        if it is None:
            return None
        text = self.out.get(it['id'])
        return parse_box(text) if kind == 'box' else parse_points(text)


class GTGround:
    """Clicks and boxes from the GT instance raster (ScanNet)."""

    def __init__(self, gt):
        from scipy import ndimage
        self.gt, self.nd = gt, ndimage
        self.by_label = defaultdict(list)
        for i, l in zip(gt.ids, gt.labels):
            self.by_label[l].append(int(i))
        self.cache = {}

    def instances(self, obj):
        labs = T.match_labels(obj, list(self.by_label))
        return [i for l in labs for i in self.by_label[l]]

    def masks(self, obj, k):
        key = (obj, k)
        if key not in self.cache:
            inst = self.gt.inst[k - 1]
            out = []
            for i in self.instances(obj):
                m = inst == i
                if m.sum() >= MIN_PX:
                    out.append((i, m))
            self.cache[key] = sorted(out, key=lambda im: -im[1].sum())
        return self.cache[key]

    def to_uv(self, x, y):
        return [float((x + 0.5) / self.gt.W * 1000), float((y + 0.5) / self.gt.H * 1000)]

    def eroded(self, m):
        """Visible-surface mask minus 2 px: edge pixels of a raster mask can carry a neighbour's depth."""
        er = self.nd.binary_erosion(m, iterations=2)
        return er if er.sum() >= 8 else m

    def interior(self, m):
        dt = self.nd.distance_transform_edt(m)
        y, x = np.unravel_index(int(np.argmax(dt)), dt.shape)
        return self.to_uv(x, y)

    def get(self, obj, k, kind, other=None):
        ms = self.masks(obj, k)
        if not ms:
            return None if kind == 'box' else []
        if kind == 'box':
            ys, xs = np.nonzero(ms[0][1])
            return [xs.min() / self.gt.W * 1000, ys.min() / self.gt.H * 1000, (xs.max() + 1) / self.gt.W * 1000, (ys.max() + 1) / self.gt.H * 1000]
        if kind == 'point':
            return [self.interior(ms[0][1])]
        if kind == 'all':
            return [self.interior(m) for _, m in ms]
        er = self.eroded(ms[0][1])
        if kind == 'mask':
            ys, xs = np.nonzero(er)
            sel = np.linspace(0, len(xs) - 1, min(len(xs), 300)).astype(int)
            return [self.to_uv(x, y) for x, y in zip(xs[sel], ys[sel])]
        ys, xs = np.nonzero(er)
        sel = np.linspace(0, len(xs) - 1, min(len(xs), 400)).astype(int)
        uv = np.array([self.to_uv(x, y) for x, y in zip(xs[sel], ys[sel])])
        P, _, _ = self.gt.lift(k, uv, mode='center')
        ok = np.isfinite(P).all(1)
        uv, P = uv[ok], P[ok]
        if not len(P):
            return []
        if kind == 'ends':
            from scipy.spatial.distance import pdist, squareform
            Dm = squareform(pdist(P))
            i, j = np.unravel_index(int(np.argmax(Dm)), Dm.shape)
            return [uv[i].tolist(), uv[j].tolist()]
        if kind == 'edge':
            oi = self.instances(other)
            if not oi:
                return [self.interior(ms[0][1])]
            c = np.mean([self.gt.obb[i]['centroid'] for i in oi], 0)
            om = self.masks(other, k)
            if om:
                ys2, xs2 = np.nonzero(self.eroded(om[0][1]))
                sel2 = np.linspace(0, len(xs2) - 1, min(len(xs2), 400)).astype(int)
                Q, _, _ = self.gt.lift(k, np.array([self.to_uv(x, y) for x, y in zip(xs2[sel2], ys2[sel2])]), mode='center')
                Q = Q[np.isfinite(Q).all(1)]
            else:
                Q = c[None]
            from scipy.spatial import cKDTree
            d = cKDTree(Q).query(P)[0]
            order = np.argsort(d)[:3]
            return uv[order].tolist()
        return []


# ----------------------------------------------------------------------------------------------- object geometry

def robust(P):
    P = P[np.isfinite(P).all(1)]
    if len(P) < 3:
        return P
    med = np.median(P, 0)
    return P[np.linalg.norm(P - med, axis=1) < OUTLIER_M]


def fit_gbox(P):
    """Gravity-aligned box (z up) of a point set: min-area rectangle of the XY hull + z extent -> OBB dict."""
    from scipy.spatial import ConvexHull
    P = P[np.isfinite(P).all(1)]
    if len(P) < 4:
        c = P.mean(0) if len(P) else np.zeros(3)
        return {'centroid': c, 'axesLengths': np.array([0.05, 0.05, 0.05]), 'normalizedAxes': np.eye(3).ravel()}
    xy = P[:, :2]
    try:
        hull = xy[ConvexHull(xy).vertices]
    except Exception:
        hull = xy
    best = None
    for i in range(len(hull)):
        e = hull[(i + 1) % len(hull)] - hull[i]
        if np.linalg.norm(e) < 1e-9:
            continue
        a = math.atan2(e[1], e[0])
        R2 = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
        q = xy @ R2.T
        lo, hi = q.min(0), q.max(0)
        area = np.prod(hi - lo)
        if best is None or area < best[0]:
            best = (area, a, lo, hi)
    _, a, lo, hi = best
    z0, z1 = np.percentile(P[:, 2], 2), np.percentile(P[:, 2], 98)
    cxy = (lo + hi) / 2
    R2 = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
    c = np.array([*(R2.T @ cxy), (z0 + z1) / 2])
    axes = np.array([[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]])
    return {'centroid': c, 'axesLengths': np.array([hi[0] - lo[0], hi[1] - lo[1], max(z1 - z0, 0.02)]), 'normalizedAxes': axes.ravel()}


class Scene:
    """One scene under one condition: object point sets from (geometry source, grounding source, variant).

    scheme 'fused' pools an object's points over every anchor (through pose); scheme 'spec' follows SPEC v3 section 0:
    one frame that shows both objects (largest smaller-visible-size), else the pair (i, j) with the smallest
    r(i, j) = |move(i, j)| + |yaw(i, j)| / 50; direction/route take each object from its best single frame."""

    def __init__(self, geo, ground, variant, scheme='fused'):
        self.geo, self.gr, self.var, self.scheme = geo, ground, variant, scheme
        self.anchors = [k for k in range(2, 33, 2) if geo.has(k)]
        if variant == 'mask':
            self.anchors = [k for k in range(1, 33) if geo.has(k)]
        self.trace = []

    def vis(self, obj, k):
        """(visible, size as an image fraction) of obj in frame k as the grounding source reports it."""
        if isinstance(self.gr, GTGround):
            ms = self.gr.masks(obj, k)
            return (True, float(ms[0][1].sum()) / (self.gr.gt.H * self.gr.gt.W)) if ms else (False, 0.0)
        b = self.gr.get(obj, k, 'box')
        size = (b[2] - b[0]) * (b[3] - b[1]) / 1e6 if b else 0.0
        if self.var == 'box':
            return bool(b), size
        p = self.gr.get(obj, k, 'point')
        if SIZE_FIX and p and not b:
            size = self.point_size(k, p[0])
        return bool(p), size

    def point_size(self, k, uv):
        """Apparent-size proxy for point-only clicks (no box): centrality / own camera distance of the lifted click."""
        cen = 1.0 - min(1.0, math.hypot(uv[0] - 500.0, uv[1] - 500.0) / 707.1)
        try:
            _, Pc, _ = self.geo.lift(k, np.asarray([uv], float))
            d = float(Pc[0, 2])
        except Exception:
            d = float('nan')
        return cen / max(d, 0.3) if math.isfinite(d) and d > 0 else 0.1 * cen

    def r_pose(self, i, j):
        Ri, ci = self.geo.cam(i)
        Rj, cj = self.geo.cam(j)
        fi, fj = Ri[:2, 2], Rj[:2, 2]
        yaw = math.degrees(math.atan2(fi[0] * fj[1] - fi[1] * fj[0], fi[0] * fj[0] + fi[1] * fj[1]))
        return float(np.linalg.norm(cj - ci)) + abs(yaw) / 50.0

    def choose_frames(self, a, b):
        va = {k: self.vis(a, k) for k in self.anchors}
        vb = {k: self.vis(b, k) for k in self.anchors}
        both = [k for k in self.anchors if va[k][0] and vb[k][0]]
        if both:
            k = max(both, key=lambda k: (min(va[k][1], vb[k][1]), -k))
            return k, k, 'both'
        A = [k for k in self.anchors if va[k][0]]
        B = [k for k in self.anchors if vb[k][0]]
        if not A or not B:
            return None
        i, j = min(((i, j) for i in A for j in B), key=lambda p: (self.r_pose(*p), abs(p[0] - p[1])))
        return i, j, 'pair'

    def best_frame(self, obj):
        vs = [(self.vis(obj, k), k) for k in self.anchors]
        vs = [(v[1], -k) for v, k in vs if v[0]]
        return -max(vs)[1] if vs else None

    def points(self, obj, kind='point', other=None, frames=None):
        """W points of obj over frames (default all anchors) from clicks (pts) or boxes (box)."""
        out, spreads, used = [], [], []
        for k in (frames or self.anchors):
            if not self.geo.has(self.geo.frame_of(k)):
                continue
            if self.var == 'mask':
                c = self.gr.get(obj, k, 'mask')
                if not c:
                    continue
                P, _, _ = self.geo.lift(k, np.asarray(c, float), mode='center')
                out.append(P[np.isfinite(P).all(1)])
                used.append(k)
                continue
            if self.var == 'box':
                b = self.gr.get(obj, k, 'box')
                if not b:
                    continue
                xs, ys = np.meshgrid(np.linspace(b[0] + 0.1 * (b[2] - b[0]), b[2] - 0.1 * (b[2] - b[0]), 12),
                                     np.linspace(b[1] + 0.1 * (b[3] - b[1]), b[3] - 0.1 * (b[3] - b[1]), 12))
                P, Pc, _ = self.geo.lift(k, np.stack([xs.ravel(), ys.ravel()], 1), mode='center')
                ok = np.isfinite(Pc[:, 2])
                if ok.sum() < 4:
                    continue
                P, z = P[ok], Pc[ok, 2]
                P = P[z <= np.percentile(z, 60)]
                out.append(P)
            else:
                c = self.gr.get(obj, k, kind, other)
                if not c:
                    continue
                P, _, s = self.geo.lift(k, np.asarray(c, float))
                ok = np.isfinite(P).all(1)
                out.append(P[ok]); spreads += list(s[ok])
            used.append(k)
        P = np.concatenate(out) if out else np.zeros((0, 3))
        return robust(P), used, spreads

    def centroid(self, obj):
        frames = None
        if self.scheme == 'spec':
            k = self.best_frame(obj)
            if k is None:
                return None, []
            frames = [k]
        P, used, _ = self.points(obj, 'point', frames=frames)
        return (np.median(P, 0) if len(P) else None), used

    def pair_points(self, a, b, kind_a='point', kind_b='point'):
        """SPEC frame choice for two objects -> (A points, B points) in W, or (None, None)."""
        ch = self.choose_frames(a, b)
        if ch is None:
            return None, None
        i, j, why = ch
        self.trace.append((a, b, i, j, why))
        A, _, _ = self.points(a, kind_a, b if kind_a == 'edge' else None, frames=[i])
        B, _, _ = self.points(b, kind_b, a if kind_b == 'edge' else None, frames=[j])
        if not len(A) and kind_a != 'point':
            A, _, _ = self.points(a, 'point', frames=[i])
        if not len(B) and kind_b != 'point':
            B, _, _ = self.points(b, 'point', frames=[j])
        return A, B


# ----------------------------------------------------------------------------------------------- programs

def closest_sets(A, B):
    if not len(A) or not len(B):
        return None
    from scipy.spatial import cKDTree
    return float(cKDTree(A).query(B)[0].min())


def run_vsi(q, sc, extras):
    t, P = q['question_type'], T.parse_vsi(q)
    if t == 'object_counting' and isinstance(sc.gr, GTGround) and sc.scheme != 'spec':
        seen = {i for k in range(1, 33) if sc.geo.has(k) for i, _ in sc.gr.masks(P['cat'], k)}
        return len(seen)
    if t == 'object_counting':
        dets = []
        for k in sc.anchors:
            if sc.var == 'box':
                c = sc.gr.get(P['cat'], k, 'all') if isinstance(sc.gr, GTGround) else sc.gr.get(P['cat'], k, 'all')
            else:
                c = sc.gr.get(P['cat'], k, 'all')
            if c:
                W_, _, _ = sc.geo.lift(k, np.asarray(c, float))
                dets += [(k, p) for p in W_ if np.isfinite(p).all()]
        if not dets:
            return 0
        cents = []
        for k, p in dets:
            for c in cents:
                if np.linalg.norm(c['p'][:2] - p[:2]) < 0.6 and k not in c['frames']:
                    c['n'] += 1; c['p'] = c['p'] + (p - c['p']) / c['n']; c['frames'].add(k); break
            else:
                cents.append({'p': p.copy(), 'n': 1, 'frames': {k}})
        return len(cents)
    if t == 'object_abs_distance' and sc.scheme == 'spec':
        A, B = sc.pair_points(P['a'], P['b'], *(('point', 'point') if sc.var == 'box' else ('edge', 'edge')))
        if A is None or not len(A) or not len(B):
            return None
        if sc.var == 'box':
            return T.obb_closest([fit_gbox(A)], [fit_gbox(B)]) if len(A) >= 4 and len(B) >= 4 else closest_sets(A, B)
        return closest_sets(A, B)
    if t == 'object_rel_distance' and sc.scheme == 'spec':
        ds = []
        for c in P['cands']:
            A, B = sc.pair_points(P['target'], c)
            if A is None or not len(A) or not len(B):
                ds.append(np.inf)
            elif sc.var == 'box' and len(A) >= 4 and len(B) >= 4:
                ds.append(T.obb_closest([fit_gbox(A)], [fit_gbox(B)]))
            else:
                ds.append(closest_sets(A, B))
        if not np.isfinite(ds).any():
            return None
        return T.letter_of(q['options'], P['cands'][int(np.argmin(ds))])
    if t == 'object_abs_distance':
        if sc.var in ('box', 'mask'):
            A, _, _ = sc.points(P['a']); B, _, _ = sc.points(P['b'])
            if len(A) < 4 or len(B) < 4:
                return None
            return T.obb_closest([fit_gbox(A)], [fit_gbox(B)])
        A, _, _ = sc.points(P['a'], 'edge', P['b']); B, _, _ = sc.points(P['b'], 'edge', P['a'])
        if not len(A):
            A, _, _ = sc.points(P['a'])
        if not len(B):
            B, _, _ = sc.points(P['b'])
        return closest_sets(A, B)
    if t == 'object_size_estimation':
        if sc.var in ('box', 'mask'):
            A, _, _ = sc.points(P['a'])
            return None if len(A) < 4 else round(float(max(fit_gbox(A)['axesLengths'])) * 100)
        best = None
        for k in sc.anchors:
            c = sc.gr.get(P['a'], k, 'ends')
            if c and len(c) >= 2:
                W_, _, _ = sc.geo.lift(k, np.asarray(c[:2], float))
                if np.isfinite(W_).all():
                    d = float(np.linalg.norm(W_[0] - W_[1]))
                    best = d if best is None or d > best else best
        return None if best is None else round(best * 100)
    if t == 'room_size_estimation':
        return floor_area(sc)
    if t == 'object_rel_distance':
        ds = []
        for c in P['cands']:
            if sc.var in ('box', 'mask'):
                A, _, _ = sc.points(P['target']); B, _, _ = sc.points(c)
                ds.append(T.obb_closest([fit_gbox(A)], [fit_gbox(B)]) if len(A) >= 4 and len(B) >= 4 else np.inf)
            else:
                A, _, _ = sc.points(P['target'], 'point'); B, _, _ = sc.points(c, 'point')
                d = closest_sets(A, B)
                ds.append(np.inf if d is None else d)
        if not np.isfinite(ds).any():
            return None
        return T.letter_of(q['options'], P['cands'][int(np.argmin(ds))])
    if t.startswith('object_rel_direction'):
        cs = [sc.centroid(P[k])[0] if sc.var == 'pts' else box_centroid(sc, P[k]) for k in ('stand', 'face', 'query')]
        if any(c is None for c in cs):
            return None
        th, _, _ = T.floor_angle(*cs)
        return T.letter_of(q['options'], T.direction_label(t, th))
    if t == 'obj_appearance_order':
        firsts = []
        for c in P['cats']:
            f = next((k for k in range(1, 33) if sc.gr.get(c, k, 'point')), 99)
            firsts.append((f, c))
        rank = {c.lower(): i for i, (_, c) in enumerate(sorted(firsts, key=lambda x: x[0]))}
        best, bscore = None, -1
        for L_, txt in T.option_texts(q['options']).items():
            seq = [x.strip().lower() for x in txt.split(',')]
            agree = sum(1 for i in range(len(seq)) for j in range(i + 1, len(seq)) if rank.get(seq[i], 99) < rank.get(seq[j], 99))
            if agree > bscore:
                best, bscore = L_, agree
        return best
    if t == 'route_planning':
        return run_route(q, P, sc)
    return None


def box_centroid(sc, obj):
    frames = None
    if sc.scheme == 'spec':
        k = sc.best_frame(obj)
        if k is None:
            return None
        frames = [k]
    A, _, _ = sc.points(obj, frames=frames)
    return None if len(A) < 4 else fit_gbox(A)['centroid']


def run_route(q, P, sc, back=135.0):
    cen = lambda n: (sc.centroid(n)[0] if sc.var == 'pts' else box_centroid(sc, n))
    S, F = cen(P['start']), cen(P['face'])
    if S is None or F is None:
        return None
    if np.linalg.norm((F - S)[:2]) < 0.3:  # start == facing object: stand 1 m in front of it, toward the cameras
        cams = np.array([sc.geo.cam(k)[1] for k in sc.anchors])
        d = cams.mean(0)[:2] - S[:2]
        here = S.copy(); here[:2] = S[:2] + d / max(np.linalg.norm(d), 1e-6)
        heading = (S - here)[:2]
    else:
        here, heading = S, (F - S)[:2]
    turns, steps = [], P['plan']
    for i, (kind, obj) in enumerate(steps):
        if kind == 'go':
            nx = cen(obj)
            if nx is None:
                return None
            heading, here = (nx - here)[:2], nx
        elif kind == 'turn':
            nxt = next((o for k2, o in steps[i + 1:] if k2 == 'go'), None)
            nx = cen(nxt) if nxt else None
            if nx is None:
                return None
            lab, _ = T.turn_label(heading, (nx - here)[:2], back)
            turns.append(lab); heading = (nx - here)[:2]
    want = ', '.join(turns).lower()
    for L_, txt in T.option_texts(q['options']).items():
        if txt.lower().replace('.', '') == want:
            return L_
    return None


def floor_area(sc, cell=0.05):
    from scipy import ndimage
    pts = [sc.geo.dense(k) for k in sc.anchors]
    P = np.concatenate([p[np.isfinite(p).all(1)] for p in pts]) if pts else np.zeros((0, 3))
    if len(P) < 100:
        return None
    z = P[:, 2]
    P = P[(z > np.percentile(z, 1) - 0.1)]
    xy = P[:, :2]
    lo = xy.min(0)
    ij = ((xy - lo) / cell).astype(int)
    grid = np.zeros(ij.max(0) + 1, bool)
    grid[ij[:, 0], ij[:, 1]] = True
    r = int(round(0.2 / cell))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = xx ** 2 + yy ** 2 <= r * r
    grid = np.pad(grid, r + 1)
    grid = ndimage.binary_closing(grid, structure=disk)
    grid = ndimage.binary_fill_holes(grid)
    return float(grid.sum() * cell * cell)


def run_vsti(q, sc):
    t, P = q['question_type'], T.parse_vsti(q)
    if t in ('camera_displacement', 'camera_movement_direction'):
        i, j = P['i'], P['j']
        if not (sc.geo.has(sc.geo.frame_of(i)) and sc.geo.has(sc.geo.frame_of(j))):
            return None
        Ri, ci = sc.geo.cam(i)
        Rj, cj = sc.geo.cam(j)
        if t == 'camera_displacement':
            return float(np.linalg.norm(cj - ci))
        d_cam = Ri.T @ (cj - ci)  # in camera i (OpenCV): x right, z forward
        comp = {'forward': d_cam[2], 'backward': -d_cam[2], 'right': d_cam[0], 'left': -d_cam[0]}
        best = max(T.option_texts(q['options']).items(), key=lambda kv: comp.get(kv[1].strip().lower(), -1e9))
        return best[0]
    k = P['k']
    if not sc.geo.has(sc.geo.frame_of(k)):
        return None
    R, c = sc.geo.cam(k)

    def pts(obj):
        Pw, _, _ = sc.points(obj, 'point', frames=[sc.geo.frame_of(k)])
        return Pw

    if t == 'camera_obj_abs_dist':
        A = pts(P['obj'])
        return None if not len(A) else float(np.min(np.linalg.norm(A - c, axis=1)))
    if t.startswith('camera_obj_rel_dist'):
        ds = []
        for o in P['cands']:
            A = pts(o)
            ds.append(np.min(np.linalg.norm(A - c, axis=1)) if len(A) else np.inf)
        return None if not np.isfinite(ds).any() else T.letter_of(q['options'], P['cands'][int(np.argmin(ds))])
    A, B = pts(P['a']), pts(P['ref'])
    if not len(A) or not len(B):
        return None
    a, b = np.median(A, 0), np.median(B, 0)
    ac, bc = R.T @ (a - c), R.T @ (b - c)
    opts = {v.lower(): k_ for k_, v in T.option_texts(q['options']).items()}
    if t == 'obj_obj_relative_pos_lr':
        return opts.get('left' if ac[0] < bc[0] else 'right')
    if t == 'obj_obj_relative_pos_ud':
        return opts.get('up' if a[2] > b[2] else 'down')
    if t == 'obj_obj_relative_pos_nf':
        return opts.get('near' if np.linalg.norm(a - c) < np.linalg.norm(b - c) else 'far')
    return None
