from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,unittest,json
from student_pilot.p3_provenance import load,file_pin
from launch_r1 import production_proof as Q
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/preflight_tests'
class Preflight21(unittest.TestCase):
 def test_component_refusal_precedes_store_producers(self):
  O.mkdir(parents=True,exist_ok=True)
  request=load(B/'proofs/capacity/400/request.json');cfg=load(request['config']['path'])
  card=load(cfg['r1_training']['mix']['path']);card['leg']='other';card.pop('successor_of',None)
  (O/'card.json').write_text(json.dumps(card));cfg['r1_training']['mix']=file_pin(O/'card.json')
  (O/'cfg.json').write_text(json.dumps(cfg));request['config']=file_pin(O/'cfg.json');request['staged_pins'][0]=request['config']
  native=os.uname();host=os.uname_result((native.sysname,'fixture-host',native.release,native.version,native.machine))
  from native_assets21 import PatchGridProcessor
  def processor(root):
   p=PatchGridProcessor(root);p._student_pilot_student='qwen35';return p
  from student_pilot import carrier_c1_run as C
  original=Path.open
  def retained(path,mode='r',*a,**kw):return original(path,mode.replace('x','w') if path.is_relative_to(O) else mode,*a,**kw)
  with patch.object(Path,'open',retained),patch.object(os,'uname',return_value=host),patch.object(C,'processor_for',processor),patch('student_pilot.s1_admission.admit',side_effect=AssertionError('store producer reached')) as producer:
   result=Q.run(request,O/'q')
  producer.assert_not_called();self.assertEqual(result['status'],'REFUSE');self.assertIn('component evidence',result['refusal'])
  (O/'RESULT.json').write_text(json.dumps(result,indent=2))
