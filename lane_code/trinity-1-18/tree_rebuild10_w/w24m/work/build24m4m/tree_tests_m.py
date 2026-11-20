from common import *
import unittest,tempfile
os.environ.update(R2_PROOFS=str(D/'tree_tests'),R2_LANE_ROOT=str(L),R2_TREE=str(T),STUDENT_PILOT_TEST_OUTPUT=str(D/'tree_tests'),LANE_TEST_OUTPUT=str(D/'tree_tests'),S1_CPU_REHEARSAL='0')
(D/'tree_tests').mkdir(exist_ok=True);tempfile.tempdir=str(D/'tmp')
records=[]
for module,count in [('tests.test_host24j',15),('tests.test_r1_processor_compat',3)]:
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(module))
 records.append(dict(module=module,tests=r.testsRun,failures=[(str(t),s) for t,s in r.failures],errors=[(str(t),s) for t,s in r.errors],skipped=[(str(t),s) for t,s in r.skipped],successful=r.wasSuccessful()))
 J.write(D/'TREE_TESTS.json',records)
 assert r.wasSuccessful() and r.testsRun==count and not r.skipped
