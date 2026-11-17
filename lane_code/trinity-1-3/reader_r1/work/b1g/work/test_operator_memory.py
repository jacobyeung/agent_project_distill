import ast,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_memo as F
W=F.W;O=W/'out';sys.path.insert(0,str(O));import tower_sequence as T
from orchard_h10.common import write
from student_pilot import sam3_tower
class MemoryGate(unittest.TestCase):
 def test_fixed_bound_without_sam_receipt(self):
  root=Path(tempfile.mkdtemp(prefix='mem_',dir=W/'work/tmp'))
  write(root/'s.json',dict(perception_memo_modules=['g3t']))
  with patch.object(sam3_tower,'Sam3Tower',side_effect=AssertionError('SAM must not load')):
   result=T.memory_probe(dict(settings=str(root/'s.json'),output=str(root/'r')))
  self.assertEqual(result['g3t_capture_bytes_upper'],3335080);self.assertTrue(result['fits'])
  self.assertEqual(result['sam_memo_bytes'],0);self.assertFalse(result['sam_measurement_required'])
  self.assertFalse(T.memory_bound(allocation_bytes=64*1024**3)['fits'])
 def test_bootstrap_requires_bound_but_no_measured_sam(self):
  tree=ast.parse((O/'tower_bootstrap.py').read_text())
  node=next(n for n in tree.body if isinstance(n,ast.If) and 'Full CPU check differs' in ast.unparse(n))
  code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'bootstrap','exec')
  proof=dict(passed=True,payload='payload',plan='plan',inputs='inputs',operator_sha256='operator',memory=T.memory_bound())
  ns=dict(proof=proof,public={'payload_sha256':'payload','plan_sha256':'plan'},sha=lambda p:'inputs',shared=Path('/project/community/jjyeung')/(O/'TOKEN').read_text().strip(),operator_sha256='operator')
  exec(code,ns)
  for value in ({},{**T.memory_bound(),'fits':False},{**T.memory_bound(),'perception_memo_modules':['sam3']},{**T.memory_bound(),'sam_measurement_required':True}):
   proof['memory']=value
   with self.assertRaisesRegex(ValueError,'Full CPU check differs'):exec(code,ns)
if __name__=='__main__':unittest.main(verbosity=2)
