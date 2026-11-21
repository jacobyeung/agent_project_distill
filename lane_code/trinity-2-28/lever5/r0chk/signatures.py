#!/usr/bin/env python3
"""R0 mesh scan option (ii): signatures and candidate pairs under stage_b/RULE.md."""
import glob, json, os, sys
import numpy as np
D='/scratch/jjyeung/orch_n30/lever5/r0chk/stage_b'; S=D+'/samples'
CH=4368; N=32
def strided_from_full(xyz):
    nv=len(xyz)
    if nv<=CH*N: return xyz
    starts=[int(round(i*(nv-CH)/(N-1))) for i in range(N)]
    return np.concatenate([xyz[s:s+CH] for s in starts])
def sig(xyz):
    z=xyz[:,2]; H=np.percentile(z,99)-np.percentile(z,1)
    xy=xyz[:,:2]-xyz[:,:2].mean(0)
    w,v=np.linalg.eigh(np.cov(xy.T)); p=xy@v
    e=sorted([np.percentile(p[:,i],99)-np.percentile(p[:,i],1) for i in (0,1)],reverse=True)
    cells=np.unique(np.floor(xyz[:,:2]/0.10).astype(np.int64),axis=0); A=len(cells)*0.01
    r=np.hypot(xy[:,0],xy[:,1]); hist=np.bincount(np.minimum((r/0.75).astype(int),7),minlength=8)/len(r)
    return dict(H=float(H),E1=float(e[0]),E2=float(e[1]),A=float(A),R=hist.tolist(),n=int(len(xyz)))
sigs={}
for f in sorted(glob.glob(S+'/*.json')):
    m=json.load(open(f)); xyz=np.load(f[:-5]+'.npy')
    if m['mode']=='full': sigs[m['scene']]=dict(group=m['group'],strided=sig(strided_from_full(xyz)),full=sig(xyz))
    else: sigs[m['scene']]=dict(group=m['group'],strided=sig(xyz))
json.dump(sigs,open(D+'/SIGNATURES.json','w'))
dev=[k for k,v in sigs.items() if v['group']=='dev']; oth=[k for k,v in sigs.items() if v['group']!='dev']
def close(a,b,t,l1):
    rel=lambda x,y: abs(x-y)<=t*max(abs(x),abs(y))
    return all(rel(a[k],b[k]) for k in ('H','E1','E2','A')) and float(np.abs(np.array(a['R'])-np.array(b['R'])).sum())<=l1
out={}
for t,l1 in ((0.05,0.10),(0.03,0.07)):
    pairs=[(d,o,sigs[o]['group']) for d in dev for o in oth if close(sigs[d]['strided'],sigs[o]['strided'],t,l1)]
    out['%g_%g'%(t,l1)]=pairs
    print('tol',t,'L1',l1,'pairs',len(pairs),'dev scenes',len({p[0] for p in pairs}),'others',len({p[1] for p in pairs}))
    if len(pairs)<=30: break
# sanity: dev full vs dev strided signature agreement
dz=[abs(sigs[d]['full']['A']-sigs[d]['strided']['A'])/sigs[d]['full']['A'] for d in dev]
print('dev strided vs full footprint rel diff median %.3f max %.3f'%(np.median(dz),max(dz)))
print('n dev',len(dev),'n others',len(oth))
json.dump(out,open(D+'/CANDIDATES.json','w'),indent=1)
