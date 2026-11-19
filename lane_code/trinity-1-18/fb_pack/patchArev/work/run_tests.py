"""Run CPU unittest targets against work/<tree> with real fixture roots; writes only under this review folder."""
import hashlib, json, os, resource, sys, tempfile, unittest, types
from pathlib import Path
W = Path(__file__).resolve().parent
ROOT = W.parent
TREE = W / sys.argv[1]
LABEL = sys.argv[2]
W21 = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
OUT = W / 'test_runs' / LABEL
OUT.mkdir(parents=True, exist_ok=False)
TMP = OUT / 'tmp'; TMP.mkdir()
tempfile.tempdir = str(TMP)
os.environ.update(TMPDIR=str(TMP), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', XDG_CACHE_HOME=str(OUT/'cache'),
    HF_HOME=str(OUT/'hf'), TORCH_HOME=str(OUT/'torch'), MPLCONFIGDIR=str(OUT/'mpl'),
    R2_FIXTURES=str(W21/'fixtures'), R2_LANE_ROOT=str(W21), R2_PROOFS=str(OUT),
    LANE_TEST_OUTPUT=str(OUT), B2_TEST_OUTPUT=str(OUT), STUDENT_PILOT_TEST_OUTPUT=str(OUT/'pilot'),
    STUDENT_CONVERTER_TEST_OUTPUT=str(OUT/'converter'), CLEAN_VSI590K_TEST_ROOT=str(OUT/'clean'),
    CLEAN_VSI590K_WORKSPACE=str(TREE), GV_FIX_ROOT=str(OUT), REVIEW_TREE=str(TREE),
    OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8')
resource.setrlimit(resource.RLIMIT_AS, (38*1024**3, 38*1024**3))
os.chdir(TREE)
sys.path[:0] = [str(TREE), str(W/'support'), str(TREE/'generator/derivgen_v7'), str(TREE/'generator/ground_rows_out')]
class RetainedDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(TMP))
    def __enter__(self): return self.name
    def __exit__(self, *args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory = RetainedDirectory
blocked = []
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        mode, flags = args[1:3]
        writing = isinstance(mode, str) and any(c in mode for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT)
        if writing and not p.is_relative_to(ROOT):
            blocked.append('OUTSIDE_WRITE:'+str(p)); raise PermissionError(blocked[-1])
        if not writing and str(p).startswith(('/data', '/home')):
            blocked.append('NFS_READ:'+str(p)); raise PermissionError(blocked[-1])
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
    raise PermissionError('CPU_TEST_WORKERS_UNAVAILABLE')
multiprocessing.process.BaseProcess.start = refuse_worker
try:
    import torch
    torch.set_num_threads(8); torch.set_num_interop_threads(1)
except ImportError:
    pass
class Result(unittest.TextTestResult):
    def __init__(self, *a, **k): super().__init__(*a, **k); self.outcomes = []
    def addSuccess(self, t): self.outcomes.append(dict(test=t.id(), status='PASS')); super().addSuccess(t)
    def addFailure(self, t, e): self.outcomes.append(dict(test=t.id(), status='FAIL', traceback=self._exc_info_to_string(e, t))); super().addFailure(t, e)
    def addError(self, t, e): self.outcomes.append(dict(test=t.id(), status='ERROR', traceback=self._exc_info_to_string(e, t))); super().addError(t, e)
    def addSkip(self, t, r): self.outcomes.append(dict(test=t.id(), status='SKIP', reason=r)); super().addSkip(t, r)
    def addSubTest(self, t, sub, e):
        if e: self.outcomes.append(dict(test=sub.id(), status='SUBTEST_FAILURE', traceback=self._exc_info_to_string(e, t)))
        super().addSubTest(t, sub, e)
names = sys.argv[3:]
if names and names[0].startswith('@'):
    names = json.loads(Path(names[0][1:]).read_text())
if any(n.startswith('tests.') for n in names):
    package = types.ModuleType('tests'); package.__path__ = [str(TREE/'tests')]
    sys.modules['tests'] = package
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
record = dict(tree=str(TREE), label=LABEL, names=names, tests=result.testsRun, failures=len(result.failures),
    errors=len(result.errors), skipped=len(result.skipped), subtest_failures=sum(o['status']=='SUBTEST_FAILURE' for o in result.outcomes),
    hostname=os.uname().nodename, blocked=blocked, outcomes=result.outcomes,
    frame_host_environment={k: os.environ.get(k) for k in ('STUDENT_R2_FRAME_HOST','STUDENT_R2_LOCAL_NODE','Q_E7','Q_E8')})
(W/'results').mkdir(exist_ok=True)
(W/'results'/(LABEL+'.json')).write_text(json.dumps(record, indent=1)+'\n')
print('RESULT', LABEL, result.testsRun, len(result.failures), len(result.errors), len(result.skipped), record['subtest_failures'], flush=True)
