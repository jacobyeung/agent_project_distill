"""Compute ScaleHead fixed-math features for every capture with an E3 per-capture JSON."""
import glob, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, torch
torch.set_num_threads(8)
from scale_head import ScaleHead, prepare_inputs, FEATURE_NAMES
E3 = '/scratch/jjyeung/orch_n30/b04_e2ehook/work/e3/work/harness'
TOWERS = '/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2'
dg = lambda v: hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()
rows = []
for sub in ('out_tr', 'out_ho'):
    for p in sorted(glob.glob(f'{E3}/{sub}/*__*.json')):
        d = json.load(open(p))['diagnostics']
        tower = f"{TOWERS}/{dg(d['capture'])[:16]}/tower.npz"
        x = prepare_inputs(tower)
        f, aux = ScaleHead.features(**x)
        rows.append(dict(capture=d['capture'], room=d['room'], split=d['split'], dataset=d['dataset'],
                         SO=d['SO'], scales=d.get('scales'), refused=d.get('refused'),
                         e3_h_raw=d.get('h_raw'), e3_span=d.get('span'), h_raw=aux[0]['h_raw'], span=aux[0]['span'],
                         tower=tower, features=f[0].tolist()))
json.dump(dict(feature_names=FEATURE_NAMES, rows=rows), open(sys.argv[1], 'w'))
print(len(rows))
