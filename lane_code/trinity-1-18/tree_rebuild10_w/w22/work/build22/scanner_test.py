from pathlib import Path
import ast,sys,unittest,importlib.util,json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import environment21f as E
from naming_test21f import check
class Scanner22(unittest.TestCase):
 def test_helper_mutation_failing_before(self):
  source='import os, subprocess\ndef helper(env):\n env["".join(["BeNcH","mArK"]) ]="q"\n subprocess.run(["true"],env=env)\nenv={**os.environ}\nhelper(env=env)'
  # The reviewer bypass needs no subprocess sink inside the helper.
  source='import os\ndef helper(env):\n env["".join(["BeNcH","mArK"]) ]="q"\ne={**os.environ}\nhelper(env=e)'
  spec=importlib.util.spec_from_file_location('old_environment22',D/'before/environment21f.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  old.scan_python(ast.parse(source),check,'reviewer.py')
  with self.assertRaisesRegex(ValueError,'non-mutation proof'):E.scan_python(ast.parse(source),check,'reviewer.py')
  records=[]
  for source in [source,
    'def helper(**kw):\n kw["env"][make_key()]="q"\nhelper(env={**os.environ})',
    'def helper(env):\n env[make_key()]="q"\nhelper(**{"env":{**os.environ}})',
    'env=os.environ.copy()\nunknown(env=env)',
    'def helper(env):\n return env\nhelper(env={**os.environ})',
    'def helper(env):\n return 0\nhelper=unknown\nhelper(env={**os.environ})',
    'import subprocess\ndef outer(subprocess):\n subprocess.run([],env={**os.environ})',
    'from subprocess import run\ndef run(env):\n env[make_key()]="q"\nrun(env={**os.environ})']:
   with self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED') as e:E.scan_python(ast.parse(source),check,'mutation.py')
   records.append(dict(source=source,result='REFUSE',reason=str(e.exception)))
  (D/'SCANNER_MUTATIONS.json').write_text(json.dumps(records,indent=2)+'\n')
 def test_proven_nonmutating_sinks(self):
  for source in ('import subprocess\nsubprocess.run(["true"],env={**os.environ})',
                 'def helper(env):\n return 0\nhelper(env={**os.environ})'):
   E.scan_python(ast.parse(source),check,'positive.py')

if __name__=='__main__':unittest.main(verbosity=2)
