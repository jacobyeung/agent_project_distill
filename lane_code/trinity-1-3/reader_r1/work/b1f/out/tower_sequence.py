"""Operator dispatch for two isolated reads within one allocation."""
import json,sys,time,hashlib
from pathlib import Path

RULES=('null_argmax','candidates_argmax')
COUNTS=(150,150,150,150,36)
# Each read owns one worker; read 0 retains its memo across all five types.
SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4),(1,3))

def descriptors(package):
 items=json.loads((Path(package)/'items/devs1_routed.json').read_text())['items']
 verify_ids=[r['id'] for r in items if r['question_type']=='object_abs_distance'][:30]
 return [dict(arm='tower',modes=['none'],stage1_select_rule=r,save_own_depth=False,
              perception_memo='verify' if i==0 else 'on',
              perception_memo_verify_ids=verify_ids if i==0 else [],
              types=[3,0,1,2,4] if i==0 else [3],expected=636 if i==0 else 150)
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
 specs=descriptors(config['package']);identity=dict(plan=config['plan_sha256'],inputs=config['inputs_sha256'],
   operator_sha256=config['operator_sha256'],cards=1,reads=specs,schedule=SCHEDULE)
 # JSON roundtrip gives a stable list representation for resume checks.
 identity=json.loads(json.dumps(identity));sealed_write(base/'metadata/IDENTITY.json',identity)
 configs={}
 for i,spec in enumerate(specs):
  root=base/'metadata/reads'/str(i)
  chosen={**settings,'stage1_select_rule':spec['stage1_select_rule'],'save_own_depth':False,
          **{k:spec[k] for k in ('perception_memo','perception_memo_verify_ids')}}
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
  assert chosen['perception_memo']==('verify' if i==0 else 'on')
  assert chosen['perception_memo_verify_ids']==descriptors(config['package'])[i]['perception_memo_verify_ids']
  result.append(dict(read=i,types=cfg['types'],args=args,settings=chosen,expected=636 if i==0 else 150))
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
 for i in (0,1):
  if clock()>=end-1800 or (Path(config['output'])/'metadata/STOP').exists():break
  cfg=configs[i]
  result=(runner or execute)(cfg,cards,end,prefix=cfg['prefix'])
  results.append(dict(read=i,types=cfg['types'],**result))
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

def memory_bound(sam_frame_bytes, *, captures=(84,60)):
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=sam_frame_bytes*32+g3t
 # Allow 1 MiB Python/allocator overhead per capture and three transient copies.
 per_capture+=1024**2
 runtime_allowance=64*1024**3
 reads=[dict(captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance) for n in captures]
 return dict(sam_frame_bytes=sam_frame_bytes,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=200*1024**3,reads=reads,
             fits=all(r['host_budget_bytes']<=200*1024**3 for r in reads))


def memory_probe(config):
 """Measure a real fixed-resolution SAM encoding during the allocated CPU check."""
 import torch
 from PIL import Image
 from e2e_reader import parity
 from e2e_reader.perception_memo import held_bytes
 from student_pilot.sam3_tower import Sam3Tower
 settings=json.loads(Path(config['settings']).read_text())
 captures=parity._captures(settings.get('frames_json',parity.FRAMES))
 first=next(iter(captures.values()))['frames'][0]
 path=parity._frame_path(first['path'],settings['frames_root'])
 from orchard_h10.common import sha,write
 if sha(path)!=first['sha256']:raise ValueError('Probe frame binding differs')
 with Image.open(path) as im:frame=im.convert('RGB')
 # FP32 bounds both supported output precisions; the processor fixes resolution.
 tower=Sam3Tower(dict(settings['sam3'],device='cpu',precision='float32'))
 features=tower.encode([frame])
 footprint=held_bytes(dict(frames=features.frames,sizes=features.sizes))
 result=memory_bound(footprint)
 result.update(measured=True,device='cpu',precision='float32',frame_sha256=first['sha256'])
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Measured perception memo exceeds host memory plan')
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
