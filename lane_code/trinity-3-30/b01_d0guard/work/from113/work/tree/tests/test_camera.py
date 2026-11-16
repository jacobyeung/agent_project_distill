"""Cambrian-P style camera supervision: targets, token insertion, rope positions, loss, gradients, export, ranks."""
import copy
import io
import json
import math
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch

from tests import auxiliary_baseline as baseline
from tests.auxiliary_toys import SPECIALS, VIDEO, Toy, ToyTokenizer, install_runner

runner = install_runner()
from student_pilot import camera_config  # noqa: E402
from student_pilot import camera_targets as targets  # noqa: E402
from student_pilot.auxiliary_losses import attach, video_features  # noqa: E402
from student_pilot.auxiliary_targets import add_to_batch, input_identity, pin  # noqa: E402
from student_pilot.camera_head import CameraSupervision  # noqa: E402
from student_pilot.ddp_core import backward_batch, collate_rows, global_batches, rank_slots, row_losses  # noqa: E402

PIN = {'path': '/fixture/camera', 'sha256': '0' * 64}
SMALL = {'embed_dim': 16, 'num_heads': 2, 'trunk_depth': 2, 'refine_iterations': 2}
LAYERS = 4
CARRIER = SPECIALS.index('<|fim_middle|>')
HW = (480, 640)


@contextmanager
def kept_directory():
    """Fixture files stay under TMPDIR; the tests never delete anything."""
    yield Path(tempfile.mkdtemp(prefix='camera-test-'))


def cam_cfg(weight=0.2, **extra):
    return camera_config.normalize({'weight': weight, **SMALL, 'supervision': PIN, **extra})


def rotation(axis, angle):
    axis = np.asarray(axis, dtype=np.float64) / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


def trajectory(seed=0):
    rng = np.random.default_rng(seed)
    poses = np.repeat(np.eye(4)[None], 32, axis=0)
    for i in range(32):
        poses[i, :3, :3] = rotation([0.1, 1.0, 0.05 * seed], 0.08 * i + 0.3 * seed) @ rotation([1, 0, 0], 0.02 * i)
        poses[i, :3, 3] = [0.15 * i + seed, 1.4 + 0.01 * i, 0.05 * i ** 1.2] + rng.normal(0, 0.01, 3)
    intrinsics = np.repeat(np.array([[500.0, 0, 320], [0, 520.0, 240], [0, 0, 1]])[None], 32, axis=0)
    return poses, intrinsics


