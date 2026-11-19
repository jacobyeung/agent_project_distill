"""A1 native-consumer parity, supervision, builder, bank and readout regressions."""
import copy
import json
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import all_frame_bank as bank32, all_frame_readout as scoring
from student_pilot.camera_targets import encode_cameras, encode_gravity, trajectory_scale
from student_pilot.decoupled_v import VisionOnly, features, target_tensors, export_heads, head_settings, readout, load_heads
from student_pilot.decoupled_vc import VisionCopy
from student_pilot.compact_label_bank import read_bank, load_bank_for_rows
from student_pilot.camera_config import CAMBRIAN_P_ROUTING
from student_pilot import recording_pose as rp
from tests import test_decoupled_v as legacy
from tests.test_recording_pose import directory, fixture, save, staged_fixture

ROOT = Path(os.environ['B9_TEST_OUTPUT'])


def target(slots=32):
    return dict(camera=[[0., 0., 0., 0., 0., 0., 1., 1., 1.]]*slots,
                camera_mask=[True]*slots, trajectory_scale=1., gravity=[0., -1., 0.], gravity_mask=True,
                point_depth=dict(uv=[[[200., 300.], [500., 500.]]]*slots,
                                 depth=[[2., 3.]]*slots, mask=[[True, True]]*slots))


class AllFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy.DecoupledTests.setUpClass()

    def pair(self, private):
        model, frozen, batch = legacy.DecoupledTests().pair()
        from p3_consumer.p3_heads import P3Heads
        model.config.p3.update(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames',
                               feature_backing='decoupled_v')
        model.auxiliary_heads = P3Heads(model.config).float()
        state = frozen.auxiliary_heads.state_dict()
        state['camera.point_depth.group_embed'] = state['camera.point_depth.group_embed'].repeat_interleave(2, 0)
        state['frame_queries'] = model.auxiliary_heads.frame_queries.detach().clone()
        model.auxiliary_heads.load_state_dict(state)
        # Nonzero, distinct queries detect missing/reordered/repeated query application.
        with torch.no_grad():
            model.auxiliary_heads.frame_queries.normal_(std=.05)
        model.config.p3['frozen_fingerprints'] = model.frozen_fingerprints()
        stage = (VisionCopy if private else VisionOnly)(copy.deepcopy(model.config), copy.deepcopy(model.model.visual))
        stage.auxiliary_heads.load_state_dict(model.auxiliary_heads.state_dict())
        return model.eval(), stage.eval(), batch

    def test_native_p3_parity_export_and_gradients_both_modes(self):
        for private in (False, True):
            with self.subTest(private=private):
                model, stage, batch = self.pair(private)
                with torch.no_grad(), legacy.DecoupledTests.capture(model, batch) as expected:
                    model(**batch, use_cache=False)
                    expected.finish()
                got = features(stage, batch)
                torch.testing.assert_close(got.states, expected.states, rtol=0, atol=0)
                for a, b in zip(got.vits[0], expected.vits[0]):
                    torch.testing.assert_close(a, b, rtol=0, atol=0)
                points = [[[200., 300.], [500., 500.]]]*16
                result = readout(stage, batch, points)
                self.assertEqual(len(result['raw_pose']), 32)
                self.assertEqual(len(readout(stage, batch, points*2)['point_depth']), 32)
                geometry = expected.geometry()
                self.assertEqual(result['point_depth'], [geometry.depth_fn(k, uv).tolist()
                                                         for k, uv in zip(range(2, 33, 2), points)])
                out = ROOT/uuid.uuid4().hex
                pin = export_heads(stage, out, 200, {'synthetic': True})
                if private:
                    _, reloaded, _ = self.pair(True)
                    load_heads(reloaded, pin)
                    self.assertEqual(readout(reloaded, batch, points), result)
                else:
                    model.load_heads(pin)
                before = {k: p.detach().clone() for k, p in model.model.visual.named_parameters()}
                stage.train()
                loss = stage(batch, target_tensors(target(), all_frames=True)).mean()
                self.assertTrue(torch.isfinite(loss))
                loss.backward()
                query = stage.auxiliary_heads.frame_queries
                self.assertIsNotNone(query.grad)
                self.assertGreater(float(query.grad.abs().sum()), 0.)
                self.assertTrue(torch.isfinite(query.grad).all())
                self.assertEqual(any(p.grad is not None for p in stage.model.visual.parameters()), private)
                for k, p in model.model.visual.named_parameters():
                    self.assertTrue(torch.equal(p, before[k]))
                optimizer = torch.optim.AdamW(stage.parameters(), lr=1e-3)
                previous = query.detach().clone()
                optimizer.step()
                self.assertFalse(torch.equal(previous, query))

    def test_legacy_expansion_and_short_rows(self):
        row = target(16)
        row['camera_mask'][4:] = [False]*12
        row['point_depth']['mask'][4:] = [[False, False]]*12
        old = target_tensors(row)
        new = target_tensors(row, all_frames=True)
        for k in ('aux_camera_target', 'aux_camera_mask', 'aux_point_depth_uv', 'aux_point_depth_gt', 'aux_point_depth_mask'):
            torch.testing.assert_close(new[k][:, 1::2], old[k], rtol=0, atol=0)
            self.assertEqual(int(torch.count_nonzero(new[k][:, ::2])), 0)
        full = target_tensors(target(), all_frames=True)
        self.assertEqual(full['aux_camera_target'].shape, (1, 32, 9))
        with self.assertRaises(ValueError): target_tensors(target())
        for private in (False, True):
            _, stage, batch = self.pair(private)
            short = {**batch, 'video_grid_thw': torch.tensor([[4,4,4]]),
                     'pixel_values_videos': batch['pixel_values_videos'][:64]}
            loss = stage.train()(short, new).mean()
            self.assertTrue(torch.isfinite(loss)); loss.backward()

    def test_encoder_matches_legacy_exactly(self):
        poses = np.repeat(np.eye(4)[None], 32, axis=0)
        poses[:, 0, 3] = np.arange(32)*.1
        k = np.repeat(np.diag([100., 100., 1.])[None], 32, axis=0)
        old, mask, scale = encode_cameras(poses, k, [100, 120])
        new, allmask, allscale = encode_cameras(poses, k, [100, 120], all_frames=True)
        np.testing.assert_array_equal(new[1::2], old)
        self.assertTrue(allmask.all())
        np.testing.assert_array_equal(new[0, :3], np.zeros(3))
        self.assertAlmostEqual(allscale, scale/2)

    def test_plan_build_fresh_rows_and_masked_depth(self):
        root = directory(); request = fixture(root)
        request.update(variant='all_frames32')
        plan = rp.make_plan(request)
        pin = save(root, 'plan.json', plan)
        _, staged = staged_fixture(root, plan, pin)
        audit = rp.build(plan, pin, [staged], root/'built')
        rows = [json.loads(line) for line in (root/'built/pose_rows.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 80)
        self.assertEqual(len({tuple(r['student_input']['frame_indices']) for r in rows}), 80)
        self.assertEqual(audit['N_histogram'], {'32': 80})
        self.assertEqual(len(rows[0]['pose_sample']['camera']), 32)
        self.assertEqual(len(plan['excluded']), 5)
        _, stage, _ = self.pair(True)
        cfg = {**stage.config.p3['camera'], 'row_routing': CAMBRIAN_P_ROUTING, 'max_groups': 32}
        cfg['point_depth'] = {**cfg['point_depth'], 'num_points_per_frame': 2}
        path = ROOT.parents[2]/'aws_run1/kit/in/689136d4.npz'
        records, _ = load_bank_for_rows(str(path), rows[:1], cfg)
        self.assertFalse(np.asarray(records[0]['point_depth']['mask']).any())
        self.assertEqual(target_tensors(records[0], all_frames=True)['aux_camera_target'].shape, (1,32,9))
        # Sparse posed ordinals support this variant without nearest-frame mapping.
        source = plan['scenes'][0]
        source.update(sparse_poses=True, frame_numbers=list(range(0,1000,2)), pose_count=500)
        source['pool'] = [v*2 for v in range(96)]
        rp.validate_plan(plan)

    def test_actual_row_encoder_and_dryrun_both_modes(self):
        import sqlite3
        from tests.test_decoupled_startup import StartupTests
        from student_pilot import decoupled_v_run as run, pose_samples
        from student_pilot.p3_provenance import load, write, file_pin
        for mode in ('decoupled_v', 'decoupled_vc'):
            helper = StartupTests()
            out, cfg, _, _ = helper.fixture(mode)
            cfg['all_frames'] = True
            # Exercise independent V-C preparation receipts too.
            cfg.pop('reuse_preparation', None)
            receipt = load(out/'receipt.json')
            receipt.pop('reused_from', None)
            receipt['settings'] = head_settings(receipt['settings']['camera'], 'fixture',
                receipt['settings']['feature_encoder_sha256'], all_frames=True)
            receipt['settings']['feature_backing'] = mode
            receipt['config_sha256'] = run.identity(cfg)
            poses = np.repeat(np.eye(4)[None], 32, axis=0)
            poses[:, 0, 3] = np.arange(32)*.1
            camera, mask, scale = encode_cameras(poses, np.repeat(np.diag([100.,100.,1.])[None],32,0),
                                                 [64,64], all_frames=True)
            conn = sqlite3.connect(out/'rows.sqlite')
            for i, raw, encoded in conn.execute('SELECT i,row,target FROM rows').fetchall():
                row, rec = json.loads(raw), json.loads(encoded)
                sample = dict(schema=pose_samples.SCHEMA, mode='collection', frames=32, positions=list(range(32)),
                    augment={**pose_samples.AUGMENT,'seed':17}, anchors=list(range(1,33)),
                    temporal_grouping='fused_pairs_all_frames', camera=camera.tolist(), camera_mask=mask.tolist(),
                    trajectory_scale=scale, gravity=[0.,0.,1.], gravity_mask=True, metric=True)
                row['pose_sample'] = sample
                rec.update({k:sample[k] for k in ('camera','camera_mask','trajectory_scale','gravity','gravity_mask')})
                conn.execute('UPDATE rows SET row=?,target=? WHERE i=?',(json.dumps(row),json.dumps(rec),i))
            conn.commit(); conn.close()
            receipt['database'] = file_pin(out/'rows.sqlite')
            write(out/'allframe_receipt.json',receipt)
            cfg['preparation'] = file_pin(out/'allframe_receipt.json')
            write(out/'allframe_admission.json',dict(verdict='PASS',config_sha256=run.identity(cfg),
                preparation=cfg['preparation'], reviewer='fixture'))
            cfg['admission'] = file_pin(out/'allframe_admission.json')
            with patch('transformers.AutoProcessor.from_pretrained',return_value=helper.processor), \
                 patch('student_pilot.batches.training_stop_token',side_effect=helper.tiny_stop), \
                 patch('student_pilot.pose_samples.augment',side_effect=lambda arrays, settings: arrays):
                report = run.dryrun(cfg,out/'allframe_dryrun.json')
            self.assertEqual(report['status'],'PASS')
            self.assertTrue(all(report['checks'].values()))
            self.assertEqual(len(report['ranks']),8)

    def test_even_metrics_match_head_acc_reference(self):
        import ast
        import math
        from collections import defaultdict
        path = Path('/scratch/jjyeung/orch_cd/head_acc/work/analyze.py')
        functions = {'qrot', 'ang', 'vang', 'dbar', 'decode', 'level', 'mra', 'stats', 'pose_eval'}
        tree = ast.parse(path.read_text())
        # Load only pure definitions; the script's unrelated datasets are never opened.
        selected = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in functions],
                              type_ignores=[])
        env = dict(np=np, math=math, defaultdict=defaultdict)
        exec(compile(selected, str(path), 'exec'), env)
        _, bank = self.fixture_bank()
        cam = bank['camera'][0].astype(float)
        pred = cam.copy()
        pred[:, :3] = pred[:, :3]*1.13 + [.03, -.02, .01]
        gt = dict(camera=cam, camera_mask=bank['camera_mask'][0], gravity=bank['gravity'][0])
        rec = dict(dataset='d1', scene='test',gt=gt,pred=dict(camera=pred,gravity=bank['gravity'][0]))
        env['GT'] = {'test':dict(ds='d1',cam=cam[1::2],up=gt['gravity'],dbar=trajectory_scale(cam[1::2],np.ones(16,bool)))}
        expected = env['pose_eval']({'test':dict(cam=pred[1::2],up=gt['gravity'])})
        actual = scoring.pose_metrics([rec], range(1,32,2))
        for key in ('rot_deg','centre_err_m','pair_rot_deg','pair_disp_mra','pair_dir4_agree'):
            for stat in ('n','mean'):
                self.assertAlmostEqual(actual['all'][key][stat],expected['all'][key][stat],places=5)

    def fixture_bank(self):
        original = read_bank(ROOT.parents[2]/'aws_run1/kit/in/689136d4.npz')
        # Synthetic missing frames suffice for schema tests, never production GT.
        camera = np.repeat(original['camera'], 2, axis=1)
        camera[:, 0] = [0,0,0,0,0,0,1,1,1]
        bank = {**original, 'schema': np.array(bank32.SCHEMA), 'anchor_frames': np.arange(32),
                'depth_anchor_frames': np.arange(1,32,2), 'camera': camera,
                'camera_mask': np.ones((38,32), bool),
                'trajectory_scale': np.array([trajectory_scale(c, np.ones(32,bool)) for c in camera])}
        return original, bank

    def test_bank_validation_and_head_acc_readout(self):
        original, bank = self.fixture_bank()
        bank32.validate_bank(bank)
        comparison = bank32.compare_even(bank, original)
        self.assertLess(comparison['rotation_deg_max'], 1e-4)
        bad = {**bank, 'anchor_frames': np.arange(1,33)}
        with self.assertRaises(ValueError): bank32.validate_bank(bad)
        gt = {k: bank[k][0] for k in ('camera', 'camera_mask', 'gravity', 'gravity_mask', 'trajectory_scale',
                                      'point_depth_uv', 'point_depth_gt', 'point_depth_mask')}
        gt['depth_anchor_frames'] = bank['depth_anchor_frames'].tolist()
        pred = dict(camera=gt['camera'], gravity=gt['gravity'], trajectory_step_m=gt['trajectory_scale'],
                    point_depth=gt['point_depth_gt'])
        records = [dict(dataset='d1', scene='synthetic', gt=gt, pred=pred)]
        result = scoring.evaluate(records, {'pose','gravity','scale','depth'}, [('d1','synthetic')], [])
        self.assertEqual(result['all_frames']['all']['rot_deg']['n'], 32)
        self.assertEqual(result['even_frames']['all']['rot_deg']['n'], 16)
        self.assertEqual(result['all_frames']['all']['centre_err_m']['median'], 0.)
        self.assertEqual(result['all_frames']['all']['pair_disp_mra']['mean'], 1.)
        self.assertEqual(result['all_frames']['all']['pair_dir4_agree']['mean'], 1.)
        from student_pilot.gate_eval import evaluate
        allgate = evaluate(records, {'pose','gravity','scale','depth'}, [('d1','synthetic')], [])
        self.assertEqual(allgate['overall']['depth_abs_rel'], result['even_gate']['overall']['depth_abs_rel'])


if __name__ == '__main__':
    unittest.main()
