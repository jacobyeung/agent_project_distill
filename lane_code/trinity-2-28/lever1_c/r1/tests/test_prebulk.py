"""Require a failed real worker boot before any bulk source opens."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'tests'))
import test_bootstrap as B


class PrebulkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.evidence=dict(delivery_sha256=B.sha(HERE/'out/delivery.tgz'),cases=[])
    @classmethod
    def tearDownClass(cls):(HERE/'out/PREBULK_CHECKS.json').write_text(getattr(json,'_a0_dumps',json.dumps)(cls.evidence,indent=2)+'\n')
    def failure(self,case):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,case)
        env['CUDA_VISIBLE_DEVICES']=''
        if case!='boot_cpu':env['SLURM_JOB_GPUS']='0'
        result=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        local=root/'work'/('a173925'+pub['token'])
        if case=='boot_cpu':local=local/'34'
        counts=B.decoded((local/'33.json').read_bytes())
        self.assertEqual(counts['bulk_calls'],0);self.assertEqual(counts['bulk_bytes'],0)
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',str(p),
                 '/project/community/jjyeung/okh7/ae71c903',str(root/'pool'),'173925',str(HERE/'orchard/o_fetch.sh')]
        fetched=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertEqual(fetched.returncode,0,fetched.stdout+fetched.stderr)
        with tarfile.open(p/'a/f/0.tgz') as archive:
            trace=[]
            for entry in archive:
                if entry.name.endswith('.json'):
                    value=B.decoded(archive.extractfile(entry).read())
                    if isinstance(value,dict):trace.extend(value.get('lines',[]))
            self.assertTrue(any("No module named 'a_missing_closure'" in line for line in trace),trace[-30:])
            boot=B.decoded(archive.extractfile('metadata/25.json').read())
            self.assertFalse(boot['passed']);self.assertEqual(boot['bulk_bytes'],0)
            self.assertEqual(boot['child_returncode'],1)
            self.assertEqual(boot['worker_returncode'],1)
            self.assertIsNone(boot['child_signal']);self.assertIsNone(boot['worker_signal'])
            self.assertEqual(boot['failed_module'],'a_missing_closure')
            tail=B.decoded(archive.extractfile('metadata/27.json').read())
            self.assertEqual(tail,boot['child_output'])
            self.assertTrue(any('a_missing_closure' in line for line in tail['lines']))
            self.assertEqual(B.decoded((p/'a/25.json').read_bytes()),boot)
        self.assertEqual(B.decoded((p/'a/f/EXIT.json').read_bytes())['status'],'FAILED')
        self.evidence['cases'].append(dict(case=case,passed=True,**counts,boot=boot,production_fetch=True,
            fetched_sha256=B.sha(p/'a/f/0.tgz'),binding='Local interpreter and filesystem replace remote runtime archives and bwrap; worker entry, loader, environment constructor, cwd, stage and fetch are real'))
    def test_success_receipt_precedes_first_bulk_source(self):
        root,p,pub,env,argv=B.BootstrapTests.setup_case(self,'boot_success')
        env.update(CUDA_VISIBLE_DEVICES='',SLURM_JOB_GPUS='0')
        result=subprocess.run(argv,env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        local=root/'work'/('a173925'+pub['token'])
        counts=B.decoded((local/'33.json').read_bytes())
        self.assertEqual(counts['bulk_calls'],1)
        self.assertTrue(counts['boot_passed_before_bulk'])
        self.evidence['success_order']=dict(passed=True,**counts,closure='Small fixture closure in the real worker; full production closure is checked separately')

    def test_manifest_covers_current_audited_closure(self):
        sys.path.insert(0,str(HERE))
        import import_audit,boot_order
        audit=import_audit.audit()
        self.assertTrue(audit['passed'],audit['unresolved'])
        files=import_audit.unpack(import_audit.unpack((HERE/'out/delivery.tgz').read_bytes())['0.tgz'])
        manifest=import_audit.decode(files['g/3.json']);expected=boot_order.closure(audit)
        self.assertEqual(manifest,expected)
        self.evidence['closure']=dict(modules=len(manifest['modules']),symbols=len(manifest['symbols']),passed=True)

    def test_mixed_archive_never_materializes_bulk(self):
        import io,hashlib,runpy,tempfile
        scope=runpy.run_path(str(HERE/'runtime/boot.py'))
        sys.path.insert(0,str(HERE))
        import build_depth
        root=Path(tempfile.mkdtemp(dir=HERE.parent/'r1_fixtures_old',prefix='mix_'))
        path=root/'0.tar'
        with tarfile.open(path,'w') as archive:
            for name,data in [('v/py',b'python fixture'),('q/0',b'policy fixture'),('m544/0',b'weights'),('f/0',b'frames')]:
                item=tarfile.TarInfo(name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        spec=dict(parts=[dict(path=str(path),bytes=len(raw),sha256=sha)],sha256=sha,destination='d',expanded_bytes=10240)
        # Load the actual delivered extractor, without a model environment.
        from types import ModuleType,SimpleNamespace
        files=build_depth.B.read_tar((HERE/'out/delivery.tgz').read_bytes())
        outer={m.name:d for m,d in files};inner={m.name:d for m,d in build_depth.B.read_tar(outer['0.tgz'])}
        chain=ModuleType('chain_save');exec(inner['orchard_h10/vendor/chain_save.py'],chain.__dict__);sys.modules['chain_save']=chain
        stage=ModuleType('a_stage');exec(inner['orchard_h10/vendor/orchard_stage.py'],stage.__dict__)
        stage.room=lambda *args:None
        result=scope['environment_archive'](spec,root,stage)
        self.assertEqual(result['bytes'],len(raw))
        self.assertEqual(result['extracted_bytes'],28)
        self.assertFalse((root/'d/m544').exists());self.assertFalse((root/'d/f').exists())
        self.assertEqual((root/'d/v/py').read_bytes(),b'python fixture')
        spec['sha256']='0'*64;spec['destination']='e'
        with self.assertRaisesRegex(ValueError,'E85'):scope['environment_archive'](spec,root,stage)
        self.evidence['mixed_archive']=dict(passed=True,bulk_bytes=0,authenticated_before_boot=True)

    def test_gpu_missing_closure_before_bulk(self):self.failure('boot_gpu')
    def test_cpu_missing_closure_before_bulk(self):self.failure('boot_cpu')

if __name__=='__main__':unittest.main(verbosity=2)
