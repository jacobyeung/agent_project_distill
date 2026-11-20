"""Admit the staged detector's pinned positive-point API before replay."""
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys


def admit(source_root):
    pin=Path(__file__).parent/'4.json'
    if not pin.is_file() or not json.loads(pin.read_text()).get('reviewed'):
        raise RuntimeError('SAM Prompt API is unreviewed; point mode refuses before the first item')
    pin=json.loads(pin.read_text()); root=Path(source_root).resolve()
    # Pin behavior as well as the constructor: matching argument names alone
    # cannot establish coordinates or the enabled geometry-encoder branches.
    for name,expected in pin['source_files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('SAM Prompt source differs: '+name)
    for key,module in tuple(sys.modules.items()):
        if key=='sam3' or key.startswith('sam3.'):
            source=getattr(module,'__file__',None)
            if not source or not Path(source).resolve().is_relative_to(root):
                raise ImportError('Foreign SAM module: '+key)
    sys.path.insert(0,str(root)); importlib.invalidate_caches()
    module=importlib.import_module(pin['module']); Prompt=module.Prompt
    verify_signature(Prompt,pin)
    if not Path(inspect.getfile(Prompt)).resolve().is_relative_to(root):
        raise ImportError('Prompt resolved outside staged SAM source')
    return Prompt,dict(signature=str(inspect.signature(Prompt)),source_root=str(root),
                       source_files=pin['source_files'],coordinates=pin['coordinates'],positive_label=1)


def verify_signature(Prompt,pin):
    parameters=list(inspect.signature(Prompt).parameters.values())
    if ([p.name for p in parameters]!=pin['parameters'] or
        any(p.kind!=inspect.Parameter.POSITIONAL_OR_KEYWORD or p.default is not None for p in parameters)):
        raise RuntimeError('SAM Prompt signature differs from the reviewed constructor')


def check_detector(tower):
    encoder=getattr(tower._backend.model,'geometry_encoder',None)
    if encoder is None or not any(getattr(encoder,k,None) is not None for k in
            ('points_direct_project','points_pool_project','points_pos_enc_project')):
        raise RuntimeError('SAM detector point encoding is disabled; deployed Sam3Tower has no admitted predict_inst fallback')


def make_prompt(Prompt,point,device):
    import torch
    xy=torch.tensor(point,dtype=torch.float32,device=device)
    if xy.shape!=(2,) or not bool(torch.isfinite(xy).all()) or not bool(((xy>=0)&(xy<=1)).all()):
        raise ValueError('Prompt requires normalized finite xy')
    return Prompt(point_embeddings=xy.reshape(1,1,2),
                  point_mask=torch.zeros((1,1),dtype=torch.bool,device=device),
                  point_labels=torch.ones((1,1),dtype=torch.long,device=device))
