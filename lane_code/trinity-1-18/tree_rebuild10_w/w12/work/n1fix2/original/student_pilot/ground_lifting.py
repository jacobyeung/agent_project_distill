"""Fixed v3.12.2 mask lifting; vendored rkit erosion, gates, ranking and box fit.

Geometry supplies lift(k, uv, mode='center') -> (world_z_up, camera_cv, spread)
and cam(k) -> (camera_to_world_rotation, camera_world_centre). No model state,
artifact paths, learned parameters or harness imports enter this module.
"""
import math
from trace_format.contracts import heading_available, status_text, new_contracts

VERSION = "3.12.2"
from trace_format.program_errors import ProgramRefusal
from decimal import Decimal

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull, cKDTree


def number(value):
    text = f'{float(value):.2f}'
    if not math.isfinite(float(value)):
        raise ValueError('Nonfinite grounding value')
    return '0.00' if text == '-0.00' else text


def mask_pixels(mask):
    mask = np.asarray(mask)
    if mask.dtype != bool or mask.ndim != 2:
        raise ValueError('Expected a boolean mask [H,W]')
    rows, cols = np.nonzero(ndimage.binary_erosion(mask, structure=np.ones((3, 3)), iterations=1))
    h, w = mask.shape
    uv = np.column_stack(((cols + .5) / w * 1000, (rows + .5) / h * 1000))
    return uv[((uv >= 20) & (uv <= 980)).all(1)]


def fit_gbox(points):
    """rkit minimum-area XY box and p2/p98 height; fail closed on degeneracy."""
    P = np.asarray(points, dtype=np.float64)
    if len(P) < 4 or not np.isfinite(P).all():
        raise ValueError('Degenerate mask box')
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
        R = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])
        q = xy @ R.T
        lo, hi = q.min(0), q.max(0)
        area = np.prod(hi - lo)
        if best is None or area < best[0]:
            best = (area, hi - lo)
    if best is None or best[0] <= 1e-12:
        raise ValueError('Degenerate mask box')
    z0, z1 = np.percentile(P[:, 2], (2, 98))
    return np.array([*best[1], max(z1 - z0, .02)])


def public_centres(geometry, frame, centre, *, metric_only=False):
    """Transform one W centroid into camera y-up and camera-1's level frame."""
    if not metric_only and not heading_available(geometry):
        raise ValueError('heading unavailable')
    R, t = (np.asarray(x, dtype=np.float64) for x in geometry.cam(frame))
    R1, t1 = (np.asarray(x, dtype=np.float64) for x in geometry.cam(1))
    if (R.shape != (3, 3) or R1.shape != (3, 3) or t.shape != (3,) or t1.shape != (3,)
            or not all(np.isfinite(x).all() for x in (R, t, R1, t1))):
        raise ValueError('Invalid geometry transforms')
    up = np.array([0., 0., 1.])
    if metric_only and new_contracts() and not heading_available(geometry):
        from trace_format.contracts import private_metric_basis
        basis = private_metric_basis(lambda k: geometry.cam(k)[0], up)
        if basis is not None:
            return (R.T @ (centre - t)) * [1, -1, 1], basis.T @ (centre - t1)
    heading = R1[:, 2].copy()
    heading -= (heading @ up) * up
    if np.linalg.norm(heading) < 1e-6:
        if not metric_only:
            raise ValueError('Undefined level basis')
        camera = (R.T @ (centre - t)) * [1, -1, 1]
        return camera, (centre - t1)[[0, 2, 1]]
    heading /= np.linalg.norm(heading)
    right = np.cross(heading, up)
    camera = (R.T @ (centre - t)) * [1, -1, 1]
    f1 = np.column_stack((right, up, heading)).T @ (centre - t1)
    return camera, f1


def interior_depths(mask, geometry, k, erode=3):
    """Camera depths of the mask interior (eroded `erode` px; the whole mask when that leaves < 20 px) at every
    interior pixel centre, before any crop: the gt_ceiling geomswap.depth_cut thresholds."""
    inner = ndimage.binary_erosion(mask, iterations=erode)
    if inner.sum() < 20:
        inner = mask
    rows, cols = np.nonzero(inner)
    h, w = mask.shape
    uv = np.column_stack(((cols + .5) / w * 1000, (rows + .5) / h * 1000))
    _, Pc, _ = (np.asarray(x, dtype=np.float64) for x in geometry.lift(k, uv, mode='center'))
    d = Pc[:, 2]
    return d[np.isfinite(d) & (d > 0)]


