import copy
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

import torch

from tests.test_decoupled_v import DecoupledTests
from student_pilot.decoupled_v import (features, target_tensors, export_heads, load_heads,
                                      readout, head_settings, RECIPE, learning_rate)
from student_pilot.decoupled_vc import VisionCopy, VC_RECIPE, parameter_groups, freeze_for_inference
from student_pilot import decoupled_v_run as run
from student_pilot.p3_provenance import file_pin, write, load

ROOT = Path(os.environ['B11_TEST_OUTPUT'])


class PrivateEncoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        DecoupledTests.setUpClass()

    def pair(self):
        base, frozen, batch = DecoupledTests().pair()
        private = VisionCopy(base.config, base.model.visual)
        private.auxiliary_heads.load_state_dict(frozen.auxiliary_heads.state_dict())
        return base, frozen, private, batch

    def target(self):
        return target_tensors(dict(camera=[[0., 0., 0., 0., 0., 0., 1., 1., 1.]]*16,
            camera_mask=[True]*16, trajectory_scale=1., gravity=[0., -1., 0.], gravity_mask=True,
            point_depth=dict(uv=[[[500., 500.], [200., 300.]]]*16, depth=[[2., 3.]]*16,
                             mask=[[True, True]]*16)))

    def test_untrained_copy_exact_native_v_features(self):
        base, frozen, private, batch = self.pair()
        expected = features(frozen, batch)
        for checkpointing in (False, True):
            private.gradient_checkpointing = checkpointing
            private.train()
            got = features(private, batch)
            torch.testing.assert_close(got.states, expected.states, rtol=0, atol=0)
            self.assertEqual(got.states.dtype, torch.bfloat16)
            self.assertTrue(got.states.requires_grad)
            for a, b in zip(got.vits[0], expected.vits[0]):
                torch.testing.assert_close(a, b, rtol=0, atol=0)
                self.assertTrue(a.requires_grad)
            torch.testing.assert_close(got.grids[0], expected.grids[0], rtol=0, atol=0)
        self.assertEqual(base.config.p3['feature_backing'], 'decoupled_v')
        self.assertTrue(all(p.dtype == torch.float32 for p in private.model.visual.parameters()))
        self.assertEqual(private.model.visual.rotary_pos_emb.inv_freq.dtype, torch.float32)
        for a, b in zip(private.model.visual.parameters(), base.model.visual.parameters()):
            self.assertNotEqual(a.data_ptr(), b.data_ptr())

    def test_checkpointed_copy_and_heads_update_base_unchanged(self):
        base, _, private, batch = self.pair()
        base.requires_grad_(False)
        before = {n: p.clone() for n, p in base.state_dict().items()}
        snapshots = {n: p.clone() for n, p in private.named_parameters()}
        private.train()
        optimizer = torch.optim.AdamW(parameter_groups(private, VC_RECIPE), weight_decay=.01)
        self.assertEqual([g['lr'] for g in optimizer.param_groups], [1e-4, 1e-5])
        loss = private(batch, self.target()).mean()
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        encoder_grads = [p.grad for p in private.model.visual.blocks.parameters()]
        self.assertTrue(all(g is not None and torch.isfinite(g).all() for g in encoder_grads))
        self.assertTrue(any(g.abs().sum() > 0 for g in encoder_grads))
        self.assertTrue(all(p.grad is not None for p in private.auxiliary_heads.parameters()))
        optimizer.step()
        for group in optimizer.param_groups:
            for p in group['params']:
                if p.grad is not None:
                    self.assertEqual(p.grad.dtype, torch.float32)
                    self.assertEqual(optimizer.state[p]['exp_avg'].dtype, torch.float32)
        changed = [n for n, p in private.named_parameters() if not torch.equal(p, snapshots[n])]
        self.assertTrue(any(n.startswith('model.visual.blocks.') for n in changed))
        self.assertTrue(any(n.startswith('auxiliary_heads.') for n in changed))
        self.assertFalse(any('language' in n for n, _ in private.named_parameters()))
        for n, p in base.state_dict().items():
            self.assertTrue(torch.equal(p, before[n]), n)
        self.assertTrue(all(p.grad is None for p in base.parameters()))
        for step in (1, 48, 400, 1600):
            head = learning_rate(step, VC_RECIPE)
            encoder = learning_rate(step, {**VC_RECIPE, 'learning_rate': 1e-5})
            self.assertAlmostEqual(encoder, head*.1)

    def test_checkpoint_recompute_matches_uncheckpointed_gradients_and_short_rows(self):
        _, _, private, batch = self.pair()
        short = {**batch, 'video_grid_thw': torch.tensor([[4, 4, 4]]),
                 'pixel_values_videos': batch['pixel_values_videos'][:64]}
        target = self.target()
        target['aux_camera_mask'][:, 4:] = False
        target['aux_point_depth_mask'][:, 4:] = False
        reference = copy.deepcopy(private)
        reference.gradient_checkpointing = False
        for model in (private, reference):
            model.train()
            model(short, target).mean().backward()
        for (name, a), (_, b) in zip(private.named_parameters(), reference.named_parameters()):
            if a.grad is None:
                self.assertIsNone(b.grad, name)
            else:
                torch.testing.assert_close(a.grad, b.grad, rtol=0, atol=0, msg=name)
        self.assertEqual(len(private.model.visual.blocks[0]._forward_hooks), 0)

    def test_export_reload_trained_copy_and_digest_rejection(self):
        _, _, private, batch = self.pair()
        private.train()
        optimizer = torch.optim.AdamW(parameter_groups(private, VC_RECIPE))
        private(batch, self.target()).mean().backward(); optimizer.step()
        out = ROOT/uuid.uuid4().hex
        pin = export_heads(private, out, 200, {'synthetic': True})
        _, _, reloaded, _ = self.pair()
        artifact = load_heads(reloaded, pin)
        self.assertEqual(artifact['feature_backing'], 'decoupled_vc')
        self.assertEqual(artifact['feature_encoder_sha256'], private.config.p3['feature_encoder_sha256'])
        for name, value in private.state_dict().items():
            torch.testing.assert_close(value, reloaded.state_dict()[name], rtol=0, atol=0)
        uv = [[[100., 200.], [900., 700.]]]*16
        self.assertEqual(readout(private, batch, uv), readout(reloaded, batch, uv))
        freeze_for_inference(reloaded)
        self.assertEqual(readout(private, batch, uv), readout(reloaded, batch, uv))
        artifact['encoder_copy']['tensor_sha256'] = '0'*64
        write(out/'bad.json', artifact)
        with self.assertRaisesRegex(ValueError, 'tensor identity'):
            load_heads(reloaded, file_pin(out/'bad.json'))
        artifact['encoder_copy']['weights']['sha256'] = '0'*64
        write(out/'bad_file.json', artifact)
        with self.assertRaisesRegex(ValueError, 'pinned input'):
            load_heads(reloaded, file_pin(out/'bad_file.json'))

    def test_reuses_pinned_v_preparation_but_rejects_changed_inputs(self):
        _, frozen, _, _ = self.pair()
        out = ROOT/uuid.uuid4().hex; out.mkdir()
        inputs = {}
        for key in ('rows', 'division', 'bank', 'camera_source', 'database'):
            write(out/(key+'.json'), {'synthetic': key})
            inputs[key] = file_pin(out/(key+'.json'))
        source = dict(schema='decoupled-v-run-v1', mode='decoupled_v', recipe=RECIPE, init_heads=None,
            base_root='/synthetic/base', base_identity='synthetic', readout={},
            preparation_output=str(out/'v'), preparation=None, admission=None,
            **{k: inputs[k] for k in ('rows', 'division', 'bank', 'camera_source')})
        settings = head_settings(frozen.config.p3['camera'], 'synthetic', 'a'*64)
        write(out/'model.json', dict(kind='base', root=source['base_root'], base_identity='synthetic',
                                    feature_encoder_sha256='a'*64))
        write(out/'v_receipt.json', dict(schema='decoupled-v-preparation-v1', config_sha256=run.identity(source),
            inputs={k: inputs[k] for k in ('rows', 'division', 'bank', 'camera_source')},
            model=file_pin(out/'model.json'), database=inputs['database'], settings=settings, count=3, audit={'depth_rows':3}))
        write(out/'v_config.json', source)
        cfg = {**source, 'mode': 'decoupled_vc', 'recipe': VC_RECIPE, 'preparation_output': str(out/'vc'),
               'reuse_preparation': {'config': file_pin(out/'v_config.json'), 'receipt': file_pin(out/'v_receipt.json')}}
        cfg['camera_overrides'] = dict(run.FIXED_CAMERA)
        source_identity = run.identity(cfg)
        with patch.object(run, 'processor_for', side_effect=AssertionError('must not decode RGB')), \
             patch('sqlite3.connect', side_effect=AssertionError('must not rescan database')):
            receipt = run.prepare(cfg)
        self.assertEqual(receipt['config_sha256'], source_identity)
        self.assertEqual(receipt['settings'], run.reused_settings(settings, cfg))
        self.assertEqual(receipt['settings']['camera'], {**settings['camera'], **run.FIXED_CAMERA})
        self.assertEqual(set(receipt['settings']['camera'])-set(settings['camera']), set(run.FIXED_CAMERA))
        self.assertEqual(receipt['model'], file_pin(out/'model.json'))
        self.assertEqual(receipt['audit'], {'depth_rows':3})
        self.assertFalse((out/'vc/rows.sqlite').exists())
        for bad in ({}, {**run.FIXED_CAMERA, 'weight':1}, {'pose_reference':'first_group_concat_v1'}):
            broken = {**cfg, 'camera_overrides':bad}
            self.assertNotEqual(run.identity(broken), source_identity)
            with self.assertRaisesRegex(ValueError, 'exactly the two'):
                run.prepare(broken)
        with self.assertRaisesRegex(ValueError, 'fresh head'):
            run.prepare({**cfg, 'init_heads':inputs['rows']})
        self.assertEqual(receipt['database'], inputs['database'])
        self.assertEqual(receipt['settings']['feature_backing'], 'decoupled_vc')
        cfg['preparation'] = file_pin(out/'vc/receipt.json')
        run.prepared(cfg)
        tampered = {**receipt, 'settings':{**receipt['settings'], 'camera':settings['camera']}}
        write(out/'tampered.json', tampered)
        with self.assertRaisesRegex(ValueError, 'Derived head settings'):
            run.prepared({**cfg, 'preparation':file_pin(out/'tampered.json')})
        cfg['bank'] = inputs['rows']
        with self.assertRaisesRegex(ValueError, 'inputs differ'):
            run.prepare(cfg)
        with self.assertRaisesRegex(ValueError, 'differs from the run'):
            run.prepared(cfg)


if __name__ == '__main__':
    unittest.main()
