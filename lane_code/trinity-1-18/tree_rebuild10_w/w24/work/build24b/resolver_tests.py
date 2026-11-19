from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,hashlib,importlib.util,io,json,runpy,sys,tarfile,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';T=L/'work/tree_r1';O=D/'proofs/pins';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/build21'),str(T)]
import joblib as J
from student_pilot.p3_provenance import file_pin
from launch_r2.build import capsule_json
K=B/'kits/n';real=L.parent/'ext/m400real';records=[]
def fixture():
 root=O/'controls';root.mkdir(exist_ok=True)
 for name in ('e.json','r.json','DONE.json','RP.json'):(root/name).write_bytes((real/name).read_bytes())
 with tarfile.open(root/'s.tar','w') as t:
  raw=(real/'MANIFEST.json').read_bytes();m=tarfile.TarInfo('MANIFEST.json');m.size=len(raw);t.addfile(m,io.BytesIO(raw))
 return root
class Pins24b(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.root=fixture()
 def test_01_real_control_manifest_pins_pass(self):
  J.bound400(J.load(K/'k/p.json'),self.root,J.load(K/'k/n.json'))
 def test_02_each_control_hash_mutation(self):
  for key in ('d','e','r','p'):
   sp=J.load(K/'k/p.json');sp['m4'][key]='0'*64
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'E10'):J.bound400(sp,self.root,J.load(K/'k/n.json'))
 def test_03_missing_binding_and_step_mutations(self):
  cfg=J.load(K/'k/n.json');sp=J.load(K/'k/p.json');sp.pop('m4')
  with self.assertRaisesRegex(ValueError,'E74'):J.bound400(sp,self.root,cfg)
  with self.assertRaisesRegex(ValueError,'E74'):J.listing400(sp,self.root)
  sp=J.load(K/'k/p.json');sp['step']=600
  with self.assertRaisesRegex(ValueError,'E75'):J.bound400(sp,self.root,cfg)
 def test_04_manifest_and_artifact_mutations(self):
  for key,error in (('v','E76'),('a','E77')):
   sp=J.load(K/'k/p.json');sp['m4'][key]='0'*64
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,error):J.bound400(sp,self.root,J.load(K/'k/n.json'))
 def test_05_config_binding_mutations(self):
  for target in ('artifact','run','receipt'):
   cfg=J.load(K/'k/n.json')
   if target=='artifact':cfg['init_artifact']['artifact']['sha256']='0'*64
   elif target=='run':cfg['r1_training']['p_run']['binding']['sha256']='0'*64
   else:cfg['r1_training']['handover_receipt']['sha256']='0'*64
   with self.subTest(target=target),self.assertRaisesRegex(ValueError,'E78'):J.bound400(J.load(K/'k/p.json'),self.root,cfg)
 def test_06_preserved_identity_functions(self):
  old=ast.parse((L/'attic/build24b/joblib.py').read_text());new=ast.parse((B/'joblib.py').read_text())
  for name in ('identities','export_identity','metadata_closure','receipt600','checkpoint600'):
   get=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(ast.dump(get(old)),ast.dump(get(new)),name)
 def test_07_real_byte_resolver_and_export_mutations(self):
  import resolver21e as R
  R.K=K;R.D=O/'real';R.D.mkdir(exist_ok=True);f=R.fixture();original=J.load
  spec=J.load(K/'k/p.json');cfg=J.load(K/'k/n.json')
  with tarfile.open(f['m']/'s.tar') as t:spec['m4']['v']=hashlib.sha256(t.extractfile('MANIFEST.json').read()).hexdigest()
  tokens=(f['pool']/spec['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();spec['m4'].update(t=tokens[2],b=int(tokens[1]))
  with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==K/'k/p.json' else original(p)):
   r=J.resolve(K,f['pool'],f['listing'],O/'resolved.json')
  self.assertEqual(r['config']['r1_training']['proof_mode'],'train');self.assertEqual(r['config']['r1_training']['init_policy'],'step400_export_weights_fresh_v1')
  self.assertEqual(r['config']['init_artifact']['artifact']['sha256'],spec['m4']['a'])
  for key,value in [('t','0'*64),('b',1)]:
   sp=deepcopy(spec);sp['m4'][key]=value
   with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(sp) if Path(p)==K/'k/p.json' else original(p)),self.subTest(key=key),self.assertRaisesRegex(ValueError,'E79'):
    J.resolve(K,f['pool'],f['listing'],O/'bad.json')
  J.write(O/'REAL_RESOLVER.json',dict(status='PASS',real_receipt=J.sha(real/'e.json'),real_artifact=spec['m4']['a'],
   stand_ins='Synthetic transport archive for absent members and export parts; eight unavailable model metadata files plus omitted tokenizer use inherited external byte boundary. Real e/r/artifact/config/binding/preparation bytes unchanged.',training_mode=r['config']['r1_training']['proof_mode']))
 def test_08_launcher_GO_and_four_ranks(self):
  calls=[];original=J.load
  def load(p):
   v=original(p)
   if Path(p)==K/'k/a.json':v['GO']=True
   return v
  with patch.dict(sys.modules,z=J),patch.object(sys,'argv',[str(K/'b/t.py'),'root','cfg']),patch('subprocess.run',side_effect=lambda cmd,**kw:calls.append(cmd) or type('R',(),{'returncode':0})()),patch.object(J,'load',load):
   with self.assertRaises(SystemExit) as ex:runpy.run_path(str(K/'b/t.py'),run_name='__main__')
  self.assertEqual(ex.exception.code,0);self.assertEqual(calls[0].count('--nproc_per_node=4'),1);self.assertIn('--nnodes=1',calls[0]);self.assertEqual(calls[0][-2:],['root','cfg'])
  with patch.dict(sys.modules,z=J),patch.object(sys,'argv',[str(K/'b/t.py')]),patch.object(J,'load',load),self.assertRaisesRegex(ValueError,'E80'):runpy.run_path(str(K/'b/t.py'),run_name='__main__')
  with patch.dict(sys.modules,z=J),patch.object(sys,'argv',[str(K/'b/t.py')]),patch('subprocess.run',side_effect=AssertionError('GO false launched')):
   with self.assertRaises(SystemExit) as ex:runpy.run_path(str(K/'b/t.py'),run_name='__main__')
  self.assertEqual(ex.exception.code,0)
 def test_09_worker_refusals(self):
  root=O/'worker';(root/'q').mkdir(parents=True,exist_ok=True)
  original=J.load;cfg=J.load(D/'proofs/capacity/n/h/config.json');pin=J.write(root/'cfg.json',cfg)
  q=dict(status='ADMIT',init_milestone=400,config=pin);J.write(root/'q/RESULT.json',q)
  def run(qvalue,go=True,bad=None):
   if bad:J.write(root/'bad.json',bad)
   def load(p):
    if Path(p)==K/'k/a.json':v=original(p);v['GO']=go;return v
    if Path(p)==root/'q/RESULT.json':return qvalue
    return original(p)
   with patch.dict(sys.modules,z=J),patch.object(sys,'argv',[str(K/'b/u.py'),str(root),str(root/('bad.json' if bad else 'cfg.json'))]),patch.object(J,'load',load),patch('student_pilot.carrier_c1_run.train',side_effect=AssertionError('unexpected training')):
    runpy.run_path(str(K/'b/u.py'),run_name='__main__')
  with self.assertRaisesRegex(ValueError,'E03'):run(q,go=False)
  for mutation in (dict(q,status='REFUSE'),dict(q,init_milestone=600)):
   with self.assertRaisesRegex(ValueError,'E81'):run(mutation)
  bad=deepcopy(cfg);bad['world_size']=8
  with self.assertRaisesRegex(ValueError,'E82'):run(q,bad=bad)
 def test_10_bound_configs_no_late_checkpoint_or_freeze(self):
  before=J.load(L/'attic/build24b/kit_n/k/n.json');after=J.load(K/'k/n.json')
  self.assertNotIn('checkpoint',after['r1_training']['p_run'])
  self.assertEqual(after['routing_opener_init'],'keep');self.assertEqual(after['r2_identity']['init']['step'],544)
  for key in ('remove_files','camera_overrides','depth','recipe'):
   self.assertEqual(after.get(key),before.get(key))
  self.assertEqual(after['r1_training']['direction_twins'],before['r1_training']['direction_twins'])
  def fields(v):
   if isinstance(v,dict):
    for k,x in v.items():
     if 'freeze' in k:yield k,x
     yield from fields(x)
   elif isinstance(v,list):
    for x in v:yield from fields(x)
  self.assertEqual(list(fields(before)),list(fields(after)))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Pins24b));J.write(D/'PIN_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),errors=len(r.errors),failures=len(r.failures)));raise SystemExit(not r.wasSuccessful())
