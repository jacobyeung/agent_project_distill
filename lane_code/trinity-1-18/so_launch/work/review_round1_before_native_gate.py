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
    'tests.test_s1_launch_kit.LaunchKitTests.test_new_run_chooses_training',
    'tests.test_s1_launch_kit.LaunchKitTests.test_job_entry_preserves_wrapper_allocation_clock',
    'tests.test_s1_launch_kit.LaunchKitTests.test_parseable_but_incomplete_checkpoint_never_restarts_cold',
    'tests.test_s1_launch_kit.LaunchKitTests.test_resume_requires_matching_binding_and_complete_payload_inventory',
]
if '--include-known-stale-gate' in sys.argv[2:]:
    names.insert(3, 'tests.test_s1_in_job_gate')
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
raise SystemExit(not result.wasSuccessful())
