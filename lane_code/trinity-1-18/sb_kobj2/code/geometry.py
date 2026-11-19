"""Train-fitted E3 S4 and G1, with no fitting or GT reads on dev sets."""
from common import *
import numpy as np
from e2e_reader.geometry import from_tower
from student_pilot.camera_targets import rotation_from_xyzw

def g3t_s4(tower):
 fits=js(ROOT/'inputs/local/FITS.json')
 assert sha(ROOT/'inputs/local/FITS.json')=='592c20480643fc8b3d45ba1a8e71cbee2998e7e02b63296f23c82c8393da9834'
 sha(ROOT/'inputs/local/e3_harness.py')
 assert fits['provenance']['split']=='train' and not fits['provenance']['heldout_accessed_during_fit']
 slots=np.asarray(tower['anchor_slots']);raw=np.asarray(tower['raw_pose']);R=np.array([rotation_from_xyzw(p[3:7]).T for p in raw[slots]])
 gravity=np.mean(-R[:,:,1],axis=0);gravity=gravity/np.linalg.norm(gravity)
 n=len(raw);depth=np.asarray(tower['depth_grid']);assert depth.shape==(n,51,51)
 def make(scale):return from_tower(raw,np.arange(n),tower['frame_indices'],depth,tower['grid_uv'],gravity,scale,tower['source_hw'])
 geo=make(1.);u,v=np.meshgrid(tower['grid_uv'],tower['grid_uv']);uv=np.column_stack((u.ravel(),v.ravel()));parts=[]
 for slot in slots:
  f=int(slot)+1;d=depth[slot].ravel();R,t=geo.cam(f);p=(geo.rays(f,uv)*d[:,None])@R.T+t;parts.append(p[np.isfinite(p).all(1)&np.isfinite(d)&(d>0)])
 points=np.concatenate(parts);z1,z99=np.percentile(points[:,2],[1,99]) if len(points) else (float('nan'),float('nan'));height=float(np.median(geo.C[slots,2,3]-z1));span=float(z99-z1)
 scale=float(np.exp(np.dot([1.,np.log(height),np.log(span)],fits['S4_coefficients']))) if height>0 and span>0 else float('nan')
 available=bool(np.isfinite(scale) and scale>0)
 if not available:scale=float(fits['S1'])
 return make(scale),dict(s4_available=available,treatment='S4 treatment',scale=scale,gravity=gravity,h_raw=height,span=span,scale_rule='S4',gravity_rule='G1')
