from common import *
import importlib.util,shutil
from student_pilot.r1_launch22 import validate_removals
from student_pilot.r1_persisted import scope
from student_pilot.r1_rooms import check_protected_rooms
from launch_r1.build import verify
F=D/'delta_sealed';F.mkdir()
for name in ('q','n','n_go','qd'):
 dest=F/kit(name).relative_to(L)
 dest.parent.mkdir(parents=True,exist_ok=True)
 def link(a,b):os.link(a,b);return b
 shutil.copytree(kit(name),dest,copy_function=link)
source=F/'pose.jsonl';source.write_text(json.dumps(dict(row_key='pose-final-fixture'))+'\n')
sp=importlib.util.spec_from_file_location('delta',L/'out/bind_protected.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
value=m.apply(F,'pose',source)
assert value['pose_cleanup']=='BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN'
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()});paths[J.sha(source)]=str(source)
for name in ('q','n','n_go','qd'):
 k=F/kit(name).relative_to(L);assert verify(k)==value['kits'][name]
 for rel in ('k/c.json','k/n.json'):
  cfg=J.load(k/rel)
  with scope(paths):validate_removals(cfg)
 for p in kit(name).rglob('*'):
  if p.is_file() and str(p.relative_to(kit(name))) not in ('k/c.json','k/n.json','k/p.json','BUILD.json','SHA256SUMS.txt'):assert J.sha(p)==J.sha(k/p.relative_to(kit(name)))
 cfg=J.load(k/'k/n.json')
 with scope(paths):
  result=check_protected_rooms(cfg,'pose',iter([dict(row_key='pose-final-fixture',dataset='scannet',scene='scene0630_00'),dict(row_key='clean',dataset='scannet',scene='scene9999_00')]),iter([dict(row_key='clean',dataset='scannet',scene='scene9999_00')]))
 assert result['checked_keys']==1
J.write(D/'DELTA_SEALED_TESTS.json',dict(status='PASS',source_kit_seals={n:J.seal(kit(n)) for n in ('q','n','n_go','qd')},result_kit_seals=value['kits'],native_validator=True,native_pose_postcondition=True,all_runtime_helpers_unchanged=True,pose_materialization='BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN',upload_top_dirs=value['top_directories'],tree_changed=False))
print('Final sealed four-kit pose delta binding, isolation and explicit materialization blocker PASS')
