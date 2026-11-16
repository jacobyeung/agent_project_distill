"""Early train read: evaluate held-out captures with the train-only FITS.json (shard k of n)."""
import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/e3_geom/work/harness')
import importlib.util as iu
sp = iu.spec_from_file_location('e3h', '/scratch/jjyeung/orch_n30/e3_geom/work/harness/harness.py'); H = iu.module_from_spec(sp); sp.loader.exec_module(H)
k, n = int(sys.argv[1]), int(sys.argv[2])
fits = json.load(open(H.OUT / 'FITS.json'))
cs, cache, inv = H.inventory()
ho = [c for c in cs if c['k1_split'] == 'train'][k::n]
dest = H.OUT.parent / 'out_tr'; dest.mkdir(exist_ok=True)
for c in ho:
    gt, tower, hw = H.load_capture(c, cache[H.digest(c)], True)
    f = H.features(c, tower, gt, hw, 'specified')
    rows = H.evaluate_capture(c, gt, tower, hw, f, fits, None, False)
    H.dump(dest / (c['canonical'].replace('/', '__') + '.json'), dict(diagnostics=f, items=rows))
    print(c['canonical'], flush=True)
print('SHARD_DONE', flush=True)
