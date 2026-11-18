"""Declare the complete artifact read closure without copying external towers."""
import hashlib
import json
import os
from pathlib import Path


def write_manifest(directory, model, cfg):
    directory=Path(directory).resolve()
    files={}
    for p in directory.rglob('*'):
        if not p.is_file() or p.name=='eat1-artifact.json': continue
        role='head' if p.name=='heads.pt' else 'lm' if 'full_weights' in p.parts else 'config'
        with p.open('rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
        files[str(p.relative_to(directory))]=dict(sha256=h,role=role)
    geometry=getattr(model,'geometry_online',None)
    if geometry:
        for role in ('weights','config'):
            entry=geometry['encoder'][role]
            p=Path(entry['path']).resolve()
            with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
            if h!=entry['sha256']: raise ValueError('tower_export_pin_mismatch')
            files[os.path.relpath(p,directory)]=dict(sha256=h,role='tower' if role=='weights' else 'config')
    modules={'model.language_model':dict(role='lm',name='lm'),
             'model.visual':dict(role='vit',name='base_vit'),
             'auxiliary_heads.pose':dict(role='head',name='pose_head')}
    for attribute,role,name in (('depth','head','depth_head'),('geometry_encoder','tower','g3t'),('gf1','connector','gf1')):
        if hasattr(model.auxiliary_heads,attribute): modules['auxiliary_heads.'+attribute]=dict(role=role,name=name)
    value=dict(schema='eat1-artifact-v1',root='.',files=files,modules=modules)
    (directory/'eat1-artifact.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return value
