import sys,subprocess,os,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4n'
records=[]
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','arm_negatives','native_arm_tests'):
 with (D/(name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 records.append(dict(name=name,returncode=p.returncode));(D/'TEST_RUNS.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-2200:],flush=True)
