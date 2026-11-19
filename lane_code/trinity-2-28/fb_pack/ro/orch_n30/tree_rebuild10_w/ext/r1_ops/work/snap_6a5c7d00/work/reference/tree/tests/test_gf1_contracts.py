"""Dense RGB identity, cached generation, stage binding and memory arithmetic."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from student_pilot import gf1, gf1_config, gf1_memory, carrier_c1_data as data
from student_pilot import pose_samples as samples
from tests.test_gf1 import fixture, equal


class Contracts(unittest.TestCase):
    def test_native_cached_generation_both_injections(self):
        for injection in ('pre_lm','lm_012'):
            model,batch,_=fixture(1,injection);model.eval()
            geometry=model.geometry_online;model.geometry_online=None
            expected=model.generate(batch,max_new_tokens=3,do_sample=False,eos_token_id=None,pad_token_id=0)
            model.geometry_online=geometry
            actual=model.generate(batch,max_new_tokens=3,do_sample=False,eos_token_id=None,pad_token_id=0)
            self.assertTrue(torch.equal(expected,actual))
            with torch.no_grad():
                for output in model.auxiliary_heads.gf1.outputs:output.weight.normal_(std=.0003)
            generated=model.generate(batch,max_new_tokens=3,do_sample=False,eos_token_id=None,pad_token_id=0)
            self.assertEqual(generated.shape[1],batch['input_ids'].shape[1]+3)

    def test_dense_rgb_nesting_preserves_sparse_augmentation(self):
        dense=dict(frames=['a','b','c','d'],frame_indices=[0,1,2,3],timestamps=[0.,1.,2.,3.],fps=1,total_num_frames=4)
        inputs=dict(frames=['a','c'],frame_indices=[0,2],timestamps=[0.,2.],geometry_dense=dense,
                    fps=1,total_num_frames=4,question='where?',options=[])
        row=dict(student_input=inputs,target='A',category=samples.CATEGORY,pose_sample=dict(augment={}))
        raw=np.stack([np.full((4,4,3),20*i,np.uint8) for i in range(4)])
        snapshots={}
        def augment(arrays,settings):return arrays+np.arange(len(arrays),dtype=np.uint8)[:,None,None,None]
        def encode(processor,question,options,arrays,*a):
            snapshots['lm']=arrays.copy();return {},{}
        with patch.object(data,'layout_inputs',return_value=inputs),patch.object(samples,'load_frames',return_value=raw),\
             patch.object(samples,'check_sample'),patch.object(samples,'augment',side_effect=augment),\
             patch.object(samples,'encode_frames',side_effect=encode):
            batch,_=data.encode_layout_row(None,row,'duplicate',None,gf1=gf1.normalize(dict(dense_frames=4)))
        np.testing.assert_array_equal(snapshots['lm'][::2],augment(raw[[0,2]],{}))
        from student_pilot.g3t_online import native_square_518
        expected,_=native_square_518(augment(raw,{}), expected_frames=4)
        # Sparse augmentation uses its own draw positions: assert the unpatched native result.
        augmented=augment(raw,{});augmented[[0,2]]=augment(raw[[0,2]],{})
        expected,_=native_square_518(augmented, expected_frames=4)
        self.assertTrue(torch.equal(batch['aux_g3t_images'][0],expected))
        self.assertEqual(batch['aux_gf1_lm_indices'].tolist(),[[0,2]])
        bad=copy.deepcopy(row);bad['student_input']['frames'][1]='wrong'
        with self.assertRaises(ValueError):gf1.dense_inputs(bad,dict(dense_frames=4))

    def test_routed_head_features_feed_connector_without_replacing_fp32_modules(self):
        from student_pilot import tower_read as T
        model,batch,_=fixture();encoder=model.auxiliary_heads.geometry_encoder
        module=torch.nn.Module();module.aggregator=torch.nn.Linear(1,1)
        module.local_camera_head=torch.nn.Linear(1,1);module.global_camera_head=torch.nn.Linear(1,1)
        module.depth_head=torch.nn.Linear(1,1);depth=module.depth_head
        originals={k:v for k,v in module.named_children()}
        before=copy.deepcopy(module.state_dict())
        tower=SimpleNamespace(module=module,dense_frames=64,device=torch.device('cpu'))
        pins=model.geometry_online['encoder']
        with patch.object(T,'WEIGHTS_SHA256',pins['weights']['sha256']),\
             patch.object(T,'CONFIG_SHA256',pins['config']['sha256']),\
             patch.object(T,'SOURCE_SHA256',pins['source_sha256']):
            gf1.share_head_tower(model,tower)
        self.assertTrue(all(getattr(module,k) is v for k,v in originals.items()))
        self.assertTrue(equal(before,module.state_dict()));self.assertIs(module.depth_head,depth)
        with torch.inference_mode():
            cam,local,global_,bank=encoder(batch['aux_g3t_images'][0])
            blocks=[None]*24
            for j,i in enumerate(model.geometry_online['gf1']['layers']):
                blocks[i]=torch.zeros(1,64,9,2048);blocks[i][0,:,5:]=bank[j]
            blocks[23]=torch.zeros(1,64,9,2048);blocks[23][0,:,0]=cam
            gf1.bind_head_features(model,batch,blocks,5,batch['aux_g3t_images'][0],
                batch['aux_g3t_coords'][0],list(range(0,64,2)),local,global_)
        self.assertFalse(torch.is_inference(batch['aux_gf1_shared'].bank))
        self.assertIs(copy.deepcopy(batch['aux_gf1_shared']).encoder,encoder)
        result=model(batch,stream='vqa');result['loss'].backward()
        self.assertEqual(encoder.calls,2);self.assertTrue(result['metrics']['gx']['shared_head_tower'])
        self.assertGreater(float(model.auxiliary_heads.gf1.outputs[0].weight.grad.abs().sum()),0.)

    def test_requested_twelve_layer_bank_matches_native_aggregator(self):
        from student_pilot import g3t_online as gx
        from student_pilot._tower_native import selected_layers
        from tests.test_gf1 import settings
        cfg=settings();cfg['gf1']['layers']=list(range(12,24));cfg['gf1']['top_k']=2
        encoder=gx.G3TEncoder(cfg,dict(aggregator=dict(img_size=28,patch_size=14,embed_dim=16,depth=24,
            num_heads=2,patch_embed='conv'),head=dict(dim_in=32,trunk_depth=1,num_heads=2)),image_size=28)
        images=torch.rand(1,4,3,28,28)
        with torch.no_grad():
            _,bank=encoder._lean(images[0])
            blocks,start=selected_layers(encoder.aggregator,images,layers=sorted(set([4,11]+list(range(12,24)))))
        self.assertTrue(torch.equal(bank,torch.stack([blocks[i][0,:,start:] for i in range(12,24)])))

    def test_stall_guard_stops_only_its_child_group_and_keeps_log(self):
        import os
        import sys
        import tempfile
        from unittest.mock import Mock
        from scripts import gf1_stall_guard as guard
        root=Path(tempfile.mkdtemp(prefix='gf1_guard_',dir=os.environ['LANE_TEST_OUTPUT']))
        for stalled in (False,True):
            log=root/('stall.log' if stalled else 'exit.log')
            child=SimpleNamespace(pid=123456,poll=Mock(return_value=None if stalled else 0),
                                  wait=Mock(return_value=-15),returncode=0)
            argv=['guard','--log',str(log),'--stall-seconds','1','--startup-seconds','1','--poll-seconds','.05','--','fixture']
            with patch.object(sys,'argv',argv),patch.object(guard.subprocess,'Popen',return_value=child) as launch,\
                 patch.object(guard.time,'monotonic',side_effect=[0.,2.]),patch.object(guard.time,'sleep'),\
                 patch.object(guard.signal,'signal'),patch.object(guard.os,'killpg') as kill:
                self.assertEqual(guard.main(),124 if stalled else 0)
                self.assertTrue(launch.call_args.kwargs['start_new_session'])
                if stalled:kill.assert_called_once_with(child.pid,guard.signal.SIGTERM)
                else:kill.assert_not_called()
            self.assertEqual('GF1_STALL' in log.read_text(),stalled)

    def test_prefix_and_supervised_forward_share_one_tower_call(self):
        from student_pilot.carrier_c1_routing import prefix_batch
        from student_pilot.carrier_c1_run import move
        model,batch,_=fixture();batch['aux_gf1_cache']=gf1.ClipCache()
        prefix=move(prefix_batch(batch),torch.device('cpu'))
        with torch.no_grad():model.hidden(prefix)
        self.assertEqual(model.auxiliary_heads.geometry_encoder.calls,2)
        result=model(move(batch,torch.device('cpu')),stream='vqa')
        result['loss'].backward()
        self.assertEqual(model.auxiliary_heads.geometry_encoder.calls,2)
        self.assertTrue(result['metrics']['gx']['tower_cache_hit'])
        self.assertIsNone(batch['aux_gf1_cache'].value)

    def test_nonzero_warm_camera_context_is_preserved(self):
        model,_,_=fixture()
        gf1.check_camera_context(model,{})
        with torch.no_grad():model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.fill_(.01)
        with self.assertRaisesRegex(ValueError,'camera context'):gf1.check_camera_context(model,{})
        gf1.check_camera_context(model,dict(geometry_online=copy.deepcopy(model.geometry_online)))
        donor=copy.deepcopy(model.geometry_online);donor.pop('gf1')
        gf1.check_camera_context(model,dict(geometry_online=donor))
        donor['input']='wrong'
        with self.assertRaisesRegex(ValueError,'camera context'):gf1.check_camera_context(model,dict(geometry_online=donor))

    def test_stage1_bf16_base_forward_and_wrapper_contract(self):
        from student_pilot import carrier_c1_run as run
        from tests.test_gf1_trainer import collectives
        model,batch,cfg=fixture(1)
        model.model.to(torch.bfloat16);model.lm_head.to(torch.bfloat16)
        result=model(batch,stream='vqa');result['loss'].backward()
        self.assertGreater(float(model.auxiliary_heads.gf1.outputs[0].weight.grad.abs().sum()),0.)
        calls=[]
        def wrap(*args,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(mixed_precision=kwargs['mixed_precision'])
        with collectives(),patch('torch.distributed.fsdp.FullyShardedDataParallel',side_effect=wrap):
            wrapped=run.wrap_model(model,torch.device('cpu'))
        self.assertFalse(wrapped.mixed_precision.cast_root_forward_inputs)
        self.assertEqual(len(calls),1)
        self.assertTrue(all(not p.requires_grad for p in model.model.parameters()))

    def test_stage_configs_preserve_mix_and_lm_rate(self):
        root=Path(__file__).resolve().parents[1]
        _,_,source=fixture(2)
        source['init_artifact']=dict(artifact=dict(path='/fixture/artifact.json',sha256='a'*64),lm='full',heads=['pose'])
        source['lm_lr_scale']=.6
        for stage in (1,2):
            config=json.loads((root/f'configs/gf1_stage{stage}.json').read_text())
            if stage==2: config['gf1']['gf1_init']='zero'
            result=gf1_config.bind(source,config,'/scratch/run','/scratch/prepared')
            self.assertEqual(result['recipe']['global_batch'],source['recipe']['global_batch'])
            self.assertEqual(result['mix'],source['mix']);self.assertEqual(result['world_size'],config['world_size'])
            self.assertEqual(result['geometry_online']['gf1']['layers'],[11,17,23])
            self.assertEqual(result['lm_lr_scale'],.6)
        with torch.device('meta'):
            dense=gf1.Fusion(4096,gf1.normalize({}))
            routed=gf1.Fusion(4096,gf1.normalize(dict(layers=list(range(12,24)),top_k=2)))
        self.assertEqual(len(routed.projections),12)
        self.assertEqual(sum(p.numel() for p in dense.parameters()),gf1_memory.estimate(32,1)['parameter_assumptions']['connector'])
        self.assertLess(gf1_memory.estimate(32,1)['estimate_GiB'],48)
        self.assertLess(gf1_memory.estimate(32,2)['estimate_GiB'],80)

if __name__=='__main__':unittest.main()
