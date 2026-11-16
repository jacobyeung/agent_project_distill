"""Portable contracts and an opt-in, single-run CPU memory/time measurement."""
import collections
import json
import math
import os
import resource
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest import mock

import numpy as np
import torch
from torch.nn import functional as F

from student_pilot.mask_grounding_head import (
    MDGConfig, MaskGroundingHead, _allowed_mask, _at_points, _decode_points,
    _sample_points, load_artifact, save_artifact,
)


def config(**kwargs):
    values = dict(vit_dim=8, lm_dim=16, dim=16, heads=4, mlp=32, pixel_dim=8,
                  blocks=2, phrase_max=3, points=24, stem_pretrained=False)
    values.update(kwargs)
    return MDGConfig(**values)


def features(cfg, frames=2, labels=2, grid=(1, 2), dtype=torch.float32):
    gh, gw = grid
    taps = [torch.randn(frames, gh * gw, cfg.lm_dim, dtype=dtype) for _ in range(cfg.n_taps)]
    vit = [torch.randn(frames, 2 * gh, 2 * gw, cfg.vit_dim, dtype=dtype) for _ in range(cfg.n_vit)]
    pixels = torch.rand(frames, 3, 32 * gh, 32 * gw)
    query = torch.randn(labels, 2, cfg.lm_dim, dtype=dtype)
    phrase = torch.randn(labels, cfg.phrase_max, 2, cfg.lm_dim, dtype=dtype)
    phrase_mask = torch.ones(labels, cfg.phrase_max, dtype=torch.bool)
    phrase_mask[:, -1] = False
    return taps, vit, pixels, query, phrase, phrase_mask


def targets(labels=2, frames=2, shape=(24, 32)):
    presence = torch.ones(labels, frames)
    presence[:, 1::2] = 0
    masks = torch.zeros(labels, frames, *shape, dtype=torch.bool)
    masks[..., 3:-3, 3:-3] = True
    masks &= presence[..., None, None].bool()
    return dict(frame_presence=presence, frame_valid=torch.ones_like(presence, dtype=torch.bool),
                clip_present=torch.ones(labels), mask_valid=presence.bool(), masks=masks)


def run(head, inputs, grid=(1, 2), geo=None):
    taps, vit, pixels, query, phrase, phrase_mask = inputs
    return head(head.encode_video(taps, vit, pixels, grid, geo), query, phrase, phrase_mask)


class MaskGroundingHeadTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)

    def test_shapes_backward_and_detached_inputs(self):
        for frames in (1, 2, 32):
            with self.subTest(frames=frames):
                cfg = config()
                head = MaskGroundingHead(cfg)
                inputs = features(cfg, frames=frames, dtype=torch.bfloat16)
                for value in (*inputs[0], *inputs[1], *inputs[2:5]):
                    value.requires_grad_()
                with torch.autocast('cpu', dtype=torch.bfloat16):
                    outs = run(head, inputs)
                    losses = head.loss(outs, targets(frames=frames))
                self.assertEqual(len(outs), cfg.blocks)
                for out in outs:
                    self.assertEqual(out['mask_logit'].shape, (2, frames, 8, 16))
                    self.assertEqual(out['frame_logit'].shape, (2, frames))
                    self.assertEqual(out['clip_logit'].shape, (2,))
                    self.assertEqual(out['iou'].shape, (2, frames))
                    self.assertTrue(((out['iou'] >= 0) & (out['iou'] <= 1)).all())
                    self.assertTrue(all(t.dtype == torch.float32 for t in out.values()))
                self.assertEqual(set(losses), {'total', 'bce', 'dice', 'frame', 'clip', 'iou'})
                self.assertTrue(all(torch.isfinite(v) for v in losses.values()))
                losses['total'].backward()
                for name, parameter in head.named_parameters():
                    self.assertIsNotNone(parameter.grad, name)
                    self.assertTrue(torch.isfinite(parameter.grad).all(), name)
                for value in (*inputs[0], *inputs[1], *inputs[2:5]):
                    self.assertIsNone(value.grad)

    def test_zero_geometry_is_bit_identical_and_receives_gradients(self):
        cfg = config(geo_dim=5)
        head = MaskGroundingHead(cfg).eval()
        inputs = features(cfg)
        geo = torch.randn(2, 2, 4, 5, requires_grad=True)
        base = head.encode_video(*inputs[:3], (1, 2))
        actual = head.encode_video(*inputs[:3], (1, 2), geo)
        for name in ('memory', 'pixel', 'frame'):
            self.assertTrue(torch.equal(base[name], actual[name]), name)
        for a, b in zip(head(base, *inputs[3:]), head(actual, *inputs[3:])):
            for name in a:
                self.assertTrue(torch.equal(a[name], b[name]), name)
        head.loss(head(actual, *inputs[3:]), targets())['total'].backward()
        for name, parameter in head.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
        self.assertGreater(head.geo_proj.weight.grad.abs().sum(), 0)
        self.assertIsNone(geo.grad)
        no_geo = MaskGroundingHead(config()).eval()
        no_geo.load_state_dict({k: v for k, v in head.state_dict().items() if not k.startswith('geo_')})
        self.assertTrue(torch.equal(base['memory'], no_geo.encode_video(*inputs[:3], (1, 2))['memory']))

    def test_batch_attention_memory_is_shared_and_rows_are_safe(self):
        head = MaskGroundingHead(config())
        inputs = features(head.cfg, frames=2, labels=3)
        inputs[-1].zero_()
        calls = []
        original = F.scaled_dot_product_attention
        def capture(q, k, v, **kwargs):
            mask = kwargs.get('attn_mask')
            if mask is not None:
                self.assertTrue(mask.any(-1).all())
            calls.append((tuple(q.shape), tuple(k.shape)))
            return original(q, k, v, **kwargs)
        with mock.patch('torch.nn.functional.scaled_dot_product_attention', side_effect=capture):
            outs = run(head, inputs)
        self.assertEqual(len(calls), head.cfg.blocks * 3)
        for index in range(head.cfg.blocks):
            self_call, frame, global_call = calls[index * 3:index * 3 + 3]
            self.assertEqual(self_call[0], (3, 4, 6, 4))
            self.assertEqual(frame, ((2, 4, 3, 4), (2, 4, 8, 4)))
            self.assertEqual(global_call, ((1, 4, 3, 4), (1, 4, 16, 4)))
        self.assertTrue(all(torch.isfinite(v).all() for out in outs for v in out.values()))
        allowed = _allowed_mask(-torch.ones(2, 3, 8, 16), (2, 4))
        self.assertTrue(allowed.all())
        logits = torch.full((1, 1, 8, 16), -1.)
        logits[..., :4, :8] = 1
        self.assertEqual(_allowed_mask(logits, (2, 4)).sum(), 2)

    def test_labels_and_padding_do_not_interact(self):
        head = MaskGroundingHead(config()).eval()
        inputs = features(head.cfg, labels=2)
        inputs[-1][0].zero_()
        baseline = run(head, inputs)
        inputs[3][1].add_(100)
        inputs[4][1].add_(100)
        inputs[4][0].fill_(float('nan'))
        actual = run(head, inputs)
        for before, after in zip(baseline, actual):
            for name in before:
                torch.testing.assert_close(before[name][0], after[name][0], rtol=0, atol=0)

    def test_second_grid_and_stem_normalization(self):
        head = MaskGroundingHead(config()).eval()
        inputs = features(head.cfg, frames=1, grid=(2, 3))
        seen = []
        hook = head.stem.conv1.register_forward_pre_hook(lambda module, args: seen.append(args[0].detach()))
        out = run(head, inputs, grid=(2, 3))[-1]
        hook.remove()
        self.assertEqual(out['mask_logit'].shape, (2, 1, 16, 24))
        torch.testing.assert_close(seen[0], (inputs[2] - head.stem.mean) / head.stem.std)

    def test_loss_formula_validity_deep_weights_and_iou_probability(self):
        head = MaskGroundingHead(config(points=8))
        out = dict(mask_logit=torch.zeros(2, 2, 8, 16, requires_grad=True),
                   frame_logit=torch.zeros(2, 2, requires_grad=True),
                   clip_logit=torch.zeros(2, requires_grad=True),
                   iou=torch.full((2, 2), .5, requires_grad=True))
        target = targets()
        target['clip_present'][1] = 0
        target['frame_valid'][1] = False
        target['mask_valid'].zero_()
        target['frame_presence'][1] = float('nan')
        parts = head.loss([out, out], target)
        self.assertAlmostEqual(parts['frame'].item(), 1.5 * .25 * math.log(2), places=6)
        self.assertAlmostEqual(parts['clip'].item(), 1.5 * math.log(2), places=6)
        self.assertEqual(parts['bce'].item(), 0)
        self.assertEqual(parts['dice'].item(), 0)
        self.assertEqual(parts['iou'].item(), 0)
        target['mask_valid'][0, 0] = True
        parts = head.loss([out, out], target)
        self.assertAlmostEqual(parts['bce'].item(), 1.5 * math.log(2), places=6)
        self.assertAlmostEqual(parts['iou'].item(), 1.5 * .25, places=6)
        expected = sum(getattr(head.cfg, 'w_' + k) * parts[k] for k in ('bce', 'dice', 'frame', 'clip', 'iou'))
        torch.testing.assert_close(parts['total'], expected)
        parts['total'].backward()
        self.assertEqual(out['frame_logit'].grad[1].abs().sum(), 0)
        target['frame_valid'].zero_()
        self.assertEqual(head.loss([out, out], target)['frame'].item(), 0)

    def test_point_sampling_determinism_normalization_and_nearest_targets(self):
        logits = torch.randn(3, 1, 8, 16)
        torch.manual_seed(7)
        first = _sample_points(logits, 24, 3., .75)
        torch.manual_seed(7)
        self.assertTrue(torch.equal(first, _sample_points(logits, 24, 3., .75)))
        self.assertEqual(first.shape, (3, 24, 2))
        self.assertTrue(((first >= 0) & (first < 1)).all())
        torch.manual_seed(7)
        candidates = torch.rand(3, 72, 2)
        ranking = (-_at_points(logits, candidates).abs()).topk(18, dim=1).indices
        torch.testing.assert_close(first[:, :18], candidates.gather(1, ranking[..., None].expand(-1, -1, 2)))
        raster = torch.arange(12).reshape(1, 1, 3, 4).float()
        points = torch.tensor([[[.125, 1 / 6], [.875, 5 / 6]]])
        torch.testing.assert_close(_at_points(raster, points, 'nearest'), torch.tensor([[0., 11.]]))
        head = MaskGroundingHead(config())
        outs = run(head, features(head.cfg))
        torch.manual_seed(55)
        a = head.loss(outs, targets())
        torch.manual_seed(55)
        b = head.loss(outs, targets())
        self.assertTrue(all(torch.equal(a[k], b[k]) for k in a))

    def test_decode_components_distance_and_fallback_match(self):
        masks = np.zeros((8, 13, 17), dtype=bool)
        masks[0, 2:11, 2:15] = True
        masks[0, 4:9, 4:13] = False
        masks[1, 2:11, 2:5] = True
        masks[1, 2:5, 2:15] = True
        masks[1, 8:11, 2:15] = True
        masks[2, 1:4, 1:4] = True
        masks[2, 7:12, 9:16] = True
        masks[3, 0:3, 0:3] = True
        masks[4, 1, 1] = True
        masks[4, 2, 2] = True
        masks[6] = True
        masks[7, 2:5, 2:5] = True
        masks[7, 8:11, 10:13] = True
        heat = np.where(masks, 1., -1.).astype(np.float32)[None]
        heat[0, 4, 2, 2] = 2
        heat[0, 5, 5, 6] = -.5
        fast, fallback = _decode_points(heat), _decode_points(heat, scipy=False)
        np.testing.assert_array_equal(fast, fallback)
        for frame in (0, 1, 2, 3, 4, 6, 7):
            x, y = fast[0, frame]
            self.assertTrue(masks[frame, int(y / 1000 * 13), int(x / 1000 * 17)])
        self.assertGreater(fast[0, 2, 0], 500)
        self.assertLess(fast[0, 7, 0], 500)
        np.testing.assert_array_equal(fast[0, 5], (round(6.5 / 17 * 1000), round(5.5 / 13 * 1000)))
        with mock.patch.dict('sys.modules', {'scipy': None}):
            np.testing.assert_array_equal(_decode_points(heat), fallback)
        out = dict(mask_logit=torch.from_numpy(heat), frame_logit=torch.zeros(1, 8),
                   clip_logit=torch.zeros(1), iou=torch.full((1, 8), .7))
        decoded = MaskGroundingHead.decode(out, tau=.3)
        self.assertTrue((decoded['prob'] == .25).all())
        self.assertFalse(decoded['present'].any())
        self.assertTrue(torch.equal(decoded['area'], torch.from_numpy(masks.sum((-1, -2)))[None]))
        self.assertTrue(torch.equal(decoded['mask'], torch.from_numpy(masks)[None]))
        torch.testing.assert_close(decoded['iou'], out['iou'])

    def test_default_parameter_count_by_module(self):
        with torch.device('meta'):
            head = MaskGroundingHead(MDGConfig(vit_dim=1152))
        counts = collections.Counter()
        for name, parameter in head.named_parameters():
            counts[name.split('.')[0]] += parameter.numel()
        print('MDG parameters: ' + json.dumps(dict(counts), sort_keys=True), flush=True)
        total = sum(counts.values())
        print(f'MDG total trainable parameters: {total:,}', flush=True)
        self.assertGreater(total, 39_000_000)
        self.assertLess(total, 46_000_000)

    def test_artifact_round_trip_immutable_and_strict_without_stem_source(self):
        root = Path(tempfile.mkdtemp(prefix='mdg-head-', dir=os.environ.get('LANE_TEST_OUTPUT', os.environ.get('TMPDIR'))))
        head = MaskGroundingHead(config()).eval()
        inputs = features(head.cfg)
        expected = run(head, inputs)
        meta = dict(tau=.6, base_artifact=dict(path='/frozen/T0/artifact.json', sha256='a' * 64),
                    trainer_commit='synthetic', step=1, metrics={'loss': 1.}, split_identity='synthetic')
        save_artifact(root / 'good', head, meta)
        loaded, actual_meta = load_artifact(root / 'good')
        self.assertEqual(actual_meta, dict(meta, schema='mdg-head-v1', config=asdict(head.cfg)))
        for a, b in zip(expected, run(loaded, inputs)):
            for name in a:
                torch.testing.assert_close(a[name], b[name], rtol=0, atol=0)
        with self.assertRaises(FileExistsError):
            save_artifact(root / 'good', head, meta)
        pretrained = dict(actual_meta)
        pretrained['config'] = dict(pretrained['config'], stem_pretrained=True, stem_weights='/absent/local/weights.pth')
        folder = root / 'portable'
        folder.mkdir()
        (folder / 'mdg.json').write_text(json.dumps(pretrained))
        torch.save(head.state_dict(), folder / 'mdg.pt')
        with mock.patch('torch.hub.download_url_to_file', side_effect=AssertionError('network forbidden')):
            load_artifact(folder)
        torch.save({}, folder / 'mdg.pt')
        with self.assertRaises(RuntimeError):
            load_artifact(folder)
        with self.assertRaises(ValueError):
            save_artifact(root / 'bad', head, dict(meta, schema='bad'))
        with self.assertRaises(ValueError):
            save_artifact(root / 'bad', head, dict(meta, tau=float('nan')))

    def test_configuration_and_input_guards(self):
        for kwargs in (dict(dim=15), dict(heads=3), dict(points=0), dict(oversample=.5),
                       dict(importance=1.1), dict(presence_prior=1), dict(w_iou=float('nan'))):
            with self.assertRaises(ValueError):
                config(**kwargs)
        head = MaskGroundingHead(config())
        inputs = features(head.cfg)
        with self.assertRaises(ValueError):
            head.encode_video(*inputs[:3], (0, 2))
        with self.assertRaises(ValueError):
            head.encode_video(inputs[0], inputs[1][:1], inputs[2], (1, 2))
        with self.assertRaises(ValueError):
            head.encode_video(*inputs[:3], (2, 2))
        with self.assertRaises(ValueError):
            head(head.encode_video(*inputs[:3], (1, 2)), inputs[3], inputs[4], inputs[5].float())

    @unittest.skipUnless(os.environ.get('MDG_HEAD_BENCHMARK') == '1', 'opt-in full-size single CPU run')
    def test_full_size_cpu_measurement(self):
        cfg = MDGConfig(vit_dim=1152)
        head = MaskGroundingHead(cfg)
        inputs = features(cfg, frames=32, labels=34, grid=(10, 14))
        target = targets(labels=34, frames=32, shape=(240, 320))
        target['clip_present'][24:] = 0
        target['frame_valid'][24:] = False
        target['mask_valid'][24:] = False
        target['masks'][24:] = False
        baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        start = time.perf_counter()
        outs = run(head, inputs, grid=(10, 14))
        parts = head.loss(outs, target)
        parts['total'].backward()
        elapsed = time.perf_counter() - start
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print('MDG_CPU_MEASUREMENT ' + json.dumps(dict(
            Q=34, F=32, grid=[10, 14], dim=512, lm_dim=4096, vit_dim=1152,
            points=cfg.points, blocks=cfg.blocks, threads=torch.get_num_threads(),
            mask_valid_pairs=int(target['mask_valid'].sum()), loss=float(parts['total'].detach()),
            seconds=elapsed, peak_rss_mib=peak / 1024,
            pre_forward_high_water_mib=baseline / 1024, high_water_growth_mib=(peak - baseline) / 1024,
        ), sort_keys=True), flush=True)
        self.assertTrue(torch.isfinite(parts['total']))


if __name__ == '__main__':
    unittest.main()
