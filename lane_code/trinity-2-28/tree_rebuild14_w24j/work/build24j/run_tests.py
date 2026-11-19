"""Run bounded retained CPU regressions without deleting fixtures."""
import json
import os
from pathlib import Path
import resource
import sys
import tempfile
import unittest
import traceback

J = Path(__file__).resolve().parents[2]
tree = J / 'work' / sys.argv[1]
label = sys.argv[2]
root = J / 'work/build24j' / label
root.mkdir(parents=True, exist_ok=False)
tmp = root / 'tmp'
tmp.mkdir()
for key in ('TMPDIR', 'R2_PROOFS', 'LANE_TEST_OUTPUT', 'STUDENT_PILOT_TEST_OUTPUT',
            'XDG_CACHE_HOME', 'HF_HOME', 'TORCH_HOME', 'TRITON_CACHE_DIR'):
    os.environ[key] = str(tmp)
for key in ('R2_FIXTURES', 'R2_LANE_ROOT'):
    os.environ[key] = str(J / 'work/build24j/fixtures' if os.environ.get('HOST24J_FIXTURES') else J)
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
tempfile.tempdir = str(tmp)
resource.setrlimit(resource.RLIMIT_AS, (19 * 1024**3, 19 * 1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE, (200 * 1024**2, 200 * 1024**2))

def guard(event, args):
    if event in ('os.remove', 'os.rmdir'):
        raise RuntimeError('No deletion: ' + repr(args))
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, (str, bytes)) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            if not Path(os.fsdecode(path)).resolve().is_relative_to(J):
                raise RuntimeError('Write outside J: ' + str(path))
sys.addaudithook(guard)
sys.path.insert(0, str(tree))
sys.path.insert(1, str(J / 'work/build24j'))
names = sys.argv[3:] or [
    'tests.' + p.stem for p in sorted((tree / 'tests').glob('test_*.py'))
    if any(s in p.read_text() for s in ('launch_r1', 'r1_population', 'r1_handover', 'r1_loader'))
]
with (root / 'tests.log').open('w') as log:
    suites = []
    import_errors = []
    for name in names:
        try:
            suites.append(unittest.defaultTestLoader.loadTestsFromName(name))
        except Exception:
            import_errors.append(dict(module=name, traceback=traceback.format_exc()))
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(suites))
report = dict(modules=names, ran=result.testsRun,
              import_errors=import_errors,
              errors=[dict(test=str(t), traceback=e) for t, e in result.errors],
              failures=[dict(test=str(t), traceback=e) for t, e in result.failures],
              skipped=[dict(test=str(t), reason=e) for t, e in result.skipped])
(root / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(label=label, ran=result.testsRun, errors=len(result.errors),
                     failures=len(result.failures), skipped=len(result.skipped), import_errors=len(import_errors))))
