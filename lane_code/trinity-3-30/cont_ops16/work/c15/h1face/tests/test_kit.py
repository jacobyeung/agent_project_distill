import offline_guard
import ast
import base64
import importlib.util
from contextlib import contextmanager
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import re
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
import binding as B
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
        for step,camera in [(100,False),(200,False)]:
            dest=directory()/'prepared';token='a'+uuid.uuid4().hex[:12]
            cfg=L.prepare(token,dest,step,camera,run='359fcc3c')
            L.validate_request(cfg);L.validate_batch((dest/'BATCH.sh').read_text(),cfg)
            self.assertEqual(cfg['families'],['main','away','forward','a7'])
            args=L.submit_argv(None,token)
            self.assertIn('--partition=general',args);self.assertIn('--gres=gpu:1',args)
            self.assertIn('--job-name=a15_cot_ap'+token,args)
            self.assertNotIn('sbatch',L.submit_command(token)[:1])
            for word in ('revsi','vsi','distill','qgen','split'):
                self.assertNotIn(word,' '.join(args).lower())
            broken=copy.deepcopy(cfg);broken['families']=['main']
            with self.assertRaises(ValueError):L.validate_request(broken)
            with self.assertRaises(FileExistsError):L.prepare(token,dest,step,camera,run='359fcc3c')
        for step,camera in [(s,False) for s in (400,600,800,1000)]+[(100,True)]:
            with self.assertRaises(ValueError):L.prepare('a000000001',directory()/'x',step,camera,run='359fcc3c')

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

    def test_return_retains_all_raw_journals(self):
        root=directory();source=root/'source';source.mkdir();output=root/'out';output.mkdir()
        expected={}
        for family in ('main','away','forward','camera'):
            for rel in ('0','budget_2048/0','budget_4096/0'):
                name=family+'/a0/results/'+rel+'/items_a0.jsonl'
                raw=(json.dumps(dict(response_text='raw generation '+name))+'\n').encode()
                path=source/name;path.parent.mkdir(parents=True);path.write_bytes(raw)
                expected[name]=raw
        with patch.object(A.shutil,'disk_usage',return_value=NS(free=10**12)):
            saved=A.save(source,output,0)
        with tarfile.open(saved['path']) as archive:
            self.assertEqual({m.name:archive.extractfile(m).read() for m in archive},expected)
        self.assertLess(saved['bytes'],A.ARCHIVE_LIMIT)

    def test_prepared_bootstrap_entry(self):
        for step in (100,200):
            root=directory();dest=root/'prepared'
            config=L.prepare('a'+uuid.uuid4().hex[:12],dest,step,run='359fcc3c')
            match=re.search(r"raw=base64.b64decode\('([^']+)'",(dest/'BATCH.sh').read_text())
            with tarfile.open(fileobj=io.BytesIO(base64.b64decode(match[1]))) as archive:
                for item in archive:
                    target=root/item.name;target.parent.mkdir(exist_ok=True)
                    target.write_bytes(archive.extractfile(item).read())
            spec=importlib.util.spec_from_file_location('packaged_job',root/'bootstrap/orchard_job.py')
            job=importlib.util.module_from_spec(spec);spec.loader.exec_module(job)
            argv=['orchard_job.py','--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')]
            with patch.object(sys,'argv',argv),patch.object(job,'run',return_value=0) as run,\
                 patch.object(R,'publish',side_effect=AssertionError('Unexpected publish')):
                with self.assertRaises(SystemExit) as exit:job.main()
                self.assertEqual(exit.exception.code,0)
                run.assert_called_once_with(str(root),config)
                # A modified packaged dependency must still fail before run().
                (root/'bootstrap/chain_save.py').write_text('tampered')
                with self.assertRaisesRegex(ValueError,'dependency'):job.main()
                self.assertEqual(run.call_count,1)

    def test_offline_guard_blocks_real_commands_and_network(self):
        import socket
        for argv in (['gcloud','storage','cp','fake','gs://fake'],
                     ['/usr/bin/gcloud','version'],['ssh','fake'],['sbatch','fake']):
            with self.assertRaises(offline_guard.OfflineViolation):subprocess.run(argv)
        with self.assertRaises(offline_guard.OfflineViolation):
            subprocess.run('gcloud version',shell=True)
        with self.assertRaises(offline_guard.OfflineViolation):socket.socket()

    def test_failure_return_uses_mock_publisher(self):
        import trace_runtime
        root=directory()
        config=L.prepare('a'+uuid.uuid4().hex[:12],root/'prepared',100)
        with patch.object(R,'write_test',side_effect=ValueError('fixture pool refusal')),\
             patch.object(R,'publish',return_value=dict(status='COMPLETE')) as publish,\
             patch.object(J,'card',return_value={}),patch.object(J.signal,'signal'),\
             patch.object(trace_runtime,'snapshot'),patch.object(trace_runtime,'collect'):
            self.assertEqual(J.run(root,config),1)
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[4],1)
        self.assertTrue((root/'RETURN.json').is_file())

    def test_final_pins_match(self):
        pins=json.loads((ROOT/'evidence/FINAL_PINS.json').read_text())
        for name,digest in pins.items():
            with self.subTest(name=name):self.assertEqual(S.sha(ROOT/name),digest)

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
        original=(ROOT/'readk/kit/launcher/export_stage.py').read_text()
        candidate=(ROOT/'kit/launcher/export_stage.py').read_text()
        def body(s):return ast.dump(next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='stage_export'),include_attributes=False)
        candidate=candidate.replace("(args.run not in T.EXPORT_RUNS and (args.run, args.step) != ('469ddece', 544) and not B.r1_step(args.run, args.step))",
                                    'args.run not in T.EXPORT_RUNS')
        self.assertEqual(body(original),body(candidate))

    def test_ordered_cloud_stream_requires_whole_digest_before_stage(self):
        for corrupt in (False, True):
            root=directory();(root/'archives').mkdir();(root/'bootstrap').mkdir()
            chunks=[b'one',b'two',b'three',b'four'];body=b''.join(chunks)
            uri='gs://cmu-gpucloud-jjyeung/q8/8865619b/359fcc3c_m100.tar'
            receipt=root/'input.done'
            digest='0'*64 if corrupt else hashlib.sha256(body).hexdigest()
            receipt.write_text(f'q8/8865619b/359fcc3c_m100.tar {len(body)} {digest}\n')
            config=dict(spec=dict(step=100,export_binding=B.expected('359fcc3c',100),artifact={},models={}),assets=dict(gcloud_config='fixture'))
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
                return fake_receipt_dir/Path(value).name if str(value).startswith('/project/community/') else Path(value)
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
                    self.assertEqual((root/'archives/COMPLETE.done').read_bytes(),receipt.read_bytes())
                    self.assertEqual(json.loads((root/'archives/COMPLETE.json').read_text()),
                                     E.parse_done(receipt.read_bytes(),'359fcc3c',100))
            self.assertEqual(observed,[uri+'.part%02d-of-04'%i for i in range(4)])

    def test_done_sample_and_strict_identity(self):
        sample=next(line for line in (ROOT/'readk/evidence/DONE_SAMPLES.txt').read_bytes().splitlines()
                    if line.startswith(b'q8/'))
        with self.assertRaises(ValueError):E.parse_done(sample+b'\n','469ddece',1)
        retired_sample=sample
        sample=sample.replace(b'469ddece_m1.tar',b'359fcc3c_m100.tar')
        parsed=E.parse_done(sample+b'\n','359fcc3c',100)
        self.assertEqual(parsed['bytes'],21583032320)
        for step in (100,200):
            raw=f'q8/8865619b/359fcc3c_m{step}.tar 123 '.encode()+b'a'*64+b'\n'
            self.assertEqual(E.parse_done(raw,'359fcc3c',step)['bytes'],123)
            bad=[retired_sample,raw.replace(b'359fcc3c',b'469ddece'),raw.replace(b'q8/8865619b',b'q8/other'),
                 raw.replace(f'_m{step}'.encode(),b'_m544'),b'gs://cmu-gpucloud-jjyeung/'+raw,
                 raw.replace(b'.tar ',b'.tar.part00-of-04 '),raw.replace(b' 123 ',b' 0 '),
                 raw.replace(b' 123 ',b' -1 '),raw.replace(b' 123 ',b' 1.2 '),
                 raw.replace(b'a'*64,b'a'*63),raw.replace(b'a'*64,b'A'*64),
                 raw+b'\n',raw+b'extra',raw.replace(b' 123 ',b'\t123 '),
                 json.dumps(dict(object=parsed['object'],bytes=123,sha256='a'*64)).encode()]
            for value in bad:
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):E.parse_done(value,'359fcc3c',step)

    def test_wrong_done_refused_before_cloud_or_disk_reservation(self):
        root=directory();receipt=root/'gcs_359fcc3c_m100.done'
        receipt.write_text('q8/8865619b/469ddece_m100.tar 123 '+'a'*64+'\n')
        def path(value):
            return root/Path(value).name if str(value).startswith('/project/community/') else Path(value)
        with patch.object(E,'Path',side_effect=path),patch.object(S,'room') as room,\
             patch.object(S,'process_stream') as stream:
            with self.assertRaisesRegex(ValueError,'identity'):
                E.fetch_and_stage(root,dict(spec=dict(step=100,export_binding=B.expected('359fcc3c',100))))
        room.assert_not_called();stream.assert_not_called()


if __name__=='__main__':unittest.main()
