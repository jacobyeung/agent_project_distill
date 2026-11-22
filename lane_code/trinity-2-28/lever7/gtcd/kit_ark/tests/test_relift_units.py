"""kit_ark relift_t: both d units on the real dump with toy d tracks; equality assertions only, no value is printed.
Toy units under gtcd/work/toy_units: the ScanNet unit on the real dense/DENSE_D.json (28 OK captures), the ARKit unit on a toy
manifest (dense_ark/DENSE_D_ARK.json, datasets ['arkit'], the 18 ARKit captures with status OK); toy d track files hold the GT
instance on every anchor (the bound instance of b's seed units).
  1. relift_t.main on both units (d = GT): d == e (cells and gaps) on every row, the three populations scannet_scannetpp (84),
     arkit (33) and pooled (117) are read, each P/R is 1, each reading equals reading_d on its own statistics, labels name the
     population and the pooled label says all 117; a, e, t, s, b equal RELIFT_GTCB.json (main asserts it); the output carries
     both units' contracts;
  2. compute with populations and d = the real b tracks (injected) -> d == b and d-b == 0 in every population, which sets
     d_no_better_than_b in each;
  3. relift_t.main with the ARKit unit absent -> scannet_scannetpp read, arkit and pooled not_read with their reasons;
  4. unit_state: a unit missing one track file is 'incomplete' (file listed); a manifest of the wrong datasets, or track files on
     another dense manifest, raise; no complete unit refuses.
p1cpu interpreter. Writes only under gtcd/work/toy_units."""
import json, shutil, sys, time
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import gtc_common as G
import relift_t as RT

t0 = time.monotonic()
W = G.ROOT/'work/toy_units'
R = G.load_relift(); R.dependencies()
_fresh = {}
_orig_fresh = RT.fresh_relift
def cached_fresh(R):
    if 'v' not in _fresh:
        _fresh['v'] = _orig_fresh(R)
    return _fresh['v']
RT.fresh_relift = cached_fresh
refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
items, objects, _ = G.eligible(R, refs)
gtp = {i['capture']: i['gt_path'] for i in items}
seeds_b = G.read_json(G.SEEDS_B)


def equal(rows, x, y):
    return all(r[x] == r[y] and r['gaps'][x] == r['gaps'][y] for r in rows)


# toy ARKit manifest (only what relift reads: datasets, captures with status)
ark_caps = sorted(c['capture'] for c in G.read_frames_index()['captures'] if c['capture'].startswith('arkitscenes/'))
assert len(ark_caps) == 18
ark_man = W/'dense_ark/DENSE_D_ARK.json'
G.write_json(ark_man, dict(schema='toy', datasets=['arkit'], captures=[dict(capture=c, status='OK') for c in ark_caps]))
sn_caps, sn_not_ok, sn_ds = RT.dense_population(G.DENSE_MANIFEST)
assert sn_ds == ['scannet', 'scannetpp'] and len(sn_caps) == 28 and not sn_not_ok


def toy_tracks(d, caps, dense_path):
    spec = dict(seeds_sha256=G.sha256_file(G.SEEDS_B), dense_sha256=G.sha256_file(dense_path), toy=True)
    for c in seeds_b['captures']:
        if c['capture'] not in caps:
            continue
        with np.load(gtp[c['capture']]) as z:
            inst = z['inst'].copy()
        recs = [dict(unit=u['unit'], masks=G.pack(inst == u['instance_id'])) for u in c['units'] if u['arm'] == 'b']
        if recs:
            G.write_json(d/'d'/(G.stub(c['capture'])+'.json.gz'), dict(contract=spec, anchors=32, skipped_units=[], units=recs), gz=True)


toy_sn, toy_ark = W/'out/track', W/'out_ark/track'
toy_tracks(toy_sn, sn_caps, G.DENSE_MANIFEST); toy_tracks(toy_ark, set(ark_caps), ark_man)
n_sn = sum(1 for i in items if i['capture'] in sn_caps); n_ark = sum(1 for i in items if i['capture'] in ark_caps)
assert n_sn + n_ark == 117
base = ['--tracks-d', str(toy_sn), '--dense', str(G.DENSE_MANIFEST), '--gtcd-relift', str(W/'absent_RELIFT_GTCD.json')]

# 1.
out1 = W/'RELIFT_both.json'
assert RT.main(base+['--tracks-d-ark', str(toy_ark), '--dense-ark', str(ark_man), '--out', str(out1)]) == 0
res = G.read_json(out1)
assert res['status'] == 'complete' and set(res['track_contract_digest_d']) == {'scannet_scannetpp', 'arkit'}
assert equal([r for r in res['rows']], 'd', 'e') and all('d' in r for r in res['rows'])
want = dict(scannet_scannetpp=(n_sn, {'all', 'ScanNet/ScanNet++', 'ScanNet', 'ScanNet++'}), arkit=(n_ark, {'all', 'ARKit'}),
            pooled=(117, {'all', 'ScanNet/ScanNet++', 'ARKit', 'ScanNet', 'ScanNet++'}))
