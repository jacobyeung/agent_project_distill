"""Preparation accepts an unpopulated binding; the sampler refuses it."""
from pathlib import Path
from copy import deepcopy
import json,os,sys,tempfile
L=Path(__file__).resolve().parents[2];D=L/'work/build23';B=L/'work/build21';O=D/'proofs/capacity'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
os.environ['B21C_PORTABLE']='1'
import portable21c
portable21c.install()
from student_pilot.p3_provenance import load,write,file_pin
from student_pilot.r2_contract import preparation
from student_pilot.r1_mix import validate_binding
from student_pilot.r1_persisted import proof_scope,scope
cfg=load(O/'400/q/c.json')
result={}
root=Path(tempfile.mkdtemp(prefix='bootstrap_',dir=D/'proofs'))
from student_pilot.r1_handover import bind_target
with proof_scope(),scope(cfg['r1_training']['persisted_files']):
    cfg.pop('r2_sampling',None)
    cfg=bind_target(cfg,root/'before_handover.json')
    try:preparation(cfg)
    except ValueError as error:
        assert str(error)=='R1_SCENE_AND_SAMPLER_BINDINGS_REQUIRED',str(error)
        result['before']=str(error)
    else:raise AssertionError('Missing preparation binding accepted')
    card=load(cfg['r1_training']['mix']['path'])
    write(root/'population.json',dict(schema='r1-population-v1',complete=False,after_all_filters=False,
        card_sha256=cfg['r1_training']['mix']['sha256'],counts={c['type']:0 for c in card['cells']},
        evidence=[cfg['r1_training']['mix']]))
    pop=file_pin(root/'population.json')
    write(root/'indices.json',dict(population_sha256=pop['sha256'],cells={c['type']:[] for c in card['cells']}))
    cfg['r2_sampling']=dict(schema='r1-sampling-v1',card=cfg['r1_training']['mix'],population=pop,indices=file_pin(root/'indices.json'))
    cfg=bind_target(cfg,root/'handover.json')
    preparation(cfg);result['after_preparation']='PASS'
    try:validate_binding(cfg['r2_sampling'])
    except ValueError as error:
        assert str(error)=='R1_COMPLETE_FILTERED_POPULATION_REQUIRED',str(error)
        result['before_population_training_refusal']=str(error)
    else:raise AssertionError('Incomplete population admitted')
write(D/'BOOTSTRAP.json',dict(status='PASS',**result))
print(json.dumps(result))
