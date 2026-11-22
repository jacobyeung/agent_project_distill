"""J1 per-frame rules, numpy only (imported by detect.py in the SAM 3 interpreter, by relift_j1.py and by the tests).

Served contract (dump 174135's read package; file:line in the served copies under j1/served):
  prompt      = the operand name as the model writes it in its ground call, lowercased and stripped
                (b/e2e_reader/stage1.py:24-25, 82); the step-544 rows write the question's own name (no alias table).
  retention   = per anchor, SAM 3 queries in descending conditional score (stable on query id), kept while
                score x presence >= 0.05, at most 30 (stage1.py:21, 95-99).
  masks       = native mask logits, bilinear to the source frame size, > 0, then routed_features.resize to 480x640
                (stage1.py:103-104; routed_features.py:8, 16-21); the relift grid is that mask[::2, ::2]
                (routed_features.py:199, accept_features).
  lift floor  = conditional score >= 0.3 before any proposal enters a served track (stage1.py:134; routed_candidates.py:87, 99).
Arms (per anchor; masks on the (32,240,320) grid):
  h1 (deployable): the retained proposal ranked first by score x presence (one presence per anchor, so the served score
      order, stage1.py:98, routed_features.py:68); kept if it is above both served floors (joint >= 0.05 and score >= 0.3);
      empty otherwise. Ties keep the served order (the earlier stored proposal).
  h0 (pool oracle): among all retained proposals of the anchor, the one with the highest IoU against the bound GT instance
      on the grid; kept if IoU >= 0.5; empty where GT is empty or no proposal reaches 0.5. Ties keep the earlier proposal.
  k (box oracle): SAM 3's top-scoring mask for the GT instance's tight box (box_from_mask) as its only prompt, on every
      anchor where GT is non-empty; empty where GT is empty.
Parity (frame_match, the registered gate): pair the two sides' retained proposals one to one, greedily by mask IoU at 480x640
  (highest first, pairs with IoU >= 0.95 only). An operand-frame matches when every proposal on either side that is clear of the
  numerical boundary (conditional score >= 0.3, the lift floor, and score x presence >= 0.06, 0.01 above the retention floor)
  has a partner; proposals inside the boundary may stay unpaired (bf16 rounding moves them across the 0.05 floor, the cap of 30
  and the order of near-equal low-score queries; the CPU rehearsal showed this tail is where identical code disagrees). Two
  empty lists match. frame_match_strict (same count and every proposal paired) is reported beside it and does not gate.
"""
import math
import numpy as np

JOINT_FLOOR = .05      # stage1.py:21 K1_CONTRACT joint_floor
CAP = 30               # stage1.py:21 K1_CONTRACT cap
LIFT_FLOOR = .3        # stage1.py:134 floor=.3 (routed_candidates.lift)
H0_IOU = .5
PARITY_IOU = .95
PARITY_BAR = .95
PARITY_JOINT = .06     # boundary: proposals under this joint score, or under the lift floor, may stay unpaired
CANVAS = (480, 640)
GRID = (240, 320)


def to_grid(mask480):
    """Served 480x640 mask -> relift grid, as accept_features keeps it (mask[::2, ::2])."""
    m = np.asarray(mask480, bool)
    if m.shape != CANVAS:
        raise ValueError('proposal mask is not 480x640')
    return m[::2, ::2].copy()


