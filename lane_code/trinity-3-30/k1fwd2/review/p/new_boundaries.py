"""Only these model-forward boundaries have CPU stand-ins."""
import sys
from pathlib import Path
import numpy as np
import hashlib
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B

class CPU:
 synthetic=True
 checkpoint={'step':544,'identity':'CPU_FIXTURE_NOT_WEIGHTS'}
 def tower(self,c,images):
  from student_pilot.tower_read import TowerState
  n=len(images);pose=np.zeros((n,9));pose[:,6]=1;pose[:,7:]=1.;pose[:,0]=np.arange(n)*.005
  v,u=np.mgrid[0:51,0:51]/50.;grid=2.+.7*(u-.5)**2+.8*(v-.5)**2
  depth=np.repeat(grid[None],32,axis=0)
  return TowerState(pose,depth,np.broadcast_to(np.linspace(.1,1.,51)[None,None,:],depth.shape).copy(),np.array([x['index'] for x in c['dense_frames']]),np.array(c['anchor_slots']))
 def own(self,c,images,state):
  v,u=np.mgrid[0:51,0:51]/50.;grid=2.+.7*(u-.5)**2+.8*(v-.5)**2
  return np.repeat(grid[None],32,axis=0)*2.,np.array([0.,-1.,0.])
 def sam(self):
  import torch
  from stub_backend import StubBackend,seed
  from sam3_tower import attach_sam3_tower
  backend=StubBackend()
  def forward(backbone_out,find_input,geometric_prompt,find_target):
   key=round(float(backbone_out['language_features'].sum()),6)
   def is_prompt(p):return abs(key-(seed(p)%9973/9973.))<1e-5
   missing=is_prompt('lamp') or is_prompt('light')
   left=is_prompt('chair') or is_prompt('seat')
   x0,x1=(8,19) if left else (29,40)
   m=torch.full((1,1,36,48),-12.);m[:,:,10:27,x0:x1]=12.
   return dict(pred_logits=torch.tensor([[[-20. if missing else 8.]]]),presence_logit_dec=torch.tensor([[8.]]),pred_boxes=torch.tensor([[[.3 if left else .7,.5,.25,.5]]]),pred_masks=m)
  backend.model.forward_grounding=forward
  return attach_sam3_tower(torch.nn.Linear(1,1),dict(device='cpu'),enabled=True,backend=backend)

