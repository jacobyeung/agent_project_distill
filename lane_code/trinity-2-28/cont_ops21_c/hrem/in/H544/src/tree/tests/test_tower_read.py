"""Portable CPU checks for dense tower reconstruction and routed decoding."""
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np
import torch

from student_pilot import tower_read as T
from student_pilot import tower_scale as S


def tower_state():
    raw = np.zeros((64, 9))
    raw[:, 0] = np.arange(64) / 10
    raw[:, 6] = 1
    raw[:, 7:] = [1., 1.2]
    shape = (32, 51, 51)
    return T.TowerState(raw, np.ones(shape), np.arange(np.prod(shape)).reshape(shape),
                        np.arange(64) * 3, np.arange(0, 64, 2))


def tower_batch(state=None):
    state = tower_state() if state is None else state
    return dict(tower_frame_indices=state.frame_indices, tower_anchor_slots=state.anchor_slots,
                tower_lm_frame_indices=state.frame_indices[state.anchor_slots])


class TowerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(min(8, torch.get_num_threads()))

    def test_scale_exact_boundary_population_and_hash_pin(self):
        d = np.array([1., 1., 1., 1., 1., 1., 1., 1.])
        c = np.arange(8.)
        v = np.array([2., 2., 2., 2., .1, 10., 4., 6.])
        scale, selected, threshold = S.estimate_scale(d, c, v)
        self.assertEqual(threshold, 3.5)
        np.testing.assert_array_equal(selected, [False]*6 + [True, True])
        self.assertEqual(scale, 5.)
        with mock.patch.object(S, 'ESTIMATOR_SHA256', '0'*64):
            with self.assertRaisesRegex(ValueError, 'hash differs'):
                S.estimate_scale(d, c, v)
        with self.assertRaisesRegex(ValueError, 'No eligible'):
            S.estimate_scale(d, np.ones(8), v)

    def test_state_scales_translation_only_and_keeps_native_anchors(self):
        state = tower_state()
        raw, scale = state.scaled_pose9(np.full((32, 51, 51), 2.))
        self.assertEqual(scale, 2.)
        np.testing.assert_array_equal(raw[:, :3], state.raw_pose9[::2, :3] * 2)
        np.testing.assert_array_equal(raw[:, 3:], state.raw_pose9[::2, 3:])
        self.assertFalse(state.raw_pose9.flags.writeable)
        state.validate_batch(tower_batch(state))
        with self.assertRaisesRegex(ValueError, 'frame indices differ'):
            state.validate_batch(dict(tower_batch(state), frame_indices=np.arange(32)))
        with self.assertRaises(ValueError):
            T.TowerState(state.raw_pose9, state.depth_grid, state.depth_conf_grid,
                         np.arange(64), np.arange(32) + 1)

    def test_owner_keeps_all_tower_parameters_outside_student(self):
        student = torch.nn.Linear(2, 2)
        module = torch.nn.ModuleDict({'depth_head': torch.nn.Linear(2, 2),
                                      'aggregator': torch.nn.Linear(2, 2)})
        keys, parameters = set(student.state_dict()), list(student.parameters())
        tower = T.attach_tower(student, {}, module=module)
        self.assertEqual(set(student.state_dict()), keys)
        self.assertEqual(list(student.parameters()), parameters)
        self.assertNotIn(module, list(student.modules()))
        student.train()
        self.assertFalse(module.training)
        self.assertTrue(all(not p.requires_grad for p in tower.module.parameters()))
        with self.assertRaises(ValueError):
            T.FrozenG3TTower({'dense_frames': 48}, module=module)
        with self.assertRaises(ValueError):
            T.FrozenG3TTower({'unrecognized': True}, module=module)

    def test_missing_dense_native_frames_and_bad_alignment_fail_before_loading(self):
        tower = T.FrozenG3TTower({'weights_path': '/missing', 'config_path': '/missing'})
        with self.assertRaisesRegex(ValueError, 'dense native'):
            tower.run({'pixel_values_videos': torch.zeros(32, 3)})
        with mock.patch.object(tower, '_load') as load:
            with self.assertRaisesRegex(ValueError, 'frame indices differ'):
                tower.run(dict(tower_native_frames=[None]*64, tower_frame_indices=np.arange(64), tower_anchor_slots=np.arange(0, 64, 2),
                               frame_indices=np.arange(32)))
            load.assert_not_called()

    def test_source_and_weight_pins_fail_closed_without_building_large_model(self):
        from student_pilot import g3t_online
        tower = T.FrozenG3TTower({'weights_path': '/missing', 'config_path': '/missing'})
        with mock.patch.object(g3t_online, 'vendor_digest', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'source pin'):
                tower._load()
        with mock.patch.object(g3t_online, 'vendor_digest', return_value=T.SOURCE_SHA256), \
                mock.patch.object(T, '_hash', side_effect=[T.CONFIG_SHA256, 'changed']):
            with self.assertRaisesRegex(ValueError, 'weights_path'):
                tower._load()

    def test_pose_conversion_uses_frame_one_and_native_fov(self):
        local = np.tile([0., 0., 0., 1., 1., 1.2], (64, 1)).astype(np.float32)
        global_ = np.tile([0., 0., 0., 0., 1.], (64, 1)).astype(np.float32)
        global_[:, 0] = 7 + np.arange(64) / 10
        full = T.g3t_to_c1_pose9(local, global_, np.tile([0., 0., 1024., 1024.], (64, 1)))
        cropped = T.g3t_to_c1_pose9(local, global_, np.tile([0., 256., 1024., 768.], (64, 1)))
        np.testing.assert_allclose(full['raw_pose'][0, :7], [0, 0, 0, 0, 0, 0, 1], atol=1e-7)
        np.testing.assert_allclose(full['raw_pose'][:, 0], np.arange(64) / 10, atol=1e-6)
        np.testing.assert_allclose(full['raw_pose'][:, 7:], np.tile([1., 1.2], (64, 1)), atol=1e-6)
        self.assertTrue((cropped['raw_pose'][:, 7] < full['raw_pose'][:, 7]).all())
        np.testing.assert_allclose(cropped['raw_pose'][:, 8], full['raw_pose'][:, 8], atol=1e-7)

    def test_dense_native_aggregator_precedes_anchor_dpt_with_real_tiny_components(self):
        from student_pilot.c1r_ref import source_import
        source_import(T.Path(T.__file__).parent / 'g3t_vendor')
        from vggt.models.aggregator import Aggregator
        from vggt.heads.camera_head import CameraHead
        from vggt.heads.dpt_head import DPTHead
        from vggt.utils.load_fn import load_and_preprocess_images_square as preprocess
        from student_pilot import _tower_native as native
        torch.manual_seed(13)
        model = torch.nn.Module()
        model.aggregator = Aggregator(img_size=28, embed_dim=8, depth=24, num_heads=2,
                                     mlp_ratio=1, patch_embed='conv')
        for name, encoding, bias in (
                ('local_camera_head', 'noT_quaR_FoV', [0, 0, 0, 1, .3, .3]),
                ('global_camera_head', 'absT_quaRy_noFoV', [0, 0, 0, 0, 1])):
            head = CameraHead(dim_in=16, trunk_depth=1, num_heads=2, pose_encoding_type=encoding)
            with torch.no_grad():
                head.pose_branch.fc2.weight.mul_(.001)
                head.pose_branch.fc2.bias.copy_(torch.tensor(bias))
            setattr(model, name, head)
        model.depth_head = DPTHead(dim_in=16, features=8, out_channels=[8]*4, output_dim=2, activation='exp')
        model.point_head = DPTHead(dim_in=16, features=8, out_channels=[8]*4, output_dim=4, activation='inv_log')
        tower = T.FrozenG3TTower({'depth_chunk_size': 8}, module=model)
        original_resize = T.F.interpolate

        def small_preprocess(images, size):
            value, coords = preprocess(images, 28)
            coords[:, :4] *= 1024 / 28
            return value, coords

        def resize(*args, **kwargs):
            if kwargs.get('size') == (518, 518):
                kwargs['size'] = (28, 28)
            return original_resize(*args, **kwargs)

        batch = dict(tower_native_frames=[np.full((24, 32, 3), k, np.uint8) for k in range(64)],
                     tower_frame_indices=np.arange(64), tower_anchor_slots=np.arange(0, 64, 2), frame_indices=np.arange(0, 64, 2))
        with mock.patch('vggt.utils.load_fn.load_and_preprocess_images_square', side_effect=small_preprocess), \
                mock.patch.object(T.F, 'interpolate', side_effect=resize), \
                mock.patch.object(native, 'selected_layers', wraps=native.selected_layers) as aggregate, \
                mock.patch.object(model.depth_head, 'forward', wraps=model.depth_head.forward) as dpt:
            state = tower.run(batch)
        self.assertEqual(aggregate.call_args.args[1].shape[1], 64)
        self.assertEqual(dpt.call_count, 4)
        self.assertTrue(all(c.kwargs['images'].shape[1] == 8 for c in dpt.call_args_list))
        self.assertEqual(state.raw_pose9.shape, (64, 9))
        self.assertEqual(state.depth_grid.shape, (32, 51, 51))
        self.assertEqual(state.points_grid.shape, (32, 51, 51, 3))
        self.assertTrue(np.isfinite(state.depth_grid).all())


