"""Operator dispatch for one distance read within one allocation."""
import json,sys,time,hashlib
from pathlib import Path

RULES=('candidates_argmax',)
COUNTS=(0,0,0,580,0)
SCHEDULE=((0,3),)

def descriptors(package):
 return [dict(arm='tower',modes=['none'],stage1_select_rule='candidates_argmax',save_own_depth=False,
              perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
              types=[3],expected=580)]

def sealed_write(path,value):
 from orchard_h10.common import write
 if path.exists() and json.loads(path.read_text())!=value:raise ValueError('Read identity differs')
 write(path,value)

def prepare(config):
 from orchard_h10.common import ORDER,canonical
 base=Path(config['output']);settings=json.loads(Path(config['settings']).read_text())
 if config.get('optional'):raise ValueError('Unexpected optional input')
 from e2e_reader.perception_memo import settings as memo_settings
 memo_settings(settings,required=True)
 if settings['stage1_select_rule'] not in RULES:raise ValueError('unknown_stage1_select_rule')
 specs=descriptors(config['package']);identity=dict(plan=config['plan_sha256'],inputs=config['inputs_sha256'],
   operator_sha256=config['operator_sha256'],cards=1,reads=specs,schedule=SCHEDULE)
 # JSON roundtrip gives a stable list representation for resume checks.
 identity=json.loads(json.dumps(identity));sealed_write(base/'metadata/IDENTITY.json',identity)
 configs={}
 for i,spec in enumerate(specs):
  root=base/'metadata/reads'/str(i)
  chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False,
          'types':[ORDER[t] for t in spec['types']],**{k:spec[k] for k in ('perception_memo','perception_memo_verify_ids','perception_memo_modules')}}
  path=root/'metadata/0.json';sealed_write(path,chosen)
  sealed_write(root/'metadata/READ_IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  configs[i]={**config,'items':str(Path(config['package'])/'items/dist580.json'),'output':str(root),'settings':str(path),
      'cache_root':str(base/'cache'/str(i)), 'stop_file':str(base/'metadata/STOP'),
      'single_worker':True,'arms':['tower'],'modes':['none'],'types':[ORDER[t] for t in spec['types']],
      'stage1_select_rule':spec['stage1_select_rule'],
      'stop_margin':1800,'return_margin':1200,**memo_settings(chosen)}

 return configs

def rehearsal(config):
 from orchard_h10.runner import control,worker_args
 from orchard_h10.common import ORDER
 configs=prepare(config);result=[]
 for i,cfg in configs.items():
  t=ORDER.index(cfg['types'][0])
  control(cfg)
  args=worker_args(dict(config=cfg,type=t,index=0,cards=1,stop_at=1,finish_by=2))
  assert args[args.index('--arms')+1]=='tower'
  assert args[args.index('--modes')+1]=='none'
  assert args[args.index('--types')+1]==','.join(cfg['types'])
  assert args[args.index('--stop-file')+1]==str(Path(config['output'])/'metadata/STOP')
  assert json.loads(Path(args[args.index('--settings')+1]).read_text())['stage1_select_rule']==RULES[i]
  chosen=json.loads(Path(args[args.index('--settings')+1]).read_text())
  assert chosen['perception_memo']=='on'
  assert chosen['perception_memo_verify_ids']==descriptors(config['package'])[i]['perception_memo_verify_ids']
  result.append(dict(read=i,types=cfg['types'],args=args,settings=chosen,expected=580))
 # Exercise each selected rule through the real tower socket with stub weights.
 from unittest.mock import patch
 from types import SimpleNamespace
 import torch
 from e2e_reader import stage1,real
 for rule in RULES:
  made=[]
  def init(obj,detect,head,geometry,rule='candidates_argmax'):
   obj.rule=rule;obj.head=head;obj.diagnostics={};made.append(obj)
  head=SimpleNamespace(with_null=lambda *a:torch.tensor([1.,2.,100.]))
  with patch.object(stage1.StageOne,'__init__',init),patch.object(real,'TowerG3T',return_value=None),patch('e2e_reader.geometry.frame_count',return_value=32):
   value=real.real_perception(None,device='cpu',perception_memo_modules=['g3t'],sam3_tower=object(),selector_head=head,stage1_select_rule=rule)
   value.socket(None,None)
  assert made[0].rule==rule
  assert made[0].select(dict(x=torch.zeros(2,58),name='x'))==1
 if config.get('measure_memory'):
  result[0]['full_reader']=full_reader_rehearsal(configs[0])
 return result

