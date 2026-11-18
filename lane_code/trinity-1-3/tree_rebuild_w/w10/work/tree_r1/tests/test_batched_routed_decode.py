"""Native CPU hybrid-cache parity, independent stops and forced responses."""
import copy
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from student_pilot import carrier_c1_decode as D, carrier_c1_batch_decode as B
from tests.test_carrier_c1_final import FakeTokenizer, final_fixture
from tests.test_grounding_decode import FakeGH, fixture as ground_fixture
from tests.test_mdg_features import fixture as mdg_fixture, small_layers
from tests.test_ground_backend import StreamTokenizer, StubDecoder


class Tokenizer(FakeTokenizer):
    pad_token_id = 0
    words = {**FakeTokenizer.words, 30: '<ground obj="chair">', 31: '<ground obj="missing">',
             32: '<gap a="chair" b="missing">', 33: '<pose frame=40>',
             34: '<angle S=P1 F=P2 Q=P3 rule=medium>', 35: '<angle S=P1 F=P2 Q=P3 rule=hard>',
             36: '<closest A=P1 B=P2,P3>', 37: ' frame=2 pts=[[500,500],[300,700],[700,200]]>'}


def fixture():
    model, batch, _ = final_fixture()
    p = SimpleNamespace(tokenizer=Tokenizer(), _routing_tokens={'ids': {'<depth_at': 40, '<move': 45, '<turn': 47, '<pose': 33}})
    return model.eval(), p, batch


def varied(batch, count=4):
    rows = []
    for i in range(count):
        row = {k: v.clone() if isinstance(v, torch.Tensor) else copy.deepcopy(v) for k, v in batch.items()}
        for key in ('input_ids', 'attention_mask', 'mm_token_type_ids', 'labels'):
            if key in row:
                value = 10 + i if key == 'input_ids' else 1 if key == 'attention_mask' else -100 if key == 'labels' else 0
                row[key] = torch.cat((row[key], row[key].new_full((1, i * 3), value)), 1)
        row['pixel_values_videos'] = row['pixel_values_videos'] + i * .01
        rows.append(row)
    return rows


class Script:
    def __init__(self, tokens):
        self.tokens, self.seen = iter(tokens), []
    def __call__(self, ids, logits):
        self.seen.append((list(ids), logits.clone()))
        out = torch.full_like(logits, -1e9)
        out[:, next(self.tokens)] = 0
        return out


