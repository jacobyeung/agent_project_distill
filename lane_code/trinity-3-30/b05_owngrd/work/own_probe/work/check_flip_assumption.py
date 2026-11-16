"""Counterexample to mandatory input-flip equivariance in a learned-position ViT."""
import numpy as np
import torch
from PIL import Image
from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
from own_feats.core import FrozenEncoder,pool
from probe_common import ROOT
from provenance import write_json

def run():
    torch.set_num_threads(4);torch.manual_seed(17)
    cfg=Qwen3_5VisionConfig(depth=4,hidden_size=32,intermediate_size=64,num_heads=4,patch_size=2,temporal_patch_size=2,spatial_merge_size=2,out_hidden_size=32,num_position_embeddings=16)
    cfg._attn_implementation='sdpa';enc=FrozenEncoder(Qwen3_5VisionModel(cfg),'qwen_vit',taps=(1,2,3,4))
    im=Image.fromarray(np.random.default_rng(17).integers(0,256,(16,24,3),dtype=np.uint8))
    a=enc.encode([im],(16,24),cpu_dtype=torch.float32);b=enc.encode([im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)],(16,24),cpu_dtype=torch.float32)
    left=torch.zeros(1,16,24);left[:,:,:12]=1;right=left.flip(-1)
    x=pool(a,right);y=pool(b,left);mapped=pool([m.flip(2) for m in a],left)
    error=float((x-y).abs().max());spatial=float((x-mapped).abs().max())
    assert error>1e-4 and spatial<1e-6
    write_json(ROOT/'out/FLIP_COUNTEREXAMPLE.json',dict(input_flip_max_abs=error,map_flip_max_abs=spatial,seed=17,model='CPU tiny Qwen3.5 vision architecture, random frozen weights',conclusion='Learned positions do not guarantee input-flip equivariance. Provider stubs and the exact map-flip pool invariant test raster alignment.'))
    print(error,spatial)
if __name__=='__main__':run()
