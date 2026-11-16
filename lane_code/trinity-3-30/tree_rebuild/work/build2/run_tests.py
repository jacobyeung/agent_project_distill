"""Reuse the bounded build-1 runner; load the reviewed shared test file unchanged."""
import importlib.util
import os
from pathlib import Path
import runpy
import sys

L = Path(__file__).resolve().parents[2]
os.environ['BUILD1_RESULT_PREFIX'] = os.environ.get('B2_PREFIX', 'B2_')
original = importlib.util.spec_from_file_location


def spec(name, location, *args, **kwargs):
    if name == 'trace_grammar':
        location = L/'work/tree_r1/student_pilot/trace_grammar.py'
    return original(name, location, *args, **kwargs)


importlib.util.spec_from_file_location = spec
if 'shared_grammar_tests' in sys.argv:
    module_spec = original('shared_grammar_tests', L/'work/shared/test_trace_grammar.py')
    module = importlib.util.module_from_spec(module_spec)
    sys.modules['shared_grammar_tests'] = module
    module_spec.loader.exec_module(module)
runpy.run_path(str(L/'work/build1/run_tests.py'), run_name='__main__')
