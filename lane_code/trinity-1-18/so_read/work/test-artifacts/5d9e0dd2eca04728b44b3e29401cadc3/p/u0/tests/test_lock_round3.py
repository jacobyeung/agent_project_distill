"""Run the same behavioral lock regression against current or round-1-before a4."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
SRC=Path(__file__).resolve().parents[2]
L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

fixtures=load('lock_behavior',SRC/'u0/tests/test_read_journal.py')
if os.environ.get('READ_LOCK_BEFORE')=='1':
    # Keep the identical test body and journal primitive; change only the reviewed launcher.
    fixtures.launch=load('h1eval.h10.launch',L/'work/review-before/src/h1eval/h10/launch.py')
suite=unittest.TestSuite([fixtures.RunnerTests('test_deadline_recovery_keeps_writer_lock')])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
