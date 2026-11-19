"""Exercise the native grounding loader with real sealed inputs and export files."""
from pathlib import Path
import base64,hashlib,json,os,sqlite3,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';O=B/'proofs/ground_runtime'
def offline(event,args):
    if event in ('socket.connect','socket.bind','socket.getaddrinfo'):
        raise PermissionError('CPU proof forbids network operations')
sys.addaudithook(offline)
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
monitor=Monitor(T)
import torch
from transformers import Qwen3_5ForConditionalGeneration
from student_pilot import carrier_c1_run as C,grounding_train as G,source_seal
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.p3_provenance import file_pin,load,digest,sha256
from tests.test_carrier_c1 import fixture
from tests.test_carrier_c1_run import RunnerTests
from tests.test_r2_data_path import TinyProcessor
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n');return file_pin(p)
kit=B/'kits/r1'
capsule=json.loads((kit/'k/7.json').read_text());raw=base64.b64decode(capsule['payload'],validate=True)
assert hashlib.sha256(raw).hexdigest()==capsule['sha256']
code=json.loads(raw);code['archive']['path']=str(kit/code['archive']['path'])
cfg=dict(schema='carrier-c1-run-v1',init='base',parallel='fsdp',all_frames=True,
    training_mode='final',frame_layout='duplicate',frame_markers=True,depth_enabled=True,
    depth_fov_source='pose_head',carrier_placement='append_after_temporal_group_video_tokens_v1',
    base_identity='fixture',trace_program_version='3.13',world_size=4,
    mix=['pose','vqa','pointing','routing'],code=write(O/'code.json',code),streams={})
cfg['scheduled_sampling']=load(L/'work/n1fix2/inputs/config.json')['scheduled_sampling']
db=O/'empty.db'
with sqlite3.connect(db) as connection:connection.execute('CREATE TABLE IF NOT EXISTS rows (row TEXT)')
assert sqlite3.connect(db).execute('SELECT count(*) FROM rows').fetchone()[0]==0
dbpin=file_pin(db);streams={}
for name in cfg['mix']:
    pin=write(O/(name+'.json'),dict(database=dbpin,count=0))
    cfg['streams'][name]=pin;streams[name]=dict(receipt=pin,database=dbpin,count=0,source_count=0)
cfg['recipe']=C.recipe_for(cfg)
tiny,_,_=fixture(4,training_mode='final')
camera=tiny.auxiliary_heads.pose.settings
depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=4,context_depth=1,vit_layers=[1,2,3])
model=CarrierC1(Qwen3_5ForConditionalGeneration(tiny.config).float(),camera,depth,5,
    cfg['carrier_placement'],'final',True,cfg['recipe'],frame_layout='duplicate',depth_fov_source='pose_head')
model.trace_program_version='3.13'
model_cfg=write(O/'model/config.json',model.config.to_dict())
manifest=write(O/'model.json',dict(root=str(O/'model'),files={'config.json':model_cfg['sha256']}))
identity=C.identity(cfg)
receipt=dict(schema='c1-preparation-v1',config_sha256=identity,trainer_commit=code['commit'],
    source_seal=source_seal.binding(code,identity),streams=streams,recipe=cfg['recipe'],model=manifest,
    camera=camera,depth=depth,**{k:cfg[k] for k in ('training_mode','frame_layout','frame_markers',
        'depth_enabled','depth_fov_source','carrier_placement','trace_program_version')})
cfg['preparation']=write(O/'preparation/receipt.json',receipt)
cfg['admission']=write(O/'admission.json',dict(verdict='PASS',reviewer='synthetic-cpu-fixture',
    config_sha256=identity,preparation=cfg['preparation']))
assert C.identity(cfg)==identity
config_pin=write(O/'config.json',cfg)
native_mkdir,native_open=Path.mkdir,Path.open
def retain(p,mode=0o777,parents=False,exist_ok=False):
    return native_mkdir(p,mode=mode,parents=parents,exist_ok=True if p.is_relative_to(O) else exist_ok)
def overwrite(p,mode='r',*args,**kwargs):
    return native_open(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*args,**kwargs)
with RunnerTests().local_collectives(),patch.object(Path,'mkdir',retain),patch.object(Path,'open',overwrite),\
        patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
    C.export(O/'m200',model,model,cfg,200)
runtime_cfg=dict(c1_config=config_pin,base_artifact=file_pin(O/'m200/artifact.json'),trace_program_version='3.13')
processor=TinyProcessor()
with patch.object(C,'processor_for_receipt',return_value=processor),patch.object(C,'load_model',return_value=model):
    loaded,actual_processor,native=G.load_runtime(runtime_cfg,torch.device('cpu'))
assert loaded is model and actual_processor is processor and native==cfg
assert loaded.readout_evaluation_config==cfg and not any(p.requires_grad for p in loaded.parameters())
record=dict(status='PASS',real_functions=['source_seal.verify','carrier_c1_run.prepared',
    'carrier_c1_run.export','carrier_c1_run.load_artifact','grounding_train.load_runtime'],
    source_seal=code['tree_sha256'],config=config_pin,artifact=runtime_cfg['base_artifact'],
    rows=0,config_forwarded=True,parameters_frozen=True,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    network='Audit hook refuses connect, bind and name resolution before system calls.',
    standins='Tiny native model and tokenizer replace pretrained loading; local collectives replace GPU transport. Preparation, source seal, artifact writer and readers run without stubs. Admission labels and the empty local store are synthetic.',
    limitations='No production admission, real scenes or GPU execution.')
(O/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');monitor.save(O);print(json.dumps(record))
