"""Executable adoption regressions against the reviewed round-6 snapshot."""
import ast
import copy
import hashlib
import importlib.util
import io
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(SRC),str(SRC/'u0/tests'),str(SRC/'u0'),str(L/'out/kit_parity50')]
import test_round5 as r5
import test_round4 as r4
BEFORE=os.environ.get('READ_ROUND6_BEFORE')=='1'
E=L/'work/round6-before-u0' if BEFORE else SRC/'u0'
OUT=L/'out_round6' if BEFORE else L/'out'
sha=r5.sha
write=r5.write
fresh=r5.fresh
load=r5.load


def proof_fixture(package, public, helper):
    """Complete synthetic receipt with the same fields as cont_ops' CPU proof."""
    root=package.parent/'node';operator=sha(package/'a/6.py')
    with __import__('tarfile').open(package/'0.tgz') as tar:
        guard=hashlib.sha256(tar.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
    g=dict(passed=True,path='7.py',guard_target='6.py',action='test',operator_sha256=operator,
        operator_sha256_before=operator,operator_sha256_after=operator,batch_sha256=sha(package/'BATCH.sh'),
        events=['guard_installed','write_test','operator_dispatch'],pool=str(root/'wpool'),token=public['token'],
        write_test=dict(bytes=4*1024**2,sha256='a'*64),guard_target_sha256=guard,
        requested_argv=['python',str(root/'a/5.py'),str(root/'a/1.json')],
        dispatched_argv=['python',str(root/'7.py'),str(root/'a/1.json')])
    memory=dict(fits=True,basis='fixed_g3t_shapes',read_cache_bytes=12*1024**3,
                perception_memo_modules=['g3t'],sam_measurement_required=False)
    proof=dict(passed=True,entry_sequence_passed=True,bundle_guard_passed=True,
        plan=public['plan_sha256'],payload=public['payload_sha256'],inputs=sha(package/'a/1.json'),
        operator_sha256=operator,root=str(root),bundle_guard=g,
        entry_sequence=dict(g,entry_sequence_passed=True),memory=memory,
        ready=dict(restore='b'*64,binding='c'*64))
    write(package/'a/c/ENVIRONMENT.json',dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9'))
    proof['ready']['environment']=sha(package/'a/c/ENVIRONMENT.json')
    write(package/'a/c/MEMORY.json',memory)
    return proof


def asset_fixture(root, cfg, proof, template=None):
    export=root/'export';export.mkdir()
    write(export/'RESTORE.json',{'fixture':'export'})
    write(root/'manifest.json',{'fixture':'manifest'})
    write(root/'binding.json',dict(root=str(root),name='manifest.json',sha256=sha(root/'manifest.json')))
    binding=cfg['export_binding']
    identity={k:binding[k] for k in ('run','step','member_directory','lineage','object','config_sha256','archive_sha256')}
    identity['artifact']=dict(sha256='a'*64,bytes=123)
    identity['preparation']={k:dict(sha256=v) for k,v in binding['preparation_sha256'].items()}
    if binding['step']==400:
        identity=json.loads((L/'out/operations/BOUND_EXPORT.json').read_text())
    write(root/'ENVIRONMENT.json',dict(versions=dict(torch='2.11.0+cu129',transformers='5.12.0'),cuda='12.9'))
    proof['ready']['environment']=sha(root/'ENVIRONMENT.json')
    write(root/'export-pin.json',identity)
    write(root/'1.json',dict(export_pin=dict(path='a/export.json',sha256=sha(root/'export-pin.json'),bytes=(root/'export-pin.json').stat().st_size)))
    proof['inputs']=sha(root/'1.json')
    proof['ready'].update(restore=sha(export/'RESTORE.json'),binding=sha(root/'binding.json'))
    config=dict(template or {},export=str(export),artifact_manifest=str(root/'binding.json'),export_pin=str(root/'export-pin.json'))
    config['environment_receipt']=str(root/'ENVIRONMENT.json')
    return config


def selected_gate(helper, args):
    template=json.loads(Path(args[3]).read_text());root=Path(args[3]).parent
    if not hasattr(helper,'DEFAULT_BOUND_EXPORT'):return helper.gate(*args)
    receipts=root/'receipts';receipts.mkdir(exist_ok=True)
    for source,name in ((Path(template['export'])/'RESTORE.json','RESTORE.json'),(Path(template['artifact_manifest']),'binding.json'),(Path(template['export_pin']),'EXPORT_PIN.json'),(root/'1.json','1.json'),(root/'ENVIRONMENT.json','ENVIRONMENT.json')):
        (receipts/name).write_bytes(source.read_bytes())
    kwargs={'bound_export':template['export_pin']} if 'bound_export' in inspect.signature(helper.gate).parameters else {}
    return helper.gate(*args,asset_receipts=receipts,**kwargs)


def gate_receipt(package, public, cfg, proof):
    from a9 import pack
    value=dict(passed=True,adoption_plan_sha256=public['plan_sha256'],
        adoption_profile={k:cfg[k] for k in r5.load('receipt_helper6',SRC/'u0/a20.py').PROFILE_KEYS},
        adoption_assets=dict(restore=proof['ready']['restore'],binding=proof['ready']['binding'],
                             export_pin=sha(package/'a/export.json')),
        adoption_kit=cfg.get('gate_kit_sha256',{}),required_device_type='H100_80GB')
    environment=json.loads((package/'a/c/ENVIRONMENT.json').read_text())
    value['adoption_environment']=dict(sha256=sha(package/'a/c/ENVIRONMENT.json'),torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])
    write(package/'a/g.json',{'u0':pack(value)})
    return value


class Round6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r5.Round5Tests.setUpClass()
        cls.base=r5.Round5Tests.base;cls.target=r5.Round5Tests.target
        cls.binding_path=r5.Round5Tests.root/'binding.json'
        cls.builder=load('builder6',E/'a19.py');cls.helper=load('operations6',E/'a20.py')
        cls.kit=load('kit6',OUT/'kit_parity50/run.py')

    def test_f1_readme_unpack_subprocess(self):
        capture=io.StringIO()
        with redirect_stdout(capture):r4.Round4Tests('test_f2_step600_real_job_and_rehearsal_memory').test_f2_step600_real_job_and_rehearsal_memory()
        root=Path(re.search(r'CPU step-600 fixture: (.+)',capture.getvalue()).group(1))
        local_name='step600' if BEFORE else 'adopted'
        local=fresh();(local/local_name).symlink_to(root/'built',target_is_directory=True)
        folder=root/'built/f';folder.mkdir()
        (folder/'0.tgz').write_bytes((root/'verified.tgz').read_bytes())
        (folder/'EXIT.json').write_bytes((root/'verified.json').read_bytes())
        readme=(OUT/'kit_parity50/README.md').read_text()
        block=next(b for b in re.findall(r'```bash\n(.*?)\n```',readme,re.S) if '--archive "$LOCAL/'+local_name+'/f/0.tgz"' in b)
        start=block.index('CUDA_VISIBLE_DEVICES=')
        if '(cd "$LOCAL/'+local_name+'"' in block:start=block.index('(cd "$LOCAL/'+local_name+'"')
        result=subprocess.run(['bash','-c',block[start:]],env=dict(os.environ,LOCAL=str(local),READ_PYTHON=sys.executable),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((local/local_name/'unpack-success.json').stat().st_size)
        print('README unpack command: exit 0; authenticated partial return accepted.')

    def operations(self):
        root=fresh();self.helper.operations(self.target,self.binding_path,L/'out/operations',root/'ops')
        return root,root/'ops'

    def test_f2_detached_locked_fill_exit_success_and_failure(self):
        for rc in (0,17):
            root,ops=self.operations();package=root/'package';(package/'a').mkdir(parents=True)
            text=(ops/'o_pull_fill.sh').read_text()
            self.assertIn('nohup bash',text,'Pull/fill still runs in the foreground')
            self.assertIn('0.lock',text);self.assertIn('trap',text)
            # Keep the actual launcher, lock and exit trap; replace external IO only.
            start=text.index('export TZ=UTC')
            text=text[:start]+'sleep 0.15\nexit '+str(rc)+'\n'
            text=re.sub(r'^P=.*$', 'P='+str(package),text,flags=re.M)
            script=ops/'probe.sh';script.write_text(text)
            subprocess.run(['bash','-n',str(script)],check=True)
            first=subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=3)
            self.assertEqual(first.returncode,0,first.stderr)
            second=subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=3)
            self.assertNotEqual(second.returncode,0)
            deadline=time.monotonic()+3
            while not (package/'a/1.txt').exists() and time.monotonic()<deadline:time.sleep(.02)
            self.assertEqual((package/'a/1.txt').read_text().strip(),str(rc))
            self.assertTrue((package/'a/0.log').is_file())
        print('Detached fill: success=0, failure=17, duplicate launch refused.')

    def submit_fixture(self):
        root=fresh();p=root/'package';(p/'a/c').mkdir(parents=True)
        for rel in ('0.json','0.tgz','BATCH.sh','a/6.py'):(p/rel).write_bytes((self.target/'package'/rel).read_bytes())
        write(p/'a/1.json',{});write(p/'a/export.json',{})
        pub=json.loads((p/'0.json').read_text());cfg=json.loads(self.builder.unpack((p/'0.tgz').read_bytes())['9.json'])
        proof=proof_fixture(p,pub,self.helper);write(p/'a/c/CPU.json',proof)
        for n in ('dry.json','dry2.json'):write(p/'a'/n,dict(passed=True))
        gate_receipt(p,pub,cfg,proof)
        pool=root/'pool';pool.mkdir();script=root/'check.py';script.write_text(self.helper.SUBMIT_CHECK)
        return p,proof,[sys.executable,'-I','-s','-B',str(script),str(p),str(pool)]

    def test_f3_full_cont_ops_receipt_checks(self):
        p,proof,command=self.submit_fixture()
        good=subprocess.run(command,capture_output=True,text=True);self.assertEqual(good.returncode,0,good.stderr)
        mutations=[('bundle_guard','batch_sha256','0'*64),('bundle_guard','path','6.py'),
            ('entry_sequence','events',[]),('entry_sequence','guard_target_sha256','0'*64),
            ('entry_sequence','requested_argv',[]),('entry_sequence','dispatched_argv',[]),
            ('entry_sequence','batch_sha256','0'*64),('memory','perception_memo_modules',[]),
            ('memory','sam_measurement_required',True)]
        for group,key,value in mutations:
            with self.subTest(field=group+'.'+key):
                bad=copy.deepcopy(proof);bad[group][key]=value;write(p/'a/c/CPU.json',bad)
                self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
        write(p/'a/c/CPU.json',proof);write(p/'a/c/MEMORY.json',{})
        self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'MEMORY.json differs')
        # A fresh package seal cannot repair a stale CPU BATCH pin.
        write(p/'a/c/MEMORY.json',proof['memory']);(p/'BATCH.sh').write_bytes((p/'BATCH.sh').read_bytes()+b'\n')
        write(p/'PACKAGE.json',{'files':{'BATCH.sh':sha(p/'BATCH.sh')}})
        self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Resealed BATCH bypassed CPU proof')

    def test_f4_every_copied_a4_member_pinned_before_output(self):
        names=('package/BATCH.sh','package/3.py','package/a/0.json','package/a/4.py','package/a/7.py','fetch_return.py')
        for rel in names:
            with self.subTest(member=rel):
                original=(self.base/rel).read_bytes();(self.base/rel).write_bytes(original+b'\n')
                try:
                    output=fresh()/'refused'
                    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
                        self.builder.build(self.base,SRC,self.binding_path,output,'ab0123456789',enable_extensions=True,
                            manifest_path=L/'out/patches/MANIFEST.json',extension_pins_path=L/'out/kit_parity50/EXTENSION_PINS.json')
                    self.assertFalse(output.exists())
                finally:(self.base/rel).write_bytes(original)
        manifest=json.loads((L/'out/patches/MANIFEST.json').read_text())
        manifest['operator_base_pin']['decoded_bootstrap_sha256']='0'*64
        root=fresh();write(root/'manifest.json',manifest)
        with self.assertRaisesRegex(ValueError,'bootstrap pin'):
            self.builder.build(self.base,SRC,self.binding_path,root/'refused','ab0123456789',enable_extensions=True,
                manifest_path=root/'manifest.json',extension_pins_path=L/'out/kit_parity50/EXTENSION_PINS.json')

    def gate_fixture(self):
        root=fresh();p,pub,cfg=self.helper.package_config(self.target)
        write(root/'prepared.json',{k:cfg[k] for k in self.helper.PROFILE_KEYS})
        proof=dict(passed=True,plan=pub['plan_sha256'],payload=pub['payload_sha256'],
            operator_sha256=sha(p/'a/6.py'),ready=dict(settings=sha(root/'prepared.json')))
        template=asset_fixture(root,cfg,proof);write(root/'CPU.json',proof);write(root/'template.json',template)
        args=(self.target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'settings.json',root/'config.json')
        return root,args,template

    def test_f5_checkpoint_binding_and_runtime_recheck(self):
        root,args,template=self.gate_fixture();cfg=selected_gate(self.helper,args)
        for path in (Path(template['export'])/'RESTORE.json',Path(template['artifact_manifest']),Path(template['export_pin'])):
            with self.subTest(asset=path.name):
                original=path.read_bytes();path.write_bytes(original+b'\n')
                try:
                    if not BEFORE or path.name!='export-pin.json':
                        with self.assertRaises(ValueError):selected_gate(self.helper,args)
                finally:path.write_bytes(original)
        pin=json.loads(Path(template['export_pin']).read_text());pin['step']+=1;write(Path(template['export_pin']),pin)
        with self.assertRaisesRegex(ValueError,'export identity|export pin'):selected_gate(self.helper,args)

    def test_f5_runtime_asset_recheck(self):
        root,args,template=self.gate_fixture();cfg=selected_gate(self.helper,args)
        self.assertTrue(hasattr(self.kit,'validate_assets'),'Gate lacks runtime asset authentication')
        self.kit.validate_assets(cfg)
        for path in (Path(template['export'])/'RESTORE.json',Path(template['artifact_manifest']),Path(template['export_pin']),root/'manifest.json'):
            with self.subTest(asset=path.name):
                original=path.read_bytes();path.write_bytes(original+b'\n')
                try:
                    with self.assertRaises(ValueError):self.kit.validate_assets(cfg)
                finally:path.write_bytes(original)

    def test_f5_production_device_is_required(self):
        self.assertTrue(hasattr(self.kit,'validate_device'),'GPU name is recorded but never required')
        root,args,_=self.gate_fixture();cfg=selected_gate(self.helper,args)
        self.assertEqual(cfg.get('required_device_type'),'H100_80GB')
        fake=types.SimpleNamespace(cuda=types.SimpleNamespace(get_device_properties=lambda _:types.SimpleNamespace(
            name='NVIDIA H100 80GB HBM3',major=9,minor=0,total_memory=80*1024**3,multi_processor_count=132)))
        self.kit.validate_device(cfg,fake)
        for name,memory,major in [('NVIDIA A100-SXM4-80GB',80,8),('NVIDIA H100 NVL',94,9),('NVIDIA H200',141,9)]:
            fake.cuda.get_device_properties=lambda _,n=name,m=memory,c=major:types.SimpleNamespace(name=n,major=c,minor=0,total_memory=m*1024**3,multi_processor_count=132)
            with self.subTest(device=name),self.assertRaises(ValueError):self.kit.validate_device(cfg,fake)

    def test_info_done_whitespace(self):
        root,ops=self.operations();text=(ops/'o_pull_fill.sh').read_text()
        self.assertNotIn('test "$(cat "$E/5")" =',text,'Whitespace-only receipt changes still refuse')
        line=next(line for line in text.splitlines() if '"$E/5"' in line and '.split()' in line)
        binding=json.loads(self.binding_path.read_text());e=root/'e';e.mkdir()
        (e/'5').write_text(binding['object']+'\t  '+str(binding['archive_bytes'])+' \n '+binding['archive_sha256']+'\n')
        result=subprocess.run(['bash','-c','E='+str(e)+'\n'+line],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        (e/'5').write_text((e/'5').read_text()+' extra')
        self.assertNotEqual(subprocess.run(['bash','-c','E='+str(e)+'\n'+line],capture_output=True).returncode,0)

    def test_info_submit_requires_successful_bound_gpu_gate(self):
        p,proof,command=self.submit_fixture()
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        from a9 import read_wire,pack
        good=json.loads((p/'a/g.json').read_text());value=read_wire(good)
        for key,bad in [('passed',False),('adoption_plan_sha256','0'*64),('required_device_type','A100_80GB'),
                        ('adoption_assets',{}),('adoption_profile',{})]:
            write(p/'a/g.json',{'u0':pack(dict(value,**{key:bad}))})
            with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
        write(p/'a/g.json',{})
        self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main(verbosity=2)
