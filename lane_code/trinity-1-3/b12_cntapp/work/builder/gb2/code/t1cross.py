import ctypes; ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import numpy as np, sys
sys.path.insert(0, '/scratch/jjyeung/orch_cd/integ_v3/work/generator')
from derivgen.native import native_mesh
asset=sys.argv[1]
c=np.load(f'{asset}/official_cameras.npz'); FI,F,V=native_mesh(f'{asset}/instance_mesh.npz', raster_compatible=True)
H,W=240,320; raster=c['raster_hw']; scale=np.diag([W/float(raster[1]),H/float(raster[0]),1.])
yy,xx=np.mgrid[0:H,0:W]; xs=xx.ravel(); ys=yy.ravel()
for f in range(32):
    K=scale@c['intrinsics'][f]; c2w=np.asarray(c['camera_poses'][f],np.float64); w2c=np.linalg.inv(c2w)
    v=np.asarray(V,np.float64)@w2c[:3,:3].T+w2c[:3,3]; tri=v[F]; z=tri[...,2]
    cross=np.nonzero((z>1e-6).any(1)&~(z>1e-6).all(1))[0]
    fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
    d=np.stack([(xs+.5-cx)/fx,(ys+.5-cy)/fy,np.ones(xs.size)],1)
    nh=0; hp=set()
    for j in cross:
        p0,p1,p2=tri[j]; e1,e2=p1-p0,p2-p0; pv=np.cross(d,e2); det=pv@e1
        good=np.abs(det)>1e-18; inv=np.where(good,1/np.where(good,det,1),0); tv=-p0
        uu=(pv@tv)*inv; qv=np.cross(tv,e1); vv=(d@qv)*inv; tt=(qv@e2)*inv
        hit=good&(uu>=0)&(vv>=0)&(uu+vv<=1)&(tt>0)
        if hit.any(): nh+=1; hp|=set(np.nonzero(hit)[0].tolist())
    print('frame',f,'crossing tris',len(cross),'that hit pixels',nh,'pixels',len(hp),flush=True)
