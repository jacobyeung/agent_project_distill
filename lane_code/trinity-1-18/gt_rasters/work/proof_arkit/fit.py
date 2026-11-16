import sys; sys.path.insert(0,'.')
exec(open('probe.py').read().split("def world")[0])
def world(f, off):
    d=D[f].astype(np.float64); v,u=np.mgrid[0:H,0:W].astype(np.float64)
    x=(u+off-K[0,2])/K[0,0]*d; y=(v+off-K[1,2])/K[1,1]*d
    P=np.stack([x,y,d,np.ones_like(d)],-1).reshape(-1,4)@C[f].astype(np.float64).T
    return P[:,:3]
vol=np.prod(L,1); floor=(cen[:,2]-L[:,2]/2).min()
def assign(P, valid, m, mf):
    out=np.full(len(P),-1,np.int32)
    for k in np.argsort(vol)[::-1]:
        loc=(P-cen[k])@A[k].T
        ins=(np.abs(loc)<=L[k]/2+m).all(1)
        out[ins]=k
    out[P[:,2]<floor+mf]=-1
    out[~valid]=-1
    return out
frames=[f for f in range(32) if (D[f]>0).any()]
for off in [0.0,0.5]:
    Ps={f:world(f,off) for f in frames}
    for m in [0.03,0.035,0.04,0.05]:
        for mf in [0.0,0.03,0.035,0.04]:
            agree=np.mean([(assign(Ps[f],D[f].reshape(-1)>0,m,mf)==I[f].reshape(-1)).mean() for f in frames])
            print(off,m,mf,'%.5f'%agree,flush=True)
