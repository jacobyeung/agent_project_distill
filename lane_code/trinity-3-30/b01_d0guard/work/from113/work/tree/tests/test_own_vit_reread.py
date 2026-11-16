"""Native tiny-Qwen tests; synthetic pixels only, no checkpoints or evaluation scans."""
import copy
from dataclasses import replace
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch
from torch.nn import functional as F
from transformers import Qwen2VLImageProcessorPil
from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel

from student_pilot.reread import Config, ReRead, rgb_hash
from student_pilot.point_depth_head import vit_grids_by_row


def fixture():
    torch.manual_seed(13)
    config = Qwen3_5VisionConfig(depth=4, hidden_size=32, intermediate_size=48,
                num_heads=4, out_hidden_size=32, num_position_embeddings=16,
                patch_size=16, temporal_patch_size=2, spatial_merge_size=2)
    config._attn_implementation = 'sdpa'
    visual = Qwen3_5VisionModel(config).float().eval()
    model = torch.nn.Module()
    model.model = torch.nn.Module()
    model.model.visual = visual
    model.model.rope_deltas = torch.tensor([[37]])
    model.eval()
    proc = Qwen2VLImageProcessorPil(patch_size=16, temporal_patch_size=2, merge_size=2)
    rng = np.random.default_rng(8)
    frames = {i: rng.integers(0, 256, size=(320, 448, 3), dtype=np.uint8) for i in (1, 2, 3)}
    return model, proc, frames


def bind(model, proc, frames, **kwargs):
    return ReRead(model, layers=(1, 2, 3, 4), **kwargs).bind_clip('a' * 64, frames, processor=proc)


