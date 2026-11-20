"""Run the actual local lifting/provider functions on synthetic geometry, CPU only."""
import importlib.util
import json
import hashlib
from pathlib import Path
import sys
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
from capture import Capture

class LiftingTests(unittest.TestCase):
    def test_exact_lifter_hook(self):
        here=Path(__file__).parent
        pins=json.loads((here/'SOURCE_PINS.json').read_text())
        for name in ('stage1','grounding'):
            data=(here/f'fixtures/{name}.py.txt').read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),pins[f'fixtures/{name}.py.txt'])
        package=ModuleType('fixture_reader');package.__path__=[]
        gm=ModuleType('fixture_reader.geometry');gm.frame_count=lambda g:32
        box=ModuleType('trace_format.box_v313');box.in_f1=lambda g,c,l,a:dict(centre=c,lengths=l,axes=a)
        trace=ModuleType('trace_format');trace.__path__=[]
        mod=ModuleType('fixture_reader.grounding');mod.__package__='fixture_reader'
        code=compile((here/'fixtures/grounding.py.txt').read_text(),str(here/'fixtures/grounding.py.txt'),'exec')
        with patch.dict(sys.modules,{'fixture_reader':package,'fixture_reader.geometry':gm,
                                    'trace_format':trace,'trace_format.box_v313':box}):
            exec(code,mod.__dict__)
            class S:
                def features(self):return None
                def select(self):return None
            def lift(frame,uv,mode):
                p=np.c_[uv/1000,1+uv[:,0]/1000+uv[:,1]/1000]
                return p,p,np.zeros(len(p))
            g=NS(has=lambda f:True,lift=lift)
            masks=np.zeros((32,4,4),bool);masks[:3,1:3,1:3]=True
            baseline=mod.lift_bestspread('x',masks,g)
            cap=Capture(S,mod);cap.by_name['x']={}
            with cap:
                actual=mod.lift_bestspread('x',masks,g)
                mod.MinAreaBoxProvider()('x',actual,g,actual['best'])
            self.assertEqual(actual,baseline)
            self.assertEqual(cap.by_name['x']['lift']['frame_count'],3)
            self.assertEqual(cap.by_name['x']['lift']['point_frames'],[1])
            self.assertIsNotNone(cap.by_name['x']['fitted_box']['world']['centroid'])

if __name__=='__main__':unittest.main()
