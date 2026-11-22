"""GTC-D relift_t on the real dump with toy d tracker outputs; equality assertions only, no value is printed or written.
  1. real t/s/b tracks + d = GT instance on every anchor (toy d track files through track_source with b's seeds, on the dense
     OK captures) -> d == e on every d item (cells and gaps), d precision/recall == 1, the d population is the ScanNet/ScanNet++
     items, and every a/e/t/s/b output equals RELIFT_GTCB.json (and the t/s part RELIFT_GTC.json);
  2. d = served masks (injected), with one capture excluded as if its anchors had failed the sha check -> d == a on the rest,
     the excluded capture's items carry no d, and the population label names the exclusion and the absence of ARKit;
  3. d = the real b tracks (injected) -> d == b, so d-b is 0 and the reading is not_the_source by 'd no better than b';
  4. the d section has every registered field and its reading equals reading_d on its own statistics;
  5. a d track directory missing one capture file is refused (FileNotFoundError); a file on another dense manifest is refused.
Each compute() also asserts its a and e equal a fresh in-process relift.run and relift.stats over the fresh rows.
p1cpu interpreter. Writes toy d track files (GT masks only) under gtcd/work/toy_tracks_d."""
import json, shutil, sys, time
from pathlib import Path
import numpy as np
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import gtc_common as G
import relift_t as RT

t0 = time.monotonic()
R = G.load_relift(); R.dependencies()
fresh = RT.fresh_relift(R)
print('fresh relift run done (values not shown) %.0f s' % (time.monotonic()-t0), flush=True)


def equal(rows, x, y):
    return all(r[x] == r[y] and r['gaps'][x] == r['gaps'][y] for r in rows)


d_caps, not_ok, datasets = RT.dense_population()
assert datasets == ['scannet', 'scannetpp'] and not not_ok and len(d_caps) == 28
assert all(not c.startswith('arkitscenes/') for c in d_caps)
dense_sha = G.sha256_file(G.DENSE_MANIFEST)
seeds_b = G.read_json(G.SEEDS_B)
toy = G.ROOT/'work/toy_tracks_d'
refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
items, objects, _ = G.eligible(R, refs)
gtp = {i['capture']: i['gt_path'] for i in items}
spec = dict(seeds_sha256=G.sha256_file(G.SEEDS_B), dense_sha256=dense_sha, toy=True)
for c in seeds_b['captures']:
    if c['capture'] not in d_caps:
        continue
    with np.load(gtp[c['capture']]) as z:
        inst = z['inst'].copy()
    recs = [dict(unit=u['unit'], masks=G.pack(inst == u['instance_id'])) for u in c['units'] if u['arm'] == 'b']
    G.write_json(toy/'d'/(G.stub(c['capture'])+'.json.gz'), dict(contract=spec, anchors=32, skipped_units=[], units=recs), gz=True)
src_ts = RT.track_source(G.GTC_OUT/'track')
src_b = RT.track_source(G.GTCB_OUT/'track', G.SEEDS_B, G.B_ARMS)
src_d = RT.track_source(toy, G.SEEDS_B, G.D_ARMS, seed_arm={'d': 'b'}, captures=d_caps, dense_sha=dense_sha)
n_sn = sum(1 for i in items if not i['capture'].startswith('arkitscenes/'))

# 1.
res = RT.compute(R, fresh, src_ts, src_b, src_d, d_caps)
drows = [r for r in res['rows'] if 'd' in r]
assert len(drows) == n_sn and all(r['capture'] in d_caps for r in drows) and all(r['dataset'] == 'ScanNet/ScanNet++' for r in drows)
assert equal(drows, 'd', 'e'), 'd = GT via track files differs from e'
assert all(v['precision'] == 1. and v['recall'] == 1. for v in res['d']['precision_recall'].values())
print('PASS d(GT track files) == e on the %d ScanNet/ScanNet++ items; d precision/recall == 1; no ARKit item carries d' % len(drows), flush=True)
assert RT.assert_ts_equal(res, src_ts.contract)
assert RT.assert_gtcb_equal(res, src_ts.contract, src_b.contract)
print('PASS a, e, t, s, b outputs (rows, statistics, precision/recall, readings, reproduction, section b) equal RELIFT_GTCB.json '
      'and the t/s part RELIFT_GTC.json', flush=True)

