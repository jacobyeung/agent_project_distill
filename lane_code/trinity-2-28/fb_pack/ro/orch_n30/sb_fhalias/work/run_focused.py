"""Run the source report's focused suites without executing its launchers."""
import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1];T=Path(sys.argv[1]).resolve();label=sys.argv[2];group=sys.argv[3]
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
O=W/'work'/('focused_'+label)/group;O.mkdir(parents=True,exist_ok=True)
tmp=O/'tmp';tmp.mkdir(exist_ok=True);tempfile.tempdir=str(tmp)
os.environ.update(TMPDIR=str(tmp),R2_FIXTURES=str(S/'fixtures'),R2_PROOFS=str(O),R2_LANE_ROOT=str(S),LANE_TEST_OUTPUT=str(tmp))
sys.path[:0]=[str(T),str(W/'work/support')]
class RetainedDirectory:
    def __init__(self,suffix=None,prefix=None,dir=None,**kw):self.name=tempfile.mkdtemp(suffix=suffix,prefix=prefix,dir=str(tmp))
    def __enter__(self):return self.name
    def __exit__(self,*a):return False
    def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
reads=set();writes=set();blocked=[]
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2]
        writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)
        if writing:
            if not p.is_relative_to(W):blocked.append(str(p));raise PermissionError('OUTSIDE_WRITE:'+str(p))
            writes.add(str(p))
        elif p.is_relative_to(S.parent) or p.is_relative_to(W):reads.add(str(p))
        elif str(p).startswith(('/data','/home')):blocked.append(str(p));raise PermissionError('NFS_READ:'+str(p))
    if event in ('os.remove','os.rmdir','socket.connect','subprocess.Popen'):blocked.append(event);raise PermissionError('FORBIDDEN:'+event)
sys.addaudithook(audit)
import torch
torch.set_num_threads(8);torch.set_num_interop_threads(1)
groups={
 'main':['export_mutation17.HashTwin', 'tests.test_r1_build13.PopulationTests', 'tests.test_r1_build14.Build14', 'tests.test_r1_build15.Build15', 'tests.test_r1_build16.Build16', 'tests.test_r1_build17.Boundary', 'tests.test_r1_build17.Composition', 'tests.test_r1_build17.Rooms', 'tests.test_r1_build18.Admission18', 'tests.test_r1_build18.Rooms18', 'tests.test_r1_build19.Components19', 'tests.test_r1_build20.Review20', 'tests.test_r1_export17.Export17', 'tests.test_r2_build12.Build12', 'tests.test_r2_build3.Build3', 'tests.test_r2_build_n1.R1', 'tests.test_r2_n1fix.N1Fix', 'tests.test_r2_n1fix3.Confirmation3'],
 'edges':['edge_test16.Edges','stage_test16.Staging'],
 'producer':['export_edges17.ProducerEdges'],
 'r2':['tests.test_r2_data_path','tests.test_r2_host_runtime','tests.test_r2_launch_dispatch'],
}
class Result(unittest.TextTestResult):
    outcomes=[]
    def addSuccess(self,t):self.outcomes.append([t.id(),'PASS']);super().addSuccess(t)
    def addFailure(self,t,e):self.outcomes.append([t.id(),'FAIL']);super().addFailure(t,e)
    def addError(self,t,e):self.outcomes.append([t.id(),'ERROR']);super().addError(t,e)
    def addSkip(self,t,r):self.outcomes.append([t.id(),'SKIP',r]);super().addSkip(t,r)
result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromNames(groups[group]))
inputs={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads-writes) if Path(p).is_file()}
inputs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(W/'out'/('focused_'+label+'_'+group+'.json')).write_text(json.dumps(dict(input_sha256=inputs,modules=groups[group],tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),successful=result.wasSuccessful(),outcomes=result.outcomes,blocked=blocked),indent=2)+'\n')
print('RESULT',result.testsRun,len(result.failures),len(result.errors),'blocked',blocked)
sys.exit(not result.wasSuccessful())
