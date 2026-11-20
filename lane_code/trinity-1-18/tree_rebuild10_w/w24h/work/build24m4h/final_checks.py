import sys,subprocess,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
a=L/'attic/build24m4h/test_pass2';a.mkdir()
for name in ('arming_final','review_negatives','native_arm','resolver','proofs','guard_q','guard_n'):
 p=D/name
 if p.exists():p.rename(a/name)
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','suites','native_arm_tests','audit'):
 p=D/(name+'.log')
 if p.exists():p.rename(a/p.name)
for name in ('TEST_RUNS.json','ARM_TESTS.json','ARM_MISSING_DB_TEST.json','NATIVE_ARM_TESTS.json','INVARIANTS.json'):
 p=D/name
 if p.exists():p.rename(a/name)
for n in ('guard_q','guard_n'):(D/n).mkdir()
with (D/'suites.log').open('w') as f:
 subprocess.run([sys.executable,'-I','-s','-B',str(D/'run_suites.py')],stdout=f,stderr=subprocess.STDOUT,check=True)
for name in ('native_arm_tests','audit'):
 with (D/(name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT)
 print(name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-2000:],flush=True)