class GPU:
 synthetic=False
 def __init__(self,settings,phase="all"):
  import torch
  self.settings=settings;self.device='cuda:0';self.model=None;self.sam_model=None
  if torch.cuda.device_count()!=1:raise ValueError('Require exactly one visible assigned card')
  if torch.cuda.get_device_properties(0).total_memory<40*1024**3:raise ValueError('Require at least 40 GiB VRAM')
  if phase in ('all','own'):
   artifact=B.load(B.checked(settings['artifact']))
   if artifact['step']!=settings.get('export_step',544):raise ValueError('Require the pinned export step')
  self.checkpoint=settings['artifact']
 def tower(self,c,images):
  from student_pilot.tower_read import FrozenG3TTower,WEIGHTS_SHA256,CONFIG_SHA256
  s=self.settings
  if s['tower_weights']['sha256']!=WEIGHTS_SHA256 or s['tower_config']['sha256']!=CONFIG_SHA256:raise ValueError('Frozen tower identity differs')
  if self.model is not None:self.model.to('cpu')
  if self.sam_model is not None:
   import torch
   # SAM loads inference tensors lazily; preserve that state across device copies.
   with torch.inference_mode():self.sam_model._backend.model.to('cpu')
  tower=FrozenG3TTower(dict(weights_path=str(B.checked(s['tower_weights'])),config_path=str(B.checked(s['tower_config'])),device=self.device,dense_frames=len(images),depth_chunk_size=8,dtype='bf16'))
  return tower.run(dict(tower_native_frames=images,tower_frame_indices=[f['index'] for f in c['dense_frames']],tower_anchor_slots=c['anchor_slots'],frame_indices=c['anchor_indices']))
 def own(self,c,images,state):
  import torch,read_runtime,routed
  from evalpath import runtime
  from student_pilot.carrier_c1_decode import _prepare_decode
  from student_pilot.ground_context import closed_adapters
  s=self.settings;cfg=B.load(B.checked(s['config']))
  if self.model is None:
   selected=None if s.get('trainer_selection')=='export_seal' else dict(root=str(B.TREE),sources={n.removeprefix('student_pilot/'):h for n,h in routed.source_pins().items() if n.startswith('student_pilot/')})
   self.model,self.processor,self.info=read_runtime.load_model(s['config'],s['artifact'],s['data_receipt'],device=self.device,selected_trainer=selected)
  else:self.model.to(self.device)
  # Normalized trainer input is a pinned RGB-only row, never a GT answer or response prefix.
  row=c['model_row'];si=row['student_input']
  if si['frame_indices']!=c['anchor_indices'] or si['video_identity']['video_sha256']!=c['video_sha256']:raise ValueError('Own-head prompt/frames differ')
  if [f['sha256'] for f in si['frames']]!=[c['dense_frames'][i]['sha256'] for i in c['anchor_slots']]:raise ValueError('Own-head RGB hash mismatch')
  batch=B.common.move_batch(runtime.prompt_batch(self.processor,row,cfg,'routed'),self.device)
  seen=[];head=self.model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth if s.get('fov_variants') else None
  if head is not None:
   if 'encode' in head.__dict__:raise ValueError('Point-depth encode is already wrapped')
   served_encode=head.encode
   def encode(grid,vit,fov):
    # Observe the served pose-head FoV; the served latent is the unchanged call's result.
    seen.append(fov.detach().clone());return served_encode(grid,vit,fov)
   head.encode=encode
  try:own=closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads
  finally:
   if head is not None:head.__dict__.pop('encode')
  if own.depth_map is None or own.gravity is None:raise ValueError('Own heads missing')
  axis=torch.as_tensor(state.grid_uv.copy(),device=own.depth_map.device);yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
  with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
  if head is not None:
   if own.depth_head is not head:raise ValueError('Served depth head differs')
   self.fov_variants(c,batch,seen,uv,depth)
  gravity=own.gravity.detach().cpu().numpy() if isinstance(own.gravity,torch.Tensor) else np.asarray(own.gravity)
  self.model.to('cpu')
  return depth,gravity
 def fov_variants(self,c,batch,seen,uv,served):
  # PATCH_DONOR3 scale_donor.forward at the donor checkpoint (this export): a separate private feature
  # pass, V1 = private depth.fov on its states, V2 = frozen G3T raw_pose9[anchor_slots,7:9]; one
  # point-depth encode/query per source. Nothing here feeds the served own.npz.
  import math,time,torch
  from student_pilot.decoupled_v import features
  s=self.settings['fov_variants']
  if s.get('schema')!='k1-fov-variants-v1':raise ValueError('FoV variant settings differ')
  if getattr(self,'g3t',None) is None:self.g3t=B.load(B.checked(s['g3t']))['captures']
  dest=Path(s['root'])/B.digest(c['canonical'])[:16]
  if not dest.is_dir() or (dest/'fov.npz').exists() or (dest/'own.npz').exists():raise ValueError('FoV variant destination differs')
  if len(seen)!=1 or tuple(seen[0].shape)!=(32,2):raise ValueError('Expected one served point-depth encode with [32,2] FoV')
  depth=self.model.auxiliary_heads.depth;head=depth.auxiliary_heads.camera.point_depth
  def valid(f):
   return tuple(f.shape)==(32,2) and bool(torch.isfinite(f).all()) and bool(((f>0)&(f<math.pi)).all())
  def grid(cap,f):
   return head.query(head.encode(cap.grids[0],cap.vits[0],f.float()),uv).double().cpu().numpy().reshape(32,51,51)
  arrays=dict(fov_B=seen[0].float().cpu().numpy());missing={};checks={};seconds={}
  start=time.monotonic()
  with torch.no_grad():
   cap=features(depth,batch,allow_short=True)
   if tuple(cap.states.shape[:2])!=(1,32):raise ValueError('Donor feature pass requires one clip with 32 anchor frames')
   seconds['features']=time.monotonic()-start
   control=grid(cap,seen[0])
   checks['second_pass_pose_fov_bit_identical']=bool(np.array_equal(control,served))
   checks['second_pass_pose_fov_max_abs']=float(np.max(np.abs(control-served)))
   fovs={}
   if hasattr(depth,'fov'):fovs['V1']=(1e-4+(math.pi-2e-4)*depth.fov(cap.states.float()).sigmoid())[0]
   else:missing['V1']='MISSING: model.auxiliary_heads.depth.fov'
   r=self.g3t.get(c['canonical'])
   if r is None:missing['V2']='MISSING: no cached G3T FoV for this capture (outside the scored set)'
   else:
    if r['anchor_indices']!=c['anchor_indices'] or r['capture_sha256']!=B.digest(c):raise ValueError('G3T FoV capture/anchor identity differs')
    fovs['V2']=torch.as_tensor(np.asarray(r['fov_hw_rad'],dtype=np.float64),device=cap.states.device,dtype=torch.float32)
   for name,f in fovs.items():
    if not valid(f):raise ValueError('FoV '+name+' requires finite vertical/horizontal radians')
    t=time.monotonic();g=grid(cap,f)
    if g.shape!=(32,51,51) or not np.isfinite(g).all() or np.any(g<=0):raise ValueError('Variant depth must be finite positive 32x51x51: '+name)
    arrays['depth_'+name]=g;arrays['fov_'+name]=f.float().cpu().numpy();seconds[name]=time.monotonic()-t
  np.savez_compressed(dest/'fov.npz',**arrays)
  B.write(dest/'FOV_RECEIPT.json',dict(schema='k1-fov-variants-v1',capture_sha256=B.digest(c),canonical=c['canonical'],
   checkpoint=self.checkpoint,served_depth_sha256=hashlib.sha256(np.ascontiguousarray(served).tobytes()).hexdigest(),
   sources=dict(B='live pose-head FoV, stages[-1][...,7:9] as passed to the served encode',
                V1='1e-4+(pi-2e-4)*sigmoid(depth.fov(states)) on a separate private feature pass (scale_donor V1)',
                V2='frozen G3T raw_pose9[anchor_slots,7:9] from the K1 tower phase cache (scale_donor V2)'),
   g3t=s['g3t'],missing=missing,checks=checks,seconds=seconds,keys=sorted(arrays),
   files={'fov.npz':B.sha(dest/'fov.npz')},boundaries_sha256=B.sha(__file__)))
 def sam(self):
  import torch
  from sam3_tower import attach_sam3_tower
  s=self.settings
  if s['sam_checkpoint']['sha256']!=B.perception.SAM_SHA:raise ValueError('Frozen SAM checkpoint differs')
  if self.sam_model is None:
   settings=dict(device=self.device,checkpoint_path=str(B.checked(s['sam_checkpoint'])),source_root=s['sam_source'],receipt_path=str(B.checked(s['sam_receipt'])))
   self.sam_model=attach_sam3_tower(torch.nn.Linear(1,1),settings,enabled=True)
  else:
   with torch.inference_mode():self.sam_model._backend.model.to(self.device)
  return self.sam_model
