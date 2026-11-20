from common import *
a=L/'attic/build24m4j/suites_second';a.mkdir()
for name in ('arming_final','review_negatives','resolver','proofs','guard_q','guard_n','native_arm'):
 p=D/name
 if p.exists():p.rename(a/name)
for name in ('scans','kit_tests','naming_tests','guard_q_new','guard_n_new','guard_q_legacy','guard_n_legacy','resolver_tests','resolver600_tests','resolver23_tests','arm_tests','review_tests','coverage_tests','arm_missing_test','arm_negatives','native_arm_tests','suites'):
 p=D/(name+'.log')
 if p.exists():p.rename(a/p.name)
p=D/'TEST_RUNS.json';p.rename(a/p.name)
for n in ('guard_q','guard_n'):(D/n).mkdir()
