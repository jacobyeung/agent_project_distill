from pathlib import Path
import sys, json, hashlib, importlib.util, unittest, ast, subprocess, copy
from types import SimpleNamespace
from unittest.mock import patch

L=Path(__file__).resolve().parents[2]; D=L/'work/build24m4o3'
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import z, ep, rb
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
x=module('new_x',L/'out/rcj/x.py')
old=module('old_x',L/'attic/build24m4o3/out/rcj/x.py')
pc=module('new_pc',L/'out/rcj/pc.py')
nd=module('new_nd',L/'out/rcj/nd.py')
F=D/'fixtures';F.mkdir()

class Tests(unittest.TestCase):
    def test_present_absent_empty_and_oversized(self):
        for label,raws in [('absent',{}),('empty',{'pc_n.log':b''}),
                ('small',{'pc_n.log':b'RuntimeError: fixture\n','pc_p.log':bytes(range(256)),'rd.log':b'\x00\xff\r\n'}),
                ('large',{n:bytes(range(256))*8193 for n in ('pc_n.log','pc_p.log','rd.log')})]:
            root=F/label;out=root/'out';out.mkdir(parents=True)
            for name,raw in raws.items():(root/name).write_bytes(raw)
            (root/'other.log').write_bytes(b'private')
            files,errors=x.log_tails(root,out)
            self.assertEqual(errors,[])
            self.assertEqual(set(p.name for p in out.iterdir()),{n+'.tail' for n in raws})
            for name,raw in raws.items():
                tail=raw[-65536:];v=files[name+'.tail']
                self.assertEqual((out/(name+'.tail')).read_bytes(),tail)
                self.assertEqual(v,dict(source=name,size=len(tail),sha256=hashlib.sha256(tail).hexdigest(),
                    full_size=len(raw),full_sha256=hashlib.sha256(raw).hexdigest()))

    def publication(self,module,label,mode,rc,gate=True,proc_rc=0,rd_rc=0,logs=True,tail_error=False):
        root=F/label;root.mkdir();remote=root/'remote';target=remote/'o/123'
        native=root/('dr/p/q' if mode=='r' else 'r');native.mkdir(parents=True)
        bases=[native/'base',native/'selection'] if mode=='r' else [native]
        for b in bases:
            b.mkdir(exist_ok=True);(b/'rows.sqlite').write_bytes(b'SQLite format 3\x00fixture')
        z.write(root/'mode.json',dict(mode=mode))
        z.write(remote/'rcj/P_SAMPLE_I.json',{})
        def load(p):
            return dict(n_root=str(remote)) if str(p).endswith('k/p.json') else z.load(p)
        def sha(p):
            return x.DB if Path(p)==bases[0]/'rows.sqlite' and gate else z.sha(p)
        Z=SimpleNamespace(load=load,sha=sha,write=z.write)
        def rd(*args):
            if logs:(root/'rd.log').write_bytes(b'diff\x00\xff\n'*12000)
            return rd_rc
        def check(*args,**kw):
            if logs:
                (root/'pc_n.log').write_bytes(b'child\n'*14000)
                (root/'pc_p.log').write_bytes(b'other\n')
            z.write(root/'proc_check.json',dict(status='FAIL' if proc_rc else 'PASS',reason='E95:n:1' if proc_rc else ''))
            return proc_rc
        def ns(*args):
            for n in ('n_sample.json','nd.json','na.json.gz'):(target/n).write_bytes(b'{}\n')
            return dict(status='PASS',files=['n_sample.json','nd.json','na.json.gz'],bytes=9)
        if tail_error:(root/'pc_n.log').symlink_to(root/'mode.json')
        with patch.object(module,'attach',return_value=Z),patch.object(ep,'artifact_entries',return_value=[]),\
                patch.object(module,'rdiff',side_effect=rd),patch.object(module,'launch',side_effect=check),\
                patch.object(module,'sample',return_value=dict(status='PASS')),patch.object(module,'nsample',side_effect=ns),\
                patch.object(module.time,'monotonic',return_value=1):
            result=module.publish(L/'out/kit_qd',root,'123',rc)
        return result,{p.name:p.read_bytes() for p in target.iterdir()},z.load(target/'timings.json')

    def test_success_refusal_and_failed_checks_preserve_existing_outputs(self):
        for i,(rc,gate,proc,rd) in enumerate([(0,True,0,0),(7,True,0,0),(0,True,1,0),(7,True,1,1),(7,False,1,0)]):
            a,af,at=self.publication(old,'old'+str(i),'r',rc,gate,proc,rd)
            b,bf,bt=self.publication(x,'new'+str(i),'r',rc,gate,proc,rd)
            self.assertEqual(a,b)
            extra=set(bf)-set(af)
            self.assertEqual(extra,{'pc_n.log.tail','pc_p.log.tail'}|({'rd.log.tail'} if gate else set()))
            for name in af:
                if name!='timings.json':self.assertEqual(af[name],bf[name])
            self.assertEqual(bt.pop('log_tail_errors'),[])
            for name in extra:bt['files'].pop(name)
            self.assertEqual(at,bt)

    def test_mode_b_byte_identical_even_with_private_logs(self):
        for i,rc in enumerate((0,7)):
            a,af,at=self.publication(old,'b_old'+str(i),'b',rc)
            b,bf,bt=self.publication(x,'b_new'+str(i),'b',rc)
            self.assertEqual((a,af),(b,bf))

    def test_missing_logs_no_placeholders_and_tail_failure_no_status_change(self):
        a,af,at=self.publication(x,'no_logs','r',7,logs=False)
        self.assertFalse(any(n.endswith('.tail') for n in af))
        b,bf,bt=self.publication(x,'bad_tail','r',7,logs=False,tail_error=True)
        self.assertEqual(a,b)
        self.assertEqual(bt['publication_errors'],[])
        self.assertEqual(bt['log_tail_errors'],[dict(file='pc_n.log.tail',error='ValueError')])

    def test_n_child_nonzero_records_real_exception_and_fail_rows(self):
        from student_pilot import p3_provenance as provenance, source_seal, mdg_parent
        root=F/'child';root.mkdir();namespace=root/'ns';q=namespace/'p/q';q.mkdir(parents=True)
        tree=namespace/'p/s';tree.mkdir();h='a'*64
        cfg=dict(streams={},code='seal')
        control=dict(config=cfg,recipe=dict(base_model='asset'),environment=dict(paths=[]))
        def load(path):
            name=str(path)
            if name.endswith('k/p.json'):return dict(namespace=str(namespace))
            return {'n.json':cfg,'base_input.json':control,'base_mounts.json':{},'seal':dict(tree_sha256=h),'asset':{}}[Path(name).name]
        samples=[dict(key=['routing',i,'q'+str(i)],row={},stored_target='{}') for i in range(80)]
        original=subprocess.run;calls=[]
        def child(cmd,**kw):
            calls.append(cmd)
            return original([sys.executable,'-I','-s','-B','-c',
                "try:\n raise ValueError('first')\nexcept ValueError:\n raise RuntimeError('final fixture cause')"],**kw)
        with patch.object(z,'load',side_effect=load),patch.object(provenance,'load',side_effect=load),\
                patch.object(provenance,'pinned',side_effect=lambda p:p),patch.object(provenance,'digest',return_value=h),\
                patch.object(source_seal,'inventory',return_value={}),patch.object(mdg_parent,'model_pin',return_value='asset'),\
                patch.object(pc,'selected',return_value=samples),patch.object(rb,'environment',return_value=dict(paths=[])),\
                patch.object(rb,'command',return_value=['--chdir',str(q),'a','b','c']),patch.object(pc.subprocess,'run',side_effect=child):
            result=pc.run_bound(L/'out/kit_qd',root)
        value=json.loads((root/'proc_check.json').read_bytes())
        self.assertEqual(result,1);self.assertEqual(value['status'],'FAIL')
        self.assertEqual(value['reason'],'ValueError:E95:n:1:RuntimeError: final fixture cause')
        self.assertEqual(len(calls),1);self.assertFalse((root/'pc_p.log').exists())
        self.assertEqual(len(value['rows']),80)
        self.assertTrue(all(r['status']=='FAIL' and r['reason']=='E95' for r in value['rows']))
        out=root/'out';out.mkdir();files,errors=x.log_tails(root,out)
        self.assertEqual(errors,[]);self.assertEqual(set(files),{'pc_n.log.tail'})
        self.assertIn(b'RuntimeError: final fixture cause',(out/'pc_n.log.tail').read_bytes())

    def test_reason_bounded_and_p_unchanged(self):
        p=F/'reason.log';p.write_bytes(b'ValueError: '+b'x'*100000+b'\nRuntimeError: final\n  note\n')
        self.assertEqual(pc.child_reason(p,'n',-9),'E95:n:-9:RuntimeError: final')
        self.assertEqual(pc.child_reason(p,'p',1),'E95:p:1')
        self.assertEqual(pc.child_reason(F/'missing','n',1),'E95:n:1')
        p2=F/'reason_long.log';p2.write_bytes(b'ValueError: '+b'\xff'*12000+b'\n')
        reason=pc.child_reason(p2,'n',1)
        self.assertLess(len(json.dumps(reason).encode()),25000)

    def test_shared_budget(self):
        self.assertEqual(nd.LIMIT,5_000_000-(4<<16))
        root=F/'budget';target=root/'out';target.mkdir(parents=True)
        for name in ('pc_n.log','pc_p.log','rd.log'):(root/name).write_bytes(b'x'*65537)
        files,errors=x.log_tails(root,target);self.assertEqual(errors,[])
        detail='ValueError:E95:n:1:'+chr(0xfffd)*4096
        metadata=len(json.dumps(dict(files=files,reason=detail,log_tail_errors=[])).encode())
        self.assertLess((nd.LIMIT-1)+sum(v['size'] for v in files.values())+metadata,5_000_000)

    def test_only_expected_functions_change(self):
        def funcs(path):return {n.name:ast.dump(n) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        for name,changed,added in [('x.py',{'publish'},{'log_tails'}),('pc.py',{'run_bound'},{'child_reason'}),('nd.py',set(),set())]:
            a=funcs(L/'attic/build24m4o3/out/rcj'/name);b=funcs(L/'out/rcj'/name)
            self.assertEqual({n for n in a if a[n]!=b[n]},changed);self.assertEqual(set(b)-set(a),added)

r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
(D/'TESTS.json').write_text(json.dumps(dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,
    errors=[str(v) for v in r.errors],failures=[str(v) for v in r.failures]),indent=2)+'\n')
raise SystemExit(not r.wasSuccessful())
