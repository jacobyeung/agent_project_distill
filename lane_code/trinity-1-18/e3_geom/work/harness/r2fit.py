"""R2 multipliers from train shard rows only (median gt/R0 per tower condition)."""
import json, glob, collections, numpy as np
fits = json.load(open('out/FITS.json'))
g = collections.defaultdict(list)
for p in glob.glob('out_tr/*.json'):
    for r in json.load(open(p))['items']:
        assert r['split'] == 'train'
        if r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+') and r['pred']:
            g[r['arm'][:-3]].append(r['gt'] / r['pred'])
fits['R2'] = {k: dict(k=float(np.median(v)), n_used=len(v), split='train') for k, v in g.items()}
json.dump(fits, open('out_tr/FITS_R2_from_shards.json', 'w'), indent=1)
print({k: (round(v['k'], 3), v['n_used']) for k, v in fits['R2'].items()})
