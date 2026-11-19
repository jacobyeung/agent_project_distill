"""Small trainable LM adapters; disabling them restores the immutable SFT reference."""
from contextlib import contextmanager
import math
import torch
from torch import nn

class LowRank(nn.Module):
    def __init__(self,base,rank,alpha):
        super().__init__(); self.base=base; self.enabled=True; self.scale=alpha/rank
        self.a=nn.Parameter(torch.empty(rank,base.in_features,device=base.weight.device,dtype=torch.float32))
        self.b=nn.Parameter(torch.zeros(base.out_features,rank,device=base.weight.device,dtype=torch.float32))
        nn.init.kaiming_uniform_(self.a,a=math.sqrt(5))
    @property
    def weight(self): return self.base.weight
    @property
    def bias(self): return self.base.bias
    def forward(self,x):
        y=self.base(x)
        if self.enabled:
            delta=torch.nn.functional.linear(torch.nn.functional.linear(x.float(),self.a),self.b)
            y=y+(self.scale*delta).to(y.dtype)
        return y

def install(model,rank=16,alpha=32):
    model.requires_grad_(False)
    selected=[]
    # MLP projections are shared by every Qwen3.5 decoder layer, including DeltaNet layers.
    for name,mod in list(model.model.language_model.named_modules()):
        if isinstance(mod,nn.Linear) and name.rsplit('.',1)[-1] in ('gate_proj','up_proj','down_proj'):
            parent,leaf=name.rsplit('.',1)
            setattr(model.model.language_model.get_submodule(parent),leaf,LowRank(mod,rank,alpha))
            selected.append(name)
    if not selected: raise ValueError('No native Qwen MLP projections found')
    return selected

@contextmanager
def reference(model):
    layers=[m for m in model.modules() if isinstance(m,LowRank)]
    before=[m.enabled for m in layers]
    try:
        for m in layers: m.enabled=False
        with torch.no_grad(): yield
    finally:
        for m,v in zip(layers,before): m.enabled=v

def state(model):
    return {n:p.detach().cpu() for n,p in model.named_parameters() if p.requires_grad}
