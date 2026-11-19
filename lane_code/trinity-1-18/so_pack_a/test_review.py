"""Review round 1 regressions; selectable source root supports before/after proof."""
import copy, json, os, subprocess, sys, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,os.environ.get('PACK_SOURCE',str(Path(__file__).parent)))
import pack as P
import test_support as T

class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w=Path(os.environ['PACK_REVIEW_WORK'])
        reused=os.environ.get('PACK_REVIEW_FIXTURE')
        if reused:
            cls.w.mkdir();fixture=Path(reused);cls.p=fixture/'p';cls.c=P.read(fixture/'config.json');cls.c['work']=str(cls.w/'state')
        else:cls.p,cls.c=T.fixture(cls.w)
        # Also permit the before tree to reach tests of remote planning.
        cls.c['remote_input_pins']={k:dict(bytes=v['bytes']) for k,v in cls.c['mirrors'].items()}
        cls.f=P.package_files(cls.p);cls.n=0
        d=Path(reused)/'1.tgz' if reused else cls.w/'1.tgz'
        if not reused:d.write_bytes(P.tar_bytes(cls.f))
        cls.b=dict(token=P.read(cls.p/'0.json')['token'],package=str(cls.p),delivery=str(d),sha256=P.file_digest(d),tree=P.fingerprint(cls.f))
    def fresh(self,n):
        type(self).n+=1;return self.w/(n+str(self.n))
    def test_r1_detached_slow_fill(self):
        scripts=P.plan(self.c,self.b);text=Path(scripts['fill']).read_text()
        self.assertIn('setsid nohup',text)
        p=self.fresh('a');(p/'a').mkdir(parents=True)
        body='#!/bin/bash\nset -eu\numask 077\nsleep 1\nprintf "0\\n" > a/1.txt\n'
        shell=P.detached_fill(body,str(p));script=self.fresh('f.sh');script.write_text(shell)
        start=time.monotonic();r=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=.8)
        self.assertEqual(r.returncode,0,r.stderr);self.assertLess(time.monotonic()-start,.8);self.assertFalse((p/'a/1.txt').exists())
        time.sleep(1.2);self.assertEqual((p/'a/1.txt').read_text(),'0\n')
        again=subprocess.run(['bash',str(script)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1);self.assertNotEqual(again.returncode,0)
        calls=[];waits=[]
        def call(k):
            calls.append(k);return subprocess.CompletedProcess([],0,b'wait\n' if len(calls)==2 else b'complete\n',b'')
        with patch.object(P,'checked',return_value=self.b):P.execute(self.c,{},['fill'],call=call,sleeper=waits.append)
        self.assertEqual(calls,['fill','fill_poll','fill_poll']);self.assertEqual(waits,[60,60])
    def test_r2_structural_without_archive_mirrors(self):
        c=dict(self.c,fill_mode='structural',mirrors={})
        r=P.probe('fill',self.p,self.fresh('q'),c)
        self.assertEqual(r['mode'],'structural');self.assertFalse(r['production_archive_identity']);self.assertLess(r['standin_bytes'],1048576)
        self.assertTrue(r['resolution']['environment_resolved'])
        f=dict(self.f);f['a/4.py']=f['a/4.py'].replace(b"inputs['archives'].append(",b"inputs['archives'].__setitem__(4,")
        bad=P.extract(T.seal(f),self.fresh('bad'));w=self.fresh('q')
        with self.assertRaises(P.Rejected):P.probe('fill',bad,w,c)
        self.assertIn('Fill must append',(w/'0.log').read_text())
    def test_r4_readonly_preflight_precedes_place(self):
        Path(self.c['ledger']).write_text(self.b['token']+'\n')
        scripts=P.plan(self.c,self.b);self.assertIn('preflight',scripts)
        code=P.heredocs(Path(scripts['preflight']).read_text())[0]
        import pack_checks as Q
        mapping={k:v['path'] for k,v in self.c['mirrors'].items()}
        with Q.Mirrors(mapping):exec(compile(code,'preflight','exec'),{})
        bad=dict(mapping);name=self.c['fill']['done'];bad[name]=str(self.w/'absent')
        with Q.Mirrors(bad):
            with self.assertRaisesRegex(ValueError,'Required staged input'):exec(compile(code,'preflight','exec'),{})
        calls=[]
        def call(k):calls.append(k);return subprocess.CompletedProcess([],1,b'',b'absent staged part')
        with patch.object(P,'checked',return_value=self.b):
            with self.assertRaisesRegex(P.Rejected,'before placement'):P.execute(self.c,scripts,['place'],call=call)
        self.assertEqual(calls,['preflight']);self.assertFalse((Path(self.c['work'])/'place.attempt').exists())
    def test_r3_actual_D_integration(self):
        self.assertIn('PACK_NATIVE_RESULT',os.environ,'Required D integration result: run test_native.py first')
        result=P.read(os.environ['PACK_NATIVE_RESULT']);self.assertTrue(result['d_all_checks_passed'])
        evidence=P.read(result['d_check_file']);self.assertEqual(evidence['check']['checker'],P.source_fingerprint())
        checks=evidence['check']['checks'];self.assertEqual(checks['logic']['native_dry']['family'],'distance')
        for mode in ('logic','guard','trap','stop','login','fill','receipt'):self.assertTrue(checks[mode]['passed'])
        for key in ('cpu','gpu'):self.assertIn('04:00:00',Path(evidence['scripts'][key]).read_text())
    def test_r5_system_command_only(self):
        P.shell_privacy('head -n 1 /tmp/0')
        P.shell_privacy('fin(){ rc=$?; { head -n 1 "$L"; tail -n 60 "$L"; }; }')
        for text in ('echo head','head /tmp/model','head /tmp/head','A=head /bin/true'):
            with self.assertRaises(P.Rejected):P.shell_privacy(text)
        f=P.package_files(T.B5);f['BATCH.sh']=f['BATCH.sh'].replace(b'set -uo pipefail\n',b'set -uo pipefail\numask 077\n');p=P.extract(T.seal(f),self.fresh('native'))
        self.assertEqual(P.privacy(p,{})['names'],15)
        with self.assertRaisesRegex(P.Rejected,'umask'):P.privacy(T.B5,{})
    def test_r6_login_runtime_guard_submit_pool(self):
        runs=[];original=P.run
        def traced(argv,*args,**kwargs):runs.append(argv);return original(argv,*args,**kwargs)
        with patch.object(P,'run',side_effect=traced):guard=P.probe('guard',self.p,self.fresh('q'),self.c)
        self.assertEqual(runs[0][0],'/usr/bin/python3','CPU guard must execute under the login interpreter')
        self.assertTrue(guard.get('python','').startswith('3.6.8'))
        r=P.probe('fill',self.p,self.fresh('q'),self.c)
        self.assertTrue(r['submit_executed']);self.assertTrue(r['pool']['positive']);self.assertTrue(r['pool']['oversize_rejected'])
    def test_r6_operational_inventory(self):
        docs=Path(os.environ.get('PACK_DOCS',str(Path(P.__file__).parent/'out')))
        for name in ('NOTE_FOR_CONT_OPS.md','ORCHARD_ONLY_CHECKS.md'):
            text=(docs/name).read_text()
            for term in ('Review round 1: finding -> fix -> test','REUSE_PARTS_FROM','PREP_FROM','a/f.log','job.stage','8.py submit','Trinity ledger'):
                self.assertIn(term,text)
    def test_r7_production_module_import(self):
        f=dict(self.f);pay=P.untar(f['0.tgz'])
        pay['h1eval/h10/launch.py']=b'from . import aa_pack_relative\nassert aa_pack_relative.VALUE==1\n'
        pay['h1eval/h10/aa_pack_relative.py']=b'VALUE=1\n'
        p=P.extract(T.seal(f,pay),self.fresh('relative'));w=self.fresh('q')
        self.assertTrue(P.probe('logic',p,w,self.c)['passed'])
    def test_r8_gpu_only_retry(self):
        config=self.fresh('cfg');P.write(config,self.c);called=[]
        with patch.object(P,'checked',return_value=self.b),patch.object(P,'plan',return_value={'gpu':'/tmp/0'}),patch.object(P,'execute',side_effect=lambda c,s,ph,*args:called.append(ph)):
            P.main(['gpu','--config',str(config),'--enable','--execute-remote','--yes','--token',self.b['token']])
        self.assertEqual(called,[['gpu']])
        scripts=P.plan(self.c,self.b);text=Path(scripts['gpu']).read_text()
        for word in ('COMPLETED','CPU.json','test ! -e','a/8.txt','mkdir "$P/a/g.lock"'):self.assertIn(word,text)
        self.assertLess(text.index('test ! -s'),text.index('mkdir "$P/a/g.lock"'))
        c=dict(self.c,work=str(self.fresh('retry')));P.state_root(c)
        (Path(c['work'])/'cpu.attempt').write_text('123')
        results=[subprocess.CompletedProcess([],0,b'COMPLETED|\n',b''),subprocess.CompletedProcess([],1,b'',b'queue busy'),subprocess.CompletedProcess([],0,b'COMPLETED|\n',b''),subprocess.CompletedProcess([],0,b'456\n',b'')]
        with patch.object(P,'checked',return_value=self.b),patch.object(P.subprocess,'run',side_effect=results):
            with self.assertRaisesRegex(P.Rejected,'queue busy'):P.execute(c,scripts,['gpu'],True,self.b['token'],sleeper=lambda n:None)
            P.execute(c,scripts,['gpu'],True,self.b['token'],sleeper=lambda n:None)
    def test_r9_only_python_stdin_heredocs(self):
        P.shell_privacy("/usr/bin/python3 -I -s -B - <<'A'\nprint('model')\nA\n")
        for text in ("cat >a/0 <<'A'\nmodel /tmp/0\nA\nbash a/0", "bash <<'A'\nmodel\nA", "cat <<'A' # python3 -\nmodel\nA"):
            with self.assertRaisesRegex(P.Rejected,'Only Python stdin'):P.shell_privacy(text)
    def test_r11_login_exact_delivery(self):
        c=dict(self.c,work=str(self.fresh('state')));d=self.fresh('noncanonical.tgz');raw=Path(self.b['delivery']).read_bytes();d.write_bytes(raw[:4]+b'\x01\x00\x00\x00'+raw[8:])
        b=dict(self.b,delivery=str(d),sha256=P.file_digest(d));P.write(Path(c['work'])/'BUILD.json',b)
        w=self.fresh('login');w.mkdir();driver=self.fresh('driver.py')
        driver.write_text('import sys\nsys.path.insert(0,%r)\nimport pack as P,pack_checks as Q\nfrom pathlib import Path\noriginal=P.place_code\ndef place(b):\n assert b["sha256"]==%r,"Login must place recorded delivery bytes"\n return original(b)\nP.place_code=place\nQ.login(Path(%r),Path(%r),%r)\n'%(str(Path(P.__file__).parent),b['sha256'],str(self.p),str(w),c))
        result=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(driver)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=P.environment(w))
        self.assertEqual(result.returncode,0,result.stderr.decode())
        r=P.probe('login',self.p,self.fresh('q'),c)
        self.assertTrue(r.get('recorded_delivery',False));self.assertEqual(r.get('delivery_sha256'),b['sha256'])
    def test_required_inputs_refuse_by_name(self):
        c=dict(required_inputs=[dict(name='step-600 binding',path=str(self.w/'absent'))])
        with self.assertRaisesRegex(P.Rejected,'Required input missing: step-600 binding'):P.required_inputs(c)
        pin=dict(name='routed test_sequence.py',path=str(self.w/'absent'))
        with self.assertRaisesRegex(P.Rejected,'routed test_sequence'):P.required_inputs(dict(required_inputs=[pin]))

if __name__=='__main__':
    P.limits();unittest.main(verbosity=2)
