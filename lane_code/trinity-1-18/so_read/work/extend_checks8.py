from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0/tests'
p=E/'test_round3.py';s=p.read_text().replace("patch.object(sys,'argv',['u0.py']),patch.object(torch.cuda,'is_available',return_value=False):", "patch.object(sys,'argv',['u0.py']),patch.object(torch.cuda,'is_available',return_value=False), \\\n                 patch.object(kit,'validate_environment',return_value=None,create=True):");p.write_text(s)
p=E/'test_round8.py';s=p.read_text();at=s.index('    def test_f2_submit_checks_environment_versions_and_sha')
s=s[:at]+'''    def test_f2_gpu_shell_preflight_executes_archived_interpreter(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        self.assertIn('# BEGIN GPU_ENVIRONMENT',text,'GPU shell preflight is missing')
        block=text.split('# BEGIN GPU_ENVIRONMENT\\n')[1].split('# END GPU_ENVIRONMENT')[0]
        root=fresh();logical=root/'logical';(logical/'d/v').mkdir(parents=True)
        # The executable at d/v/py is a test double for CUDA imports only.
        # Execute the actual README heredoc and shell setup without a GPU.
        wrapper=logical/'d/v/py'
        wrapper.write_text('#!'+sys.executable+'\\n'+"""import os,sys,types
values={'torch':'2.11.0+cu129','transformers':'5.12.0','cuda':'12.9'}
key=os.environ.get('MUTATE_ENVIRONMENT')
if key in values:values[key]='wrong'
t=types.ModuleType('torch');t.__version__=values['torch'];t.version=types.SimpleNamespace(cuda=values['cuda'])
t.set_num_threads=lambda n:None;t.cuda=types.SimpleNamespace(is_available=lambda:key!='available')
f=types.ModuleType('transformers');f.__version__=values['transformers']
sys.modules.update(torch=t,transformers=f)
sys.argv=['-',sys.argv[-1]]
exec(compile(sys.stdin.read(),'<README GPU preflight>','exec'))
""")
        wrapper.chmod(0o700)
        write(logical/'d/ENVIRONMENT.json',dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9'))
        block=block.replace('GPU_KIT=/scratch/jjyeung/ab0123456789','GPU_KIT='+str(root/'kit'))
        env=dict(os.environ,GPU_LOGICAL=str(logical),READ_PYTHON='/wrong/interpreter')
        result=subprocess.run(['bash','-eu','-c',block],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('preflight passed',result.stdout)
        for key in ('torch','transformers','cuda','available'):
            with self.subTest(field=key):
                result=subprocess.run(['bash','-eu','-c',block],env=dict(env,MUTATE_ENVIRONMENT=key),capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn('preflight failed',result.stderr)
        print('README GPU block runs d/v/py and refuses each version mismatch or unavailable CUDA; CUDA imports are test doubles.')

    def test_f2_gate_authenticates_environment_before_gpu(self):
        self.assertIn('environment',inspect.getsource(self.helper.gate),'Gate omits CPU environment receipt binding')
        r6.Round6Tests.setUpClass();fixture=r6.Round6Tests();fixture.target=r6.Round6Tests.target;fixture.helper=self.helper
        root,args,template=fixture.gate_fixture()
        cfg=r6.selected_gate(self.helper,args)
        self.assertEqual(cfg['adoption_environment']['sha256'],sha(root/'ENVIRONMENT.json'))
        write(root/'ENVIRONMENT.json',dict(versions=dict(torch='wrong',transformers='5.12.0'),cuda='12.9'))
        with self.assertRaisesRegex(ValueError,'Environment'):r6.selected_gate(self.helper,args)

'''+s[at:];p.write_text(s)
print('Added executable GPU shell preflight and CPU-bound environment gate tests; isolated legacy worker-setup test from environment preflight.')
