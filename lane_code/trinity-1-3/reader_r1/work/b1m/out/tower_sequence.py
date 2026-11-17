"""Operator dispatch for two isolated reads within one allocation."""
import json,sys,time,hashlib
from pathlib import Path

RULES=('null_argmax','candidates_argmax')
COUNTS=(150,150,150,150,36)
# Distance under each rule precedes the remaining baseline types.
SCHEDULE=((0,3),(1,3),(0,0),(0,1),(0,2),(0,4))

def descriptors():
 return [dict(arm='tower',modes=['none'],stage1_select_rule=r,save_own_depth=False,
              perception_memo='verify' if i==0 else 'on',
              perception_memo_verify_reads=30 if i==0 else None,
              perception_memo_verify_types=['object_abs_distance'] if i==0 else None,perception_memo_max_bytes=64*1024**3,
              types=[0,1,2,3,4] if i==0 else [3],expected=636 if i==0 else 150)
         for i,r in enumerate(RULES)]

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
 specs=descriptors();identity=dict(plan=config['plan_sha256'],inputs=config['inputs_sha256'],
   operator_sha256=config['operator_sha256'],cards=1,reads=specs,schedule=SCHEDULE)
 # JSON roundtrip gives a stable list representation for resume checks.
 identity=json.loads(json.dumps(identity));sealed_write(base/'metadata/IDENTITY.json',identity)
 configs={}
 for i,spec in enumerate(specs):
  root=base/str(i)
  chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False,
          **{k:spec[k] for k in ('perception_memo','perception_memo_verify_reads','perception_memo_max_bytes','perception_memo_verify_types')}}
  path=root/'metadata/0.json';sealed_write(path,chosen)
  sealed_write(root/'metadata/IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  for t in spec['types']:
   segment=dict(chosen)
   segment_path=root/str(t)/'metadata/0.json';sealed_write(segment_path,segment)
   configs[i,t]={**config,'output':str(root/str(t)),'settings':str(segment_path),
      'arms':['tower'],'modes':['none'],'types':[ORDER[t]],'stage1_select_rule':spec['stage1_select_rule'],
      'stop_margin':1800,'return_margin':1200,**memo_settings(segment)}
 return configs

def rehearsal(config):
 from orchard_h10.runner import control,worker_args
 from orchard_h10.common import ORDER
 configs=prepare(config);result=[]
 for (i,t),cfg in configs.items():
  control(cfg)
  args=worker_args(dict(config=cfg,type=t,index=0,cards=1,stop_at=1,finish_by=2))
  assert args[args.index('--arms')+1]=='tower'
  assert args[args.index('--modes')+1]=='none'
  assert args[args.index('--types')+1]==ORDER[t]
  assert json.loads(Path(args[args.index('--settings')+1]).read_text())['stage1_select_rule']==RULES[i]
  chosen=json.loads(Path(args[args.index('--settings')+1]).read_text())
  assert chosen['perception_memo']==('verify' if i==0 else 'on')
  assert chosen['perception_memo_verify_types']==(['object_abs_distance'] if i==0 else None)
  result.append(dict(read=i,type=t,args=args,settings=chosen,expected=COUNTS[t]))
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
   value=real.real_perception(None,device='cpu',sam3_tower=object(),selector_head=head,stage1_select_rule=rule)
   value.socket(None,None)
  assert made[0].rule==rule
  assert made[0].select(dict(x=torch.zeros(2,58),name='x'))==(-1 if rule==RULES[0] else 1)
 return result

def run(config,end,cards,runner=None,clock=time.time):
 from orchard_h10.runner import run as execute
 from orchard_h10.common import write
 if len(cards)!=1 or not cards[0]:raise ValueError('Require exactly one assigned card')
 configs=prepare(config);results=[];failure=None
 for i,t in SCHEDULE:
  if clock()>=end-1800 or (Path(config['output'])/'metadata/STOP').exists():break
  cfg=configs[i,t]
  result=(runner or execute)(cfg,cards,end,prefix=cfg['prefix'])
  results.append(dict(read=i,type=t,**result))
  if result['failure'] or not result['complete']:
   failure=result['failure'];break
 reads=[]
 for i,n in ((0,636),(1,150)):
  rows=[r for r in results if r['read']==i]
  completed=sum(r['completed'] for r in rows)
  reads.append(dict(read=i,completed=completed,expected=n,complete=completed==n))
 summary=dict(completed=sum(r['completed'] for r in reads),expected=786,
              complete=all(r['complete'] for r in reads),failure=failure,reads=reads,segments=results)
 write(Path(config['output'])/'SUMMARY.json',summary)
 return summary

def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());p=Path(cfg['package'])
 sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)]
 from orchard_h10.common import install_process_guard
 install_process_guard(Path(sys.argv[1]).resolve().parent)
 if cfg.get('rehearsal'):
  from orchard_h10.common import write
  write(Path(cfg['config']['output'])/'REHEARSAL.json',rehearsal(cfg['config']));return
 import os
 result=run(cfg['config'],cfg['end'],os.environ['CUDA_VISIBLE_DEVICES'].split(','))
 raise SystemExit(1 if result['failure'] else 0)

if __name__=='__main__':main()
