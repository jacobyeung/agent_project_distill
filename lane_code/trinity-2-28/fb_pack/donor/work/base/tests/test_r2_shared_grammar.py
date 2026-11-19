"""Run the rows lane's unchanged validator tests from the packaged fixture."""
import importlib.util
from tests.test_r2_data_path import LANE

def load_tests(loader,tests,pattern):
    path=LANE/'grammar/work/test_trace_grammar.py'
    spec=importlib.util.spec_from_file_location('published_grammar_tests',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
