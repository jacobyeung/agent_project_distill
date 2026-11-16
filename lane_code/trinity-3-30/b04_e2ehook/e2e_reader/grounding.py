"""Grounding socket for <ground obj=NAME mode="box"> and <gap ...> (stage 1).

Stage 1: frozen SAM 3 inside the artifact proposes candidates for the name as written, the
tree's candidate producer links them across frames, and the SELECTOR HEAD (a module of the
model) picks one candidate or "none" by argmax. The picked candidate's mask pixels in its best
frame (largest mask area) are unprojected with this read's geometry (G3T depth x the scale head);
points whose depth-stencil spread exceeds the frame's median spread are dropped (lift_bestspread),
and the printed box is a gravity-aligned minimum-area rectangle over the kept points with their
full height. No alias table, no depth cut, no fitted box policy, no accept threshold.
Stage 2 (brief 05) replaces `propose` + `select` by the own-encoder head behind the same socket.
"""
import numpy as np

PROVIDER_ID = 'e2e_minarea_bestspread_v1'


def _hull(points):
    """Monotone-chain convex hull of 2-D points (exact)."""
    P = sorted(set(map(tuple, np.asarray(points, float).tolist())))
    if len(P) <= 2:
        return np.asarray(P, float)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.asarray(lower[:-1] + upper[:-1], float)


def min_area_box(points):
    """Gravity-aligned box (world z up): minimum-area floor rectangle of all points (rotating
    edges of the convex hull) and the points' full height. Returns centre, lengths, axes."""
    P = np.asarray(points, float).reshape(-1, 3)
    P = P[np.isfinite(P).all(1)]
    if len(P) < 4:
        raise ValueError('box_needs_four_points')
    hull = _hull(P[:, :2])
    if len(hull) < 3:
        raise ValueError('degenerate_floor_footprint')
    best = None
    for i in range(len(hull)):
        e = hull[(i + 1) % len(hull)] - hull[i]
        n = np.linalg.norm(e)
        if n == 0:
            continue
        u = e / n
        v = np.array([-u[1], u[0]])
        a, b = hull @ u, hull @ v
        area = (a.max() - a.min()) * (b.max() - b.min())
        if best is None or area < best[0]:
            best = (area, u, v, a.min(), a.max(), b.min(), b.max())
    _, u, v, a0, a1, b0, b1 = best
    z0, z1 = P[:, 2].min(), P[:, 2].max()
    centre_xy = u * (a0 + a1) / 2 + v * (b0 + b1) / 2
    centre = np.array([centre_xy[0], centre_xy[1], (z0 + z1) / 2])
    lengths = np.array([a1 - a0, b1 - b0, z1 - z0])
    axes = np.array([[u[0], u[1], 0.], [v[0], v[1], 0.], [0., 0., 1.]])
    if not (lengths > 0).all():
        raise ValueError('degenerate_box')
    return dict(centroid=centre, axesLengths=lengths, normalizedAxes=axes)


class MinAreaBoxProvider:
    provider_id = PROVIDER_ID

    def __call__(self, name, obj, geometry, best):
        from trace_format.box_v313 import in_f1
        parts = [np.asarray(obj['points'].get(str(k), []), float).reshape(-1, 3) for k in obj['frames']]
        points = np.concatenate(parts) if parts else np.zeros((0, 3))
        raw = min_area_box(points)
        return in_f1(geometry, raw['centroid'], raw['axesLengths'], raw['normalizedAxes'])


def mask_pixels(mask):
    """Centres of every pixel of a boolean mask on the 0..1000 canvas of geometry.lift."""
    rows, cols = np.nonzero(mask)
    h, w = mask.shape
    return np.column_stack(((cols + .5) / w * 1000, (rows + .5) / h * 1000))