def full_reader_rehearsal(config):
 """Exercise staged RGBs and the real reader with deterministic CPU model stubs."""
 from contextlib import ExitStack
 from types import SimpleNamespace as NS
 from unittest.mock import patch
 import numpy as np
 import torch
 from PIL import Image
 from e2e_reader import parity,real
 from student_pilot import sam3_tower,carrier_c1_decode as decode,tower_read
 from h1eval.h10 import launch,parity_adapter
 from h1eval.items import load_manifest
 from evalpath import runtime
 from evalpath.run import score_item
 from orchard_h10.common import write,sha
 if config.get('device')!='cpu':raise ValueError('CPU rehearsal requires CPU')
 package=Path(config['package'])
 manifest=load_manifest(package/'items/dist580.json')
 settings=json.loads(Path(config['settings']).read_text())
 expected=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
   perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,
   types=['object_abs_distance'])
 if any(settings.get(k)!=v for k,v in expected.items()):raise ValueError('Rehearsal settings differ')
 # Never fabricate a restore or alter the staged settings in the allocated check.
 if not (Path(config['export'])/'RESTORE.json').is_file():raise ValueError('Restore is absent')
 root=Path(config['output'])/'metadata/full_reader'
 root.mkdir(parents=True,exist_ok=False)
 class Budget:
  def __init__(self,*a,**k):pass
  def __call__(self,*args):return args[-1]
  def receipt(self,*a):return {'cpu_stub':True}
 class Tokenizer:
  chunks=['<think>','</think><answer>21.52</answer>']
  eos_token_id=2
  def convert_tokens_to_ids(self,t):return 3 if t=='<tool_response>' else 4
  def encode(self,s,**kw):return [1000+x for x in s.encode()]
  def decode(self,ids,**kw):return ''.join(self.chunks[i-10] if 10<=i<12 else chr(i-1000) if i>=1000 else '' for i in ids)
 def logits(i):
  z=torch.full((1,1,1300),-100.);z[0,0,10+i if i<2 else 2]=100.
  return NS(logits=z,past_key_values=None)
 reports=[]
 for ordinal,name in enumerate(('R0-dev-reworded','R0-dev-twin')):
  item=next(r for r in manifest['items'] if r['id'] in manifest['sets'][name])
  index=manifest['items'].index(item);journal=root/str(ordinal)
  args=launch.parser().parse_args(['--items',str(package/'items/dist580.json'),
    '--export',config['export'],'--artifact-manifest',config['binding'],
    '--reader-root',str(package/'b'),'--out',str(journal),'--export-pin',config['export_pin'],
    '--settings',config['settings'],'--types','object_abs_distance','--arms','tower',
    '--modes','none','--device','cpu','--shard',f'{index}/{len(manifest["items"])}','--type-journals'])
  art=NS(manifest=dict(components={k:dict(files=[dict(rel=k+'/weights',
    sha256=hashlib.sha256(k.encode()).hexdigest(),bytes=1)]) for k in ('g3t','sam3')}),
    allowed=set(),env_roots=(),write_roots=(),code=set())
  art.verify=lambda:art
  art.files=lambda component:[Path(settings['sam3'][k]).resolve() for k in ('checkpoint_path','receipt_path')]+[Path('model.safetensors'),Path('config.json')]
  proc=NS(tokenizer=Tokenizer(),_routing_tokens={'ids':{}});model=NS();loads=[];seq=[0];seen=[]
  def load(*a,**k):
   if k.get('device')!='cpu':raise ValueError('Model stub requires CPU')
   loads.append(1);return model,proc,{'config':{},'export':{'frame_layout':'duplicate'}}
  def prefill(*a,**k):
   seq[0]=0
   heads=NS(pose9=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1)),gravity=np.array([0.,-1.,0.]),
     depth_map=torch.ones(32,1,1,1),depth_head=NS(query=lambda d,uv:torch.full(uv.shape[:2],3.)))
   return NS(heads=heads,native=NS(generation_config=NS(eos_token_id=2)),cap=10000,stream=None,output=logits(0))
  def consume(*a,**k):seq[0]+=1;return logits(seq[0]),None
  def prompt(processor,row,*a):
   si=row['student_input']
   if si['question']!=item['question'] or si['frame_indices']!=item['source_frame_indices']:
    raise ValueError('Prompt item binding differs')
   for f in si['frames']:
    digest=sha(f['path'])
    if digest!=f['sha256']:raise ValueError('Prompt frame SHA256 differs')
    with Image.open(f['path']) as im:
     im.load();seen.append(dict(path=f['path'],sha256=digest,size=list(im.size)))
   return dict(input_ids=torch.ones(1,1,dtype=torch.long),attention_mask=torch.ones(1,1,dtype=torch.long))
  original_audit=real.Audit
  with ExitStack() as stack:
   stubs=[patch.object(parity,'install',lambda *a:None),patch.object(parity,'Artifact',lambda *a,**k:art),
    patch.object(parity,'load_native',load),patch.object(parity,'install_hook',lambda m,h:h),
    patch.object(parity,'_head',lambda *a:NS()),patch.object(parity,'policy',lambda:NS(ThinkingBudget=Budget,DECODE_BUDGET=1)),
    patch.object(sam3_tower,'Sam3Tower',lambda *a:NS()),patch.object(runtime,'prompt_batch',prompt),
    patch.object(tower_read,'FrozenG3TTower',side_effect=AssertionError('Direct distance stub must not invoke G3T')),
    patch.object(decode,'_prepare_decode',prefill),patch.object(decode,'consume_cache_tokens',consume),
    patch.object(real,'Audit',lambda a,**k:original_audit(a,enforce=False))]
   for stub in stubs:stack.enter_context(stub)
   result=launch.run_types(args,make_real=parity_adapter.make_capped_real)
  rows=launch.read_records(journal/'3'/str(index)/'items.jsonl')
  if result['completed']!=1 or len(rows)!=1 or len(loads)!=1 or len(seen)!=32:
   raise ValueError('Full reader did not complete exactly one item')
  row=rows[0];output=row['output']
  if (row['id']!=item['id'] or row['complete'] is not True or row['type']!='object_abs_distance'
      or row['arm']!='tower' or row['mode']!='none' or output['finish']!='eos'
      or output['calls']['records']!=[] or output['tokens']!=[10,11,2]):
   raise ValueError('Full reader finished record differs')
  score=score_item({**item,'ground_truth':item.get('answer',item['ground_truth'])},parity.decoded(output))
  ground_truth_score=score_item(item,parity.decoded(output))
  if score['parse_failed'] or output['scores']['answer']!=score['score']:
   raise ValueError('Official score differs')
  environment=json.loads((journal/'3'/str(index)/'environment.json').read_text())
  if any(environment['binding'].get(k)!=v for k,v in expected.items()):
   raise ValueError('Full reader type or settings binding differs')
  reports.append(dict(passed=True,set=name,item=item['id'],frames=seen,record=row,
    official_score=score,ground_truth_score=ground_truth_score,environment_binding=environment['binding']))
 proof=dict(passed=True,device='cpu',records=reports,
   stubbed=['artifact audit enforcement','weights and model forward','tokenizer','prompt tensor construction','decode budget policy'],
   real=['launch','mixed native mapping','frame SHA256 and PNG decode','ParityGenerator','generate_real','CallHook','decode loop','official scoring'])
 write(root/'FULL_READER.json',proof)
 return proof


