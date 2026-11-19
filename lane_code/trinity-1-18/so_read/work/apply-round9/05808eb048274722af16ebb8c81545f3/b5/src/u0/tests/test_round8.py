"""Round-8 regressions: real loader admission, environment binding and fixed export."""
import copy
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import types
import unittest
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SRC),str(SRC/'b'),str(SRC/'u0'),str(SRC/'u0/tests'),str(L/'out/kit_parity50')]
import torch
torch.set_num_threads(8)
import test_round6 as r6
import test_round5 as r5
BEFORE=os.environ.get('READ_ROUND8_BEFORE')=='1'
OUT=L/'out_round8' if BEFORE else L/'out'
E=L/'work/round8-before-u0' if BEFORE else SRC/'u0'
OP=Path(os.environ.get('READ_OPERATOR4_SOURCE',str(L/'work/operator4')))
sha=r5.sha;write=r5.write;fresh=r5.fresh;load=r5.load

class PassedAdmission(Exception):pass

class Round8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node=load('node8',L/'work/round8-before-5.py' if BEFORE else OP/'package/a/5.py')
        cls.builder=load('builder8',E/'a19.py');cls.helper=load('helper8',E/'a20.py')
        cls.kit=load('kit8',OUT/'kit_parity50/run.py')

    def stage(self,root,d,namespace=None):
        dest=root/'4.tar';results=root/'results';results.mkdir(exist_ok=True)
        kwargs={'results':results} if 'results' in inspect.signature(self.node.stage_gate_assets).parameters else {}
        return self.node.stage_gate_assets(root,dict(read_extensions=True,logical=str(d.parent)),
            types.SimpleNamespace(namespace=namespace or (lambda _:[])),dest,subprocess.run,dict(os.environ),**kwargs)

    def test_f1_preserved_absolute_link_passes_real_artifact_and_load_native(self):
        from e2e_reader.artifact import Artifact,build_manifest,write_manifest
        from e2e_reader import parity
        root=fresh();d=root/'logical/d';e=d/'e';m=d/'m400';e.mkdir(parents=True);m.mkdir()
        (m/'heads.pt').write_bytes(b'heads fixture')
        (e/'heads.pt').symlink_to(m/'heads.pt')
        (m/'shard').write_bytes(b'weights fixture')
        write(e/'full_weights.json',dict(root=str(m),files=['shard']))
        write(e/'artifact.json',dict(heads=dict(path=str(e/'heads.pt')),full_weights=dict(path=str(e/'full_weights.json'))))
        write(d/'config.json',{})
        write(e/'receipt.json',dict(model=dict(path=str(e/'full_weights.json'),sha256=sha(e/'full_weights.json')),camera={}))
        write(e/'RESTORE.json',dict(local={},original=dict(config=dict(sha256=sha(d/'config.json')))))
        names=['m400/heads.pt','m400/shard','e/artifact.json','e/full_weights.json']
        manifest=build_manifest(d,{'fixture':('checkpoint',names)})
        _,pin=write_manifest(d,manifest)
        record=self.stage(root,d)
        d.rename(d.with_name('retained'));d.mkdir()
        subprocess.run(['/bin/tar','-xf',record['path'],'-C',str(d)],check=True)
        artifact=Artifact(d,'E2E_MANIFEST.json',pin,required_roles=('checkpoint',)).verify()
        trainer=types.ModuleType('student_pilot.carrier_c1_run')
        def reached(*a,**k):raise PassedAdmission()
        trainer.processor_for_receipt=reached
        parent=types.ModuleType('student_pilot');parent.carrier_c1_run=trainer
        with patch.object(parity,'install'),patch.dict(sys.modules,{'student_pilot':parent,'student_pilot.carrier_c1_run':trainer}):
            try:
                with self.assertRaises(PassedAdmission):parity.load_native(e,settings={'config':str(d/'config.json')},artifact=artifact)
            except ValueError as error:self.fail('Real load_native rejected extracted link: '+str(error))
        self.assertTrue((e/'heads.pt').is_symlink())
        self.assertIn(str((e/'heads.pt').resolve()),artifact.allowed)
        print('Absolute e/heads.pt symlink survives tar/extract; real Artifact.verify and load_native admission pass before model loading.')

    def test_f1_external_symlinks_refuse_before_archive(self):
        for kind in ('absolute','relative','directory','chain','dangling','cycle'):
            with self.subTest(kind=kind):
                root=fresh();d=root/'logical/d';d.mkdir(parents=True);outside=root/'outside';outside.mkdir();(outside/'value').write_text('outside')
                link=d/'bad'
                if kind=='relative':link.symlink_to('../../outside/value')
                elif kind=='directory':link.symlink_to(outside,target_is_directory=True)
                elif kind=='chain':
                    (d/'chain').symlink_to(outside/'value');link.symlink_to('chain')
                elif kind=='dangling':link.symlink_to(outside/'missing')
                elif kind=='cycle':link.symlink_to('bad')
                else:link.symlink_to(outside/'value')
                # Old tar may itself reject dangling/cyclic links. Its stderr must identify validation.
                try:self.stage(root,d)
                except subprocess.CalledProcessError:pass
                else:self.fail('Archive accepted escaping symlink: '+kind)
                err=root/'results/4.err'
                self.assertTrue(err.exists(),'Symlink refusal diagnostic is missing')
                self.assertIn('symlink',err.read_text().lower())

    def test_info_tar_stderr_is_retained(self):
        root=fresh();d=root/'logical/d';d.mkdir(parents=True)
        script=root/'fail.py';script.write_text('import sys\nprint("fixture tar failed",file=sys.stderr)\nraise SystemExit(17)\n')
        with self.assertRaises(subprocess.CalledProcessError):
            self.stage(root,d,lambda _:[sys.executable,'-I','-s','-B',str(script)])
        err=root/'results/4.err';self.assertTrue(err.exists(),'Tar stderr was discarded')
        self.assertIn('fixture tar failed',err.read_text())

    def test_f2_runtime_environment_and_receipt(self):
        self.assertTrue(hasattr(self.kit,'validate_environment'),'GPU environment lacks a preflight')
        root=fresh();env=root/'ENVIRONMENT.json'
        write(env,dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9',python='/opaque/d/v/py'))
        expected=dict(sha256=sha(env),torch='2.11.0+cu129',transformers='5.12.0',cuda='12.9')
        cfg=dict(environment_receipt=str(env),adoption_environment=expected,adoption_kit=self.kit.kit_hashes(),
            adoption_plan_sha256='a'*64,adoption_profile={},adoption_assets={},required_device_type='H100_80GB')
        fake_torch=types.SimpleNamespace(__version__=expected['torch'],version=types.SimpleNamespace(cuda=expected['cuda']))
        fake_transformers=types.SimpleNamespace(__version__=expected['transformers'])
        with patch.dict(sys.modules,torch=fake_torch,transformers=fake_transformers):
            self.assertEqual(self.kit.validate_environment(cfg),expected)
            self.kit.write_gate_receipt(root,cfg,True,**({'guard_self_test':{'passed':True,'checks':dict(add_=True,copy_=True,load_state_dict=True)}} if 'guard_self_test' in inspect.signature(self.kit.write_gate_receipt).parameters else {}))
            from a9 import read_wire
            self.assertEqual(read_wire(json.loads((root/'ue.json').read_text()))['adoption_environment'],expected)
            for field in ('torch','transformers','cuda'):
                bad=copy.deepcopy(cfg);bad['adoption_environment'][field]='wrong'
                with self.subTest(field=field),self.assertRaises(ValueError):self.kit.validate_environment(bad)
            raw=env.read_bytes();env.write_bytes(raw+b'\n')
            with self.assertRaises(ValueError):self.kit.validate_environment(cfg)
            env.write_bytes(raw);fake_torch.version.cuda=None
            with self.assertRaises(ValueError):self.kit.validate_environment(cfg)
        print('Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.')

    def test_f2_gpu_shell_preflight_executes_archived_interpreter(self):
        # Use A4's real namespace argv; never substitute a host-executable d/v/py.
        host_path=OUT/'kit_parity50/host.py'
        self.assertTrue(host_path.is_file(),'Preflight lacks A4 namespace launcher')
        host=load('host8',host_path)
        from orchard_h10.common import template
        _,J,*_=template()
        root=fresh();inputs={'python':'/scratch/jjyeung/b01ec87a6f29b/d/v/py'}
        args=['-c',host.PREFLIGHT,'/scratch/jjyeung/a123456789abc/u0/u2.json']
        command=host.namespace_command(root,inputs,J,args)
        self.assertEqual(command,J.namespace(root)+[inputs['python'],'-B','-I']+args)
        self.assertNotIn('sys.executable',inspect.getsource(self.kit.main))
        self.assertEqual(inspect.getsource(self.kit.main).count('worker_command('),3)
        self.assertIn('namespace_command',inspect.getsource(self.kit.worker_command))
        print('Preflight and every worker launch require real A4 namespace argv and the authenticated wrapper path; no host d/v/py test double.')

    def test_f2_gate_authenticates_environment_before_gpu(self):
        self.assertIn('environment',inspect.getsource(self.helper.gate),'Gate omits CPU environment receipt binding')
        r6.Round6Tests.setUpClass();fixture=r6.Round6Tests();fixture.target=r6.Round6Tests.target;fixture.helper=self.helper
        root,args,template=fixture.gate_fixture()
        cfg=r6.selected_gate(self.helper,args)
        self.assertEqual(cfg['adoption_environment']['sha256'],sha(root/'ENVIRONMENT.json'))
        write(root/'ENVIRONMENT.json',dict(versions=dict(torch='wrong',transformers='5.12.0'),cuda='12.9'))
        with self.assertRaisesRegex(ValueError,'Environment'):r6.selected_gate(self.helper,args)

    def test_f2_submit_checks_environment_versions_and_sha(self):
        r6.Round6Tests.setUpClass();fixture=r6.Round6Tests();fixture.target=r6.Round6Tests.target
        fixture.helper=self.helper;fixture.builder=self.builder
        p,proof,command=fixture.submit_fixture()
        from a9 import pack,read_wire
        value=read_wire(json.loads((p/'a/g.json').read_text()))
        # Supply an independently CPU-bound environment even to the reviewed checker.
        environment=dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9')
        write(p/'a/c/ENVIRONMENT.json',environment);proof['ready']['environment']=sha(p/'a/c/ENVIRONMENT.json');write(p/'a/c/CPU.json',proof)
        expected=dict(sha256=proof['ready']['environment'],torch=environment['versions']['torch'],transformers='5.12.0',cuda='12.9')
        value['adoption_environment']=expected;write(p/'a/g.json',{'u0':pack(value)})
        result=subprocess.run(command,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
        for field in expected:
            bad=copy.deepcopy(value);bad['adoption_environment'][field]='wrong';write(p/'a/g.json',{'u0':pack(bad)})
            with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)

    def test_f3_builder_refuses_other_export_before_reading_base(self):
        binding=json.loads((L/'out/operations/binding.default.json').read_text())
        for key in ('step','run','member_directory','lineage','object','config_sha256','archive_sha256','archive_bytes','base_identity','frame_layout','preparation_sha256'):
            root=fresh();bad=copy.deepcopy(binding)
            if key=='step':bad[key]=600
            elif key=='archive_bytes':bad[key]+=1
            elif key=='preparation_sha256':bad[key]['config']='a'*64
            elif key in ('config_sha256','archive_sha256'):bad[key]='a'*64
            elif key=='lineage':bad[key]='RL'
            else:bad[key]='other'
            write(root/'binding.json',bad)
            with self.subTest(field=key):
                try:
                    with self.assertRaisesRegex(ValueError,'step.400'):
                        self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
                except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                self.assertFalse((root/'output').exists())
        self.assertNotIn('--bound-export',(OUT/'kit_parity50/README.md').read_text())
        self.assertNotIn('For a different target',(OUT/'kit_parity50/README.md').read_text())

    def test_f4_readme_archive_path_accepts_symlinked_parent(self):
        text=(OUT/'kit_parity50/README.md').read_text();code=text.split("<<'PYASSET'\n")[1].split('\nPYASSET')[0]
        root=fresh();p=root/'physical';(p/'a/c').mkdir(parents=True);alias=root/'alias';alias.symlink_to(p,target_is_directory=True)
        (p/'a/4.tar').write_bytes(b'fixture archive')
        cfg=dict(logical='/scratch/jjyeung/abcdef123456')
        (p/'0.tgz').write_bytes(self.builder.tarbytes({'9.json':json.dumps(cfg).encode()}))
        write(p/'a/c/CPU.json',dict(passed=True,gate_assets=dict(logical=cfg['logical'],path=str(p/'a/4.tar'),bytes=(p/'a/4.tar').stat().st_size,sha256=sha(p/'a/4.tar'))))
        result=subprocess.run([sys.executable,'-I','-s','-B','-',str(alias),str(p/'a/4.tar')],input=code,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),cfg['logical'])

    def test_info_gpu_commands_and_aliases(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        self.assertIn("inputs['python']",text)
        self.assertIn('XDG_CACHE_HOME/HF_HOME/TRITON_CACHE_DIR',text)
        self.assertIn('aliases must be symlinks',text.lower())
        self.assertIn('--job-name="a15_cot_ap${GATE_TOKEN}"',text)
        self.assertIn('secrets.token_hex',text)
        self.assertRegex(text,r'33 GB.{0,50}estimat|estimat.{0,50}33 GB')
        self.assertNotIn('cp "$GPU_LOGICAL/d/binding.json"',text)

if __name__=='__main__':unittest.main(verbosity=2)
