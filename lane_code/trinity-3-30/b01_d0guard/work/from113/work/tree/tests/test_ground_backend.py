"""Fixed v3.12 geometry and actual native-cache MDG decode on a tiny C1."""
import copy
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

from student_pilot import carrier_c1_decode as decode, ground_lifting as lifting, mdg_decode
from student_pilot import mdg_features as features, p3_printed_calculator as calculator
from tests.test_mdg_features import fixture, small_layers

torch.set_num_threads(min(8, torch.get_num_threads()))


class Geometry:
    def cam(self, k):
        return np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]]), np.array([k - 1., 0, 0])

    def lift(self, k, uv, mode='center'):
        # Slanted depth surface has nonzero horizontal extent and height.
        d = 1 + uv[:, 0] / 1000
        cam = np.column_stack(((uv[:, 0] / 500 - 1) * d,
                               (uv[:, 1] / 500 - 1) * d, d))
        R, t = self.cam(k)
        return cam @ R.T + t, cam, np.zeros(len(uv))


def masks():
    mask = np.zeros((32, 12, 12), dtype=bool)
    mask[0, 2:10, 2:10] = True
    mask[2, 1:11, 1:11] = True
    return mask


class LiftingTests(unittest.TestCase):
    def test_exact_text_and_every_success_registers_a_new_point(self):
        result = lifting.lift_object('Kitchen Chair', masks(), np.ones(32) * .97, Geometry(), tau=.5)
        registry = calculator.PrintedPointRegistry()
        text = lifting.render_ground(result, registry)
        self.assertEqual(text.splitlines()[0], 'Kitchen Chair: frames 1,3 (best 3)')
        self.assertTrue(text.splitlines()[1].startswith('P1: cam3 '))
        self.assertTrue(lifting.render_ground(result, registry).splitlines()[1].startswith('P2: cam3 '))
        self.assertEqual(registry.execute('<dist P1 P2>')['text'], '0.00 m')
        self.assertRegex(text.splitlines()[2], r'^size \d+\.\d{2} x \d+\.\d{2} x \d+\.\d{2} m$')

    def test_null_erosion_threshold_and_invalid_inputs(self):
        registry = calculator.PrintedPointRegistry()
        for mask, prob in ((np.zeros_like(masks()), np.ones(32)), (masks(), np.zeros(32))):
            result = lifting.lift_object('missing', mask, prob, Geometry(), tau=.5)
            self.assertEqual(lifting.render_ground(result, registry), 'missing: not seen')
        with self.assertRaises(ValueError):
            lifting.lift_object('x', masks(), np.full(32, np.nan), Geometry(), tau=.5)
        self.assertEqual(lifting.number(-.00001), '0.00')
        self.assertEqual(len(lifting.mask_pixels(np.ones((1, 1), dtype=bool))), 0)
        invalid = lifting.lift_object('x', masks(), np.ones(32), lifting.OwnGeometryAdapter(None), tau=.5)
        self.assertEqual(lifting.render_ground(invalid, registry), 'x: not seen')

    def test_spread_gates_and_degenerate_box_fail_closed(self):
        geo = Geometry()
        original = geo.lift
        def bad(*args, **kwargs):
            p, pc, s = original(*args, **kwargs)
            return p, pc, s + .26
        geo.lift = bad
        self.assertFalse(lifting.lift_object('x', masks(), np.ones(32), geo, tau=.5)['seen'])
        with self.assertRaises(ValueError):
            lifting.fit_gbox(np.ones((5, 3)))

    def test_gap_uses_surface_points_and_raw_common_frames(self):
        a = lifting.lift_object('a', masks(), np.ones(32), Geometry(), tau=.5)
        b = copy.deepcopy(a)
        self.assertEqual(lifting.render_gap(a, b), '0.00 m')
        a['visible'], b['visible'] = [1, 3], [1, 2]
        a['points'].pop('1')
        b['points']['2'] = b['points']['3']
        self.assertIsNotNone(lifting.gap_objects(a, b))
        b['visible'] = [2]
        self.assertIsNotNone(lifting.gap_objects(a, b))

    def test_size_failure_preserves_seen_centroid(self):
        geo = Geometry()
        geo.lift = lambda k, uv, **kw: (np.tile([0., 2., 1.], (len(uv), 1)),
                       np.tile([0., -1., 2.], (len(uv), 1)), np.zeros(len(uv)))
        result = lifting.lift_object('visible', masks(), np.ones(32), geo, tau=.5)
        self.assertTrue(result['seen'])
        self.assertIsNone(result['size'])
        text = lifting.render_ground(result, calculator.PrintedPointRegistry())
        self.assertIn('P1: cam3 ', text)
        self.assertTrue(text.endswith('size unavailable'))

    def test_multi_gap_uses_printed_decimal_minimum_and_ties(self):
        a = dict(name='a', seen=True, visible=[1], areas={'1': 1.}, points={'1': [[0., 0, 0]]})
        def b(name, distance):
            return dict(name=name, seen=True, visible=[1], areas={'1': 1.}, points={'1': [[distance, 0, 0]]})
        audit = []
        self.assertEqual(lifting.render_gaps(a, [b('Y1', .974), b('Y2', 1.424)], audit=audit),
                         'Y1: 0.97 m\nY2: 1.42 m\nmin "Y1" 0.97 m')
        self.assertEqual(audit[0]['frames'], [1, 1])
        self.assertEqual(lifting.render_gaps(a, [b('Y1', .974), b('Y2', .973)]),
                         'Y1: 0.97 m\nY2: 0.97 m\nmin "Y1","Y2" 0.97 m')
        missing = b('missing', 0.)
        missing['seen'] = False
        self.assertEqual(lifting.render_gaps(a, [b('Y1', .97), missing]), 'not seen')

    def test_world_centroid_is_transformed_once(self):
        geo = Geometry()
        angle = .6
        R = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1.]])
        base = geo.cam
        geo.cam = lambda k: (R @ base(k)[0], R @ base(k)[1])
        result = lifting.lift_object('a', masks(), np.ones(32), geo, tau=.5)
        P = np.asarray(result['points'][str(result['best'])])
        expected = lifting.public_centres(geo, result['best'], np.median(P, axis=0))
        np.testing.assert_array_equal(result['camera'], expected[0])
        np.testing.assert_array_equal(result['f1'], expected[1])


