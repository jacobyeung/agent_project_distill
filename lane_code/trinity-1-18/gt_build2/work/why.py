import numpy as np, sys
sys.argv=[sys.argv[0]]+sys.argv[1:]
from relift import *
for fn in sys.argv[1:]:
    z=np.load(fn); depth=z['depth']; Kf=z['K_frames']; c2w=z['c2w']; cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    I=relift(z); O=z['inst']; _,H,W=depth.shape
    print(fn.split('/')[-1], 'labels', list(z['labels']))
    # recompute per-pixel z at output res using source mapping
    SHr,SWr=(SW,SH) if H==320 else (SH,SW)
    allz=[]
    zs=np.zeros(depth.shape)
    for f in range(32):
        if not depth[f].any(): continue
        yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
        K=np.diag([SWr/W,SHr/H,1])@Kf[f]; fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
        v,u=np.meshgrid(yi,xi,indexing='ij'); d=np.round(depth[f].astype(np.float64)*1000)/1000
        M=c2w[f].astype(np.float64)
        P=np.stack([(u+.5-cx)/fx*d,(v+.5-cy)/fy*d,d,np.ones_like(d)],-1)@M.T
        zs[f]=P[...,2]
        png=np.zeros((SHr,SWr)); png[np.ix_(yi,xi)]=np.round(depth[f]*1000); dd=png/1000.
        vv,uu=np.mgrid[0:SHr,0:SWr]
        Q=np.stack([(uu+.5-cx)/fx*dd,(vv+.5-cy)/fy*dd,dd,np.ones_like(dd)],-1).reshape(-1,4)@M.T
        allz.append(Q[dd.reshape(-1)>0,2])
    cut=np.percentile(np.concatenate(allz),2)+0.05
    dm=(I!=O)
    ks=np.unique(O[dm])
    for k in ks:
        m=dm&(O==k)
        print(' box',k,z['labels'][k],'n',m.sum(),'z range %.4f %.4f'%(zs[m].min(),zs[m].max()),'cut %.4f'%cut,'box zc %.3f L'%cen[k][2],L[k].round(3), 'frames',np.unique(np.nonzero(m)[0]))
        # pixels of box k that agree
        ag=(~dm)&(O==k); print('   agreeing pixels of k',ag.sum(), 'their zmin %.4f'%(zs[ag].min() if ag.any() else np.nan))
