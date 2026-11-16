import numpy as np, time, sys
sys.path.insert(0, '/scratch/jjyeung/orch_cd/integ_v3/work/generator')
from raycast_cr import first_hits
t=time.time()
from derivgen.native import native_mesh
print('import',time.time()-t,flush=True)
FI,F,V=native_mesh('../proof_pinned/scene0475_01/instance_mesh.npz',raster_compatible=True)
print('mesh',time.time()-t,F.dtype,V.dtype,flush=True)
c=np.load('../proof_pinned/scene0475_01/official_cameras.npz')
for f in range(3):
    t=time.time(); K=np.diag([0.5,0.5,1])@c['intrinsics'][f]; d,fc=first_hits(V,F,c['camera_poses'][f],K,(240,320)); print(f,time.time()-t,flush=True)
