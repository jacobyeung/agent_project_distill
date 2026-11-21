#!/usr/bin/env python3
"""Settle candidate pairs: best rigid 2D alignment (rotation about z + translation) of wall-band point sets; report median NN distance."""
import glob, json, sys
import numpy as np
from scipy.spatial import cKDTree
R='/scratch/jjyeung/orch_n30/lever5/r0chk'
rng=np.random.default_rng(0)
def load(scene):
    f=(glob.glob(f'{R}/stage_c/samples/*_{scene}_full.npy')+glob.glob(f'{R}/stage_b/samples/dev_{scene}_full.npy'))[0]
    return np.load(f)
def band(x,n=60000):
    z=x[:,2]; lo,hi=np.percentile(z,[1,99]); x=x[(z>lo+0.3)&(z<hi-0.3)]
    xy=x[:,:2]; k=np.unique(np.floor(xy/0.05).astype(np.int64),axis=0)*0.05+0.025   # 5 cm occupancy
    if len(k)>n: k=k[rng.choice(len(k),n,replace=False)]
    return k-k.mean(0)
def rot(t): c,s=np.cos(t),np.sin(t); return np.array([[c,-s],[s,c]])
def score(a,b):
    ta,tb=cKDTree(a),cKDTree(b); best=(1e9,None)
    for deg in range(0,360,3):
        q=b@rot(np.radians(deg)).T; sh=np.zeros(2)
        for _ in range(8):  # translation ICP
            d,i=ta.query(q+sh); m=d<np.percentile(d,80); sh+=np.mean(a[i[m]]-(q[m]+sh),0)
        d1,_=ta.query(q+sh); d2,_=cKDTree(q+sh).query(a); s=0.5*(np.median(d1)+np.median(d2))
        if s<best[0]: best=(s,deg)
    return best
out=[]
x=load(sys.argv[1]) if len(sys.argv)>1 else None
pairs=json.load(open(f'{R}/stage_b/INSPECT_PAIRS.json'))
# positive control: dev scene vs itself rotated 37 deg, shifted, independently subsampled
d0=load(pairs[0][1]); a=band(d0); b=band(d0)@rot(np.radians(37)).T+np.array([0.4,-0.2]); b=b[rng.choice(len(b),len(b)//2,replace=False)]
pc=score(a,b); print('positive control (same scene, rotated/resampled): median NN %.3f m at %d deg'%pc)
for k,dv,tr,g in pairs:
    s=score(band(load(dv)),band(load(tr))); out.append(dict(kind=k,dev=dv,other=tr,group=g,median_nn_m=round(float(s[0]),4),deg=s[1]))
    print(k,dv,tr,'median NN %.3f m at %d deg'%s, flush=True)
json.dump(dict(positive_control_m=float(pc[0]),pairs=out),open(f'{R}/stage_c/ALIGN.json','w'),indent=1)
