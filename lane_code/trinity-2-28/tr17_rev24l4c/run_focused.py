"""Reviewer test runner: writes only under this folder, no deletion, network or subprocess."""
import json, os, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
tree = HERE / 'tree/work/tree_r1'
label = sys.argv[1]
area = HERE / 'tmp' / label
area.mkdir(parents=True)
tempfile.tempdir = str(area)
for name in ('TMPDIR', 'LANE_TEST_OUTPUT', 'R2_PROOFS'):
    os.environ[name] = str(area)
sys.path.insert(0, str(tree))
os.chdir(tree)


def guard(event, args):
    if event in ('os.remove', 'os.rmdir'):
        raise PermissionError('NO_DELETION:' + str(args))
    if event in ('socket.connect', 'socket.bind', 'subprocess.Popen', 'os.system'):
        raise PermissionError('NO_NETWORK_OR_SUBPROCESS:' + event)
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            p = Path(os.fsdecode(path)).absolute()
            if (not p.is_relative_to(HERE) or p.is_relative_to(tree)) and str(p) != '/dev/null':
                raise PermissionError('WRITE_OUTSIDE_AREA:' + str(p))


sys.addaudithook(guard)
suite = unittest.TestLoader().loadTestsFromNames(sys.argv[2:])
with (HERE / f'{label}.log').open('x') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print(json.dumps(dict(label=label, run=result.testsRun, errors=len(result.errors),
                      failures=len(result.failures), skipped=len(result.skipped))))
for test, error in result.errors + result.failures:
    print(test.id(), error.strip().splitlines()[-1][:200])
