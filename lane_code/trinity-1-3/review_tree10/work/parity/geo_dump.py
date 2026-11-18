"""Differential parity: print handler responses for seeded own-head outputs.
usage: geo_dump.py TREE MODE(legacy|new) OUT N"""
import sys, json, math
tree, mode, out, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
sys.path.insert(0, tree)
import numpy as np, torch
from student_pilot import carrier_c1_routing as routing
from student_pilot import carrier_c1_decode as D
from trace_format.contracts import contract_epoch, heading_plane_min
from scipy.spatial.transform import Rotation

class FakeHead:
    """Stands in for point_depth.query: float32 in, float32 out, like the real head."""
    def __init__(self, seed):
        r = np.random.default_rng(seed)
        self.a, self.b, self.c = r.uniform(0.5, 4), r.uniform(20, 200), r.uniform(20, 200)
    def query(self, depth_map, uv):
        u, v = uv[..., 0], uv[..., 1]
        f = torch.arange(1, uv.shape[0] + 1, dtype=torch.float32)[:, None]
        return (self.a + 0.4 * torch.sin(u / self.b) + 0.3 * torch.cos(v / self.c) + 0.01 * f).float()

def case(seed):
    r = np.random.default_rng(seed)
    F = 32
    p = np.zeros((F, 9))
    p[:, :3] = r.uniform(-3, 3, (F, 3))
    q = Rotation.random(F, random_state=seed).as_quat()  # xyzw
    # some frames nearly vertical to exercise heading availability
    for k in r.choice(np.arange(1, F), 4, replace=False):
        q[k] = Rotation.from_euler('xyz', [r.choice([-1, 1]) * r.uniform(1.35, 1.5707), r.uniform(-3, 3), 0]).as_quat()
    p[:, 3:7] = q
    p[:, 7] = r.uniform(0.6, 1.4, F); p[:, 8] = r.uniform(0.6, 1.6, F)
    up = np.array([0., -1., 0.]) + r.normal(0, 0.05 if seed % 3 else 0.6, 3)
    return p, up, FakeHead(seed), r

def run(seed, epoch):
    p, up, head, r = case(seed)
    dmap = torch.zeros((32, 1))
    def depth(frame, points):
        uv = torch.full((dmap.shape[0], len(points), 2), 500.)
        uv[frame - 1] = torch.as_tensor(points, dtype=torch.float32)
        return head.query(dmap, uv)[frame - 1].double().cpu().numpy()
    kw = {}
    if mode == 'new':
        from student_pilot.fixed_readout import DepthReadout, HeadingReadout
        dr, hr = DepthReadout(), HeadingReadout(0.3)
        kw = dict(readout=lambda frame, uv, fov: dr(depth_map=dmap, fov_hw=fov, uv=uv, frame=frame, depth_head=head),
                  heading=lambda op, a, b=None: hr(operation=op, first_rotation=a, second_rotation=b, threshold=heading_plane_min()))
    res = []
    with contract_epoch(epoch, heading_plane_min=0.3):
        try:
            g = routing.OwnGeometry(p, up, depth, **kw)
        except Exception as e:
            return [('init', type(e).__name__ + str(e))]
        reg = D.calculator.PrintedPointRegistry()
        calls = []
        for _ in range(6):
            calls.append(f'<pose frame={int(r.integers(1, 33))}>')
            i, j = map(int, r.integers(1, 33, 2))
            calls.append(f'<turn from={i} to={j}>')
            calls.append(f'<move from={i} to={j}>')
            pts = ','.join(f'[{int(r.integers(20, 981))},{int(r.integers(20, 981))}]' for _ in range(int(r.integers(1, 5))))
            calls.append(f'<depth_at frame={int(r.integers(1, 33))} pts=[{pts}]>')
        for c in calls:
            try:
                text, info = D.respond(c, reg, g)
            except Exception as e:
                text = 'RAISE ' + type(e).__name__ + ': ' + str(e)
            res.append((c, text))
    return res

out_rows = []
for seed in range(N):
    for epoch in (False, True):
        out_rows.append(dict(seed=seed, epoch=epoch, res=run(seed, epoch)))
json.dump(out_rows, open(out, 'w'))
print(mode, tree[-30:], len(out_rows))
