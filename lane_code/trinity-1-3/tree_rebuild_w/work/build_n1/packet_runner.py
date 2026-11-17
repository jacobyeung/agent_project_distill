from pathlib import Path
import os
import sys
import json
import tempfile
import shutil
import signal
L=Path(__file__).resolve().parents[2]
tree=L/'work/tree_r1'
overlay=Path(os.environ.get('R4_OVERLAY', str(L/'work/src_r6')))
import importlib.abc, importlib.util
class OverlayFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        parts=fullname.split('.')
        if parts[0]=='derivgen': parts=['generator','derivgen_v7']+parts
        candidate=overlay/Path(*parts).with_suffix('.py')
        if candidate.is_file():
            return importlib.util.spec_from_file_location(fullname,candidate)
if sys.argv[1]=='overlay':sys.meta_path.insert(0,OverlayFinder())
if '/work/mutation_r6/' in sys.argv[1] and '/round_' not in sys.argv[1]:
    raise SystemExit('Pre-final mutation evidence superseded; no test launched.')
tag=sys.argv[2]
os.chdir(tree)
sys.path[:0]=[str(tree),str(L/'work/contracts_r6/tests_r6')]
root=L/'work/tmp/packet_r6'
proof=L/'work/build_n1/proofs/packet'
proof.mkdir(parents=True,exist_ok=True)
root.mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(root)
tempfile.TemporaryDirectory.cleanup=lambda self: self._finalizer.detach()
tempfile.TemporaryDirectory._cleanup=classmethod(lambda cls,*args,**kwargs: None)
shutil.rmtree=lambda *args,**kwargs: None
for key in ('STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT','LANE_TEST_OUTPUT','TMPDIR'):
    os.environ[key]=str(root)
os.environ['CLEAN_VSI590K_WORKSPACE']=str(tree)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
def audit(event,args):
    if event in ('os.system','socket.connect'):
        raise PermissionError('CPU proof does not launch external commands or network connections')
    if event in ('os.remove','os.rmdir'):
        raise PermissionError('Proof retains all fixtures')
    if event=='open' and isinstance(args[0],(str,bytes)):
        path=Path(os.fsdecode(args[0])).absolute()
        if str(path).startswith(('/home/','/data/','/data2/','/data3/')):
            raise PermissionError('Proof does not access external records: '+str(path))
        flags=args[2]
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT) and not path.is_relative_to(L):
            raise PermissionError('Proof writes only in lane: '+str(path))
sys.addaudithook(audit)
sys.path.insert(0,str(L/'work/build5'))
from compact_tmp import inventory, compact
sizes=[]
import pytest
class Coverage:
    current='collection'
    hits={}
    results={}
    def pytest_collection_modifyitems(self,items):
        first=os.environ.get('R6_MUTATION_FIRST')
        if first:items.sort(key=lambda item: first not in item.nodeid)
    def pytest_collectstart(self,collector):
        self.current=collector.nodeid+' [collection]'
    paths={}
    tracked=set(json.loads((L/'work/contracts_r6/PATCH_MANIFEST_R6.json').read_text())['files'])
    tracked.update('tests_r6/'+p.name for p in (L/'work/contracts_r6/tests_r6').glob('*.py'))
    def trace(self, frame,event,arg):
        filename=frame.f_code.co_filename
        if filename not in self.paths:
            rel = filename[len(str(overlay))+1:] if filename.startswith(str(overlay)+'/') else filename[len(str(tree))+1:] if filename.startswith(str(tree)+'/') else None
            if filename.startswith(str(L/'work/contracts_r6/tests_r6')+'/'):rel='tests_r6/'+Path(filename).name
            self.paths[filename]=rel if rel in self.tracked else None
        name=self.paths[filename]
        if name is None:return None
        if event=='line':
            self.hits.setdefault(name,{}).setdefault(str(frame.f_lineno),set()).add(self.current)
        return self.trace
    def pytest_runtest_setup(self,item):
        measured=sum(inventory(L/'work/tmp').values())
        sizes.append(dict(test=item.nodeid,phase='before',bytes=measured))
        if measured>200*1024**2:raise RuntimeError('temporary storage policy')
        self.current=item.nodeid
        (root/'current_test.txt').write_text(item.nodeid)
        signal.signal(signal.SIGALRM,lambda *args: (_ for _ in ()).throw(TimeoutError('CPU test exceeded 90 seconds')))
        signal.alarm(90)
    def pytest_runtest_teardown(self,item):
        signal.alarm(0)
        measured=sum(inventory(L/'work/tmp').values())
        sizes.append(dict(test=item.nodeid,phase='after',bytes=measured))
        compact(root)
        if measured>200*1024**2:raise RuntimeError('temporary storage policy')
    def pytest_runtest_logreport(self,report):
        if report.when=='call' or report.failed or report.skipped:
            self.results[report.nodeid]=dict(outcome=report.outcome,when=report.when,
                detail=str(report.longrepr) if report.failed or report.skipped else '')
cov=Coverage()
args=(json.loads((L/('work/base_tests_extra.json' if sys.argv[3]=='base-extra' else 'work/base_tests.json')).read_text())
      if sys.argv[3].startswith('base') else ([] if sys.argv[3]=='tree' else [str(L/'work/contracts_r6/tests_r6')]))
args+=['-q','-p','no:cacheprovider','--basetemp',str(root/'pytest'), '--tb=short',
       '--log-file', str(root/'pytest.log'),'--continue-on-collection-errors']
if len(sys.argv)>4: args+=sys.argv[4:]
if not sys.argv[3].startswith('base') and not os.environ.get('R6_NO_TRACE'):sys.settrace(cov.trace)
result=pytest.main(args,plugins=[cov])
sys.settrace(None)
(proof/'results.json').write_text(json.dumps(cov.results,indent=2))
(proof/'trace.json').write_text(json.dumps({k:{n:sorted(ts) for n,ts in v.items()} for k,v in cov.hits.items()}))
(proof/'temporary_sizes.json').write_text(json.dumps(sizes,indent=2))
raise SystemExit(result)
