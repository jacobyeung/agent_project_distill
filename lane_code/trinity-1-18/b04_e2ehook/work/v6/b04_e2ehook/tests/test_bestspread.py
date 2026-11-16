"""lift_bestspread (the reader's lifting, ORCH 1958Z): best frame only, points with depth-stencil spread at most
the frame's median; equal to the K1-priced variant (lift_price.py sha 8f78bf08) on synthetic reads."""
import os
from pathlib import Path
import numpy as np
import pytest
from e2e_reader.grounding import lift_bestspread, lift_plain, mask_pixels, ground_session, MinAreaBoxProvider

PRICED = Path(os.environ.get('LIFT_PRICE', '/dev/shm/jjyeung_b04/lift_price.py'))


class Geo:
    """Two pinhole frames looking down +z, camera 2 shifted +1 m in x; an object square at z=2 on a z=5
    background; the spread is (p80-p20)/p50 of depth over the tree's 5x5 stencil of +-10 canvas units."""
    def __init__(self):
        self.C = np.repeat(np.eye(4)[None], 2, 0); self.C[1, 0, 3] = 1.0
        self.K = np.repeat(np.array([[500., 0, 500], [0, 500., 500], [0, 0, 1.]])[None], 2, 0)
        self.A = np.repeat(np.eye(3)[None], 2, 0)

    def has(self, k):
        return 1 <= k <= len(self.C)

    def cam(self, k):
        return self.C[k - 1, :3, :3], self.C[k - 1, :3, 3]

    def _depth(self, k, uv):
        x0 = (np.array([-0.25, 0.25]) - self.cam(k)[1][0]) * 250 + 500
        inside = (uv[:, 0] >= x0[0]) & (uv[:, 0] <= x0[1]) & (np.abs(uv[:, 1] - 500) <= 62.5)
        return np.where(inside, 2.0, 5.0)

    def lift(self, k, uv, mode='center'):
        R, t = self.cam(k)
        uv = np.asarray(uv, float)
        off = np.array([(dx, dy) for dx in np.linspace(-10, 10, 5) for dy in np.linspace(-10, 10, 5)])
        d = self._depth(k, np.clip(uv[:, None] + off, 0, 1000).reshape(-1, 2)).reshape(len(uv), 25)
        p20, p50, p80 = np.percentile(d, (20, 50, 80), axis=1)
        pc = np.column_stack((uv, np.ones(len(uv)))) @ np.linalg.inv(self.K[k - 1]).T * self._depth(k, uv)[:, None]
        return pc @ R.T + t, pc, (p80 - p20) / np.maximum(p50, 1e-3)


def masks(geo, pad):
    """Pixels whose centres lie on the object in each frame, plus `pad` canvas units of background columns
    left and right of it in frame 1 (mask edges that spill onto the background)."""
    M = np.zeros((2, 100, 100), bool)
    for k in (1, 2):
        x0 = (np.array([-0.25, 0.25]) - geo.cam(k)[1][0]) * 250 + 500
        p = pad if k == 1 else 0
        M[k - 1, int(np.ceil(437.5 / 10)):int(562.5 / 10), int(np.ceil((x0[0] - p) / 10)):int((x0[1] + p) / 10)] = True
    return M


def test_drops_flying_ring_and_keeps_best_frame():
    g = Geo()
    plain, r = lift_plain('o', masks(g, 10), g), lift_bestspread('o', masks(g, 10), g)
    P = np.asarray(r['points']['1'])
    assert r['frames'] == plain['frames'] and r['best'] == 1 and list(r['points']) == ['1']
    assert np.allclose(P[:, 2], 2.0) and np.ptp(P[:, 0]) <= 0.5
    assert np.ptp(np.concatenate([np.asarray(v) for v in plain['points'].values()])[:, 0]) > 0.6


def test_not_seen_passes_through():
    g = Geo(); M = np.zeros((2, 100, 100), bool)
    assert lift_bestspread('o', M, g)['seen'] is False


@pytest.mark.skipif(not PRICED.is_file(), reason='priced lift_price.py not on this host')
def test_equals_priced_variant():
    src = PRICED.read_text()
    ns = dict(np=np, lift_plain=lift_plain, mask_pixels=mask_pixels)
    exec(src[src.index('def lift_best'):src.index('def lift_hull')], ns)
    exec(src[src.index('def _best_points'):src.index('def lift_bestotsu')], ns)
    g = Geo()
    for pad in (0, 10, 20):
        a, b = lift_bestspread('o', masks(g, pad), g), ns['lift_bestspread']('o', masks(g, pad), g)
        assert a['best'] == b['best'] and a['points'] == b['points'] and b['frames'] == [b['best']]


def test_session_uses_bestspread(monkeypatch):
    import e2e_reader.grounding as G
    calls = []
    monkeypatch.setattr(G, 'lift_bestspread', lambda *a: calls.append(a) or lift_plain(*a))
    g = Geo(); s = ground_session.__wrapped__ if hasattr(ground_session, '__wrapped__') else ground_session
    assert MinAreaBoxProvider.provider_id == 'e2e_minarea_bestspread_v1'
    src = Path(G.__file__).read_text()
    assert 'lifted = lift_bestspread(name' in src and 'lifted = lift_plain(name' not in src
