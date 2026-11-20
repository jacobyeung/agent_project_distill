from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24j/work/tree_r1']
from pathlib import Path
from unittest.mock import patch
import ast,base64,importlib.util,json,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4j';K=L/'work/build24/kits/n'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24j/work/tree_r1']
sys.path.insert(0,str(Path(__file__).resolve().parent))
import joblib as J,environment21f as E
sp=importlib.util.spec_from_file_location('scanner24d',D/'naming24m1_n.py');N=importlib.util.module_from_spec(sp);sp.loader.exec_module(N)
from launch_r2.build import capsule_json,bad_string
import naming_test21f as F,naming_test21g as G
F.N=N;G.N=N;F.D=D;G.D=D
class Naming(unittest.TestCase):
 def scan(self):
  with patch.object(E,'__file__',str(D/'scanners/n/environment21f.py')):return N.scan_decoded(K)
 def test_environment_mutations(self):
  cases=['key,value=("BeNcHmArK","q")\nos.environ[key]=value',
   'os.putenv("BeNcHmArK","q")','os.environ.setdefault("BeNcHmArK","q")',
   'for key,value in [("BeNcHmArK","q")]:\n os.environ[key]=value',
   'os.environ[f"{runtime}"]="q"','def helper(e):\n e["BeNcHmArK"]="q"\ne={**os.environ}\nhelper(e)\nsubprocess.run([],env=e)']
  p=K/'b/h.py';original=Path.read_text
  for source in cases:
   raw=p.read_text()+'\n'+source+'\n'
   with self.subTest(source=source),patch.object(Path,'read_text',lambda q,*a,**kw:raw if q==p else original(q,*a,**kw)),self.assertRaisesRegex(ValueError,'(INPUT_NAME|ENV_UNRESOLVED)'):self.scan()
 def test_stage_name_mutation(self):
  p=K/'k/p.json';v=J.load(p);v['p_files']['k/BeNcHmArK.json']='0'*64;raw=capsule_json(v)
  rb=Path.read_bytes;rt=Path.read_text
  with patch.object(Path,'read_bytes',lambda q:raw if q==p else rb(q)),patch.object(Path,'read_text',lambda q,*a,**kw:raw.decode() if q==p else rt(q,*a,**kw)),self.assertRaisesRegex(ValueError,'INPUT_NAME'):self.scan()
 def test_shell_edit_invalidates_certificate(self):
  s=base64.b64decode(J.load_raw(K/'k/j.json')['payload']).decode()
  with patch.object(E,'__file__',str(D/'scanners/n/environment21f.py')):
   self.assertTrue(E.scan_shell(s,lambda *a:None,'k/j.json'))
   with self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED'):E.scan_shell(s+'\nexport Q="$runtime"\n',lambda *a:None,'k/j.json')
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Naming)
 for cls,name in [(F.Naming21f,'test_21d_python_negative_controls'),(F.Naming21f,'test_unresolved_python_forms'),(G.Naming21g,'test_inherited_positive'),(G.Naming21g,'test_inherited_negative')]:suite.addTest(cls(name))
 r=unittest.TextTestRunner(verbosity=2).run(suite)
 J.write(D/'NAMING_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),errors=len(r.errors),failures=len(r.failures)))
 raise SystemExit(not r.wasSuccessful())
