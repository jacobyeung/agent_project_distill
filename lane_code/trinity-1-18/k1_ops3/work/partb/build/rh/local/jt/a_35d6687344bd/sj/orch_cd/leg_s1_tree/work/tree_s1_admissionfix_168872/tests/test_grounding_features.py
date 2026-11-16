"""Native C1 prefill parity and merge-window raster regressions."""
from types import SimpleNamespace
import copy
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_decode as decode, grounding_features as features
from student_pilot.carrier_c1_data import insert_frame_carriers, C1_A, C1_B, C1_C
from tests.test_carrier_c1_final import final_fixture, FakeTokenizer


class MarkerTokenizer:
    _c1_frame_markers = True

    def encode(self, text, **kwargs):
        return [5] if text == '<|fim_middle|>' else [20, 21]

    def convert_tokens_to_ids(self, token):
        return {'<|fim_middle|>': 5, '<|vision_start|>': 62, '<|video_pad|>': 61}[token]


def tiny_clip(frames=32, h=4, w=4, placement=C1_A):
    model, _, _ = final_fixture(placement)
    model.frame_layout = 'duplicate'
    model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    ids = torch.tensor([[2] + [x for _ in range(frames) for x in [62] + [61] * (h * w // 4) + [63]] + [10, 11]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), mm_token_type_ids=torch.where(ids == 61, 2, 0),
        video_grid_thw=torch.tensor([[frames, h, w]]), pixel_values_videos=torch.randn(frames * h * w, 24))
    batch = insert_frame_carriers(batch, MarkerTokenizer(), carrier_placement=placement, frame_layout='duplicate')
    return model.eval().requires_grad_(False), batch


class Features(unittest.TestCase):
    def test_production_tap_indices_match_native_hidden_states(self):
        from transformers import Qwen3_5ForConditionalGeneration
        model, batch = tiny_clip(h=2, w=2)
        config = copy.deepcopy(model.config)
        config.text_config.num_hidden_layers = 26
        config.text_config.layer_types = ['linear_attention', 'full_attention'] * 13
        native = Qwen3_5ForConditionalGeneration(config).float()
        model.config = model.model.config = config
        model.model.language_model, model.lm_head = native.model.language_model, native.lm_head
        model.eval().requires_grad_(False)
        original, states = model.model.language_model.forward, []
        def hidden_states(*args, **kwargs):
            output = original(*args, **{**kwargs, 'output_hidden_states': True})
            states.append(output.hidden_states)
            return output
        with mock.patch.object(model.model.language_model, 'forward', side_effect=hidden_states):
            captured = features.capture(model, batch)
        index = features.frame_token_index(batch)
        self.assertEqual(len(states), 1)
        for tap, layer in zip(captured.taps, (16, 24, 26)):
            self.assertTrue(torch.equal(tap, states[0][layer][0, index].to(torch.bfloat16)))
        changed = {**batch, 'input_ids': batch['input_ids'].clone()}
        changed['input_ids'][0, -2:] = torch.tensor([15, 16])
        other = features.capture(model, changed)
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(captured.taps, other.taps)))

    def test_frame_runs_with_markers_and_carriers(self):
        for frames in (2, 32):
            with self.subTest(frames=frames):
                _, batch = tiny_clip(frames)
                index = features.frame_token_index(batch)
                self.assertEqual(tuple(index.shape), (frames, 4))
                self.assertTrue((batch['input_ids'][0, index] == 61).all())
                self.assertTrue((index[:, 1:] - index[:, :-1] == 1).all())
                self.assertTrue((batch['input_ids'][0, index[:, 0] - 1] == 62).all())
                self.assertTrue((batch['input_ids'][0, index[:, 0] - 2] == 21).all())
                self.assertTrue((batch['input_ids'][0, index[:, -1] + 1] == 5).all())
                broken = dict(batch)
                broken['mm_token_type_ids'] = batch['mm_token_type_ids'].clone()
                broken['mm_token_type_ids'][0, index[0, 0]] = 0
                with self.assertRaisesRegex(ValueError, 'count'):
                    features.frame_token_index(broken)

    def test_capture_equals_decode_prefill_and_hf_tap(self):
        for placement in (C1_A, C1_B, C1_C):
            with self.subTest(placement=placement), mock.patch.object(features, 'TAP_LAYERS', (1, 1)):
                model, batch = tiny_clip(placement=placement)
                processor = SimpleNamespace(tokenizer=FakeTokenizer(), _routing_tokens={'ids': {'<pose': 39}})
                captured = features.capture(model, batch)
                norm, hf = [], []
                original = model.model.language_model.forward
                def with_states(*args, **kwargs):
                    result = original(*args, **{**kwargs, 'output_hidden_states': True})
                    hf.append(result.hidden_states)
                    return result
                with features.capture_from_hooks(model, batch) as observed, mock.patch.object(
                        model.model.language_model, 'forward', side_effect=with_states):
                    handle = model.model.language_model.norm.register_forward_hook(lambda module, args, out: norm.append(out.detach()))
                    try:
                        def eos(ids, logits):
                            result = torch.full_like(logits, -1e9); result[:, 1] = 0
                            return result
                        record = decode.generate(model, processor, batch, logits_processor=eos)
                    finally:
                        handle.remove()
                self.assertEqual(record['finish'], 'eos')
                self.assertTrue(torch.equal(captured.hidden, norm[0]))
                self.assertTrue(torch.equal(observed.finish().hidden, captured.hidden))
                index = features.frame_token_index(batch)
                self.assertTrue(torch.equal(captured.taps[0], hf[0][1][0, index].to(torch.bfloat16)))
                self.assertTrue(torch.equal(captured.taps[-1], hf[0][-1][0, index].to(torch.bfloat16)))
                self.assertEqual(captured.grid, (2, 2))
                self.assertEqual(tuple(captured.vit.shape), (32, 4, 4, 32))
                self.assertTrue(all(not value.requires_grad for value in [*captured.taps, captured.vit, captured.hidden]))

    def test_known_vit_raster_and_merged_output_order(self):
        model, batch = tiny_clip(h=4, w=8)
        raster = torch.arange(32 * 4 * 8).reshape(32, 4, 8, 1).expand(-1, -1, -1, 32).float()
        packed = raster.reshape(32, 2, 2, 4, 2, 32).permute(0, 1, 3, 2, 4, 5).reshape(-1, 32)
        with mock.patch.object(features, 'TAP_LAYERS', (1, 1)), features.capture_from_hooks(model, batch) as captured:
            model.model.visual.merger(packed)
            length = batch['input_ids'].shape[1]
            hidden = torch.arange(length).float()[None, :, None].expand(1, -1, 32)
            for hook in model.model.language_model.layers[0]._forward_hooks.values():
                hook(model.model.language_model.layers[0], (), hidden)
            model.model.language_model.norm(hidden)
        result = captured.finish()
        self.assertTrue(torch.equal(result.vit, raster))
        merged_cells = packed.reshape(32, 2, 4, 4, 32).mean(3)[..., 0]
        expected = raster[..., 0].reshape(32, 2, 2, 4, 2).mean((2, 4))
        self.assertTrue(torch.equal(merged_cells, expected))
        self.assertTrue(torch.equal(result.taps[0][..., 0], features.frame_token_index(batch).to(torch.bfloat16)))

    def test_phrase_embeddings_padding_and_freezing(self):
        model, _ = tiny_clip()
        tokenizer = SimpleNamespace(encode=lambda text, **kwargs: [2] * len(text))
        embeds, mask = features.phrase_embeddings(model, tokenizer, ['a', 'abc'])
        self.assertEqual(tuple(embeds.shape), (2, 3, 32))
        self.assertEqual(mask.tolist(), [[True, False, False], [True, True, True]])
        self.assertFalse(embeds.requires_grad)
        self.assertTrue((embeds[0, 1:] == 0).all())
        with self.assertRaisesRegex(ValueError, 'Empty'):
            features.phrase_embeddings(model, tokenizer, [''])

    def test_short_capture_and_type_drift_refuse_and_hooks_cleanup(self):
        model, batch = tiny_clip(2)
        hooks = len(model.get_input_embeddings()._forward_hooks)
        with mock.patch.object(features, 'TAP_LAYERS', (1, 1)), self.assertRaisesRegex(ValueError, '32'):
            features.capture(model, batch)
        self.assertEqual(len(model.get_input_embeddings()._forward_hooks), hooks)
        model, batch = tiny_clip()
        batch['mm_token_type_ids'] = torch.zeros_like(batch['input_ids'])
        with self.assertRaises(ValueError): features.frame_token_index(batch)


if __name__ == '__main__':
    unittest.main()
