"""Native Qwen3.5 + native tiny G3T CPU acceptance, without socket collectives."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
from torch.nn import functional as F
from student_pilot import gf1, g3t_online as gx
from student_pilot.carrier_c1 import CarrierC1, parameter_groups, RECIPE
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.carrier_c1_data import insert_frame_carriers, mixed_indices

# Do not import test_gx_carrier: its socket probe is outside this lane's authorization.
from tests.test_carrier_c1 import Tokenizer


def settings(stage=1, injection='pre_lm', router=False):
    production = json.loads((Path(__file__).resolve().parents[1]/f'configs/gf1_stage{stage}.json').read_text())
    cfg = gf1.normalize(production['gf1'] | dict(injection=injection, hidden=16, dense_frames=64,
                             layers=[0, 1, 2], top_k=2 if router else 0))
    return dict(schema='gx-carrier-v1', mode='frozen', encoder=dict(repository=gx.REPOSITORY,
        revision=gx.REVISION, source_sha256=gx.vendor_digest(),
        weights=dict(path='/fixture/model.safetensors', sha256='a'*64),
        config=dict(path='/fixture/config.json', sha256='b'*64)), input=gx.INPUT, feature=gx.FEATURE,
        connector=dict(out_init='zero', rms_cam='warm_start_carrier_median_rms_v1', rms_scale=1.),
        finetune=None, gf1=cfg)


class TinyEncoder(gx.G3TEncoder):
    def __init__(self, block):
        super().__init__(block, dict(aggregator=dict(img_size=28, patch_size=14, embed_dim=16, depth=3,
            num_heads=2, patch_embed='conv'), head=dict(dim_in=32, trunk_depth=1, num_heads=2)), image_size=28)
        self.calls = 0
    def forward(self, images, coords=None):
        self.calls += 1
        assert not torch.is_grad_enabled(), 'Tower must run under no_grad'
        cam, local, global_, bank = super().forward(images, coords)
        return F.pad(cam, (0, 2048-cam.shape[-1])), local, global_, F.pad(bank, (0, 2048-bank.shape[-1]))


def fixture(stage=1, injection='pre_lm', router=False):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    torch.manual_seed(31)
    text = dict(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=3,
                num_attention_heads=4, num_key_value_heads=2, head_dim=8, use_cache=False,
                layer_types=['linear_attention','full_attention','full_attention'], linear_key_head_dim=4,
                linear_value_head_dim=4, linear_num_key_heads=4, linear_num_value_heads=4,
                pad_token_id=0, rope_parameters=dict(rope_type='default', rope_theta=10000.,
                                                    mrope_section=[1,1,2], partial_rotary_factor=1.))
    vision = dict(depth=3, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=32,
                  num_position_embeddings=16, patch_size=2, temporal_patch_size=2, spatial_merge_size=2)
    config = Qwen3_5Config(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                          vision_start_token_id=62, vision_end_token_id=63)
    for item in (config,config.text_config,config.vision_config): item._attn_implementation='sdpa'
    base = Qwen3_5ForConditionalGeneration(config).float()
    camera = dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
                  weight_gravity=.05,weight_scale=.02,supervision=dict(path='/fixture',sha256='a'*64))
    geometry = settings(stage, injection, router)
    stage_config=json.loads((Path(__file__).resolve().parents[1]/f'configs/gf1_stage{stage}.json').read_text())
    cfg = dict(schema='carrier-c1-run-v1', training_mode='final', depth_enabled=False,
        depth_fov_source='pose_head', frame_layout='duplicate', init='base', parallel='fsdp',all_frames=True,
        carrier_placement='append_after_temporal_group_video_tokens_v1', streams=dict(pose={},vqa={},pointing={},routing={}),
        mix=['pose','vqa','pointing','routing'],world_size=4, reference_world_size=4,
        steps=stage_config['steps'],milestones=stage_config['milestones'],geometry_online=geometry,
        trace_program_version='3.14')
    cfg['scheduled_sampling']=dict(seed=17,max_own_probability=1.,pose_open_deg=45.,pose_full_deg=25.,
        fov_open_deg=2.,depth_open_absrel=.25,ema_steps=100,force_from_step=0,exposure_from_step=None,exposure_probability=0.)
    cfg['recipe']=recipe_for(cfg)
    with patch.object(gx,'G3TEncoder',TinyEncoder):
        model=CarrierC1(base,camera,{},5,training_mode='final',depth_enabled=False,
            frame_layout='duplicate',depth_fov_source='pose_head',recipe=cfg['recipe'],
            geometry_online=geometry,geometry_runtime=dict(image_mean=[.5]*3,image_std=[.25]*3))
    from student_pilot.trace_version import bind
    bind(model,cfg)
    ids=torch.tensor([[2]+[v for _ in range(32) for v in (62,61,63)]+[10,11,12,13]])
    batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=torch.full_like(ids,-100),
        mm_token_type_ids=torch.where(ids==61,2,0),video_grid_thw=torch.tensor([[32,2,2]]),
        pixel_values_videos=torch.randn(128,24))
    batch['labels'][0,-2:]=ids[0,-2:]
    batch=insert_frame_carriers(batch,Tokenizer(),frame_layout='duplicate')
    batch.update(aux_g3t_images=torch.rand(1,64,3,28,28),
                 aux_g3t_coords=torch.tensor([[[0.,0.,1024.,1024.]]*64]),aux_gf1_lm_indices=torch.arange(0,64,2)[None])
    return model,batch,cfg


def logits(model,batch):
    return model.lm_head(model.hidden(batch))


def equal(a,b):
    if isinstance(a,torch.Tensor): return torch.equal(a,b)
    if isinstance(a,dict): return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(tuple,list)): return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


class GF1Tests(unittest.TestCase):
    def test_step_zero_checkpoint_identity(self):
        for injection in ('pre_lm','lm_012'):
            for stage in (1,2):
                model,batch,cfg=fixture(stage,injection)
                model.eval()
                with torch.no_grad():
                    # Same loaded carrier checkpoint, with GF1 disabled vs attached.
                    geometry=model.geometry_online;model.geometry_online=None
                    expected=logits(model,batch).clone();model.geometry_online=geometry
                    actual=logits(model,batch)
                self.assertTrue(torch.equal(expected,actual), (stage,injection,float((expected-actual).abs().max())))
                self.assertEqual(model.auxiliary_heads.geometry_encoder.calls,2)

    def test_exact_patch_alignment_and_crop(self):
        features=torch.zeros(2,4,4,1);features[1,2,3,0]=8
        coords=torch.tensor([[0.,0.,1024.,1024.]]*2)
        pooled=gf1.area_pool(features,coords,torch.tensor([2,4,4]))
        self.assertEqual(pooled.nonzero()[:,0].tolist(),[7]);self.assertEqual(float(pooled[7]),2.)
        # Right half of a padded square: x=3 maps to right output cell, no padding leak.
        cropped=gf1.area_pool(features,torch.tensor([[512.,0.,1024.,1024.]]*2),[2,4,4])
        self.assertEqual(cropped.nonzero()[:,0].tolist(),[7]);self.assertEqual(float(cropped[7]),4.)

    def test_every_rank_forward_backward_and_gradient_isolation(self):
        records=[]
        for stage in (1,2):
            for rank in range(4):
                model,batch,cfg=fixture(stage);model.train()
                # Distinct deterministic rank batch, with the native global plan's rank index.
                plan=next(mixed_indices(dict(pose=20,vqa=20,pointing=20,routing=20),1,
                    training_mode='final',mix=cfg['recipe']['mix'],world=cfg['world_size']))
                index=next(ids[rank] for stream,ids in plan if stream=='vqa')
                batch['pixel_values_videos']=batch['pixel_values_videos'] + index/100
                optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
                losses=[]
                for step in range(2):
                    optimizer.zero_grad(set_to_none=True)
                    result=model(batch,stream='vqa');result['loss'].backward()
                    self.assertTrue(torch.isfinite(result['loss']))
                    out=model.auxiliary_heads.gf1.outputs[0].weight
                    self.assertGreater(float(out.grad.abs().sum()),0.)
                    if step==1:
                        self.assertGreater(sum(float(p.grad.abs().sum()) for p in model.auxiliary_heads.gf1.projections.parameters()),0.)
                    if stage==1:
                        self.assertTrue(all(p.grad is None for n,p in model.named_parameters() if not n.startswith('auxiliary_heads.gf1.')))
                    else:
                        self.assertGreater(sum(float(p.grad.abs().sum()) for p in model.model.language_model.parameters() if p.grad is not None),0.)
                        self.assertEqual(next(g['lr'] for g in optimizer.param_groups if g['name']=='gf1'),cfg['recipe']['lm_learning_rate'])
                    self.assertTrue(all(p.grad is None for p in model.auxiliary_heads.geometry_encoder.parameters()))
                    optimizer.step();losses.append(float(result['loss'].detach()))
                records.append(dict(stage=stage,rank=rank,row=index,losses=losses))
        Path(os.environ['LANE_TEST_OUTPUT'],'gf1_ranks.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_save_load_resume_step3_optimizer_exact(self):
        records=[]
        for stage in (1,2):
            model,batch,cfg=fixture(stage);model.train()
            optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
            def step(m,o):
                o.zero_grad(set_to_none=True);loss=m(batch,stream='vqa')['loss'];loss.backward();o.step();return loss.detach()
            step(model,optimizer);step(model,optimizer)
            path=Path(tempfile.mkdtemp(prefix='gf1_resume_',dir=os.environ['LANE_TEST_OUTPUT']))/'step2.pt'
            torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),rng=torch.get_rng_state(),step=2),path)
            third=step(model,optimizer)
            resumed,_,_=fixture(stage);resumed.train()
            restored=torch.load(path,weights_only=True)
            resumed.load_state_dict(restored['model'])
            opt=torch.optim.AdamW(parameter_groups(resumed,cfg['recipe']),foreach=False)
            opt.load_state_dict(restored['optimizer']);torch.set_rng_state(restored['rng'])
            other=step(resumed,opt)
            self.assertTrue(torch.equal(third,other));self.assertTrue(equal(model.state_dict(),resumed.state_dict()))
            self.assertTrue(equal(optimizer.state_dict(),opt.state_dict()))
            records.append(dict(stage=stage,step=3,loss=float(third),model_exact=True,optimizer_exact=True))
        Path(os.environ['LANE_TEST_OUTPUT'],'gf1_resume.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_deep_checkpoint_recomputation_and_router(self):
        for injection,router in [('lm_012',False),('pre_lm',True)]:
            model,batch,cfg=fixture(1,injection,router);model.train()
            optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
            for _ in range(2):
                optimizer.zero_grad(set_to_none=True);model(batch,stream='vqa')['loss'].backward();optimizer.step()
            self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.auxiliary_heads.gf1.parameters()))
            if router:self.assertGreater(float(model.auxiliary_heads.gf1.router.weight.grad.abs().sum()),0.)

    def test_nested_frame_rejection(self):
        model,batch,_=fixture()
        for mapping in ([[0,0]],[[2,0]],[[0,4]]):
            with self.assertRaises(ValueError):model({**batch,'aux_gf1_lm_indices':torch.tensor(mapping)},stream='vqa')
        with self.assertRaises(ValueError):gf1.dense_inputs(dict(student_input=dict(frames=[])),gf1.DEFAULT)

if __name__=='__main__': unittest.main()
