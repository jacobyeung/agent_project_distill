"""Preparation and authorization records cannot create a circular target identity."""
from pathlib import Path
from copy import deepcopy
import json,sys,os,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1';O=B/'proofs/target_prepared'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from tests.test_r2_n1fix import handover_fixture,write
from student_pilot import r1_training as training,carrier_c1_run as run
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
cfg,_,_,_=handover_fixture(O/'producer')
expected=training.target_identity(cfg)
native_identity=run.identity(cfg)
prepared=deepcopy(cfg)
for name in ('preparation','admission','authorization','milestone_gate'):
    prepared[name]=write(O/(name+'.json'),dict(config_sha256=native_identity))
assert run.identity(prepared)==native_identity
assert training.target_identity(prepared)==expected
assert training.start(prepared)==200
bad=dict(r1_training={},streams={'vqa':write(O/'invalid_receipt.json',dict(database={'sha256':'bad'}))})
try:training.target_identity(bad)
except ValueError as e:assert 'TARGET_STORE_INVALID' in str(e)
else:raise AssertionError('Invalid receipt admitted')
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',source_seal=digest(inventory(T)),harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_identity_stable=True,target_identity_stable=True,continuation_step=200,derived_store_hashes=expected['stores'],scope='Config content and authenticated stream inputs define N; derived records that already bind that config do not create a recursive hash.'),indent=2))
monitor.save(O)
print('Prepared target identity is stable and the native handover admits.')
