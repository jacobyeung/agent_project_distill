import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import torch

from student_pilot import carrier_c1_data as data, carrier_c1_run as run
from student_pilot.carrier_c1 import parameter_groups
from student_pilot.carrier_c1_sweep import capped_steps, dense_pose_row, recipe_for
from student_pilot.p3_provenance import file_pin, write
from tests.test_carrier_c1 import fixture, Tokenizer


class SweepTests(unittest.TestCase):
    def test_placement_masks_temporal_ids_and_answer_boundaries(self):
        for placement in data.PLACEMENTS:
            with self.subTest(placement=placement):
                model, batch, _ = fixture(4, placement=placement)
                positions = batch['aux_camera_positions'][0, :8]
                expected = list(range(12, 20)) if placement == data.C1_B else [3,4,8,9,13,14,18,19]
                self.assertEqual(positions.tolist(), expected)
                self.assertTrue((batch['labels'][0, positions] == -100).all())
                self.assertTrue((batch['attention_mask'][0, positions] == 1).all())
                self.assertEqual(int((batch['labels'] != -100).sum()), 2)
                mask = data.standard_attention_mask(batch, placement == data.C1_C)[0, 0]
                end = int(batch['aux_video_prefix_end'][0])
                self.assertEqual(bool(mask[0, end]), placement == data.C1_C)
                self.assertFalse(bool(mask[end, end+1]))
                self.assertFalse(bool(mask[end+1, end+2]))
                self.assertTrue(bool(mask[end+1, end]))
                native, _ = model.model.get_rope_index(batch['input_ids'], batch['mm_token_type_ids'],
                    video_grid_thw=batch['video_grid_thw'], attention_mask=batch['attention_mask'])
                changed = data.frame_position_ids(native, batch)
                keep = torch.ones(native.shape[-1], dtype=torch.bool)
                keep[positions] = False
                torch.testing.assert_close(changed[:,:,keep], native[:,:,keep], rtol=0, atol=0)
                torch.testing.assert_close(changed[:,0,positions], native[:,0,batch['aux_camera_rope_sources'][0,:8]])
                if placement == data.C1_B:
                    self.assertEqual(tuple(model.auxiliary_heads.frame_embeddings.weight.shape), (32,32))
                with self.assertRaisesRegex(ValueError,'Batch carrier_placement'):
                    model.hidden({**batch,'aux_carrier_placement':torch.tensor([(data.PLACEMENTS.index(placement)+1)%3])})

    def test_b_frame_grid_coordinates_preserve_padding_text_axis_and_pair_identity(self):
        model, _, _ = fixture(4, placement=data.C1_B, training_mode='pose_only', depth_enabled=False)
        embedding = model.auxiliary_heads.frame_embeddings.weight.detach()
        self.assertGreater(float(embedding.std()), 9e-5)
        self.assertLess(float(embedding.std()), 1.1e-4)
        self.assertTrue((embedding[::2] != embedding[1::2]).any(-1).all())
        ids = torch.tensor([[2,62,61,61,61,61,63,62,61,61,61,61,63,10,11,0,0]])
        batch = data.insert_frame_carriers(dict(input_ids=ids, attention_mask=(ids != 0).long(),
            mm_token_type_ids=torch.where(ids == 61,2,0), video_grid_thw=torch.tensor([[2,4,4]])),
            Tokenizer(), carrier_placement=data.C1_B)
        native,_ = model.model.get_rope_index(batch['input_ids'],batch['mm_token_type_ids'],
            video_grid_thw=batch['video_grid_thw'],attention_mask=batch['attention_mask'])
        saved = native.clone()
        text = torch.arange(native.shape[-1])[None,None,:]
        four = torch.cat((text,native),dim=0)
        fixed = data.frame_position_ids(four,batch)
        slots = batch['aux_camera_positions'][0,:4]
        refs = batch['aux_camera_rope_sources'][0,:4]
        torch.testing.assert_close(fixed[0],text[0],rtol=0,atol=0)
        torch.testing.assert_close(fixed[1:,0,slots],native[:,0,refs],rtol=0,atol=0)
        torch.testing.assert_close(fixed[1:],data.frame_position_ids(native,batch),rtol=0,atol=0)
        torch.testing.assert_close(native,saved,rtol=0,atol=0)
        torch.testing.assert_close(fixed[:,:,-2:],four[:,:,-2:],rtol=0,atol=0)
        self.assertTrue(torch.equal(fixed[1:,0,slots[0]],fixed[1:,0,slots[1]]))

    def test_padding_and_native_visual_grid_are_preserved(self):
        ids = torch.tensor([[2,62,61,61,61,61,63,62,61,61,61,61,63,10,11,0,0]])
        batch = dict(input_ids=ids, attention_mask=(ids != 0).long(), labels=torch.full_like(ids,-100),
                     mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([[2,4,4]]))
        batch['labels'][0,14] = 11
        for placement in data.PLACEMENTS:
            result = data.insert_frame_carriers(batch,Tokenizer(),carrier_placement=placement)
            self.assertEqual(int((result['input_ids'] == 61).sum()), 8)
            self.assertEqual(result['attention_mask'][0,-2:].tolist(), [0,0])
            mask = data.standard_attention_mask(result, placement == data.C1_C)
            self.assertFalse(mask[..., -2:].any())
        ids=torch.tensor([[2,62,61]])
        bare=dict(input_ids=ids,attention_mask=torch.ones_like(ids),video_grid_thw=torch.tensor([[1,2,2]]))
        for placement in data.PLACEMENTS:
            result=data.insert_frame_carriers(bare,Tokenizer(),carrier_placement=placement)
            self.assertEqual(int((result['input_ids']==5).sum()),2)

    def test_native_c_only_full_attention_is_bidirectional_and_checkpoint_gradients_match(self):
        model,batch,target = fixture(4,placement=data.C1_C)
        full, linear = [], []
        layers = model.model.language_model.layers
        a = layers[1].self_attn.register_forward_pre_hook(
            lambda m,a,k: full.append(k['attention_mask'].detach().clone()),with_kwargs=True)
        b = layers[0].linear_attn.register_forward_pre_hook(
            lambda m,a,k: linear.append(k['attention_mask']),with_kwargs=True)
        result = model(batch,target)
        result['loss'].backward()
        a.remove(); b.remove()
        end = int(batch['aux_video_prefix_end'][0])
        self.assertTrue(all(bool(mask[0,0,0,end]) for mask in full))
        self.assertTrue(all(mask is None or mask.ndim == 2 for mask in linear))
        expected = {n:p.grad.clone() for n,p in model.named_parameters() if p.grad is not None}
        model.zero_grad(set_to_none=True)
        model.model.language_model.gradient_checkpointing_disable()
        model(batch,target)['loss'].backward()
        for name,p in model.named_parameters():
            if name in expected:
                torch.testing.assert_close(p.grad,expected[name],atol=2e-6,rtol=2e-5)

    def test_all_placements_question_independence_future_frame_access_and_generation(self):
        for placement in data.PLACEMENTS:
            with self.subTest(placement=placement):
                model,batch,target=fixture(4,placement=placement)
                model.eval()
                with torch.no_grad():
                    first=model(batch,target,return_states=True)['states']
                    changed={**batch,'input_ids':batch['input_ids'].clone()}
                    changed['input_ids'][0,-4:]=torch.tensor([20,21,22,23])
                    torch.testing.assert_close(first,model(changed,target,return_states=True)['states'],rtol=0,atol=0)
                    changed={**batch,'pixel_values_videos':batch['pixel_values_videos'].clone()}
                    changed['pixel_values_videos'][-4:]*=-4
                    last=model(changed,target,return_states=True)['states']
                    if placement == data.C1_A:
                        torch.testing.assert_close(first[:,0],last[:,0],rtol=0,atol=0)
                    else:
                        self.assertFalse(torch.equal(first[:,0],last[:,0]))
                before=len(model.model.language_model._forward_pre_hooks)
                output=model.generate(batch,max_new_tokens=2,do_sample=False,pad_token_id=0,eos_token_id=1)
                self.assertGreater(output.shape[1],batch['input_ids'].shape[1])
                self.assertEqual(len(model.model.language_model._forward_pre_hooks),before)

    def test_pose_only_batch_schedule_and_lm_gradients(self):
        cfg=dict(training_mode='pose_only',depth_enabled=False,schedule=dict(startup_seconds=300,
            p95_step_seconds=30,checkpoint_seconds=120,export_seconds=180))
        recipe=recipe_for(cfg)
        self.assertEqual(recipe['steps'],800)
        self.assertEqual(recipe['milestones'],[100,200,400,800])
        self.assertEqual(capped_steps(cfg['schedule']),399)
        self.assertEqual(recipe['mix'],['pose']*4)
        self.assertEqual(recipe['weights']['depth'],0)
        plans=list(data.mixed_indices({'pose':37},6,training_mode='pose_only'))
        self.assertEqual(plans[3:],list(data.mixed_indices({'pose':37},6,start_step=3,training_mode='pose_only')))
        self.assertTrue(all([s for s,_ in plan]==['pose']*4 for plan in plans))
        with self.assertRaises(ValueError):
            list(data.mixed_indices(dict(pose=4,vqa=4,pointing=4),1,training_mode='pose_only'))
        with self.assertRaises(ValueError):
            capped_steps({**cfg['schedule'],'p95_step_seconds':float('nan')})
        model,batch,target=fixture(training_mode='pose_only',depth_enabled=False)
        self.assertFalse(hasattr(model.auxiliary_heads,'depth'))
        self.assertEqual(model.auxiliary_heads.pose.settings['weight_gravity'],0.)
        self.assertEqual(model.auxiliary_heads.pose.settings['weight_scale'],0.)
        loss=model(batch,target)
        loss['loss'].backward()
        self.assertGreater(sum(float(p.grad.abs().sum()) for p in model.model.language_model.parameters() if p.grad is not None),0)
        self.assertEqual(float(model.lm_head.weight.grad.abs().sum()),0.)
        for stream in ('vqa','pointing','routing'):
            with self.assertRaises(ValueError):
                model(batch,target,stream=stream)

    def test_pose_only_native_encoding_masks_every_lm_label(self):
        from types import SimpleNamespace
        model,batch,target=fixture()
        keep=batch['input_ids'][0] != 5
        raw={k:(v[:,keep] if k in ('input_ids','labels','attention_mask','mm_token_type_ids') else v)
             for k,v in batch.items() if not k.startswith('aux_')}
        processor=SimpleNamespace(tokenizer=Tokenizer(),video_processor=SimpleNamespace(merge_size=2))
        with patch('student_pilot.pose_samples.encode_row',return_value=(raw,{})), \
             patch.object(data,'target_tensors',return_value=target):
            encoded,_,_=data.encode(processor,{}, {},'pose',data.C1_B,'pose_only')
            self.assertTrue((encoded['labels'] == -100).all())
            with self.assertRaises(ValueError):
                data.encode(processor,{}, {},'vqa',data.C1_B,'pose_only')

    def test_dense_selector_and_config_identity(self):
        row=dict(category='camera_pose_only',student_input={'frames':[{}]*32},
                 pose_sample={'recording':{'sampling':{'variant':'all_frames32'}}})
        target=dict(camera=[[0,0,0,0,0,0,1,1,1]]*32,camera_mask=[True]*32)
        self.assertTrue(dense_pose_row(row,target))
        self.assertFalse(dense_pose_row(row,{**target,'camera_mask':[True,False]*16}))
        self.assertFalse(dense_pose_row({**row,'pose_sample':{}},target))
        cfg=dict(schema='carrier-c1-run-v1',training_mode='pose_only',depth_enabled=False,init='base',
            parallel='fsdp',all_frames=True,streams={'pose':{}},carrier_placement=data.C1_A,
            schedule=dict(startup_seconds=300,p95_step_seconds=30,checkpoint_seconds=120,export_seconds=180))
        cfg['recipe']=recipe_for(cfg)
        run.validate(cfg)
        for placement in (data.C1_B,data.C1_C):
            self.assertNotEqual(run.identity(cfg),run.identity({**cfg,'carrier_placement':placement}))
        for change in ({'streams':dict(pose={},vqa={})},{'init':'warm_start'},{'carrier_placement':'unknown'}):
            with self.assertRaises(ValueError):
                run.validate({**cfg,**change})

    def test_pose_only_index_reads_dense_rows_and_budget_stop_saves_for_resume(self):
        root=Path(tempfile.mkdtemp(prefix='sweep_',dir=os.environ['LANE_TEST_OUTPUT']))
        row=dict(category='camera_pose_only',student_input={'frames':[{}]*32},
                 pose_sample={'recording':{'sampling':{'variant':'all_frames32'}}})
        target=dict(camera=[[0,0,0,0,0,0,1,1,1]]*32,camera_mask=[True]*32)
        with sqlite3.connect(root/'rows.sqlite') as conn:
            conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            conn.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps({**row,'pose_sample':{}}),json.dumps(target)))
            conn.execute('INSERT INTO rows VALUES(1,?,?)',(json.dumps(row),json.dumps(target)))
        write(root/'indices.json',[1])
        receipt=dict(carrier_placement=data.C1_C,training_mode='pose_only',streams={'pose':dict(
            database=file_pin(root/'rows.sqlite'),indices=file_pin(root/'indices.json'),count=1)})
        rows=run.Rows(receipt,None)
        try:
            with patch.object(data,'encode',return_value=('batch', 'targets', {'qid': 'fixture'})) as encoder:
                self.assertEqual(rows.get('pose',0),('batch', 'targets', {'qid': 'fixture'}))
                self.assertEqual(encoder.call_args.args[-2:],(data.C1_C,'pose_only'))
                self.assertEqual(encoder.call_args.args[1],row)
        finally:
            rows.close()
        cfg=dict(training_mode='pose_only',depth_enabled=False,
                 schedule=dict(startup_seconds=13200,p95_step_seconds=100,checkpoint_seconds=20,export_seconds=20))
        recipe=recipe_for(cfg)
        self.assertEqual(recipe['steps'],800)
        self.assertEqual(capped_steps(cfg['schedule']),2)
        model,batch,target=fixture(training_mode='pose_only',depth_enabled=False)
        model.recipe=recipe
        class DenseRows:
            def get(self,stream,index):
                if stream != 'pose': raise AssertionError(stream)
                return batch,target,{}
        optimizer=torch.optim.AdamW(parameter_groups(model))
        with patch.object(run,'checkpoint') as save,patch.object(run,'export') as export:
            report=run.run_steps(model,model,optimizer,DenseRows(),{'pose':1},root,cfg,{},
                                 torch.device('cpu'),distributed=False)
        self.assertEqual(report['last_step'],2)
        self.assertTrue(report['stopped_for_resume'])
        self.assertEqual(report['stop_reason'],'budget_or_signal')
        export.assert_not_called()
        self.assertEqual(save.call_args.args[-1],2)

    def test_all_placement_exports_reload_and_cross_placement_is_refused(self):
        root=Path(tempfile.mkdtemp(prefix='export_',dir=os.environ['LANE_TEST_OUTPUT']))
        for placement in data.PLACEMENTS:
            model,batch,target=fixture(4,placement=placement,training_mode='pose_only',depth_enabled=False)
            destination=root/str(data.PLACEMENTS.index(placement))
            with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1), \
                 patch.object(run.dist,'barrier'), \
                 patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
                run.export(destination,model,model,{'base_identity':'fixture','trace_program_version':'3.13'},2)
            pin=file_pin(destination/'artifact.json')
            fresh,_,_=fixture(4,placement=placement,training_mode='pose_only',depth_enabled=False)
            run.load_artifact(fresh,pin)
            self.assertTrue(fresh.eval().probe(batch,target)['finite'])
            if placement == data.C1_B:
                from student_pilot.p3_provenance import load
                stale = load(pin['path'])
                self.assertEqual(stale['carrier_position_policy'],'frame_grid_anchor_v2')
                stale.pop('carrier_position_policy')
                write(destination/'old_position_policy.json',stale)
                with self.assertRaisesRegex(ValueError,'position policy'):
                    run.load_artifact(fresh,file_pin(destination/'old_position_policy.json'))
            other,_,_=fixture(4,placement=data.PLACEMENTS[(data.PLACEMENTS.index(placement)+1)%3],
                                training_mode='pose_only',depth_enabled=False)
            with self.assertRaisesRegex(ValueError,'placement'):
                run.load_artifact(other,pin)

    def test_b_runtime_temporal_ids_embedding_gradients_and_generation_prefill(self):
        model,batch,target=fixture(placement=data.C1_B,training_mode='pose_only',depth_enabled=False)
        model.eval()
        native,_=model.model.get_rope_index(batch['input_ids'],batch['mm_token_type_ids'],
            video_grid_thw=batch['video_grid_thw'],attention_mask=batch['attention_mask'])
        expected=data.frame_position_ids(native,batch)
        positions=[];norms=[]
        rope=model.model.language_model.rotary_emb.register_forward_pre_hook(lambda m,a: positions.append(a[1].clone()))
        norm=model.model.language_model.norm.register_forward_hook(lambda m,a,o: norms.append(o.detach().clone()))
        try:
            model(batch,target)['loss'].backward()
            gradient=model.auxiliary_heads.frame_embeddings.weight.grad
            self.assertTrue((gradient.norm(dim=1)>0).all())
            torch.testing.assert_close(positions[0],expected,rtol=0,atol=0)
            forward=norms[0]
            norms.clear();positions.clear()
            model.generate(batch,max_new_tokens=2,do_sample=False,pad_token_id=0,eos_token_id=1)
            torch.testing.assert_close(positions[0],expected,rtol=0,atol=0)
            torch.testing.assert_close(norms[0],forward,rtol=0,atol=0)
        finally:
            rope.remove();norm.remove()

    def test_pose_only_resume_reproduces_next_update_for_every_placement(self):
        root=Path(tempfile.mkdtemp(prefix='resume_',dir=os.environ['LANE_TEST_OUTPUT']))
        for number,placement in enumerate(data.PLACEMENTS):
            with self.subTest(placement=placement):
                model,batch,target=fixture(4,placement=placement,training_mode='pose_only',depth_enabled=False)
                class Rows:
                    def get(self,stream,index): return batch,target,{}
                optimizer=torch.optim.AdamW(parameter_groups(model))
                plans=list(data.mixed_indices({'pose':9},2,training_mode='pose_only'))
                bound={'placement':placement,'training_mode':'pose_only'}
                run.optimize_step(model,optimizer,Rows(),plans[0],0,torch.device('cpu'),1)
                def gather(out,value,*args,**kwargs): out[0]=value
                with patch.object(run.dist,'get_rank',return_value=0),patch.object(run.dist,'get_world_size',return_value=1), \
                     patch.object(run.dist,'barrier'),patch.object(run.dist,'all_gather_object',side_effect=gather), \
                     patch.object(run.dist,'broadcast'),patch.object(run.dist,'broadcast_object_list'), \
                     patch.object(run.dist,'get_backend',return_value='gloo'):
                    pin=run.checkpoint(root/str(number),model,optimizer,bound,1)
                    run.optimize_step(model,optimizer,Rows(),plans[1],0,torch.device('cpu'),2)
                    expected={n:p.detach().clone() for n,p in model.named_parameters()}
                    self.assertEqual(run.restore(pin,model,optimizer,bound),1)
                    run.optimize_step(model,optimizer,Rows(),plans[1],0,torch.device('cpu'),2)
                for name,p in model.named_parameters():
                    torch.testing.assert_close(p,expected[name],rtol=0,atol=0)


if __name__ == '__main__':
    unittest.main()
