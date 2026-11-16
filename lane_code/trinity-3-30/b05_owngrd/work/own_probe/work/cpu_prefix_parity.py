"""Compare O2 with MDG's unchanged capture_prefix using an LM-free prefill fixture."""
import argparse
import ast
from dataclasses import dataclass
import json
import re
from pathlib import Path
from types import SimpleNamespace
from contextlib import AbstractContextManager
import numpy as np
from PIL import Image
import torch
from torch import nn
from own_feats import load,pack_qwen,FrozenEncoder
from own_feats.core import pixels
from provenance import receipt,write_json,sha256
from probe_common import ROOT,O


def definitions(path,names,ns):
    tree=ast.parse(Path(path).read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if len(nodes)!=len(names):raise ValueError('Reference definitions missing')
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)


def run(a):
    torch.set_num_threads(4);torch.manual_seed(17)
    source=O/'mdg_build/work/c1mix_mdg/student_pilot'
    ns=dict(torch=torch,dataclass=dataclass,re=re,AbstractContextManager=AbstractContextManager,TAP_LAYERS=(16,24),VIT_BLOCKS=(9,17,25))
    definitions(source/'point_depth_head.py',{'vit_blocks','vit_layer_hooks','vit_grids_by_row'},ns)
    definitions(source/'grounding_features.py',{'ClipFeatures','FeatureCapture','frame_token_index'},ns)
    ns['gh']=SimpleNamespace(FeatureCapture=ns['FeatureCapture'])
    definitions(source/'mdg_features.py',{'PrefixFeatures','capture_prefix','unpatchify'},ns)
    if a.real:
        encoder=load('qwen_vit',device='cpu')
    else:
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        cfg=Qwen3_5VisionConfig(depth=27,hidden_size=32,intermediate_size=64,num_heads=4,patch_size=16,
                              temporal_patch_size=2,spatial_merge_size=2,out_hidden_size=32,num_position_embeddings=16)
        cfg._attn_implementation='sdpa';encoder=FrozenEncoder(Qwen3_5VisionModel(cfg),'qwen_vit')
    encoder.taps=(9,17,25,27)  # Reference MDG capture contract, independent of probe taps.
    array=np.random.default_rng(17).integers(0,256,size=(320,448,3),dtype=np.uint8)
    image=Image.fromarray(array)
    from transformers.models.qwen2_vl.image_processing_pil_qwen2_vl import Qwen2VLImageProcessorPil
    cfg=json.loads((O/'mdg_build/work/t0bundle/base/preprocessor_config.json').read_text())
    processor=Qwen2VLImageProcessorPil(patch_size=16,temporal_patch_size=2,merge_size=2,image_mean=cfg['image_mean'],image_std=cfg['image_std'])
    reference_inputs=processor(images=[image],do_resize=False,return_tensors='pt')
    packed=torch.as_tensor(reference_inputs['pixel_values']);grid=torch.as_tensor(reference_inputs['image_grid_thw'])
    model=nn.Module();model.model=nn.Module();model.model.visual=encoder.model
    model.model.language_model=nn.Module();model.model.language_model.layers=nn.ModuleList([nn.Identity() for _ in range(26)])
    model.model.language_model.norm=nn.Identity();model.model.rope_deltas=torch.zeros(1,1)
    model.config=SimpleNamespace(vision_config=encoder.model.config,video_token_id=7);model.eval()
    count=int(grid[0,1]*grid[0,2]//4)
    batch=dict(input_ids=torch.tensor([[1]+[7]*count+[2]]),video_grid_thw=grid,pixel_values_videos=packed,
               mm_token_type_ids=torch.tensor([[0]+[2]*count+[0]]))
    def prefill(model,batch,native):
        model.model.visual(batch['pixel_values_videos'],batch['video_grid_thw'])
        hidden=torch.zeros(1,count+2,8)
        for layer in model.model.language_model.layers:hidden=layer(hidden)
        model.model.language_model.norm(hidden)
        return SimpleNamespace(past_key_values=None)
    ns['_native']=lambda m:None;ns['_prefill']=prefill
    with torch.no_grad():
        reference=ns['capture_prefix'](model,batch)
        got=encoder.encode([image],(320,448),cpu_dtype=torch.float32)
    diffs=[float(((x-y).abs()/y.abs().clamp_min(1e-8)).max()) for x,y in zip(got[:3],reference.vit)]
    if not all(x<1e-4 for x in diffs):raise AssertionError(diffs)
    # capture_prefix exposes blocks 9/17/25 only; block 27 has an independent merger-input test.
    final=[];hook=encoder.model.merger.register_forward_pre_hook(lambda m,args:final.append(args[0].detach()))
    with torch.no_grad():encoder.model(packed,grid)
    hook.remove();ref27=ns['vit_grids_by_row'](final[0],grid,2)[0]
    finaldiff=float(((got[-1]-ref27).abs()/ref27.abs().clamp_min(1e-8)).max())
    if finaldiff>=1e-4:raise AssertionError(finaldiff)
    value=dict(status='PASS',real_t0_visual_weights=a.real,size_hw=[320,448],frames=1,dtype='float32',
               capture_prefix_blocks=[9,17,25],max_relative_difference=diffs,block27_vs_merger_input=finaldiff,
               limit='The prefill fixture exercises MDG capture and the real vision tower; no 9B LM forward runs.',
               weights=encoder.metadata,provenance=receipt([source/'mdg_features.py',source/'grounding_features.py',source/'point_depth_head.py'],
                                                        [Path(__file__),ROOT/'work/own_feats/core.py'],vars(a)))
    write_json(a.out,value);print(json.dumps({k:value[k] for k in ('status','real_t0_visual_weights','max_relative_difference','block27_vs_merger_input')}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--real',action='store_true');p.add_argument('--out',required=True);run(p.parse_args())
