"""CPU contracts for temporal references, native video encoding, and mask diagnostics."""
import ast
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from common import save,sha
from pointing_video import QUESTION,EMPTY_THINK,question,parse_output,processed_hw
from score_pointing_video import score_mask,score_rows,PARSINGS


def retained():return Path(tempfile.mkdtemp(prefix='x8_',dir=ROOT/'checks'))


def membership():
    value=json.loads((ROOT/'inputs/pointing_review.json').read_text())
    for i,r in enumerate(value['items']):r['obj']='chair' if i<650 else 'missing'
    return value


class PointingVideo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        cls.processor=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        cls.processor._student_pilot_student='qwen35'

    def tasks(self):
        from data import tasks_for
        root=retained();m=root/'m.json';save(m,membership())
        return tasks_for(dict(benchmark='pointing_video',membership=dict(path=str(m),sha256=sha(m)),
                              variants=['A','B','C']),dict(pointing_video_root='/opaque'))

    def test_prompts_match_training_question_and_frame_references(self):
        source=Path('/scratch/jjyeung/orch_cd/mixdata/work/pointing/point_build.py')
        tree=ast.parse(source.read_text())
        original=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id=='QUESTION' for t in n.targets))
        self.assertEqual(QUESTION,original)
        it=dict(frame=7,obj='chair',source_index=155,fps=30.)
        self.assertEqual(question(it,'A'),original.format(obj='chair',k=7))
        self.assertEqual(question(it,'B'),original.format(obj='chair',k=13))
        self.assertEqual(question(it,'C').count('at 5.2 s'),2)
        self.assertNotIn('frame 7',question(it,'C'))
        self.assertEqual(question({**it,'frame':32},'B'),original.format(obj='chair',k=63))

    def test_membership_variants_preserve_viewpoint_and_source(self):
        tasks=self.tasks()
        self.assertEqual(len(tasks),3000);self.assertEqual(len({t['example_id'] for t in tasks}),3000)
        for a,b,c in zip(tasks[::3],tasks[1::3],tasks[2::3]):
            self.assertEqual([a['variant'],b['variant'],c['variant']],['A','B','C'])
            self.assertEqual(a['membership_id'],b['membership_id']);self.assertEqual(a['frame'],c['frame'])
            self.assertEqual(a['source_index'],a['source_frame_indices'][a['frame']-1])

    def test_duplicate_video_stage_equals_trainer_layout_and_shared_decode(self):
        from test_frames import video
        from frame_stage import stage
        from media import load,decode,pixel_digest
        from trainer.layout_reference import layout_inputs
        root=retained();v=root/'0.mp4';video(v,65,10)
        tasks=self.tasks()[:6];indices=list(range(0,64,2))
        for t in tasks:
            t.update(video_path=str(v),source_frame_indices=indices,source_index=indices[t['frame']-1],fps=10.,total_num_frames=65)
        cfg=root/'cfg.json';save(cfg,dict(binding='bound',source_sha256='source',roots={},
            datasets=[dict(benchmark='pointing_video')],cells=[dict(layout='duplicate',benchmarks=['pointing_video'])]))
        class Inline:
            def __init__(self,**kw):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def map(self,fn,values):return map(fn,values)
        with patch('frame_stage.tasks_for',return_value=tasks),patch('frame_stage.ThreadPoolExecutor',Inline):
            index=stage(cfg,root/'cache',1)
        self.assertEqual(index['decodes'],1);self.assertEqual(index['errors'],0)
        expected,audit=decode({**tasks[0],'benchmark':'pointing'},'spread')
        si=dict(frames=[dict(path=str(i),sha256='a'*64) for i in indices],frame_indices=indices,
                timestamps=[i/10 for i in indices],fps=10.,total_num_frames=65)
        trainer=layout_inputs(dict(student_input=si),'duplicate')
        for t in tasks:
            actual,receipt=load(t,'duplicate',root/'cache',sha(root/'cache/0.json'))
            np.testing.assert_array_equal(actual,np.repeat(expected,2,axis=0))
            self.assertEqual(receipt['metadata']['frames_indices'],trainer['frame_indices'])
            self.assertEqual(receipt['pixel_sha256'],pixel_digest(actual))
            self.assertEqual(len(actual),64)

    def test_empty_think_video_prefix_native_ids_pixels_and_resize(self):
        from pointing_video import video_prompt,compare_video
        from parity import prompt
        from transformers.video_utils import VideoMetadata
        from media import kwargs
        p=self.processor;task=self.tasks()[0]
        arrays=np.zeros((64,48,96,3),np.uint8)
        meta=dict(fps=10.,frames_indices=[i*2 for i in range(32) for _ in range(2)],
                  total_num_frames=65,height=48,width=96)
        value=prompt(p,task)
        self.assertTrue(value.endswith(EMPTY_THINK));self.assertEqual(value,video_prompt(p,task))
        call=p(text=[value],videos=[arrays],video_metadata=[VideoMetadata(**meta)],
               **kwargs(64),return_tensors='pt',return_metadata=True)
        with patch('parity.processor_evidence',return_value=(p,dict(vllm_processor_class_verified=True))):
            check=compare_video(p,object(),task,arrays,meta,call['input_ids'][0].tolist(),True)
        self.assertTrue(check['prompt_equal']);self.assertTrue(check['pixels']['pass'])
        self.assertEqual(call['video_grid_thw'][0,0],32)
        self.assertEqual(processed_hw(p,48,96,64),[int(x)*16 for x in call['video_grid_thw'][0,1:]])
        text=p.tokenizer.decode(call['input_ids'][0],skip_special_tokens=False)
        self.assertIn('<0.0 seconds>',text);self.assertIn('<6.2 seconds>',text)

    def test_parsings_eroded_masks_and_neighbor_only_hits(self):
        mask=np.zeros((40,80),bool);mask[8:24,40:64]=True
        for text,parsing in [('{"point_2d":[650,400]}','xy_1000'),('{"point_2d":[400,650]}','yx_1000'),
                             ('{"point_2d":[104,32]}','processed_pixels'),('{"point_2d":[0.65,0.4]}','fractions')]:
            value=score_mask(text,[mask],[80,160])
            self.assertEqual(value['parsings'][parsing]['inside'],1.,parsing)
        self.assertEqual(score_mask('{"point_2d":[500,400]}',[mask],[80,160])['parsings']['xy_1000']['inside'],0.)
        small=np.zeros((40,80),bool);small[15:18,50:53]=True
        self.assertEqual(score_mask('{"point_2d":[650,400]}',[small],[80,160])['parsings']['xy_1000']['inside'],1.)
        other=np.zeros_like(mask);other[8:24,8:24]=True
        result=score_mask('{"point_2d":[650,400]}',[other],[80,160],{'k-1':[mask],'k+1':[other]})
        self.assertEqual(result['neighbors']['k-1']['exclusive_inside'],1.)
        self.assertEqual(result['neighbors']['k+1']['inside'],0.)

    def test_null_malformed_origin_and_coordinate_domains(self):
        self.assertFalse(parse_output('{"point_2d":[0,0]}')['parse_failed'])
        for text in ('bad','{"point_2d":[true,2]}','{"point_2d":[NaN,2]}','{"point_2d":null,"point_2d":[1,2]}'):
            self.assertTrue(parse_output(text)['parse_failed'])
        null=score_mask('{"point_2d":null}',[],[40,80])
        bad=score_mask('bad',[],[40,80])
        self.assertTrue(null['explicit_none']);self.assertFalse(bad['explicit_none'])
        for name in PARSINGS:
            self.assertEqual(null['parsings'][name]['none_score'],1.)
            self.assertTrue(bad['parsings'][name]['malformed'])
        out=score_mask('{"point_2d":[1001,2]}',[],[40,80])
        self.assertTrue(all(v['malformed'] for v in out['parsings'].values()))
        self.assertFalse(parse_output('```json\n{"point_2d":[0.5,0.4]}\n```')['parse_failed'])

    def test_score_all_variants_visibility_missing_boundaries_and_identity(self):
        m=membership();m.pop('review_only');tasks=self.tasks()
        rows=[{**t,'status':'complete','processed_height_width':[40,80],
               'raw_generation':'{"point_2d":[500,500]}' if t['obj']=='chair' else '{"point_2d":null}'} for t in tasks]
        gg=SimpleNamespace(gt=SimpleNamespace(valid=np.ones(32,bool)),
            masks=lambda obj,k:[(1,np.ones((40,80),bool))] if obj=='chair' else [])
        with patch('score_pointing_video.programs',return_value=object()),patch('score_pointing_video.ground',return_value=gg):
            result=score_rows(rows,m)
            for v,r in result['variants'].items():
                self.assertEqual((r['visible'],r['absent']),(650,350));self.assertTrue(r['complete'])
                self.assertEqual(r['inside_rate'],1.);self.assertEqual(r['none_rate'],1.)
                self.assertEqual(r['explicit_none_rate'],1.);self.assertEqual(r['malformed_rate'],0.)
                self.assertLess(r['neighbors']['k-1']['eligible'],1000)
            incomplete=score_rows(rows[:-1],m)
            self.assertFalse(incomplete['variants']['C']['complete'])
            with self.assertRaisesRegex(ValueError,'Duplicate'):score_rows(rows+[rows[0]],m)
            changed=deepcopy(rows[:1]);changed[0]['frame']=2
            with self.assertRaisesRegex(ValueError,'differs'):score_rows(changed,m)

    def test_separate_preset_bind_64_greedy_and_real_pinned_membership(self):
        import bind_vl
        from data import tasks_for
        from erosion_report import embedded
        root=retained();m=ROOT/'inputs/pointing_membership.json'
        args=bind_vl.parser().parse_args(['--preset','pointing_video_base','--models',str(ROOT/'inputs/MODELS.example.json'),
            '--gpus','4','--gpu-cap','32','--other-gpus','28','--build-only','--pointing-membership',str(m)+'@'+sha(m),
            '--artifact-dir',str(root)])
        cfg=bind_vl.bind(args)
        self.assertEqual(cfg['cells'],[dict(model='base',layout='duplicate',benchmarks=['pointing_video'])])
        self.assertEqual((cfg['thinking'],cfg['max_tokens'],cfg['temperature']),(False,64,0))
        spec=deepcopy(cfg['datasets'][0]);raw=embedded(spec['membership'],root/'kit/k/1.tar')
        local=root/'m.json';save(local,raw);spec['membership']=dict(path=str(local),sha256=sha(local))
        self.assertEqual(len(tasks_for(spec,cfg['roots'])),3000)
        self.assertEqual(raw,json.loads(m.read_text()))

    def test_worker_video_cap_error_identity_resume_and_merge(self):
        import worker
        from merge import merge
        root=retained();tasks=self.tasks()[:18]
        config=dict(cells=[dict(model='base',layout='duplicate',benchmarks=['pointing_video'])],
            datasets=[dict(benchmark='pointing_video')],roots={},binding='bound',output=str(root/'out'),
            max_model_len=49152,max_seqs=8,inflight=4,gpus=1)
        path=root/'cfg.json';save(path,config);calls=[];fail_once={'yes':True}
        class Engine:
            @classmethod
            def from_engine_args(cls,args):return cls()
            async def generate(self,req,params,request_id):
                calls.append((req,params,request_id))
                if request_id=='gpointing_video:'+tasks[-1]['example_id'] and fail_once['yes']:
                    fail_once['yes']=False;raise RuntimeError('synthetic error')
                yield SimpleNamespace(prompt_token_ids=[1],outputs=[SimpleNamespace(
                    text='{"point_2d":[500,500]}',token_ids=[1]*64,finish_reason='length')])
            def shutdown(self):pass
        names=['vllm','vllm.engine','vllm.engine.arg_utils','vllm.sampling_params',
               'vllm.v1','vllm.v1.engine','vllm.v1.engine.async_llm']
        modules={n:types.ModuleType(n) for n in names}
        modules['vllm'].SamplingParams=lambda **kw:SimpleNamespace(**kw)
        modules['vllm'].__version__='0.32.0'
        modules['vllm.engine.arg_utils'].AsyncEngineArgs=lambda **kw:SimpleNamespace(**kw)
        modules['vllm.sampling_params'].RequestOutputKind=SimpleNamespace(FINAL_ONLY=1)
        modules['vllm.v1.engine.async_llm'].AsyncLLM=Engine
        def check(p,e,t,a,m,ids,pixels=False,cell=None):
            value=dict(benchmark='pointing_video',example_id=t['example_id'],prompt_equal=True)
            if pixels:value['pixels']=dict(pass_=True,**{'pass':True})
            return value
        async def inline(fn,*args,**kw):return fn(*args,**kw)
        args=SimpleNamespace(config=str(path),cell=0,rank=0,world=1,model='synthetic',
                             cache=str(root/'cache'),frames_sha256='pin',attempt='a')
        with patch.dict(sys.modules,modules),patch('transformers.AutoProcessor.from_pretrained',return_value=self.processor),\
             patch('worker.tasks_for',return_value=tasks),patch('merge.tasks_for',return_value=tasks),\
             patch('worker.load',return_value=(np.zeros((64,48,96,3),np.uint8),{'metadata':{}})),\
             patch('worker.compare',side_effect=check),patch('worker.asyncio.to_thread',side_effect=inline),\
             patch('asyncio.BaseEventLoop.set_default_executor'):
            asyncio.run(worker.run(args))
            summary=merge(config,0,'a')
            self.assertTrue(summary['parity_pass'])
            self.assertEqual(summary['benchmarks']['pointing_video']['completed'],17)
            rows=[json.loads(line) for line in (root/'out/0/items_a.jsonl').read_text().splitlines()]
            error=next(r for r in rows if r['status']=='error')
            self.assertEqual(error['variant'],'C');self.assertEqual(error['membership_id'],tasks[-1]['membership_id'])
            complete=next(r for r in rows if r['status']=='complete')
            self.assertEqual(complete['processed_height_width'],processed_hw(self.processor,48,96,64))
            self.assertEqual(complete['max_new_tokens'],64);self.assertTrue(complete['hit_token_cap'])
            self.assertEqual(complete['at_4096']['max_new_tokens'],64)
            asyncio.run(worker.run(args))
            self.assertEqual(merge(config,0,'a')['benchmarks']['pointing_video']['completed'],18)
        from media import kwargs
        self.assertTrue(all(c[0]['mm_processor_kwargs']==kwargs(64) for c in calls))
        self.assertTrue(all(c[0]['prompt'].endswith(EMPTY_THINK) for c in calls))
        self.assertTrue(all(c[1].temperature==0 for c in calls))
        self.assertTrue(all(c[1].max_tokens==64 for c in calls if c[2].startswith('g')))
        self.assertEqual(sum(c[2].startswith('g') for c in calls),19)


if __name__=='__main__':unittest.main(verbosity=2)
