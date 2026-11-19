"""Regression checks for score retention, pairing, detectors and read gates."""
from common import *
from ruling0749 import *
from registration import select_construction,CATEGORIES,primary
import unittest,uuid

class Checks(unittest.TestCase):
 def setUp(self):
  self.base=dict(row_id='r',room='room',capture='capture',prediction=1.,label=1.,member_frames={'a':[1,2],'b':[3,4,5]})
 def test_retain_nonzero_A0(self):
  candidate=dict(self.base,prediction=None)
  self.assertEqual(score_pair(candidate,self.base,False),(1.,1.))
  self.assertEqual(score_pair(candidate,self.base,True),(0.,1.))
 def test_preserve_stored_score(self):
  self.assertEqual(score_pair(dict(self.base,prediction=100),dict(self.base,score=.7),False),(.7,.7))
 def test_no_double_refusal_gain(self):
  r=dict(self.base,prediction=None)
  self.assertEqual(contrast([r],[r],{'capture':False})['estimate'],0.)
 def test_pairing(self):
  with self.assertRaises(ValueError):contrast([dict(self.base,row_id='other')],[self.base],{'capture':True})
  with self.assertRaises(ValueError):score_pair(dict(self.base,room='wrong'),self.base,True)
 def test_detector_boundary(self):
  self.assertTrue(detector(self.base))
  self.assertFalse(detector(dict(self.base,member_frames={'a':[1,2,3],'b':[1,2,3]})))
  self.assertIsNone(detector(dict(self.base,member_frames={})))
 def test_detector_independent_of_truth(self):
  self.assertEqual(detector(self.base),detector(dict(self.base,label=999,prediction=999)))
 def test_refused_second_retains_first(self):
  d=doubt([dict(self.base,prediction=None)],[self.base],{'capture':True})
  self.assertEqual(d['repair_gain']['estimate'],0.)
  self.assertEqual(d['paired_numeric'],0)
 def test_closer_and_harm(self):
  first=dict(self.base,prediction=2.);second=dict(self.base,prediction=1.5)
  d=doubt([second],[first],{'capture':True})
  self.assertEqual((d['closer'],d['worse'],d['ties']),(1,0,0))
 def test_construction_sequence(self):
  tower=dict(P0_status='COMPLETE',P1_status='COMPLETE',P1_minus_P0={'ci95':[.1,2]})
  track=dict(P2_status='COMPLETE',P2_minus_P1={'ci95':[-1,2]},P2_minus_P0={'ci95':[1,2]})
  self.assertEqual(select_construction(tower,track),'P1')
  tower['P1_minus_P0']['ci95']=[0,2]
  self.assertEqual(select_construction(tower,track),'P2')
  track['P2_status']='MISSING'
  with self.assertRaises(Missing):select_construction(tower,track)
 def test_selected_size_gate(self):
  folder=ROOT/'work/tests0749'/uuid.uuid4().hex;folder.mkdir(parents=True)
  path=folder/'screen.json'
  d=dict(status='COMPLETE',selection_split='K1-train',construction='P1',object_set_sha256='synthetic',size_screen_pass=True,treatment={'ci95':[-1,0]},geometries={g:dict(object_set_sha256='synthetic',refusals_score_zero=True) for g in ('serving','g3t_s4')})
  write(path,dict(d,synthetic=True));self.assertEqual(require_size_screen(path,'P1')['construction'],'P1')
  with self.assertRaises(Missing):require_size_screen(path,'P0')
  d['geometries'].pop('g3t_s4');write(path,dict(d,synthetic=True))
  with self.assertRaises(Missing):require_size_screen(path,'P1')
 def test_package_D_missing(self):
  with self.assertRaises(Missing):package_d(ROOT/'inputs/PACKAGE_D_BINDING.json')
  self.assertNotIn('object_abs_distance',CATEGORIES)
 def test_missing_primary(self):
  with self.assertRaises(Missing):primary(ROOT/'work/ABSENT_PRIMARY.json')
 def test_scorer_boundaries(self):
  self.assertEqual(score(1.,1.),1.)
  self.assertGreater(score(.5,1.),0.)
  self.assertEqual(score(None,1.),0.)

if __name__=='__main__':
 pins();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 write(ROOT/'out/TESTS0749.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),production_evaluation_reads=0))
 if not result.wasSuccessful():raise SystemExit(1)
