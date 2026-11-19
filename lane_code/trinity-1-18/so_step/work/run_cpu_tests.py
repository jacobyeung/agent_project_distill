import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
                  MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
                  LANE_TEST_OUTPUT=str(ROOT/'test_runs'), TMPDIR=str(ROOT/'test_runs'))
if hasattr(os,'sched_getaffinity'):
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path.insert(0,os.environ.get('SO_TEST_TREE',str(ROOT/'tree')))
import torch
torch.set_num_threads(8)

if __name__ == '__main__':
    local_only = '--local-only' in sys.argv
    names = [n for n in sys.argv[1:] if n != '--local-only'] or ['tests.test_so_prefetch','tests.test_so_cache','tests.test_so_metrics']
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    if local_only:
        def leaves(items):
            for item in items:
                if isinstance(item,unittest.TestSuite):
                    yield from leaves(item)
                else:
                    yield item
        selected=[]
        for case in leaves(suite):
            if 'test_two_rank_' in case.id():
                print('NOT_RUN_SOCKET_REQUIRED: '+case.id(),flush=True)
            else:
                selected.append(case)
        suite=unittest.TestSuite(selected)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
