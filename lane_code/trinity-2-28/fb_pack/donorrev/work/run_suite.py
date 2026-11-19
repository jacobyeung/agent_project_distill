import os, sys, json, tempfile, types, unittest
from pathlib import Path

W = Path(__file__).resolve().parent
tree = W / sys.argv[1]
dest = W / ('suite_' + sys.argv[1]); dest.mkdir(exist_ok=True)
for k in ('TMPDIR', 'LANE_TEST_OUTPUT', 'STUDENT_PILOT_TEST_OUTPUT', 'STUDENT_CONVERTER_TEST_OUTPUT',
          'CLEAN_VSI590K_TEST_ROOT', 'B2_TEST_OUTPUT', 'B9_TEST_OUTPUT', 'B11_TEST_OUTPUT'):
    os.environ[k] = str(dest)
os.environ.update(CLEAN_VSI590K_WORKSPACE=str(tree), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', XDG_CACHE_HOME=str(dest / 'cache'), HF_HOME=str(dest / 'hf'),
                  TORCH_HOME=str(dest / 'torch'))
tempfile.tempdir = str(dest)
os.chdir(tree); sys.path.insert(0, str(tree))
p = types.ModuleType('tests'); p.__path__ = [str(tree / 'tests')]; sys.modules['tests'] = p
import torch
torch.set_num_threads(int(os.environ.get('NT', '8')))
NFS = ('/home/', '/data/', '/data2/', '/data3/')


def guard(event, args):
    if event == 'open' and not isinstance(args[0], int):
        q = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:]
        if str(q).startswith(NFS):
            raise PermissionError('guard: NFS read ' + str(q))
        writing = (mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writing and not q.is_relative_to(W) and str(q) != '/dev/null':
            raise PermissionError('guard: write ' + str(q))
    if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.unlink'):
        q = Path(os.fsdecode(args[0])).resolve()
        if not q.is_relative_to(W):
            raise PermissionError('guard: fs ' + str(q))
    if event in ('os.listdir', 'os.scandir') and args and args[0] is not None and not isinstance(args[0], int):
        if str(Path(os.fsdecode(args[0])).resolve()).startswith(NFS):
            raise PermissionError('guard: NFS scan')
    if event in ('os.kill', 'os.killpg', 'socket.connect', 'socket.bind', 'os.system', 'os.exec',
                 'os.posix_spawn', 'subprocess.Popen', 'os.fork', 'os.forkpty'):
        raise PermissionError('guard: ' + event)


sys.addaudithook(guard)
names = sys.argv[2:]
results = {}


class R(unittest.TextTestResult):
    def addSuccess(self, t): super().addSuccess(t); results[t.id()] = 'ok'
    def addFailure(self, t, e): super().addFailure(t, e); results[t.id()] = 'FAIL ' + self._exc_info_to_string(e, t).strip().splitlines()[-1][:300]
    def addError(self, t, e): super().addError(t, e); results[t.id()] = 'ERROR ' + self._exc_info_to_string(e, t).strip().splitlines()[-1][:300]
    def addSkip(self, t, r): super().addSkip(t, r); results[t.id()] = 'skip'


suite = unittest.TestSuite()
for n in names:
    try:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(n))
    except Exception as exc:
        results[n] = 'LOADERROR ' + repr(exc)[:300]
unittest.TextTestRunner(resultclass=R, verbosity=0, stream=open(dest / 'runner.log', 'w')).run(suite)
(W / ('suite_' + sys.argv[1] + '.json')).write_text(json.dumps(results, indent=1, sort_keys=True))
print(sys.argv[1], len(results), sum(v == 'ok' for v in results.values()), 'ok')
