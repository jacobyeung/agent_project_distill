"""Second-review regressions; READ228_REVIEW2_KIT selects preserved code."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

FIXTURE=Path(__file__).resolve().parents[1]
TARGET=Path(os.environ.get('READ228_REVIEW2_KIT',str(FIXTURE))).resolve()
sys.path.insert(0,str(TARGET))
import common228 as C
import compare228 as Q
import observe228 as O
import stage228 as S
WORK=Path(os.environ.get('READ228_TEST_WORK','/scratch/jjyeung/orch_n30/so_reads228/work/round2/fixtures'))
WORK.mkdir(parents=True,exist_ok=True)
REF=FIXTURE/'reference'
FIXED=C.read(FIXTURE/'FIRST50.json')
ENV='metadata/reads/0/metadata/journals/3/0/environment.json'
def directory():return Path(tempfile.mkdtemp(prefix='r2_',dir=str(WORK)))
def candidate():
    root=directory()/'ret';shutil.copytree(str(REF),str(root))
    C.write(root/'SUMMARY.json',dict(failure=None,completed=50,complete=False))
    C.write(root/'metadata/LOCAL_RUN.json',dict(backend='trinity-local',host='trinity-2-28',mode='OFF'))
    C.write(root/'metadata/CARDS.json',dict(snapshot=dict(name='NVIDIA RTX 6000 Ada Generation')))
    C.write(root/'metadata/RETURN_ID.json',dict(job='234567'))
    for p in (root/'metadata/reads').glob('*/metadata/journals/*/*/environment.json'):
        value=C.read(p);value['host']='trinity-2-28';C.write(p,value)
    return root
def change(path,fn):
    value=C.read(path);fn(value);C.write(path,value)
def result(root,left=REF):return Q.compare(left,root,first50=FIXED)

class ComparatorFindings(unittest.TestCase):
    def test_positive_control(self):self.assertEqual(result(candidate())['verdict'],'SAME_INSTRUMENT')

    def test_medium2_whole_binding(self):
        for key in ('settings_sha256','artifact_manifest_sha256','reader_entry','maker_name','device','arms','modes','r0_pin','schema','ids','count','new_key'):
            with self.subTest(key=key):
                root=candidate();change(root/ENV,lambda v:v['binding'].update({key:'CHANGED'}))
                got=result(root);self.assertFalse(got['eligible'])
                self.assertTrue(any('binding' in r and key in r for r in got['ineligibility_reasons']))

    def test_medium2_whole_settings(self):
        for key in ('arm','config','frames_root','new_key'):
            with self.subTest(key=key):
                root=candidate();change(root/ENV,lambda v:v['settings'].update({key:'CHANGED'}))
                got=result(root);self.assertFalse(got['eligible'])
                self.assertTrue(any('settings' in r and key in r for r in got['ineligibility_reasons']))

    def test_medium2_missing_keys(self):
        root=candidate();change(root/ENV,lambda v:v['settings'].pop('arm'))
        self.assertFalse(result(root)['eligible'])

    def test_low5_summary_failure(self):
        root=candidate();change(root/'SUMMARY.json',lambda v:v.update(failure='telemetry failed; run is diagnostic-only'))
        self.assertFalse(result(root)['eligible'])

    def test_low5_summary_completed(self):
        root=candidate();change(root/'SUMMARY.json',lambda v:v.update(completed=49))
        self.assertFalse(result(root)['eligible'])

    def test_low5_failed_marker(self):
        root=candidate();C.write(root/'FAILED.json',dict(error='failed'))
        self.assertFalse(result(root)['eligible'])

    def test_low5_missing_summary(self):
        root=candidate();(root/'SUMMARY.json').rename(root/'SUMMARY.saved')
        self.assertFalse(result(root)['eligible'])

    def test_low6_reference_identity_pin(self):
        left=directory()/'reference';shutil.copytree(str(REF),str(left));root=candidate()
        for side in (left,root):change(side/'metadata/IDENTITY.json',lambda v:v.update(inputs='CHANGED'))
        got=result(root,left);self.assertFalse(got['eligible'])
        self.assertTrue(any('reference pin' in r and 'IDENTITY.json' in r for r in got['ineligibility_reasons']))

    def test_low6_reference_environment_pin(self):
        left=directory()/'reference';shutil.copytree(str(REF),str(left));root=candidate()
        for side in (left,root):change(side/ENV,lambda v:v['settings'].update(arm='CHANGED'))
        got=result(root,left);self.assertFalse(got['eligible'])
        self.assertTrue(any('reference pin' in r and 'environment.json' in r for r in got['ineligibility_reasons']))

    def test_low6_first50_contains_all_reference_pins(self):
        pins=C.read(TARGET/'FIRST50.json').get('reference_sha256',{})
        wanted=['metadata/IDENTITY.json']+[str(p.relative_to(REF)) for p in REF.glob('metadata/reads/*/metadata/journals/*/*/environment.json')]
        self.assertEqual(set(pins),set(wanted))
        for name in wanted:self.assertEqual(pins[name],C.sha(REF/name))

class LaunchFindings(unittest.TestCase):
    def test_low7_no_settings_import_append(self):
        text=(TARGET/'worker228.py').read_text()
        self.assertNotIn("sys.argv.extend(['--settings'",text)

    def test_low8_all_wrapper_environments(self):
        root=directory();fake=root/'python';fake.write_text('#!/usr/bin/env bash\n/usr/bin/env\n');fake.chmod(0o755)
        for script in ('run228.sh','read228.sh','compare228.sh'):
            with self.subTest(script=script):
                env=dict(os.environ,READ228_CONTROL_PYTHON=str(fake),READ228_CONTROL_ROOT=str(root/'control'),HOME='/home/forbidden',TMPDIR='/tmp',XDG_CACHE_HOME='/home/cache')
                got=subprocess.run(['bash',str(TARGET/script),'--help'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                self.assertEqual(got.returncode,0,got.stderr)
                values=dict(line.split('=',1) for line in got.stdout.splitlines() if '=' in line)
                for key in ('HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_STATE_HOME','TMPDIR','HF_HOME','TRITON_CACHE_DIR','CUDA_CACHE_PATH','MPLCONFIGDIR'):
                    self.assertTrue(values.get(key,'').startswith(str(root/'control')+'/'),(key,values.get(key)))

    def test_low9_cuda_oom_variants(self):
        torch=types.SimpleNamespace(cuda=types.SimpleNamespace(OutOfMemoryError=type('OOM',(RuntimeError,),{})))
        for message in ('CUDA error: out of memory','CUBLAS_STATUS_ALLOC_FAILED'):
            with self.subTest(message=message):self.assertTrue(O.is_oom(RuntimeError(message),torch))
        self.assertFalse(O.is_oom(RuntimeError('unrelated failure'),torch))

    def test_low9_cuda_oom_variants_write_marker_and_stop(self):
        for message in ('CUDA error: out of memory','CUBLAS_STATUS_ALLOC_FAILED'):
            with self.subTest(message=message):
                out=directory();calls=[]
                def factory():
                    def generate(item):calls.append(item['id']);raise RuntimeError(message)
                    return generate
                parity=types.SimpleNamespace(make_real=factory)
                launch=types.SimpleNamespace(commit_record=lambda *a:None)
                cuda=types.SimpleNamespace(OutOfMemoryError=type('OOM',(RuntimeError,),{}),
                    synchronize=lambda d:None,reset_peak_memory_stats=lambda d:None,
                    max_memory_allocated=lambda d:123,max_memory_reserved=lambda d:456)
                state=O.install(parity,launch,types.SimpleNamespace(cuda=cuda),out,out/'STOP',50,enabled=True)
                with self.assertRaises(RuntimeError):parity.make_real()(dict(id='one'))
                self.assertEqual(calls,['one']);self.assertEqual(state['committed'],[])
                self.assertTrue((out/'telemetry/OOM.json').is_file());self.assertTrue((out/'STOP').is_file())
                self.assertEqual(C.read(out/'telemetry/OOM.json')['error'],message)

    def test_info10_coordinator_unpacks_for_ingest(self):
        text=(TARGET/'coordinator228.sh').read_text()
        self.assertIn('unpack228.py',text);self.assertIn('ingest228.py',text)
        self.assertIn('$kit_dir/ingest/',text)

    def test_medium4_namespace_used_without_relocation(self):
        text=(TARGET/'coordinator228.sh').read_text()
        self.assertNotIn('--relocate-runtime',text)
        self.assertIn('--check-namespace',text)
        self.assertIn('operator_command',(TARGET/'runner228.py').read_text())
        import namespace228 as N
        with patch.object(N,'namespace_command',return_value=['bwrap','fixture']) as command:
            argv=N.operator_command({'python':'/logical/d/v/py'},'--probe','/logical/p',plan={'fixture':True})
        command.assert_called_once_with({'fixture':True})
        self.assertEqual(argv[:5],['bwrap','fixture','/logical/d/v/py','-B','-I'])

if __name__=='__main__':unittest.main(verbosity=2)
