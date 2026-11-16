"""Metric object proposals, cross-view candidates, selection and MDG exports."""
from dataclasses import dataclass, field
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from scipy.special import expit

SHAPE = (80, 112)


@dataclass
class Proposal:
    frame: int
    index: int
    score: float
    presence: float
    mask: np.ndarray = field(repr=False)
    points: np.ndarray = field(repr=False)
    center: np.ndarray
    extent: float
    depth: float
    voxels: frozenset = field(repr=False)
    prior: float = 1.

    @property
    def joint(self):
        return self.score * self.presence


@dataclass
class Candidate:
    name: str
    id: str
    proposals: list
    features: dict = field(default_factory=dict)
    slot: int = -1

    @property
    def voxels(self):
        return frozenset().union(*(p.voxels for p in self.proposals))

    @property
    def center(self):
        return np.median([p.center for p in self.proposals], axis=0)


def small_rle(rle):
    """Exact ndimage.zoom(order=0) samples without materializing native masks."""
    h, w = rle['size']
    y = ndimage.zoom(np.arange(h), SHAPE[0]/h, order=0, prefilter=False)
    x = ndimage.zoom(np.arange(w), SHAPE[1]/w, order=0, prefilter=False)
    counts = np.asarray(rle['counts'], np.int64)
    if np.any(counts < 0) or counts.sum() != h*w:
        raise ValueError('Invalid RLE')
    if (h, w) not in {(480, 640), SHAPE}:
        full = np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')
        return ndimage.zoom(full, (SHAPE[0]/h, SHAPE[1]/w), order=0, prefilter=False)
    return (np.searchsorted(np.cumsum(counts), y[:, None]+x[None, :]*h,
                            side='right') % 2).astype(bool)


def voxel_set(points):
    return frozenset(map(tuple, np.floor(np.asarray(points)/.10).astype(np.int64)))


def lift_grid(geo):
    """Precompute the exact MaskGround lift/eligibility at every mask pixel."""
    rows, cols = np.indices(SHAPE)
    uv = np.column_stack(((cols.ravel()+.5)/SHAPE[1]*1000,
                          (rows.ravel()+.5)/SHAPE[0]*1000))
    edge = np.minimum(uv, 1000-uv).min(1)
    grids = {}
    for frame in range(1, 33):
        if not geo.has(frame):
            continue
        P, Pc, spread = geo.lift(frame, uv, mode='center')
        ok = (((uv >= 20) & (uv <= 980)).all(1) & np.isfinite(P).all(1)
              & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0) & np.isfinite(spread)
              & (spread <= np.where(edge <= 40, .10, .25)))
        grids[frame] = (P, Pc[:, 2], ok)
    return grids


