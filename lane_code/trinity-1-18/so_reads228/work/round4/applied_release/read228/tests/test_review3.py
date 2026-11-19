"""Third-review regressions; stdlib-only so the entire suite also runs with -S."""
from contextlib import ExitStack
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
import shutil
from unittest.mock import patch

FIXTURE=Path(__file__).resolve().parents[1]
TARGET=Path(os.environ.get('READ228_REVIEW3_KIT',str(FIXTURE))).resolve()
sys.path.insert(0,str(TARGET))
import common228 as C
import runner228 as R
import namespace228 as N
import stage228 as S
sys.path.insert(0,str(FIXTURE/'tests'))
from test_stage2 import archive
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/round3/fixtures'))
WORK.mkdir(parents=True,exist_ok=True)
C.install_imports(TARGET/'A10b/src')

def directory():return Path(tempfile.mkdtemp(prefix='a',dir=str(WORK)))

def full_adapter(test,kit,work):
    root,cfg,inputs,export=C.deployment(kit/'A10b')
    cfg=dict(cfg);inputs=dict(inputs)
    logical=work/'logical';(logical/'d/q').mkdir(parents=True)
    (logical/'p').symlink_to(kit/'A10b/src',target_is_directory=True)
    cfg['logical']=str(logical)
    C.write(logical/'d/settings.json',{k:cfg[k] for k in
        ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')})
    out=work/'run'
    gpu=dict(uuid='GPU-0123456789abcdef',name='NVIDIA RTX 6000 Ada Generation',
             memory_used_mib=0,memory_total_mib=49140,processes=[])
    # The parent may be -S. Only the separate operator process has installed packages.
    def command(inputs,*args,**kw):
        return [sys.executable,'-I','-s','-B',str(FIXTURE/'tests/operator_cpu_fixture.py'),str(kit),*args]
    with ExitStack() as stack:
        for name,value in [('target_host',lambda:'trinity-2-28'),('deployment',lambda p:(root,cfg,inputs,export)),
            ('stage_check',lambda *a,**kw:dict(environment={},namespace=dict(bwrap={'fixture':True}))),
            ('snapshot',lambda c:gpu),('idle_gate',lambda *a,**kw:gpu),('operator_command',command),('STAGE',work/'stage')]:
            stack.enter_context(patch.object(R,name,value))
        result=R.run_one(types.SimpleNamespace(package=str(root),card='0',out=str(out),items=50,on=False))
    test.assertEqual(result,0,(out/'ret/logs/1.log').read_text())
    summary=C.read(out/'ret/SUMMARY.json')
    test.assertEqual(summary['completed'],50);test.assertEqual(summary['expected'],636)
    for name in ('IDENTITY.json','projection.json'):
        test.assertTrue((out/'ret/metadata/reads/0/metadata'/name).is_file())
    command=C.read(out/'metadata/COMMAND.json')
    test.assertEqual(command['argv'][:5],['nice','-n','10','bash',inputs['policy']['vnice']])
    test.assertNotIn('/usr/bin/bwrap',command['argv'])
    test.assertTrue(command['start_new_session']);test.assertTrue(command['inherited_namespace'])
    args=C.read(out/'metadata/WORKER_ARGS.json')
    test.assertIn('--type-journals',args);test.assertEqual(args[args.index('--shard')+1],'0/1')
    test.assertEqual(C.read(out/'ret/metadata/LOCAL_RUN.json')['mode'],'OFF')
    return out

class Review3Tests(unittest.TestCase):
    def test_high1_native_parent_without_site_packages_runs_separate_operator(self):
        self.assertTrue((TARGET/'operator228.py').is_file(),'missing package operator entry')
        full_adapter(self,TARGET,directory())
        if sys.flags.no_site:
            self.assertNotIn('numpy',sys.modules);self.assertNotIn('torch',sys.modules)

    def test_high1_no_numpy_probe_refuses_before_any_card_or_run_directory(self):
        self.assertTrue(callable(getattr(R,'probe_operator',None)),'missing pre-gate operator probe')
        root=directory();out=root/'run'
        cfg=dict(logical=str(TARGET/'A10b'))
        inputs=dict(python=sys.executable)
        command=[sys.executable,'-I','-S','-B',str(TARGET/'operator228.py'),'--probe',str(TARGET/'A10b/src')]
        seen=[];real=subprocess.run
        def launch(argv,**kw):
            if '--probe' in argv:seen.append(list(argv))
            return real(argv,**kw)
        with ExitStack() as stack:
            for name,value in [('target_host',lambda:None),('deployment',lambda p:(TARGET/'A10b',cfg,inputs,{})),
                               ('stage_check',lambda *a,**k:{}),('operator_command',lambda *a,**k:command),('STAGE',root/'stage')]:
                stack.enter_context(patch.object(R,name,value))
            stack.enter_context(patch.object(R.subprocess,'run',side_effect=launch))
            snapshot=stack.enter_context(patch.object(R,'snapshot'))
            gate=stack.enter_context(patch.object(R,'idle_gate'))
            with self.assertRaisesRegex(C.Refusal,'Operator import probe failed') as caught:
                R.run_one(types.SimpleNamespace(package='unused',card='0',out=str(out),items=50,on=False))
            self.assertIn('numpy',str(caught.exception))
            snapshot.assert_not_called();gate.assert_not_called()
        self.assertFalse(out.exists());self.assertFalse((root/'stage/locks').exists())
        self.assertEqual(seen,[command])
        proof=C.read(root/'stage/OPERATOR_PROBE.json')
        self.assertFalse(proof['passed']);self.assertEqual(proof['returncode'],2)

    def test_high1_probe_cli_returns_two_without_numpy(self):
        self.assertTrue((TARGET/'operator228.py').is_file(),'missing package operator entry')
        got=subprocess.run([sys.executable,'-I','-S','-B',str(TARGET/'operator228.py'),'--probe',
                            str(TARGET/'A10b/src')],capture_output=True,text=True)
        self.assertEqual(got.returncode,2,got.stderr)
        self.assertIn('numpy',got.stderr);self.assertIn('REFUSED',got.stderr)

    def test_high1_operator_and_probe_share_namespace_interpreter(self):
        self.assertTrue(callable(getattr(N,'operator_command',None)),'missing shared control path')
        inputs=C.read(TARGET/'A10b/package/a/1.json')
        with patch.object(N,'namespace_command',return_value=['/usr/bin/bwrap','--fixture']):
            a=N.operator_command(inputs,'--probe','/logical/p')
            out=directory();(out/'metadata').mkdir()
            b=N.operator_command(inputs,'--execute',str(out/'metadata/dispatch.json'))
        self.assertEqual(a[:2],b[:2])
        self.assertEqual(b[2:5],['--bind',str(out),str(out)])
        self.assertEqual(a[2:-2],b[5:-2])
        self.assertEqual(a[:5],['/usr/bin/bwrap','--fixture',inputs['python'],'-B','-I'])
        self.assertEqual(a[-3],str(TARGET/'operator228.py'))

    def test_high1_worker_uses_package_policy_without_nested_bwrap(self):
        self.assertTrue((TARGET/'operator228.py').is_file(),'missing namespace operator')
        op=C.load_module(TARGET/'operator228.py','review3_operator')
        inputs=C.read(TARGET/'A10b/package/a/1.json')
        self.assertTrue(callable(getattr(op,'worker_command',None)))
        argv=op.worker_command(inputs['python'],['bash',inputs['policy']['vnice']],Path('/run/worker.json'))
        self.assertEqual(argv[:5],['nice','-n','10','bash',inputs['policy']['vnice']])
        self.assertNotIn('/usr/bin/bwrap',argv);self.assertFalse(any('/data3/' in x for x in argv))

    def test_high1_native_controller_has_no_operator_or_framework_execution(self):
        text=(TARGET/'runner228.py').read_text()
        self.assertNotIn('operator.run(',text)
        self.assertNotIn('runner.run(',text)
        self.assertIn('probe_operator(',text)

    def test_high1_harness_runs_a_suite_without_site_packages(self):
        text=(TARGET/'tests/run_tests.sh').read_text()
        self.assertIn('-S',text);self.assertIn('test_review3.py',text)
        if sys.flags.no_site:
            self.assertIsNone(importlib.util.find_spec('numpy'))
            self.assertIsNone(importlib.util.find_spec('torch'))

    def test_low2_banned_name_refuses_before_stage(self):
        out=directory()/'h1trial'
        with patch.object(R,'target_host'),patch.object(R,'deployment',return_value=(None,{},None,None)),\
             patch.object(R,'stage_check',side_effect=AssertionError('stage reached')) as stage,\
             patch.object(R,'snapshot') as snapshot:
            with self.assertRaisesRegex(ValueError,'Non-opaque'):
                R.run_one(types.SimpleNamespace(package='unused',card='0',out=str(out),items=50,on=False))
            stage.assert_not_called();snapshot.assert_not_called()
        self.assertFalse(out.exists())

    def test_low2_coordinator_validates_name_before_work(self):
        text=(TARGET/'coordinator228.sh').read_text()
        self.assertLess(text.index('unsafe ingest directory name'),text.index('source "$kit_dir/control_environment228.sh"'))
        self.assertLess(text.index('unsafe ingest directory name'),text.index('--verify-runtime-pins'))

    def test_low3_report_pushes_with_timeout_and_reuses_master(self):
        # The delivery report embeds COORDINATOR.md. The additive patch ships the
        # recipe directly; generated validation reports are outside that patch.
        path=TARGET/'REPORT.md'
        text=(path if path.is_file() else TARGET/'COORDINATOR.md').read_text()
        self.assertIn('timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib',text)
        self.assertIn('tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - .',text)
        self.assertNotIn('ControlPath=',text)
        self.assertIn('test ! -e',text)

    def test_info4_plan_stages_private_logical_root(self):
        plan=C.read(TARGET/'STAGE_PLAN.json')
        self.assertIn('private_logical',plan)
        private=Path(plan['private_logical']);logical=Path(plan['logical'])
        self.assertTrue(C.beneath(private,plan['stage_root']));self.assertNotEqual(private,logical)
        for g in plan['input_archives']:self.assertEqual(Path(g['destination']),private/'d')
        self.assertEqual(Path(plan['code']['destination']),private/'p')
        for g in plan['runtime_archives']:
            self.assertNotIn('sj/'+logical.name,g['namespace_map'])
            self.assertEqual(Path(g['destination']),Path(plan['private_runtime']))

    def test_info4_host_translation_never_reads_other_lane(self):
        root=directory();logical=root/'shared';private=root/'private'
        (logical/'d/s').mkdir(parents=True);(private/'d/s').mkdir(parents=True)
        (logical/'d/s/item').write_text('other lane');(private/'d/s/item').write_text('pinned')
        plan=dict(logical=str(logical),private_logical=str(private),stage_root=str(root/'stage'),
                  environment=dict(local_base_python=str(root/'uv/bin/python3.12')))
        path=N.host_path(logical/'d/s/item',plan)
        self.assertEqual(path,private/'d/s/item');self.assertEqual(path.read_text(),'pinned')
        self.assertEqual((logical/'d/s/item').read_text(),'other lane')

    def test_info4_namespace_overlays_private_root_after_sj_bind(self):
        root=directory();runtime=root/'private_rt';(runtime/'sj').mkdir(parents=True)
        private=root/'private';private.mkdir()
        plan=dict(stage_root=str(root),logical='/scratch/jjyeung/b01ec87a6f29b',private_logical=str(private))
        argv=N.namespace_command(plan)
        overlay=['--bind',str(private),plan['logical']]
        self.assertEqual(argv[-3:],overlay)
        self.assertLess(argv.index(str(runtime/'sj')),len(argv)-3)

    def test_info4_real_namespace_reads_private_bytes_and_preserves_shared_bytes(self):
        root=directory();runtime=root/'private_rt';(runtime/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu').mkdir(parents=True)
        for n in ('prepare','operator_probe','namespace_probe'):(root/n).mkdir()
        (runtime/'fsw').mkdir();(runtime/'m/ap').mkdir(parents=True)
        logical=root/'shared';private=root/'private'
        for path,value in ((logical,'other lane'),(private,'pinned archive')):
            (path/'d/s').mkdir(parents=True);(path/'d/s/item').write_text(value)
        plan=dict(stage_root=str(root),logical=str(logical),private_logical=str(private))
        command=N.namespace_command(plan)+['/usr/bin/python3','-I','-S','-B','-c',
            'from pathlib import Path; print(Path('+repr(str(logical/'d/s/item'))+').read_text())']
        result=subprocess.run(command,capture_output=True,text=True,timeout=30,env=C.clean_environment(root/'control'))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'pinned archive')
        self.assertEqual((logical/'d/s/item').read_text(),'other lane')

    def test_info4_stage_verifies_private_files_without_opening_shared_root(self):
        root=directory();logical=root/'shared';private=root/'private';data=private/'d';data.mkdir(parents=True)
        (logical/'d/s').mkdir(parents=True);(logical/'d/s/extra.py').write_text('other lane')
        cfg=dict(logical=str(logical),plan_sha256='fixture',stage1_select_rule='candidates_argmax',
            perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
        for name in ('frames','source','e','v','q'):(data/name).mkdir()
        (data/'v/py').write_text('#!/bin/sh\nexit 0\n');(data/'v/py').chmod(0o755)
        (data/'weights').mkdir();(data/'weights/x').write_bytes(b'x')
        C.write(data/'weights/full_weights.json',dict(files=[],index=dict(name='x',bytes=1,sha256=C.sha(data/'weights/x'))))
        C.write(data/'q/env.json',dict(versions={}))
        for name in ('vnice','terminator'):
            (data/'q'/(name+'.sh')).write_bytes((TARGET/'evidence/q'/(name+'.sh')).read_bytes())
        files={name:dict(path=str(logical/'d'/rel),bytes=(data/rel).stat().st_size,sha256=C.sha(data/rel))
               for name,rel in [('full_weights','weights/full_weights.json'),('env','q/env.json')]}
        inputs=dict(files=files,frames_root=str(logical/'d/frames'),sam_source=str(logical/'d/source'),
            python=str(logical/'d/v/py'),env_roots=[str(logical/'d/v/site')],
            policy={name:str(logical/'d/q'/(name+'.sh')) for name in ('vnice','terminator')})
        export=dict(step=400,preparation={})
        for name in ('e/RESTORE.json','binding.json','manifest.json'):C.write(data/name,{'fixture':True})
        C.write(data/'6.json',export)
        C.write(data/'settings.json',{**{k:cfg[k] for k in ('stage1_select_rule','perception_memo',
            'perception_memo_modules','perception_memo_verify_ids','save_own_depth')},'env_roots':inputs['env_roots']})
        C.write(data/'READY.json',dict(settings=C.sha(data/'settings.json'),binding=C.sha(data/'binding.json'),restore=C.sha(data/'e/RESTORE.json')))
        plan=dict(logical=str(logical),private_logical=str(private),stage_root=str(root/'stage'),environment={},
            input_archives=[dict(destination=str(data))],runtime_archives=[],
            budget=dict(free_floor_bytes=0,limit_bytes=150000000000,code_returns_cache_allowance_bytes=5000000000))
        inventory={str(p):dict(bytes=p.stat().st_size,sha256=C.sha(p)) for p in data.rglob('*') if p.is_file()}
        real_read=S.read;real_open=Path.open;opened=[]
        def read(path):return plan if Path(path).name=='STAGE_PLAN.json' else real_read(path)
        def open(path,*args,**kw):
            self.assertFalse(C.beneath(path,logical),'stage read another lane: '+str(path))
            opened.append(str(path));return real_open(path,*args,**kw)
        with patch.object(S,'read',side_effect=read),patch.object(S,'STAGE',root/'stage'),\
             patch.object(S,'staging_receipts',return_value=dict(files=inventory,runtime_members={},namespace={})),\
             patch.object(S,'source_check'),patch.object(S,'runtime_requirements',return_value={}),\
             patch.object(Path,'open',open):
            proof=S.stage_check(root,cfg,inputs,export,prepare=False,check_env=False)
        self.assertTrue(proof['passed']);self.assertIn(str(data/'weights/x'),opened)
        self.assertIn(str(data/'q/vnice.sh'),opened);self.assertIn(str(data/'q/terminator.sh'),opened)
        self.assertEqual(proof['inventory_check']['checked_roots'],[str(data)])

    def test_info4_code_install_uses_private_root(self):
        root=directory();logical=root/'shared';private=root/'private'
        plan=dict(stage_root=str(root/'stage'),logical=str(logical),private_logical=str(private),environment={})
        real=S.read
        def read(path):return plan if Path(path).name=='STAGE_PLAN.json' else real(path)
        with patch.object(S,'read',side_effect=read):
            S.code_install(TARGET/'A10b',dict(logical=str(logical)))
        self.assertTrue((private/'p/orchard_h10/entry.py').is_file())
        self.assertFalse(logical.exists())

    def test_info5_extraction_logs_stay_under_stage(self):
        root=directory();group,mapping=archive(root,[('s/a.py',b'pinned','file')]);stage=root/'stage'
        with patch.object(S,'STAGE',stage):S.extract_group(group,mapping,root/'private/d')
        logs=list((stage/'extraction_logs').glob('*.log'))
        self.assertEqual(len(logs),1)
        self.assertFalse((root/'private/read228_extraction_logs').exists())

    def test_info6_policy_has_no_data3_dependency(self):
        self.assertEqual(str(C.VNICE),'/scratch/jjyeung/b01ec87a6f29b/d/q/vnice.sh')
        inputs=C.read(TARGET/'A10b/package/a/1.json')
        self.assertEqual(str(C.VNICE),inputs['policy']['vnice'])
        checked=[];real=C.checked
        def check(path,spec):checked.append(str(path));return real(path,spec)
        with patch.object(C,'checked',side_effect=check):C.deployment(TARGET/'A10b')
        self.assertFalse(any('/data3/' in p for p in checked))
        self.assertIn(str(TARGET/'evidence/q/vnice.sh'),checked)

    def test_info8_readme_requires_fresh_name_after_directory_exists(self):
        text=(TARGET/'README.md').read_text()
        self.assertIn('Any refusal after the run directory exists needs a fresh run name.',text)

if __name__=='__main__':unittest.main(verbosity=2)
