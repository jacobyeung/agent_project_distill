"""Optional local providers. Missing source, pins, or weights cause an explicit refusal."""
import importlib
import json
import re
import sys
from pathlib import Path
import torch
from torch import nn
from .core import pixels
from provenance import sha256


def quarter_layers(depth):
    if depth<4: raise ValueError('Encoder needs at least four blocks')
    return tuple((depth*i+3)//4 for i in range(1,5))


def token_grid(out, frames, h, w, patch, prefix):
    count=(h//patch)*(w//patch)
    if out.ndim!=3 or out.shape[:2]!=(frames,count+prefix):
        raise ValueError('Special-token count or spatial grid differs')
    return out[:,-count:].reshape(frames,h//patch,w//patch,-1)


def pinned_local(path, custom=False):
    root=Path(path).resolve()
    if not str(root).startswith('/scratch/'):
        raise ValueError('Encoder code/weights must be staged on /scratch')
    pin=root/'LOCAL_PIN.json'
    value=json.loads(pin.read_text())
    if not re.fullmatch('[0-9a-f]{40}',value.get('revision','')):
        raise ValueError('LOCAL_PIN.json requires a full pinned revision')
    for filename,expected in value['files'].items():
        p=(root/filename).resolve()
        if root not in p.parents or sha256(p)!=expected:
            raise ValueError(f'Local encoder pin differs: {p}')
    for p in root.rglob('*'):
        if p.is_file() and p.name!='LOCAL_PIN.json' and p.suffix in ('.json','.safetensors','.bin','.py'):
            if str(p.relative_to(root)) not in value['files']:
                raise ValueError(f'Unpinned encoder input: {p}')
    if custom:
        for p in root.rglob('*.py'):
            if str(p.relative_to(root)) not in value['files']:
                raise ValueError(f'Unpinned custom code: {p}')
    return root,value


class HFProvider(nn.Module):
    def __init__(self,model,processor,arm):
        super().__init__(); self.net=model; self.processor=processor; self.arm=arm

    def dense(self,frames,size_hw):
        h,w=size_hw
        patch=int(self.net.config.patch_size)
        if h%patch or w%patch: raise ValueError(f'{self.arm} dimensions must divide patch {patch}')
        x=pixels(frames,size_hw,self.processor.image_mean,self.processor.image_std).to(next(self.net.parameters()).device)
        states=self.net(pixel_values=x,output_hidden_states=True).hidden_states
        depth=int(self.net.config.num_hidden_layers)
        if len(states)!=depth+1: raise ValueError('HF hidden states must include the embedding layer')
        prefix=1+int(getattr(self.net.config,'num_register_tokens',0))
        return [token_grid(states[k],len(frames),h,w,patch,prefix) for k in quarter_layers(depth)]


class RadioProvider(nn.Module):
    def __init__(self,model): super().__init__(); self.net=model
    def dense(self,frames,size_hw):
        if any(s%32 for s in size_hw): raise ValueError('RADIO size must be a multiple of 32')
        x=pixels(frames,size_hw,mean=(0,0,0),std=(1,1,1)).to(next(self.net.parameters()).device)
        # RADIO's underlying timm ViT emits prefix tokens followed by raster patches.
        trunk=getattr(self.net,'radio_model',self.net).model
        blocks=trunk.blocks;layers=quarter_layers(len(blocks));captured={};hooks=[]
        for k in layers:
            def hook(module,args,out,k=k): captured[k]=out
            hooks.append(blocks[k-1].register_forward_hook(hook))
        try: result=self.net(x)
        finally:
            for hook in hooks: hook.remove()
        if not isinstance(result,dict) or not {'backbone','sam3'}<=set(result):
            raise ValueError('Pinned RADIO must return backbone and sam3 adaptor')
        # The adaptor is checked but is not an extra feature stream/head capacity.
        h,w=size_hw;prefix=int(trunk.num_prefix_tokens)
        patch=trunk.patch_embed.patch_size
        patch=int(patch[0] if isinstance(patch,(tuple,list)) else patch)
        if patch!=16: raise ValueError('Pinned RADIO patch must be 16')
        return [token_grid(captured[k],len(frames),h,w,patch,prefix) for k in layers]


class SamProvider(nn.Module):
    def __init__(self,model): super().__init__(); self.net=model
    def dense(self,frames,size_hw):
        # The PE trunk supports dynamic sizes only on multiples of its 14-pixel patch.
        if tuple(size_hw)!=(1008,1008): raise ValueError('SAM PE input must be 1008 square')
        x=pixels(frames,size_hw).to(next(self.net.parameters()).device)
        layers=quarter_layers(len(self.net.blocks));captured={};hooks=[]
        for k in layers:
            def hook(module,args,out,k=k): captured[k]=out
            hooks.append(self.net.blocks[k-1].register_forward_hook(hook))
        try: self.net(x)
        finally:
            for hook in hooks: hook.remove()
        maps=[captured[k] for k in layers]
        if any(m.ndim!=4 or m.shape[:3]!=(len(frames),72,72) for m in maps):
            raise ValueError('SAM PE block outputs must be NHWC on the 72 x 72 grid')
        return maps


def provider(arm,cfg,device):
    if arm=='g3t':
        import g3t_taps
        return g3t_taps.load(cfg,device)
    if arm in ('dinov3_vitl16','dinov2_vitl14_reg','cradio_v4_so400m'):
        from transformers import AutoModel,AutoImageProcessor
        root,pin=pinned_local(cfg['path'],custom=arm=='cradio_v4_so400m')
        if arm=='cradio_v4_so400m':
            model=AutoModel.from_pretrained(str(root),local_files_only=True,trust_remote_code=True,
                                           adaptor_names=['sam3'])
            trunk=getattr(model,'radio_model',model).model
            return RadioProvider(model),dict(pin,taps=list(quarter_layers(len(trunk.blocks))),index_base=1,normalization='RADIO internal input conditioner; caller [0,1]')
        model=AutoModel.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
        processor=AutoImageProcessor.from_pretrained(str(root),local_files_only=True)
        return HFProvider(model,processor,arm),dict(pin,taps=list(quarter_layers(model.config.num_hidden_layers)),index_base=1,patch_size=model.config.patch_size,image_mean=processor.image_mean,image_std=processor.image_std)
    if arm=='sam3_pe':
        source=Path(cfg['source_root']).resolve()
        if not str(source).startswith('/scratch/'):
            raise ValueError('SAM source must be a local /scratch copy')
        receipt=json.loads(Path(cfg['receipt']).read_text())
        for key,pin in receipt['source_files'].items():
            if sha256(source/key)!=pin: raise ValueError(f'SAM source mismatch: {key}')
        if sha256(cfg['path'])!=receipt['checkpoint_sha256']: raise ValueError('SAM checkpoint mismatch')
        if 'sam3' in sys.modules and Path(sys.modules['sam3'].__file__).resolve().parent!=source/'sam3':
            raise ValueError('Another SAM source is already imported')
        sys.path.insert(0,str(source))
        from sam3.model_builder import build_sam3_image_model
        model=build_sam3_image_model(checkpoint_path=cfg['path'],load_from_HF=False,device='cpu',
                                    eval_mode=True,enable_inst_interactivity=False)
        trunk=model.backbone.vision_backbone.trunk
        return SamProvider(trunk),dict(receipt,taps=list(quarter_layers(len(trunk.blocks))),index_base=1,input_hw=[1008,1008],patch_size=14)
    raise ValueError(f'Unknown encoder arm: {arm}')