def lift(cache, name, geo, floor=.3, prior=None, grids=None):
    """Lift every eligible cached proposal, preserving score-sorted local indices."""
    from compat import tower
    phrase = tower().phrase(name)
    if phrase not in cache['phrases']:
        return [], []
    grids = lift_grid(geo) if grids is None else grids
    out, rejected = [], []
    for frame in range(1, 33):
        record = cache['frames'][str(frame-1)]['phrases'][phrase]
        instances = sorted(record.get('instances') or [], key=lambda p: -float(p['score']))
        for index, instance in enumerate(instances):
            if float(instance['score']) < floor:
                continue
            mask = small_rle(instance['mask'])
            if frame not in grids:
                rejected.append(dict(frame=frame, index=index, reason='invalid_pose'))
                continue
            P, depth, valid = grids[frame]
            ok = ndimage.binary_erosion(mask, structure=np.ones((3, 3))).ravel() & valid
            points = P[ok]
            if not len(points):
                rejected.append(dict(frame=frame, index=index, reason='no_eligible_pixels'))
                continue
            center = np.median(points, axis=0)
            out.append(Proposal(frame, index, float(instance['score']), float(record['presence']),
                       mask, points, center, float(np.quantile(np.linalg.norm(points-center, axis=1), .9)),
                       float(np.mean(depth[ok])), voxel_set(points),
                       float(prior[frame-1]) if prior is not None else 1.))
    return out, rejected


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def root(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def join(self, a, b):
        a, b = self.root(a), self.root(b)
        if a != b:
            self.parent[max(a, b)] = min(a, b)

    def groups(self):
        out = {}
        for i in range(len(self.parent)):
            out.setdefault(self.root(i), []).append(i)
        return list(out.values())


def overlap(a, b):
    return len(a.intersection(b))/max(1, min(len(a), len(b)))


def linked(a, b):
    if a.frame == b.frame:
        return False
    radius = max(.30, .5*min(a.extent, b.extent)) + .05*(a.depth+b.depth)/2
    return np.linalg.norm(a.center-b.center) <= radius or overlap(a.voxels, b.voxels) >= .25


def link(proposals, name='object'):
    """Union cross-frame edges, then peel highest-joint members of repeated frames.

    Displaced proposals remain candidates. Every output has at most one mask per
    frame, and the induced graph is connected after each split.
    """
    n = len(proposals)
    edges, uf = [[] for _ in range(n)], UnionFind(n)
    for i in range(n):
        for j in range(i):
            if linked(proposals[i], proposals[j]):
                edges[i].append(j); edges[j].append(i); uf.join(i, j)
    result = []

    def components(indices):
        pending, out = set(indices), []
        while pending:
            todo = [min(pending)]; pending.remove(todo[0]); group = []
            while todo:
                i = todo.pop(); group.append(i)
                new = sorted(pending.intersection(edges[i]))
                pending.difference_update(new); todo.extend(new)
            out.append(sorted(group))
        return out

    for group in uf.groups():
        remaining = set(group)
        while remaining:
            chosen = {}
            for i in sorted(remaining, key=lambda i: (-proposals[i].joint, i)):
                chosen.setdefault(proposals[i].frame, i)
            kept = set(chosen.values())
            result.extend(components(kept))
            remaining.difference_update(kept)
    result.sort(key=lambda g: min(g))
    return [Candidate(name, f'{name}:{i:03d}', [proposals[j] for j in g])
            for i, g in enumerate(result)]


def visible_voxels(voxels, geo):
    points = (np.array(sorted(voxels), float)+.5)*.10
    visible = []
    if not len(points):
        return visible
    for frame in range(1, 33):
        if not geo.has(frame):
            continue
        r, t = geo.cam(frame)
        pc = (points-t) @ r
        fh, fw = geo.fov_of(frame)
        z = pc[:, 2]
        safe = np.where(z > 0, z, 1.)
        uv = (pc[:, :2]/safe[:, None]/np.tan(np.array([fw, fh])/2)+1)*500
        inside = (z > 0) & ((uv >= 0) & (uv <= 1000)).all(1) & np.isfinite(uv).all(1)
        good = np.zeros(len(points), bool)
        if inside.any():
            d = geo._depth(frame-1, uv[inside, 0], uv[inside, 1])
            good[inside] = np.isfinite(d) & (abs(z[inside]-d) <= np.maximum(.15, .10*d))
        if good.mean() >= .30:
            visible.append(frame)
    return visible


def features(candidate, geo=None):
    p = candidate.proposals
    joints = sorted([v.joint for v in p], reverse=True)
    prior_joints = sorted([v.joint*v.prior for v in p], reverse=True)
    support = len(p)
    visible = visible_voxels(candidate.voxels, geo) if geo is not None else [v.frame for v in p]
    best = min(p, key=lambda v: (-v.joint, v.frame, v.index))
    candidate.features.update(peak=float(np.mean(joints[:2])), support=support,
        consensus=support/max(1, len(visible)), visibility_frames=visible,
        visible_count=len(visible), best_view_area=max(float(v.mask.mean()) for v in p),
        prior_peak=float(np.mean(prior_joints[:2])), best_presence=best.prior,
        representative_frame=best.frame, representative_index=best.index,
        exclusivity_margin=0.)
    return candidate.features


def scene_candidates(by_name, geo=None):
    """Attach shared physical-object slots across names for exclusivity."""
    flat = [c for cs in by_name.values() for c in cs]
    for c in flat:
        features(c, geo)
    uf = UnionFind(len(flat))
    voxels = [c.voxels for c in flat]
    centers = [c.center for c in flat]
    depths = [float(np.mean([p.depth for p in c.proposals])) for c in flat]
    extents = [float(np.median([p.extent for p in c.proposals])) for c in flat]
    for i, a in enumerate(flat):
        for j, b in enumerate(flat[:i]):
            if a.name == b.name:
                continue
            radius = max(.30, .5*min(extents[i], extents[j])) + .025*(depths[i]+depths[j])
            if np.linalg.norm(centers[i]-centers[j]) <= radius or overlap(voxels[i], voxels[j]) >= .25:
                uf.join(i, j)
    for slot, group in enumerate(uf.groups()):
        for i in group:
            flat[i].slot = slot
            rivals = [flat[j].features['peak'] for j in group if flat[j].name != flat[i].name]
            flat[i].features['exclusivity_margin'] = flat[i].features['peak']-max(rivals, default=0.)
    return by_name


def select(by_name, rule='seed', threshold=0., order=None, prior=False, external=None,
           weights=None, oracle_scores=None, k=None):
    """Select candidates. Oracle scores must be explicitly supplied by a diagnostic caller."""
    if rule not in {'seed', 'seed_excl', 'seed_excl_fwd', 'fused', 'oracle', 'oracle_topk'}:
        raise ValueError('Unknown selector '+rule)
    if rule in {'oracle', 'oracle_topk'} and oracle_scores is None:
        raise ValueError('Oracle selection requires explicit diagnostic scores')
    if rule == 'fused' and weights is None:
        raise ValueError('Fused selection requires frozen weights')
    feature = 'prior_peak' if prior else 'peak'

    def score(c):
        if rule == 'fused':
            x = dict(c.features, **(external or {}).get(c.id, {}))
            return float(expit(weights.get('intercept', 0.) + sum(
                value*float(x[key]) for key, value in weights.items() if key != 'intercept')))
        return c.features[feature]

    ranked = {name: sorted(cs, key=lambda c: (-score(c), c.id)) for name, cs in by_name.items()}
    if rule in {'oracle', 'oracle_topk'}:
        out = {}
        for name, cs in ranked.items():
            eligible = cs if rule == 'oracle' or k is None else cs[:k]
            eligible = [c for c in eligible if oracle_scores.get(c.id, 0.) > 0]
            out[name] = min(eligible, key=lambda c: (-oracle_scores[c.id], -score(c), c.id)) if eligible else None
        return out
    if rule == 'seed_excl':
        names = list(by_name)
        slots = sorted({c.slot for cs in ranked.values() for c in cs})
        matrix = np.full((len(names), len(slots)+len(names)), -1e6)
        matrix[:, len(slots):] = threshold
        choices = {}
        col = {slot: i for i, slot in enumerate(slots)}
        for q, name in enumerate(names):
            for c in ranked[name]:
                j = col[c.slot]
                if score(c) > matrix[q, j]:
                    matrix[q, j] = score(c); choices[q, j] = c
        rows, cols = linear_sum_assignment(-matrix)
        out = dict.fromkeys(names)
        for q, j in zip(rows, cols):
            if j < len(slots) and matrix[q, j] >= threshold:
                out[names[q]] = choices[q, j]
        return out
    claimed, out = set(), {}
    for name in list(dict.fromkeys([*(order or []), *by_name])):
        eligible = [c for c in ranked[name] if score(c) >= threshold and
                    (rule != 'seed_excl_fwd' or c.slot not in claimed)]
        out[name] = eligible[0] if eligible else None
        if out[name] is not None:
            claimed.add(out[name].slot)
    return out


def empty_values(n):
    prob = np.zeros((n, 32), np.float32)
    return dict(prob=prob, frame_prob=prob.copy(), clip_prob=np.ones(n, np.float32),
                iou=prob.copy(), uv=np.zeros((n, 32, 2), np.float32),
                mask=np.zeros((n, 32)+SHAPE, bool), area=np.zeros((n, 32), np.float64))


def values_for(names, selected):
    values = empty_values(len(names))
    for q, name in enumerate(names):
        c = selected.get(name)
        if c is None:
            continue
        assert len({p.frame for p in c.proposals}) == len(c.proposals)
        for p in c.proposals:
            k = p.frame-1
            values['mask'][q, k] = p.mask
            values['prob'][q, k] = 1.
            values['iou'][q, k] = p.score
            row, col = np.unravel_index(np.argmax(ndimage.distance_transform_edt(p.mask)), SHAPE)
            values['uv'][q, k] = np.rint([(col+.5)/SHAPE[1]*1000, (row+.5)/SHAPE[0]*1000])
    values['area'] = values['mask'].mean(axis=(-1, -2))
    values['frame_prob'] = values['prob'].copy()
    return values


def ground_from_values(names, values, tau=.5, audit=None):
    """An in-memory MaskGround uses the unchanged kit implementation."""
    from rk.ground import MaskGround, mdg
    ground = MaskGround.__new__(MaskGround)
    ground.names, ground.values, ground.audit = names, values, audit or {}
    ground.by_name = {mdg().label(n): i for i, n in enumerate(names)}
    ground.tau, ground.geo, ground.cache = tau, None, {}
    return ground


def candidate_json(c):
    return dict(id=c.id, name=c.name, slot=c.slot, features=c.features, center=c.center.tolist(),
                proposals=[dict(frame=p.frame, index=p.index, score=p.score, presence=p.presence,
                    joint=p.joint, prior=p.prior, center=p.center.tolist(), extent=p.extent,
                    mean_depth=p.depth, eligible_points=len(p.points), voxels=len(p.voxels),
                    area=float(p.mask.mean())) for p in c.proposals])


def export(out, scene, names, selected, frame_indices, by_name=None, audit=None, values=None):
    from rk.ground import mdg
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    stem = scene.replace('/', '__')
    metadata = dict(tau=.5, source='ofs', gt_substitution=False,
                    frame_indices=list(map(int, frame_indices)))
    metadata.update(audit or {})
    values = values_for(names, selected) if values is None else values
    mdg().save_npz(out/(stem+'.npz'), names, values, metadata)
    sidecar = dict(scene=scene, selected={n: c.id if c else None for n, c in selected.items()},
                   candidates={n: [candidate_json(c) for c in cs] for n, cs in (by_name or {}).items()},
                   audit=metadata)
    if by_name is not None:
        (out/(stem+'.candidates.json')).write_text(json.dumps(sidecar, allow_nan=False)+'\n')
    entry = dict(scene=scene, scene_key=scene, npz=stem+'.npz', frame_indices=metadata['frame_indices'])
    path = out/'INDEX.json'
    index = json.loads(path.read_text()) if path.exists() else {}
    index[scene] = entry
    path.write_text(json.dumps(index, indent=1)+'\n')
    return entry
