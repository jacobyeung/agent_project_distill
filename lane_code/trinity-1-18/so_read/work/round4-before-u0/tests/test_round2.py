"""Round-2 regressions. READ_ROUND2_BEFORE=1 selects the reviewed bytes."""
import copy
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import types
import unittest
import uuid
from unittest.mock import patch

import torch
torch.set_num_threads(8)
SRC=Path(__file__).resolve().parents[2]
L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
INPUT=Path(os.environ['READ_INPUT_SRC'])
BEFORE=os.environ.get('READ_ROUND2_BEFORE')=='1'
E=L/'work/round2-before/src/u0' if BEFORE else SRC/'u0'
KIT=L/'work/round2-before/kit' if BEFORE else L/'out/kit_parity50'
sys.path[:0]=[str(E),str(SRC),str(SRC/'b'),str(INPUT/'tree'),str(INPUT)]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def directory():
    root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex
    root.mkdir(parents=True);return root


def require(test,name):
    path=E/name;test.assertTrue(path.is_file(),'Missing implementation: '+name)
    return path


class Round2Tests(unittest.TestCase):
    def test_f1_actual_isolated_script_plain_and_opaque(self):
        # Execute the real loader as a script under -I. Tiny dependent modules
        # avoid model loading but retain a4's real top-level a8 import.
        loader=load('entry_definition',E/'a8.py')
        for opaque in (False,True):
            with self.subTest(opaque=opaque):
                root=directory();extension=root/'u0';extension.mkdir()
                for package in ('b/e2e_reader','h1eval','h1eval/h10'):
                    p=root/package;p.mkdir(parents=True,exist_ok=True);(p/'__init__.py').write_text('')
                (extension/'a8.py').write_bytes((E/'a8.py').read_bytes())
                (extension/'a9.py').write_bytes((E/'a9.py').read_bytes())
                for name,filename in loader.MODULES:
                    text=''
                    if filename=='a4.py':
                        text='def main(argv):\n from a8 import source_hash\n assert len(source_hash())==64\n return 0\n'
                    (extension/filename).write_text(text)
                command=[sys.executable,'-I','-s','-B',str(extension/'a8.py'),'--enable-extensions']
                if opaque:command+=['--opaque']
                result=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_f2_all_three_path_checks_accept_established_roots(self):
        boundary=load('path_boundary',E/'a9.py');root=directory()
        paths=['/scratch/jjyeung/ab0123456789/u1',
               '/project/community/jjyeung/okh7/a15_cot_apab0123456789/u2.json',
               '/project/community/jjyeung/ab0123456789/0.tgz']
        for path in paths:
            boundary.seal_settings({'asset':path},root/'u0')
            cfg=json.loads((E/'tests/u1.json').read_text())
            for key in ('journal_root','items','export','export_pin','artifact_manifest','reader_root','settings'):cfg[key]=path
            boundary.validate_config(cfg)
            self.assertTrue(boundary.OPAQUE_PATH.fullmatch(path))
        from orchard_h10.common import FORBIDDEN,opaque
        for word in FORBIDDEN:
            with self.assertRaises(ValueError):opaque(['/scratch/jjyeung/u0/'+word])
            self.assertFalse(boundary.OPAQUE_PATH.fullmatch('/scratch/jjyeung/u0/'+word))
        for path in ('/scratch/somebody/u0','/project/community/else/u0','/scratch/jjyeung/u0/../u1',
                     '/scratch/jjyeung/u0//u1','/scratch/jjyeung/u0/model.safetensors'):
            self.assertFalse(boundary.OPAQUE_PATH.fullmatch(path),path)

    def test_f3_approved_argv_budget_script_and_retry(self):
        module=load('array_policy',require(self,'a15.py'))
        cfg=json.loads((SRC/'u0/tests/u1.json').read_text())
        args=('ab0123456789',cfg,'/scratch/jjyeung/u0/u1','/scratch/jjyeung/u0/u2','/scratch/jjyeung/u0/u3')
        with self.assertRaisesRegex(ValueError,'OFF'):module.submission(*args)
        with self.assertRaisesRegex(ValueError,'owner approval'):module.submission(*args,enabled=True)
        cfg['policy']['approved']=True
        plan=module.submission(*args,enabled=True)
        for flag in ('--account=mt01','--export=NONE','--output=/dev/null','--error=/dev/null',
                     '--job-name=a15_cot_apab0123456789','--array=0-1%2','--requeue'):
            self.assertIn(flag,plan['argv'])
        from orchard_h10.common import opaque
        opaque(plan['argv']);opaque([plan['script']])
        cfg['attempt_seconds']=172800
        with self.assertRaisesRegex(ValueError,'budget'):module.submission(*args,enabled=True)
        # Execute only the shell control flow with local fake worker/scheduler
        # functions. No scheduler binary, job, or GPU is invoked.
        for code,restarts,expected,want_retry in ((0,0,0,False),(2,0,2,False),(75,0,0,True),(75,1,75,False)):
            text=plan['script'];lines=text.splitlines()
            lines=[f'(exit {code}) &' if line.startswith('nice ') else line for line in lines]
            text='\n'.join(lines).replace('set -euo pipefail',
                 'set -euo pipefail\nscontrol() { printf "retry:%s:%s\\n" "$1" "$2"; }')
            env=dict(os.environ,SLURM_RESTART_COUNT=str(restarts),SLURM_ARRAY_JOB_ID='123',SLURM_ARRAY_TASK_ID='1')
            result=subprocess.run(['bash'],input=text,text=True,env=env,capture_output=True)
            self.assertEqual(result.returncode,expected,result.stderr)
            self.assertEqual('retry:requeue:123_1' in result.stdout,want_retry)

    def test_f4_build_pins_on_overlay_and_off_package_bytes(self):
        builder=load('production_builder',require(self,'a12.py'))
        original=load('original_builder',INPUT/'orchard_h10/build.py')
        original.B=INPUT/'b';original.T=INPUT/'orchard_h10/vendor'
        inventory=original.sources();root=directory()
        for name,path in inventory.items():
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        for path in (SRC/'u0').rglob('*'):
            if path.is_file():
                dest=root/'u0'/path.relative_to(SRC/'u0');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        for implementation in (original,builder):
            implementation.K=root;implementation.B=root/'b';implementation.T=root/'orchard_h10/vendor'
        self.assertEqual(set(original.sources()),set(builder.sources()))
        on=builder.sources(True)
        self.assertIn('u0/a8.py',on)
        for name,alias in (('entry','a13'),('job','a16'),('runner','a17'),('prepare','a18')):
            self.assertEqual(on['orchard_h10/'+name+'.py'],root/'u0'/(alias+'.py'))
        original.build(root/'u1','ab0123456789')
        builder.build(root/'u2','ab0123456789')
        for name in ('0.tgz','0.json','CONFIG.json','BATCH.sh','PACKAGE.json'):
            self.assertEqual((root/'u1'/name).read_bytes(),(root/'u2'/name).read_bytes(),name)
        builder.build(root/'u3','ab0123456789',enable_extensions=True)
        with tarfile.open(root/'u3/0.tgz') as archive:
            cfg=json.load(archive.extractfile('9.json'))
            self.assertIs(cfg['read_extensions'],True)
            self.assertIs(cfg['read_scene_shards'],True)
            self.assertEqual(cfg['read_cache_bytes'],12*1024**3)
            for name,pin in cfg['payload_pins'].items():
                raw=archive.extractfile(name).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256'],name)
            self.assertIn('u0/a8.py',cfg['payload_pins'])
            self.assertEqual(archive.extractfile('orchard_h10/entry.py').read(),(E/'a13.py').read_bytes())

    def test_f4_scene_summary_and_existing_return_envelope(self):
        runner=load('production_runner',require(self,'a17.py'))
        from a8 import activate
        activate(enabled=True)
        fixtures=load('round2_journal_fixture',SRC/'u0/tests/test_read_journal.py')
        case=fixtures.RunnerTests();case.setUp()
        try:
            case.manifest['items'][0]['question_type']='camera_displacement'
            types_=['camera_displacement','camera_rotation']
            out=case.root/'production'
            cfg=dict(package=str(SRC),output=str(out),items=str(case.root/'items.json'),types=types_,
                     arms=['tower'],modes=['none'],read_extensions=True,read_scene_shards=True,read_atomic_journal=True)
            from orchard_h10.common import ORDER
            for kind in types_:
                for i in range(3):
                    args=case.args('unused',shard=f'{i}/3',scene=True)
                    args.out=str(out/'metadata/journals'/str(ORDER.index(kind))/str(i));args.types=kind
                    fixtures.launch.run(args,make_real=case.make_real)
            with patch('h1eval.items.load_manifest',return_value=case.manifest):
                summary=runner.summarize(cfg,['0','1','2'])
                self.assertTrue(summary['complete']);self.assertEqual(summary['completed'],5)
                receipt=runner.merge_return(cfg,['0','1','2'])
            self.assertEqual(receipt['items'],5)
            sys.path.insert(0,str(INPUT/'orchard_h10/vendor'))
            import chain_save
            self.assertIn(receipt['path'],chain_save.members(out))
            # Compare the canonical payload from the integrated return to one shard.
            args=case.args('single',scene=True);fixtures.launch.run(args,make_real=case.make_real)
            fixtures.merge(case.manifest,[args.out],case.root/'merged')
            self.assertEqual((out/receipt['path']).read_bytes(),(case.root/'merged/answer_trace_return.tgz').read_bytes())
        finally:case.doCleanups()

    def test_f4_dispatch_uses_extension_entry_only_when_enabled(self):
        entry=require(self,'a13.py')
        import a8
        from h1eval.h10 import launch
        root=directory();path=root/'0.json'
        saved_path=sys.path[:]
        try:
            for enabled in (False,True):
                path.write_text(json.dumps(dict(action=2,package=str(SRC),config={'read_extensions':enabled})))
                with patch.object(sys,'argv',[str(entry),str(path)]), \
                     patch('orchard_h10.common.install_process_guard') as guard, \
                     patch('orchard_h10.runner.worker_args',return_value=['--items','u0']), \
                     patch.object(a8,'activate') as activate, \
                     patch.object(a8,'main',return_value=17) as extended, \
                     patch.object(launch,'main',return_value=17) as ordinary:
                    with self.assertRaises(SystemExit) as exited:runpy.run_path(str(entry),run_name='__main__')
                    self.assertEqual(exited.exception.code,17);guard.assert_called_once()
                    if enabled:
                        activate.assert_called_once_with(enabled=True)
                        extended.assert_called_once_with(['--enable-extensions','--items','u0'])
                        ordinary.assert_not_called()
                    else:
                        activate.assert_not_called();extended.assert_not_called()
                        ordinary.assert_called_once_with(['--items','u0'])
        finally:sys.path[:]=saved_path

    def test_f5_sam_default_capacity_and_raw_mutation_safety(self):
        cache=load('round2_cache_safety',E/'a0.py')
        self.assertTrue(hasattr(cache,'cache_bytes'),'Missing SAM capacity policy')
        self.assertEqual(cache.cache_bytes({'read_sam_cache':'on'}),12*1024**3)
        self.assertEqual(cache.cache_bytes({}),4*1024**3)
        self.assertEqual(cache.cache_bytes({'read_sam_cache':'on','read_cache_bytes':1000000}),1000000)
        # Model the reservation of a 3 GiB payload without allocating it.
        value=object();payload=3*1024**3
        for cap,hits in ((4*1024**3,0),(cache.cache_bytes({'read_sam_cache':'on'}),1)):
            store=cache.ReadCache(cap)
            with patch.object(cache,'nbytes',side_effect=lambda v:payload if v is value else 128), \
                 patch.object(cache,'payload_bytes',return_value=payload), \
                 patch.object(cache,'snapshot',return_value=b'fixture'), \
                 patch.object(cache,'restore',return_value=value):
                store.call('sam_features','clip',lambda:value)
                store.call('sam_features','clip',lambda:value)
            self.assertEqual(store.stats['sam_features']['hits'],hits)
        model=torch.nn.Linear(2,2).eval().requires_grad_(False)
        before=cache.module_identity(model)
        stamp=(id(model.weight),model.weight.data_ptr(),model.weight._version)
        model.weight.data.add_(1)
        self.assertEqual(stamp,(id(model.weight),model.weight.data_ptr(),model.weight._version))
        self.assertNotEqual(before,cache.module_identity(model))

    def test_f6_nonatomic_deadline_counts_under_lock(self):
        from a8 import activate
        activate(enabled=True)
        from h1eval.h10 import launch
        root=directory();binding={'ids':['a'],'arms':['tower'],'modes':[{'name':'none'}]}
        (root/'environment.json').write_text(json.dumps({'binding':binding}))
        row={'id':'a','arm':'tower','mode':'none','complete':True}
        (root/'items.jsonl').write_text(json.dumps(row)+'\n')
        original=(root/'items.jsonl').read_bytes();reader=launch.read_records;checks=[]
        def checked(path):
            with (root/'writer.lock').open('a') as other:
                with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            checks.append(True);return reader(path)
        with patch.object(launch,'read_records',side_effect=checked):
            with self.assertRaises(launch.ReadDeadline) as raised:
                with launch.writer_guard(root,binding,atomic=False,expected=2):raise launch.ReadDeadline()
        self.assertEqual(raised.exception.progress,dict(completed=1,expected=2,stopped=True,initialized=True))
        self.assertTrue(checks);self.assertEqual((root/'items.jsonl').read_bytes(),original)
        self.assertFalse((root/'committed').exists())

    def test_f7_lock_wait_is_bounded_and_then_recovers(self):
        worker=load('array_lock',E/'a7.py');self.assertTrue(hasattr(worker,'acquire'),'Missing bounded lock wait')
        root=directory();clock=[0.];sleeps=[]
        def sleep(seconds):clock[0]+=seconds;sleeps.append(seconds)
        with (root/'lock').open('a') as holder,(root/'lock').open('a') as second:
            fcntl.flock(holder,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.assertFalse(worker.acquire(second,.5,clock=lambda:clock[0],sleep=sleep))
            self.assertAlmostEqual(clock[0],.5);self.assertGreater(len(sleeps),1)
            fcntl.flock(holder,fcntl.LOCK_UN)
            self.assertTrue(worker.acquire(second,.5,clock=lambda:clock[0],sleep=sleep))

    def test_f8_processor_bypass_is_counted(self):
        cache=load('round2_processor',E/'a0.py')
        class Processor:
            def to_dict(self):return {}
            def __call__(self,value):return value
        store=cache.ReadCache(1000000);proxy=cache.VideoProcessorCache(Processor(),store)
        value=object();self.assertIs(proxy(value),value);self.assertIs(proxy(value),value)
        self.assertEqual(store.stats.get('processor',{}).get('bypasses'),2)
        self.assertEqual(len(store.entries),0)

    def test_f9_roots_and_manifest_checked_before_any_arm(self):
        kit=load('root_check_kit',KIT/'run.py')
        self.assertTrue(hasattr(kit,'validate_roots'),'Missing independent root validation')
        root=directory();original=root/'u0';source=root/'u1';original.mkdir();(source/'u0').mkdir(parents=True)
        (source/'u0/a8.py').write_bytes(b'fixture')
        pins={'u0/a8.py':hashlib.sha256(b'fixture').hexdigest()}
        for target in (original,source):(target/'base.py').write_bytes(b'base')
        inventory={'base.py':hashlib.sha256(b'base').hexdigest()}
        base=dict(inventory=inventory,files=1,sha256=hashlib.sha256(json.dumps(sorted(inventory.items()),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
        (root/'BASE_PIN.json').write_text(json.dumps(base))
        (root/'EXTENSION_PINS.json').write_text(json.dumps(pins));kit.HERE=root
        cfg={'original_source_root':str(original),'source_root':str(source)}
        kit.validate_roots(cfg)
        with self.assertRaisesRegex(ValueError,'must differ'):kit.validate_roots(dict(cfg,original_source_root=str(source)))
        (source/'u0/a8.py').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'hash differs'):kit.validate_roots(cfg)
        (source/'u0/a9.py').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'inventory differs'):kit.validate_roots(cfg)

    def test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs(self):
        module=load('test_strength',E/'tests/test_round1.py')
        case=module.ReviewRegressions('test_f2_absent_hits_and_incomplete_trace_cannot_pass')
        with patch.object(module.checker,'compare',side_effect=ValueError('unrelated fixture failure')):
            result=unittest.TestResult();case.run(result)
        self.assertFalse(result.wasSuccessful(),'An unrelated ValueError was accepted')
        self.assertTrue(hasattr(module,'load_tests'),'Behavioural tests missing from round-1 suite')
        suite=module.load_tests(unittest.TestLoader(),unittest.TestSuite(),None)
        def names(suite):
            for test in suite:
                if isinstance(test,unittest.TestSuite):yield from names(test)
                else:yield test.id()
        self.assertTrue(any(name.endswith('test_deadline_recovery_keeps_writer_lock') for name in names(suite)))

    def test_f16_no_descriptive_environment_variable(self):
        source=(KIT/'run.py').read_text()
        self.assertTrue("os.environ['H10_SETTINGS']" not in source,'Descriptive settings environment remains')
        self.assertTrue("sys.argv.extend(['--settings',cfg['settings']])" in source,'Missing native-tree selection through in-process arguments')


if __name__=='__main__':unittest.main(verbosity=2)
