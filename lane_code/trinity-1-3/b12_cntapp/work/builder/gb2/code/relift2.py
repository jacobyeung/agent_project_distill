"""relift with arithmetic variants; rule = band floor + exempt boxes (bottom >= cut). usage: relift2.py ARITH FLOOR files"""
import ctypes; ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import numpy as np, sys, os
from multiprocessing import Pool
SH, SW = 192, 256
def lift_one(d, K, M, ar):
    fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
    SHr,SWr=d.shape
    v,u=np.mgrid[0:SHr,0:SWr].astype(np.float64)
    if 'd32' in ar: d=d.astype(np.float32).astype(np.float64)
    if 'kinv' in ar:
        Ki=np.linalg.inv(K); pix=np.stack([u+.5,v+.5,np.ones_like(u)],-1)
        cam=(pix@Ki.T)*d[...,None]; X,Y=cam[...,0],cam[...,1]
    elif 'mulfirst' in ar: X=(u+.5-cx)*d/fx; Y=(v+.5-cy)*d/fy
    else: X=(u+.5-cx)/fx*d; Y=(v+.5-cy)/fy*d
    if 'f32' in ar:
        h=np.stack([X,Y,d,np.ones_like(d)],-1).reshape(-1,4).astype(np.float32)
        return (h@M.astype(np.float32).T)[:,:3].astype(np.float64)
    if 'rt' in ar:
        c=np.stack([X,Y,d],-1).reshape(-1,3); M=M.astype(np.float64)
        return c@M[:3,:3].T+M[:3,3]
    if 'rtein' in ar:
        pass
    return (np.stack([X,Y,d,np.ones_like(d)],-1).reshape(-1,4)@M.astype(np.float64).T)[:,:3]
def relift(z, ar='', floor='A', margin=0.03, floor_off=0.05):
    depth=z['depth']; Kf=z['K_frames']; c2w=z['c2w']; cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    if 'b32' in ar: cen,L,A=cen.astype(np.float32),L.astype(np.float32),A.astype(np.float32)
    _,H,W=depth.shape; SHr,SWr=(SW,SH) if H==320 else (SH,SW)
    yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
    ordk=np.argsort(np.prod(z['obb_lengths'],1))[::-1]
    pts=[]
    for f in range(32):
        if not depth[f].any(): pts.append(None); continue
        png=np.zeros((SHr,SWr)); png[np.ix_(yi,xi)]=np.round(depth[f].astype(np.float64)*1000)
        K=np.diag([SWr/W,SHr/H,1])@Kf[f]
        P=lift_one(png/1000.0,K,c2w[f],ar)
        pts.append((P,png.reshape(-1)>0))
    p2=np.percentile(np.concatenate([P[ok,2] for x in pts if x is not None for P,ok in [x]]),2); cut=p2+floor_off
    ex=(z['obb_centroid'][:,2]-z['obb_lengths'][:,2]/2)>=cut
    inst=np.full((32,H,W),-1,np.int32)
    for f,x in enumerate(pts):
        if x is None: continue
        P,ok=x; out=np.full(len(P),-1,np.int32)
        if 'b32' in ar: P=P.astype(np.float32)
        below=(P[:,2]<cut)&(P[:,2]>=cut-2*floor_off)
        inex=np.zeros(len(P),bool)
        for k in ordk:
            m=(np.abs((P-cen[k])@A[k].T)<=L[k]/2+margin).all(1)
            if ex[k]: inex|=m
            if floor=='A' and not ex[k]: m&=~below
            out[m]=k
        if floor=='B': out[below&(out>=0)&~ex[np.maximum(out,0)]]=-1
        elif floor=='C': out[below&~inex]=-1
        out[~ok]=-1
        inst[f]=out.reshape(SHr,SWr)[np.ix_(yi,xi)]
    return inst
def job(a):
    fn,ar,floor=a; z=np.load(fn); I=relift(z,ar,floor); O=z['inst']; dm=I!=O
    pairs={}
    for a_,b_ in zip(O[dm],I[dm]): pairs[(int(a_),int(b_))]=pairs.get((int(a_),int(b_)),0)+1
    return os.path.basename(fn), int(dm.sum()), sorted(pairs.items(),key=lambda t:-t[1])[:4]
if __name__=='__main__':
    ar,floor=sys.argv[1],sys.argv[2]; files=sys.argv[3:]
    with Pool(12) as p:
        res=p.map(job,[(f,ar,floor) for f in files])
    bad=[r for r in res if r[1]]
    print(ar,floor,'exact',len(res)-len(bad),'of',len(res),bad)
