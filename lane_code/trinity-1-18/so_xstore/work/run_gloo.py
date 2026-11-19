"""Optional existing Gloo baseline. No new store-equivalence assertion exists."""
from pathlib import Path
import os
import resource
import sys
import unittest

L = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(L / 'work/tree'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
soft, hard = resource.getrlimit(resource.RLIMIT_AS)
ceiling = 8 * (1 << 30)
resource.setrlimit(resource.RLIMIT_AS, (min(v for v in (soft, hard, ceiling) if v > 0), hard))
import torch
torch.set_num_threads(8)
print('BASELINE ONLY: native prepare/adopt/fallback bitwise first-loss proof is not implemented.', flush=True)
suite = unittest.defaultTestLoader.loadTestsFromNames([
    'tests.test_carrier_c1_run.RunnerTests.test_actual_fsdp_gloo_resume_and_export',
    'tests.test_s1_checkpoint_buffers',
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
