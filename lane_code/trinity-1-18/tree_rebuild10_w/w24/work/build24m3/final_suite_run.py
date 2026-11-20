from common import *
import subprocess
records=[]
for name in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','kit_tests','naming_tests'):
 with (D/(name+'_sealed.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=p.returncode))
 J.write(D/'FINAL_SUITES.json',records);print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'_sealed.log')).read_text()[-2500:],flush=True)
assert all(x['returncode']==0 for x in records)
