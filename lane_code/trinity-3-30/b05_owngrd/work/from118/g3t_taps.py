"""G3T spatial taps with explicit LM frame order and sparse intermediate retention."""
from contextlib import contextmanager
import difflib
import hashlib
import importlib
import inspect
import json
import sys
import textwrap
import types
from pathlib import Path

import torch
from torch import nn

from provenance import sha256

VENDOR = Path('/scratch/jjyeung/orch_cd/integ_v3/work/tree/student_pilot/g3t_vendor')
TAPS = (5, 11, 17, 23)  # Zero-based quarter-depth probe taps.


def import_vendor(root=VENDOR):
    root=Path(root).resolve()
    if not str(root).startswith('/scratch/'):
        raise ValueError('G3T vendor must be local')
    for key,module in tuple(sys.modules.items()):
        if key=='vggt' or key.startswith('vggt.'):
            path=getattr(module,'__file__',None)
            if path and not Path(path).resolve().is_relative_to(root):
                raise ValueError('Another G3T source is imported')
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    return importlib.import_module('vggt.models.g3t').G3T


def sparse_source(source):
    """Retain None placeholders so existing heads keep their original indices."""
    old='''                concat_inter = torch.cat([frame_intermediates[i], global_intermediates[i]], dim=-1)
                output_list.append(concat_inter)'''
    new='''                idx = len(output_list)
                concat_inter = (torch.cat([frame_intermediates[i], global_intermediates[i]], dim=-1)
                                if self.training or idx in getattr(self, '_own_keep_indices', (4, 5, 11, 17, 23, self.depth-1)) else None)
                output_list.append(concat_inter)'''
    if source.count(old)!=1: raise ValueError('G3T aggregator source no longer matches audited patch')
    return source.replace(old,new)


@contextmanager
def sparse_retention(aggregator, indices=TAPS):
    """Temporary instance-only patch; no weights, global classes or source files change."""
    if aggregator.training: raise ValueError('Sparse tap patch is inference-only')
    keep=tuple(sorted(set(indices)|{4,11,17,23,aggregator.depth-1}))
    if min(keep)<0 or max(keep)>=aggregator.depth: raise ValueError('Invalid G3T tap indices')
    if hasattr(aggregator,'_own_keep_indices'): raise ValueError('Nested sparse capture is unsupported')
    method=aggregator.forward
    source=textwrap.dedent(inspect.getsource(type(aggregator).forward))
    # Match the audited source independently of indentation introduced by dedent.
    source=source.replace('            concat_inter = torch.cat([frame_intermediates[i], global_intermediates[i]], dim=-1)\n'
                          '            output_list.append(concat_inter)',
                          '            idx = len(output_list)\n'
                          '            concat_inter = (torch.cat([frame_intermediates[i], global_intermediates[i]], dim=-1)\n'
                          '                            if idx in self._own_keep_indices else None)\n'
                          '            output_list.append(concat_inter)')
    if '_own_keep_indices' not in source: raise ValueError('Unrecognized aggregator implementation')
    namespace={}
    exec(compile(source, '<own_probe sparse G3T>', 'exec'), method.__func__.__globals__, namespace)
    aggregator._own_keep_indices=keep
    aggregator.forward=types.MethodType(namespace['forward'],aggregator)
    try:
        yield aggregator
    finally:
        aggregator.forward=method
        del aggregator._own_keep_indices


def maps_from_tokens(tokens, patch_start, size_hw, patch_size, frame_order=None, indices=TAPS):
    h,w=(int(x)//patch_size for x in size_hw)
    result={}
    for k in tuple(indices)+(len(tokens)-1,):
        x=tokens[k]
        if x is None or x.ndim!=4 or x.shape[0]!=1 or x.shape[2]-patch_start!=h*w:
            raise ValueError(f'Invalid G3T tokens at block {k}')
        x=x[0,:,patch_start:,:].reshape(x.shape[1],h,w,x.shape[-1])
        if frame_order is not None:
            order=torch.as_tensor(frame_order,dtype=torch.long,device=x.device)
            if sorted(order.tolist())!=list(range(len(x))):
                raise ValueError('frame_order must be the LM-order permutation of all frames')
            x=x[order]
        result[str(k)]=x
    result['trunk']=result[str(len(tokens)-1)]
    return result


class TapCapture:
    """Capture tokens during an existing full G3T forward; preserve every head output."""
    def __init__(self,model,size_hw,frame_order=None,sparse=True):
        self.model,self.size_hw,self.frame_order,self.sparse=model,size_hw,frame_order,sparse
        self.maps=None
    def __enter__(self):
        from contextlib import nullcontext
        self.context=sparse_retention(self.model.aggregator) if self.sparse else nullcontext()
        self.context.__enter__()
        def hook(module,args,value):
            tokens,start=value
            self.maps=maps_from_tokens(tokens,start,self.size_hw,module.patch_size,self.frame_order)
        self.hook=self.model.aggregator.register_forward_hook(hook)
        return self
    def __exit__(self,*args):
        self.hook.remove()
        return self.context.__exit__(*args)


class G3TProvider(nn.Module):
    def __init__(self,model): super().__init__(); self.net=model
    def dense(self,frames,size_hw):
        from own_feats.core import pixels
        if any(s%14 for s in size_hw): raise ValueError('G3T sizes must divide patch size 14')
        x=pixels(frames,size_hw,(0,0,0),(1,1,1)).to(next(self.net.parameters()).device)
        # The whole clip enters temporal attention in the given LM frame order.
        with sparse_retention(self.net.aggregator):
            tokens,start=self.net.aggregator(x[None])
        maps=maps_from_tokens(tokens,start,size_hw,14)
        return [maps[str(k)] for k in TAPS]  # trunk aliases block 23, so concatenate it only once.


def load(cfg,device):
    from safetensors import safe_open
    cls=import_vendor(cfg.get('source_root',VENDOR))
    path=Path(cfg['path'])
    expected=cfg.get('sha256')
    if not expected: raise ValueError('G3T needs the published checkpoint sha256 in its weight config')
    if sha256(path)!=expected: raise ValueError('G3T checkpoint incomplete or sha256 mismatch')
    # Probe uses aggregator only. No camera, point or depth weights enter GPU memory.
    model=cls(enable_point=False,enable_depth=False,enable_gravity_camera_heads=False)
    with safe_open(str(path),framework='pt',device='cpu') as f:
        state={k.removeprefix('aggregator.'):f.get_tensor(k) for k in f.keys() if k.startswith('aggregator.')}
    model.aggregator.load_state_dict(state,strict=True)
    metadata=dict(weights_sha256=expected,source_sha256=sha256(Path(cfg.get('source_root',VENDOR))/'vggt/models/aggregator.py'),
                  taps=list(TAPS),index_base=0,trunk_alias=23,frame_order='caller LM order')
    return G3TProvider(model),metadata


def write_patch(path):
    src=VENDOR/'vggt/models/aggregator.py'
    before=src.read_text();after=sparse_source(before)
    Path(path).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                                                   fromfile='a/student_pilot/g3t_vendor/vggt/models/aggregator.py',
                                                   tofile='b/student_pilot/g3t_vendor/vggt/models/aggregator.py')))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--write-patch',required=True)
    write_patch(p.parse_args().write_patch)
