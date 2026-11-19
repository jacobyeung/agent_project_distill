"""Native hybrid-cache continuation, prefill hooks and processor-layout parity."""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid

import torch

from student_pilot import grounding_features as gh, mdg_features as mdg
from student_pilot import carrier_c1_decode as decode
from student_pilot.point_depth_head import vit_grids_by_row
from tests.test_carrier_c1_final import FakeTokenizer
from tests.test_grounding_features import tiny_clip


class Tokenizer:
    pad_token_id = 0

    def encode(self, text, **kwargs):
        return [6 + ord(c) % 32 for c in text]

    def __call__(self, text, **kwargs):
        return dict(input_ids=self.encode(text), offset_mapping=[(i, i + 1) for i in range(len(text))])


def small_layers():
    stack = ExitStack()
    for module, key, value in ((gh, 'TAP_LAYERS', (1, 1)), (mdg, 'TAP_LAYERS', (1, 1)),
                               (mdg, 'VIT_BLOCKS', (1, 2, 3)), (mdg, 'QUERY_LAYER', 1)):
        stack.enter_context(mock.patch.object(module, key, value))
    return stack


def fixture(frames=32):
    model, batch = tiny_clip(frames=frames, h=2, w=4)
    model.mdg_tokenizer = Tokenizer()
    return model, batch


def cache_tensors(cache):
    return {(i, key): value.clone() for i, layer in enumerate(cache.layers)
            for key in ('keys', 'values', 'conv_states', 'recurrent_states')
            if isinstance(value := getattr(layer, key, None), torch.Tensor)}


