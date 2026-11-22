"""J1 synthetic unit tests (CPU, numpy only; p1cpu or the SAM 3 interpreter). No real output is read.
top-1 rule, IoU-oracle rule, box from GT, grid resize, parity matcher, precision/recall toy, verdict bars, needed-items toy,
detector-file round trip through relift_j1.DetectStore's decoding."""
import math, sys
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import j1_common as G
import select_j1 as S

PASS = []


def ok(name):
    PASS.append(name); print('PASS', name, flush=True)


def rect(r0, r1, c0, c1, shape=S.GRID):
    m = np.zeros(shape, bool); m[r0:r1, c0:c1] = True; return m


# top-1: score x presence order, ties to the earlier entry, both floors
P = lambda s, p=1.: dict(score=s, presence=p)
assert S.top1([]) is None
assert S.top1([P(.9), P(.95), P(.5)]) == 1
assert S.top1([P(.9), P(.9)]) == 0                      # tie keeps the served (earlier) order
assert S.top1([P(.29, 1.)]) is None                      # below the lift floor 0.3 on score
assert S.top1([P(.3, 1.)]) == 0                          # at the lift floor
assert S.top1([P(1., .05)]) == 0 and S.top1([P(.9, .06)]) == 0   # joint 0.05 and 0.054 kept
assert S.top1([P(.9, .04)]) is None                      # joint 0.036 < 0.05
assert S.top1([P(.6, .1), P(.4, .1)]) == 0               # one presence per anchor: joint order == score order
assert S.top1([P(.25), P(.2)]) is None                   # the best is under the floor -> empty, the next is not tried
ok('top1_rule')

# IoU oracle
gt = rect(10, 30, 10, 30)
a = rect(10, 30, 10, 30); b = rect(10, 30, 10, 20); c = rect(50, 60, 50, 60)
assert S.iou_oracle([c, b, a], gt) == 2
assert S.iou_oracle([b], gt) == 0                        # IoU exactly 0.5 is kept
assert S.iou_oracle([rect(10, 30, 10, 19)], gt) is None  # IoU 0.45
assert S.iou_oracle([a, a.copy()], gt) == 0              # tie -> earlier
assert S.iou_oracle([a], np.zeros(S.GRID, bool)) is None  # GT empty -> empty
assert S.iou_oracle([], gt) is None
frames = [[dict(score=.9, presence=1., mask240=c), dict(score=.8, presence=1., mask240=a)]] + [[] for _ in range(31)]
gt32 = np.zeros((32,)+S.GRID, bool); gt32[0] = gt
h1 = S.arm_h1(frames); h0 = S.arm_h0(frames, gt32)
assert np.array_equal(h1[0], c) and not h1[1:].any() and np.array_equal(h0[0], a) and not h0[1:].any()
ok('iou_oracle_rule_and_arms')

# box from GT: normalised cx, cy, w, h; inverse on the grid; empty -> None
m = rect(24, 48, 32, 96)
bx = S.box_from_mask(m)
assert np.allclose(bx, [(32+96)/2/320, (24+48)/2/240, 64/320, 24/240])
assert S.box_pixels(bx) == (24, 48, 32, 96)
m2 = np.zeros(S.GRID, bool); m2[5, 7] = True; m2[100, 200] = True
assert S.box_pixels(S.box_from_mask(m2)) == (5, 101, 7, 201)
assert S.box_from_mask(np.zeros(S.GRID, bool)) is None
full = np.ones(S.GRID, bool); assert np.allclose(S.box_from_mask(full), [.5, .5, 1., 1.])
ok('box_from_gt')

# grid resize: 480x640 -> [::2, ::2]; pixel doubling round-trips; other shapes refused
rng = np.random.default_rng(0)
g = rng.random(S.GRID) > .7
up = np.repeat(np.repeat(g, 2, 0), 2, 1)
assert up.shape == S.CANVAS and np.array_equal(S.to_grid(up), g)
odd = np.zeros(S.CANVAS, bool); odd[1::2, 1::2] = True
assert not S.to_grid(odd).any()                           # [::2, ::2] keeps even rows and columns only
try:
    S.to_grid(np.zeros((240, 320), bool)); raise AssertionError('grid mask accepted')
except ValueError:
    pass
ok('resize_to_grid')

