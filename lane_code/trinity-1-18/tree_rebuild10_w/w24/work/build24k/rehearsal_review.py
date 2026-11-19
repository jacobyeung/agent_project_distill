"""Attach the fixture review after consuming the native host pin."""
from pathlib import Path
import sys,json,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';root=Path('/tmp/q_22c714e1')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(root/'kit_n_go/b')]
import joblib as J
from student_pilot.p3_provenance import pinned,load,file_pin
from student_pilot.r1_persisted import scope
from student_pilot.carrier_c1_run import identity
from rv import sync_preparation
cfg=J.load(root/'v.json');result=J.load(root/'p2/q/RESULT.json')
native=result['host_receipt'];assert file_pin(root/'p2/q/host.json')==native
host=load(pinned(cfg['r1_training']['host_receipt']));assert host==load(pinned(native))
value=identity(cfg)
review=dict(verdict='PASS',config_identity=value,evidence=dict(scope='synthetic CPU fixture only',native_host=native))
cfg['r1_training']['review']=J.write(root/'review.json',review)
sync_preparation(cfg,root,'prepared_review.json');assert identity(cfg)==value
# The trainer's explicit CPU fixture authorization cannot authorize any GPU.
cfg['admission']=J.write(root/'admission.json',dict(verdict='PASS',reviewer='cpu-fixture-regression',config_sha256=value,preparation=cfg['preparation']))
cfg['authorization']=J.write(root/'authorization.json',dict(verdict='GO',new_gpus=0,config_sha256=value,job_id='b24k_fresh',scope='CPU fixture only'))
J.write(root/'v.json',cfg)
J.write(root/'gates.json',dict(status='PASS',identity=value,host_source=native,host_written_by='launch_r1.production_proof',fixture_receipts=['review'],production_gates_supplied=False))
