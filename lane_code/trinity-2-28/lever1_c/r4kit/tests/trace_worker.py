"""Record real worker imports through restore, loading, routed prompts and batch one.
Run on CPU only; the delivery's workload code is not rewritten.
"""
import sys
seen = set()
events = []
phase = 'fixture'
def audit(event, args):
    if event == 'import':
        seen.add(args[0]); events.append(dict(module=args[0], phase=phase))
sys.addaudithook(audit)
import os
from pathlib import Path
import json
import importlib.util
import types
import time
import hashlib
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    XDG_CACHE_HOME=str(ROOT/'out/cache'), HF_HOME=str(ROOT/'out/cache/hf'))
def mod(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value
sys.path.insert(0,str(mod('native_fixture',ROOT/'tests/native_fixture.py').prepare(ROOT)))
import torch
vision_fixture=torch.library.Library('torchvision','DEF')
vision_fixture.define('nms(Tensor dets, Tensor scores, float iou_threshold) -> Tensor')
t=mod('fixture',ROOT/'tests/test_fixes.py')
B,C,FILES,package=t.B,t.C,t.FILES,t.package
t.Fixes.setUpClass()
tests=types.ModuleType('tests'); tests.__path__=[str(ROOT/'in/D400/src/tree/tests')]; sys.modules['tests']=tests
from tests.test_carrier_c1_final import final_fixture, FakeTokenizer
tiny, _, _=final_fixture()
from student_pilot import carrier_c1_run as trainer
from student_pilot import pose_samples
from parity_kit import stage_restore
from e2e_reader import parity
from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
placement='append_after_temporal_group_video_tokens_v1'
model_receipt=dict(camera=dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
    weight_gravity=.05,weight_scale=.02,supervision={'path':'/fixture','sha256':'a'*64}),
    depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=4,context_depth=1,vit_layers=[1,2,3]),
    carrier_placement=placement,training_mode='final',depth_enabled=True,
    recipe=trainer.RECIPE if hasattr(trainer,'RECIPE') else __import__('student_pilot.carrier_c1',fromlist=['RECIPE']).RECIPE,
    depth_fov_source='pose_head', trace_program_version='3.14')
p,cfg,_=package();d=p/'d';d.mkdir();cfg['logical']=str(p)
cfg['inputs']['frames_root']=str(d/'f');(d/'f').mkdir()
(d/'f/0').write_bytes(b'0')
data=C.loads(FILES['1.json'])
for cap in data['captures'].values():
    for f in cap['frames']:f.update(path='0',sha256=hashlib.sha256(b'0').hexdigest())
C.store(p/'1.json',data);C.store(p/'2.json',cfg)
# Build a tiny authenticated export; the real restore verifies every
# hash/size and writes its normal metadata through the opaque Path view.
base=d/'b';base.mkdir();weights=d/'m400/full_weights';weights.mkdir(parents=True)
def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=B.jd(value);path.write_bytes(C.pack(raw));return dict(bytes=len(raw),sha256=B.digest(raw))
asset_names=('config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json')
assets={}
for name in asset_names:
    raw=B.jd(tiny.config.to_dict()) if name=='config.json' else b'{}'
    (base/name).write_bytes(raw);assets[name]=B.digest(raw)
original=B.jd(dict(schema='p3-model-input-v1',base_identity='a',files=assets))
archive=d/'o/0.tgz';archive.parent.mkdir();archive.write_bytes(B.archive({'model.json':original}))
from safetensors.torch import save_file
from student_pilot import full_ft
state={k:v.detach().to(torch.bfloat16).clone().contiguous() for k,v in full_ft.base_parameters(tiny)}
save_file(state,str(weights/'0.bin'))
index=dict(weight_map={k:'0.bin' for k in state})
ix=put(weights/'0.json',index)
full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='0.bin',**B.pin((weights/'0.bin').read_bytes()))],
          index=dict(name='0.json',**ix),tensor_count=len(state))
fp=put(weights/'full_weights.json',full)
torch.save(tiny.auxiliary_heads.state_dict(), d/'m400/heads.pt')
artifact=dict(config_sha256='a'*64,base_identity='a',frame_layout='duplicate',
              full_weights=dict(sha256=fp['sha256']),heads=dict(sha256=B.digest((d/'m400/heads.pt').read_bytes())))
