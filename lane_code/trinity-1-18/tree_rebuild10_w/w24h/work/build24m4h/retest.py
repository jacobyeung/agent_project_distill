import sys,subprocess,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
a=L/'attic/build24m4h/test_pass1';a.mkdir()
for name in ('arming_final','review_negatives','resolver','proofs','guard_q','guard_n','publication_q','publication_r','published_q','published_r'):
 p=D/name
 if p.exists():p.rename(a/name)
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','suites','offline'):
 p=D/(name+'.log')
 if p.exists():p.rename(a/p.name)
for name in ('TEST_RUNS.json','OFFLINE.json','ARM_TESTS.json','ARM_MISSING_DB_TEST.json'):
 p=D/name
 if p.exists():p.rename(a/name)
for n in ('guard_q','guard_n'):(D/n).mkdir()
with (D/'offline.log').open('w') as f:
 p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'offline.py')],stdout=f,stderr=subprocess.STDOUT)
print('offline',p.returncode,flush=True)
with (D/'suites.log').open('w') as f:
 p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'run_suites.py')],stdout=f,stderr=subprocess.STDOUT)
print('suites',p.returncode,flush=True)
