"""Radius consensus in the routed kit's metric, gravity-aligned coordinate frame."""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Candidate:
    frame: int  # 1-based viewpoint, never the video source-frame index
    uv: object  # x,y on the native 0..1000 canvas
    confidence: float = 1.0
    instance: int = 0
    mask: object = field(default=None, repr=False)
    source: str = 'point'
    object_id: str = ''  # Stable object reference; SAM proposal indices are frame-local.
    keypoint: str = 'centroid'
    toward: str = ''    # Other stable object reference for nearest_surface.
    axis: str = ''      # Shared object/world axis for paired extent ends.


def select(candidates, geometry, radius=.5):
    """Maximize distinct-frame support in a fixed-radius ball around an observed point.

    Radius is 0.5 metric metres by default, independent of GT/object size. Balls
    do not chain through intermediate points. Each frame contributes one vote;
    nearest-to-seed wins within a frame. Ties use confidence, dispersion, then
    input order. A singleton is retained and explicitly lacks consensus.
    """
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError('radius must be a positive number of metres')
    if len({(c.object_id, c.keypoint, c.toward, c.axis) for c in candidates}) > 1:
        raise ValueError('Use select_keypoints for multiple objects or keypoint roles')
    good, xyz, rejected = [], [], []
    for i, c in enumerate(candidates):
        uv = np.asarray(c.uv, dtype=float)
        if (not 1 <= c.frame <= 32 or uv.shape != (2,) or not np.isfinite(uv).all()
                or (uv < 0).any() or (uv > 1000).any() or not np.isfinite(c.confidence)):
            rejected.append(dict(index=i, reason='invalid_candidate'))
            continue
        if not geometry.has(c.frame):
            rejected.append(dict(index=i, reason='invalid_pose'))
            continue
        P, Pc, spread = geometry.lift(c.frame, uv[None], mode='center')
        if not np.isfinite(P).all() or not np.isfinite(Pc).all() or Pc[0, 2] <= 0:
            rejected.append(dict(index=i, reason='invalid_depth_or_pose'))
            continue
        good.append(i)
        xyz.append(P[0])
    empty = dict(status='empty', frames_kept=[], best_frame=None, position=None,
                 best_position=None, candidate_indices=[], support=0, rival_support=0,
                 radius_m=radius, rejected=rejected)
    if not good:
        return empty
    P = np.asarray(xyz)
    # A clip has only 32 frames; bound memory for SAM caches with many instances.
    frames = np.array([candidates[i].frame for i in good])
    conf = np.array([candidates[i].confidence for i in good])
    balls = {}
    for seed, center in enumerate(P):
        dist = np.linalg.norm(P-center, axis=1)
        neighbors = np.flatnonzero(dist <= radius + 1e-10)
        chosen = []
        for frame in sorted(set(frames[neighbors])):
            members = neighbors[frames[neighbors] == frame]
            chosen.append(min(members, key=lambda j: (dist[j], -conf[j], good[j])))
        members = tuple(sorted(chosen))
        if members in balls:
            continue
        median = np.median(P[list(members)], axis=0)
        dispersion = float(np.linalg.norm(P[list(members)]-median, axis=1).mean())
        balls[members] = (-len(members), -float(conf[list(members)].sum()), dispersion, seed)
    ordered = sorted(balls, key=lambda members: balls[members])
    kept = list(ordered[0])
    position = np.median(P[kept], axis=0)
    rival = next((list(m) for m in ordered[1:] if not set(m).intersection(kept)
                  and np.linalg.norm(np.median(P[list(m)], axis=0)-position) > radius), [])
    ambiguous = bool(rival and len(rival) == len(kept))
    best = min(kept, key=lambda j: (np.linalg.norm(P[j]-position), -conf[j], frames[j], good[j]))
    return dict(status='singleton' if len(kept) == 1 else 'ambiguous' if ambiguous else 'consensus',
                frames_kept=sorted(map(int, frames[kept])), best_frame=int(frames[best]),
                position=position.tolist(), best_position=P[best].tolist(),
                candidate_indices=[good[j] for j in kept], support=len(kept),
                rival_support=len(rival), radius_m=radius, rejected=rejected,
                max_distance_to_position=float(np.linalg.norm(P[kept]-position, axis=1).max()))


