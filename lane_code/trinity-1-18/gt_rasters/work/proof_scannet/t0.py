import numpy as np, time, sys
from raycast_cr import first_hits
r=np.load('/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0155_01.npz')
m=np.load('instance_mesh.npz'); V,F,FI=m['vertices_world'],m['faces'],m['face_instance_ids']
for f in [0,10]:
  for off in [0.5,0.0]:
    for mode in ['z','ray']:
      t=time.time(); d,fc=first_hits(V,F,r['c2w'][f],r['K_frames'][f],(240,320),off=off,mode=mode)
      hit=fc>=0; dd=np.where(hit,d,0).astype(np.float32)
      inst=np.full(fc.shape,-1,np.int32); inst[hit]=FI[fc[hit]]; inst[dd<=0]=-1
      D=r['depth'][f]; I=r['inst'][f]
      both=(D>0)&(dd>0)
      print(f,off,mode,'%.1fs'%(time.time()-t),'hitmask_agree',((D>0)==(dd>0)).mean(),'inst_eq',(I==inst).mean(),'depth_exact',(D==dd).mean(),'maxabs',np.abs(D-dd)[both].max(),'med',np.median(np.abs(D-dd)[both]))
