from common import *
import tempfile,unittest,importlib.util
tempfile.tempdir=str(D/'native_hosts');Path(tempfile.tempdir).mkdir()
sys.path.insert(0,str(L/'work/build21'))
import portable21c
portable21c.install()
from tests import test_host24j,test_host24l,test_host24n,test_host24l3,test_host24l4r
test_host24j.__file__=str(L.parent/'work/x24l3_back/work/tree_r1/tests/test_host24j.py')
def base(self):
 p=L.parent/'work/x24l3_back/work/tree_r1_base/student_pilot/r1_handover.py'
 spec=importlib.util.spec_from_file_location('student_pilot.handover24n_base',p)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
test_host24n.DonorPins.base=base
suite=unittest.TestSuite()
for module in (test_host24j,test_host24l,test_host24n,test_host24l3,test_host24l4r):suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
r=unittest.TextTestRunner(verbosity=2).run(suite)
J.write(D/'NATIVE_HOST_TESTS.json',dict(tests=r.testsRun,status='PASS' if r.wasSuccessful() else 'FAIL',skips=[str(x) for x in r.skipped],errors=[str(x) for x in r.errors],failures=[str(x) for x in r.failures]))
raise SystemExit(not r.wasSuccessful())
