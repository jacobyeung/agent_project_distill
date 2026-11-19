"""Executable staging, receipt and export-selection regressions; no GPU or scheduler."""
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import types
import unittest
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SRC),str(SRC/'u0'),str(SRC/'u0/tests'),str(L/'out/kit_parity50')]
import test_round6 as r6
import test_round5 as r5
BEFORE=os.environ.get('READ_ROUND7_BEFORE')=='1'
OUT=L/'out_round7' if BEFORE else L/'out'
E=L/'work/round7-before-u0' if BEFORE else SRC/'u0'
OP=Path(os.environ.get('READ_OPERATOR4_SOURCE',str(L/'work/operator4')))
sha=r5.sha;write=r5.write;fresh=r5.fresh;load=r5.load


class Round7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r6.Round6Tests.setUpClass()
        cls.target=r6.Round6Tests.target;cls.base=r6.Round6Tests.base
        cls.helper=load('helper7',E/'a20.py')
        cls.builder=load('builder7',E/'a19.py')
        cls.kit=load('kit7',OUT/'kit_parity50/run.py')
        cls.node=load('node7',L/'work/round7-before-5.py' if BEFORE else OP/'package/a/5.py')

    def test_f1_archive_runs_inside_live_namespace_and_survives_it(self):
        self.assertTrue(hasattr(self.node,'stage_gate_assets'),'CPU proof does not stage the assets while its namespace exists')
        root=fresh();d=root/'private/d';d.mkdir(parents=True)
        (d/'weights').write_bytes(b'fixture weights');(d/'link').symlink_to('weights')
        (d/'READY.json').write_text('{"settings":"fixture"}')
        wrapper=root/'ns.py'
        wrapper.write_text('import subprocess,sys\na=sys.argv[2:]\nif a[0]=="/bin/tar": a[a.index("-C")+1]=sys.argv[1]\nelse: a[-1]=sys.argv[1];a[0]=sys.executable\nraise SystemExit(subprocess.call(a))\n')
        calls=[]
        def namespace(r):
            self.assertTrue(d.exists());calls.append(r)
            return [sys.executable,'-I','-s','-B',str(wrapper),str(d)]
        J=types.SimpleNamespace(namespace=namespace)
        dest=root/'pool/4.tar';dest.parent.mkdir()
        cfg=dict(read_extensions=True,logical='/scratch/jjyeung/abcdef123456')
        record=self.node.stage_gate_assets(root/'private',cfg,J,dest,subprocess.run,dict(os.environ))
        self.assertEqual(calls,[root/'private'])
        self.assertEqual(record,dict(path=str(dest),sha256=sha(dest),bytes=dest.stat().st_size,logical=cfg['logical']))
        d.rename(root/'unreachable')
        with tarfile.open(dest) as tar:
            self.assertEqual(tar.extractfile('./weights').read(),b'fixture weights')
            self.assertTrue(tar.getmember('./link').issym())
            self.assertEqual(tar.extractfile('./link').read(),b'fixture weights')
        with self.assertRaises(FileExistsError):
            self.node.stage_gate_assets(root/'private',cfg,J,dest,subprocess.run,dict(os.environ))
        with patch.object(J,'namespace',side_effect=AssertionError('OFF staging ran')):
            self.assertIsNone(self.node.stage_gate_assets(root,{},J,root/'off.tar',subprocess.run,{}))
        self.assertFalse((root/'off.tar').exists())
        print('Live namespace tar: regular file and symlink preserved; archive survives namespace loss; duplicate and OFF guarded.')

    def test_f2_fill_wait_missing_token_dead_pid_timeout_and_success(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        self.assertIn('# BEGIN FILL_WAIT',text,'Fill wait has no bounded executable block')
        block=text.split('# BEGIN FILL_WAIT\n')[1].split('# END FILL_WAIT')[0]
        self.assertIn('${PACKAGE_TOKEN:?',block)
        root=fresh();(root/'a').mkdir();(root/'a/0.txt').write_text('99999999\n')
        block=re.sub(r'^P=.*$', 'P='+str(root),block,flags=re.M).replace('sleep 60','sleep 0.01')
        env=dict(os.environ,PACKAGE_TOKEN='abcdef123456',FILL_MAX_SECONDS='1')
        missing=dict(env);missing.pop('PACKAGE_TOKEN')
        self.assertNotEqual(subprocess.run(['bash','-eu','-c',block],env=missing,capture_output=True,timeout=3).returncode,0)
        dead=subprocess.run(['bash','-eu','-c',block],env=env,capture_output=True,text=True,timeout=3)
        self.assertNotEqual(dead.returncode,0);self.assertIn('worker is gone',dead.stderr)
        (root/'a/0.txt').write_text(str(os.getpid()))
        timeout=subprocess.run(['bash','-eu','-c',block],env=env,capture_output=True,text=True,timeout=3)
        self.assertNotEqual(timeout.returncode,0);self.assertIn('wait exceeded',timeout.stderr)
        (root/'a/1.txt').write_text('0\n')
        self.assertEqual(subprocess.run(['bash','-eu','-c',block],env=env,capture_output=True,timeout=3).returncode,0)
        (root/'a/1.txt').write_text('17\n')
        self.assertNotEqual(subprocess.run(['bash','-eu','-c',block],env=env,capture_output=True,timeout=3).returncode,0)
        print('Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.')

    def test_f3_exact_sxm_name_and_132_sms(self):
        cfg=dict(required_device_type='H100_80GB')
        def check(name,sms):
            prop=types.SimpleNamespace(name=name,major=9,minor=0,total_memory=80*1024**3,multi_processor_count=sms)
            self.kit.validate_device(cfg,types.SimpleNamespace(cuda=types.SimpleNamespace(get_device_properties=lambda _:prop)))
        check('NVIDIA H100 80GB HBM3',132)
        for name,sms in [('NVIDIA H100 PCIe',114),('NVIDIA H100 80GB HBM3',114),('NVIDIA H100 PCIe',132)]:
            with self.subTest(name=name,sms=sms),self.assertRaises(ValueError):check(name,sms)

    def fixture(self,target=None,identity=None):
        target=target or self.target;root=fresh();p,pub,cfg=self.helper.package_config(target)
        write(root/'prepared.json',{k:cfg[k] for k in self.helper.PROFILE_KEYS})
        proof=dict(passed=True,plan=pub['plan_sha256'],payload=pub['payload_sha256'],
            operator_sha256=sha(p/'a/6.py'),ready=dict(settings=sha(root/'prepared.json')))
        template=r6.asset_fixture(root,cfg,proof)
        ep=Path(template['export_pin'])
        value=identity or json.loads(ep.read_text())
        write(ep,value);write(root/'selected.json',value)
        write(p/'a/1.json',dict(export_pin=dict(path='a/export.json',sha256=sha(ep),bytes=ep.stat().st_size)))
        proof['inputs']=sha(p/'a/1.json')
        write(root/'CPU.json',proof);write(root/'template.json',template)
        args=(target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'settings.json',root/'config.json')
        kwargs={'bound_export':root/'selected.json'} if 'bound_export' in inspect.signature(self.helper.gate).parameters else {}
        return root,p,args,kwargs

    def test_info_export_bytes_bound_to_cpu_inputs_before_gpu(self):
        root,p,args,kwargs=self.fixture();self.helper.gate(*args,**kwargs)
        ep=root/'export-pin.json';ep.write_bytes(ep.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'export pin|export bytes'):self.helper.gate(*args,**kwargs)

    def test_info_receipt_records_and_submit_checks_kit_comparator_sample(self):
        self.assertTrue(hasattr(self.kit,'kit_hashes'),'Receipt omits executing kit/comparator/sample bytes')
        got=self.kit.kit_hashes()
        self.assertEqual(got,{'run.py':sha(OUT/'kit_parity50/run.py'),
            'compare.py':sha(OUT/'kit_parity50/compare.py'),'sample50.json':sha(OUT/'kit_parity50/sample50.json')})
        fixture=r6.Round6Tests();fixture.target=self.target;fixture.helper=self.helper;fixture.builder=self.builder
        p,proof,command=fixture.submit_fixture()
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        from a9 import pack,read_wire
        value=read_wire(json.loads((p/'a/g.json').read_text()))
        for name in ('run.py','compare.py','sample50.json'):
            bad=copy.deepcopy(value);bad['adoption_kit'][name]='0'*64
            write(p/'a/g.json',{'u0':pack(bad)})
            with self.subTest(file=name):
                result=subprocess.run(command,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn('kit',result.stderr)
        cfg={key:value[key] for key in ('adoption_plan_sha256','adoption_profile','adoption_assets','required_device_type')}
        cfg['adoption_kit']=got;root=fresh()
        with patch.object(self.kit,'validate_environment',return_value=value['adoption_environment'],create=True):
            self.kit.write_gate_receipt(root,cfg,True)
        self.assertEqual(read_wire(json.loads((root/'ue.json').read_text()))['adoption_kit'],got)

    def test_info_unpack_ignores_python_environment_and_keeps_sibling_import(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        block=next(b for b in re.findall(r'```bash\n(.*?)\n```',text,re.S) if './unpack_return.py' in b)
        self.assertIn(' -s -E -B ./unpack_return.py',block)
        root=fresh();target=root/'adopted';target.mkdir();(target/'f').mkdir()
        (target/'fetch_return.py').write_text('VALUE=17\n')
        (target/'unpack_return.py').write_text('from fetch_return import VALUE\nassert VALUE==17\nprint("fixture unpack passed")\n')
        block=block[block.index('(cd '):]
        result=subprocess.run(['bash','-eu','-c',block],env=dict(os.environ,LOCAL=str(root),READ_PYTHON=sys.executable,
            PYTHONHOME='/invalid-python-home',PYTHONPATH='/invalid-python-path'),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('fixture unpack passed',(target/'unpack-success.json').read_text())

    def test_info_host_paths_allocation_and_input_evidence(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        self.assertNotIn('$LOCAL/5.tar',text)
        self.assertIn('salloc --account=mt01',text)
        self.assertIn('physically exist and be writable',text)
        self.assertIn('1.json',next(b for b in re.findall(r'```bash\n(.*?)\n```',text,re.S) if 'CPU.json MEMORY.json' in b))

    def test_rebind_step400_only(self):
        if BEFORE:
            self.assertIn('bound_export',inspect.signature(self.helper.gate).parameters,'Gate lacks reviewed export binding')
        self.assertNotIn('bound_export',inspect.signature(self.helper.gate).parameters)
        default=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())
        self.assertEqual(default['step'],400)
        self.assertEqual(default['artifact']['sha256'],'5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd')
        root,p,args,kwargs=self.fixture(identity=default)
        config=self.helper.gate(*args)
        self.assertEqual(config['adoption_assets']['export_pin'],sha(root/'export-pin.json'))
        changed=copy.deepcopy(default);changed['artifact']['sha256']='b'*64
        root,p,args,kwargs=self.fixture(identity=changed)
        with self.assertRaisesRegex(ValueError,'step-400 export'):self.helper.gate(*args)
        print('Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.')


if __name__=='__main__':unittest.main(verbosity=2)
