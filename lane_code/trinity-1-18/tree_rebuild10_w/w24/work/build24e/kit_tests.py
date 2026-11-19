import os
from pathlib import Path
from unittest.mock import patch
import ast,importlib.util,json,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'));B=L/'work/build21'
sys.path[:0]=[str(D),str(B),str(T)]
import joblib as J,environment21f as E
sys.path.insert(0,str(L/'work/build24d'))
from i import normalized
from student_pilot.r1_persisted import scope
from student_pilot.r1_coverage import deferred,validate_binding,source_names
from student_pilot.r1_launch22 import validate_removals
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r2.build import capsule_json,bad_string
class Kit24(unittest.TestCase):
 def test_minimal_and_vqa_pins(self):
  before=J.load(L/'work/build22/kits/q/k/n.json')
  for name in ('q','n'):
   k=D/'kits'/name;c=J.load(k/'k/n.json');spec=J.load(k/'k/p.json')
   paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24e'/('UPLOADS_'+name+'.json'))['files']}
   with scope(paths):
    validate_removals(c);validate_binding(c);self.assertTrue(deferred(c,read_pins=True));self.assertEqual(source_names(J.load(paths[c['r1_training']['row_sources']['sha256']]),c),())
   self.assertEqual([v['sha256'] for v in c['remove_files']],[v['sha256'] for v in before['remove_files']]);self.assertEqual(len(c['remove_files']),12)
   for key in ('direction_twins','camera_wording_exclusion','wording_exclusion','component_rows','not_present_slots'):
    self.assertEqual(normalized(c['r1_training'][key]),normalized(before['r1_training'][key]))
   self.assertEqual(c['routing_opener_init'],'keep');self.assertEqual(c['r2_identity']['init']['step'],544)
   self.assertEqual(c['world_size'],4);self.assertEqual(c['recipe']['world_size'],4)
   self.assertNotIn('routing_inputs',c['r1_training']);self.assertEqual(c['r1_training']['row_slice_inputs'],{})
   self.assertFalse(c.get('so_step'));self.assertNotIn('Q_E7',(k/'b/z.py').read_text())
   self.assertFalse(J.load(k/'BUILD.json')['GO']);self.assertFalse(J.load(k/'k/a.json')['GO'])
   self.assertEqual(J.load(k/'k/a.json')['source']['tree_sha256'],digest(inventory(T)))
   self.assertNotIn('e3c72962e3fd774c7e15fa1e4aeae1b6642264bf4f3cf54b9e350b8d7bfb9707',spec['pin_paths'])
 def test_launch_and_exact_resource_certificate(self):
  q=D/'kits/q';n=D/'kits/n';qs=(q/'job.sh').read_text();ns=(n/'job.sh').read_text()
  self.assertEqual(ns,qs.replace('--partition=general','--partition=advanced').replace('--gres=gpu:1','--gres=gpu:4'))
  self.assertEqual(J.load(n/'k/p.json')['step'],400)
  self.assertEqual(J.load(n/'k/n.json')['r1_training']['proof_mode'],'train')
  def check(value,where):
   if bad_string(value,J.load(n/'b/wh.json')):raise ValueError('NAME:'+where)
  with patch.object(E,'__file__',str(L/'work/build24e/scanners/n/environment21f.py')):
   self.assertTrue(E.scan_shell(ns,check,'job.sh'))
   with self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED'):
    E.scan_shell(ns+'\nexport ${DYNAMIC}=q\n',check,'job.sh')
 def test_unfilled600_refuses(self):
  with self.assertRaisesRegex(ValueError,'^E68$'):
   J.resolve(L/'attic/build24b/kit_n',D/'proofs/resolver/f/pool',D/'proofs/resolver/f/l.json',D/'proofs/unfilled.json')
 def test_bootstrap_environment_capability(self):
  source=(D/'joblib.py').read_text()
  self.assertTrue(E.scan_python(ast.parse(source),lambda value,where:None,'b/z.py'))
  mutation=source+'\ndef helper(env):\n env["".join(["bad","name"]) ]="q"\ne={**os.environ}\nhelper(env=e)\n'
  with self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED'):
   E.scan_python(ast.parse(mutation),lambda value,where:None,'b/z.py')
 def test_source_inventory_mutation(self):
  k=D/'kits/q';spec=importlib.util.spec_from_file_location('scan24',L/'work/build24e/naming24e_q.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
  p=k/'k/c0.json';v=J.load(p);v['files'][next(iter(v['files']))]='0'*64;raw=capsule_json(v)
  original=Path.read_bytes;original_text=Path.read_text
  with patch.object(Path,'read_bytes',lambda q:raw if q==p else original(q)),patch.object(Path,'read_text',lambda q,*a,**kw:raw.decode() if q==p else original_text(q,*a,**kw)):
   with self.assertRaisesRegex(ValueError,'SOURCE_INVENTORY'):N.scan_decoded(k)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Kit24));J.write(L/'work/build24e/KIT_TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),successful=r.wasSuccessful()));raise SystemExit(not r.wasSuccessful())
