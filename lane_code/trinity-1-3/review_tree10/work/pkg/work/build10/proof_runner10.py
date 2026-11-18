"""Bounded local tests with exact-source statement observations."""
from pathlib import Path
import hashlib, json, os, sys, tempfile, time, unittest
L=Path(__file__).resolve().parents[2]
B=L/'work/build10'
name=sys.argv[1]
out=B/'proofs'/name
out.mkdir(parents=True,exist_ok=True)
temp=L/'work/tmp'/name
temp.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(L/'work/tmp'), EAT1_TMP=str(temp), HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', XDG_CACHE_HOME=str(temp/'cache'), HF_HOME=str(temp/'hf'))
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
counter=0
def fixed_temp(suffix=None,prefix=None,dir=None):
    global counter
    counter+=1
    p=temp/f'{prefix or "case"}{counter:04d}{suffix or ""}'
    p.mkdir(parents=True,exist_ok=True)
    return str(p)
tempfile.mkdtemp=fixed_temp
class Retained:
    def __init__(self,*a,**kw):self.name=fixed_temp(*a,**kw)
    def __enter__(self):return self.name
    def __exit__(self,*a):return False
    def cleanup(self):pass
tempfile.TemporaryDirectory=Retained
hits={}
def line(code, number):
    if code.co_filename.startswith((str(B),str(L/'work/tree_r1'))):
        hits.setdefault(code.co_filename,set()).add(number)
    else:
        return sys.monitoring.DISABLE
sys.monitoring.use_tool_id(3,'build10')
sys.monitoring.register_callback(3,sys.monitoring.events.LINE,line)
sys.monitoring.set_events(3,sys.monitoring.events.LINE)
def size():return sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
receipts=[]
class Result(unittest.TextTestResult):
    def startTest(self,test):
        self.before=size()
        if self.before>200_000_000:raise RuntimeError('Temporary storage cap reached')
        super().startTest(test)
    def stopTest(self,test):
        after=size()
        receipts.append(dict(test=test.id(),before=self.before,after=after))
        if after>200_000_000:raise RuntimeError('Temporary storage cap reached')
        super().stopTest(test)
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[2:])
with (out/'test.log').open('w') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(suite)
sys.monitoring.set_events(3,0)
coverage={p:dict(sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest(),lines=sorted(lines)) for p,lines in hits.items() if Path(p).is_file()}
(out/'COVERAGE.json').write_text(json.dumps(coverage,indent=1)+'\n')
record=dict(run=result.testsRun,failures=[(t.id(),e) for t,e in result.failures],
            errors=[(t.id(),e) for t,e in result.errors],skips=result.skipped,storage=receipts)
(out/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors))))
sys.exit(not result.wasSuccessful())
