"""Exercise the retained tower and authenticated exception return on CPU."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_fixes as fixtures
from test_fixes import HERE, temp, BD
import contextlib
import hashlib
import json
import subprocess
import types
import io
import tarfile
import time
import zlib
import unittest
from unittest.mock import patch


class FailureTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.FixTests.setUpClass.__func__)

    @classmethod
    def tearDownClass(cls):
        import j
        (HERE/'out/FAILURE_CHECKS.json').write_text(j.wire_dumps(cls.evidence,indent=2)+'\n')

    def test_vendor_pin_dynamic_import_and_corruption(self):
        from student_pilot import g3t_online as online,tower_read as tower,c1r_ref
        parent={m.name:d for m,d in BD.B.read_tar((BD.GB/'out2/t1/delivery.tgz').read_bytes())}
        original={m.name:d for m,d in BD.B.read_tar(parent['0.tgz'])}
        prefix='tree/student_pilot/g3t_vendor/'
        members={n[len(prefix):]:d for n,d in original.items() if n.startswith(prefix) and n.endswith('.py')}
        expected=hashlib.sha256(''.join(f'{n}\0{BD.B.sha(d)}\n' for n,d in sorted(members.items())).encode()).hexdigest()
        self.assertEqual(len(members),26)
        self.assertEqual(expected,tower.SOURCE_SHA256)
        self.assertEqual(online.vendor_digest(),expected)
        self.assertEqual(c1r_ref.source_import(online.VENDOR).__name__,'G3T')
        for name,module in tuple(sys.modules.items()):
            if name=='vggt' or name.startswith('vggt.'):
                self.assertTrue(Path(module.__file__).is_relative_to(self.payload))
        target=Path(str(online.VENDOR/'vggt/models/g3t.py'));raw=target.read_bytes()
        try:
            target.write_bytes(raw+b'\n')
            self.assertNotEqual(online.vendor_digest(),expected)
            with self.assertRaisesRegex(tower.TowerError,'source pin differs'):
                tower.FrozenG3TTower(dict(weights_path='0',config_path='0'))._load()
        finally:target.write_bytes(raw)
        class ReachedWeights(Exception):pass
        with patch.object(tower,'_hash',side_effect=ReachedWeights),self.assertRaises(ReachedWeights):
            tower.FrozenG3TTower(dict(weights_path='0',config_path='0'))._load()
        self.evidence['source']=dict(passed=True,files=len(members),parent_digest=expected,corrupt_source_rejected=True)

    def test_one_capture_real_tower_bridge_cpu_heads(self):
        import numpy as np
        import torch
        from PIL import Image
        from student_pilot import tower_read, _tower_native, carrier_c1_decode, ground_context
        from e2e_reader import real,artifact
        from g import w,t
        from g.d import decode
        class Head(torch.nn.Module):
            def __init__(self,kind):super().__init__();self.kind=kind
            def forward(self,blocks,images=None,**kw):
                n=blocks[0].shape[1] if images is None else images.shape[1]
                if self.kind in ('local','global'):
                    a=torch.zeros((1,n,6 if self.kind=='local' else 5))
                    a[:,:,3]=1
                    if self.kind=='local':a[:,:,4:]=1.2
                    return [a]
                conf=torch.arange(16.).reshape(1,1,4,4).expand(1,n,4,4)
                return torch.full((1,n,4,4,3 if self.kind=='point' else 1),2.),conf
        class Module(torch.nn.Module):
            def __init__(self):
                super().__init__();self.aggregator=object()
                self.local_camera_head=Head('local');self.global_camera_head=Head('global')
                self.depth_head=Head('depth');self.point_head=Head('point')
        module=Module()
        frozen=tower_read.FrozenG3TTower(dict(device='cpu',dense_frames=64,dtype='fp32'),module=module)
        perception=real.real_perception(None,device='cpu',perception_memo='verify',
            perception_memo_modules=['g3t'],perception_memo_verify_ids=['0'])
        perception.g3t.model=frozen
        language=torch.nn.Linear(1,1,bias=False)
        state=types.SimpleNamespace(heads=types.SimpleNamespace(gravity=np.array([0.,-1.,0.]),
            depth_map=torch.ones(1),depth_head=types.SimpleNamespace(query=lambda data,uv:torch.full(uv.shape[:2],4.))))
        def prepare(*a,**kw):language(torch.ones((1,1)));return state
        gen=types.SimpleNamespace(model=types.SimpleNamespace(model=types.SimpleNamespace(language_model=language)),
            processor=None,device='cpu',perception=perception,prompt_batch=lambda *a:{},artifact=None)
        slots=list(range(0,64,2))
        frames=dict(anchor_indices=slots,dense_indices=list(range(64)),anchor_slots=slots,
            native_frames=[Image.new('RGB',(64,48),(10,20,30))]*64)
        ref=dict(item_id='0',capture='0',source_indices=slots,mapping=dict(dense_count=64,frame_binding_sha256='0'*64))
        @contextlib.contextmanager
        def audit(*a):yield types.SimpleNamespace(entries=0)
        def layers(agg,images):return [torch.zeros((1,64,1,1))]*24,5
        # Preserve preprocessing, pose conversion, sampling, TowerState checks,
        # own-depth scaling and worker capture. Replace only neural forwards.
        with patch.object(_tower_native,'selected_layers',layers),patch.object(carrier_c1_decode,'_prepare_decode',prepare),\
             patch.object(ground_context,'closed_adapters',side_effect=lambda f:f),patch.object(artifact,'Audit',audit),\
             patch('e2e_reader.perception_memo.weight_identity',return_value={}):
            with t.fresh_perception(gen):row=w.capture_one(gen,dict(frames=frames,row={}),ref)
        depth,_=decode(row)
        self.assertEqual(depth.shape,(32,51,51));np.testing.assert_allclose(depth,4.)
        self.assertEqual((row['prefills'],row['decode_steps']),(1,0))
        self.assertEqual(row['metadata']['tower_scale'],2.)
        self.assertEqual(perception.memo.entries,{})
        self.evidence['capture']=dict(passed=True,dense=64,anchors=32,prefills=1,decode_steps=0,scale=2.,
            real='preprocessing, conversion, sampling, validation, own scaling, capture',stubbed='neural forwards and weight identity')

    def test_bounded_traceback_and_authenticated_archive(self):
        from orchard_h10 import e,job
        import j,tarfile
        out=temp()/'r';(out/'metadata').mkdir(parents=True)
        try:
            try:raise ValueError('g3t tower depth '+('x\n'*300))
            except ValueError as error:raise RuntimeError('student reader outer') from error
        except RuntimeError as error:e.exception(out/'metadata/7.json',error)
        value=j.loads((out/'metadata/7.json').read_bytes())
        self.assertLessEqual(len(value['lines']),200)
        self.assertIn('RuntimeError: student reader outer',value['lines'])
        with e.capture(out/'metadata/8.json') as stream:
            p=subprocess.run([sys.executable,'-I','-s','-B','-c',"raise ValueError('g3t tower depth')"],stdout=stream,stderr=subprocess.STDOUT)
        self.assertEqual(p.returncode,1)
        self.assertTrue(any('Traceback' in s for s in j.loads((out/'metadata/8.json').read_bytes())['lines']))
        for path in (out/'metadata').iterdir():
            raw=path.read_bytes()
            if path.suffix=='.0':bytes.fromhex(raw.decode().replace('\n',''))
            else:self.assertEqual(set(j.wire_loads(raw)),{'a0'})
            self.assertFalse(any(word in raw.decode().lower() for word in ('g3t','tower','depth','student','reader')))
        S,J,R,*_=job.template()
        job.write(out/'FAILED.json',dict(error='E98'))
        with patch.object(R,'pool_operation',return_value={}),patch.object(R,'upload',return_value=dict(verified=True)):
            receipt=R.publish(out,str(out.parent/'0'),'a0123456789abcdef','0'*64,1)
        archive=Path(receipt['local_return'])/'result.tar.gz'
        self.assertEqual(BD.B.sha(archive.read_bytes()),receipt['archive_sha256'])
        with tarfile.open(archive) as tf:
            self.assertEqual(tf.extractfile('metadata/7.json').read(),(out/'metadata/7.json').read_bytes())
            self.assertEqual(tf.extractfile('metadata/8.json').read(),(out/'metadata/8.json').read_bytes())
        self.evidence['diagnostics']=dict(passed=True,max_lines=200,max_line_chars=2048,authenticated_members=2)

    def test_capture_descendant_holds_pipe(self):
        from orchard_h10 import e
        import j
        path=temp()/'27.json'
        # The direct child exits while its descendant retains both write ends.
        code="import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(3)']); print('child completed',flush=True)"
        start=time.monotonic()
        with e.capture(path) as stream:
            result=subprocess.run([sys.executable,'-I','-B','-c',code],stdout=stream,stderr=subprocess.STDOUT)
        self.assertEqual(result.returncode,0)
        self.assertLess(time.monotonic()-start,2)
        self.assertIn('child completed',j.loads(path.read_bytes())['lines'])
        self.evidence['descendant_capture']=dict(passed=True,seconds=time.monotonic()-start,descendant_holds_pipe_seconds=3)

    def test_capture_drains_bounded_tail(self):
        from orchard_h10 import e
        import j
        path=temp()/'27.json'
        code="import sys; sys.stdout.write(('x'*3000+'\\n')*500); print('last output',flush=True)"
        with e.capture(path) as stream:
            result=subprocess.run([sys.executable,'-I','-B','-c',code],stdout=stream,stderr=subprocess.STDOUT)
        self.assertEqual(result.returncode,0)
        tail=j.loads(path.read_bytes())
        self.assertEqual(tail['lines'][-1],'last output')
        self.assertLessEqual(len(tail['lines']),200)
        self.assertTrue(all(len(line)<=2048 for line in tail['lines']))
        self.assertLessEqual(path.stat().st_size,262144)

    def test_boot_signal_receipt(self):
        from orchard_h10 import boot,common,runner
        import j
        root=temp();(root/'a').mkdir();(root/'r/metadata').mkdir(parents=True)
        config=dict(output=str(root/'r'),python=sys.executable,prefix=[])
        common.write(root/'r/metadata/25.json',dict(passed=False,failed_module=None,bulk_bytes=0))
        with patch.object(runner,'control',return_value=root/'a'),patch.object(runner,'environment',return_value={}),patch.object(common,'checked_run',return_value=subprocess.CompletedProcess([], -15)):
            with self.assertRaises(subprocess.CalledProcessError):boot.worker(dict(config=config))
        worker=j.loads((root/'r/metadata/25.json').read_bytes())
        self.assertEqual(worker['worker_returncode'],-15);self.assertEqual(worker['worker_signal'],15)
        original_path=boot.Path
        def path(value):return root/'shared' if str(value)=='/project/community/jjyeung' else original_path(value)
        def exited(argv,**kwargs):
            common.write(root/'r/metadata/25.json',worker)
            kwargs['stdout'].write(b'output before signal\n')
            return subprocess.CompletedProcess(argv,-9)
        namespace=types.SimpleNamespace(physical=lambda r,p:root/'r',namespace=lambda r:[],environment=lambda r:{})
        cfg=dict(logical='/scratch/a0',token=self.info['token'],plan_sha256=self.info['plan_sha256'])
        with patch.object(boot,'Path',side_effect=path),patch.object(common,'checked_run',side_effect=exited),patch.dict(os.environ,SLURM_JOB_ID='123456'):
            with self.assertRaises(subprocess.CalledProcessError):boot.launch(root,cfg,dict(python=sys.executable,policy=dict(vnice='/tmp/0')),namespace,0,0)
        receipt=j.loads((root/'shared'/cfg['token']/'a/25.json').read_bytes())
        self.assertEqual(receipt['child_returncode'],-9);self.assertEqual(receipt['child_signal'],9)
        self.assertEqual(receipt['worker_signal'],15);self.assertFalse(receipt['passed'])
        self.assertIn('output before signal',receipt['child_output']['lines'])
        self.evidence['signal_status']=dict(passed=True,simulated=True,child_signal=9,worker_signal=15)

    def test_worker_exception_receipt(self):
        from g import w
        from student_pilot.tower_errors import TowerError
        import j
        root=temp();cfg=dict(output=str(root/'r'),settings='0.json',stop_file=str(root/'0'))
        with patch.object(w,'bind_reader_root',side_effect=TowerError('Tower G3T source pin differs')):
            result=w.run(cfg,100.,clock=lambda:0.)
        self.assertEqual(result['failure'],'E99:546f7765724572726f72')
        self.assertEqual(result['completed'],0)
        self.assertFalse(j.loads((root/'r/metadata/PARITY.json').read_bytes())['trusted'])
        trace=j.loads((root/'r/metadata/7.json').read_bytes())['lines']
        self.assertTrue(any('Tower G3T source pin differs' in line for line in trace))
        self.evidence['worker_failure']=dict(passed=True,code=result['failure'],lines=len(trace))

    def test_worker_failure_through_production_fetch(self):
        from g import w
        from orchard_h10 import job
        from student_pilot.tower_errors import TowerError
        import j,runpy
        root=temp();out=root/'r';pool=root/'0'
        cfg=dict(output=str(out),settings='0.json',stop_file=str(root/'1'))
        with patch.object(w,'bind_reader_root',side_effect=TowerError('injected current delivery worker exception')):
            result=w.run(cfg,100.,clock=lambda:0.)
        self.assertEqual(result['completed'],0)
        job_id='123456';token=self.info['token']+format(int(job_id),'08x')
        plan=self.info['plan_sha256']
        job.write(out/'FAILED.json',dict(plan_sha256=plan,error=result['failure']))
        job.write(out/'metadata/RETURN_ID.json',dict(token=token,job=job_id))
        job.write(out/'metadata/CAPTURE.json',dict(uploaded=False,error=result['failure']))
        _,_,R,*_=job.template()
        local_io={'__name__':'local_pool_io'}
        exec(compile(self.files['orchard_h10/vendor/return_io.py'],'return_io.py','exec'),local_io)
        operate=local_io['operate'];operate('test',pool,token)
        # Use real publication and real pool-copy receipts. Cloud is unavailable.
        with patch.dict(os.environ,{'SLURM_JOB_ID':job_id}),\
             patch.object(R,'pool_operation',side_effect=lambda action,pool,token,local=None,**kw:operate(action,pool,token,local)),\
             patch.object(R,'upload',side_effect=RuntimeError('local test has no cloud channel')):
            receipt=R.publish(out,pool,token,plan,1)
        self.assertTrue(receipt['returned'])
        self.assertEqual(receipt['verified_channels'],['pool'])
        original_plan=j.loads(self.files['9.json'])
        command=[sys.executable,'-I','-s','-B',str(HERE/'tests/local_fetch.py'),'parent',
                 str(self.package),original_plan['pool'],str(pool),job_id,str(HERE/'orchard/o_fetch.sh')]
        process=subprocess.run(command,cwd=HERE,text=True,capture_output=True,env=os.environ.copy())
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        fetched=self.package/'a/f/0.tgz'
        self.assertEqual(BD.B.sha(fetched.read_bytes()),receipt['archive_sha256'])
        with tarfile.open(fetched) as archive:
            trace=j.loads(archive.extractfile('metadata/7.json').read())
            self.assertTrue(any('injected current delivery worker exception' in line for line in trace['lines']))
            self.assertEqual(archive.extractfile('metadata/7.json').read(),(out/'metadata/7.json').read_bytes())
        dest=self.package/'a/f'
        auth=runpy.run_path(str(self.package/'a/7.py'))
        ex=j.loads((dest/'EXIT.json').read_bytes())
        got=j.loads((dest/'RETURN_RECEIPT.json').read_bytes())
        self.assertFalse(ex['complete']);self.assertEqual(ex['status'],'FAILED')
        for field,value in [('token','a00000000'),('plan_sha256','0'*64),('archive_sha256','0'*64)]:
            with self.assertRaises(ValueError):auth['validate_exit'](dict(ex,**{field:value}),fetched,plan,token)
        with self.assertRaises(ValueError):auth['validate_receipt'](dict(got,returned=False),ex,dest/'EXIT.json',fetched,plan,token)
        self.evidence['production_fetch']=dict(passed=True,delivery_sha256=self.info['delivery_sha256'],
            source_archive_sha256=receipt['archive_sha256'],fetched_sha256=BD.B.sha(fetched.read_bytes()),
            fetched=os.path.relpath(fetched,HERE),traceback=trace,failed_status_accepted=True,
            production_script_sha256=BD.B.sha((HERE/'orchard/o_fetch.sh').read_bytes()),
            package_pins_checked=True,plan_pin_checked=True,pool_receipt_checked=True,
            fetched_receipt_checked=True,inner_identity_checked=True,negative_checks=4,
            adaptations=['local pool path binding','local interpreter binding','cloud channel disabled'],
            empirical_gpu_result=False)

    def test_early_source_gate_and_lazy_rgb(self):
        from orchard_h10 import s,job
        import j
        started=time.monotonic();s.preflight(self.payload)
        elapsed=time.monotonic()-started
        empty=temp();(empty/'l.json').write_text(j.wire_dumps(dict(views={})))
        with self.assertRaisesRegex(ValueError,'E54'):s.preflight(empty)
        S=job.template()[0];root=temp();archive=root/'0';blob=io.BytesIO()
        raw={'f/0.png':b'first','f/1.png':b'second','g/0':b'shared'}
        with tarfile.open(fileobj=blob,mode='w') as tf:
            for name,value in raw.items():
                item=tarfile.TarInfo(name);item.size=len(value);tf.addfile(item,io.BytesIO(value))
        archive.write_bytes(blob.getvalue());index={}
        with archive.open('rb') as stream:s.extract(S,stream,root/'d',100,['f','g'],archive,index)
        self.assertFalse((root/'d/f').exists())
        members=lambda n:[dict(path=n,sha256=BD.B.sha(raw[n]))]
        s.materialize(index,members('f/0.png'),root/'d')
        self.assertEqual((root/'d/f/0.png').read_bytes(),b'first')
        self.assertFalse((root/'d/f/1.png').exists())
        s.materialize(index,members('f/1.png'),root/'d')
        self.assertEqual((root/'d/f/1.png').read_bytes(),b'second')
        with self.assertRaisesRegex(ValueError,'E57'):
            s.materialize(index,[dict(path='f/0.png',sha256='0'*64)],root/'d')
        self.evidence['early_stage']=dict(passed=True,source_gate_seconds=elapsed,missing_vendor_rejected=True,
            indexed_frames=len(index),deferred_second_png=True,corrupt_rgb_rejected=True)

    def test_incremental_memory_and_incomplete_capture(self):
        from g.m import Monitor
        import j
        root=temp();cuda=types.SimpleNamespace(reset_peak_memory_stats=lambda:None,max_memory_allocated=lambda:1234)
        monitor=Monitor(root,types.SimpleNamespace(cuda=cuda))
        try:
            monitor.begin('0')
            row=j.loads((root/'5.json').read_bytes())[0]
            self.assertEqual(row['status'],'active')
            self.assertGreater(row['process_rss_hwm_bytes'],0)
            self.assertGreater(row['rss_peak_bytes'],0)
            self.assertEqual(row['gpu_max_allocated_bytes'],1234)
            self.assertGreaterEqual(row['seconds'],0)
            monitor.finish('written');monitor.begin('1')
        finally:monitor.close()
        rows=j.loads((root/'5.json').read_bytes())
        self.assertEqual([r['status'] for r in rows],['written','incomplete'])
        self.assertLessEqual(len(j.loads((root/'13.json').read_bytes())['lines']),200)
        for path in root.iterdir():
            self.assertEqual(set(j.wire_loads(path.read_bytes())),{'a0'})
        self.evidence['memory']=dict(passed=True,incomplete_preserved=True,gpu_double_bytes=1234,
            process_hwm='kernel cumulative bytes',capture_rss='one-second sampled peak bytes')

    def test_first_write_before_second_stage_and_tower_failure(self):
        import torch,j
        from g import w
        from orchard_h10 import s
        from e2e_reader import parity
        from h1eval.h10 import parity_adapter as adapter
        from h1eval import items
        refs=w.load_rows();reference=j.loads((self.payload/'g/8.json').read_bytes())
        manifests={r['task']['native']:r['mapping']['frame_binding_sha256'] for r in refs}
        original_digest=items.digest
        digest=lambda value:value['anchors'] if 'anchors' in value else original_digest(value)
        settings=dict(save_own_depth=False,perception_memo_modules=['g3t'],export_dir='e',artifact_manifest='a')
        factory=types.SimpleNamespace(load_info={'export':{'step':544}},generator=types.SimpleNamespace(perception=types.SimpleNamespace(memo=None)))
        events=[];root=temp();cfg=dict(output=str(root/'r'),settings='0.json',stop_file=str(root/'0'))
        def stage(settings,capture):
            if events:
                self.assertIn('capture',events)
                data=zlib.decompressobj(31).decompress((root/'c/0.gz').read_bytes())
                self.assertTrue(data.endswith(b'\n'))
                self.assertEqual(j.loads((root/'r/metadata/4.json').read_bytes())['items'],events.count('capture'))
            events.append('stage')
        def tower(*args):events.append('tower');return None,{'0':1}
        def load(*args,**kw):self.assertEqual(events,['stage','tower']);events.append('load');return factory
        def capture(gen,bound,ref,**kw):
            if events.count('capture')==0:self.assertEqual(kw['tower_result'],{'0':1})
            else:self.assertIsNone(kw['tower_result'])
            events.append('capture')
            return dict(metadata=dict(geometry=reference['geometry'][ref['item_id']]['geometry']),timings={})
        with contextlib.ExitStack() as stack:
            for owner,name,value in [(w,'bind_reader_root',lambda:self.payload/'b'),(w,'assert_reader_root',lambda root:None),
                (adapter,'settings_for',lambda *a:settings),(adapter,'prepare_runtime',lambda *a:None),
                (adapter,'artifact_spec',lambda *a:None),(adapter,'make_capped_real',load),
                (parity,'_captures',lambda *a:manifests),(parity,'bind_item',lambda *a:{}),
                (items,'digest',digest),(w,'start_tower',tower),(w,'capture_one',capture),(s,'stage_capture',stage),
                (torch.cuda,'get_device_name',lambda *a:'H100'),(torch.cuda,'synchronize',lambda:None),
                (torch.cuda,'reset_peak_memory_stats',lambda:None),(torch.cuda,'max_memory_allocated',lambda:9876)]:
                stack.enter_context(patch.object(owner,name,side_effect=value))
            result=w.run(cfg,100.,clock=lambda:0.)
            self.assertTrue(result['complete']);self.assertEqual(events.count('capture'),60)
            failed=temp();cfg.update(output=str(failed/'r'),stop_file=str(failed/'0'))
            with patch.object(s,'stage_capture') as staging,patch.object(w,'start_tower',side_effect=RuntimeError('tower failure')),patch.object(adapter,'make_capped_real') as loading:
                result=w.run(cfg,100.,clock=lambda:0.)
                self.assertEqual(result['completed'],0);loading.assert_not_called();self.assertEqual(staging.call_count,1)
            row=j.loads((failed/'r/metadata/5.json').read_bytes())[0]
            self.assertEqual(row['status'],'incomplete');self.assertEqual(row['gpu_max_allocated_bytes'],9876)
        self.evidence['first_write']=dict(passed=True,captures=60,first_write_before_next_stage=True,
            early_tower_before_carrier=True,failed_tower_prevents_carrier_and_next_stage=True)


if __name__=='__main__':unittest.main(verbosity=2)
