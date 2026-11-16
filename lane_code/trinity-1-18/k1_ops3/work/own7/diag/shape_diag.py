"""Analysis only: compare candidate mask shapes vs GT raster shapes for one capture. usage: shape_diag.py CANONICAL"""
import json,sys,collections
from pathlib import Path
import numpy as np
KIT=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a')
sys.path[:0]=[str(KIT/'work'),str(KIT/'work/refit')]
import k1_pipeline as K
import bindings as B, k1_guard as guard
import build_tables as T
K._native(); guard.install()
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'))
c=[x for x in m['captures'] if x['canonical']==sys.argv[1]][0]
dest=Path('/scratch/jjyeung/k1/run_convert_2')/B.digest(c['canonical'])[:16]
raw,geo,rec=K.cached(c,dest)
gt=K.gt_arrays(c)
print('gt instances',gt['instances'].shape,gt['instances'].dtype,'gt path',c['gt'])
with guard.capture(c):feats,g=T.extract(c,raw,geo)
shapes=collections.Counter(mask.shape for grp in feats.values() for cand in grp for mask in cand['masks'].values())
print('mask shapes',shapes)
print('tower source_hw?',json.load(open(Path('/scratch/jjyeung/k1/run_tower_sam_2')/B.digest(c['canonical'])[:16]/'PHASE_COMPLETE.json')).get('source_hw'))
truth=gt['instances']
def best(mask,t):
    ids=[i for i in np.unique(t) if i>=0]
    return max((float((mask&(t==i)).sum())/max(1,float((mask|(t==i)).sum())) for i in ids),default=0.)
if truth.shape[1:]!=next(iter(shapes)):
    for name,op in [('rot90k1',lambda a:np.rot90(a,1)),('rot90k3',lambda a:np.rot90(a,3)),('transpose',lambda a:a.T),('rot90k1_flipud',lambda a:np.flipud(np.rot90(a,1))),('stretch_nearest',lambda a:a[(np.arange(240)*320//240)][:,(np.arange(320)*240//320)])]:
        vals=[]
        for grp in feats.values():
            for cand in grp:
                for frame,mask in cand['masks'].items():
                    vals.append(best(mask.astype(bool),op(truth[frame-1])))
        vals=np.array(vals); print(name,'n',len(vals),'mean best IoU %.3f'%vals.mean(),'frac>0.5 %.3f'%(vals>.5).mean())
else:
    vals=np.array([best(mask.astype(bool),truth[f-1]) for grp in feats.values() for cand in grp for f,mask in cand['masks'].items()])
    print('identity','n',len(vals),'mean best IoU %.3f'%vals.mean(),'frac>0.5 %.3f'%(vals>.5).mean())