def run(config,end,cards,runner=None,clock=time.time):
 from orchard_h10.runner import run as execute
 from orchard_h10.common import write
 if len(cards)!=1 or not cards[0]:raise ValueError('Require exactly one assigned card')
 configs=prepare(config);results=[];failure=None
 for i in (0,):
  if clock()>=end-1800 or (Path(config['output'])/'metadata/STOP').exists():break
  cfg=configs[i]
  result=(runner or execute)(cfg,cards,end,prefix=cfg['prefix'])
  results.append(dict(read=i,types=cfg['types'],**result))
  if result['failure'] or not result['complete']:
   failure=result['failure'];break
 reads=[]
 for i,n in ((0,580),):
  rows=[r for r in results if r['read']==i]
  completed=sum(r['completed'] for r in rows)
  reads.append(dict(read=i,completed=completed,expected=n,complete=completed==n))
 summary=dict(completed=sum(r['completed'] for r in reads),expected=580,
              complete=all(r['complete'] for r in reads),failure=failure,reads=reads,segments=results)
 write(Path(config['output'])/'SUMMARY.json',summary)
 return summary

def memory_bound(*, captures=(98,), allocation_bytes=200*1024**3):
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=g3t+1024**2
 runtime_allowance=64*1024**3
 reads=[dict(read=i,captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance) for i,n in enumerate(captures)]
 return dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],
             sam_memo_bytes=0,sam_measurement_required=False,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=allocation_bytes,reads=reads,
             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))


def memory_probe(config):
 """Check the retained G3T bound without loading or measuring SAM."""
 from orchard_h10.common import write
 settings=json.loads(Path(config['settings']).read_text())
 if settings['perception_memo_modules']!=['g3t']:raise ValueError('Unsupported operator memo modules')
 result=memory_bound()
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Perception memo exceeds host memory plan')
 return result


def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());p=Path(cfg['package'])
 sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 from orchard_h10.common import install_process_guard
 install_process_guard(Path(sys.argv[1]).resolve().parent)
 if cfg.get('rehearsal'):
  from orchard_h10.common import write
  write(Path(cfg['config']['output'])/'REHEARSAL.json',rehearsal(cfg['config']))
  if cfg['config'].get('measure_memory'):memory_probe(cfg['config'])
  return
 import os
 result=run(cfg['config'],cfg['end'],os.environ['CUDA_VISIBLE_DEVICES'].split(','))
 raise SystemExit(1 if result['failure'] else 0)

if __name__=='__main__':main()
