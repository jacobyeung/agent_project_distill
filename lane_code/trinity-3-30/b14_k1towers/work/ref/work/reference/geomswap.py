"""Tower geometry under the fixed, fused programs (prog_v2, VSI_FIX / VSTI_FIX), on GT instance masks.

A condition is a '+'-joined tag list applied to the scene's GT source (GT masks always):
  dT / pT / kT     tower depth / tower pose / tower intrinsics (fov) instead of GT (absent = GT)
  stow sfit sgt    scale of the tower parts: as exported (frozen GT-free rule; default), one oracle scalar per scan
                   (median GT/tower depth over valid pixels, applied to tower depth and tower translations), or
                   oracle per frame (depth: per-frame median ratio; translations: Sim(3) scale of the trajectory)
  tw_<name>        tower export: vcd (own V-C depth head; default), g3t (G3T depth x scale), gtg (G3T depth, GT gravity)
  f_<rule>         fusion rule: all (default), best1, agree, agreeL, trim, align (see Fused below)
  dc / er2         per-mask depth cut (grd_selector rule) / 2-px erosion before lifting
  n_<model><v>     noise on GT geometry: grid<G> (depth sampled on a G x G grid, bilinear: edge blur), frs<s>
                   (per-frame log-normal depth scale), lf<s> (smooth multiplicative field), gs<s> (global scale),
                   rot<deg> (per-frame rotation about the camera centre), tr<cm> (per-frame translation, per axis)
Tower poses are aligned to the GT world by yaw + translation about the tower's own gravity (z-up in both), so the
tower's gravity and scale errors stay; distances, sizes, directions and room area are invariant to that alignment.
Seeds are per (scene, condition), so every condition is paired item by item."""
import math
import sys
import zlib

import numpy as np
from scipy import ndimage

sys.path[:0] = ['/scratch/jjyeung/orch_cd/gt_ceiling/work/tp', '/scratch/jjyeung/orch_cd/gt_ceiling/work/gl']
import programs as PR  # noqa: E402
import prog_v2 as V  # noqa: E402

TOWER = {'vcd': '/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_vcd/scannet__%s.npz',
         'g3t': '/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64/scannet__%s.npz',
         'gtg': '/scratch/jjyeung/orch_cd/ttower/work/geo/heads_g3s64_gtg/scannet__%s.npz'}
H, W = 240, 320


# ------------------------------------------------------------------------------------------------ tower inputs

def tower_raw(scene, name='vcd'):
    """Tower depth on the GT 240 x 320 raster (bilinear from the depth grid), c2w in the tower world, per-frame K."""
    z = np.load(TOWER[name] % scene)
    grid = z['depth_grid'].astype(np.float32)
    G = grid.shape[1]
    ys, xs = np.mgrid[0:H, 0:W]
    s = (G - 1) / 1000.0
    x = np.clip((xs + .5) / W * 1000 * s, 0, G - 1)
    y = np.clip((ys + .5) / H * 1000 * s, 0, G - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, G - 1), np.minimum(y0 + 1, G - 1)
    fx, fy = x - x0, y - y0
    D = (grid[:, y0, x0] * (1 - fx) * (1 - fy) + grid[:, y0, x1] * fx * (1 - fy) + grid[:, y1, x0] * (1 - fx) * fy
         + grid[:, y1, x1] * fx * fy).astype(np.float32)
    c2w = np.tile(np.eye(4), (32, 1, 1))
    c2w[:, :3, :3], c2w[:, :3, 3] = z['r_grav'], z['t_grav']
    Ks = np.tile(np.eye(3), (32, 1, 1))
    fh, fw = z['fov_hw'][:, 0], z['fov_hw'][:, 1]
    Ks[:, 0, 0], Ks[:, 1, 1] = W / 2 / np.tan(fw / 2), H / 2 / np.tan(fh / 2)
    Ks[:, 0, 2], Ks[:, 1, 2] = W / 2, H / 2
    return D, c2w, Ks


def depth_scales(gtd, tod, valid):
    """Per-scan and per-frame median GT/tower depth ratios over valid GT pixels."""
    per, allr = np.ones(len(gtd)), []
    for k in range(len(gtd)):
        if not valid[k]:
            continue
        m = gtd[k] > 0
        if m.sum() < 100:
            continue
        r = gtd[k][m] / np.maximum(tod[k][m], 1e-3)
        per[k] = np.median(r)
        allr.append(r[::7])
    return (float(np.median(np.concatenate(allr))) if allr else 1.0), per


def align_yaw(tc, gc, scale=1.0):
    """Yaw about z + translation mapping scale * tower centres onto GT centres (least squares on valid frames)."""
    a, b = scale * tc, gc
    am, bm = a.mean(0), b.mean(0)
    A, B = a[:, :2] - am[:2], b[:, :2] - bm[:2]
    th = math.atan2((A[:, 0] * B[:, 1] - A[:, 1] * B[:, 0]).sum(), (A * B).sum())
    Rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    return Rz, bm - Rz @ am


