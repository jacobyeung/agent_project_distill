"""Fix4 target regressions. CPU-only; real tar headers, namespace and operator guard."""
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch

FIXTURE=Path(__file__).resolve().parents[1]
TARGET=Path(os.environ.get('READ228_FIX4_KIT',str(FIXTURE))).resolve()
sys.path.insert(0,str(TARGET))
import common228 as C
import runtime228 as R
import namespace228 as N
import stage228 as S
WORK=Path(os.environ.get('READ228_TEST_WORK',str(FIXTURE.parent/'fixtures')))
WORK.mkdir(parents=True,exist_ok=True)

def directory():return Path(tempfile.mkdtemp(prefix='a',dir=str(WORK)))

def archive(root,rows,ident='r0'):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as writer:
        for name,kind,body in rows:
            item=tarfile.TarInfo(name);item.mode=0o755
            if kind=='file':item.size=len(body);writer.addfile(item,io.BytesIO(body))
            else:
                item.type={'dir':tarfile.DIRTYPE,'link':tarfile.SYMTYPE,'hardlink':tarfile.LNKTYPE,
                           'fifo':tarfile.FIFOTYPE,'char':tarfile.CHRTYPE}[kind]
                if kind in ('link','hardlink'):item.linkname=body
                writer.addfile(item)
    path=root/(ident+'.tar');path.write_bytes(stream.getvalue())
    part=dict(path='/project/'+ident,bytes=path.stat().st_size,sha256=C.sha(path))
    return dict(id=ident,parts=[part],sha256=part['sha256'],namespace_map={'sj/test':str(root/'private_rt/sj/test')}),{part['path']:path}

def extract_all(groups,mapping):
    if hasattr(R,'extract_runtimes'):return R.extract_runtimes(groups,mapping,limit=1000000)
    # Exercise the old coordinator's sequential behavior for before/after evidence.
    for group in groups:R.extract_runtime(group,mapping,limit=1000000)

def fixture_plan(root):
    private=root/'private_rt';logical=root/'shared';own=root/'private_logical'
    for rel in ('sj/uv-python/cpython-3.12.13-linux-x86_64-gnu','fsw','m/ap'):
        (private/rel).mkdir(parents=True,exist_ok=True)
    for rel in ('prepare','operator_probe','namespace_probe'):(root/rel).mkdir()
    own.mkdir()
    return dict(stage_root=str(root),private_runtime=str(private),logical=str(logical),private_logical=str(own))

