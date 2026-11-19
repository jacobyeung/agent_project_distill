"""Namespace and production guard regressions, with preserved round-9 controls."""
import ast
import copy
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import types
import unittest
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SRC),str(SRC/'u0'),str(SRC/'u0/tests'),str(L/'out/kit_parity50')]
import torch
torch.set_num_threads(8)
import test_round5 as r5
import test_round6 as r6
BEFORE=os.environ.get('READ_ROUND9_BEFORE')=='1'
OUT=L/('out_round9' if BEFORE else 'out')
load=r5.load;fresh=r5.fresh;sha=r5.sha

class Round9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kit=load('kit9',OUT/'kit_parity50/run.py')

    def host(self):
        path=OUT/'kit_parity50/host.py'
        self.assertTrue(path.is_file(),'Missing namespace host launcher')
        return load('host9',path)

    def test_f1_all_commands_use_real_namespace_and_input_wrapper(self):
        host=self.host()
        from orchard_h10.common import template
        _,J,*_=template()
        root=fresh();kit='/scratch/jjyeung/a123456789abc'
        inputs={'python':'/scratch/jjyeung/b01ec87a6f29b/d/v/py'}
        with patch.dict(os.environ,USER='jjyeung',SLURM_JOB_ID='123',CUDA_VISIBLE_DEVICES='0'):
            env=host.gate_environment(root,kit,J)
        self.assertEqual(env['HOME'],str(root/'home'));self.assertEqual(env['TMPDIR'],str(root/'temp'))
        self.assertEqual(env['OPENBLAS_NUM_THREADS'],'1')
        self.assertEqual(env['TRITON_CACHE_DIR'],kit+'/u6/u1')
        for args in (['-c',host.PREFLIGHT,kit+'/u0/u2.json'],[kit+'/u0/u0.py',kit+'/u0/u2.json'],['--worker','ON']):
            command=host.namespace_command(root,inputs,J,args)
            prefix=J.namespace(root)
            self.assertEqual(command[:len(prefix)],prefix)
            self.assertEqual(command[len(prefix):len(prefix)+3],[inputs['python'],'-B','-I'])
            self.assertEqual(command[-len(args):],args)
        source=inspect.getsource(self.kit.main)
        self.assertNotIn('sys.executable',source)
        self.assertEqual(source.count('worker_command('),3)
        self.assertNotIn("OPENBLAS_NUM_THREADS='8'",source)
        self.assertIn('namespace_command',inspect.getsource(self.kit.worker_command))
        print('Real J.namespace prefix and inputs[python] wrap preflight, parent and all three worker launch sites; J.environment retains HOME/TMPDIR/OPENBLAS=1.')

    def test_f1_runtime_staging_reuses_package_block_and_pins(self):
        host=self.host()
        from orchard_h10.common import template
        from orchard_h10 import job
        S,J,*_=template()
        # The group loop and bwrap copy are byte-identical to the package block.
        block=inspect.getsource(job.stage).split("    for i,group in enumerate(assets['groups']):",1)[1].split("    for i,a in enumerate(inputs['archives']):",1)[0]
        self.assertIn("    for i,group in enumerate(assets['groups']):"+block,inspect.getsource(host.stage_runtime))
        root=fresh();source=root/'source';source.mkdir();target=root/'root';target.mkdir()
        archive=source/'0.tar'
        with tarfile.open(archive,'w') as t:
            data=b'fixture interpreter';m=tarfile.TarInfo('sj/uv-python/fixture');m.size=len(data);t.addfile(m,io.BytesIO(data))
        bwrap=source/'bwrap';bwrap.write_bytes(b'fixture bwrap')
        assets={'groups':[[[str(archive),archive.stat().st_size,sha(archive)]]],
                'bwrap_pin':dict(path=str(bwrap),bytes=bwrap.stat().st_size,sha256=sha(bwrap))}
        with patch.object(S,'room'):
            receipt=host.stage_runtime(target,assets,S)
        self.assertEqual((target/'sj/uv-python/fixture').read_bytes(),b'fixture interpreter')
        self.assertEqual(receipt['bwrap']['sha256'],sha(bwrap))
        bad=copy.deepcopy(assets);bad['groups'][0][0][2]='0'*64
        another=root/'bad';another.mkdir()
        with patch.object(S,'room'),self.assertRaisesRegex(ValueError,'SHA256'):
            host.stage_runtime(another,bad,S)
        pins=json.loads((OUT/'kit_parity50/RUNTIME_PINS.json').read_text())
        actual=json.loads((SRC/'orchard_h10/vendor/ORCHARD_ASSETS.json').read_text())
        self.assertEqual(pins['groups'],actual['groups']);self.assertEqual(pins['bwrap_pin'],actual['bwrap_pin'])
        self.assertEqual(sum(len(g) for g in pins['groups']),13)
        print('Package staging block extracts pinned fixture runtime; changed part hash refuses; 13 part pins plus bwrap match A4 receipts.')

    def test_f1_actual_launch_calls_namespace_twice(self):
        host=self.host()
        from orchard_h10.common import template
        S,J,*_=template()
        root=fresh();kit='/scratch/jjyeung/a123456789abc'
        inputs={'python':'/scratch/jjyeung/b01ec87a6f29b/d/v/py'}
        with patch.object(host,'runtime_context',return_value=(inputs,S,J)), \
             patch.dict(os.environ,USER='jjyeung',SLURM_JOB_ID='123',CUDA_VISIBLE_DEVICES='0'), \
             patch.object(host.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
            self.assertEqual(host.launch(root,kit),0)
        self.assertEqual(run.call_count,2)
        for call in run.call_args_list:
            command=call.args[0];prefix=J.namespace(root)+[inputs['python'],'-B','-I']
            self.assertEqual(command[:len(prefix)],prefix)
            self.assertEqual(call.kwargs['env']['OPENBLAS_NUM_THREADS'],'1')
            self.assertEqual(call.kwargs['env']['U0_ROOT'],str(root))
        self.assertIn(host.PREFLIGHT,run.call_args_list[0].args[0])
        self.assertIn(kit+'/u0/u0.py',run.call_args_list[1].args[0])
        print('Actual host launch calls preflight then parent with real namespace prefixes and the input wrapper.')

    def test_f1_authenticated_bootstrap_and_physical_asset_extraction(self):
        host=self.host()
        from orchard_h10.common import template
        S,J,*_=template()
        root=fresh();package=root/'package';(package/'a/c').mkdir(parents=True)
        original=Path(os.environ['READ_INPUT_SRC']).parent/'package'
        for name in ('0.tgz','0.json','a/1.json'):
            (package/name).write_bytes((original/name).read_bytes())
        public=json.loads((package/'0.json').read_text())
        with tarfile.open(package/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
        archive=package/'a/4.tar'
        with tarfile.open(archive,'w') as t:
            for name,raw in (('binding.json',b'{}'),('ENVIRONMENT.json',b'{}'),('m400/heads.pt',b'heads'),('v/py',b'wrapper bytes remain untouched')):
                item=tarfile.TarInfo(name);item.size=len(raw);t.addfile(item,io.BytesIO(raw))
            item=tarfile.TarInfo('e/heads.pt');item.type=tarfile.SYMTYPE;item.linkname=cfg['logical']+'/d/m400/heads.pt';t.addfile(item)
        proof=dict(passed=True,payload=public['payload_sha256'],plan=public['plan_sha256'],inputs=sha(package/'a/1.json'),
                   gate_assets=dict(path=str(archive),logical=cfg['logical'],bytes=archive.stat().st_size,sha256=sha(archive)))
        (package/'a/c/CPU.json').write_text(json.dumps(proof))
        physical=root/'root';physical.mkdir();kit='/scratch/jjyeung/a123456789abc';calls=[]
        real_run=subprocess.run
        def unpack(command,**kwargs):
            prefix=J.namespace(physical)
            self.assertEqual(command[:len(prefix)],prefix)
            self.assertEqual(command[len(prefix):],['/bin/tar','-xf','-','-C',cfg['logical']+'/d'])
            calls.append(command)
            return real_run(['/bin/tar','-xf','-','-C',str(J.physical(physical,cfg['logical']+'/d'))],**kwargs)
        with patch.object(host,'stage_runtime',return_value={'fixture':True}),patch.object(J,'storage_proof'), \
             patch.object(S,'room'),patch.object(host.subprocess,'run',side_effect=unpack), \
             patch.dict(os.environ,USER='jjyeung',SLURM_JOB_ID='123',CUDA_VISIBLE_DEVICES='0'):
            receipt=host.stage(package,physical,kit,archive)
        self.assertEqual(len(calls),1)
        data=J.physical(physical,cfg['logical']+'/d')
        self.assertEqual((data/'v/py').read_bytes(),b'wrapper bytes remain untouched')
        self.assertEqual(os.readlink(data/'e/heads.pt'),cfg['logical']+'/d/m400/heads.pt')
        self.assertEqual(os.readlink(data/'7.json'),'binding.json')
        self.assertEqual(os.readlink(data/'9.json'),'ENVIRONMENT.json')
        self.assertEqual(receipt['inputs'],sha(package/'a/1.json'))
        self.assertEqual((physical/'bootstrap/orchard_h10/job.py').read_bytes(),(SRC/'orchard_h10/job.py').read_bytes())
        proof['inputs']='0'*64;(package/'a/c/CPU.json').write_text(json.dumps(proof))
        with self.assertRaises(ValueError):host.authenticate(package)
        print('Authenticated real A4 bootstrap stages fixture 4.tar to root/sj/<logical>/d with preserved wrapper/links; changed input proof refuses. Runtime I/O and bwrap execution are explicit doubles.')

    def test_f2_real_guard_self_test_and_each_missed_operation(self):
        self.assertTrue(hasattr(self.kit,'guard_self_test'),'Missing production guard self-test')
        from a0 import WeightGuard
        result=self.kit.guard_self_test({'source_root':str(SRC)})
        self.assertEqual(result,{'passed':True,'checks':dict(add_=True,copy_=True,load_state_dict=True)})
        for missed in ('add_','copy_','load_state_dict'):
            index=('add_','copy_','load_state_dict').index(missed)
            class SelectiveGuard(WeightGuard):
                count=0
                def __init__(self,provider):
                    self.index=SelectiveGuard.count;SelectiveGuard.count+=1
                    super().__init__(provider)
                def check(self):
                    if self.index!=index:return super().check()
            with patch('a0.WeightGuard',SelectiveGuard):
                bad=self.kit.guard_self_test({'source_root':str(SRC)})
            self.assertFalse(bad['passed']);self.assertIs(bad['checks'][missed],False)
        source=inspect.getsource(self.kit.main)
        self.assertLess(source.index('guard_self_test('),source.index('for mode in'))
        print('Real frozen scratch module detects add_, copy_ and load_state_dict; each injected detection miss fails independently before workers.')

    def test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt(self):
        self.assertIn('guard_self_test',inspect.signature(self.kit.write_gate_receipt).parameters,'Receipt omits self-test')
        cfg=dict(adoption_plan_sha256='a'*64,adoption_profile={},adoption_assets={},required_device_type='H100_80GB')
        root=fresh();bad={'passed':False,'checks':dict(add_=True,copy_=False,load_state_dict=True)}
        with patch.object(self.kit,'validate_kit'),patch.object(self.kit,'validate_environment',return_value={}):
            self.kit.write_gate_receipt(root,cfg,False,guard_self_test=bad)
            from a9 import read_wire
            value=read_wire(json.loads((root/'ue.json').read_text()))
            self.assertFalse(value['passed']);self.assertEqual(value['guard_self_test'],bad)
            with self.assertRaises(ValueError):self.kit.write_gate_receipt(root,cfg,True,guard_self_test=bad)
            with self.assertRaises(ValueError):self.kit.write_gate_receipt(root,cfg,True)
        print('A missed mutation persists in failed ue.json; missing or failed guard evidence cannot produce passed=true.')

    def test_f2_main_records_failure_and_never_starts_workers(self):
        self.assertTrue(hasattr(self.kit,'guard_self_test'),'Missing production self-test')
        from contextlib import ExitStack
        import a9
        root=fresh();settings=root/'settings.json';settings.write_text('{}')
        cfg=dict(settings=str(settings),source_root=str(SRC),adoption_plan_sha256='a'*64,
                 adoption_profile={},adoption_assets={},required_device_type='H100_80GB')
        config=root/'config.json';config.write_text(json.dumps({'u0':a9.pack(cfg)}))
        sample=root/'sample.json';sample.write_text(json.dumps({'u0':a9.pack([])}))
        identity=root/'identity.json';identity.write_text(json.dumps({'u0':a9.pack({})}))
        for setup_error in (False,True):
            output=root/('failure' if not setup_error else 'exception')
            with ExitStack() as stack:
                stack.enter_context(patch.object(json,'loads',json.loads))
                stack.enter_context(patch.object(a9,'install_log_boundary'))
                stack.enter_context(patch.object(a9,'validate_paths'))
                stack.enter_context(patch.object(a9.OPAQUE_PATH,'fullmatch',return_value=True))
                stack.enter_context(patch.object(self.kit,'SAMPLE',sample));stack.enter_context(patch.object(self.kit,'IDENTITY',identity))
                for name in ('validate_roots','validate_profile','validate_assets','validate_kit'):
                    stack.enter_context(patch.object(self.kit,name))
                stack.enter_context(patch.object(self.kit,'validate_environment',return_value={}))
                bad=dict(passed=False,checks=dict(add_=False,copy_=True,load_state_dict=True))
                stack.enter_context(patch.object(self.kit,'guard_self_test',**({'side_effect':RuntimeError('fixture')} if setup_error else {'return_value':bad})))
                worker=stack.enter_context(patch.object(self.kit,'worker_command',side_effect=AssertionError('Worker started after failed self-test')))
                stack.enter_context(patch.object(sys,'argv',['u0.py',str(config),'--out',str(output),'--enable-gpu','--public']))
                self.assertEqual(self.kit.main(),1);worker.assert_not_called()
            receipt=a9.read_wire(a9.RAW_LOADS((output/'ue.json').read_text()))
            self.assertFalse(receipt['passed']);self.assertFalse(receipt['guard_self_test']['passed'])
            if setup_error:self.assertEqual(receipt['guard_self_test']['errors'],{'setup':'RuntimeError'})
        print('Actual main writes failed ue.json and starts zero workers for a missed mutation or self-test setup exception.')

    def test_f2_submit_requires_all_three_guard_checks(self):
        # Exercise the same standalone submit checker used by operators.
        helper=load('helper9',L/'work/round9-before-a20.py' if BEFORE else SRC/'u0/a20.py')
        self.assertIn("gate.get('guard_self_test')",helper.SUBMIT_CHECK,'Submit omits guard evidence')
        r6.Round6Tests.setUpClass();f=r6.Round6Tests();f.target=r6.Round6Tests.target;f.helper=helper;f.builder=r6.Round6Tests.builder
        package,proof,command=f.submit_fixture()
        from a9 import pack,read_wire
        path=package/'a/g.json';value=read_wire(json.loads(path.read_text()))
        value['guard_self_test']={'passed':True,'checks':dict(add_=True,copy_=True,load_state_dict=True)}
        path.write_text(json.dumps({'u0':pack(value)}))
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        for op in ('add_','copy_','load_state_dict'):
            bad=copy.deepcopy(value);bad['guard_self_test']['checks'][op]=False
            path.write_text(json.dumps({'u0':pack(bad)}))
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
        print('Submit accepts complete guard evidence and rejects each missed mutation.')

    def test_f3_staging_transfer_precedes_allocation_and_roots_extract(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        allocation=text.index('salloc --account')
        for marker in ('--enable-extensions gate','a11.py" seal','a11.py" stage-kit','--bwlimit=8000'):
            self.assertLess(text.index(marker),allocation,marker)
        for command in ('tar -xzf "$GPU_TRANSFER/4.tgz" -C "$GPU_PHYSICAL_KIT"',
                        'tar -xf "$GPU_PHYSICAL_KIT/1.tar" -C "$GPU_PHYSICAL_KIT/u1"',
                        'tar -xf "$GPU_PHYSICAL_KIT/2.tar" -C "$GPU_PHYSICAL_KIT/u2"'):
            self.assertIn(command,text)
        self.assertIn('--stage',text);self.assertIn('--run',text)
        self.assertNotIn('interpreter outside bwrap',text)
        root=fresh();transfer=root/'transfer';transfer.mkdir();physical=root/'root/sj/a123456789abc'
        members={}
        for number,label in ((1,'patched'),(2,'original')):
            buf=io.BytesIO()
            with tarfile.open(fileobj=buf,mode='w') as t:
                raw=label.encode();item=tarfile.TarInfo('source.py');item.size=len(raw);t.addfile(item,io.BytesIO(raw))
            members[str(number)+'.tar']=buf.getvalue()
        members['u0/u0.py']=b'fixture kit'
        with tarfile.open(transfer/'4.tgz','w:gz') as t:
            for name,raw in members.items():
                item=tarfile.TarInfo(name);item.size=len(raw);t.addfile(item,io.BytesIO(raw))
        (transfer/'4.sha256').write_text(sha(transfer/'4.tgz')+'  4.tgz\n')
        block=text.split('mkdir -p "$GPU_PHYSICAL_KIT"',1)[1].split('# Stage runtime',1)[0]
        block='mkdir -p "$GPU_PHYSICAL_KIT"'+block
        result=subprocess.run(['bash','-eu','-c',block],env=dict(os.environ,GPU_TRANSFER=str(transfer),GPU_PHYSICAL_KIT=str(physical)),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((physical/'u1/source.py').read_text(),'patched')
        self.assertEqual((physical/'u2/source.py').read_text(),'original')
        self.assertEqual((physical/'u0/u0.py').read_bytes(),b'fixture kit')
        print('Gate/seal/stage-kit/transfer precede salloc; exact README host commands successfully extract kit and both source fixture archives.')

    def test_info_token_and_framework_gap_and_guard_limits(self):
        text=(OUT/'kit_parity50/README.md').read_text()
        self.assertIn('GPU_KIT="/scratch/jjyeung/${GATE_TOKEN}"',text)
        self.assertNotIn('ab0123456789',(OUT/'kit_parity50/config.example.json').read_text())
        evidence=(OUT/'FRAMEWORK_EVIDENCE.md').read_text()
        for phrase in ('2.13.0+cu130','5.19.0','load_state_dict','2.11.0+cpu','5.12.1'):
            self.assertIn(phrase,evidence)
        for phrase in ('Raw writes restored between boundaries','Models must remain frozen'):
            self.assertIn(phrase,text)
        print('Fresh token derives kit paths; framework version gap and carried guard limits are explicit.')

    def test_info_round7_logs_are_labelled(self):
        names=('lock_round3','operator_round3','public','read_cache','read_journal','round1','round2','round3')
        for name in names:
            self.assertTrue((OUT/'checks/round7'/('applied_'+name+'.txt')).is_file(),name)
            self.assertFalse((OUT/'checks'/('applied_'+name+'.txt')).exists(),name)
        print('Eight carried round-7 applied logs live only under checks/round7.')

if __name__=='__main__':unittest.main(verbosity=2)
