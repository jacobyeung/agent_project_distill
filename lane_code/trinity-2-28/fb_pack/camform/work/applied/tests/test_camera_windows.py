"""B6 CPU regressions for long camera rows; all fixtures are retained."""
import copy
import json
import random
import unittest
from unittest.mock import patch

import numpy as np
import torch

from student_pilot import auxiliary_losses, camera_config, camera_targets, compact_label_bank
from student_pilot import ddp_core, ddp_config, full_ft, pose_samples, recording_pose as rp
from student_pilot.camera_head import CameraSupervision
from student_pilot.common import canonical_bytes
from tests.fullft_toys import bf16_batch, tiny_base
from tests.test_camera import cam_cfg, trajectory
from tests.test_full_ft import CarrierTokenizer
from tests import test_heads_only as b1
from tests import test_recording_pose as b2
from tools import heads_only_configs


def poses96():
    poses, intrinsics = trajectory()
    # Keep the first 32 frames exact, then extend the metric trajectory.
    extra = np.repeat(poses[-1:,:,:], 64, axis=0)
    extra[:, 0, 3] += np.arange(1, 65) * .15
    return np.concatenate((poses, extra)), np.repeat(intrinsics[:1], 96, axis=0)


def record(count):
    poses, intrinsics = poses96()
    camera, mask, scale, gravity = pose_samples.encode_sample(poses, intrinsics, (480, 640),
        range(count), max_groups=48)
    return {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': scale,
            'gravity': gravity.tolist(), 'gravity_mask': True, 'metric': True, 'lm_weight': 0.0}


def native_row(groups):
    prompt = [1] + [62, 61, 63] * groups + [2]
    ids = torch.tensor([prompt + [3, 4]])
    labels = ids.clone()
    labels[:, :len(prompt)] = -100
    return {'input_ids': ids, 'labels': labels, 'attention_mask': torch.ones_like(ids),
            'mm_token_type_ids': torch.where(ids == 61, 2, 0),
            'pixel_values_videos': torch.randn(groups * 4, 24), 'video_grid_thw': torch.tensor([[groups, 2, 2]])}


