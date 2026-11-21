"""Synthetic CPU tests: seed rules, frame order, mask resize, carry rule, precision/recall, codecs, forecast.
p1cpu interpreter (numpy, scipy); imports relift.py unchanged only for the served raster resize. Prints test names and PASS."""
import json, sys
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import gtc_common as G
import seeds as S
import track as T
import relift_t as RT

R = G.load_relift(); R.dependencies()
rng = np.random.default_rng(20261121)
RESULTS = []


def case(fn):
    fn(); RESULTS.append(fn.__name__); print('PASS', fn.__name__, flush=True)
    return fn


@case
def test_t_seed_first_visible():
    m = np.zeros((32,)+G.GRID, bool)
    assert S.first_visible(m) is None
    m[6, 10, 10] = True; m[3, 5:8, 5:8] = True
    assert S.first_visible(m) == 4            # first anchor with a pixel, 1-based
    assert S.first_visible(m, 10) is None     # 9 px on anchor 4, 1 px on anchor 7
    assert S.first_visible(m, 9) == 4
    m[0, 0, 0] = True
    assert S.first_visible(m) == 1


@case
def test_s_seed_rule_k1_s_a0():
    class Stub:
        def __init__(self, best, seen=True):
            self.best, self.seen = best, seen
            self.grounding = self
            self.masks_array = lambda sel: np.asarray(sel, bool)
        def lift_bestspread(self, name, masks, g):
            return dict(seen=self.seen, best=self.best)
    masks = rng.random((32,)+G.GRID) > .7
    st, slot, mm = S.served_seed(Stub(5), 'chair', dict(selected_masks=masks), None)
    assert (st, slot) == ('OK', 5) and np.array_equal(mm[slot-1], masks[4])
    assert S.served_seed(Stub(5, False), 'chair', dict(selected_masks=masks), None)[:2] == ('UNSEEN', None)
    assert S.served_seed(Stub(5), 'chair', None, None)[:2] == ('NO_SERVED_OBJECT', None)


@case
def test_lift_best_is_largest_lifted_area_ties_lowest():
    # The deployed lift_plain best rule, read from the source the dump ran (K1 S_A0 used obj['best'] of the same lift).
    src = Path(R.grounding.__file__).read_text()
    assert 'largest mask area among frames with lifted' in src


@case
def test_frame_order_and_plan():
    seeds = dict(captures=[dict(capture='b/2', units=[dict(unit='t_1', arm='t', seed_slot=3), dict(unit='s_x', arm='s', seed_slot=30)]),
                           dict(capture='a/1', units=[dict(unit='t_2', arm='t', seed_slot=5)])])
    p = T.plan(seeds, ['t', 's'], 'all', 32)
    assert [(a, c['capture']) for a, c, _, _ in p] == [('t', 'a/1'), ('t', 'b/2'), ('s', 'a/1'), ('s', 'b/2')]
    p4 = T.plan(seeds, ['t', 's'], 'all', 4)
    assert [u['unit'] for u in p4[1][2]] == ['t_1'] and p4[0][3] == ['t_2'] and p4[3][3] == ['s_x']
    f = G.read_frames_index()
    assert f['eligible_captures'] == 46 and not f['missing']
    for c in f['captures']:
        assert [x['slot'] for x in c['frames']] == list(range(1, 33))
        idx = [x['index'] for x in c['frames']]
        assert idx == c['anchor_indices'] and all(a < b for a, b in zip(idx, idx[1:]))


@case
def test_mask_resize_served_path():
    for _ in range(20):
        m = rng.random(G.GRID) > rng.uniform(.3, .99)
        up = G.seed_to_canvas(m, R.resize)
        assert up.shape == G.CANVAS and up.dtype == bool
        assert np.array_equal(G.canvas_to_grid(up), m)          # round trip is exact at the 2x ratio
        assert np.array_equal(up, R.resize(m, G.CANVAS))         # the served raster's own resize, unchanged
    big = rng.random(G.CANVAS) > .5
    assert np.array_equal(G.canvas_to_grid(big), big[::2, ::2])
    odd = rng.random((360, 480)) > .5
    assert G.canvas_to_grid(odd, R.resize).shape == G.GRID
    try:
        G.canvas_to_grid(odd); raise AssertionError('non-canvas mask accepted without the served resize')
    except ValueError:
        pass


