import numpy as np, sys
from relift import SH, SW
for fn in sys.argv[1:]:
    z=np.load(fn); depth=z['depth']; Kf=z['K_frames']; c2w=z['c2w']; cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3); O=z['inst']
    _,H,W=depth.shape; SHr,SWr=(SW,SH) if H==320 else (SH,SW)
    yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
    allz=[]; per=[]
    for f in range(32):
        if not depth[f].any(): per.append(None); continue
        K=np.diag([SWr/W,SHr/H,1])@Kf[f]; fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
        png=np.zeros((SHr,SWr)); png[np.ix_(yi,xi)]=np.round(depth[f]*1000); dd=png/1000.
        vv,uu=np.mgrid[0:SHr,0:SWr]; M=c2w[f].astype(np.float64)
        Q=(np.stack([(uu+.5-cx)/fx*dd,(vv+.5-cy)/fy*dd,dd,np.ones_like(dd)],-1).reshape(-1,4)@M.T)[:,:3]
        allz.append(Q[dd.reshape(-1)>0,2]); per.append((Q,dd.reshape(-1)>0))
    cut=np.percentile(np.concatenate(allz),2)+0.05
    print(fn.split('/')[-1],'cut',cut)
    for f,x in enumerate(per):
        if x is None: print(f,'missing'); continue
        Q,ok=x; inany=np.zeros(len(Q),bool)
        for k in range(len(L)): inany|=(np.abs((Q-cen[k])@A[k].T)<=L[k]/2+0.03).all(1)
        o=O[f]; src=np.full((SHr,SWr),-9); src[np.ix_(yi,xi)]=o; src=src.reshape(-1)
        below=inany&ok&(Q[:,2]<cut)
        kept=below&(src>=0); 
        print(f,'below&inbox',below.sum(),'orig kept',kept.sum(), 'zmin kept %.4f'%(Q[kept,2].min() if kept.any() else 0), 'frame zmin %.4f'%Q[ok,2].min(), 'n zero depth', (~ok).sum())
        if kept.any():
            rem=below&(src<0)
            print('   kept z [%.4f, %.4f]  removed z [%.4f, %.4f]'%(Q[kept,2].min(),Q[kept,2].max(),Q[rem,2].min() if rem.any() else 0,Q[rem,2].max() if rem.any() else 0), 'kept boxes', np.unique(src[kept]))
            # pixel positions
            vv2,uu2=np.unravel_index(np.nonzero(kept)[0],(SHr,SWr)); print('   kept rows',vv2.min(),vv2.max(),'cols',uu2.min(),uu2.max())
            vv3,uu3=np.unravel_index(np.nonzero(rem)[0],(SHr,SWr)); 
            if rem.any(): print('   rem rows',vv3.min(),vv3.max(),'cols',uu3.min(),uu3.max())
            for nm,m in (('kept',kept),('rem',rem)):
                if not m.any(): continue
                for k in [3] if 'bathtub' in list(z['labels']) else np.unique(src[kept]):
                    loc=(Q[m]-cen[k])@A[k].T; r=np.abs(loc)/(L[k]/2)
                    ink=(np.abs(loc)<=L[k]/2+0.03).all(1)
                    print('   ',nm,'box',k,'in k',ink.sum(),'/',m.sum(),'max|loc|/half per axis (in k)', r[ink].max(0).round(3) if ink.any() else None, 'min', r[ink].min(0).round(3) if ink.any() else None)
