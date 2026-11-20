import torch
from types import SimpleNamespace
def _prepare_decode(model,processor,batch,max_new_tokens=None):
 from .decoupled_v import features
 depth=model.auxiliary_heads.depth
 cap=features(depth,batch,allow_short=True)
 head=depth.auxiliary_heads.camera.point_depth
 fov=model.pose_fov[None].float()
 dm=head.encode(cap.grids[0],cap.vits[0],fov[0])
 return SimpleNamespace(heads=SimpleNamespace(depth_map=dm,depth_head=head,gravity=torch.tensor([0.,-1.,0.])))
