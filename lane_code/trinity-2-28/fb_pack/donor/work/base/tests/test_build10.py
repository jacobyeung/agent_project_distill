import unittest
import math
import numpy as np
import torch
from student_pilot.fixed_readout import DepthReadout

class DepthMath(unittest.TestCase):
    def test_numeric_byte_parity(self):
        module=DepthReadout()
        rng=np.random.default_rng(19)
        for uv in ([0,0],[1000,1000],[500,500],[350,750]):
            for _ in range(30):
                values=rng.uniform(0.00001,10,25)
                vertical,horizontal=rng.uniform(.2,2,2)
                got=module(None,[vertical,horizontal],uv,1,None,sampled=values)
                p20,p30,p50,p80=(np.percentile(values,q) for q in (20,30,50,80))
                ray=np.array([(uv[0]/500-1)*math.tan(horizontal/2),(uv[1]/500-1)*math.tan(vertical/2),1.])
                self.assertEqual(got['spread'],(p80-p20)/max(p50,1e-3))
                np.testing.assert_array_equal(got['camera_point'],np.round(ray*p30,8))
        self.assertFalse(list(module.parameters()))

    def test_real_depth_query_and_roundtrip(self):
        from student_pilot.point_depth_head import PointDepthHead
        head=PointDepthHead(16,dict(d_proj=16,num_heads=4,context_depth=1,mlp_hidden=16),16)
        module=DepthReadout()
        feature=torch.randn(32,16,4,4)
        got=module(feature,[1.,1.],[500,500],2,head)
        clone=DepthReadout();clone.load_state_dict(module.state_dict())
        again=clone(feature,[1.,1.],[500,500],2,head)
        np.testing.assert_array_equal(got['camera_point'],again['camera_point'])
        with self.assertRaises(ValueError):module(None,[1,1],[500,500],1,None,sampled=np.zeros(25))

    def test_model_forward(self):
        from tests.test_batched_routed_decode import fixture
        model,processor,batch=fixture()
        calls=[]
        handle=model.auxiliary_heads.depth_readout.register_forward_hook(lambda *args:calls.append(True))
        got=model(dict(depth_map=None,fov_hw=[1,1],uv=[500,500],frame=1,depth_head=None,
                       sampled=np.ones(25)),stream='depth_readout')
        handle.remove()
        self.assertEqual(len(calls),1)
        self.assertEqual(got['depth_p30'],1.)
