"""Run every native optimizer microstep for all four rank plans on CPU."""
import argparse
import copy
import hashlib
import json
import resource
import sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--tree',required=True);p.add_argument('--out',required=True);p.add_argument('--h1',action='store_true');a=p.parse_args()
sys.path.insert(0,a.tree)
import torch
from tests.fixtures import tiny, Processor, routing_batch, K
from student_pilot import carrier_c1_run as run, carrier_c1_routing as routing
from student_pilot.carrier_c1_data import mixed_indices
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_sweep import recipe_for

torch.set_num_threads(2)
raw=[json.loads(s) for s in (K/'rows/camera_fixtures.jsonl').read_text().splitlines()]
clip=json.loads(next((K/'tmp/manifests').glob('*.json')).read_text())
# Exercise camera and ground/gap rows; source paths remain opaque metadata.
source=Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/rows_slices/slices_final/a0_units.jsonl')
with source.open() as f: raw.extend(json.loads(next(f)) for _ in range(2))
packed=[]
for r in raw:
 if r['question_type'].startswith('camera'):
  packed.append(routing.c1_row(r,clip))
 else:
  # These are GT-valued ground rows; the synthetic RGB prefix is shared by all fixtures.
  from student_pilot.ground_rows import pack
  r=pack({**r['ground_record'], 'suffix':r['target']}, r['provenance'])
  packed.append(dict(qid=r['qid'],routing=r,target=r['target'],student_input=dict(question=r['question'],options=r['options'])))
cfg=json.loads(Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/kit07ca49df_meta/m/k/b02e4385.json').read_text())
settings={'faithful_own_camera_rows':a.h1,'routing_pose_targets':a.h1}
if a.h1:
 cfg['scheduled_sampling'].update(max_own_probability=.5,force_from_step=1)
recipe=recipe_for(cfg)

class Rows:
 processor=Processor()
 h1=settings
 def __init__(self,base,targets):
  self.base=base;self.targets=targets
 def count(self,stream): return len(packed) if stream=='routing' else 16
 def row(self,stream,index): return packed[index],None
 def get(self,stream,index):
  if stream!='routing':
   return copy.deepcopy(self.base),copy.deepcopy(self.targets) if stream=='pose' else None,{'qid':f'{stream}-{index}'}
  row=packed[index]; b, audit=routing_batch(self.base,row)
  if a.h1:
   from student_pilot.h1 import pose_targets
   t,c=pose_targets(row,b,self.h1);audit['h1_pose']=c
   return b,t,audit
  return b,None,audit

def digest_tensor(x):
 return hashlib.sha256(x.detach().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()

reports=[]
for rank in range(4):
 model,base,targets=tiny();model.recipe=copy.deepcopy(recipe)
 model.train()
 rows=Rows(base,targets)
 plan=next(mixed_indices({s:rows.count(s) for s in ('pose','vqa','pointing','routing')},1,seed=17,training_mode='final',mix=recipe['mix'],world=4))
 captured=[]
 def capture(module,args,kwargs,output):
  if kwargs.get('stream')=='readout': return
  b=args[0]
  captured.append(dict(stream=kwargs.get('stream'),inputs={k:digest_tensor(v) for k,v in b.items() if isinstance(v,torch.Tensor)},
                       loss=float(output['loss'].detach()),components={k:float(v) for k,v in output['components'].items()},
                       trained_tokens=int((b['labels']!=-100).sum())))
 handle=model.register_forward_hook(capture,with_kwargs=True)
 optimizer=torch.optim.AdamW(parameter_groups(model,recipe))
 gates=routing.Gates(recipe['scheduled_sampling'],False)
 info,_=run.optimize_step(model,optimizer,rows,plan,rank,torch.device('cpu'),1,gates=gates)
 handle.remove()
 report=dict(rank=rank,microsteps=captured,rows=len(captured),h1=info.get('h1'),
             gates=info['gates'],parameters={n:digest_tensor(v) for n,v in model.state_dict().items()},
             peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 reports.append(report)
 print(json.dumps({k:v for k,v in report.items() if k not in ('parameters','microsteps')}),flush=True)
Path(a.out).write_text(json.dumps(reports,indent=2)+'\n')
