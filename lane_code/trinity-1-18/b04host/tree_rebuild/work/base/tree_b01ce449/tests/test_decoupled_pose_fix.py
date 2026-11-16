"""CPU regressions for origin conditioning and recovery from negative FoV logits."""
import math
import copy
import os
from pathlib import Path
import unittest
import uuid

import numpy as np
import torch

from student_pilot.camera_config import normalize
from student_pilot.camera_head import CameraSupervision
from student_pilot.camera_targets import encode_cameras, rotation_from_xyzw
from student_pilot.decoupled_v import head_settings, learning_rate
from student_pilot.gate_eval import evaluate_scene
from student_pilot.pose_samples import encode_sample


def settings(**extra):
    return dict(weight=.2, weight_gravity=.1, weight_scale=.04, embed_dim=64,
                num_heads=4, trunk_depth=4, refine_iterations=4, trajectory_balance=False,
                supervision={'path': '/unused', 'sha256': '0'*64}, **extra)


FIX = dict(pose_reference='first_group_concat_v1', fov_activation='bounded_sigmoid_v1')


class PoseFixTests(unittest.TestCase):
    def test_opt_in_and_legacy_artifact_shapes(self):
        old = CameraSupervision(16, settings())
        fixed = CameraSupervision(16, settings(**FIX))
        self.assertEqual(old.projector.in_features, 16)
        self.assertEqual(fixed.projector.in_features, 32)
        self.assertNotIn('pose_reference', old.settings)
        self.assertNotIn('fov_activation', old.settings)
        self.assertEqual(float(old.head.activate_fov(torch.tensor(-1.))), 0.)
        artifact = head_settings(settings(**FIX), 'base', 'a'*64)
        for key, value in FIX.items():
            self.assertEqual(artifact['camera'][key], value)
        restored = CameraSupervision(16, artifact['camera'])
        restored.load_state_dict(fixed.state_dict(), strict=True)
        x = torch.randn(1,16,16)
        torch.testing.assert_close(restored.predict(x)[-1], fixed.predict(x)[-1], rtol=0, atol=0)
        with self.assertRaises(RuntimeError):
            restored.load_state_dict(old.state_dict(), strict=True)
        for key in FIX:
            with self.assertRaises(ValueError):
                normalize(settings(**{key:'unknown'}))
        with self.assertRaisesRegex(ValueError, 'without a G3T'):
            normalize(settings(**FIX, g3t_prior=True))

    def test_reference_changes_pose_but_rest_permutation_does_not(self):
        torch.manual_seed(29)
        x = torch.randn(1,16,32)
        move_origin = torch.roll(torch.arange(16), -7)
        keep_origin = torch.cat((torch.tensor([0]), torch.arange(15,0,-1)))
        for reference in (False, True):
            head = CameraSupervision(32, settings(**FIX) if reference else settings())
            a = head.predict(x)[-1]
            b = head.predict(x[:,move_origin])[-1]
            c = head.predict(x[:,keep_origin])[-1]
            torch.testing.assert_close(c, a[:,keep_origin], atol=1e-6, rtol=1e-5)
            if reference:
                self.assertGreater(float((b-a[:,move_origin]).abs().max().detach()), 1e-3)
            else:
                torch.testing.assert_close(b, a[:,move_origin], atol=1e-6, rtol=1e-5)

    def test_negative_fov_logits_have_recovery_gradient_and_valid_readout(self):
        torch.manual_seed(31)
        head = CameraSupervision(32, settings(**FIX))
        with torch.no_grad():
            head.head.pose_branch.fc2.weight[7:].zero_()
            head.head.pose_branch.fc2.bias[7:] = -1.
        x = torch.randn(1,16,32)
        stages, _, _, depth_fov = head.predict_all(x, return_fov_raw=True)
        torch.testing.assert_close(depth_fov, stages[-1][...,7:9], rtol=0, atol=0)
        def focal_loss():
            return sum(.6**(3-i)*(p[...,7:9]-1.).abs().mean() for i,p in enumerate(head.predict(x)))/4
        before = focal_loss()
        before.backward()
        self.assertTrue((head.head.pose_branch.fc2.bias.grad[7:] < 0).all())
        optimizer = torch.optim.SGD([head.head.pose_branch.fc2.bias], lr=.1)
        optimizer.step()
        self.assertLess(float(focal_loss().detach()), float(before.detach()))
        fov = head.head.activate_fov(torch.tensor([-1e6, -4., 0., 4., 1e6]))
        self.assertTrue(((fov > 0) & (fov < math.pi)).all())

    def test_reference_conditioned_head_learns_relative_yaw(self):
        # Identical frame sets with different origins defeat an unmarked set head.
        torch.manual_seed(29)
        yaw = torch.linspace(-1.4,1.4,16)
        signal = torch.stack([yaw.sin(),yaw.cos(),(2*yaw).sin(),(2*yaw).cos()],-1) @ torch.randn(4,1152)
        perm = torch.roll(torch.arange(16),-7)
        x = torch.stack([signal, signal[perm]])
        angles = torch.stack([yaw, yaw[perm]])
        angles = angles-angles[:,:1]
        target = torch.zeros(2,16,9)
        target[...,4], target[...,6] = torch.sin(angles/2), torch.cos(angles/2)
        target[...,7:] = 1.
        torch.manual_seed(31)
        head = CameraSupervision(1152, settings(**FIX, weight_trans=0., weight_focal=0.))
        optimizer = torch.optim.AdamW(head.parameters(), lr=1e-4, weight_decay=.01)
        mask = torch.ones(2,16,dtype=torch.bool)
        first = None
        for step in range(201):
            stages = head.predict(x)
            loss = .2*sum(.6**(3-i)*head.stage_loss(p,target,mask,torch.ones(2)) for i,p in enumerate(stages)).mean()/4
            if first is None:
                first = float(loss.detach())
            if step == 200:
                break
            optimizer.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(head.parameters(),1.)
            for group in optimizer.param_groups:
                group['lr'] = learning_rate(step+1)
            optimizer.step()
        q = torch.nn.functional.normalize(stages[-1][...,3:7].detach(),dim=-1)
        error = 2*torch.acos((q*target[...,3:7]).sum(-1).abs().clamp(max=1.))*180/math.pi
        self.assertLess(float(loss.detach()), first*.3)
        self.assertLess(float(error.median()), 3.)

    def test_encoder_direction_origin_order_and_units(self):
        poses = np.tile(np.eye(4),(32,1,1))
        for i in range(32):
            angle = .17+i*.07
            poses[i,:3,:3] = rotation_from_xyzw([0,np.sin(angle/2),0,np.cos(angle/2)])
            poses[i,:3,3] = [.2*i, .1*np.sin(i), -.05*i]
        intrinsics = np.tile([[400.,0,320.],[0,500.,240.],[0,0,1.]],(32,1,1))
        camera, mask, _ = encode_cameras(poses,intrinsics,(480,640))
        sample, sample_mask, _, _ = encode_sample(poses,intrinsics,(480,640),list(range(32)))
        np.testing.assert_allclose(camera,sample)
        np.testing.assert_array_equal(mask,sample_mask)
        for g in range(16):
            expected = np.linalg.inv(poses[2*g+1])@poses[0]
            np.testing.assert_allclose(rotation_from_xyzw(camera[g,3:7]),expected[:3,:3],atol=1e-12)
            np.testing.assert_allclose(camera[g,:3],expected[:3,3],atol=1e-12)
        np.testing.assert_allclose(camera[:,7:],np.tile([2*math.atan(480/1000),2*math.atan(640/800)],(16,1)))
        record = dict(dataset='synthetic',scene='nonidentity_origin',gt=dict(camera=camera,camera_mask=mask),pred=dict(camera=camera))
        self.assertLess(max(evaluate_scene(record,{'pose'})['rotation_deg']),1e-5)
        wrong = camera.copy(); wrong[:,3:6] *= -1
        record['pred']['camera'] = wrong
        self.assertGreater(np.median(evaluate_scene(record,{'pose'})['rotation_deg']),60.)

    def test_fixed_native_v_and_vc_training_export_readout(self):
        from tests.test_decoupled_v import DecoupledTests
        from student_pilot.decoupled_v import VisionOnly, target_tensors, readout, export_heads, load_heads
        from student_pilot.decoupled_vc import VisionCopy, freeze_for_inference
        DecoupledTests.setUpClass()
        base, _, batch = DecoupledTests().pair()
        cfg = copy.deepcopy(base.config)
        cfg.p3['camera'].update(FIX)
        target = target_tensors(dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*16,
            camera_mask=[True]*16, trajectory_scale=1., gravity=[0.,-1.,0.], gravity_mask=True,
            point_depth=dict(uv=[[[500.,500.]]]*16, depth=[[2.]]*16, mask=[[True]]*16)))
        for cls in (VisionOnly, VisionCopy):
            model = cls(copy.deepcopy(cfg), copy.deepcopy(base.model.visual)).train()
            optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
            loss = model(batch,target).mean(); loss.backward()
            gradient = model.auxiliary_heads.camera.head.pose_branch.fc2.weight.grad
            self.assertGreater(float(gradient[3:7].norm()),0.)
            self.assertGreater(float(gradient[7:].norm()),0.)
            optimizer.step()
            root = Path(os.environ['LANE_TEST_OUTPUT'])/uuid.uuid4().hex
            artifact = export_heads(model,root,1,{'synthetic':True})
            restored = cls(copy.deepcopy(cfg),copy.deepcopy(base.model.visual))
            load_heads(restored,artifact)
            actual = readout(model,batch,[[[500.,500.]]]*16)
            self.assertEqual(actual,readout(restored,batch,[[[500.,500.]]]*16))
            self.assertEqual(actual['invalid_fov_frames'],[])
            self.assertIsNone(actual['geometry_error'])
            if cls is VisionCopy:
                freeze_for_inference(restored)
                self.assertEqual(actual,readout(restored,batch,[[[500.,500.]]]*16))


if __name__ == '__main__':
    unittest.main()
