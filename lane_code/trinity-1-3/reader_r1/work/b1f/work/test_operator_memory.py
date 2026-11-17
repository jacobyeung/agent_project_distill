import ast,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_memo as F
W=F.W;O=W/'out';sys.path.insert(0,str(O));import tower_sequence as T
from orchard_h10.common import write,sha
from student_pilot import sam3_tower

class MemoryGate(unittest.TestCase):
 def test_probe_measures_and_checks(self):
  root=Path(tempfile.mkdtemp(prefix='mem_',dir=W/'work/tmp'));im=root/'0.png';F.Image.new('RGB',(64,48)).save(im)
  settings=dict(frames_root=str(root),frames_json={'captures':{'x':{'frames':[{'path':'0.png','sha256':sha(im)}]}}},sam3={})
  write(root/'s.json',settings);cfg=dict(settings=str(root/'s.json'),output=str(root/'r'))
  with patch.object(sam3_tower,'Sam3Tower',return_value=F.Sam()) as ctor:
   result=T.memory_probe(cfg);self.assertTrue(result['measured']);self.assertTrue(result['fits'])
   self.assertEqual(ctor.call_args.args[0]['precision'],'float32')
  self.assertFalse(T.memory_bound(256*1024**2)['fits'])
 def test_bootstrap_requires_measured_fitting_receipt(self):
  tree=ast.parse((O/'tower_bootstrap.py').read_text())
  node=next(n for n in tree.body if isinstance(n,ast.If) and 'Full CPU check differs' in ast.unparse(n))
  code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'bootstrap','exec')
  proof=dict(passed=True,payload='payload',plan='plan',inputs='inputs',operator_sha256='operator',memory=dict(measured=True,fits=True))
  ns=dict(proof=proof,public={'payload_sha256':'payload','plan_sha256':'plan'},sha=lambda p:'inputs',shared=Path('/project/community/jjyeung/a9439d0fb0487'),operator_sha256='operator')
  exec(code,ns)
  for value in ({},{'measured':False,'fits':True},{'measured':True,'fits':False}):
   proof['memory']=value
   with self.assertRaisesRegex(ValueError,'Full CPU check differs'):exec(code,ns)
if __name__=='__main__':unittest.main(verbosity=2)
