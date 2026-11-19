"""CPU fixtures: run with Python -I -s -B and this file's absolute path."""
import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np
import torch
torch.set_num_threads(8)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e2e_reader.read_cache import (ReadCache, VideoProcessorCache, digest, install_vision_cache,
                                   restore, snapshot, switches)
from e2e_reader import stage1


class TinyVideoProcessor:
    def __init__(self): self.calls=0;self.factor=2
    def to_dict(self): return {'factor':self.factor}
    def __call__(self, videos, **kwargs):
        self.calls += 1
        return {'pixels':torch.as_tensor(videos[0].copy())*self.factor,
                'metadata':kwargs.get('metadata')}


@dataclasses.dataclass
class Metadata:
    fps: float
    frames_indices: list


@dataclasses.dataclass
class VisionOutput:
    last_hidden_state: torch.Tensor
    pooler_output: torch.Tensor


class Qwen3_5VisionModel(torch.nn.Module):
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.tensor(2.))
        self.config=types.SimpleNamespace(to_dict=lambda:{'width':1});self.calls=0
    def forward(self, hidden_states, grid_thw, **kwargs):
        self.calls += 1
        return VisionOutput(hidden_states*self.weight, hidden_states.sum()*self.weight)


class ReadCacheTests(unittest.TestCase):
    def test_defaults_and_validation(self):
        self.assertEqual(set(switches({}).values()), {'off'})
        with self.assertRaises(ValueError): switches({'read_sam_cache':True})
        with self.assertRaises(ValueError): ReadCache(0)

    def test_exact_storage_signed_zero_nan_bfloat_and_mutation(self):
        value={'array':np.array([-0.,np.nan,2.],dtype=np.float64),
               'tensor':torch.tensor([-0.,1.],dtype=torch.bfloat16),
               'metadata':Metadata(24.,[1,3])}
        cache=ReadCache(100000)
        a=cache.call('test','key',lambda:value)
        original=digest(a)
        a['tensor'].fill_(4);a['array'][0]=2;a['metadata'].frames_indices.append(8)
        b=cache.call('test','key',lambda:None)
        self.assertEqual(digest(b),original)
        b['tensor'].fill_(8)
        self.assertEqual(digest(cache.call('test','key',lambda:None)),original)

    def test_key_invalidates_pixels_metadata_kwargs_dtype_and_order(self):
        a=np.zeros((2,2,3),np.uint8); b=a.copy();b[0,0,0]=1
        values=[(a,Metadata(24.,[1,3]),{}),(b,Metadata(24.,[1,3]),{}),
                (a,Metadata(30.,[1,3]),{}),(a,Metadata(24.,[3,1]),{}),
                (a,Metadata(24.,[1,3]),{'resize':False}),
                (a.astype(np.float32),Metadata(24.,[1,3]),{})]
        self.assertEqual(len(set(map(digest,values))),len(values))

    def test_budget_eviction_oversize_and_process_reset(self):
        cache=ReadCache(800)
        for k in range(4):cache.call('x',k,lambda:np.zeros(300,np.uint8))
        self.assertLessEqual(cache.held_bytes,800)
        self.assertGreater(cache.stats['x']['evictions'],0)
        cache.call('x','big',lambda:np.zeros(1000,np.uint8))
        self.assertNotIn(('x','big'),cache.entries)
        with patch('e2e_reader.read_cache.os.getpid',return_value=cache.pid+1):
            cache.call('x','child',lambda:1)
            self.assertEqual(len(cache.entries),1)

    def test_processor_keeps_question_out_and_metadata_in_key(self):
        target=TinyVideoProcessor();proxy=VideoProcessorCache(target,ReadCache(100000))
        pixels=np.zeros((2,3,3),np.uint8)
        a=proxy([pixels],metadata=Metadata(24.,[0,1]))
        b=proxy([pixels],metadata=Metadata(24.,[0,1]))
        self.assertEqual(digest(a),digest(b));self.assertEqual(target.calls,1)
        proxy([pixels],metadata=Metadata(25.,[0,1]));self.assertEqual(target.calls,2)
        target.factor=3
        proxy([pixels],metadata=Metadata(24.,[0,1]));self.assertEqual(target.calls,3)

    def test_vision_returns_same_type_and_keeps_outer_hooks(self):
        visual=Qwen3_5VisionModel().eval().requires_grad_(False)
        model=types.SimpleNamespace(model=types.SimpleNamespace(visual=visual))
        cache=ReadCache(100000);install_vision_cache(model,cache)
        hook_calls=[];visual.register_forward_hook(lambda *args:hook_calls.append(1))
        with torch.no_grad():
            a=visual(torch.ones(2),torch.tensor([1,1,2]))
            b=visual(torch.ones(2),torch.tensor([1,1,2]))
            self.assertIsInstance(b,VisionOutput);self.assertEqual(digest(a),digest(b))
            self.assertEqual(visual.calls,1);self.assertEqual(len(hook_calls),2)
            visual.weight.add_(1)
            visual(torch.ones(2),torch.tensor([1,1,2]));self.assertEqual(visual.calls,2)
        with self.assertRaisesRegex(ValueError,'no-grad'): visual(torch.ones(2),torch.tensor([1,1,2]))

    def test_vision_child_hook_bypasses_cache(self):
        visual=Qwen3_5VisionModel().eval().requires_grad_(False)
        visual.child=torch.nn.Identity().eval()
        original=visual.forward
        visual.forward=lambda *a,**k:visual.child(original(*a,**k))
        cache=ReadCache(100000)
        install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=visual)),cache)
        calls=[];visual.child.register_forward_hook(lambda *args:calls.append(1))
        with torch.no_grad():
            visual(torch.ones(2),torch.tensor([1,1,2]));visual(torch.ones(2),torch.tensor([1,1,2]))
        self.assertEqual(len(calls),2);self.assertEqual(visual.calls,2)
        self.assertEqual(cache.stats['vision_bypass']['calls'],2)

    def test_installed_transformers_video_packing_without_torchvision(self):
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        from transformers.video_utils import VideoMetadata
        # This CPU env lacks torchvision. Exercise native packing and metadata;
        # the GPU kit must exercise production RGB conversion/resize/normalization.
        target=Qwen3VLVideoProcessor(size={'shortest_edge':2048,'longest_edge':2048},
                                    do_convert_rgb=False,do_resize=False,do_normalize=False)
        proxy=VideoProcessorCache(target,ReadCache(1000000))
        pixels=np.arange(2*32*32*3,dtype=np.uint8).reshape(2,32,32,3)
        def kwargs():return dict(video_metadata=[VideoMetadata(total_num_frames=2,fps=1.,
                                frames_indices=[0,1],height=32,width=32)],
                                do_sample_frames=False,return_tensors='pt',return_metadata=True)
        baseline=target([pixels],**kwargs())
        first=proxy([pixels],**kwargs());second=proxy([pixels],**kwargs())
        self.assertEqual(type(baseline),type(second))
        self.assertEqual(digest(baseline),digest(first));self.assertEqual(digest(first),digest(second))
        self.assertEqual(proxy.cache.stats['processor']['hits'],1)

    def test_installed_transformers_tiny_vision_and_output_mutation(self):
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel as NativeVision
        cfg=Qwen3_5VisionConfig(depth=1,hidden_size=16,intermediate_size=32,num_heads=2,
                               out_hidden_size=16,num_position_embeddings=16,
                               patch_size=16,spatial_merge_size=2,temporal_patch_size=2)
        cfg._attn_implementation='eager'
        torch.manual_seed(3)
        visual=NativeVision(cfg).eval().requires_grad_(False)
        pixels=torch.randn(8,3*2*16*16);grid=torch.tensor([[2,2,2]])
        with torch.no_grad():baseline=visual(pixels,grid_thw=grid,return_dict=True)
        cache=ReadCache(1000000)
        install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=visual)),cache)
        with torch.no_grad():
            first=visual(pixels,grid_thw=grid,return_dict=True)
            first.pooler_output=tuple(first.pooler_output.split(1))
            second=visual(pixels,grid_thw=grid,return_dict=True)
        self.assertEqual(type(baseline),type(second));self.assertEqual(digest(baseline),digest(second))
        self.assertEqual(cache.stats['vision']['hits'],1)

    def test_sam_caches_raw_values_but_recomputes_geometry(self):
        from PIL import Image
        tower=types.SimpleNamespace(device='cpu',precision='float32',image_batch_size=1,
                                    native_image_batch=False,_owner=object())
        calls={'encode':0,'detect':0}
        class ClipFeatures:
            def __init__(self,frames,sizes,owner):self.frames,self.sizes,self.owner=frames,sizes,owner
        def encode(images):
            calls['encode']+=1
            return ClipFeatures(({'f':torch.ones(1,1,1,1)},),((2,2),),tower._owner)
        tower.encode=encode
        def detect(t,features,name):
            calls['detect']+=1
            assert features.owner is tower._owner
            return [[{'mask':np.ones((2,2),dtype=bool),'score':.5,'presence':.9}]]
        class Stage:
            def __init__(self,detect,head,geometry,rule):self.detect,self.geometry=detect,geometry
            def propose(self,name):return {'raw':self.detect(name),'geometry':self.geometry}
            def select(self,x):return 0
        class Socket:
            def __init__(self,propose,*args):self.propose=propose
        module=types.ModuleType('student_pilot.sam3_tower');module.ClipFeatures=ClipFeatures
        package=types.ModuleType('student_pilot');package.__path__=[]
        artifact=types.SimpleNamespace(manifest={'components':{'sam3':{'files':[
            {'rel':'w','sha256':'a'*64,'bytes':1}]}}})
        frames={'native_frames':[Image.new('RGB',(2,2))], 'anchor_slots':[0],
                'anchor_indices':[1], 'dense_indices':[1]}
        cache=ReadCache(100000)
        from e2e_reader import grounding,geometry
        with patch.dict(sys.modules,{'student_pilot':package,'student_pilot.sam3_tower':module}), \
             patch.object(stage1,'StageOne',Stage),patch.object(stage1,'sam3_detect',detect), \
             patch.object(grounding,'StageOneSocket',Socket),patch.object(geometry,'frame_count',return_value=1):
            factory=stage1.stage1_factory(tower,None,lambda f:f['native_frames'],artifact=artifact,read_cache=cache)
            a=factory(frames,'question-one').propose('Chair')
            b=factory(frames,'question-two').propose(' chair ')
            self.assertEqual(digest(a['raw']),digest(b['raw']))
            self.assertNotEqual(a['geometry'],b['geometry'])
            self.assertEqual(calls,{'encode':1,'detect':1})
            factory(frames,'q3').propose('table')
            self.assertEqual(calls,{'encode':1,'detect':2})
            frames['native_frames'][0].putpixel((0,0),(1,0,0))
            factory(frames,'q4').propose('chair')
            self.assertEqual(calls,{'encode':2,'detect':3})
            artifact.manifest['components']['sam3']['files'][0]['sha256']='b'*64
            factory(frames,'q5').propose('chair')
            self.assertEqual(calls,{'encode':3,'detect':4})

    def test_fifty_stub_reads_original_default_off_and_cache_on(self):
        from contextlib import ExitStack
        from e2e_reader import parity,real
        source=Path(os.environ['READ_INPUT_SRC'])/'b/e2e_reader/parity.py'
        spec=importlib.util.spec_from_file_location('e2e_reader.reference_parity',source)
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        tasks=[dict(id=f'q{i}',room=f'room{i%5}',question_type='object_abs_distance',
                    question=f'question {i}',pixels=i%5) for i in range(50)]
        class Artifact:
            def __init__(self,*a,**k):pass
            def verify(self):return self
        class Budget:
            def __init__(self,*a,**k):pass
            def receipt(self,n):return {'tokens':n}
        def prompt(p,r):
            value=p.video_processor([np.full((2,),r['pixels'],np.float32)])
            return dict(pixels=value['pixels'],question=r['question'])
        runtime=types.ModuleType('evalpath.runtime');runtime.prompt_batch=lambda p,r,*a:prompt(p,r)
        package=types.ModuleType('evalpath');package.runtime=runtime
        def generate(model,processor,batch,*a,**k):
            with torch.no_grad():v=model.model.visual(batch['pixels'],torch.tensor([1,1,2]))
            text=batch['question']+' </think> '+str(float(v.pooler_output))
            return dict(text=text,tokens=list(text.encode()),finish='eos',calls={'records':[]},
                        heads={'pose9':[float(v.pooler_output)]},scale=None,entries={'prefill':1,'steps':2})
        settings=dict(arm='own_depth',frames_json={'captures':{}},dense_manifest={'captures':{}},
                      perception_memo='off',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
        all_results=[];hit_counts=[]
        for module,enabled in ((original,False),(parity,False),(parity,True)):
            visual=Qwen3_5VisionModel().eval().requires_grad_(False)
            model=types.SimpleNamespace(model=types.SimpleNamespace(visual=visual))
            processor=types.SimpleNamespace(video_processor=TinyVideoProcessor(),tokenizer=object(),
                                            _routing_tokens={'ids':{'ground':1}})
            cfg=dict(settings)
            if enabled:cfg.update(read_processor_cache='on',read_vision_cache='on')
            with ExitStack() as stack:
                stack.enter_context(patch.dict(sys.modules,{'evalpath':package,'evalpath.runtime':runtime}))
                stack.enter_context(patch.object(real,'real_perception',return_value=object()))
                stack.enter_context(patch.object(real,'generate_real',side_effect=generate))
                patches=dict(Artifact=Artifact,install=lambda *a:None,key=lambda t:t['id'],
                    load_native=lambda *a,**k:(model,processor,{'config':{},'export':{'frame_layout':'spread'}}),
                    install_hook=lambda m,h:h,CallHook=lambda *a:object(),
                    policy=lambda:types.SimpleNamespace(ThinkingBudget=Budget,DECODE_BUDGET=16384),
                    bind_item=lambda t,s:dict(id=t['id'],row=t,frames={}),score=lambda t,r:{'answer':1.})
                for name,value in patches.items():stack.enter_context(patch.object(module,name,value))
                gen=module.make_real('unused',dict(root='unused',name='x',sha256='a'*64),tasks,
                                     settings=cfg,device='cpu')
                values=[gen(t) for t in tasks]
                semantic=[{k:v for k,v in r.items() if k not in ('seconds','read_cache')} for r in values]
                all_results.append(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode())
                hit_counts.append(visual.calls)
        self.assertEqual(all_results[0],all_results[1]);self.assertEqual(all_results[1],all_results[2])
        self.assertEqual(hit_counts,[50,50,5])


if __name__=='__main__': unittest.main(verbosity=2)
