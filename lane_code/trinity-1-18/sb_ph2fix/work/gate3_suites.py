"""Run CPU suites without overwriting packaged test receipts."""
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'sb_mask_phrase/part2'))
name = {'part2': 'test_part2', 'launcher': 'test_launcher'}[sys.argv[1]]
suite = unittest.defaultTestLoader.loadTestsFromName(name)
if 'torch' in sys.modules:
    sys.modules['torch'].set_num_threads(8)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
