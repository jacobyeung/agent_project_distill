"""Finding regressions, runnable against either preserved round-0 code or this kit."""
from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import types
import unittest
from unittest.mock import patch

FIXTURE=Path(__file__).resolve().parents[1]
TARGET=Path(os.environ.get('READ228_REVIEW_KIT',str(FIXTURE))).resolve()
sys.path.insert(0,str(TARGET))
import torch
torch.set_num_threads(8)
import common228 as C
import compare228 as compare
import runner228 as runner
import stage228 as stage
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/review_tests'))
WORK.mkdir(parents=True,exist_ok=True)
C.install_imports(TARGET/"A10b/src")
REFERENCE=FIXTURE/'reference'
FIXED=C.read(FIXTURE/'FIRST50.json')

def directory():path=WORK/('a'+uuid.uuid4().hex);path.mkdir();return path
def candidate():
    root=directory()/'ret';shutil.copytree(str(REFERENCE),str(root))
    C.write(root/'SUMMARY.json',dict(completed=50,failure=None,complete=False))
    C.write(root/'metadata/LOCAL_RUN.json',dict(backend='trinity-local',host='trinity-2-28',mode='OFF',synthetic_cpu_fixture=True))
    C.write(root/'metadata/CARDS.json',dict(snapshot=dict(name='NVIDIA RTX 6000 Ada Generation')))
    C.write(root/'metadata/RETURN_ID.json',dict(job='234567',token='dc76460c3a164'+format(234567,'08x')))
    p=root/'metadata/reads/0/metadata/journals/3/0/environment.json'
    env=C.read(p);env['host']='trinity-2-28';C.write(p,env)
    return root
def result(root):return compare.compare(REFERENCE,root,first50=FIXED)
def change_json(path,fn):
    value=C.read(path);fn(value);C.write(path,value)
def env_path(root):return root/'metadata/reads/0/metadata/journals/3/0/environment.json'

