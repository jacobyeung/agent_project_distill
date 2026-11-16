import importlib.util,json,pathlib,sys,tempfile,unittest,uuid
B=pathlib.Path(__file__).resolve().parents[1];R=B.parents[1]/'guard_kit/report'
# Retain all fixture directories inside the build.
class RetainedDirectory:
 def __init__(self,*args,**kwargs):
  p=B/'work/report_fixtures'/uuid.uuid4().hex;p.mkdir(parents=True);self.name=str(p)
 def __enter__(self):return self.name
 def __exit__(self,*args):return False
 def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
spec=importlib.util.spec_from_file_location('guard_report_tests',R/'tests/test_guard_read.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
suite=unittest.defaultTestLoader.loadTestsFromModule(m);r=unittest.TextTestRunner(verbosity=2).run(suite)
(B/'out/REPORT_TESTS.json').write_text(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),source=str(R/'tests/test_guard_read.py'),adaptation='Temporary fixture directories retained in build; report and test source unchanged'),indent=2)+'\n')
sys.exit(not r.wasSuccessful())
