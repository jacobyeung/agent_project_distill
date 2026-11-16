"""Single-prefill routed grounding, typed calls and recorded-output replay."""
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_decode as decode
from student_pilot import grounding_features as features
from student_pilot import p3_printed_calculator as calculator
from student_pilot.carrier_c1_data import insert_frame_carriers
from tests.test_carrier_c1 import Tokenizer
from tests.test_carrier_c1_final import FakeTokenizer, final_fixture


class GroundTokenizer(FakeTokenizer):
    words = {**FakeTokenizer.words, 40: '<ground obj="chair">', 41: '<ground obj="missing">',
             42: ' Next', 45: '<pose', 46: '<ground obj="chair">', 47: '<ground obj="bad\t">'}


class FakeGH(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.video_calls, self.query_calls = 0, 0

    def encode_video(self, taps, vit, grid):
        self.video_calls += 1
        self.taps, self.vit, self.grid = taps, vit, grid
        return dict(video=taps[0])

    def encode_query(self, embeds, mask):
        self.query_calls += 1
        return embeds

    def forward(self, memory, query):
        prob = torch.zeros((len(query), 32))
        prob[:, :4] = torch.tensor([.5, .95, .97, .95])
        return dict(prob=prob, uv=torch.tensor([[[412, 550]]*32]*len(query)))

    @staticmethod
    def decode(output):
        return output


def fixture():
    model, _, _ = final_fixture()
    model.frame_layout = 'duplicate'
    model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    ids = torch.tensor([[2] + [v for _ in range(32) for v in (62, 61, 63)] + [10, 11]])
    batch = dict(input_ids=ids, attention_mask=torch.ones_like(ids), mm_token_type_ids=torch.where(ids == 61, 2, 0),
        video_grid_thw=torch.tensor([[32, 2, 2]]), pixel_values_videos=torch.randn(128, 24))
    batch = insert_frame_carriers(batch, Tokenizer(), frame_layout='duplicate')
    processor = SimpleNamespace(tokenizer=GroundTokenizer(), _routing_tokens=dict(ids={'<pose': 45}))
    return model.eval(), processor, batch


def scripted(model, processor, batch, script):
    stream = iter(script)
    def force(ids, logits):
        out = torch.full_like(logits, -1e9)
        out[:, next(stream)] = 0.
        return out
    with mock.patch.object(features, 'TAP_LAYERS', (1, 1)):
        return decode.generate(model, processor, batch, logits_processor=force)


class GroundCalls(unittest.TestCase):
    def test_parse_errors_and_unavailable_head(self):
        registry = calculator.PrintedPointRegistry()
        self.assertEqual(decode.parse_ground('<ground obj="a_2- x">'), 'a_2- x')
        self.assertEqual(decode.parse_ground('<ground obj="'+'a'*40+'">'), 'a'*40)
        self.assertEqual(decode.parse_ground('<ground obj="Kitchen Chair #2">'), 'Kitchen Chair #2')
        for name in ('', 'mug\t'):
            text, info = decode.respond(f'<ground obj="{name}">', registry, None)
            self.assertEqual((text, info['code']), ('error: bad_object', 'bad_object'))
        for call in ('<ground>', '<ground obj=chair>', '<ground object="chair">'):
            self.assertEqual(decode.respond(call, registry, None)[1]['code'], 'malformed_call')
        self.assertEqual(decode.respond('<ground obj="chair">', registry, None)[0], 'error: head_readout')
        self.assertEqual(decode.respond('<ground obj="chair">', registry, None, lambda n: n+': not seen'),
                         ('chair: not seen', dict(kind='ground', name='chair')))

    def test_format_not_seen_and_ties(self):
        p, uv = [.1]*32, [[430, 561]]*32
        self.assertEqual(decode.ground_text('cup', p, uv, .5), 'cup: not seen')
        p[2], p[3], p[5], p[9] = .97, .95, .95, .8
        self.assertEqual(decode.ground_text('chair', p, uv, .5),
                         'chair: f3 [430,561] 0.97 | f4 [430,561] 0.95 | f6 [430,561] 0.95')
        self.assertEqual(decode.ground_text('cup', [.5]+[0.]*31, uv, .5), 'cup: f1 [430,561] 0.50')

    def test_routed_capture_cached_queries_and_replay(self):
        model, processor, batch = fixture()
        model.grounding_head, model.grounding_meta = FakeGH(), dict(tau=.6)
        prefill = []
        handle = model.model.language_model.norm.register_forward_hook(lambda m, a, o: prefill.append(o.shape[1]))
        modules = [model.get_input_embeddings(), model.model.language_model.norm,
                   model.model.language_model.layers[0], model.model.visual.merger]
        before = [(len(m._forward_hooks), len(m._forward_pre_hooks)) for m in modules]
        try:
            record = scripted(model, processor, batch, [40, 40, 45, 46, 47, 1])
        finally:
            handle.remove()
        after = [(len(m._forward_hooks), len(m._forward_pre_hooks)) for m in modules]
        before[1] = (before[1][0]-1, before[1][1])
        self.assertEqual(before, after)
        self.assertEqual(sum(n > 1 for n in prefill), 1)
        self.assertEqual([r['kind'] for r in record['calls']], ['ground', 'ground', 'ground', 'error'])
        self.assertEqual(record['calls'][0]['response'], 'chair: f3 [412,550] 0.97 | f2 [412,550] 0.95 | f4 [412,550] 0.95')
        self.assertEqual(record['calls'][1]['response'], record['calls'][0]['response'])
        self.assertEqual((model.grounding_head.video_calls, model.grounding_head.query_calls), (1, 1))
        self.assertEqual(len(record['heads']['ground_queries']), 1)
        self.assertEqual(decode.replay(record), dict(calls=4, mismatches=0, byte_equal=True))
        record['heads']['ground_queries'][0]['uv'][2] = [0, 0]
        self.assertFalse(decode.replay(record)['byte_equal'])

    def test_no_ground_call_preserves_tokens_and_prefill(self):
        model, processor, batch = fixture()
        with mock.patch.object(features, 'capture_from_hooks', side_effect=AssertionError('unexpected GH hooks')):
            baseline = scripted(model, processor, batch, [42, 1])
        model.grounding_head, model.grounding_meta = FakeGH(), dict(tau=.6)
        grounded = scripted(model, processor, batch, [42, 1])
        self.assertEqual(baseline['tokens'], grounded['tokens'])
        self.assertEqual(baseline['heads']['pose9'], grounded['heads']['pose9'])
        self.assertEqual(grounded['heads']['ground_queries'], [])
        self.assertEqual(model.grounding_head.video_calls, 0)
        self.assertEqual(decode.replay(baseline), dict(calls=0, mismatches=0, byte_equal=True))

    def test_ground_not_seen_and_no_gh_generate(self):
        model, processor, batch = fixture()
        missing = scripted(model, processor, batch, [40, 1])
        self.assertEqual(missing['calls'][0]['response'], 'error: head_readout')
        model.grounding_head, model.grounding_meta = FakeGH(), dict(tau=1.)
        record = scripted(model, processor, batch, [41, 1])
        self.assertEqual(record['calls'][0]['response'], 'missing: not seen')
        self.assertTrue(decode.replay(record)['byte_equal'])

    def test_explicit_head_reuses_captured_prefill(self):
        model, processor, batch = fixture()
        model.grounding_meta, model.grounding_tokenizer = dict(tau=.6), processor.tokenizer
        with mock.patch.object(features, 'TAP_LAYERS', (1, 1)), torch.no_grad():
            captured = features.capture(model, batch)
            gh = FakeGH()
            heads = decode.HeadState(model, batch, captured.hidden, gh=gh, taps=captured)
            self.assertIs(heads.grounding_features, captured)
            self.assertTrue(heads.ground('chair').startswith('chair: f3 '))
            self.assertEqual(gh.video_calls, 1)

    def test_tail_does_not_span_prior_responses(self):
        prefix = '<ground obj="chair"><tool_response>chair: not seen</tool_response>'
        for name in ('chair', 'a'*40, 'not<valid', 'not>valid'):
            call = f'<ground obj="{name}">'
            self.assertEqual(decode.GROUND_TAIL.search(prefix+call)[0], call)


if __name__ == '__main__':
    unittest.main()