def sim_scale(tc, gc):
    """Scale of the yaw-only similarity that best maps tower centres to GT centres."""
    best = None
    for s in np.exp(np.linspace(np.log(.25), np.log(4), 241)):
        Rz, t = align_yaw(tc, gc, s)
        e = np.mean(np.sum((s * tc @ Rz.T + t - gc) ** 2, 1))
        best = (e, s) if best is None or e < best[0] else best
    s0 = best[1]
    for s in s0 * np.exp(np.linspace(-.02, .02, 81)):
        Rz, t = align_yaw(tc, gc, s)
        e = np.mean(np.sum((s * tc @ Rz.T + t - gc) ** 2, 1))
        best = (e, s) if e < best[0] else best
    return float(best[1])


def aligned_pose(tc2w, gc2w, valid, scale):
    """Tower c2w with translations x scale, aligned to the GT world by yaw + translation."""
    v = np.asarray(valid, bool)
    Rz, t = align_yaw(tc2w[v, :3, 3], gc2w[v, :3, 3], scale)
    out = tc2w.copy()
    out[:, :3, :3] = Rz @ tc2w[:, :3, :3]
    out[:, :3, 3] = scale * tc2w[:, :3, 3] @ Rz.T + t
    return out


# ------------------------------------------------------------------------------------------------ noise on GT geometry

def rng_for(scene, cond):
    return np.random.default_rng(zlib.crc32(f'{scene}|{cond}'.encode()))


def depth_grid_blur(D, G):
    """Sample each frame's depth at G x G nodes (holes filled from the nearest valid pixel), bilinear back."""
    out = np.zeros_like(D)
    ys, xs = np.mgrid[0:H, 0:W]
    s = (G - 1) / 1000.0
    x = np.clip((xs + .5) / W * 1000 * s, 0, G - 1)
    y = np.clip((ys + .5) / H * 1000 * s, 0, G - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, G - 1), np.minimum(y0 + 1, G - 1)
    fx, fy = x - x0, y - y0
    nu = np.clip((np.arange(G) / (G - 1) * 1000 / 1000 * W).astype(int), 0, W - 1)
    nv = np.clip((np.arange(G) / (G - 1) * 1000 / 1000 * H).astype(int), 0, H - 1)
    for k in range(len(D)):
        d = D[k]
        if not (d > 0).any():
            continue
        idx = ndimage.distance_transform_edt(d <= 0, return_distances=False, return_indices=True)
        f = d[idx[0], idx[1]]
        g = f[np.ix_(nv, nu)]
        out[k] = g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x1] * fx * (1 - fy) + g[y1, x0] * (1 - fx) * fy + g[y1, x1] * fx * fy
        out[k][d <= 0] = 0
    return out


def depth_noise(D, model, v, rng):
    D = D.copy()
    if model == 'grid':
        return depth_grid_blur(D, int(v))
    if model == 'frs':
        return D * np.exp(rng.normal(0, v, len(D)))[:, None, None].astype(np.float32)
    if model == 'gs':
        return D * np.float32(v)
    if model == 'lf':
        for k in range(len(D)):
            f = ndimage.zoom(rng.normal(0, v, (3, 4)), (H / 3, W / 4), order=3)[:H, :W]
            D[k] = D[k] * np.exp(f).astype(np.float32)
        return D
    raise ValueError(model)