class BatchDecode(unittest.TestCase):
    def compare(self, model, processor, rows, scripts, **kwargs):
        serial_hooks = [Script(s) for s in scripts]
        single = [D.generate(model, processor, row, logits_processor=hook,
                             **{k: v[i] if k in ('donor_batch', 'tower_state') else v for k, v in kwargs.items()})
                  for i, (row, hook) in enumerate(zip(rows, serial_hooks))]
        batch_hooks = [Script(s) for s in scripts]
        previous = model.model.rope_deltas
        batched = D.generate(model, processor, rows, logits_processor=batch_hooks, **kwargs)
        self.assertIs(model.model.rope_deltas, previous)
        self.assertEqual(single, batched)
        for expected, actual in zip(serial_hooks, batch_hooks):
            self.assertEqual(len(expected.seen), len(actual.seen))
            for (prefix_a, a), (prefix_b, b) in zip(expected.seen, actual.seen):
                self.assertEqual(prefix_a, prefix_b)
                torch.testing.assert_close(a, b, rtol=2e-4, atol=2e-5)
        return single

    def test_ragged_prompts_forced_responses_and_row_stops(self):
        model, p, batch = fixture()
        rows = varied(batch)
        scripts = [[1], [42, 42, 1], [40, 41, 49, 1], [45, 46, 33, 32, 1]]
        shapes = []
        handle = model.model.language_model.norm.register_forward_hook(lambda m, a, o: shapes.append(tuple(o.shape[:2])))
        try:
            result = self.compare(model, p, rows, scripts)
        finally:
            handle.remove()
        self.assertTrue(any(b > 1 and length == 1 for b, length in shapes))
        self.assertEqual([r['finish'] for r in result], ['eos'] * 4)
        self.assertEqual([len(r['calls']) for r in result], [0, 0, 2, 3])
        self.assertTrue(all(D.replay(r)['byte_equal'] for r in result))

    def test_native_greedy_tokens_equal_after_compaction(self):
        model, p, batch = fixture()
        rows = varied(batch)
        def greedy(limit):
            def stop(ids, logits):
                logits = logits.clone()
                # Restrict to ordinary text to test unforced native argmax.
                logits[:, 30:] = -float('inf')
                if len(ids) >= limit:
                    logits[:] = -float('inf'); logits[:, 1] = 0
                return logits
            return stop
        expected = [D.generate(model, p, row, logits_processor=greedy(3+i)) for i, row in enumerate(rows)]
        actual = D.generate(model, p, rows, logits_processor=[greedy(3+i) for i in range(4)])
        self.assertEqual(expected, actual)

    def test_call_limit_and_context_cut_inside_response(self):
        model, p, batch = fixture()
        rows = varied(batch)
        with self.assertRaisesRegex(ValueError,'call budget exhausted'):
            self.compare(model, p, rows, [[1], [40, 41, 49], [32, 32], [42, 1]], max_calls=1)
        model.config.text_config.max_position_embeddings = rows[-1]['input_ids'].shape[1] + 3
        with self.assertRaisesRegex(ValueError,'response exceeds token budget'):
            self.compare(model, p, rows, [[40, 41], [32], [42, 42, 42, 42, 42, 42], [40, 41]])

    def test_shuffle_uses_each_donor(self):
        model, p, batch = fixture()
        rows = varied(batch)
        self.compare(model, p, rows, [[45, 46, 1]] * 4, mode='shuffle', donor_batch=list(reversed(rows)))

    def test_singleton_list_and_invalid_inputs(self):
        model, p, batch = fixture()
        self.compare(model, p, [batch], [[42, 1]])
        self.assertEqual(D.generate(model, p, []), [])
        with self.assertRaisesRegex(ValueError, 'one value per prompt'):
            D.generate(model, p, [batch] * 4, logits_processor=Script([1]))
        with self.assertRaisesRegex(ValueError, 'single-row'):
            D.generate(model, p, {**batch, 'input_ids': batch['input_ids'].repeat(2, 1)})
        with self.assertRaisesRegex(ValueError, 'unpadded'):
            D.generate(model, p, [{**batch, 'attention_mask': torch.zeros_like(batch['attention_mask'])}])
        with self.assertRaisesRegex(ValueError, 'impersonate'):
            D.generate(model, p, [batch], logits_processor=[Script([43])])
        with self.assertRaisesRegex(ValueError, '16384'):
            D.generate(model, p, [batch], max_new_tokens=4)

    def test_mdg_private_prefix_queries_gaps_and_replay(self):
        from student_pilot import mdg_lora
        model, batch = mdg_fixture()
        rows = varied(batch)
        p = SimpleNamespace(tokenizer=StreamTokenizer(), _routing_tokens={'ids': {'<ground': 2}})
        model.mdg_head, model.mdg_meta = StubDecoder(), dict(tau=.5, labels=['chair', 'other chair'])
        mdg_lora.install(model, 2)
        with torch.no_grad():
            for parameter in model.auxiliary_heads.mdg_lora.parameters():
                parameter.normal_(0, .05)
        with small_layers():
            out = self.compare(model, p, rows, [[2, 2, 3, 4, 1], [6, 1], [2, 9, 7, 1], [9, 9, 1]])
        self.assertTrue(all(D.replay(r)['byte_equal'] for r in out))
        self.assertEqual([len(r['heads']['ground_queries']) for r in out], [1, 0, 2, 1])
        self.assertTrue(out[0]['calls'][0]['response'].startswith('Chair: frames'))
        self.assertIn('P1:', out[3]['calls'][0]['response'])
        self.assertIn('P2:', out[3]['calls'][1]['response'])

    def test_grounding_head_keeps_each_video_memory(self):
        model, p, batch = ground_fixture()
        model.grounding_head, model.grounding_meta = FakeGH(), dict(tau=.6)
        with small_layers():
            out = self.compare(model, p, varied(batch), [[40, 40, 1], [1], [41, 1], [40, 1]])
        self.assertEqual([len(r['heads']['ground_queries']) for r in out], [1, 0, 1, 1])
        self.assertEqual(model.grounding_head.video_calls, 6)

    def test_tower_states_keep_row_geometry_and_shuffle(self):
        from tests.test_tower_read import tower_state, tower_batch
        model, p, batch = fixture()
        states = [tower_state() for _ in range(4)]
        rows = [{**row, **tower_batch(state)} for row, state in zip(varied(batch), states)]
        out = self.compare(model, p, rows, [[45, 46, 1]] * 4,
                           pose_source='tower', tower_state=states)
        self.assertTrue(all(D.replay(r)['byte_equal'] for r in out))

    def test_tower_error_is_per_row(self):
        model, p, batch = fixture()
        prepare = D._prepare_decode
        rows = varied(batch)
        def failing(model, processor, batch, **kwargs):
            if batch is rows[1]:
                raise D.TowerError('synthetic tower failure')
            state = prepare(model, processor, batch, **{**kwargs, 'pose_source': 'own', 'tower_state': None})
            state.heads.tower_scale = 1.
            return state
        with mock.patch.object(D, '_prepare_decode', side_effect=failing):
            out = D.generate(model, p, rows, pose_source='tower', logits_processor=[Script([1]) for _ in rows])
        self.assertEqual([r['finish'] for r in out], ['eos', 'tower_error', 'eos', 'eos'])
        self.assertEqual(out[1]['generated_tokens'], 0)

    def test_eight_traces_per_routed_form(self):
        model, p, batch = fixture()
        rows = varied(batch, 8)
        forms = {'absolute_distance': [40, 41, 49], 'relative_distance': [40, 37, 36],
                 'direction_medium': [40, 37, 34], 'direction_hard': [40, 37, 35]}
        for kind, calls in forms.items():
            for start in (0, 4):
                with self.subTest(kind=kind, start=start):
                    self.compare(model, p, rows[start:start+4],
                                 [[42] * (j % 3) + calls + [42] * (j % 2) + [1] for j in range(start, start+4)])


if __name__ == '__main__':
    unittest.main()
