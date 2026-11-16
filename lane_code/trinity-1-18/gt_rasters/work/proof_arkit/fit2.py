exec(open('fit.py').read().split("frames=[f")[0])
from PIL import Image
ds=sorted(glob.glob('src/42899922_frames/lowres_depth/*.png'),key=ts)
pc=sorted(glob.glob('src/42899922_frames/lowres_wide_intrinsics/*.pincam'),key=ts)
yi=np.floor(np.arange(240)*192/240).astype(int); xi=np.floor(np.arange(320)*256/320).astype(int)
frames=[f for f in range(32) if (D[f]>0).any()]
def src_world(f, off):
    d=np.array(Image.open(ds[f])).astype(np.float64)/1000.0
    w,h,fx,fy,cx,cy=np.loadtxt(pc[f])
    v,u=np.mgrid[0:192,0:256].astype(np.float64)
    x=(u+off-cx)/fx*d; y=(v+off-cy)/fy*d
    P=np.stack([x,y,d,np.ones_like(d)],-1).reshape(-1,4)@C[f].astype(np.float64).T
    return P[:,:3], d.reshape(-1)>0
for off in [0.0,0.5]:
  for m in [0.03]:
    for mf in [0.03,0.035]:
        ag=[]
        for f in frames:
            P,valid=src_world(f,off); a=assign(P,valid,m,mf).reshape(192,256)[np.ix_(yi,xi)]
            ag.append((a==I[f]).mean())
        print(off,m,mf,'%.6f'%np.mean(ag),flush=True)
