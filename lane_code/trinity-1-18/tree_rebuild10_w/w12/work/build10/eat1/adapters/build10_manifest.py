"""Declare build 10's registered modules in the two native tiny-reader artifacts."""
import os
from pathlib import Path

def entries(model,tree,artifact,modules):
    result=dict(modules)
    for name in ('depth_readout','heading'):
        module=getattr(model.auxiliary_heads,name)
        result['auxiliary_heads.'+name]=dict(role='fixed_math',name=name,inputs=module.inputs,outputs=module.outputs,
            buffers={k:dict(file='weights.pt',key='auxiliary_heads.'+name+'.'+k) for k,_ in module.named_buffers()})
    config=Path(tree)/'trace_format/readout_config.json'
    files={'weights.pt':'lm',os.path.relpath(config,artifact):'config'}
    if hasattr(model.auxiliary_heads,'geometry_encoder'):
        files[os.path.relpath(Path(tree)/'configs/gf1_stage1.json',artifact)]='config'
        source=Path(tree)/'student_pilot'
        paths=[source/'g3t_online.py',*sorted((source/'g3t_vendor').rglob('*.py'))]
        names=[os.path.relpath(p,artifact) for p in paths]
        files.update({p:'tower' for p in names})
        result['auxiliary_heads.geometry_encoder']=dict(result['auxiliary_heads.geometry_encoder'],files=names)
    return files,result
