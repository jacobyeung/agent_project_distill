from pathlib import Path
import os,sys,json,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'))
O=B/'proofs'/os.environ.get('B14_PROOF','tests');O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
os.environ.update(LANE_TEST_OUTPUT=str(L/'work/tmp'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    HF_HOME=str(L/'work/tmp/hf'),XDG_CACHE_HOME=str(L/'work/tmp/cache'),TORCH_HOME=str(L/'work/tmp/torch'))
import tempfile
tempfile.tempdir=str(L/'work/tmp')
class RetainedDirectory:
    def __init__(self,suffix=None,prefix=None,dir=None,**kw):
        self.name=tempfile.mkdtemp(suffix=suffix,prefix=prefix,dir=str(L/'work/tmp'))
    def __enter__(self):return self.name
    def __exit__(self,*args):return False
    def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
from monitor9 import Monitor
m=Monitor(T)
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:] or ['tests.test_r1_build14'])
class Result(unittest.TextTestResult):
    sizes=[]
    def startTest(self,t):
        n=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert n<=200_000_000
        self.sizes.append(dict(test=str(t),phase='before',bytes=n));super().startTest(t)
    def stopTest(self,t):
        n=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert n<=200_000_000
        self.sizes.append(dict(test=str(t),phase='after',bytes=n));super().stopTest(t)
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
m.save(O)
(O/'TESTS.json').write_text(json.dumps(dict(tests=r.testsRun,failures=r.failures,errors=r.errors,
    successful=r.wasSuccessful(),storage=r.sizes),default=str,indent=2))
raise SystemExit(not r.wasSuccessful())
