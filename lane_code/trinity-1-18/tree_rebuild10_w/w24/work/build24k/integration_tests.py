from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import base64,hashlib,json,sys,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path[:0]=[str(L/'work/build24/kits/n/b'),str(L/'work/tree_r1'),str(L/'work/build24f'),str(L/'work/build24')]
import z,pl,joblib as J
from kit24f import reseal
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import pinned
from launch_r1 import entry
from tests.test_host24j import config

F=D/'integration_final';F.mkdir();kit=F/'kit';shutil.copytree(L/'work/build24/kits/n',kit)
spec=J.load(kit/'k/p.json');spec.update(step=600,uploads=[],host_paths={},n_root=str(F/'target'))
def cap(path,value):
 doc=json.loads(path.read_text());raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());path.write_text(json.dumps(doc))
cap(kit/'k/p.json',spec)
try:pl.selection_pin(kit)
except ValueError as e:assert str(e)=='R1_ROUTING_SELECTION_PIN_MISSING'
else:raise AssertionError('placeholder passed')
pin=J.write(F/'selection.json',dict(regenerated_sha256='1'*64,rows=1,row_id_digest='2'*64,inputs_pinned={}))
(F/'target/u').mkdir(parents=True);shutil.copyfile(pin['path'],F/'target/u'/pin['sha256'])
host=J.load(kit/'k/h.json');host['routing_selection']=dict(path='u/'+pin['sha256'],sha256=pin['sha256']);cap(kit/'k/h.json',host);reseal(kit)
assert pl.selection_pin(kit)[0]==host['routing_selection']
resolved=J.load(D/'proofs/resolver600_v2/filled_A_resolved.json');resolved['kit_sha256']=z.seal(kit)
cfg=config();cfg.update(r1_training=dict(persisted_files=resolved['config']['r1_training']['persisted_files']),streams={})
resolved['external_metadata']=[]
resolved['config']=cfg;resolved['request']=dict(weights=False,frame_roots=[],milestone=400,memory_gib=8,device='cpu')
records=[]
for mode in ('q','r'):
 root=F/mode;root.mkdir();request,paths,stage=pl.plan_payload(kit,resolved,root,regeneration=mode=='r')
 assert not (root/'q').exists()
 assert request['binaries']==host['binaries'] and request['job_tmp']==str(root/'q')
 assert request['routing_base']['sha256']==J.load(kit/'k/r.json')['routing_base']['sha256']
 assert 'routing_inputs' not in request
 with scope(paths):
  prepared=J.load(pinned(request['config']));entries=J.load(pinned(request['staging']))['entries']
  with patch.object(entry,'TMP_NAMESPACE',F):
   q,job_tmp,evidence=entry.begin_host(prepared,root/'q',request)
   with entry.host_environment(job_tmp):
    stage(entries,q)
    assert pinned(request['config']).is_relative_to(q)
   stage.close()
 assert (q/'n.json').read_bytes()==(root/'i/m/n.json').read_bytes()
 assert (q/'source_code.json').exists() and not (q/'c.json').exists()
 assert (q/'w/full_weights.json').is_file()
 assert all(p.stat().st_mode&0o777==0o700 for p in [q,*[p for p in q.rglob('*') if p.is_dir()]])
 records.append(dict(mode=mode,fresh_before_native=True,staged_files=len(entries),immutable_config=True,native_weight_layout=True))
 try:pl.plan_payload(kit,resolved,root,regeneration=True)
 except ValueError as e:assert str(e)=='R1_HOST_JOB_TMP_NOT_FRESH'
 else:raise AssertionError('existing q accepted')
J.write(D/'INTEGRATION_TESTS.json',dict(status='PASS',records=records,placeholder_refusal='R1_ROUTING_SELECTION_PIN_MISSING',fixture_pin_accepted=True,
    scope='Native planner/copier, namespace, metadata and export layout; tiny resolver transport; no production admission'))
print('native planner/copier, fresh namespace, routing placeholder/pin and source metadata PASS')
