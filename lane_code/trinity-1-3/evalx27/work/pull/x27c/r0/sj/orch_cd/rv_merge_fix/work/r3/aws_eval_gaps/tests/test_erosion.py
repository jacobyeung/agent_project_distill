"""CPU erosion contracts using two tensors, synthetic masks, and local media."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
from common import save,sha
from c1_export import headers
from stage import prepare
from pointing import parsed
from score_pointing import score_mask
from erosion_bind import stratified,source_contract,validate_pointing
from erosion_report import paired_estimate,pointing_pairs,vsi_pairs


def retained():
    return Path(tempfile.mkdtemp(prefix='x6_',dir=ROOT/'checks'))


def synthetic_membership():
    from erosion_bind import TOOL
    contract=source_contract(TOOL/'aws/kit/a.py')
    return dict(seed=17,count=1000,review_only=True,contract=contract,
                sources=dict(items='0'*64,scenes='0'*64,programs='0'*64),
                items=[dict(id='i'+str(i),scene='scannet/s'+str(i//32),obj='chair',frame=i%32+1,
                    source_index=i%32,frame_indices=list(range(32)),fps=10.,total_num_frames=32,
                    video_rel='scannet/s'+str(i//32)+'.mp4') for i in range(1000)])


class Erosion(unittest.TestCase):
    def export(self):
        import torch
        from safetensors.torch import save_file
        root=retained();base=root/'base';base.mkdir()
        tensors={'model.language_model.a':torch.ones((2,3),dtype=torch.bfloat16),
                 'model.visual.b':torch.zeros((4,),dtype=torch.bfloat16)}
        save_file(tensors,str(base/'model.safetensors'))
        save(base/'config.json',dict(model_type='qwen3_5'))
        save(base/'tokenizer_config.json',dict(synthetic=True))
        save(base/'preprocessor_config.json',dict(size={'shortest_edge':524288,'longest_edge':4718592}))
        files=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size) for p in sorted(base.iterdir())]
        manifest=root/'base.json';save(manifest,dict(files=files))
        staged=prepare(dict(kind='snapshot',path=str(base),manifest=dict(path=str(manifest),sha256=sha(manifest))),None,root/'b')
        milestone=root/'m400';weights=milestone/'full_weights';weights.mkdir(parents=True)
        self.write_weights(weights,tensors)
        save(milestone/'artifact.json',dict(schema='carrier-c1-artifact-v1',step=400,
             full_weights=dict(path=str(weights/'full_weights.json'),sha256=sha(weights/'full_weights.json')),
             heads=dict(path='/does/not/exist/heads.pt',sha256='f'*64)))
        spec=dict(kind='c1_export',path=str(milestone/'artifact.json'),sha256=sha(milestone/'artifact.json'))
        return root,staged,weights,spec,tensors

    def write_weights(self,weights,tensors):
        from safetensors.torch import save_file
        shard=weights/'model-00001-of-00001.safetensors'
        save_file(tensors,str(shard))
        index=weights/'model.safetensors.index.json'
        save(index,dict(weight_map={k:shard.name for k in tensors}))
        save(weights/'full_weights.json',dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=len(tensors),
            index=dict(name=index.name,sha256=sha(index)),
            files=[dict(name=shard.name,sha256=sha(shard),bytes=shard.stat().st_size,tensors=len(tensors))]))

    def repin(self,spec,weights):
        artifact=Path(spec['path'])
        value=json.loads(artifact.read_text());value['full_weights']['sha256']=sha(weights/'full_weights.json')
        save(artifact,value);spec['sha256']=sha(artifact)

    def test_export_exact_native_and_no_heads(self):
        root,base,weights,spec,tensors=self.export()
        dest=prepare(spec,base,root/'out')
        self.assertEqual(headers(dest/'model-00001-of-00001.safetensors'),headers(base/'model.safetensors'))
        self.assertEqual((dest/'config.json').read_bytes(),(base/'config.json').read_bytes())
        self.assertEqual((dest/'preprocessor_config.json').read_bytes(),(base/'preprocessor_config.json').read_bytes())
        self.assertFalse((dest/'heads.pt').exists())
        self.assertEqual(sha(dest/'model-00001-of-00001.safetensors'),sha(weights/'model-00001-of-00001.safetensors'))

    def test_export_hash_chain_and_missing_shards(self):
        root,base,weights,spec,tensors=self.export()
        bad={**spec,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'hash'):prepare(bad,base,root/'badpin')
        with (weights/'model-00001-of-00001.safetensors').open('ab') as f:f.write(b'x')
        with self.assertRaisesRegex(ValueError,'hash/size'):prepare(spec,base,root/'badshard')

    def test_export_lists_all_mapping_failures(self):
        import torch
        root,base,weights,spec,tensors=self.export()
        changed={'wrapped.a':tensors['model.language_model.a'],
                 'model.visual.b':torch.zeros(5,dtype=torch.float32)}
        self.write_weights(weights,changed);self.repin(spec,weights)
        with self.assertRaises(ValueError) as ctx:prepare(spec,base,root/'badmap')
        for word in ('model.language_model.a','wrapped.a','model.visual.b','dtype','shape'):
            self.assertIn(word,str(ctx.exception))

    def test_point_parse_compatibility_and_failures(self):
        self.assertEqual(parsed('```json\n{"point_2d": [500, 700]}\n```')['points'],[[500.,700.]])
        self.assertFalse(parsed('{"point_2d": null}')['parse_failed'])
        self.assertTrue(parsed('garbage')['parse_failed'])
        self.assertTrue(parsed('{"point_2d": [-1, 100]}')['parse_failed'])
        self.assertTrue(parsed('{"point_2d": [0, 0]}')['parse_failed'])
        from erosion_bind import programs
        module=programs()
        for text in ('{"point_2d":[15.5,999]}','{"point_2d":null}','[1, 200]','{"point_2d":[0,0]}'):
            self.assertEqual(parsed(text)['points'],module.parse_points(text))

    def test_point_mask_erosion_null_and_denominator(self):
        mask=np.zeros((20,20),bool);mask[4:16,4:16]=True
        self.assertEqual(score_mask('{"point_2d":[500,500]}',[mask])['inside'],1.)
        self.assertEqual(score_mask('{"point_2d":[210,500]}',[mask])['inside'],0.)
        self.assertEqual(score_mask('{"point_2d":null}',[mask])['inside'],0.)
        self.assertEqual(score_mask('{"point_2d":null}',[])['none_score'],1.)
        bad=score_mask('broken',[])
        self.assertEqual(bad['none_score'],1.) # toolprog null means no valid parsed points
        self.assertTrue(bad['parse_failed'])
        small=np.zeros((20,20),bool);small[8:11,8:11]=True
        self.assertEqual(score_mask('{"point_2d":[450,450]}',[small])['inside'],1.)

    def test_stratified_fixed_membership(self):
        rows=[dict(example_id=str(i),question_type='t'+str(i%8)) for i in range(500)]
        one=stratified(rows)
        self.assertEqual(one,stratified(list(reversed(rows))))
        self.assertEqual(len(one),100)
        sizes=[sum(r['question_type']=='t'+str(i) for r in one) for i in range(8)]
        self.assertTrue(all(n in (12,13) for n in sizes))
        value=synthetic_membership();validate_pointing(value,review=True)
        with self.assertRaisesRegex(ValueError,'review-only'):validate_pointing(value)
        value['items'][0]['visible']=True
        with self.assertRaisesRegex(ValueError,'Private'):validate_pointing(value,review=True)

    def test_pointing_bind_visible_absent_and_private_boundary(self):
        from erosion_bind import pointing_membership,TOOL
        root=retained();items=root/'items.jsonl';scenes=root/'scenes.json'
        rows=[dict(id=str(i),scene_key='scannet/s',frame=i%32+1,obj='chair' if i<900 else 'missing',kind='point')
              for i in range(1400)]
        items.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        save(scenes,{'scannet/s':dict(frame_indices=list(range(32)),video_rel='scannet/s.mp4',fps=10.,total_num_frames=32)})
        gg=SimpleNamespace(gt=SimpleNamespace(valid=np.ones(32,bool)),
                           masks=lambda obj,k:[(1,np.ones((20,20),bool))] if obj=='chair' else [])
        with patch('erosion_bind.ROOT',root),patch('erosion_bind.programs',return_value=object()),\
             patch('erosion_bind.ground',return_value=gg):
            path=pointing_membership(items,scenes,root,TOOL/'aws/kit/a.py',TOOL/'tp/programs.py')
            first=path.read_bytes()
            self.assertEqual(first,pointing_membership(items,scenes,root,TOOL/'aws/kit/a.py',TOOL/'tp/programs.py').read_bytes())
        public=json.loads(first);private=json.loads((root/'inputs/pointing_private.json').read_text())
        self.assertEqual(len(public['items']),1000)
        self.assertEqual(sum(private['visibility'].values()),650)
        self.assertEqual(len(private['visibility'])-sum(private['visibility'].values()),350)
        self.assertEqual(private['membership_sha256'],sha(path))
        self.assertTrue(all('visible' not in r and 'mask' not in r for r in public['items']))

    def test_bootstrap_pairs_scenes_and_official_macro(self):
        rows=[dict(scene='s'+str(i//4),question_type='t'+str(i%2),base=.5,candidate=.75) for i in range(40)]
        r=paired_estimate(rows,draws=1000)
        self.assertEqual(r['difference'],.25);self.assertEqual(r['ci90'],[.25,.25])
        self.assertEqual(r['scenes'],10)
        same=paired_estimate([{**r,'candidate':r['base']} for r in rows],draws=1000)
        self.assertEqual(same['ci90'],[0.,0.])
        macro=paired_estimate([dict(scene='s',question_type='frequent',base=0.,candidate=1.)]*9+
                             [dict(scene='s',question_type='rare',base=1.,candidate=0.)],macro=True,draws=100)
        self.assertEqual(macro['difference'],0.)
        macro2=paired_estimate([dict(scene='s',question_type='object_rel_direction_'+t,base=0.,candidate=1.)
                              for t in ('easy','medium','hard')]+[dict(scene='s',question_type='object_counting',base=1.,candidate=0.)],macro=True,draws=100)
        self.assertAlmostEqual(macro2['difference'],0.)

    def test_pointing_generation_and_summary(self):
        from scoring import score_item,benchmark_summary
        task=dict(benchmark='pointing',example_id='0',question_type='point')
        r=dict(**task,status='complete',**score_item(task,'{"point_2d": null}',48,cap=48))
        self.assertTrue(r['hit_token_cap']);self.assertEqual(r['max_new_tokens'],48)
        self.assertEqual(score_item(task,'{"point_2d":null}',48)['max_new_tokens'],48)
        s=benchmark_summary([r],[task],True)
        self.assertEqual(s['numbers_status'],'Trinity GT scoring required')
        self.assertIsNone(s['overall_score'])

    def test_image_prompt_pixels_and_no_video_size_override(self):
        from transformers import AutoProcessor
        from pointing import image_batch,compare_image
        from parity import prompt
        p=AutoProcessor.from_pretrained('/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',local_files_only=True)
        contract=source_contract('/scratch/jjyeung/orch_cd/toolprog/work/aws/kit/a.py')
        task=dict(benchmark='pointing',example_id='0',point_prompt=contract['prompt'].format(obj='chair'))
        self.assertEqual(contract['image_processor_kwargs'],{})
        self.assertFalse(prompt(p,task).endswith('<think>\n'))
        arrays=np.zeros((1,56,56,3),np.uint8)
        batch=image_batch(p,task,arrays)
        with patch('parity.processor_evidence',return_value=(p,dict(vllm_processor_class_verified=True))):
            c=compare_image(p,object(),task,arrays,batch['input_ids'][0].tolist(),True)
        self.assertTrue(c['prompt_equal']);self.assertTrue(c['pixels']['pass'])

    def test_pointing_cpu_frame_stage_shared_decode(self):
        import av
        from media import decode_pointing,load,pixel_digest
        from frame_stage import stage
        root=retained();video=root/'0.mp4'
        with av.open(str(video),'w') as c:
            s=c.add_stream('libx264',rate=10);s.width=32;s.height=32;s.pix_fmt='yuv420p'
            for i in range(40):
                f=av.VideoFrame.from_ndarray(np.full((32,32,3),i*4,np.uint8),format='rgb24')
                for packet in s.encode(f):c.mux(packet)
            for packet in s.encode():c.mux(packet)
        indices=list(range(0,32))
        tasks=[dict(benchmark='pointing',example_id=str(i),video_path=str(video),source_frame_indices=indices,
               source_index=i,frame=i+1,fps=10.,total_num_frames=40) for i in (3,7)]
        cfg=root/'cfg.json';save(cfg,dict(binding='x6',source_sha256='x6',roots={},datasets=[dict(benchmark='pointing')],
            cells=[dict(layout='spread',benchmarks=['pointing'])]*2))
        # One worker avoids this sandbox's executor wake-up restriction.
        class Inline:
            def __init__(self,**kw):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def map(self,fn,values):return map(fn,values)
        with patch('frame_stage.tasks_for',return_value=tasks),patch('frame_stage.ThreadPoolExecutor',Inline):
            index=stage(cfg,root/'cache',1)
        self.assertEqual(index['decodes'],1)
        expected,_=decode_pointing(tasks[0],'spread')
        for task in tasks:
            actual,audit=load(task,'spread',root/'cache',sha(root/'cache/0.json'))
            np.testing.assert_array_equal(actual,expected[task['frame']-1:task['frame']])
            self.assertEqual(audit['metadata']['frames_indices'],[task['source_index']])

    def test_erosion_bind_roundtrip(self):
        import bind_vl
        from data import tasks_for
        from erosion_report import embedded
        root=retained();path=root/'membership.json';save(path,synthetic_membership())
        args=bind_vl.parser().parse_args(['--preset','erosion','--models',str(ROOT/'inputs/MODELS.example.json'),
            '--candidate','c1a400=/opaque/m400/artifact.json@'+'1'*64,'--gpu-cap','8','--build-only',
            '--pointing-membership',str(path)+'@'+sha(path)])
        cfg=bind_vl.bind(args)
        self.assertEqual(len(cfg['cells']),2);self.assertTrue(cfg['parity_per_benchmark'])
        self.assertEqual(cfg['models']['c1a400']['kind'],'c1_export')
        specs=[]
        for dataset in cfg['datasets']:
            local=deepcopy(dataset)
            for key,value in local.items():
                if isinstance(value,dict) and str(value.get('path','')).startswith('$Q/'):
                    raw=embedded(value,ROOT/'kit/k/1.tar');p=root/(key+dataset['benchmark']+'.json');save(p,raw)
                    local[key]=dict(path=str(p),sha256=sha(p))
            specs.append(local)
        from evalpath.items import MEMBERSHIP_SHA256
        # Keep exact canonical membership bytes, whose pin is part of the official contract.
        specs[0]['membership']=dict(path=str(args.vsi_membership),sha256=MEMBERSHIP_SHA256)
        vs=tasks_for(specs[0],cfg['roots']);pt=tasks_for(specs[1],cfg['roots'])
        self.assertEqual((len(vs),len(pt)),(100,1000))
        self.assertTrue(all(t['benchmark']=='vsi500_slice' for t in vs))
        from parity import probe_tasks
        probes=probe_tasks(cfg,sorted(vs+pt,key=lambda r:(r['benchmark'],r['example_id'])))
        self.assertEqual(len(probes),32);self.assertEqual(sum(i<2 for _,i in probes),4)

    def test_bootstrap_resolves_new_membership_pin(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('_x6_bootstrap',ROOT/'kit/b/1.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        request=dict(datasets=[dict(benchmark='vsi500_slice',rows=dict(path='$Q/1.json'),
                    membership=dict(path='$Q/2.json'),slice_membership=dict(path='$Q/3.json')),
                    dict(benchmark='pointing',membership=dict(path='$Q/4.json'))])
        mod.resolve_inputs(request,Path('/tmp/opaque/q'))
        self.assertEqual(request['datasets'][0]['slice_membership']['path'],'/tmp/opaque/q/3.json')
        self.assertEqual(request['datasets'][1]['membership']['path'],'/tmp/opaque/q/4.json')

    def test_report_cli_pairing_diagnostics_and_parity_gate(self):
        import erosion_report
        from common import archive
        from evalpath.items import digest
        from erosion_bind import TOOL
        root=retained()
        point=synthetic_membership();point.pop('review_only');point['sources']['programs']=sha(TOOL/'tp/programs.py')
        members=dict(seed=17,items=[dict(example_id=str(i),question_type='object_counting',dataset='scannet',scene='s'+str(i//5)) for i in range(100)])
        blobs={'1.json':json.dumps(point).encode(),'2.json':json.dumps(members).encode()}
        specs=[dict(benchmark='pointing',membership=dict(path='$Q/1.json',sha256=hashlib.sha256(blobs['1.json']).hexdigest())),
               dict(benchmark='vsi500_slice',slice_membership=dict(path='$Q/2.json',sha256=hashlib.sha256(blobs['2.json']).hexdigest()))]
        cfg=dict(datasets=specs,cells=[dict(model=m,layout='spread',benchmarks=['vsi500_slice','pointing']) for m in ('base','candidate')],smoke_items=0)
        cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
        save(root/'request.json',cfg);archive(root/'metadata.tar',blobs)
        for i,model in enumerate(('base','candidate')):
            identity=digest(dict(request=cfg['binding'],cell=i))
            directory=root/str(i);directory.mkdir()
            save(directory/'summary_a.json',dict(binding=identity,model=model,parity_pass=i==0,layout='spread',attempt='a'))
            rows=[dict(**m,scene_name=m['scene'],benchmark='vsi500_slice',status='complete',binding=identity,
                question='How many?',options=[],ground_truth='10',video_path='opaque.mp4',raw_generation='</think>\n10',
                output_tokens=4,parse_failed=False,hit_token_cap=False) for m in members['items']]
            (directory/'items_a.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        scored=dict(complete=True,expected=1000,completed=1000,missing_or_failed=[],cap_hits=2,parse_failures=3,
                    visible=650,absent=350,inside_rate=1.,none_rate=1.,items=[
                        dict(example_id=str(i),scene='s'+str(i//20),visible=i<650,inside=1.,none_score=1.) for i in range(1000)])
        argv=['erosion_report.py','--request',str(root/'request.json'),'--metadata',str(root/'metadata.tar'),
              '--runs',str(root),'--attempt','a','--output',str(root/'report.json')]
        with patch('sys.argv',argv),patch('erosion_report.score_rows',return_value=scored):erosion_report.main()
        result=json.loads((root/'report.json').read_text())['candidates']['candidate']
        self.assertEqual(result['numbers_status'],'do not count')
        self.assertEqual(result['vsi500_slice']['overall']['ci90'],[0.,0.])
        self.assertEqual(result['pointing']['inside']['n'],650)
        self.assertEqual(result['pointing']['none']['n'],350)
        self.assertIn('object_counting',(root/'report.md').read_text())
        self.assertEqual(result['pointing']['diagnostics']['candidate']['parse_failures'],3)
        candidate=__import__('score_pointing').read_records(root/'1/items_a.jsonl')
        base=__import__('score_pointing').read_records(root/'0/items_a.jsonl')
        missing=vsi_pairs(base,candidate[:-1],members)
        self.assertFalse(missing['complete']);self.assertEqual(missing['missing_or_failed']['candidate'],['99'])

    def test_image_worker_contract_and_per_benchmark_merge(self):
        import asyncio
        import types
        import worker
        from merge import merge
        from evalpath.items import digest
        root=retained()
        tasks=[dict(benchmark=b,example_id=str(i),question_type='point' if b=='pointing' else 'object_counting',
                    question='How many?',options=[],ground_truth='10',point_prompt='Point to the chair.')
               for b in ('pointing','vsi500_slice') for i in range(16)]
        cfg=dict(cells=[dict(model='base',layout='spread',benchmarks=['vsi500_slice','pointing'])],
            datasets=[dict(benchmark=b) for b in ('pointing','vsi500_slice')],roots={},binding='x6',output=str(root/'o'),
            max_model_len=49152,max_seqs=16,inflight=4,gpus=1,parity_per_benchmark=True)
        save(root/'cfg.json',cfg)
        calls=[]
        class Processor:
            tokenizer=SimpleNamespace(decode=lambda ids,**kw:'{"point_2d":null}' if ids==[2] else '</think>\n10')
            def apply_chat_template(self,msg,**kw):
                if msg[0]['content'][0]['type']=='image':
                    if kw.get('enable_thinking') is not False:raise AssertionError('Image thinking must be off')
                    return 'image'
                return '<think>\n'
        class Engine:
            @classmethod
            def from_engine_args(cls,args):
                calls.append(('engine',args));return cls()
            async def generate(self,req,params,request_id):
                calls.append((request_id,req,params))
                image='image' in req['multi_modal_data']
                yield SimpleNamespace(prompt_token_ids=[1],outputs=[SimpleNamespace(
                    text='{"point_2d":null}' if image else '</think>\n10',token_ids=[2 if image else 1],finish_reason='stop')])
            def shutdown(self):pass
        mods={n:types.ModuleType(n) for n in ('vllm','vllm.engine','vllm.engine.arg_utils','vllm.sampling_params',
                                             'vllm.v1','vllm.v1.engine','vllm.v1.engine.async_llm')}
        mods['vllm'].SamplingParams=lambda **kw:SimpleNamespace(**kw)
        mods['vllm'].__version__='0.32.0'
        mods['vllm.engine.arg_utils'].AsyncEngineArgs=lambda **kw:SimpleNamespace(**kw)
        mods['vllm.sampling_params'].RequestOutputKind=SimpleNamespace(FINAL_ONLY=1)
        mods['vllm.v1.engine.async_llm'].AsyncLLM=Engine
        async def inline(fn,*args,**kw):return fn(*args,**kw)
        def check(p,e,t,a,m,ids,pixels=False,cell=None):
            r=dict(benchmark=t['benchmark'],example_id=t['example_id'],prompt_equal=True)
            if pixels:r['pixels']=dict(pass_=True,**{'pass':True})
            return r
        args=SimpleNamespace(config=str(root/'cfg.json'),cell=0,rank=0,world=1,model='tiny',cache='tiny',
                             frames_sha256='tiny',attempt='a')
        with patch.dict(sys.modules,mods),patch('transformers.AutoProcessor.from_pretrained',return_value=Processor()),\
             patch('worker.tasks_for',side_effect=lambda s,r:[t for t in tasks if t['benchmark']==s['benchmark']]),\
             patch('merge.tasks_for',side_effect=lambda s,r:[t for t in tasks if t['benchmark']==s['benchmark']]),\
             patch('worker.load',return_value=(np.zeros((1,32,32,3),np.uint8),dict(metadata={}))),\
             patch('worker.compare',side_effect=check),patch('worker.asyncio.to_thread',side_effect=inline),\
             patch('asyncio.BaseEventLoop.set_default_executor'):
            asyncio.run(worker.run(args));summary=merge(cfg,0,'a')
        self.assertTrue(summary['parity_pass']);self.assertEqual(len(summary['parity_checks']),32)
        for request_id,req,params in calls[1:]:
            if request_id.startswith('gpointing'):
                self.assertEqual(params.max_tokens,48)
                self.assertIn('image',req['multi_modal_data']);self.assertNotIn('mm_processor_kwargs',req)
            if request_id.startswith('gvsi500_slice'):self.assertEqual(params.max_tokens,16384)
        rows=__import__('score_pointing').read_records(root/'o/0/items_a.jsonl')
        self.assertEqual(sum('raw_generation' in r for r in rows),32)


if __name__=='__main__':unittest.main()
