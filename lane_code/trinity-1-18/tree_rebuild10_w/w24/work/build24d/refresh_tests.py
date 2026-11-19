from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import importlib.util,json,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24d';O=D/'refresh_tests';O.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1'),str(L/'work/build21')]
import native24 as N
import joblib as J
from student_pilot import s1_pool,r1_persisted as P
from student_pilot.p3_provenance import load,pinned,file_pin
sp=importlib.util.spec_from_file_location('refresh24d',L/'work/build24/kits/n/b/i.py');I=importlib.util.module_from_spec(sp);sp.loader.exec_module(I)
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
class Refresh(unittest.TestCase):
 def setUp(self):
  self.req=J.load(D/'go/r.json');self.cfg=J.load(self.req['config']['path'])
 def test_before_rejects_old_fixture_implementation(self):
  with P.scope(aliases),self.assertRaisesRegex(ValueError,'Pool selection implementation differs'):
   list(s1_pool.selected_rows(self.cfg['s1_routing']['selection'],'source'))
 def test_after_native_regeneration_same_rows(self):
  with P.scope(aliases):
   request=I.refresh(self.req,O/'pass');cfg=load(pinned(request['config']));result=list(s1_pool.selected_rows(cfg['s1_routing']['selection'],'source'))
   self.assertEqual(len(result),1);self.assertEqual(request['routing_base'],self.req['routing_base'])
   old=load(pinned(self.cfg['s1_routing']['selection']));new=load(pinned(cfg['s1_routing']['selection']))
   self.assertEqual(old['selected_rows'],new['selected_rows']);self.assertEqual(new['implementation'],s1_pool.implementation())
   self.assertEqual(cfg['r1_training'],self.cfg['r1_training'])
   J.write(D/'REFRESH_EVIDENCE.json',dict(status='PASS',native_rows=len(result),routing_base_unchanged=True,init_and_training_fields_unchanged=True))
 def test_changed_selection_refuses(self):
  original=s1_pool.prepare
  def change(*a,**kw):
   result=original(*a,**kw);result['selected_rows']+=1;return result
  with P.scope(aliases),patch.object(s1_pool,'prepare',change),self.assertRaisesRegex(ValueError,'E86:selected_rows'):I.refresh(self.req,O/'bad')
 def test_current_selection_is_unchanged(self):
  request=J.load(D/'go/r2.json')
  with P.scope(aliases):self.assertIs(I.refresh(request,O/'unused'),request)
 def test_actual_production_mismatch_is_authenticated(self):
  real=L.parent/'ext/m400real';r=J.load(real/'r.json');cfg=J.load(real/('files'+r['config']['path']));pin=cfg['s1_routing']['selection'];p=real/('files'+pin['path'])
  self.assertEqual(J.sha(p),pin['sha256']);self.assertNotEqual(J.load(p)['implementation'],s1_pool.implementation())
if __name__=='__main__':
 with P.scope(aliases):r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Refresh))
 J.write(D/'REFRESH_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),errors=len(r.errors),failures=len(r.failures)))
 raise SystemExit(not r.wasSuccessful())
