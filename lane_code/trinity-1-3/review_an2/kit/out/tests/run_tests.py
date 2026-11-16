"""Run tests with a persistent machine-readable result; never discard case files."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

folder=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('test_native_vs_direct',folder/'test_native_vs_direct.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
loader=unittest.TestLoader()
suite=loader.loadTestsFromModule(module) if '--all' in sys.argv else loader.loadTestsFromTestCase(module.SyntheticTests)
if '--all' in sys.argv:
    advspec=importlib.util.spec_from_file_location('test_adversarial',folder/'test_adversarial.py')
    adv=importlib.util.module_from_spec(advspec)
    advspec.loader.exec_module(adv)
    suite.addTests(loader.loadTestsFromModule(adv))
result=unittest.TextTestRunner(verbosity=2).run(suite)
if '--all' in sys.argv:
    (folder/'ADVERSARIAL_RESULTS.json').write_text(json.dumps(adv.RESULTS, indent=2)+'\n')
path=folder/('RESULTS.json' if '--all' in sys.argv else 'SYNTHETIC_RESULTS.json')
path.write_text(json.dumps(dict(mode='PLUMBING — not model scores',tests_run=result.testsRun,
    failures=[dict(test=str(t),traceback=s) for t,s in result.failures],
    errors=[dict(test=str(t),traceback=s) for t,s in result.errors],
    skipped=[dict(test=str(t),reason=s) for t,s in result.skipped],
    successful=result.wasSuccessful(),test_source=str(folder/'test_native_vs_direct.py')),indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() else 1)
