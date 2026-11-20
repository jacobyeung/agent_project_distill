import runpy, sys
from pathlib import Path
j = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(j/'work/tree_r1_24l4r'))
import tests
import importlib.util
spec = importlib.util.spec_from_file_location('tests.test_host24l4s', j/'work/tree_r1/tests/test_host24l4s.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
setattr(tests, 'test_host24l4s', module)
sys.argv = [str(j/'work/validation/run_tests.py'), 'tree_r1_24l4r', 'snapshot_native_before24l4s', 'tests.test_host24l4s']
runpy.run_path(sys.argv[0], run_name='__main__')