@case
def test_carry_rule():
    n = 32; seed = np.zeros(G.GRID, bool); seed[10:20, 10:20] = True
    pos = np.zeros(G.CANVAS, bool); pos[0:40, 0:40] = True
    result = {t: (pos, 1.5) for t in range(4, n)}
    result[4] = (np.zeros(G.CANVAS, bool), 9.)   # seed frame output is replaced by the seed itself
    result[6] = (pos, -0.1)                      # non-positive score -> empty
    result[7] = (np.zeros(G.CANVAS, bool), 0.3)  # positive empty
    grid, scores, carried, pe = T.carried_masks(result, 5, seed, n)
    assert not grid[:4].any() and not any(carried[:4]) and scores[:4] == [None]*4   # before the seed: empty (forward)
    assert np.array_equal(grid[4], seed) and carried[4]
    assert not grid[6].any() and not carried[6] and scores[6] == -0.1
    assert carried[7] and not grid[7].any() and pe == 1
    assert np.array_equal(grid[8], pos[::2, ::2]) and carried[8]
    assert T.object_frames('t', 5, 32, 'both') == 28 and T.object_frames('s', 5, 32, 'both') == 32 and T.object_frames('s', 5, 32, 'forward') == 28


@case
def test_precision_recall_toy():
    P = np.zeros((4, 2, 4), bool); Gt = np.zeros((4, 2, 4), bool)
    P[0, 0, :2] = True; Gt[0, 0, 1:3] = True     # frame 1: inter 1, |P| 2, |G| 2
    P[1, 0, 0] = True                            # frame 2: prediction only -> precision 0, recall undefined
    Gt[2, 1, :] = True                           # frame 3: GT only -> recall 0, precision undefined
    recs = G.precision_recall(P, Gt)             # frame 4: both empty -> excluded
    assert [r['frame'] for r in recs] == [1, 2, 3]
    assert recs[0] == dict(frame=1, precision=.5, recall=.5)
    assert recs[1] == dict(frame=2, precision=0., recall=None) and recs[2] == dict(frame=3, precision=None, recall=0.)
    s = G.summarize_pr(recs)
    assert s == dict(union_frames=3, pred_frames=2, gt_frames=2, precision=.25, recall=.25)
    assert G.summarize_pr(G.precision_recall(Gt, Gt))['precision'] == 1. == G.summarize_pr(G.precision_recall(Gt, Gt))['recall']


@case
def test_codecs():
    m = rng.random((32,)+G.GRID) > .8
    assert np.array_equal(G.unpack(json.loads(json.dumps(G.pack(m)))), m)
    assert G.mask_sha(m) == G.mask_sha(m.copy()) != G.mask_sha(~m)
    assert G.mask_sha(np.zeros((2, 3), bool)) != G.mask_sha(np.zeros((3, 2), bool))


@case
def test_binding_digest_reproduces():
    caps, dense = G.frame_manifests()
    refs = json.loads(G.ITEMS.read_text())['items']
    assert all(G.binding(r['mapping']['native'], caps, dense) == r['mapping']['frame_binding_sha256'] for r in refs)


@case
def test_forecast_arithmetic():
    seeds = dict(captures=[dict(capture='a/1', units=[dict(unit='t_1', arm='t', seed_slot=1), dict(unit='t_2', arm='t', seed_slot=31),
                                                      dict(unit='s_1', arm='s', seed_slot=16)])])
    k = T.K1
    f = T.forecast(seeds, ['t', 's'])
    want_t = k['overhead_per_unit']+32*k['embed_per_frame']+(32+2)*k['track_per_object_frame']
    want_s = k['overhead_per_unit']+32*k['embed_per_frame']+32*k['track_per_object_frame']
    assert abs(f['by_arm']['t']['seconds']-want_t) < 1e-9 and abs(f['by_arm']['s']['seconds']-want_s) < 1e-9
    assert abs(f['total_seconds']-(want_t+want_s+k['load_seconds'])) < 1e-9
    assert T.forecast(seeds, ['t'])['by_arm'].keys() == {'t'}


@case
def test_real_seeds_consistent():
    s = G.read_json(G.OUT/'SEEDS_GTC.json')
    assert s['summary']['items'] == 117 and s['summary']['captures'] == 46
    for c in s['captures']:
        assert G.sha256_file(c['seeds_file']) == c['seeds_sha256']
        for u in c['units']:
            m240, m480 = T.load_seed(c['seeds_file'], u['unit'])
            assert G.mask_sha(m240) == u['seed_sha256_240'] and G.mask_sha(m480) == u['seed_sha256_480'] and m240.any()
            assert np.array_equal(m480, G.seed_to_canvas(m240, R.resize))
    # t seeds sit on the first visible anchor of their GT instance
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    gtp = {i['capture']: i['gt_path'] for i in items}
    units = {(c['capture'], u['unit']): (c, u) for c in s['captures'] for u in c['units']}
    for o in s['objects'][:60]:
        if o['t']['status'] != 'OK':
            continue
        with np.load(gtp[o['capture']]) as z:
            target = z['inst'] == o['instance_id']
        c, u = units[(o['capture'], o['t']['unit'])]
        assert u['seed_slot'] == S.first_visible(target) == o['t']['slot']
        assert np.array_equal(T.load_seed(c['seeds_file'], u['unit'])[0], target[u['seed_slot']-1])


