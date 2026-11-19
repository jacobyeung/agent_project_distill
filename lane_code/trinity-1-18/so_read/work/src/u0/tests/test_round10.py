"""Executable wrapper, staged aliases, direct workers and one-pass archive checks."""
import copy
import hashlib
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import types
import unittest
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SRC),str(SRC/'u0'),str(SRC/'u0/tests')]
import torch
torch.set_num_threads(8)
import test_round5 as r5
BEFORE=os.environ.get('READ_ROUND10_BEFORE')=='1'
OUT=L/('out_round10' if BEFORE else 'out')
BOOT=b'''"""Interpreter front end: template venv plus the pinned overlay in d/v/site (appended, base wins)."""
import runpy
import site
import sys

args = sys.argv[1:]
while args and args[0] in ('-B', '-I', '-s', '-E'):
    args.pop(0)
if not args or args[0].startswith('-'):
    raise SystemExit('boot.py runs a script path only')
site.addsitedir('/scratch/jjyeung/b01ec87a6f29b/d/v/site')
sys.argv = args
runpy.run_path(args[0], run_name='__main__')
'''
WRAPPER=b'#!/bin/sh\nexec /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python -I -B /scratch/jjyeung/b01ec87a6f29b/d/v/boot.py "$@"\n'
WRAPPER_PINS={'v/py':{'bytes':160,'sha256':'6fcf54ddf27fe5e2f755b8c3bacef8322486b5b292625847baa77d4fcc632416'},
              'v/boot.py':{'bytes':443,'sha256':'bce29ff7a0fe85d34d31a419d6ad1d0f9f333ef97b7a7fc2ce5ddcfb7da4536f'}}