# parity matcher (registered rule: every proposal clear of the boundary is paired at IoU >= 0.95; strict rule beside it)
A = rect(0, 100, 0, 100, S.CANVAS); B = rect(200, 300, 200, 300, S.CANVAS); C = rect(400, 450, 0, 50, S.CANVAS)
A96 = rect(0, 100, 0, 96, S.CANVAS); A94 = rect(0, 100, 0, 94, S.CANVAS)
Q = lambda m, s=.9, p=1.: dict(mask480=m, score=s, presence=p)
assert S.frame_match([], [])[0] and S.frame_match_strict([], [])
m, why = S.frame_match([Q(A)], []); assert not m and why['unpaired_clear'] == 1
assert S.frame_match([Q(A), Q(B)], [Q(B), Q(A)])[0] and S.frame_match_strict([Q(A), Q(B)], [Q(B), Q(A)])   # order-free
assert S.frame_match([Q(A96), Q(B)], [Q(A), Q(B)])[0]                        # IoU 0.96
assert not S.frame_match([Q(A94), Q(B)], [Q(A), Q(B)])[0]                    # IoU 0.94, both clear of the boundary
assert not S.frame_match([Q(A), Q(A)], [Q(A), Q(B)])[0]                      # one-to-one: the duplicate cannot take B
# boundary: an extra proposal under the lift floor, or with joint under 0.06, may stay unpaired (strict rule fails)
assert S.frame_match([Q(A), Q(C, .29)], [Q(A)])[0] and not S.frame_match_strict([Q(A), Q(C, .29)], [Q(A)])
assert S.frame_match([Q(A)], [Q(A), Q(C, .9, .066)])[0]                      # joint 0.0594 < 0.06
assert not S.frame_match([Q(A)], [Q(A), Q(C, .9, .07)])[0]                   # joint 0.063: clear, must pair
assert not S.frame_match([Q(A, .29)], [Q(B)])[0]                             # the clear dump proposal B has no partner
assert S.frame_match([Q(A94, .2)], [Q(A, .25)])[0]                           # both in the tail: unpaired allowed
assert S.iou(np.zeros(S.CANVAS, bool), np.zeros(S.CANVAS, bool)) == 1. and S.frame_match([Q(np.zeros(S.CANVAS, bool))], [Q(np.zeros(S.CANVAS, bool))])[0]   # empty == empty
ok('parity_matcher')

# precision / recall toy and the empty-GT count
pred = np.zeros((3, 4, 4), bool); truth = np.zeros((3, 4, 4), bool)
pred[0, :2, :2] = True; truth[0, :2, :] = True                 # P=4, G=8, I=4 -> p 1, r .5
pred[1, 0, 0] = True                                           # GT empty -> p 0, counted
truth[2, 3, 3] = True                                          # P empty -> r 0
s = G.summarize_pr(G.precision_recall(pred, truth))
assert s['union_frames'] == 3 and s['pred_frames'] == 2 and s['gt_frames'] == 2 and s['pred_on_empty_gt'] == 1
assert math.isclose(s['precision'], .5) and math.isclose(s['recall'], .25)
ok('precision_recall_toy')

# verdict bars
V = lambda m, lo, hi: dict(mean=m, ci95=[lo, hi])
assert S.verdict(V(8, .1, 15)) == 'source' and S.verdict(V(8, .1, 15), True) == 'opens'
assert S.verdict(V(8, 0., 15)) == 'undecided' and S.verdict(V(7.9, 1, 15)) == 'undecided'
assert S.verdict(V(4, -3, 7.9)) == 'closes' and S.verdict(V(4, -3, 8)) == 'undecided' and S.verdict(V(4.1, -3, 7)) == 'undecided'
assert S.verdict(dict(mean=None, ci95=None)) == 'undecided'
ok('verdict_bars')

# needed items: closed form on toy rooms
rows = []
for r, vals in enumerate([[10, 14], [2, 6], [12], [6, 10, 8]]):
    rows += [dict(room='r%d' % r, d=v) for v in vals]
n = S.needed_items(rows, 'd')
N, R, m = 8, 4, 68/8
Srm = [(24-2*m), (8-2*m), (12-m), (24-3*m)]
se = math.sqrt(R/(R-1)*sum(x*x for x in Srm))/N
assert math.isclose(n['mean'], m) and math.isclose(n['se'], se) and n['bar'] == 'source'
assert n['rooms_needed'] == math.ceil(R*(n['z']*se/m)**2) and n['items_needed'] == math.ceil(R*(n['z']*se/m)**2*N/R)
low = [dict(room='r%d' % (i % 5), d=v) for i, v in enumerate([1, 3, -2, 5, 0, 2, 4, -1, 3, 1])]
nl = S.needed_items(low, 'd'); assert nl['bar'] == 'closes' and math.isclose(nl['margin'], 8-nl['mean'])
mid = [dict(room='r%d' % i, d=v) for i, v in enumerate([5, 7, 6, 6])]
nm = S.needed_items(mid, 'd'); assert nm['bar'] is None and 'between the bars' in nm['reason']
# doubling the rooms with the same values halves SE^2, so the rooms needed stay the same
big = rows + [dict(room=r['room']+'b', d=r['d']) for r in rows]
nb = S.needed_items(big, 'd'); assert abs(nb['rooms_needed'] - n['rooms_needed']) <= 1
ok('needed_items_toy')

# detector-file round trip (the GPU job's record layout) through DetectStore's decoding
sys.argv = ['x']
import relift_j1 as RJ
assert np.array_equal(S.to_grid(RJ.upsample(g)), g)
mask = rng.random(S.CANVAS) > .9
rec = dict(score=.5, presence=.25, mask=G.pack(mask))
import json
back = G.unpack(json.loads(G.dumps_plain(rec))['mask'])
assert np.array_equal(back, mask)
ok('mask_codec_round_trip')
print('{"status": "PASS", "tests": %d}' % len(PASS))