class TowerDecode(unittest.TestCase):
    def fixture(self):
        from tests.test_carrier_c1_final import final_fixture, FakeTokenizer
        model, batch, _ = final_fixture()
        model.eval()
        batch = {k: v[:, :-2] if k in ('input_ids', 'attention_mask', 'labels', 'mm_token_type_ids') else v
                 for k, v in batch.items()}
        processor = SimpleNamespace(tokenizer=FakeTokenizer(),
                                    _routing_tokens=dict(ids={'<depth_at': 40, '<move': 45, '<pose': 39,
                                                              '<turn': 47, '<box_3d': 38}))
        batch.update(tower_batch())
        return model, batch, processor

    @staticmethod
    def force(ids, logits):
        script = [45, 46, 1]
        generated = [i for i in ids if i in script]
        out = torch.full_like(logits, -1e9)
        out[:, script[len(generated)]] = 0.
        return out

    def test_default_decode_matches_untouched_reference_byte_for_byte(self):
        import importlib.util
        import os
        from student_pilot import carrier_c1_decode as decode
        path = os.environ.get('TOWER_BASE_DECODE')
        if not path:
            self.skipTest('Set TOWER_BASE_DECODE to the untouched matching base decode file')
        spec = importlib.util.spec_from_file_location('student_pilot._tower_base_decode', path)
        base = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(base)
        model, batch, processor = self.fixture()
        old = base.generate(model, processor, batch, logits_processor=self.force)
        new = decode.generate(model, processor, batch, logits_processor=self.force)
        self.assertEqual(new, old)

    def test_tower_decode_emits_call_and_matches_harness_text_on_native_qwen_cpu(self):
        from student_pilot import carrier_c1_decode as decode, head_programs as hp
        model, batch, processor = self.fixture()
        state = tower_state()
        # Fix only the private depth query so the metric scale is exactly known.
        depth = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        tower = T.attach_tower(model, {}, module=torch.nn.Linear(1, 1))
        order = []

        def run(_batch):
            order.append('tower')
            return state

        handle = model.model.language_model.register_forward_pre_hook(lambda *args: order.append('lm'))
        try:
            with mock.patch.object(tower, 'run', side_effect=run) as execute, \
                    mock.patch.object(depth, 'query', side_effect=lambda fmap, uv: torch.full(uv.shape[:2], 2.)):
                record = decode.generate(model, processor, batch, logits_processor=self.force, pose_source='tower')
            self.assertEqual(execute.call_count, 1)
        finally:
            handle.remove()
        self.assertEqual(order[:2], ['tower', 'lm'])
        self.assertEqual(record['finish'], 'eos')
        self.assertEqual(record['calls'][0]['call'], '<move from=2 to=9>')
        self.assertEqual(record['heads']['depth_queries'], [])
        self.assertEqual(record['heads']['pose_source'], 'tower')
        self.assertEqual(record['heads']['tower_scale'], 2.)
        raw, _ = state.scaled_pose9(np.full((32, 51, 51), 2.))
        np.testing.assert_array_equal(record['heads']['pose9'], raw)
        from student_pilot.camera_targets import rotation_from_xyzw
        rotations = [rotation_from_xyzw(q).T for q in raw[:, 3:7]]
        centres = [-r @ p[:3] for r, p in zip(rotations, raw)]
        # head_programs uses camera y-down; v3.11 public move text uses y-up.
        dx, dy, dz = hp.move_values(rotations[1], centres[1], centres[8], record['heads']['gravity'])
        expected = hp.format_move((dx, -dy, dz))
        self.assertEqual(record['calls'][0]['response'], expected)
        self.assertTrue(decode.replay(record)['byte_equal'])
        self.assertNotRegex(expected, r'\d+\.\d{3,}|seconds|\bsec\b')

    def test_head_state_uses_own_gravity_and_depth_conditioning(self):
        from student_pilot import carrier_c1_decode as decode
        model, batch, _ = self.fixture()
        with torch.no_grad():
            hidden = model.hidden(batch)
            own = decode.HeadState(model, batch, hidden)
            tower = decode.HeadState(model, batch, hidden, pose_source='tower', tower_state=tower_state())
        np.testing.assert_array_equal(own.gravity, tower.gravity)
        torch.testing.assert_close(own.depth_map, tower.depth_map, atol=0, rtol=0)
        self.assertEqual(tower.queries, [])
        np.testing.assert_array_equal(tower.pose9[:, 7:], tower_state().raw_pose9[::2, 7:])
        geometry = tower.geometry()
        self.assertRegex(geometry.turn_text(1, 32), r'^turn = [+-]\d+ deg$')
        self.assertNotRegex(geometry.pose_text(32), r'\d+\.\d{3,}|seconds')
        with self.assertRaisesRegex(ValueError, 'pose_source'):
            decode.HeadState(model, batch, hidden, pose_source='invalid')

    def test_vertical_move_answers_match_camera_y_down_harness(self):
        from student_pilot import carrier_c1_routing as routing, head_programs as hp
        options = ['Up', 'Down', 'Forward', 'Backward', 'Left', 'Right']
        for sign, expected_answer in ((1, 'A'), (-1, 'B')):
            with self.subTest(public_y_sign=sign):
                state = tower_state()
                raw = state.raw_pose9.copy()
                raw[:, :3] = 0
                raw[2:, 1] = sign
                state = T.TowerState(raw, state.depth_grid, state.depth_conf_grid,
                                     state.frame_indices, state.anchor_slots)
                heads = SimpleNamespace(depth_map=torch.ones(32, 1, 1, 1), gravity=np.array([0., -1., 0.]),
                                        depth_head=SimpleNamespace(query=lambda fmap, uv: torch.full(uv.shape[:2], 2.)))
                T.apply_tower(heads, state, tower_batch(state))
                geo = routing.OwnGeometry(heads.pose9, heads.gravity, None)
                response = geo.move_text(1, 2)
                dx, dy, dz, _ = hp.parse_move(response)
                # The model's public trace evaluates Up=+dy and Down=-dy.
                components = [dy, -dy, dz, -dz, -dx, dx]
                tower_answer = chr(65 + int(np.argmax(components)))
                ri, ci = geo.camera(1)
                rj, cj = geo.camera(2)
                harness_values = hp.move_values(ri, ci, cj, heads.gravity)
                harness_text = hp.format_move(harness_values)
                harness_answer = hp.hp_answer('camera_movement_direction', options, harness_text)
                self.assertEqual(tower_answer, expected_answer)
                self.assertEqual(tower_answer, harness_answer)
                hx, hy, hz = harness_values
                self.assertEqual(response, hp.format_move((hx, -hy, hz)))

    def test_shuffle_prepares_only_the_donor_tower(self):
        from student_pilot import carrier_c1_decode as decode
        model, batch, processor = self.fixture()
        donor = dict(batch)
        tower = T.attach_tower(model, {}, module=torch.nn.Linear(1, 1))
        depth = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        with mock.patch.object(tower, 'run', return_value=tower_state()) as run, \
                mock.patch.object(depth, 'query', side_effect=lambda fmap, uv: torch.full(uv.shape[:2], 2.)):
            record = decode.generate(model, processor, batch, logits_processor=self.force,
                                     pose_source='tower', mode='shuffle', donor_batch=donor)
        self.assertIs(run.call_args.args[0], donor)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(record['heads']['tower_scale'], 2.)
        self.assertTrue(decode.replay(record)['byte_equal'])


if __name__ == '__main__':
    unittest.main()
