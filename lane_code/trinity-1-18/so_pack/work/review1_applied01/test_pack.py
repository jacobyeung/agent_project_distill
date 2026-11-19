"""Mutation tests using supplied package helpers. Outputs stay under --work."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tarfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import pack as P
import pack_probes as Q

MIRROR=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')
ROUTE=MIRROR/'cont_ops16/work/c15/r1route/out3'
DB=MIRROR/'cont_ops18/dbuild'
CPU='/scratch/jjyeung/envs/p1cpu/bin/python'
ROOT=None


def tarbytes(files,gz=False):
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w:gz' if gz else 'w') as tar:
        for n,d in sorted(files.items()):
            m=tarfile.TarInfo(n);m.size=len(d);m.mode=0o600;tar.addfile(m,io.BytesIO(d))
    return b.getvalue()


def copy_package(dest,which='B5'):
    dest.mkdir(mode=0o700)
    for n,d in P.package_files(ROUTE/which/'package').items():
        p=dest/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
    (dest/'a').chmod(0o700)
    return dest


def reseal(package, update_bundle=True):
    pub=P.read(package/'0.json');pk=P.read(package/'PACKAGE.json')
    pay=P.unpack((package/'0.tgz').read_bytes());plan=json.loads(pay['9.json'])
    pub.update(payload_bytes=(package/'0.tgz').stat().st_size,
               payload_sha256=P.file_sha(package/'0.tgz'),plan_sha256=P.canonical(plan))
    P.write(package/'0.json',pub);P.write(package/'CONFIG.json',pub)
    if update_bundle:
        batch=(package/'BATCH.sh').read_text();bm=P.bundle(batch.encode())
        bm['0.json']=(package/'0.json').read_bytes();bm['7.py']=(package/'a/6.py').read_bytes()
        old=next(l for l in batch.splitlines() if l.startswith('b=bytes.fromhex('))
        batch=batch.replace(old,'b=bytes.fromhex(%r)'%tarbytes(bm,True).hex())
        (package/'BATCH.sh').write_text(batch)
    for n in pk['files']:pk['files'][n]=P.file_sha(package/n)
    P.write(package/'PACKAGE.json',pk)


def fill_fixture(root,drop_env=False):
    """Exact fill source; only its sealed test binding is synthetic."""
    package=copy_package(root/'p')
    oldpay=P.unpack((package/'0.tgz').read_bytes());plan=json.loads(oldpay['9.json'])
    binding=copy.deepcopy(plan['export_binding']);binding['config_sha256']='c'*64
    receipt=dict(config_sha256=binding['config_sha256'],frame_layout='duplicate')
    raw_receipt=json.dumps(receipt,sort_keys=True).encode()
    config=dict(base_identity=binding['base_identity'],frame_layout='duplicate',
        preparation=dict(path='/scratch/jjyeung/abc/prepared/s1_receipt.json',sha256=P.sha(raw_receipt)))
    raw_config=json.dumps(config,sort_keys=True).encode()
    data=dict(status='PREPARED',schema='s1-in-job-data-v1',real_frames_verified=True,
        rehearsal=False,synthetic=False,config=dict(path='/scratch/jjyeung/abc/inputs/config.json',
        sha256=P.sha(raw_config)),preparation=config['preparation'])
    raw_data=json.dumps(data,sort_keys=True).encode()
    prep={'config':raw_config,'receipt':raw_receipt,'data_receipt':raw_data}
    binding['preparation_sha256']={n:P.sha(d) for n,d in prep.items()}
    run=binding['run'];member=binding['member_directory']
    heads=b'heads';weights=b'weights';index=b'index'
    full=dict(schema='full-ft-export-v1',dtype='bfloat16',
        files=[dict(name='w',bytes=len(weights),sha256=P.sha(weights))],
        index=dict(name='i',bytes=len(index),sha256=P.sha(index)))
    fullraw=json.dumps(full).encode()
    artifact=dict(step=binding['step'],config_sha256=binding['config_sha256'],
        base_identity=binding['base_identity'],frame_layout='duplicate',geometry_online=False,
        heads=dict(path='/runs/'+run+'/'+member+'/heads.pt',sha256=P.sha(heads)),
        full_weights=dict(path='/runs/'+run+'/'+member+'/full_weights/full_weights.json',sha256=P.sha(fullraw)))
    raw=tarbytes({member+'/heads.pt':heads,member+'/full_weights/w':weights,
        member+'/full_weights/i':index,member+'/full_weights/full_weights.json':fullraw,
        member+'/artifact.json':json.dumps(artifact).encode()})
    fixtures=root/'f';fixtures.mkdir();mirrors={};part_paths=[]
    remote=P.REMOTE_ROOT+'/abc123/e/'
    for i in range(4):
        part=fixtures/str(i);part.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4])
        rp=remote+str(i);part_paths.append(rp)
        mirrors[rp]=dict(local=str(part),bytes=part.stat().st_size,sha256=P.file_sha(part))
    extra={'done':(binding['object']+' '+str(len(raw))+' '+P.sha(raw)+'\n').encode()}
    extra.update(prep)
    for n,d in extra.items():
        path=fixtures/n;path.write_bytes(d)
        mirrors[remote+n]=dict(local=str(path),bytes=len(d),sha256=P.sha(d))
    text=(package/'a/4.py').read_text()
    import re
    values={'REVIEWED_OBJECT':repr(binding['object']),'REVIEWED_ARCHIVE_BYTES':str(len(raw)),
            'REVIEWED_ARCHIVE_SHA256':repr(P.sha(raw))}
    for n,v in values.items():text=re.sub(r'^'+n+r' = .*$',n+' = '+v,text,flags=re.M)
    if drop_env:
        text=text.replace("inputs['archives'].append(dict(","inputs['archives'][4]=dict(")
        text=text.replace("expanded_bytes=sum(map(len,raw.values()))))","expanded_bytes=sum(map(len,raw.values())))")
    (package/'a/4.py').write_text(text)
    plan['export_binding']=binding;oldpay['9.json']=json.dumps(plan,sort_keys=True).encode()
    (package/'0.tgz').write_bytes(tarbytes(oldpay,True));reseal(package)
    f=dict(parts=part_paths,object=binding['object'],lineage=binding['lineage'],step=binding['step'])
    for n in extra:f[n]=remote+n
    cfg=dict(python=CPU,remote=dict(root=P.REMOTE_ROOT,walltime='02:30:00'),fill=f,mirrors=mirrors)
    return package,cfg


def repin_payload(package,pay):
    plan=json.loads(pay['9.json'])
    for n in plan['payload_pins']:
        plan['payload_pins'][n]=dict(bytes=len(pay[n]),sha256=P.sha(pay[n]))
    pay['9.json']=json.dumps(plan,sort_keys=True).encode()
    (package/'0.tgz').write_bytes(tarbytes(pay,True));reseal(package)


def empty_ledger(root):
    p=root/'ledger.jsonl';p.write_text('')
    return dict(path=str(p),sha256=P.file_sha(p))


def execute_fixture_fill(package,cfg):
    pub=P.read(package/'0.json');remote=P.REMOTE_ROOT+'/'+P.PREFIX+pub['token']
    args=P.fill_argv(cfg,remote)
    old=sys.argv[:]
    try:
        with Q.Mirrors(cfg['mirrors'],remote,package):
            sys.argv=args[4:]
            runpy.run_path(remote+'/a/4.py',run_name='__main__')
    finally:sys.argv=old
    return P.read(package/'a/0.json'),P.read(package/'a/1.json')


class PackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=ROOT/'src'
        P.extract((ROUTE/'B5/package/0.tgz').read_bytes(),cls.src)
        # CPU thread limit before any tensor operation; source citation in report.
        import torch
        torch.set_num_threads(8)

    def setUp(self):
        self.w=ROOT/('a'+os.urandom(6).hex());self.w.mkdir()

    def test_01_null_frame_metadata_defect(self):
        row=dict(student_input=dict(frames=[dict(path='a',sha256='a'*64)],
            frame_indices=[0],timestamps=[0.],fps=30.,total_num_frames=1))
        self.assertEqual(Q.check_rows(self.src,[row]),1)
        bad=copy.deepcopy(row);bad['student_input']['total_num_frames']=None
        with self.assertRaises((TypeError,ValueError)):Q.check_rows(self.src,[bad])
        bad=copy.deepcopy(row);bad['student_input']['fps']=None
        with self.assertRaises((TypeError,ValueError)):Q.check_rows(self.src,[bad])

    def test_02_isolated_import_defect(self):
        p=self.w/'a';p.mkdir();(p/'read_filter.py').write_text('VALUE=3\n')
        bad=p/'worker.py';bad.write_text('import read_filter\nfrom pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).parent))\n')
        with self.assertRaises(P.GateError):
            Q.isolated_entry(CPU,bad,[],self.w,self.w/'bad.log')
        self.assertIn('ModuleNotFoundError',(self.w/'bad.log').read_text())
        bad.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).parent))\nimport read_filter\n')
        Q.isolated_entry(CPU,bad,[],self.w,self.w/'good.log')

    def test_03_fill_drops_environment_archive_defect(self):
        package,cfg=fill_fixture(self.w,drop_env=True)
        base,filled=execute_fixture_fill(package,cfg)
        with self.assertRaisesRegex(P.GateError,'append|env'):
            P.preserved(base,filled,P.file_sha(package/'a/6'))

    def test_03b_exact_fill_preserves_env_control(self):
        package,cfg=fill_fixture(self.w)
        base,filled=execute_fixture_fill(package,cfg)
        P.preserved(base,filled,P.file_sha(package/'a/6'))
        self.assertEqual(filled['archives'][4],base['archives'][4])
        self.assertEqual(len(filled['archives']),len(base['archives'])+1)

    def test_F06_real_rows_nonzero_and_null_through_logic_probe(self):
        P.probe(CPU,'logic',ROUTE/'B5/package',self.w/'good',{'python':CPU})
        self.assertGreater(P.read(self.w/'good/result.json')['rows_checked'],0)
        for field,suffix in (('total_num_frames','R0_QUESTIONS_dev_f32.jsonl'),
                             ('fps','/r3/TASKS.jsonl')):
            package=copy_package(self.w/field)
            pay=P.unpack((package/'0.tgz').read_bytes())
            name=next(n for n in pay if n.endswith(suffix))
            lines=pay[name].decode().splitlines();row=json.loads(lines[0]);row[field]=None
            lines[0]=json.dumps(row);pay[name]=('\n'.join(lines)+'\n').encode()
            repin_payload(package,pay)
            with self.assertRaises(P.GateError):P.probe(CPU,'logic',package,self.w/(field+'bad'),{'python':CPU})
            self.assertIn(field,(self.w/(field+'bad/probe.log')).read_text())

    def test_F06_zero_rows_fail_closed(self):
        package=copy_package(self.w/'p');pay=P.unpack((package/'0.tgz').read_bytes())
        for n in list(pay):
            if n.endswith(('.json','.jsonl')) and n!='9.json':
                # Preserve non-row metadata; remove only actual row sources.
                try:
                    values=[json.loads(l) for l in pay[n].decode().splitlines() if l.strip()] if n.endswith('.jsonl') else [json.loads(pay[n])]
                    if any(list(Q.rows_in(v)) for v in values):pay[n]=b'' if n.endswith('.jsonl') else b'[]'
                except ValueError:pass
        repin_payload(package,pay)
        with self.assertRaises(P.GateError):P.probe(CPU,'logic',package,self.w/'bad',{'python':CPU})
        self.assertIn('zero rows',(self.w/'bad/probe.log').read_text())

    def test_F09_import_order_through_logic_probe(self):
        package=copy_package(self.w/'p');pay=P.unpack((package/'0.tgz').read_bytes())
        pay['z/read_filter.py']=b'VALUE=3\n'
        pay['z/worker.py']=b'import read_filter\nfrom pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).parent))\n'
        repin_payload(package,pay)
        with self.assertRaises(P.GateError):P.probe(CPU,'logic',package,self.w/'bad',{'python':CPU})
        logs=list((self.w/'bad').glob('import*.log'))
        self.assertTrue(any('ModuleNotFoundError' in p.read_text() for p in logs))
        pay['z/worker.py']=b'from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).parent))\nimport read_filter\n'
        repin_payload(package,pay)
        P.probe(CPU,'logic',package,self.w/'good',{'python':CPU})

    def test_F09_dropped_env_through_real_python36_fill_probe(self):
        package,cfg=fill_fixture(self.w,drop_env=True)
        with self.assertRaises(P.GateError):P.probe(CPU,'fill',package,self.w/'bad',cfg)
        text=(self.w/'bad/probe.log').read_text()
        self.assertIn('Fill must append preparation archive',text)
        self.assertNotIn('Traceback (most recent call last):\n  File',text.split('Fill must append')[1])

    def test_04_stale_bundle_descriptor_defect(self):
        p=copy_package(self.w/'p');f=(p/'BATCH.sh').read_text();bm=P.bundle(f.encode())
        pub=json.loads(bm['0.json']);pub['token']='a01234567890';bm['0.json']=json.dumps(pub).encode()
        line=next(l for l in f.splitlines() if l.startswith('b=bytes.fromhex('))
        (p/'BATCH.sh').write_text(f.replace(line,'b=bytes.fromhex(%r)'%tarbytes(bm,True).hex()))
        reseal(p,update_bundle=False)
        with self.assertRaisesRegex(P.GateError,'Bundle descriptor differs'):P.structure(p)

    def test_05_silent_early_batch_failure_defect(self):
        batch=(ROUTE/'B5/package/BATCH.sh').read_text()
        result=Q.trap_probe(batch,ROUTE/'B5/package',self.w/'good')
        self.assertTrue(result['passed'])
        with self.assertRaisesRegex(P.GateError,'EXIT trap'):
            Q.trap_probe(batch.replace('trap fin EXIT','true'),ROUTE/'B5/package',self.w/'bad')

    def test_06_usr1_without_end_slot_defect(self):
        batch=(ROUTE/'B5/package/BATCH.sh').read_text()
        with self.assertRaisesRegex(P.GateError,'USR1 did not drain'):
            Q.trap_probe(batch,ROUTE/'B5/package',self.w/'bad',ignore_signal=True)
        with self.assertRaisesRegex(P.GateError,'USR1 did not drain'):
            Q.trap_probe(batch.replace("trap 'kill -USR1 $PID 2>/dev/null' USR1",
                                     "trap ':' USR1"),ROUTE/'B5/package',self.w/'noforward')

    def test_06b_native_runner_stop_handler_defect(self):
        P.probe(CPU,'stop',ROUTE/'B5/package',self.w/'good',{'python':CPU})
        package=copy_package(self.w/'p');pay=P.unpack((package/'0.tgz').read_bytes())
        n='orchard_h10/runner.py';old=b"marker.write_text(str(number)+'\\n')"
        self.assertEqual(pay[n].count(old),1)
        pay[n]=pay[n].replace(old,b"pass  # planted ignored stop")
        plan=json.loads(pay['9.json']);plan['payload_pins'][n]=dict(bytes=len(pay[n]),sha256=P.sha(pay[n]))
        pay['9.json']=json.dumps(plan,sort_keys=True).encode()
        (package/'0.tgz').write_bytes(tarbytes(pay,True));reseal(package)
        with self.assertRaises(P.GateError):P.probe(CPU,'stop',package,self.w/'bad',{'python':CPU})
        logs=list((self.w/'bad').glob('stop.log'))
        self.assertTrue(logs)
        self.assertIn('stop/end proof failed',logs[0].read_text())

    def test_F01_name_argv_env_and_stale_identity_boundaries(self):
        public={'token':'a01234567890'}
        P.privacy({'0.txt':b'dataset same sample shutdown split'},{},public)
        for name,raw in [('model.txt',b'ok'),('0.sh',b'python3 /tmp/dataset.py'),
                         ('0.sh',b'export V=benchmark'),('0.sh',b'#SBATCH --comment=model'),
                         ('0.sh',b'env MODEL=x true'),('0.sh',b'python3 --x qwen')]:
            with self.subTest(name=name,raw=raw):
                with self.assertRaises(P.GateError):P.privacy({name:raw},{},public)
        # Archive names and bytes remain private; stale identities do not.
        archive=tarbytes({'model.py':b'# dataset old123'},True)
        P.privacy({'0.tgz':archive},{},public)
        with self.assertRaisesRegex(P.GateError,'Stale identity'):
            P.privacy({'0.tgz':archive},{},public,extra=['old123'])
        p=copy_package(self.w/'p');batch=(p/'BATCH.sh').read_bytes()
        bm=P.bundle(batch);bm['0.py']+=b'\n# old456\n'
        line=next(l for l in batch.decode().splitlines() if l.startswith('b=bytes.fromhex('))
        batch=batch.decode().replace(line,'b=bytes.fromhex(%r)'%tarbytes(bm,True).hex()).encode()
        with self.assertRaisesRegex(P.GateError,'Stale identity'):
            P.privacy({'BATCH.sh':batch},{},P.read(p/'0.json'),extra=['old456'])
        for tok in ('camera','123456789abc','a1;echo bad','a01234567890\n'):
            with self.assertRaises(P.GateError):P.token(tok)
        with self.assertRaises(P.GateError):
            P.privacy({'customstudy.txt':b'ok'},{},public,forbidden_extra=['customstudy'])

    def test_symlink_duplicate_and_traversal_archives(self):
        for name in ('../bad','/tmp/bad','a/../b','./a'):
            with self.assertRaises(P.GateError):P.unpack(tarbytes({name:b'x'}))
        b=io.BytesIO()
        with tarfile.open(fileobj=b,mode='w') as t:
            m=tarfile.TarInfo('0');m.type=tarfile.SYMTYPE;m.linkname='/tmp/a';t.addfile(m)
        with self.assertRaises(P.GateError):P.unpack(b.getvalue())
        b=io.BytesIO()
        with tarfile.open(fileobj=b,mode='w') as t:
            for _ in range(2):
                m=tarfile.TarInfo('0');m.size=1;t.addfile(m,io.BytesIO(b'x'))
        with self.assertRaises(P.GateError):P.unpack(b.getvalue())

    def test_default_off_and_fail_fast_all_never_transports(self):
        cfg=self.w/'c.json';P.write(cfg,{'workspace':str(self.w)})
        with self.assertRaisesRegex(P.GateError,'Disabled'):
            P.main(['build','--config',str(cfg)])
        with patch.object(P,'build',return_value={}),patch.object(P,'built',return_value={'package':'x'}), \
             patch.object(P,'local_check',side_effect=P.GateError('planted')), \
             patch.object(P,'stage_remote') as transport:
            with self.assertRaisesRegex(P.GateError,'planted'):
                P.main(['all','--enable','--config',str(cfg)])
            transport.assert_not_called()
        with patch.object(P,'run',return_value={}) as local:
            P.probe(CPU,'fill',Path('a'),self.w/'timer',{'fill_timeout_seconds':3600})
            self.assertEqual(local.call_args.kwargs['timeout'],3600)
        for value in (0,-1,7201,True):
            with self.assertRaises(P.GateError):
                P.probe(CPU,'fill',Path('a'),self.w/'timer',{'fill_timeout_seconds':value})

    def test_submission_authorization_and_remote_script_syntax(self):
        # Planning cannot accidentally call ossh. Operational scripts retain
        # native receipt/queue gates; the strict outbound scan rejects their
        # descriptive literals rather than weakening the user's policy.
        p=ROUTE/'B5/package';tok=P.read(p/'0.json')['token']
        raw=tarbytes(P.package_files(p),True);delivery=self.w/'d.tgz';delivery.write_bytes(raw)
        b=dict(package=str(p),delivery=str(delivery),report={'token':tok})
        cfg=dict(workspace=str(self.w),remote=dict(root=P.REMOTE_ROOT,
            walltime='04:00:00',ossh='/unavailable/ossh.sh',
            cpu_script=dict(path=str(DB/'o_cpu_D.sh'),sha256=P.file_sha(DB/'o_cpu_D.sh')),
            submit_script=dict(path=str(DB/'o_sub_D.sh'),sha256=P.file_sha(DB/'o_sub_D.sh'))))
        from types import SimpleNamespace
        args=SimpleNamespace(yes=False,token=None,execute_remote=False)
        with patch.object(P,'checked',return_value=b):
            with self.assertRaisesRegex(P.GateError,'explicit --token'):
                P.stage_remote('submit',cfg,args)
            args.yes=True;args.token='a01234567890'
            with self.assertRaises(P.GateError):P.stage_remote('submit',cfg,args)
        scripts={'place':P.remote_place(cfg,b),'submit':P.remote_submit(cfg,b)}
        package,fillcfg=fill_fixture(self.w)
        fillcfg['remote'].update(cfg['remote'])
        scripts['fill']=P.remote_fill(fillcfg,b)
        for n,text in scripts.items():
            path=self.w/(n+'.sh');path.write_text(text)
            r=subprocess.run(['nice','-n','10','bash','-n',str(path)],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertEqual(r.returncode,0,r.stderr.decode())
            P.shell_surfaces(text,'outbound '+n)
        self.assertIn('sacct',scripts['submit']);self.assertIn('CPU.json',scripts['submit'])
        self.assertIn('squeue',scripts['submit']);self.assertNotIn('sleep 60',scripts['submit'])

    def test_all_plans_every_phase_before_any_remote_execution(self):
        cfg=self.w/'c.json';P.write(cfg,{'workspace':str(self.w)})
        events=[]
        def plan(action,c,args,plan_only=False):
            self.assertTrue(plan_only);events.append('plan '+action)
            p=self.w/(action+'.sh');p.write_text('true\n');return p
        def execute(action,*args):events.append('execute '+action)
        args=['all','--enable','--yes','--execute-remote','--token','a0123456789ab','--config',str(cfg)]
        with patch.object(P,'build',return_value={}),patch.object(P,'built',return_value={'package':'x'}), \
             patch.object(P,'local_check',return_value={}),patch.object(P,'stage_remote',side_effect=plan), \
             patch.object(P,'run_remote',side_effect=execute):P.main(args)
        self.assertEqual(events,['plan place','plan fill','plan submit',
                                 'execute place','execute fill','execute submit'])
        events.clear()
        def bad_plan(action,c,args,plan_only=False):
            if action=='submit':raise P.GateError('planted operational privacy failure')
            return plan(action,c,args,plan_only)
        with patch.object(P,'build',return_value={}),patch.object(P,'built',return_value={'package':'x'}), \
             patch.object(P,'local_check',return_value={}),patch.object(P,'stage_remote',side_effect=bad_plan), \
             patch.object(P,'run_remote') as remote:
            with self.assertRaisesRegex(P.GateError,'operational privacy'):
                P.main(args)
            remote.assert_not_called()

    def test_F02_real_submit_preflight_fails_before_place(self):
        package,cfg=fill_fixture(self.w)
        tok=P.read(package/'0.json')['token'];delivery=self.w/'1.tgz'
        delivery.write_bytes(tarbytes(P.package_files(package),True))
        b=dict(package=str(package),delivery=str(delivery),report={'token':tok})
        cfg.update(workspace=str(self.w))
        cfg['remote'].update(ossh='/unavailable/ossh.sh',
            cpu_script=dict(path=str(DB/'o_cpu_D.sh'),sha256=P.file_sha(DB/'o_cpu_D.sh')),
            submit_script=dict(path=str(DB/'o_sub_D.sh'),sha256='0'*64))
        path=self.w/'cfg.json';P.write(path,cfg)
        with patch.object(P,'build',return_value=b),patch.object(P,'built',return_value=b), \
             patch.object(P,'checked',return_value=b),patch.object(P,'local_check',return_value={}), \
             patch.object(P,'run_remote') as remote:
            with self.assertRaisesRegex(P.GateError,'Remote script source hash differs: submit_script'):
                P.main(['all','--enable','--yes','--execute-remote','--token',tok,'--config',str(path)])
            remote.assert_not_called()

    def test_F01_containment_and_login_environment(self):
        package=copy_package(self.w/'p');P.containment(package)
        (package/'a/4.py').chmod(0o644)
        with self.assertRaisesRegex(P.GateError,'0600'):P.containment(package)
        path=self.w/'0.sh';path.write_text(P.shell_header())
        env=dict(os.environ,OPAQUE='dataset')
        r=subprocess.run(['bash',str(path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
        self.assertNotEqual(r.returncode,0);self.assertIn(b'Non-opaque environment: OPAQUE',r.stderr)

    def test_transport_stream_with_local_copy_stub_and_no_retry(self):
        # This stub only copies stdin into this test folder. It never calls SSH.
        tok='a0123456789ab';received=self.w/'0.received';stub=self.w/'0.sh'
        stub.write_text('set -euo pipefail\ncat > '+P.shlex.quote(str(received))+"\necho LOCAL_STUB_OK\n")
        script=self.w/'1.sh';script.write_text('true\n')
        c={'workspace':str(self.w),'remote':{'root':P.REMOTE_ROOT,'walltime':'04:00:00','ossh':str(stub)}}
        from types import SimpleNamespace
        args=SimpleNamespace(yes=True,token=tok,execute_remote=True)
        from contextlib import redirect_stdout
        capture=io.StringIO()
        dry=SimpleNamespace(yes=True,token=tok,execute_remote=False)
        with patch.object(P,'checked',return_value={'report':{'token':tok}}), \
             patch.object(P,'remote_place',return_value='true\n'),redirect_stdout(capture):
            P.stage_remote('place',c,dry)
        self.assertIn('set -o pipefail; pv -q -L 8000000 ',capture.getvalue())
        self.assertIn('| timeout 300 bash ',capture.getvalue())
        with patch.object(P,'checked',return_value={'report':{'token':tok}}):
            with self.assertRaisesRegex(P.GateError,'Planned remote script changed'):
                P.run_remote('place',c,args,script,'0'*64)
            self.assertFalse(received.exists())
            P.run_remote('place',c,args,script,P.file_sha(script))
            self.assertEqual(received.read_bytes(),script.read_bytes())
            self.assertIn('LOCAL_STUB_OK',(self.w/'place_remote.log').read_text())
            with self.assertRaisesRegex(P.GateError,'already attempted'):
                P.run_remote('place',c,args,script,P.file_sha(script))

    def test_F03_short_calls_and_F10_accounting_error_budget(self):
        from types import SimpleNamespace
        args=SimpleNamespace(yes=True,token='a0123456789ab',execute_remote=True)
        manifest={}
        for phase in ('cpu','poll','gpu'):
            p=self.w/(phase+'.sh');p.write_text('true\n')
            manifest[phase]=dict(path=str(p),sha256=P.file_sha(p))
        script=self.w/'submit.json';P.write(script,manifest)
        cfg=dict(workspace=str(self.w),remote=dict(walltime='04:00:00',ossh='/unavailable'))
        calls=[]
        def reply(action,*unused):
            calls.append(action)
            if 'poll' not in action:return ''
            return ['PACK_CPU_RETRY\n','PACK_CPU_WAIT 1 RUNNING\n','PACK_CPU_READY\n'][sum('poll' in x for x in calls)-1]
        with patch.object(P,'checked',return_value={'report':{'token':args.token}}), \
             patch.object(P,'remote_call',side_effect=reply),patch.object(P.time,'sleep') as sleep:
            P.run_remote('submit',cfg,args,script,P.file_sha(script))
        self.assertEqual(calls,['submit_cpu','submit_poll_0001','submit_poll_0002','submit_poll_0003','submit_gpu'])
        self.assertEqual([c.args for c in sleep.call_args_list],[(60,)]*4)
        self.assertEqual(P.transport_command(cfg)[:2],['timeout','300'])
        cfg['remote']['timeout_seconds']=301
        with self.assertRaises(P.GateError):P.transport_command(cfg)
        cfg['remote'].pop('timeout_seconds');other=self.w/'other';other.mkdir();cfg['workspace']=str(other)
        def broken(action,*unused):return 'PACK_CPU_RETRY\n'
        with patch.object(P,'checked',return_value={'report':{'token':args.token}}), \
             patch.object(P,'remote_call',side_effect=broken) as call,patch.object(P.time,'sleep'):
            with self.assertRaisesRegex(P.GateError,'Three consecutive sacct errors'):
                P.run_remote('submit',cfg,args,script,P.file_sha(script))
            self.assertFalse(any(c.args[0]=='submit_gpu' for c in call.call_args_list))
        expired=self.w/'expired';expired.mkdir();cfg['workspace']=str(expired)
        with patch.object(P,'checked',return_value={'report':{'token':args.token}}), \
             patch.object(P,'remote_call',return_value='PACK_CPU_WAIT 1 RUNNING\n') as call, \
             patch.object(P.time,'sleep'),patch.object(P.time,'monotonic',side_effect=[0,1,14401]):
            with self.assertRaisesRegex(P.GateError,'CPU wait expired'):
                P.run_remote('submit',cfg,args,script,P.file_sha(script))
            self.assertFalse(any(c.args[0]=='submit_gpu' for c in call.call_args_list))

    def test_F10_all_nonrunning_states_stop_with_diagnostics(self):
        b={'report':{'token':'a0123456789ab'}}
        cfg={'remote':{'walltime':'04:00:00',
            'cpu_script':dict(path=str(DB/'o_cpu_D.sh'),sha256=P.file_sha(DB/'o_cpu_D.sh')),
            'submit_script':dict(path=str(DB/'o_sub_D.sh'),sha256=P.file_sha(DB/'o_sub_D.sh'))}}
        local=self.w/(P.PREFIX+b['report']['token']);(local/'a/c').mkdir(parents=True)
        (local/'a/4.txt').write_text('123\n');(local/'a/4.err').write_text('CPU_FIXTURE_DIAGNOSTIC\n')
        (local/'a/c/CPU.json').write_text('{}')
        script=self.w/'poll.sh'
        text=P.remote_submit(cfg,b,'poll').replace(P.REMOTE_ROOT+'/'+P.PREFIX+b['report']['token'],str(local))
        script.write_text(text);stub=self.w/'sacct'
        env=dict(os.environ,PATH=str(self.w)+':'+os.environ['PATH'])
        for state in ('BOOT_FAIL','DEADLINE','REVOKED','UNKNOWN','FAILED','CANCELLED+','PENDING','RUNNING','CONFIGURING','COMPLETING','COMPLETED'):
            stub.write_text('#!/bin/bash\necho '+state+'\n');stub.chmod(0o700)
            r=subprocess.run(['bash',str(script)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            running=state in ('PENDING','RUNNING','CONFIGURING','COMPLETING')
            self.assertEqual(r.returncode==0,running or state=='COMPLETED',state)
            if r.returncode:self.assertIn(b'CPU_FIXTURE_DIAGNOSTIC',r.stderr)
        stub.write_text('#!/bin/bash\necho ACCOUNTING_UNAVAILABLE >&2\nexit 1\n')
        r=subprocess.run(['bash',str(script)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
        self.assertEqual(r.returncode,0);self.assertIn(b'PACK_CPU_RETRY',r.stdout)
        self.assertIn(b'ACCOUNTING_UNAVAILABLE',r.stderr)

    def test_F11_custom_terms_cover_remote_path_and_fill_argv(self):
        b={'report':{'token':'a0123456789ab'}}
        cfg={'remote':{'walltime':'04:00:00'},'forbidden_extra':['okh7']}
        with self.assertRaisesRegex(P.GateError,'remote package path'):P.remote_settings(cfg,b)
        package,cfg=fill_fixture(self.w);cfg['forbidden_extra']=['sft']
        with self.assertRaisesRegex(P.GateError,'fill argv'):P.remote_fill(cfg,b)

    def test_F13_ledger_reuse_rejected_before_builder(self):
        ledger=self.w/'ledger.jsonl';ledger.write_text('{"job":"a15_cot_apa0123456789ab"}\n')
        cfg={'workspace':str(self.w),'token_ledger':dict(path=str(ledger),sha256=P.file_sha(ledger)),
             'builder':{'path':str(DB/'build_d.py')}}
        with patch.object(P,'run') as builder:
            with self.assertRaisesRegex(P.GateError,'Trinity ledger'):P.build(cfg,'a0123456789ab')
            builder.assert_not_called()
        cfg['token_ledger']['sha256']='0'*64
        with self.assertRaisesRegex(P.GateError,'ledger SHA'):P.build(cfg,'b0123456789ab')

    def test_fixed_token_operational_adapter_is_explicit(self):
        root=MIRROR/'cont_ops17/work';pub=P.read(ROUTE/'A4/package/0.json')
        b={'report':{'token':pub['token']}}
        cfg={'remote':{'walltime':'05:00:00','root':P.REMOTE_ROOT}}
        for key,name in (('cpu_script','o_cpu_B4.sh'),('submit_script','o_sub_A4.sh')):
            path=root/name
            cfg['remote'][key]={'path':str(path),'sha256':P.file_sha(path)}
            self.assertEqual(P.sealed_script(cfg,key),path.read_text())
        with self.assertRaisesRegex(P.GateError,'parameterized'):
            P.remote_submit(cfg,b)
        for key in ('cpu_script','submit_script'):cfg['remote'][key]['parameterize']=True
        text=P.remote_submit(cfg,b,'cpu')+P.remote_submit(cfg,b)
        self.assertNotIn('d50ba921ef1f4',text)
        self.assertIn('test "${P:?}" = '+P.REMOTE_ROOT+'/'+P.PREFIX+pub['token'],text)
        self.assertIn('--time "$T"',text)
        self.assertIn('--time=04:00:00',text)
        self.assertIn('All CPU receipt checks passed',text)
        path=self.w/'a.sh';path.write_text(text)
        r=subprocess.run(['nice','-n','10','bash','-n',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertEqual(r.returncode,0,r.stderr.decode())

    def test_real_native_metadata_guard_and_logic(self):
        for mode in ('metadata','guard','logic'):
            P.probe(CPU,mode,ROUTE/'B5/package',self.w/mode,{'python':CPU})

    def test_F01_supplied_packages_pass_name_privacy(self):
        for name in ('A4','B5'):
            f,p,pub,plan=P.structure(ROUTE/name/'package')
            self.assertGreater(P.privacy(f,p,pub)['surfaces_checked'],0)

    def test_F08_real_python36_login_runtime(self):
        import warnings,re
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            self.assertRegex(P.utc(),r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
        P.probe(CPU,'login',ROUTE/'B5/package',self.w/'login',{'python':CPU})
        result=P.read(self.w/'login/result.json')
        self.assertIn('3.6.8',result['python'])
        self.assertTrue(result['generated_place_executed'])
        for n in ('pack.py','pack_probes.py'):
            r=subprocess.run(['/usr/bin/python3','-I','-s','-B','-c',
                'import sys;compile(open(sys.argv[1],"rb").read(),sys.argv[1],"exec")',str(HERE/n)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertEqual(r.returncode,0,r.stderr.decode())
        fixture=self.w/'fixture';fixture.mkdir();package,cfg=fill_fixture(fixture)
        # Tiny archive metadata exercises login APIs; dependency resolution is
        # deliberately separate and is never granted by this fixture.
        base=P.read(package/'a/0.json');tiny=fixture/'0';tiny.write_bytes(b'x')
        for archive in base['archives'][1:]:
            for pin in archive['parts']:
                cfg['mirrors'][pin['path']]=dict(local=str(tiny),bytes=1,sha256=P.file_sha(tiny))
                pin.update(bytes=1,sha256=P.file_sha(tiny))
        P.write(package/'a/0.json',base);reseal(package)
        P.write(fixture/'cfg.json',cfg)
        code=('import sys,runpy,json;from pathlib import Path;'
              'sys.path.insert(0,'+repr(str(HERE))+');import pack as P,pack_probes as Q;'
              'ns=runpy.run_path('+repr(str(HERE/'test_pack.py'))+');'
              'p=Path('+repr(str(package))+');c=P.read('+repr(str(fixture/'cfg.json'))+');'
              'ns["execute_fixture_fill"](p,c);'
              'remote=P.REMOTE_ROOT+"/"+P.PREFIX+P.read(p/"0.json")["token"];'
              'sys.argv=[remote+"/3.py","check","--gpus","1","--time","02:30:00"];'
              '\nwith Q.Mirrors(c["mirrors"],remote,p):runpy.run_path(remote+"/3.py",run_name="__main__")\n'
              'assert P.read(p/"2.json")["passed"] is True\nprint("REAL_36_FILL_AND_PUBLIC_CHECK_PASS",sys.version)')
        P.run(['/usr/bin/python3','-I','-s','-B','-c',code],fixture,fixture/'runtime.log')
        self.assertIn('REAL_36_FILL_AND_PUBLIC_CHECK_PASS',(fixture/'runtime.log').read_text())

    def test_mirror_hashes_and_write_refusal(self):
        f=self.w/'0';f.write_bytes(b'abc')
        mirrors={'/project/0':dict(local=str(f),bytes=3,sha256=P.file_sha(f))}
        self.assertEqual(P.validate_mirrors(mirrors,100),3)
        with Q.Mirrors(mirrors,'/project/a',self.w/'a'):
            self.assertEqual(Path('/project/0').read_bytes(),b'abc')
            with self.assertRaises(P.GateError):Path('/project/0').write_bytes(b'no')
        mirrors['/project/0']['sha256']='0'*64
        with self.assertRaises(P.GateError):P.validate_mirrors(mirrors,100)

    def test_local_receipt_rejects_a_changed_checker(self):
        P.write(self.w/'checks/CHECK.json',{'schema':'so_pack-local-v1','passed':True,
                                         'checker_sha256':{'pack.py':'0'*64}})
        with patch.object(P,'built',return_value={'package':'not-needed'}):
            with self.assertRaisesRegex(P.GateError,'Checker source changed'):
                P.checked({'workspace':str(self.w)})

    def test_existing_D_builder_is_called_and_preserved(self):
        sys.path.insert(0,str(DB));from build_support import write_tar
        source=self.w/'source.tgz';parts=[];b5=ROUTE/'B5/package'
        names=['0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json','PACKAGE.json','SUBMIT.cmd',
               'a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json']
        for n in names:
            m=tarfile.TarInfo(n);m.mode=(b5/n).stat().st_mode&0o777;parts.append((m,(b5/n).read_bytes()))
        source.write_bytes(write_tar(parts));stage=self.w/'stage'
        cfg=dict(workspace=str(self.w),python=CPU,token_ledger=empty_ledger(self.w),builder=dict(path=str(DB/'build_d.py'),
            sha256=P.file_sha(DB/'build_d.py'),args=[str(stage),str(source),P.file_sha(source),
            str(DB/'evidence/items/dist580.json'),str(DB/'bind_D200.json'),
            '--timing',str(DB/'TIMING_D.json')],report=str(stage/'BUILD.json'),key='D',
            env={'KROOT':str(self.w/'k')}))
        before={n:P.file_sha(DB/n) for n in ('build_d.py','build_support.py','make_items_d.py')}
        b=P.build(cfg);P.structure(b['package'])
        self.assertEqual(before,{n:P.file_sha(DB/n) for n in before})
        self.assertEqual(b['report']['export_binding']['step'],200)
        checkcfg=dict(cfg,remote={'walltime':'04:00:00'})
        P.probe(CPU,'metadata',b['package'],self.w/'d_metadata',checkcfg)
        P.probe(CPU,'logic',b['package'],self.w/'d_logic',checkcfg)
        P.write(ROOT/'D_BUILD_CONFIG.json',cfg);P.write(ROOT/'D_BUILD_STATE.json',b)


def main():
    global ROOT
    P.limit_resources();os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
    ROOT=Path(a.work).resolve();P.require(P.inside(ROOT,'/scratch/jjyeung/orch_n30/so_pack'),
                                         'Test writes must stay under so_pack')
    ROOT.mkdir(parents=True,exist_ok=False)
    env=P.clean_env(ROOT);os.environ.clear();os.environ.update(env)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PackTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    P.write(ROOT/'RESULTS.json',dict(passed=result.wasSuccessful(),tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),utc=P.utc(),
        planted_defects=['null frame metadata','isolated import','env archive overwrite',
                         'stale bundle descriptor','silent early batch failure','USR1 without end slot'],
        scope='native packaging helpers plus synthetic export and cooperative signal fixtures'))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
