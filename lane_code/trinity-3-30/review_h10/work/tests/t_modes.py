"""Refute registered M3 modes on the kit's real-GT camera fixture: 180 deg flips horizontal move, k scales, negate flips turn."""
import re, itertools
import numpy as np
from h1eval.perception import Heads, perturb
from h1eval import scorers as S
from tests.fixtures import camera_fixtures
from student_pilot.carrier_c1_routing import OwnGeometry

rows, clip, _ = camera_fixtures()
h = Heads(np.array(clip['gt_pose9']), np.array(clip['gt_up']), lambda f, uv: 2.+np.asarray(uv)[:, 0]*.001, 'A')
own = OwnGeometry(h.pose9, h.gravity, h.depth)
NUM = r'[+-]?\d+(?:\.\d*)?'
def mv(g, a, b):
    t = g.move_text(a, b); m = re.search(r'dx = (%s) m, dy = (%s) m, dz = (%s) m, distance = (%s) m' % ((NUM,)*4), t)
    return np.array(list(map(float, m.groups())))
pairs = [(1, 9), (3, 20), (10, 31), (2, 32), (17, 18)]
bad = []
r180, _ = perturb(h, {'name': 'rotate_translation', 'deg': 180.})
g180 = OwnGeometry(r180.pose9, r180.gravity, r180.depth)
print('gravity', h.gravity)
for a, b in pairs:
    u, v = mv(own, a, b), mv(g180, a, b)
    ok = np.allclose(v[[0, 2]], -u[[0, 2]], atol=0.011) and abs(v[1]-u[1]) < 0.011 and abs(v[3]-u[3]) < 0.011
    print('rot180', (a, b), u, v, 'OK' if ok else 'BAD'); bad += [] if ok else [('rot180', a, b)]
    if own.turn_text(a, b) != g180.turn_text(a, b): bad.append(('rot180_turn_changed', a, b))
for k in (0.5, 2.):
    s, _ = perturb(h, {'name': 'scale_translation', 'k': k}); g = OwnGeometry(s.pose9, s.gravity, s.depth)
    for a, b in pairs:
        u, v = mv(own, a, b), mv(g, a, b)
        ok = abs(v[3]-k*u[3]) <= 0.011 + 1e-9
        if not ok: bad.append(('scale', k, a, b, u[3], v[3]))
        if own.turn_text(a, b) != g.turn_text(a, b): bad.append(('scale_turn_changed', k, a, b))
n, _ = perturb(h, {'name': 'negate_turn'})
gt_ = OwnGeometry(n.turn_pose9, n.gravity, n.depth); gm = OwnGeometry(n.pose9, n.gravity, n.depth)
for a, b in pairs:
    x = float(re.search(NUM, own.turn_text(a, b).split('=')[1])[0]); y = float(re.search(NUM, gt_.turn_text(a, b).split('=')[1])[0])
    ok = abs(x+y) < 1.01 or abs(abs(x)-180) < 1.01
    print('negate', (a, b), own.turn_text(a, b), '|', gt_.turn_text(a, b), 'OK' if ok else 'BAD')
    if not ok: bad.append(('negate', a, b))
    if gm.move_text(a, b) != own.move_text(a, b): bad.append(('negate_move_changed', a, b))
print('BAD', bad)
