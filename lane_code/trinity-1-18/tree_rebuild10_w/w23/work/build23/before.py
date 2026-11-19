from pathlib import Path
import json,sys,shutil
L=Path(__file__).resolve().parents[2]; D=L/'work/build23'; T=L/'work/tree_r1'
sys.path[:0]=[str(T),str(L/'work/build21')]
from student_pilot import r1_coverage as C
from student_pilot.r1_population import Membership
from student_pilot.p3_provenance import write,file_pin
paths=['student_pilot/r1_coverage.py','student_pilot/s1_admission.py','student_pilot/r1_population.py',
       'student_pilot/r1_rooms.py','launch_r1/entry.py','launch_r1/production_proof.py']
for name in paths:
    p=L/'attic/build23/tree'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(T/name,p)
for name in ('UPLOADS.json','PACKAGE_MANIFEST.json','kit.py','joblib.py','naming21.py'):
    p=L/'attic/build23'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(L/'work/build21'/name,p)
records=[]
cfg={'r1_training':{'routing_slices':'deferred_first_boundary'}}
try:
    assert C.source_names({},cfg)==()
except (TypeError,AssertionError) as e:records.append(dict(case='declaration yields no slices',status='FAIL_BEFORE',error=str(e)))
p=D/'membership_before.json';write(p,dict(schema='r1-source-membership-v1',sources={}))
try:
    got=Membership(file_pin(p)).cell(dict(qid='p_distance',question_type='object_abs_distance'),'routing')
    assert got=='routing_base'
except (ValueError,AssertionError) as e:records.append(dict(case='P absolute distance preserved as base',status='FAIL_BEFORE',error=str(e)))
write(D/'BEFORE.json',records)
print(json.dumps(records,indent=2))
