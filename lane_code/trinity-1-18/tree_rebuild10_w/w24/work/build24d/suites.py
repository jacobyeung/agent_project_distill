from pathlib import Path
import json,subprocess,sys,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
records=[]
for name in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','resolver600_tests','resolver23_tests','kit_tests'):
 with (D/(name+'.log')).open('w') as log:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=p.returncode));(D/'SUITES.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
