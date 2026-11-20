from common import *
import subprocess,copy
from student_pilot.r1_persisted import scope
from student_pilot.r1_rooms import check_protected_rooms
from student_pilot.row_removals import Removals
records=[]
for name in ('q','n','n_go','qd'):
 root=D/'census_final'/(name+'_clean');k=root/'sealed';cfg=J.load(root/'cfg.json')
 def invoke(expected):
  p=subprocess.run([sys.executable,'-B','-s',str(k/'b/h.py'),str(root/'p'),str(root/'h_final.json')],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'91'})
  if expected:assert p.returncode and expected in p.stderr,(name,expected,p.stderr)
  else:assert p.returncode==0,(name,p.stderr)
 source=root/'p/q/ss.json';raw=source.read_bytes()
 source.write_bytes(raw+b'\n');invoke('E10:');source.write_bytes(raw)
 report=root/'c5.json';raw=report.read_bytes();value=J.load(report);value['streams']['pointing']['source_pins'][0]['count']+=1
 report.write_text(json.dumps(value));invoke('R1_CENSUS_SOURCE_PINS_DIFFER:pointing');report.write_bytes(raw)
 invoke(None);records.append(dict(kit=name,source_descriptor_tamper='REFUSE',source_pins_tamper='REFUSE',clean='PASS'))
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
F=D/'delta_fixture'
for p in (F/'pose.jsonl',F/'pose_second.jsonl'):paths[J.sha(p)]=str(p)
cfg=J.load(F/'work/build24/kits/q/k/n.json')
listed=[dict(row_key=json.loads(line)['row_key'],dataset='scannet',scene='scene0630_00') for p in (F/'pose.jsonl',F/'pose_second.jsonl') for line in p.read_text().splitlines()]
with scope(paths):
 remove=Removals(cfg['remove_files'],stream='pose')
 assert all(not remove.keep(r) for r in listed)
 result=check_protected_rooms(cfg,'pose',iter(listed),iter([dict(row_key='clean',dataset='scannet',scene='scene9999_00')]))
 assert result['checked_keys']==len(listed)
records.append(dict(case='delta_pose_native_postcondition',result=result))
J.write(D/'BINDING_FINAL_TESTS.json',dict(status='PASS',records=records))
print('Staging-manifest/source-pin tamper refusal and pose delta post-condition PASS')
