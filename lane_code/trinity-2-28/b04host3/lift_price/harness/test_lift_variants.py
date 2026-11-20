"""CPU tests for the lifting variants of lift_price.py (the exact bytes priced): best-frame and majority hull."""
import os, sys
from pathlib import Path
import numpy as np
READER = Path(os.environ.get('B04_READER', '/scratch/jjyeung/orch_n30/b04_e2ehook'))
sys.path.insert(0, str(READER))
from e2e_reader.grounding import lift_plain
SRC = Path(os.environ.get('LIFT_PRICE', Path(__file__).with_name('lift_price.py'))).read_text()
from e2e_reader.grounding import mask_pixels
ns = dict(np=np, lift_plain=lift_plain, mask_pixels=mask_pixels)
exec(SRC[SRC.index('def lift_best'):SRC.index('LIFTS = dict')], ns)
lift_best, lift_hull, lift_besthull = ns['lift_best'], ns['lift_hull'], ns['lift_besthull']


class Geo:
    """Two pinhole frames looking down +z, camera 2 shifted +1 m in x; object plane z=2 in a square, background z=5."""
    def __init__(self, n=2):
        self.C = np.repeat(np.eye(4)[None], n, 0); self.C[1, 0, 3] = 1.0
        f = 500.; self.K = np.repeat(np.array([[f, 0, 500], [0, f, 500], [0, 0, 1.]])[None], n, 0)
        self.A = np.repeat(np.eye(3)[None], n, 0)

    def has(self, k):
        return 1 <= k <= len(self.C)

    def cam(self, k):
        return self.C[k - 1, :3, :3], self.C[k - 1, :3, 3]

    def lift(self, k, uv, mode='center'):
        R, t = self.cam(k)
        ray = np.column_stack((uv, np.ones(len(uv)))) @ np.linalg.inv(self.K[k - 1]).T
        # depth 2 inside the object's image square, 5 outside (the flying-pixel background)
        x0 = (np.array([-0.25, 0.25]) - t[0]) * 500 / 2 + 500
        inside = (uv[:, 0] >= x0[0]) & (uv[:, 0] <= x0[1]) & (np.abs(uv[:, 1] - 500) <= 62.5)
        d = np.where(inside, 2.0, 5.0)
        pc = ray * d[:, None]
        return pc @ R.T + t, pc, np.zeros(len(uv))


def masks(geo, pad):
    """Pixels whose centres lie on the object square in each frame, plus `pad` canvas units of background ring in frame 1 only."""
    M = np.zeros((2, 100, 100), bool)
    for k in (1, 2):
        t = geo.cam(k)[1]
        x0 = (np.array([-0.25, 0.25]) - t[0]) * 500 / 2 + 500
        p = pad if k == 1 else 0
        c0, c1 = int(np.ceil((x0[0] - p) / 10)), int((x0[1] + p) / 10)
        r0, r1 = int(np.ceil((500 - 62.5 - p) / 10)), int((500 + 62.5 + p) / 10)
        M[k - 1, r0:r1, c0:c1] = True
    return M


def span(r):
    P = np.concatenate([np.asarray(r['points'][str(f)]) for f in r['frames']])
    return P[:, 0].max() - P[:, 0].min()


def test_plain_inflated_by_background_ring():
    g = Geo(); r = lift_plain('obj', masks(g, 30), g)
    assert r['seen'] and span(r) > 0.9


def test_hull_carves_background_ring():
    g = Geo(); r = lift_hull('obj', masks(g, 30), g)
    assert r['seen'] and span(r) < 0.6
    P = np.concatenate([np.asarray(r['points'][str(f)]) for f in r['frames']])
    assert np.allclose(P[:, 2], 2.0)


def test_hull_keeps_consistent_object():
    g = Geo(); a = lift_plain('obj', masks(g, 0), g); b = lift_hull('obj', masks(g, 0), g)
    assert b['frames'] == a['frames'] and sum(map(len, b['points'].values())) >= 0.9 * sum(map(len, a['points'].values()))


def test_best_keeps_only_largest_frame():
    g = Geo(); r = lift_best('obj', masks(g, 30), g)
    assert r['frames'] == [1] and list(r['points']) == ['1']
    r = lift_besthull('obj', masks(g, 30), g)
    assert len(r['frames']) == 1 and span(r) < 0.6


def test_single_frame_object_untouched_by_hull():
    g = Geo(); M = masks(g, 30); M[1] = False
    a, b = lift_plain('obj', M, g), lift_hull('obj', M, g)
    assert a['points'] == b['points']


def test_bestspread_and_bestotsu_on_ring():
    exec(SRC[SRC.index('def _best_points'):SRC.index('LIFTS = dict')], ns)
    g = Geo()  # a one-pixel background ring: thinner than the object, as at real mask edges
    r = ns['lift_bestotsu']('obj', masks(g, 10), g)
    assert r['frames'] == [1] and span(r) < 0.6
    P = np.asarray(r['points']['1']); assert np.allclose(P[:, 2], 2.0)
    r = ns['lift_bestspread']('obj', masks(g, 10), g)
    assert r['frames'] == [1] and len(r['points']['1']) > 0
