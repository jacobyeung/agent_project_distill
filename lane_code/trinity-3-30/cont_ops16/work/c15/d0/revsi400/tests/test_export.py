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


class ExportTests(unittest.TestCase):
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

    def test_offline_guard_blocks_real_commands_and_network(self):
        import socket
        for argv in (['gcloud','storage','cp','fake','gs://fake'],
                     ['/usr/bin/gcloud','version'],['ssh','fake'],['sbatch','fake']):
            with self.assertRaises(offline_guard.OfflineViolation):subprocess.run(argv)
        with self.assertRaises(offline_guard.OfflineViolation):
            subprocess.run('gcloud version',shell=True)
        with self.assertRaises(offline_guard.OfflineViolation):socket.socket()

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
            digest='0'*64 if corrupt else hashlib.sha256(body).hexdigest()
            receipt.write_text(f'q8/8865619b/359fcc3c_m100.tar {len(body)} {digest}\n')
            config=dict(spec=dict(step=100,artifact={},models={},package=str(J.SJ/'a0/p')),assets=dict(gcloud_config='fixture'))
            (J.physical(root,config['spec']['package'])/'launcher').mkdir(parents=True)
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
                    self.assertEqual((root/'archives/COMPLETE.done').read_bytes(),receipt.read_bytes())
                    self.assertEqual(json.loads((root/'archives/COMPLETE.json').read_text()),
                                     E.parse_done(receipt.read_bytes(),'359fcc3c',100))
            self.assertEqual(observed,[uri+'.part%02d-of-04'%i for i in range(4)])

    def test_wrong_done_refused_before_cloud_or_disk_reservation(self):
        root=directory();receipt=root/'gcs_359fcc3c_m100.done'
        receipt.write_text('q8/8865619b/469ddece_m100.tar 123 '+'a'*64+'\n')
        def path(value):
            return root if str(value).startswith('/project/community/') else Path(value)
        with patch.object(E,'Path',side_effect=path),patch.object(S,'room') as room,\
             patch.object(S,'process_stream') as stream:
            with self.assertRaisesRegex(ValueError,'identity'):
                E.fetch_and_stage(root,dict(spec=dict(step=100)))
        room.assert_not_called();stream.assert_not_called()
