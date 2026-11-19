"""Defect-level before/after evidence; remote snippets run locally under 3.6.8."""
import copy, io, json, os, subprocess, sys, tarfile, time, unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
sys.path.insert(0,os.environ.get('PACK_SOURCE',str(Path(__file__).parent)))
import pack as P
import test_support as T

class Review3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['PACK_R3_WORK']);cls.root.mkdir()
        fixture=Path(os.environ['PACK_R3_FIXTURE']);cls.p=fixture/'p';cls.config=P.read(fixture/'config.json')
        cls.f=P.package_files(cls.p);cls.d=fixture/'1.tgz';cls.plan=P.structure(cls.p)[3]
        cls.b=dict(token=P.read(cls.p/'0.json')['token'],package=str(cls.p),delivery=str(cls.d),sha256=P.file_digest(cls.d),tree=P.fingerprint(cls.f))
    def setUp(self):
        self.w=self.root/self._testMethodName;self.w.mkdir();self.c=copy.deepcopy(self.config)
        self.c.update(work=str(self.w/'state'),ledger=str(self.w/'ledger'));Path(self.c['ledger']).write_text(self.b['token']+'\n')
        self.mapping={k:v['path'] for k,v in self.c['mirrors'].items()}
        self.remote=self.w/'r';self.mapping[P.remote_path(self.b)]=str(self.remote)
    def snippet(self,code,label):
        driver=self.w/(label+'.py');driver.write_text('import sys\nsys.path.insert(0,%r)\nimport pack_checks as Q\nwith Q.Mirrors(%r):exec(compile(%r,"remote","exec"),{})\n'%(str(Path(P.__file__).parent),self.mapping,code))
        return subprocess.run(['/usr/bin/python3','-I','-s','-B',str(driver)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(self.w))
    def receipt(self):
        (self.remote/'v').mkdir(parents=True,exist_ok=True,mode=0o700);self.remote.chmod(0o700)
        rows=[]
        for name in self.c['fill']['parts']:
            p=Path(self.mapping[name]);s=p.stat()
            rows.append(dict(path=name,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino,sha256=P.file_digest(p)))
        P.write(self.remote/'v/0.json',dict(schema=1,parts=rows));(self.remote/'v/0.txt').write_text('0\n')
    def preflight(self):return P.heredocs(P.remote_preflight(self.c,self.b))[0]
    def refuse_before_place(self,needle=None):
        code=self.preflight();calls=[]
        def call(phase):
            calls.append(phase)
            if phase=='preflight':return self.snippet(code,'preflight')
            (P.state_root(self.c)/'place.attempt').write_text('spent');return subprocess.CompletedProcess([],0,b'',b'')
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaisesRegex(P.Rejected,'before placement') as error:P.execute(self.c,{},['place'],True,self.b['token'],call=call)
        if needle:self.assertIn(needle,str(error.exception))
        self.assertEqual(calls,['preflight']);self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_01_base_path_conflicting_sha(self):
        f=dict(self.f);base=json.loads(f['a/0.json']);base['archives'][0]['parts'][0].update(path=self.c['fill']['parts'][0],sha256='0'*64)
        f['a/0.json']=T.jd(base)
        with self.assertRaisesRegex(P.Rejected,'conflicting base sha256'):P.export_identity(self.c,f,self.plan)
    def test_01_missing_part_sha(self):
        plan=copy.deepcopy(self.plan);plan['export_binding']['parts'][0].pop('sha256')
        with self.assertRaisesRegex(P.Rejected,r'parts\[\].sha256'):P.export_identity(self.c,self.f,plan)
    def test_01_missing_receipt_before_place(self):self.refuse_before_place()
    def test_01_same_size_wrong_part_before_place(self):
        name=self.c['fill']['parts'][1];raw=Path(self.mapping[name]).read_bytes();bad=self.w/'bad';bad.write_bytes(bytes([raw[0]^1])+raw[1:]);self.mapping[name]=str(bad)
        self.receipt();self.refuse_before_place('differs from binding')
    def test_01_stale_receipt_before_place(self):
        name=self.c['fill']['parts'][1];p=self.w/'part';p.write_bytes(Path(self.mapping[name]).read_bytes());self.mapping[name]=str(p)
        self.receipt();s=p.stat();os.utime(str(p),ns=(s.st_atime_ns,s.st_mtime_ns+1000000000));self.refuse_before_place('stale')
    def test_01_receipt_path_key_before_place(self):
        self.receipt();p=self.remote/'v/0.json';v=P.read(p);v['parts'][0]['path']+='.other';P.write(p,v);self.refuse_before_place('differs from binding')
    def test_01_wrong_step_tar_header_before_place(self):
        name=self.c['fill']['parts'][0];raw=Path(self.mapping[name]).read_bytes()
        member=tarfile.TarInfo.frombuf(raw[:512],'utf-8','strict');member.name=member.name.replace('m600','m544')
        p=self.w/'part';p.write_bytes(member.tobuf()+raw[512:]);self.assertEqual(p.stat().st_size,len(raw));self.mapping[name]=str(p);self.receipt()
        # Keep the receipt's expected SHA to isolate the independent header guard.
        v=P.read(self.remote/'v/0.json');v['parts'][0]['sha256']=self.plan['export_binding']['parts'][0]['sha256'];P.write(self.remote/'v/0.json',v)
        self.refuse_before_place('tar member differs')
    def test_01_detached_verify_and_place(self):
        scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No detached verify phase exists')
        self.assertIn('verify_poll',scripts);body=(Path(self.c['work'])/'commands/verify_body.sh').read_text()
        code=P.heredocs(body)[0];(self.remote/'v').mkdir(parents=True,mode=0o700);self.remote.chmod(0o700)
        good=self.snippet(code,'verify');self.assertEqual(good.returncode,0,good.stderr)
        receipt=P.read(self.remote/'v/0.json');self.assertEqual(len(receipt['parts']),4)
        for row,pin in zip(receipt['parts'],self.plan['export_binding']['parts']):self.assertEqual(row['sha256'],pin['sha256']);self.assertIn('mtime_ns',row)
        good=self.snippet(self.preflight(),'ready');self.assertEqual(good.returncode,0,good.stderr)
        placed=self.snippet(P.place_code(self.b),'place');self.assertEqual(placed.returncode,0,placed.stderr)
        self.assertTrue((self.remote/'0.json').is_file());self.assertTrue((self.remote/'v/0.json').is_file())
        again=self.snippet(P.place_code(self.b),'place_again');self.assertNotEqual(again.returncode,0)
        # Real detached shell, slow body, exclusive launch, private output containment.
        root=self.w/'slow';body='#!/bin/bash\nset -eu\numask 077\nsleep 1\nprintf "0\\n" >v/0.txt\n'
        launcher=P.detached_verify(body,str(root));script=self.w/'launch.sh';script.write_text(launcher)
        start=time.monotonic();r=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=.8)
        self.assertEqual(r.returncode,0,r.stderr);self.assertLess(time.monotonic()-start,.8)
        again=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1);self.assertNotEqual(again.returncode,0)
        time.sleep(1.1);self.assertEqual((root/'v/0.txt').read_text(),'0\n');self.assertEqual({x.name for x in root.iterdir()},{'v'})
        for p in root.rglob('*'):self.assertEqual(p.stat().st_mode & 0o777,0o700 if p.is_dir() else 0o600)
    def test_01_verify_hash_failure_no_receipt(self):
        scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No export hash verifier exists')
        name=self.c['fill']['parts'][2];p=self.w/'bad';raw=Path(self.mapping[name]).read_bytes();p.write_bytes(bytes([raw[0]^1])+raw[1:]);self.mapping[name]=str(p)
        (self.remote/'v').mkdir(parents=True,mode=0o700)
        code=P.heredocs((Path(self.c['work'])/'commands/verify_body.sh').read_text())[0]
        r=self.snippet(code,'verify');self.assertNotEqual(r.returncode,0);self.assertIn(b'sha256 differs',r.stderr)
        self.assertFalse((self.remote/'v/0.json').exists());self.assertFalse((self.remote/'v/0.txt').exists());self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_01_verify_without_ledger_and_polling(self):
        scripts=P.plan(self.c,self.b);self.assertIn('verify',scripts,'No token-independent verification exists')
        self.c['ledger']=str(self.w/'absent');calls=[];waits=[]
        def call(k):calls.append(k);return subprocess.CompletedProcess([],0,b'wait\n' if len(calls)==2 else b'complete\n',b'')
        with patch.object(P,'checked',return_value=self.b):P.execute(self.c,scripts,['verify'],True,self.b['token'],call=call,sleeper=waits.append)
        self.assertEqual(calls,['verify','verify_poll','verify_poll']);self.assertEqual(waits,[60,60]);self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_01_failed_verify_can_recheck_same_token(self):
        self.assertTrue(hasattr(P,'detached_verify'),'No token-independent verifier exists')
        root=self.w/'retry';first=self.w/'first.sh';second=self.w/'second.sh'
        first.write_text(P.detached_verify('#!/bin/bash\numask 077\nprintf "9\\n" >v/0.exit\nexit 9\n',str(root)))
        second.write_text(P.detached_verify('#!/bin/bash\numask 077\nsleep 1\nprintf "0\\n" >v/0.txt\n',str(root)))
        r=subprocess.run(['bash',str(first)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1);self.assertEqual(r.returncode,0,r.stderr)
        end=time.monotonic()+2
        while not (root/'v/0.exit').exists() and time.monotonic()<end:time.sleep(.02)
        self.assertEqual((root/'v/0.exit').read_text(),'9\n')
        r=subprocess.run(['bash',str(second)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1);self.assertEqual(r.returncode,0,r.stderr)
        again=subprocess.run(['bash',str(second)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1);self.assertNotEqual(again.returncode,0)
        time.sleep(1.1);self.assertEqual((root/'v/0.txt').read_text(),'0\n');self.assertFalse((root/'v/0.exit').exists())
        archives=[p for p in (root/'v').iterdir() if p.is_dir()];self.assertEqual(len(archives),1);self.assertEqual((archives[0]/'0.exit').read_text(),'9\n')
        self.assertEqual({p.name for p in root.iterdir()},{'v'});self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_02_shell_bypasses(self):
        for line in ('sbatch --comm=abc x','sbatch --comme abc','sbatch --job-na=other','sbatch -vJ other','SBATCH_JOB_NAME=other sbatch x','export SBATCH_COMMENT=abc','SLURM_X=abc sbatch x'):
            with self.subTest(line=line):
                with self.assertRaises(P.Rejected):P.shell_privacy(line)
    def test_02_submit_receipt_argv(self):
        for n,args in enumerate((['--comm=abc'],['-J','other'],['--job-na=other'])):
            f=dict(self.f);f['2.json']=T.jd(dict(argv=['sbatch','--job-name='+P.PREFIX+self.b['token']]+args));p=P.extract(f,self.w/str(n))
            with self.subTest(args=args):
                with self.assertRaises(P.Rejected):P.privacy(p,self.c)
    def test_02_native_submit_stub_argv(self):
        f=dict(self.f);pay=P.untar(f['0.tgz']);s=pay['orchard_h10/common.py'];self.assertIn(b"'--parsable'",s)
        pay['orchard_h10/common.py']=s.replace(b"'--parsable'",b"'--parsable', '--comm=abc'",1)
        p=P.extract(T.seal(f,pay),self.w/'p');w=self.w/'q'
        with self.assertRaises(P.Rejected):P.probe('fill',p,w,self.c)
        self.assertIn('Slurm --comment is forbidden',(w/'0.log').read_text())
    def test_03_native_forbidden_addition(self):
        pay=P.untar(self.f['0.tgz']);pay['orchard_h10/common.py']=pay['orchard_h10/common.py'].replace(b"FORBIDDEN = (",b"FORBIDDEN = ('zz_private_term',",1)
        p=P.extract(T.seal(self.f,pay),self.w/'p')
        with self.assertRaisesRegex(P.Rejected,'Native FORBIDDEN'):P.structure(p)
    def test_04_all_dependency_fields(self):
        import pack_structural as S
        base=P.read(self.p/'a/0.json')
        for key in ('python','frames_root','sam_source','policy','env_roots','policy_receipt','environment_receipt'):
            with self.subTest(key=key):
                changed=copy.deepcopy(base);changed[key]='wrong'
                with self.assertRaisesRegex(P.Rejected,'Dependency layout differs'):S.dependency_reference(changed,self.c)
    def test_05_every_remote_action_requires_yes(self):
        for phase in ('verify','place','fill'):
            for yes,tok in ((False,self.b['token']),(True,'a123456789ab')):
                with self.subTest(phase=phase,yes=yes):
                    with patch.object(P,'checked',return_value=self.b):
                        with self.assertRaisesRegex(P.Rejected,'--yes.*token'):P.execute(self.c,{},[phase],yes,tok,call=lambda k:subprocess.CompletedProcess([],0,b'complete\n',b''),sleeper=lambda n:None)
    def test_05_print_preflight_before_place(self):
        cfg=self.w/'c.json';P.write(cfg,self.c);out=io.StringIO()
        with patch.object(P,'checked',return_value=self.b),patch.object(P,'plan',return_value=dict(preflight='/tmp/preflight.sh',place='/tmp/place.sh')),redirect_stdout(out):P.main(['place','--enable','--config',str(cfg)])
        text=out.getvalue();self.assertIn('/tmp/preflight.sh',text);self.assertLess(text.index('/tmp/preflight.sh'),text.index('/tmp/place.sh'))
    def test_06_placeholder_identity(self):
        for old in ('REPLACE_SOURCE_TOKEN','REPLACE_SOURCE_PAYLOAD_SHA','REPLACE_SOURCE_PLAN_SHA','f'*65,'X'*12):
            with self.subTest(old=old):
                with self.assertRaisesRegex(P.Rejected,'Invalid old identity'):P.structure(self.p,dict(old_identities=[old]))
    def test_07_operator_docs(self):
        docs=Path(os.environ['PACK_DOCS']);note=(docs/'NOTE_FOR_CONT_OPS.md').read_text();orchard=(docs/'ORCHARD_ONLY_CHECKS.md').read_text()
        self.assertIn('parts[i].sha256',note);self.assertIn('pack.py verify',note)
        for word in ('a3.tar','10,240','05dc8f79','confirm header layout on the staged m544 part 0, read-only','Review round 3: finding -> fix -> test'):self.assertIn(word,orchard)
    def test_07_native_archive_documented(self):
        text=(Path(os.environ['PACK_DOCS'])/'ORCHARD_ONLY_CHECKS.md').read_text()
        for word in ('a3.tar','10,240','05dc8f79'):self.assertIn(word,text)
    def test_07_header_confirmation_documented(self):
        text=(Path(os.environ['PACK_DOCS'])/'ORCHARD_ONLY_CHECKS.md').read_text()
        self.assertIn('confirm header layout on the staged m544 part 0, read-only',text)

if __name__=='__main__':P.limits();unittest.main(verbosity=2)
