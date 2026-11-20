from common import *
a=L/'attic/build24m4j/suites_third';a.mkdir()
for name in ('arming_final','review_negatives','resolver','proofs','guard_q','guard_n','native_arm'):
 p=D/name
 if p.exists():p.rename(a/name)
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','arm_negatives','native_arm_tests','suites'):
 p=D/(name+'.log')
 if p.exists():p.rename(a/p.name)
(D/'TEST_RUNS.json').rename(a/'TEST_RUNS.json')
for n in ('guard_q','guard_n'):(D/n).mkdir()
# Rebuild the delta after resealing the complete import closure.
(D/'upload').rename(L/'attic/build24m4j/upload_before_batches')
for name in ('UPLOADS_24M4J.json','UPLOADS_24M4J.list','UPLOADS_24M4J_GO.json','RCJ_USAGE.md'):
 (L/'out'/name).rename(L/'attic/build24m4j'/('before_batches_'+name))
