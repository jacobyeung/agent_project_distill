"""Value checks that expose grid, convention, reference, anchor and scale errors."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

from student_pilot import tower_read as T
from tests.test_tower_read import tower_batch, tower_state
from tests import test_tower_read as fixtures
from tests.tower_live_parity import quat_R


class TowerValues(unittest.TestCase):
    def test_scale_query_grid_matches_exporter_xy_endpoints(self):
        state = tower_state()
        # Confidence selects right-side pixels. Transposing uv changes the median.
        yy, xx = np.meshgrid(np.linspace(0, 1000, 51, dtype=np.float32),
                             np.linspace(0, 1000, 51, dtype=np.float32), indexing='ij')
        conf = np.broadcast_to(xx, (32, 51, 51)).copy()
        state = T.TowerState(state.raw_pose9, state.depth_grid, conf,
                             state.frame_indices, state.anchor_slots)
        captured = []
        def query(fmap, uv):
            captured.append(uv.cpu().numpy())
            return 1 + .002 * uv[..., 0] + .0003 * uv[..., 1]
        heads = SimpleNamespace(depth_map=torch.ones(32, 1, 1, 1),
                                depth_head=SimpleNamespace(query=query))
        T.apply_tower(heads, state, tower_batch(state))
        expected_uv = np.stack((xx, yy), -1).reshape(1, -1, 2).repeat(32, axis=0)
        np.testing.assert_array_equal(captured[0], expected_uv)
        expected_depth = 1 + .002 * expected_uv[..., 0] + .0003 * expected_uv[..., 1]
        expected_s = np.median(expected_depth.reshape(32, 51, 51)[conf > np.median(conf)])
        self.assertAlmostEqual(heads.tower_scale, float(expected_s), places=6)
        self.assertEqual(getattr(heads, 'queries', []), [])

    def test_non_even_anchors_print_the_lms_native_frames(self):
        from student_pilot import carrier_c1_decode as decode, carrier_c1_routing as routing
        model, batch, processor = fixtures.TowerDecode().fixture()
        state = tower_state()
        slots = np.floor(np.linspace(0, 63, 32)).astype(int)
        self.assertFalse(np.array_equal(slots, np.arange(0, 64, 2)))
        raw = state.raw_pose9.copy()
        raw[:, 1] = np.arange(64)**2 / 1000
        state = T.TowerState(raw, state.depth_grid, state.depth_conf_grid, state.frame_indices, slots)
        batch.update(tower_batch(state))
        depth = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        with mock.patch.object(depth, 'query', side_effect=lambda fmap, uv: torch.full(uv.shape[:2], 2.)):
            record = decode.generate(model, processor, batch, logits_processor=fixtures.TowerDecode.force,
                                     pose_source='tower', tower_state=state)
        self.assertEqual(record['finish'], 'eos')
        expected = raw[slots].copy()
        expected[:, :3] *= 2
        np.testing.assert_array_equal(record['heads']['pose9'], expected)
        geo = routing.OwnGeometry(expected, record['heads']['gravity'], None)
        actual = routing.OwnGeometry(record['heads']['pose9'], record['heads']['gravity'], None)
        for frame in (2, 9, 32):
            self.assertEqual(actual.pose_text(frame), geo.pose_text(frame))
        self.assertEqual(record['calls'][0]['response'], geo.move_text(2, 9))
        self.assertEqual(state.frame_indices[slots[-1]], state.frame_indices[-1])

    def test_nonidentity_rotation_and_frame_zero_reference(self):
        # Compose the two G3T camera heads independently with numpy matrices.
        n = 64
        theta = np.linspace(.13, .79, n)
        local = np.stack((np.sin(theta/2), np.zeros(n), np.zeros(n), np.cos(theta/2),
                          np.full(n, 1.), np.full(n, 1.2)), -1).astype(np.float32)
        yaw = np.linspace(-.22, .33, n)
        global_ = np.stack((2 + np.arange(n)/10, .2 + np.arange(n)**2/2000,
                            -.7 + np.arange(n)/20, np.sin(yaw/2), np.cos(yaw/2)), -1).astype(np.float32)
        w2c = []
        for a, b in zip(local, global_):
            L, G = np.eye(4), np.eye(4)
            L[:3, :3] = quat_R(a[:4])
            G[:3, :3] = quat_R([0, b[3], 0, b[4]])
            G[:3, 3] = b[:3]
            w2c.append(L @ G)
        expected = np.array([w @ np.linalg.inv(w2c[0]) for w in w2c])
        converted = T.g3t_to_c1_pose9(local, global_, np.tile([0., 0., 1024., 1024.], (n, 1)))['raw_pose']
        for k in (0, 1, 17, 63):
            np.testing.assert_allclose(quat_R(converted[k, 3:7]), expected[k, :3, :3], atol=1e-6)
            np.testing.assert_allclose(converted[k, :3], expected[k, :3, 3], atol=1e-6)
        np.testing.assert_allclose(converted[0, :7], [0, 0, 0, 0, 0, 0, 1], atol=1e-7)

    def test_scale_never_changes_nonidentity_rotation_or_fov(self):
        state = tower_state()
        raw = state.raw_pose9.copy()
        a = np.linspace(0, .8, 64)
        raw[:, 3] = np.sin(a/2)
        raw[:, 6] = np.cos(a/2)
        state = T.TowerState(raw, state.depth_grid, state.depth_conf_grid, state.frame_indices, state.anchor_slots)
        scaled, s = state.scaled_pose9(np.full((32, 51, 51), 3.))
        self.assertEqual(s, 3.)
        np.testing.assert_array_equal(scaled[:, 3:], raw[state.anchor_slots, 3:])
        np.testing.assert_allclose(np.linalg.norm(scaled[:, 3:7], axis=1), 1, atol=1e-12)

    def test_mandatory_metadata_fails_before_loading(self):
        state = tower_state()
        tower = T.FrozenG3TTower({'weights_path': '/missing', 'config_path': '/missing'})
        full = dict(tower_batch(state), tower_native_frames=[None]*64)
        for key in ('tower_anchor_slots', 'tower_lm_frame_indices', 'tower_frame_indices'):
            batch = {k: v for k, v in full.items() if k != key}
            with self.subTest(missing=key), mock.patch.object(tower, '_load') as load:
                with self.assertRaises(T.TowerError):
                    tower.run(batch)
                load.assert_not_called()
        with self.assertRaises(T.TowerError):
            state.validate_batch(dict(tower_batch(state), frame_indices=np.arange(32)))
        with self.assertRaises(T.TowerError):
            state.validate_batch(dict(tower_batch(state), tower_lm_frame_indices=np.arange(32)))
        # Mutation of public settings must fail closed, too.
        tower.dense_frames = 48
        with self.assertRaises(T.TowerError):
            tower.run(dict(full, tower_native_frames=[None]*48))

    def test_loader_builds_config_accepts_storage_dtype_and_keeps_fp32(self):
        import tempfile
        from safetensors.torch import save_file
        from student_pilot import c1r_ref, g3t_online
        out = Path(tempfile.mkdtemp(prefix='tower-load-', dir=os.environ.get('LANE_TEST_OUTPUT', '/tmp')))
        config = dict(embed_dim=1024, img_size=518, patch_size=14, enable_depth=True,
                      enable_point=True, enable_gravity_camera_heads=True)
        (out/'config.json').write_text(json.dumps(config))
        def tiny(**kwargs):
            self.assertEqual(kwargs, config)
            return torch.nn.ModuleDict({'aggregator': torch.nn.Linear(2, 2)})
        for dtype in (torch.float32, torch.float16, torch.bfloat16):
            model = tiny(**config)
            save_file({k: v.to(dtype).contiguous() for k, v in model.state_dict().items()}, str(out/'model.safetensors'))
            tower = T.FrozenG3TTower(dict(weights_path=str(out/'model.safetensors'), config_path=str(out/'config.json')))
            with mock.patch.object(g3t_online, 'vendor_digest', return_value=T.SOURCE_SHA256), \
                    mock.patch.object(T, '_hash', side_effect=[T.CONFIG_SHA256, T.WEIGHTS_SHA256]), \
                    mock.patch.object(c1r_ref, 'source_import', return_value=tiny):
                tower._load()
            for key, value in tower.module.state_dict().items():
                self.assertEqual(value.dtype, torch.float32)
                torch.testing.assert_close(value, model.state_dict()[key].to(dtype).float(), rtol=0, atol=0)
            self.assertFalse(tower.module.training)
            self.assertTrue(all(not p.requires_grad and p.is_inference() for p in tower.module.parameters()))
        config['patch_size'] = 16
        (out/'config.json').write_text(json.dumps(config))
        tower = T.FrozenG3TTower(dict(weights_path=str(out/'model.safetensors'), config_path=str(out/'config.json')))
        with mock.patch.object(g3t_online, 'vendor_digest', return_value=T.SOURCE_SHA256), \
                mock.patch.object(T, '_hash', side_effect=[T.CONFIG_SHA256, T.WEIGHTS_SHA256]), \
                mock.patch.object(c1r_ref, 'source_import') as build:
            with self.assertRaisesRegex(T.TowerError, 'config differs'):
                tower._load()
            build.assert_not_called()

    def test_failed_items_record_reasons_and_next_item_decodes(self):
        from student_pilot import carrier_c1_decode as decode
        model, batch, processor = fixtures.TowerDecode().fixture()
        tower = T.attach_tower(model, {}, module=torch.nn.Linear(1, 1))
        state = tower_state()
        depth = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        bad_pose = state.raw_pose9.copy()
        bad_pose[7, 6] = 0
        def invalid_pose(_):
            return T.TowerState(bad_pose, state.depth_grid, state.depth_conf_grid, state.frame_indices, state.anchor_slots)
        def no_scale(_):
            return T.TowerState(state.raw_pose9, state.depth_grid, np.ones_like(state.depth_conf_grid),
                                state.frame_indices, state.anchor_slots)
        records = []
        for bad, reason in ((invalid_pose, 'unit-quaternion'), (no_scale, 'No eligible')):
            with mock.patch.object(tower, 'run', side_effect=bad), \
                    mock.patch.object(depth, 'query', side_effect=lambda fmap, uv: torch.full(uv.shape[:2], 2.)):
                records.append(decode.generate(model, processor, batch, pose_source='tower', logits_processor=fixtures.TowerDecode.force))
            self.assertEqual(records[-1]['finish'], 'tower_error')
            self.assertIn(reason, records[-1]['tower_error'])
            self.assertIsNone(records[-1]['heads']['pose9'])
            self.assertEqual(records[-1]['calls'], [])
        bad = dict(batch, tower_lm_frame_indices=np.arange(32))
        records.append(decode.generate(model, processor, bad, pose_source='tower', tower_state=state))
        self.assertEqual(records[-1]['finish'], 'tower_error')
        with mock.patch.object(depth, 'query', side_effect=lambda fmap, uv: torch.full(uv.shape[:2], 2.)):
            records.append(decode.generate(model, processor, batch, pose_source='tower', tower_state=state,
                                           logits_processor=fixtures.TowerDecode.force))
        self.assertEqual(records[-1]['finish'], 'eos')
        self.assertEqual(len(records), 4)  # failures remain in the denominator
        self.assertEqual(sum(r['finish'] == 'tower_error' for r in records), 3)
        with self.assertRaisesRegex(ValueError, 'refuses tower_state'):
            decode.generate(model, processor, batch, pose_source='own', tower_state=state)


class TowerRealInputs(unittest.TestCase):
    def test_raw_scannet_gt_rotation_and_centres(self):
        root = os.environ.get('TOWER_INPUT_ROOT')
        if not root:
            self.skipTest('PENDING-INPUT: set TOWER_INPUT_ROOT to cached n64, V-C exports and raw ScanNet GT')
        from tests.tower_gt_check import check
        report = check(Path(root), limit=10)
        self.assertEqual(report['status'], 'PASS', report)
        self.assertGreaterEqual(report['scenes'], 5)

    def test_live_extraction_gate(self):
        spec = os.environ.get('TOWER_LIVE_INPUTS')
        if not spec:
            self.skipTest('PENDING-INPUT: set TOWER_LIVE_INPUTS to the live gate JSON input paths')
        from tests.tower_live_parity import check
        inputs = json.loads(Path(spec).read_text())
        inputs['tree'] = Path(T.__file__).resolve().parents[1]
        report = check(**inputs)
        if report['status'] == 'PENDING-INPUT':
            self.skipTest('PENDING-INPUT: '+json.dumps(report))
        self.assertEqual(report['status'], 'PASS', report)


if __name__ == '__main__':
    unittest.main()
