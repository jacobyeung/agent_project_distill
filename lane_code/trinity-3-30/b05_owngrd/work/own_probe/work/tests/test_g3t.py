import sys
import ast
import types
import unittest
from pathlib import Path
import torch
from torch import nn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from g3t_taps import import_vendor,TapCapture,maps_from_tokens,sparse_retention,TAPS,write_patch,sparse_source,VENDOR
torch.set_num_threads(4)


class G3TTests(unittest.TestCase):
    def test_grid_and_frame_order(self):
        x=torch.arange(3*6).reshape(1,3,6,1).float()
        x=torch.cat([torch.full((1,3,5,1),-1.),x],2)
        maps=maps_from_tokens([x]*24,5,(28,42),14,frame_order=[2,0,1])
        self.assertTrue(torch.equal(maps['5'][:,:, :,0],torch.arange(18).reshape(3,2,3)[[2,0,1]]))
        self.assertIs(maps['trunk'],maps['23'])

    def test_all_heads_byte_equal_sparse_and_taps(self):
        cls=import_vendor()
        from vggt.models.aggregator import Aggregator
        from vggt.heads.camera_head import CameraHead
        from vggt.heads.dpt_head import DPTHead
        torch.manual_seed(17)
        model=cls.__new__(cls);nn.Module.__init__(model)
        model.aggregator=Aggregator(img_size=28,patch_size=14,embed_dim=32,depth=24,num_heads=4,
                                    mlp_ratio=2,patch_embed='conv',rope_freq=100)
        model.local_camera_head=CameraHead(dim_in=64,trunk_depth=1,num_heads=4,pose_encoding_type='noT_quaR_FoV')
        model.global_camera_head=CameraHead(dim_in=64,trunk_depth=1,num_heads=4,pose_encoding_type='absT_quaRy_noFoV')
        model.depth_head=DPTHead(dim_in=64,features=8,out_channels=[8,8,8,8],output_dim=2,activation='exp',conf_activation='expp1')
        model.point_head=DPTHead(dim_in=64,features=8,out_channels=[8,8,8,8],output_dim=4,activation='inv_log',conf_activation='expp1')
        model.eval();x=torch.rand(3,3,28,42);before=set(model.state_dict())
        with torch.inference_mode():
            original=model(x)
            with TapCapture(model,(28,42),sparse=False) as full:with_taps=model(x)
            with TapCapture(model,(28,42),sparse=True) as sparse:reduced=model(x)
            with sparse_retention(model.aggregator):tokens,start=model.aggregator(x[None])
            tree=ast.parse(sparse_source((VENDOR/'vggt/models/aggregator.py').read_text()))
            cls_node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Aggregator')
            forward=next(n for n in cls_node.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
            method=model.aggregator.forward;namespace={}
            exec(compile(ast.Module(body=[forward],type_ignores=[]),'<delivered static patch>','exec'),method.__func__.__globals__,namespace)
            model.aggregator.forward=types.MethodType(namespace['forward'],model.aggregator)
            try:static=model(x)
            finally:model.aggregator.forward=method
        self.assertEqual(sum(t is not None for t in tokens),5)
        self.assertEqual(set(model.state_dict()),before)
        for key in original:
            if isinstance(original[key],list):
                for a,b,c,d in zip(original[key],with_taps[key],reduced[key],static[key]):
                    self.assertTrue(torch.equal(a,b),key);self.assertTrue(torch.equal(a,c),key);self.assertTrue(torch.equal(a,d),key)
            else:
                self.assertTrue(torch.equal(original[key],with_taps[key]),key)
                self.assertTrue(torch.equal(original[key],reduced[key]),key)
                self.assertTrue(torch.equal(original[key],static[key]),key)
        for key in full.maps:self.assertTrue(torch.equal(full.maps[key],sparse.maps[key]),key)
        self.assertFalse(hasattr(model.aggregator,'_own_keep_indices'))


if __name__=='__main__':unittest.main()
