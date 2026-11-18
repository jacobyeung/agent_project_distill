"""Regression coverage for the review fixes, using only candidate code and local fixtures."""
import offline_guard
import ast
import base64
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import unittest
from unittest.mock import patch
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'kit/launcher'),str(ROOT/'kit/reader')]
import orchard_launcher as L
import x7 as X
import h1pair as P


def folder():
    path=ROOT/'evidence'/('fix1_'+uuid.uuid4().hex);path.mkdir(mode=0o700);return path


def row(family,i,score):
    return dict(family=family,id=str(i),room='room'+str(i%4),scene='room'+str(i%4),score=score,
                task_type='object_counting',step=200,budget=2048,scoring_basis='answer')


class Fix1(unittest.TestCase):
    def test_frame_loader_duplicates_exact_anchor_pixels_and_indices(self):
        import numpy as np
        sys.path.insert(0,str(ROOT/'kit/reader/evaluator'))
        import media
        tree=ast.parse((ROOT/'kit/reader/x7.py').read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='load_frames')
        task=dict(example_id='x',frame_refs=list(range(32)),source_frame_indices=list(range(0,96,3)),fps=24,total_num_frames=100)
        anchors=np.arange(32*2*3*3,dtype=np.uint8).reshape(32,2,3,3)
        scope=dict(by_id={'x':task},arrays_for=lambda refs:anchors,media=media)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<loader-test>','exec'),scope)
        arrays,audit=scope['load_frames'](task,'duplicate',None,None)
        self.assertEqual(len(arrays),64)
        np.testing.assert_array_equal(arrays[::2],anchors)
        np.testing.assert_array_equal(arrays[1::2],anchors)
        self.assertEqual(audit['metadata']['frames_indices'],media.frame_list(task['source_frame_indices'],24,100,'duplicate')[0])
        self.assertEqual(audit['pixel_sha256'],media.pixel_digest(arrays))
        with self.assertRaises(ValueError):scope['load_frames'](task,'spread',None,None)

    def test_harm_is_scoped_to_main_and_extra_only(self):
        for family in ('main','a7','r0dev','away','forward'):
            a=[row(family,i,1) for i in range(8)];b=[dict(r,score=0) for r in a]
            result=P.compare(a,b,200);label='r0dev' if family=='a7' else family
            item=result['families'][label]['object_counting']
            self.assertEqual(item['ci95_pp'],[-100,-100])
            self.assertEqual(item['harm'],label in ('main','r0dev'))
            self.assertEqual(item['f1_registered'],item['harm'])

    def test_cli_membership_refusal_has_nonzero_exit_and_clear_message(self):
        root=folder();a=root/'a.jsonl';b=root/'b.jsonl';out=root/'out.json'
        a.write_text(json.dumps(row('main',0,1))+'\n');b.write_text(json.dumps(row('main',1,1))+'\n')
        err=io.StringIO()
        with patch.object(sys,'argv',['h1pair','--d0',str(a),'--h1',str(b),'--step','200','--output',str(out)]),contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as result:P.main()
        self.assertNotEqual(result.exception.code,0);self.assertIn('Unequal (family, id) membership',err.getvalue())
        self.assertFalse(out.exists())
        with self.assertRaises(ValueError):P.compare([row('main',0,1)],[row('main',0,1),row('away',1,1)],200)

    def test_bootstrap_and_payload_keep_alias_and_key_on_trinity(self):
        dest=folder()/'prepared';cfg=L.prepare('a000000001',dest,200,families=['a7'])
        script=(dest/'BATCH.sh').read_text();self.assertNotIn('r0dev',script.lower())
        raw=base64.b64decode(re.search(r"^raw=base64\.b64decode\('([^']+)'",script,re.M)[1])
        def check(data):
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                for member in archive:
                    self.assertNotRegex(member.name.lower(),r'r0|scannet|revsi|distill|sft|h1|split')
                    body=archive.extractfile(member).read()
                    if member.name.endswith('.tar.gz'):check(body)
                    else:
                        self.assertNotIn(b'r0dev',body.lower())
                        for private in (b'ID_KEY.json',b'ID_MAP.json',b'FAMILY_ALIASES.json'):
                            self.assertNotIn(private,body)
                        if (ROOT/'evidence/ID_KEY.json').exists():
                            self.assertNotIn(json.loads((ROOT/'evidence/ID_KEY.json').read_text())['key_hex'].encode(),body)
        check(raw)
        self.assertEqual(cfg['families'],['a7']);L.validate_batch(script,cfg)

    def test_asset_modes_refuse_before_hash_or_extract(self):
        root=folder();p=root/'a';p.write_bytes(b'fixture');p.chmod(0o600)
        reg=dict(files={'a':dict(path=str(p),bytes=7,sha256='a'*64)})
        for directory_mode,file_mode,message in ((0o755,0o600,'directory'),(0o700,0o644,'files'),(0o700,0o700,'files')):
            root.chmod(directory_mode);p.chmod(file_mode)
            with patch.object(X,'sha',side_effect=AssertionError('Hash ran before mode refusal')):
                with self.assertRaisesRegex(ValueError,message):X.stage_assets(reg,folder())
        root.chmod(0o700);p.chmod(0o600)
        with patch.object(X,'sha',return_value='bad') as hashed:
            with self.assertRaisesRegex(ValueError,'bytes'):X.stage_assets(reg,folder())
        hashed.assert_called_once()

    def test_ids_use_persistent_key_and_distinct_domains(self):
        spec=importlib.util.spec_from_file_location('asset_builder',ROOT/'tools/build_assets.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        key=bytes.fromhex(json.loads((ROOT/'evidence/ID_KEY.json').read_text())['key_hex'])
        self.assertEqual(len(key),32)
        self.assertEqual((ROOT/'evidence/ID_KEY.json').stat().st_mode & 0o777,0o600)
        mapping=json.loads((ROOT/'evidence/ID_MAP.json').read_text())
        for line in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines():
            item=json.loads(line);old=mapping[item['id']];value=old['id']
            self.assertEqual(item['id'],builder.opaque(key,'item',value))
            self.assertEqual(item['room'],builder.opaque(key,'room',old['room']))
            self.assertNotEqual(item['id'],hashlib.sha256(value.encode()).hexdigest()[:24])
            for index,ref in zip(item['source_frame_indices'],item['frame_refs']):
                self.assertEqual(ref,item['room']+'/'+builder.opaque(key,'frame',old['room']+'/'+str(index))+'.png')
        self.assertNotEqual(builder.opaque(key,'room','x'),builder.opaque(key,'item','x'))
        self.assertNotEqual(builder.opaque(key,'room','x'),builder.opaque(bytes(32),'room','x'))

if __name__=='__main__':unittest.main()
