"""Train-fitted E3 S4 and G1, with no fitting or GT reads on dev sets."""
from common import *
import numpy as np
from e2e_reader.geometry import from_tower
from student_pilot.camera_targets import rotation_from_xyzw

def g3t_s4(tower):
 fits=js(ROOT/'inputs/local/FITS.json')
 assert fits['provenance']['split']=='train' and not fits['provenance']['heldout_accessed_during_fit']
 slots=np.asarray(tower['anchor_slots']);raw=np.asarray(tower['raw_pose']);R=np.array([rotation_from_xyzw(p[3:7]).T for p in raw[slots]])
 gravity=np.mean(-R[:,:,1],axis=0);gravity=gravity/np.linalg.norm(gravity)
 n=len(raw);depth=np.asarray(tower['depth_grid']);assert depth.shape==(n,51,51)
 def make(scale):return from_tower(raw,np.arange(n),tower['frame_indices'],depth,tower['grid_uv'],gravity,scale,tower['source_hw'])
 geo=make(1.);u,v=np.meshgrid(tower['grid_uv'],tower['grid_uv']);uv=np.column_stack((u.ravel(),v.ravel()));parts=[]
 for slot in slots:
  f=int(slot)+1;d=depth[slot].ravel();R,t=geo.cam(f);p=(geo.rays(f,uv)*d[:,None])@R.T+t;parts.append(p[np.isfinite(p).all(1)&np.isfinite(d)&(d>0)])
 points=np.concatenate(parts);z1,z99=np.percentile(points[:,2],[1,99]);height=float(np.median(geo.C[slots,2,3]-z1));span=float(z99-z1)
 if height<=0 or span<=0:raise ValueError('nonpositive_height_feature')
 scale=float(np.exp(np.dot([1.,np.log(height),np.log(span)],fits['S4_coefficients'])))
 if not np.isfinite(scale) or scale<=0:raise ValueError('invalid S4 scale')
 return make(scale),dict(scale=scale,gravity=gravity,h_raw=height,span=span,scale_rule='S4',gravity_rule='G1')

def da3_f32(scene):
 cfgpath=ROOT/'config/DA3_ROOM_HOOK.json'
 if not cfgpath.exists():raise Missing(str(cfgpath)+' (room kit path not supplied)')
 cfg=js(cfgpath);p=local(cfg['prediction_root'])/scene/'pred.npz';d=npz(p)
 # Native DA3 metric geometry requires a pinned room-kit adapter, not an inferred NPZ schema.
 assert sha(cfg['adapter_path'])==cfg['adapter_sha256'];adapter=module(cfg['adapter_path'],'room_da3_adapter')
 return adapter.geometry(d),dict(prediction_path=str(p),scale_rule='DA3 native metric')
