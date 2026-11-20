from pathlib import Path
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,time,unittest
from unittest.mock import patch

L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21f';K=B/'kits/q'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y/work/tree_r1c']
import naming24m1_n as N
import environment21f as E
from launch_r2.build import bad_string
spec=importlib.util.spec_from_file_location('naming21e_frozen',Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y/work/build24m4y/old_naming21.py'))
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
B=Path(__file__).resolve().parent;K=L/'work/build24/kits/q'
wh=json.loads((K/'b/wh.json').read_text())

def check(value,where):
    if bad_string(value,wh):raise ValueError('ENV_NAME:'+where+':'+value)


class Naming21f(unittest.TestCase):
    controls=[]

    def refused(self,source,pattern='(?:ENV_NAME|ENV_UNRESOLVED):'):
        with self.assertRaisesRegex(ValueError,pattern) as caught:
            N.scan_python_environment(ast.parse(source),check,'fixture.py')
        self.controls.append(dict(test=self.id(),source=source,result='REFUSE',error=str(caught.exception)))

    def mutation(self,label,source):
        path=K/'b/o.py';original=Path.read_text
        text=path.read_text()+'\n'+source+'\n'
        def read(p,*args,**kwargs):
            return text if p==path else original(p,*args,**kwargs)
        with patch.object(Path,'read_text',read):
            print('mutation '+label,flush=True)
            started=time.monotonic();trace=sys.gettrace();sys.settrace(None)
            try:before=old.scan_decoded(K)
            finally:sys.settrace(trace)
            self.assertEqual(before['status'],'PASS')
            with self.assertRaisesRegex(ValueError,'(?:INPUT_NAME|ENV_UNRESOLVED):b/o.py:') as caught:
                N.scan_decoded(K)
        self.controls.append(dict(test=self.id(),label=label,source=source,old='PASS',
            old_checked_strings=before['checked_strings'],new='REFUSE',error=str(caught.exception),seconds=time.monotonic()-started))

    def test_required_mutations(self):
        pair='key, value = ("BeNcHmArK", "q")\n'
        cases={
            'reviewer_tuple':pair+'os.environ[key] = value',
            'putenv':pair+'os.putenv(key, value)',
            'setdefault':pair+'os.environ.setdefault(key, value)',
            'loop_pairs':'for key, value in [("BeNcHmArK", "q")]:\n os.environ[key] = value',
            'fstring':pair+'os.environ[f"{key}"] = value',
            'helper_map':'def make_env():\n key, value = ("BeNcHmArK", "q")\n return {key:value}\nsubprocess.run(["true"], env=make_env())',
        }
        for label,source in cases.items():
            with self.subTest(label=label):self.mutation(label,source)

    def test_21d_python_negative_controls(self):
        # Reuse every source case verbatim from the frozen 21d test file.
        tree=ast.parse((B/'naming_test21d.py').read_text())
        method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_python_environment_forms')
        cases=next(ast.literal_eval(n.value) for n in method.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='cases' for t in n.targets))
        for source in cases:
            with self.subTest(source=source):self.refused(source,'ENV_NAME:.*(BeNcHmArK|DaTaSeT)')

    def test_unresolved_python_forms(self):
        cases=[
            'key,*rest=("Q","q")\nos.environ[key]=rest[0]',
            'key=next(iter(keys))\nos.environ[key]="q"',
            'os.environ["Q"]=make_value()',
            'os.environ["Q"]=f"{runtime}"',
            'os.environ.update(runtime)',
            'os.environ.update(**runtime)',
            'os.environ.setdefault(runtime,"q")',
            'os.putenv("Q",runtime)',
            'getattr(os,"putenv")(runtime,"q")',
            'getattr(os.environ,"setdefault")(runtime,"q")',
            'getattr(os,runtime)("Q","q")',
            'g=getattr\ng(os,runtime)("Q","q")',
            'g=getattr\ng(os,"putenv")(runtime,"q")',
            'setattr(os,"environ",runtime)',
            'setenv=os.environ.__setitem__\nsetenv(runtime,"q")',
            'from os import environ as e\ne[runtime]="q"',
            'from os import putenv as p\np(runtime,"q")',
            'e,other=(os.environ,0)\ne[runtime]="q"',
            'os.environ["Q"],other=(runtime,0)',
            'os.environ["Q"]+=runtime',
            'del os.environ[runtime]',
            'os.environ.pop(runtime,None)',
            'run(env={runtime:"q"})',
            'run(env={"Q":runtime})',
            'run(env={**runtime,"Q":"q"})',
            'env={"Q":"q"}\nenv.update(runtime)\nrun(env=env)',
            'env={"Q":"q"}\na=env\na[runtime]="q"\nrun(env=env)',
            'env={"Q":"q"}\nhelper(env)\nrun(env=env)',
            'def make_env():\n return {"Q":"q"}\nrun(env=make_env())',
            'def launch(env):\n run(env=env)',
            'subprocess.run(["true"],**runtime)',
            'run(**{"env":runtime})',
            'subprocess.Popen(*runtime)',
            'from subprocess import run as r\nr(*runtime)',
            'os.execve("/bin/true",[],runtime)',
            'os.spawnve(0,"/bin/true",[],runtime)',
            'helper(os.environ)',
            'exec(runtime)',
            'f=exec\nf(runtime)',
            'os.__dict__[runtime]("Q","q")',
            'from os import *',
            'box={"e":os.environ}\nbox["e"][runtime]="q"',
            'box=[os.environ]\nbox[0][runtime]="q"',
            'helper(os.putenv)',
            'env=os.environ if flag else {}\nenv[runtime]="q"',
            'def get_env():\n return os.environ\nget_env()[runtime]="q"',
            'key="Q"\nmatch runtime:\n case key:\n  os.environ[key]="q"',
            'def other():\n key="Q"\nos.environ[key]="q"',
            'import sys\no=sys.modules["os"]\no.putenv(runtime,"q")',
            'from importlib import import_module as load\no=load("os")\no.putenv(runtime,"q")',
            'def dict(**kwargs):\n return runtime\nrun(env=dict(Q="q"))',
            'def dict(**kwargs):\n pass\nrun(env=dict(Q="q"))',
            'class dict:\n def __new__(cls,**kwargs):\n  return runtime\nrun(env=dict(Q="q"))',
            'run(env=dict(Q="q"))',
            'def env():\n return {"Q":"q"}\nrun(env=env)',
            'os.putenv.__call__(runtime,"q")',
            'os.environ.update.__call__(runtime)',
            'subprocess.Popen.__call__("true",0,None,None,None,None,None,True,False,None,runtime)',
            'getattr(os.putenv,"__call__")(runtime,"q")',
            'os.environ.update=helper',
            'os.putenv=helper',
            'getattr(unknown,runtime)("Q","q")',
            'get_module().environ[runtime]="q"',
            'get_module().putenv(runtime,"q")',
            'import posix\nposix.putenv(runtime,"q")',
            'getattr=helper\ngetattr(os,"putenv")("Q","q")',
            'import builtins as b\nb.exec(runtime)',
            'from builtins import exec as e\ne(runtime)',
            '__builtins__["exec"](runtime)',
        ]
        for source in cases:
            with self.subTest(source=source):self.refused(source)

    def test_literal_python_forms(self):
        cases=[
            'os.environ["Q"]="q"',
            'key="Q"\nvalue="q"\nos.environ[key]=value',
            'os.putenv("Q","q")',
            'p=os.putenv\np("Q","q")',
            'os.environ.setdefault("Q","q")',
            'os.environ.update({"Q":"q"})',
            'os.environ.update([("Q","q")])',
            'os.environ.update(Q="q")',
            'getattr(os,"putenv")("Q","q")',
            'env={"Q":"q"}\nsubprocess.run(env=env)',
            'subprocess.run(env={"Q":"q"})',
            'subprocess.run(env={**os.environ,"Q":"q"})',
            'env=os.environ.copy()\nsubprocess.run(env=env)',
            'subprocess.run(**{"env":{"Q":"q"}})',
            'os.execve("/bin/true",[],{"Q":"q"})',
            'value=os.environ["Q"]',
        ]
        for source in cases:
            with self.subTest(source=source):N.scan_python_environment(ast.parse(source),check,'fixture.py')
            self.controls.append(dict(test=self.id(),source=source,result='PASS'))

    def test_allowlist_requires_literal_key(self):
        self.assertEqual(E.ENVIRONMENT_VALUE_ALLOWLIST,frozenset({'Q_ROOT','Q_KIT','Q_NS','TK_KIT_HOME','TK_JOBDIR'}))
        with patch.object(E,'ENVIRONMENT_VALUE_ALLOWLIST',frozenset({'Q'})):
            N.scan_python_environment(ast.parse('os.environ["Q"]=runtime'),check,'fixture.py')
            self.refused('os.environ[runtime]="q"')
            self.refused('os.environ["Q"]="BeNcHmArK"','ENV_NAME:')
            N.scan_python_environment(ast.parse('subprocess.run(env={**os.environ,"Q":runtime})'),check,'fixture.py')
            E.scan_shell('export Q="$runtime"',check,'fixture.sh')

    def test_shell_forms(self):
        cases=[
            'export Q="$runtime"',
            'export "${key}"=q',
            'env "${key}=q" true',
            'Q="$runtime" true',
            'Q="$runtime"',
            'Q=$(helper)',
            'export Q',
            'eval "$runtime"',
            'source "$runtime"',
            '. "$runtime"',
            'export "${!key}"',
            'declare -x "$runtime"',
            'printf -v "$key" q',
            'srun --export=Q=$runtime true',
            '#SBATCH --export=ALL',
            'env -S "$runtime"',
            'bash -c "$runtime"',
            'for key in Q; do export "$key=q"; done',
            'read Q',
            'alias e=export; e "$runtime"',
            'Q=q;export "$runtime"',
            'Q+=q',
            'local -n Q=R',
        ]
        for source in cases:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'ENV_UNRESOLVED:') as caught:
                E.scan_shell(source,check,'fixture.sh')
            self.controls.append(dict(test=self.id(),source=source,result='REFUSE',error=str(caught.exception)))
        for source in ['export Q=q','Q=q true','env Q=q true','srun --export=Q=q true','Q=q\nexport Q']:
            with self.subTest(source=source):self.assertTrue(E.scan_shell(source,check,'fixture.sh'))
        for source in ['export BeNcHmArK=q','env Q=DaTaSeT true']:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'ENV_NAME:'):
                E.scan_shell(source,check,'fixture.sh')

    @classmethod
    def tearDownClass(cls):
        (D/'MUTATIONS.json').write_text(json.dumps(cls.controls,indent=2)+'\n')
