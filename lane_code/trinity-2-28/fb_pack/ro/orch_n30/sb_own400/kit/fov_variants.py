"""Separate FoV readout extension; the sealed GPU.own and HeadState stay unchanged."""
import time,math
import numpy as np
from core import *

def validate_fov(fov):
 a=np.asarray(fov)
 if a.shape!=(32,2) or not np.isfinite(a).all() or not ((a>0)&(a<np.pi)).all():raise Refusal('Invalid FoV: require [32,2] vertical,horizontal radians')
 return a

def g3t_fov(c):
 p=KIT/'inputs/G3T_FOV.json';r=read(p)['captures'].get(c['canonical'])
 if r is None:raise Refusal('MISSING G3T FoV: '+str(p)+' '+c['canonical'])
 if r['capture_sha256']!=digest(c) or r['anchor_indices']!=c['anchor_indices']:raise Refusal('G3T anchor/capture mismatch')
 return validate_fov(r['fov_hw_rad'])

def private_fov(depth,captured):
 # Exact carrier_c1.PrivateDepth.forward parameterization, before detached encode.
 return 1e-4+(math.pi-2e-4)*depth.fov(captured.states.float()).sigmoid()

def encode_grid_with_fov(encode,query,captured,fov,uv):
 """HeadState's encode/query path with an explicit FoV, without another LM/ViT pass."""
 import torch
 with torch.no_grad():
  latent=encode(captured.grids[0],captured.vits[0],fov.float())
  return query(latent,uv).double().cpu().numpy().reshape(32,51,51)

def own_with_fov_variants(boundary,c,images,state):
 import torch
 from student_pilot import decoupled_v
 depth=boundary.model.auxiliary_heads.depth;head=depth.auxiliary_heads.camera.point_depth
 original_features=decoupled_v.features;original_encode=head.encode
 captured=[];extra={};fovs={};timing={};missing={}
 def capture_features(model,batch,**kwargs):
  result=original_features(model,batch,**kwargs)
  if model is depth:captured.append(result)
  return result
 def encode(grid,vit,pose_fov):
  base=original_encode(grid,vit,pose_fov)
  if len(captured)!=1:raise Refusal('Expected exactly one private-ViT capture')
  cap=captured[0];axis=torch.as_tensor(state.grid_uv.copy(),device=pose_fov.device)
  yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
  fovs['B']=validate_fov(pose_fov.detach().float().cpu().numpy())
  for name in ('V1','V2'):
   if name=='V1' and not hasattr(depth,'fov'):
    missing[name]='MISSING: checkpoint model.auxiliary_heads.depth.fov';continue
   if pose_fov.is_cuda:torch.cuda.synchronize()
   start=time.monotonic()
   if name=='V1':fov=private_fov(depth,cap)[0].float()
   else:fov=torch.as_tensor(g3t_fov(c),dtype=torch.float32,device=pose_fov.device)
   fovs[name]=validate_fov(fov.detach().cpu().numpy())
   extra[name]=encode_grid_with_fov(original_encode,head.query,cap,fov,uv)
   valid_grid(extra[name])
   if pose_fov.is_cuda:torch.cuda.synchronize()
   timing[name]=time.monotonic()-start
  return base
 had_local='encode' in head.__dict__;local=head.__dict__.get('encode')
 decoupled_v.features=capture_features;head.encode=encode
 try:
  with torch.no_grad():base,gravity=boundary.own(c,images,state)
 finally:
  decoupled_v.features=original_features
  if had_local:head.encode=local
  else:del head.__dict__['encode']
 return base,gravity,{'depths':extra,'fovs':fovs,'seconds':timing,'missing':missing,'private_vit_passes':len(captured)}
