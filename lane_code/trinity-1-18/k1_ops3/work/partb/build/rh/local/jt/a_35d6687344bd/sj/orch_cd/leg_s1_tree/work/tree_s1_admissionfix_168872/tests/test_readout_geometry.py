"""CPU regression for Stage-1 scoring when P3 rejects the predicted FoV."""
import json
import math
import unittest
from unittest.mock import patch

import torch

from tests import test_decoupled_v as fixtures
from student_pilot.decoupled_v import features, readout
from student_pilot.decoupled_vc import VisionCopy
from student_pilot.p3_grammar import ToolError
from student_pilot.readout_geometry import validation_summary


class ReadoutGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.DecoupledTests.setUpClass()

    def models(self):
        base, frozen, batch = fixtures.DecoupledTests().pair()
        private = VisionCopy(base.config, base.model.visual)
        private.auxiliary_heads.load_state_dict(frozen.auxiliary_heads.state_dict())
        return [(frozen, batch), (private, batch)]

    def check_readout(self, model, batch, count):
        points = [[[100., 200.], [900., 700.]]] * count
        model.eval()
        camera = model.auxiliary_heads.camera
        capture = features(model, batch)
        anchors = model.config.p3['anchors']
        selected = list(range(2, 33, 2)) if count == 16 else anchors
        with torch.no_grad():
            pose, gravity, scale = camera.predict_all(capture.states)
            geometry = capture.geometry()
            old = dict(raw_pose=pose[-1][0].double().cpu().tolist(),
                       gravity_up=gravity[-1][0].double().cpu().tolist(),
                       trajectory_step_m=float(scale[-1][0].exp()),
                       point_depth=[geometry.depth_fn(k, p).tolist() for k, p in zip(selected, points)])
        valid = readout(model, batch, points)
        # Serialization must preserve every scored byte, not just approximate values.
        self.assertEqual(json.dumps({k: valid[k] for k in old}), json.dumps(old))
        self.assertIsNone(valid['geometry_error'])
        self.assertEqual(valid['invalid_fov_frames'], [])

        predict = camera.predict_all
        def invalid(states, **inputs):
            pose, gravity, scale = predict(states, **inputs)
            pose = [value.clone() for value in pose]
            pose[-1][0, 0, 7:9] = torch.tensor([0., 4.])
            pose[-1][0, -1, 7:9] = torch.tensor([-1., math.pi])
            return pose, gravity, scale

        with patch.object(camera, 'predict_all', side_effect=invalid):
            with self.assertRaises(ToolError) as caught:
                capture.geometry()
            self.assertEqual(caught.exception.code, 'invalid_fov')
            got = readout(model, batch, points)
            with torch.no_grad():
                pose, _, _ = camera.predict_all(capture.states)
                fmap = camera.point_depth.encode(capture.grids[0], capture.vits[0], pose[-1][0, :, 7:9])
                expected = [camera.point_depth.query(
                    fmap[anchors.index(k):anchors.index(k)+1],
                    torch.as_tensor(p, dtype=torch.float32, device=fmap.device)[None]
                )[0].double().cpu().tolist() for k, p in zip(selected, points)]
            self.assertEqual(json.dumps(got['point_depth']), json.dumps(expected))
            self.assertEqual(got['geometry_error'], 'invalid_fov')
            self.assertEqual(got['invalid_fov_frames'], [
                dict(frame=anchors[0], fov_hw_rad=got['raw_pose'][0][7:9]),
                dict(frame=anchors[-1], fov_hw_rad=got['raw_pose'][-1][7:9])])
            self.assertEqual(validation_summary([valid, got]), dict(
                geometry_error_rows=1, geometry_errors={'invalid_fov': 1},
                invalid_fov_rows=1, invalid_fov_frames=2))
            self.assertTrue(all(math.isfinite(v) for row in got['point_depth'] for v in row))
            json.dumps(got, allow_nan=False)

    def test_valid_and_invalid_fov_both_modes(self):
        for model, batch in self.models():
            with self.subTest(mode=model.config.p3['feature_backing']):
                self.check_readout(model, batch, 16)

    def test_other_tool_errors_are_recorded(self):
        model, batch = self.models()[0]
        with patch('student_pilot.p3_heads.PrefixCapture.geometry',
                   side_effect=ToolError('invalid_rotation', 'fixture')):
            result = readout(model, batch, [[[500., 500.]]] * 16)
        self.assertEqual(result['geometry_error'], 'invalid_rotation')
        self.assertEqual(result['invalid_fov_frames'], [])
        self.assertEqual(len(result['point_depth']), 16)

    def test_all_frame_fov_both_modes_and_query_layouts(self):
        from tests.test_all_frames import AllFrameTests
        for private in (False, True):
            _, model, batch = AllFrameTests().pair(private)
            for count in (16, 32):
                with self.subTest(private=private, count=count):
                    self.check_readout(model, batch, count)

    def test_all_frame_summary_retains_odd_frame_failures(self):
        from student_pilot import all_frame_readout
        records = [dict(pred=dict(geometry_error='invalid_fov',
                                 invalid_fov_frames=[dict(frame=1, fov_hw_rad=[0., 4.])]))]
        with patch.object(all_frame_readout, 'pose_metrics', return_value={}), \
             patch.object(all_frame_readout, 'even_records', return_value=[]), \
             patch.object(all_frame_readout, 'gate', return_value={}):
            result = all_frame_readout.evaluate(records, [], [], [])
        self.assertEqual(result['geometry_validation']['invalid_fov_frames'], 1)
        self.assertEqual(result['geometry_validation']['invalid_fov_rows'], 1)

    def test_query_contract_errors_still_raise(self):
        model, batch = self.models()[0]
        with self.assertRaisesRegex(ValueError, 'Depth query slots'):
            readout(model, batch, [[[500., 500.]]] * 15)

    def check_evaluate(self, model, batch, all_frames=False):
        import gzip
        import os
        from pathlib import Path
        import uuid
        import numpy as np
        from student_pilot import decoupled_v_run as run
        from student_pilot.p3_provenance import file_pin, load, write
        from unittest.mock import Mock

        root = Path(os.environ['LANE_TEST_OUTPUT']) / uuid.uuid4().hex
        root.mkdir()
        slots = len(model.config.p3['anchors'])
        keys = [('d1', str(i)) for i in range(38)]
        camera_gt = np.tile([0., 0., 0., 0., 0., 0., 1., 1., 1.], (38, slots, 1))
        camera_gt[:, :, 0] = np.arange(slots) * .1
        bank = dict(dataset_tokens=np.array([k[0] for k in keys]), scene_tokens=np.array([k[1] for k in keys]),
                    camera=camera_gt, camera_mask=np.ones((38, slots), dtype=bool),
                    gravity=np.tile([0., -1., 0.], (38, 1)), gravity_mask=np.ones(38, dtype=bool),
                    trajectory_scale=np.ones(38), point_depth_uv=np.full((38, 16, 2, 2), 500.),
                    point_depth_gt=np.ones((38, 16, 2)), point_depth_mask=np.ones((38, 16, 2), dtype=bool),
                    frame_set_sha256=np.array(['fixture']*38), depth_anchor_frames=np.arange(1, 32, 2))
        rows = [dict(dataset=d, scene=s, qid=s, student_input=dict(
            frame_indices=list(range(32)), frames=[dict(sha256='a'*64)]*32)) for d, s in keys]
        with gzip.open(root/'rows.gz', 'wt') as stream:
            stream.write(''.join(json.dumps(row)+'\n' for row in rows))
        write(root/'inventory.json', dict(files=[file_pin(root/'rows.gz')]))
        write(root/'training.json', dict(scenes=[]))
        write(root/'bank.json', dict(synthetic=True))
        cfg = dict(mode='decoupled_v', readout_output=str(root/'readout'), all_frames=all_frames,
                   readout=dict(bank=file_pin(root/'bank.json'), training_scenes=file_pin(root/'training.json'),
                                rows_inventory=file_pin(root/'inventory.json')))
        artifact = dict(step=200, weights=dict(synthetic=True))
        write(root/'heads.json', artifact)
        predict = model.auxiliary_heads.camera.predict_all
        def invalid(states, **inputs):
            pose, gravity, scale = predict(states, **inputs)
            pose = [p.clone() for p in pose]
            pose[-1][0, 0, 7:9] = torch.tensor([0., 4.])
            return pose, gravity, scale
        encoded = {k: Mock(to=Mock(return_value=v)) for k, v in batch.items()}
        bank_module = 'all_frame_bank' if all_frames else 'compact_label_bank'
        with patch.object(run, 'prepared', return_value=({'settings': {}}, {'root': '/unused'})), \
             patch.object(run, 'processor_for'), patch.object(run, 'load_vision', return_value=model), \
             patch.object(model, 'to', return_value=model), patch.object(run, 'load_heads', return_value=artifact), \
             patch.object(run, 'encode', return_value=encoded), \
             patch('student_pilot.'+bank_module+'.read_bank', return_value=bank), \
             patch('student_pilot.compact_label_bank.frame_set_sha256', return_value='fixture'), \
             patch.object(model.auxiliary_heads.camera, 'predict_all', side_effect=invalid):
            run.evaluate(cfg, [file_pin(root/'heads.json')])
        result = load(root/'readout/200.json')
        report = load(result['report']['path'])
        expected = dict(geometry_error_rows=38, geometry_errors={'invalid_fov': 38},
                        invalid_fov_rows=38, invalid_fov_frames=38)
        self.assertEqual(result['gate_report_summary']['geometry_validation'], expected)
        self.assertEqual(report['report']['heads'], result['gate_report_summary'])
        self.assertEqual(result['gate_report_summary']['summary']['num_scenes'], 38)
        self.assertEqual(result['gate_report_summary']['summary']['depth_points'], 38*16*2)
        for row in result['scene_first_session'].values():
            if model.auxiliary_heads.camera.spatial_pose is not None:
                self.assertEqual(row['pose_input'], 'spatial_tokens_v1')
            self.assertEqual(row['geometry_error'], 'invalid_fov')
            self.assertEqual(row['invalid_fov_frames'], [dict(frame=model.config.p3['anchors'][0],
                                                             fov_hw_rad=[0., 4.])])
        if all_frames:
            self.assertEqual(report['detail']['all_frame_comparison']['geometry_validation'], expected)

    def test_evaluate_persists_errors_and_scores_entire_cohort(self):
        self.check_evaluate(*self.models()[0])

    def test_all_frame_evaluate_persists_odd_frame_failures(self):
        from tests.test_all_frames import AllFrameTests
        _, model, batch = AllFrameTests().pair(False)
        self.check_evaluate(model, batch, all_frames=True)

    def test_spatial_evaluate_records_input_for_both_banks(self):
        import copy
        from student_pilot.decoupled_v_run import SPATIAL_CAMERA
        base, _, batch = fixtures.DecoupledTests().pair()
        for all_frames in (False, True):
            cfg = copy.deepcopy(base.config)
            cfg.p3['camera'].update(SPATIAL_CAMERA)
            if all_frames:
                cfg.p3.update(anchors=list(range(1, 33)), temporal_grouping='fused_pairs_all_frames')
            model = VisionCopy(cfg, base.model.visual)
            self.check_evaluate(model, batch, all_frames=all_frames)