class TargetRefusalTests(unittest.TestCase):
    def test_private_runtime_plan_and_native_control(self):
        plan=C.read(TARGET/'STAGE_PLAN.json');root=Path(plan.get('private_runtime','/missing'))
        self.assertEqual(root,Path(plan['stage_root'])/'private_rt')
        for group in plan['runtime_archives']:
            self.assertEqual(Path(group['destination']),root)
            for name,dest in group['namespace_map'].items():self.assertEqual(Path(dest),root/name)
        self.assertEqual(Path(plan['environment']['control_python']),root/R.CPYTHON)
        self.assertEqual(plan['environment']['control_python'],plan['environment']['local_base_python'])
        for name in ('coordinator228.sh','run228.sh','read228.sh','compare228.sh'):
            self.assertIn(str(root/R.CPYTHON),(TARGET/name).read_text())

    def test_unknown_namespace_in_last_archive_writes_nothing(self):
        root=directory();groups=[];mapping={}
        for ident,rows in [('r0',[('sj/test/first','file',b'first')]),
                           ('r1',[('sj/test/second','file',b'second')]),
                           ('r2',[('unknown/late','file',b'late')])]:
            group,parts=archive(root,rows,ident);groups.append(group);mapping.update(parts)
        with self.assertRaises(C.Refusal):extract_all(groups,mapping)
        self.assertFalse((root/'private_rt').exists(),'preflight refusal created runtime files')

    def test_conflict_in_last_archive_preserves_existing_and_writes_nothing(self):
        root=directory();old=root/'private_rt/sj/test/old';old.parent.mkdir(parents=True);old.write_bytes(b'other')
        before=(old.stat().st_ino,old.stat().st_mtime_ns,old.read_bytes())
        a,m=archive(root,[('sj/test/new','file',b'new')],'r0')
        b,n=archive(root,[('sj/test/old','file',b'ours')],'r2');m.update(n)
        with self.assertRaises(C.Refusal):extract_all([a,b],m)
        self.assertEqual(before,(old.stat().st_ino,old.stat().st_mtime_ns,old.read_bytes()))
        self.assertFalse((old.parent/'new').exists())

    def test_unsafe_member_types_refuse_before_writing(self):
        for kind,body in [('fifo',''),('char',''),('hardlink','sj/test/new')]:
            with self.subTest(kind=kind):
                root=directory();group,m=archive(root,[('sj/test/new','file',b'new'),('sj/test/bad',kind,body)])
                with self.assertRaises(C.Refusal):extract_all([group],m)
                self.assertFalse((root/'private_rt').exists())

    def test_absolute_and_parent_paths_refuse_before_writing(self):
        for name in ('/absolute/file','sj/test/../escape'):
            root=directory();group,m=archive(root,[('sj/test/new','file',b'new'),(name,'file',b'bad')])
            with self.assertRaises(C.Refusal):extract_all([group],m)
            self.assertFalse((root/'private_rt').exists())

    def test_escaping_links_refuse_before_writing(self):
        for link in ('../../../../outside','/home/other/file'):
            root=directory();group,m=archive(root,[('sj/test/new','file',b'new'),('sj/test/link','link',link)])
            with self.assertRaises(C.Refusal):extract_all([group],m)
            self.assertFalse((root/'private_rt').exists())

    def test_parent_symlink_in_later_group_refuses_before_writing(self):
        root=directory();a,m=archive(root,[('sj/test/parent/child','file',b'new')],'r0')
        b,n=archive(root,[('sj/test/parent','link','elsewhere')],'r2');m.update(n)
        with self.assertRaises(C.Refusal):extract_all([a,b],m)
        self.assertFalse((root/'private_rt').exists())

    def test_late_pin_failure_writes_nothing(self):
        root=directory();a,m=archive(root,[('sj/test/first','file',b'first')],'r0')
        b,n=archive(root,[('sj/test/last','file',b'last')],'r2');m.update(n)
        b['parts'][0]['sha256']='0'*64
        with self.assertRaises(C.Refusal):extract_all([a,b],m)
        self.assertFalse((root/'private_rt').exists())

    def test_identical_rerun_preserves_inode_mode_mtime(self):
        self.assertTrue(callable(getattr(R,'extract_runtimes',None)))
        root=directory();g,m=archive(root,[('sj/test/file','file',b'pinned'),('sj/test/alias','link','file')])
        first=extract_all([g],m);path=root/'private_rt/sj/test/file';path.chmod(0o640)
        before=(path.stat().st_ino,path.stat().st_mode,path.stat().st_mtime_ns)
        second=extract_all([g],m)
        self.assertEqual(before,(path.stat().st_ino,path.stat().st_mode,path.stat().st_mtime_ns))
        self.assertEqual(first,second)

    def test_real_lists_zero_body_preflight_and_unknown_namespace(self):
        self.assertTrue(callable(getattr(R,'preflight_runtime',None)),'missing all-archive pass 1')
        import runtime_registry228 as G
        plan=C.read(TARGET/'STAGE_PLAN.json');G.validate_registry(plan)
        root=directory();groups=[];streams={};count=0
        for group in plan['runtime_archives']:
            rows=G.list_headers(TARGET/group['member_list']['path']);count+=len(rows)
            stream=io.BytesIO();zero=[]
            with tarfile.open(fileobj=stream,mode='w') as writer:
                for row in rows:
                    member=tarfile.TarInfo(row['name']);member.type=row['type'].encode();member.linkname=row['link']
                    member.size=0;writer.addfile(member)
                    zero.append(dict(row,bytes=0))
            raw=stream.getvalue();streams[group['id']]=raw
            groups.append(dict(id=group['id'],parts=[group['id']],sha256=hashlib.sha256(raw).hexdigest(),
                expanded_bytes=0,member_headers_sha256=C.canonical(zero),
                namespace_map={k:str(root/'private_rt'/k) for k in plan['runtime_registry']}))
        class Stream(io.BytesIO):
            def __init__(self,parts,mapping):super().__init__(streams[parts[0]]);self.digest=hashlib.sha256()
            def read(self,size):raw=super().read(size);self.digest.update(raw);return raw
        with patch.object(S,'PartStream',Stream):
            got=R.preflight_runtime(groups,{},limit=1)
            self.assertEqual(sum(len(g['members']) for g in got['groups'].values()),115837)
            self.assertFalse((root/'private_rt').exists())
            extra=io.BytesIO()
            with tarfile.open(fileobj=extra,mode='w') as writer:writer.addfile(tarfile.TarInfo('unregistered/file'))
            streams['extra']=extra.getvalue()
            groups.append(dict(id='extra',parts=['extra'],namespace_map=groups[0]['namespace_map']))
            with self.assertRaisesRegex(C.Refusal,'Unregistered runtime namespace'):
                R.preflight_runtime(groups,{},limit=1)
        self.assertFalse((root/'private_rt').exists())
        self.assertEqual(count,115837)

    def test_helper_records_are_not_runtime_binds(self):
        plan=C.read(TARGET/'STAGE_PLAN.json');registry=plan.get('runtime_registry',{})
        self.assertIn('x/pull.py',registry);self.assertIn('x/need_frames.txt',registry)
        for name in ('x/pull.py','x/need_frames.txt'):
            self.assertEqual(registry[name]['kind'],'record_only');self.assertIsNone(registry[name]['namespace_path'])
        self.assertIn('non_runtime_namespaces',(TARGET/'stage228.py').read_text())

    def test_real_namespace_private_runtime_logical_control_and_x_isolation(self):
        root=directory();plan=fixture_plan(root);private=Path(plan['private_runtime'])
        for rel,value in [('sj/orch_cd/legs1_reads/file','private runtime'),('m/ap/19252904/file','private ap'),('x/pull.py','never execute')]:
            path=private/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value)
        shared=Path(plan['logical']);shared.mkdir();(shared/'file').write_text('other lane')
        (Path(plan['private_logical'])/'file').write_text('private logical')
        try:argv=N.namespace_command(plan)
        except C.Refusal as error:self.fail(str(error))
        self.assertIn(str(private/'sj'),argv)
        self.assertNotIn(str(private/'x'),argv)
        code='''import json
from pathlib import Path
print(json.dumps([Path('/scratch/jjyeung/orch_cd/legs1_reads/file').read_text(),
Path(%r).read_text(),Path(%r).read_text(),Path(%r).exists(),Path(%r).exists(),Path(%r).is_file()]))
'''%(N.AP+'/19252904/file',str(shared/'file'),str(private/'x/pull.py'),'/x/pull.py',str(N.HERE/'operator228.py'))
        got=subprocess.run(argv+['/usr/bin/python3','-I','-S','-B','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           universal_newlines=True,timeout=30,env=C.clean_environment(root/'namespace_probe'))
        self.assertEqual(got.returncode,0,got.stderr)
        self.assertEqual(json.loads(got.stdout),['private runtime','private ap','private logical',False,False,True])
        self.assertEqual((shared/'file').read_text(),'other lane')

    def test_host_translation_private_sj_and_absolute_link(self):
        root=directory();plan=fixture_plan(root);private=Path(plan['private_runtime'])
        python=private/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12'
        python.parent.mkdir();python.write_bytes(b'private python')
        plan['environment']=dict(local_base_python=str(python))
        link=private/'sj/envs/p1cpu/bin/python3.12';link.parent.mkdir(parents=True)
        link.symlink_to('/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12')
        self.assertEqual(N.host_path('/scratch/jjyeung/envs/p1cpu/bin/python3.12',plan),python)
        self.assertEqual(N.host_path(N.UV+'/bin/python3.12',plan),python)

    def test_footprint_counts_private_root_without_following_shared_links(self):
        plan=C.read(TARGET/'STAGE_PLAN.json')
        self.assertIn('runtime_expanded_bytes',plan['budget'])
        self.assertEqual(plan['budget']['runtime_expanded_bytes'],10371055588)
        root=directory();private=root/'private_rt';private.mkdir();(private/'body').write_bytes(b'x'*23)
        (private/'link').symlink_to('/scratch/jjyeung/envs/p1cpu')
        got=S.local_bytes([private]);self.assertEqual(got['bytes'],23+len('/scratch/jjyeung/envs/p1cpu'))
        self.assertIn("roots.append(plan['private_runtime'])",(TARGET/'stage228.py').read_text())

    def test_coordinator_fresh_kit2_stage_then_single_gate(self):
        text=(TARGET/'coordinator228.sh').read_text()
        self.assertIn('/reads228/kit2',text);self.assertNotIn('/reads228/kit\"',text)
        self.assertIn('/private_rt/sj/uv-python/',text)
        self.assertLess(text.index('--extract-runtime'),text.index('--check-namespace'))
        self.assertEqual(text.count('bash "$kit_dir/run228.sh"'),1)

    def test_bootstrap_harness_selects_actual_python368(self):
        text=(TARGET/'tests/run_tests.sh').read_text()
        self.assertIn('bootstrap_python=/usr/bin/python3',text)
        self.assertIn('sys.version_info[:3] != (3,6,8)',text)
        self.assertIn('"$bootstrap_python" -I -s -B "$test_dir/test_bootstrap36.py"',text)

    def test_operator_installs_guard_before_policy_or_spawn(self):
        C.install_imports(TARGET/'A10b/src')
        import orchard_h10.common as sealed
        import orchard_h10
        fake_runner=types.ModuleType('orchard_h10.runner')
        operator=C.load_module(TARGET/'operator228.py','fix4_operator')
        out=directory();seen=[]
        class Stop(Exception):pass
        def guard(path):seen.append(Path(path));raise Stop()
        with patch.object(operator,'target_host'),patch.object(operator,'install_imports'),\
             patch.object(operator,'load_module'),patch.object(orchard_h10,'runner',fake_runner,create=True),\
             patch.dict(sys.modules,{'orchard_h10.runner':fake_runner}),patch.object(sealed,'install_process_guard',side_effect=guard),\
             patch.object(operator,'policy_check',side_effect=AssertionError('policy ran before guard')):
            with self.assertRaises(Stop):operator.execute(dict(out=str(out),config=dict(package=str(TARGET/'A10b/src'),prefix=['bash','fixture']),
                                                              card='GPU-fixture',end=1,operator='fixture'))
        self.assertEqual(seen,[out])

    def test_existing_symlink_target_cannot_escape_private_root(self):
        root=directory();alias=root/'private_rt/sj/test/external';alias.parent.mkdir(parents=True)
        alias.symlink_to('/tmp')
        g,m=archive(root,[('sj/test/new','file',b'new'),('sj/test/link','link','external/file')])
        with self.assertRaises(C.Refusal):extract_all([g],m)
        self.assertFalse((alias.parent/'new').exists())
        self.assertEqual(os.readlink(str(alias)),'/tmp')

    def test_symlink_cycle_refuses_before_writing(self):
        root=directory();g,m=archive(root,[('sj/test/new','file',b'new'),
            ('sj/test/a','link','b'),('sj/test/b','link','a')])
        with self.assertRaises(C.Refusal):extract_all([g],m)
        self.assertFalse((root/'private_rt').exists())

    def test_staging_helpers_extract_as_records_without_execution(self):
        plan=C.read(TARGET/'STAGE_PLAN.json')
        self.assertIn('x/pull.py',plan.get('runtime_registry',{}))
        root=directory();body=b'raise RuntimeError("must never execute")\n'
        g,m=archive(root,[('x/pull.py','file',body),('x/need_frames.txt','file',b'frames\n')])
        g['namespace_map']={n:str(root/'private_rt'/n) for n in plan['runtime_registry']}
        proof=extract_all([g],m)
        self.assertEqual((root/'private_rt/x/pull.py').read_bytes(),body)
        self.assertIn(str(root/'private_rt/x/need_frames.txt'),proof['files'])

    def test_stage_entry_refuses_late_unknown_before_runtime_writes(self):
        self.assertTrue(callable(getattr(R,'extract_runtimes',None)))
        import runtime_registry228 as G
        root=directory();groups=[];mapping={}
        for ident,rows in [('r0',[('sj/test/new','file',b'new')]),('r2',[('unknown/file','file',b'bad')])]:
            g,m=archive(root,rows,ident)
            for part in g['parts']:part['target']=str(m[part['path']])
            groups.append(g);mapping.update(m)
        plan=dict(runtime_archives=groups,input_archives=[],private_runtime=str(root/'private_rt'),
                  budget=dict(runtime_expanded_allowance_bytes=1000,free_floor_bytes=0))
        original=S.read
        def read(path):return plan if Path(path).name=='STAGE_PLAN.json' else original(path)
        with patch.object(S,'read',side_effect=read),patch.object(S,'target_host'),\
             patch.object(S,'deployment',return_value=(root,{},None,None)),patch.object(S,'verify_runtime_pins'),\
             patch.object(S,'STAGE',root),patch.object(G,'validate_registry',return_value={'passed':True}):
            with self.assertRaisesRegex(C.Refusal,'Unregistered runtime namespace'):S.main(['fixture','--extract-runtime'])
        self.assertFalse((root/'private_rt').exists())
        receipt=C.read(root/'STAGE_CHECK.json');self.assertFalse(receipt['passed'])
        self.assertEqual(receipt['phase'],'runtime_extraction')

if __name__=='__main__':unittest.main(verbosity=2)
