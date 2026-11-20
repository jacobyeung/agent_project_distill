from common import *
import subprocess
records=[]
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','arm_missing_test','arm_negatives'):
 with (D/(name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-B','-s',str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=p.returncode));J.write(D/'TEST_RUNS.json',records)
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-3500:],flush=True)
