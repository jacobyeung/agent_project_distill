"""lift_bestspread (the reader's lifting, ORCH 1958Z): best frame only, points with depth-stencil spread at most
the frame's median; equal to the K1-priced variant (lift_price.py sha 8f78bf08) on synthetic reads."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from e2e_reader.grounding import lift_bestspread, lift_plain, mask_pixels, ground_session, MinAreaBoxProvider

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449']
PRICED = ROOT / 'tests/data/lift_price_v2_8f78bf08.py'  # frozen copy of the K1-priced harness, checked by sha256
PRICED_SHA = '8f78bf0825574be3bd37ef236e6ea2a9e29c68e1035ee18e2da93a11c8363c1c'
GEO = ROOT / 'work/n13/ret/native/geometry'


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


def test_equals_priced_variant():
    raw = PRICED.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PRICED_SHA
    src = raw.decode()
    ns = dict(np=np, lift_plain=lift_plain, mask_pixels=mask_pixels)
    exec(src[src.index('def lift_best'):src.index('def project')], ns)
    exec(src[src.index('def _best_points'):src.index('def lift_bestotsu')], ns)
    g = Geo()
    for pad in (0, 10, 20):
        a, b = lift_bestspread('o', masks(g, pad), g), ns['lift_bestspread']('o', masks(g, pad), g)
        assert a['best'] == b['best'] and a['points'] == b['points'] and b['frames'] == [b['best']]


def _served(monkeypatch, lift=None):
    """A real ground_session on a dev-S1 geometry behind a fake stage-1 socket: one candidate for 'a' with
    masks of different areas in frames 3-5. Returns (servers, session, masks, geometry, calls)."""
    import e2e_reader.grounding as G
    from e2e_reader import geometry as GM
    from e2e_reader.grounding import StageOneSocket
    from e2e_reader.servers import ReadServers
    clip = sorted(json.loads((ROOT / 'out/proofs/GUARD_VERDICTS_DEVS1.json').read_text())['per_clip'])[0]
    geo = GM.from_npz(GEO / (clip + '.npz'))
    M = {}
    for k, (r0, c0, h, w) in zip((3, 4, 5), ((80, 90, 70, 110), (90, 100, 40, 60), (70, 120, 30, 40))):
        if geo.has(k):
            M[k] = np.zeros((240, 320), bool); M[k][r0:r0 + h, c0:c0 + w] = True
    calls = []
    real = lift if lift is not None else G.lift_bestspread
    monkeypatch.setattr(G, 'lift_bestspread', lambda *a: calls.append(a[0]) or real(*a))
    session = ground_session(geo, StageOneSocket(lambda name: ([dict(candidate_id=name + ':0', masks=M)], None),
                                                 lambda x: 0, (240, 320), GM.frame_count(geo)))
    full = np.zeros((GM.frame_count(geo), 240, 320), bool)
    for k, m in M.items():
        full[k - 1] = m
    return ReadServers(geo, session), session, full, geo, calls


def test_session_uses_bestspread(monkeypatch):
    assert MinAreaBoxProvider.provider_id == 'e2e_minarea_bestspread_v1'
    servers, session, full, geo, calls = _served(monkeypatch)
    text = servers.session_call('<ground obj="a" mode="box">')[0]
    assert calls == ['a'] and not text.startswith('error'), text
    inst, = session._instances('a')
    want = lift_bestspread('a', full, geo)
    assert inst['points'] == want['points'] and list(inst['points']) == [str(inst['best'])]
    plain = lift_plain('a', full, geo)
    assert inst['frames'] == plain['frames'] and len(inst['frames']) > 1 and inst['best'] == plain['best']
    kept, every = (set(map(tuple, p)) for p in (inst['points'][str(inst['best'])], plain['points'][str(plain['best'])]))
    assert kept and kept < every
    plain_servers = _served(monkeypatch, lift=lift_plain)[0]
    assert plain_servers.session_call('<ground obj="a" mode="box">')[0] != text


def test_session_error_comes_from_bestspread(monkeypatch):
    def boom(*a):
        raise ValueError('spy_bestspread')
    servers = _served(monkeypatch, lift=boom)[0]
    assert servers.session_call('<ground obj="a" mode="box">')[0] == 'error: spy_bestspread'
