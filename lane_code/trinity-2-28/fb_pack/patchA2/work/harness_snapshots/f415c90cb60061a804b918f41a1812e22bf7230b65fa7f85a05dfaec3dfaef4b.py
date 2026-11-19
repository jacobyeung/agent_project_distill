if __name__ != '__main__':
    raise ImportError('CPU_TEST_WORKERS_UNAVAILABLE: the sandbox does not support worker processes')
"""Run CPU tests with retained fixtures and the dispatch's filesystem restrictions."""
import hashlib, json, os, resource, sys, tempfile, traceback, unittest, types
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RUNNER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
TREE = ROOT/'work'/sys.argv[1]
LABEL = sys.argv[2]
RO = ROOT.parent/'ro/orch_n30'
OUT = ROOT/'work/test_runs'/LABEL
OUT.mkdir(parents=True, exist_ok=True)
TMP = OUT/'tmp'; TMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TMP)
os.environ.update(TMPDIR=str(TMP), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', XDG_CACHE_HOME=str(OUT/'cache'),
    HF_HOME=str(OUT/'hf'), TORCH_HOME=str(OUT/'torch'), MPLCONFIGDIR=str(OUT/'mpl'),
    R2_FIXTURES=str(RO/'tree_rebuild10_w/w21/fixtures'),
    R2_LANE_ROOT=str(RO/'tree_rebuild10_w/w21'), R2_PROOFS=str(OUT),
    LANE_TEST_OUTPUT=str(OUT), B2_TEST_OUTPUT=str(OUT), STUDENT_PILOT_TEST_OUTPUT=str(OUT/'pilot'),
    STUDENT_CONVERTER_TEST_OUTPUT=str(OUT/'converter'), CLEAN_VSI590K_TEST_ROOT=str(OUT/'clean'),
    CLEAN_VSI590K_WORKSPACE=str(TREE), GV_FIX_ROOT=str(OUT),
    OMP_NUM_THREADS='16', MKL_NUM_THREADS='16', OPENBLAS_NUM_THREADS='16', STUDENT_IO_THREADS='1')
resource.setrlimit(resource.RLIMIT_AS, (38*1024**3, 38*1024**3))
os.chdir(TREE)
sys.path[:0] = [str(TREE), str(ROOT/'work/support'), str(TREE/'generator/derivgen_v7'),
                str(TREE/'generator/ground_rows_out')]
class RetainedDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(TMP))
    def __enter__(self): return self.name
    def __exit__(self, *args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory = RetainedDirectory
reads, writes, blocked = set(), set(), []
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        mode, flags = args[1:3]
        writing = isinstance(mode, str) and any(c in mode for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)
        if writing:
            if not p.is_relative_to(ROOT):
                blocked.append('OUTSIDE_WRITE:'+str(p)); raise PermissionError(blocked[-1])
            writes.add(str(p))
        elif str(p).startswith(('/data', '/home')):
            blocked.append('NFS_READ:'+str(p)); raise PermissionError(blocked[-1])
        elif p.is_relative_to(ROOT.parent) or p.is_relative_to(RO): reads.add(str(p))
    if event in ('os.remove', 'os.rmdir', 'os.kill', 'os.killpg', 'socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'):
        blocked.append('FORBIDDEN:'+event); raise PermissionError(blocked[-1])
    if event in ('os.mkdir', 'os.rename', 'os.symlink'):
        paths = args[:2] if event == 'os.rename' else (args[1],) if event == 'os.symlink' else args[:1]
        for path in paths:
            if isinstance(path, (str, bytes)) and not Path(os.fsdecode(path)).absolute().is_relative_to(ROOT):
                blocked.append('OUTSIDE_WRITE:'+str(path)); raise PermissionError(blocked[-1])
sys.addaudithook(audit)
import multiprocessing.process
def refuse_worker(self):
    raise PermissionError('CPU_TEST_WORKERS_UNAVAILABLE: worker processes are disabled in the sandbox')
multiprocessing.process.BaseProcess.start = refuse_worker
import concurrent.futures
original_thread_pool_init = concurrent.futures.ThreadPoolExecutor.__init__
def capped_thread_pool_init(self, max_workers=None, *args, **kwargs):
    return original_thread_pool_init(self, min(max_workers or 16, 16), *args, **kwargs)
concurrent.futures.ThreadPoolExecutor.__init__ = capped_thread_pool_init
import torch
torch.set_num_threads(16)
torch.set_num_interop_threads(1)
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.outcomes=[]
    def addSuccess(self,t): self.outcomes.append(dict(test=t.id(),status='PASS')); super().addSuccess(t)
    def addFailure(self,t,e): self.outcomes.append(dict(test=t.id(),status='FAIL',traceback=self._exc_info_to_string(e,t))); super().addFailure(t,e)
    def addError(self,t,e): self.outcomes.append(dict(test=t.id(),status='ERROR',traceback=self._exc_info_to_string(e,t))); super().addError(t,e)
    def addSkip(self,t,r): self.outcomes.append(dict(test=t.id(),status='SKIP',reason=r)); super().addSkip(t,r)
    def addExpectedFailure(self,t,e): self.outcomes.append(dict(test=t.id(),status='EXPECTED_FAILURE')); super().addExpectedFailure(t,e)
    def addUnexpectedSuccess(self,t): self.outcomes.append(dict(test=t.id(),status='UNEXPECTED_SUCCESS')); super().addUnexpectedSuccess(t)
    def addSubTest(self,t,sub,e):
        if e: self.outcomes.append(dict(test=sub.id(),status='SUBTEST_FAILURE',traceback=self._exc_info_to_string(e,t)))
        super().addSubTest(t,sub,e)
names = sys.argv[3:]
if names == ['alias-focused']:
    reference = json.loads((ROOT/'work/support/FOCUSED_REFERENCE.json').read_text())
    names = [r['test'].split(' (',1)[1].rstrip(')') for r in reference['storage'] if r['phase']=='before']
    names += ['edge_test16.Edges', 'stage_test16.Staging', 'export_edges17.ProducerEdges']
elif names == ['alias-integration']:
    names = ['alias2_tests.AliasIntegration', 'tests.test_r2_host_runtime.Runtime',
             'tests.test_r2_build3.Build3.test_native_prepare_and_every_rank_encode']
if names == ['full']:
    package = types.ModuleType('tests'); package.__path__ = [str(TREE/'tests')]
    sys.modules['tests'] = package
    child = types.ModuleType('tests.headcall'); child.__path__ = [str(TREE/'tests/headcall')]
    sys.modules['tests.headcall'] = child; package.headcall = child
    names = ['.'.join(p.relative_to(TREE).with_suffix('').parts)
             for p in sorted((TREE/'tests').rglob('test*.py'))]
suite = unittest.TestSuite()
for name in names:
    try:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    except Exception as error:
        def failed_import(error=error): raise error
        test = unittest.FunctionTestCase(failed_import, description=name)
        test.id = lambda name=name: name+'.IMPORT_ERROR'
        suite.addTest(test)
result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
sys.settrace(None)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
inputs = {p:sha(p) for p in sorted(reads-writes) if Path(p).is_file()}
inputs[str(Path(__file__))] = RUNNER_SHA256
record = dict(command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/run_tests.py '+' '.join(sys.argv[1:]),
    inputs_sha256=inputs, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
    skipped=len(result.skipped), successful=result.wasSuccessful(), outcomes=result.outcomes,
    blocked=blocked, names=names, scope='CPU; network, subprocesses, NFS reads, outside writes and deletion denied; temporary fixtures retained')
record['hostname'] = os.uname().nodename
record['details'] = getattr(sys.modules.get('patch_a2_checks'), 'DETAILS', [])
record['frame_host_environment'] = {k:os.environ.get(k) for k in ('STUDENT_R2_FRAME_HOST','STUDENT_R2_LOCAL_NODE','Q_E7','Q_E8')}
(ROOT/'out'/(LABEL+'.json')).write_text(json.dumps(record,indent=2)+'\n')
(ROOT/'STATUS.md').write_text(f'{LABEL}: {result.testsRun} tests completed with {len(result.failures)} failures, {len(result.errors)} errors and {len(result.skipped)} skips. Detailed outcomes, tracebacks, commands and input hashes are in out/{LABEL}.json.\n')
print('RESULT', result.testsRun, len(result.failures), len(result.errors), len(result.skipped), flush=True)
sys.exit(not result.wasSuccessful())
