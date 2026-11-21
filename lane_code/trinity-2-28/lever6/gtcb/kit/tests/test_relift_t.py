"""GTC-B relift_t on the real dump with toy b tracker outputs; equality assertions only, no value is printed or written.
  1. real t/s tracks (gtc/out/track) + b = GT instance on every frame (toy b track files through track_source on SEEDS_GTCB)
     -> b == e on every item (cells and gaps), b precision/recall == 1, and every t/s output equals RELIFT_GTC.json;
  2. b = served masks (injected)                                    -> b == a;
  3. b = the real t tracks (injected)                               -> b == t;
  4. the b reading field equals reading_b on its own b-a statistic, and the b section has every registered field;
  5. an incomplete b track directory is refused.
Each compute() also asserts its a and e equal a fresh in-process relift.run and relift.stats over the fresh rows.
p1cpu interpreter. Writes toy b track files (GT masks only) under gtcb/work/toy_tracks_b."""
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


# toy b track files: every b unit carries its GT instance on all 32 anchors
seeds_b = G.read_json(G.SEEDS_B)
toy = G.ROOT/'work/toy_tracks_b'
refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
items, objects, _ = G.eligible(R, refs)
gtp = {i['capture']: i['gt_path'] for i in items}
spec = dict(seeds_sha256=G.sha256_file(G.SEEDS_B), toy=True)
for c in seeds_b['captures']:
    with np.load(gtp[c['capture']]) as z:
        inst = z['inst'].copy()
    recs = [dict(unit=u['unit'], masks=G.pack(inst == u['instance_id'])) for u in c['units'] if u['arm'] == 'b']
    G.write_json(toy/'b'/(G.stub(c['capture'])+'.json.gz'), dict(contract=spec, anchors=32, skipped_units=[], units=recs), gz=True)
src_ts = RT.track_source(G.GTC_OUT/'track')
src_b = RT.track_source(toy, G.SEEDS_B, G.B_ARMS)

# 1.
res = RT.compute(R, fresh, src_ts, src_b)
assert res['reproduction']['a_e_rows_equal'] and res['reproduction']['items'] == 117
assert equal(res['rows'], 'b', 'e'), 'b = GT via track files differs from e'
assert all(v['precision'] == 1. and v['recall'] == 1. for v in res['b']['precision_recall'].values())
print('PASS b(GT track files) == e on 117 items; b precision/recall == 1', flush=True)
assert RT.assert_ts_equal(res, src_ts.contract)
print('PASS t and s outputs (rows, statistics, precision/recall, reading, reproduction) equal RELIFT_GTC.json', flush=True)

# 4. b section fields and reading (no value shown)
bs = {x['dataset']: x for x in res['b']['statistics']}
assert set(bs) == {'all', 'ARKit', 'ScanNet/ScanNet++'} and bs['all']['n'] == 117 == bs['ARKit']['n']+bs['ScanNet/ScanNet++']['n']
assert all(set(x['versus']) == {'b-a', 'b-t', 'e-a'} and set(x['share_of_e_minus_a']) >= {'mean', 'ci95'} and 'cell_b' in x for x in bs.values())
assert all(x['versus']['e-a'] == y['versus_a']['e-a'] for x, y in zip(res['b']['statistics'], res['statistics']))
assert res['b']['reading'] == RT.reading_b(bs['all']['versus']['b-a']) and res['b']['reading']['verdict'] in RT.B_VERDICTS
assert set(res['b']['precision_recall']) == {'all', 'ARKit', 'ScanNet/ScanNet++'}
assert set(res['b']['seed_facts']) == {'all', 'ARKit', 'ScanNet/ScanNet++'} and 'median_area_240' in res['b']['seed_facts']['all']
print('PASS b section: per-dataset statistics, b-a/b-t/e-a, share, precision/recall, seed facts, reading field', flush=True)

# 2. served masks injected for b -> b == a
res2 = RT.compute(R, fresh, src_ts, lambda arm, ctx: ctx['served'])
assert equal(res2['rows'], 'b', 'a'), 'served-mask b differs from a'
print('PASS b(served) == a on 117 items', flush=True)

# 3. real t tracks injected for b -> b == t
res3 = RT.compute(R, fresh, src_ts, lambda arm, ctx: src_ts('t', ctx))
assert equal(res3['rows'], 'b', 't'), 'b fed the t tracks differs from t'
print('PASS b(t tracks) == t on 117 items', flush=True)

# 5. an incomplete b track directory is refused
bad = G.ROOT/'work/toy_tracks_b_missing'
if not bad.exists():
    shutil.copytree(toy, bad)
    victim = next((bad/'b').glob('*.json.gz')); victim.rename(victim.with_name(victim.name+'.aside'))
try:
    RT.track_source(bad, G.SEEDS_B, G.B_ARMS); raise AssertionError('incomplete b track directory accepted')
except FileNotFoundError:
    print('PASS incomplete b track directory refused', flush=True)
print(json.dumps(dict(status='PASS', seconds=round(time.monotonic()-t0))))