def depth_cut_keep(depth, interior, margin=0.15, min_keep=8):
    """Fusion-policy depth cut: keep lifted pixels whose camera depth lies inside the interior's
    [P10 - margin, P90 + margin]; all True when < 10 interior depths or < min_keep pixels survive."""
    if len(interior) < 10:
        return np.ones(len(depth), bool)
    lo, hi = np.percentile(interior, 10) - margin, np.percentile(interior, 90) + margin
    keep = (depth >= lo) & (depth <= hi)
    return keep if keep.sum() >= min_keep else np.ones(len(depth), bool)


def lift_object(name, masks, prob, geometry, *, tau, depth_cut=False):
    masks, prob = np.asarray(masks), np.asarray(prob, dtype=np.float64)
    if (masks.dtype != bool or masks.ndim != 3 or masks.shape[0] != 32 or min(masks.shape[1:]) < 1
            or prob.shape != (32,) or not np.isfinite(prob).all() or ((prob < 0) | (prob > 1)).any()
            or not math.isfinite(tau) or not 0 <= tau <= 1):
        raise ValueError('Invalid grounding masks, probability or tau')
    result = dict(name=name, seen=False, frames=[], visible=[], areas={}, points={})
    if depth_cut:
        # Box-only geometry for the predicted-mode fusion policy; frames, best, seen and enumeration use 'points'.
        result['points_cut'] = {}
    spreads = {}
    for k, mask in enumerate(masks, 1):
        if prob[k - 1] < tau or not mask.any() or not getattr(geometry, 'has', lambda _: True)(k):
            continue
        result['visible'].append(k)
        result['areas'][str(k)] = float(mask.mean())
        uv = mask_pixels(mask)
        if not len(uv):
            continue
        try:
            P, Pc, spread = (np.asarray(x, dtype=np.float64) for x in geometry.lift(k, uv, mode='center'))
            if P.shape != (len(uv), 3) or Pc.shape != P.shape or spread.shape != (len(uv),):
                raise ValueError('Invalid lifted mask shape')
            edge = np.minimum(uv, 1000 - uv).min(1)
            ok = (np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
                  & np.isfinite(spread) & (spread >= 0)
                  & (spread <= np.where(edge <= 40, .10, .25)))
            cut = None
            if depth_cut and ok.any():
                cut = ok & depth_cut_keep(Pc[:, 2], interior_depths(mask, geometry, k))
                if not cut.any():
                    cut = ok
        except ProgramRefusal:
            raise
        except (ValueError, FloatingPointError):
            continue
        if ok.any():
            result['frames'].append(k)
            result['points'][str(k)] = P[ok].tolist()
            if depth_cut:
                result['points_cut'][str(k)] = P[cut].tolist()
            spreads[k] = float(np.median(spread[ok]))
    if not result['frames']:
        return result
    best = min(result['frames'], key=lambda k: (-result['areas'][str(k)], k))
    P = np.asarray(result['points'][str(best)])
    try:
        centre = np.median(P, axis=0)
        if heading_available(geometry):
            camera, f1 = public_centres(geometry, best, centre)
        else:
            camera, f1 = public_centres(geometry, best, centre, metric_only=True)
            result['heading_unavailable'] = True
    except (ValueError, FloatingPointError):
        return result
    try:
        size = fit_gbox(P)
        size[:2] = sorted(size[:2], reverse=True)
        size = size.tolist()
    except (ValueError, FloatingPointError):
        size = None
    result.update(seen=True, best=best, prob=float(prob[best - 1]), camera=camera.tolist(),
                  f1=None if f1 is None else f1.tolist(), size=size, spread=spreads[best])
    return result


def render_ground(result, registry):
    if not result['seen']:
        return result['name'] + ': not seen'
    # Registry decimal arithmetic must consume exactly the displayed values.
    rounded = lambda xs: [number(x) for x in xs]
    extra = {'heading_defined': not result.get('heading_unavailable', False)} if new_contracts() else {}
    point = registry.register(camera=list(map(float, rounded(result['camera']))),
                              f1=list(map(float, rounded(result['f1']))),
                              spread=float(number(result['spread'])), requested_frame=result['best'],
                              **extra)
    frames = ','.join(map(str, result['frames']))
    size = 'size unavailable' if result['size'] is None else 'size ' + ' x '.join(rounded(result['size'])) + ' m'
    return (f"{result['name']}: frames {frames} (best {result['best']})\n"
            + point['line'] + '\n' + size)


