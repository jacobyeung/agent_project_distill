"""Reload an RL adapter artifact on its authenticated N/P C1 starting export."""
import torch
from . import provenance as P
from .adapters import install
from .train import load_export

def load(pin,device):
    artifact=P.load(P.checked(pin))
    if artifact['schema']!='rl-on-n-adapter-export-v1':raise ValueError('Foreign RL export')
    torch.manual_seed(artifact['init_seed'])
    model,processor=load_export(P.load(P.checked(artifact['source_config'])),artifact['base_export'],device,artifact['start_mode'])
    selected=install(model,artifact['adapter_rank'],artifact['adapter_alpha'])
    if selected!=artifact['adapter_modules']:raise ValueError('Adapter module mapping changed')
    saved=torch.load(P.checked(artifact['weights']),map_location='cpu',weights_only=True)['adapters']
    live={n:p for n,p in model.named_parameters() if p.requires_grad}
    if set(live)!=set(saved):raise ValueError('Adapter parameter set differs')
    with torch.no_grad():
        for name,p in live.items():
            if p.shape!=saved[name].shape:raise ValueError('Adapter shape differs')
            p.copy_(saved[name])
    return model.eval(),processor
