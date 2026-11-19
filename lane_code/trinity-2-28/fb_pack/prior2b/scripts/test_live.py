import sys,json,hashlib,unittest,time
from pathlib import Path
from cpu_guard import install
W=Path(__file__).resolve().parents[1];tree=sys.argv[1];T=W/'work'/tree
install(W,tree);sys.path.insert(0,str(T))
modules=sys.argv[2:] or ['tests.test_r1_direction_prior','tests.test_r1_build13','tests.test_r1_build14','tests.test_r1_build16','tests.test_host24j']
modules=[m for m in modules if (T/Path(m.replace('.','/')).with_suffix('.py')).is_file()]
class Result(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.records=[]
 def addSuccess(self,t):super().addSuccess(t);self.records.append(dict(id=t.id(),status='PASS'))
 def addError(self,t,e):super().addError(t,e);self.records.append(dict(id=t.id(),status='ERROR',error=str(e[1])))
 def addFailure(self,t,e):super().addFailure(t,e);self.records.append(dict(id=t.id(),status='FAIL',error=str(e[1])))
 def addSkip(self,t,r):super().addSkip(t,r);self.records.append(dict(id=t.id(),status='SKIP',reason=r))
suite=unittest.TestSuite()
for module in modules:
 try:suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
 except Exception as error:suite.addTest(unittest.loader._FailedTest(module,error))
with (W/'out'/('INTEGRATION_'+tree+'.log')).open('w') as f:r=unittest.TextTestRunner(stream=f,verbosity=2,resultclass=Result).run(suite)
inputs=[]
paths=[Path(__file__),W/'scripts/cpu_guard.py',*[p for p in sorted(T.rglob('*')) if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and 'artifacts' not in p.parts]]
original=W/'work/tree_r1_base/launch_r1/entry.py'
if original.is_file():paths.append(original.resolve())
for p in paths:inputs.append(dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
out=dict(status='PASS' if r.wasSuccessful() else 'FAIL',tree=tree,tests=r.testsRun,errors=len(r.errors),failures=len(r.failures),skips=len(r.skipped),records=r.records,inputs=inputs)
(W/'out'/('INTEGRATION_'+tree+'.json')).write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('records','inputs')},flush=True)
