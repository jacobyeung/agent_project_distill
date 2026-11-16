"""Pose + point-depth head arms: one test class per defect of the pre-GPU review (REVIEW.md IDs)."""
import copy
import hashlib
import io
import json
import math
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

from tests.auxiliary_toys import ToyTokenizer, install_runner

runner = install_runner()
from student_pilot import adapters  # noqa: E402
from student_pilot import camera_config  # noqa: E402
from student_pilot import camera_targets as targets  # noqa: E402
from student_pilot import compact_label_bank as bank_mod  # noqa: E402
from student_pilot import gate_eval  # noqa: E402
from student_pilot import head_api  # noqa: E402
from student_pilot import point_depth_head as pdh  # noqa: E402
from student_pilot.auxiliary_losses import attach, capture_camera_states, visual_grids  # noqa: E402
from student_pilot.auxiliary_targets import add_to_batch  # noqa: E402
from student_pilot.ddp_core import build_optimizer, collate_rows, row_losses  # noqa: E402
from tests.pd_toys import ToyVLM, ToyVisionBlock, video_row  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PIN = {'path': '/fixture/bank.npz', 'sha256': '0' * 64}
SMALL_DEPTH = {'weight': 0.5, 'd_proj': 16, 'mlp_hidden': 16, 'num_heads': 2, 'context_depth': 1, 'vit_layers': [1, 2, 4],
               'num_points_per_frame': 8}
SMOKE_BANK = Path('/scratch/jjyeung/pd_build2/label_bank_smoke20_v2.npz')
SMOKE_BANK_SHA256 = '87bf2a90e09c2c977996dec4a9930dae270eac0e711c9eda8b4391e480aa6c6b'


def cfg(depth=True, **extra):
    value = {'weight': 1.0, 'weight_gravity': 0.5, 'weight_scale': 0.2, 'embed_dim': 16, 'num_heads': 2, 'trunk_depth': 2,
             'refine_iterations': 2, 'supervision': PIN, **extra}
    if depth:
        value['point_depth'] = dict(SMALL_DEPTH)
    return camera_config.normalize(value)


def rotation(axis, angle):
    axis = np.asarray(axis, dtype=np.float64) / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


def trajectory(seed=0):
    rng = np.random.default_rng(seed)
    poses = np.repeat(np.eye(4)[None], 32, axis=0)
    for i in range(32):
        # A camera looking roughly horizontally (OpenCV: +z forward, +y down) in a z-up world, panning and pitching.
        level = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])  # columns: camera x->world x, y->world -z (down), z->world y
        poses[i, :3, :3] = rotation([0, 0, 1], 0.07 * i + 0.4 * seed) @ rotation([1, 0, 0], 0.15 + 0.01 * i) @ level
        poses[i, :3, 3] = [0.12 * i + seed, 1.0 + 0.05 * i, 1.4 + 0.01 * i] + rng.normal(0, 0.01, 3)
    intrinsics = np.repeat(np.array([[500.0, 0, 320], [0, 520.0, 240], [0, 0, 1]])[None], 32, axis=0)
    return poses, intrinsics


def record(seed=0, points=8):
    poses, intrinsics = trajectory(seed)
    camera, mask, scale = targets.encode_cameras(poses, intrinsics, (480, 640))
    gravity, ok = targets.encode_gravity(poses)
    rng = np.random.default_rng(seed + 100)
    return {'camera': camera.tolist(), 'camera_mask': mask.tolist(), 'trajectory_scale': scale, 'lm_weight': 1.0,
            'gravity': gravity.tolist(), 'gravity_mask': bool(ok),
            'point_depth': {'uv': rng.uniform(50, 950, (16, points, 2)).tolist(),
                            'depth': rng.uniform(1.0, 4.0, (16, points)).tolist(),
                            'mask': np.ones((16, points), bool).tolist()}}


def encoded(tokenizer, rows):
    return collate_rows([add_to_batch(batch, row, tokenizer) for row, batch in rows], 0)


def toy_heads(seed=7, **extra):
    torch.manual_seed(seed)
    tokenizer = ToyTokenizer()
    model = ToyVLM()
    heads = attach(model, None, tokenizer, cfg(**extra))
    return tokenizer, model, heads


def output_dir():
    root = Path(os.environ.get('LANE_TEST_OUTPUT') or tempfile.gettempdir())
    return Path(tempfile.mkdtemp(prefix='pd_heads_', dir=root))


def merged_output(output):
    """Qwen3.5 vision towers return the merged tokens directly (transformers 5.3) or as pooler_output (5.12)."""
    return output.pooler_output if hasattr(output, 'pooler_output') else output