def iou(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    u = np.count_nonzero(a | b)
    return np.count_nonzero(a & b)/u if u else 1.   # two empty masks are identical (the dump holds 9 empty proposal masks)


def top1(props):
    """Index of h1's proposal among one anchor's retained proposals [dict(score, presence)], or None.
    Rank by score x presence, ties to the earlier entry; keep only above both served floors."""
    if not props:
        return None
    # float32 products, as the served retention computes them in torch (stage1.py:97, 99)
    joint = [float(np.float32(p['score'])*np.float32(p['presence'])) for p in props]
    best = max(range(len(props)), key=lambda i: (joint[i], -i))
    p = props[best]
    if joint[best] >= float(np.float32(JOINT_FLOOR)) and float(p['score']) >= LIFT_FLOOR:
        return best
    return None


def iou_oracle(masks240, gt240):
    """Index of h0's proposal among one anchor's retained proposal masks (grid), or None; GT empty -> None."""
    gt = np.asarray(gt240, bool)
    if not gt.any() or not len(masks240):
        return None
    vals = [iou(m, gt) for m in masks240]
    best = max(range(len(vals)), key=lambda i: (vals[i], -i))
    return best if vals[best] >= H0_IOU else None


def box_from_mask(gt240):
    """Tight box of a grid mask as SAM 3's box prompt: [cx, cy, w, h] normalised to [0, 1] (Sam3Processor.add_geometric_prompt
    format). Pixel (r, c) of the grid covers [c, c+1) x [r, r+1); None when the mask is empty."""
    m = np.asarray(gt240, bool)
    if m.ndim != 2 or not m.any():
        return None
    rows = np.flatnonzero(m.any(1)); cols = np.flatnonzero(m.any(0))
    h, w = m.shape
    x0, x1 = cols[0]/w, (cols[-1]+1)/w; y0, y1 = rows[0]/h, (rows[-1]+1)/h
    return [(x0+x1)/2, (y0+y1)/2, x1-x0, y1-y0]


def box_pixels(box, shape=GRID):
    """Inverse of box_from_mask on a grid: (r0, r1, c0, c1) half-open, for tests."""
    cx, cy, bw, bh = box; h, w = shape
    return (int(round((cy-bh/2)*h)), int(round((cy+bh/2)*h)), int(round((cx-bw/2)*w)), int(round((cx+bw/2)*w)))


def pair(mine, theirs, thr=PARITY_IOU):
    """Greedy one-to-one pairing of two proposal lists [dict(mask480, score, presence)] by mask IoU, highest first, only pairs
    with IoU >= thr. Returns (pairs [(i, j, iou)], unpaired indices of mine, unpaired indices of theirs)."""
    M = np.zeros((len(mine), len(theirs)))
    for i, a in enumerate(mine):
        for j, b in enumerate(theirs):
            M[i, j] = iou(a['mask480'], b['mask480'])
    pairs, ui, uj = [], set(range(len(mine))), set(range(len(theirs)))
    if M.size:
        for flat in np.argsort(-M, axis=None, kind='stable'):
            i, j = divmod(int(flat), M.shape[1])
            if M[i, j] < thr:
                break
            if i in ui and j in uj:
                ui.discard(i); uj.discard(j); pairs.append((i, j, float(M[i, j])))
    return pairs, sorted(ui), sorted(uj)


def boundary(p):
    """A proposal inside the numerical boundary: under the lift floor, or joint score under PARITY_JOINT (float32 product)."""
    return float(p['score']) < LIFT_FLOOR or float(np.float32(p['score'])*np.float32(p['presence'])) < float(np.float32(PARITY_JOINT))


def frame_match(mine, theirs, thr=PARITY_IOU):
    """(match, detail) for one operand-frame under the registered rule: every proposal clear of the boundary, on either side,
    has a one-to-one partner with IoU >= thr; boundary proposals may stay unpaired."""
    if not mine and not theirs:
        return True, dict(reason='both_empty', strict=True)
    pairs, ui, uj = pair(mine, theirs, thr)
    clear = [i for i in ui if not boundary(mine[i])] + [j for j in uj if not boundary(theirs[j])]
    strict = len(mine) == len(theirs) and not ui and not uj
    return not clear, dict(reason='matched' if not clear else 'unpaired_clear', strict=strict, pairs=len(pairs),
                           unpaired_mine=len(ui), unpaired_dump=len(uj), unpaired_clear=len(clear),
                           min_pair_iou=min((x[2] for x in pairs), default=None))


def frame_match_strict(mine, theirs, thr=PARITY_IOU):
    """Descriptive: same count and every proposal paired with IoU >= thr."""
    return frame_match(mine, theirs, thr)[1]['strict']


def arm_h1(frames):
    """(32,240,320) h1 masks from 32 anchors of retained proposals [dict(score, presence, mask240)]."""
    out = np.zeros((len(frames),)+GRID, bool)
    for f, props in enumerate(frames):
        i = top1(props)
        if i is not None:
            out[f] = props[i]['mask240']
    return out


def arm_h0(frames, gt):
    out = np.zeros((len(frames),)+GRID, bool)
    for f, props in enumerate(frames):
        i = iou_oracle([p['mask240'] for p in props], gt[f])
        if i is not None:
            out[f] = props[i]['mask240']
    return out


# ---------------------------------------------------------------- reading

def verdict(m, oracle=False):
    """Registered bars on X - a (mean, ci95): >= 8 with lower bound > 0 -> source (opens for an oracle);
    <= 4 with upper bound < 8 -> closes; else undecided."""
    if m['mean'] is None or m['ci95'] is None:
        return 'undecided'
    if m['mean'] >= 8 and m['ci95'][0] > 0:
        return 'opens' if oracle else 'source'
    if m['mean'] <= 4 and m['ci95'][1] < 8:
        return 'closes'
    return 'undecided'


def needed_items(rows, key, z=1.959963984540054):
    """Paired items (and rooms) the interval of mean(key) would need, at the observed per-room spread and mean, to clear the
    nearer bar. Cluster (room) standard error of the item-weighted mean: SE^2 = R/(R-1) * sum_r (S_r - m n_r)^2 / N^2, which
    scales as 1/R at the observed items per room N/R. Source bar (mean >= 8): need z*SE < mean; closing bar (mean <= 4): need
    z*SE < 8 - mean; a mean strictly between 4 and 8 clears no bar at any size."""
    rooms = {}
    for r in rows:
        s = rooms.setdefault(r['room'], [0, 0.]); s[0] += 1; s[1] += r[key]
    R = len(rooms); N = sum(v[0] for v in rooms.values())
    if R < 2:
        return dict(rooms=R, items=N, bar=None, reason='fewer than two rooms')
    m = sum(v[1] for v in rooms.values())/N
    se = math.sqrt(R/(R-1)*sum((v[1]-m*v[0])**2 for v in rooms.values()))/N
    out = dict(mean=m, se=se, rooms=R, items=N, items_per_room=N/R, z=z)
    if m >= 8:
        bar, margin = 'source', m
    elif m <= 4:
        bar, margin = 'closes', 8-m
    else:
        out.update(bar=None, reason='observed mean lies between the bars (4, 8); no item count clears either at this mean',
                   distance_to_source_bar=8-m, distance_to_closing_bar=m-4)
        return out
    rooms_needed = R*(z*se/margin)**2 if se > 0 else 0.
    out.update(bar=bar, margin=margin, rooms_needed=int(math.ceil(rooms_needed)),
               items_needed=int(math.ceil(rooms_needed*N/R)), already_clears=z*se < margin)
    return out
