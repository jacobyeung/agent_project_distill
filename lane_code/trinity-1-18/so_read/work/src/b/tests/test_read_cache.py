"""CPU fixtures: run with Python -I -s -B and this file's absolute path."""
import dataclasses
import importlib.util
import json
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


if __name__=='__main__': unittest.main(verbosity=2)