for key, (n, groups) in want.items():
    sec = res['d'][key]
    st = {x['dataset']: x for x in sec['statistics']}
    assert sec['status'] == 'read' and sec['items'] == n == st['all']['n'] and set(st) == groups, key
    assert all(set(x['versus']) == {'d-a', 'd-b', 'd-t', 'e-a', 'b-a'} and 'mean' in x['share_of_e_minus_a'] for x in st.values())
    assert sec['headline']['d-a'] == st['all']['versus']['d-a'] and sec['headline']['d-b'] == st['all']['versus']['d-b']
    assert sec['reading'] == RT.reading_d(st['all']['versus']['d-a'], st['all']['versus']['d-b'])
    assert set(sec['precision_recall']) == groups and all(v['precision'] == 1. and v['recall'] == 1. for v in sec['precision_recall'].values())
    assert sec['population']['label'].startswith('%s items of the 117 (%d items)' % (RT.UNIT_NAMES[key], n)), key
assert 'all 117 items' in res['d']['pooled']['population']['label'] and 'excluded' not in res['d']['pooled']['population']['label']
assert res['d']['units']['scannet_scannetpp']['status'] == res['d']['units']['arkit']['status'] == 'complete'
assert res['d']['units']['scannet_scannetpp']['equals_relift_gtcd'] is None
print('PASS both units, d = GT: d == e on all 117 rows; scannet_scannetpp (%d), arkit (%d), pooled (117) read, each with its own '
      'reading, d-a beside d-b, share, per-dataset P/R == 1 and its label; a/e/t/s/b equal RELIFT_GTCB.json' % (n_sn, n_ark), flush=True)

# 2. d = real b tracks injected, populations as main builds them
src_ts = RT.track_source(G.GTC_OUT/'track'); src_b = RT.track_source(G.GTCB_OUT/'track', G.SEEDS_B, G.B_ARMS)
pops = dict(scannet_scannetpp=set(sn_caps), arkit=set(ark_caps)); pops['pooled'] = pops['scannet_scannetpp'] | pops['arkit']
res2 = RT.compute(R, cached_fresh(R), src_ts, src_b, lambda arm, ctx: src_b('b', ctx), pops['pooled'], populations=pops)
assert equal(res2['rows'], 'd', 'b')
for key in pops:
    sec = res2['d'][key]; v = sec['statistics'][0]['versus']
    assert v['d-b']['mean'] == 0 and sec['reading']['d_no_better_than_b'] and sec['reading'] == RT.reading_d(v['d-a'], v['d-b']), key
assert RT.assert_gtcb_equal(res2, src_ts.contract, src_b.contract)
print('PASS d = b tracks: d == b, d-b == 0 and d_no_better_than_b in each of the three populations', flush=True)

# 3. ARKit unit absent
out3 = W/'RELIFT_sn_only.json'
assert RT.main(base+['--tracks-d-ark', str(W/'no_such/track'), '--dense-ark', str(W/'no_such/DENSE_D_ARK.json'), '--out', str(out3)]) == 0
res3 = G.read_json(out3)
assert res3['d']['scannet_scannetpp']['status'] == 'read' and res3['d']['scannet_scannetpp']['items'] == n_sn
assert res3['d']['arkit'] == dict(status='not_read', reason='unit absent: no dense manifest')
assert res3['d']['pooled']['status'] == 'not_read' and 'both units' in res3['d']['pooled']['reason']
assert not any('d' in r for r in res3['rows'] if r['capture'] in ark_caps)
print('PASS ARKit unit absent: the ScanNet unit is read alone; arkit and pooled not_read with their reasons', flush=True)

# 4. unit_state edges
bad = W/'out_ark_missing/track'
if not bad.exists():
    shutil.copytree(toy_ark, bad)
    v = sorted((bad/'d').glob('*.json.gz'))[0]; v.rename(v.with_name(v.name+'.aside'))
st, src, _, _ = RT.unit_state('arkit', ark_man, bad)
assert st['status'] == 'incomplete' and src is None and len(st['missing']) == 1
for args in (('arkit', G.DENSE_MANIFEST, toy_sn), ('scannet_scannetpp', ark_man, toy_ark)):
    try:
        RT.unit_state(*args); raise AssertionError('wrong-dataset manifest accepted')
    except ValueError:
        pass
other = W/'dense_ark_other/DENSE_D_ARK.json'
G.write_json(other, dict(schema='toy2', datasets=['arkit'], captures=[dict(capture=c, status='OK') for c in ark_caps]))
try:
    RT.unit_state('arkit', other, toy_ark); raise AssertionError('track files on another dense manifest accepted')
except ValueError:
    pass
try:
    RT.main(base[:0]+['--tracks-d', str(bad.parent/'none'), '--dense', str(W/'none.json'), '--tracks-d-ark', str(bad),
                      '--dense-ark', str(ark_man), '--out', str(W/'never.json')])
    raise AssertionError('no complete unit accepted')
except SystemExit as x:
    assert 'no complete d unit' in str(x)
assert not (W/'never.json').exists()
print('PASS unit_state: missing track file -> incomplete (listed); wrong-dataset manifest and foreign dense manifest raise; '
      'no complete unit refused', flush=True)
print(json.dumps(dict(status='PASS', seconds=round(time.monotonic()-t0))))
