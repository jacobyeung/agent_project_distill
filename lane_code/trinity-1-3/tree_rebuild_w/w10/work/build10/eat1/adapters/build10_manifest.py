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
    return {'weights.pt':'lm',os.path.relpath(config,artifact):'config'},result
