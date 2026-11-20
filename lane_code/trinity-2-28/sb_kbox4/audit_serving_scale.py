"""Compare the convert and serving scale rules on every available training capture."""
import json
import time
import numpy as np
import torch
from debug_geometry import ROOT, K1, OUT, PINS, read, write, npz, digest, median_ratio, tower_scale_rule, sources


def main():
    torch.set_num_threads(8)
    start=time.monotonic()
    caps=json.loads(read(ROOT/'train_manifest.json'))['captures']
    rows=[]
    for c in caps:
        assert c['k1_split']=='train'
        key=digest(c['canonical'])[:16]
        paths=[K1/'run_tower_sam_2'/key/'tower.npz', K1/'own_170235/native/probe'/key/'own.npz',K1/'run_convert_2'/key/'geometry.npz']
        missing=[str(p) for p in paths if not p.is_file()]
        if missing:
            rows.append(dict(capture=c['canonical'],status='MISSING',paths=missing));continue
        tower, own, gd=[npz(p) for p in paths]
        serving=median_ratio(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
        gated,_,_=tower_scale_rule.estimate(tower['depth_grid'],tower['depth_conf_grid'],own['depth'])
        rows.append(dict(capture=c['canonical'],status='OK',gd_scale=float(gd['scale']),gated_scale=gated,serving_scale=serving,
            reader_float32_scale=float(torch.tensor(float(np.log(serving))).exp()),
            relative_change=serving/float(gd['scale'])-1,gd_matches_gated=bool(np.isclose(gated,float(gd['scale']),rtol=0,atol=1e-12))))
    sources();read(ROOT/'audit_serving_scale.py')
    valid=[r for r in rows if r['status']=='OK']
    changed=[r for r in valid if abs(r['relative_change'])>1e-6]
    summary=dict(captures=len(rows),available=len(valid),missing=len(rows)-len(valid),
        convert_equals_gated=sum(r['gd_matches_gated'] for r in valid),
        serving_scale_differs_over_1ppm=len(changed),max_absolute_relative_change=max(abs(r['relative_change']) for r in valid))
    write(OUT/'SERVING_SCALE_AUDIT.json',dict(summary=summary,rows=rows,seconds=time.monotonic()-start))
    print(json.dumps(summary));print(json.dumps(sorted(changed,key=lambda r:-abs(r['relative_change']))[:5],indent=2))


if __name__=='__main__':main()
