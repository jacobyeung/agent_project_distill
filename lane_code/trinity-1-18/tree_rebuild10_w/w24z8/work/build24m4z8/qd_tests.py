from common import *
import copy,itertools
from unittest.mock import patch
from types import SimpleNamespace
from student_pilot import r1_persisted as P, r1_mix, carrier_c1_run as C
from student_pilot.p3_provenance import digest
from launch_r1 import production_proof as Q
replicas={p.name:str(p) for p in (D/'inputs').iterdir() if p.is_file() and len(p.name)==64}
from student_pilot.r1_handover import compare_configs
checks=[]
for name in NAMES:
 for rel in ('k/c.json','k/n.json'):
  cfg=J.load(kit(name)/rel)
  assert cfg.get('max_pixels') is None and cfg.get('min_pixels') is None and cfg['frame_count']==32
  source=J.load(input_file(cfg['r1_training']['p_run']['config']['sha256']))
  with P.scope(replicas):compare_configs(source,cfg,replicas=replicas)
  checks.append(dict(kit=name,config=rel,status='\x50ASS',min_pixels=None,max_pixels=None,frame_count=32,identity=C.identity(cfg)))
J.write(D/'HANDOVER_TESTS.json',checks)
n=J.load(kit('n')/'k/n.json');qd=J.load(kit('qd')/'k/n.json')
assert qd==n and C.identity(qd)==C.identity(n)
assert P.init_policy(qd['r1_training'])==P.INIT_POLICY
bad=copy.deepcopy(qd);bad['r1_training']['proof_mode']='q'
try:P.init_policy(bad['r1_training'])
except ValueError as e:assert str(e)=='P_EXPORT_INIT_TRAIN_MODE_REQUIRED';refusal=str(e)
else:raise AssertionError('Proof policy unexpectedly accepted q')
# The kit's population is a pre-preparation declaration. Build explicit synthetic
# complete indices from its authenticated card to exercise the native row planner.
with P.scope(replicas):
 card=J.load(input_file(qd['r2_sampling']['card']['sha256']))
 allocated=r1_mix.allocate(card,{c['type']:100000 for c in card['cells']})
 population_counts=allocated['draws'];offset={s:0 for s in r1_mix.STREAMS};cells={}
 for c in card['cells']:
  start=offset[c['stream']];size=population_counts[c['type']]
  cells[c['type']]=list(range(start,start+size));offset[c['stream']]+=size
 evidence=J.write(D/'qd_evidence.json',dict(scope='Synthetic prepared stores; no production-row claim'))
 cardpin=J.write(D/'qd_card.json',card)
 poppin=J.write(D/'qd_population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,evidence=[evidence],card_sha256=cardpin['sha256'],counts=population_counts))
 indpin=J.write(D/'qd_indices.json',dict(population_sha256=poppin['sha256'],cells=cells))
 sampling=dict(schema='r1-sampling-v1',card=cardpin,population=poppin,indices=indpin)
 card,indices,allocation=r1_mix.validate_binding(sampling)
 counts={stream:sum(len(indices['cells'][cell['type']]) for cell in card['cells'] if cell['stream']==stream) for stream in r1_mix.STREAMS}
 expected=next(r1_mix.plans(sampling,counts,1000,start_step=0))
 old=next(r1_mix.plans(sampling,counts,1000,start_step=400))
 assert expected!=old
 receipt=dict(streams={s:dict(count=c) for s,c in counts.items()})
 captured=[]
 class Model:
  def parameters(self):return []
  def to(self,device):return self
  def eval(self):return self
 class Rows:
  def __init__(self,*args):pass
  def close(self):pass
 def run_rows(model,rows,plans,ranks,device=None,sink=None):
  captured.append(dict(plans=plans,ranks=list(ranks),device=str(device)))
  records=[dict(stream=s,rank=r,index=ix[r],finite=True,loss=1.0) for plan in plans for s,ix in plan for r in ranks]
  sink(records);return records
 testcfg=copy.deepcopy(qd);testcfg['preparation']=dict(path='fixture',sha256='a'*64);testcfg['r2_sampling']=sampling
 with patch.object(C,'validate'),patch.object(C,'prepared',return_value=(receipt,{})),patch.object(C,'processor_for_receipt',return_value=object()),patch.object(C,'load_model',return_value=Model()),patch.object(C.full_ft,'base_parameters',return_value=[]),patch.object(C,'Rows',Rows),patch.object(C,'check_plan_rows',side_effect=run_rows):
  result=Q.forward(testcfg,D,0,'cuda:0')
 assert captured[0]['plans']==[expected] and captured[0]['ranks']==[0,1,2,3] and captured[0]['device']=='cuda:0'
 assert len(J.load(D/'f.json')['records'])==288
J.write(D/'QD_STEP1_TESTS.json',dict(status='\x50ASS',config_differences=[],prepared_input_identity=C.identity(qd),
 proof_mode='train',reason='Native init_policy requires train; discovery still invokes a.py q and has no trainer entrypoint.',
 rejected_q_policy=refusal,step1_plan_sha256=digest(expected),step401_plan_sha256=digest(old),rows=288,
 forward=result,scope='Authenticated card with synthetic complete prepared stores/indices; native plans and first_batch_check selection. Model loading, row encoding and numerical forward are stubbed. Real prepared production data is unavailable locally.'))
assert not any((kit('qd')/'b'/s).exists() for s in ('t.py','u.py','e.sh'))
print('HANDOVER 8/8 \x50ASS; QD step-1 288 native selections \x50ASS; qd/n config identities identical')
