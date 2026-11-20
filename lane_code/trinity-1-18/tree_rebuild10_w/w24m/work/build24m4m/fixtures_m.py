from common import *
import subprocess
records=[]
for name in ('command_tests_m','rcj_l_tests','sample_retest','pc_integration','mount_tests','rdiff_mount_test','rcj_contract_tests','plan_current','transport_tests','rcj_scan','qd_tests'):
 p=D/(name+'.py')
 if not p.exists():raise ValueError('Missing fixture: '+name)
 with (D/(name+'_m.log')).open('x') as f:
  child=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(p)],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=child.returncode));J.write(D/'FIXTURE_RUNS.json',records)
 print(name,child.returncode,flush=True)
 if child.returncode:print((D/(name+'_m.log')).read_text()[-4000:],flush=True)
