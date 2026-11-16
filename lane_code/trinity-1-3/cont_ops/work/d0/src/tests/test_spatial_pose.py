"""Spatial observability, native gradient/export paths, and CPU comparison contract."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import unittest
import uuid
from unittest.mock import patch

import torch

from student_pilot.camera_config import normalize
from student_pilot.camera_head import CameraSupervision
from student_pilot.decoupled_v_run import FIXED_CAMERA, SPATIAL_CAMERA, identity, validate
from student_pilot.decoupled_vc import VC_BATCH4H_RECIPE
from student_pilot.pose_overfit import fit_variant, selected_indices
from student_pilot.spatial_pose import TOKEN_BUDGET, pool_grid, positions_2d
from tests.test_decoupled_pose_fix import settings


def shifted_fixture():
    """One fixed content vector moves horizontally. No yaw or row ID in channels."""
    content = torch.randn(64, generator=torch.Generator().manual_seed(39)) * 8
    grids, targets = [], []
    for origin in (0, 3):
        columns = torch.roll(torch.arange(8).repeat(2), -origin)
        grid = torch.zeros(16, 2, 8, 64)
        grid[torch.arange(16), :, columns] = content
        # Camera-from-origin yaw: the image shifts right as camera yaw decreases.
        yaw = (columns.float() - columns[0]) * .25
        target = torch.zeros(16, 9)
        target[:, 4], target[:, 6] = (yaw / 2).sin(), (yaw / 2).cos()
        target[:, 7:] = 1.
        grids.append(grid); targets.append(target)
    return torch.stack([g.mean((1, 2)) for g in grids]), grids, torch.stack(targets), torch.ones(2, 16, dtype=torch.bool)


class SpatialTests(unittest.TestCase):
    def test_identity_schema_and_legacy_keys(self):
        from tests.test_decoupled_schedule import config
        cfg = config(); validate(cfg)
        fixed = {**cfg, 'camera_overrides': FIXED_CAMERA}
        spatial = {**cfg, 'camera_overrides': SPATIAL_CAMERA}
        validate(fixed); validate(spatial)
        self.assertNotEqual(identity(fixed), identity(spatial))
        for bad in ({'pose_input':'spatial_tokens_v1'}, {**SPATIAL_CAMERA, 'other':1}):
            with self.assertRaises(ValueError): validate({**cfg, 'camera_overrides':bad})
        with self.assertRaises(ValueError): normalize(settings(pose_input='spatial_tokens_v1'))
        with self.assertRaises(ValueError): normalize(settings(**FIXED_CAMERA, pose_input='unknown'))
        old = CameraSupervision(64, settings(**FIXED_CAMERA))
        restored = CameraSupervision(64, settings(**FIXED_CAMERA))
        restored.load_state_dict(old.state_dict(), strict=True)
        self.assertFalse(any('spatial_pose' in k for k in old.state_dict()))
        with self.assertRaises(ValueError): CameraSupervision(64, settings(**SPATIAL_CAMERA)).predict(torch.randn(1,16,64))

    def test_budget_positions_origin_and_mask(self):
        for height, width in ((24,32),(32,24),(1,1024),(7,7),(2,3)):
            pooled = pool_grid(torch.randn(4,height,width,16))
            h,w = pooled.shape[1:3]
            self.assertLessEqual(h*w,TOKEN_BUDGET)
            self.assertLessEqual(h,height); self.assertLessEqual(w,width)
            if height < width: self.assertLessEqual(h,w)
        pos = positions_2d(2,8,64,'cpu')
        self.assertEqual(len(pos.unique(dim=0)), 16)
        torch.manual_seed(31)
        head = CameraSupervision(64,settings(**SPATIAL_CAMERA))
        states, grids, _, _ = shifted_fixture()
        keep = torch.tensor([0]+list(range(15,0,-1)))
        moved = torch.roll(torch.arange(16),-3)
        a = head.predict(states,spatial_grids=grids)[-1]
        b = head.predict(states[:,keep],spatial_grids=[g[keep] for g in grids])[-1]
        torch.testing.assert_close(b,a[:,keep],atol=1e-5,rtol=1e-4)
        c = head.predict(states[:,moved],spatial_grids=[g[moved] for g in grids])[-1]
        self.assertGreater(float((c-a[:,moved]).abs().max().detach()),1e-4)
        key = torch.tensor([[True]*4+[False]*12])
        small = head.predict_all(states[:1],key_mask=key,spatial_grids=[grids[0][:4]])[0][-1]
        extended = torch.cat((grids[0][:4],torch.randn_like(grids[0][4:])*100),0)
        padded = head.predict_all(states[:1],key_mask=key,spatial_grids=[extended])[0][-1]
        torch.testing.assert_close(small[:,:4],padded[:,:4],atol=1e-5,rtol=1e-4)

    def test_shifted_content_pooled_fails_spatial_learns(self):
        old_threads = torch.get_num_threads(); torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads,old_threads)
        states, grids, targets, masks = shifted_fixture()
        torch.testing.assert_close(states,states[:1,:1].expand_as(states),rtol=0,atol=0)
        # Controlled observability test uses a faster LR; the real-row comparison
        # below uses the unchanged production schedule and 200 steps.
        recipe = {**VC_BATCH4H_RECIPE,'learning_rate':1e-3}
        results = {}
        for name, extra in (('pooled',FIXED_CAMERA),('spatial',SPATIAL_CAMERA)):
            results[name] = fit_variant(settings(**extra),states,grids,targets,masks,recipe,width=64)
        report = {k:{f:v[f] for f in ('initial','final','seconds')} for k,v in results.items()}
        print(json.dumps({'shifted_content':report}))
        Path(os.environ['LANE_TEST_OUTPUT']).parent.joinpath('shifted.json').write_text(json.dumps(report,indent=2)+'\n')
        self.assertGreater(results['pooled']['final']['median_deg'],25.)
        self.assertLess(results['spatial']['final']['median_deg'],10.)
        self.assertLess(results['spatial']['final']['mean_deg'],results['pooled']['final']['mean_deg']*.3)

    def test_native_vc_gradient_export_readout_short_and_geometry(self):
        from tests.test_decoupled_v import DecoupledTests
        from student_pilot.decoupled_v import target_tensors, export_heads, load_heads, readout, features
        from student_pilot.decoupled_vc import VisionCopy
        from student_pilot.next_gpu_check import check
        DecoupledTests.setUpClass()
        base,_,batch = DecoupledTests().pair()
        cfg = copy.deepcopy(base.config); cfg.p3['camera'].update(SPATIAL_CAMERA)
        model = VisionCopy(cfg,base.model.visual).train()
        # Pose-only gradient proves the encoder path, independent of depth loss.
        capture = features(model,batch)
        spatial = [row[-1] for row in capture.vits]
        capture.vits[0][-1].retain_grad()
        pose = model.auxiliary_heads.camera.predict(capture.states,spatial_grids=spatial)[-1]
        pose[...,3:7].square().mean().backward()
        self.assertGreater(float(capture.vits[0][-1].grad.norm()),0)
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in model.model.visual.parameters()))
        model.zero_grad(set_to_none=True)
        target = dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*16,camera_mask=[True]*4+[False]*12,
            trajectory_scale=1.,gravity=[0.,-1.,0.],gravity_mask=True,
            point_depth=dict(uv=[[[500.,500.]]]*16,depth=[[2.]]*16,mask=[[True]]*4+[[False]]*12))
        short = {**batch,'video_grid_thw':torch.tensor([[4,4,4]]),'pixel_values_videos':batch['pixel_values_videos'][:64]}
        model(short,target_tensors(target)).mean().backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.auxiliary_heads.parameters()))
        probe = check(model,short,target_tensors(target))
        self.assertEqual(probe['settings'],SPATIAL_CAMERA)
        out = Path(os.environ['LANE_TEST_OUTPUT'])/uuid.uuid4().hex
        artifact = export_heads(model,out,1,{'synthetic':True})
        restored = VisionCopy(copy.deepcopy(cfg),base.model.visual)
        load_heads(restored,artifact)
        self.assertEqual(restored.config.p3['camera']['pose_input'],'spatial_tokens_v1')
        actual=readout(model,batch,[[[500.,500.]]]*16)
        self.assertEqual(actual,readout(restored,batch,[[[500.,500.]]]*16))
        self.assertEqual(actual['pose_input'],'spatial_tokens_v1')
        # Geometry uses and records the same spatial dispatch.
        with patch.object(restored.auxiliary_heads.camera,'predict_all',wraps=restored.auxiliary_heads.camera.predict_all) as call:
            self.assertEqual(features(restored,batch).geometry().pose_input,'spatial_tokens_v1')
            self.assertIsNotNone(call.call_args.kwargs['spatial_grids'])

    def test_real_row_runner_caches_once_and_reports_both_variants(self):
        self.check_real_row_runner()

    def test_all_frame_real_row_runner_caches_fused_grids(self):
        self.check_real_row_runner(all_frames=True)

    def check_real_row_runner(self, all_frames=False):
        from tests.test_decoupled_startup import StartupTests
        from student_pilot import pose_overfit as overfit
        from student_pilot.p3_provenance import load
        StartupTests.setUpClass(); fixture=StartupTests()
        out,cfg,_,_ = fixture.fixture('decoupled_vc',fixed=True,all_frames=all_frames)
        cfg['camera_overrides']=SPATIAL_CAMERA
        receipt=load(cfg['preparation']['path'])
        receipt['settings']['camera'].update(SPATIAL_CAMERA); receipt['count']=32
        with sqlite3.connect(receipt['database']['path']) as db:
            row,target = db.execute('SELECT row,target FROM rows WHERE i=0').fetchone()
            for i in range(9,32): db.execute('INSERT INTO rows VALUES (?,?,?)',(i,row,target))
        manifest=load(receipt['model']['path'])
        original=overfit.fit_variant
        def fast(*args): return original(*args,steps=2,width=32)
        with patch('student_pilot.decoupled_v_run.prepared',return_value=(receipt,manifest)), \
             patch('student_pilot.decoupled_v_run.processor_for',return_value=fixture.processor), \
             patch('student_pilot.batches.training_stop_token',side_effect=fixture.tiny_stop), \
             patch.object(overfit,'fit_variant',side_effect=fast), \
             patch.object(overfit,'features',wraps=overfit.features) as forward:
            report=overfit.real_row_overfit(cfg,out/'overfit.json')
        self.assertEqual(forward.call_count,32)
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['indices'],selected_indices(32))
        self.assertEqual(set(report['variants']),{'pooled','spatial_tokens_v1'})
        for variant in report['variants'].values():
            for stage in ('initial','final'):
                self.assertTrue({'mean_deg','median_deg','count'} <= variant[stage].keys())
                self.assertEqual(variant[stage]['count'], 32*(32 if all_frames else 16))
        self.assertTrue(all(r['pooled_shape'][0] == 16 for r in report['row_bindings']))
        with self.assertRaises(ValueError): selected_indices(31)
        with self.assertRaises(ValueError): overfit.real_row_overfit(cfg,out/'overfit.json')

    def test_all_frame_spatial_dispatch_gradients_reload_and_short_rows(self):
        from tests.test_decoupled_v import DecoupledTests
        from tests.test_all_frames import target
        from student_pilot.decoupled_v import features, target_tensors, export_heads, load_heads, readout
        from student_pilot.decoupled_vc import VisionCopy
        from student_pilot.next_gpu_check import check
        DecoupledTests.setUpClass()
        base, _, batch = DecoupledTests().pair()
        cfg = copy.deepcopy(base.config)
        cfg.p3.update(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames')
        cfg.p3['camera'].update(SPATIAL_CAMERA)
        model = VisionCopy(cfg, base.model.visual).train()
        with torch.no_grad():
            model.auxiliary_heads.frame_queries.normal_(std=.05)
        capture = features(model, batch)
        camera = model.auxiliary_heads.camera
        inputs = capture.pose_inputs()
        self.assertEqual(inputs['spatial_grids'][0].shape[0], 16)
        self.assertEqual(inputs['frame_queries'].shape[0], 32)
        prediction = camera.predict(capture.states, **inputs)[-1]
        # Pooled feature values cannot leak into spatial predictions.
        changed = camera.predict(torch.randn_like(capture.states)*100, **inputs)[-1]
        torch.testing.assert_close(prediction, changed, rtol=0, atol=0)
        seen = []
        hook = camera.projector.register_forward_pre_hook(lambda m, a: seen.append(a[0]))
        camera.predict(capture.states, **inputs)
        hook.remove()
        tokens = camera.spatial_pose(inputs['spatial_grids'], 16).repeat_interleave(2, 1)
        tokens = tokens + model.auxiliary_heads.frame_queries[None]
        torch.testing.assert_close(seen[0], torch.cat((tokens, tokens[:, :1].expand_as(tokens)), -1))
        prediction[..., 3:7].square().mean().backward()
        self.assertGreater(float(model.auxiliary_heads.frame_queries.grad.norm()), 0.)
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in model.model.visual.parameters()))
        model.zero_grad(set_to_none=True)
        short = {**batch, 'video_grid_thw':torch.tensor([[4,4,4]]),
                 'pixel_values_videos':batch['pixel_values_videos'][:64]}
        record = target(16)
        record['camera_mask'][4:] = [False]*12
        record['point_depth']['mask'][4:] = [[False, False]]*12
        targets = target_tensors(record, all_frames=True)
        model(short, targets).mean().backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.auxiliary_heads.parameters()))
        self.assertGreater(float(model.auxiliary_heads.frame_queries.grad[:8].norm()), 0.)
        self.assertEqual(float(model.auxiliary_heads.frame_queries.grad[8:].norm()), 0.)
        self.assertEqual(check(model, short, targets)['settings'], SPATIAL_CAMERA)
        artifact = export_heads(model, Path(os.environ['LANE_TEST_OUTPUT'])/uuid.uuid4().hex, 1, {'synthetic':True})
        restored = VisionCopy(copy.deepcopy(cfg), base.model.visual)
        load_heads(restored, artifact)
        for slots in (16, 32):
            uv = [[[500., 500.]]]*slots
            actual = readout(model, batch, uv)
            self.assertEqual(actual, readout(restored, batch, uv))
            self.assertEqual(actual['pose_input'], 'spatial_tokens_v1')
            self.assertEqual(len(actual['raw_pose']), 32)
            self.assertEqual(len(actual['point_depth']), slots)
        self.assertEqual(features(restored, batch).geometry().pose_input, 'spatial_tokens_v1')

    def test_all_frame_real_row_fit_uses_queries(self):
        from tests.test_decoupled_overfit import pose_fixture
        states, targets, masks = pose_fixture(all_frames=True)
        grids = [row[:, None, None, :].expand(-1, 2, 2, -1) for row in states[:2]]
        for extra in (FIXED_CAMERA, SPATIAL_CAMERA):
            result = fit_variant(settings(**extra), states[:2].repeat_interleave(2, 1),
                                 grids, targets[:2], masks[:2], VC_BATCH4H_RECIPE, steps=2, width=32)
            self.assertEqual(result['final']['count'], 64)

    def test_real_row_runner_skips_short_rows(self):
        from tests.test_decoupled_startup import StartupTests
        from student_pilot import pose_overfit as overfit
        from student_pilot.p3_provenance import load
        StartupTests.setUpClass(); fixture=StartupTests()
        out,cfg,_,_ = fixture.fixture('decoupled_vc',fixed=True)
        cfg['camera_overrides']=SPATIAL_CAMERA
        receipt=load(cfg['preparation']['path'])
        receipt['settings']['camera'].update(SPATIAL_CAMERA); receipt['count']=40
        with sqlite3.connect(receipt['database']['path']) as db:
            row,target = db.execute('SELECT row,target FROM rows WHERE i=0').fetchone()
            for i in range(9,32): db.execute('INSERT INTO rows VALUES (?,?,?)',(i,row,target))
            short=json.loads(row); short['student_input']['frames']=short['student_input']['frames'][:8]
            for i in range(32,40): db.execute('INSERT INTO rows VALUES (?,?,?)',(i,json.dumps(short),target))
        manifest=load(receipt['model']['path'])
        original=overfit.fit_variant
        def fast(*args): return original(*args,steps=2,width=32)
        with patch('student_pilot.decoupled_v_run.prepared',return_value=(receipt,manifest)), \
             patch('student_pilot.decoupled_v_run.processor_for',return_value=fixture.processor), \
             patch('student_pilot.batches.training_stop_token',side_effect=fixture.tiny_stop), \
             patch.object(overfit,'fit_variant',side_effect=fast):
            report=overfit.real_row_overfit(cfg,out/'overfit.json')
        order=selected_indices(40)
        self.assertEqual(report['indices'],[i for i in order if i<32])
        self.assertEqual(report['skipped_rows'],sum(i>=32 for i in order[:order.index(report['indices'][-1])]))
        self.assertEqual(report['status'],'PASS')


if __name__ == '__main__':
    unittest.main()
