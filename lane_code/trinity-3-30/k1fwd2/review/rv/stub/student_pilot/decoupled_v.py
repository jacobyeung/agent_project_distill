import torch
from types import SimpleNamespace
CALLS=[]
def features(model,batch,allow_short=False):
 CALLS.append(1)
 g=torch.Generator().manual_seed(7)
 T=32;H=W=4;D=model.dim
 states=torch.randn(1,T,D,generator=g)+model.auxiliary_heads.frame_queries[None]
 return SimpleNamespace(states=states,grids=[torch.randn(T,H,W,D,generator=g)],vits=[[torch.randn(T,2*H,2*W,D,generator=g) for _ in range(3)]])
