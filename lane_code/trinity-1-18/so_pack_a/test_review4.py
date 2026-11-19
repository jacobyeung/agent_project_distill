"""Round-4 defect regressions; generated remote code executes locally on Python 3.6.8."""
import copy, io, json, os, subprocess, sys, tarfile, time, unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ.get('PACK_SOURCE',str(Path(__file__).parent)))
import pack as P
import test_review3 as R3

class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['PACK_R4_WORK']);cls.root.mkdir(exist_ok=True)
        fixture=Path(os.environ['PACK_R4_FIXTURE']);cls.p=fixture/'p';cls.config=P.read(fixture/'config.json')
        cls.f=P.package_files(cls.p);cls.d=fixture/'1.tgz';cls.plan=P.structure(cls.p)[3]
        cls.b=dict(token=P.read(cls.p/'0.json')['token'],package=str(cls.p),delivery=str(cls.d),sha256=P.file_digest(cls.d),tree=P.fingerprint(cls.f))
    setUp=R3.Review3.setUp
    snippet=R3.Review3.snippet
    receipt=R3.Review3.receipt
    preflight=R3.Review3.preflight
    refuse_before_place=R3.Review3.refuse_before_place
    def local_parts(self):
        for index,name in enumerate(self.c['fill']['parts']):
            p=self.w/str(index);p.write_bytes(Path(self.mapping[name]).read_bytes());self.mapping[name]=str(p)
    def localize(self,text):
        for old,new in sorted(self.mapping.items(),key=lambda kv:-len(kv[0])):text=text.replace(old,new)
        return text
    def launch(self,label):
        # Placement bytes are unrelated to receipt recovery and are covered by test_review3.
        with patch.object(P,'place_code',return_value="raise AssertionError('not a placement test')"):
            scripts=P.plan(self.c,self.b)
        p=self.w/(label+'.sh');p.write_text(self.localize(Path(scripts['verify']).read_text()))
        r=subprocess.run(['nice','-n','10','bash',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(self.w),timeout=5)
        return r
    def wait_receipt(self):
        end=time.monotonic()+5
        while time.monotonic()<end:
            if (self.remote/'v/0.txt').exists() or (self.remote/'v/0.exit').exists():break
            time.sleep(.02)
        self.assertTrue((self.remote/'v/0.txt').is_file(),(self.remote/'v/0.log').read_text())
    def ready(self):
        code=self.localize(self.preflight());r=self.snippet(code,'ready')
        self.assertEqual(r.returncode,0,r.stderr);self.assertFalse((Path(self.c['work'])/'place.attempt').exists());self.assertFalse((self.remote/'a').exists())
    def verify(self):
        self.local_parts();r=self.launch('first');self.assertEqual(r.returncode,0,r.stderr);self.wait_receipt();self.ready()

class Review4(Base):
    def test_01_hardlink_ctime_does_not_stale(self):
        self.verify();p=Path(self.mapping[self.c['fill']['parts'][1]]);old=p.stat();os.link(str(p),str(self.w/'link'))
        self.assertNotEqual(p.stat().st_ctime_ns,old.st_ctime_ns);self.ready()
    def test_01_chmod_does_not_stale(self):
        self.verify();p=Path(self.mapping[self.c['fill']['parts'][1]]);old=p.stat();p.chmod(0o400)
        self.assertNotEqual(p.stat().st_ctime_ns,old.st_ctime_ns);self.ready()
    def test_01_client_device_does_not_stale(self):
        self.verify();p=self.remote/'v/0.json';v=P.read(p)
        for row in v['parts']:row['device']=row.get('device',0)+123456
        P.write(p,v);self.ready()
    def test_01_inode_is_not_persistent_key(self):
        self.verify();p=self.remote/'v/0.json';v=P.read(p)
        for row in v['parts']:row['inode']=row.get('inode',0)+123456
        P.write(p,v);self.ready()
    def test_01_success_is_idempotent(self):
        self.verify();p=self.remote/'v/0.json';before=p.read_bytes();r=self.launch('again')
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(p.read_bytes(),before);self.ready()
        self.assertEqual([p for p in (self.remote/'v').iterdir() if p.is_dir()],[])
    def test_01_stale_success_rehashes_same_token(self):
        self.verify();p=Path(self.mapping[self.c['fill']['parts'][1]]);s=p.stat();os.utime(str(p),ns=(s.st_atime_ns,s.st_mtime_ns+1000000000))
        r=self.snippet(self.localize(self.preflight()),'stale');self.assertNotEqual(r.returncode,0);self.assertIn(b'stale',r.stderr)
        r=self.launch('again');self.assertEqual(r.returncode,0,r.stderr);self.wait_receipt();self.ready()
        archives=[p for p in (self.remote/'v').iterdir() if p.is_dir()];self.assertEqual(len(archives),1)
        self.assertTrue((archives[0]/'0.json').is_file());self.assertEqual((archives[0]/'0.txt').read_text(),'0\n')
    def test_01_binding_key_mismatch_can_reverify(self):
        self.verify();p=self.remote/'v/0.json';v=P.read(p);v['parts'][1]['path']+='.old';P.write(p,v)
        r=self.launch('again');self.assertEqual(r.returncode,0,r.stderr);self.wait_receipt();self.ready()
    def test_02_noncanonical_paths_refuse_check(self):
        for key in ('parts','done','config','receipt','data_receipt'):
            original=self.c['fill'][key][0] if key=='parts' else self.c['fill'][key]
            for path in (original.replace('/okh7/','/okh7//'),original.replace('/okh7/','/okh7/./'),original+'/',original.lstrip('/'),'//'+original.lstrip('/'),original.replace('/okh7/','/okh7/x/../')):
                with self.subTest(key=key,path=path):
                    c=copy.deepcopy(self.c)
                    if key=='parts':c['fill'][key][0]=path
                    else:c['fill'][key]=path
                    c['remote_input_pins'][path]=c['remote_input_pins'][original]
                    with self.assertRaisesRegex(P.Rejected,'canonical absolute'):P.export_identity(c,self.f,self.plan)
    def test_03_policy_archive_is_sha_pinned(self):
        manifest=P.read(Path(os.environ['PACK_DOCS'])/'REQUIRED_INPUTS.json');pin=next(p for p in manifest['inputs'] if p['group']=='native_dry2')
        bad=self.w/'a3.tar';bad.write_bytes(b'x'*10240);pin=dict(pin,path=str(bad))
        with self.assertRaisesRegex(P.Rejected,'hash differs'):P.required_inputs(dict(required_inputs=[pin]))
        self.assertEqual(pin.get('bytes'),10240);self.assertEqual(pin.get('sha256'),'05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae')
    def test_04_scheduler_variable_bypasses(self):
        for line in ('SBATCH_JOB_NAME+=other sbatch x','printf -v SBATCH_JOB_NAME other','export SBATCH_JOB_NAME','read SBATCH_JOB_NAME','declare -x SBATCH_COMMENT','for SBATCH_JOB_NAME in a; do true; done','sbatch --admin-comment=x','printf -v SLURM_JOB_ID 12','SLURM_JOB_ID+=1 sbatch x','echo $SLURM_JOB_NAME','echo ${SLURM_JOB_ID:=12}'):
            with self.subTest(line=line):
                with self.assertRaises(P.Rejected):P.shell_privacy(line)
    def test_05_dot_prefix_header_accepted(self):
        p=self.w/'part';entry=tarfile.TarInfo('./m600/');entry.type=tarfile.DIRTYPE;p.write_bytes(entry.tobuf())
        r=self.snippet(P.V.COMMON+'header(%r,"m600")\n'%str(p),'header');self.assertEqual(r.returncode,0,r.stderr)
    def test_06_operator_docs_current(self):
        docs=Path(os.environ['PACK_DOCS'])
        for name in ('NOTE_FOR_CONT_OPS.md','REPORT.md'):
            text=(docs/name).read_text()
            with self.subTest(name=name):
                self.assertNotIn('pack.py:7',text);self.assertIn('v/*',text)
        inventory=(docs/'CHECK_INVENTORY.md').read_text();self.assertIn('verify receipt',inventory);self.assertIn('parts[i].sha256',inventory)
        self.assertNotIn('hashes real archives[1:]',inventory)
        self.assertIn('verify receipt',P.read(docs/'REQUIRED_INPUTS.json')['remote_check'])
    def test_06_verify_failure_advises_safe_retry(self):
        calls=[]
        def call(k):calls.append(k);return subprocess.CompletedProcess([],1 if k=='verify_poll' else 0,b'',b'recorded failure')
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaises(P.Rejected) as error:P.execute(self.c,{},['verify'],True,self.b['token'],call=call,sleeper=lambda n:None)
        self.assertIn('recorded failure permits explicit verify retry',str(error.exception));self.assertEqual(calls,['verify','verify_poll'])
    def test_06_all_reuses_verified_build(self):
        self.verify();P.write(P.state_root(self.c)/'BUILD.json',self.b);cfg=self.w/'c.json';P.write(cfg,self.c);calls=[]
        def execute(c,scripts,phases,*args):
            calls.extend(phases);r=self.launch('all_verify');self.assertEqual(r.returncode,0,r.stderr);self.ready()
        with patch.object(P,'checked',return_value=self.b),patch.object(P,'local_check',return_value={}),patch.object(P,'execute',side_effect=execute),patch.object(P,'place_code',return_value='pass'),redirect_stdout(io.StringIO()):
            try:rc=P.main(['all','--config',str(cfg),'--enable','--yes','--token',self.b['token'],'--execute-remote'])
            except P.Rejected as error:self.fail('all cannot reuse verified build: '+str(error))
        self.assertEqual(rc,0);self.assertEqual(calls,['verify','place','fill','cpu','gpu'])
    def test_07_production_needs_old_identity(self):
        for identities in ([],None):
            c=dict(builder={'path':'unused'})
            if identities is not None:c['old_identities']=identities
            with self.subTest(identities=identities):
                with self.assertRaisesRegex(P.Rejected,'old identity'):P.structure(self.p,c)
    def test_07_ledger_precedes_verify_in_note(self):
        text=(Path(os.environ['PACK_DOCS'])/'NOTE_FOR_CONT_OPS.md').read_text()
        self.assertLess(text.index('Reserve the built token'),text.index('pack.py verify'))
        self.assertIn('finish every link and chmod',text)

class Safety4(Base):
    def test_recovery_lock_refuses_concurrent_launcher(self):
        import fcntl
        self.verify();p=Path(self.mapping[self.c['fill']['parts'][1]]);s=p.stat();os.utime(str(p),ns=(s.st_atime_ns,s.st_mtime_ns+1000000000))
        before=(self.remote/'v/0.json').read_bytes()
        with (self.remote/'v/0.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=self.launch('locked')
            self.assertNotEqual(r.returncode,0);self.assertEqual((self.remote/'v/0.json').read_bytes(),before)
        r=self.launch('unlocked');self.assertEqual(r.returncode,0,r.stderr);self.wait_receipt();self.ready()
    def test_uncertain_and_placed_verify_refuse(self):
        self.verify();(self.remote/'v/0.txt').write_text('partial')
        r=self.launch('uncertain');self.assertNotEqual(r.returncode,0)
        (self.remote/'v/0.txt').write_text('0\n');(self.remote/'a').mkdir()
        r=self.launch('placed');self.assertNotEqual(r.returncode,0);self.assertIn(b'after placement',r.stderr)
    def test_wrong_bytes_after_success_never_authorize_place(self):
        self.verify();p=Path(self.mapping[self.c['fill']['parts'][1]]);raw=p.read_bytes();p.write_bytes(bytes([raw[0]^1])+raw[1:])
        r=self.launch('again');self.assertEqual(r.returncode,0,r.stderr)
        end=time.monotonic()+5
        while not (self.remote/'v/0.exit').exists() and time.monotonic()<end:time.sleep(.02)
        self.assertFalse((self.remote/'v/0.txt').exists());self.assertFalse((self.remote/'v/0.json').exists())
        self.assertIn('sha256 differs',(self.remote/'v/0.log').read_text());self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
        r=self.snippet(self.localize(self.preflight()),'bad');self.assertNotEqual(r.returncode,0)
    def test_only_job_id_reads_allowed(self):
        for line in ('echo "$SLURM_JOB_ID"','echo "${SLURM_JOB_ID}"','J=${SLURM_JOB_ID:-0}'):P.shell_privacy(line)
    def test_header_rejections_remain(self):
        for i,name in enumerate(('./m544/','../m600/','././@PaxHeader','./')):
            p=self.w/str(i);entry=tarfile.TarInfo(name);entry.type=tarfile.DIRTYPE;p.write_bytes(entry.tobuf())
            r=self.snippet(P.V.COMMON+'header(%r,"m600")\n'%str(p),'bad'+str(i));self.assertNotEqual(r.returncode,0)
    def test_builder_free_fixture_still_allowed(self):P.structure(self.p,dict(old_identities=[]))

if __name__=='__main__':P.limits();unittest.main(verbosity=2)
