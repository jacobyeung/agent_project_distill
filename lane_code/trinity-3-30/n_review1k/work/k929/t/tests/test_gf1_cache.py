"""GF-1 cached pool(n_hat) bank, identity refusal, online pose rows and the shuffled-bank read (CPU, tiny)."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from torch.nn import functional as F

from student_pilot import gf1, gf1_cache as C, g3t_online as gx, carrier_c1_data as data, pose_samples as samples
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.carrier_c1_data import insert_frame_carriers
from tests.test_carrier_c1 import Tokenizer

SIDE = 56          # tiny tower raster (4 x 4 patches of 14)
GRID = (32, 4, 6)  # Qwen video grid: 32 temporal groups, 2 x 3 merger cells per frame
FRAME_WH = (64, 48)


def out_dir():
    root = Path(os.environ.get('LANE_TEST_OUTPUT') or tempfile.mkdtemp())
    return Path(tempfile.mkdtemp(prefix='gf1_cache_', dir=root))


def settings(cached=None, encoder_bf16=False, injection='pre_lm', router=False, layers=(0, 1, 2)):
    production = json.loads((Path(__file__).resolve().parents[1]/'configs/gf1_stage1.json').read_text())
    value = production['gf1'] | dict(injection=injection, hidden=16, dense_frames=64, layers=list(layers),
                                     top_k=2 if router else 0)
    if cached is not None:
        value['cached_bank'] = cached
    block = dict(schema='gx-carrier-v1', mode='frozen', encoder=dict(repository=gx.REPOSITORY,
        revision=gx.REVISION, source_sha256=gx.vendor_digest(),
        weights=dict(path='/fixture/model.safetensors', sha256='a'*64),
        config=dict(path='/fixture/config.json', sha256='b'*64)), input=gx.INPUT, feature=gx.FEATURE,
        connector=dict(out_init='zero', rms_cam='warm_start_carrier_median_rms_v1', rms_scale=1.),
        finetune=None, gf1=gf1.normalize(value))
    if encoder_bf16:
        block['encoder_dtype'] = 'bf16'
    return block


class Tiny(gx.G3TEncoder):
    calls = 0
    def __init__(self, block):
        super().__init__(block, dict(aggregator=dict(img_size=SIDE, patch_size=14, embed_dim=16, depth=3,
            num_heads=2, patch_embed='conv'), head=dict(dim_in=32, trunk_depth=1, num_heads=2)), image_size=SIDE)
    def forward(self, images, coords=None):
        Tiny.calls += 1
        assert not torch.is_grad_enabled()
        cam, local, global_, bank = super().forward(images, coords)
        return F.pad(cam, (0, 2048-cam.shape[-1])), local, global_, F.pad(bank, (0, 2048-bank.shape[-1]))


def small_square(frames, expected_frames=32):
    """The native square loader at full fidelity, then resized to the tiny tower raster; ROI unchanged."""
    images, coords = REAL_SQUARE(frames, expected_frames=expected_frames)
    return F.interpolate(images.float(), (SIDE, SIDE), mode='bilinear', align_corners=False).half(), coords


REAL_SQUARE = gx.native_square_518


def model_for(block, base_bf16=False, seed=31):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    torch.manual_seed(seed)
    text = dict(vocab_size=64, hidden_size=32, intermediate_size=64, num_hidden_layers=3,
                num_attention_heads=4, num_key_value_heads=2, head_dim=8, use_cache=False,
                layer_types=['linear_attention','full_attention','full_attention'], linear_key_head_dim=4,
                linear_value_head_dim=4, linear_num_key_heads=4, linear_num_value_heads=4,
                pad_token_id=0, rope_parameters=dict(rope_type='default', rope_theta=10000.,
                                                    mrope_section=[1,1,2], partial_rotary_factor=1.))
    vision = dict(depth=3, hidden_size=32, intermediate_size=64, num_heads=4, out_hidden_size=32,
                  num_position_embeddings=16, patch_size=2, temporal_patch_size=2, spatial_merge_size=2)
    config = Qwen3_5Config(text_config=text, vision_config=vision, image_token_id=60, video_token_id=61,
                          vision_start_token_id=62, vision_end_token_id=63)
    for item in (config, config.text_config, config.vision_config): item._attn_implementation = 'sdpa'
    base = Qwen3_5ForConditionalGeneration(config).float()
    camera = dict(embed_dim=64, num_heads=4, trunk_depth=4, refine_iterations=4,
                  weight_gravity=.05, weight_scale=.02, supervision=dict(path='/fixture', sha256='a'*64))
    from student_pilot.carrier_c1_sweep import recipe_for
    cfg = dict(schema='carrier-c1-run-v1', training_mode='final', depth_enabled=False,
        depth_fov_source='pose_head', frame_layout='duplicate', init='base', parallel='fsdp', all_frames=True,
        carrier_placement='append_after_temporal_group_video_tokens_v1', streams=dict(pose={},vqa={},pointing={},routing={}),
        mix=['pose','vqa','pointing','routing'], world_size=4, reference_world_size=4, steps=10, milestones=[10],
        geometry_online=block, trace_program_version='3.14')
    cfg['scheduled_sampling'] = dict(seed=17, max_own_probability=1., pose_open_deg=45., pose_full_deg=25.,
        fov_open_deg=2., depth_open_absrel=.25, ema_steps=100, force_from_step=0, exposure_from_step=None,
        exposure_probability=0.)
    cfg['recipe'] = recipe_for(cfg)
    with patch.object(gx, 'G3TEncoder', Tiny):
        model = CarrierC1(base, camera, {}, 5, training_mode='final', depth_enabled=False, frame_layout='duplicate',
                          depth_fov_source='pose_head', recipe=cfg['recipe'], geometry_online=block,
                          geometry_runtime=dict(image_mean=[.5]*3, image_std=[.25]*3))
    from student_pilot.trace_version import bind
    bind(model, cfg)
    with torch.no_grad():
        # Open every connector path: nonzero output matrix, non-unit LayerNorm affine, live router.
        g = torch.Generator().manual_seed(seed)
        fusion = model.auxiliary_heads.gf1
        for norm in fusion.norms:
            norm.weight.copy_(1 + .5 * torch.randn(norm.weight.shape, generator=g))
            norm.bias.copy_(.2 * torch.randn(norm.bias.shape, generator=g))
        for output in fusion.outputs:
            output.weight.copy_(.05 * torch.randn(output.weight.shape, generator=g))
        if fusion.router is not None:
            fusion.router.weight.copy_(torch.randn(fusion.router.weight.shape, generator=g))
    if base_bf16:
        from student_pilot import full_ft
        for _, parameter in full_ft.base_parameters(model):
            parameter.data = parameter.data.to(torch.bfloat16)
    return model


def text_batch(rows=1, seed=5):
    t, h, w = GRID
    cells = (h // 2) * (w // 2)
    ids = torch.tensor([[2] + [v for _ in range(t) for v in [62] + [61]*cells + [63]] + [10, 11, 12, 13]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), labels=torch.full_like(ids, -100),
                 mm_token_type_ids=torch.where(ids == 61, 2, 0), video_grid_thw=torch.tensor([list(GRID)]),
                 pixel_values_videos=torch.randn(t*h*w, 24, generator=torch.Generator().manual_seed(seed)))
    batch['labels'][0, -2:] = ids[0, -2:]
    batch = insert_frame_carriers(batch, Tokenizer(), frame_layout='duplicate')
    if rows == 1:
        return batch
    return {k: torch.cat([v]*rows) for k, v in batch.items()}


def write_clip_frames(root, name, seed):
    """64 sha256-pinned PNG frames; the LM uses every second frame (nested anchors 0, 2, ..., 62)."""
    from PIL import Image
    root = Path(root)/name
    root.mkdir(parents=True)
    rng = np.random.default_rng(seed)
    frames = []
    for i in range(64):
        path = root/f'frame_{i:03d}.png'
        Image.fromarray(rng.integers(0, 256, (FRAME_WH[1], FRAME_WH[0], 3), dtype=np.uint8)).save(path)
        frames.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    ordinals = list(range(0, 128, 2))
    dense = dict(frames=frames, frame_indices=ordinals, timestamps=[i/10 for i in ordinals], fps=10.,
                 total_num_frames=200)
    sparse = dict(frames=frames[::2], frame_indices=ordinals[::2], timestamps=dense['timestamps'][::2], fps=10.,
                  total_num_frames=200, question='where?', options=[], geometry_dense=dense)
    return dict(qid=name, dataset='scannet', student_input=sparse, target='A')


def online_geometry(row):
    images, coords = small_square(samples.load_frames(row['student_input']['geometry_dense']), 64)
    return dict(aux_g3t_images=images[None], aux_g3t_coords=coords[None],
                aux_gf1_lm_indices=torch.arange(0, 64, 2)[None], aux_gf1_cache=gf1.ClipCache())


def capture(model):
    seen = []
    handle = model.auxiliary_heads.gf1.register_forward_hook(lambda m, a, o: seen.append(tuple(x.detach().clone() for x in o)))
    return seen, handle


def read(model, batch):
    """(residuals, logits) under eval/no_grad."""
    model.eval()
    seen, handle = capture(model)
    try:
        with torch.no_grad():
            logits = model.lm_head(model.hidden(batch)).float()
    finally:
        handle.remove()
        if isinstance(batch.get('aux_gf1_cache'), gf1.ClipCache):
            batch['aux_gf1_cache'].clear()
    return seen[0], logits


def grads(model, batch):
    model.train()
    model.zero_grad(set_to_none=True)
    model(batch, stream='vqa')['loss'].backward()
    return {n: p.grad.detach().clone() for n, p in model.auxiliary_heads.gf1.named_parameters() if p.grad is not None}


def diff(a, b):
    a, b = a.float(), b.float()
    scale = float(b.abs().max())
    absolute = float((a - b).abs().max())
    return dict(max_abs=absolute, max_rel=absolute / max(scale, 1e-30), ref_max=scale)


class CachedBank(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.root = out_dir()
        cls.rows = [write_clip_frames(cls.root/'frames', name, seed) for name, seed in (('a', 1), ('b', 2), ('c', 3))]
        cls.patcher = patch.object(gx, 'native_square_518', side_effect=small_square)
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        torch.set_num_threads(cls.previous_threads)

    def cache_cfg(self, dtype, tag):
        return dict(root=str(self.root/f'cache_{tag}_{dtype}'), dtype=dtype)

    def cached_batch(self, model, row, cfg):
        record = C.write_clip(model.auxiliary_heads.geometry_encoder, row, cfg['root'], grid=list(GRID), dtype=cfg['dtype'])
        dense, anchors = gf1.dense_inputs(row, model.geometry_online['gf1'])
        entry = C.load_cached(cfg, C.clip_key(dense), anchors)
        batch = text_batch()
        batch.update(aux_gf1_cache=gf1.ClipCache(), aux_gf1_lm_indices=torch.tensor([anchors]),
                     aux_gf1_rowbanks=C.RowBanks([entry]))
        return batch, record

    def test_algebra_holds_in_the_code(self):
        # Area weights: non-negative, and every merger cell's weights sum to one, border cells included.
        source = torch.eye(16).reshape(16, 4, 4).permute(1, 2, 0)[None]  # one-hot per patch
        for roi in ([0., 128., 1024., 896.], [37.5, 101.3, 1000.2, 917.9], [0., 0., 1024., 1024.]):
            weights = gf1.area_pool(source, torch.tensor([roi]), (1, 4, 6))
            self.assertTrue(bool((weights >= 0).all()))
            torch.testing.assert_close(weights.sum(-1), torch.ones(6), rtol=0, atol=2e-6)
        # LayerNorm is affine with learned weight and bias; the projection is token-shared.
        fusion = model_for(settings()).auxiliary_heads.gf1
        self.assertTrue(all(n.elementwise_affine and n.bias is not None for n in fusion.norms))
        self.assertTrue(all(p.weight.dtype == torch.float32 for p in fusion.projections))

    def test_parity_cached_vs_online(self):
        # Rule fixed before the noise floor was measured. FP32 cases: every tensor within 1e-5 relative.
        # BF16 cases: residuals and logits within 2**-6 relative (two BF16 ulps at the largest value);
        # each connector gradient within max(2**-6, 0.25 * floor), where floor is the same tensor's
        # online-BF16 vs online-FP32 deviation on identical weights (the precision the trainer accepts).
        report = dict(rule=dict(
            fp32='max|cached-online| <= 1e-5 * max|online| for residuals, logits and connector gradients',
            bf16_forward='max|cached-online| <= 2**-6 * max|online| for residuals and logits',
            bf16_gradients='max|cached-online|/max|online| <= max(2**-6, 0.25 * floor_rel), floor_rel = '
                           'online BF16 tower/base vs online FP32 tower/base on identical weights'), cases=[])
        cases = [  # (name, base and tower in BF16, cache dtype, injection, router)
            ('fp32_tower_fp32_cache_pre_lm', False, 'float32', 'pre_lm', False),
            ('fp32_tower_fp32_cache_lm012', False, 'float32', 'lm_012', False),
            ('fp32_tower_fp32_cache_router', False, 'float32', 'pre_lm', True),
            ('fp32_tower_bf16_cache_pre_lm', False, 'bfloat16', 'pre_lm', False),
            ('bf16_tower_bf16_base_fp32_cache_pre_lm', True, 'float32', 'pre_lm', False),
            ('bf16_tower_bf16_base_bf16_cache_pre_lm', True, 'bfloat16', 'pre_lm', False),
            ('bf16_tower_bf16_base_bf16_cache_lm012_router', True, 'bfloat16', 'lm_012', True),
        ]
        row = self.rows[0]
        failures = []
        for name, bf16, dtype, injection, router in cases:
            cfg = self.cache_cfg(dtype, name)
            block = settings(cached=cfg, encoder_bf16=bf16, injection=injection, router=router)
            model = model_for(block, base_bf16=bf16)
            online = text_batch(); online.update(online_geometry(row))
            cached, record = self.cached_batch(model, row, cfg)
            self.assertEqual(record['bank_dtype'], 'bfloat16' if bf16 else 'float32')
            Tiny.calls = 0
            res_o, log_o = read(model, online)
            self.assertEqual(Tiny.calls, 1)
            res_c, log_c = read(model, cached)
            self.assertEqual(Tiny.calls, 1, 'cached read must not run the tower')
            self.assertEqual(model.gx_metrics['cached_rows'], 1)
            g_o, g_c = grads(model, online), grads(model, cached)
            self.assertEqual(Tiny.calls, 2)
            floor = {}
            if bf16:
                reference = model_for(settings(cached=cfg, injection=injection, router=router))
                ref_batch = text_batch(); ref_batch.update(online_geometry(row))
                res_r, log_r = read(reference, ref_batch)
                g_r = grads(reference, ref_batch)
                floor = {f'residual_{i}': diff(a, b) for i, (a, b) in enumerate(zip(res_o, res_r))}
                floor['logits'] = diff(log_o, log_r)
                floor.update({'grad.' + n: diff(g_o[n], g_r[n]) for n in g_r})
            entry = dict(case=name, tower_and_base_dtype='bfloat16' if bf16 else 'float32', cache_dtype=dtype,
                         connector_dtype=str(model.auxiliary_heads.gf1.projections[0].weight.dtype),
                         residual_dtype=str(res_o[0].dtype), bank_dtype=record['bank_dtype'],
                         injection=injection, router=router, tensors={})
            for i, (a, b) in enumerate(zip(res_c, res_o)):
                entry['tensors'][f'residual_{i}'] = diff(a, b)
            entry['tensors']['logits'] = diff(log_c, log_o)
            self.assertEqual(set(g_o), set(g_c))
            expected = {'norms', 'projections', 'outputs'} | ({'router'} if router else set())
            self.assertEqual({n.split('.')[0] for n in g_o}, expected)
            for n in sorted(g_o):
                self.assertGreater(float(g_o[n].abs().max()), 0, n)
                entry['tensors']['grad.' + n] = diff(g_c[n], g_o[n])
            low = not bf16 and dtype == 'float32'
            for tensor, value in entry['tensors'].items():
                if low:
                    tol = 1e-5
                elif tensor.startswith('grad.') and tensor in floor:
                    tol = max(2**-6, .25 * floor[tensor]['max_rel'])
                else:
                    tol = 2**-6
                value['tolerance_rel'] = tol
                if tensor in floor:
                    value['bf16_floor_rel'] = floor[tensor]['max_rel']
                value['pass'] = value['max_rel'] <= tol
                if not value['pass']:
                    failures.append((name, tensor, value))
            entry['worst_rel'] = max(v['max_rel'] for v in entry['tensors'].values())
            entry['verdict'] = 'pass' if all(v['pass'] for v in entry['tensors'].values()) else 'fail'
            report['cases'].append(entry)
        report['verdict'] = 'pass' if not failures else 'fail'
        path = Path(os.environ.get('GF1_CACHE_PARITY_OUT', str(out_dir()/'PARITY.json')))
        path.write_text(json.dumps(report, indent=1) + '\n')
        self.assertEqual(failures, [])

    def test_zero_feature_ablation_matches(self):
        cfg = self.cache_cfg('float32', 'zero')
        model = model_for(settings(cached=cfg))
        model.gx_zero_feature = True
        online = text_batch(); online.update(online_geometry(self.rows[0]))
        cached, _ = self.cached_batch(model, self.rows[0], cfg)
        a, _ = read(model, online); b, _ = read(model, cached)
        torch.testing.assert_close(b[0], a[0], rtol=0, atol=1e-6)

    def test_writer_is_deterministic_and_content_addressed(self):
        cfg = self.cache_cfg('bfloat16', 'det')
        model = model_for(settings(cached=cfg))
        encoder = model.auxiliary_heads.geometry_encoder
        first = C.write_clip(encoder, self.rows[1], cfg['root'], grid=list(GRID), dtype='bfloat16')
        again = C.write_clip(encoder, self.rows[1], cfg['root'], grid=list(GRID), dtype='bfloat16')
        self.assertEqual(first, again)
        key = C.clip_key(self.rows[1]['student_input']['geometry_dense'])
        self.assertEqual(first['clip_key'], key)
        path = Path(cfg['root'])/(key + '.safetensors')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), first['tensor']['sha256'])
        self.assertEqual(first['shape'], [3, 32, 6, 2048])
        self.assertEqual(json.loads((Path(cfg['root'])/(key + '.json')).read_text()), first)

    def test_mismatched_identity_refuses(self):
        cfg = self.cache_cfg('float32', 'refuse')
        model = model_for(settings(cached=cfg))
        batch, record = self.cached_batch(model, self.rows[0], cfg)
        dense, anchors = gf1.dense_inputs(self.rows[0], model.geometry_online['gf1'])
        key = record['clip_key']
        record_path = Path(cfg['root'])/(key + '.json')
        original = record_path.read_text()
        # Model side: layer list, tower weights, merger grid, cache dtype, code version.
        for field, value in (('layers', [0, 1, 3]), ('tower', {**record['tower'], 'weights_sha256': 'c'*64}),
                             ('merger_grid', [32, 4, 8]), ('code_version', '0'*64), ('bank_dtype', 'bfloat16'),
                             ('norm', {**record['norm'], 'eps': 1e-6})):
            with self.subTest(model_side=field):
                bad = copy.deepcopy(batch)
                bad['aux_gf1_rowbanks'].entries[0].record = {**record, field: value}
                with self.assertRaisesRegex(ValueError, 'identity differs in ' + field):
                    read(model, bad)
        # A cache built for another layer bank refuses under the live model.
        other = model_for(settings(cached=cfg, layers=(0, 1, 2)))
        other.geometry_online['gf1']['layers'] = [0, 1, 3]
        with self.assertRaisesRegex(ValueError, 'identity differs in layers'):
            read(other, copy.deepcopy(batch))
        # Data side: clip key, anchors, tensor bytes, dtype switch.
        with self.assertRaisesRegex(ValueError, 'identity differs from the row'):
            C.load_cached(cfg, key, [a + 0 for a in anchors[:-1]] + [63])
        with self.assertRaisesRegex(ValueError, 'identity differs from the row'):
            C.load_cached({**cfg, 'dtype': 'bfloat16'}, key, anchors)
        record_path.write_text(original.replace(record['tensor']['sha256'], 'f'*64))
        try:
            with self.assertRaisesRegex(ValueError, 'sha256 differs'):
                C.load_cached(cfg, key, anchors)
        finally:
            record_path.write_text(original)
        self.assertIsNotNone(C.load_cached(cfg, key, anchors))
        # The cached input refuses when the switch is off.
        off = model_for(settings())
        with self.assertRaisesRegex(ValueError, 'switch is off'):
            read(off, copy.deepcopy(batch))

    def test_mixed_batch_pose_row_runs_tower_online(self):
        cfg = self.cache_cfg('float32', 'mixed')
        model = model_for(settings(cached=cfg))
        cached_a, _ = self.cached_batch(model, self.rows[0], cfg)
        single_b = text_batch(); single_b.update(online_geometry(self.rows[1]))
        single_a = text_batch(); single_a.update(online_geometry(self.rows[0]))
        res_a, _ = read(model, single_a)
        res_b, _ = read(model, single_b)
        mixed = text_batch(rows=2)
        geo_b = online_geometry(self.rows[1])
        # Row 0 carries a cache (its RGB slot is unused); row 1 is the augmented pose row and runs online.
        mixed.update(aux_g3t_images=torch.cat([torch.zeros_like(geo_b['aux_g3t_images']), geo_b['aux_g3t_images']]),
                     aux_g3t_coords=torch.cat([geo_b['aux_g3t_coords']]*2),
                     aux_gf1_lm_indices=torch.arange(0, 64, 2)[None].repeat(2, 1), aux_gf1_cache=gf1.ClipCache(),
                     aux_gf1_rowbanks=C.RowBanks([cached_a['aux_gf1_rowbanks'].entries[0], None]))
        Tiny.calls = 0
        res, _ = read(model, mixed)
        self.assertEqual(Tiny.calls, 1)
        self.assertEqual((model.gx_metrics['tower_forwards'], model.gx_metrics['cached_rows']), (1, 1))
        half = res[0].shape[0] // 2
        torch.testing.assert_close(res[0][half:], res_b[0], rtol=0, atol=0)
        torch.testing.assert_close(res[0][:half], res_a[0], rtol=1e-5, atol=1e-6)

    def encode(self, row, gf1_cfg):
        def encode_frames(processor, question, options, arrays, *args):
            self.lm_arrays = arrays.copy()
            return text_batch(), {}
        with patch.object(samples, 'encode_frames', side_effect=encode_frames), patch.object(samples, 'check_sample'), \
             patch.object(samples, 'augment', side_effect=lambda a, s: (a.astype(np.int16) + 7).clip(0, 255).astype(np.uint8)):
            return data.encode_layout_row(None, row, 'duplicate', None, gf1=gf1_cfg)

    def test_encoder_paths_cached_pose_missing_and_off(self):
        cfg = self.cache_cfg('float32', 'encode')
        block = settings(cached=cfg)
        model = model_for(block)
        C.write_clip(model.auxiliary_heads.geometry_encoder, self.rows[0], cfg['root'], grid=list(GRID), dtype='float32')
        gcfg = block['gf1']
        # Off: the original keys and values, no audit field.
        off_batch, off_audit = self.encode(self.rows[0], settings()['gf1'])
        self.assertNotIn('aux_gf1_rowbanks', off_batch)
        self.assertNotIn('gf1_bank', off_audit)
        expected, _ = small_square(samples.load_frames(self.rows[0]['student_input']['geometry_dense']), 64)
        self.assertTrue(torch.equal(off_batch['aux_g3t_images'][0], expected))
        off_lm = self.lm_arrays
        # Cached non-pose row: no dense RGB decode for the tower, same LM bytes.
        batch, audit = self.encode(self.rows[0], gcfg)
        self.assertEqual(audit['gf1_bank']['source'], 'cached')
        self.assertNotIn('aux_g3t_images', batch)
        self.assertEqual(batch['aux_gf1_rowbanks'].entries[0].kind, 'cached')
        np.testing.assert_array_equal(self.lm_arrays, off_lm)
        # Pose row: per-row augmentation, so the tower runs online even with a cache present.
        pose = {**copy.deepcopy(self.rows[0]), 'category': samples.CATEGORY, 'pose_sample': dict(augment={})}
        batch, audit = self.encode(pose, gcfg)
        self.assertEqual(audit['gf1_bank'], dict(source='online', reason='pose_row_augmented', clip_key=audit['gf1_bank']['clip_key']))
        self.assertNotIn('aux_gf1_rowbanks', batch)
        self.assertIn('aux_g3t_images', batch)
        # A non-pose clip without a cache record refuses; the writer covers every clip before training.
        with self.assertRaisesRegex(ValueError, 'has no record'):
            self.encode(self.rows[2], gcfg)
        # A missing root refuses instead of silently running every row online.
        with self.assertRaisesRegex(ValueError, 'root is missing'):
            self.encode(self.rows[0], gf1.normalize({**gcfg, 'cached_bank': dict(root='/scratch/none/x', dtype='float32')}))

    def test_normalize_switch(self):
        base = dict(dense_frames=64)
        self.assertNotIn('cached_bank', gf1.normalize(base))
        self.assertEqual(gf1.normalize(base), gf1.normalize(dict(base)))
        for bad in (dict(root='relative', dtype='float32'), dict(root='/x', dtype='float16'), dict(root='/x')):
            with self.assertRaises(ValueError):
                gf1.normalize({**base, 'cached_bank': bad})


class ShuffledBank(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = out_dir()
        cls.rows = [write_clip_frames(cls.root/'frames', name, seed) for name, seed in (('a', 11), ('b', 12), ('c', 13))]
        cls.patcher = patch.object(gx, 'native_square_518', side_effect=small_square)
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_plan_is_a_seeded_derangement_preferring_dataset_and_grid(self):
        units = ([dict(clip_key=f's{i}', dataset='scannet', grid=[32, 20, 26]) for i in range(5)] +
                 [dict(clip_key=f'p{i}', dataset='scannetpp', grid=[32, 18, 28]) for i in range(3)] +
                 [dict(clip_key='p_odd', dataset='scannetpp', grid=[32, 20, 26])] +
                 [dict(clip_key='k0', dataset='arkitscenes', grid=[32, 20, 26])])
        plan = C.shuffled_bank_plan(units, seed=17)
        donors = {p['clip_key']: p['donor_clip_key'] for p in plan['pairs']}
        self.assertEqual(sorted(donors), sorted(u['clip_key'] for u in units))
        self.assertEqual(sorted(donors.values()), sorted(donors))
        self.assertTrue(all(k != v for k, v in donors.items()))
        self.assertTrue(all(donors[f's{i}'].startswith('s') or donors[f's{i}'] in ('p_odd', 'k0') for i in range(5)))
        self.assertEqual(plan, C.shuffled_bank_plan(list(reversed(units)), seed=17))
        self.assertNotEqual(plan['permutation_sha256'], C.shuffled_bank_plan(units, seed=18)['permutation_sha256'])
        strict = C.shuffled_bank_plan(units, seed=17, require_same_grid=True)
        self.assertTrue(all(p['grid'] == p['donor_grid'] for p in strict['pairs']))
        self.assertEqual(plan['counts']['clips'], 10)
        with self.assertRaises(ValueError):
            C.shuffled_bank_plan(units[:1], seed=1)
        with self.assertRaises(ValueError):
            C.shuffled_bank_plan([dict(clip_key='x', dataset='d', grid=[32, 2, 2]),
                                  dict(clip_key='y', dataset='d', grid=[32, 4, 4]),
                                  dict(clip_key='z', dataset='d', grid=[32, 4, 4])], seed=1, require_same_grid=True)

    def test_path_aliases_of_one_clip_share_a_donor_and_content_conflicts_refuse(self):
        cfg = settings()['gf1']
        alias = copy.deepcopy(self.rows[0])
        for f in alias['student_input']['geometry_dense']['frames'] + alias['student_input']['frames']:
            f['path'] = '/alias' + f['path']
        rows, plan = C.shuffle_rows([self.rows[0], alias, self.rows[1], self.rows[2]], cfg, seed=5,
                                    grids={C.clip_key(gf1.dense_inputs(r, cfg)[0]): [32, 20, 26] for r in self.rows})
        self.assertEqual(rows[0]['student_input']['geometry_bank_donor']['clip_key'],
                         rows[1]['student_input']['geometry_bank_donor']['clip_key'])
        self.assertEqual(plan['counts']['clips'], 3)
        bad = copy.deepcopy(self.rows[0])
        for part in (bad['student_input']['geometry_dense'], bad['student_input']):
            part['timestamps'] = [t + 1. for t in part['timestamps']]
        with self.assertRaisesRegex(ValueError, 'disagree'):
            C.shuffle_rows([self.rows[0], bad, self.rows[1]], cfg, seed=5,
                           grids={C.clip_key(gf1.dense_inputs(r, cfg)[0]): [32, 20, 26] for r in self.rows})

    def donor_batch(self, row, gf1_cfg):
        holder = {}
        def encode_frames(processor, question, options, arrays, *args):
            holder['lm'] = arrays.copy()
            return text_batch(), {}
        with patch.object(samples, 'encode_frames', side_effect=encode_frames):
            batch, audit = data.encode_layout_row(None, row, 'duplicate', None, gf1=gf1_cfg)
        return batch, audit, holder['lm']

    def test_swapped_bank_reaches_connector_and_true_read_is_unchanged(self):
        block = settings()
        model = model_for(block)
        grids = {C.clip_key(r['student_input']['geometry_dense']): list(GRID) for r in self.rows}
        shuffled, plan = C.shuffle_rows(self.rows, block['gf1'], seed=17, grids=grids)
        donors = {p['clip_key']: p['donor_clip_key'] for p in plan['pairs']}
        key_of = {C.clip_key(r['student_input']['geometry_dense']): r for r in self.rows}
        truth = {}
        for row in self.rows:
            batch, audit, lm = self.donor_batch(row, block['gf1'])
            self.assertNotIn('gf1_bank', audit)
            self.assertNotIn('aux_gf1_rowbanks', batch)
            batch = {**text_batch(), **{k: v for k, v in batch.items() if k.startswith('aux_g')}}
            truth[C.clip_key(row['student_input']['geometry_dense'])] = (read(model, batch)[0][0], lm)
        for row in shuffled:
            own = C.clip_key(row['student_input']['geometry_dense'])
            batch, audit, lm = self.donor_batch(row, block['gf1'])
            self.assertEqual(audit['gf1_bank']['donor_clip_key'], donors[own])
            self.assertEqual(audit['gf1_bank']['permutation_sha256'], plan['permutation_sha256'])
            np.testing.assert_array_equal(lm, truth[own][1])   # the LM still sees its own frames
            entry = batch['aux_gf1_rowbanks'].entries[0]
            expected, _ = small_square(samples.load_frames(key_of[donors[own]]['student_input']['geometry_dense']), 64)
            self.assertTrue(torch.equal(entry.images, expected))
            batch = {**text_batch(), **{k: v for k, v in batch.items() if k.startswith('aux_g')}}
            residual = read(model, batch)[0][0]
            self.assertEqual(model.gx_metrics['donor_rows'], 1)
            # pre_lm without router: the residual depends only on the bank, so it equals the donor's true read.
            self.assertTrue(torch.equal(residual, truth[donors[own]][0]))
            self.assertFalse(torch.allclose(residual, truth[own][0]))
        # Training refuses donors; pose rows refuse donors.
        batch, _, _ = self.donor_batch(shuffled[0], block['gf1'])
        batch = {**text_batch(), **{k: v for k, v in batch.items() if k.startswith('aux_g')}}
        model.train()
        with self.assertRaisesRegex(ValueError, 'read-time option'):
            model(batch, stream='vqa')
        pose = {**copy.deepcopy(shuffled[0]), 'category': samples.CATEGORY, 'pose_sample': dict(augment={})}
        with patch.object(samples, 'check_sample'), self.assertRaisesRegex(ValueError, 'pose rows'):
            self.donor_batch(pose, block['gf1'])

    def test_cached_donor_and_membership_receipt(self):
        from student_pilot import dense_eval
        root = out_dir()
        cfg = dict(root=str(root/'cache'), dtype='float32')
        block = settings(cached=cfg)
        model = model_for(block)
        for row in self.rows:
            C.write_clip(model.auxiliary_heads.geometry_encoder, row, cfg['root'], grid=list(GRID), dtype='float32')
        grids = {C.clip_key(r['student_input']['geometry_dense']): list(GRID) for r in self.rows}
        shuffled, plan = C.shuffle_rows(self.rows, block['gf1'], seed=3, grids=grids, require_same_grid=True)
        donors = {p['clip_key']: p['donor_clip_key'] for p in plan['pairs']}
        for row in shuffled:
            batch, audit, _ = self.donor_batch(row, block['gf1'])
            self.assertEqual(audit['gf1_bank']['source'], 'shuffled_cached')
            entry = batch['aux_gf1_rowbanks'].entries[0]
            self.assertEqual(entry.record['clip_key'], donors[audit['gf1_bank']['clip_key']])
            batch = {**text_batch(), **{k: v for k, v in batch.items() if k.startswith('aux_g')}}
            read(model, batch)
            self.assertEqual((model.gx_metrics['cached_rows'], model.gx_metrics['donor_rows']), (1, 1))
        # Membership: off writes the original receipt; on records the permutation beside the rows.
        dense = {r['qid']: r['student_input']['geometry_dense'] for r in self.rows}
        plain = [dict(qid=r['qid'], dataset='scannet', student_input={k: v for k, v in r['student_input'].items()
                                                                      if k != 'geometry_dense'} | dict(clip_id=r['qid']))
                 for r in self.rows]
        off = dense_eval.prepare_membership(plain, dense, dict(dense_frames=64), root/'off')
        self.assertNotIn('shuffled_bank', off)
        self.assertFalse((root/'off'/'bank_permutation.json').exists())
        on = dense_eval.prepare_membership(plain, dense, dict(dense_frames=64), root/'on',
                                           shuffle=dict(seed=3, grids=grids))
        stored = json.loads((root/'on'/'bank_permutation.json').read_text())
        self.assertEqual(on['shuffled_bank']['permutation_sha256'], stored['permutation_sha256'])
        rows = [json.loads(line) for line in (root/'on'/'rows.jsonl').read_text().splitlines()]
        self.assertTrue(all(r['student_input']['geometry_bank_donor']['clip_key'] !=
                            C.clip_key(r['student_input']['geometry_dense']) for r in rows))
        self.assertEqual({k: v for k, v in on.items() if k not in ('shuffled_bank', 'rows')},
                         {k: v for k, v in off.items() if k != 'rows'})


if __name__ == '__main__':
    unittest.main()
