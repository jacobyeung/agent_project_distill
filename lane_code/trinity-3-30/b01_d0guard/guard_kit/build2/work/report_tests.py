from pathlib import Path
import importlib.util,json,os,sys,tempfile,unittest,uuid
B=Path(__file__).resolve().parents[1];R=B.parents[1]/'guard_kit/report'
class RetainedDirectory:
 def __init__(self,*args,**kwargs):
  path=B/'work/report_fixtures'/uuid.uuid4().hex;path.mkdir(parents=True);self.name=str(path)
 def __enter__(self):return self.name
 def __exit__(self,*args):return False
 def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
os.environ['GUARD_READ_PATH']=str(R/'guard_read.py')
spec=importlib.util.spec_from_file_location('report_tests',R/'tests/test_guard_read.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
(B/'out/REPORT_TESTS.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'),indent=2)+'\n')
sys.exit(not r.wasSuccessful())
