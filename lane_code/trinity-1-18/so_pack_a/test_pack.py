"""Regression tests never invoke ssh, scp, Slurm, GPUs or delete files."""
import copy, io, json, os, re, subprocess, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack as P
import test_support as T
import pack_token as K
import pack_checks as Q

class Packaging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w=Path(os.environ.get('PACK_TEST_WORK',str(Path(__file__).parent/'work'/('t'+os.urandom(5).hex()))))
        reused=os.environ.get('PACK_TEST_FIXTURE')
        if reused:
            cls.w.mkdir();cls.p=Path(reused)/'p';cls.c=P.read(Path(reused)/'config.json');cls.c['work']=str(cls.w/'state')
        else:cls.p,cls.c=T.fixture(cls.w)
        cls.f=P.package_files(cls.p);cls.counter=0
    def fresh(self,label):
        type(self).counter+=1;return self.w/(label+str(self.counter))
    def mutated(self,change,payload=False):
        f=dict(self.f);pay=P.untar(f['0.tgz']) if payload else None
        change(pay if payload else f)
        return P.extract(T.seal(f,pay),self.fresh('p'))
    def fails_probe(self,mode,p,needle,c=None):
        w=self.fresh('q')
        with self.assertRaises(P.Rejected):P.probe(mode,p,w,c or self.c)
        self.assertIn(needle,(w/'0.log').read_text())
    def test_01_surface_scope_and_argv(self):
        for package in (T.A4,T.B5):
            f,pay,v,plan=P.structure(package)
            for name in f:P.opaque(name)
            self.assertTrue(any(b'model' in b for b in pay.values()))
        self.assertEqual(P.privacy(self.p,self.c)['names'],15)
        for text in ('#SBATCH --comment=model','/usr/bin/python3 /tmp/dataset.py','A=benchmark /bin/true'):
            with self.assertRaises(P.Rejected):P.shell_privacy(text)
        f=dict(self.f);f['model.log']=b'x'
        with self.assertRaises(P.Rejected):P.structure(P.extract(f,self.fresh('p')))
        P.shell_privacy("# code comment model\n/usr/bin/python3 - <<'A'\nprint('dataset')\nA\n")
    def test_02_all_checks_precede_transport(self):
        cfg=self.fresh('cfg');P.write(cfg,self.c);called=[]
        with patch.object(P,'build',return_value={}),patch.object(P,'built',return_value={'package':str(self.p)}),patch.object(P,'local_check',return_value={}),patch.object(P,'plan',side_effect=P.Rejected('late submit script rejected')),patch.object(P,'execute',side_effect=lambda *a:called.append(a)):
            with self.assertRaisesRegex(P.Rejected,'late submit'):P.main(['all','--config',str(cfg),'--enable','--yes','--token','b635a315de01e','--execute-remote'])
        self.assertEqual(called,[])
    def test_03_timeout_short_calls_and_state_machine(self):
        c=copy.deepcopy(self.c);c['work']=str(self.fresh('s'));calls=[];sleeps=[]
        results=[(0,b'123\n'),(75,b''),(0,b'RUNNING|\n'),(0,b'COMPLETED|\n'),(0,b'456\n')]
        def call(k):
            calls.append(k);rc,out=results.pop(0);return subprocess.CompletedProcess([],rc,out,b'accounting fixture')
        with patch.object(P,'checked',return_value={'token':'b635a315de01e'}):P.execute(c,{},['cpu','gpu'],True,'b635a315de01e',call,sleeps.append)
        self.assertEqual(calls,['cpu','poll','poll','poll','gpu']);self.assertEqual(sleeps,[60,60,60])
        for name in ('place','fill','cpu','poll','gpu'):
            command=P.command(c,'/tmp/'+name);self.assertIn('| timeout 300 bash ',command)
        self.assertNotIn('while',P.command(c,'/tmp/0'))
    def test_04_delivery_is_tested_tree(self):
        w=self.fresh('s');w.mkdir();f=dict(self.f);d=w/'1.tgz';d.write_bytes(P.tar_bytes(f));b=dict(token='b635a315de01e',package=str(self.p),delivery=str(d),sha256=P.file_digest(d),tree=P.fingerprint(f));P.write(w/'BUILD.json',b);c=dict(self.c,work=str(w));self.assertEqual(P.built(c),b)
        d.write_bytes(P.tar_bytes(dict(f,**{'8.log':b'changed'})))
        with self.assertRaises(P.Rejected):P.built(c)
    def test_05_adapt_cpu_identity_everywhere(self):
        p=P.ROOT+'/a15_cot_apa123456789ab';text=P.adapted_script(self.c,'cpu',p,self.p)
        self.assertNotIn('d50ba921ef1f4',text);self.assertIn('--job-name=a15_cot_apa123456789ab',text)
        path=self.fresh('script');path.write_text(text+'\nexport P='+P.ROOT+'/a15_cot_apb123456789ab\n');c=copy.deepcopy(self.c);c['remote']['cpu']=dict(path=str(path),sha256=P.file_digest(path))
        with self.assertRaises(P.Rejected):P.adapted_script(c,'cpu',p,self.p)
        c=copy.deepcopy(self.c);c['remote']['walltime']='01:00:00'
        with self.assertRaisesRegex(P.Rejected,'walltime'):P.adapted_script(c,'cpu',p,self.p)
    def test_06_defect1_real_rows_null(self):
        def mutate(pay):
            n='inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl';values=[json.loads(x) for x in pay[n].decode().splitlines()];self.assertTrue(values and 'total_num_frames' in values[0]);values[0]['total_num_frames']=None;pay[n]=('\n'.join(json.dumps(v) for v in values)+'\n').encode()
        self.fails_probe('logic',self.mutated(mutate,True),'total_num_frames')
    def test_07_adapter_leaves_native_files_unchanged(self):
        for path,kind in ((T.D/'build_d.py','d'),(T.R/'build_r10.py','r10')):
            raw=path.read_text();self.assertEqual(K.adapted(raw,kind,None,False),raw);self.assertNotEqual(K.adapted(raw,kind,'a123456789ab',True),raw)
        import ast,base64,gzip
        line=next(s for s in (T.D/'o_build_D.sh').read_text().splitlines() if s.startswith('assets = '));assets=ast.literal_eval(line.split('=',1)[1]);self.assertEqual(gzip.decompress(base64.b64decode(assets['b.py']['data'])),(T.D/'build_d.py').read_bytes())
    def test_07b_native_source_drift_blocks_release(self):
        import ast,base64,gzip
        items=T.D/'evidence/items/dist580.json'
        c=dict(builder=dict(path=str(T.D/'build_d.py'),sha256=P.file_digest(T.D/'build_d.py'),argv=['stage','source','sha',str(items),'binding']))
        with self.assertRaisesRegex(P.Rejected,'score_d.py'):P.source_preflight(c)
        with patch.object(P,'probe',side_effect=AssertionError('Probe ran before source preflight')):
            with self.assertRaisesRegex(P.Rejected,'score_d.py'):P.local_check(c,self.p,self.fresh('q'))
        here=self.fresh('coherent');here.mkdir();script=(T.D/'o_build_D.sh').read_bytes();(here/'o_build_D.sh').write_bytes(script);(here/'check_release_d.py').write_bytes((T.D/'check_release_d.py').read_bytes())
        assets=ast.literal_eval(next(l for l in script.decode().splitlines() if l.startswith('assets = ')).split('=',1)[1])
        for name,spec in assets.items():
            if name=='items/dist580.json':continue
            (here/('build_d.py' if name=='b.py' else name)).write_bytes(gzip.decompress(base64.b64decode(spec['data'])))
        c['builder']['path']=str(here/'build_d.py');self.assertEqual(P.source_preflight(c)['assets'],10)
    def test_08_real_python36_place_and_fill(self):
        for mode in ('login','fill'):
            r=P.probe(mode,self.p,self.fresh('q'),self.c);self.assertTrue(r['passed']);self.assertTrue(r['python'].startswith('3.6.8'))
        self.assertTrue(r['entry_check_executed']);self.assertTrue(r['resolution']['environment_resolved']);self.assertEqual(r['resolution']['archives'],6)
    def test_09_defect2_isolated_import_gate(self):
        def mutate(pay):
            name='h1eval/h10/launch.py';pay[name]=b'import aa_pack_sibling\n'+pay[name];pay['h1eval/h10/aa_pack_sibling.py']=b'VALUE=1\n'
        p=self.mutated(mutate,True);w=self.fresh('q')
        with self.assertRaises(P.Rejected):P.probe('logic',p,w,self.c)
        logs='\n'.join(x.read_text() for x in w.glob('i*.log'));self.assertIn('ModuleNotFoundError',logs);self.assertIn('aa_pack_sibling',logs)
    def test_09b_defect3_fill_drops_env(self):
        def mutate(f):
            a=b"inputs['archives'].append(dict(destination=archive['destination'],parts=[prep_archive],\n                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values()))))"
            b=b"inputs['archives'][4]=dict(destination=archive['destination'],parts=[prep_archive],\n                                   sha256=prep_archive['sha256'],expanded_bytes=sum(map(len,raw.values())))"
            self.assertEqual(f['a/4.py'].count(a),1);f['a/4.py']=f['a/4.py'].replace(a,b)
        self.fails_probe('fill',self.mutated(mutate),'Fill must append')
    def test_10_terminal_states_and_transport_failure(self):
        for s in ('BOOT_FAIL','DEADLINE','REVOKED','CANCELLED','FAILED','OUT_OF_MEMORY','TIMEOUT','NODE_FAIL'):
            with self.assertRaises(P.Rejected):P.poll_state(s+'|\n')
        calls=[]
        def call(k):calls.append(k);return subprocess.CompletedProcess([],124,b'',b'timeout')
        with patch.object(P,'checked',return_value={'token':'b635a315de01e'}):
            with self.assertRaisesRegex(P.Rejected,'do not retry'):P.execute(self.c,{},['gpu'],True,'b635a315de01e',call,lambda n:None)
        self.assertEqual(calls,['poll'])
        calls=[]
        def accounting(k):calls.append(k);return subprocess.CompletedProcess([],75,b'',b'accounting unavailable')
        with patch.object(P,'checked',return_value={'token':'b635a315de01e'}):
            with self.assertRaisesRegex(P.Rejected,'Repeated sacct'):P.execute(self.c,{},['gpu'],True,'b635a315de01e',accounting,lambda n:None)
        self.assertEqual(calls,['poll','poll','poll'])
    def test_11_extra_terms_reach_path_argv_env(self):
        c=copy.deepcopy(self.c);c['forbidden_extra']=['eabcdef012345']
        with self.assertRaises(P.Rejected):P.fill_argv(c,P.ROOT+'/a15_cot_apb635a315de01e')
        c['forbidden_extra']=['b635a315de01e']
        with self.assertRaises(P.Rejected):P.privacy(self.p,c)
        with self.assertRaises(P.Rejected):P.shell_privacy('A=customword /bin/true',['customword'])
    def test_12_transport_limit(self):
        command=P.command(self.c,'/tmp/0.sh');self.assertIn('pv -q -L 8000000 ',command);self.assertIn('timeout',command)
        w=self.fresh('transport');w.mkdir();stub=w/'0.sh';stub.write_text('#!/bin/bash\ncat\n');payload=w/'1.sh';payload.write_text('opaque fixture bytes\n');c=copy.deepcopy(self.c);c['remote']['ossh']=str(stub)
        r=subprocess.run(['bash','-o','pipefail','-c',P.command(c,str(payload))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,env=P.environment(w))
        self.assertEqual(r.returncode,0);self.assertEqual(r.stdout,payload.read_bytes())
        stub.write_text('#!/bin/bash\ncat >/dev/null\nsleep 3\n');c['remote']['timeout']=1
        r=subprocess.run(['bash','-o','pipefail','-c',P.command(c,str(payload))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,env=P.environment(w));self.assertEqual(r.returncode,124)
    def test_13_ledger_reuse_before_builder(self):
        path=self.fresh('ledger');path.write_text('{"token":"a123456789ab"}\n');c=dict(self.c,ledger=str(path))
        with patch.object(P,'run') as run:
            with self.assertRaisesRegex(P.Rejected,'ledger'):P.build(c,'a123456789ab')
            run.assert_not_called()
    def test_15_orchard_contract_inventory(self):
        text=(Path(__file__).parent/'out/ORCHARD_ONLY_CHECKS.md').read_text()
        for term in ('sacct','USR1','token','3.6.8','CPU.json','timeout'):self.assertIn(term,text)
    def test_16_native_dry_settings_order_and_counts(self):
        import runpy
        for package,family in ((T.A4,'full'),(T.B5,'room')):
            f,pay,v,plan=P.structure(package);base=json.loads(f['a/0.json']);op=runpy.run_path(str(package/'a/6.py'));desc=op['descriptors'](str(package));memory=op['memory_bound']()
            self.assertEqual(Q.native_dry_predicates(base,plan,pay,op,desc,memory)['family'],family)
            cases=[]
            bad=copy.deepcopy(desc);bad[0]['expected']+=1;cases.append((base,plan,pay,op,bad,memory))
            bad=copy.deepcopy(desc);bad[0]['types']=list(reversed(bad[0]['types'])) if family=='full' else [3];cases.append((base,plan,pay,op,bad,memory))
            bad=dict(plan,perception_memo_verify_ids=['x']);cases.append((base,bad,pay,op,desc,memory))
            bad=dict(op,RULES=());cases.append((base,plan,pay,bad,desc,memory))
            bad=dict(base,types=list(reversed(plan['order'])));cases.append((bad,plan,pay,op,desc,memory))
            bad=dict(pay);name='items/devs1_routed.json' if family=='full' else 'items/room134.json';items=json.loads(bad[name]);items['items']=items['items'][:-1];bad[name]=T.jd(items);cases.append((base,plan,bad,op,desc,memory))
            for args in cases:
                with self.assertRaises(P.Rejected):Q.native_dry_predicates(*args)
        def mutate(pay):
            items=json.loads(pay['items/room134.json']);items['items']=items['items'][:-1];pay['items/room134.json']=T.jd(items)
        self.fails_probe('logic',self.mutated(mutate,True),'Dry per-type item counts')
    def test_17_native_dry_binding_policy_slot(self):
        w=self.fresh('q');r=P.probe('fill',self.p,w,self.c);self.assertEqual(r['resolution']['policy_archive_slot'],4)
        p=w/(P.PREFIX+'b635a315de01e');inputs=P.read(p/'a/1.json');base=P.read(p/'a/0.json');pins=P.read(p/'a/export.json');plan=json.loads(P.untar((p/'0.tgz').read_bytes())['9.json']);helper=(p/'a/4.py').read_text()
        self.assertEqual(Q.dry_fill_identity(inputs,base,plan,pins,helper),4)
        for key in ('run','step','member_directory','lineage','object','archive_sha256'):
            bad=copy.deepcopy(pins);bad[key]='invalid'
            with self.assertRaises(P.Rejected):Q.dry_fill_identity(inputs,base,plan,bad,helper)
        bad=copy.deepcopy(pins);next(iter(bad['preparation'].values()))['sha256']='0'*64
        with self.assertRaises(P.Rejected):Q.dry_fill_identity(inputs,base,plan,bad,helper)
        bad=copy.deepcopy(inputs);bad['archives'].append(copy.deepcopy(bad['archives'][4]))
        with self.assertRaisesRegex(P.Rejected,'slot count'):Q.dry_fill_identity(bad,base,plan,pins,helper)
        bad=copy.deepcopy(inputs);bad['archives'][4]['sha256']='0'*64
        with self.assertRaisesRegex(P.Rejected,'slot count'):Q.dry_fill_identity(bad,base,plan,pins,helper)
    def test_defect4_encoded_descriptor_and_old_identity(self):
        f=dict(self.f);b=P.bundle(f['BATCH.sh']);v=json.loads(b['0.json']);v['token']='a123456789ab';b['0.json']=T.jd(v);line=next(l for l in f['BATCH.sh'].decode().splitlines() if l.startswith('b=bytes.fromhex('));f['BATCH.sh']=f['BATCH.sh'].replace(line.encode(),('b=bytes.fromhex(%r)'%P.tar_bytes(b).hex()).encode());m=json.loads(f['PACKAGE.json']);m['files']['BATCH.sh']=P.digest(f['BATCH.sh']);f['PACKAGE.json']=T.jd(m)
        with self.assertRaisesRegex(P.Rejected,'Bundle descriptor'):P.structure(P.extract(f,self.fresh('p')))
        with self.assertRaisesRegex(P.Rejected,'Old identity'):P.structure(self.p,dict(old_identities=['b635a315de01e']))
    def test_defect5_exit_capture(self):
        def mutate(f):f['BATCH.sh']=f['BATCH.sh'].replace(b'trap fin EXIT',b': # disabled EXIT')
        self.fails_probe('trap',self.mutated(mutate),'Missing EXIT')
    def test_defect6_usr1_forward_and_native_stop(self):
        def mutate(f):f['BATCH.sh']=f['BATCH.sh'].replace(b'trap \'kill -USR1 $PID 2>/dev/null\' USR1',b"trap ':' USR1")
        self.fails_probe('trap',self.mutated(mutate),'USR1 not forwarded')
        def mutate_stop(pay):pay['orchard_h10/runner.py']=pay['orchard_h10/runner.py'].replace(b"marker.write_text(str(number)+'\\n')",b'pass')
        self.fails_probe('stop',self.mutated(mutate_stop,True),'Native stop handshake')
    def test_normalization_default_off_and_directive_order(self):
        raw=P.package_files(T.B5);self.assertEqual(P.normalize_wrapper(raw),raw);f=P.normalize_wrapper(raw,True);t=f['BATCH.sh'].decode();self.assertLess(t.index('#SBATCH'),t.index('umask 077'));self.assertNotIn('head -n 1',t);self.assertEqual(set(n for n in raw if raw[n]!=f[n]),{'BATCH.sh','PACKAGE.json'})
    def test_submit_authorization_and_default_off(self):
        config=self.fresh('cfg');P.write(config,self.c)
        with self.assertRaisesRegex(P.Rejected,'Default OFF'):P.main(['check','--config',str(config)])
        with patch.object(P,'checked',return_value={'token':'b635a315de01e'}):
            for yes,tok in ((False,'b635a315de01e'),(True,'a123456789ab')):
                with self.assertRaises(P.Rejected):P.execute(self.c,{},['cpu'],yes,tok,lambda k:self.fail('unexpected call'))
    def test_native_receipt_predicates(self):
        r=P.probe('receipt',self.p,self.fresh('q'),self.c);self.assertTrue(r['full_reader_validator']);self.assertGreaterEqual(r['negative_cases'],19)
    def test_positive_all_local_checks_and_planning(self):
        c=copy.deepcopy(self.c);c['work']=str(self.fresh('s'));r=P.local_check(c,self.p,self.fresh('q'));self.assertGreater(r['checks']['logic']['rows_checked'],0)
        w=P.state_root(c);d=w/'1.tgz';d.write_bytes(P.tar_bytes(self.f));b=dict(token='b635a315de01e',package=str(self.p),delivery=str(d),sha256=P.file_digest(d),tree=P.fingerprint(self.f));P.write(w/'BUILD.json',b);P.write(w/'CHECK.json',r);scripts=P.plan(c,b);self.assertEqual(set(scripts),{'preflight','place','fill','fill_poll','cpu','poll','gpu'})
        self.assertEqual(P.checked(c),b);P.write(self.w/'POSITIVE.json',dict(check=r,scripts=scripts,build=b,config=c))

if __name__=='__main__':
    # Torch's documented intraop thread setting precedes native tensor work.
    P.limits()
    import torch
    torch.set_num_threads(8)
    unittest.main(verbosity=2)
