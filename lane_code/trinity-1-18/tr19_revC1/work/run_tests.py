"""Run named test files of one tree; print and save per-test outcomes as JSON."""
import importlib.util
import io
import json
import os
import sys
import time
import unittest
from pathlib import Path

tree = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
names = sys.argv[3:]
sys.path[:0] = [str(tree), str(tree / 'tests')]
os.chdir(tree)
records = {}
for name in names:
    path = tree / 'tests' / name
    started = time.time()
    stream = io.StringIO()
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        records[name] = dict(run=result.testsRun, failures=[(str(t), e[-1500:]) for t, e in result.failures],
                             errors=[(str(t), e[-1500:]) for t, e in result.errors],
                             skipped=len(result.skipped), ok=result.wasSuccessful(),
                             seconds=round(time.time() - started, 1))
    except BaseException as exc:  # import failure of the test module itself
        records[name] = dict(run=0, import_error=f'{type(exc).__name__}: {exc}'[:1500], ok=False,
                             seconds=round(time.time() - started, 1))
    r = records[name]
    print(name, 'ok' if r['ok'] else 'FAIL', r.get('run'), 'fail', len(r.get('failures', [])),
          'err', len(r.get('errors', [])), r.get('import_error', ''), flush=True)
out.write_text(json.dumps(records, indent=1) + '\n')