class TargetAndTrainerTests(unittest.TestCase):
    def test_48_groups_preserve_overlapping_targets_and_use_every_step(self):
        poses, intrinsics = poses96()
        target, mask, scale, gravity = pose_samples.encode_sample(poses, intrinsics, (480, 640),
                                                               range(96), max_groups=48)
        old, old_mask, _ = camera_targets.encode_cameras(poses[:32], intrinsics[:32], (480, 640))
        np.testing.assert_array_equal(target[:16], old)
        np.testing.assert_array_equal(mask[:16], old_mask)
        np.testing.assert_array_equal(gravity, camera_targets.encode_gravity(poses)[0])
        expected = np.linalg.norm(np.diff(target[:, :3], axis=0), axis=1).mean()
        self.assertEqual(scale, expected)
        camera_targets.check_record(record(96), max_groups=48)
        with self.assertRaises(ValueError):
            camera_targets.check_record(record(96))
        with self.assertRaises(ValueError):
            pose_samples.encode_sample(poses, intrinsics, (480, 640), range(96))

    def test_32_frame_batches_initialization_losses_and_gradients_are_exact(self):
        cfg = cam_cfg(weight_gravity=.2, weight_scale=.3)
        self.assertNotIn('max_groups', cfg)
        self.assertEqual(cfg, camera_config.normalize(cfg))
        for bad in (True, 15, 49, 48.0):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                camera_config.normalize({**cfg, 'max_groups': bad})
        source = native_row(16)
        baseline = camera_targets.insert_tokens(source, record(32), CarrierTokenizer())
        opted = camera_targets.insert_tokens(source, record(32), CarrierTokenizer(), max_groups=48)
        self.assertEqual(set(baseline), set(opted))
        for key in baseline:
            self.assertTrue(torch.equal(baseline[key], opted[key]), key)
        torch.manual_seed(7)
        old = CameraSupervision(16, cfg)
        torch.manual_seed(7)
        new = CameraSupervision(16, {**cfg, 'max_groups': 48})
        for key in old.state_dict():
            self.assertTrue(torch.equal(old.state_dict()[key], new.state_dict()[key]), key)
        hidden = torch.randn(1, baseline['input_ids'].shape[1], 16)
        loss1, loss2 = old.loss(hidden, baseline), new.loss(hidden, opted)
        self.assertTrue(torch.equal(loss1, loss2))
        loss1.sum().backward()
        loss2.sum().backward()
        for (name, p), (_, q) in zip(old.named_parameters(), new.named_parameters()):
            if p.grad is None:
                self.assertIsNone(q.grad, name)
            else:
                self.assertTrue(torch.equal(p.grad, q.grad), name)
        # The evaluation carrier API still pads to precisely 16, even with training capacity 48.
        self.assertEqual(camera_targets.insert_carriers(source, CarrierTokenizer())['aux_camera_positions'].shape, (1, 16))

    def test_mixed_group_masks_and_unlabelled_long_rows(self):
        batches = [camera_targets.insert_tokens(native_row(n // 2), record(n), CarrierTokenizer(), max_groups=48)
                   for n in (32, 64, 96)]
        batch = ddp_core.collate_rows(batches, 0)
        self.assertEqual(batch['aux_camera_target'].shape, (3, 48, 9))
        self.assertEqual(batch['aux_camera_positions'][0, 16:].tolist(), [-1] * 32)
        head = CameraSupervision(16, cam_cfg(max_groups=48, weight_gravity=.2, weight_scale=.2))
        hidden = torch.randn(3, batch['input_ids'].shape[1], 16)
        first = head.loss(hidden, batch)
        changed = copy.deepcopy(batch)
        changed['aux_camera_target'][~changed['aux_camera_mask']] = 1000
        changed['aux_camera_positions'][0, 16:] = -1
        second = head.loss(hidden, changed)
        self.assertTrue(torch.equal(first, second))
        # Invalid padded hidden states cannot become attention keys.
        states = head.carrier_states(hidden, batch['aux_camera_positions'])
        keys = batch['aux_camera_positions'] >= 0
        predictions = head.predict_all(states, keys)[0][-1]
        states[~keys] = 1000
        torch.testing.assert_close(predictions[keys], head.predict_all(states, keys)[0][-1][keys], rtol=0, atol=0)
        empty = {**record(96), 'camera': np.zeros((48, 9)).tolist(), 'camera_mask': [False] * 48, 'trajectory_scale': 0.0,
                 'gravity_mask': False}
        inert = camera_targets.insert_tokens(native_row(48), empty, CarrierTokenizer(), max_groups=48)
        loss = head.loss(torch.randn(1, inert['input_ids'].shape[1], 16), inert)
        self.assertEqual(loss.tolist(), [0.0])
        loss.sum().backward()
        self.assertTrue(all(p.grad is not None for p in head.parameters()))
        with self.assertRaises(ValueError):
            camera_targets.insert_tokens(native_row(48), record(96), CarrierTokenizer())

    def test_native_48_group_step_updates_only_unfrozen_heads(self):
        model = tiny_base()
        cfg = copy.deepcopy(model.config)
        cfg.vision_config.depth = 3
        model = type(model)(cfg).to(torch.bfloat16)
        root = b1.directory()
        export = b1.export_fixture(root, model)
        block = b1.frozen_block(export)
        full_ft.load_init_export(model, block, 'b' * 64)
        full_ft.prepare_model(model, block)
        heads = auxiliary_losses.attach(model, None, CarrierTokenizer(), b1.depth_camera(
            freeze_modules=['point_depth'], max_groups=48, weight_gravity=.2, weight_scale=.2))
        settings = ddp_config.normalize_training_config({'world_size': 2, 'full_ft': block}, 'qwen35')
        optimizer = full_ft.build_optimizer({}, {}, heads, block, settings)
        target = {**record(96), 'point_depth': {'uv': np.zeros((48, 2, 2)).tolist(),
                  'depth': np.zeros((48, 2)).tolist(), 'mask': np.zeros((48, 2), dtype=bool).tolist()}}
        batch = camera_targets.insert_tokens(native_row(48), target, CarrierTokenizer(), max_groups=48)
        before = {name: p.detach().clone() for name, p in model.named_parameters()}
        model.train()
        with patch.object(heads.camera.point_depth, 'forward', side_effect=AssertionError('Empty depth must not run')):
            loss = ddp_core.row_losses(model, bf16_batch(batch))
            self.assertTrue(torch.isfinite(loss).all())
            loss.sum().backward()
        optimizer.step()
        changed = []
        for name, p in model.named_parameters():
            if not torch.equal(p, before[name]):
                changed.append(name)
                self.assertTrue(p.requires_grad, name)
                self.assertTrue(name.startswith('auxiliary_heads.'), name)
                self.assertNotIn('.point_depth.', name)
            if not p.requires_grad:
                self.assertIsNone(p.grad, name)
                self.assertNotIn(p, optimizer.state)
        self.assertTrue(any('camera.head.' in name for name in changed))
        self.assertTrue(any('camera.tokens' in name for name in changed))
        self.assertFalse(torch.cuda.is_initialized())


class BuilderTests(unittest.TestCase):
    def test_windows_have_exact_raw_strides_bounds_and_random_starts(self):
        for fps in (15., 24., 30., 60.):
            for count in (64, 96):
                for jitter in (False, True):
                    gaps = rp.window_gaps(fps, jitter)
                    pool = list(range(100, 100 + (count - 1) * max(gaps) + 101))
                    sampler = rp.WindowSampler(pool, count, fps, jitter)
                    rng, starts = random.Random(17), set()
                    for _ in range(60):
                        _, _, numbers = sampler.draw(rng, 'd3')
                        starts.add(numbers[0])
                        self.assertEqual(len(numbers), count)
                        self.assertTrue(set(numbers) <= set(pool))
                        self.assertTrue(all(type(f) is int for f in numbers))
                        self.assertTrue(set(np.diff(numbers)) <= set(gaps))
                    self.assertGreater(len(starts), 10)
        for pool, n in ((list(range(96)), 96), ([0, 3, 8], 64)):
            with self.assertRaises(ValueError):
                rp.WindowSampler(pool, n, 30.)

    def test_window_plan_staging_rows_audit_and_frozen_depth_admission(self):
        for variant in rp.VARIANTS:
            root = b2.directory()
            request = {**b2.fixture(root), 'variant': variant, 'pool_size': 384, 'rows_per_scene': 4}
            plan = rp.make_plan(request)
            rp.validate_plan(plan)
            self.assertEqual(len(plan['excluded']), 5)
            pin = b2.save(root, 'plan.json', plan)
            receipt, staged = b2.staged_fixture(root, plan, pin)
            audit = rp.build(plan, pin, [staged], root / 'built')
            rows = [json.loads(line) for line in (root / 'built/pose_rows.jsonl').read_text().splitlines()]
            n = rp.VARIANTS[variant][0]
            self.assertEqual(audit['N_histogram'], {str(n): 4})
            self.assertEqual(audit['sampling']['variant'], variant)
            self.assertEqual(audit['pool_coverage'][0]['pool_frames'], 384)
            bank = {'dataset_tokens': np.array(['d3']), 'scene_tokens': np.array([plan['scenes'][0]['scene']]),
                    'point_depth_uv': np.zeros((1, 16, 2, 2)), 'frame_indices': np.arange(32)[None]}
            cfg = b1.depth_camera(max_groups=48, freeze_modules=['point_depth'],
                                   row_routing=camera_config.CAMBRIAN_P_ROUTING)
            poses = rp.load_poses(plan['scenes'][0], {})
            with patch.object(compact_label_bank, 'read_bank', return_value=bank):
                entries, _ = compact_label_bank.load_bank_for_rows('/unused.npz', rows, cfg)
                for row, entry in zip(rows, entries):
                    pose_samples.check_sample(row, max_groups=48)
                    self.assertEqual(len(entry['camera']), n // 2)
                    selected = row['student_input']['frame_indices'][:32]
                    old, old_mask, _ = camera_targets.encode_cameras(
                        poses['c2w'][selected], poses['intrinsics'][selected], poses['raster_hw'])
                    np.testing.assert_array_equal(np.asarray(entry['camera'])[:16], old)
                    np.testing.assert_array_equal(np.asarray(entry['camera_mask'])[:16], old_mask)
                    np.testing.assert_array_equal(entry['gravity'], camera_targets.encode_gravity(
                        poses['c2w'][selected], poses['world_up'])[0])
                    self.assertEqual(np.asarray(entry['point_depth']['mask']).shape, (n // 2, 2))
                    self.assertFalse(np.asarray(entry['point_depth']['mask']).any())
                    probe = camera_targets.probe_record(entry)
                    self.assertEqual(len(probe['camera']), n // 2)
                    self.assertFalse(np.asarray(probe['point_depth']['mask']).any())
                    self.assertEqual(probe['point_depth'], entry['point_depth'])
                with self.assertRaises(ValueError):
                    compact_label_bank.load_bank_for_rows('/unused.npz', rows, {**cfg, 'max_groups': 16})
                with self.assertRaisesRegex(ValueError, 'frozen point_depth'):
                    compact_label_bank.load_bank_for_rows('/unused.npz', rows, {**cfg, 'freeze_modules': []})
            broken = copy.deepcopy(plan)
            broken['sampling']['pool_size'] = 96
            with self.assertRaises(ValueError):
                rp.validate_plan(broken)

    def test_named_random32_variant_is_fresh_per_scene_per_epoch(self):
        root = b2.directory()
        request = {**b2.fixture(root), 'variant': 'random32_per_epoch', 'pool_size': 160}
        first = rp.make_plan(request)
        again = rp.make_plan(request)
        second = rp.make_plan({**request, 'epoch': 1})
        self.assertEqual(first, again)
        scene = first['scenes'][0]
        one = rp.sampler_for(scene, first['sampling'], first['seed'])
        two = rp.sampler_for(second['scenes'][0], second['sampling'], second['seed'])
        self.assertEqual(one.draw(random.Random(1), 'd3'), one.draw(random.Random(2), 'd3'))
        self.assertNotEqual(one.order, two.order)
        self.assertEqual(len(one.order), 32)
        self.assertEqual(one.order, sorted(set(one.order)))
        rp.validate_plan(first)

    def test_config_builder_adds_long_arms_without_changing_a0_a1_bytes(self):
        root, request = b1.BuilderTests().request()
        reference = heads_only_configs.build(request)
        for count in (64, 96):
            request['rows'][f'A{count}'] = {'name': f'WINDOW{count}_STRIDE3', 'count': 1280,
                'source': b2.save(root, f'rows{count}.json', {'window_frames': count})}
        configs = heads_only_configs.build(request)
        for arm, config in reference.items():
            self.assertEqual(canonical_bytes(configs[arm]), canonical_bytes(config))
        for count in (64, 96):
            config = configs[f'A{count}_RUN1']
            self.assertEqual(config['camera']['max_groups'], 48)
            self.assertEqual(config['frames'], {'count': count, 'pixels_per_frame': list(pose_samples.DEFAULT_PIXELS)})
            self.assertEqual(ddp_config.normalize_training_config(config, 'qwen35')['frames'], config['frames'])
        self.assertEqual(set(configs) - set(reference), {'A64_RUN1', 'A96_RUN1'})


if __name__ == '__main__':
    unittest.main()
