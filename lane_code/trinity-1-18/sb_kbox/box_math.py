"""Fixed math for the K1 box ladder; no learned thresholds or split access."""
from collections import Counter
import numpy as np

FUSIONS = ('best1', 'vote2_best', 'vote2', 'allspread', 'trim')
CONSTANTS = dict(gather_score_floor=.3, gather_overlap=.25, gather_voxel_m=.10,
                 fusion_voxel_m=.05, trim_percentiles=[2, 98], appearance_share=.002,
                 member_iou=.5, bootstrap_draws=10000, bootstrap_seed=20261119)


def gather(seed, proposals):
    """Grow into unoccupied frames; choose maximal overlap against a round's union.

    Seed members stay fixed. Equal overlaps break ties by proposal index. Each
    round admits its winners simultaneously; a later round sees their union.
    """
    members = {p.frame: p for p in seed}
    if len(members) != len(seed):
        raise ValueError('seed_has_duplicate_frames')
    while True:
        union = frozenset().union(*(p.voxels for p in members.values()))
        winners = {}
        for p in proposals:
            if p.frame in members or p.score < .3 or not p.voxels:
                continue
            overlap = len(p.voxels & union) / len(p.voxels)
            if overlap < .25:
                continue
            rank = (overlap, -p.index)
            if p.frame not in winners or rank > winners[p.frame][0]:
                winners[p.frame] = (rank, p)
        if not winners:
            return [members[f] for f in sorted(members)]
        members.update({f: p for f, (_, p) in winners.items()})


def fused_points(points, best, rule):
    """Vote by distinct frames and retain original points in supported voxels."""
    if rule not in FUSIONS:
        raise ValueError(rule)
    parts = {int(f): np.asarray(p, float).reshape(-1, 3) for f, p in points.items()}
    if best not in parts:
        raise ValueError('best_frame_missing')
    if len(parts) == 1 or rule == 'best1':
        return parts[best]
    if rule in ('allspread', 'trim'):
        return np.concatenate([parts[f] for f in sorted(parts)])
    voxels = {f: [tuple(v) for v in np.floor(p / .05).astype(np.int64)] for f, p in parts.items()}
    counts = Counter(v for vs in voxels.values() for v in set(vs))
    voted = [parts[f][np.asarray([counts[v] >= 2 for v in voxels[f]], bool)] for f in sorted(parts)]
    if rule == 'vote2_best':
        voted.append(parts[best])
    return np.concatenate(voted)


def fusion_box(points, best, rule, min_area_box):
    p = fused_points(points, best, rule)
    box = min_area_box(p)
    if rule == 'trim' and len(points) > 1:
        axes = box['normalizedAxes']
        lo, hi = np.percentile(p @ axes.T, [2, 98], axis=0)
        if np.any(hi <= lo):
            raise ValueError('degenerate_trim_box')
        box = dict(centroid=((lo + hi) / 2) @ axes,
                   axesLengths=hi - lo, normalizedAxes=axes)
    return box


def mra(prediction, truth):
    if prediction is None or not np.isfinite(prediction) or truth <= 0:
        return 0.
    error = abs(prediction - truth) / truth
    return sum(error < (100 - t) / 100 for t in range(50, 100, 5)) / 10


def paired_bootstrap(left, right):
    """Item-weighted paired means, resampling physical rooms, never unmatched rows."""
    a, b = ({r['row_id']: r for r in rows} for rows in (left, right))
    ids = sorted(a.keys() & b.keys())
    if not ids:
        return dict(status='MISSING', n=0, rooms=0, estimate=None, ci95=None)
    for i in ids:
        if a[i]['room'] != b[i]['room'] or a[i]['label'] != b[i]['label']:
            raise ValueError('paired_room_or_label_mismatch')
    rooms = sorted({a[i]['room'] for i in ids})
    lookup = {r: i for i, r in enumerate(rooms)}
    cluster = np.array([lookup[a[i]['room']] for i in ids])
    delta = np.array([mra(a[i]['prediction'], a[i]['label']) - mra(b[i]['prediction'], b[i]['label']) for i in ids])
    totals = np.bincount(cluster, weights=delta, minlength=len(rooms))
    counts = np.bincount(cluster, minlength=len(rooms))
    rng = np.random.default_rng(20261119)
    draws = rng.integers(0, len(rooms), (10000, len(rooms)))
    scores = totals[draws].sum(1) / counts[draws].sum(1)
    return dict(status='OK', n=len(ids), rooms=len(rooms), estimate=float(100*delta.mean()),
                ci95=(100*np.percentile(scores, [2.5, 97.5])).tolist(), draws=10000, seed=20261119)


def first_seen(masks, printed_frames):
    share = np.asarray(masks, bool).mean(axis=(1, 2))
    eligible = np.flatnonzero(share >= .002) + 1
    truth = int(eligible[0]) if len(eligible) else None
    pred = min(printed_frames) if printed_frames else None
    return dict(first_printed=pred, first_gt=truth,
                exact=bool(truth is not None and pred == truth),
                within_one=bool(truth is not None and pred is not None and abs(pred-truth) <= 1))