ap=put(d/'m400/artifact.json',artifact)
receipt=dict(config_sha256='a'*64,frame_layout='duplicate',**model_receipt,
             model=dict(path='/a',sha256=B.digest(original)))
rp=put(d/'p0/receipt.json',receipt)
config=dict(base_identity='a',frame_layout='duplicate',carrier_placement=placement,training_mode='final',preparation=dict(path='/a',sha256=rp['sha256']))
cp=put(d/'p0/config.json',config)
data_receipt=dict(status='PREPARED',schema='s1-in-job-data-v1',config=dict(path='/b',sha256=cp['sha256']),
                  preparation=config['preparation'],real_frames_verified=True,rehearsal=False)
dp=put(d/'p0/data_receipt.json',data_receipt)
pins=dict(artifact=ap,preparation={name:dict(path='p0/'+filename,source_path=source,**pin) for name,filename,source,pin in
    [('config','config.json','/b',cp),('receipt','receipt.json','/a',rp),('data_receipt','data_receipt.json','/c',dp)]})
for name,path in [('full_weights',weights/'full_weights.json'),('artifact',d/'m400/artifact.json'),
                  ('base_config',base/'config.json'),('original_model',archive)]:
    cfg['inputs']['files'][name]['path']=str(path)
C.store(p/'2.json',cfg)
real_stage=stage_restore.stage
def preparation(*args,**kw):
    kw['export_pins']=pins
    return real_stage(*args,**kw)
class Tokenizer(FakeTokenizer):
    pad_token_id=0
    def __init__(self): self.vocab={'<|fim_middle|>':5,'<|video_pad|>':61,'<|vision_start|>':62,'<|vision_end|>':63}
    def encode(self,text,**kw):
        return [self.vocab[text]] if text in self.vocab else super().encode(text,**kw)
    def get_vocab(self): return self.vocab
    def add_tokens(self, tokens):
        for token in tokens: self.vocab[str(token)]=32+len(self.vocab)
    def convert_tokens_to_ids(self, token):
        return self.vocab.get(token, super().convert_tokens_to_ids(token))
    def decode(self, ids, skip_special_tokens=False): return ''.join('x'+str(i)+' ' for i in ids)
def processor(*a,**kw):
    from transformers import Qwen3VLProcessor, Qwen3VLVideoProcessor, Qwen2VLImageProcessor, Qwen2Tokenizer
    native=Qwen3VLProcessor(tokenizer=Qwen2Tokenizer(),
        image_processor=Qwen2VLImageProcessor(), video_processor=Qwen3VLVideoProcessor())
    native.tokenizer=Tokenizer()  # Deterministic tiny vocabulary for the native model.
    return native
def encode_frames(*a,**kw):
    ids=torch.tensor([[2]+[v for _ in range(32) for v in (62,61,63)]+[10,11,12,13]])
    result=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=torch.full_like(ids,-100),
        mm_token_type_ids=torch.where(ids==61,2,0),video_grid_thw=torch.tensor([[32,2,2]]),
        pixel_values_videos=torch.zeros((128,24)))
    result['labels'][0,-2:]=ids[0,-2:]
    return result, {}
real_load=parity.load_native
real_to=torch.Tensor.to
runtime=mod('worker',p/'5.py')
real_batches=runtime.run_batches
stages=[]
def first_batch(out, rows, progress, end, prepare_rows, generate, deadline):
    global phase
    phase='first_batch'; stages.append(phase)
    return real_batches(out,rows[:8],progress,end,prepare_rows,generate,deadline)
def loading(*args,**kw):
    global phase
    phase='model_load'; stages.append(phase); kw['device']='cpu'
    return real_load(*args,**kw)
def cpu_to(self,*args,**kw):
    if args and isinstance(args[0],str) and args[0]=='cuda:0': args=('cpu',)+args[1:]
    return real_to(self,*args,**kw)
native_dir=p/'tiny_native'; native_dir.mkdir()
Qwen3_5ForConditionalGeneration(tiny.config).float().save_pretrained(native_dir)
real_pretrained=Qwen3_5ForConditionalGeneration.from_pretrained
real_artifact=trainer.load_artifact
real_read=trainer.load
def pretrained(*a,**kw):
    kw['dtype']=torch.float32
    return real_pretrained(native_dir,**kw)
