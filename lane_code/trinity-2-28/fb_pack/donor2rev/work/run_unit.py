"""Usage: python run_unit.py <tree> [test names...]; runs inside work/<tree> with local-only outputs."""
import os, sys, tempfile, types, unittest
from pathlib import Path
W = Path(__file__).resolve().parent; T = W / sys.argv[1]; out = W / ('unit_' + sys.argv[1]); out.mkdir(exist_ok=True)
os.environ.update(LANE_TEST_OUTPUT=str(out), STUDENT_PILOT_TEST_OUTPUT=str(out), TMPDIR=str(out), CUDA_VISIBLE_DEVICES='',
                  HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', XDG_CACHE_HOME=str(out / 'cache'), HF_HOME=str(out / 'hf'),
                  OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8')
tempfile.tempdir = str(out); os.chdir(T); sys.path.insert(0, str(T))
p = types.ModuleType('tests'); p.__path__ = [str(T / 'tests')]; sys.modules['tests'] = p
import torch; torch.set_num_threads(8)
suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[2:] or ['tests.test_scale_donor'])
r = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not r.wasSuccessful())
