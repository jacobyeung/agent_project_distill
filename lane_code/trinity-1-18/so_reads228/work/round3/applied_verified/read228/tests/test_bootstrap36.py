"""Execute stdlib staging contracts with the target's Python 3.6.8 interface."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import common228 as C
import stage228 as S
import runtime228 as R
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/bootstrap36_tests'))
WORK.mkdir(parents=True,exist_ok=True)
S.STAGE=WORK/"stage"
def directory():return Path(tempfile.mkdtemp(prefix='a',dir=str(WORK)))
def archive(root,entries):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as tar:
        for name,value,kind in entries:
            item=tarfile.TarInfo(name);item.mode=0o755
            if kind=='link':item.type=tarfile.SYMTYPE;item.linkname=value;tar.addfile(item)
            else:item.size=len(value);tar.addfile(item,io.BytesIO(value))
    raw=buffer.getvalue();parts=[];mapping={}
    for i,data in enumerate((raw[:1024],raw[1024:])):
        target=root/('part'+str(i));target.write_bytes(data);source='/project/part'+str(i)
        parts.append(dict(path=source,bytes=len(data),sha256=C.sha(target)));mapping[source]=target
    return dict(parts=parts,sha256=hashlib.sha256(raw).hexdigest(),expanded_bytes=sum(len(v) for n,v,k in entries if k!='link')),mapping

class BootstrapTests(unittest.TestCase):
    def test_cli_imports_on_system_python(self):
        self.assertTrue(callable(S.main));self.assertTrue(callable(R.relocate_runtime))
        self.assertEqual(os.environ.get('CUDA_VISIBLE_DEVICES'),'')

    def test_input_archive_extracts_and_authenticates_on_python36(self):
        root=directory();group,mapping=archive(root,[('q/env.json',b'{"versions":{}}','file')])
        got=S.extract_group(group,mapping,root/'d')
        self.assertEqual((root/'d/q/env.json').read_bytes(),b'{"versions":{}}')
        self.assertEqual(got[str(root/'d/q/env.json')]['sha256'],C.sha(root/'d/q/env.json'))

    def test_runtime_maps_package_namespaces_and_absolute_python_link(self):
        root=directory();entries=[('sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',b'#!/bin/sh\nexit 0\n','file'),
            ('m/ap/19252904/e/bin/python',R.UV+'/bin/python3.12','link'),('m/ap/19252904/e/pyvenv.cfg',b'include-system-site-packages = false\n','file')]
        group,mapping=archive(root,entries)
        namespace={'sj':str(root/'scratch'),'m/ap':str(root/'runtime/m/ap'),'fsw':str(root/'runtime/fsw')}
        group['namespace_map']=namespace
        got=R.extract_runtime(group,mapping,limit=1024)
        link=root/'runtime/m/ap/19252904/e/bin/python'
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(str(link)),R.UV+'/bin/python3.12')
        self.assertEqual(got['archive_sha256'],group['sha256'])

    def test_runtime_rejects_external_symlink_and_unregistered_namespace(self):
        root=directory();group,mapping=archive(root,[('m/ap/escape','/home/other/secret','link')])
        group['namespace_map']={'m/ap':str(root/'runtime/m/ap')}
        with self.assertRaisesRegex(C.Refusal,'Unregistered absolute'):R.extract_runtime(group,mapping,limit=10)
        with self.assertRaisesRegex(C.Refusal,'Unregistered runtime namespace'):R.runtime_path('unknown/file',group['namespace_map'])

    def test_runtime_checks_last_part_hash_after_tar_end(self):
        root=directory();group,mapping=archive(root,[('sj/test',b'x','file')])
        group['namespace_map']={'sj':str(root/'scratch')};group['parts'][-1]['sha256']='0'*64
        with self.assertRaisesRegex(C.Refusal,'part pin'):R.extract_runtime(group,mapping,limit=10)

    def test_runtime_default_off_and_relocation_preserves_original_bytes(self):
        root=directory();stage=root/'stage';data=root/'logical/d';base=stage/'runtime/m/ap/19252904/e'
        plan=dict(stage_root=str(stage),logical=str(data.parent),environment=dict(local_base_env=str(base),
            local_base_python=str(root/'uv/bin/python3.12')))
        files={}
        for path,raw in [(data/'v/py',('#!/bin/sh\nexec '+R.AP+'/19252904/e/bin/python "$@"\n').encode()),
                         (data/'v/boot.py',b'print("overlay")\n'),(base/'pyvenv.cfg',('home = '+R.UV+'/bin\n').encode())]:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o755)
            files[str(path)]=dict(bytes=len(raw),sha256=C.sha(path))
        (base/'bin').mkdir();(base/'bin/python').write_bytes(b'python fixture')
        C.write(stage/'INPUT_EXTRACTION.json',dict(files=files));C.write(stage/'RUNTIME_EXTRACTION.json',dict(files={}))
        with self.assertRaisesRegex(C.Refusal,'OFF'):R.relocate_runtime(plan)
        with self.assertRaisesRegex(C.Refusal,'namespace'):R.relocate_runtime(plan,enabled=True)
        for path,spec in files.items():C.checked(path,spec)

    def test_no_runtime_fetch_or_implicit_fallback(self):
        plan=C.read(HERE/'STAGE_PLAN.json');missing=C.read(HERE/'MISSING.json')
        self.assertFalse(missing['fetch_allowed']);self.assertEqual(len(missing['files']),13)
        self.assertEqual(sum(p['bytes'] for p in missing['files']),10497433600)
        self.assertEqual(plan['environment']['control_python'],plan['environment']['local_base_python'])
        for p in missing['files']:
            self.assertEqual(p['host'],'orchard-login-001');self.assertEqual(len(p['sha256']),64)

if __name__=='__main__':unittest.main(verbosity=2)
