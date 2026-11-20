from common import *
import subprocess
names=('scans','kit_tests','guard_q_legacy','guard_n_legacy','resolver600_tests')
for name in names:
 if name=='resolver600_tests':
  p=D/'resolver600';
  if p.exists():p.rename(L/'attic/build24m4l/resolver600_first')
 with (D/(name+'_l2.log')).open('w') as f:
  child=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 print(name,child.returncode,flush=True)
 if child.returncode:print((D/(name+'_l2.log')).read_text()[-2500:],flush=True)
