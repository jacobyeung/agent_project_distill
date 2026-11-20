from common import *
import unittest, tempfile
os.environ.update(R2_PROOFS=str(D/'tree_tests'),R2_LANE_ROOT=str(L),R2_TREE=str(T),STUDENT_PILOT_TEST_OUTPUT=str(D/'tree_tests'),LANE_TEST_OUTPUT=str(D/'tree_tests'),S1_CPU_REHEARSAL='0')
(D/'tree_tests').mkdir(exist_ok=True);tempfile.tempdir=str(D/'tmp')
mods=['tests.test_r1_processor_compat','tests.test_carrier_c1_single_image','tests.test_host24j','tests.test_carrier_c1_run']
suite=unittest.defaultTestLoader.loadTestsFromNames(mods)
r=unittest.TextTestRunner(verbosity=2).run(suite)
J.write(D/'TREE_TESTS.json',dict(modules=mods,tests=r.testsRun,failures=[(str(t),s) for t,s in r.failures],errors=[(str(t),s) for t,s in r.errors],skipped=[(str(t),s) for t,s in r.skipped],successful=r.wasSuccessful()))
raise SystemExit(not r.wasSuccessful())
