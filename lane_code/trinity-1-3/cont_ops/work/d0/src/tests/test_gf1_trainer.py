"""Actual C1 optimizer, stream admission and immutable checkpoint/restore on CPU."""
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import torch
import torch.distributed as dist
from student_pilot import carrier_c1_run as run, gf1
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.decoupled_v import target_tensors
from student_pilot.carrier_c1_data import mixed_indices
from tests.test_gf1 import fixture, equal


def collectives():
    context=ExitStack()
    for name,value in [('get_rank',0),('get_world_size',1),('get_backend','gloo')]:
        context.enter_context(patch.object(dist,name,return_value=value))
    for name in ('barrier','broadcast','broadcast_object_list'):
        context.enter_context(patch.object(dist,name))
    context.enter_context(patch.object(dist,'all_gather_object',side_effect=lambda out,value:out.__setitem__(0,value)))
    return context


class Rows:
    def __init__(self,batch):self.batch=batch
    def count(self,stream):return 40
    def get(self,stream,index):
        batch=copy.deepcopy(self.batch)
        batch['pixel_values_videos']+=index/100
        if stream=='pose':
            record=dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*32,camera_mask=[True]*2+[False]*30,
                trajectory_scale=1.,gravity=[0.,-1.,0.],gravity_mask=True,
                point_depth=dict(uv=[[[500.,500.]]]*32,depth=[[2.]]*32,mask=[[False]]*32))
            targets=target_tensors(record,all_frames=True);batch['labels'].fill_(-100)
        else: targets=None
        return batch,targets,dict(index=index)


class TrainerAcceptance(unittest.TestCase):
    def _native_rank(self, stage, rank):
        reports=[]
        model,batch,cfg=fixture(stage);model.train();rows=Rows(batch)
        optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
        plans=list(mixed_indices(dict(pose=40,vqa=40,pointing=40,routing=40),3,
            training_mode='final',mix=cfg['recipe']['mix'],world=cfg['world_size']))
        # GT values remain in the fixture's routing row; no scheduled readout substitutes its targets.
        first,_=run.optimize_step(model,optimizer,rows,plans[0],rank,torch.device('cpu'),1,False)
        self.assertFalse(first['skipped_microsteps']);self.assertEqual(set(first['stream_means']),{'pose','vqa','pointing','routing'})
        self.assertGreater(first['gradient_norms']['gf1'],0.)
        if stage==1:self.assertEqual(set(first['gradient_norms']),{'gf1'})
        run.optimize_step(model,optimizer,rows,plans[1],rank,torch.device('cpu'),2,False)
        root=Path(tempfile.mkdtemp(prefix=f'gf1_native_s{stage}r{rank}_',dir=os.environ['LANE_TEST_OUTPUT']))
        with collectives():
            pin=run.checkpoint(root/'checkpoint2',model,optimizer,{},2)
        third,_=run.optimize_step(model,optimizer,rows,plans[2],rank,torch.device('cpu'),3,False)
        restored,_,_=fixture(stage);restored.train()
        other=torch.optim.AdamW(parameter_groups(restored,cfg['recipe']),foreach=False)
        with collectives():self.assertEqual(run.restore(pin,restored,other,{}),2)
        result,_=run.optimize_step(restored,other,rows,plans[2],rank,torch.device('cpu'),3,False)
        self.assertTrue(equal(model.state_dict(),restored.state_dict()))
        self.assertTrue(equal(optimizer.state_dict(),other.state_dict()))
        self.assertEqual(third['components'],result['components'])
        reports.append(dict(stage=stage,rank=rank,first_stream_losses=first['stream_means'],
            first_gradients=first['gradient_norms'],checkpoint=str(pin['path']),step3_model_exact=True,
            step3_optimizer_exact=True,step3_loss_exact=True,collectives='mocked, no sockets'))
        Path(os.environ['LANE_TEST_OUTPUT'],f'gf1_native_s{stage}r{rank}.json').write_text(json.dumps(reports[0],indent=2)+'\n')

    def test_checkpointed_decoder_gradients_equal_plain(self):
        for injection in ('pre_lm','lm_012'):
            model,batch,cfg=fixture(1,injection);model.train()
            with torch.no_grad():
                for output in model.auxiliary_heads.gf1.outputs:output.weight.normal_(std=.0003)
            model(batch,stream='vqa')['loss'].backward()
            gradients={n:p.grad.clone() for n,p in model.named_parameters() if p.requires_grad}
            model.zero_grad(set_to_none=True);model.model.language_model.gradient_checkpointing_disable()
            model(batch,stream='vqa')['loss'].backward()
            self.assertTrue(all(torch.equal(gradients[n],p.grad) for n,p in model.named_parameters() if p.requires_grad))

    def test_lean_bank_equals_native_aggregator(self):
        model,batch,_=fixture();encoder=model.auxiliary_heads.geometry_encoder
        with torch.no_grad():
            cam,bank=encoder._lean(batch['aux_g3t_images'][0])
            native,start=encoder.aggregator(batch['aux_g3t_images'])
        self.assertTrue(torch.equal(bank,torch.stack([x[0,:,start:] for x in native])))

def _rank_test(stage, rank):
    def test(self):self._native_rank(stage, rank)
    return test

for _stage in (1,2):
    for _rank in range(4):
        setattr(TrainerAcceptance, f'test_stage{_stage}_rank{_rank}_streams_and_resume', _rank_test(_stage,_rank))

if __name__=='__main__':unittest.main()
