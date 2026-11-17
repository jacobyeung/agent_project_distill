"""Operator dispatch for two isolated reads within one allocation."""
import json,sys,time,hashlib
from pathlib import Path

RULES=('null_argmax','candidates_argmax')
COUNTS=(150,150,150,150,36)
# Distance under each rule precedes the remaining baseline types.
SCHEDULE=((0,3),(1,3),(0,0),(0,1),(0,2),(0,4))

def descriptors():
 return [dict(arm='tower',modes=['none'],stage1_select_rule=r,save_own_depth=False,
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
 specs=descriptors();identity=dict(plan=config['plan_sha256'],inputs=config['inputs_sha256'],
   operator_sha256=config['operator_sha256'],cards=1,reads=specs,schedule=SCHEDULE)
 # JSON roundtrip gives a stable list representation for resume checks.
 identity=json.loads(json.dumps(identity));sealed_write(base/'metadata/IDENTITY.json',identity)
 configs={}
 for i,spec in enumerate(specs):
  root=base/str(i)
  chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False}
  path=root/'metadata/0.json';sealed_write(path,chosen)
  sealed_write(root/'metadata/IDENTITY.json',dict(**identity,read=i,settings_sha256=canonical(chosen)))
  for t in spec['types']:
   configs[i,t]={**config,'output':str(root/str(t)),'settings':str(path),
      'arms':['tower'],'modes':['none'],'types':[ORDER[t]],'stage1_select_rule':spec['stage1_select_rule'],
      'stop_margin':1800,'return_margin':1200}
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
  result.append(dict(read=i,type=t,args=args,expected=COUNTS[t]))
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