class StreamTokenizer:
    eos_token_id, pad_token_id = 1, 0
    words = {0: '', 1: '', 2: '<ground obj="Chair">', 3: '<gap a="Chair" b="Chair">',
             4: '<dist P1 P2>', 9: '<ground obj="other chair">', 6: ' prose',
             7: '<gap a="Chair" b="other chair">'}
    def decode(self, ids, **kwargs):
        return ''.join(self.words[int(i)] for i in ids)
    def encode(self, text, **kwargs):
        for token, word in self.words.items():
            if text == word and word:
                return [token]
        token = max(self.words) + 1
        self.words = {**self.words, token: text}
        return [token]
    def __call__(self, text, **kwargs):
        ids, offsets, at = [], [], 0
        words = sorted(((i, s) for i, s in self.words.items() if s), key=lambda p: -len(p[1]))
        while at < len(text):
            i, s = next((i, s) for i, s in words if text.startswith(s, at))
            ids.append(i)
            offsets.append((at, at + len(s)))
            at += len(s)
        return dict(input_ids=ids, offset_mapping=offsets)
    def convert_tokens_to_ids(self, token):
        return {'<tool_response>': 55, '</tool_response>': 56}[token]


class CharacterTokenizer:
    pad_token_id = 0
    def __init__(self):
        chars = sorted(set('<ground obj="chair">'))
        self.ids = {c: i + 6 for i, c in enumerate(chars)}
        self.words = {v: c for c, v in self.ids.items()}
    def encode(self, text, **kwargs):
        return [self.ids[c] for c in text]
    def decode(self, ids, **kwargs):
        return ''.join(self.words[int(i)] for i in ids)
    def __call__(self, text, **kwargs):
        return dict(input_ids=self.encode(text), offset_mapping=[(i, i+1) for i in range(len(text))])


