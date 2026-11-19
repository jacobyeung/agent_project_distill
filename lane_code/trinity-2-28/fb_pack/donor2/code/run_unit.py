import os,sys,tempfile,types,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1];T=W/'work'/os.environ.get('DONOR_TREE','new');out=W/'work'/('unit_'+T.name)
out.mkdir(exist_ok=True);os.environ.update(LANE_TEST_OUTPUT=str(out),TMPDIR=str(out),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(out/'cache'))
tempfile.tempdir=str(out);sys.path.insert(0,str(T));p=types.ModuleType('tests');p.__path__=[str(T/'tests')];sys.modules['tests']=p
import torch
torch.set_num_threads(16)
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:] or ['tests.test_scale_donor'])
r=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not r.wasSuccessful())
