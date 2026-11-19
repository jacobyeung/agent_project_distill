"""Native tiny Qwen CPU fixtures; no pretrained weights or network access."""
import copy
import json
import math
import os
from pathlib import Path
import tempfile
import time
import unittest

import numpy as np
import torch

from student_pilot.carrier_c1 import CarrierC1, parameter_groups
from student_pilot.carrier_c1_data import insert_frame_carriers, mixed_indices, mask_target
from student_pilot.decoupled_v import target_tensors
from student_pilot.p3_provenance import file_pin


class Tokenizer:
    def encode(self, text, **kwargs):
        return [5]

    def convert_tokens_to_ids(self, token):
        return 5 if token == '<|fim_middle|>' else 61


def fixture(groups=16, depth_labels=True, placement='append_after_temporal_group_video_tokens_v1',
            training_mode='mixed', depth_enabled=True, trace_program_version='3.13'):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    torch.manual_seed(31)
    text = dict(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                num_attention_heads=4, num_key_value_heads=2, head_dim=8, use_cache=False,
                layer_types=['linear_attention', 'full_attention'], linear_key_head_dim=4,
                linear_value_head_dim=4, linear_num_key_heads=4, linear_num_value_heads=4,
                pad_token_id=0, rope_parameters=dict(rope_type='default', rope_theta=10000.,
                                                    mrope_section=[1, 1, 2], partial_rotary_factor=1.))
    vision = dict(depth=3, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=32,
                  num_position_embeddings=16, patch_size=2, temporal_patch_size=2, spatial_merge_size=2)
    config = Qwen3_5Config(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                         vision_start_token_id=62, vision_end_token_id=63)
    for item in (config, config.text_config, config.vision_config):
        item._attn_implementation = 'sdpa'
    base = Qwen3_5ForConditionalGeneration(config).float()
    camera = dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
                  weight_gravity=.05, weight_scale=.02, supervision={'path':'/fixture', 'sha256':'a'*64})
    depth = dict(weight=.05, d_proj=16, mlp_hidden=16, num_heads=4, context_depth=1, vit_layers=[1,2,3])
    model = CarrierC1(base, camera, depth, 5, placement, training_mode, depth_enabled)
    model.trace_program_version = trace_program_version
    ids = torch.tensor([[2]+[v for _ in range(groups) for v in (62,61,63)]+[10,11,12,13]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids,-100),
                 mm_token_type_ids=torch.where(ids==61,2,0),
                 video_grid_thw=torch.tensor([[groups,2,2]]), pixel_values_videos=torch.randn(groups*4,24))
    batch['labels'][0,-2:] = ids[0,-2:]
    batch = insert_frame_carriers(batch, Tokenizer(), carrier_placement=placement)
    record = dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*32,
                  camera_mask=[True]*(2*groups)+[False]*(32-2*groups),
                  trajectory_scale=1., gravity=[0.,-1.,0.], gravity_mask=True,
                  point_depth=dict(uv=[[[500.,500.],[200.,300.]]]*32, depth=[[2.,3.]]*32,
                                   mask=[[depth_labels,depth_labels]]*(2*groups)+[[False,False]]*(32-2*groups)))
    return model, batch, target_tensors(record, all_frames=True)


