import importlib.util
from pathlib import Path
import runpy
import sys
j = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(j/'work/tree_r1_24l4s'))
import tests
spec = importlib.util.spec_from_file_location('tests.test_host24l4t', j/'work/tree_r1/tests/test_host24l4t.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
setattr(tests, 'test_host24l4t', module)
sys.argv = [str(j/'work/validation/run_tests.py'), 'tree_r1_24l4s', 'failing_before24l4t', 'tests.test_host24l4t']
runpy.run_path(sys.argv[0], run_name='__main__')
