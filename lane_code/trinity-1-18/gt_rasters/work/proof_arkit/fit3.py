exec(open('fit2.py').read().split("for off in")[0])
T,AA,TT=load_traj('src/42899922_frames/lowres_wide.traj')
def pose64(f):
    i=np.argmin(np.abs(T-ts(ds[f]))); return c2w_of(AA[i],TT[i],'scipy')
def src_world2(f, off, p64):
    d=np.array(Image.open(ds[f])).astype(np.float64)/1000.0
    w,h,fx,fy,cx,cy=np.loadtxt(pc[f])
    v,u=np.mgrid[0:192,0:256].astype(np.float64)
    x=(u+off-cx)/fx*d; y=(v+off-cy)/fy*d
    Cm=pose64(f) if p64 else C[f].astype(np.float64)
    P=np.stack([x,y,d,np.ones_like(d)],-1).reshape(-1,4)@Cm.T
    return P[:,:3], d.reshape(-1)>0
from collections import Counter
for p64 in [False,True]:
  for mf in [0.035, 0.04, 0.05]:
    cnt=Counter(); ex=[]; tot=0
    for f in frames:
        P,valid=src_world2(f,0.5,p64); a=assign(P,valid,0.03,mf)
        A2=a.reshape(192,256)[np.ix_(yi,xi)]; tot+=(A2!=I[f]).sum()
        # residual at source res: compare via upsampled mapping back
        bad=np.argwhere(A2!=I[f])
        for y,x in bad[:200]:
            p=yi[y]*256+xi[x]; k=I[f][y,x] if I[f][y,x]>=0 else a[p]
            loc=(P[p]-cen[k])@A[k].T
            ex.append((f,int(a[p]),int(I[f][y,x]),round(float((np.abs(loc)-L[k]/2).max()),4),round(float(P[p,2]-floor),4)))
    print('p64',p64,'mf',mf,'mismatch px',tot)
    for e in ex[:12]: print('  ',e)
