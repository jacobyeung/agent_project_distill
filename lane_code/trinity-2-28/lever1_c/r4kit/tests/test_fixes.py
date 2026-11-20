import copy
import hashlib
import importlib.util
import io
import itertools
import subprocess
import json
import os
from pathlib import Path
import signal
import sys
import tarfile
import time
import types
import unittest
import uuid
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                  XDG_CACHE_HOME=str(ROOT/'out/cache'),HF_HOME=str(ROOT/'out/cache/hf'),
                  MPLCONFIGDIR=str(ROOT/'out/cache/mpl'))

def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s)
    sys.modules[name]=m;s.loader.exec_module(m);return m

C=mod('a_storage',ROOT/'src/storage.py')
B=mod('builder',ROOT/'build.py')
ctl=mod('ctl',ROOT/'src/control.py')
probe=mod('probe',ROOT/'src/probe.py')
batched=mod('batched',ROOT/'src/batch.py')

def members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:return {m.name:t.extractfile(m).read() for m in t}
FILES=members((ROOT/'out/delivery.tgz').read_bytes())
SOURCES=C.loads(FILES['8.bin'])
EVIDENCE={}


def fresh():
    p=ROOT/'out'/('f'+uuid.uuid4().hex);p.mkdir();return p


def package():
    p=fresh()
    for n,v in FILES.items():(p/n).write_bytes(v)
    cfg=C.loads(FILES['2.json']);cfg['package']=str(p);C.store(p/'2.json',cfg)
    pins=json.loads((p/'0.json').read_bytes());pins['files']['2.json']=B.pin((p/'2.json').read_bytes())
    (p/'0.json').write_bytes(B.jd(pins))
    (p/'a').mkdir()
    current=dict(passed=True,package=ctl.sha(p/'0.json'),payload=ctl.sha(p/'0.tgz'),frozen=cfg['frozen'])
    C.store(p/'a/4.json',current)
    return p,cfg,current


