"""Same desired-behavior tests against each tree; only host/environment are mocked."""
import ast, hashlib, json, os, sys, unittest
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parents[1]
T=Path(sys.argv[1]).resolve(); label=sys.argv[2]
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
sys.path[:0]=[str(T),str(W/'work/support')]
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
from student_pilot.p3_provenance import load,pinned
from student_pilot.job_env import key, ALIASES
from launch_r2.build import bad_string
from naming21 import scan_python_environment
cfgpath=S/'work/build21/proofs/capacity/400/request_config.json'
cfg=load(cfgpath); manifests={k:pinned(v) for k,v in cfg['r1_training']['routing_inputs'].items()}
assert all(load(p)['count']==0 and load(p)['row_bindings']=={} for p in manifests.values())
hashes=load(S/'work/build21/kits/q/b/wh.json')
u=os.uname(); records=[]; reads={str(cfgpath),str(Path(__file__).resolve())}

def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2]
        writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)
        if writing and not p.is_relative_to(W): raise PermissionError('OUTSIDE_WRITE:'+str(p))
        if not writing and p.is_relative_to(S.parent) or not writing and p.is_relative_to(W):reads.add(str(p))
    if event in ('os.remove','os.rmdir','socket.connect','subprocess.Popen'):raise PermissionError('FORBIDDEN:'+event)
sys.addaudithook(audit)

def boundary(env,host):
    return patch.object(os,'uname',return_value=os.uname_result((u.sysname,host,u.release,u.version,u.machine))),patch.dict(os.environ,env,clear=True)

CASES=[('alias_one',{'Q_E7':'1'},'fixture-frame-host',True),
 ('missing',{},'fixture-frame-host',False),('alias_zero',{'Q_E7':'0'},'fixture-frame-host',False),
 ('trinity',{'Q_E7':'1','STUDENT_R2_FRAME_HOST':'1'},'trinity-1-18',False),
 ('local',{'Q_E7':'1','STUDENT_R2_FRAME_HOST':'1','STUDENT_R2_LOCAL_NODE':'1'},'fixture-frame-host',False),
 ('native_one',{'STUDENT_R2_FRAME_HOST':'1'},'fixture-frame-host',True),
 ('native_zero',{'STUDENT_R2_FRAME_HOST':'0'},'fixture-frame-host',False),
 ('worker_translated_k6',{'K6':'1','STUDENT_R2_FRAME_HOST':'1'},'fixture-frame-host',True),
 ('k6_alone',{'K6':'1'},'fixture-frame-host',False),
 ('alias_zero_native_one',{'Q_E7':'0','STUDENT_R2_FRAME_HOST':'1'},'fixture-frame-host',False),
 ('alias_one_native_zero',{'Q_E7':'1','STUDENT_R2_FRAME_HOST':'0'},'fixture-frame-host',True)]

# Baseline contract: Q_E7 is ignored. The patched contract gives it precedence.
if 'STUDENT_R2_FRAME_HOST' not in ALIASES:
    baseline = {'alias_one':False, 'alias_zero_native_one':True, 'alias_one_native_zero':False}
    CASES = [(name,env,host,baseline.get(name,expected)) for name,env,host,expected in CASES]

class Boundary(unittest.TestCase):
    def test_intake(self):
        for case,env,host,expected in CASES:
            for family,manifest in manifests.items():
                with self.subTest(case=case,family=family):
                    a,b=boundary(env,host)
                    with a,b:
                        try:
                            rows,report=intake(manifest,limit=None);status=True;error=None;self.assertEqual(rows,[])
                        except ValueError as e:status=False;error=str(e);self.assertEqual(error,'Local slices must contain at most 2000 rows per family')
                        records.append(dict(operation='intake',case=case,family=family,environment=env,host=host,accepted=status,error=error,resolved_key=key('STUDENT_R2_FRAME_HOST')))
                    self.assertEqual(status,expected)
    def test_materialize_host_boundary(self):
        for case,env,host,expected in CASES:
            with self.subTest(case=case):
                a,b=boundary(env,host)
                with a,b:
                    with self.assertRaises(ValueError) as caught:
                        materialize(list(manifests.values()),W/'work'/('boundary_'+label)/case,full=True)
                error=str(caught.exception)
                passed=error=='Full materialization requires the bound sampling table'
                self.assertIn(error,('Full materialization requires the bound sampling table','Full materialization requires an explicit frame-host admission','Full store forbidden on a local node; use slices of at most 2000 rows per family'))
                records.append(dict(operation='materialize',case=case,environment=env,host=host,host_boundary_passed=passed,error=error))
                self.assertEqual(passed,expected)
    def test_limits(self):
        for limit in (0,2001,-1,True):
            a,b=boundary({'Q_E7':'1','STUDENT_R2_FRAME_HOST':'1'},'fixture-frame-host')
            with a,b,self.assertRaisesRegex(ValueError,'Local slices'): intake(manifests['units'],limit=limit)
        a,b=boundary({},'trinity-1-18')
        with a,b:self.assertEqual(intake(manifests['units'],limit=2000)[0],[])
    def test_local_marker(self):
        root=W/'work'/('marker_'+label);root.mkdir(exist_ok=True);(root/'.r2_local_node').touch()
        old=Path.cwd()
        try:
            os.chdir(root);a,b=boundary({'Q_E7':'1','STUDENT_R2_FRAME_HOST':'1'},'fixture-frame-host')
            with a,b,self.assertRaisesRegex(ValueError,'Full store forbidden'):
                materialize(list(manifests.values()),root/'output',full=True)
        finally:os.chdir(old)
    def test_scanner(self):
        def check(value,where):
            if bad_string(value,hashes):raise ValueError('INPUT_NAME:'+where+':'+value)
        for name,accept in [('Q_E7',True),('STUDENT_R2_FRAME_HOST',False)]:
            source="import os\nos.environ[%r]='1'\n"%name
            try:scan_python_environment(ast.parse(source),check,'b/h.py');passed=True;error=None
            except ValueError as e:passed=False;error=str(e)
            records.append(dict(operation='scanner',source=source,accepted=passed,error=error));self.assertEqual(passed,accept)

result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boundary))
reads.update(str(p) for p in T.rglob('*') if p.is_file())
reads.update(str(p) for p in (W/'work/support').glob('*.py'))
reads.add(str(S/'work/build21/kits/q/b/wh.json'))
inputs={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads) if Path(p).is_file()}
(W/'out'/('boundary_'+label+'.json')).write_text(json.dumps(dict(input_sha256=inputs,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful(),records=records),indent=2)+'\n')
sys.exit(not result.wasSuccessful())
