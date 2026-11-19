"""Reload an RL adapter artifact on the immutable export A4's loader read for training."""
import torch
from . import provenance as P
from .adapters import install
from .train import load_export

def load(pin,device):
    artifact=P.load(P.checked(pin))
    if artifact['schema']!='rl-on-n-adapter-export-v2':raise ValueError('Foreign RL export')
    torch.manual_seed(artifact['init_seed'])
    model,processor,info=load_export(artifact['export_restore'],artifact['export_config'],device,artifact['grounding'])
    selected=install(model,artifact['adapter_rank'],artifact['adapter_alpha'])
    if selected!=artifact['adapter_modules']:raise ValueError('Adapter module mapping changed')
    saved=torch.load(P.checked(artifact['weights']),map_location='cpu',weights_only=True)['adapters']
    live={n:p for n,p in model.named_parameters() if p.requires_grad}
    if set(live)!=set(saved):raise ValueError('Adapter parameter set differs')
    with torch.no_grad():
        for name,p in live.items():
            if p.shape!=saved[name].shape:raise ValueError('Adapter shape differs')
            p.copy_(saved[name])
    return model.eval(),processor,info
