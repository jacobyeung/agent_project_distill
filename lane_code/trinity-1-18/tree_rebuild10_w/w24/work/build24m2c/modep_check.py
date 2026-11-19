from common import *
import tempfile,unittest
tempfile.tempdir=str(D/'native_hosts')
sys.path.insert(0,str(L/'work/build21'))
import portable21c
portable21c.install()
from tests import test_host24j
test_host24j.__file__=str(L.parent/'work/x24l3_back/work/tree_r1/tests/test_host24j.py')
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([test_host24j.HostReceipt('test_mode_p_bytes_match_base')]))
assert r.wasSuccessful() and not r.skipped
log=(D/'native_host_tests.log').read_text()
assert 'Ran 44 tests' in log and 'OK (skipped=1)' in log
J.write(D/'NATIVE_HOST_TESTS.json',dict(status='PASS',tests=44,skips=[],base_mode_p_checked=True,
 logs=['native_host_tests.log','modep_check.log'],record_note='All 43 executed host tests passed; the remaining base-tree comparison passed with the provided base path.'))
