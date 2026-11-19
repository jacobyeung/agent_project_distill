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

    def test_every_privacy_surface_including_nested_bundle(self):
        public={'token':'a01234567890'}
        P.privacy({'0.txt':b'ok'},{},public)
        for name,raw in [('model.txt',b'ok'),('0.py',b'# dataset\n'),
                         ('0.json',b'{"PATH":"/tmp/qwen"}'),
                         ('0.sh',b'export V=benchmark'),('0.txt',b'/tmp/scannet')]:
            with self.subTest(name=name,raw=raw):
                with self.assertRaises(P.GateError):P.privacy({name:raw},{},public)
        bm={'0.py':b'# dataset','0.json':b'{}','7.py':b'pass'}
        batch=('b=bytes.fromhex(%r)\n'%tarbytes(bm,True).hex()).encode()
        with self.assertRaises(P.GateError):P.privacy({'BATCH.sh':batch},{},public)
        for tok in ('camera','123456789abc','a1;echo bad','a01234567890\n'):
            with self.assertRaises(P.GateError):P.token(tok)
        with self.assertRaises(P.GateError):
            P.privacy({'0.txt':b'customstudy'},{},public,forbidden_extra=['customstudy'])

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
            if n!='submit':P.opaque(text,'outbound '+n)
        with self.assertRaisesRegex(P.GateError,'Forbidden word'):
            P.opaque(scripts['submit'],'outbound submit')
        self.assertIn('sacct',scripts['submit']);self.assertIn('CPU.json',scripts['submit'])
        self.assertIn('squeue',scripts['submit']);self.assertIn('sleep 60',scripts['submit'])

    def test_real_native_metadata_guard_and_logic(self):
        for mode in ('metadata','guard','logic'):
            P.probe(CPU,mode,ROUTE/'B5/package',self.w/mode,{'python':CPU})

    def test_supplied_packages_are_not_privacy_releases(self):
        for name in ('A4','B5'):
            f,p,pub,plan=P.structure(ROUTE/name/'package')
            with self.assertRaises(P.GateError):P.privacy(f,p,pub)

    def test_python36_grammar(self):
        for n in ('pack.py','pack_probes.py'):
            ast.parse((HERE/n).read_text(),filename=n,feature_version=(3,6))

    def test_mirror_hashes_and_write_refusal(self):
        f=self.w/'0';f.write_bytes(b'abc')
        mirrors={'/project/0':dict(local=str(f),bytes=3,sha256=P.file_sha(f))}
        self.assertEqual(P.validate_mirrors(mirrors,100),3)
        with Q.Mirrors(mirrors,'/project/a',self.w/'a'):
            self.assertEqual(Path('/project/0').read_bytes(),b'abc')
            with self.assertRaises(P.GateError):Path('/project/0').write_bytes(b'no')
        mirrors['/project/0']['sha256']='0'*64
        with self.assertRaises(P.GateError):P.validate_mirrors(mirrors,100)

    def test_existing_D_builder_is_called_and_preserved(self):
        sys.path.insert(0,str(DB));from build_support import write_tar
        source=self.w/'source.tgz';parts=[];b5=ROUTE/'B5/package'
        names=['0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json','PACKAGE.json','SUBMIT.cmd',
               'a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json']
        for n in names:
            m=tarfile.TarInfo(n);m.mode=(b5/n).stat().st_mode&0o777;parts.append((m,(b5/n).read_bytes()))
        source.write_bytes(write_tar(parts));stage=self.w/'stage'
        cfg=dict(workspace=str(self.w),python=CPU,builder=dict(path=str(DB/'build_d.py'),
            sha256=P.file_sha(DB/'build_d.py'),args=[str(stage),str(source),P.file_sha(source),
            str(DB/'evidence/items/dist580.json'),str(DB/'bind_D200.json'),
            '--timing',str(DB/'TIMING_D.json')],report=str(stage/'BUILD.json'),key='D',
            env={'KROOT':str(self.w/'k')}))
        before={n:P.file_sha(DB/n) for n in ('build_d.py','build_support.py','make_items_d.py')}
        b=P.build(cfg);P.structure(b['package'])
        self.assertEqual(before,{n:P.file_sha(DB/n) for n in before})
        self.assertEqual(b['report']['export_binding']['step'],200)
        P.write(ROOT/'D_BUILD_CONFIG.json',cfg);P.write(ROOT/'D_BUILD_STATE.json',b)


def main():
    global ROOT
    P.limit_resources()
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args()
    ROOT=Path(a.work).resolve();P.require(str(ROOT).startswith(str(HERE.parent.resolve())+'/'),
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