def rotvec(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * Kx + (1 - math.cos(th)) * Kx @ Kx


def pose_noise(c2w, model, v, rng):
    out = c2w.copy()
    for k in range(len(c2w)):
        if model == 'rot':
            out[k, :3, :3] = rotvec(rng.normal(0, math.radians(v) / math.sqrt(3), 3)) @ c2w[k, :3, :3]
        elif model == 'tr':
            out[k, :3, 3] = c2w[k, :3, 3] + rng.normal(0, v / 100.0, 3)
        else:
            raise ValueError(model)
    return out


# ------------------------------------------------------------------------------------------------ geometry source

class Geo(PR.GTSource):
    """GTSource with swapped depth, pose and per-frame intrinsics; GT masks, validity and annotations unchanged."""

    def __init__(self, base, depth, c2w, Ks, rule='all', mods=()):
        self.__dict__.update(base.__dict__)
        self.depth, self.c2w = depth, c2w
        self.Ks = Ks if Ks is not None else np.tile(base.K, (len(depth), 1, 1))
        self.Kinvs = np.linalg.inv(self.Ks)
        self.rule, self.mods = rule, set(mods)

    def Kof(self, k):
        return self.Ks[k - 1]

    def lift(self, k, uv, mode='p30'):
        self.Kinv = self.Kinvs[k - 1]
        return PR.GTSource.lift(self, k, uv, mode)

    def dense(self, k, step=4):
        self.Kinv = self.Kinvs[k - 1]
        return PR.GTSource.dense(self, k, step)


def Kof(gt, k):
    return gt.Kof(k) if hasattr(gt, 'Kof') else gt.K


def depth_cut(m, D):
    """grd_selector depth_consistent: keep mask pixels inside the interior's P10 - 0.15 m .. P90 + 0.15 m."""
    inner = ndimage.binary_erosion(m, iterations=3)
    if inner.sum() < 20:
        inner = m
    d = D[inner]
    d = d[d > 0]
    if len(d) < 10:
        return m
    lo, hi = np.percentile(d, 10) - .15, np.percentile(d, 90) + .15
    keep = m & (D >= lo) & (D <= hi)
    return keep if keep.sum() >= 8 else m


def kabsch(A, B):
    """Rigid R, t minimising |R A + t - B|."""
    ca, cb = A.mean(0), B.mean(0)
    U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, cb - R @ ca


def icp_to(P, ref, iters=8, keep=.7, max_move=.5):
    """Trimmed point-to-point ICP of P onto ref; returns the transformed P (unchanged if the move exceeds max_move)."""
    from scipy.spatial import cKDTree
    tree = cKDTree(ref)
    rs = np.random.default_rng(0)
    Q = P[rs.choice(len(P), min(len(P), 400), replace=False)]
    Rt, tt = np.eye(3), np.zeros(3)
    for _ in range(iters):
        X = Q @ Rt.T + tt
        d, j = tree.query(X)
        sel = d <= np.quantile(d, keep)
        if sel.sum() < 6:
            break
        R, t = kabsch(X[sel], ref[j[sel]])
        Rt, tt = R @ Rt, R @ tt + t
    c = P.mean(0)
    if np.linalg.norm(c @ Rt.T + tt - c) > max_move:
        return P
    return P @ Rt.T + tt


class Fused(V.Fused):
    """prog_v2.Fused with per-frame intrinsics, per-mask depth cut / erosion, and a fusion rule:
      all     every frame's points (prog_v2)
      best1   only the frame with the largest mask
      agree   frames whose per-frame centre lies within 0.2 m + 0.5 x the median per-frame extent of the median centre
      agreeL  the same with 0.4 m + 1.0 x
      trim    all frames, then the P2..P98 range on each world axis
      align   each frame's points rigidly ICP-aligned (trimmed) onto the growing model, largest mask first"""

    def __init__(self, gt, min_px=V.MIN_PX, step=2, frames=None):
        self.gt, self.min_px = gt, min_px
        self.rule = getattr(gt, 'rule', 'all')
        mods = getattr(gt, 'mods', set())
        ys, xs = np.mgrid[0:H:step, 0:W:step]
        pix = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5, np.ones(xs.size)], 1)
        self.yx = (ys.ravel(), xs.ravel())
        self.frames = frames if frames is not None else [k for k in range(1, len(gt.valid) + 1) if gt.has(k)]
        self.pts, self.px, self._box, self._fused = {}, {}, {}, {}
        for k in self.frames:
            inst = gt.inst[k - 1]
            ids, cnt = np.unique(inst, return_counts=True)
            sub = inst[self.yx]
            D = gt.depth[k - 1]
            d = D[self.yx]
            R, t = gt.cam(k)
            rays = pix @ np.linalg.inv(Kof(gt, k)).T
            for i, n in zip(ids, cnt):
                if i < 0:
                    continue
                self.px.setdefault(int(i), {})[k] = int(n)
                if n < min_px:
                    continue
                if mods & {'dc', 'er2'}:
                    m = inst == i
                    if 'er2' in mods:
                        e = ndimage.binary_erosion(m, ndimage.generate_binary_structure(2, 1), iterations=2)
                        m = e if e.sum() >= 8 else m
                    if 'dc' in mods:
                        m = depth_cut(m, D)
                    sel = m[self.yx] & (d > 0)
                else:
                    sel = (sub == i) & (d > 0)
                if sel.sum() < 3:
                    continue
                P = (rays[sel] * d[sel][:, None]) @ R.T + t
                self.pts.setdefault(int(i), []).append((k, P, int(n)))

    def frame_points(self, i):
        return self.pts.get(i, [])

    def points(self, i):
        if i in self._fused:
            return self._fused[i]
        fr = self.pts.get(i)
        out = None
        if fr:
            r = self.rule
            if r == 'best1' or len(fr) == 1:
                out = max(fr, key=lambda x: x[2])[1]
            elif r in ('agree', 'agreeL'):
                cs = np.stack([np.median(P, 0) for _, P, _ in fr])
                ext = np.median([np.max(np.percentile(P, 90, 0) - np.percentile(P, 10, 0)) for _, P, _ in fr])
                c = np.median(cs, 0)
                a, b = (.2, .5) if r == 'agree' else (.4, 1.)
                ok = np.linalg.norm(cs - c, axis=1) <= a + b * ext
                if not ok.any():
                    ok = np.linalg.norm(cs - c, axis=1) <= np.min(np.linalg.norm(cs - c, axis=1))
                out = np.concatenate([P for (_, P, _), o in zip(fr, ok) if o])
            elif r == 'trim':
                P = np.concatenate([P for _, P, _ in fr])
                lo, hi = np.percentile(P, 2, 0), np.percentile(P, 98, 0)
                out = P[np.all((P >= lo) & (P <= hi), 1)]
            elif r == 'align':
                order = sorted(fr, key=lambda x: -x[2])
                model = order[0][1]
                parts = [model]
                for _, P, _ in order[1:]:
                    ref = np.concatenate(parts)
                    if len(ref) > 3000:
                        ref = ref[np.random.default_rng(1).choice(len(ref), 3000, replace=False)]
                    parts.append(icp_to(P, ref))
                out = np.concatenate(parts)
            else:
                out = np.concatenate([P for _, P, _ in fr])
        self._fused[i] = out
        return out


