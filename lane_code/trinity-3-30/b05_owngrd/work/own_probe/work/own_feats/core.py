from contextlib import nullcontext
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F

from provenance import sha256, digest

DEFAULT_BUNDLE = Path('/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle')
DEFAULT_T0 = Path('/scratch/jjyeung/orch_cd/mdg_build/work/data/t0mind/ap/244cdf20/runs/e59f7158/m800')
TAPS = (7, 14, 21, 27)  # One-based, ceil(depth * quarter).


def channel_reduce(x, width=1024):
    """Parameter-free channel averaging gives every probe the same input width."""
    shape=x.shape
    return F.adaptive_avg_pool1d(x.float().reshape(-1,1,shape[-1]),width).reshape(*shape[:-1],width)


def readout_maps(maps, readout='four', statistics=None):
    if readout not in ('four','final','unstandardized'): raise ValueError('Unknown readout')
    if len(maps)!=4: raise ValueError('Every encoder must expose four quarter-depth taps')
    if statistics is not None and readout!='unstandardized':
        from .standardize import standardize_maps
        maps=standardize_maps(maps,statistics)
    selected=maps if readout=='four' else maps[-1:]
    if readout=='unstandardized':selected=maps
    width=1024//len(selected)
    return [F.layer_norm(channel_reduce(F.layer_norm(m.float(), (m.shape[-1],)),width),(width,)) for m in selected]


def pixels(frames, size_hw, mean=(.5, .5, .5), std=(.5, .5, .5)):
    h, w = map(int, size_hw)
    if min(h, w) < 1 or not frames:
        raise ValueError('Positive size and at least one frame required')
    arr = np.stack([np.asarray(im.convert('RGB').resize((w, h), Image.Resampling.BICUBIC),
                               dtype=np.float32) / 255. for im in frames])
    x = torch.from_numpy(arr).permute(0, 3, 1, 2)
    return (x - x.new_tensor(mean)[None,:,None,None]) / x.new_tensor(std)[None,:,None,None]


