"""CPU contracts: no weights, CUDA, remote calls, or scheduler calls."""
import ast
import asyncio
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from evalpath import official
from media import frame_list,kwargs
from parity import trainer_encode,prompt,compare
from scoring import score_item,benchmark_summary,metric_for
from worker import append,read_journal
from data import tasks_for
from common import sha
import bind_vl


def retained():
    return Path(tempfile.mkdtemp(dir=ROOT/'checks'))


def definitions(path):
    source=Path(path).read_text()
    return {n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        cls.processor=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        cls.processor._student_pilot_student='qwen35'

    def test_01_source_closure(self):
        pins=json.loads((ROOT/'evaluator/evalpath/SOURCE_PINS.json').read_text())
        defs=definitions(ROOT/'evaluator/evalpath/official.py')
        for source in ('run_eval.py','score_and_aggregate.py'):
            for name,expected in pins[source]['functions'].items():
                self.assertEqual(hashlib.sha256(defs[name].encode()).hexdigest(),expected)
        self.assertEqual(sha(ROOT/'evaluator/evalpath/sampling.py'),'9235a822a813648ee0da7cf9cc79531a4cbb7b6344e8fee369e5b34e615d82e1')
        for src,dest in [('batches.py','batches.py'),('pose_samples.py','pose_samples.py'),('carrier_c1_data.py','layout_reference.py')]:
            original=definitions(ROOT/'inputs/trainer_sources'/src)
            for name,body in definitions(ROOT/'evaluator/trainer'/dest).items():
                if dest=='layout_reference.py' and name=='layout_inputs':
                    # The opt-in adapter is checked against this pinned original in X1.
                    self.assertEqual(definitions(ROOT/'checks/X1_BASELINE/layout_before.py')[name],original[name])
                elif dest=='batches.py' and name=='training_text':
                    adapter=json.loads((ROOT/'inputs/TRAINER_ADAPTER.json').read_text())
                    self.assertEqual(body.replace(adapter['added_branch'],''),original[name])
                    self.assertEqual(sha(ROOT/'evaluator/trainer/batches.py'),adapter['adapted_sha256'])
                else:self.assertEqual(body,original[name])
        self.assertTrue(sha(ROOT/'evaluator/metric.py').startswith('aa0c7968'))

    def test_02_real_prompt_bytes_20_each(self):
        source=ROOT/'checks/X1_BASELINE/rows.json'
        value=json.loads(source.read_text())
        vsi=value if isinstance(value,list) else value['items']
        revsi=json.loads((ROOT/'inputs/revsi_rows.json').read_text())
        from trainer.batches import training_text
        observed=[]
        parent=self.processor
        class Capture:
            def __getattr__(self,key):return getattr(parent,key)
            def apply_chat_template(self,messages,**kw):
                observed.append(messages[0]['content'][1]['text'])
                return parent.apply_chat_template(messages,**kw)
        counts={}
        for name,rows in [('vsi500',vsi),('revsi',revsi)]:
            for r in rows[:20]:
                observed.clear()
                p,_=training_text(Capture(),r['question'],r.get('options') or [],'0\n')
                expected=official.build_prompt_context(r,'ours').encode()
                self.assertTrue(observed)
                self.assertTrue(all(s.encode()==expected for s in observed))
                self.assertEqual(p,prompt(parent,r))
            counts[name]=20
        (ROOT/'checks/PROMPT_BYTES.json').write_text(json.dumps(counts)+'\n')

    def test_03_layouts_against_trainer(self):
        from trainer.layout_reference import layout_inputs
        fps,total=10.,2000
        anchors=list(range(0,960,30))
        si=dict(frames=[dict(path=str(i),sha256='a'*64) for i in anchors],frame_indices=anchors,
                timestamps=[i/fps for i in anchors],fps=fps,total_num_frames=total,recording_id='r')
        for layout in ('spread','duplicate','P0.5','P0.2'):
            row={'student_input':deepcopy(si)}
            gap=float(layout[1:]) if layout.startswith('P') else None
            if gap:
                row['student_input']['partner_frames']=[dict(path='x',sha256='b'*64,recording_id='r',
                    frame_index=i+round(gap*fps),timestamp=(i+round(gap*fps))/fps) for i in anchors]
            expected=layout_inputs(row,'paired' if gap else layout,gap)
            observed,fallback=frame_list(anchors,fps,total,layout)
            self.assertEqual(observed,expected['frame_indices'])
            self.assertEqual([i/fps for i in observed],expected['timestamps'])
            self.assertFalse(fallback)
        edge=[k*999//31 for k in range(32)]
        observed,fallback=frame_list(edge,10.,1000,'P0.5')
        self.assertEqual(observed[-2:],[999,994]);self.assertEqual(fallback,[999])
        # Nonintegral FPS uses nearest source frame; timestamps report the realized gap.
        expanded,_=frame_list(edge,29.97,1000,'P0.2')
        self.assertEqual(expanded[1]-expanded[0],6)
        self.assertEqual(kwargs(64)['size']['longest_edge'],64*384*384)

    def test_04_cpu_pixels_and_ids(self):
        import torch
        from transformers.video_utils import VideoMetadata
        task=dict(question='How many chairs?',options=[],benchmark='vsi500',example_id='0')
        arrays=np.zeros((32,56,56,3),dtype=np.uint8)
        arrays[:,1,1,0]=np.arange(32)
        for layout in ('spread','duplicate','P0.5','P0.2'):
            indices,_=frame_list(list(range(0,960,30)),10.,2000,layout)
            video=arrays if layout=='spread' else np.repeat(arrays,2,axis=0)
            meta=dict(total_num_frames=2000,fps=10.,frames_indices=indices,height=56,width=56)
            batch,audit=trainer_encode(self.processor,task,video,meta,dict(layout=layout,benchmarks=['vsi500']))
            plain=self.processor(text=[prompt(self.processor,task)],videos=[video],video_metadata=[VideoMetadata(**meta)],
                    **kwargs(len(video)),return_tensors='pt',return_metadata=True)
            self.assertTrue(torch.equal(batch['pixel_values_videos'],plain['pixel_values_videos']))
            self.assertTrue(torch.equal(batch['video_grid_thw'],plain['video_grid_thw']))
            ids=plain['input_ids'][0].tolist()
            self.assertEqual(ids,batch['input_ids'][0,:audit['prompt_tokens']].tolist())
            # Failed registry introspection cannot certify vLLM pixels.
            with patch('parity.processor_evidence',return_value=(None,dict(vllm_processor_class_verified=False))):
                c=compare(self.processor,object(),task,video,meta,ids,True,cell=dict(layout=layout,benchmarks=['vsi500']))
            self.assertTrue(c['prompt_equal']);self.assertFalse(c['pixels']['pass'])

    def test_05_official_scoring_and_cap(self):
        t=dict(benchmark='vsi500',example_id='1',question_type='object_counting',ground_truth='10',options=[])
        r=score_item(dict(t,thinking=True),'\n</think>\n10',12)
        self.assertEqual(r['score'],1.);self.assertTrue(r['empty_think'])
        self.assertEqual(score_item(dict(t,thinking=True),'unfinished',16384,finish='length')['score'],0.)
        self.assertTrue(score_item(dict(t,thinking=True),'unfinished',16384,finish='length')['hit_token_cap'])
        rec={**t,**r,'status':'complete'}
        good=benchmark_summary([rec],[t],True)
        bad=benchmark_summary([rec],[t],False)
        self.assertEqual(good['numbers_status'],'eligible');self.assertEqual(bad['numbers_status'],'do not count')
        self.assertEqual(good['overall_score'],1.)
        vsti={**t,'benchmark':'vstiv3','question_type':'camera_obj_abs_dist'}
        self.assertEqual(benchmark_summary([{**vsti,**r,'status':'complete'}],[vsti],True)['overall_score'],1.)

    def test_06_revsi_official_metric(self):
        rows=json.loads((ROOT/'inputs/revsi_rows.json').read_text())
        records=[]
        for t in rows:
            r=score_item(dict(t,thinking=True),'reason\n</think>\n'+str(t['ground_truth']),5)
            records.append({**t,**r,'status':'complete'})
        s=benchmark_summary(records,rows,True)
        self.assertAlmostEqual(s['overall_score'],1.)
        self.assertEqual(len(s['per_category']),7)
        self.assertEqual(s['visible_32']['count'],350)
        self.assertAlmostEqual(s['visible_32']['official_metric']['overall_acc'],100.)
        for question_type in metric_for(rows).mcq_question_types:
            t=next(t for t in rows if t['question_type']==question_type)
            self.assertEqual(score_item(dict(t,thinking=True),'</think>\nZ',5)['score'],0.)

    def test_07_resume_partial_journal(self):
        p=retained()/'0.jsonl'
        append(p,dict(key='a',binding='x',status='complete',layout='duplicate'))
        with p.open('a') as f:f.write('{"partial":')
        append(p,dict(key='b',binding='x',status='error',layout='duplicate'))
        self.assertEqual(set(read_journal(p,'x','duplicate')),{'a'})
        with self.assertRaises(ValueError):read_journal(p,'y','duplicate')

    def test_08_bind_roundtrips(self):
        results=[]
        for preset,count in [('P4',3),('references',2),('E11c',2)]:
            args=bind_vl.parser().parse_args(['--preset',preset,'--models',str(ROOT/'inputs/MODELS.example.json'),
                                            '--gpu-cap','8','--build-only'])
            r=bind_vl.bind(args)
            self.assertEqual(len(r['cells']),count)
            with tarfile.open(ROOT/'kit/k/1.tar') as tf:
                restored=json.load(tf.extractfile('0.json'))
                self.assertEqual(restored,r)
                for spec in restored['datasets']:
                    for k in ('rows','membership','indices'):
                        if spec.get(k,{}).get('path','').startswith('$Q/'):
                            self.assertEqual(hashlib.sha256(tf.extractfile(spec[k]['path'][3:]).read()).hexdigest(),spec[k]['sha256'])
            results.append(dict(preset=preset,cells=count,roundtrip=True))
        (ROOT/'checks/BIND.json').write_text(json.dumps(results,indent=1)+'\n')
        with self.assertRaises(ValueError):bind_vl.validate_models({}, {'base'},True)
        args=bind_vl.parser().parse_args(['--preset','E11c','--models',str(ROOT/'inputs/MODELS.example.json'),
                                         '--gpu-cap','1','--build-only'])
        with self.assertRaises(ValueError):bind_vl.bind(args)

    def test_09_archive_staging(self):
        from stage import prepare
        from common import archive
        d=retained();base=d/'b';base.mkdir()
        (base/'config.json').write_text('{"model_type":"qwen3_5"}')
        (base/'tokenizer_config.json').write_text('{}')
        (base/'model.safetensors.index.json').write_text('{"weight_map":{"x":"absent.safetensors"}}')
        artifact=d/'0.tar'
        archive(artifact,{'full_weights/model.safetensors':b'synthetic-only'})
        model=prepare(dict(kind='archive',path=str(artifact),sha256=sha(artifact)),base,d/'m')
        self.assertEqual((model/'config.json').read_bytes(),(base/'config.json').read_bytes())
        self.assertEqual((model/'model.safetensors').read_bytes(),b'synthetic-only')
        self.assertFalse((model/'model.safetensors.index.json').exists())
        with self.assertRaises(ValueError):prepare(dict(kind='archive',path=str(artifact),sha256='0'*64),base,d/'n')

    def test_10_worker_failure_resume_and_merge(self):
        import worker
        from merge import merge
        d=retained()
        tasks=[dict(benchmark='vsi500',example_id=str(i),question_type='object_counting',ground_truth='10',
                    question='How many?',options=[]) for i in range(16)]
        config=dict(cells=[dict(model='base',layout='duplicate',benchmarks=['vsi500'])],datasets=[dict(benchmark='vsi500')],
                    roots={},binding='test',output=str(d/'out'),max_model_len=49152,max_seqs=16,inflight=4,gpus=1)
        cfg=d/'0.json';cfg.write_text(json.dumps(config))
        calls=[];fail_once={'yes':True}
        processor=self.processor
        long='r '*5000+'\n</think>\n10'
        longids=processor.tokenizer.encode(long,add_special_tokens=False)
        class Engine:
            @classmethod
            def from_engine_args(cls,args):return cls()
            async def generate(self,req,params,request_id):
                calls.append((request_id,req,params))
                if request_id=='gvsi500:9' and fail_once['yes']:
                    fail_once['yes']=False
                    raise RuntimeError('synthetic item error')
                raw=long if request_id=='gvsi500:1' else '</think>\n10'
                ids=longids if request_id=='gvsi500:1' else processor.tokenizer.encode(raw,add_special_tokens=False)
                yield SimpleNamespace(prompt_token_ids=[1,2],outputs=[SimpleNamespace(text=raw,token_ids=ids,finish_reason='stop')])
            def shutdown(self):pass
        modules={n:types.ModuleType(n) for n in ['vllm','vllm.engine','vllm.engine.arg_utils','vllm.sampling_params',
                                                'vllm.v1','vllm.v1.engine','vllm.v1.engine.async_llm']}
        modules['vllm'].SamplingParams=lambda **kw:SimpleNamespace(**kw)
        modules['vllm'].__version__='0.32.0'
        modules['vllm.engine.arg_utils'].AsyncEngineArgs=lambda **kw:SimpleNamespace(**kw)
        modules['vllm.sampling_params'].RequestOutputKind=SimpleNamespace(FINAL_ONLY=1)
        modules['vllm.v1.engine.async_llm'].AsyncLLM=Engine
        def check(p,e,t,a,m,ids,pixels=False,cell=None):
            c=dict(benchmark=t['benchmark'],example_id=t['example_id'],prompt_equal=t['example_id']!='3')
            if pixels:c['pixels']={'pass':True}
            return c
        async def inline_thread(fn,*args,**kw):
            # This sandbox cannot wake asyncio's selector from a worker thread.
            # CPU mocks need no executor; AWS retains asyncio.to_thread unchanged.
            return fn(*args,**kw)
        args=SimpleNamespace(config=str(cfg),cell=0,rank=0,world=1,model='synthetic',cache=str(d/'cache'),
                             frames_sha256='synthetic',attempt='a')
        with patch.dict(sys.modules,modules),patch('transformers.AutoProcessor.from_pretrained',return_value=processor),\
             patch('worker.tasks_for',return_value=tasks),patch('merge.tasks_for',return_value=tasks),\
             patch('worker.load',return_value=(np.zeros((64,8,8,3),np.uint8),{'metadata':{}})),\
             patch('worker.compare',side_effect=check),patch('worker.asyncio.to_thread',side_effect=inline_thread),\
             patch('asyncio.BaseEventLoop.set_default_executor'):
            asyncio.run(worker.run(args))
            result=merge(config,0,'a')['benchmarks']['vsi500']
            self.assertEqual(result['completed'],15)
            self.assertEqual(result['numbers_status'],'do not count')
            self.assertEqual(len(calls),32)
            first=read_journal(d/'out/0/g0.jsonl',__import__('evalpath.items',fromlist=['digest']).digest({'request':'test','cell':0}))
            self.assertEqual(first['vsi500:1']['score'],1.)
            self.assertEqual(first['vsi500:1']['at_4096']['score'],0.)
            self.assertTrue(first['vsi500:1']['at_4096']['hit_token_cap'])
            asyncio.run(worker.run(args))
            result=merge(config,0,'a')['benchmarks']['vsi500']
            self.assertEqual(result['completed'],16)
            self.assertEqual(result['numbers_status'],'do not count')
            self.assertEqual(len(calls),49) # Every invocation checks parity; only the failed item regenerates.
            self.assertTrue(all(c[1]['mm_processor_kwargs']==kwargs(64) for c in calls))
            self.assertTrue(all(c[2].temperature==0 for c in calls))
            parity_path=d/'out/0/p0_a.json'
            parity=json.loads(parity_path.read_text())
            for c in parity['checks']:c['prompt_equal']=True
            parity_path.write_text(json.dumps(parity))
            result=merge(config,0,'a')['benchmarks']['vsi500']
            self.assertEqual(result['numbers_status'],'eligible')
            self.assertEqual(result['completed'],16)
            config['smoke_items']=16
            self.assertEqual(merge(config,0,'a')['benchmarks']['vsi500']['numbers_status'],'do not count')

    def test_11_real_pyav_tier_and_original_indices(self):
        import av
        from fractions import Fraction
        from media import decode
        d=retained();p=d/'0.mp4'
        with av.open(str(p),'w') as container:
            stream=container.add_stream('mpeg4',rate=1)
            stream.width=32;stream.height=32;stream.pix_fmt='yuv420p'
            for i in range(32):
                frame=av.VideoFrame.from_ndarray(np.full((32,32,3),i*4,dtype=np.uint8),format='rgb24')
                for packet in stream.encode(frame):container.mux(packet)
            for packet in stream.encode():container.mux(packet)
        source=[k*319//31 for k in range(32)]
        task=dict(benchmark='revsi',video_path=str(p),source_frame_indices=source)
        pixels,audit=decode(task,'spread')
        self.assertEqual(len(pixels),32)
        self.assertEqual(audit['metadata']['frames_indices'],source)
        self.assertEqual(audit['metadata']['fps'],10.)
        self.assertEqual(audit['metadata']['total_num_frames'],320)
        task={'benchmark':'vsi500','video_path':str(p)}
        _,audit=decode(task,'P0.5')
        self.assertEqual(audit['metadata']['frames_indices'][-2:],[31,30])

    def test_12_official_slice_and_custom_binding(self):
        d=retained();cells=d/'cells.json'
        cells.write_text(json.dumps([dict(model='base',layout='spread',benchmarks=['official5130'])]))
        args=bind_vl.parser().parse_args(['--preset','custom','--cells',str(cells),'--models',str(ROOT/'inputs/MODELS.example.json'),
                                        '--gpu-cap','8','--slice','137','--seed','23','--build-only'])
        r=bind_vl.bind(args)
        with tarfile.open(ROOT/'kit/k/1.tar') as tf:
            for member in tf.getmembers():
                target=d/member.name;target.write_bytes(tf.extractfile(member).read())
        spec=r['datasets'][0]
        spec['rows']['path']=str(d/Path(spec['rows']['path']).name)
        first=tasks_for(spec,r['roots']);second=tasks_for(spec,r['roots'])
        self.assertEqual(len(first),137);self.assertEqual(first,second)
        spec['seed']=24
        self.assertNotEqual(first,tasks_for(spec,r['roots']))



if __name__=='__main__':unittest.main(verbosity=2)