# 4. d section fields and reading (no value shown)
ds = {x['dataset']: x for x in res['d']['statistics']}
assert set(ds) == {'all', 'ScanNet/ScanNet++', 'ScanNet', 'ScanNet++'} and ds['all']['n'] == n_sn == ds['ScanNet']['n']+ds['ScanNet++']['n']
assert all(set(x['versus']) == {'d-a', 'd-b', 'd-t', 'e-a', 'b-a'} and set(x['share_of_e_minus_a']) >= {'mean', 'ci95'} and 'cell_d' in x
           for x in ds.values())
assert res['d']['reading'] == RT.reading_d(ds['all']['versus']['d-a'], ds['all']['versus']['d-b'])
assert res['d']['reading']['verdict'] in RT.D_VERDICTS and isinstance(res['d']['reading']['d_no_better_than_b'], bool)
assert set(res['d']['precision_recall']) == {'all', 'ScanNet', 'ScanNet++', 'ScanNet/ScanNet++'}
lab = RT.population_label(items, d_caps, not_ok, datasets)
assert lab.startswith('ScanNet+ScanNet++ items of the 117 (%d items)' % n_sn) and 'ARKit is absent' in lab and 'excluded' not in lab
print('PASS d section: overall and per-dataset statistics, d-a/d-b/d-t/e-a/b-a, share, precision/recall, reading, population label', flush=True)

# 2. served masks injected for d, one capture excluded
victim = sorted(d_caps)[0]; caps2 = d_caps - {victim}
res2 = RT.compute(R, fresh, src_ts, src_b, lambda arm, ctx: ctx['served'], caps2)
d2 = [r for r in res2['rows'] if 'd' in r]
assert equal(d2, 'd', 'a') and len(d2) == n_sn - sum(1 for i in items if i['capture'] == victim)
assert not any('d' in r for r in res2['rows'] if r['capture'] == victim)
assert RT.assert_gtcb_equal(res2, src_ts.contract, src_b.contract)
lab2 = RT.population_label(items, caps2, {victim: 'SHA_MISMATCH'}, datasets)
assert ('%s (SHA_MISMATCH)' % victim) in lab2 and 'ARKit is absent' in lab2
print('PASS d(served) == a; an excluded capture carries no d and is named in the label; other cells unchanged', flush=True)

# 3. real b tracks injected for d -> d == b and the 'no better than b' clause decides
res3 = RT.compute(R, fresh, src_ts, src_b, lambda arm, ctx: src_b('b', ctx), d_caps)
d3 = [r for r in res3['rows'] if 'd' in r]
assert equal(d3, 'd', 'b')
r3 = res3['d']['reading']; s3 = res3['d']['statistics'][0]['versus']
assert s3['d-b']['mean'] == 0 and r3['d_no_better_than_b'] and r3['verdict'] in ('not_the_source', 'source_when_dense')
assert r3 == RT.reading_d(s3['d-a'], s3['d-b'])
print('PASS d(b tracks) == b; d-b == 0 sets d_no_better_than_b and the reading follows reading_d', flush=True)

# 5. missing d track file and a file on another dense manifest are refused
bad = G.ROOT/'work/toy_tracks_d_missing'
if not bad.exists():
    shutil.copytree(toy, bad)
    v = next((bad/'d').glob('*.json.gz')); v.rename(v.with_name(v.name+'.aside'))
try:
    RT.track_source(bad, G.SEEDS_B, G.D_ARMS, seed_arm={'d': 'b'}, captures=d_caps, dense_sha=dense_sha)
    raise AssertionError('d track directory with a missing capture accepted')
except FileNotFoundError:
    print('PASS d track directory with a missing capture file refused', flush=True)
try:
    RT.track_source(toy, G.SEEDS_B, G.D_ARMS, seed_arm={'d': 'b'}, captures=d_caps, dense_sha='0'*64)
    raise AssertionError('d track files on another dense manifest accepted')
except ValueError:
    print('PASS d track files on another dense manifest refused', flush=True)
print(json.dumps(dict(status='PASS', seconds=round(time.monotonic()-t0))))
