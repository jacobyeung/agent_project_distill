from common import *
import subprocess
records=[]
for name in ('qd_scan_final','qd_tests'):
 with (D/(name+'.log')).open('x') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=p.returncode));J.write(D/'REMAINING_CHECKS.json',records)
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text(),flush=True)
