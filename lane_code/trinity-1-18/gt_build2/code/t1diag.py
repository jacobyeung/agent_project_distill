"""ScanNet++ tie diagnostic: per pixel, hits whose depth is within TOL of the best, with face/instance ids; also near-edge hits (barycentric within EPS of 0)."""
import ctypes; ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import numpy as np, json, sys
sys.path.insert(0, '/scratch/jjyeung/orch_cd/integ_v3/work/generator')
sys.path.insert(0, '/scratch/jjyeung/orch_n30/gt_build/work/cr/builder_cr')
from derivgen.native import native_mesh
asset=sys.argv[1]; EPS=float(sys.argv[2]) if len(sys.argv)>2 else 1e-9
c=np.load(f'{asset}/official_cameras.npz'); FI,F,V=native_mesh(f'{asset}/instance_mesh.npz', raster_compatible=True)
H,W=240,320; raster=c['raster_hw']; scale=np.diag([W/float(raster[1]),H/float(raster[0]),1.])
print('faces',len(F),'FI dtype',FI.dtype, 'neg FI',int((FI<0).sum()))
tot=dict(tie_diffinst=0, tie_sameinst=0, edge_best=0, hole_cand=0)
for f in range(32):
    K=scale@c['intrinsics'][f]; c2w=np.asarray(c['camera_poses'][f],np.float64); w2c=np.linalg.inv(c2w)
    v=np.asarray(V,np.float64)@w2c[:3,:3].T+w2c[:3,3]; tri=v[F]; keep=(tri[...,2]>1e-6).all(1); idx=np.nonzero(keep)[0]; tri=tri[idx]
    fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]; off=0.5
    px=fx*tri[...,0]/tri[...,2]+cx-off; py=fy*tri[...,1]/tri[...,2]+cy-off
    x0=np.clip(np.ceil(px.min(1)),0,W).astype(np.int64); x1=np.clip(np.floor(px.max(1)),-1,W-1).astype(np.int64)
    y0=np.clip(np.ceil(py.min(1)),0,H).astype(np.int64); y1=np.clip(np.floor(py.max(1)),-1,H-1).astype(np.int64)
    nx=x1-x0+1; ny=y1-y0+1; ok=(nx>0)&(ny>0); idx,tri,x0,y0,nx,ny=idx[ok],tri[ok],x0[ok],y0[ok],nx[ok],ny[ok]
    a=nx*ny; rep=np.repeat(np.arange(len(a)),a); local=np.arange(rep.size)-np.repeat(np.cumsum(a)-a,a)
    xs=x0[rep]+local%nx[rep]; ys=y0[rep]+local//nx[rep]
    d=np.stack([(xs+off-cx)/fx,(ys+off-cy)/fy,np.ones(xs.size)],1)
    p0,p1,p2=tri[rep,0],tri[rep,1],tri[rep,2]; e1,e2=p1-p0,p2-p0; pv=np.cross(d,e2); det=(e1*pv).sum(1)
    good=np.abs(det)>1e-18; inv=np.where(good,1.0/np.where(good,det,1.0),0.0); tv=-p0
    uu=(tv*pv).sum(1)*inv; qv=np.cross(tv,e1); vv=(d*qv).sum(1)*inv; tt=(e2*qv).sum(1)*inv
    hit=good&(uu>=0)&(vv>=0)&(uu+vv<=1)&(tt>0)
    near=good&(uu>=-EPS)&(vv>=-EPS)&(uu+vv<=1+EPS)&(tt>0)&~hit
    pix=ys*W+xs; fid=idx[rep]
    best=np.full(H*W,np.inf); np.minimum.at(best,pix[hit],tt[hit])
    # ties among hits
    hb=hit&(np.abs(tt-best[pix])<=1e-12*np.maximum(1,np.abs(best[pix])))
    P_=pix[hb]; I_=FI[fid[hb]]
    o=np.argsort(P_,kind='stable'); P_,I_=P_[o],I_[o]
    u_,start,cnt=np.unique(P_,return_index=True,return_counts=True)
    multi=cnt>1
    for s,n in zip(start[multi],cnt[multi]):
        if len(set(I_[s:s+n].tolist()))>1: tot['tie_diffinst']+=1; print(' f',f,'pix',divmod(int(P_[s]),W),'tie insts',I_[s:s+n].tolist(), 'fids', fid[hb][o][s:s+n].tolist())
        else: tot['tie_sameinst']+=1
    # near-miss hits closer than best (would become best if inclusive with tolerance)
    nb=near&(tt<best[pix]+1e-9)
    for q in np.unique(pix[nb]):
        sel=nb&(pix==q)
        bi=np.isfinite(best[q])
        print(' f',f,'pix',divmod(int(q),W),'near-edge closer hit: inst',FI[fid[sel]].tolist(),'best finite',bool(bi))
        tot['hole_cand' if not bi else 'edge_best']+=1
    # fragile best: best hit whose barycentric margin < EPS
    hbest=hit&(tt==best[pix])
    m=np.minimum(np.minimum(uu,vv),1-uu-vv)
    fr=hbest&(m<EPS)
    for q in np.nonzero(fr)[0]:
        others=hit&(pix==pix[q])&(np.arange(len(pix))!=q)
        alt=tt[others].min() if others.any() else np.inf
        if alt>tt[q]*(1+1e-9):
            tot['fragile_best']=tot.get('fragile_best',0)+1
            print(' f',f,'pix',divmod(int(pix[q]),W),'fragile best inst',int(FI[fid[q]]),'margin %.2e'%m[q],'next depth',alt,'best',tt[q], 'next inst', int(FI[fid[others][np.argmin(tt[others])]]) if others.any() else None)
print(tot)
