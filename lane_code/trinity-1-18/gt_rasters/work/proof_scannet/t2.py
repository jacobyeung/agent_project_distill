import numpy as np, time, sys, cProfile, pstats
from raycast_cr import first_hits
m=np.load('../proof_pinned/scene0475_01/instance_mesh.npz'); V,F=m['vertices_world'],m['faces']
c=np.load('../proof_pinned/scene0475_01/official_cameras.npz')
K=np.diag([0.5,0.5,1])@c['intrinsics'][0]
cProfile.run("first_hits(V,F,c['camera_poses'][0],K,(240,320))",'p.out')
pstats.Stats('p.out').sort_stats('tottime').print_stats(12)