# ----------------------------------------------------------------------------------------------- C3
class VisionMasterWeightTests(unittest.TestCase):
    """C3: the unfrozen vision blocks train as FP32 masters at 2e-6; the export is a BF16 cast."""

    def model(self, depth=3, dim=32):
        torch.manual_seed(3)
        model = nn.Module()
        model.model = nn.Module()
        model.model.visual = nn.Module()
        model.model.visual.blocks = nn.ModuleList([ToyVisionBlock(dim) for _ in range(depth)])
        with torch.no_grad():
            for name, parameter in model.named_parameters():
                if 'norm' in name and name.endswith('weight'):
                    parameter.fill_(1.0)
                else:
                    parameter.normal_(0, 0.03)
        model.config = type('C', (), {'vision_config': type('V', (), {'depth': depth})()})()
        return model.to(torch.bfloat16)

    def forward(self, model, x):
        for block in model.model.visual.blocks:
            x = block(x)
        return x

    def step(self, model, master, seed=0):
        params = adapters.unfreeze_vision_blocks(model) if master else [
            (n, p.requires_grad_(True)) for n, p in adapters.discover_vision_block_parameters(model)]
        groups = {'vision_blocks': params}
        optimizer = build_optimizer(groups, None, {'unfreeze_vision_blocks': True, 'vision_learning_rate': 2e-6,
                                                   'learning_rate': 2.83e-4, 'weight_decay': 0.0, 'betas': [0.9, 0.999]})
        before = {n: p.detach().double().clone() for n, p in params}
        x = torch.randn(64, 32, generator=torch.Generator().manual_seed(seed)).to(torch.bfloat16)
        with torch.autocast('cpu', dtype=torch.bfloat16):
            loss = self.forward(model, x).float().pow(2).mean()
        loss.backward()
        optimizer.step()
        return params, before, optimizer

    def test_one_step_moves_every_element_by_the_learning_rate(self):
        model = self.model()
        params, before, optimizer = self.step(model, master=True)
        self.assertEqual([g['group_name'] for g in optimizer.param_groups], ['adapter', 'vision_blocks'])
        self.assertEqual(optimizer.param_groups[1]['lr'], 2e-6)
        moved = total = 0
        for name, parameter in params:
            self.assertEqual(parameter.dtype, torch.float32, name)
            delta = (parameter.detach().double() - before[name]).abs()
            graded = parameter.grad.abs() > 1e-6
            # AdamW's first step moves every element with a nonzero gradient by lr * g / (|g| + eps) ~ lr.
            close = (delta - 2e-6).abs() <= 2e-6 * 0.02
            moved += int((close | ~graded).sum())
            total += delta.numel()
            if 'norm' in name and name.endswith('weight'):
                self.assertTrue(bool(close[graded].all()), name)  # LayerNorm weights at 1.0 move too
        self.assertGreater(moved / total, 0.999)

    def test_bf16_parameters_would_not_move(self):
        """The defect this fixes: in-place BF16 updates at 2e-6 round away (BF16's spacing near 0.03 is ~1e-4)."""
        model = self.model()
        params, before, _ = self.step(model, master=False)
        changed = sum(int((p.detach().double() != before[n]).sum()) for n, p in params)
        total = sum(p.numel() for _, p in params)
        self.assertLess(changed / total, 0.1)
        norms = [(p.detach().double() != before[n]).any() for n, p in params if 'norm' in n and n.endswith('weight')]
        self.assertFalse(any(norms))

    def test_step0_forward_is_unchanged_under_autocast(self):
        model = self.model()
        x = torch.randn(16, 32).to(torch.bfloat16)
        with torch.no_grad(), torch.autocast('cpu', dtype=torch.bfloat16):
            reference = self.forward(model, x)
            adapters.unfreeze_vision_blocks(model)
            masters = self.forward(model, x)
        self.assertTrue(torch.equal(reference, masters))

    def test_hundred_steps_track_an_fp64_reference(self):
        model, reference = self.model(), self.model()
        params = adapters.unfreeze_vision_blocks(model)
        ref_params = [(n, p.detach().double().clone().requires_grad_(True)) for n, p in
                      adapters.discover_vision_block_parameters(reference)]
        opt = torch.optim.AdamW([p for _, p in params], lr=2e-6, weight_decay=0.0, foreach=False)
        ref_opt = torch.optim.AdamW([p for _, p in ref_params], lr=2e-6, weight_decay=0.0, foreach=False)
        start = {n: p.detach().double().clone() for n, p in params}
        generator = torch.Generator().manual_seed(1)
        for _ in range(100):
            for (_, p), (_, q) in zip(params, ref_params):
                g = torch.randn(p.shape, generator=generator, dtype=torch.float64)
                p.grad, q.grad = g.float(), g
            opt.step()
            ref_opt.step()
        for (name, p), (_, q) in zip(params, ref_params):
            update, expected = p.detach().double() - start[name], q.detach() - start[name]
            self.assertLess(float((update - expected).norm() / expected.norm()), 0.02, name)

    def test_export_is_a_bf16_cast_that_the_evaluator_loads(self):
        model = self.model()
        params, _, _ = self.step(model, master=True)
        path = output_dir() / 'vision_blocks.safetensors'
        saved = adapters.save_vision_blocks(model, path)
        for name, parameter in params:
            tensor = saved[adapters.canonical_vision_block_name(name)]
            self.assertEqual(tensor.dtype, torch.bfloat16)
            self.assertTrue(torch.equal(tensor, parameter.detach().to(torch.bfloat16)))
        evaluator = self.model()
        report = adapters.load_vision_blocks(evaluator, path)
        self.assertTrue(report['vision_blocks_exact_equality'])

    def test_raw_checkpoint_scoring_drops_heads_and_casts_masters(self):
        """L2: adapters.pt carries head tensors and FP32 vision masters; scoring filters the heads, uses BF16."""
        from student_pilot.orchard_eval import generate
        model = self.model()
        params = adapters.unfreeze_vision_blocks(model)
        directory = output_dir()
        saved = {name: p.detach().clone() for name, p in params}
        saved['auxiliary_heads.camera.tokens'] = torch.zeros(2, 4)
        torch.save(saved, directory / 'adapters.pt')
        fresh = self.model()

        def attach_ddp(m, training):
            adapters.unfreeze_vision_blocks(m)
            return m, {'targets': {}}
        with patch('student_pilot.adapters.attach_ddp_adapters', side_effect=attach_ddp), \
                patch('student_pilot.adapters.trainable_groups',
                      side_effect=lambda m, t: {'vision_blocks': adapters.discover_vision_block_parameters(m)}), \
                patch.object(generate, 'verify_pin', return_value=None):
            loaded = generate.load_checkpoint_adapters(fresh, directory, {'training': {}, 'weights': {}})
        for name, parameter in adapters.discover_vision_block_parameters(loaded):
            self.assertEqual(parameter.dtype, torch.bfloat16)
            self.assertTrue(torch.equal(parameter, saved[name].to(torch.bfloat16)))


    def test_real_qwen35_vision_tower_with_fp32_masters(self):
        """The HF Qwen3.5 vision blocks run unchanged with FP32 masters under autocast and train them in FP32."""
        try:
            from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
            from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        except ImportError:
            self.skipTest('transformers 5.12 is not installed')
        config = Qwen3_5VisionConfig(depth=3, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=48,
                                     patch_size=4, temporal_patch_size=2, spatial_merge_size=2, in_channels=3,
                                     num_position_embeddings=64)
        config._attn_implementation = 'sdpa'
        torch.manual_seed(0)
        tower = Qwen3_5VisionModel(config).to(torch.bfloat16)
        grid = torch.tensor([[2, 4, 6]])
        pixels = torch.randn(2 * 4 * 6, 3 * 2 * 4 * 4)
        with torch.no_grad(), torch.autocast('cpu', dtype=torch.bfloat16):
            reference = merged_output(tower(pixels, grid_thw=grid))
        holder = nn.Module()
        holder.model = nn.Module()
        holder.model.visual = tower
        holder.config = type('C', (), {'vision_config': config})()
        params = adapters.unfreeze_vision_blocks(holder)
        self.assertEqual(len(params), 3 * len(adapters.VISION_BLOCK_SUFFIXES))
        with torch.autocast('cpu', dtype=torch.bfloat16):
            output = merged_output(tower(pixels, grid_thw=grid))
        self.assertEqual(output.dtype, torch.bfloat16)
        self.assertTrue(torch.equal(output.detach(), reference))
        output.float().pow(2).mean().backward()
        for name, parameter in params:
            self.assertEqual((parameter.dtype, parameter.grad.dtype), (torch.float32, torch.float32), name)
            self.assertGreater(float(parameter.grad.abs().sum()), 0, name)


