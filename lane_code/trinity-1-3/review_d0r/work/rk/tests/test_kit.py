import ast
from contextlib import contextmanager
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit/launcher'))
import orchard_launcher as L
import orchard_stage as S
import orchard_job as J
import orchard_results as R
import export_stage as E
import chain_save as A
import return_io


def directory():
    p=ROOT/'evidence'/('test_'+uuid.uuid4().hex)
    p.mkdir();return p


def archive(root, bad=None):
    path=root/'input.tar'
    names=['m100/artifact.json','m100/heads.pt','m100/full_weights/full_weights.json']
    if bad=='missing':names.pop()
    if bad=='traversal':names.append('m100/../evil')
    if bad=='absolute':names.append('/m100/evil')
    if bad=='step':names.append('m200/evil')
    if bad=='extra':names.append('m100/extra')
    if bad=='duplicate':names.append(names[0])
    if bad=='collision':names.append('m100/full_weights/full_weights.json/evil')
    with tarfile.open(path,'w') as tf:
        for name in names:
            item=tarfile.TarInfo(name);item.size=2;tf.addfile(item,io.BytesIO(b'{}'))
        if bad in ('symlink','hardlink','fifo'):
            item=tarfile.TarInfo('m100/full_weights/evil')
            item.type={'symlink':tarfile.SYMTYPE,'hardlink':tarfile.LNKTYPE,'fifo':tarfile.FIFOTYPE}[bad]
            item.linkname='artifact.json';tf.addfile(item)
    done=root/'COMPLETE.json';done.write_text(json.dumps(dict(object='gs://x',bytes=path.stat().st_size,sha256=S.sha(path))))
    return path,done