def _m(mean, lo, hi):
    return dict(mean=mean, ci95=[lo, hi], defined_draws=10000, undefined_draws=0)


@case
def test_seed200_membership_count():
    # Population count only (registration: 58 of 117 items); the per-object path compute() uses must agree.
    s = G.read_json(G.OUT/'SEEDS_GTC.json')
    members = RT.seed200_items(s)
    assert len({o['item_id'] for o in s['objects']}) == 117 and len(members) == 58
    area = {(c['capture'], u['unit']): u['area_240'] for c in s['captures'] for u in c['units'] if u['arm'] == 't'}
    by_item = {}
    for o in s['objects']:
        by_item.setdefault(o['item_id'], []).append(o['t']['status'] == 'OK' and area[(o['capture'], o['t']['unit'])] >= 200)
    assert {i for i, v in by_item.items() if all(v)} == members
    # synthetic: one small seed or one missing seed excludes the item
    toy = dict(captures=[dict(capture='c', units=[dict(unit='u1', arm='t', area_240=200), dict(unit='u2', arm='t', area_240=199),
                                                  dict(unit='s1', arm='s', area_240=5)])],
               objects=[dict(item_id='i1', capture='c', t=dict(status='OK', unit='u1')),
                        dict(item_id='i1', capture='c', t=dict(status='OK', unit='u1')),
                        dict(item_id='i2', capture='c', t=dict(status='OK', unit='u1')),
                        dict(item_id='i2', capture='c', t=dict(status='OK', unit='u2')),
                        dict(item_id='i3', capture='c', t=dict(status='OK', unit='u1')),
                        dict(item_id='i3', capture='c', t=dict(status='NOT_VISIBLE', unit=None))])
    assert RT.seed200_items(toy) == {'i1'}


@case
def test_reading_guard_branches():
    src, nots, mid = _m(9., .5, 17.), _m(2., -3., 7.), _m(6., -1., 13.)
    sub_meets, sub_misses = _m(10., 1., 19.), _m(10., -1., 21.)
    # 1. first bar met: source, whatever the subset shows
    assert RT.reading(src, sub_misses)['verdict'] == 'source_once_seed_right'
    assert RT.reading(src, sub_meets, _m(9., 1., 17.))['s_minus_a_meets_first_bar'] is True
    # 2. second bar met, subset misses the first bar: not the source
    assert RT.reading(nots, sub_misses)['verdict'] == 'not_the_source'
    assert RT.reading(nots, dict(mean=None, ci95=None))['verdict'] == 'not_the_source'
    # 3. second bar met, subset meets the first bar: the guard makes it undecided
    r = RT.reading(nots, sub_meets); assert r['verdict'] == 'undecided' and 'guard' in r['reason']
    # 4. neither bar: undecided, and the guard does not change it
    assert RT.reading(mid, sub_meets)['verdict'] == 'undecided' and RT.reading(mid, sub_misses)['verdict'] == 'undecided'
    assert 'guard' not in RT.reading(mid, sub_meets)['reason']
    assert RT.reading(dict(mean=None, ci95=None), sub_meets)['verdict'] == 'undecided'
    assert all(RT.reading(f, b)['verdict'] in RT.VERDICTS for f in (src, nots, mid) for b in (sub_meets, sub_misses))


@case
def test_reading_bar_edges():
    v = lambda m, lo, hi, sub=_m(0., -1., 1.): RT.reading(_m(m, lo, hi), sub)['verdict']
    assert v(8., 1e-9, 16.) == 'source_once_seed_right'
    assert v(8., 0., 16.) == 'undecided'                 # lower bound must be > 0
    assert v(np.nextafter(8., 0), 1., 16.) == 'undecided' # mean must be >= 8
    assert v(4., -4., np.nextafter(8., 0)) == 'not_the_source'
    assert v(4., -4., 8.) == 'undecided'                 # upper bound must be < 8
    assert v(np.nextafter(4., 5), -4., 7.) == 'undecided' # mean must be <= 4
    # subset edges of the guard
    assert v(4., -4., 7., _m(8., 1e-9, 16.)) == 'undecided'
    assert v(4., -4., 7., _m(8., 0., 16.)) == 'not_the_source'
    assert v(4., -4., 7., _m(np.nextafter(8., 0), 1., 16.)) == 'not_the_source'


print(json.dumps(dict(status='PASS', tests=len(RESULTS))))
