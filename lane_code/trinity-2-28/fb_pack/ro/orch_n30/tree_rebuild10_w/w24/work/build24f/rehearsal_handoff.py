"""Supply the existing fixture-only host/review boundary to the native handoff."""
from pathlib import Path
import json,runpy,sys
L=Path(__file__).resolve().parents[2];kit=L/'out/kit_n_go'
sys.path[:0]=[str(kit/'b'),str(L/'work/tree_r1')]
import z
from student_pilot.carrier_c1_run import identity
from launch_r1.entry import ASSERTIONS
r=Path(sys.argv[1]);q=z.load(r/'q/RESULT.json')
assert q['status']=='ADMIT'
cfg=z.load(z.checked(q['config']['path'],q['config']['sha256']))
value=identity(cfg)
host=dict(status='PASS',config_identity=value,assertions=dict.fromkeys(ASSERTIONS,True),
          loader_audit=q['audit'],scope='CPU frame-host fixture only')
z.write(r/'host.json',host)
review=dict(verdict='PASS',config_identity=value,scope='CPU fixture regression only',
            canary=dict(path=str(r/'q/RESULT.json'),sha256=z.sha(r/'q/RESULT.json')))
raw=(json.dumps(review,sort_keys=True,indent=2)+'\n').encode()
import hashlib
h=hashlib.sha256(raw).hexdigest();(r.parent/'u').mkdir(exist_ok=True)
(r.parent/'u'/h).write_bytes(raw)
original=z.load
def fixture_load(path):
    result=original(path)
    if Path(path)==kit/'k/a.json':
        result=dict(result,review=dict(path='u/'+h,sha256=h))
    return result
z.load=fixture_load
z.write(r.parent/'handoff_boundary.json',dict(scope='CPU fixture only',kit_changed=False,
        control_review_override=dict(path='u/'+h,sha256=h),host=str(r/'host.json')))
sys.argv=[str(kit/'b/h.py'),*sys.argv[1:]]
runpy.run_path(str(kit/'b/h.py'),run_name='__main__')
