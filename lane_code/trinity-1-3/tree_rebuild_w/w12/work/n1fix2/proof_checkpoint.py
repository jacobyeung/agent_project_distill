"""Produce the sealed checkpoint manifest and consume it through the handover reader."""
from pathlib import Path
from copy import deepcopy
import ast,json,sys,os,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=L/'work/build12/proofs/n1/checkpoint'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
import torch
from tests.test_r2_n1fix import handover_fixture,write
from tests.test_carrier_c1_run import RunnerTests
from student_pilot import carrier_c1_run as run,r1_handover as handover,r1_training as training
from student_pilot.p3_provenance import load,file_pin
from student_pilot.carrier_c1 import parameter_groups
cfg,p,model,artifact=handover_fixture(O/'producer')
base=L/'work/base/tree_b01ce449/student_pilot/carrier_c1_run.py'
node=next(n for n in ast.parse(base.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='checkpoint')
space=dict(vars(run));exec(compile(ast.Module(body=[node],type_ignores=[]),str(base),'exec'),space)
optimizer=torch.optim.AdamW(parameter_groups(model),weight_decay=.01)
bound=load(cfg['r1_training']['p_run']['binding']['path'])
with RunnerTests().local_collectives():
    complete=space['checkpoint'](O/'producer/checkpoint',model,optimizer,bound,200)
cfg['r1_training']['p_run']['checkpoint']=complete
cfg['r1_training']['continuation_identity']=training.target_identity(cfg)['config_identity']
mapping=load(cfg['r1_training']['handover_mapping']['path'])
mapping['target']['config_identity']=cfg['r1_training']['continuation_identity']
cfg['r1_training']['handover_mapping']=write(O/'mapping.json',mapping)
assert training.start(cfg)==200
bad=deepcopy(cfg);source=deepcopy(p)
prep=load(bad['r1_training']['p_run']['preparation']['path'])
prep['streams']['vqa'].update(count=127,indices=write(O/'indices.json',list(range(1,128))))
pin=write(O/'forged_preparation.json',prep);source['preparation']=pin
binding=deepcopy(bound);binding['preparation']=pin
bad['r1_training']['p_run'].update(config=write(O/'forged_config.json',source),preparation=pin,binding=write(O/'forged_binding.json',binding))
try:handover.donor(bad,artifact)
except ValueError as error:
    refusal=str(error);assert 'CHECKPOINT_BINDING_MISMATCH' in refusal
else:raise AssertionError('Forged preparation admitted')
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',step=200,checkpoint=complete,checkpoint_binding_matches=load(complete['path'])['binding']==bound,
    forged_preparation_refusal=refusal,producer=str(base.relative_to(L)),producer_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    real_functions=['sealed export','sealed bind_output','sealed checkpoint','full_ft.write_rank_shard','r1_handover.donor','r1_training.start'],
    standins='Tiny seeded native weights replace pretrained GPU weights; local rank, barrier, broadcast and gather operations replace distributed GPU collectives. Preparation metadata and step label are synthetic. The checkpoint manifest, shard/RNG pins and binding are written by the sealed producer, not supplied as an operator assertion.'),indent=2))
monitor.save(O);print('Native sealed checkpoint binds the preparation and rejects the forgery.')
