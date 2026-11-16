"""Emit exact ttower keys for V-C and scaled G3T depth, with receipts per capture."""
import argparse
import json
from pathlib import Path
import numpy as np
from devs1_anchors import save,sha
from rk.geom import convert,references

EXTRA={'pose_source','depth_source','fov_source'}

def heads(g3t,own,out,group):
    g3t,own,out=map(Path,(g3t,own,out));refs=references();done=skipped=0
    for p in sorted(g3t.glob('*__*.npz')):
        v=own/p.name
        if not v.is_file():raise ValueError('Missing own heads: '+str(v))
        inputs=dict(g3t=sha(p),own=sha(v),rule=refs[2],group=group,implementation=sha(__file__),converter=sha(Path(__file__).parent/'rk/geom.py'))
        receipt=out/'receipts'/group/(p.stem+'.json')
        vc=out/('heads_'+group+'_vcd')/p.name;gd=out/('heads_'+group)/p.name
        if receipt.exists():
            previous=json.loads(receipt.read_text())
            if previous['inputs']!=inputs:raise ValueError('Resume inputs changed: '+p.stem)
            if vc.exists() and gd.exists() and previous['outputs']=={str(x.relative_to(out)):sha(x) for x in [vc,gd]}:
                skipped+=1;continue
            raise ValueError('Resume output missing or corrupt: '+p.stem)
        record=convert(p,v,vc.parent,'g3t','own',refs)
        with np.load(vc,allow_pickle=False) as z:values={k:z[k] for k in z.files if k not in EXTRA}
        with np.load(p,allow_pickle=False) as g:
            if len(g['frame_indices'])!=int(group[3:]):raise ValueError('Dense group mismatch')
            depth=(g['depth_grid'].astype(float)*float(values['scale'])).astype(np.float32)
        for dest,d in [(vc,values['depth_grid']),(gd,depth)]:
            dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix('.part')
            with tmp.open('wb') as f:np.savez(f,**dict(values,depth_grid=d))
            tmp.replace(dest)
        save(receipt,dict(inputs=inputs,outputs={str(x.relative_to(out)):sha(x) for x in [vc,gd]},scale=record['s'],scale_rule_outside_fitted_format=group=='g3s32',fov='g3t',gravity='own',depths=['own','g3t_x_s']))
        done+=1
    if not done+skipped:raise ValueError('No tower captures')
    return dict(completed=done,resumed=skipped)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['g3t','own','out']:p.add_argument('--'+n,required=True)
    p.add_argument('--group',choices=['g3s32','g3s64'],required=True);a=p.parse_args();print(json.dumps(heads(**vars(a))))
