import unittest
import torch
from tests.fixtures import tiny,camera_fixtures,packed,routing_batch,Processor
from student_pilot import carrier_c1_run as run,h1

class OwnForward(unittest.TestCase):
    def test_native_readout_faithful_labels_and_full_forward(self):
        torch.set_num_threads(2)
        model,base,_=tiny();model.recipe['weights']['routing']=1.
        raw,clip,_=camera_fixtures();row=packed(raw[0],clip);batch,audit=routing_batch(base,row)
        class Rows:
            h1={'faithful_own_camera_rows':True,'routing_pose_targets':True};processor=Processor()
            def row(self,*args):return row,None
        own,audit=run.own_values(model,Rows(),batch,audit,0,(True,True),torch.device('cpu'))
        self.assertEqual(audit['h1']['values'],'own')
        targets,_=h1.pose_targets(row,own,{})
        value=model(own,run.move(targets,torch.device('cpu')),stream='routing')
        self.assertTrue(torch.isfinite(value['loss']))
        self.assertGreater(float(value['components']['routing']),0.)
        self.assertGreater(float(value['components']['pose']),0.)
        value['loss'].backward()
        self.assertGreater(float(model.lm_head.weight.grad.norm()),0.)
