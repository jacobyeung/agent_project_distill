"""Bounded unittest runner with standard-library line tracing and durable evidence."""
import ast
import difflib
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback
import unittest
import multiprocessing.process
import subprocess
L=Path(__file__).resolve().parents[2]
tree=Path(os.environ.get('R2_TREE', L/'work/tree_r1')).resolve()
sys.path.insert(0,str(tree))
temp_budget_root=Path(os.environ['TMPDIR'])
private_tmp=temp_budget_root/('run_'+str(time.time_ns()))
private_tmp.mkdir()
os.environ['TMPDIR']=str(private_tmp)
tempfile.tempdir=str(private_tmp)
class RetainedDirectory:
    def __init__(self,suffix=None,prefix=None,dir=None,**kwargs):
        self.name=tempfile.mkdtemp(suffix=suffix,prefix=prefix,dir=str(private_tmp))
    def __enter__(self):return self.name
    def __exit__(self,*args):return False
    def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
output=Path(sys.argv[1]).resolve()
output.mkdir(parents=True,exist_ok=False)
os.environ['R2_PROOFS']=str(output)
os.environ['R2_FIXTURES']=str(L/'fixtures')
hits={}
locations={}
monitor=sys.monitoring
monitor.use_tool_id(4,'bounded-proof')
def started(code,offset):
    if code.co_filename.startswith(str(tree)+'/'):
        monitor.set_local_events(4,code,monitor.events.LINE)
    return monitor.DISABLE
def line(code,number):
    hits.setdefault(code.co_filename,set()).add(number)
monitor.register_callback(4,monitor.events.PY_START,started)
monitor.register_callback(4,monitor.events.LINE,line)
snapshots={str(p.relative_to(tree)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tree.rglob('*.py')}
denied=[]
def audit(event,args):
    if event in ('os.'+'remove','os.'+'rmdir','shutil.'+'rmtree','os.system','socket.connect','socket.bind','os.fork','os.posix_spawn'):
        denied.append(dict(event=event,path=str(args[0])[:300] if args else ''))
        raise PermissionError('Proof policy refused '+event)
    if event=='subprocess.Popen':
        executable,command=args[:2]
        denied.append(dict(event=event,path=str(executable)))
        raise PermissionError('Package proof forbids unaudited child processes')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        mode,flags=args[1:3]
        writing=bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT))
        temporary=private_tmp
        inside=p==L or L in p.parents or p==output or output in p.parents or p==temporary or temporary in p.parents
        library=any(p==q or q in p.parents for q in (Path(sys.prefix),Path(sys.base_prefix),Path('/usr'),Path('/etc'),Path('/proc'),Path('/sys'),Path('/dev')))
        if writing and not inside and p!=Path('/dev/null') or not writing and not inside and not library:
            denied.append(dict(event=event,path=str(p),writing=writing))
            raise PermissionError('Proof file is outside package/runtime: '+str(p))
if os.environ.get('R2_PACKAGE_AUDIT')=='1':
    sys.addaudithook(audit)
    def no_child(*args,**kwargs):
        denied.append(dict(event='child_process',path='blocked'))
        raise PermissionError('Package proof forbids unaudited child processes')
    multiprocessing.process.BaseProcess.start=no_child
    subprocess._fork_exec=no_child
    import _posixsubprocess
    _posixsubprocess.fork_exec=no_child
def size(path):
    total=0
    for p in Path(path).rglob('*'):
        try:
            if p.is_file() and not p.is_symlink():total+=p.stat().st_size
        except FileNotFoundError:
            continue
    return total
current_result=None
lane=Path(os.environ.get('R2_LANE_ROOT',L))
base_lane_bytes=size(lane)-size(temp_budget_root)
reserve=int(os.environ.get('R2_TEST_RESERVE','200000000'))
if reserve<200_000_000:
    if len(sys.argv)<3 or reserve<20_000_000:
        raise ValueError('Reduced reserve requires explicit bounded test names')
    import resource
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE)
    resource.setrlimit(resource.RLIMIT_FSIZE,(min(soft,reserve),min(hard,reserve)))
class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        global current_result
        super().__init__(*args,**kwargs)
        current_result=self
    def startTest(self,test):
        if size(temp_budget_root) > 200_000_000:
            raise RuntimeError('Temporary storage cap reached')
        if base_lane_bytes+size(output)+size(temp_budget_root)>4_000_000_000-reserve:
            raise RuntimeError('Lane storage reserve reached; no further tests started')
        self.before=set(Path(os.environ['TMPDIR']).iterdir())
        super().startTest(test)
    def stopTest(self,test):
        super().stopTest(test)
        if size(temp_budget_root) > 200_000_000:
            raise RuntimeError('Temporary storage cap reached')
        # Completed test products become permanent proof artifacts by rename;
        # no checkpoint, store, or cache is copied. Index every former location.
        destination=output/'artifacts'/test.id()
        for p in sorted(set(Path(os.environ['TMPDIR']).iterdir())-self.before):
            destination.mkdir(parents=True,exist_ok=True)
            target=destination/p.name
            p.rename(target)
            locations[str(p)]=str(target)
        (output/'artifact_locations.json').write_text(json.dumps(locations,indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps(dict(completed=self.testsRun,failures=len(self.failures),
            errors=len(self.errors),skips=len(self.skipped),last=str(test)))+'\n')
pattern='test_*.py' if os.environ.get('R2_ALL_TESTS')=='1' else 'test_r2*.py'
names=sys.argv[2:] or ['tests.'+p.stem for p in sorted((tree/'tests').glob(pattern))]
monitor.set_events(4,monitor.events.PY_START)
fatal=None
try:
    suite=unittest.TestSuite()
    for name in names:
        try:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
        except BaseException as error:
            message=type(error).__name__+': '+str(error)
            def import_failure(message=message):
                raise RuntimeError(message)
            suite.addTest(unittest.FunctionTestCase(import_failure,description=name))
    (output/'TEST_INVENTORY.json').write_text(json.dumps(dict(modules=names,discovered_tests=suite.countTestCases()),indent=2)+'\n')
    with (output/'tests.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
except BaseException:
    fatal=traceback.format_exc()
    result=current_result
finally:
    monitor.set_events(4,0)
(output/'hits.json').write_text(json.dumps({str(Path(k).relative_to(tree)):sorted(v) for k,v in hits.items()}))
record=dict(tests=result.testsRun,failures=[(str(t),e) for t,e in result.failures],
            errors=[(str(t),e) for t,e in result.errors],skips=[(str(t),e) for t,e in result.skipped],
            tmp_bytes=size(os.environ['TMPDIR']))
record['fatal']=fatal
(output/'results.json').write_text(json.dumps(record,indent=2)+'\n')
(output/'source_hashes.json').write_text(json.dumps(snapshots,indent=2)+'\n')
(output/'policy_refusals.json').write_text(json.dumps(denied,indent=2)+'\n')
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in record.items()}))
sys.exit(bool(fatal) or not result.wasSuccessful())