class MDGFeatures(unittest.TestCase):
    def test_prefill_matches_gh_decode_and_native_hidden_states(self):
        model, batch = fixture()
        raw, hf = {}, []
        original = model.model.language_model.forward

        def forward(*args, **kwargs):
            output = original(*args, **{**kwargs, 'output_hidden_states': True})
            hf.append(output.hidden_states)
            return output

        handles = [block.register_forward_hook(lambda module, args, out, k=k: raw.setdefault(k, out.detach().clone()))
                   for k, block in enumerate(model.model.visual.blocks, 1)]
        try:
            with small_layers(), mock.patch.object(model.model.language_model, 'forward', side_effect=forward):
                prefix = mdg.capture_prefix(model, batch)
        finally:
            for handle in handles:
                handle.remove()
        with small_layers():
            reference = gh.capture(model, batch)
        self.assertTrue(torch.equal(prefix.hidden, reference.hidden))
        index = gh.frame_token_index(batch)
        for tap, layer in zip(prefix.taps, (1, 1, 2)):
            self.assertTrue(torch.equal(tap, hf[0][layer][0, index].to(torch.bfloat16)))
        for k, tap in enumerate(prefix.vit, 1):
            self.assertTrue(torch.equal(tap, vit_grids_by_row(raw[k], batch['video_grid_thw'], 2)[0]))
        self.assertEqual(prefix.grid, (1, 2))
        self.assertEqual(tuple(prefix.pixels.shape), (32, 3, 4, 8))
        self.assertEqual(prefix.pixels.dtype, torch.float32)
        self.assertTrue(bool(((prefix.pixels >= 0) & (prefix.pixels <= 1)).all()))
        self.assertEqual(prefix.cache.get_seq_length(), prefix.prefix_len)
        self.assertTrue(all(not t.requires_grad for t in [*prefix.taps, *prefix.vit, prefix.pixels, prefix.hidden]))
        processor = SimpleNamespace(tokenizer=FakeTokenizer(), _routing_tokens={'ids': {'<pose': 39}})
        norm = []
        handle = model.model.language_model.norm.register_forward_hook(lambda module, args, out: norm.append(out.detach()))

        def eos(ids, logits):
            value = torch.full_like(logits, -1e9)
            value[:, 1] = 0
            return value

        try:
            record = decode.generate(model, processor, batch, logits_processor=eos)
        finally:
            handle.remove()
        self.assertEqual(record['finish'], 'eos')
        self.assertTrue(torch.equal(prefix.hidden, norm[0]))

    def test_production_taps_and_vit_blocks_match_native_outputs(self):
        from transformers import Qwen3_5ForConditionalGeneration
        model, batch = fixture(frames=2)
        cfg = copy.deepcopy(model.config)
        cfg.text_config.num_hidden_layers = 26
        cfg.text_config.layer_types = ['linear_attention', 'full_attention'] * 13
        cfg.vision_config.depth = 26
        native = Qwen3_5ForConditionalGeneration(cfg).float()
        model.config = cfg
        model.model, model.lm_head = native.model, native.lm_head
        model.eval().requires_grad_(False)
        hf, vit, handles = [], {}, []
        original = model.model.language_model.forward

        def forward(*args, **kwargs):
            out = original(*args, **{**kwargs, 'output_hidden_states': True})
            hf.append(out.hidden_states)
            return out

        for k in mdg.VIT_BLOCKS:
            handles.append(model.model.visual.blocks[k - 1].register_forward_hook(
                lambda module, args, out, k=k: vit.setdefault(k, out.detach().clone())))
        try:
            with mock.patch.object(model.model.language_model, 'forward', side_effect=forward):
                prefix = mdg.capture_prefix(model, batch)
        finally:
            for handle in handles:
                handle.remove()
        index = gh.frame_token_index(batch)
        for tap, layer in zip(prefix.taps, (16, 24, 26)):
            self.assertTrue(torch.equal(tap, hf[0][layer][0, index].to(torch.bfloat16)))
        for tap, k in zip(prefix.vit, mdg.VIT_BLOCKS):
            self.assertTrue(torch.equal(tap, vit_grids_by_row(vit[k], batch['video_grid_thw'], 2)[0]))
        names = ['chair', 'long table']
        states = mdg.suffix_states(model, prefix, names, chunk=2)
        for i, name in enumerate(names):
            full = mdg.full_forward_states(model, batch, name)
            torch.testing.assert_close(states.query[i], full.query[0], atol=1e-5, rtol=0)
            torch.testing.assert_close(states.phrase[i], full.phrase[0], atol=1e-5, rtol=0)

    def test_chunks_match_full_forward_and_preserve_all_prefix_states(self):
        model, batch = fixture()
        names = ['a', 'table', 'long desk chair', 'box']
        with small_layers():
            prefix = mdg.capture_prefix(model, batch)
            saved = cache_tensors(prefix.cache)
            delta = prefix.rope_deltas.clone()
            references = [mdg.full_forward_states(model, batch, name) for name in names]
            with mock.patch.object(model, 'carrier_embeddings', side_effect=AssertionError('suffix carrier hook')):
                for chunk in (1, 2, 3):
                    result = mdg.suffix_states(model, prefix, names, chunk=chunk)
                    repeated = mdg.suffix_states(model, prefix, names, chunk=chunk)
                    self.assertTrue(torch.equal(result.query, repeated.query))
                    self.assertTrue(torch.equal(result.phrase, repeated.phrase))
                    for i, reference in enumerate(references):
                        torch.testing.assert_close(result.query[i], reference.query[0], atol=1e-5, rtol=0)
                        torch.testing.assert_close(result.phrase[i], reference.phrase[0], atol=1e-5, rtol=0)
                        self.assertTrue(torch.equal(result.phrase_mask[i], reference.phrase_mask[0]))
                    self.assertEqual(result.phrase_mask.sum(1).tolist(), [1, 5, 8, 3])
                    self.assertEqual(result.query.dtype, torch.float32)
                    self.assertFalse(result.phrase.requires_grad)
                    self.assertEqual(prefix.cache.get_seq_length(), prefix.prefix_len)
                    for key, value in cache_tensors(prefix.cache).items():
                        self.assertTrue(torch.equal(value, saved[key]), key)
            self.assertTrue(torch.equal(prefix.rope_deltas, delta))
            self.assertTrue(torch.equal(result.phrase[~result.phrase_mask], torch.zeros_like(result.phrase[~result.phrase_mask])))

    def test_saved_rope_delta_survives_other_prefills_and_single_token_continuation(self):
        model, batch = fixture(frames=2)
        with small_layers():
            prefix = mdg.capture_prefix(model, batch)
            reference = mdg.full_forward_states(model, batch, 'chair')
            model.model.rope_deltas = torch.tensor([[987]])
            actual = mdg.suffix_states(model, prefix, ['chair'])
            self.assertEqual(model.model.rope_deltas.item(), 987)
            torch.testing.assert_close(actual.query, reference.query, atol=1e-5, rtol=0)
            with mock.patch.object(mdg, 'suffix_tokens', return_value=([8], slice(0, 1))):
                actual = mdg.suffix_states(model, prefix, ['one'])
                reference = mdg.full_forward_states(model, batch, 'one')
            torch.testing.assert_close(actual.query, reference.query, atol=1e-5, rtol=0)

    def test_processor_unpatchify_round_trip_after_resize_rescale(self):
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        video = torch.arange(6 * 3 * 35 * 51).reshape(6, 3, 35, 51).remainder(256).to(torch.uint8)
        processor = Qwen3VLVideoProcessor(do_sample_frames=False,
                                         size={'shortest_edge': 6 * 32 * 64, 'longest_edge': 6 * 32 * 64},
                                         image_mean=[.1, .3, .7], image_std=[.2, .4, .6])
        resized = []
        original = processor.rescale_and_normalize

        def normalize(videos, do_rescale, factor, do_normalize, mean, std):
            resized.append(videos.float() * factor)
            return original(videos, do_rescale, factor, do_normalize, mean, std)

        with mock.patch.object(processor, 'rescale_and_normalize', side_effect=normalize):
            batch = processor(videos=[video], return_tensors='pt')
        actual = mdg.unpatchify(batch['pixel_values_videos'], batch['video_grid_thw'],
                                image_mean=processor.image_mean, image_std=processor.image_std)
        self.assertNotEqual(tuple(resized[0].shape[-2:]), (35, 51))
        torch.testing.assert_close(actual, resized[0][0, ::2], atol=2e-7, rtol=0)

    def test_suffix_span_uses_whole_string_tokenization(self):
        ids, span = mdg.suffix_tokens(Tokenizer(), 'desk chair')
        self.assertEqual(ids, Tokenizer().encode('<ground obj="desk chair">'))
        self.assertEqual(ids[span], Tokenizer().encode('desk chair'))
        for name in ('', ' ', 'a"b', '<x>', 'x\ny'):
            with self.assertRaises(ValueError):
                mdg.suffix_tokens(Tokenizer(), name)

    def test_parity_comparison_passes_and_detects_changed_states(self):
        model, batch = fixture()
        with small_layers():
            report = mdg.compare_parity(model, batch, ['a', 'table', 'long chair'], chunk=2)
            self.assertTrue(report['passed'], report)
            self.assertTrue(report['prefill_hidden_bitwise_equal'])
            original = mdg.full_forward_states

            def wrong(*args):
                result = original(*args)
                return mdg.SuffixStates(-result.query, result.phrase, result.phrase_mask)

            with mock.patch.object(mdg, 'full_forward_states', side_effect=wrong):
                bad = mdg.compare_parity(model, batch, ['a'])
            self.assertFalse(bad['passed'])
            self.assertFalse(bad['labels'][0]['query']['passed'])

    def test_bf16_comparison_meets_canary_tolerances(self):
        model, batch = fixture()
        model.bfloat16()
        batch['pixel_values_videos'] = batch['pixel_values_videos'].bfloat16()
        with small_layers():
            report = mdg.compare_parity(model, batch, ['a', 'table', 'long chair'], chunk=2)
        self.assertTrue(report['passed'], report)
        self.assertGreaterEqual(min(row[part]['cosine'] for row in report['labels']
                                    for part in ('query', 'phrase')), .999)

    def test_cli_writes_tiny_model_canary_and_fails_nonzero(self):
        model, batch = fixture()
        root = Path(os.environ.get('LANE_TEST_OUTPUT', 'artifacts')) / ('mdg_cli_' + uuid.uuid4().hex)
        root.mkdir(parents=True)
        artifact, clips = root / 'artifact.json', root / 'clips.jsonl'
        artifact.write_text('{}\n')
        clip = dict(scene='synthetic', qid='tiny', path='tiny.npz', rgb_wh=[8, 4],
                    frame_indices=list(range(32)), frame_sha256=['a' * 64] * 32)
        clips.write_text(json.dumps(clip) + '\n')
        processor = SimpleNamespace(tokenizer=Tokenizer())
        args = ['mdg_features', 'parity', '--config', str(root / 'config.json'), '--artifact', str(artifact),
                '--clips-jsonl', str(clips), '--frame-root', str(root), '--n', '1', '--device', 'cpu']
        with mock.patch('student_pilot.grounding_train.bind_frames'), \
             mock.patch('sys.argv', args + ['--out', str(root/'refused.json')]):
            with self.assertRaisesRegex(ValueError,'no authenticated R2 bank adapter'):
                mdg.main()
        self.assertFalse((root/'refused.json').exists())
        # Test CLI parity separately with a tiny loader boundary stand-in.
        with small_layers(), mock.patch('student_pilot.mdg_runtime.load_runtime',
                return_value=(model, processor, {})), mock.patch('student_pilot.grounding_train.bind_frames'), \
                mock.patch('student_pilot.carrier_c1_canary.prompt_batch', return_value=batch), \
                mock.patch('student_pilot.grounding_targets._raster', return_value=(None, None, None, None, None, None)), \
                mock.patch('student_pilot.grounding_targets._visible', return_value=(None, None, ['table', 'a'])):
            with mock.patch('sys.argv', args + ['--out', str(root / 'pass.json')]):
                with self.assertRaises(SystemExit) as passed:
                    mdg.main()
            self.assertEqual(passed.exception.code, 0)
            report = json.loads((root / 'pass.json').read_text())
            self.assertTrue(report['passed'])
            self.assertEqual([row['name'] for row in report['clips'][0]['labels']], ['a', 'table'])
            with mock.patch.object(mdg, 'compare_parity', return_value={'passed': False}), \
                    mock.patch('sys.argv', args + ['--out', str(root / 'fail.json')]):
                with self.assertRaises(SystemExit) as failed:
                    mdg.main()
            self.assertEqual(failed.exception.code, 1)
            self.assertFalse(json.loads((root / 'fail.json').read_text())['passed'])

    def test_memory_estimate_matches_native_hybrid_cache_and_9b_config(self):
        from transformers import Qwen3_5Config
        model, batch = fixture(frames=2)
        with small_layers():
            prefix = mdg.capture_prefix(model, batch)
        tensors = cache_tensors(prefix.cache)
        estimate = mdg.cache_memory(model.config, prefix.prefix_len, dtype=torch.float32)
        self.assertEqual(estimate['per_label_bytes'], sum(t.numel() * t.element_size() for t in tensors.values()))
        expanded = mdg.expand_cache(prefix.cache, 3)
        actual = cache_tensors(expanded)
        self.assertEqual(sum(t.numel() * t.element_size() for t in actual.values()), 3 * estimate['per_label_bytes'])
        for (i, key), saved in tensors.items():
            value = getattr(expanded.layers[i], key)
            self.assertNotEqual(value.data_ptr(), getattr(prefix.cache.layers[i], key).data_ptr())
            for row in value:
                self.assertTrue(torch.equal(row, saved[0]))
        report = mdg.cache_memory(Qwen3_5Config())
        self.assertEqual((report['full_layers'], report['linear_layers']), (8, 24))
        self.assertEqual(report['per_label_bytes'], 354418688)
        root = Path(os.environ.get('LANE_TEST_OUTPUT', 'artifacts')) / ('mdg_features_' + uuid.uuid4().hex)
        root.mkdir(parents=True)
        (root / 'cache_9b_10k.json').write_text(json.dumps(report, indent=2) + '\n')

    def test_empty_names_bad_chunk_training_and_hook_cleanup(self):
        model, batch = fixture(frames=2)
        with small_layers():
            prefix = mdg.capture_prefix(model, batch)
            empty = mdg.suffix_states(model, prefix, [])
            self.assertEqual(tuple(empty.query.shape), (0, 2, 32))
            for chunk in (0, -1, 1.5):
                with self.assertRaises(ValueError):
                    mdg.suffix_states(model, prefix, ['a'], chunk=chunk)
            hooks = len(model.get_input_embeddings()._forward_hooks)
            with mock.patch.object(model.model.visual, 'forward', side_effect=RuntimeError('fixture')):
                with self.assertRaisesRegex(RuntimeError, 'fixture'):
                    mdg.capture_prefix(model, batch)
            self.assertEqual(len(model.get_input_embeddings()._forward_hooks), hooks)
            self.assertTrue(all(not block._forward_hooks for block in model.model.visual.blocks))
            model.train()
            with self.assertRaises(ValueError):
                mdg.suffix_states(model, prefix, ['a'])


if __name__ == '__main__':
    unittest.main()
