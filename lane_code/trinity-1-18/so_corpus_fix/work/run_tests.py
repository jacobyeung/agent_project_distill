"""Run only the requested local synthetic modules under isolated Python."""
import argparse
import importlib.util
import os
import sys
import unittest

import torch

torch.set_num_threads(8)

ROOT = os.path.dirname(os.path.abspath(__file__))
parser = argparse.ArgumentParser()
parser.add_argument('--tool', default=os.path.join(ROOT, 'tool'))
parser.add_argument('--tests', default=os.path.join(ROOT, 'tool', 'tests'))
parser.add_argument('--enable-review2', action='store_true')
parser.add_argument('--case', action='append')
parser.add_argument('modules', nargs='+')
args = parser.parse_args()
sys.path.insert(0, args.tests)
sys.path.insert(0, args.tool)
import ingest_read

# The immutable input tool also writes its test fixtures only in this workspace.
ingest_read.SCRATCH = os.path.join(ROOT, 'fixtures')
os.makedirs(ingest_read.SCRATCH, exist_ok=True)
if args.enable_review2:
    original_main = ingest_read.main
    def main(argv):
        return original_main(argv + ['--review2-checks'] if argv[0] == 'ingest' else argv)
    ingest_read.main = main
suite = unittest.TestSuite()
for name in args.modules:
    path = os.path.join(args.tests, name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if args.case:
        for case in args.case:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(case, module))
    else:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
