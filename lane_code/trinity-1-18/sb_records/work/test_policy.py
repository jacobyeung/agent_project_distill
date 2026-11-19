import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'policy_tree'))
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_r2_policy')
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
