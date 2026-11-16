"""CPU contracts for explicit 64-anchor VSI slice cells and 32-anchor controls."""
import asyncio
from copy import deepcopy
import importlib.util
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
from evalpath.items import digest
from frame_stage import stage
from media import decode,frame_list,identity,item_key,kwargs,load
from parity import compare,prompt,trainer_encode
from test_frames import video
from trainer.layout_reference import layout_inputs

BASELINE=ROOT/'checks/X1_BASELINE'
CELL=dict(model='t0m800',layout='spread',benchmarks=['vsi500_slice'],decoding='qwen_sampling',frames=64)


def retained():
    return Path(tempfile.mkdtemp(prefix='x1_',dir=ROOT/'checks'))


def args(cells,artifact):
    return bind_vl.parser().parse_args([
        '--preset','custom','--cells',str(cells),'--models',str(BASELINE/'models.json'),
        '--vsi-rows',str(BASELINE/'rows.json'),'--vsi-membership',str(BASELINE/'membership.json'),
        '--pointing-membership',str(ROOT/'inputs/pointing_membership.json')+'@'+sha(ROOT/'inputs/pointing_membership.json'),
        '--remote-root','/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/abcdef12',
        '--gpu-cap','8','--build-only','--artifact-dir',str(artifact)])


def slice_tasks():
    spec=dict(benchmark='vsi500_slice')
    for k,p in [('rows',BASELINE/'rows.json'),('membership',BASELINE/'membership.json'),
                ('slice_membership',ROOT/'inputs/vsi500_slice.json')]:
        spec[k]=dict(path=str(p),sha256=sha(p))
    return tasks_for(spec,dict(video_root='/unavailable'))


