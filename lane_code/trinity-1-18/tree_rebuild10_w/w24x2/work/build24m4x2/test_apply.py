from pathlib import Path
import sys,json,os,subprocess,shutil,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4x2';sys.path[:0]=[str(D),str(L/'work/tree_r1c')]
from seal import z,write,NAMES
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
U=L.parent/'w24u';F=D/('reapply_'+str(time.time_ns()));F.mkdir();base=z.load(D/'BASELINE.json')
assert digest(inventory(U/'work/tree_r1c'))==base['tree']
def link(p,q):
 q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(p.stat().st_mode&511)
for rel in inventory(U/'work/tree_r1c'):link(U/'work/tree_r1c'/rel,F/'work/tree_r1c'/rel)
for name in NAMES:
 rel='out/kit_'+name if name in ('n_go','qd') else 'work/build24/kits/'+name
 assert verify(U/rel)==base['kits'][name]
 for p in (U/rel).rglob('*'):
  if p.is_file():link(p,F/p.relative_to(U))
helpers={p.name:z.sha(p) for p in (U/'out/rcj').iterdir() if p.is_file()}
assert helpers['ch.py']==base['rcj']['ch.py']
for name in helpers:link(U/'out/rcj'/name,F/'out/rcj'/name)
for name in ('TREE_FILES.sha256','TREE_SEAL.json'):link(U/'out'/name,F/'out'/name)
cmd=[sys.executable,'-I','-s','-B',str(L/'out/apply_24m4v.py'),str(F)]
r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(D/'apply_test.log').write_text(r.stdout);assert r.returncode==0,r.stdout
result=z.load(F/'work/build24m4x2_apply/RESULT.json')
upload=z.load(result['uploads']);listed={v['name']:v for v in upload['files']}
for name in ('x.py','nd.py','ps.py'):
 if helpers[name]!=upload['baseline_rcj'][name]:assert listed['rcj/'+name]['sha256']==helpers[name]
for name,h in helpers.items():assert z.sha(F/'out/rcj'/name)==(z.sha(L/'out/rcj/ch.py') if name=='ch.py' else h)
assert digest(inventory(U/'work/tree_r1c'))==base['tree']
assert {p.name:z.sha(p) for p in (U/'out/rcj').iterdir() if p.is_file()}==helpers
write(D/'APPLY_TEST.json',dict(status='PASS',source=str(U),copy=str(F),before_helpers=helpers,
 after=result,original_workspace_unchanged=True,all_u_helpers_preserved_except_scoped_ch=True))
print('Apply-on-24m4u-copy PASS; original unchanged; helper changes preserved')
