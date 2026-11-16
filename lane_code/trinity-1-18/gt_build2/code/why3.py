import numpy as np, sys
from relift import SH, SW
def lift(z):
    depth=z['depth']; Kf=z['K_frames']; c2w=z['c2w']
    _,H,W=depth.shape; SHr,SWr=(SW,SH) if H==320 else (SH,SW)
    yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
    per=[]
    for f in range(32):
        if not depth[f].any(): per.append(None); continue
        K=np.diag([SWr/W,SHr/H,1])@Kf[f]; fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
        png=np.zeros((SHr,SWr)); png[np.ix_(yi,xi)]=np.round(depth[f]*1000); dd=png/1000.
        vv,uu=np.mgrid[0:SHr,0:SWr]; M=c2w[f].astype(np.float64)
        Q=(np.stack([(uu+.5-cx)/fx*dd,(vv+.5-cy)/fy*dd,dd,np.ones_like(dd)],-1).reshape(-1,4)@M.T)[:,:3]
        o=z['inst'][f]; src=np.full((SHr,SWr),-9); src[np.ix_(yi,xi)]=o
        per.append((Q,dd.reshape(-1)>0,src.reshape(-1)))
    return per,(SHr,SWr)
if __name__=='__main__':
    fn=sys.argv[1]; k=int(sys.argv[2]); z=np.load(fn); per,_=lift(z)
    cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    cut=np.percentile(np.concatenate([Q[ok,2] for x in per if x for Q,ok,_ in [x]]),2)+0.05
    for f,x in enumerate(per):
        if x is None: continue
        Q,ok,src=x; ink=(np.abs((Q-cen[k])@A[k].T)<=L[k]/2+0.03).all(1)&ok
        b=ink&(Q[:,2]<cut)
        if ink.any(): print(f,'in k',ink.sum(),'below cut',b.sum(),'orig=k among below',(src[b]==k).sum(),'orig=k total',(src==k).sum(), 'orig other among below',np.unique(src[b]))
