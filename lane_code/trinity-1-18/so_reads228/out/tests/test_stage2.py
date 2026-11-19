"""Second-review staging/namespace/ingest fixtures; no model or target-host access."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch

FIXTURE=Path(__file__).resolve().parents[1]
TARGET=Path(os.environ.get('READ228_REVIEW2_KIT',str(FIXTURE))).resolve()
sys.path.insert(0,str(TARGET))
import common228 as C
import stage228 as S
import runtime228 as R
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/round2/stage_fixtures'))
WORK.mkdir(parents=True,exist_ok=True)
S.STAGE=WORK/"stage"
def directory():return Path(tempfile.mkdtemp(prefix='s2_',dir=str(WORK)))
def archive(root,entries):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as writer:
        for name,raw,kind in entries:
            member=tarfile.TarInfo(name);member.mode=0o755
            if kind=='link':member.type=tarfile.SYMTYPE;member.linkname=raw;writer.addfile(member)
            else:member.size=len(raw);writer.addfile(member,io.BytesIO(raw))
    raw=stream.getvalue();parts=[];mapping={}
    for i,data in enumerate((raw[:1024],raw[1024:])):
        path=root/('part'+str(i));path.write_bytes(data);source='/project/part'+str(i)
        parts.append(dict(path=source,bytes=len(data),sha256=C.sha(path)));mapping[source]=path
    return dict(parts=parts,sha256=hashlib.sha256(raw).hexdigest(),expanded_bytes=sum(len(v) for n,v,k in entries if k!='link')),mapping

class StageFindings(unittest.TestCase):
    def test_medium3_conflicts_list_all_and_preserve_other_lane(self):
        root=directory();dest=root/'d';(dest/'s').mkdir(parents=True)
        paths=[dest/'s/a.py',dest/'s/b.py']
        for p in paths:p.write_bytes(b'other lane')
        before=[(p.stat().st_ino,p.read_bytes(),p.stat().st_mode) for p in paths]
        group,mapping=archive(root,[('s/a.py',b'archive A','file'),('s/b.py',b'archive B','file'),('s/new.py',b'new','file')])
        with self.assertRaises(C.Refusal) as caught:S.extract_group(group,mapping,dest)
        for p in paths:self.assertIn(str(p),str(caught.exception))
        self.assertEqual(before,[(p.stat().st_ino,p.read_bytes(),p.stat().st_mode) for p in paths])
        self.assertFalse((dest/'s/new.py').exists())

    def test_medium3_matching_member_is_skipped_without_metadata_change(self):
        root=directory();dest=root/'d';dest.mkdir();p=dest/'same';p.write_bytes(b'same');p.chmod(0o640)
        before=(p.stat().st_ino,p.stat().st_mtime_ns,p.stat().st_mode)
        group,mapping=archive(root,[('same',b'same','file'),('new',b'new','file')])
        commands=[];real=S.subprocess.Popen
        def launch(argv,**kwargs):commands.append(argv);return real(argv,**kwargs)
        with patch.object(S.subprocess,'Popen',side_effect=launch):got=S.extract_group(group,mapping,dest)
        self.assertEqual(before,(p.stat().st_ino,p.stat().st_mtime_ns,p.stat().st_mode))
        self.assertEqual(len(got),2);self.assertTrue(any('--skip-old-files' in c for c in commands))

    def test_medium3_unexplained_files_refuse_with_list(self):
        self.assertTrue(callable(getattr(S,'reconcile',None)),'stage lacks destination reconciliation')
        root=directory();data=root/'d';(data/'s').mkdir(parents=True);(data/'k').mkdir()
        known=data/'s/known.py';known.write_bytes(b'pinned')
        extras=[data/'s/stale.py',data/'k/other-lane.pt']
        for p in extras:p.write_bytes(b'other lane')
        files={str(known):dict(bytes=6,sha256=C.sha(known))}
        plan=dict(input_archives=[dict(destination=str(data))],runtime_archives=[])
        with patch.object(S,'STAGE',root/'stage'):
            with self.assertRaises(C.Refusal) as caught:S.reconcile(plan,dict(files=files,runtime_members={}),data)
        for p in extras:self.assertIn(str(p),str(caught.exception));self.assertEqual(p.read_bytes(),b'other lane')

    def test_medium3_stage_refuses_extras_before_import_or_prepare(self):
        root=directory();data=root/'logical/d';(data/'s').mkdir(parents=True)
        extra=data/'s/swarm_build.py';extra.write_bytes(b'other lane')
        plan=dict(input_archives=[dict(destination=str(data))],runtime_archives=[])
        real_read=S.read
        def read(path):return plan if Path(path).name=='STAGE_PLAN.json' else real_read(path)
        with patch.object(S,'STAGE',root/'stage'),patch.object(S,'read',side_effect=read),\
             patch.object(S,'staging_receipts',return_value=dict(files={},runtime_members={})),\
             patch.object(S,'versions') as probe:
            with self.assertRaises(C.Refusal) as caught:
                S.stage_check(root,dict(logical=str(data.parent)),{}, {},prepare=True)
            self.assertIn(str(extra),str(caught.exception));probe.assert_not_called()
        self.assertEqual(extra.read_bytes(),b'other lane');self.assertFalse((data/'e').exists())

    def test_high1_runtime_inventory_records_all_names(self):
        root=directory();group,mapping=archive(root,[('sj/runtime/one',b'x','file')]);group['namespace_map']={'sj':str(root/'scratch')}
        got=R.extract_runtime(group,mapping,limit=10)
        self.assertIn('members',got);self.assertEqual([r['name'] for r in got['members']],['sj/runtime/one'])

    def test_high1_runtime_members_must_supply_prepare(self):
        self.assertTrue(callable(getattr(S,'runtime_requirements',None)),'stage lacks runtime member requirements')
        root=directory();base=root/'base';py=root/'uv/bin/python3.12';overlay=root/'d/v'
        plan=dict(environment=dict(local_base_env=str(base),local_base_python=str(py),versions={'torch':'fixture'}))
        inputs=dict(python=str(overlay/'py'),env_roots=[str(overlay/'site')])
        with self.assertRaisesRegex(C.Refusal,'cannot supply sealed prepare'):S.runtime_requirements(plan,{},inputs)
        files={str(p):{} for p in (py,base/'bin/python',base/'pyvenv.cfg',overlay/'py',overlay/'boot.py',
                py.parents[1]/'lib/python3.12/encodings/__init__.py',overlay/'site/torch/__init__.py')}
        self.assertTrue(S.runtime_requirements(plan,files,inputs)['passed'])

    def test_medium4_runtime_absolute_link_bytes_preserved(self):
        self.assertEqual(R.runtime_path('sj',{'sj':'/scratch/jjyeung'}),Path('/scratch/jjyeung'))
        root=directory();raw=R.UV+'/bin/python3.12'
        group,mapping=archive(root,[('m/ap/19252904/e/bin/python',raw,'link')])
        group['namespace_map']={'m/ap':str(root/'runtime/m/ap'),'sj':str(root/'scratch')}
        got=R.extract_runtime(group,mapping,limit=10);p=root/'runtime/m/ap/19252904/e/bin/python'
        self.assertEqual(os.readlink(str(p)),raw);self.assertEqual(got['files'][str(p)]['link'],raw)

    def test_medium4_no_relocation_of_authenticated_bytes(self):
        root=directory();stage=root/'stage';data=root/'logical/d';base=stage/'runtime/m/ap/19252904/e'
        plan=dict(stage_root=str(stage),logical=str(data.parent),environment=dict(local_base_env=str(base),local_base_python=str(root/'uv/bin/python3.12')))
        files={}
        for path,raw in [(data/'v/py',('#!/bin/sh\nexec '+R.AP+'/19252904/e/bin/python "$@"\n').encode()),
                         (data/'v/boot.py',b'print("overlay")\n'),(base/'pyvenv.cfg',('home = '+R.UV+'/bin\n').encode())]:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            files[str(path)]=dict(bytes=len(raw),sha256=C.sha(path))
        (base/'bin').mkdir();(base/'bin/python').write_bytes(b'fixture')
        C.write(stage/'INPUT_EXTRACTION.json',dict(files=files));C.write(stage/'RUNTIME_EXTRACTION.json',dict(files={}))
        with self.assertRaises(C.Refusal):R.relocate_runtime(plan,enabled=True)
        for p,spec in files.items():C.checked(p,spec)

    def test_medium4_calls_sealed_namespace_and_records_both_bwrap_identities(self):
        self.assertTrue((TARGET/'namespace228.py').is_file(),'namespace adapter missing')
        import namespace228 as N
        root=directory();runtime=root/'runtime';runtime.mkdir();(runtime/'sj').symlink_to('/scratch/jjyeung',target_is_directory=True)
        plan=dict(stage_root=str(root));expected=N.package_namespace().namespace(runtime);expected[0]='/usr/bin/bwrap'
        self.assertEqual(N.namespace_command(plan),expected)
        fake=root/'bwrap';fake.write_bytes(b'root binary fixture')
        identity=types.SimpleNamespace(st_mode=0o100755,st_uid=0,st_size=fake.stat().st_size)
        real_stat=Path.stat
        def stat(path,*args,**kwargs):return identity if path==fake else real_stat(path,*args,**kwargs)
        with patch.object(N,'BWRAP',fake),patch.object(Path,'stat',stat),patch.object(N.os,'access',return_value=True),\
             patch.object(N.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='bubblewrap 0.4.0\n',stderr='')):
            value=N.bwrap_identity()
        self.assertEqual(value['executed']['sha256'],C.sha(fake));self.assertIn('sha256',value['package_pin'])
        self.assertNotEqual(value['executed']['sha256'],value['package_pin']['sha256'])

    def test_info10_ingest_uses_summary_despite_failed_exit_status(self):
        self.assertTrue((TARGET/'ingest228.py').is_file(),'ingest adapter missing')
        import ingest228 as I
        kit=directory();root=kit/'ingest/run';C.write(root/'SUMMARY.json',dict(completed=50,complete=False,failure=None))
        C.write(root/'EXIT.json',dict(status='FAILED'))
        with patch.object(I,'HERE',kit):
            got=I.ingest(root,dict(verdict='SAME_INSTRUMENT',eligible=True));self.assertEqual(got['status'],'READY_FOR_CORPUS')
            C.write(root/'FAILED.json',dict(error='fail'))
            self.assertEqual(I.ingest(root,dict(verdict='SAME_INSTRUMENT',eligible=True))['status'],'DIAGNOSTIC_ONLY')
            with self.assertRaises(C.Refusal):I.ingest(kit/'elsewhere',{})

    def test_namespace_probe_maps_preserved_absolute_python_link(self):
        self.assertTrue((TARGET/'namespace228.py').is_file())
        import namespace228 as N
        root=directory();python=root/'uv/bin/python3.12';python.parent.mkdir(parents=True);python.write_bytes(b'python')
        link=root/'runtime/m/ap/19252904/e/bin/python';link.parent.mkdir(parents=True);link.symlink_to(N.UV+'/bin/python3.12')
        plan=dict(stage_root=str(root),environment=dict(local_base_python=str(python)))
        self.assertEqual(N.host_path(N.AP+'/19252904/e/bin/python',plan),python)
        self.assertEqual(os.readlink(str(link)),N.UV+'/bin/python3.12')

    def test_stage_refusal_persists_runtime_member_list(self):
        root=directory();receipt=dict(groups={'r0':{'members':[{'name':'sj/runtime/file'}]}})
        C.write(root/'RUNTIME_EXTRACTION.json',receipt)
        # Both implementations refuse missing input extraction. The repaired stage
        # also retains the runtime list and refusal reason in STAGE_CHECK.json.
        with patch.object(S,'STAGE',root):
            with self.assertRaises(C.Refusal):
                S.stage_check(root,dict(logical=str(root/'logical')),{}, {},check_env=False)
        self.assertTrue((root/'STAGE_CHECK.json').is_file())
        got=C.read(root/'STAGE_CHECK.json');self.assertFalse(got['passed'])
        self.assertEqual(got['runtime_extraction'],receipt)

if __name__=='__main__':unittest.main(verbosity=2)