def artifact(model,artifact_pin):
    from student_pilot import trained_groups
    state=tiny.auxiliary_heads.state_dict()
    groups={name:dict(names=sorted(values),initial_sha256='0'*64,
        final_sha256=trained_groups.fingerprint({k:state[k] for k in values})[0],
        changed=True,gradient_steps=1) for name,values in trained_groups.parameters(model).items()}
    def metadata(path):
        value=real_read(path)
        if str(path)==artifact_pin['path']:
            value.update(schema='carrier-c1-artifact-v1',pose_backing='lm_final_norm',
                placement=model.carrier_placement,training_mode=model.training_mode,
                frame_layout=model.frame_layout,depth_backing='tiny',
                config_sha256=trainer.identity(config),trace_program_version='3.14',step=400,
                trained_groups=dict(schema=trained_groups.SCHEMA,step=400,groups=groups))
        return value
    with patch.object(trainer,'load',side_effect=metadata):
        value=real_artifact(model,artifact_pin)
    model.float()  # CPU tiny decode uses float32 after validating the BF16 export.
    return value
# Patching these boundaries leaves the production restore, processor binding,
# model constructor, prompt encoder, prefill/cache merge and decode loop live.
phase='restore'; stages.append(phase)
import numpy as np
with patch.object(stage_restore,'stage',side_effect=preparation), \
     patch.object(AutoProcessor,'from_pretrained',side_effect=processor), \
     patch.object(Qwen3_5ForConditionalGeneration,'from_pretrained',side_effect=pretrained), \
     patch.object(trainer,'load_artifact',side_effect=artifact), \
     patch.object(pose_samples,'load_frames',return_value=np.zeros((32,4,4,3),dtype=np.uint8)), \
     patch.object(pose_samples,'encode_frames',side_effect=encode_frames), \
     patch.object(parity,'load_native',side_effect=loading), \
     patch.object(torch.Tensor,'to',cpu_to), \
     patch.object(runtime,'run_batches',side_effect=first_batch):
    runtime.run(p,'g',time.time()+180)
summary=C.loads((p/'a/1.json').read_bytes())
assert summary['records']==8, summary
assert 'student_pilot.carrier_c1_canary' in seen
batch=C.loads((p/'a/3.jsonl').read_bytes().splitlines()[0])
assert batch['status']=='complete' and batch['steps']>1, batch
modules={n:str(getattr(m,'__file__','') or '') for n,m in sys.modules.items()}
output=dict(passed=True,stages=stages,events=events,modules=modules,
    spec_names={n:getattr(getattr(m,'__spec__',None),'name',n) for n,m in sys.modules.items()},
    audit_modules=sorted(seen),records=summary['records'],batch=batch,
    method='sys.addaudithook(import) plus successful sys.modules inventory; delivered runtime.run(g) on CPU',
    doubles=['tiny authenticated export and meta head-shape proof','AutoProcessor asset boundary constructs native Qwen3VLProcessor with tiny tokenizer',
        'from_pretrained redirects to saved tiny native checkpoint','tiny artifact metadata and trained-group contract',
        'CPU decode uses float32 after real BF16 export loading',
        'load_frames and encode_frames RGB/tokenizer doubles','cuda:0 tensor/model transfers redirected to CPU',
        'run_batches restricted to first eight rows','unused torchvision NMS schema'],
    real=['runtime.run','stage_restore.stage','stage_restore.prove_depth','stage_restore.depth_shapes',
        'processor_for_receipt','load_native','trainer.load_model','trainer.load_artifact','full_ft.load_export',
        'Qwen3_5ForConditionalGeneration.from_pretrained','evalpath.prompt_batch',
        'carrier_c1_canary.prompt_batch','carrier_c1_data.encode','carrier_c1_data.encode_layout_row',
        'runtime.run_batches','batch.generate','_prepare_decode','consume_cache_tokens'],
    source_delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()))
(ROOT/'out/WORKER_IMPORT_TRACE.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(passed=True,modules=len(modules),audit_modules=len(seen),records=summary['records'])))