class Frames64(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        cls.processor=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        cls.processor._student_pilot_student='qwen35'

    def test_f64_and_same_job_control_bind(self):
        for file,count in [('cells_t0m800_f64.json',1),('cells_t0m800_f32f64.json',2)]:
            root=retained();cfg=bind_vl.bind(args(ROOT/'inputs'/file,root))
            self.assertEqual(len(cfg['cells']),count)
            self.assertEqual(cfg['cells'][-1],CELL)
            self.assertEqual(cfg['max_tokens'],16384);self.assertEqual(cfg['max_model_len'],49152)
            self.assertTrue(cfg['thinking'])
            if count==2:self.assertNotIn('frames',cfg['cells'][0])
            self.assertEqual(cfg['datasets'][0]['slice_membership']['sha256'],sha(ROOT/'inputs/vsi500_slice.json'))

    def test_refuses_unsupported_cells_before_reading_media(self):
        bad=[{**CELL,'frames':n} for n in (0,16,63,128,True,64.,'64',None)]
        bad += [{**CELL,'layout':l} for l in ('duplicate','P0.5','P0.2','paired')]
        bad += [{**CELL,'benchmarks':b} for b in (['pointing'],['revsi','vsi500_slice'],['vstiv3'],
                  ['official5130'],['pointing_video'],['vsi500_slice','pointing'])]
        root=retained()
        for cell in bad:
            with self.subTest(cell=cell):
                path=root/'bad.json';save(path,[cell])
                with self.assertRaisesRegex(ValueError,'frames'):
                    bind_vl.bind(args(path,root/'bind'))
        self.assertEqual(frame_count({k:v for k,v in CELL.items() if k!='frames'}),32)
        self.assertEqual(frame_count({**CELL,'frames':32}),32)
        with self.assertRaisesRegex(ValueError,'frames=64'):
            decode(dict(benchmark='pointing',video_path='/unopened'),'spread',64)

    def test_existing_bind_bytes_and_source_authentication(self):
        root=ROOT/'checks/X1_BASELINE/after'
        cfg=bind_vl.bind(args(ROOT/'inputs/cells_t0m800.json',root))
        before=json.loads((BASELINE/'before/inputs/REQUEST.json').read_text())
        self.assertNotIn('frames',cfg['cells'][0])
        changes={k for k in cfg if cfg[k]!=before[k]}
        self.assertEqual(changes,{'source_sha256','binding','output'})
        # Holding authenticated source constant isolates cell/request serialization.
        expected=deepcopy(cfg)
        for k in changes:expected[k]=before[k]
        self.assertEqual(expected,before)
        fixed=ROOT/'checks/X1_BASELINE/fixed_source'
        actual_sha=bind_vl.sha
        def pinned_source(path):
            return before['source_sha256'] if Path(path)==fixed/'kit/k/0.tar' else actual_sha(path)
        with patch('bind_vl.sha',side_effect=pinned_source):
            normalized=bind_vl.bind(args(ROOT/'inputs/cells_t0m800.json',fixed))
        self.assertEqual(normalized,before)
        self.assertEqual((fixed/'inputs/REQUEST.json').read_bytes(),(BASELINE/'before/inputs/REQUEST.json').read_bytes())
        self.assertEqual((fixed/'kit/k/1.tar').read_bytes(),(BASELINE/'before/kit/k/1.tar').read_bytes())
        self.assertEqual((fixed/'kit/k/2.json').read_bytes(),(BASELINE/'before/kit/k/2.json').read_bytes())
        save(ROOT/'checks/X1_BIND_COMPARISON.json',dict(
            existing_cells_unchanged=True,fixed_source_request_and_bind_bytes_equal=True,
            authenticated_source_changes=sorted(changes),before_binding=before['binding'],after_binding=cfg['binding'],
            note='fixed_source is a test-only serialization probe, never an authenticated shipping stage'))

    def test_official_two_pass_decode_64_anchors(self):
        root=retained();path=root/'0.mp4';video(path,97,10)
        task=dict(benchmark='vsi500_slice',example_id='same',video_path=str(path))
        arrays,audit=decode(task,'spread',64)
        expected=[k*96//63 for k in range(64)]
        self.assertEqual(audit['anchor_indices'],expected)
        self.assertEqual(audit['metadata']['frames_indices'],expected)
        self.assertEqual(audit['metadata']['total_num_frames'],97)
        with av.open(str(path)) as c:
            all_frames=[f.to_ndarray(format='rgb24') for f in c.decode(video=0)]
        np.testing.assert_array_equal(arrays,np.stack([all_frames[i] for i in expected]))
        self.assertEqual(frame_list(expected,10.,97,'spread',64),(expected,[]))
        with self.assertRaises(ValueError):frame_list(expected,10.,97,'spread')

    def test_same_job_cache_separation_and_short_video_error(self):
        root=retained();long=root/'long.mp4';short=root/'short.mp4'
        video(long,97,10);video(short,40,10)
        tasks=[dict(benchmark='vsi500_slice',example_id=p.stem,video_path=str(p)) for p in (long,short)]
        cfg=dict(binding='x1',source_sha256='s',roots={},datasets=[dict(benchmark='vsi500_slice')],
            cells=[{k:v for k,v in CELL.items() if k!='frames'},CELL])
        path=root/'cfg.json';save(path,cfg)
        with patch('frame_stage.tasks_for',return_value=tasks):index=stage(path,root/'cache',1)
        self.assertEqual(index['decodes'],4);self.assertEqual(index['errors'],1)
        pin=sha(root/'cache/0.json')
        for task in tasks:
            self.assertNotEqual(identity(task,'spread'),identity(task,'spread',64))
            self.assertNotEqual(item_key(task,'spread'),item_key(task,'spread',64))
            self.assertEqual(len(load(task,'spread',root/'cache',pin)[0]),32)
        self.assertEqual(len(load(tasks[0],'spread',root/'cache',pin,64)[0]),64)
        with self.assertRaisesRegex(ValueError,'only 40 decoded frames, need 64'):
            load(tasks[1],'spread',root/'cache',pin,64)

    def test_layout_reference_opt_in_and_legacy_equivalence(self):
        spec=importlib.util.spec_from_file_location('layout_before',BASELINE/'layout_before.py')
        previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
        for count in (32,64):
            si=dict(frames=[dict(path=str(i),sha256='a'*64) for i in range(count)],
                frame_indices=list(range(count)),timestamps=[i/10 for i in range(count)],fps=10.,total_num_frames=100)
            row=dict(student_input=si)
            if count==32:
                for layout in ('spread','duplicate'):
                    self.assertEqual(layout_inputs(row,layout),previous.layout_inputs(row,layout))
            else:
                self.assertEqual(layout_inputs(row,'spread',frames=64),si)
                with self.assertRaises(ValueError):layout_inputs(row,'spread')
                for layout in ('duplicate','paired'):
                    with self.assertRaises(ValueError):layout_inputs(row,layout,gap=.2 if layout=='paired' else None,frames=64)
                with self.assertRaises(ValueError):layout_inputs(row,'duplicate')

    def test_cpu_prompt_ids_pixels_grid_and_budget(self):
        import torch
        from transformers.video_utils import VideoMetadata
        task=slice_tasks()[0];p=self.processor
        arrays=np.zeros((64,64,96,3),np.uint8)
        indices=[k*999//63 for k in range(64)]
        meta=dict(total_num_frames=1000,fps=10.,frames_indices=indices,height=64,width=96)
        with self.assertRaisesRegex(ValueError,'32 input frames'):trainer_encode(p,task,arrays,meta)
        batch,audit=trainer_encode(p,task,arrays,meta,CELL)
        self.assertEqual(audit['video_grid_thw'][0][0],32)
        self.assertEqual(audit['original_frame_indices'],indices)
        np.testing.assert_allclose(audit['temporal_patch_timestamps_seconds'],[(indices[i]+indices[i+1])/20 for i in range(0,64,2)])
        native=p(text=[prompt(p,task)],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
            **kwargs(64),return_tensors='pt',return_metadata=True)
        ids=native['input_ids'][0].tolist()
        self.assertEqual(ids,batch['input_ids'][0,:audit['prompt_tokens']].tolist())
        self.assertTrue(torch.equal(batch['pixel_values_videos'],native['pixel_values_videos']))
        with patch('parity.processor_evidence',return_value=(p,dict(vllm_processor_class_verified=True))):
            result=compare(p,object(),task,arrays,meta,ids,True,cell=CELL)
        self.assertTrue(result['prompt_equal']);self.assertTrue(result['pixels']['pass'])
        self.assertLessEqual(len(ids)+16384,49152)
        self.assertEqual(kwargs(64)['size'],dict(shortest_edge=64*128**2,longest_edge=64*384**2))
        self.assertEqual(kwargs(32)['size'],dict(shortest_edge=32*128**2,longest_edge=32*384**2))
        resized=p.video_processor(videos=[arrays],**kwargs(64),return_tensors='pt')['video_grid_thw'][0,1:]
        small=p.video_processor(videos=[arrays[:32]],**kwargs(32),return_tensors='pt')['video_grid_thw'][0,1:]
        self.assertTrue(torch.equal(resized,small))

    def test_prompt_budget_formula_for_all_100_questions(self):
        import torch
        from transformers.video_utils import VideoMetadata
        rows=slice_tasks();p=self.processor
        base=[(t['example_id'],len(p.tokenizer.encode(prompt(p,t),add_special_tokens=False))) for t in rows]
        self.assertEqual(len(rows),100)
        # A 384x384 processed frame supplies 144 visual tokens per temporal group.
        replacement=p.replace_video_token(dict(video_grid_thw=torch.tensor([[32,24,24]]),
            video_metadata=[VideoMetadata(fps=1.,frames_indices=list(range(64)),total_num_frames=64)]),0)
        expanded=[]
        for task in rows:
            text,_=p.get_text_with_replacements([prompt(p,task)],videos_replacements=[replacement])
            expanded.append((task['example_id'],len(p.tokenizer.encode(text[0],add_special_tokens=False))))
        max_base=max(n for _,n in base);max_synthetic=max(n for _,n in expanded)
        self.assertLess(max_synthetic+16384,49152)
        report=dict(items=100,max_unexpanded_prompt_tokens=max_base,
            max_prompt_tokens_with_384_square_and_synthetic_timestamps=max_synthetic,
            actual_max_prompt_tokens=None,reason='Slice/canonical metadata lacks video dimensions, FPS, decoded frame counts and timestamps; source videos are not in this kit.',
            visual_tokens_max_64_square=4608,extra_visual_tokens_vs_32_square=2304,
            general_formula='L = B - 1 + 32*(processed_height/32)*(processed_width/32) + 64 + sum(timestamp token counts); require L <= 32768.',
            formula='L = B - 1 + 4608 + 64 + sum(token_count(<timestamp_g seconds>), g=0..31); require L <= 32768 for 16384 output tokens in 49152 context.',
            max_timestamp_token_sum_allowed=32768-(max_base-1+4608+64),
            fewer_than_64_count=None,frame_count_metadata_items=0)
        save(ROOT/'checks/X1_CONTEXT.json',report)

    def test_worker_control_records_summary_and_short_video_error(self):
        import worker
        from merge import merge
        root=retained();tasks=[]
        for name,count in [('long',97),('short',40)]:
            path=root/(name+'.mp4');video(path,count,10)
            tasks.append(dict(benchmark='vsi500_slice',example_id=name,video_path=str(path),
                question='How many chairs?',options=[],ground_truth='10',question_type='object_counting'))
        control={k:v for k,v in CELL.items() if k!='frames'}
        cfg=dict(cells=[control,CELL],datasets=[dict(benchmark='vsi500_slice')],roots={},binding='x1',source_sha256='s',
            output=str(root/'out'),max_model_len=49152,max_seqs=8,inflight=2,gpus=1)
        path=root/'cfg.json';save(path,cfg)
        with patch('frame_stage.tasks_for',return_value=tasks):stage(path,root/'cache',1)
        calls=[]
        class Engine:
            @classmethod
            def from_engine_args(cls,args):
                self.assertEqual(args.seed,17);self.assertEqual(args.max_model_len,49152)
                return cls()
            async def generate(self,req,params,request_id):
                calls.append((req,params,request_id))
                yield SimpleNamespace(prompt_token_ids=[1],outputs=[SimpleNamespace(
                    text='</think>\n10',token_ids=[1],finish_reason='stop')])
            def shutdown(self):pass
        mods={n:types.ModuleType(n) for n in ('vllm','vllm.engine','vllm.engine.arg_utils','vllm.sampling_params',
            'vllm.v1','vllm.v1.engine','vllm.v1.engine.async_llm')}
        mods['vllm'].__version__='0.32.0';mods['vllm'].SamplingParams=lambda **kw:SimpleNamespace(**kw)
        mods['vllm.engine.arg_utils'].AsyncEngineArgs=lambda **kw:SimpleNamespace(**kw)
        mods['vllm.sampling_params'].RequestOutputKind=SimpleNamespace(FINAL_ONLY=1)
        mods['vllm.v1.engine.async_llm'].AsyncLLM=Engine
        async def inline(fn,*args,**kw):return fn(*args,**kw)
        def check(p,e,t,a,m,ids,pixels=False,cell=None):
            self.assertEqual(len(a),cell.get('frames',32))
            r=dict(benchmark=t['benchmark'],example_id=t['example_id'],prompt_equal=True)
            if pixels:r['pixels']={'pass':True}
            return r
        a=SimpleNamespace(config=str(path),cell=0,rank=0,world=1,model='synthetic',cache=str(root/'cache'),
            frames_sha256=sha(root/'cache/0.json'),attempt='x1')
        with patch.dict(sys.modules,mods),patch('transformers.AutoProcessor.from_pretrained',return_value=self.processor),\
             patch('worker.tasks_for',return_value=tasks),patch('worker.compare',side_effect=check),\
             patch('worker.asyncio.to_thread',side_effect=inline),patch('merge.tasks_for',return_value=tasks):
            asyncio.run(worker.run(a));summary32=merge(cfg,0,'x1')
            a.cell=1
            asyncio.run(worker.run(a));summary=merge(cfg,1,'x1')
        control_rows=list(map(json.loads,(root/'out/0/items_x1.jsonl').read_text().splitlines()))
        self.assertEqual(summary32['frames'],32)
        for row in control_rows:
            self.assertEqual(row['status'],'complete');self.assertEqual(row['frames'],32)
            self.assertEqual(len(row['anchor_indices']),32)
        rows={r['example_id']:r for r in map(json.loads,(root/'out/1/items_x1.jsonl').read_text().splitlines())}
        self.assertEqual(rows['long']['frames'],64);self.assertEqual(len(rows['long']['anchor_indices']),64)
        self.assertEqual(rows['short']['frames'],64);self.assertEqual(rows['short']['status'],'error')
        self.assertIsNone(rows['short']['anchor_indices']);self.assertIn('need 64',rows['short']['error'])
        self.assertEqual(summary['frames'],64)
        self.assertEqual(summary['anchor_indices']['vsi500_slice:long'],rows['long']['anchor_indices'])
        self.assertEqual(summary['benchmarks']['vsi500_slice']['frames'],64)
        generations=[(req,par) for req,par,k in calls if k.startswith('g')]
        self.assertEqual(len(generations),3)
        self.assertEqual([len(req['multi_modal_data']['video'][0][0]) for req,_ in generations],[32,32,64])
        for req,par in generations:
            self.assertEqual(req['mm_processor_kwargs'],kwargs(len(req['multi_modal_data']['video'][0][0])))
            self.assertEqual((par.seed,par.temperature,par.top_p,par.top_k,par.max_tokens),(17,.6,.95,20,16384))


if __name__=='__main__':unittest.main()
