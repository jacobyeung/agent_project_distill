from pathlib import Path
from pathlib import Path
import ast,json,sys,unittest
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24o/work/tree_r1c']
import naming24m1_n as N
import environment21f as E
from naming_test21f import Naming21f,check

class Naming21g(unittest.TestCase):
    controls=[]
    def scan(self,source):return N.scan_python_environment(ast.parse(source),check,'fixture.py')
    def test_inherited_positive(self):
        for source in [
            'subprocess.run(env={**os.environ,"Q":"q"})',
            'env={**os.environ,"Q":"q"}\nsubprocess.run(env=env)',
            'env=os.environ.copy()\nenv["Q"]="q"\nsubprocess.run(env=env)',
            'def launch():\n env=os.environ.copy()\n env["Q"]="q"\n subprocess.run(env=env)',
            'def launch():\n env={**os.environ,"Q":"q"}\n subprocess.run(env=env)',
        ]:
            with self.subTest(source=source):self.scan(source)
            self.controls.append(dict(source=source,result='PASS'))
    def test_inherited_negative(self):
        for source in [
            'env={**os.environ}\nenv[key]="q"\nrun(env=env)',
            'env=os.environ.copy()\nenv[key]="q"\nrun(env=env)',
            'env={**os.environ}\nenv["Q"]=runtime\nrun(env=env)',
            'env={**os.environ}\nenv["Q"]="BeNcHmArK"\nrun(env=env)',
            'env={**os.environ}\nenv["BeNcHmArK"]="q"\nrun(env=env)',
            'env={**os.environ}\nalias=env\nalias[key]="q"\nrun(env=env)',
            'env={**os.environ}\nhelper(env)\nrun(env=env)',
            'env={**os.environ}\nenv.update(runtime)\nrun(env=env)',
            'env={**os.environ}\nfor key,value in pairs:\n env[key]=value\nrun(env=env)',
            'env={**os.environ}\nenv={**runtime}\nrun(env=env)',
            'env={**os.environ}\nrun(env=env.copy())',
            'env={**os.environ}\ndef helper():\n env[key]="q"\nhelper()\nrun(env=env)',
            'os=helper()\nrun(env={**os.environ,"Q":"q"})',
            'run(env={**os.environ.copy(),"Q":"q"})',
            'run(env={**os.environ,"Q":make_value()})',
            'run(env={**os.environ,make_key():"q"})',
            'run(env=os.environ)',
            'env=dict(os.environ)\nrun(env=env)',
        ]:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'ENV_(NAME|UNRESOLVED):') as caught:self.scan(source)
            self.controls.append(dict(source=source,result='REFUSE',error=str(caught.exception)))
    def test_full_kit_nonliteral_after_spread(self):
        case=Naming21f('test_required_mutations')
        case.mutation('nonliteral_after_spread','key,value=("BeNcHmArK","q")\nenv={**os.environ}\nenv[key]=value\nsubprocess.run(["true"],env=env)')
        self.controls.extend(case.controls[-1:])
    def test_shell_certificate_binds_all_bytes(self):
        records=json.loads((B/'environment_shell21g.json').read_text())
        import base64
        for doc in records:
            path=B/'kits/q'/doc;raw=path.read_text()
            if doc.endswith('.json'):raw=base64.b64decode(json.loads(raw)['payload']).decode()
            self.assertTrue(E.scan_shell(raw,check,doc))
            with self.subTest(doc=doc),self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED:'):
                E.scan_shell(raw+'\nexport Q="$runtime"\n',check,doc)
    @classmethod
    def tearDownClass(cls):(D/'INHERITANCE_CONTROLS.json').write_text(json.dumps(cls.controls,indent=2)+'\n')
