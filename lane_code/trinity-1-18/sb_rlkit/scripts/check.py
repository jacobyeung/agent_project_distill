"""Run bounded CPU unit tests and write a hashed receipt."""
import os
from pathlib import Path
import sys
import unittest
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tests'))
P.sha(__file__);P.sha(root/'tests/test_kit.py')
suite=unittest.defaultTestLoader.loadTestsFromName('test_kit')
with (root/'out/TEST_RESULTS.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
P.write(root/'out/TEST_RESULTS.json',dict(schema='rl-on-n-tests-v1',status='PASS' if result.wasSuccessful() else 'FAIL',
    tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
    command='PYTHONPATH=overlay /scratch/jjyeung/envs/p1cpu/bin/python -B scripts/check.py'))
print('Tests:',result.testsRun,'failures:',len(result.failures),'errors:',len(result.errors))
raise SystemExit(not result.wasSuccessful())
