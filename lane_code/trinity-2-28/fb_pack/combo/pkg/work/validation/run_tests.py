import json, os, sys, tempfile, unittest
from pathlib import Path
J = Path(__file__).resolve().parents[2]
tree = J/'work'/sys.argv[1]
label = sys.argv[2]
area = J/'work/validation'/label
area.mkdir()
tempfile.tempdir = str(area)
for name in ('TMPDIR', 'LANE_TEST_OUTPUT', 'R2_PROOFS'):
    os.environ[name] = str(area)
os.environ['R2_FIXTURES'] = str(J/'work/validation/lane')
os.environ['R2_LANE_ROOT'] = str(J/'work/validation/lane')
sys.path.insert(0, str(tree))
os.chdir(tree)
def guard(event, args):
    if event in ('os.remove', 'os.rmdir'):
        raise PermissionError('NO_DELETION:'+str(args))
    if event in ('socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'):
        raise PermissionError('NO_NETWORK_OR_SUBPROCESS:'+event)
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            p = Path(os.fsdecode(path)).absolute()
            if not p.is_relative_to(J) and str(p) != '/dev/null':
                raise PermissionError('WRITE_OUTSIDE_J:'+str(p))
sys.addaudithook(guard)
modules = sys.argv[3:]
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = []
    def addSuccess(self, test):
        self.passed.append(test.id())
        super().addSuccess(test)
loader = unittest.TestLoader()
suite = loader.loadTestsFromNames(modules)
with (J/'out'/f'{label}.log').open('x') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
record = dict(tree=str(tree), modules=modules, tests_run=result.testsRun,
              passed=result.passed, errors=[dict(test=t.id(), traceback=s) for t,s in result.errors],
              failures=[dict(test=t.id(), traceback=s) for t,s in result.failures],
              skipped=[dict(test=t.id(), reason=s) for t,s in result.skipped])
(J/'out'/f'{label}.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(dict(label=label, run=result.testsRun, passed=len(result.passed),
                     errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))))
for test, error in result.errors + result.failures:
    print(test.id(), error.strip().splitlines()[-1])
