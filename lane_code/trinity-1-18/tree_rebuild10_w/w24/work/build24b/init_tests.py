from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import importlib.util,json,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';T=L/'work/tree_r1';O=D/'proofs/init';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/build24'),str(L/'work/n1fix2')]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import r1_persisted as P,r1_training as R
from launch_r1 import entry
from student_pilot.p3_provenance import load,pinned,file_pin
import joblib as J
REAL=L.parent/'ext/m400real';REAL=REAL if REAL.exists() else D/'inputs/m400real';receipt=load(REAL/'e.json');run=load(REAL/'r.json');AP=receipt['pins']['artifact']
paths={p['sha256']:str(REAL/('files'+p['path'])) for p in receipt['pins'].values() if (REAL/('files'+p['path'])).is_file()}
BEFORE=[]
def old(name,file):
 sp=importlib.util.spec_from_file_location(name,L/'attic/build24b/tree'/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
oldp=old('student_pilot._persisted24','student_pilot/r1_persisted.py');olde=old('launch_r1._entry24','launch_r1/entry.py')
def cfg():
 return dict(init_artifact={'artifact':AP},r1_training=dict(proof_mode='train',init_policy=P.INIT_POLICY,handover_receipt=file_pin(REAL/'e.json'),p_run=run,persisted_files=paths))
def verify(c):
 v=c['r1_training'];return P.verify(v['handover_receipt'],v['p_run'],c['init_artifact']['artifact'],v['persisted_files'],proof_mode=v.get('proof_mode'),init_policy=P.init_policy(v))
class Init24b(unittest.TestCase):
 def test_01_before_reader_refuses_real_receipt(self):
  with self.assertRaisesRegex(ValueError,'P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED') as e:oldp.export_only(receipt,'train')
  BEFORE.append(dict(reader='r1_persisted.export_only',refusal=str(e.exception)))
 def test_02_before_entry_refuses_real_receipt(self):
  with self.assertRaisesRegex(ValueError,'P_EXPORT_ONLY_TRAINING_LAUNCH_REFUSED') as e:olde.admit(cfg())
  BEFORE.append(dict(reader='launch_r1.entry.admit',refusal=str(e.exception)))
 def test_03_real400_reader_accepts_without_proof_scope(self):
  r=verify(cfg());self.assertEqual(r['receipt']['step'],400);self.assertFalse(r['unread']);self.assertFalse(r['export_bytes_verified'])
  self.assertEqual(set(r['absent']),{'heads',*[k for k in receipt['pins'] if k.startswith('export/') and k.endswith(('.safetensors','.index.json'))]})
  J.write(O/'REAL_READER.json',dict(status='PASS',receipt=file_pin(REAL/'e.json'),verified=sorted(r['verified']),absent=sorted(r['absent']),without_proof_scope=True))
 def test_04_policy_absent_is_not_permission(self):
  c=cfg();c['r1_training'].pop('init_policy')
  with self.assertRaisesRegex(ValueError,'P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED'):verify(c)
  with self.assertRaisesRegex(ValueError,'P_EXPORT_ONLY_TRAINING_LAUNCH_REFUSED'):entry.admit(c)
 def test_05_policy_value_mutations(self):
  for bad in (None,True,False,400,{},[],'step600_export_weights_fresh_v1',''):
   c=cfg();c['r1_training']['init_policy']=bad
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_POLICY_INVALID'):verify(c)
  with self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_POLICY_INVALID'):P.export_only(receipt,'train',init_policy='wrong')
 def test_06_training_mode_mutations(self):
  for bad in (None,'q','training',True):
   c=cfg();c['r1_training']['proof_mode']=bad
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_TRAIN_MODE_REQUIRED'):verify(c)
   with self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_TRAIN_MODE_REQUIRED'):P.export_only(receipt,bad,init_policy=P.INIT_POLICY)
 def test_07_receipt_required_mutations(self):
  for key in ('handover_receipt','persisted_files'):
   c=cfg();c['r1_training'].pop(key)
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_RECEIPT_REQUIRED'):entry.admit(c)
 def test_08_milestone_schema_mutations(self):
  for change in ({'step':200},{'step':600},{'step':400.0},{'step':True},{'step':None},{'schema':'p-handover-v1'},{'schema':'wrong'}):
   h=dict(receipt,**change)
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'P_EXPORT_INIT_STEP400_ONLY'):P.export_only(h,'train',init_policy=P.INIT_POLICY)
 def test_09_checkpoint_run_and_receipt_closure_still_refuse(self):
  c=cfg();c['r1_training']['p_run']=dict(run,checkpoint=run['config'])
  with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_PIN_MISMATCH:checkpoint'):verify(c)
  for key,change,error in [('step',200,'P_EXPORT_INIT_STEP400_ONLY'),('checkpoint_status','available','P_EXPORT_ONLY_CHECKPOINT_STATUS_MISMATCH'),('stop_step',1000,'P_EXPORT_ONLY_CHECKPOINT_STATUS_MISMATCH'),('trainer_commit','changed','P_EXPORT_HANDOVER_RUN_BINDING_MISMATCH')]:
   c=cfg();c['r1_training']['handover_receipt']=J.write(O/'bad.json',dict(receipt,**{key:change}))
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,error):verify(c)
 def test_10_artifact_pin_and_relocation_still_refuse(self):
  c=cfg();c['init_artifact']['artifact']=dict(AP,sha256='0'*64)
  with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_PIN_MISMATCH:artifact'):verify(c)
  c=cfg();c['r1_training']['persisted_files']=dict(paths,**{'0'*64:'absent'})
  with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_UNBOUND_RELOCATION'):verify(c)
 def test_11_fresh_counter_after_native_progress_checks(self):
  c=cfg()
  with P.scope(paths),patch('student_pilot.r1_handover.progress',return_value={'step':400}) as check:
   self.assertEqual(R.start(c),0);check.assert_called_once()
  with P.scope(paths),patch('student_pilot.r1_handover.progress',side_effect=ValueError('P_EXPORT_TARGET_CONFIG_MISMATCH')):
   with self.assertRaisesRegex(ValueError,'P_EXPORT_TARGET_CONFIG_MISMATCH'):R.start(c)
 def test_12_q_still_requires_proof_scope(self):
  with self.assertRaisesRegex(ValueError,'P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED'):P.export_only(receipt,'q')
  with P.proof_scope():self.assertTrue(P.export_only(receipt,'q'))
 def test_13_entry_advances_to_unchanged_validation(self):
  with patch('student_pilot.r1_training.validate',side_effect=ValueError('NEXT_UNCHANGED_CHECK')):
   with self.assertRaisesRegex(ValueError,'NEXT_UNCHANGED_CHECK'):entry.admit(cfg())
 def test_14_handover_without_policy_unchanged(self):
  self.assertFalse(P.export_only(dict(schema='p-handover-v1',step=600),'train'))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Init24b))
 J.write(O/'TESTS.json',dict(successful=r.wasSuccessful(),tests=r.testsRun,before=BEFORE));monitor.save(O)
 raise SystemExit(not r.wasSuccessful())
