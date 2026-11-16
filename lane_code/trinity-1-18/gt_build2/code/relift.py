"""Recompute inst of an original arkit_gt npz from its own depth/K/c2w/obb arrays under a rule, compare."""
import ctypes; ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import numpy as np, sys, glob, os, json
SH, SW = 192, 256
def relift(z, order='vol', margin=0.03, floor_pct=2.0, floor_off=0.05, mm='div', floor='global', band=False):
    depth=z['depth']; Kf=z['K_frames']; c2w=z['c2w']; cen=z['obb_centroid']; L=z['obb_lengths']; A=z['obb_axes'].reshape(-1,3,3)
    _,H,W=depth.shape; SHr,SWr=(SW,SH) if H==320 else (SH,SW)
    yi=np.floor(np.arange(H)*SHr/H).astype(int); xi=np.floor(np.arange(W)*SWr/W).astype(int)
    vol=np.prod(L,1)
    if order=='vol': ordk=np.argsort(vol)[::-1]
    elif order=='volm': ordk=np.argsort(np.prod(L+2*margin,1))[::-1]
    elif order=='vol_stable': ordk=np.argsort(-vol, kind='stable')
    elif order=='index': ordk=np.arange(len(L))
    elif order=='rindex': ordk=np.arange(len(L))[::-1]
    pts=[]
    for f in range(32):
        if not depth[f].any(): pts.append(None); continue
        png=np.zeros((SHr,SWr)); png[np.ix_(yi,xi)]=np.round(depth[f].astype(np.float64)*1000)
        d=png/1000.0
        K=np.diag([SWr/W,SHr/H,1])@Kf[f]
        fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
        v,u=np.mgrid[0:SHr,0:SWr].astype(np.float64)
        M=c2w[f].astype(np.float64)
        P=(np.stack([(u+.5-cx)/fx*d,(v+.5-cy)/fy*d,d,np.ones_like(d)],-1).reshape(-1,4)@M.T)[:,:3]
        pts.append((P,d.reshape(-1)>0))
    cut=np.percentile(np.concatenate([P[ok,2] for x in pts if x is not None for P,ok in [x]]),floor_pct)+floor_off
    inst=np.full((32,H,W),-1,np.int32); slack=[]
    for f,x in enumerate(pts):
        if x is None: continue
        P,ok=x; out=np.full(len(P),-1,np.int32)
        ex=(cen[:,2]-L[:,2]/2)>=cut
        below=P[:,2]<cut
        if band: below&=P[:,2]>=cut-2*floor_off
        inex=np.zeros(len(P),bool)
        for k in ordk:
            m=(np.abs((P-cen[k])@A[k].T)<=L[k]/2+margin).all(1)
            if ex[k]: inex|=m
            if floor=='exemptA' and not ex[k]: m&=~below
            out[m]=k
        if floor=='global': out[below]=-1
        elif floor=='exemptC': out[below&~inex]=-1
        elif floor=='exemptB': out[below&(out>=0)&~ex[np.maximum(out,0)]]=-1
        out[~ok]=-1
        inst[f]=out.reshape(SHr,SWr)[np.ix_(yi,xi)]
    return inst
if __name__=='__main__':
    order,floor,band=sys.argv[1].split(','); band=band=='band'; files=sys.argv[2:]
    for fn in files:
        z=np.load(fn); I=relift(z,order=order,floor=floor,band=band); O=z['inst']
        dm=I!=O
        pairs={}
        for a,b in zip(O[dm],I[dm]): pairs[(int(a),int(b))]=pairs.get((int(a),int(b)),0)+1
        print(os.path.basename(fn), len(z['ids']), int(dm.sum()), sorted(pairs.items(),key=lambda t:-t[1])[:6], flush=True)
