from common import *
from student_pilot.r1_persisted import scope
import subprocess
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
sys.path.insert(0,str(kit('q')/'b'))
import cs
root=D/'census/q_clean';cfg=J.load(root/'cfg.json')
source=J.load(root/'p/q/ss.json');pin=source['pose'][0]['population']
staged=root/'p/q/u'/pin['sha256'];staged.parent.mkdir(exist_ok=True);os.link(pin['path'],staged)
source['pose'][0]['population']=dict(path='/unavailable/original/pose.sqlite',sha256=pin['sha256'])
replace(root/'p/q/ss.json',json.dumps(source))
paths[pin['sha256']]=str(staged)
with scope(paths):cs.publish(root/'kit',root,cfg,'91')
k=root/'sealed';replace(k/'b/cs.py',(kit('q')/'b/cs.py').read_bytes())
for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
reseal(k)
r=subprocess.run([sys.executable,'-B','-s',str(k/'b/h.py'),str(root/'p'),str(root/'staged_alias.json')],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'91'})
assert r.returncode==0,r.stderr
J.write(D/'STAGED_CENSUS_TESTS.json',dict(status='PASS',native_h=True,original_path='/unavailable/original/pose.sqlite',resolved_sha256=pin['sha256'],authenticated_staged_copy=str(staged),receipt_pin=J.load(root/'p/hr.json')['protected_census']))
print('h.py authenticates original receipt pins through staged SHA map PASS')
