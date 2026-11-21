"""relift_t on the real dump with toy tracker outputs; equality assertions only, no value is printed or written.
  1. t = GT instance (through toy track files and track_source)  -> t == e on every item (cells and gaps);
  2. t = served masks, s = served masks (injected)                -> t == a and s == a;
  3. s = GT instance (injected)                                   -> s == e;
  4. the seed-size subset count from compute() equals the count from SEEDS_GTC alone, and the reading field is emitted.
Each compute() also asserts its a and e equal a fresh in-process relift.run and relift.stats over the fresh rows.
p1cpu interpreter. Writes toy track files (GT masks only) under gtc/work/toy_tracks."""
import json, sys, time
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


# 1. toy track files: every t unit carries its GT instance on all 32 anchors; s units carry the GT instance too.
seeds_path = G.OUT/'SEEDS_GTC.json'; seeds = G.read_json(seeds_path)
toy = G.ROOT/'work/toy_tracks'
refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
items, objects, _ = G.eligible(R, refs)
gtp = {i['capture']: i['gt_path'] for i in items}
s_target = {}
for o in seeds['objects']:
    if o['s']['status'] == 'OK':
        s_target.setdefault((o['capture'], o['s']['unit']), set()).add(o['instance_id'])
spec = dict(seeds_sha256=G.sha256_file(seeds_path), toy=True)
for c in seeds['captures']:
    with np.load(gtp[c['capture']]) as z:
        inst = z['inst'].copy()
    for arm in G.ARMS:
        us = [u for u in c['units'] if u['arm'] == arm]
        if not us:
            continue
        recs = []
        for u in us:
            iid = u['instance_id'] if arm == 't' else sorted(s_target[(c['capture'], u['unit'])])[0]
            recs.append(dict(unit=u['unit'], masks=G.pack(inst == iid)))
        G.write_json(toy/arm/(G.stub(c['capture'])+'.json.gz'), dict(contract=spec, anchors=32, skipped_units=[], units=recs), gz=True)
src = RT.track_source(toy, seeds_path)
res = RT.compute(R, fresh, src)
assert res['reproduction']['a_e_rows_equal'] and res['reproduction']['items'] == 117
# t units keyed by (capture, instance): t must equal e everywhere except operands whose GT never shows on an anchor
# (t has no seed -> empty masks), where e lifts the same empty raster; so equality must hold on every item.
assert equal(res['rows'], 't', 'e'), 't = GT via track files differs from e'
assert all(v['precision'] == 1. and v['recall'] == 1. for k in ('t',) for v in res['precision_recall'][k].values())
print('PASS t(GT track files) == e on 117 items; t precision/recall == 1', flush=True)
# seed-size subset: compute()'s per-row membership equals the count from SEEDS_GTC alone (counts only, no value shown)
n200 = len(RT.seed200_items(seeds))
st = {x['dataset']: x for x in res['statistics']}
assert st['all']['seed200']['n'] == sum(r['seed200'] for r in res['rows']) == n200 == 58
assert st['ARKit']['seed200']['n'] + st['ScanNet/ScanNet++']['seed200']['n'] == n200
assert all(set(x['seed200']) == {'n', 'rooms', 't_minus_a'} and set(x['seed200']['t_minus_a']) >= {'mean', 'ci95'} for x in st.values())
assert res['reading']['verdict'] in RT.VERDICTS and res['reading']['reason']
assert res['reading'] == RT.reading(st['all']['versus_a']['t-a'], st['all']['seed200']['t_minus_a'], st['all']['versus_a']['s-a'])
print('PASS seed200 subset count from compute() == SEEDS_GTC count == 58; per-dataset counts sum; reading field present', flush=True)

# 2. served masks injected for t and s -> both equal a
served = lambda arm, ctx: ctx['served']
res2 = RT.compute(R, fresh, served)
assert equal(res2['rows'], 't', 'a') and equal(res2['rows'], 's', 'a'), 'served-mask tracker output differs from a'
print('PASS t(served) == a and s(served) == a on 117 items', flush=True)

# 3. GT injected for s -> s equals e
res3 = RT.compute(R, fresh, lambda arm, ctx: ctx['target'] if arm == 's' else ctx['served'])
assert equal(res3['rows'], 's', 'e') and equal(res3['rows'], 't', 'a')
print('PASS s(GT) == e and t(served) == a', flush=True)

# 4. a missing track file is refused
import shutil
bad = G.ROOT/'work/toy_tracks_missing'
if not bad.exists():
    shutil.copytree(toy, bad)
    victim = next((bad/'s').glob('*.json.gz')); victim.rename(victim.with_name(victim.name+'.aside'))
try:
    RT.track_source(bad, seeds_path); raise AssertionError('incomplete track directory accepted')
except FileNotFoundError:
    print('PASS incomplete track directory refused', flush=True)
print(json.dumps(dict(status='PASS', seconds=round(time.monotonic()-t0))))
