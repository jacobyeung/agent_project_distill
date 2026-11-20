"""The exact E3 sensor fused-box rule over the fixed served-reader points."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json,time
import numpy as np
import k1x as K

CONTEXT=None


def fused_objects(objects):
    from trace_format.box_v313 import fit_gbox_full
    result={}
    for n,obj in objects.items():
        new=dict(obj,boxes={})
        if obj['seen']:
            try:
                parts=[np.asarray(obj['points'].get(str(f),[]),float).reshape(-1,3) for f in obj['frames']]
                points=np.concatenate(parts)
                if len(points)<4:raise ValueError('box_needs_four_points')
                if len(points)>20000:
                    points=points[np.random.default_rng(0).choice(len(points),20000,replace=False)]
                new['boxes']['e3_fused']=fit_gbox_full(points)
            except ValueError:
                new['oracle_error']='e3_fused_box_unavailable'
        result[n]=new
    return result


def capture(c):
    args,D,M,head=CONTEXT
    start=time.monotonic();I=K.Inputs()
    geo,t,own,gt,cache,meta=K.load_capture(c,args,I,D)
    names=sorted({n for r in c['rows'] for n in r['operands']})
    gm=K.gt_masks(c,names,gt)
    dm,choices=K.selected_masks(c,names,geo,cache,gt,head,D)
    result={r['id']:{} for r in c['rows']}
    for m,ms in [('GT',gm),('deployed',dm)]:
        objects=K.lifted(ms,geo,D);fused=fused_objects(objects)
        for r in c['rows']:
            result[r['id']][m+'/e3_fused']=K.predict(r,geo,fused,D,'e3_fused')
            result[r['id']][m+'/base']=K.predict(r,geo,objects,D)
    receipt=dict(capture=c['canonical'],box=result,choices=choices,input_sha256=I.hashes,seconds=time.monotonic()-start)
    K.write(K.ROOT/'out_box/e3_fused'/(c['canonical'].replace('/','__')+'.json'),receipt)
    print(f"DONE {c['canonical']} {receipt['seconds']:.1f}s",flush=True)
    return c['canonical']


def main():
    global CONTEXT
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing
    args=K.options(['run','--out',str(K.ROOT/'out_box')]);I=K.Inputs();M=K.metadata(args,I);D=K.dependencies(args)
    head,_=D.load_head(args.selector)
    for ext in ('json','safetensors'):I.read(args.selector/f'selector_head.{ext}')
    for p in (Path(__file__),K.ROOT/'k1x.py',args.tree/'trace_format/box_v313.py'):I.read(p)
    CONTEXT=args,D,M,head
    with ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('fork')) as pool:
        done=list(pool.map(capture,M.captures))
    K.write(args.out/'E3_RECEIPT.json',dict(captures=done,input_sha256=I.hashes,
        rule='E3 sensor FusedBoxProvider: fit_gbox_full over all served post-spread points; cap 20000, RNG seed 0',
        isolation='Only the box provider changes. Lift, mask choices, geometry, reader guard and distance program remain served.'))


if __name__=='__main__':main()