def project_frac(gt, k, P):
    R, t = gt.cam(k)
    Pc = (P - t) @ R
    z = Pc[:, 2]
    ok = z > 0.1
    if not ok.any():
        return 0.0
    uv = (Pc[ok] / z[ok, None]) @ Kof(gt, k).T
    inside = (uv[:, 0] >= 0) & (uv[:, 0] < gt.W) & (uv[:, 1] >= 0) & (uv[:, 1] < gt.H)
    return float(inside.sum()) / len(P)


def install():
    """Route prog_v2's fused geometry and projection through the per-frame-K, rule-aware versions."""
    V.Fused = Fused
    V.project_frac = project_frac


# ------------------------------------------------------------------------------------------------ conditions

def parse(cond):
    c = dict(d='G', p='G', k='G', s='tow', tw='vcd', f='all', mods=set(), noise=[])
    if cond in ('gt', ''):
        return c
    for tok in cond.split('+'):
        if tok in ('dT', 'pT', 'kT'):
            c[tok[0]] = 'T'
        elif tok in ('stow', 'sfit', 'sgt'):
            c['s'] = tok[1:]
        elif tok.startswith('tw_'):
            c['tw'] = tok[3:]
        elif tok.startswith('f_'):
            c['f'] = tok[2:]
        elif tok in ('dc', 'er2'):
            c['mods'].add(tok)
        elif tok.startswith('n_'):
            body = tok[2:]
            model = body.rstrip('0123456789.')
            c['noise'].append((model, float(body[len(model):])))
        else:
            raise ValueError('unknown token ' + tok)
    return c


class SceneGeo:
    """Per scene: GT source, tower inputs (lazy) and the scales; make(cond) returns the condition's Geo."""

    def __init__(self, scene, base):
        self.scene, self.base, self._tw = scene, base, {}

    def tower(self, name):
        if name not in self._tw:
            D, c2w, Ks = tower_raw(self.scene, name)
            b = self.base
            s_fit, s_frame = depth_scales(b.depth, D, b.valid)
            v = np.asarray(b.valid, bool)
            s_traj = sim_scale(c2w[v, :3, 3], b.c2w[v, :3, 3])
            self._tw[name] = dict(D=D, c2w=c2w, Ks=Ks, s_fit=s_fit, s_frame=s_frame, s_traj=s_traj)
        return self._tw[name]

    def make(self, cond):
        c = parse(cond) if isinstance(cond, str) else cond
        b = self.base
        depth, c2w, Ks = b.depth, b.c2w, None
        if 'T' in (c['d'], c['p'], c['k']):
            tw = self.tower(c['tw'])
            if c['d'] == 'T':
                sc = {'tow': 1.0, 'fit': tw['s_fit']}.get(c['s'])
                depth = tw['D'] * (np.float32(sc) if sc is not None else tw['s_frame'][:, None, None].astype(np.float32))
            if c['p'] == 'T':
                s = {'tow': 1.0, 'fit': tw['s_fit'], 'gt': tw['s_traj']}[c['s']]
                c2w = aligned_pose(tw['c2w'], b.c2w, b.valid, s)
            if c['k'] == 'T':
                Ks = tw['Ks']
        rng = rng_for(self.scene, cond if isinstance(cond, str) else repr(cond))
        for model, v in c['noise']:
            if model in ('rot', 'tr'):
                c2w = pose_noise(c2w, model, v, rng)
            else:
                depth = depth_noise(depth, model, v, rng)
        return Geo(b, depth, c2w, Ks, c['f'], c['mods'])
