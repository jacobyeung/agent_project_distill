"""Analysis-only grounding funnel. Unknown evidence never counts as success."""
import itertools
import math
import random
from collections import Counter, defaultdict

STAGES = tuple('S%d' % i for i in range(6))


def stage(e):
    """First failure, with strict upstream observability and explicit unknowns.

    proposed means a raw proposal matching the target in at least one frame,
    not merely a nonempty name-prompt cache. selected_correct_frames counts matched
    frames of the selected identity, not its printed (possibly wrong) support.
    """
    required = ('visible', 'proposed', 'selected_correct',
                'selected_correct_frames', 'outside_box_m')
    for k in required:
        if e.get(k) is None:
            return 'U', k
        v = e[k]
        if k in required[:3] and type(v) is not bool:
            raise ValueError(k + ' must be boolean or null')
        if k == 'visible' and not v:
            return 'S0', None
        if k == 'proposed' and not v:
            return 'S1', None
        if k == 'selected_correct' and not v:
            return 'S2', None
        if k == 'selected_correct_frames':
            if type(v) is not int or v < 0:
                raise ValueError('invalid frame count')
            if v < 3:
                return 'S3', None
        if k == 'outside_box_m':
            if not math.isfinite(v) or v < 0:
                raise ValueError('invalid box distance')
            if v > .25:
                return 'S4', None
    return 'S5', None


def worse(stages):
    """Earlier failure is worse. Unknown operands prevent stage assignment."""
    if 'S0' in stages:
        return 'S0'
    if not stages or 'U' in stages:
        return 'U'
    if any(x not in STAGES for x in stages):
        raise ValueError('invalid stage')
    return min(stages, key=STAGES.index)


def outside_obb(point, center, axes, full_lengths):
    """Euclidean distance to an oriented box, axes stored as rows, metres."""
    if len(point) != 3 or len(center) != 3 or len(axes) != 3:
        raise ValueError('3D vectors required')
    if any(len(a) != 3 for a in axes) or len(full_lengths) != 3:
        raise ValueError('3D axes/lengths required')
    vals = list(point) + list(center) + list(full_lengths) + sum(axes, [])
    if any(not math.isfinite(x) for x in vals) or any(x <= 0 for x in full_lengths):
        raise ValueError('invalid box')
    for i in range(3):
        for j in range(3):
            if abs(sum(axes[i][k] * axes[j][k] for k in range(3)) - (i == j)) > 1e-6:
                raise ValueError('axes must be orthonormal')
    local = [sum((point[k] - center[k]) * a[k] for k in range(3)) for a in axes]
    return math.sqrt(sum(max(abs(x) - length / 2, 0.) ** 2
                         for x, length in zip(local, full_lengths)))


def mask_iou(a, b):
    """Sets of raster pixel indices, at exactly the same resolution."""
    union = a | b
    return len(a & b) / len(union) if union else 0.


def synthetic_evidence(gt, candidates, chosen, position=None, box=None, raw_candidates=None):
    """Small-capture matcher used by tests; GT maps displayed frame to pixels.

    Real adapters must bind a particular annotated instance and certify complete
    frame visibility. A track matches when at least half its nonempty member
    masks have IoU > .5; this follows the cited route-table identity rule.
    """
    visible = any(gt.values())
    raw_candidates = candidates if raw_candidates is None else raw_candidates
    proposed = any(mask_iou(set(m), set(gt.get(f, ()))) > .5
                   for c in raw_candidates for f, m in c.items())
    matches = []
    for c in candidates:
        frames = [f for f, m in c.items() if m]
        hit = [f for f in frames if mask_iou(set(c[f]), set(gt.get(f, ()))) > .5]
        matches.append((bool(frames) and 2 * len(hit) >= len(frames), hit))
    correct = chosen is not None and 0 <= chosen < len(matches) and matches[chosen][0]
    return dict(visible=visible, proposed=proposed,
                selected_correct=correct,
                selected_correct_frames=len(matches[chosen][1]) if correct else 0,
                outside_box_m=outside_obb(position, **box) if position is not None and box else None)


def percentile(a, q):
    if not a:
        return None
    x = sorted(a)
    t = (len(x) - 1) * q
    lo = int(t)
    return x[lo] + (x[min(lo + 1, len(x) - 1)] - x[lo]) * (t - lo)


def summarize(rows, reference='S5', draws=10000, seed=20261120):
    """Paired room bootstrap for counts, scores and association point budgets.

    Rows: room, group, score (0..100). Draw whole rooms, use item-weighted means.
    Association budget = n_group/N * (mean_reference - mean_group), signed.
    Empty-group draws remain undefined; their count is reported, not redrawn.
    All groups in a draw share the same room resampling.
    """
    if any(not r.get('room') for r in rows):
        raise ValueError('physical room required')
    if any(not math.isfinite(r['score']) or not 0 <= r['score'] <= 100 for r in rows):
        raise ValueError('score must be finite percent')
    groups = sorted(set(r['group'] for r in rows))
    rooms = sorted(set(r['room'] for r in rows))
    cells = defaultdict(lambda: [0, 0.])
    for r in rows:
        z = cells[r['room'], r['group']]
        z[0] += 1
        z[1] += r['score']
    def estimate(selected):
        counts = dict.fromkeys(groups, 0)
        sums = dict.fromkeys(groups, 0.)
        for room in selected:
            for g in groups:
                n, s = cells[room, g]
                counts[g] += n
                sums[g] += s
        total = sum(counts.values())
        means = {g: sums[g] / counts[g] if counts[g] else None for g in groups}
        ref = means.get(reference)
        return {g: dict(count=counts[g], score=means[g],
                        association_points=counts[g] / total * (ref - means[g])
                        if ref is not None and means[g] is not None else None)
                for g in groups}
    result = estimate(rooms)
    samples = {g: defaultdict(list) for g in groups}
    rng = random.Random(seed)
    for _ in range(draws):
        sample = estimate([rng.choice(rooms) for _ in rooms])
        for g in groups:
            for k, v in sample[g].items():
                if v is not None:
                    samples[g][k].append(v)
    for g in groups:
        result[g]['rooms'] = len(set(r['room'] for r in rows if r['group'] == g))
        for k in ('count', 'score', 'association_points'):
            v = samples[g][k]
            result[g][k + '_ci95'] = [percentile(v, .025), percentile(v, .975)] if v else None
            result[g][k + '_defined_draws'] = len(v)
    return dict(groups=result, draws=draws, seed=seed, rooms=len(rooms), items=len(rows),
                reference=reference, interpretation='association, not a counterfactual recovery')


def sample_indices(total, count, anchors):
    """Nested maximum-gap insertion preserves the reader's original anchors.

    Uniformly resampling would replace the original 32 frames. This ablation
    instead adds 32 then 32 frames, so the 32/64/96 sets are nested. Ties choose
    the earlier interval; source-index midpoint rounds down.
    """
    points = set(anchors)
    if len(anchors) != 32 or len(points) != 32 or list(anchors) != sorted(points):
        raise ValueError('32 distinct increasing original anchors required')
    if total < count or min(points) < 0 or max(points) >= total or count not in (32, 64, 96):
        raise ValueError('invalid sample request')
    if anchors[0] != 0 or anchors[-1] != total - 1:
        raise ValueError('endpoint-bound capture required')
    while len(points) < count:
        ordered = sorted(points)
        a, b = max(zip(ordered, ordered[1:]), key=lambda ab: (ab[1] - ab[0], -ab[0]))
        if b - a < 2:
            raise ValueError('insufficient distinct frames')
        points.add((a + b) // 2)
    return sorted(points)
