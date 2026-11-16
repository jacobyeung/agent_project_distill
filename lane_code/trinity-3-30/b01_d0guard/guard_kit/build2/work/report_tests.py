from pathlib import Path
import importlib.util,json,os,sys,tempfile,unittest,uuid
import hashlib
B=Path(__file__).resolve().parents[1];R=B.parents[1]/'guard_kit/report'
sys.path.insert(0,str(B/'work'))
from report_review_tests import suite as review_suite
REPORT_SHA256='5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11'
class ReportSourcePin(unittest.TestCase):
 def test_report_source_matches_authorized_pin(self):
  self.assertEqual(hashlib.sha256((R/'guard_read.py').read_bytes()).hexdigest(),REPORT_SHA256)
class RetainedDirectory:
 def __init__(self,*args,**kwargs):
  path=B/'work/report_fixtures'/uuid.uuid4().hex;path.mkdir(parents=True);self.name=str(path)
 def __enter__(self):return self.name
 def __exit__(self,*args):return False
 def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
os.environ['GUARD_READ_PATH']=str(R/'guard_read.py')
spec=importlib.util.spec_from_file_location('report_tests',R/'tests/test_guard_read.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
suite=unittest.defaultTestLoader.loadTestsFromModule(m)
suite.addTests(review_suite(m))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ReportSourcePin))
r=unittest.TextTestRunner(verbosity=2).run(suite)
(B/'out/REPORT_TESTS.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL',report_sha256=REPORT_SHA256),indent=2)+'\n')
sys.exit(not r.wasSuccessful())