def record_for(seed=0, valid=None):
    camera, mask, scale = targets.encode_cameras(*trajectory(seed), HW, valid)
    return {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': scale}


def video_row(tokenizer, target='There are 4 chairs.', qid='r', camera=None):
    """Native-like layout: per temporal group a timestamp, vision start, 4 video tokens, vision end."""
    start, end = SPECIALS.index('<|vision_start|>'), SPECIALS.index('<|vision_end|>')
    prompt, types = [start], [0]
    for g in range(16):
        stamp = tokenizer.encode(f'<{2.5 * g:.1f} seconds>')
        prompt += stamp + [start] + [VIDEO] * 4 + [end]
        types += [0] * (len(stamp) + 1) + [2] * 4 + [0]
    text = tokenizer.encode('How many chairs are here?\n\nAnswer.<|im_end|>\n')
    prompt, types = prompt + text, types + [0] * len(text)
    suffix = tokenizer.encode(target + '<|endoftext|>')
    ids = prompt + suffix
    padding = (-len(ids)) % 8
    input_ids = torch.tensor([ids + [0] * padding])
    labels = torch.full_like(input_ids, -100)
    labels[0, len(prompt):len(ids)] = input_ids[0, len(prompt):len(ids)]
    batch = {'input_ids': input_ids, 'labels': labels, 'attention_mask': torch.tensor([[1] * len(ids) + [0] * padding]),
             'mm_token_type_ids': torch.tensor([types + [0] * (len(suffix) + padding)]), 'video_grid_thw': torch.tensor([[16, 4, 4]])}
    row = {'qid': qid, 'target': target, 'student_input': {'question': 'How many chairs are here?', 'options': []}}
    if camera is not None:
        row['_camera'] = camera
    return row, batch


class TargetTests(unittest.TestCase):
    def test_encoding_conventions(self):
        poses, intrinsics = trajectory(1)
        camera, mask, scale = targets.encode_cameras(poses, intrinsics, HW)
        self.assertTrue(mask.all())
        # Group g describes its second frame 2g+1, relative to the camera of sampled frame 0.
        for g in range(16):
            relative = np.linalg.inv(poses[2 * g + 1]) @ poses[0]
            np.testing.assert_allclose(camera[g, :3], relative[:3, 3], atol=1e-9)
            np.testing.assert_allclose(targets.rotation_from_xyzw(camera[g, 3:7]), relative[:3, :3], atol=1e-9)
            self.assertGreaterEqual(camera[g, 6], 0)
        self.assertAlmostEqual(camera[3, 7], 2 * math.atan(480 / (2 * 520)))
        self.assertAlmostEqual(camera[3, 8], 2 * math.atan(640 / (2 * 500)))
        self.assertAlmostEqual(scale, np.mean([np.linalg.norm(camera[g, :3] - camera[g - 1, :3]) for g in range(1, 16)]))
        # A common rigid change of world coordinates leaves every target unchanged.
        world = np.eye(4)
        world[:3, :3], world[:3, 3] = rotation([1, 2, 3], 0.7), [4, -2, 8]
        moved, _, moved_scale = targets.encode_cameras(world @ poses, intrinsics, HW)
        np.testing.assert_allclose(moved, camera, atol=1e-8)
        self.assertAlmostEqual(moved_scale, scale)
        self.assertEqual(targets.check_record({**record_for(1), 'metric': True})[1].sum(), 16)

    def test_masks_and_contract_refusals(self):
        poses, intrinsics = trajectory(2)
        valid = np.ones(32, bool)
        valid[0] = False  # origin camera missing: the whole row is unsupervised
        camera, mask, scale = targets.encode_cameras(poses, intrinsics, HW, valid)
        self.assertFalse(mask.any())
        self.assertEqual((np.abs(camera).sum(), scale), (0, 0.0))
        valid = np.ones(32, bool)
        valid[1] = False  # group 0's anchor missing: only group 0 is masked
        camera, mask, scale = targets.encode_cameras(poses, intrinsics, HW, valid)
        self.assertEqual(mask.tolist(), [False] + [True] * 15)
        bad = poses.copy()
        bad[5, 0, 0] = 3.0  # group 2 is not rigid
        camera, mask, scale = targets.encode_cameras(bad, intrinsics, HW)
        self.assertFalse(mask[2])
        self.assertEqual(mask.sum(), 15)
        self.assertAlmostEqual(scale, targets.trajectory_scale(camera, mask))
        good = {**record_for(2), 'metric': True}
        for change, message in [({'trajectory_scale': 9.0}, 'recomputation'), ({'metric': False}, 'metric'),
                                ({'camera': [[0.0] * 9] * 16}, 'quaternion')]:
            with self.assertRaisesRegex(ValueError, message):
                targets.check_record({**good, **change})
        flipped = copy.deepcopy(good)
        flipped['camera'][4][3:7] = [-v for v in flipped['camera'][4][3:7]]
        with self.assertRaisesRegex(ValueError, 'quaternion'):
            targets.check_record(flipped)

    def test_sidecar_load_keeps_census_and_identity(self):
        rows = []
        for index in range(3):
            row = {'qid': f'q{index}', 'dataset': 'scannet', 'scene': 's', 'target': 'x',
                   'student_input': {'question': 'q', 'options': [], 'fps': 1., 'total_num_frames': 32,
                                     'frame_indices': list(range(32)), 'timestamps': list(range(32)),
                                     'frames': [{'path': f'/rgb/{i}.png', 'sha256': f'{i:064x}'} for i in range(32)]}}
            rows.append(row)
        records = [{'qid': row['qid'], 'input_sha256': input_identity(row), 'metric': True, 'sources': {}, 'deferred': {},
                    **record_for(index, None if index != 2 else np.zeros(32, bool))} for index, row in enumerate(rows)]
        with kept_directory() as root:
            def write(name, rows_out):
                path = root / name
                path.write_text(json.dumps({'schema': targets.SCHEMA, 'pose_encoding': targets.POSE_ENCODING,
                                            'translation_unit_m': 1.0, 'rows': rows_out}))
                return pin(path)
            loaded = targets.load_for_rows(rows, cam_cfg(supervision=write('ok.json', records)))
            self.assertEqual([any(r['camera_mask']) for r in loaded], [True, True, False])
            self.assertIsNone(targets.load_for_rows(rows, cam_cfg(0.0)))
            moved = copy.deepcopy(records)
            moved[0]['input_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'RGB input'):
                targets.load_for_rows(rows, cam_cfg(supervision=write('moved.json', moved)))
            with self.assertRaisesRegex(ValueError, 'census'):
                targets.load_for_rows(rows, cam_cfg(supervision=write('short.json', records[:2])))
            empty = [{**r, **record_for(0, np.zeros(32, bool))} for r in records]
            with self.assertRaisesRegex(ValueError, 'no training row'):
                targets.load_for_rows(rows, cam_cfg(supervision=write('empty.json', empty)))
            self.assertEqual([r['lm_weight'] for r in loaded], [1.0, 1.0, 1.0])
            posed = [{**row, 'pool': 'r1m', 'category': targets.POSE_ONLY_CATEGORY} if i == 0 else row for i, row in enumerate(rows)]
            loaded = targets.load_for_rows(posed, cam_cfg(supervision=write('pose_only.json', records)))
            self.assertEqual([r['lm_weight'] for r in loaded], [0.0, 1.0, 1.0])
            unposed = [{**row, 'category': targets.POSE_ONLY_CATEGORY} if i == 2 else row for i, row in enumerate(rows)]
            with self.assertRaisesRegex(ValueError, 'pose-only row has no camera'):
                targets.load_for_rows(unposed, cam_cfg(supervision=write('pose_only_empty.json', records)))


class InsertionTests(unittest.TestCase):
    def test_carriers_follow_each_group_and_leave_everything_else_in_place(self):
        tokenizer = ToyTokenizer()
        row, batch = video_row(tokenizer, camera=record_for(0))
        inserted = add_to_batch(batch, row, tokenizer)
        positions = inserted['aux_camera_positions'][0].tolist()
        ids, labels = inserted['input_ids'][0], inserted['labels'][0]
        self.assertEqual(len(positions), 16)
        self.assertTrue(all(int(ids[p]) == CARRIER and int(ids[p - 1]) == VIDEO for p in positions))
        self.assertTrue(all(int(labels[p]) == -100 and int(inserted['mm_token_type_ids'][0, p]) == 0
                            and int(inserted['attention_mask'][0, p]) == 1 for p in positions))
        keep = torch.ones_like(ids, dtype=torch.bool)
        keep[positions] = False
        for key in ('input_ids', 'labels', 'attention_mask', 'mm_token_type_ids'):
            self.assertTrue(torch.equal(inserted[key][0][keep], batch[key][0]), key)
        self.assertEqual(inserted['input_ids'].shape[1], batch['input_ids'].shape[1] + 16)
        hidden = torch.randn(1, ids.shape[0], 12)
        self.assertEqual(video_features(hidden, inserted, VIDEO, 2).shape, (1, 16, 4, 4, 12))
        # Rows without camera supervision keep their encoding, as in Cambrian-P.
        row, plain = video_row(tokenizer, camera=record_for(0, np.zeros(32, bool)))
        unchanged = add_to_batch(plain, row, tokenizer)
        self.assertTrue(torch.equal(unchanged['input_ids'], plain['input_ids']))
        self.assertEqual(unchanged['aux_camera_positions'].tolist(), [[-1] * 16])
        row, twice = video_row(tokenizer, camera=record_for(0))
        with self.assertRaisesRegex(ValueError, 'already contains'):
            add_to_batch(inserted, row, tokenizer)

    @unittest.skipUnless(importlib_available := __import__('importlib').util.find_spec('transformers') is not None,
                         'transformers is not installed')
    @unittest.skipUnless(__import__('tests.version_pin', fromlist=['x']).on_trainer_pin(),
                         __import__('tests.version_pin', fromlist=['x']).REASON)
    def test_qwen35_rope_positions_treat_carriers_as_text(self):
        from types import SimpleNamespace
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model

        model = SimpleNamespace(config=SimpleNamespace(vision_config=SimpleNamespace(spatial_merge_size=2)))
        model.get_vision_position_ids = lambda *args, **kwargs: Qwen3_5Model.get_vision_position_ids(model, *args, **kwargs)
        tokenizer = ToyTokenizer()
        row, batch = video_row(tokenizer, camera=record_for(0))
        inserted = add_to_batch(batch, row, tokenizer)

        def rope(b):
            return Qwen3_5Model.get_rope_index(model, b['input_ids'], b['mm_token_type_ids'], video_grid_thw=b['video_grid_thw'].clone(),
                                               attention_mask=b['attention_mask'])[0][:, 0]
        before, after = rope(batch), rope(inserted)
        carriers = inserted['aux_camera_positions'][0].tolist()
        original = [j for j in range(inserted['input_ids'].shape[1]) if j not in carriers]
        for i, j in enumerate(original[:int(batch['attention_mask'].sum())]):
            shift = sum(1 for c in carriers if c < j)
            self.assertTrue(torch.equal(after[:, j], before[:, i] + shift), (i, j))
        for g, c in enumerate(carriers):
            self.assertEqual(len(set(after[:, c].tolist())), 1)  # a text position: equal on all three axes
            self.assertEqual(int(after[0, c]), int(after[:, :c].max()) + 1)


class HeadTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_loss_matches_the_weighted_l1_formula(self):
        supervision = CameraSupervision(12, cam_cfg())
        target = torch.tensor(np.stack([record_for(s)['camera'] for s in (0, 1)]), dtype=torch.float32)
        mask = torch.ones(2, 16, dtype=torch.bool)
        mask[1, 9:] = False
        delta = torch.linspace(-0.3, 0.4, 2 * 16 * 9).view(2, 16, 9)
        scale = torch.tensor([0.5, 0.01])
        loss = supervision.stage_loss(target + delta, target, mask, scale.clamp_min(0.05))
        for row in range(2):
            valid = mask[row]
            d = delta[row][valid].abs()
            expected = (1.0 * (d[:, :3] / max(float(scale[row]), 0.05)).mean(1) + 1.0 * d[:, 3:7].mean(1) + 0.5 * d[:, 7:].mean(1)).mean()
            self.assertAlmostEqual(float(loss[row]), float(expected), places=5)
        summed = CameraSupervision(12, cam_cfg(component_reduction='sum')).stage_loss(target + delta, target, mask, torch.ones(2))
        d = delta[0].abs()
        self.assertAlmostEqual(float(summed[0]), float((d[:, :3].sum(1) + d[:, 3:7].sum(1) + 0.5 * d[:, 7:].sum(1)).mean()), places=4)

    def test_head_converges_on_synthetic_trajectories(self):
        supervision = CameraSupervision(24, cam_cfg(embed_dim=32, num_heads=4))
        rows = 4
        target = torch.tensor(np.stack([record_for(s)['camera'] for s in range(rows)]), dtype=torch.float32)
        batch = {'aux_camera_positions': torch.arange(16).repeat(rows, 1), 'aux_camera_target': target,
                 'aux_camera_mask': torch.ones(rows, 16, dtype=torch.bool),
                 'aux_camera_scale': torch.tensor([record_for(s)['trajectory_scale'] for s in range(rows)], dtype=torch.float32)}
        hidden = torch.randn(rows, 16, 24)
        initial = supervision.loss(hidden, batch).mean().item()
        optimizer = torch.optim.Adam(supervision.parameters(), lr=2e-3)
        for _ in range(300):
            optimizer.zero_grad(set_to_none=True)
            supervision.loss(hidden, batch).mean().backward()
            optimizer.step()
        final = supervision.loss(hidden, batch).mean().item()
        self.assertLess(final, initial * .2, (initial, final))
        print('camera_toy_loss', json.dumps({'initial': initial, 'final': final}), flush=True)

    def test_training_forward_inserts_learned_tokens_and_reaches_every_parameter(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=LAYERS)
        heads = attach(model, None, tokenizer, cam_cfg())
        self.assertTrue(heads.has_camera and not heads.has_reason)
        row, batch = video_row(tokenizer, camera=record_for(0))
        batch = collate_rows([add_to_batch(batch, row, tokenizer)], 0)
        seen = []
        handle = model.embedding.register_forward_hook(lambda m, a, out: seen.append(out))
        loss = row_losses(model, batch)
        handle.remove()
        # The hook output captured above precedes the camera hook, so check the camera hook's effect directly.
        positions = batch['aux_camera_positions'][0]
        self.assertTrue(torch.equal(seen[0][0, positions], model.embedding.weight[CARRIER].expand(16, -1)))
        loss.sum().backward()
        self.assertIn('camera', heads.last_terms)
        self.assertGreater(float(heads.last_terms['camera']), 0)
        self.assertGreater(model.embedding.weight.grad.norm().item(), 0)
        self.assertGreater(heads.camera.tokens.grad[0].abs().sum().item(), 0)
        self.assertGreater(heads.camera.tokens.grad[1].abs().sum().item(), 0)
        for name, parameter in heads.camera.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
        self.assertEqual(model.embedding.weight.grad[CARRIER].abs().sum().item(), 0)  # carrier embedding replaced

    def test_pose_only_rows_train_the_camera_head_alone(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=LAYERS)
        heads = attach(model, None, tokenizer, cam_cfg())
        rows = [video_row(tokenizer, qid=f'p{i}', camera={**record_for(i), 'lm_weight': w}) for i, w in enumerate((0.0, 1.0))]
        batch = collate_rows([add_to_batch(b, r, tokenizer) for r, b in rows], 0)
        self.assertEqual(batch['aux_lm_weight'].tolist(), [0.0, 1.0])
        losses = row_losses(model, batch)
        camera = heads.last_terms['camera'].detach()
        unweighted = row_losses(model, {k: v for k, v in batch.items() if k != 'aux_lm_weight'}).detach()
        self.assertGreater(float(unweighted[0] - losses.detach()[0]), 0)
        self.assertAlmostEqual(float(losses.detach()[1]), float(unweighted[1]), places=5)
        model.zero_grad(set_to_none=True)
        heads.zero_grad(set_to_none=True)
        parts = {}
        losses = row_losses(model, {k: (v[:1] if torch.is_tensor(v) and v.shape[0] == 2 else v) for k, v in batch.items()}, parts)
        self.assertEqual(parts['lm'].tolist(), [0.0])  # the LM gate sees no text loss from a pose-only row
        self.assertGreater(float(heads.last_terms['camera'].sum()), 0)
        self.assertGreater(float(camera[0]), 0)
        losses.sum().backward()
        self.assertEqual(model.lm_head.weight.grad.abs().sum().item(), 0)  # no text gradient
        self.assertGreater(heads.camera.tokens.grad.abs().sum().item(), 0)
        self.assertGreater(model.embedding.weight.grad.norm().item(), 0)

    def test_rows_without_poses_keep_every_parameter_in_the_graph(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=LAYERS)
        heads = attach(model, None, tokenizer, cam_cfg())
        row, batch = video_row(tokenizer, camera=record_for(0, np.zeros(32, bool)))
        loss = row_losses(model, collate_rows([add_to_batch(batch, row, tokenizer)], 0))
        loss.sum().backward()
        self.assertEqual(float(heads.last_terms['camera'].sum()), 0)
        for name, parameter in heads.camera.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
            self.assertEqual(parameter.grad.abs().sum().item(), 0, name)

    def test_disabled_path_is_bit_identical(self):
        tokenizer = ToyTokenizer()
        self.assertIsNone(attach(Toy(layers=LAYERS), None, tokenizer, camera_config.normalize({'weight': 0.0})))
        model = Toy(layers=LAYERS)
        twin = copy.deepcopy(model)
        state = torch.random.get_rng_state().clone()
        self.assertIsNone(attach(model, None, tokenizer, camera_config.normalize({})))
        rows = [video_row(tokenizer, qid=f'r{i}', target=t)[1] for i, t in enumerate(('Four.', 'There are 2 chairs.'))]
        new, old = collate_rows(rows, 0), baseline.collate_rows(rows, 0)
        for key in new:
            self.assertTrue(torch.equal(new[key], old[key]), key)
        a = backward_batch(model, new, [1, 0], 1, 2)
        b = baseline.backward_batch(twin, old, [1, 0], 1, 2)
        self.assertTrue(torch.equal(a, b))
        for (name, p), q in zip(model.named_parameters(), twin.parameters()):
            self.assertTrue(torch.equal(p.grad, q.grad), name)
        self.assertTrue(torch.equal(state, torch.random.get_rng_state()))
        from student_pilot.ddp_config import normalize_training_config
        plain = normalize_training_config({}, 'qwen35')
        self.assertEqual(normalize_training_config({'camera': {'weight': 0.2, 'supervision': PIN}}, 'qwen35'), plain)
        with self.assertRaises(ValueError):
            normalize_training_config({'camera': {'weight': 0.2}}, 'qwen35')

    def test_head_export_roundtrip(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=LAYERS)
        heads = attach(model, None, tokenizer, cam_cfg())
        buffer = io.BytesIO()
        torch.save({k: v.detach().cpu() for k, v in heads.state_dict().items()}, buffer)
        buffer.seek(0)
        manifest = json.loads(json.dumps(heads.manifest()))
        self.assertEqual(manifest['camera']['carrier'], {'token': '<|fim_middle|>', 'id': CARRIER})
        self.assertFalse(manifest['camera']['inference_required'])
        self.assertFalse(manifest['inference_required'])
        twin = Toy(layers=LAYERS)
        loaded = attach(twin, None, tokenizer, manifest['camera']['settings'])
        loaded.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        hidden = torch.randn(2, 40, 12)
        record = record_for(3)
        batch = {'aux_camera_positions': torch.arange(16).repeat(2, 1) + 3,
                 'aux_camera_target': torch.tensor([record['camera']] * 2, dtype=torch.float32),
                 'aux_camera_mask': torch.ones(2, 16, dtype=torch.bool),
                 'aux_camera_scale': torch.tensor([record['trajectory_scale']] * 2, dtype=torch.float32)}
        self.assertTrue(torch.equal(heads.camera.loss(hidden, batch), loaded.camera.loss(hidden, batch)))


class FeatureLayerTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(23)
        torch.set_num_threads(1)

    def camera_batch(self, tokenizer):
        row, batch = video_row(tokenizer, camera=record_for(0))
        return collate_rows([add_to_batch(batch, row, tokenizer)], 0)

    def test_settings_pin_the_layers_and_their_convention(self):
        defaults = camera_config.normalize({})
        self.assertIsNone(defaults['feature_layers'])  # Cambrian-P: the final-norm states at the carriers
        self.assertEqual(defaults['feature_layer_convention'], 'hidden_states_index_k_after_k_layers_last_is_final_norm_v1')
        for bad in ([], [3, 2], [2, 2], [0], [1.5], 'final', list(range(1, 18))):
            with self.assertRaises(ValueError, msg=str(bad)):
                camera_config.normalize({'feature_layers': bad})
        with self.assertRaises(ValueError):
            camera_config.normalize({'feature_layer_convention': 'other'})
        with self.assertRaisesRegex(ValueError, 'depth'):
            attach(Toy(layers=LAYERS), None, ToyTokenizer(), cam_cfg(feature_layers=[3, 5]))

    def test_hooks_capture_exactly_the_chosen_layers_and_the_mix_learns(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=6)
        heads = attach(model, None, tokenizer, cam_cfg(feature_layers=[2, 4, 6]))  # 6 = the final norm here
        self.assertTrue(torch.equal(heads.camera.layer_logits.softmax(0), torch.full((3,), 1 / 3)))
        batch = self.camera_batch(tokenizer)
        recorded, original = {}, heads.camera.mix

        def mix(layer_states):
            recorded.update(layer_states)
            return original(layer_states)
        heads.camera.mix = mix
        row_losses(model, batch).sum().backward()
        self.assertEqual(sorted(recorded), [2, 4, 6])
        for k in (2, 4, 6):
            self.assertEqual(recorded[k].shape, (1, 16, 12))
        for k in (2, 4):
            self.assertFalse(torch.allclose(recorded[k], recorded[6]))
        self.assertGreater(heads.camera.layer_logits.grad.abs().sum().item(), 0)
        for layer in model.language_model.layers:
            self.assertEqual(len(layer._forward_hooks), 0)
        self.assertEqual(len(model.language_model.norm._forward_hooks), 0)

    def test_captured_states_equal_the_layer_outputs_at_the_carriers(self):
        tokenizer = ToyTokenizer()
        model = Toy(layers=4)
        heads = attach(model, None, tokenizer, cam_cfg(feature_layers=[1, 3]))
        batch = self.camera_batch(tokenizer)
        recorded, original = {}, heads.camera.mix
        heads.camera.mix = lambda states: (recorded.update({k: v.detach() for k, v in states.items()}), original(states))[1]
        outputs = {}
        hooks = [model.language_model.layers[i].register_forward_hook(lambda m, a, out, i=i: outputs.setdefault(i, out.detach()))
                 for i in (0, 2)]
        row_losses(model, batch)
        for hook in hooks:
            hook.remove()
        positions = batch['aux_camera_positions'][0]
        self.assertTrue(torch.equal(recorded[1][0], outputs[0][0, positions]))
        self.assertTrue(torch.equal(recorded[3][0], outputs[2][0, positions]))

    def test_gradient_checkpointing_matches_plain_layers(self):
        from torch.utils.checkpoint import set_checkpoint_early_stop
        tokenizer = ToyTokenizer()
        batch = self.camera_batch(tokenizer)
        plain = Toy(layers=4)
        attach(plain, None, tokenizer, cam_cfg(feature_layers=[2, 3]))
        reference = row_losses(plain, batch)
        reference.sum().backward()
        # Early stop on (torch's default) and off (the whole layer, hooks included, re-runs in backward).
        for early_stop, recomputed in ((True, False), (False, True)):
            checkpointed = Toy(layers=4, checkpoint=True)
            attach(checkpointed, None, tokenizer, cam_cfg(feature_layers=[2, 3]))
            checkpointed.load_state_dict(plain.state_dict())
            calls = []
            checkpointed.language_model.layers[1].register_forward_hook(lambda *a: calls.append(1))
            with set_checkpoint_early_stop(early_stop):
                losses = row_losses(checkpointed, batch)
                losses.sum().backward()
            self.assertEqual(len(calls), 2 if recomputed else 1)
            self.assertTrue(torch.allclose(losses, reference))
            for (name, p), q in zip(plain.named_parameters(), checkpointed.parameters()):
                self.assertTrue(torch.allclose(p.grad, q.grad, atol=1e-6), (early_stop, name))


class MultiNodeTests(unittest.TestCase):
    def test_exact_microbatch_ranks_match_one_process(self):
        torch.manual_seed(5)
        tokenizer = ToyTokenizer()
        rows = []
        for index in range(8):
            record = record_for(index % 3, None if index % 4 else np.zeros(32, bool))
            row, batch = video_row(tokenizer, qid=f'r{index}', target=f'There are {index} chairs.', camera=record)
            rows.append(add_to_batch(batch, row, tokenizer))
        model = Toy(layers=LAYERS)
        attach(model, None, tokenizer, cam_cfg())
        replicas = [copy.deepcopy(model) for _ in range(4)]
        window = next(global_batches(8, 0, 8, 17))
        losses = backward_batch(model, collate_rows([rows[i] for i in window['indices']], 0), [1.0] * 8, 1, 8)
        total = 0.0
        for rank, replica in enumerate(replicas):
            slots = rank_slots(window['indices'], rank, 4, 2)
            local = backward_batch(replica, collate_rows([rows[i] for i, _ in slots], 0), [w for _, w in slots], 4, 8)
            total += local.sum().item()
            for name, parameter in replica.named_parameters():
                self.assertIsNotNone(parameter.grad, (rank, name))
        self.assertAlmostEqual(total, losses.sum().item(), places=5)
        for name, parameter in model.named_parameters():
            reduced = torch.stack([dict(r.named_parameters())[name].grad for r in replicas]).mean(dim=0)
            self.assertTrue(torch.allclose(reduced, parameter.grad, atol=1e-6, rtol=1e-4), name)


class TrainerPathTests(unittest.TestCase):
    """Camera-only configs through the trainer's own encode_microbatch and memory_probe call sites."""

    def setUp(self):
        torch.manual_seed(11)
        torch.set_num_threads(1)
        self.tokenizer = ToyTokenizer()
        self.processor = types_namespace(tokenizer=self.tokenizer)
        records = [record_for(0), record_for(0, np.zeros(32, bool))]
        targets_text = ['There are 4 chairs.', 'There are 2 chairs in this long room, near the door.']
        self.rows, self.encoded, self.audits = [], {}, {}
        for index, (record, target) in enumerate(zip(records, targets_text)):
            row, batch = video_row(self.tokenizer, target=target, qid=f'r{index}', camera=record)
            self.rows.append(row)
            self.encoded[row['qid']] = batch
            # The unsupervised row is the longest, so it is a memory-probe stress row too.
            self.audits[row['qid']] = {'qid': row['qid'], 'sequence_tokens': 100 + index, 'visual_tokens': 64,
                                       'assistant_tokens_including_eos': 10 - index}

    def fake_encoding(self):
        def encode_training(processor, row):
            return {k: v.clone() for k, v in self.encoded[row['qid']].items()}, self.audits[row['qid']]
        return patch.dict(sys.modules, {'student_pilot.diagnostic_data': types_namespace(encode_training=encode_training)})

    def test_encode_microbatch_inserts_carriers_and_trains_the_camera_head(self):
        from student_pilot import ddp_training
        with self.fake_encoding():
            batch = ddp_training.encode_microbatch(self.processor, self.rows, self.audits, [0, 1])
        self.assertTrue(bool((batch['aux_camera_positions'][0] >= 0).all()))
        self.assertEqual(batch['aux_camera_positions'][1].tolist(), [-1] * 16)
        self.assertEqual(int((batch['input_ids'][0] == CARRIER).sum()), 16)
        model = Toy(layers=LAYERS)
        heads = attach(model, None, self.tokenizer, cam_cfg())
        losses = row_losses(model, batch)
        self.assertTrue(torch.isfinite(losses).all())
        self.assertGreater(float(heads.last_terms['camera'][0]), 0)
        self.assertEqual(float(heads.last_terms['camera'][1]), 0)

    def test_memory_probe_stress_rows_carry_carriers_and_run_the_camera_loss(self):
        from student_pilot import ddp_training, students
        model = Toy(layers=LAYERS)
        heads = attach(model, None, self.tokenizer, cam_cfg())
        seen = []

        def probe_candidate(model, parameters, cpu_rows, size, pad_token_id, memory_fraction, memory_fit_safety_factor=1.15):
            batch = collate_rows(cpu_rows, pad_token_id)
            row_losses(model, batch).sum().backward()
            seen.append((batch, {k: v.clone() for k, v in heads.last_terms.items()}))
            model.zero_grad(set_to_none=True)
            return {'microbatch': size, 'fits': True, 'seconds': 1.0}
        settings = {'memory_fraction': 0.9, 'max_microbatch_size': 2, 'effective_batch_size': 2, 'world_size': 1,
                    'parallel': 'ddp', 'memory_fit_safety_factor': 1.15}
        with self.fake_encoding(), patch.object(ddp_training, 'probe_candidate', probe_candidate), \
                patch.object(students, 'student_for_model', lambda model: 'qwen35'):
            report = ddp_training.memory_probe(model, self.processor, self.rows, self.audits, settings, 0, lambda: None)
        self.assertEqual(sorted(report['stress_qids']), ['r0', 'r1'])
        self.assertTrue(seen)
        for batch, terms in seen:
            self.assertTrue(bool((batch['aux_camera_positions'] >= 0).all()))
            self.assertEqual(int((batch['input_ids'] == CARRIER).sum()), 16 * batch['input_ids'].shape[0])
            self.assertTrue(bool((terms['camera'] > 0).all()))


def types_namespace(**values):
    from types import SimpleNamespace
    return SimpleNamespace(**values)


class ProtocolTests(unittest.TestCase):
    def test_camera_settings_stay_out_of_the_training_settings(self):
        from student_pilot import ddp_config
        from student_pilot.provisional_data import training_protocol_fields
        with kept_directory() as root:
            config = {'world_size': 32, 'camera': {'weight': 0.2, 'supervision': PIN}, 'checkpoint_every_steps': 50}
            path = root / 'training.json'
            path.write_text(json.dumps(config))
            fields = training_protocol_fields(path, 'qwen35')
        plain = ddp_config.normalize_training_config({'world_size': 32}, 'qwen35')
        self.assertEqual(fields['training'], plain)
        self.assertNotIn('camera', json.dumps(fields['training']))
        self.assertEqual(fields['camera'], camera_config.normalize(config['camera']))
        self.assertEqual(ddp_config.validate_camera_protocol(fields), fields['camera'])
        tampered = {**fields, 'camera': {**fields['camera'], 'weight': 0.5}}
        with self.assertRaisesRegex(ValueError, 'hash'):
            ddp_config.validate_camera_protocol(tampered)
        self.assertIsNone(ddp_config.validate_camera_protocol({}))


if __name__ == '__main__':
    unittest.main()