# ----------------------------------------------------------------------------------------------- C1, M2, M3, L1
class LabelBankTests(unittest.TestCase):
    """C1: depth labels come only from first-hit raycasts; nothing is synthesized; rows join by tokens and frames."""

    def scene_assets(self, root, dataset, scene, seed, first_hits=True, calibration=True, receipt_scene=None, gravity_up=True):
        poses, intrinsics = trajectory(seed)
        directory = root / f'{dataset}__{scene}'
        directory.mkdir(parents=True)
        indices = list(range(seed, seed + 32 * 7, 7))
        cal_path = directory / 'official_cameras.npz'
        if calibration:
            np.savez(cal_path, camera_poses=poses.astype(np.float32), intrinsics=intrinsics.astype(np.float32),
                     indices=np.array(indices), raster_hw=np.array([480, 640]))
        receipt = {'dataset': dataset, 'scene_name': receipt_scene or scene, 'gravity_up': [0, 0, 1],
                   'coordinate_frame': 'source_world_meters_opencv_camera_to_world', 'calibration': {'path': str(cal_path)}}
        if not gravity_up:
            del receipt['gravity_up']  # L1: the receipt's gravity_up is read, never assumed
        (directory / 'scene_receipt.json').write_text(json.dumps(receipt))
        fh_path = directory / 'FIRST_HITS.npz'
        if first_hits:
            rows, cols = np.meshgrid(np.arange(24), np.arange(32), indexing='ij')
            depth = np.stack([1.0 + 0.1 * f + 0.01 * rows + 0.0 * cols for f in range(32)])
            face = np.ones_like(depth, dtype=np.int64)
            face[:, :4, :] = -1  # misses in the top rows
            np.savez(fh_path, depth=depth, face_index=face)
        return {'dataset': dataset, 'scene': scene, 'receipt_path': str(directory / 'scene_receipt.json'),
                'calibration_path': None, 'first_hits_path': str(fh_path) if first_hits else None}, indices, poses

    def build(self, root):
        from tools import label_bank_build as builder
        entries, frames, poses = [], {}, {}
        for dataset, scene, seed, kwargs in (('scannet', 'scene0001_00', 0, {}),
                                             ('scannetppv2', 'abcdef0123', 1, {'first_hits': False}),
                                             ('scannet', 'scene0002_00', 2, {'receipt_scene': 'scene0009_00'}),
                                             ('scannet', 'scene0003_00', 3, {'calibration': False}),
                                             ('scannet', 'scene0004_00', 4, {'gravity_up': False})):
            entry, frames[scene], poses[scene] = self.scene_assets(root, dataset, scene, seed, **kwargs)
            entries.append(entry)
        manifest = builder.build(entries, root / 'bank.npz', num_points=8, seed=17)
        return builder, manifest, frames, poses

    def test_builder_reads_first_hits_and_defers_instead_of_inventing(self):
        root = output_dir()
        builder, manifest, frames, poses = self.build(root)
        self.assertEqual(manifest['num_scenes'], 2)
        self.assertEqual(sorted(d['reason'] for d in manifest['deferred']),
                         ['calibration missing', 'receipt gravity_up missing', 'receipt names another scene'])
        bank = bank_mod.read_bank(root / 'bank.npz')
        self.assertEqual(bank['depth_source'].tolist(), ['first_hits', 'none'])
        self.assertFalse(bank['point_depth_mask'][1].any())  # no FIRST_HITS: pose labels only
        self.assertTrue(bank['camera_mask'][1].all())
        self.assertEqual(bank['dataset_tokens'].tolist(), ['d1', 'd2'])
        self.assertEqual(bank['scene_tokens'][0], 'v' + hashlib.sha256(b'rung1 scene scannet/scene0001_00').hexdigest()[:12])
        self.assertEqual(bank['frame_indices'][0].tolist(), frames['scene0001_00'])
        # Depth comes from anchor frame 2g+1 of the raster (depth = 1 + 0.1 f + 0.01 row), never a miss row.
        uv, gt, mask = (bank[k][0].astype(np.float64) for k in ('point_depth_uv', 'point_depth_gt', 'point_depth_mask'))
        for g in range(16):
            rows = uv[g, :, 1] / 1000 * 24 - 0.5
            expected = 1.0 + 0.1 * (2 * g + 1) + 0.01 * rows
            np.testing.assert_allclose(gt[g], expected, atol=6e-3)
            self.assertTrue((rows >= 3.6).all())
        # Poses: frame 0 is the origin, group g describes frame 2g+1 (independent recomputation).
        p = poses['scene0001_00'].astype(np.float32).astype(np.float64)
        for g in range(16):
            relative = np.linalg.inv(p[2 * g + 1]) @ p[0]
            np.testing.assert_allclose(bank['camera'][0, g, :3], relative[:3, 3], atol=1e-4)
        np.testing.assert_allclose(bank['gravity'][0], p[0, :3, :3].T @ [0, 0, 1], atol=1e-5)
        recorded = {s['scene']: s for s in json.loads((root / 'bank.manifest.json').read_text())['scenes']}
        self.assertEqual(recorded['scannet/scene0001_00']['depth']['sha256'],
                         builder.sha256_file(root / 'scannet__scene0001_00' / 'FIRST_HITS.npz'))
        self.assertFalse(any(re.search('scan' 'net', str(v)) for v in bank['scene_tokens'].tolist() + bank['dataset_tokens'].tolist()))

    def test_bank_refuses_other_schemas_and_depth_sources(self):
        root = output_dir()
        self.build(root)
        good = dict(np.load(root / 'bank.npz'))
        for change, message in (({'schema': np.array('student_pilot/compact_label_bank/v1')}, 'schema'),
                                ({'depth_source': np.array(['stage_layout_depth', 'none'])}, 'first-hit'),
                                ({'origin_frame': np.array(1)}, 'origin'),
                                ({'point_depth_mask': np.ones_like(good['point_depth_mask'])}, 'without a first-hit')):
            path = root / f'bad_{len(message)}_{message[:3]}.npz'
            np.savez(path, **{**good, **change})
            with self.assertRaisesRegex(ValueError, message):
                bank_mod.read_bank(path)
        legacy = root / 'legacy.npz'
        np.savez(legacy, schema=np.array('student_pilot/compact_label_bank/v1'), camera_16=np.zeros((1, 16, 9)))
        with self.assertRaisesRegex(ValueError, 'schema v2'):
            bank_mod.read_bank(legacy)

    def test_rows_join_by_tokens_and_their_own_frame_set(self):
        root = output_dir()
        _, _, frames, _ = self.build(root)
        bank = bank_mod.read_bank(root / 'bank.npz')
        token = str(bank['scene_tokens'][0])
        good = {'qid': 'a', 'dataset': 'd1', 'scene': token, 'student_input': {'frame_indices': frames['scene0001_00']}}
        shifted = {**good, 'qid': 'b', 'student_input': {'frame_indices': [f + 1 for f in frames['scene0001_00']]}}
        missing = {**good, 'qid': 'c', 'student_input': {}}
        other = {**good, 'qid': 'd', 'scene': 'v000000000000'}
        config = cfg()
        records, audit = bank_mod.load_bank_for_rows(root / 'bank.npz', [good, shifted, missing, other], config)
        self.assertEqual([any(r['camera_mask']) for r in records], [True, False, False, False])
        self.assertTrue(np.asarray(records[0]['point_depth']['mask']).any())
        self.assertEqual(np.asarray(records[0]['point_depth']['uv']).shape, (16, 8, 2))
        self.assertEqual((audit['frame_set_mismatch'], audit['frame_set_missing'], audit['scene_not_in_bank']), (1, 1, 1))
        self.assertEqual((audit['pose_rows'], audit['depth_rows'], audit['scenes_used']), (1, 1, 1))
        with self.assertRaisesRegex(ValueError, 'pose-only'):
            bank_mod.load_bank_for_rows(root / 'bank.npz', [{**other, 'category': targets.POSE_ONLY_CATEGORY}], config)

    @unittest.skipUnless(SMOKE_BANK.is_file(), 'the pinned smoke bank lives on trinity-0-13')
    def test_pinned_smoke_bank(self):
        digest = hashlib.sha256(SMOKE_BANK.read_bytes()).hexdigest()
        self.assertEqual(digest, SMOKE_BANK_SHA256)
        bank = bank_mod.read_bank(SMOKE_BANK)
        self.assertEqual(len(bank['scene_tokens']), 20)
        self.assertEqual(set(bank['depth_source'].tolist()), {'first_hits'})
        self.assertEqual(int(bank['point_depth_mask'].sum()), 20 * 16 * 64)
        self.assertEqual(int(bank['camera_mask'].sum()), 320)


