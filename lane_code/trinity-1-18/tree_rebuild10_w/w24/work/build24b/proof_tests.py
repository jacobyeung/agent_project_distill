from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import importlib.util,os,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';T=L/'work/tree_r1';O=D/'proofs/proof_control';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/build24'),str(L/'work/n1fix2')]
import joblib as J
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_persisted import INIT_POLICY
from monitor9 import Monitor
m=Monitor(T)
from launch_r1 import production_proof as Q
spec=importlib.util.spec_from_file_location('launch_r1._oldproof24',L/'attic/build24b/tree/launch_r1/production_proof.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
class Proof24b(unittest.TestCase):
 def invoke(self,module,name,start=0):
  cfg=dict(world_size=4,s1_routing={'x':1},init_artifact={'artifact':{}},r1_training=dict(init_policy=INIT_POLICY,proof_mode='train',handover_receipt={'x':1},persisted_files={},registry={},mix=J.write(O/'card.json',dict(counting_admission='procedure_only_v1'))))
  cp=J.write(O/'cfg.json',cfg);request=dict(config=cp,room_audit={},frame_roots=[],weights=True)
  u=os.uname()
  with ExitStack() as stack:
   stubs={'student_pilot.r1_coverage.deferred':True,'student_pilot.r1_coverage.routing_request':True,'student_pilot.r1_coverage.validate_binding':None,
    'student_pilot.r1_rooms.verify_audit':dict(certifies='fixture',store='fixture'),
    'student_pilot.r1_persisted.verify':dict(receipt={'step':400},paths={}),
    'student_pilot.r1_training.training_components':{},'launch_r1.p_opener_witness.produce':{},
    'student_pilot.r1_handover.bind_target':cfg,'student_pilot.s1_admission.admit':{'config':cp},
    'student_pilot.r1_population.bind_prepared':cp,'student_pilot.r1_loader.production_audit':{'complete':True},
    'student_pilot.r1_persisted.admission':dict(paths={},init_milestone=400,absolute_resume_step=start)}
   for target,value in stubs.items():stack.enter_context(patch(target,return_value=value))
   stack.enter_context(patch.object(module,'bind_handover',return_value=cp));stack.enter_context(patch.object(module,'forward',return_value={'finite':True,'start_step':start}))
   stack.enter_context(patch.object(module,'verify_staging',return_value=[cp]));stack.enter_context(patch.object(os,'uname',return_value=os.uname_result((u.sysname,'fixture-host',u.release,u.version,u.machine))))
   return module._run(request,O/name)
 def test_before_fresh_counter_refuses(self):
  r=self.invoke(old,'before');self.assertEqual(r['refusal'],'ValueError:R1_PROOF_EXPORT_STEP_REQUIRED')
 def test_fresh_counter_with_m400_admits(self):
  r=self.invoke(Q,'after');self.assertEqual(r['status'],'ADMIT');self.assertEqual(r['init_milestone'],400);self.assertEqual(r['absolute_resume_step'],0)
 def test_continued_counter_mutation_refuses(self):
  r=self.invoke(Q,'mutation',400);self.assertEqual(r['refusal'],'ValueError:R1_PROOF_EXPORT_STEP_REQUIRED')
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Proof24b));m.save(O);J.write(D/'PROOF_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),scope='Orchestration unit test; upstream producers and forward are stubbed here. Separate capacity proof exercises native admission and full forward.'));raise SystemExit(not r.wasSuccessful())
