"""Preparation boundaries and handoff options using bounded CPU fixtures."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
import types
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import torch
torch.set_num_threads(8)
import common228 as C
import stage228 as S
import read228
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/prepare_tests'))
WORK.mkdir(parents=True,exist_ok=True)
def directory():path=WORK/('a'+uuid.uuid4().hex);path.mkdir();return path
def pinned(path,value):
    C.write(path,value);return dict(path=str(path),bytes=path.stat().st_size,sha256=C.sha(path))

class PrepareTests(unittest.TestCase):
    def test_prepare_creates_receipt_then_verifies_without_relaunch(self):
        root=directory();data=root/'logical/d';data.mkdir(parents=True);stage=root/'stage'
        (data/'frames').mkdir();(data/'source').mkdir()
        cfg=dict(logical=str(data.parent),plan_sha256='test',stage1_select_rule='candidates_argmax',
            perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False)
        shard=data/'weights/shard';shard.parent.mkdir();shard.write_bytes(b'x')
        spec=dict(name='shard',bytes=1,sha256=C.sha(shard))
        weights=pinned(data/'weights/full_weights.json',dict(files=[],index=spec))
        env=pinned(data/'q/env.json',dict(versions={'torch':'fixture'}))
        inputs=dict(files=dict(full_weights=weights,env=env),frames_root=str(data/'frames'),sam_source=str(data/'source'),
                    python=sys.executable,env_roots=[str(data/'v/site')],policy={})
        prep=pinned(data/'prep.json',dict(a=1));prep['path']='prep.json'
        export=dict(step=400,preparation=dict(config=prep))
        launches=[]
        def prepare(argv,**kwargs):
            launches.append(argv)
            self.assertIn('/usr/bin/bwrap',argv)
            dispatch=C.read(argv[-1]);self.assertEqual(dispatch['inputs']['_export'],export)
            self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'],'')
            (data/'e').mkdir()
            for name in ('e/RESTORE.json','binding.json','manifest.json'):C.write(data/name,dict(fixture=True))
            C.write(data/'6.json',export)
            C.write(data/'settings.json',{**{k:cfg[k] for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth')},'env_roots':inputs['env_roots']})
            C.write(data/'READY.json',dict(settings=C.sha(data/'settings.json'),binding=C.sha(data/'binding.json'),restore=C.sha(data/'e/RESTORE.json')))
            return types.SimpleNamespace(returncode=0)
        with ExitStack() as stack:
            for name,value in [('STAGE',stage),('source_check',lambda *a:None),('policy_check',lambda **kw:None),('staging_receipts',lambda *a:dict(fixture=True,files={},runtime_members={},namespace={'fixture':True})),
                               ('reconcile',lambda *a:dict(passed=True)),('runtime_requirements',lambda *a:dict(passed=True)),
                               ('record_prepare_products',lambda *a:None),('namespace_command',lambda *a:['/usr/bin/bwrap','--fixture']),
                               ('versions',lambda *a:dict(prefix=str(root),base_prefix=str(root),audit_coverage_verified=True)),
                               ('utc',lambda:'CPU_TEST')]:stack.enter_context(patch.object(S,name,value))
            stack.enter_context(patch.object(S.subprocess,'run',side_effect=prepare))
            stack.enter_context(patch.object(S.shutil,'disk_usage',return_value=types.SimpleNamespace(free=10**12)))
            first=S.stage_check(root,cfg,inputs,export,prepare=True)
            second=S.stage_check(root,cfg,inputs,export,prepare=True)
        self.assertTrue(first['passed']);self.assertTrue(second['passed']);self.assertEqual(len(launches),1)

    def test_incomplete_extraction_cannot_reach_preparation(self):
        root=directory()
        with patch.object(S,'STAGE',root):
            with self.assertRaisesRegex(C.Refusal,'Missing completed'):
                S.staging_receipts(C.read(HERE/'STAGE_PLAN.json'))
            C.write(root/'INPUT_EXTRACTION.json',dict(passed=False,files={}))
            with self.assertRaisesRegex(C.Refusal,'does not authenticate'):
                S.staging_receipts(C.read(HERE/'STAGE_PLAN.json'))

    def test_missing_runtime_and_wrong_hash_fail_before_control_imports(self):
        with patch.object(S,'target_host'),patch.object(S,'deployment',return_value=(None,{},None,None)):
            with self.assertRaisesRegex(C.Refusal,'MISSING.json'):
                S.main(['unused','--extract-runtime'])

    def test_deployment_rejects_modified_vnice_and_terminator(self):
        root=directory()
        for name in ('vnice','terminator'):
            p=root/(name+'.sh');p.write_bytes((HERE/'evidence/q'/p.name).read_bytes())
        with patch.object(C,'VNICE',root/'vnice.sh'),patch.object(C,'TERMINATOR',root/'terminator.sh'):
            C.policy_check()
            for name in ('vnice','terminator'):
                p=root/(name+'.sh');original=p.read_bytes();p.write_bytes(original[:-1]+b'x')
                with self.assertRaisesRegex(C.Refusal,'Wrong sha256'):C.policy_check()
                p.write_bytes(original)

    def test_read_handoff_defaults_to50_and_forwards_items(self):
        commands=[];root=directory()/'A10b'
        def launch(argv,**kwargs):commands.append(argv);return types.SimpleNamespace(returncode=2)
        with patch.object(read228,'target_host'),patch.object(read228,'package_root',return_value=root),\
             patch.object(read228.subprocess,'run',side_effect=launch):
            self.assertEqual(read228.main(['unused','0']),2)
            self.assertEqual(read228.main(['unused','0','--items','17']),2)
        self.assertEqual(commands[0][-2:],['--items','50']);self.assertEqual(commands[1][-2:],['--items','17'])

    def test_read_shell_accepts_items_without_using_missing_p1cpu_default(self):
        got=subprocess.run(['bash',str(HERE/'read228.sh'),str(HERE/'A10b'),'0','--items','50'],
            env=dict(os.environ,READ228_CONTROL_PYTHON=sys.executable,READ228_CONTROL_ROOT=str(WORK/"control")),capture_output=True,text=True)
        self.assertEqual(got.returncode,2);self.assertIn('restricted to trinity-2-28',got.stderr)
        for name in ('read228.sh','run228.sh','compare228.sh'):
            self.assertNotIn('/envs/p1cpu',(HERE/name).read_text())

    def test_runtime_probe_rejects_library_outside_audit_roots(self):
        root=directory();value=dict(versions={},cuda='13.0',python=sys.executable,python_version=[3,12,13],
            prefix=str(root),base_prefix=str(root),audit_roots=[str(root/'stdlib')],module_paths={'torch':str(root/'other/torch/__init__.py')})
        fake=types.SimpleNamespace(returncode=0,stdout=json.dumps(value),stderr='')
        with patch.object(S.subprocess,'run',return_value=fake):
            with self.assertRaisesRegex(C.Refusal,'audit roots'):
                S.versions(sys.executable,dict(versions={}),{'TMPDIR':str(root)})

if __name__=='__main__':unittest.main(verbosity=2)
