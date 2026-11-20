from common import *
import subprocess
for name in ('rcj_k','rcj_contract','plan_k','transport','extra'):
 p=D/name
 if p.exists():
  target=L/'attic/build24m4k'/('before_final_'+name)
  p.rename(target)
for name in ('transport_tests','extra_tests'):
 p=D/(name+'.py');s=p.read_text().replace("D/'p_tree'","L/'work/build24m4j/p_tree'").replace("D/'p_tree/launch_s1/b/s.py'","L/'work/build24m4j/p_tree/launch_s1/b/s.py'")
 replace(p,s)
records=[]
for name in ('plan_test','rcj_k_tests','rcj_contract_tests','transport_tests','extra_tests','rcj_scan'):
 p=D/(name+'.log')
 if p.exists():p.rename(L/'attic/build24m4k'/('before_final_'+p.name))
 with p.open('w') as f:
  result=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT)
 records.append(dict(name=name,returncode=result.returncode))
 J.write(D/'FINAL_TEST_RUNS.json',records)
 print(name,result.returncode,flush=True)
 if result.returncode:print(p.read_text()[-4000:],flush=True)
assert all(r['returncode']==0 for r in records)
