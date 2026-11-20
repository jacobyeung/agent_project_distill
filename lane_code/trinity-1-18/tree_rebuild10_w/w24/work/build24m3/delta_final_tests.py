from common import *
import importlib.util,shutil,copy
from student_pilot.r1_persisted import scope
from student_pilot.r1_launch22 import validate_removals
from student_pilot.row_removals import Removals
from launch_r1.build import verify
sp=importlib.util.spec_from_file_location('delta',L/'out/bind_protected.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
F=D/'delta_fixture'
role=F/'pose_second.jsonl';role.write_text(json.dumps({'row_key':'pose-second-fixture'})+'\n')
tree_before=J.sha(T/'student_pilot/r1_rooms.py')
result=m.apply(F,'pose',role)
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()});paths[J.sha(role)]=str(role);paths[J.sha(F/'pose.jsonl')]=str(F/'pose.jsonl')
for name in ('q','n','n_go','qd'):
 k=F/kit(name).relative_to(L);assert verify(k)==result['kits'][name]
 for doc in ('k/c.json','k/n.json'):
  cfg=J.load(k/doc)
  with scope(paths):
   validate_removals(cfg)
   assert not Removals(cfg['remove_files'],stream='pose').keep(dict(qid='pose-second-fixture'))
   assert Removals(cfg['remove_files'],stream='pointing').keep(dict(qid='pose-second-fixture'))
  assert cfg['remove_files'][-2]['role']=='protected_rooms' and cfg['remove_files'][-2]['stream']=='pose'
 assert J.load(k/'k/a.json')['GO']==(name=='n_go')
assert tree_before==J.sha(T/'student_pilot/r1_rooms.py')
assert all(not v['name'].startswith('n_go/') for v in result['files'])
J.write(D/'DELTA_FINAL_TESTS.json',dict(status='PASS',kits=result['kits'],stream='pose',native_validator=True,native_stream_isolation=True,tree_unchanged=True,upload_files=len(result['files']),receipts='Native in-job producer steps retained; production stores unavailable here.'))
print('Kit delta pose binding and native isolation PASS')
