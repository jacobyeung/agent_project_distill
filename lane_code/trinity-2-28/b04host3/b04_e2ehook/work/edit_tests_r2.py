p = '/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/tests/test_bestspread.py'
s = open(p).read()


def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b, 1)


rep('''def masks(geo, pad):
    """Pixels whose centres lie on the object in each frame, plus `pad` canvas units of background columns
    left and right of it in frame 1 (mask edges that spill onto the background)."""
    M = np.zeros((2, 100, 100), bool)
    for k in (1, 2):
        x0 = (np.array([-0.25, 0.25]) - geo.cam(k)[1][0]) * 250 + 500
        p = pad if k == 1 else 0
''', '''class BadGeo(Geo):
    """Geo whose lift returns non-finite world points (every 7th pixel), non-finite camera points (every 11th)
    and points behind the camera (every 5th), each with a low, finite spread so only the filter can drop them."""
    def lift(self, k, uv, mode='center'):
        P, pc, sp = (np.array(x, float) for x in Geo.lift(self, k, uv, mode))
        i = np.arange(len(P))
        P[i % 7 == 3] = np.nan
        pc[i % 11 == 4, 0] = np.inf
        pc[i % 5 == 2, 2] *= -1
        sp[(i % 7 == 3) | (i % 11 == 4) | (i % 5 == 2)] = 0.0
        return P, pc, sp


class StubGeo:
    """One frame; lift returns finite points in front of the camera with spreads 0, 1, ..., n-1."""
    def __init__(self):
        self.C = np.eye(4)[None]

    def has(self, k):
        return k == 1

    def lift(self, k, uv, mode='center'):
        n = len(uv)
        P = np.column_stack((np.arange(n, dtype=float), np.arange(n, dtype=float) ** 2, np.ones(n)))
        return P, P, np.arange(n, dtype=float)


def priced():
    raw = PRICED.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PRICED_SHA
    src = raw.decode()
    ns = dict(np=np, lift_plain=lift_plain, mask_pixels=mask_pixels)
    exec(src[src.index('def lift_best'):src.index('def project')], ns)
    exec(src[src.index('def _best_points'):src.index('def lift_bestotsu')], ns)
    return ns['lift_bestspread']


def masks(geo, pad, padded=1):
    """Pixels whose centres lie on the object in each frame, plus `pad` canvas units of background columns
    left and right of it in frame `padded` (mask edges that spill onto the background; that frame is the larger)."""
    M = np.zeros((2, 100, 100), bool)
    for k in (1, 2):
        x0 = (np.array([-0.25, 0.25]) - geo.cam(k)[1][0]) * 250 + 500
        p = pad if k == padded else 0
''')
rep('''def test_not_seen_passes_through():''', '''def test_later_larger_frame_is_best():
    g = Geo(); M = masks(g, 10, padded=2)
    r, plain = lift_bestspread('o', M, g), lift_plain('o', M, g)
    assert plain['best'] == 2 and r['best'] == 2 and list(r['points']) == ['2']
    P = np.asarray(r['points']['2'])
    assert len(P) and np.allclose(P[:, 2], 2.0)


def test_drops_non_finite_and_behind_camera_points():
    g = BadGeo(); M = masks(g, 10)
    r = lift_bestspread('o', M, g)
    uv = mask_pixels(M[0]); P, pc, _ = g.lift(1, uv)
    ok = np.isfinite(P).all(1) & np.isfinite(pc).all(1) & (pc[:, 2] > 0)
    kept = set(map(tuple, r['points']['1']))
    assert (~ok).sum() > 10 and kept and kept <= set(map(tuple, P[ok].tolist()))
    assert all(np.isfinite(p).all() for p in kept)


def test_fewer_than_four_kept_points_is_box_unavailable_not_unseen():
    """Documented difference: with fewer than 4 kept points the priced variant returns not seen; the shipped
    one stays seen and min_area_box raises box_needs_four_points (the tree prints `box unavailable`)."""
    from e2e_reader.grounding import min_area_box
    g = StubGeo(); M = np.zeros((1, 10, 10), bool); M[0, 0, :6] = True
    r, b = lift_bestspread('o', M, g), priced()('o', M, g)
    assert r['seen'] is True and len(r['points']['1']) == 3
    assert b['seen'] is False and b['points'] == {}
    try:
        min_area_box(r['points']['1'])
    except ValueError as e:
        assert str(e) == 'box_needs_four_points'
    else:
        raise AssertionError('min_area_box accepted 3 points')


def test_not_seen_passes_through():''')
rep('''def test_equals_priced_variant():
    raw = PRICED.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PRICED_SHA
    src = raw.decode()
    ns = dict(np=np, lift_plain=lift_plain, mask_pixels=mask_pixels)
    exec(src[src.index('def lift_best'):src.index('def project')], ns)
    exec(src[src.index('def _best_points'):src.index('def lift_bestotsu')], ns)
    g = Geo()
    for pad in (0, 10, 20):
        a, b = lift_bestspread('o', masks(g, pad), g), ns['lift_bestspread']('o', masks(g, pad), g)
        assert a['best'] == b['best'] and a['points'] == b['points'] and b['frames'] == [b['best']]''',
    '''def test_equals_priced_variant():
    ref, bests = priced(), set()
    for g in (Geo(), BadGeo()):
        for padded in (1, 2):
            for pad in (0, 10, 20):
                M = masks(g, pad, padded)
                a, b = lift_bestspread('o', M, g), ref('o', M, g)
                assert a['best'] == b['best'] and a['points'] == b['points'] and b['frames'] == [b['best']]
                bests.add(a['best'])
    assert bests == {1, 2}''')
rep('''zip((3, 4, 5), ((80, 90, 70, 110), (90, 100, 40, 60), (70, 120, 30, 40)))''',
    '''zip((3, 4, 5), ((70, 120, 30, 40), (90, 100, 40, 60), (80, 90, 70, 110)))''')
rep('''inst['best'] == plain['best']''', '''inst['best'] == plain['best'] == 5''')
rep('''    masks of different areas in frames 3-5.''', '''    masks of different areas in frames 3-5, the largest in frame 5.''')
open(p, 'w').write(s)