class CarrierTests(unittest.TestCase):
    def test_placement_mask_grid_and_short_rows(self):
        model, batch, targets = fixture(4)
        positions = batch['aux_camera_positions'][0]
        self.assertEqual(positions[:8].tolist(), [3,4,8,9,13,14,18,19])
        self.assertTrue((positions[8:] == -1).all())
        self.assertTrue((batch['labels'][0,positions[:8]] == -100).all())
        self.assertEqual(int((batch['input_ids'] == 61).sum()),4)
        self.assertEqual(int((batch['labels'] != -100).sum()),2)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            insert_frame_carriers(batch, Tokenizer())
        result = model(batch, targets)
        self.assertTrue(torch.isfinite(result['loss']))

    def test_native_final_norm_and_question_independence(self):
        model, batch, target = fixture()
        model.eval()
        captured = []
        handle = model.model.language_model.norm.register_forward_hook(lambda m,a,o: captured.append(o))
        with torch.no_grad():
            first = model(batch, target, return_states=True)
        handle.remove()
        expected = model.auxiliary_heads.pose.carrier_states(captured[0],batch['aux_camera_positions'])
        torch.testing.assert_close(first['states'], expected, rtol=0, atol=0)
        other = {**batch, 'input_ids':batch['input_ids'].clone()}
        other['input_ids'][0,-4:] = torch.tensor([20,21,22,23])
        with torch.no_grad():
            second = model(other, target, return_states=True)
        torch.testing.assert_close(first['states'], second['states'], rtol=0, atol=0)
        self.assertFalse(torch.equal(first['states'][:,0],first['states'][:,1]))

    def test_native_gradients_update_lm_pose_private_depth_but_not_base_vision(self):
        model, batch, target = fixture()
        before = {n:p.detach().clone() for n,p in model.named_parameters()}
        optimizer = torch.optim.AdamW(parameter_groups(model))
        model(batch,target)['loss'].backward()
        for prefix in ('model.language_model.', 'auxiliary_heads.pose.', 'auxiliary_heads.depth.model.visual.'):
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0
                                for n,p in model.named_parameters() if n.startswith(prefix)), prefix)
        self.assertTrue(all(p.grad is None for p in model.model.visual.parameters()))
        optimizer.step()
        self.assertTrue(any(not torch.equal(p,before[n]) for n,p in model.named_parameters()
                            if n.startswith('model.language_model.')))
        self.assertTrue(all(torch.equal(p,before[n]) for n,p in model.named_parameters()
                            if n.startswith('model.visual.')))
        model.zero_grad(set_to_none=True)
        model.auxiliary_heads.depth(batch,target)[0].backward()
        self.assertTrue(all(p.grad is None for p in model.model.language_model.parameters()))
        self.assertTrue(all(p.grad is None for p in model.auxiliary_heads.pose.parameters()))

    def test_preservation_and_pointing_train_lm_without_geometry_losses(self):
        model, batch, target = fixture()
        for stream in ('vqa','pointing'):
            model.zero_grad(set_to_none=True)
            result = model(batch,stream=stream)
            result['loss'].backward()
            self.assertGreater(float(result['components'][stream]),0)
            self.assertEqual(float(result['components']['pose']),0)
            self.assertGreater(float(model.lm_head.weight.grad.abs().sum()),0)

    def test_native_cached_generation_uses_carriers_and_cleans_hooks(self):
        model,batch,_=fixture(4)
        for key in ('input_ids','attention_mask','labels','mm_token_type_ids'):
            batch[key]=batch[key][:,:-2]
        model.eval()
        hooks_before=len(model.get_input_embeddings()._forward_hooks)
        output=model.generate(batch,max_new_tokens=2,do_sample=False,pad_token_id=0,eos_token_id=1)
        self.assertGreater(output.shape[1],batch['input_ids'].shape[1])
        self.assertLessEqual(output.shape[1],batch['input_ids'].shape[1]+2)
        self.assertEqual(len(model.get_input_embeddings()._forward_hooks),hooks_before)

    def test_a0_even_target_mapping_and_private_depth_readout(self):
        model,batch,target=fixture()
        legacy=dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*16,camera_mask=[True]*16,
                    trajectory_scale=1.,gravity=[0.,-1.,0.],gravity_mask=True,
                    point_depth=dict(uv=[[[200.,300.],[500.,500.]]]*16,
                                     depth=[[2.,3.]]*16,mask=[[True,True]]*16))
        expanded=target_tensors(legacy,all_frames=True)
        self.assertFalse(expanded['aux_camera_mask'][:,::2].any())
        self.assertTrue(expanded['aux_camera_mask'][:,1::2].all())
        self.assertFalse(expanded['aux_point_depth_mask'][:,::2].any())
        uv=[[[200.,300.],[500.,500.]]]*16
        values=model.eval().readout(batch,uv)
        self.assertEqual(len(values['raw_pose']),32)
        self.assertEqual(len(values['point_depth']),16)
        changed={**batch,'input_ids':batch['input_ids'].clone()}
        changed['input_ids'][0,-4:]=torch.tensor([20,21,22,23])
        self.assertEqual(values,model.readout(changed,uv))

    def test_mix_is_rank_aligned_resumable_and_exact(self):
        counts = dict(pose=37,vqa=11,pointing=7)
        plans = list(mixed_indices(counts,6))
        self.assertEqual(plans[3:],list(mixed_indices(counts,6,start_step=3)))
        for plan in plans:
            self.assertEqual([s for s,_ in plan],['pose','pose','vqa','pointing'])
            self.assertTrue(all(len(indices)==8 for _,indices in plan))
        with self.assertRaises(ValueError):
            list(mixed_indices({**counts,'pointing':0},1))

    def test_concave_mask_target_is_inside_and_provenance_is_checked(self):
        out = Path(tempfile.mkdtemp(dir=os.environ['LANE_TEST_OUTPUT']))
        mask = np.zeros((16,16),dtype=bool); mask[2:14,2:4]=True; mask[12:14,2:14]=True
        np.savez(out/'mask.npz',mask=mask)
        text,audit = mask_target(file_pin(out/'mask.npz'))
        self.assertTrue(mask[tuple(audit['pixel_yx'])])
        u,v = json.loads(text)['point_2d']
        self.assertTrue(mask[v*16//1000,u*16//1000])
        with self.assertRaises(ValueError):
            mask_target({'path':str(out/'mask.npz'),'sha256':'0'*64})


if __name__ == '__main__':
    unittest.main()
