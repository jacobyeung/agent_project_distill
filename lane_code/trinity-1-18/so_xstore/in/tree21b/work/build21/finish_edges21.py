from pathlib import Path
from unittest.mock import patch
import json,unittest
B=Path(__file__).resolve().parent;L=B.parents[1];O=B/'proofs/fresh_edges'
class FreshEdges21(unittest.TestCase):
 def test_native_export_in_empty_destination(self):
  import jobtest,joblib as J
  from student_pilot.full_ft import read_export
  O.mkdir(exist_ok=True);jobtest.Job20.setUpClass();f=jobtest.Job20
  target=O/'node';self.assertFalse(target.exists())
  resolved=J.resolve(f.kit,f.pool,f.listing,O/'resolved.json')
  J.stage_payload(f.kit,resolved,target)
  manifest,_=read_export(target/'w')
  self.assertEqual(manifest['tensor_count'],1)
  for name,pin in [('full_weights.json',f.receipt['pins']['full_weights']),('w.bin',f.receipt['pins']['export/w.bin'])]:
   self.assertEqual((target/'w'/name).stat().st_ino,(target/'u'/pin['sha256']).stat().st_ino)
 def test_five_slice_kit_binding_and_missing_pair_mutation(self):
  from launch_r1.build import build
  from student_pilot.p3_provenance import load
  from student_pilot import r1_coverage as C
  from student_pilot.r1_population import SLICE_CELLS
  O.mkdir(exist_ok=True)
  expected=set(SLICE_CELLS)|set(C.PINS)
  def check(path):
   build(B/'inputs/kit_config.json',L/'work/n1fix2/inputs',path)
   value=load(path/'k/c.json')['r1_training']['row_slice_inputs']
   self.assertEqual(set(value),expected)
  check(O/'kit')
  with patch.object(C,'source_names',return_value=SLICE_CELLS):
   with self.assertRaises(AssertionError):check(O/'mutant_kit')
  (O/'MUTATION.json').write_text(json.dumps(dict(mutation='omit the coverage pair from kit slice inputs',caught=True)))
