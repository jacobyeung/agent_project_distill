"""Local launch regression; use real guards and harmless return helper execution."""
import ast,copy,hashlib,importlib.util,io,json,os,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
O=Path(sys.argv.pop(1)).resolve(); W=O.parent
sys.path[:0]=[str(O),str(O/'src')]
from orchard_h10 import common,job
import node_check

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bundle(batch):
    line=next(s for s in batch.read_text().splitlines() if s.startswith('b=bytes.fromhex('))
    raw=bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0]))
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return {m.name:archive.extractfile(m).read() for m in archive}

def fresh():
    # Hex-only suffixes avoid accidental forbidden substrings in random paths.
    p=O/'checks'/('a'+os.urandom(6).hex());p.mkdir(parents=True);return p

def vendor(root):
    p=root/'bootstrap/orchard_h10/vendor/return_io.py';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((O/'src/orchard_h10/vendor/return_io.py').read_bytes());return p

def spawn(path):
    return subprocess.run([sys.executable,'-I','-s','-B',str(path),'--help'],
                          env={'PATH':'/usr/bin:/bin','CUDA_VISIBLE_DEVICES':''},capture_output=True,check=True)

class Bundle(unittest.TestCase):
    def test_old_bundle_is_overwritten(self):
        root=fresh();old=W/('boot' if O.name=='b1' else 'boot2')
        raw=bundle(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/gates/lost/reader')/('b1g' if O.name=='b1' else 'b2r')/'out/package/BATCH.sh')
        for name,data in raw.items():
            self.assertEqual(data,(old/name).read_bytes());(root/name).write_bytes(data)
        self.assertEqual((root/'6.py').read_bytes(),(O/'tower_sequence.py').read_bytes())
        before=sha(root/'6.py');v=vendor(root)
        with patch.object(subprocess,'Popen',subprocess.Popen):
            common.install_process_guard(root);spawn(v)
        self.assertNotEqual(before,sha(root/'6.py'));self.assertEqual(sha(root/'6.py'),sha(v))
        self.record('old',dict(reproduced=True,operator_sha256=before,overwritten_sha256=sha(root/'6.py')))

    def record(self,name,value):
        (O/('GUARD_'+name+'.json')).write_text(json.dumps(value,indent=2)+'\n')

    def test_new_bundle_survives_real_guard(self):
        root=fresh();vendor(root)
        with patch.object(subprocess,'Popen',subprocess.Popen):
            common.install_process_guard(root)
            proof=node_check.check_bundle_guard(O/'package',root)
        self.assertIs(proof['passed'],True)
        self.assertEqual((root/'7.py').read_bytes(),(O/'package/a/6.py').read_bytes())
        self.record('new',proof)

    def bootstrap(self,mutation=False,flag=True,nested=False,entry=True):
        root=fresh();files=bundle(O/'package/BATCH.sh')
        for name,data in files.items():(root/name).write_bytes(data)
        shared=fresh();(shared/'a/c').mkdir(parents=True)
        for name in ('0.tgz','0.json'):(shared/name).write_bytes((O/'package'/name).read_bytes())
        (shared/'a/1.json').write_bytes((O/'package/a/1.json').read_bytes())
        public=json.loads(files['0.json']);proof=dict(passed=True,entry_sequence_passed=True,full_reader_passed=True,full_reader=dict(passed=True),
            payload=public['payload_sha256'],plan=public['plan_sha256'],inputs=sha(shared/'a/1.json'),
            operator_sha256=sha(root/'7.py'),memory=dict(basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],
                sam_measurement_required=False,fits=True))
        if flag is not None:proof['bundle_guard_passed']=flag
        if entry is None:proof.pop('entry_sequence_passed')
        else:proof['entry_sequence_passed']=entry
        (shared/'a/c/CPU.json').write_text(json.dumps(proof))
        calls=[]
        def fake_main(r):
            common.install_process_guard(r)
            # The actual staging helper was extracted by the bootstrap.
            spawn(r/'p/orchard_h10/vendor/return_io.py')
            (r/'a').mkdir();(r/'a/1.json').write_text(json.dumps(dict(action=1,config={})))
            if nested:
                common.install_process_guard(r/'a');spawn(r/'p/orchard_h10/vendor/return_io.py')
                self.assertEqual(sha(r/'a/6.py'),sha(r/'6.py'))
            if mutation:(r/'7.py').write_text('raise SystemExit(99)\n')
            job.checked_run([sys.executable,'-B','-I',str(r/'a/5.py'),str(r/'a/1.json')],check=True)
        # Redirect only the unavailable community package path; execute all bootstrap logic.
        tree=ast.parse(files['0.py'])
        for n in ast.walk(tree):
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='shared' for t in n.targets):
                n.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(shared))],keywords=[])
        with patch.object(sys,'argv',['0.py',str(root)]),patch.object(sys,'path',sys.path.copy()), \
             patch.object(subprocess,'Popen',subprocess.Popen),patch.object(job,'main',fake_main), \
             patch.object(job,'checked_run',lambda argv,*a,**k:calls.append((argv,k))):
            if mutation:
                with self.assertRaisesRegex(ValueError,'Bundled operator changed after startup'):
                    exec(compile(ast.fix_missing_locations(tree),'0.py','exec'),{'__name__':'__main__'})
                self.assertEqual(calls,[])
            elif flag is not True or entry is not True:
                with self.assertRaisesRegex(ValueError,'Full CPU check differs'):
                    exec(compile(ast.fix_missing_locations(tree),'0.py','exec'),{'__name__':'__main__'})
                self.assertEqual(calls,[])
            else:
                exec(compile(ast.fix_missing_locations(tree),'0.py','exec'),{'__name__':'__main__'})
                self.assertEqual(len(calls),1)
                argv=calls[0][0];self.assertEqual(argv[-2],str(root/'7.py'))
                cfg=json.loads((root/'a/1.json').read_text())
                self.assertEqual(cfg['config']['operator_sha256'],sha(root/'7.py'))
                self.assertEqual(sha(root/'7.py'),sha(O/'tower_sequence.py'))
                self.record('dispatch',dict(passed=True,argv=argv,operator_sha256=sha(root/'7.py')))
        return root

    def test_dispatch_after_guard_has_matching_sha(self):self.bootstrap()
    def test_nested_entry_guard_preserves_operator(self):self.bootstrap(nested=True)
    def test_changed_operator_fails_before_dispatch(self):self.bootstrap(mutation=True)
    def test_missing_cpu_flag_refused(self):self.bootstrap(flag=None)
    def test_false_cpu_flag_refused(self):self.bootstrap(flag=False)
    def test_nonboolean_cpu_flag_refused(self):self.bootstrap(flag=1)
    def test_missing_entry_flag_refused(self):self.bootstrap(entry=None)
    def test_false_entry_flag_refused(self):self.bootstrap(entry=False)
    def test_nonboolean_entry_flag_refused(self):self.bootstrap(entry=1)
    def test_cpu_helper_rejects_changed_bundle(self):
        root=fresh();vendor(root);package=fresh();(package/'a').mkdir()
        for n in ('BATCH.sh','0.json','a/6.py'):(package/n).write_bytes((O/'package'/n).read_bytes())
        (package/'a/6.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Bundled operator differs'):
            node_check.check_bundle_guard(package,root)
    def test_cpu_helper_requires_real_guard_write(self):
        root=fresh();vendor(root)
        with self.assertRaises(FileNotFoundError):node_check.check_bundle_guard(O/'package',root)
    def test_cpu_helper_failure_prevents_receipt(self):
        root=fresh();results=root/'results'
        with patch.object(node_check.tempfile,'mkdtemp',return_value=str(root)), \
             patch.dict(os.environ,SLURM_JOB_ID='123'), \
             patch.object(sys,'argv',['5.py','--package',str(O/'package'),'--sequence',str(O/'package/a/6.py'),'--results',str(results)]), \
             patch.object(subprocess,'Popen',subprocess.Popen),patch.object(sys,'path',sys.path.copy()):
            S,J,*_=common.template()
            with patch.object(J,'storage_proof',return_value={'fixture':True}), \
                 patch.object(node_check,'check_bundle_guard',side_effect=ValueError('injected bundle failure')), \
                 patch.object(job,'stage',return_value=None):
                with self.assertRaisesRegex(ValueError,'injected bundle failure'):node_check.main()
        self.assertFalse((results/'CPU.json').exists())
    def test_cpu_helper_publishes_bound_guard_flag(self):
        root=fresh();results=root/'results';events=[]
        S,J,R,*_=common.template()
        real_write_test=R.write_test
        def write_test(pool,token):
            events.append('write_test')
            return real_write_test(pool,token)
        cfg=common.read_config(O/'package');logical=cfg['logical']
        def stage(*args):
            events.append('stage');(root/'a').mkdir()
        def checked(argv,**kwargs):
            value=json.loads(Path(argv[-1]).read_text())
            if value.get('action')==0:
                events.append('prepare')
                settings=dict(stage1_select_rule='null_argmax',perception_memo='on' if O.name=='b2' else 'off',
                    perception_memo_modules=['g3t'],perception_memo_verify_ids=[],types=['room_size_estimation'])
                common.write(J.physical(root,logical+'/d/READY.json'),{'fixture':True})
                common.write(J.physical(root,logical+'/d/settings.json'),settings)
            else:
                self.assertEqual(events,['stage','write_test','prepare'])
                self.assertEqual(argv[-2:], [str(root/'7.py'),str(root/'a/1.json')])
                events.append('sequence')
                if O.name=='b1':
                    value['package']=str(O/'src')
                    value['config'].update(package=str(O/'src'),python=sys.executable,
                        settings=str(J.physical(root,logical+'/d/settings.json')),
                        output=str(J.physical(root,logical+'/r')))
                    common.write(Path(argv[-1]),value)
                    subprocess.run([sys.executable,'-B','-I',argv[-2],argv[-1]],check=True,
                        env=dict(PATH='/usr/bin:/bin',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8'),
                        stdout=kwargs['stdout'],stderr=subprocess.STDOUT)
                else:
                    common.write(J.physical(root,logical+'/r/metadata/MEMORY.json'),
                        dict(fits=True,basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],sam_measurement_required=False))
                    full=json.loads((O/'LOCAL_CPU_CHECK.json').read_text())['full_reader']
                    common.write(J.physical(root,logical+'/r/REHEARSAL.json'),[dict(full_reader=full)])
        with patch.object(node_check.tempfile,'mkdtemp',return_value=str(root)), \
             patch.dict(os.environ,SLURM_JOB_ID='123'), \
             patch.object(sys,'argv',['5.py','--package',str(O/'package'),'--sequence',str(O/'package/a/6.py'),'--results',str(results)]), \
             patch.object(subprocess,'Popen',subprocess.Popen),patch.object(sys,'path',sys.path.copy()), \
             patch.object(J,'storage_proof',return_value={'fixture':True}), \
             patch.object(J,'namespace',return_value=[]),patch.object(J,'environment',return_value={}), \
             patch.object(R,'write_test',side_effect=write_test), \
             patch.object(job,'stage',side_effect=stage),patch.object(common,'checked_run',side_effect=checked):
            node_check.main()
        proof=json.loads((results/'CPU.json').read_text())
        self.assertEqual(events,['stage','write_test','prepare','sequence'])
        self.assertIs(proof['entry_sequence_passed'],True)
        self.assertEqual(proof['entry_sequence']['events'],['guard_installed','write_test','operator_dispatch'])
        self.assertIs(proof['passed'],True);self.assertIs(proof['bundle_guard_passed'],True)
        self.assertIs(proof['bundle_guard']['passed'],True)
        self.assertEqual(proof['bundle_guard']['operator_sha256'],sha(O/'package/a/6.py'))
        if O.name=='b2':self.assertIs(proof['full_reader_passed'],True)
        self.record('receipt',dict(passed=True,scope='Real guarded write test and bootstrap dispatch; staging and preparation are fixtures; b1 runs the operator subprocess; b2 operator subprocess is tested in test_cpu_helper',
                                  cpu=str(results/'CPU.json')))
        if O.name=='b1':
            local=dict(passed=True,root=str(root),results=str(results),real_model_reads=False,
                scope='Guard, 4 MiB write test, embedded bootstrap dispatch and real CPU operator subprocess; allocation, namespace, storage, stage, restore and local paths are fixtures.',
                workers=json.loads(J.physical(root,logical+'/r/REHEARSAL.json').read_text()),cpu=proof)
            common.write(O/'LOCAL_ENTRY_CHECK.json',local)
            common.write(O/'LOCAL_REHEARSAL.json',local)

    def test_dispatch_before_write_test_is_rejected(self):
        root=fresh()
        with self.assertRaisesRegex(ValueError,'Write test must precede'):
            node_check.dispatch_operator(root,dict(passed=True,events=['guard_installed']),
                [str(root/'a/5.py'),str(root/'a/1.json')],lambda *a,**k:self.fail('Early dispatch'))
    def test_operator_guard_collision_is_rejected(self):
        root=fresh();(root/'6.py').write_bytes((O/'tower_sequence.py').read_bytes())
        (root/'7.py').symlink_to('6.py')
        with self.assertRaisesRegex(ValueError,'Operator collides'):
            node_check.dispatch_operator(root,{},[],lambda *a,**k:self.fail('Colliding dispatch'))
    def test_import_bootstrap_does_not_run_job(self):
        import runpy
        with patch.object(job,'main',side_effect=AssertionError('Import ran job.main')):
            self.assertTrue(callable(runpy.run_path(str(O/'tower_bootstrap.py'))['make_dispatch']))

    def test_payload_changes_only_token(self):
        def data(p):
            with tarfile.open(p) as t:return {m.name:t.extractfile(m).read() for m in t}
        old=data(O/'original/0.tgz');new=data(O/'0.tgz')
        self.assertEqual(set(old),set(new))
        self.assertEqual([n for n in old if old[n]!=new[n]],['9.json'])
        a=json.loads(old['9.json']);b=json.loads(new['9.json']);a['token']=b['token'];self.assertEqual(a,b)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Bundle))
    (O/'tests_guard_result.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
