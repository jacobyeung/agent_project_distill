import os,sys,tempfile,types,unittest
from pathlib import Path
W=Path(__file__).resolve().parent;T=W/sys.argv[1];out=W/('unit_'+sys.argv[1]);out.mkdir(exist_ok=True)
os.environ.update(LANE_TEST_OUTPUT=str(out),STUDENT_PILOT_TEST_OUTPUT=str(out),TMPDIR=str(out),CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(out/'cache'),HF_HOME=str(out/'hf'))
tempfile.tempdir=str(out);os.chdir(T);sys.path.insert(0,str(T));p=types.ModuleType('tests');p.__path__=[str(T/'tests')];sys.modules['tests']=p
import torch;torch.set_num_threads(16)
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[2:])
r=unittest.TextTestRunner(verbosity=1).run(suite);sys.exit(not r.wasSuccessful())