def lift_plain(name, masks, geometry):
    """Unproject every pixel of the selected mask in each frame with this read's geometry.
    Keeps finite points in front of the camera; no erosion, no canvas crop, no spread filter, no depth cut."""
    from .geometry import frame_count
    masks = np.asarray(masks, bool)
    if masks.ndim != 3 or masks.shape[0] != frame_count(geometry):
        raise ValueError('masks_must_be_frames_H_W')
    result = dict(name=name, seen=False, frames=[], visible=[], areas={}, points={})
    for k, mask in enumerate(masks, 1):
        if not mask.any() or not geometry.has(k):
            continue
        result['visible'].append(k)
        result['areas'][str(k)] = float(mask.mean())
        uv = mask_pixels(mask)
        if not len(uv):
            continue
        P, Pc, _ = (np.asarray(x, np.float64) for x in geometry.lift(k, uv, mode='center'))
        ok = np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
        if ok.any():
            result['frames'].append(k)
            result['points'][str(k)] = P[ok].tolist()
    if result['frames']:
        result['seen'] = True
        result['best'] = min(result['frames'], key=lambda k: (-result['areas'][str(k)], k))
    return result


def lift_bestspread(name, masks, geometry):
    """lift_plain, then box points from the best frame only (largest mask area among frames with lifted
    points), and in it only the points whose depth-stencil spread (geometry.lift's third output) is at most
    that frame's median spread. No fitted constant: the cut is the frame's own median. `frames`, `visible`
    and `best` stay lift_plain's, so the printed frame list is unchanged; the box reads points of `best` only."""
    r = lift_plain(name, masks, geometry)
    if not r['seen']:
        return r
    b = r['best']
    uv = mask_pixels(np.asarray(masks, bool)[b - 1])
    P, Pc, spread = (np.asarray(x, np.float64) for x in geometry.lift(b, uv, mode='center'))
    ok = np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
    P, spread = P[ok], spread[ok]
    return dict(r, points={str(b): P[spread <= np.median(spread)].tolist()})


class StageOneSocket:
    """instances(name) -> [{'instance_id', 'masks'}] (0 or 1 entries).

    propose(name) -> (candidates, inputs): the frozen SAM 3 tower run on this read's frames for
    the raw name, linked into cross-frame candidates; each candidate has 'candidate_id' and
    'masks' {frame: bool[H,W]}; `inputs` are the selector head's tensors for these candidates.
    select(inputs) -> int index into candidates, or -1 for "none" (argmax of the head's logits
    with a null slot)."""

    def __init__(self, propose, select, mask_shape, frames):
        self.propose, self.select, self.mask_shape, self.frames = propose, select, tuple(mask_shape), int(frames)
        self.queries = []

    def __call__(self, name):
        candidates, inputs = self.propose(name)
        choice = int(self.select(inputs)) if candidates else -1
        self.queries.append(dict(name=name, candidates=len(candidates), choice=choice))
        if choice < 0:
            return []
        cand = candidates[choice]
        masks = np.zeros((self.frames,) + self.mask_shape, bool)
        for frame, m in cand['masks'].items():
            masks[int(frame) - 1] = np.asarray(m, bool)
        return [dict(instance_id=str(cand['candidate_id']), masks=masks)]


def ground_session(geometry, socket):
    """A v3.14 Session (tree formatter) whose instances come from `socket` and are lifted with
    lift_bestspread; boxes from MinAreaBoxProvider."""
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting

    class E2EGroundSession(Session):
        def __init__(self):
            super().__init__(ground_lifting, geometry, None, instances=lambda name: (),
                             program_version='3.14', multi_instance=True, geometry_mode='sensor',
                             box_provider=MinAreaBoxProvider())
            self.socket = socket

        def _instances(self, name):
            result = []
            for entry in self.socket(name):
                lifted = lift_bestspread(name, entry['masks'], self.geometry)
                if lifted['seen']:
                    result.append(dict(lifted, instance_id=str(entry['instance_id']), first=min(lifted['frames'])))
            return sorted(result, key=lambda r: (r['first'], r['instance_id']))

    return E2EGroundSession()
