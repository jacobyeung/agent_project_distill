from pathlib import Path
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,hashlib,importlib.util,io,json,sys,tarfile,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4n';O=D/'resolver';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24n2/work/tree_r1c']
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24n2/work/tree_r1c']
import joblib as J
import resolver21e as R
R.J=J;R.D=O;R.K=L/'work/build24/kits/n'
sp=importlib.util.spec_from_file_location('old24c','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24n2/work/build24m4n/old24c.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
records={}
class Selection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=R.fixture();f=cls.f
  cls.post=[x for x in f['manifest']['files'] if '/checkpoint_' in x['path']]
  cls.files={n:b for n,b in f['files'].items() if '/checkpoint_' not in n}
  R.archive(f['m']/'s.tar',{'MANIFEST.json':json.dumps(f['manifest']).encode(),**cls.files})
 def test_01_before_requires_post400(self):
  with self.assertRaisesRegex(KeyError,'checkpoint_000414.*complete.json') as e:old.small_archive(self.f['m']/'s.tar')
  records['before']=str(e.exception)
 def test_02_after_omits_all_post400(self):
  v,m=J.small_archive(self.f['m']/'s.tar')
  self.assertTrue(all('/checkpoint_' not in x['original'] for x in v.values()))
  records['after']=dict(status='PASS',selected=len(v),excluded=[x['path'] for x in self.post])
 def test_03_real_identity_resolve_without_post400(self):
  f=self.f;original=J.load
  for name in ('q','n'):
   k=L/'work/build24/kits'/name;spec=deepcopy(original(k/'k/p.json'))
   with tarfile.open(f['m']/'s.tar') as t:spec['m4']['v']=hashlib.sha256(t.extractfile('MANIFEST.json').read()).hexdigest()
   marker=(f['pool']/spec['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();spec['m4'].update(t=marker[2],b=int(marker[1]))
   old_load=old.load
   with R.external_boundary(f,module=old),patch.object(old,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==k/'k/p.json' else old_load(p)):
    with self.assertRaisesRegex(KeyError,'checkpoint_000414.*complete.json') as before:old.resolve(k,f['pool'],f['listing'],O/('before_'+name+'.json'))
   records['before_full_'+name]=str(before.exception)
   with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(spec) if Path(p)==k/'k/p.json' else original(p)):
    result=J.resolve(k,f['pool'],f['listing'],O/('resolved_'+name+'.json'))
   self.assertTrue(all('/checkpoint_' not in v['original'] for v in result['small_files'].values()))
   self.assertFalse(set(x['sha256'] for x in self.post)&set(result['paths']))
   records[name]=dict(status='PASS',small_files=len(result['small_files']),required_inputs=len(result['request']['staged_pins']),identity=spec['p_runtime_identity'])
 def test_04_stage_post_member_refuses_by_name(self):
  result=J.load(O/'resolved_n.json');k=L/'work/build24/kits/n'
  for item in self.post:
   bad=deepcopy(result);h=item['sha256'];bad['small_files'][h]=dict(original=item['path'],member='files'+item['path'],bytes=item['bytes'],sha256=h)
   with self.subTest(member=item['path']),self.assertRaisesRegex(ValueError,'E83:.*'+Path(item['path']).name):J.stage_payload(k,bad,O/'forbidden')
 def test_05_selected_post_pin_refuses(self):
  for item in self.post:
   with self.subTest(member=item['path']),self.assertRaisesRegex(ValueError,'E83:.*'+Path(item['path']).name):J.small_archive(self.f['m']/'s.tar',roots=[dict(path=item['path'],sha256=item['sha256'])])
 def test_06_identity_functions_unchanged(self):
  a=ast.parse(Path(old.__file__).read_text());b=ast.parse(Path(J.__file__).read_text())
  for name in ('identities','export_identity','metadata_closure','receipt600','checkpoint600','bound400'):
   get=lambda t:next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name)
   self.assertEqual(ast.dump(get(a)),ast.dump(get(b)))
 def test_07_rp_provenance_not_traversed(self):
  pin=next(x for x in self.f['manifest']['files'] if x['path'].endswith('/m400/RP.json'))
  values,_=J.small_archive(self.f['m']/'s.tar',roots=[dict(path=pin['path'],sha256=pin['sha256'])])
  self.assertEqual(set(values),{pin['sha256']})
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Selection))
 J.write(D/'RESOLVER_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),records=records,errors=[str(x) for x in r.errors],failures=[str(x) for x in r.failures]))
 raise SystemExit(not r.wasSuccessful())
