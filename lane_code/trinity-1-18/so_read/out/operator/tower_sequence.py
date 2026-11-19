"""Operator dispatch for two isolated reads within one allocation."""
import json,sys,time,hashlib
from pathlib import Path

RULES=('candidates_argmax',)
COUNTS=(150,150,150,150,36)
SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4))

def descriptors(package):
 return [dict(arm='tower',modes=['none'],stage1_select_rule='candidates_argmax',save_own_depth=False,
              perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],
              types=[3,0,1,2,4],expected=636)]

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
          **{k:spec[k] for k in ('perception_memo','perception_memo_verify_ids','perception_memo_modules')}}
  path=root/'metadata/0.json';sealed_write(path,chosen)
  sealed_write(root/'metadata/READ_IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  configs[i]={**config,'output':str(root),'settings':str(path),
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
  result.append(dict(read=i,types=cfg['types'],args=args,settings=chosen,expected=636))
 # Exercise each selected rule through the real tower socket with stub weights.
 from unittest.mock import patch
 from types import SimpleNamespace
 import torch
 from e2e_reader import stage1,real
 for rule in RULES:
  made=[]
  def init(obj,detect,head,geometry,rule='null_argmax'):
   obj.rule=rule;obj.head=head;obj.diagnostics={};made.append(obj)
  head=SimpleNamespace(with_null=lambda *a:torch.tensor([1.,2.,100.]))
  with patch.object(stage1.StageOne,'__init__',init),patch.object(real,'TowerG3T',return_value=None),patch('e2e_reader.geometry.frame_count',return_value=32):
   value=real.real_perception(None,device='cpu',perception_memo_modules=['g3t'],sam3_tower=object(),selector_head=head,stage1_select_rule=rule)
   value.socket(None,None)
  assert made[0].rule==rule
  assert made[0].select(dict(x=torch.zeros(2,58),name='x'))==1
 return result

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
 for i,n in ((0,636),):
  rows=[r for r in results if r['read']==i]
  completed=sum(r['completed'] for r in rows)
  reads.append(dict(read=i,completed=completed,expected=n,complete=completed==n))
 summary=dict(completed=sum(r['completed'] for r in reads),expected=636,
              complete=all(r['complete'] for r in reads),failure=failure,reads=reads,segments=results)
 write(Path(config['output'])/'SUMMARY.json',summary)
 return summary

def memory_bound(*, captures=(84,), allocation_bytes=200*1024**3, read_extensions=False, read_cache_bytes=0):
 if not read_extensions:read_cache_bytes=0
 if type(read_cache_bytes) is not int or not 0<=read_cache_bytes<=16*1024**3:
  raise ValueError('Invalid read cache memory bound')
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=g3t+1024**2
 runtime_allowance=64*1024**3
 reads=[dict(read=i,captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance+read_cache_bytes) for i,n in enumerate(captures)]
 return dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],
             sam_memo_bytes=0,sam_measurement_required=False,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=allocation_bytes,reads=reads,
             **({'read_cache_bytes':read_cache_bytes} if read_extensions else {}),
             fits=all(r['host_budget_bytes']<=allocation_bytes for r in reads))


def memory_probe(config):
 """Check the retained G3T bound without loading or measuring SAM."""
 from orchard_h10.common import write
 settings=json.loads(Path(config['settings']).read_text())
 if settings['perception_memo_modules']!=['g3t']:raise ValueError('Unsupported operator memo modules')
 options={}
 if config.get('read_extensions') is True:
  from e2e_reader.read_cache import cache_bytes,switches
  cap=cache_bytes(settings) if 'on' in switches(settings).values() else 0
  options=dict(read_extensions=True,read_cache_bytes=cap)
 result=memory_bound(**options)
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Perception memo exceeds host memory plan')
 return result


def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());p=Path(cfg['package'])
 sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 if cfg['config'].get('read_extensions') is True:
  sys.path.insert(0,str(p/'u0'))
  from a8 import activate
  activate(enabled=True)
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