class StubDecoder(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.video_calls = self.calls = 0
        self.seen = []
    def encode_video(self, taps, vit, pixels, grid):
        self.video_calls += 1
        self.prefix = SimpleNamespace(taps=taps, vit=vit, pixels=pixels, grid=grid)
        return pixels
    def forward(self, memory, query, phrase, phrase_mask):
        self.calls += 1
        self.seen.append(features.SuffixStates(query.clone(), phrase.clone(), phrase_mask.clone()))
        logits = torch.full((1, 32, 12, 12), -10.)
        logits[:, 0, 2:10, 2:10] = 10
        return [dict(mask_logit=logits, clip_logit=torch.ones(1) * 8,
                     frame_logit=torch.ones(1, 32) * 8, iou=torch.ones(1, 32))]
    @staticmethod
    def decode(out):
        from student_pilot.mask_grounding_head import MaskGroundingHead
        return MaskGroundingHead.decode(out)


class DecodeTests(unittest.TestCase):
    def test_atomic_openers_mean_initialization_and_identical_gate_positions(self):
        from tokenizers import Tokenizer, models, pre_tokenizers, decoders
        from transformers import PreTrainedTokenizerFast
        from student_pilot import carrier_c1_routing as routing, mdg_lora
        from student_pilot.mdg_decode_tokens import add_ground_tokens
        model, batch = fixture()
        characters = sorted(set('<ground obj="chair"><gap a="x" b="y"> ordinary prose after'))
        vocab = {'[UNK]': 0, '[PAD]': 1, '[EOS]': 2,
                 **{c: i+3 for i, c in enumerate(characters)}}
        native_tokenizer = Tokenizer(models.WordLevel(vocab, unk_token='[UNK]'))
        native_tokenizer.pre_tokenizer = pre_tokenizers.Split('', behavior='isolated')
        native_tokenizer.decoder = decoders.Fuse()
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=native_tokenizer, unk_token='[UNK]',
                                           pad_token='[PAD]', eos_token='[EOS]')
        processor = SimpleNamespace(tokenizer=tokenizer)
        old = routing.add_routing_tokens(processor)
        legacy_ids = dict(old['ids'])
        parts = {o: tokenizer.encode(o, add_special_tokens=False) for o in ('<ground', '<gap')}
        expected_input = {o: model.get_input_embeddings().weight[p].float().mean(0).clone() for o, p in parts.items()}
        expected_output = {o: model.get_output_embeddings().weight[p].float().mean(0).clone() for o, p in parts.items()}
        old_input = model.get_input_embeddings().weight.detach().clone()
        old_output = model.get_output_embeddings().weight.detach().clone()
        tokens = add_ground_tokens(processor, model)
        fresh = [tokens['ids'][o] for o in ('<ground', '<gap')]
        keep = torch.ones(len(old_input), dtype=torch.bool); keep[fresh] = False
        self.assertTrue(torch.equal(old_input[keep], model.get_input_embeddings().weight[keep]))
        self.assertTrue(torch.equal(old_output[keep], model.get_output_embeddings().weight[keep]))
        for opener in ('<ground', '<gap'):
            index = tokens['ids'][opener]
            self.assertEqual(tokenizer.encode(opener, add_special_tokens=False), [index])
            torch.testing.assert_close(model.get_input_embeddings().weight[index], expected_input[opener], rtol=0, atol=0)
            torch.testing.assert_close(model.get_output_embeddings().weight[index], expected_output[opener], rtol=0, atol=0)
        self.assertEqual({o: tokens['ids'][o] for o in legacy_ids}, legacy_ids)
        add_ground_tokens(processor, model)  # Idempotent; never reinitialize trained rows.
        model.mdg_tokenizer = tokenizer
        mdg_lora.install(model, 2)
        with self.assertRaisesRegex(ValueError, 'atomic'):
            mdg_decode.QueryStream(model, CharacterTokenizer())
        original = mdg_lora.suffix_mask
        masks = []
        def gate(model, mask):
            masks.append(mask.detach().clone())
            return original(model, mask)
        call, _ = features.suffix_tokens(tokenizer, 'chair')
        before, after = tokenizer.encode('ordinary prose ', add_special_tokens=False), tokenizer.encode(' after', add_special_tokens=False)
        with small_layers(), torch.no_grad():
            prefix = features.capture_prefix(model, batch)
            with mock.patch.object(mdg_lora, 'suffix_mask', side_effect=gate):
                features.suffix_states(model, prefix, ['chair'])
            training_gate = torch.cat([m.flatten() for m in masks]).tolist()
            masks.clear()
            stream = mdg_decode.QueryStream(model, tokenizer)
            cache = features.expand_cache(prefix.cache, 1)
            full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([before+call+after])), 1)
            with mock.patch.object(mdg_lora, 'suffix_mask', side_effect=gate):
                decode.consume_cache_tokens(features._native(model), full, torch.ones_like(full), cache, observer=stream)
            stream_gate = torch.cat([m.flatten() for m in masks]).tolist()
        self.assertEqual(training_gate, [True]*len(call))
        self.assertEqual(stream_gate, [False]*len(before) + training_gate + [False]*len(after))

    def test_mdg_generate_register_gap_cached_video_and_replay(self):
        model, batch = fixture()
        tokenizer = StreamTokenizer()
        processor = SimpleNamespace(tokenizer=tokenizer, _routing_tokens=dict(ids={'<ground': 2}))
        model.mdg_head, model.mdg_meta = StubDecoder(), dict(tau=.5, labels=['chair', 'other chair'])
        # Model fixture has a constant metric depth: give the surface a slight slope
        # through its actual query head so its XY gravity box is nondegenerate.
        script = iter([2, 2, 3, 4, 1])
        def force(ids, logits):
            out = torch.full_like(logits, -1e9)
            out[:, next(script)] = 0
            return out
        depth_head = model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth
        original = depth_head.query
        def depth_query(grid, uv):
            return original(grid, uv) + uv[..., 0] / 1000
        with small_layers(), mock.patch.object(depth_head, 'query', side_effect=depth_query):
            record = decode.generate(model, processor, batch, logits_processor=force)
        self.assertEqual(model.mdg_head.video_calls, 1)
        self.assertEqual(model.mdg_head.calls, 1)
        self.assertTrue(record['calls'][0]['response'].startswith('Chair: frames 1 (best 1)'))
        self.assertIn('P1: cam1 ', record['calls'][0]['response'])
        self.assertIn('P2: cam1 ', record['calls'][1]['response'])
        self.assertEqual([c['response'] for c in record['calls'][2:]], ['0.00 m', '0.00 m'])
        self.assertIn('<tool_response>\nChair:', record['text'])
        self.assertTrue(decode.replay(record)['byte_equal'])
        altered = copy.deepcopy(record)
        altered['heads']['ground_queries'][0]['prob'][0] = 0.
        self.assertFalse(decode.replay(altered)['byte_equal'])

    def test_multiple_objects_share_depth_grid_and_replay(self):
        model, batch = fixture()
        tokenizer = StreamTokenizer()
        processor = SimpleNamespace(tokenizer=tokenizer, _routing_tokens=dict(ids={'<ground': 2}))
        model.mdg_head, model.mdg_meta = StubDecoder(), dict(tau=.5, labels=['chair', 'other chair'])
        script = iter([2, 9, 7, 1])
        def force(ids, logits):
            out = torch.full_like(logits, -1e9)
            out[:, next(script)] = 0
            return out
        with small_layers():
            record = decode.generate(model, processor, batch, logits_processor=force)
        self.assertEqual(model.mdg_head.video_calls, 1)
        self.assertEqual(model.mdg_head.calls, 2)
        self.assertEqual(len(record['heads']['depth_queries']), 1)
        self.assertEqual(record['calls'][-1]['response'], '0.00 m')
        self.assertEqual(record['heads']['gap_queries'][0]['frames'], [1, 1])
        self.assertTrue(decode.replay(record)['byte_equal'])

    def test_mdg_not_seen_and_no_ground_call(self):
        model, batch = fixture()
        tokenizer = StreamTokenizer()
        processor = SimpleNamespace(tokenizer=tokenizer, _routing_tokens=dict(ids={'<ground': 2}))
        def run(script):
            script = iter(script)
            def force(ids, logits):
                out = torch.full_like(logits, -1e9)
                out[:, next(script)] = 0
                return out
            with small_layers():
                return decode.generate(model, processor, batch, logits_processor=force)
        baseline = run([6, 1])
        model.mdg_head, model.mdg_meta = StubDecoder(), dict(tau=1.)
        idle = run([6, 1])
        self.assertEqual(idle['tokens'], baseline['tokens'])
        self.assertEqual(model.mdg_head.video_calls, 0)
        missing = run([2, 1])
        self.assertEqual(missing['calls'][0]['response'], 'Chair: not seen')
        self.assertEqual(missing['heads']['depth_queries'], [])
        self.assertTrue(decode.replay(missing)['byte_equal'])

    def test_parser_and_gap_without_success(self):
        self.assertEqual(decode.parse_ground('<ground obj="Kitchen Chair #2">'), 'Kitchen Chair #2')
        self.assertEqual(decode.parse_gap('<gap a="A" b="B">'), ('A', 'B'))
        self.assertEqual(decode.parse_gap('<gap a="X" b="Y1" b="Y2">'), ('X', ['Y1', 'Y2']))
        for call in ('<gap b="B" a="A">', '<gap a="" b="B">', '<gap a="A" b="B" b="B">'):
            self.assertEqual(decode.respond(call, calculator.PrintedPointRegistry(), None)[1]['kind'], 'error')
        self.assertEqual(decode.respond('<gap a="A" b="B">', calculator.PrintedPointRegistry(), None)[0], 'not seen')
        with self.assertRaises(decode.CallError):
            decode.parse_ground('<ground obj="bad\u0085name">')

    def test_capture_and_stream_match_mdg_eval_features(self):
        from transformers import Qwen3_5ForConditionalGeneration
        model, batch = fixture()
        model.config.vision_config.patch_size = 16
        model.model.visual = Qwen3_5ForConditionalGeneration(model.config).float().model.visual
        batch['pixel_values_videos'] = torch.randn(32 * 8, 1536)
        tokenizer = model.mdg_tokenizer = CharacterTokenizer()
        native = features._native(model)
        stream = mdg_decode.QueryStream(model, tokenizer)
        with small_layers(), torch.no_grad():
            prefix = features.capture_prefix(model, batch)
            expected = features.suffix_states(model, prefix, ['chair'])
            with mdg_decode.PrefixCapture(model, batch) as captured:
                output = features._prefill(model, batch, native)
            actual = captured.finish()
            for x, y in zip(actual.taps + actual.vit + [actual.pixels],
                            prefix.taps + prefix.vit + [prefix.pixels]):
                self.assertTrue(torch.equal(x, y))
            ids = tokenizer.encode('<ground obj="chair">')
            full = torch.cat((batch['input_ids'], batch['input_ids'].new_tensor([ids])), dim=1)
            attention = torch.ones_like(full)
            _, cache = decode.consume_cache_tokens(native, full, attention, output.past_key_values, observer=stream)
            actual_states = stream.finish('chair')
            self.assertEqual(cache.get_seq_length(), full.shape[1])
            for key in ('query', 'phrase'):
                torch.testing.assert_close(getattr(actual_states, key), getattr(expected, key), atol=1e-5, rtol=1e-5)
            self.assertTrue(torch.equal(actual_states.phrase_mask, expected.phrase_mask))
            # Compare the actual MDG decoder outputs through mdg_eval's export path.
            from student_pilot import mdg_eval
            from student_pilot.mask_grounding_head import MDGConfig, MaskGroundingHead
            cfg = MDGConfig(vit_dim=32, lm_dim=32, dim=16, heads=4, mlp=32,
                            pixel_dim=8, blocks=2, stem_pretrained=False)
            model.mdg_head = MaskGroundingHead(cfg).eval()
            decoded, _ = mdg_decode.predict(model.mdg_head, actual, actual_states)
            with mock.patch.object(mdg_eval, 'trainer_row', return_value=({}, {})), \
                 mock.patch('student_pilot.carrier_c1_canary.prompt_batch', return_value=batch), \
                 mock.patch.object(features, 'capture_prefix', return_value=prefix):
                entry = dict(video_rel='tiny.mp4', frame_indices=list(range(32)), fps=1., total_num_frames=32)
                exported, _ = mdg_eval.predict(model, SimpleNamespace(), {}, entry, ['chair'], '.', 'cpu', 1)
            np.testing.assert_array_equal(decoded['mask'], exported['mask'])
            for key in ('prob', 'iou', 'area', 'uv', 'clip_prob', 'frame_prob'):
                np.testing.assert_allclose(decoded[key], exported[key], atol=1e-6, rtol=1e-6)



if __name__ == '__main__':
    unittest.main()
