"""Run the bounded CPU regressions without scanning or cleaning external trees."""
import os
from pathlib import Path
import sys
import unittest
import torch

torch.set_num_threads(8)
tree = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(tree), str(tree / 'launch_s1/b')]
names = [
    'tests.test_s1_admission',
    'tests.test_s1_first_batch_progress',
    'tests.test_s1_staging',
    'tests.test_s1_source_seal',
    'tests.test_s1_mdg_inputs',
    'tests.test_s1_first_step',
    'tests.test_s1_persistent_resume',
    'tests.test_s1_launch_kit',
    'tests.test_s1_production_imports',
    'tests.test_s1_checkpoint_buffers',
]
if '--include-known-stale-gate' in sys.argv[2:]:
    names.insert(3, 'tests.test_s1_in_job_gate')
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
if os.environ.get('SO_NO_LOCAL_SOCKETS') == '1':
    # This class starts a real Gloo process group from setUpClass. Load the
    # module into the gate, but report each unavailable test as an explicit skip.
    from tests.test_s1_checkpoint_buffers import CheckpointBufferTests
    CheckpointBufferTests.__unittest_skip__ = True
    CheckpointBufferTests.__unittest_skip_why__ = 'Local sockets are unavailable in this sandbox; real Gloo is required'
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
