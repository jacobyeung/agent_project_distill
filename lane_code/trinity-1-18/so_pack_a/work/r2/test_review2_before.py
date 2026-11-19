"""Round-2 defect regressions; PACK_SOURCE selects the untouched reviewed code."""
import copy, json, os, subprocess, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ.get('PACK_SOURCE',str(Path(__file__).parent)))
import pack as P
import test_support as T

class Review2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['PACK_R2_WORK']);cls.root.mkdir()
        fixture=Path(os.environ['PACK_R2_FIXTURE']);cls.p=fixture/'p';cls.config=P.read(fixture/'config.json')
        cls.f=P.package_files(cls.p);cls.d=fixture/'1.tgz'
        cls.b=dict(token=P.read(cls.p/'0.json')['token'],package=str(cls.p),delivery=str(cls.d),sha256=P.file_digest(cls.d),tree=P.fingerprint(cls.f))
    def setUp(self):
        self.w=self.root/self._testMethodName;self.w.mkdir();self.c=copy.deepcopy(self.config)
        self.c['work']=str(self.w/'state');self.c['ledger']=str(self.w/'ledger');Path(self.c['ledger']).write_text(self.b['token']+'\n')
    def preflight(self,code,mapping,label):
        driver=self.w/(label+'.py')
        driver.write_text('import sys\nsys.path.insert(0,%r)\nimport pack_checks as Q\nwith Q.Mirrors(%r):exec(compile(%r,"preflight","exec"),{})\n'%(str(Path(P.__file__).parent),mapping,code))
        return subprocess.run(['/usr/bin/python3','-I','-s','-B',str(driver)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(self.w))
    def test_01_wrong_part_pins_at_check(self):
        for label,sizes in [('one',[1,0,0,0]),('same_sum',[1,-1,0,0])]:
            c=copy.deepcopy(self.c);c['fill_mode']='structural';c['mirrors']={}
            for path,delta in zip(c['fill']['parts'],sizes):c['remote_input_pins'][path]['bytes']+=delta
            w=self.w/label
            with self.assertRaises(P.Rejected):P.probe('fill',self.p,w,c)
            self.assertIn('part size differs from binding',(w/'0.log').read_text())
    def test_01_missing_binding_parts_names_input(self):
        f=dict(self.f);pay=P.untar(f['0.tgz']);plan=json.loads(pay['9.json']);plan['export_binding'].pop('parts');pay['9.json']=json.dumps(plan).encode()
        p=P.extract(T.seal(f,pay),self.w/'p');c=dict(self.c,fill_mode='structural',mirrors={});w=self.w/'q'
        with self.assertRaises(P.Rejected):P.probe('fill',p,w,c)
        self.assertIn('Required input missing: export_binding_pin',(w/'0.log').read_text())
    def test_01_wrong_done_before_place_attempt(self):
        self.corrupt_preflight('done')
    def test_01_wrong_preparation_before_place_attempt(self):
        for name in ('config','receipt','data_receipt'):
            with self.subTest(name=name):self.corrupt_preflight(name)
    def corrupt_preflight(self,key):
        scripts=P.plan(self.c,self.b);code=P.heredocs(Path(scripts['preflight']).read_text())[0]
        mapping={k:v['path'] for k,v in self.c['mirrors'].items()}
        good=self.preflight(code,mapping,key+'good');self.assertEqual(good.returncode,0,good.stderr)
        path=self.c['fill'][key];raw=Path(mapping[path]).read_bytes();bad=self.w/(key+'.bad')
        if key=='done':raw=raw[:-2]+(b'0' if raw[-2:-1]!=b'0' else b'1')+raw[-1:]
        else:raw=raw.replace(b'{',b'[',1)
        bad.write_bytes(raw);self.assertEqual(bad.stat().st_size,Path(mapping[path]).stat().st_size);mapping[path]=str(bad)
        calls=[];c=dict(self.c,work=str(self.w/key))
        def call(phase):
            calls.append(phase)
            if phase=='preflight':return self.preflight(code,mapping,key+'bad')
            (P.state_root(c)/'place.attempt').write_text('spent');return subprocess.CompletedProcess([],0,b'',b'')
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(c,scripts,['place'],call=call)
        self.assertEqual(calls,['preflight']);self.assertFalse((Path(c['work'])/'place.attempt').exists())
    def test_02_dropped_real_dependency(self):
        f=dict(self.f);base=json.loads(f['a/0.json']);base['archives'].pop(2);f['a/0.json']=T.jd(base);p=P.extract(T.seal(f),self.w/'p')
        c=dict(self.c,fill_mode='structural',mirrors={});w=self.w/'q'
        with self.assertRaises(P.Rejected):P.probe('fill',p,w,c)
        self.assertIn('Dependency layout differs from pinned reference',(w/'0.log').read_text())
    def test_03_unreserved_token_before_preflight(self):
        Path(self.c['ledger']).write_text('');calls=[]
        def call(k):calls.append(k);return subprocess.CompletedProcess([],0,b'',b'')
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaisesRegex(P.Rejected,'reserve.*Trinity ledger'):P.execute(self.c,{},['place'],call=call)
        self.assertEqual(calls,[]);self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_04_all_job_names_and_no_comments(self):
        for line in ('#SBATCH --job-name=other','#SBATCH --comment=ticket42','sbatch --job-name=xyz --comment=abc','sbatch -J xyz','sbatch -Jxyz','sbatch --job-name other','sbatch --comment abc'):
            with self.subTest(line=line):
                with self.assertRaises(P.Rejected):P.shell_privacy(line)
        for line in ('sbatch --job-name=a15_cot_apa123456789ab','sbatch -J a15_cot_apf123456789ab','sbatch --job-name="${P##*/}"'):
            P.shell_privacy(line)
    def test_05_exact_forbidden_rule_documented(self):
        docs=Path(os.environ.get('PACK_DOCS',str(Path(P.__file__).parent/'out')))
        for name in ('NOTE_FOR_CONT_OPS.md','REPORT.md'):
            text=(docs/name).read_text()
            for term in ('^a15_cot_ap[a-f][0-9a-f]{10,15}$','forbidden_extra','case-insensitively, as substrings','Python stdin heredoc bodies','old_identities','0700','0600','umask 077','/tmp/a<job><token>'):
                self.assertIn(term,text)
    def test_06_five_rows_and_error_limit(self):
        text=(Path(os.environ.get('PACK_DOCS',str(Path(P.__file__).parent/'out')))/'ORCHARD_ONLY_CHECKS.md').read_text()
        for label in ('6(a): staged content identity','6(b): structural dependency layout','6(c): ledger reservation','6(d): CPU failure text','6(e): transport and remote environments'):
            self.assertIn(label,text)
        self.assertIn('the third consecutive error aborts',text);self.assertNotIn('at most three consecutive errors',text)
    def test_07_failed_cpu_returns_log_text(self):
        scripts=P.plan(self.c,self.b);p=self.w/'p';(p/'a').mkdir(parents=True);(p/'a/4.txt').write_text('123\n')
        for name in ('4.err','4.log'):(p/'a'/name).write_text('cpu_failure_'+name+'\n')
        text=Path(scripts['poll']).read_text().replace(P.remote_path(self.b),str(p))
        text=text.replace(P.HEADER,P.HEADER+"sacct(){ printf 'FAILED|\\n'; }\n",1)
        script=self.w/'poll.sh';script.write_text(text)
        result=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(self.w))
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn(b'cpu_failure_4.err',result.stderr);self.assertIn(b'cpu_failure_4.log',result.stderr)
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaisesRegex(P.Rejected,'cpu_failure_4.err'):P.execute(self.c,scripts,['gpu'],True,self.b['token'],call=lambda k:result,sleeper=lambda n:None)
    def test_08_pinned_native_harness_is_executed(self):
        script=self.w/'native.py';script.write_text("raise ValueError('native dry refusal sentinel')\n"+Path(self.c['native_dry']['path']).read_text())
        c=dict(self.c,native_dry=dict(path=str(script),sha256=P.file_digest(script)));w=self.w/'q'
        with self.assertRaises(P.Rejected):P.probe('fill',self.p,w,c)
        self.assertIn('native dry refusal sentinel',(w/'0.log').read_text())
    def test_09_transport_uses_caller_identity(self):
        captured=[]
        def call(argv,**kw):captured.append(kw['env']);return subprocess.CompletedProcess(argv,0,b'',b'')
        with patch.dict(os.environ,HOME='/tmp/caller_home',SSH_AUTH_SOCK='/tmp/caller_sock'),patch.object(P,'checked',return_value=self.b),patch.object(P.subprocess,'run',side_effect=call):
            P.execute(self.c,dict(preflight='/tmp/0',place='/tmp/1'),['place'])
        self.assertEqual(len(captured),2)
        for env in captured:self.assertEqual(env.get('HOME'),'/tmp/caller_home');self.assertEqual(env.get('SSH_AUTH_SOCK'),'/tmp/caller_sock')
    def test_10_fill_body_bash_syntax(self):
        original=P.shell_join
        def broken(argv):return 'if then' if '/a/4.py' in ' '.join(argv) else original(argv)
        with patch.object(P,'shell_join',side_effect=broken):
            with self.assertRaises(P.Rejected):P.plan(self.c,self.b)
    def test_10_receipt_interpreter_label(self):
        r=P.probe('receipt',self.p,self.w/'q',self.c)
        self.assertTrue(r.get('python','').startswith(sys.version.split()[0]),'receipt wrapper interpreter must report its actual version')

if __name__=='__main__':P.limits();unittest.main(verbosity=2)