class Findings(unittest.TestCase):
    def test_finding2_stage_plan_has_no_download_or_governor_actions(self):
        text=(TARGET/'STAGE_PLAN.json').read_text()
        self.assertNotIn('Orchard_IO_governor_stream',text)
        self.assertNotIn('register_command',text);self.assertNotIn('launch_command',text)

    def test_high1_environment_versions_are_resolved(self):
        expected=C.read(FIXTURE/'evidence/q/env.json')['versions']
        self.assertEqual(C.read(TARGET/'STAGE_PLAN.json')['environment']['versions'],expected)

    def test_high1_scratch_runtime_prefix_is_accepted(self):
        tmp=directory();prefix='/scratch/jjyeung/orch_n30/reads228/runtime/m/ap/19252904/e'
        env=dict(versions=C.read(FIXTURE/'evidence/q/env.json')['versions'],python=prefix+'/bin/python',cuda='13.0',
            prefix=prefix,base_prefix='/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu',python_version=[3,12,13],
            audit_roots=[prefix+'/lib/python3.12/site-packages'],module_paths={'torch':prefix+'/lib/python3.12/site-packages/torch/__init__.py'})
        fake=types.SimpleNamespace(returncode=0,stdout=json.dumps(env),stderr='')
        with patch.object(stage.subprocess,'run',return_value=fake):
            got=stage.versions(prefix+'/bin/python',dict(versions=env['versions']),{'TMPDIR':str(tmp)})
        self.assertEqual(got['versions'],env['versions'])

    def test_high1_prepare_precedes_gpu_gate(self):
        class Prepared(Exception):pass
        events=[]
        def prepare(*args,**kwargs):
            events.append('prepare');self.assertIs(kwargs.get('prepare'),True);raise Prepared()
        with patch.object(runner,'target_host'),patch.object(runner,'deployment',return_value=(None,{},None,None)),\
             patch.object(runner,'stage_check',side_effect=prepare),patch.object(runner,'snapshot') as gpu:
            with self.assertRaises(Prepared):
                runner.run_one(types.SimpleNamespace(package='unused',card='0',out=str(directory()/'run'),items=50,on=False))
            gpu.assert_not_called()
        self.assertEqual(events,['prepare'])

    def test_high3_one_ulp_stage1_drift_preserves_instrument(self):
        root=candidate();path=root/'metadata/reads/0/metadata/journals/3/0/items.jsonl'
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        record=next(r for row in rows for r in row['output']['calls']['records'] if isinstance(r.get('stage1',{}).get('sam3',{}).get('max_score'),float))
        old=record['stage1']['sam3']['max_score'];record['stage1']['sam3']['max_score']=math.nextafter(old,math.inf)
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        got=result(root)
        self.assertEqual(got['verdict'],'SAME_INSTRUMENT')
        self.assertEqual(got['identical']['call_placement'],50);self.assertEqual(got['identical']['trace'],49)
        self.assertTrue(any('stage1' in d['path'] for item in got['per_item'] for d in item['trace_diff']))

    def test_high4_orchard_against_orchard_is_ineligible(self):
        got=result(REFERENCE);self.assertFalse(got['eligible']);self.assertEqual(got['verdict'],'DIAGNOSTIC_ONLY')

    def test_high4_positive_local_provenance(self):
        got=result(candidate());self.assertTrue(got['eligible']);self.assertEqual(got['verdict'],'SAME_INSTRUMENT')

    def test_high4_local_host_is_mandatory(self):
        root=candidate();change_json(root/'metadata/LOCAL_RUN.json',lambda v:v.update(host='orchard-community-4'))
        self.assertFalse(result(root)['eligible'])

    def test_high4_ada_card_is_mandatory(self):
        root=candidate();change_json(root/'metadata/CARDS.json',lambda v:v.update(snapshot=dict(name='NVIDIA H100')))
        self.assertFalse(result(root)['eligible'])

    def test_high4_every_journal_host_is_mandatory(self):
        root=candidate();value=C.read(env_path(root));value['host']='orchard-community-4'
        C.write(root/'metadata/reads/0/metadata/journals/4/0/environment.json',value)
        self.assertFalse(result(root)['eligible'])

    def test_high4_orchard_job_cannot_be_reused(self):
        root=candidate();change_json(root/'metadata/RETURN_ID.json',lambda v:v.update(job=173060))
        self.assertFalse(result(root)['eligible'])

    def test_low6_worker_identity_and_all_caches_are_local(self):
        root=directory();env=C.clean_environment(root)
        self.assertEqual(env.get('USER'),'jjyeung');self.assertEqual(env.get('LOGNAME'),'jjyeung')
        for key in ('HOME','CUDA_CACHE_PATH','MPLCONFIGDIR'):
            self.assertIn(key,env);self.assertTrue(Path(env[key]).is_relative_to(root));self.assertTrue(Path(env[key]).is_dir())

    def test_low7_off_is_checked_in_settings(self):
        root=candidate();change_json(env_path(root),lambda v:v['settings'].update(read_processor_cache='on'))
        self.assertFalse(result(root)['eligible'])

    def test_low8_deployment_verifies_both_policy_scripts(self):
        root=TARGET/('A10b' if (TARGET/'A10b').exists() else 'A4');seen=[]
        original=C.checked
        def check(path,spec):
            seen.append(Path(path).name);return original(path,spec)
        with patch.object(C,'VNICE',FIXTURE/'evidence/q/vnice.sh'),\
             patch.object(C,'TERMINATOR',FIXTURE/'evidence/q/terminator.sh',create=True),patch.object(C,'checked',side_effect=check):
            C.deployment(root)
        self.assertIn('vnice.sh',seen);self.assertIn('terminator.sh',seen)

    def test_low9_compare_output_cannot_escape_scratch(self):
        with patch.object(compare,'compare',return_value=dict(verdict='SAME_INSTRUMENT')),patch.object(compare,'write') as write:
            with self.assertRaises(C.Refusal):compare.main([str(REFERENCE),'--out','/home/jjyeung/forbidden.json'])
            write.assert_not_called()

    def test_low9_original_unpack_acceptance_test_writes_under_work(self):
        # Intercept its child command before it can write to an unauthorized destination.
        spec=importlib.util.spec_from_file_location('reviewed_test_kit',TARGET/'tests/test_kit.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.WORK=directory()
        real_run=subprocess.run
        def child(argv,**kwargs):
            if '--out' in argv:
                dest=Path(argv[argv.index('--out')+1])
                self.assertTrue(dest.is_relative_to(module.WORK),'test output escaped work: '+str(dest))
            return real_run(argv,**kwargs)
        with patch.object(module.subprocess,'run',side_effect=child):
            test=module.ReturnTests('test_partial_return_accepted_by_original_a4_unpacker')
            outcome=unittest.TestResult();test.run(outcome)
        self.assertEqual(outcome.errors+outcome.failures,[])

class RunnerFindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(FIXTURE/'tests'))
        from test_review3 import full_adapter
        cls.out=full_adapter(unittest.TestCase(),FIXTURE,directory())
        cls.rc=C.read(cls.out/'RESULT.json')['returncode']
        cls.options=[C.read(cls.out/'metadata/COMMAND.json')]

    def test_medium5_orchard_metadata_members_are_present(self):
        self.assertEqual(self.rc,0)
        paths={row['path'] for row in C.read(FIXTURE/'ORCHARD_MEMBERS.json')['members']}
        required=['metadata/reads/0/metadata/IDENTITY.json','metadata/reads/0/metadata/projection.json',
                  'metadata/reads/0/metadata/a/30.json','metadata/ALLOCATION.json','metadata/STORAGE.json','logs/0.log','logs/1.log']
        for name in required:
            self.assertIn(name,paths);self.assertTrue((self.out/'ret'/name).is_file(),name)
        identity=C.read(self.out/'ret/metadata/reads/0/metadata/IDENTITY.json')
        # Compare semantic fields/schema against the authenticated Orchard identity.
        baseline=C.read(FIXTURE/'ORCHARD_METADATA.json')['read_identity']
        self.assertEqual(set(identity),set(baseline))
        for key in set(identity)-{'settings_sha256'}:self.assertEqual(identity[key],baseline[key],key)
        projection=C.read(self.out/'ret/metadata/reads/0/metadata/projection.json')
        self.assertEqual(set(projection),set(C.read(FIXTURE/'ORCHARD_METADATA.json')['projection']))
        self.assertEqual(projection['sample_reads'],50)

    def test_info11_worker_has_own_process_group(self):
        self.assertEqual(len(self.options),1);self.assertIs(self.options[0].get('start_new_session'),True)

if __name__=='__main__':unittest.main(verbosity=2)