class ReReadTests(unittest.TestCase):
    def test_320_448_native_prefill_taps_fp32_exact(self):
        model, proc, frames = fixture()
        packed = proc(images=list(frames.values()), do_resize=False, return_tensors='pt')
        # A duplicate-frame video prefill uses these same native patch vectors.
        grid = torch.tensor([[3, 20, 28]])
        captured, handles = {}, []
        for k in (1, 2, 3, 4):
            handles.append(model.model.visual.blocks[k-1].register_forward_hook(
                lambda m, a, o, k=k: captured.__setitem__(k, o.detach().clone())))
        with torch.no_grad():
            model.model.visual(packed['pixel_values'], grid_thw=grid)
        for h in handles:
            h.remove()
        reader = bind(model, proc, frames)
        taps = reader.features((3, 1, 2), (320, 448))
        for k, raw in captured.items():
            expected = vit_grids_by_row(raw, grid, 2)[0][[2, 0, 1]]
            torch.testing.assert_close(taps[k], expected, rtol=0, atol=0)
        self.assertEqual(reader.forward_calls, 3)
        self.assertTrue(all(not v.requires_grad for v in taps.values()))

    def test_cache_chunk_order_duplicate_slots_and_rebind(self):
        model, proc, frames = fixture()
        reader = bind(model, proc, frames, chunk_size=2)
        first = reader.features((3, 1, 3, 2), (320, 448))
        self.assertEqual((reader.forward_calls, reader.frames_encoded), (2, 3))
        second = reader.features((1, 3), (320, 448))
        self.assertEqual(reader.forward_calls, 2)
        torch.testing.assert_close(first[1][[1, 0]], second[1], rtol=0, atol=0)
        second[1].zero_()
        torch.testing.assert_close(reader.features((1,), (320, 448))[1][0], first[1][1], rtol=0, atol=0)
        altered = {1: np.zeros_like(frames[1])}
        reader.bind_clip('b' * 64, altered, processor=proc)
        changed = reader.features((1,), (320, 448))
        self.assertFalse(torch.equal(changed[1][0], first[1][1]))
        self.assertEqual(reader.forward_calls, 3)

    def test_cache_budget_and_size_keys(self):
        model, proc, frames = fixture()
        reader = bind(model, proc, frames, max_cache_bytes=4*20*28*32*4)
        reader.features((1, 2), (320, 448))
        self.assertEqual(len(reader.cache), 1)
        reader.features((2,), (320, 448))
        self.assertEqual(reader.forward_calls, 2)
        high = reader.features((2,), (480, 640))
        self.assertEqual(high[1].shape, (1, 30, 40, 32))
        self.assertLessEqual(reader.cache_bytes, reader.max_cache_bytes)

    def test_failure_removes_hooks_and_preserves_rope_parameters_optimizer(self):
        model, proc, frames = fixture()
        reader = bind(model, proc, frames)
        state = {k: v.clone() for k, v in model.state_dict().items()}
        optimizer = torch.optim.AdamW(model.parameters())
        groups = [[id(p) for p in g['params']] for g in optimizer.param_groups]
        train_flags = [m.training for m in model.modules()]
        rope = model.model.rope_deltas
        hooks = [len(b._forward_hooks) for b in model.model.visual.blocks]
        with patch.object(model.model.visual.blocks[1], 'forward', side_effect=RuntimeError('fixture failure')):
            with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
                reader.features((1,), (320, 448))
        self.assertEqual(hooks, [len(b._forward_hooks) for b in model.model.visual.blocks])
        self.assertIs(model.model.rope_deltas, rope)
        self.assertEqual(train_flags, [m.training for m in model.modules()])
        self.assertEqual(groups, [[id(p) for p in g['params']] for g in optimizer.param_groups])
        reader.features((1,), (320, 448))
        self.assertEqual(set(state), set(model.state_dict()))
        for k, value in state.items():
            self.assertTrue(torch.equal(value, model.state_dict()[k]), k)
        self.assertTrue(all(p.grad is None for p in model.parameters()))

    def test_validation_and_model_mutation(self):
        model, proc, frames = fixture()
        reader = bind(model, proc, frames)
        for ids, size in [((0,), (320, 448)), ((True,), (320, 448)), ((4,), (320, 448)),
                          ((1,), (321, 448)), ((), (320, 448))]:
            with self.assertRaises(ValueError):
                reader.features(ids, size)
        model.train()
        with self.assertRaisesRegex(ValueError, 'eval'):
            reader.features((1,), (320, 448))
        model.eval()
        with torch.no_grad():
            next(model.parameters()).add_(1)
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            reader.features((1,), (320, 448))

    def test_native_prefill_pack_reuse(self):
        model, proc, frames = fixture()
        pack = proc(images=list(frames.values()), do_resize=False, return_tensors='pt')
        batch = dict(video_grid_thw=torch.tensor([[3, 20, 28]]), pixel_values_videos=pack['pixel_values'])
        reader = ReRead(model, layers=(1, 4)).bind_clip('c'*64, frames, prefill_batch=batch)
        result = reader.features((2, 1), (320, 448))
        native = bind(model, proc, frames).features((2, 1), (320, 448))
        for k in result:
            torch.testing.assert_close(result[k], native[k], rtol=0, atol=0)
        with self.assertRaisesRegex(ValueError, 'processor'):
            reader.features((2,), (480, 640))

    def test_sdpa_path_observed_and_forced_math(self):
        model, proc, frames = fixture()
        reader = bind(model, proc, frames, sdpa_backend='math')
        with patch.object(F, 'scaled_dot_product_attention', wraps=F.scaled_dot_product_attention) as spy:
            reader.features((1,), (320, 448))
        self.assertEqual(spy.call_count, 4)
        model.model.visual.config._attn_implementation = 'eager'
        reader.bind_clip('a'*64, frames, processor=proc)
        with self.assertRaisesRegex(ValueError, 'requires vision'):
            reader.features((1,), (320, 448))

    def test_vc_matches_existing_bf16_functional_path(self):
        model, proc, frames = fixture()
        model.auxiliary_heads = torch.nn.Module()
        model.auxiliary_heads.depth = torch.nn.Module()
        model.auxiliary_heads.depth.model = torch.nn.Module()
        model.auxiliary_heads.depth.model.visual = copy.deepcopy(model.model.visual)
        model.eval()
        visual = model.auxiliary_heads.depth.model.visual
        captured = []
        handle = visual.blocks[3].register_forward_hook(lambda m, a, o: captured.append(o.detach().clone()))
        pack = proc(images=[frames[1]], do_resize=False, return_tensors='pt')
        with torch.no_grad():
            torch.func.functional_call(visual, {n: p.to(torch.bfloat16) for n, p in visual.named_parameters()},
                (pack['pixel_values'].to(torch.bfloat16),), {'grid_thw': pack['image_grid_thw']})
        handle.remove()
        reader = ReRead(model, layers=(4,), tower='vc').bind_clip('d'*64, frames, processor=proc)
        actual = reader.features((1,), (320, 448))[4]
        expected = vit_grids_by_row(captured[0], pack['image_grid_thw'], 2)[0]
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)
        self.assertEqual(next(visual.parameters()).dtype, torch.float32)


