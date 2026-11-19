"""Attach CPU fixture host/review evidence; never edit the launch kit."""
from pathlib import Path
from copy import deepcopy
import json,sys,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';root=Path('/tmp/q_22c714e1')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import native24 as N
os.environ['S1_REHEARSAL_ATTEMPT']='b24f_fresh'
import joblib as J
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot import r1_persisted as P,r1_rooms as Rooms,r1_direction_twins as Twins
from launch_r1 import entry
syn=load(L/'work/build24/proofs/capacity/TWIN_BOUNDARY.json')['pins']
Twins.ROWS=syn['rows']['sha256'];Twins.BINDING=syn['binding']['sha256'];Twins.ALIASES=syn['aliases']['sha256'];Rooms.STORE=syn['source_database']['sha256']
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
cfg=load(root/'v.json');q=load(root/'p2/q/RESULT.json');assert q['status']=='ADMIT'
identity=N.C.identity(cfg);records=[]
with P.scope(aliases),P.scope(cfg['r1_training']['persisted_files']):
 try:entry.admit(cfg)
 except ValueError as e:records.append(dict(stage='u.py/entry.admit before fixture host',refusal=str(e)))
 else:raise AssertionError('expected missing host admission')
 # The frame-host boundary supplies a fixture-only receipt. The native audit
 # remains the actual canary audit; this receipt is not production evidence.
 host=dict(status='PASS',config_identity=identity,assertions=dict.fromkeys(entry.ASSERTIONS,True),loader_audit=q['audit'],scope='CPU frame-host fixture only')
 cfg['r1_training']['host_receipt']=J.write(root/'host.json',host)
 try:entry.admit(cfg)
 except ValueError as e:records.append(dict(stage='u.py/entry.admit before fixture review',refusal=str(e)))
 else:raise AssertionError('expected pending review')
 # This review certifies only that this tiny fixture's authenticated canary
 # passed. It grants no approval to the production configuration or upload.
 review=dict(verdict='PASS',config_identity=identity,scope='CPU fixture regression only',canary=file_pin(root/'p2/q/RESULT.json'))
 cfg['r1_training']['review']=J.write(root/'review.json',review)
 assert entry.admit(cfg)==0
 before=deepcopy(cfg)
 cfg['r1_training']['host_receipt']=J.write(root/'host_bad.json',dict(host,status='FAIL'))
 try:entry.admit(cfg)
 except ValueError as e:assert str(e)=='R1_HOST_ADMISSION_MISSING';records.append(dict(mutation='host FAIL',refusal=str(e)))
 else:raise AssertionError('bad host accepted')
 cfg=before
 cfg['r1_training']['review']=J.write(root/'review_bad.json',dict(review,verdict='FAIL'))
 try:entry.admit(cfg)
 except ValueError as e:assert str(e)=='INDEPENDENT_REVIEW_PENDING';records.append(dict(mutation='review FAIL',refusal=str(e)))
 else:raise AssertionError('bad review accepted')
 cfg['r1_training']['review']=file_pin(root/'review.json')
 # Preparation authenticates these gate pins too, though they do not change
 # the training identity or row plan.
 prep=load(pinned(cfg['preparation']));prep['r1_training']=deepcopy(cfg['r1_training'])
 cfg['preparation']=J.write(root/'prepared.json',prep)
 assert N.C.identity(cfg)==identity
 cfg['admission']=J.write(root/'admission.json',dict(verdict='PASS',reviewer='cpu-fixture-regression',config_sha256=identity,preparation=cfg['preparation']))
 from student_pilot import rehearsal
 cfg['authorization']=J.write(root/'authorization.json',dict(verdict='GO',new_gpus=0,config_sha256=identity,job_id=rehearsal.attempt_id(),scope='CPU fixture only'))
 assert entry.admit(cfg)==0
 J.write(root/'v.json',cfg)
 J.write(root/'gates.json',dict(status='PASS',identity=identity,records=records,production_gates_supplied=False,fixture_gate_pins={k:cfg['r1_training'][k] for k in ('host_receipt','review')}))
