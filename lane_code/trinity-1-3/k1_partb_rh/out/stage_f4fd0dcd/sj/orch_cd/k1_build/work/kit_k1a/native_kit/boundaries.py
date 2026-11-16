"""Only these model-forward boundaries have CPU stand-ins."""
import sys
from pathlib import Path
import numpy as np
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
   if artifact['step']!=544:raise ValueError('Require step-544 export')
  self.checkpoint=settings['artifact']
 def tower(self,c,images):
  from student_pilot.tower_read import FrozenG3TTower,WEIGHTS_SHA256,CONFIG_SHA256
  s=self.settings
  if s['tower_weights']['sha256']!=WEIGHTS_SHA256 or s['tower_config']['sha256']!=CONFIG_SHA256:raise ValueError('Frozen tower identity differs')
  if self.model is not None:self.model.to('cpu')
  if self.sam_model is not None:self.sam_model._backend.model.to('cpu')
  tower=FrozenG3TTower(dict(weights_path=str(B.checked(s['tower_weights'])),config_path=str(B.checked(s['tower_config'])),device=self.device,dense_frames=len(images),depth_chunk_size=8,dtype='bf16'))
  return tower.run(dict(tower_native_frames=images,tower_frame_indices=[f['index'] for f in c['dense_frames']],tower_anchor_slots=c['anchor_slots'],frame_indices=c['anchor_indices']))
 def own(self,c,images,state):
  import torch,read_runtime,routed
  from evalpath import runtime
  from student_pilot.carrier_c1_decode import _prepare_decode
  from student_pilot.ground_context import closed_adapters
  s=self.settings;cfg=B.load(B.checked(s['config']))
  if self.model is None:
   selected=dict(root=str(B.TREE),sources={n.removeprefix('student_pilot/'):h for n,h in routed.source_pins().items() if n.startswith('student_pilot/')})
   self.model,self.processor,self.info=read_runtime.load_model(s['config'],s['artifact'],s['data_receipt'],device=self.device,selected_trainer=selected)
  else:self.model.to(self.device)
  # Normalized trainer input is a pinned RGB-only row, never a GT answer or response prefix.
  row=c['model_row'];si=row['student_input']
  if si['frame_indices']!=c['anchor_indices'] or si['video_identity']['video_sha256']!=c['video_sha256']:raise ValueError('Own-head prompt/frames differ')
  if [f['sha256'] for f in si['frames']]!=[c['dense_frames'][i]['sha256'] for i in c['anchor_slots']]:raise ValueError('Own-head RGB hash mismatch')
  batch=B.common.move_batch(runtime.prompt_batch(self.processor,row,cfg,'routed'),self.device)
  own=closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads
  if own.depth_map is None or own.gravity is None:raise ValueError('Own heads missing')
  axis=torch.as_tensor(state.grid_uv.copy(),device=own.depth_map.device);yy,xx=torch.meshgrid(axis,axis,indexing='ij');uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
  with torch.no_grad():depth=own.depth_head.query(own.depth_map,uv).double().cpu().numpy().reshape(32,51,51)
  gravity=own.gravity.detach().cpu().numpy() if isinstance(own.gravity,torch.Tensor) else np.asarray(own.gravity)
  self.model.to('cpu')
  return depth,gravity
 def sam(self):
  import torch
  from sam3_tower import attach_sam3_tower
  s=self.settings
  if s['sam_checkpoint']['sha256']!=B.perception.SAM_SHA:raise ValueError('Frozen SAM checkpoint differs')
  if self.sam_model is None:
   settings=dict(device=self.device,checkpoint_path=str(B.checked(s['sam_checkpoint'])),source_root=s['sam_source'],receipt_path=str(B.checked(s['sam_receipt'])))
   self.sam_model=attach_sam3_tower(torch.nn.Linear(1,1),settings,enabled=True)
  else:self.sam_model._backend.model.to(self.device)
  return self.sam_model
