"""ARKit pin alignment for K1 rasters (rows_a2/work/k1r): list lowres_depth once per capture (paced, metadata only),
and require the depth timestamp at each raster pin (frame_indices, timestamp-sorted depth index) to equal the
frame-plan RGB timestamp at that index within 1 ms. Writes work/ARK_PIN_TS_CHECK_K1.json {alias: 'ok' | reason}."""
import gzip, json, os, sys, time, numpy as np
W = '/scratch/jjyeung/orch_n30/b12_cntapp/work/'; K = '/scratch/jjyeung/orch_n30/rows_a2/work/k1r/dose_pool/out/arkit_gt/gt/'
A = '/data3/shared/datasets/arkitscenes/3dod/'
P = json.load(gzip.open('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/frame_plan.json.gz', 'rt'))['a']
can = json.load(open(sys.argv[1])); lst = W + 'inputs/ark_lists_k1/'
def ts(s): return float(s.split('_')[1].rsplit('.', 1)[0])
out = {}
for alias, c in sorted(can.items()):
    i = c.split('/')[-1]; p = P.get(alias.split('/')[1]); f = lst + i + '.depth_list.txt'
    if p is None: out[alias] = 'no plan'; continue
    pins = [int(x) for x in np.load(K + i + '.npz')['frame_indices']]
    if not os.path.exists(f):
        names = None
        for sp in ('Training', 'Validation'):
            d = f'{A}{sp}/{i}/{i}_frames/lowres_depth'
            if os.path.isdir(d): names = sorted(os.listdir(d), key=ts); break
        time.sleep(1.0)
        if names is None: out[alias] = 'no depth listing'; continue
        open(f, 'w').write('\n'.join(names) + '\n')
    names = open(f).read().split()
    need = {n[0]: n[1] for n in p['need']}
    if any(k not in need for k in pins): out[alias] = 'pin not in plan'; continue
    if max(pins) >= len(names): out[alias] = 'pin beyond depth'; continue
    d = max(abs(ts(names[k]) - need[k]) for k in pins)
    out[alias] = 'ok' if d <= 0.001 else f'ts mismatch {d:.3f}s'
json.dump(out, open(W + 'ARK_PIN_TS_CHECK_K1.json', 'w'), indent=0, sort_keys=True)
import collections; print(collections.Counter(v if not v.startswith('ts mismatch') else 'ts mismatch' for v in out.values()))