def pack_qwen(rgb, patch=16, temporal=2, merge=2):
    """Duplicate each frame, then pack [F,H/m,W/m,m,m,C,T,p,p]."""
    n, c, h, w = rgb.shape
    if h % (patch*merge) or w % (patch*merge):
        raise ValueError('Qwen input dimensions must be multiples of patch*merge (32)')
    x = rgb[:,None].expand(n,temporal,c,h,w).reshape(n,temporal,c,h//patch,patch,w//patch,patch)
    x = x.reshape(n,temporal,c,h//patch//merge,merge,patch,w//patch//merge,merge,patch)
    packed = x.permute(0,3,6,4,7,2,1,5,8).reshape(n*h//patch*w//patch,c*temporal*patch*patch)
    return packed, torch.tensor([[n,h//patch,w//patch]], dtype=torch.long)


def unpack_qwen(tokens, grid, merge=2):
    n, h, w = map(int, grid[0])
    if tokens.ndim != 2 or tokens.shape[0] != n*h*w or h % merge or w % merge:
        raise ValueError('Invalid packed Qwen feature grid')
    return tokens.reshape(n,h//merge,w//merge,merge,merge,-1).permute(0,1,3,2,4,5).reshape(n,h,w,-1)


def pool(maps, masks):
    """Area-weighted mean per tap, L2-normalized per tap, concatenated.

    masks [R,H,W] uses one map frame for all regions, or one region per frame.
    Pass (masks, frame_indices) for arbitrary region-to-frame assignments.
    Zero-area masks produce zero features; callers retain their invalidity flag.
    """
    if isinstance(masks, tuple):
        masks, frame_ids = masks
    else:
        frame_ids = None
    masks = torch.as_tensor(masks, dtype=torch.float32)
    if masks.ndim != 3 or not maps:
        raise ValueError('pool requires [R,H,W] masks and nonempty maps')
    if not torch.isfinite(masks).all() or (masks < 0).any() or (masks > 1).any():
        raise ValueError('Mask weights must be finite and in [0,1]')
    result = []
    for m in maps:
        if m.ndim != 4:
            raise ValueError('Map layout must be [frames,height,width,channels]')
        if frame_ids is None:
            ids = torch.zeros(len(masks),dtype=torch.long) if len(m)==1 else torch.arange(len(masks))
            if len(m) not in (1,len(masks)):
                raise ValueError('Explicit frame_indices required')
        else:
            ids = torch.as_tensor(frame_ids,dtype=torch.long)
        if ids.shape != (len(masks),) or (ids<0).any() or (ids>=len(m)).any():
            raise ValueError('Invalid region frame indices')
        weights = F.interpolate(masks[:,None], size=m.shape[1:3], mode='area')[:,0]
        feats = m.detach().float().cpu()[ids]
        average = (feats*weights[...,None]).sum((1,2))/weights.sum((1,2)).clamp_min(1e-12)[:,None]
        result.append(F.normalize(average,dim=-1))
    return torch.cat(result,-1)


class FrozenEncoder:
    def __init__(self, model, kind, device='cpu', taps=TAPS, metadata=None):
        self.device = torch.device(device)
        self.model = model.eval().requires_grad_(False).to(self.device)
        self.kind, self.taps, self.metadata = kind, tuple(taps), metadata or {}

    @torch.inference_mode()
    def encode(self, pil_frames, size_hw, *, cpu_dtype=torch.float16):
        context = torch.autocast('cuda',dtype=torch.bfloat16) if self.device.type=='cuda' else nullcontext()
        with context:
            self.last_forward_context=dict(device=str(self.device),bf16_autocast=bool(
                self.device.type=='cuda' and torch.is_autocast_enabled('cuda') and
                torch.get_autocast_dtype('cuda')==torch.bfloat16))
            if self.kind in ('qwen_vit','vc_vit'):
                x, grid = pack_qwen(pixels(pil_frames,size_hw),
                                    self.model.config.patch_size,self.model.config.temporal_patch_size,
                                    self.model.config.spatial_merge_size)
                out, hooks = {}, []
                for k in self.taps:
                    def hook(module, inputs, value, k=k):
                        out[k] = value[0] if isinstance(value, tuple) else value
                    hooks.append(self.model.blocks[k-1].register_forward_hook(hook))
                try:
                    self.model(x.to(self.device),grid.to(self.device))
                finally:
                    for hook in hooks: hook.remove()
                maps = [unpack_qwen(out[k],grid,self.model.config.spatial_merge_size) for k in self.taps]
            else:
                maps = self.model.dense(pil_frames, size_hw)
        for m in maps:
            if m.ndim != 4 or len(m) != len(pil_frames) or not torch.isfinite(m).all():
                raise ValueError('Encoder emitted an invalid dense map')
        converted=[m.detach().to(device='cpu',dtype=cpu_dtype) for m in maps]
        if not all(torch.isfinite(m).all() for m in converted):
            raise ValueError('Encoder map overflow after output dtype cast')
        return converted


def _tensor_digest(state):
    h = hashlib.sha256()
    for k,v in sorted(state.items()):
        h.update(k.encode()); h.update(str(tuple(v.shape)).encode()); h.update(str(v.dtype).encode())
        h.update(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return h.hexdigest()


def load(arm, weights=None, device='cpu'):
    """Load a frozen arm. weights may be a path or an explicit configuration dict."""
    cfg = dict(weights) if isinstance(weights,dict) else ({'path':str(weights)} if weights else {})
    if arm in ('qwen_vit','vc_vit'):
        from safetensors import safe_open
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        config_path = Path(cfg.get('config',DEFAULT_BUNDLE/'base/config.json'))
        vcfg = Qwen3_5VisionConfig(**json.loads(config_path.read_text())['vision_config'])
        vcfg._attn_implementation = 'sdpa'
        with torch.device('meta'):
            model = Qwen3_5VisionModel(vcfg)
        path = Path(cfg.get('path',DEFAULT_T0/('full_weights' if arm=='qwen_vit' else 'heads.pt')))
        if arm == 'qwen_vit':
            index_path = path/'model.safetensors.index.json'
            index = json.loads(index_path.read_text())['weight_map']
            selected = {k:v for k,v in index.items() if k.startswith('model.visual.')}
            state = {}
            for filename in sorted(set(selected.values())):
                with safe_open(str(path/filename),framework='pt',device='cpu') as f:
                    for key in sorted(k for k,v in selected.items() if v==filename):
                        state[key.removeprefix('model.visual.')] = f.get_tensor(key)
            source = dict(index_sha256=sha256(index_path), weights_path=str(path))
        else:
            raw = torch.load(path,map_location='cpu',mmap=True,weights_only=True)
            state = {k.removeprefix('depth.model.visual.'):v for k,v in raw.items() if k.startswith('depth.model.visual.')}
            source = dict(weights_path=str(path))
        if not state:
            raise ValueError('No visual tensors found')
        source.update(selected_tensors_sha256=_tensor_digest(state),config_sha256=sha256(config_path))
        model.load_state_dict(state,strict=True,assign=True)
        rotary=model.rotary_pos_emb
        model.rotary_pos_emb=type(rotary)(dim=vcfg.hidden_size//vcfg.num_heads//2,theta=getattr(rotary,'theta',10000.))
        if any(b.is_meta for b in model.buffers()):
            raise ValueError('Qwen has an unmaterialized nonpersistent buffer')
        model.float()
        return FrozenEncoder(model,arm,device,metadata=source)
    from .providers import provider
    model, metadata = provider(arm,cfg,device)
    return FrozenEncoder(model,arm,device,taps=(),metadata=metadata)


def encode(arm, pil_frames, size_hw):
    if not isinstance(arm,FrozenEncoder):
        raise TypeError('Pass the handle returned by load(), not an unbound arm name')
    return arm.encode(pil_frames,size_hw)