# ----------------------------------------------------------------------------------------------- H1, M6
class DepthInputTests(unittest.TestCase):
    """H1: the depth head reads the full per-row grids, and ViT tokens are restored to raster order."""

    def test_vit_order_matches_the_qwen_video_processor(self):
        """Patches packed by the real Qwen3-VL video processor land on their raster cell (both transformers pins)."""
        try:
            from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        except ImportError:
            self.skipTest('transformers with Qwen3-VL is not installed')
        processor = Qwen3VLVideoProcessor(patch_size=4, temporal_patch_size=2, merge_size=2,
                                          size={'shortest_edge': 16 * 24, 'longest_edge': 16 * 24 * 4})
        frames, height, width = 4, 16, 24
        video = torch.zeros(frames, 3, height, width)
        video[:, 0] = torch.arange(height)[:, None].float()
        video[:, 1] = torch.arange(width)[None, :].float()
        video[:, 2] = torch.arange(frames)[:, None, None].float()
        packed = processor(videos=[video], do_resize=False, do_rescale=False, do_normalize=False, do_sample_frames=False,
                           return_tensors='pt')
        grid = packed['video_grid_thw']
        self.assertEqual(grid.tolist(), [[2, 4, 6]])
        # Each packed row is [channel, temporal, patch, patch]; its channel means give the patch's row, column, time.
        patches = packed['pixel_values_videos'].reshape(-1, 3, 2 * 4 * 4).mean(dim=-1)
        restored = pdh.vit_grids_by_row(patches, grid, 2)[0]
        for t in range(2):
            for i in range(4):
                for j in range(6):
                    self.assertEqual(restored[t, i, j].tolist(), [4 * i + 1.5, 4 * j + 1.5, 2 * t + 0.5])

    def test_vit_order_matches_qwen_rotary_positions(self):
        try:
            from transformers.vision_utils import get_vision_position_ids
        except ImportError:
            self.skipTest('transformers.vision_utils arrived after 5.3; the processor test covers the order there')
        grids = torch.tensor([[16, 4, 6], [16, 6, 4]])
        positions = get_vision_position_ids(grids, 2).float()
        t_index = torch.cat([torch.arange(t).repeat_interleave(h * w) for t, h, w in grids.tolist()]).float()
        restored = pdh.vit_grids_by_row(torch.cat((positions, t_index[:, None]), dim=1), grids, 2)
        for (t, h, w), grid in zip(grids.tolist(), restored):
            self.assertEqual(tuple(grid.shape), (t, h, w, 3))
            rows, cols = torch.meshgrid(torch.arange(h), torch.arange(w), indexing='ij')
            expected = torch.stack((rows.float(), cols.float()), dim=-1)
            for frame in range(t):
                self.assertTrue(torch.equal(grid[frame, ..., :2], expected))
                self.assertTrue(torch.all(grid[frame, ..., 2] == frame))

    def test_point_queries_land_on_their_patch(self):
        height, width = 6, 8
        fmap = torch.eye(height * width).reshape(height * width, height, width)[None]
        uv = torch.tensor([[[(j + 0.5) / width * 1000, (i + 0.5) / height * 1000] for i in range(height) for j in range(width)]])
        centre = pdh.sample_points(fmap, uv)[0, :, 0]
        self.assertTrue(torch.allclose(centre, torch.eye(height * width), atol=1e-6))
        corner = pdh.sample_points(fmap, torch.tensor([[[2 / width * 1000, 3 / height * 1000]]]))[0, 0, 0]
        cells = {(i, j) for i in (2, 3) for j in (1, 2)}
        for index in range(height * width):
            expected = 0.25 if divmod(index, width) in cells else 0.0
            self.assertAlmostEqual(float(corner[index]), expected, places=6)

    def test_training_capture_feeds_full_grids(self):
        tokenizer, model, heads = toy_heads()
        rows = [video_row(tokenizer, 4, 6, seed=0), video_row(tokenizer, 6, 4, seed=1)]
        rows = [({**row, '_camera': record(i)}, batch) for i, (row, batch) in enumerate(rows)]
        batch = encoded(tokenizer, rows)
        seen, block_out, norm_out = {}, {}, []
        original = heads.camera.depth_loss

        def spy(targets_, present, last_pose, grids, vit, size):
            seen.update(grids=grids, vit=vit)
            return original(targets_, present, last_pose, grids, vit, size)
        heads.camera.depth_loss = spy
        hooks = [model.visual.blocks[k - 1].register_forward_hook(lambda m, a, o, k=k: (block_out.setdefault(k, o.detach()), None)[1])
                 for k in (1, 2, 4)]
        hooks.append(model.language_model.norm.register_forward_hook(lambda m, a, o: norm_out.append(o.detach())))
        losses = row_losses(model, batch)
        for hook in hooks:
            hook.remove()
        self.assertTrue(torch.isfinite(losses).all())
        offsets = [0, 16 * 4 * 6]
        for row, (h, w) in enumerate(((4, 6), (6, 4))):
            grid = seen['grids'][row]
            self.assertEqual(tuple(grid.shape), (16, h // 2, w // 2, 24))
            positions = torch.where(batch['input_ids'][row] == model.config.video_token_id)[0]
            self.assertTrue(torch.equal(grid.detach(), norm_out[0][row, positions].reshape(16, h // 2, w // 2, 24)))
            for layer, k in enumerate((1, 2, 4)):
                vit = seen['vit'][row][layer]
                self.assertEqual(tuple(vit.shape), (16, h, w, 8))
                for t, i, j in ((0, 0, 0), (3, h - 1, 1), (15, 2, w - 1)):
                    packed = offsets[row] + t * h * w + ((i // 2) * (w // 2) + j // 2) * 4 + (i % 2) * 2 + (j % 2)
                    self.assertTrue(torch.equal(vit[t, i, j].detach(), block_out[k][packed]))
        losses.sum().backward()
        for name, parameter in heads.camera.point_depth.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
        self.assertGreater(float(model.visual.blocks[0].attn.qkv.weight.grad.abs().sum()), 0)

    def test_vit_hooks_under_gradient_checkpointing_match_plain_blocks(self):
        """The ViT hooks keep the first forward's outputs; a checkpointed re-run in backward changes nothing."""
        from torch.utils.checkpoint import set_checkpoint_early_stop
        tokenizer = ToyTokenizer()
        rows = [({**row, '_camera': record(1)}, batch) for row, batch in [video_row(tokenizer, 4, 6, seed=2)]]
        batch = encoded(tokenizer, rows)
        torch.manual_seed(11)
        plain = ToyVLM()
        attach(plain, None, tokenizer, cfg())
        reference = row_losses(plain, batch)
        reference.sum().backward()
        for early_stop in (True, False):
            checkpointed = ToyVLM(checkpoint=True)
            attach(checkpointed, None, tokenizer, cfg())
            checkpointed.load_state_dict(plain.state_dict())
            calls = []
            checkpointed.visual.blocks[1].register_forward_hook(lambda *a: calls.append(1))
            with set_checkpoint_early_stop(early_stop):
                losses = row_losses(checkpointed, batch)
                losses.sum().backward()
            self.assertEqual(len(calls), 1 if early_stop else 2)
            self.assertTrue(torch.allclose(losses, reference))
            for (name, p), q in zip(plain.named_parameters(), checkpointed.parameters()):
                self.assertTrue(torch.allclose(p.grad, q.grad, atol=1e-6), (early_stop, name))

    def test_mismatches_raise_instead_of_falling_back(self):
        with self.assertRaisesRegex(ValueError, 'token count'):
            pdh.vit_grids_by_row(torch.zeros(10, 4), torch.tensor([[16, 4, 6]]), 2)
        head = pdh.PointDepthHead(24, {**SMALL_DEPTH}, vit_dim=8)
        with self.assertRaisesRegex(ValueError, 'ViT grids'):
            head.encode(torch.zeros(16, 2, 3, 24), [torch.zeros(16, 2, 3, 8)] * 3, torch.ones(16, 2))
        with self.assertRaisesRegex(ValueError, 'vision tower width'):
            pdh.PointDepthHead(24, {**SMALL_DEPTH}, vit_dim=None)
        with self.assertRaisesRegex(ValueError, r'\[0, 1000\]'):
            head.query(torch.zeros(16, 16, 4, 6), torch.full((16, 2, 2), 1001.0))

    def test_depth_conditions_on_the_predicted_field_of_view(self):
        """M6: changing the GT field of view in the targets changes nothing in the depth prediction."""
        tokenizer, model, heads = toy_heads()
        row, batch = video_row(tokenizer)
        rec = record(0)
        other = copy.deepcopy(rec)
        for g in range(16):
            other['camera'][g][7:9] = [1.0, 1.4]
        values = []
        for item in (rec, other):
            heads.camera.last_components = {}
            row_losses(model, encoded(tokenizer, [({**row, '_camera': item}, batch)]))
            values.append(heads.camera.last_components['point_depth'])
        self.assertTrue(torch.equal(values[0], values[1]))

    def test_depth_head_fits_a_toy_depth_field(self):
        torch.manual_seed(0)
        head = pdh.PointDepthHead(24, {**SMALL_DEPTH, 'num_points_per_frame': 32}, vit_dim=8)
        llm = torch.randn(16, 3, 4, 24)
        vit = [torch.randn(16, 6, 8, 8) for _ in range(3)]
        fov = torch.full((16, 2), 1.0)
        uv = torch.rand(16, 32, 2) * 1000
        depth = 1.0 + 3.0 * torch.sigmoid(vit[0][:, :, :, :1].permute(0, 3, 1, 2))  # depth readable from the ViT map
        gt = pdh.sample_points(depth, uv)[..., 0, 0]
        mask = torch.ones(16, 32, dtype=torch.bool)
        optimizer = torch.optim.Adam(head.parameters(), lr=3e-3)
        first = None
        for _ in range(150):
            optimizer.zero_grad()
            loss = head.row_loss(head(llm, vit, fov, uv), gt, mask)
            first = float(loss.detach()) if first is None else first
            loss.backward()
            optimizer.step()
        self.assertLess(float(loss), 0.5 * first)


# ----------------------------------------------------------------------------------------------- H6
class CameraConfigTests(unittest.TestCase):
    """H6: configs without a camera block, and arm U's disabled block, pass train()'s startup check."""

    def write(self, value):
        path = output_dir() / 'config.json'
        path.write_text(json.dumps(value))
        return path

    def test_no_camera_and_disabled_camera_give_none(self):
        from student_pilot.ddp_config import camera_protocol_fields, load_camera_config, validate_camera_protocol
        for value in ({}, {'camera': {'weight': 0.0}}, {'unfreeze_vision_blocks': True, 'camera': {'weight': 0.0}}):
            path = self.write(value)
            self.assertIsNone(load_camera_config(path))
            self.assertEqual(camera_protocol_fields(value), {})
            self.assertIsNone(validate_camera_protocol({}))
        enabled = {'camera': {'weight': 1.0, 'supervision': PIN}}
        self.assertEqual(load_camera_config(self.write(enabled)), camera_config.normalize(enabled['camera']))

    def test_train_startup_check_accepts_every_arm(self):
        from student_pilot import ddp_config, ddp_training, provisional_data
        base = {'world_size': 32, 'effective_batch_size': 256, 'seed': 17, 'learning_rate': 2.83e-4}
        arms = {'U_absent': {**base, 'unfreeze_vision_blocks': True},
                'U_weight0': {**base, 'unfreeze_vision_blocks': True, 'camera': {'weight': 0.0}},
                'P': {**base, 'unfreeze_vision_blocks': True, 'camera': {'weight': 1.0, 'supervision': PIN}},
                'none': dict(base)}
        for name, value in arms.items():
            with self.subTest(arm=name):
                path = self.write(value)
                protocol = provisional_data.training_protocol_fields(path, 'qwen35')
                settings = ddp_config.normalize_training_config(protocol['training'], 'qwen35')
                run_control = ddp_config.validate_run_control_protocol(protocol)
                camera = ddp_config.validate_camera_protocol(protocol)
                self.assertTrue(ddp_training.training_config_matches(path, 'qwen35', settings, run_control, camera))
                changed = self.write({**value, 'camera': {'weight': 1.0, 'weight_rot': 2.0, 'supervision': PIN}})
                self.assertFalse(ddp_training.training_config_matches(changed, 'qwen35', settings, run_control, camera))


# ----------------------------------------------------------------------------------------------- H2
class ArmConfigTests(unittest.TestCase):
    """H2: every arm and smoke config passes the trainer's own normalization; the spec pins bank, closure, names."""

    def base(self):
        from student_pilot.ddp_config import SEGMENT_LOSS_REDUCTION
        return {'world_size': 32, 'effective_batch_size': 256, 'seed': 17, 'learning_rate': 2.83e-4, 'epochs': 1,
                'max_steps': 1550, 'loss_reduction': SEGMENT_LOSS_REDUCTION, 'checkpoint_every_steps': 25}

    def test_arm_and_smoke_configs_normalize(self):
        from tools import pd_arm_configs as arms
        from student_pilot.ddp_config import normalize_training_config
        configs = arms.arm_configs(self.base(), self.base(), SMOKE_BANK_SHA256, '/r/b/87bf2a90.npz')
        self.assertEqual(sorted(configs), ['P', 'PD', 'U', 'XP'])
        for name, config in configs.items():
            settings = normalize_training_config(config, 'qwen35')
            self.assertTrue(settings['unfreeze_vision_blocks'])
            self.assertEqual((settings['vision_learning_rate'], settings['head_learning_rate']), (2e-6, 1e-4))
            camera = camera_config.from_training_config(config)
            if name == 'U':
                self.assertIsNone(camera)
                continue
            self.assertEqual(camera['weight'], 1.0)  # Cambrian-P's effective pose weight
            self.assertIsNone(camera['feature_layers'])  # the final-norm states
            self.assertEqual(camera['head_only_steps'], 50)
            self.assertEqual(camera['gate'], arms.CAMERA_GATE)
            self.assertEqual(camera['supervision']['sha256'], SMOKE_BANK_SHA256)
            self.assertEqual(camera['point_depth'] is not None, name == 'PD')
        smoke = arms.smoke_config(self.base(), SMOKE_BANK_SHA256, '/r/b/87bf2a90.npz')
        settings = normalize_training_config(smoke, 'qwen35')
        self.assertEqual((settings['world_size'], settings['effective_batch_size'], settings['max_steps']), (8, 32, 60))
        camera = camera_config.from_training_config(smoke)
        self.assertEqual((camera['head_only_steps'], camera['gate'], camera['lm_gate']), (10, None, None))
        spec = arms.spec(configs, smoke, SMOKE_BANK_SHA256, [['d1', 'v0123456789ab']], 'f' * 40)
        names = list(spec['job_names'].values())
        self.assertEqual(len(set(names)), 5)
        for name in names:
            self.assertRegex(name, r'^a15_cot_ap[0-9a-f]{8}$')
        self.assertFalse(arms.BANNED.search(json.dumps(spec['configs'])))
        self.assertEqual(spec['bank']['sha256'], SMOKE_BANK_SHA256)
        self.assertIn('d9b941d1e641', spec['closures']['rg2p2_launcher'])

    def test_lm_gate_from_reference_metrics(self):
        from tools import pd_arm_configs as arms
        path = output_dir() / 'metrics.jsonl'
        path.write_text(''.join(json.dumps({'step': s, 'loss': 1.0 + s / 1000}) + '\n' for s in range(1, 201)))
        gate = arms.lm_gate_from_metrics(path)
        self.assertEqual(gate['reference']['steps'], list(range(191, 201)))
        self.assertEqual(camera_config.normalize({'lm_gate': gate})['lm_gate']['reference']['values'][0], 1.191)


# ----------------------------------------------------------------------------------------------- H3, M1
class FrameConventionTests(unittest.TestCase):
    """H3: group g describes frame 2g+1; every pose is relative to frame 0, phase 2's camera 1."""

    def test_targets_and_gravity_reference_follow_the_convention(self):
        poses, intrinsics = trajectory(3)
        camera, mask, _ = targets.encode_cameras(poses, intrinsics, (480, 640))
        gravity, _ = targets.encode_gravity(poses)
        self.assertEqual(targets.ANCHOR_FRAMES, tuple(range(1, 32, 2)))
        r_grav, t_grav, _ = targets.to_gravity_reference_frame(camera, gravity)
        # Independent construction from world coordinates: origin at camera 0, z up, y its horizontal forward.
        forward = poses[0, :3, 2].copy()
        forward[2] = 0
        y_axis = forward / np.linalg.norm(forward)
        z_axis = np.array([0.0, 0.0, 1.0])
        x_axis = np.cross(y_axis, z_axis)
        world_to_ref = np.stack((x_axis, y_axis, z_axis))
        for g in range(16):
            f = 2 * g + 1
            np.testing.assert_allclose(t_grav[g], world_to_ref @ (poses[f, :3, 3] - poses[0, :3, 3]), atol=1e-9)
            np.testing.assert_allclose(r_grav[g], world_to_ref @ poses[f, :3, :3], atol=1e-9)
        self.assertGreater(world_to_ref @ poses[0, :3, 0] @ [1, 0, 0], 0.99)  # camera right is +X

    def test_head_api_uses_phase2_one_based_frames_with_origin_frame_1(self):
        """Pins the one convention: 1-based frames 1..32, origin frame 1; group g answers frame 2g + 2."""
        self.assertEqual(head_api.FRAME_ORIGIN, 1)
        self.assertEqual(head_api.POSE_FRAMES, (1,) + tuple(range(2, 33, 2)))
        self.assertEqual(head_api.DEPTH_FRAMES, tuple(range(2, 33, 2)))
        self.assertEqual([head_api.group_of_frame(f) for f in (2, 4, 32)], [0, 1, 15])
        for frame in (1, 3, 5, 31, 0, 33, 2.0):
            with self.assertRaises(ValueError, msg=str(frame)):
                head_api.group_of_frame(frame)
        poses, intrinsics = trajectory(5)  # poses[i] is 1-based frame i + 1
        camera, _, scale = targets.encode_cameras(poses, intrinsics, (480, 640))
        gravity, _ = targets.encode_gravity(poses)

        class Exact(nn.Module):
            """A supervision stub whose heads return the GT encodings, to pin the API's indexing."""
            point_depth = None

            def __init__(self):
                super().__init__()
                self.projector = nn.Linear(4, 4)

            def predict_all(self, states):
                return ([torch.tensor(camera)[None]], [torch.tensor(gravity)[None]], [torch.tensor([math.log(scale)])])
        session = head_api.HeadSession(Exact(), torch.zeros(16, 4))
        forward = poses[0, :3, 2].copy()
        forward[2] = 0
        y_axis = forward / np.linalg.norm(forward)
        world_to_ref = np.stack((np.cross(y_axis, [0, 0, 1.0]), y_axis, [0, 0, 1.0]))
        everything = head_api.pose_all(session)
        self.assertEqual(sorted(everything), list(head_api.POSE_FRAMES))
        for frame, (r, t, info) in everything.items():
            np.testing.assert_allclose(t, world_to_ref @ (poses[frame - 1, :3, 3] - poses[0, :3, 3]), atol=1e-9)
            np.testing.assert_allclose(r, world_to_ref @ poses[frame - 1, :3, :3], atol=1e-9)
        np.testing.assert_allclose(everything[1][1], np.zeros(3))
        self.assertAlmostEqual(everything[2][2]['trajectory_step_m'], scale)
        r_rel, t_rel = session.relative_pose(8)
        relative = np.linalg.inv(poses[7]) @ poses[0]
        np.testing.assert_allclose(r_rel, relative[:3, :3], atol=1e-9)
        np.testing.assert_allclose(t_rel, relative[:3, 3], atol=1e-9)
        with self.assertRaisesRegex(ValueError, 'shares temporal group 2 with frame 6'):
            session.pose(5)

    def test_pair32_is_refused(self):
        """M1: per-frame addressing has no supervision, so it is not offered."""
        with self.assertRaisesRegex(ValueError, 'group16'):
            camera_config.normalize({'frame_addressing': 'pair32'})


# ----------------------------------------------------------------------------------------------- H4
class HeadApiTests(unittest.TestCase):
    """H4: sessions read the same states as training, through the same hooks, and raise on missing inputs."""

    def training_inputs(self, model, heads, tokenizer, row, batch):
        recorded = {}
        carrier, depth = heads.camera.carrier_states, heads.camera.depth_loss

        def spy_carrier(hidden, positions, layer_states=None):
            states = carrier(hidden, positions, layer_states)
            recorded['carrier'] = states.detach()
            return states

        def spy_depth(targets_, present, last_pose, grids, vit, size):
            recorded.update(grids=[g.detach() for g in grids], vit=[[v.detach() for v in vs] for vs in vit])
            return depth(targets_, present, last_pose, grids, vit, size)
        heads.camera.carrier_states, heads.camera.depth_loss = spy_carrier, spy_depth
        model.eval()
        with torch.no_grad():
            row_losses(model, encoded(tokenizer, [({**row, '_camera': record(0)}, batch)]))
        heads.camera.carrier_states, heads.camera.depth_loss = carrier, depth
        return recorded

    def test_session_matches_the_training_path(self):
        for layers in (None, [1, 2]):
            with self.subTest(feature_layers=layers):
                tokenizer, model, heads = toy_heads(feature_layers=layers)
                row, batch = video_row(tokenizer, 6, 4, seed=3)
                expected = self.training_inputs(model, heads, tokenizer, row, batch)
                prompt = {k: v for k, v in batch.items() if k != 'labels'}
                session = head_api.HeadSession.from_forward(model, targets.insert_carriers(prompt, tokenizer))
                states = capture_camera_states(model, targets.insert_carriers(prompt, tokenizer))
                self.assertTrue(torch.equal(states['carrier_states'], expected['carrier'][0]))
                self.assertTrue(torch.equal(states['visual_grid'], expected['grids'][0]))
                for a, b in zip(states['vit_grids'], expected['vit'][0]):
                    self.assertTrue(torch.equal(a, b))
                with torch.no_grad():
                    stages, gravity, scale = heads.camera.predict_all(expected['carrier'])
                np.testing.assert_allclose(session.raw_pose, stages[-1][0].double().numpy(), atol=1e-6)
                r, t, info = head_api.pose(6, session=session)
                self.assertEqual((info['group'], info['reference']), (2, head_api.REFERENCE_FRAME))
                r_rel, t_rel = session.relative_pose(6)
                r_grav, t_grav, _ = targets.to_gravity_reference_frame(stages[-1][0].double().numpy(), gravity[-1][0].double().numpy())
                np.testing.assert_allclose(r, r_grav[2], atol=1e-6)
                r0, t0, _ = session.pose(1)
                np.testing.assert_allclose(t0, np.zeros(3))
                points = np.array([[100.0, 200.0], [900.0, 50.0]])
                with torch.no_grad():
                    fov = stages[-1][0, :, 7:9].clamp(0.1, math.pi - 0.1)
                    direct = heads.camera.point_depth(expected['grids'][0], expected['vit'][0], fov,
                                                      torch.tensor(np.repeat(points[None], 16, 0), dtype=torch.float32))
                with head_api.bind_session(session):
                    np.testing.assert_allclose(head_api.depth(6, points), direct[2].double().numpy(), rtol=1e-5)
                    self.assertAlmostEqual(head_api.depth(32, [100.0, 200.0]), float(direct[15, 0]), places=5)

    def test_missing_inputs_and_unanswerable_frames_raise(self):
        tokenizer, model, heads = toy_heads()
        row, batch = video_row(tokenizer)
        prompt = {k: v for k, v in batch.items() if k != 'labels'}
        with self.assertRaisesRegex(ValueError, 'carriers'):
            capture_camera_states(model, prompt)
        states = capture_camera_states(model, targets.insert_carriers(prompt, tokenizer))
        with self.assertRaisesRegex(ValueError, 'visual grid'):
            head_api.HeadSession(heads.camera, states['carrier_states'])
        session = head_api.HeadSession(heads.camera, states['carrier_states'], states['visual_grid'], states['vit_grids'])
        for call in (lambda: session.pose(3), lambda: session.depth(1, [5.0, 5.0]), lambda: session.depth(4, [5.0, 1200.0]),
                     lambda: session.pose(0)):
            with self.assertRaises(ValueError):
                call()
        with self.assertRaisesRegex(ValueError, 'HeadSession'):
            head_api.pose(1)
        _, model2, heads2 = toy_heads(depth=False, weight_gravity=0.0)
        states2 = capture_camera_states(model2, targets.insert_carriers(prompt, tokenizer))
        bare = head_api.HeadSession(heads2.camera, states2['carrier_states'])
        with self.assertRaisesRegex(ValueError, 'gravity'):
            bare.pose(2)
        with self.assertRaisesRegex(ValueError, 'point-depth'):
            bare.depth(2, [5.0, 5.0])


# ----------------------------------------------------------------------------------------------- C2, H5
class GateTests(unittest.TestCase):
    """C2 and H5: measured G3T numbers only, the agreed thresholds, medians, and failure on anything missing."""

    def scene(self, dataset='d1', scene='v1', rotate_deg=0.0, depth_scale=1.0, seed=0, drop=None):
        rec = record(seed, points=8)
        gt = {'camera': np.asarray(rec['camera']), 'camera_mask': np.asarray(rec['camera_mask']),
              'gravity': np.asarray(rec['gravity']), 'gravity_mask': True, 'trajectory_scale': rec['trajectory_scale'],
              'point_depth_uv': np.asarray(rec['point_depth']['uv']), 'point_depth_gt': np.asarray(rec['point_depth']['depth']),
              'point_depth_mask': np.asarray(rec['point_depth']['mask'])}
        camera = gt['camera'].copy()
        if rotate_deg:
            turn = rotation([0, 1, 0], math.radians(rotate_deg))
            for g in range(16):
                camera[g, 3:7] = targets.quaternion_xyzw(turn @ targets.rotation_from_xyzw(camera[g, 3:7]))
        pred = {'camera': camera, 'gravity': gt['gravity'].copy(), 'trajectory_step_m': rec['trajectory_scale'],
                'point_depth': gt['point_depth_gt'] * depth_scale}
        if drop:
            pred[drop] = None
        return {'dataset': dataset, 'scene': scene, 'gt': gt, 'pred': pred}

    HEADS = {'pose', 'gravity', 'scale', 'depth'}

    def test_g3t_reference_quotes_the_measurements(self):
        text = (ROOT / 'tests/fixtures/g3t_reference/EXCERPT.md').read_text()
        lines = [line.rstrip('\n') for line in io.StringIO(text)]
        rows = {'d1': next(l for l in lines if l.startswith('| **ScanNet** (')),
                'd2': next(l for l in lines if l.startswith('| **ScanNet++** ('))}
        for token, line in rows.items():
            cells = [c.strip() for c in re.findall(r'[^|]+', line.strip().strip('|'))]
            ref = gate_eval.G3T_REFERENCE[token]
            self.assertEqual(ref['n_scenes'], int(cells[1]))
            self.assertEqual(ref['raw_scale_median'], float(cells[2].strip('*')))
            self.assertEqual(ref['raw_scale_sd_ln'], float(cells[7].strip('*')))
            for cell, (mean_key, median_key) in zip(cells[9:12], (('rotation_deg_sim3_mean', 'rotation_deg_sim3_median'),
                                                                   ('rotation_deg_procrustes_mean', 'rotation_deg_procrustes_median'),
                                                                   ('relative_rotation_deg_pairwise_mean', 'relative_rotation_deg_pairwise_median'))):
                mean, median = re.findall(r'[\d.]+', cell)
                self.assertEqual((ref[mean_key], ref[median_key]), (float(mean), float(median)))
            self.assertEqual(ref['ate_rms_m_median_after_sim3'], float(re.match(r'[\d.]+', cells[12]).group()))
            self.assertIsNone(ref['metric_translation_m'])
            self.assertIsNone(ref['depth_abs_rel'])
            self.assertIsNone(ref['depth_delta125'])
        probe = next(l for l in lines if l.startswith('| g3t |'))
        cells = [c.strip() for c in re.findall(r'[^|]+', probe.strip().strip('|'))]
        self.assertEqual(gate_eval.G3T_REFERENCE['d1']['probe_scale_mra'], float(re.match(r'[\d.]+', cells[1]).group()))
        self.assertEqual(gate_eval.G3T_REFERENCE['d1']['probe_scale_mean_abs_ln_err'], float(cells[2]))
        self.assertEqual(gate_eval.G3T_REFERENCE['d2']['probe_scale_mra'], float(re.match(r'[\d.]+', cells[4]).group()))
        self.assertEqual(gate_eval.G3T_REFERENCE['d2']['probe_scale_mean_abs_ln_err'], float(cells[5]))

    def test_thresholds_are_the_agreed_gate(self):
        self.assertEqual(gate_eval.GATE, {'rotation_deg_median_max': 5.2, 'position_m_median_max': 0.25,
                                          'heading_deg_median_max': 10.0, 'depth_abs_rel_max': 0.10,
                                          'depth_delta125_min': 0.90, 'depth_abs_err_m_median_max': 0.20,
                                          'decision_agreement_min': 0.85})

    def run_gate(self, records, heads=HEADS):
        keys = [(r['dataset'], r['scene']) for r in records]
        return gate_eval.evaluate(records, heads, keys, [('d1', 'train')])

    def test_perfect_heads_pass_and_errors_fail(self):
        perfect = self.run_gate([self.scene(scene='a'), self.scene('d2', 'b', seed=1)])
        self.assertTrue(perfect['gate']['passed'], perfect['gate'])
        self.assertEqual(perfect['overall']['rotation_deg']['median'], 0.0)
        self.assertEqual(set(perfect['by_dataset']), {'d1', 'd2'})
        self.assertEqual(perfect['g3t_reference']['d1'], gate_eval.G3T_REFERENCE['d1'])
        rotated = self.run_gate([self.scene(scene='a', rotate_deg=8.0)])
        self.assertFalse(rotated['gate']['checks']['rotation_deg_median'])
        self.assertAlmostEqual(rotated['overall']['rotation_deg']['median'], 8.0, places=4)
        scaled = self.run_gate([self.scene(scene='a', depth_scale=1.3)])
        self.assertFalse(scaled['gate']['checks']['depth_abs_rel'])
        self.assertFalse(scaled['gate']['checks']['depth_delta125'])

    def test_medians_resist_one_bad_scene(self):
        records = [self.scene(scene=f's{i}', seed=i) for i in range(4)] + [self.scene(scene='bad', rotate_deg=60.0)]
        result = self.run_gate(records)
        self.assertTrue(result['gate']['checks']['rotation_deg_median'])
        self.assertGreater(result['overall']['rotation_deg']['p90'], 50)

    def test_missing_predictions_raise_and_unmeasured_criteria_fail(self):
        for drop in ('gravity', 'point_depth', 'trajectory_step_m', 'camera'):
            with self.assertRaisesRegex(ValueError, 'Missing prediction'):
                self.run_gate([self.scene(scene='a', drop=drop)])
        pose_only = self.run_gate([self.scene(scene='a')], heads={'pose'})
        self.assertFalse(pose_only['gate']['passed'])
        self.assertEqual(pose_only['gate']['checks']['depth_abs_rel'], 'not_measured')
        self.assertEqual(pose_only['gate']['checks']['position_m_median'], 'not_measured')

    def test_heldout_contract(self):
        record_ = self.scene(scene='a')
        with self.assertRaisesRegex(ValueError, 'not on the held-out'):
            gate_eval.evaluate([record_], self.HEADS, [('d1', 'b')], [])
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            gate_eval.evaluate([record_], self.HEADS, [('d1', 'a')], [('d1', 'a')])

    def test_heldout_list_file(self):
        listed = json.loads((ROOT / 'configs/gate_heldout_scenes_v1.json').read_text())
        self.assertEqual(len(listed['scenes']), 38)
        for dataset, scene in listed['scenes']:
            self.assertIn(dataset, ('d1', 'd2'))
            self.assertRegex(scene, r'^v[0-9a-f]{12}$')
        self.assertEqual(len({tuple(s) for s in listed['scenes']}), 38)

    def test_driver_on_a_toy_checkpoint(self):
        from student_pilot import gate_driver
        tokenizer, model, heads = toy_heads()
        root = output_dir()
        rows, columns = [], {k: [] for k in bank_mod.ARRAYS if k not in ('schema', 'pose_encoding', 'translation_unit_m',
                                                                         'origin_frame', 'anchor_frames')}
        for seed in (0, 1):
            row, batch = video_row(tokenizer, seed=seed)
            rec = record(seed)
            rows.append((row, batch))
            frames = row['student_input']['frame_indices']
            for key, value in (('dataset_tokens', 'd1'), ('scene_tokens', row['scene']), ('frame_indices', frames),
                               ('frame_set_sha256', bank_mod.frame_set_sha256(frames)), ('camera', rec['camera']),
                               ('camera_mask', rec['camera_mask']), ('trajectory_scale', rec['trajectory_scale']),
                               ('gravity', rec['gravity']), ('gravity_mask', True), ('depth_source', 'first_hits'),
                               ('point_depth_uv', rec['point_depth']['uv']), ('point_depth_gt', rec['point_depth']['depth']),
                               ('point_depth_mask', rec['point_depth']['mask'])):
                columns[key].append(value)
        arrays = {k: np.asarray(v) for k, v in columns.items()}
        arrays.update(schema=np.array(bank_mod.BANK_SCHEMA), pose_encoding=np.array(camera_config.POSE_ENCODING),
                      translation_unit_m=np.array(1.0), origin_frame=np.array(0), anchor_frames=np.array(targets.ANCHOR_FRAMES),
                      point_depth_uv=arrays['point_depth_uv'].astype(np.float16),
                      point_depth_gt=arrays['point_depth_gt'].astype(np.float16), camera=arrays['camera'].astype(np.float32))
        np.savez(root / 'bank.npz', **arrays)
        encodings = {row['scene']: {k: v for k, v in batch.items() if k != 'labels'} for row, batch in rows}
        heldout = [('d1', row['scene']) for row, _ in rows]
        result = gate_driver.run_gate(model, tokenizer, [row for row, _ in rows], root / 'bank.npz', heldout, [],
                                      lambda row: encodings[row['scene']])
        self.assertEqual(result['heads'], ['depth', 'gravity', 'pose', 'scale'])
        self.assertEqual(result['overall']['num_scenes'], 2)
        self.assertEqual(result['overall']['depth_points'], 2 * 16 * 8)
        self.assertIn('passed', result['gate'])
        stray = {**rows[0][0], 'scene': 'v999999999999'}
        with self.assertRaisesRegex(ValueError, 'no labels'):
            gate_driver.run_gate(model, tokenizer, [stray], root / 'bank.npz', heldout, [], lambda row: encodings[rows[0][0]['scene']])


# ----------------------------------------------------------------------------------------------- head-only warmup
class HeadOnlyWarmupTests(unittest.TestCase):
    """Recipe: random heads send no gradient into the student until head_only_steps, then ramp in."""

    def test_schedule(self):
        settings = cfg(head_only_steps=4)
        self.assertEqual([camera_config.backbone_gradient_scale(s, settings) for s in range(9)],
                         [0, 0, 0, 0, 0.2, 0.4, 0.6, 0.8, 1.0])
        self.assertEqual(camera_config.backbone_gradient_scale(0, cfg()), 1.0)

    def test_head_losses_reach_the_student_only_after_the_hold(self):
        grads = {}
        for step in (0, 9):
            tokenizer, model, heads = toy_heads(head_only_steps=4)
            heads.set_step(step, 100)
            row, batch = video_row(tokenizer)
            # A pose-only row: its text target has weight 0, so every student gradient comes from the heads.
            loss = row_losses(model, encoded(tokenizer, [({**row, '_camera': {**record(0), 'lm_weight': 0.0}}, batch)]))
            loss.sum().backward()
            grads[step] = (float(model.visual.blocks[0].attn.qkv.weight.grad.abs().sum()),
                           float(model.language_model.layers[0].weight.grad.abs().sum()),
                           float(heads.camera.projector.weight.grad.abs().sum()),
                           float(heads.camera.point_depth.llm_proj.weight.grad.abs().sum()))
        self.assertEqual(grads[0][:2], (0.0, 0.0))
        self.assertGreater(min(grads[0][2:]), 0)
        self.assertGreater(min(grads[9]), 0)


if __name__ == '__main__':
    unittest.main()