def scan(root):
    files=[]
    def check(raw,name):
        lower=raw.lower()
        hits=[w for w in B.DENY if w.encode() in lower]
        assert not hits,(name,hits)
    def strings(obj,name):
        if isinstance(obj,str):check(obj.encode(),name)
        elif isinstance(obj,dict):
            for k,v in obj.items():strings(k,name);strings(v,name)
        elif isinstance(obj,list):
            for v in obj:strings(v,name)
    for p in sorted(root.rglob('*')):
        check(str(p.relative_to(root)).encode(),str(p))
        if not p.is_file():continue
        raw=p.read_bytes()
        if p.suffix=='.tgz' or p.name.endswith('.tgz.partial'):
            for name,data in members(raw).items():
                check(name.encode(),str(p))
                if name.endswith('.tgz'):
                    for n,v in members(data).items():check(n.encode(),n);check(v,n)
                else:check(data,name)
        else:check(raw,str(p))
        try:strings(json.loads(raw),str(p))
        except (ValueError,UnicodeDecodeError):pass
        if p.suffix=='.jsonl':
            for line in raw.splitlines():strings(json.loads(line),str(p))
        files.append(dict(path=str(p.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
    return files


class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=fresh();C.materialize(cls.code,SOURCES)
        import torch
        torch.set_num_threads(2)

    def test_01_sources_are_opaque_and_importable(self):
        inventory=scan(self.code)
        self.assertEqual(len(inventory),len(SOURCES))
        from e2e_reader.parity import load_native
        from parity_kit.stage_restore import stage
        from student_pilot.carrier_c1_decode import consume_cache_tokens
        self.assertTrue(all(callable(x) for x in (load_native,stage,consume_cache_tokens)))
        EVIDENCE['opaque_sources']=dict(files=len(inventory),inventory=inventory)

    def test_02_every_controller_failure_fetches(self):
        cases=('check','materialize','room','storage','extract','copy','unpack','launch','worker','timeout','alarm')
        results=[]
        for mode, case in itertools.product(('c','g'), cases):
            with self.subTest(mode=mode, case=case):
                p,cfg,current=package();root=p/'z'
                S=types.SimpleNamespace(room=lambda *a:None,extract_stream=lambda *a,**k:None,
                    copy_parts=lambda *a,**k:None,unpack=lambda *a,**k:None)
                J=types.SimpleNamespace(storage_proof=lambda *a,**k:None)
                injected=[]
                def failed(*args,**kwargs):
                    injected.append(case);raise RuntimeError(case)
                def extracting(stream,target,*args,**kwargs):
                    for n,v in FILES.items():(target/n).write_bytes(v)
                S.extract_stream=extracting
                def prepare(p,root,cfg,job,end):
                    if case in ('launch','worker','timeout','alarm'):
                        (root/'p/a').mkdir(parents=True)
                        # A finished pair must survive all later failures.
                        with (root/'p/a/0.jsonl').open('wb') as f:
                            for a in (0,1):f.write(C.pack(json.dumps(dict(i='a',a=a,text='<ground',n=1))))
                        return J,root/'p'
                    return ctl_prepare(p,root,cfg,job,end)
                def launch(*args):
                    if case=='timeout':raise ctl.subprocess.TimeoutExpired(['0'],1)
                    if case=='alarm':
                        with ctl.bounded(time.time()+.02):
                            time.sleep(.05)
                    if case=='worker':return 1
                    raise OSError('launch')
                ctl_prepare=ctl.prepare
                if case in ('room','storage','extract','copy','unpack'):
                    attr={'room':'room','storage':'storage_proof','extract':'extract_stream','copy':'copy_parts','unpack':'unpack'}[case]
                    setattr(J if case=='storage' else S,attr,failed)
                # Reach archive failures without materializing unapproved external inputs.
                if case in ('copy','unpack'):
                    cfg['assets']['groups']=[[['/tmp/0',0,'0']]]
                    C.store(p/'2.json',cfg)
                    C.store(p/'2.json',cfg)
                try:
                    with patch.dict(os.environ,{'A_M':mode,'SLURM_JOB_ID':'123'}), \
                         patch.object(ctl,'check',side_effect=failed if case=='check' else lambda p:current), \
                         patch.object(ctl,'materialize',side_effect=failed if case=='materialize' else lambda *a:(S,J)), \
                         patch.object(ctl,'prepare',side_effect=prepare),patch.object(ctl,'launch',side_effect=launch):
                        self.assertEqual(ctl.work(p,root),1)
                finally:
                    # Restore codec helper altered only for the synthetic extraction case.
                    if case in ('copy','unpack'): C.materialize=ORIGINAL_MATERIALIZE
                if case in ('check','materialize','room','storage','extract','copy','unpack'):
                    self.assertEqual(injected,[case])
                dest=p/'f';ctl.fetch(p,dest,mode)
                receipt=ctl.read(dest/'1.json');self.assertFalse(receipt['passed'])
                returned=members((dest/'0.tgz').read_bytes())
                self.assertIn('1.json',returned)
                if case in ('launch','worker','timeout','alarm'):
                    self.assertEqual(len(returned['0.jsonl'].splitlines()),2)
                if case != 'worker':
                    diagnostic=C.loads(returned['2.json'])
                    self.assertIn('Traceback',diagnostic['traceback'])
                    self.assertLessEqual(len(diagnostic['traceback'].splitlines()),200)
                scan(dest)
                results.append(dict(mode=mode,case=case,receipt=receipt))
        EVIDENCE['failure_fetches']=results

    def test_03_bounded_launch_and_staging(self):
        src=(ROOT/'src/control.py').read_text()
        self.assertIn('timeout=remaining',src);self.assertIn('timeout=60',src)
        with self.assertRaises(ctl.Deadline):
            with ctl.bounded(time.time()+.01):time.sleep(.02)
        for n in ('room','storage_proof','copy_parts','unpack','extract_stream'):
            self.assertIn(n,src)
        p,cfg,_=package();root=p/'z';root.mkdir();local=root/'p';local.mkdir()
        J=types.SimpleNamespace(environment=lambda r:{'PATH':'/usr/bin'},namespace=lambda r:['0'])
        with patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'0'}),patch.object(ctl.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
            ctl.launch(root,local,cfg,'g',time.time()+30,J)
            self.assertGreater(run.call_args.kwargs['timeout'],0)
            self.assertLessEqual(run.call_args.kwargs['timeout'],30)

    def test_04_native_cpu_batch_parity(self):
        import torch
        tests=types.ModuleType('tests');tests.__path__=[str(ROOT/'in/D400/src/tree/tests')];sys.modules['tests']=tests
        from tests.test_carrier_c1_final import final_fixture,FakeTokenizer
        model,batch,_=final_fixture();model.eval()
        class Tokenizer(FakeTokenizer):
            pad_token_id=0
            def decode(self,ids,skip_special_tokens=False):return ''.join('x'+str(i)+' ' for i in ids)
        processor=types.SimpleNamespace(tokenizer=Tokenizer(),_routing_tokens={'ids':{'<pose':33}})
        rows=[]
        for i in range(8):
            row={k:v.clone() if isinstance(v,torch.Tensor) else copy.deepcopy(v) for k,v in batch.items() if k!='labels'}
            for key in ('input_ids','attention_mask','mm_token_type_ids'):
                value=10+i if key=='input_ids' else int(key=='attention_mask')
                row[key]=torch.cat((row[key],row[key].new_full((1,3*i),value)),1)
            rows.append(row)
        from student_pilot.carrier_c1_decode import _prepare_decode,consume_cache_tokens
        from student_pilot.ground_context import closed_adapters
        expected=[]
        t0=time.monotonic()
        with torch.no_grad():
            for row in rows:
                state=closed_adapters(_prepare_decode)(model,processor,row,max_new_tokens=None)
                cache=[state.output.past_key_values]
                def choose(out):
                    logits=out.logits[:,-1,:].float().clone()
                    logits[:,[processor.tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>','</tool_response>')]+[model.carrier_id]]=-float('inf')
                    return logits.argmax(-1).item()
                def advance(ids):
                    full=torch.cat((row['input_ids'],row['input_ids'].new_tensor([ids])),1)
                    attn=torch.cat((row['attention_mask'],row['attention_mask'].new_ones((1,len(ids)))),1)
                    out,cache[0]=consume_cache_tokens(state.native,full,attn,cache[0],observer=state.stream)
                    return out
                expected.append(probe.decode(state.output,choose,advance,processor.tokenizer,{processor.tokenizer.eos_token_id}))
            serial_s=time.monotonic()-t0;t0=time.monotonic()
            actual={};metrics={};batched.generate(model,processor,rows,probe,lambda i,r:actual.__setitem__(i,r),metrics=metrics)
            self.assertGreater(metrics['prefill_s'],0)
            self.assertGreater(metrics['max_step_s'],0)
            self.assertEqual(metrics['steps'],64)
            batch_s=time.monotonic()-t0
        self.assertEqual(expected,[actual[i] for i in range(8)])
        self.assertTrue(any(r['n']==64 for r in expected))
        EVIDENCE['native_cpu_parity']=dict(rows=8,lengths=[r['input_ids'].shape[1] for r in rows],
            tokens=[r['tokens'] for r in expected],identical=True,serial_s=serial_s,batch_s=batch_s,
            scope='Tiny native hybrid model on CPU; full checkpoint GPU parity and speed remain unmeasured')

    def test_05_actual_cpu_rehearsal_and_scan(self):
        import torch
        from parity_kit import stage_restore
        from student_pilot import carrier_c1_run as trainer,carrier_c1_canary
        from e2e_reader import parity
        p,cfg,_=package();d=p/'d';d.mkdir();cfg['logical']=str(p)
        cfg['inputs']['frames_root']=str(d/'f');(d/'f').mkdir()
        (d/'f/0').write_bytes(b'0')
        data=C.loads(FILES['1.json'])
        for cap in data['captures'].values():
            for f in cap['frames']:f.update(path='0',sha256=hashlib.sha256(b'0').hexdigest())
        C.store(p/'1.json',data);C.store(p/'2.json',cfg)
        # Build a tiny authenticated export; the real restore verifies every
        # hash/size and writes its normal metadata through the opaque Path view.
        base=d/'b';base.mkdir();weights=d/'m400/full_weights';weights.mkdir(parents=True)
        def put(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            raw=B.jd(value);path.write_bytes(C.pack(raw));return dict(bytes=len(raw),sha256=B.digest(raw))
        asset_names=('config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json')
        assets={}
        for name in asset_names:
            (base/name).write_bytes(b'{}');assets[name]=B.digest(b'{}')
        original=B.jd(dict(schema='p3-model-input-v1',base_identity='a',files=assets))
        archive=d/'o/0.tgz';archive.parent.mkdir();archive.write_bytes(B.archive({'model.json':original}))
        (weights/'0.bin').write_bytes(b'0')
        index=dict(weight_map={'x':'0.bin'})
        ix=put(weights/'0.json',index)
        full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='0.bin',bytes=1,sha256=B.digest(b'0'))],
                  index=dict(name='0.json',**ix),tensor_count=1)
        fp=put(weights/'full_weights.json',full)
        (d/'m400/heads.pt').write_bytes(b'0')
        artifact=dict(config_sha256='a'*64,base_identity='a',frame_layout='duplicate',
                      full_weights=fp,heads=dict(sha256=B.digest(b'0')))
        ap=put(d/'m400/artifact.json',artifact)
        receipt=dict(config_sha256='a'*64,frame_layout='duplicate',camera={},depth={},
                     model=dict(path='/a',sha256=B.digest(original)))
        rp=put(d/'p0/receipt.json',receipt)
        config=dict(base_identity='a',frame_layout='duplicate',preparation=dict(path='/a',sha256=rp['sha256']))
        cp=put(d/'p0/config.json',config)
        data_receipt=dict(status='PREPARED',schema='s1-in-job-data-v1',config=dict(path='/b',sha256=cp['sha256']),
                          preparation=config['preparation'],real_frames_verified=True,rehearsal=False)
        dp=put(d/'p0/data_receipt.json',data_receipt)
        pins=dict(artifact=ap,preparation={name:dict(path='p0/'+filename,source_path=source,**pin) for name,filename,source,pin in
            [('config','config.json','/b',cp),('receipt','receipt.json','/a',rp),('data_receipt','data_receipt.json','/c',dp)]})
        for name,path in [('full_weights',weights/'full_weights.json'),('artifact',d/'m400/artifact.json'),
                          ('base_config',base/'config.json'),('original_model',archive)]:
            cfg['inputs']['files'][name]['path']=str(path)
        C.store(p/'2.json',cfg)
        real_stage=stage_restore.stage
        def preparation(*args,**kw):
            kw['export_pins']=pins
            return real_stage(*args,**kw)
        processor=types.SimpleNamespace(tokenizer=types.SimpleNamespace(decode=lambda *a,**k:'<ground'))
        def prompt(processor,row,cfg):
            self.assertNotIn('ground_truth',row)
            return dict(input_ids=torch.tensor([[2,3]]),attention_mask=torch.ones((1,2),dtype=torch.long),
                        pixel_values_videos=torch.zeros((2,4)),video_grid_thw=torch.tensor([[1,2,2]]))
        runtime=mod('actual_runtime',p/'5.py')
        # The production runtime, loader, binder, prompt adapter and all output
        # writes run. Only external weights/RGB processing use CPU doubles.
        with patch.object(stage_restore,'stage',side_effect=preparation), \
             patch.object(stage_restore,'prove_depth',return_value=dict(passed=True)), \
             patch.object(trainer,'processor_for_receipt',return_value=processor), \
             patch.object(carrier_c1_canary,'prompt_batch',side_effect=prompt), \
             patch.object(parity,'load_native',side_effect=AssertionError('model loaded')):
            runtime.run(p,'c',time.time()+60)
        self.assertTrue(C.loads((p/'a/1.json').read_bytes())['passed'])
        files=scan(p)
        EVIDENCE['cpu_rehearsal']=dict(files=files,passed=True,entry='delivered 5.py run(c)',
            doubles=['tiny authenticated export inputs','head-shape proof','processor construction','RGB processor'],
            real=['stage_restore.stage','opaque importer','runtime.run','trainer_row','evalpath.prompt_batch','receipt/output writes','all created file scans'])
        # Deliberate leak must fail the same scanner.
        (p/'12.json').write_text('{"x":"gro\\u0075nd"}')
        with self.assertRaises(AssertionError):scan(p)

    def test_06_archive_filter_and_encoded_metadata(self):
        import orchard_stage as stage
        root=fresh()
        raw=B.archive({'p0/config.json':b'{"ground":"reader"}', 's/sam.py':b'forbidden','b/config.json':b'{}'})
        inv=stage.extract_stream(io.BytesIO(raw),root,None,100000,retain_roots=('p0','b'))
        self.assertNotIn('s/sam.py',inv)
        self.assertEqual(C.loads((root/'p0/config.json').read_bytes()),{'ground':'reader'})
        scan(root)

    def test_07_partial_pair_writer_and_fetch(self):
        runtime=mod('partial_runtime',ROOT/'src/runtime.py');runtime.C=C
        p,cfg,_=package();records=p/'z/a';records.mkdir(parents=True)
        rows=[dict(i=str(i//2),r='a',a=i%2) for i in range(8)]
        progress=[0]
        with (records/'0.jsonl').open('wb') as stream:
            writer=runtime.PairWriter(stream,rows,progress,time.monotonic())
            item=dict(text='<ground',tokens=[27,1884],n=2,g=True,o=[],finish='call')
            writer.emit(0,dict(item));self.assertEqual(stream.tell(),0)
            writer.emit(1,dict(item));self.assertEqual(progress,[2])
            writer.emit(3,dict(item));self.assertEqual(progress,[2])
        with (records/'0.jsonl').open('ab') as f:f.write(b'{"a0":"7b')
        (records/'1.json').write_bytes(b'{')
        ctl.finalize(p,records,cfg,'g','123',time.time(),1,ctl.Deadline())
        ctl.fetch(p,p/'f');returned=members((p/'f/0.tgz').read_bytes())
        result=[C.loads(line) for line in returned['0.jsonl'].splitlines()]
        self.assertEqual([(r['i'],r['a']) for r in result],[('0',0),('0',1)])
        self.assertEqual(C.loads(returned['1.json'])['records'],2)
        self.assertFalse(ctl.read(p/'f/1.json')['passed'])
        for name,raw in returned.items():
            self.assertFalse(any(w.encode() in raw.lower() for w in B.DENY))
        EVIDENCE['partial_pairs']=dict(completed_pairs=1,unfinished_arm_omitted=True,real_fetch=True)

    def test_08_worker_traceback_real_entry_and_fetch(self):
        results=[]
        for mode in ('c','g'):
            p,cfg,_=package(); local=p/'z/p'; local.mkdir(parents=True)
            for n,v in FILES.items(): (local/n).write_bytes(v)
            broken=dict(cfg); broken.pop('logical')
            C.store(local/'2.json',broken)
            # Run the delivered worker's real exception handler before any
            # model import, GPU use or access to external inputs.
            result=subprocess.run([sys.executable,'-I','-s','-B',str(local/'5.py'),str(local),mode,str(time.time()+30)],
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
            self.assertEqual(result.returncode,1)
            self.assertEqual((result.stdout,result.stderr),(b'',b''))
            ctl.finalize(p,local/'a',cfg,mode,'123',time.time(),1)
            ctl.fetch(p,p/'f',mode)
            returned=members((p/'f/0.tgz').read_bytes())
            diagnostic=C.loads(returned['4.json'])
            self.assertIn('KeyError',diagnostic['traceback'])
            self.assertIn('logical',diagnostic['traceback'])
            self.assertIn('line ',diagnostic['traceback'])
            scan(p/'f')
            results.append(dict(mode=mode,traceback=diagnostic['traceback'],real_worker=True,real_fetch=True))
        EVIDENCE['worker_tracebacks']=results

    def test_09_bounded_diagnostics_and_both_failures(self):
        p,cfg,_=package(); records=p/'z';records.mkdir()
        runtime=mod('error_runtime',p/'5.py');runtime.C=C
        def failed(*unused): raise RuntimeError(('ground reader word\n'*400)+'student tail')
        with patch.object(runtime,'run',side_effect=failed):
            self.assertEqual(runtime.main(p,'c',time.time()+20),1)
        worker=C.loads((p/'a/4.json').read_bytes())
        self.assertLessEqual(len(worker['traceback'].splitlines()),200)
        self.assertIn('student tail',worker['traceback'])
        try: raise RuntimeError('tower launch')
        except RuntimeError as error:
            ctl.finalize(p,p/'a',cfg,'c','123',time.time(),1,error)
        ctl.fetch(p,p/'f','c');returned=members((p/'f/0.tgz').read_bytes())
        self.assertIn('tower launch',C.loads(returned['2.json'])['traceback'])
        self.assertIn('student tail',C.loads(returned['4.json'])['traceback'])
        scan(p/'f')
        with self.assertRaises(ValueError):ctl.fetch(p,p/'f2','word')
        EVIDENCE['bounded_tracebacks']=dict(lines=len(worker['traceback'].splitlines()),both_preserved=True,deny_scan=True)

    def test_10_slow_batch_admission_and_timing_fetch(self):
        runtime=mod('timing_runtime',ROOT/'src/runtime.py');runtime.C=C
        for slow in (True,False):
            p,cfg,_=package(); out=p/'z';out.mkdir()
            now=[1000.]; progress=[0]; calls=[]
            rows=[dict(i=str(i//2),r='a',a=i%2) for i in range(16)]
            def prepare(group):now[0]+=2;return group
            def generate(group,emit,deadline,metrics):
                calls.append(len(group));now[0]+=40 if slow else 4
                metrics.update(prefill_s=10 if slow else 1,max_step_s=2 if slow else .02,steps=3)
                for i in range(len(group)):emit(i,dict(text='x',n=3,tokens=[1,1,1]))
            with patch.object(runtime.time,'time',side_effect=lambda:now[0]),patch.object(runtime.time,'monotonic',side_effect=lambda:now[0]):
                status=runtime.run_batches(out,rows,progress,1200,prepare,generate,lambda:None)
            self.assertEqual(calls,[8] if slow else [8,8])
            self.assertEqual(status,'timeout' if slow else 'complete')
            self.assertEqual(progress,[8] if slow else [16])
            C.store(out/'1.json',dict(passed=False,records=progress[0],status=status))
            ctl.finalize(p,out,cfg,'g','123',time.time(),0)
            ctl.fetch(p,p/'f');returned=members((p/'f/0.tgz').read_bytes())
            timing=[C.loads(line) for line in returned['3.jsonl'].splitlines()]
            self.assertEqual(len(timing),2)
            self.assertEqual(timing[0]['completed_pairs'],4)
            self.assertEqual(timing[0]['elapsed_s'],42 if slow else 6)
            if slow:
                self.assertEqual(timing[1]['status'],'not_admitted')
                self.assertGreater(timing[1]['required_s']+10,timing[1]['remaining_s'])
            result=[C.loads(line) for line in returned['0.jsonl'].splitlines()]
            self.assertEqual(len(result),progress[0])
            self.assertTrue(all((result[j]['a'],result[j+1]['a'])==(0,1) for j in range(0,len(result),2)))
            scan(p/'f')
            EVIDENCE['batch_admission_'+str(slow)]=dict(timing=timing,complete_pairs=progress[0]//2,real_fetch=True)



ORIGINAL_MATERIALIZE=C.materialize
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Fixes))
    (ROOT/'out/FIX_CHECKS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),tests=result.testsRun,evidence=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
