from common import *
import subprocess
A=L/'attic/build24m4j/arm_baseline';A.mkdir()
for n in ('arming_final','review_negatives','native_arm'):
 p=D/n
 if p.exists():p.rename(A/n)
names=('arm_tests','review_tests','coverage_tests','arm_missing_test','arm_negatives','native_arm_tests')
for name in (*names,'final_checks'):
 p=D/(name+'.log')
 if p.exists():p.rename(A/p.name)
records=J.load(D/'TEST_RUNS.json')
for name in names:
 with (D/(name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'bootstrap.py'),str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'B21C_PORTABLE':'1'})
 for row in records:
  if row['name']==name:row['returncode']=p.returncode
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-1800:],flush=True)
replace(D/'TEST_RUNS.json',json.dumps(records,indent=2)+'\n')