class KitTests(unittest.TestCase):
    def test_prepare_both_steps_and_camera(self):
        for step,camera in [(100,False),(200,False),(100,True)]:
            dest=directory()/'prepared';token='a'+uuid.uuid4().hex[:12]
            cfg=L.prepare(token,dest,step,camera)
            L.validate_request(cfg);L.validate_batch((dest/'BATCH.sh').read_text(),cfg)
            self.assertEqual(cfg['families'],['main','away','forward']+(['camera'] if camera else []))
            args=L.submit_argv(None,token)
            self.assertIn('--partition=general',args);self.assertIn('--gres=gpu:1',args)
            self.assertIn('--job-name=a15_cot_ap'+token,args)
            self.assertNotIn('sbatch',L.submit_command(token)[:1])
            for word in ('revsi','vsi','distill','qgen','split'):
                self.assertNotIn(word,' '.join(args).lower())
            broken=copy.deepcopy(cfg);broken['families']=['main']
            with self.assertRaises(ValueError):L.validate_request(broken)
            with self.assertRaises(FileExistsError):L.prepare(token,dest,step,camera)

    def test_reject_identity_and_payload_tamper(self):
        for token in ('hasword','../123456789','p123456789'):
            with self.assertRaises(ValueError):L.valid_token(token)
        with self.assertRaises(ValueError):L.prepare('a123456789',directory()/'x',544)
        dest=directory()/'prepared';cfg=L.prepare('a'+uuid.uuid4().hex[:12],dest,100)
        with self.assertRaises(ValueError):L.validate_batch((dest/'BATCH.sh').read_text()+'x',cfg)
        broken=copy.deepcopy(cfg);broken['spec']['step']=200
        with self.assertRaises(ValueError):L.validate_request(broken)

    def stage_fixture(self,root,path,done):
        args=NS(root=str(root/'job'),run='359fcc3c',step=100,tar=str(path),done=str(done),full=True,bwrap='unused')
        with patch.object(E.T,'writable',side_effect=lambda p:Path(p)),\
             patch.object(E,'completed_local',side_effect=lambda p,tar=False:Path(p)),\
             patch.object(S,'room'),patch.object(E,'run_export_checker',return_value=dict(status='VERIFIED',step=100)):
            return E.stage_export(args)

    def test_archive_admission(self):
        root=directory();path,done=archive(root)
        result=self.stage_fixture(root,path,done)
        self.assertEqual(result['status'],'complete');self.assertEqual(result['checker_mode'],'full')
        self.assertEqual(result['tar_sha256'],S.sha(path))
        with self.assertRaisesRegex(ValueError,'exists'):self.stage_fixture(root,path,done)

    def test_archive_attacks(self):
        for bad in ('missing','traversal','absolute','step','extra','duplicate','collision','symlink','hardlink','fifo'):
            with self.subTest(bad=bad):
                root=directory();path,done=archive(root,bad)
                with self.assertRaises(ValueError):self.stage_fixture(root,path,done)
                self.assertFalse((root/'job/exports/359fcc3c_m100').exists())

    def test_digest_before_extraction(self):
        for field,value in [('sha256','0'*64),('bytes',1)]:
            root=directory();path,done=archive(root)
            info=json.loads(done.read_text());info[field]=value;done.write_text(json.dumps(info))
            with self.assertRaises(ValueError):self.stage_fixture(root,path,done)
            self.assertFalse((root/'job/exports/359fcc3c_m100').exists())

    def test_full_checker_on_miniature_tensor(self):
        import importlib.util,struct
        spec=importlib.util.spec_from_file_location('mini_checker',ROOT/'kit/reader/out/export_check.py')
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        root=directory();base=root/'base';weights=root/'m100/full_weights';base.mkdir();weights.mkdir(parents=True)
        def tensor(p):
            h=json.dumps({'weight':dict(dtype='BF16',shape=[1],data_offsets=[0,2])}).encode()
            p.write_bytes(struct.pack('<Q',len(h))+h+b'00')
        tensor(base/'model.safetensors');tensor(weights/'model.safetensors')
        idx=weights/'model.safetensors.index.json';idx.write_text(json.dumps(dict(weight_map={'weight':'model.safetensors'})))
        manifest=weights/'full_weights.json';manifest.write_text(json.dumps(dict(schema='full-ft-export-v1',dtype='bfloat16',
            index=dict(name=idx.name,sha256=S.sha(idx)),tensor_count=1,
            files=[dict(name='model.safetensors',bytes=(weights/'model.safetensors').stat().st_size,
                        sha256=S.sha(weights/'model.safetensors'),tensors=1)])))
        artifact=weights.parent/'artifact.json';artifact.write_text(json.dumps(dict(schema='carrier-c1-artifact-v1',step=100,
            full_weights=dict(path=str(manifest),sha256=S.sha(manifest)))))
        self.assertEqual(checker.check_export(artifact,S.sha(artifact),base,100)['status'],'VERIFIED')
        (weights/'model.safetensors').write_bytes((weights/'model.safetensors').read_bytes()[:-2]+b'11')
        with self.assertRaisesRegex(ValueError,'Shard hash'):checker.check_export(artifact,S.sha(artifact),base,100)

    def test_pool_retains_write_test(self):
        root=directory();pool=root/'pool';token='a123456789'
        result=return_io.operate('test',pool,token)
        self.assertEqual(result['bytes'],4*1024**2)
        self.assertEqual(return_io.sha(pool/token/'.wtest'),result['sha256'])
        with self.assertRaises(FileExistsError):return_io.operate('test',pool,token)
        with patch.object(return_io,'POOL_LIMIT',1):
            with self.assertRaises(ValueError):return_io.operate('test',pool,'b123456789')

    def test_return_contains_items_and_summary(self):
        root=directory();(root/'ITEMS.jsonl').write_text('{}\n');(root/'SUMMARY.json').write_text('{}')
        self.assertIn('ITEMS.jsonl',A.members(root));self.assertIn('SUMMARY.json',A.members(root))
        self.assertEqual(R.GCS_ROOT,'gs://cmu-gpucloud-jjyeung/q8/ae71c903')

    def test_h100_check(self):
        env=dict(USER='x',SLURM_JOB_ID='123',CUDA_VISIBLE_DEVICES='0')
        def query(args,**kwargs):
            if args[0]=='pgrep':return NS(stdout='',returncode=1)
            return NS(stdout='0, GPU-123, NVIDIA H100 80GB HBM3, 0, 0\n' if 'index,uuid,name' in ' '.join(args) else '',returncode=0)
        with patch.dict(J.os.environ,env),patch.object(J.subprocess,'run',side_effect=query):
            self.assertEqual(J.card(True)['gpu_uuid'],'GPU-123')
        with patch.dict(J.os.environ,dict(env,CUDA_VISIBLE_DEVICES='0,1')),patch.object(J.subprocess,'run',side_effect=query):
            with self.assertRaises(ValueError):J.card(True)

    def test_stage_function_is_exact_reviewed_body(self):
        original=Path('/scratch/jjyeung/orch_n30/trin_read/build_t5/milestone.py').read_text()
        candidate=(ROOT/'kit/launcher/export_stage.py').read_text()
        def body(s):return ast.dump(next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='stage_export'),include_attributes=False)
        self.assertEqual(body(original),body(candidate))

    def test_ordered_cloud_stream_requires_whole_digest_before_stage(self):
        for corrupt in (False, True):
            root=directory();(root/'archives').mkdir();(root/'bootstrap').mkdir()
            chunks=[b'one',b'two',b'three',b'four'];body=b''.join(chunks)
            uri='gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m100.tar'
            receipt=root/'input.done'
            receipt.write_text(json.dumps(dict(object=uri,bytes=len(body),
                sha256='0'*64 if corrupt else hashlib.sha256(body).hexdigest())))
            config=dict(spec=dict(step=100,artifact={},models={}),assets=dict(gcloud_config='fixture'))
            observed=[]
            @contextmanager
            def stream(argv,env,log):
                observed.append(argv[-1]);yield io.BytesIO(chunks[len(observed)-1])
            def path(value):
                return receipt if str(value).startswith('/project/community/') else Path(value)
            # The fixed receipt path is composed with / after Path construction.
            fake_receipt_dir=root/'receipts';fake_receipt_dir.mkdir()
            (fake_receipt_dir/'gcs_359fcc3c_m100.done').write_bytes(receipt.read_bytes())
            def path(value):
                return fake_receipt_dir if str(value).startswith('/project/community/') else Path(value)
            with patch.object(E,'Path',side_effect=path),patch.object(S,'room'),\
                 patch.object(S,'process_stream',side_effect=stream),\
                 patch.object(E,'stage_export',return_value=dict(artifact_sha256='a'*64)) as stage:
                if corrupt:
                    with self.assertRaisesRegex(ValueError,'Whole archive'):E.fetch_and_stage(root,config)
                    stage.assert_not_called();self.assertFalse((root/'archives/export.tar').exists())
                else:
                    E.fetch_and_stage(root,config)
                    self.assertTrue(stage.call_args.args[0].full)
                    self.assertEqual((root/'archives/export.tar').read_bytes(),body)
                    self.assertEqual(config['spec']['artifact']['sha256'],'a'*64)
            self.assertEqual(observed,[uri+'.part%02d-of-04'%i for i in range(4)])


if __name__=='__main__':unittest.main()
