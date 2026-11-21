#!/usr/bin/env python3
"""Upper wall band (top 0.3-0.9 m below ceiling percentile), 5 cm occupancy; best rotation+translation; score = mean two-sided inlier fraction at 0.10 m."""
import glob, json
import numpy as np
from scipy.spatial import cKDTree
R='/scratch/jjyeung/orch_n30/lever5/r0chk'; rng=np.random.default_rng(1); CH=4368;N=32
def load(scene,strided_ok=False):
    f=(glob.glob(f'{R}/stage_c/samples/*_{scene}_full.npy')+glob.glob(f'{R}/stage_b/samples/dev_{scene}_full.npy')+(glob.glob(f'{R}/stage_b/samples/*_{scene}_strided.npy') if strided_ok else []))[0]
    return np.load(f)
def band(x,n=20000):
    z=x[:,2]; hi=np.percentile(z,99); x=x[(z>hi-0.9)&(z<hi-0.3)]
    k=np.unique(np.floor(x[:,:2]/0.05).astype(np.int64),axis=0)*0.05+0.025
    if len(k)>n: k=k[rng.choice(len(k),n,replace=False)]
    return k-k.mean(0)
def rot(t): c,s=np.cos(t),np.sin(t); return np.array([[c,-s],[s,c]])
def score(a,b):
    ta=cKDTree(a); best=(-1,None)
    for deg in range(0,360,3):
        q=b@rot(np.radians(deg)).T; sh=np.zeros(2)
        for _ in range(8):
            d,i=ta.query(q+sh); m=d<np.percentile(d,70); sh+=np.mean(a[i[m]]-(q[m]+sh),0)
        d1,_=ta.query(q+sh); d2,_=cKDTree(q+sh).query(a); s=0.5*((d1<0.10).mean()+(d2<0.10).mean())
        if s>best[0]: best=(s,deg)
    return best
pairs=json.load(open(f'{R}/stage_b/INSPECT_PAIRS.json'))
d0=load(pairs[0][1]); a=band(d0); b=band(d0)@rot(np.radians(37)).T+np.array([0.4,-0.2]); b=b[rng.choice(len(b),len(b)//2,replace=False)]
print('positive control: inlier %.3f'%score(a,b)[0])
# negative baseline: each candidate dev scene vs 3 random non-candidate full dev scenes (full blocks available for all 100 dev)
devs=sorted({p[1] for p in pairs}); others=[f.split('dev_')[1][:-9] for f in glob.glob(f'{R}/stage_b/samples/dev_*_full.npy')]
others=[o for o in others if o not in devs]; neg=[]
for dv in devs:
    for o in rng.choice(others,3,replace=False): neg.append(score(band(load(dv)),band(load(o)))[0])
print('negative baseline (dev vs unrelated dev): max %.3f median %.3f n %d'%(max(neg),np.median(neg),len(neg)))
out=[]
for k,dv,tr,g in pairs:
    s=score(band(load(dv)),band(load(tr))); out.append(dict(kind=k,dev=dv,other=tr,inlier=round(float(s[0]),3),deg=s[1])); print(k,dv,tr,'inlier %.3f at %d deg'%s,flush=True)
json.dump(dict(negative=neg,pairs=out),open(f'{R}/stage_c/ALIGN2.json','w'),indent=1)
