from pathlib import Path
import os, re, shutil
L=Path(__file__).resolve().parents[1]
I=L/'work/build24m4l'; D=L/'work/build24m4m'; D.mkdir()
def adapt(s):
 s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w(?:\d+[a-z]*)?(?=/|[\x27\"])',str(L),s)
 s=s.replace("L.parent/'w24e/work/", "L/'work/")
 return s.replace('build24m4l','build24m4m').replace('24M4L','24M4M')
for p in I.glob('*.py'):
 (D/p.name).write_text(adapt(p.read_text()))
for directory in ('scanners','rcj_scanner'):
 for p in (I/directory).rglob('*'):
  if p.is_file():
   q=D/p.relative_to(I);q.parent.mkdir(parents=True,exist_ok=True)
   q.write_text(adapt(p.read_text()))
for name in ('inputs','tmp','cache','guard_q','guard_n','rcj_k'):(D/name).mkdir()
for p in (I/'inputs').iterdir():
 if p.is_file():os.link(p,D/'inputs'/p.name)
for name in ('CONFIG_DELTA.json','CONFIG_IDENTITIES.json','UPLOADS_n.json','CONFIG_INPUTS.json'):
 if (I/name).is_file():shutil.copyfile(I/name,D/name)
(D/'run.sh').write_text(adapt((I/'run.sh').read_text()).replace('ulimit -v 16777216','ulimit -v 15000000'))
print('Build scripts staged',D)