class Round10Tests(unittest.TestCase):
    def setUp(self):
        self.host=r5.load('host10',OUT/'kit_parity50/host.py')
        self.kit=r5.load('kit10',OUT/'kit_parity50/run.py')

    def test_f1_real_boot_refuses_c_and_runs_actual_preflight_script(self):
        self.assertTrue((OUT/'kit_parity50/u5.py').is_file(),'Preflight must be a shipped script')
        root=r5.fresh();v=root/'v';v.mkdir();kit=root/'u0';kit.mkdir()
        for name,raw in (('v/py',WRAPPER),('v/boot.py',BOOT)):
            self.assertEqual(dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),WRAPPER_PINS[name])
        (v/'boot.py').write_bytes(BOOT)
        # Only the wrapper double changes: use the test interpreter and relocate
        # its boot pathname into the fixture. The complete boot bytes stay exact.
        command=WRAPPER.decode().replace(WRAPPER.decode().split()[2],sys.executable).replace('/scratch/jjyeung/b01ec87a6f29b/d/v/boot.py',str(v/'boot.py'))
        (v/'py').write_text(command);(v/'py').chmod(0o700)
        refused=subprocess.run([str(v/'py'),'-B','-I','-c','print(1)'],capture_output=True,text=True)
        self.assertNotEqual(refused.returncode,0);self.assertIn('boot.py runs a script path only',refused.stderr)
        (kit/'u5.py').write_bytes((OUT/'kit_parity50/u5.py').read_bytes())
        (kit/'a9.py').write_bytes((OUT/'kit_parity50/a9.py').read_bytes())
        (kit/'u0.py').write_text("def validate_kit(cfg): pass\ndef validate_environment(cfg):\n assert cfg == {'fixture': True}\nif __name__ == '__main__': print('Parent fixture ran')\n")
        (kit/'torch.py').write_text("class cuda:\n @staticmethod\n def is_available(): return True\ndef set_num_threads(n): assert n == 8\n")
        from a9 import pack
        (kit/'u2.json').write_text(json.dumps({'u0':pack({'fixture':True})}))
        J=types.SimpleNamespace(namespace=lambda root:[],environment=lambda root:dict(os.environ))
        real_run=subprocess.run;calls=[]
        def capture(argv,**kwargs):
            calls.append(argv)
            result=real_run(argv,**kwargs,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            if len(calls)==1:self.assertIn('Environment preflight passed',result.stdout)
            return result
        with patch.object(self.host,'runtime_context',return_value=({'python':str(v/'py')},None,J)),patch.object(self.host.subprocess,'run',side_effect=capture):
            self.assertEqual(self.host.launch(root,str(root)),0)
        self.assertEqual(calls[0],[str(v/'py'),'-B','-I',str(kit/'u5.py'),str(kit/'u2.json')])
        self.assertEqual((v/'boot.py').read_bytes(),BOOT)
        print('Exact 443-byte boot refuses -c; host launches the shipped preflight and parent through the wrapper double. CUDA/version imports are explicit CPU stubs.')

    def test_f1_public_script_is_pinned_and_tampering_refuses(self):
        self.assertIn('u5.py',self.kit.kit_hashes(),'Missing executable preflight hash')
        root=r5.fresh();dest=root/'u0'
        helper=L/'work/round10-before-a11.py' if BEFORE else SRC/'u0/a11.py'
        cmd=[sys.executable,'-I','-s','-B',str(helper),'stage-kit','--source-root',str(SRC),'--input',str(OUT/'kit_parity50'),'--out',str(dest)]
        subprocess.run(cmd,check=True,capture_output=True)
        staged=r5.load('public10',dest/'u0.py')
        cfg={'adoption_kit':staged.kit_hashes()};staged.validate_kit(cfg)
        self.assertEqual((dest/'u5.py').read_bytes(),(OUT/'kit_parity50/u5.py').read_bytes())
        (dest/'u5.py').write_bytes((dest/'u5.py').read_bytes()+b'\n')
        with self.assertRaises(ValueError):staged.validate_kit(cfg)
        print('Public u0/u5.py preserves shipped bytes; validate_kit rejects its mutation.')

    def fixture(self):
        from orchard_h10.common import template
        S,J,*_=template();root=r5.fresh();package=root/'package';(package/'a/c').mkdir(parents=True)
        original=Path(os.environ['READ_INPUT_SRC']).parent/'package'
        for name in ('0.tgz','0.json','a/1.json'):(package/name).write_bytes((original/name).read_bytes())
        public=json.loads((package/'0.json').read_text())
        with tarfile.open(package/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
        logical=cfg['logical'];archive=package/'a/4.tar'
        files={'binding.json':b'{}','ENVIRONMENT.json':b'{}','6.json':b'{}','e/0':b'e','f/0':b'f','h/0':b'h','s/0':b's',
               'p0/config.json':b'{}','k/sam3.pt':b'weights','k/SAM3_RECEIPT.json':b'{}','v/site/0':b'site'}
        with tarfile.open(archive,'w') as t:
            for name,raw in files.items():
                m=tarfile.TarInfo(name);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
        asset=dict(path=str(archive),logical=logical,bytes=archive.stat().st_size,sha256=r5.sha(archive))
        proof=dict(passed=True,payload=public['payload_sha256'],plan=public['plan_sha256'],inputs=r5.sha(package/'a/1.json'),gate_assets=asset)
        (package/'a/c/CPU.json').write_text(json.dumps(proof));physical=root/'root';physical.mkdir()
        return root,package,physical,archive,cfg,S,J

    def test_f2_stage_resolves_every_sealed_path_with_one_alias_table(self):
        self.assertTrue(hasattr(self.host,'ALIASES'),'Missing shared prepared-path aliases')
        from a11 import relocate
        from a9 import seal_settings,read_wire,validate_paths
        root,package,physical,archive,cfg,S,J=self.fixture();logical=cfg['logical'];real_popen=subprocess.Popen
        def local_tar(argv,**kwargs):
            self.assertEqual(argv,J.namespace(physical)+['/bin/tar','-xf','-','-C',logical+'/d'])
            return real_popen(['/bin/tar','-xf','-','-C',str(J.physical(physical,logical+'/d'))],**kwargs)
        with patch.object(self.host,'stage_runtime',return_value={}),patch.object(S,'room'),patch.object(J,'storage_proof'),patch.object(self.host.subprocess,'Popen',side_effect=local_tar),patch.dict(os.environ,USER='jjyeung',SLURM_JOB_ID='123'):
            self.host.stage(package,physical,'/scratch/jjyeung/a123456789abc',archive)
        settings=dict(export_dir=logical+'/d/e',artifact_manifest=logical+'/d/binding.json',tree=logical+'/p/tree',
            config=logical+'/d/p0/config.json',frames_root=logical+'/d/f',selector_head=logical+'/d/h',
            sam3=dict(source_root=logical+'/d/s',checkpoint_path=logical+'/d/k/sam3.pt',receipt_path=logical+'/d/k/SAM3_RECEIPT.json'),
            env_roots=[logical+'/d/v/site'],environment_receipt=logical+'/d/ENVIRONMENT.json',export_pin=logical+'/d/6.json')
        neutral=relocate(settings,self.host.private_aliases(logical));sealed=root/'sealed.json';seal_settings(neutral,sealed)
        decoded=read_wire(json.loads(sealed.read_bytes()));validate_paths(decoded)
        seen=[]
        def resolve(value):
            if isinstance(value,dict):
                for v in value.values():resolve(v)
            elif isinstance(value,list):
                for v in value:resolve(v)
            elif isinstance(value,str) and value.startswith('/'):
                path=J.physical(physical,value);self.assertTrue(path.exists(),value);seen.append(value)
        resolve(decoded)
        for alias,target in self.host.ALIASES:
            p=J.physical(physical,logical+'/d/'+alias)
            self.assertTrue(p.is_symlink());self.assertEqual(p.resolve(),J.physical(physical,logical+'/'+target).resolve())
        self.assertEqual(len(seen),12)
        print('host.stage creates every shared alias; all 12 absolute settings paths seal and resolve, including code and site roots. Runtime and namespace execution are explicit doubles.')

    def test_f2_missing_nested_path_refuses_before_self_test(self):
        self.assertTrue(hasattr(self.kit,'validate_existing_paths'),'Missing pre-self-test path admission')
        root=r5.fresh();(root/'present').write_text('ok')
        self.kit.validate_existing_paths({'nested':[str(root/'present')]})
        with self.assertRaisesRegex(ValueError,'missing'):
            self.kit.validate_existing_paths({'nested':[{'path':str(root/'absent')}]})
        source=inspect.getsource(self.kit.main)
        self.assertIn('validate_existing_paths(settings)',source)
        self.assertLess(source.index('validate_existing_paths(settings)'),source.index('guard_self_test('))
        print('Nested missing absolute settings path refuses before the guard self-test; existing paths pass.')

    def test_f3_workers_are_direct_inside_namespace(self):
        root=r5.fresh();inputs={'python':'/scratch/jjyeung/b01ec87a6f29b/d/v/py'}
        from orchard_h10.common import template
        S,J,*_=template()
        with patch.object(self.kit,'host_module',return_value=self.host),patch.object(self.host,'runtime_context',return_value=(inputs,S,J)),patch.dict(os.environ,U0_ROOT=str(root),U0_KIT='/scratch/jjyeung/a123456789abc',USER='jjyeung',SLURM_JOB_ID='123'):
            self.assertEqual(self.kit.worker_command(['u0.py','u2.json']),[inputs['python'],'-B','-I','u0.py','u2.json'])
            env=self.kit.worker_environment();self.assertEqual(env['OPENBLAS_NUM_THREADS'],'1');self.assertEqual(env['HOME'],str(root/'home'))
        print('U0_ROOT workers call inputs[python] directly and retain J.environment; no nested bwrap.')

    def test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin(self):
        self.assertTrue(hasattr(self.host,'extract_assets'),'Missing one-pass extraction/hash')
        root=r5.fresh();archive=root/'4.tar'
        with tarfile.open(archive,'w') as t:
            raw=b'fixture';m=tarfile.TarInfo('0');m.size=len(raw);t.addfile(m,io.BytesIO(raw))
        asset=dict(bytes=archive.stat().st_size,sha256=r5.sha(archive));real_open=Path.open
        for corrupt in (False,True):
            dest=root/('bad' if corrupt else 'good');dest.mkdir();opens=[];reads=[]
            class Counted:
                def __enter__(self):self.stream=real_open(archive,'rb');return self
                def __exit__(self,*a):self.stream.close()
                def read(self,n):
                    raw=self.stream.read(n);reads.append(len(raw));return raw
            def counted(path,*a,**kw):
                if path==archive and a==('rb',):opens.append(path);return Counted()
                return real_open(path,*a,**kw)
            pin=dict(asset,sha256='0'*64) if corrupt else asset
            with patch.object(Path,'open',counted):
                if corrupt:
                    with self.assertRaisesRegex(ValueError,'archive differs'):self.host.extract_assets(archive,pin,['/bin/tar','-xf','-','-C',str(dest)],dict(os.environ))
                else:self.host.extract_assets(archive,pin,['/bin/tar','-xf','-','-C',str(dest)],dict(os.environ))
            self.assertEqual(len(opens),1);self.assertEqual(sum(reads),asset['bytes']);self.assertEqual((dest/'0').read_bytes(),b'fixture')
        self.assertNotIn('sha(archive)',inspect.getsource(self.host.stage))
        print('Extraction reads all 10,240 archive bytes once, hashes the same stream, and refuses a changed hash before publishing staging success.')

    def test_f4_readme_has_no_asset_preread_and_generates_aliases(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        block=text.split("<<'PYASSET'",1)[1].split('\nPYASSET',1)[0]
        self.assertNotIn("archive.open('rb')",block,'README rehashes the archive before staging')
        self.assertIn('host.private_aliases',text,'README must generate from the staging alias table')
        self.assertIn('u0/u5.py',text)
        print('README generates PRIVATE_ALIASES from the host table and does not reread 4.tar before extraction.')

if __name__=='__main__':unittest.main(verbosity=2)
