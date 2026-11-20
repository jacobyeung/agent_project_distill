from common import *
import subprocess
for name in ('rd_mount','RDIFF_MOUNT_TEST.log'):
 p=D/name
 if p.exists():
  q=L/'attic/build24m4n/fixture_attempt'/name;q.parent.mkdir(parents=True,exist_ok=True);p.rename(q)
records=[]
for name in ('kit_tests','rdiff_mount_test'):
 with (D/(name+'_m2.log')).open('x') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=p.returncode));J.write(D/'RETEST_RUNS.json',records)
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'_m2.log')).read_text(),flush=True)