class DecodeTests(unittest.TestCase):
    def prepare(self):
        from tests.test_grounding_decode import fixture as routed_fixture
        model, processor, batch = routed_fixture()
        frames = {i: np.full((4, 4, 3), i, dtype=np.uint8) for i in range(1, 33)}
        batch.update(video_sha256='e'*64, frame_indices=list(range(32)),
                     frame_rgb_sha256=[rgb_hash(v) for v in frames.values()])
        config = Config(frames=frames, frame_indices=tuple(range(32)), clip_key='e'*64,
                        layers=(1, 2, 3), size_hw=(4, 4), preload_ids=(1, 4), chunk_size=1)
        return model, processor, batch, config

    def run_decode(self, model, processor, batch):
        from student_pilot.carrier_c1_decode import generate
        def eos(ids, logits):
            values = torch.full_like(logits, -1e9)
            values[:, 42 if not ids else 1] = 0
            return values
        if isinstance(batch, list):
            return generate(model, processor, batch, logits_processor=[eos] * len(batch))
        return generate(model, processor, batch, logits_processor=eos)

    def test_generate_lm_hidden_bytes_cache_and_record_equal(self):
        model, proc, batch, cfg = self.prepare()
        captured = []
        handle = model.model.language_model.norm.register_forward_hook(
            lambda m, a, o: captured.append(o.detach().clone()))
        baseline = self.run_decode(model, proc, batch)
        baseline_hidden = captured[:]
        captured.clear()
        state = {k: v.clone() for k, v in model.state_dict().items()}
        reads = []
        original = ReRead.features
        def observe(reader, ids, size):
            self.assertEqual(len(captured), 1)  # Inside generate, after the prefill.
            rope = model.model.rope_deltas
            result = original(reader, ids, size)
            self.assertIs(model.model.rope_deltas, rope)
            reads.append(reader)
            return result
        with patch.object(ReRead, 'features', observe):
            enabled = self.run_decode(model, proc, {**batch, 'own_vit_reread': cfg})
        handle.remove()
        self.assertEqual(baseline, enabled)
        self.assertEqual(len(reads), 1)
        self.assertEqual(reads[0].frames_encoded, 2)
        self.assertEqual(len(baseline_hidden), len(captured))
        for a, b in zip(baseline_hidden, captured):
            self.assertEqual(a.contiguous().view(torch.uint8).numpy().tobytes(),
                             b.contiguous().view(torch.uint8).numpy().tobytes())
        for k, v in state.items():
            self.assertTrue(torch.equal(v, model.state_dict()[k]))

    def test_batched_rows_have_independent_readers_and_flags_off_parity(self):
        model, proc, batch, cfg = self.prepare()
        baseline = self.run_decode(model, proc, [batch, batch])
        readers = []
        original = Config.bind
        def record(config, *args):
            result = original(config, *args)
            readers.append(result)
            return result
        with patch.object(Config, 'bind', record):
            actual = self.run_decode(model, proc, [{**batch, 'own_vit_reread': cfg},
                                                   {**batch, 'own_vit_reread': cfg}])
        self.assertEqual(baseline, actual)
        self.assertEqual(len(readers), 2)
        self.assertIsNot(readers[0].cache, readers[1].cache)
        self.assertEqual([r.frames_encoded for r in readers], [2, 2])

    def test_frame_identity_rejected_before_prefill(self):
        model, proc, batch, cfg = self.prepare()
        bad = {**batch, 'frame_indices': list(reversed(range(32))), 'own_vit_reread': cfg}
        with patch.object(model.model.visual, 'forward', side_effect=AssertionError('prefill ran')):
            with self.assertRaisesRegex(ValueError, 'source indices'):
                self.run_decode(model, proc, bad)
        bad = {**batch, 'frame_rgb_sha256': ['0'*64] * 32, 'own_vit_reread': cfg}
        with self.assertRaisesRegex(ValueError, 'RGB differs'):
            self.run_decode(model, proc, bad)

    def test_live_prefill_kv_and_recurrent_cache_bytes_unchanged(self):
        from student_pilot.carrier_c1_decode import _prepare_decode
        model, proc, batch, cfg = self.prepare()
        cfg = replace(cfg, preload_ids=())
        with torch.no_grad():
            state = _prepare_decode(model, proc, {**batch, 'own_vit_reread': cfg})
        cache = state.output.past_key_values
        def tensors(obj, prefix='', seen=None):
            seen = set() if seen is None else seen
            if id(obj) in seen:
                return {}
            seen.add(id(obj))
            if isinstance(obj, torch.Tensor):
                return {prefix: (id(obj), obj.contiguous().view(torch.uint8).numpy().tobytes())}
            items = (obj.items() if isinstance(obj, dict) else enumerate(obj) if isinstance(obj, (list, tuple))
                     else vars(obj).items() if hasattr(obj, '__dict__') else [])
            result = {}
            for k, value in items:
                result.update(tensors(value, f'{prefix}/{k}', seen))
            return result
        before = tensors(cache)
        self.assertTrue(any('keys' in k for k in before))
        self.assertTrue(any('recurrent' in k for k in before))
        rope = model.model.rope_deltas
        state.heads.own_rereader.features((4, 1), (4, 4))
        self.assertIs(model.model.rope_deltas, rope)
        self.assertEqual(before, tensors(cache))


if __name__ == '__main__':
    unittest.main()
