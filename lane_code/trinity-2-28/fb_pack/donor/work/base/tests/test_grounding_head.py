"""CPU contracts for dense grounding, local points, and portable artifacts."""
import json
import math
import os
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest import mock

import torch
from torch.nn import functional as F

from student_pilot.grounding_head import GHConfig, GroundingHead, load_artifact, save_artifact


def config(**kwargs):
    return GHConfig(**dict(vit_dim=8, lm_dim=16, dim=16, heads=4, frames=4, blocks=2,
                           text_layers=1, **kwargs))


def features(cfg, grid=(2, 3), labels=2, dtype=torch.float32):
    gh, gw = grid
    taps = [torch.randn(cfg.frames, gh * gw, cfg.lm_dim, dtype=dtype) for _ in range(cfg.n_taps)]
    vit = torch.randn(cfg.frames, 2 * gh, 2 * gw, cfg.vit_dim, dtype=dtype)
    phrase = torch.randn(labels, 3, cfg.lm_dim, dtype=dtype)
    mask = torch.tensor([[True, True, False]]).expand(labels, -1)
    return taps, vit, phrase, mask


def targets(shape):
    labels, frames, height, width = shape
    presence = torch.ones(labels, frames)
    presence[:, 1::2] = 0
    mass = torch.zeros(shape)
    mass[..., 0, 0] = presence
    point = torch.empty(labels, frames, 2)
    point[..., 0], point[..., 1] = 500 / width, 500 / height
    return dict(presence=presence, presence_valid=torch.ones_like(presence, dtype=torch.bool),
                mass=mass, point=point, point_valid=presence.bool())


class GroundingHeadTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)

    def test_default_parameter_count(self):
        with torch.device('meta'):
            head = GroundingHead(GHConfig(vit_dim=1152))
        count = sum(p.numel() for p in head.parameters())
        print(f'GroundingHead default parameters: {count:,}', flush=True)
        self.assertGreater(count, 20_000_000)
        self.assertLess(count, 50_000_000)

    def test_shapes_backward_and_frozen_inputs_for_two_grids(self):
        for grid in ((2, 3), (3, 4)):
            with self.subTest(grid=grid):
                cfg = config()
                head = GroundingHead(cfg)
                taps, vit, phrase, mask = features(cfg, grid)
                for value in [*taps, vit, phrase]:
                    value.requires_grad_()
                out = head(head.encode_video(taps, vit, grid), head.encode_query(phrase, mask))
                self.assertEqual(out['presence'].shape, (2, cfg.frames))
                self.assertEqual(out['heat'].shape, (2, cfg.frames, 2 * grid[0], 2 * grid[1]))
                losses = head.loss(out, targets(out['heat'].shape))
                self.assertEqual(set(losses), {'total', 'presence', 'heat', 'point'})
                self.assertTrue(all(torch.isfinite(value) for value in losses.values()))
                losses['total'].backward()
                for name, parameter in head.named_parameters():
                    self.assertIsNotNone(parameter.grad, name)
                    self.assertTrue(torch.isfinite(parameter.grad).all(), name)
                self.assertTrue(all(value.grad is None for value in [*taps, vit, phrase]))

    def test_own_frame_attention_has_no_global_token_axis(self):
        cfg = config()
        head = GroundingHead(cfg)
        taps, vit, phrase, mask = features(cfg)
        seen = []
        original = F.scaled_dot_product_attention
        def attention(q, k, v, **kwargs):
            seen.append((q.shape, k.shape))
            return original(q, k, v, **kwargs)
        with mock.patch('torch.nn.functional.scaled_dot_product_attention', side_effect=attention):
            head(head.encode_video(taps, vit, (2, 3)), head.encode_query(phrase, mask))
        block_calls = seen[cfg.text_layers:]
        self.assertEqual(len(block_calls), cfg.blocks * 3)
        for i in range(cfg.blocks):
            self_call, cross, reverse = block_calls[3 * i:3 * i + 3]
            self.assertEqual((self_call[0][0], self_call[0][-2], self_call[1][-2]), (2, 4, 4))
            self.assertEqual((cross[0][0], cross[0][-2], cross[1][-2]), (8, 1, 6))
            self.assertEqual((reverse[0][0], reverse[0][-2], reverse[1][-2]), (8, 6, 1))

    def test_balanced_bce_matches_hand_computation_and_empty_classes(self):
        head = GroundingHead(config())
        logits = torch.tensor([[math.log(3), 0., -math.log(3), math.log(3)]], requires_grad=True)
        out = dict(presence=logits, heat=torch.zeros(1, 4, 2, 2, requires_grad=True))
        target = targets(out['heat'].shape)
        target['presence'] = torch.tensor([[1., 1., 0., float('nan')]])
        result = head.loss(out, target)
        expected = .5 * ((-math.log(.75) - math.log(.5)) / 2 - math.log(.75))
        self.assertAlmostEqual(result['presence'].item(), expected, places=6)
        for value in (0., 1.):
            target['presence'].fill_(value)
            expected = .5 * sum(math.log1p(math.exp((1 - 2 * value) * x)) for x in logits[0].tolist()) / 4
            self.assertAlmostEqual(head.loss(out, target)['presence'].item(), expected, places=6)

    def test_heat_ce_matches_hand_computation_on_2x2(self):
        head = GroundingHead(config())
        heat = torch.tensor([[[[1., 2.], [3., 4.]], [[9., 7.], [6., 3.]]]], requires_grad=True)
        target = targets(heat.shape)
        target['mass'][0, 0] = torch.tensor([[.1, .2], [.3, .4]])
        actual = head.loss(dict(presence=torch.zeros(1, 2), heat=heat), target)['heat']
        expected = math.log(sum(math.exp(x) for x in (1, 2, 3, 4))) - 3
        self.assertAlmostEqual(actual.item(), expected, places=6)

    def test_decode_one_hot_cell_centres_and_clipped_edge_window(self):
        heat = torch.full((1, 2, 4, 6), -torch.inf)
        heat[0, 0, 2, 3], heat[0, 1, 0, 0] = 0., 0.
        decoded = GroundingHead.decode(dict(presence=torch.zeros(1, 2), heat=heat))
        self.assertEqual(decoded['uv'].tolist(), [[[583, 625], [83, 125]]])
        self.assertTrue(torch.equal(decoded['prob'], torch.full((1, 2), .5)))
        heat = torch.full((1, 1, 4, 4), -50.)
        heat[0, 0, :2, :2] = torch.tensor([[math.log(4), math.log(2)], [0., 0.]])
        # The distant cell has mass but lies outside the selected local window.
        heat[0, 0, 3, 3] = math.log(3)
        uv = GroundingHead.decode(dict(presence=torch.zeros(1, 1), heat=heat))['uv']
        self.assertEqual(uv.tolist(), [[[219, 188]]])

    def test_training_point_uses_prediction_window_and_soft_weights(self):
        head = GroundingHead(config())
        heat = torch.full((1, 1, 4, 4), -10., requires_grad=True)
        with torch.no_grad():
            heat[0, 0, :2, :2] = torch.tensor([[math.log(4), math.log(2)], [0., 0.]])
            heat[0, 0, 3, 3] = math.log(3)
        target = targets(heat.shape)
        target['point'].fill_(875.)
        point_loss = head.loss(dict(presence=torch.zeros(1, 1), heat=heat), target)['point']
        self.assertAlmostEqual(point_loss.item(), ((875 - 218.75) + (875 - 187.5)) / 2000, places=6)
        point_loss.backward()
        self.assertGreater(heat.grad[0, 0, :2, :2].abs().sum().item(), 0)
        self.assertEqual(heat.grad[0, 0, 3, 3].item(), 0)

    def test_loss_ignores_nan_and_invalid_entries(self):
        head = GroundingHead(config())
        out = dict(presence=torch.randn(1, 4, requires_grad=True), heat=torch.randn(1, 4, 2, 2, requires_grad=True))
        target = targets(out['heat'].shape)
        target['presence'][0, 1] = float('nan')
        target['presence_valid'][0, 2:] = False
        target['mass'][0, 1:] = float('nan')
        target['point'][0, 1:] = float('nan')
        actual = head.loss(out, target)
        sliced = {key: value[:, :1] for key, value in out.items()}
        sliced_target = {key: value[:, :1] for key, value in target.items()}
        expected = head.loss(sliced, sliced_target)
        for name in actual:
            torch.testing.assert_close(actual[name], expected[name])
        actual['total'].backward()
        self.assertTrue(torch.isfinite(out['heat'].grad).all())
        self.assertEqual(out['heat'].grad[:, 1:].abs().sum().item(), 0)
        target['presence_valid'].fill_(False)
        zero = head.loss(out, target)
        self.assertTrue(all(value.item() == 0 for value in zero.values()))
        zero['total'].backward()

    def test_invalid_mass_and_point_are_ignored_independently(self):
        head = GroundingHead(config())
        out = dict(presence=torch.zeros(1, 2), heat=torch.zeros(1, 2, 2, 2, requires_grad=True))
        target = targets(out['heat'].shape)
        target['presence'].fill_(1)
        target['mass'][0, 0].fill_(float('nan'))
        target['mass'][0, 1, 1, 1] = 1
        target['point_valid'].fill_(True)
        target['point'][0, 1].fill_(float('nan'))
        loss = head.loss(out, target)
        self.assertAlmostEqual(loss['heat'].item(), math.log(4), places=6)
        self.assertTrue(torch.isfinite(loss['point']))

    def test_fp32_head_on_bf16_inputs_and_outer_autocast(self):
        cfg = config()
        head = GroundingHead(cfg)
        taps, vit, phrase, mask = features(cfg, dtype=torch.bfloat16)
        with torch.autocast('cpu', dtype=torch.bfloat16):
            memory, query = head.encode_video(taps, vit, (2, 3)), head.encode_query(phrase, mask)
            out = head(memory, query)
            loss = head.loss(out, targets(out['heat'].shape))
        self.assertTrue(all(value.dtype == torch.float32 for value in out.values()))
        self.assertTrue(all(value.dtype == torch.float32 for value in loss.values()))
        loss['total'].backward()
        self.assertTrue(all(p.dtype == torch.float32 and p.grad is not None for p in head.parameters()))

    def test_text_padding_does_not_change_query(self):
        cfg = config()
        head = GroundingHead(cfg).eval()
        _, _, phrase, mask = features(cfg)
        expected = head.encode_query(phrase[:, :2], mask[:, :2])
        phrase[:, 2] = float('nan')
        torch.testing.assert_close(head.encode_query(phrase, mask), expected)
        empty = head.encode_query(phrase[:, :0], mask[:, :0])
        self.assertEqual(empty.shape, (2, cfg.dim))
        self.assertTrue(torch.isfinite(empty).all())

    def test_token_update_can_be_disabled(self):
        cfg = config(token_update=False)
        head = GroundingHead(cfg)
        taps, vit, phrase, mask = features(cfg)
        out = head(head.encode_video(taps, vit, (2, 3)), head.encode_query(phrase, mask))
        head.loss(out, targets(out['heat'].shape))['total'].backward()
        self.assertTrue(all(p.grad is not None for p in head.parameters()))

    def test_200_step_synthetic_overfit(self):
        cfg = config()
        head = GroundingHead(cfg)
        taps, vit, phrase, mask = features(cfg, (2, 2))
        flag = torch.tensor([1., 0., 1., 0.])
        for tap in taps:
            tap[..., 0] = (flag * 2 - 1)[:, None] * 4
        target = targets((2, 4, 4, 4))
        target['mass'].zero_()
        cells = torch.randint(0, 16, (2, 4))
        for q in range(2):
            for f in range(4):
                row, col = divmod(cells[q, f].item(), 4)
                vit[f, row, col, q] += 6
                if flag[f]:
                    target['mass'][q, f, row, col] = 1
                target['point'][q, f] = torch.tensor([(col + .5) * 250, (row + .5) * 250])
        optimizer = torch.optim.Adam(head.parameters(), lr=.003)
        for _ in range(200):
            optimizer.zero_grad(set_to_none=True)
            out = head(head.encode_video(taps, vit, (2, 2)), head.encode_query(phrase, mask))
            loss = head.loss(out, target)['total']
            self.assertTrue(torch.isfinite(loss))
            loss.backward()
            optimizer.step()
        with torch.no_grad():
            out = head(head.encode_video(taps, vit, (2, 2)), head.encode_query(phrase, mask))
            decoded = head.decode(out)
        accuracy = ((decoded['prob'] >= .5) == target['presence'].bool()).float().mean().item()
        error = ((decoded['uv'].float() - target['point']) / 250).norm(dim=-1)[target['point_valid']]
        print(f'GroundingHead synthetic overfit: presence={accuracy:.3f}, max point error={error.max().item():.4f} cells', flush=True)
        self.assertEqual(accuracy, 1.)
        self.assertLess(error.max().item(), 1.)

    def test_artifact_round_trip_schema_and_strict_state(self):
        cfg = config()
        head = GroundingHead(cfg).eval()
        root = Path(tempfile.mkdtemp(prefix='grounding_head_', dir=os.environ['LANE_TEST_OUTPUT']))
        meta = dict(tau=.6, base_artifact=dict(path='/frozen/T0/artifact.json', sha256='a' * 64),
                    trainer_commit='fixture', step=200, metrics=dict(loss=.01))
        save_artifact(root / 'good', head, meta)
        loaded, actual_meta = load_artifact(root / 'good')
        self.assertEqual(actual_meta, dict(meta, schema='grounding-head-v1', config=asdict(cfg)))
        for name, value in head.state_dict().items():
            self.assertTrue(torch.equal(value, loaded.state_dict()[name]), name)
        taps, vit, phrase, mask = features(cfg)
        with torch.no_grad():
            expected = head(head.encode_video(taps, vit, (2, 3)), head.encode_query(phrase, mask))
            actual = loaded(loaded.encode_video(taps, vit, (2, 3)), loaded.encode_query(phrase, mask))
        self.assertTrue(all(torch.equal(expected[k], actual[k]) for k in expected))
        with self.assertRaises(FileExistsError):
            save_artifact(root / 'good', head, meta)
        for name in ('missing', 'extra', 'schema'):
            folder = root / name
            folder.mkdir()
            state = dict(head.state_dict())
            metadata = dict(actual_meta)
            if name == 'missing':
                state.pop('tap_mix')
            elif name == 'extra':
                state['foreign.weight'] = torch.zeros(1)
            else:
                metadata['schema'] = 'foreign-head-v1'
            torch.save(state, folder / 'gh.pt')
            (folder / 'gh.json').write_text(json.dumps(metadata))
            with self.assertRaises(ValueError if name == 'schema' else RuntimeError):
                load_artifact(folder)

    def test_configuration_and_artifact_validation(self):
        for overrides in (dict(dim=15), dict(dropout=1.), dict(point_weight=float('nan')), dict(frames=0)):
            values = asdict(config())
            values.update(overrides)
            with self.assertRaises(ValueError):
                GHConfig(**values)
        head = GroundingHead(config())
        root = Path(tempfile.mkdtemp(prefix='grounding_invalid_', dir=os.environ['LANE_TEST_OUTPUT']))
        with self.assertRaises(ValueError):
            save_artifact(root, head, dict(schema='wrong'))


if __name__ == '__main__':
    unittest.main()