def centroid(mask):
    """Arithmetic mask centroid in normalized coordinates (may lie in a hole)."""
    rows, cols = np.nonzero(mask)
    if not len(rows):
        return None
    h, w = mask.shape
    return [(float(cols.mean())+.5)/w*1000, (float(rows.mean())+.5)/h*1000]


def from_points(rows):
    """Text-point cache or mask-decoder clicks; nulls never acquire a vote."""
    result = []
    for r in rows:
        if r.get('parse_status', 'point') != 'point' or r.get('point_2d') is None:
            continue
        if r.get('parity_pass') is False:
            raise ValueError('Cannot select a text cache whose image parity failed')
        result.append(Candidate(int(r['frame']), r['point_2d'], float(r.get('confidence', 1)),
                                int(r.get('instance', 0)), source=r.get('source', 'point'),
                                object_id=r.get('object_id', r.get('obj', '')),
                                keypoint=r.get('keypoint', 'centroid'), toward=r.get('toward', ''),
                                axis=r.get('axis', '')))
    return result


def select_keypoints(candidates, geometry, radius=.5):
    """Select each stable object/role independently; preserve global input indices.

    A nearest_surface point names the other object. Extent ends name the SAME
    object/world axis across views; image-left/image-right are not stable roles.
    Duplicate 2D proposals can still use instance, but it is not a track ID.
    """
    groups = {}
    for i, c in enumerate(candidates):
        if not c.object_id or c.keypoint not in ('centroid', 'nearest_surface', 'extent_start', 'extent_end'):
            raise ValueError('Keypoints require an object_id and a supported role')
        if c.keypoint == 'nearest_surface':
            if not c.toward or c.toward == c.object_id or c.axis:
                raise ValueError('Surface keypoints require another object in toward and no axis')
        elif c.toward:
            raise ValueError('Only nearest_surface accepts toward')
        if c.keypoint.startswith('extent_'):
            if not c.axis:
                raise ValueError('Extent ends require a stable object/world axis')
        elif c.axis:
            raise ValueError('Only extent ends accept axis')
        key = (c.object_id, c.keypoint, c.toward, c.axis)
        groups.setdefault(key, []).append(i)
    results = []
    for (obj, role, toward, axis), indices in sorted(groups.items()):
        selection = select([candidates[i] for i in indices], geometry, radius)
        selection['candidate_indices'] = [indices[i] for i in selection['candidate_indices']]
        selection['rejected'] = [{**r, 'index': indices[r['index']]} for r in selection['rejected']]
        results.append(dict(object_id=obj, keypoint=role, toward=toward, axis=axis, **selection))
    return results


def _keypoint_distance(selections, first, second, min_support):
    if type(min_support) is not int or min_support < 1:
        raise ValueError('min_support must be a positive integer')
    found = []
    for wanted in (first, second):
        matches = [s for s in selections if all(s[k] == v for k, v in wanted.items())]
        if len(matches) > 1:
            raise ValueError('Duplicate keypoint selection')
        if not matches or matches[0]['best_position'] is None:
            return dict(status='missing_keypoint', distance_m=None)
        s = matches[0]
        if s['status'] == 'ambiguous':
            return dict(status='ambiguous', distance_m=None)
        if s['support'] < min_support:
            return dict(status='insufficient_support', distance_m=None)
        found.append(s)
    # Use observed lifted surface points, not a median that may lie off-surface.
    p, q = [np.asarray(s['best_position'], dtype=float) for s in found]
    return dict(status='ok', distance_m=float(np.linalg.norm(p-q)),
                positions=[p.tolist(), q.tolist()], frames=[s['best_frame'] for s in found],
                support=[s['support'] for s in found], observed_surface_points=True)


def keypoint_gap(selections, a, b, min_support=1):
    """Distance between reciprocal facing-surface points, even in disjoint frames."""
    if a == b:
        raise ValueError('Gap requires distinct object references')
    return _keypoint_distance(selections,
        dict(object_id=a, keypoint='nearest_surface', toward=b),
        dict(object_id=b, keypoint='nearest_surface', toward=a), min_support)


def keypoint_extent(selections, obj, axis, min_support=1):
    """Distance between the two ends of one named object/world axis."""
    return _keypoint_distance(selections,
        dict(object_id=obj, keypoint='extent_start', axis=axis),
        dict(object_id=obj, keypoint='extent_end', axis=axis), min_support)
