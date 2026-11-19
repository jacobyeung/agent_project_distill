"""Neutral identifiers retain the exact two-slot absence boundary."""
from pathlib import Path
from copy import deepcopy
import importlib.util,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(D),str(L/'work/tree_r1')]
from student_pilot import r1_absence as A
from student_pilot.p3_provenance import load,file_pin
class Neutral22(unittest.TestCase):
 def test_exact_codes_failing_before(self):
  cfg=load(D/'inputs/config.json');pin=file_pin(D/'proofs/absence/heads.pt')
  spec=importlib.util.spec_from_file_location('student_pilot.named_absence22',D/'before/r1_absence_named.py')
  old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  with self.assertRaisesRegex(ValueError,'SLOT_FORBIDDEN'):old.evidence(cfg,{'heads':pin})
  self.assertEqual(set(A.evidence(cfg,{'heads':pin})),set(A.PREFIXES))
  for codes in (['0'],['0','2'],['0','1','1'],list(A.PREFIXES),['lineage','data'],{'0':'component','1':'component'}):
   bad=deepcopy(cfg);bad['r1_training']['not_present_slots']=codes
   with self.subTest(codes=codes),self.assertRaisesRegex(ValueError,'SLOT_FORBIDDEN'):A.evidence(bad,{'heads':pin})
