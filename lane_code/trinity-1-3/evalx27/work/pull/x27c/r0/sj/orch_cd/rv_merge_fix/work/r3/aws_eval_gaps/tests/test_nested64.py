"""CPU contracts for nested 64-frame grids, greedy binds, and anchor-slot reports."""
import asyncio
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import av
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
import bind_vl
from cells import frame_count
from common import save,sha
from data import tasks_for
from frame_stage import stage
from media import decode,identity,item_key,kwargs,load
from merge import merge
from nested_sampling import nested_indices
from parity import compare,prompt,trainer_encode
from trainer.layout_reference import layout_inputs
from test_frames import video
import test_frames64 as x1

DEV_ROWS=Path('/scratch/jjyeung/orch_cd/evalx/work/devpool/DEV_ITEMS.jsonl')
NESTED=dict(model='base',layout='spread',benchmarks=['vsi500','devrows'],frames=64,frame_set='nested')


def retained():
    return Path(tempfile.mkdtemp(prefix='x7_',dir=ROOT/'checks'))


class Nested64(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        cls.processor=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        cls.processor._student_pilot_student='qwen35'

    def test_nested_properties_and_exact_tie_order(self):
        for total in (64,65,66,67,80,94,95,97,125,1000,10001,1000000):
            with self.subTest(total=total):
                indices=nested_indices(total)
                anchors=[k*(total-1)//31 for k in range(32)]
                self.assertEqual(len(indices),64)
                self.assertEqual(indices,sorted(set(indices)))
                self.assertTrue(set(anchors)<=set(indices))
                self.assertEqual(indices[0],anchors[0]);self.assertEqual(indices[0],0)
                self.assertEqual(indices[-1],total-1)
        self.assertEqual(nested_indices(64),list(range(64)))
        # Equal width-4 gaps split left to right, then the first width-2 gap splits.
        self.assertEqual(nested_indices(125),sorted(list(range(0,125,4))+list(range(2,125,4))+[1]))
        # Odd width-3 gaps use the floor midpoint; the earliest width-2 gap goes next.
        self.assertEqual(nested_indices(94),sorted(list(range(0,94,3))+list(range(1,94,3))+[2]))
        for total in (0,1,16,31,32,40,63):
            with self.subTest(total=total),self.assertRaisesRegex(ValueError,'need 64'):
                nested_indices(total)

    def test_frame_set_and_benchmark_validation(self):
        for benchmarks in (['vsi500'],['devrows'],['vsi500_slice'],['vsi500','devrows'],
                           ['devrows','vsi500_slice','vsi500'],['official5130'],['official5130','vsi500']):
            for selection in ({},{'frame_set':'nested'}):
                self.assertEqual(frame_count({**NESTED,'benchmarks':benchmarks,**selection}),64)
                self.assertEqual(frame_count({k:v for k,v in {**NESTED,'benchmarks':benchmarks,**selection}.items()
                                              if k!='frame_set'}),64)
        for value in (None,'uniform','',False,32,[],{}):
            with self.subTest(frame_set=value),self.assertRaisesRegex(ValueError,'frame_set'):
                frame_count({**NESTED,'frame_set':value})
        for frames in (32,None):
            cell={**NESTED}
            if frames is None:cell.pop('frames')
            else:cell['frames']=frames
            with self.assertRaisesRegex(ValueError,'frame_set'):frame_count(cell)
        for layout in ('duplicate','paired','P0.2','P0.5'):
            with self.assertRaisesRegex(ValueError,'frames=64'):frame_count({**NESTED,'layout':layout})
        for benchmarks in ([],['revsi'],['pointing'],['pointing_video'],['vstiv3'],['official5130','revsi'],['devrows','revsi']):
            with self.assertRaisesRegex(ValueError,'frames=64'):frame_count({**NESTED,'benchmarks':benchmarks})

    def test_grid_build_binds_and_real_devrows(self):
        all_cells=json.loads((ROOT/'inputs/cells_grid.json').read_text())
        base=json.loads((ROOT/'inputs/cells_grid_base.json').read_text())
        t0=json.loads((ROOT/'inputs/cells_grid_t0.json').read_text())
        self.assertEqual(all_cells,base+t0)
        self.assertEqual([(c['model'],c['frames']) for c in all_cells],
                         [('base',32),('base',64),('t0m800',32),('t0m800',64)])
        evidence=[]
        for file in ('cells_grid.json','cells_grid_base.json','cells_grid_t0.json'):
            root=retained();a=x1.args(ROOT/'inputs'/file,root);a.dev_rows=DEV_ROWS
            cfg=bind_vl.bind(a)
            self.assertEqual(cfg['cells'],json.loads((ROOT/'inputs'/file).read_text()))
            self.assertEqual((cfg['temperature'],cfg['max_tokens'],cfg['thinking']),(0,16384,True))
            for cell in cfg['cells']:
                self.assertNotIn('decoding',cell)
                self.assertEqual(cell['benchmarks'],['vsi500','devrows'])
            with tarfile.open(root/'kit/k/1.tar') as tf:
                counts={}
                for spec in cfg['datasets']:
                    embedded={**spec}
                    for key,pin in spec.items():
                        if not isinstance(pin,dict) or not pin.get('path','').startswith('$Q/'):continue
                        name=pin['path'][3:];path=root/'metadata'/name;path.parent.mkdir(exist_ok=True)
                        path.write_bytes(tf.extractfile(name).read())
                        embedded[key]={**pin,'path':str(path)}
                    rows=tasks_for(embedded,cfg['roots'])
                    counts[spec['benchmark']]=len(rows)
                    if spec['benchmark']=='devrows':self.assertEqual(sha(embedded['rows']['path']),sha(DEV_ROWS))
            self.assertEqual(counts,dict(vsi500=500,devrows=858))
            evidence.append(dict(cells=file,counts=counts,binding=cfg['binding']))
        # A floor-uniform devrows-only 64-frame cell also binds without opt-in nesting.
        root=retained();path=root/'cells.json'
        cell={k:v for k,v in NESTED.items() if k!='frame_set'};cell['benchmarks']=['devrows']
        save(path,[cell]);a=x1.args(path,root/'bind');a.dev_rows=DEV_ROWS
        cfg=bind_vl.bind(a);self.assertEqual(cfg['cells'],[cell])
        self.assertEqual(cfg['datasets'][0]['rows']['sha256'],sha(DEV_ROWS))
        save(ROOT/'checks/X7_BIND.json',dict(build_only=True,dev_rows=str(DEV_ROWS),dev_rows_sha256=sha(DEV_ROWS),grids=evidence))

    def test_nested_decode_exact_pixels_and_anchor_slots(self):
        root=retained()
        for total,benchmark in ((64,'devrows'),(94,'vsi500_slice'),(125,'vsi500')):
            path=root/(str(total)+'.mp4');video(path,total,10)
            task=dict(benchmark=benchmark,video_path=str(path))
            arrays,audit=decode(task,'spread',64,'nested')
            anchors,official=decode(task,'spread')
            indices=nested_indices(total)
            self.assertEqual(audit['metadata']['frames_indices'],indices)
            self.assertEqual(audit['anchor_indices'],indices)
            slots=audit['anchor_slots']
            self.assertEqual(slots,sorted(set(slots)));self.assertEqual(len(slots),32)
            self.assertEqual(slots[0],0)
            self.assertEqual([indices[s] for s in slots],official['anchor_indices'])
            np.testing.assert_array_equal(arrays[slots],anchors)
            with av.open(str(path)) as c:
                all_frames=[f.to_ndarray(format='rgb24') for f in c.decode(video=0)]
            np.testing.assert_array_equal(arrays,np.stack([all_frames[i] for i in indices]))

    def test_nested_layout_and_prompt_pixel_parity(self):
        import torch
        from transformers.video_utils import VideoMetadata
        task=x1.slice_tasks()[0];p=self.processor
        indices=nested_indices(1000)
        slots=[indices.index(k*999//31) for k in range(32)]
        si=dict(frames=[dict(path=str(i),sha256='a'*64) for i in indices],frame_indices=indices,
                timestamps=[i/10 for i in indices],fps=10.,total_num_frames=1000,anchor_slots=slots)
        self.assertEqual(layout_inputs(dict(student_input=si),'spread',frames=64),si)
        cell={**NESTED,'benchmarks':['vsi500_slice']}
        arrays=np.arange(64*32*48*3,dtype=np.uint8).reshape(64,32,48,3)
        meta=dict(total_num_frames=1000,fps=10.,frames_indices=indices,height=32,width=48)
        batch,audit=trainer_encode(p,task,arrays,meta,cell)
        native=p(text=[prompt(p,task)],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
                 **kwargs(64),return_tensors='pt',return_metadata=True)
        ids=native['input_ids'][0].tolist()
        self.assertEqual(ids,batch['input_ids'][0,:audit['prompt_tokens']].tolist())
        self.assertEqual(audit['original_frame_indices'],indices)
        self.assertTrue(torch.equal(batch['pixel_values_videos'],native['pixel_values_videos']))
        self.assertTrue(torch.equal(batch['video_grid_thw'],native['video_grid_thw']))
        with patch('parity.processor_evidence',return_value=(p,dict(vllm_processor_class_verified=True))):
            result=compare(p,object(),task,arrays,meta,ids,True,cell=cell)
        self.assertTrue(result['prompt_equal']);self.assertTrue(result['pixels']['pass'])

    def test_cache_separation_worker_reports_errors_and_greedy_defaults(self):
        import worker
        root=retained();tasks=[]
        for name,total in (('long',125),('short',40)):
            path=root/(name+'.mp4');video(path,total,10)
            tasks.append(dict(benchmark='devrows',example_id=name,video_path=str(path),
                              question='How many chairs?',options=[],ground_truth='10',question_type='object_counting'))
        nested={**NESTED,'benchmarks':['devrows']}
        floor={k:v for k,v in nested.items() if k!='frame_set'}
        cfg=dict(cells=[{**floor,'frames':32},floor,nested,{**nested,'model':'t0m800'}],
                 datasets=[dict(benchmark='devrows')],roots={},binding='x7',source_sha256='s',
                 output=str(root/'out'),max_model_len=49152,max_seqs=8,inflight=2,gpus=1)
        path=root/'cfg.json';save(path,cfg)
        with patch('frame_stage.tasks_for',return_value=tasks):index=stage(path,root/'cache',1)
        self.assertEqual(index['decodes'],6);self.assertEqual(index['errors'],2)
        pin=sha(root/'cache/0.json')
        for task in tasks:
            variants=((32,None),(64,None),(64,'nested'))
            self.assertEqual(len({item_key(task,'spread',n,s) for n,s in variants}),3)
            self.assertEqual(len({json.dumps(identity(task,'spread',n,s),sort_keys=True) for n,s in variants}),3)
            for n,selection in variants:
                if task['example_id']=='short' and n==64:
                    with self.assertRaisesRegex(ValueError,'need 64'):load(task,'spread',root/'cache',pin,n,selection)
                else:
                    # Loading PNGs must work when PyAV is unavailable.
                    with patch.dict(sys.modules,{'av':None}):arrays,audit=load(task,'spread',root/'cache',pin,n,selection)
                    self.assertEqual(len(arrays),n)
                    if selection:self.assertEqual(len(audit['anchor_slots']),32)
        calls=[]
        class Engine:
            @classmethod
            def from_engine_args(cls,args):return cls()
            async def generate(self,req,params,request_id):
                calls.append((req,params,request_id))
                yield SimpleNamespace(prompt_token_ids=[1],outputs=[SimpleNamespace(text='</think>\n10',token_ids=[1],finish_reason='stop')])
            def shutdown(self):pass
        mods={n:types.ModuleType(n) for n in ('vllm','vllm.engine','vllm.engine.arg_utils','vllm.sampling_params',
              'vllm.v1','vllm.v1.engine','vllm.v1.engine.async_llm')}
        mods['vllm'].__version__='0.32.0';mods['vllm'].SamplingParams=lambda **kw:SimpleNamespace(**kw)
        mods['vllm.engine.arg_utils'].AsyncEngineArgs=lambda **kw:SimpleNamespace(**kw)
        mods['vllm.sampling_params'].RequestOutputKind=SimpleNamespace(FINAL_ONLY=1)
        mods['vllm.v1.engine.async_llm'].AsyncLLM=Engine
        async def inline(fn,*args,**kw):return fn(*args,**kw)
        def check(p,e,t,a,m,ids,pixels=False,cell=None):
            self.assertEqual(m['frames_indices'],nested_indices(125))
            r=dict(benchmark=t['benchmark'],example_id=t['example_id'],prompt_equal=True)
            if pixels:r['pixels']={'pass':True}
            return r
        a=SimpleNamespace(config=str(path),cell=2,rank=0,world=1,model='synthetic',cache=str(root/'cache'),
                          frames_sha256=pin,attempt='x7')
        with patch.dict(sys.modules,mods),patch('transformers.AutoProcessor.from_pretrained',return_value=self.processor),\
             patch('worker.tasks_for',return_value=tasks),patch('worker.compare',side_effect=check),\
             patch('worker.asyncio.to_thread',side_effect=inline),\
             patch('merge.tasks_for',return_value=tasks):
            asyncio.run(worker.run(a));summary=merge(cfg,2,'x7')
        rows={r['example_id']:r for r in map(json.loads,(root/'out/2/items_x7.jsonl').read_text().splitlines())}
        self.assertEqual(rows['long']['status'],'complete');self.assertEqual(rows['long']['frame_set'],'nested')
        self.assertEqual(rows['long']['anchor_slots'],rows['long']['media']['anchor_slots'])
        self.assertEqual(rows['long']['anchor_slots'][0],0);self.assertEqual(len(rows['long']['anchor_slots']),32)
        self.assertEqual(rows['short']['status'],'error');self.assertIsNone(rows['short']['anchor_slots'])
        self.assertIn('need 64',rows['short']['error'])
        self.assertEqual(summary['anchor_slots']['devrows:long'],rows['long']['anchor_slots'])
        self.assertEqual(summary['benchmarks']['devrows']['anchor_slots']['long'],rows['long']['anchor_slots'])
        generations=[(req,par) for req,par,k in calls if k.startswith('g')]
        self.assertEqual(len(generations),1)
        req,params=generations[0]
        self.assertEqual((params.temperature,params.max_tokens),(0,16384))
        self.assertTrue(req['prompt'].endswith('<think>\n'))
        self.assertEqual(req['mm_processor_kwargs'],kwargs(64))


if __name__=='__main__':unittest.main()