def gap_objects(a, b, *, audit=None):
    if not a['seen'] or not b['seen']:
        return None
    common = set(a['visible']).intersection(b['visible'])
    if common:
        pairs = [(k, k) for k in sorted(common, key=lambda k:
                 (-min(a['areas'][str(k)], b['areas'][str(k)]), k))]
    else:
        pairs = []
    chosen = set(pairs)
    pairs.extend(sorted(((i, j) for i in a['visible'] for j in b['visible'] if (i, j) not in chosen),
                        key=lambda p: (abs(p[0] - p[1]), *p)))
    for i, j in pairs:
        A, B = a['points'].get(str(i), []), b['points'].get(str(j), [])
        if len(A) and len(B):
            distance = float(cKDTree(A).query(B)[0].min())
            if audit is not None:
                audit.append(dict(a=a['name'], b=b['name'], frames=[i, j], distance=distance))
            return distance
    return None


def render_gap(a, b, *, audit=None):
    distance = gap_objects(a, b, audit=audit)
    return 'not seen' if distance is None else number(distance) + ' m'


def render_gaps(a, candidates, *, audit=None):
    """Minimum over displayed Decimal gaps; retain every displayed tie."""
    if len(candidates) < 2 or len({b['name'] for b in candidates}) != len(candidates):
        raise ValueError('Multi-candidate gap requires distinct candidates')
    values = [gap_objects(a, b, audit=audit) for b in candidates]
    if any(value is None for value in values):
        return 'not seen'
    displayed = [number(value) for value in values]
    minimum = min(map(Decimal, displayed))
    names = [b['name'] for b, value in zip(candidates, displayed) if Decimal(value) == minimum]
    lines = [f"{b['name']}: {value} m" for b, value in zip(candidates, displayed)]
    lines.append('min ' + ','.join('"' + name + '"' for name in names) + f' {minimum:.2f} m')
    return '\n'.join(lines)


class OwnGeometryAdapter:
    """Unrounded centre-depth lifting through the existing own/tower read layer."""
    def __init__(self, geometry):
        self.geometry = geometry
        self.grids = {}

    def cam(self, frame):
        if self.geometry is None:
            raise ValueError('Coordinate basis unavailable')
        from trace_format.contracts import new_contracts
        p = self.geometry.camera_pose(frame) if new_contracts() else self.geometry.pose(frame)
        return p['camera_R_L1'][[0, 2, 1]], p['camera_t_L1'][[0, 2, 1]]

    def fov_of(self, frame):
        return self.geometry.fov(frame)

    def _depth(self, slot, u, v):
        frame = slot + 1
        if frame not in self.grids:
            axis = np.linspace(0, 1000, 51, dtype=np.float32)
            x, y = np.meshgrid(axis, axis)
            depth = np.asarray(self.geometry.depth(frame, np.column_stack((x.ravel(), y.ravel()))),
                               dtype=np.float32)
            if depth.shape != (2601,):
                raise ValueError('Invalid grounding depth grid')
            self.grids[frame] = depth.reshape(51, 51)
        x, y = np.clip(np.asarray(u) * .05, 0, 50), np.clip(np.asarray(v) * .05, 0, 50)
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        x1, y1 = np.minimum(x0 + 1, 50), np.minimum(y0 + 1, 50)
        fx, fy = x - x0, y - y0
        depth = self.grids[frame]
        return (depth[y0, x0] * (1-fx) * (1-fy) + depth[y0, x1] * fx * (1-fy)
                + depth[y1, x0] * (1-fx) * fy + depth[y1, x1] * fx * fy)

    def lift(self, frame, uv, mode='center'):
        if self.geometry is None:
            raise ValueError('Coordinate basis unavailable')
        if mode != 'center':
            raise ValueError('Grounding uses centre depth')
        uv = np.asarray(uv, dtype=np.float64)
        offsets = np.array([(dx, dy) for dx in np.linspace(-10, 10, 5)
                            for dy in np.linspace(-10, 10, 5)])
        stencil = np.clip(uv[:, None] + offsets, 0, 1000)
        # rkit exports V-C on a 51x51 endpoint grid and interpolates it. Keep
        # that depth substrate identical, rather than re-querying its MLP at
        # every mask pixel. Record one exact grid read per used frame for C2.
        def query(points):
            return self._depth(frame-1, *np.asarray(points).T)
        dp = query(stencil.reshape(-1, 2)).reshape(len(uv), 25)
        p20, p50, p80 = np.percentile(dp, (20, 50, 80), axis=1)
        spread = (p80 - p20) / np.maximum(p50, 1e-3)
        d = query(uv)
        vertical, horizontal = self.geometry.fov(frame)
        ray = np.column_stack(((uv[:, 0] / 500 - 1) * math.tan(horizontal / 2),
                               (uv[:, 1] / 500 - 1) * math.tan(vertical / 2), np.ones(len(uv))))
        Pc = ray * d[:, None]
        R, t = self.cam(frame)
        return Pc @ R.T + t, Pc, spread
