"""Run all local regression fixtures; compatible with Python 3.6 and 3.12."""
import os
from pathlib import Path
import sys
import unittest
here = Path(__file__).resolve().parent
os.environ.setdefault('LCS_TEST_WORK', str(here.parent / 'test-work'))
sys.path.insert(0, str(here))
suite = unittest.defaultTestLoader.discover(str(here), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
