from pathlib import Path
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,sys,unittest
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d';K=B/'kits/q'
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24j/work/tree_r1']
import joblib as J
import naming21 as N
from launch_r2.build import capsule_json,bad_string
spec=importlib.util.spec_from_file_location('naming21c_original',L/'attic/build21d/naming21.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class Naming21d(unittest.TestCase):
    controls=[]

    def scans(self,document,raw,pattern,before=False):
        path=K/document;read_text=Path.read_text;read_bytes=Path.read_bytes
        def text(p,*a,**kw):return raw.decode() if p==path else read_text(p,*a,**kw)
        def binary(p):return raw if p==path else read_bytes(p)
        result=dict(test=self.id(),document=document)
        with patch.object(Path,'read_text',text),patch.object(Path,'read_bytes',binary):
            if before:
                # Coverage concerns the changed scanner, not this frozen control.
                trace=sys.gettrace();sys.settrace(None)
                try:prior=old.scan_decoded(K)
                finally:sys.settrace(trace)
                self.assertEqual(prior['status'],'PASS')
                result.update(old='PASS',old_checked_strings=prior['checked_strings'])
            with self.assertRaisesRegex(ValueError,pattern) as context:N.scan_decoded(K)
            result.update(new='REFUSE',error=str(context.exception))
        self.controls.append(result)

    def nested(self,change,pattern,before=False):
        value=J.load(K/'k/s.json');entry=next(iter(value['entries'].values()))
        content=json.loads(base64.b64decode(entry['payload']));change(content)
        raw=json.dumps(content,sort_keys=True).encode()
        entry.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        self.scans('k/s.json',capsule_json(value),pattern,before)

    def test_reviewer_nested_key_failing_before(self):
        self.nested(lambda v:v.update({'BeNcHmArK':'DaTaSeT'}),'INPUT_NAME:.*BeNcHmArK',True)

    def test_reviewer_environment_name_failing_before(self):
        raw=(K/'b/o.py').read_bytes()+b'\nos.environ["BeNcHmArK"]="q"\n'
        self.scans('b/o.py',raw,'INPUT_NAME:.*environment:BeNcHmArK',True)

    def test_nested_value_failing_before(self):
        self.nested(lambda v:v.update({'neutral':{'more':['DaTaSeT']}}),'INPUT_NAME:.*DaTaSeT',True)

    def test_shell_export(self):
        self.scans('b/f.sh',(K/'b/f.sh').read_bytes()+b'\nexport BeNcHmArK=1\n','EXECUTABLE_NAME:.*BeNcHmArK')

    def test_env_dict_key_failing_before(self):
        raw=(K/'b/o.py').read_bytes()+b'\nsubprocess.run(["true"], env={"BeNcHmArK":"1"})\n'
        self.scans('b/o.py',raw,'INPUT_NAME:.*environment:BeNcHmArK',True)

    def test_environment_values_no_path(self):
        raw=(K/'b/o.py').read_bytes()+b'\nos.environ["Q"]="DaTaSeT"\n'
        self.scans('b/o.py',raw,'INPUT_NAME:.*environment:DaTaSeT',True)

    def test_allowlisted_annotation_is_exact(self):
        self.nested(lambda v:v.update(room_rule='BeNcHmArK'),'INPUT_NAME:.*room_rule:BeNcHmArK')

    def test_allowlisted_annotation_is_location_bound(self):
        self.nested(lambda v:v.update(other={'room_rule':N.ROOM_RULE}),'INPUT_NAME:.*other/room_rule:Only')

    def test_unknown_nested_key(self):
        self.nested(lambda v:v.update(extra=[{'Teacher':'q'}]),'INPUT_NAME:.*Teacher')

    def test_known_schema_key_does_not_exempt_value(self):
        v=J.load(K/'k/c.json');v['geometry_connector']='BeNcHmArK'
        self.scans('k/c.json',capsule_json(v),'INPUT_NAME:.*geometry_connector:BeNcHmArK')

    def test_new_hash_key_cannot_exempt_identity(self):
        v=J.load(K/'k/n.json');v['s1_routing']['catalog']['0'*64]='BeNcHmArK'
        self.scans('k/n.json',capsule_json(v),'INPUT_NAME:.*BeNcHmArK')

    def test_source_inventory_is_frozen(self):
        v=J.load(K/'k/7.json');v['files']['BeNcHmArK']='0'*64
        self.scans('k/7.json',capsule_json(v),'SOURCE_INVENTORY')

    def test_shell_environment_forms(self):
        for line in ['Q=DaTaSeT true','srun --export=ALL,BeNcHmArK=1 true',
            'sbatch --export=Q=DaTaSeT q.sh','export BeNcH"mArK"=1',
            'export BeNcH\\\nmArK=1']:
            with self.subTest(line=line):
                self.scans('b/f.sh',(K/'b/f.sh').read_bytes()+('\n'+line+'\n').encode(),
                    '(EXECUTABLE_NAME|INPUT_NAME):.*(BeNcH|DaTaSeT)')

    def test_python_environment_forms(self):
        cases=[
            'os.environ.update({"BeNcHmArK":"1"})',
            'os.environ.update(Q="DaTaSeT")',
            'os.environ.update(BeNcHmArK="1")',
            'os.environ.update([("Q", "DaTaSeT")])',
            'os.environ.setdefault("BeNcHmArK", "1")',
            'os.putenv("BeNcHmArK", "1")',
            'os.putenv("Q", "DaTaSeT")',
            'from os import putenv as p\np("Q", "DaTaSeT")',
            'import os as x\nx.environ["BeNcHmArK"]="1"',
            'from os import environ as e\ne["Q"]="DaTaSeT"',
            'e=os.environ\ne.update({"BeNcHmArK":"1"})',
            'env={"BeNcHmArK":"1"}\nrun(env=env)',
            'env={}\nenv.update(BeNcHmArK="1")\nrun(env=env)',
            'env={}\nenv["Q"]="DaTaSeT"\nrun(env=env)',
            'run(env=dict(BeNcHmArK="1"))',
            'run(env={"Q":"DaTaSeT"})',
            'run(env={"Q":"BeNcH"+"mArK"})',
            'a="BeNcH"\nb="mArK"\nos.environ[a+b]="1"',
            'a="BeNcHmArK"\nos.environ[f"{a}"]="1"',
            'os.environb[b"BeNcHmArK"]=b"1"',
            'os.environ={"BeNcHmArK":"1"}',
            'os.environ["Q"]:str="DaTaSeT"',
            'os.environ["Q"]+="DaTaSeT"',
            'setenv=os.environ.update\nsetenv(BeNcHmArK="1")',
            'from os import putenv\np=putenv\np("Q","DaTaSeT")',
            'def make_env():\n return {"BeNcHmArK":"1"}\nrun(env=make_env())',
        ]
        wh=J.load(K/'b/wh.json')
        def check(value,where):
            if bad_string(value,wh):raise ValueError('ENV_NAME:'+where+':'+value)
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError,'ENV_NAME:.*(BeNcHmArK|DaTaSeT)') as context:
                    N.scan_python_environment(ast.parse(source),check,'fixture.py')
                self.controls.append(dict(test=self.id(),source=source,new='REFUSE',error=str(context.exception)))
        clean='import os\nenv={**os.environ,"Q":"opaque"}\nsubprocess.run(env=env)\nos.environ.update(Q="1")'
        self.assertTrue(N.scan_python_environment(ast.parse(clean),check,'fixture.py'))

    def test_executable_inventory_is_recursive(self):
        # The injected files exist only in this in-memory inventory.
        rglob=Path.rglob;read_text=Path.read_text;read_bytes=Path.read_bytes
        for relative,raw in [('k/a.py',b'os.environ["BeNcHmArK"]="q"\n'),
            ('k/a.sh',b'export BeNcHmArK=1\n')]:
            path=K/relative
            def paths(root,pattern):
                yield from rglob(root,pattern)
                if root==K and pattern in ('*','*'+path.suffix):yield path
            def text(p,*a,**kw):return raw.decode() if p==path else read_text(p,*a,**kw)
            def binary(p):return raw if p==path else read_bytes(p)
            with self.subTest(relative=relative),patch.object(Path,'rglob',paths),patch.object(Path,'read_text',text),patch.object(Path,'read_bytes',binary):
                with self.assertRaisesRegex(ValueError,'(INPUT_NAME|EXECUTABLE_NAME):.*BeNcHmArK') as context:N.scan_decoded(K)
            self.controls.append(dict(test=self.id(),document=relative,new='REFUSE',error=str(context.exception)))

    def test_final_kit(self):
        result=N.scan_decoded(K);self.assertEqual(result['status'],'PASS')
        self.assertEqual(len(result['provenance_allowlist']),6)
        self.assertTrue(result['environment_sinks'])
        J.write(D/'SCAN.json',result)

    @classmethod
    def tearDownClass(cls):J.write(D/'MUTATIONS.json',cls.controls)
