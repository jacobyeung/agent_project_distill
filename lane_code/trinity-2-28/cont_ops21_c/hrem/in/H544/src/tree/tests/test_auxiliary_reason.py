"""Query-token heads: token contract, value parsing, heads, prediction mixing and the generation loop."""
import json
import math
import unittest

import torch

from tests.auxiliary_toys import SPECIALS, TIMES, Toy, ToyTokenizer, encoded_row, install_runner

install_runner()
from student_pilot import auxiliary_config as config  # noqa: E402
from student_pilot import auxiliary_reason as reason  # noqa: E402
from student_pilot import auxiliary_targets as targets  # noqa: E402
from student_pilot.auxiliary_losses import AuxiliaryHeads, attach, mix_microbatch, reason_predict, video_features  # noqa: E402
from student_pilot.ddp_core import backward_batch, collate_rows, row_losses  # noqa: E402

COUNT, DIST, SIZE, TIME, DEPTH, ANGLE, COORD = (reason.QUERY_TOKENS[kind] for kind in reason.KINDS)
QUESTION = 'How many tables are in the room?'
TARGET = (f'At {TIME}6.0 seconds a table appears. There are {COUNT}3 tables. The door is {DIST}2.4 m away, '
          f'the sofa is {SIZE}185 cm long and the wall is {DEPTH}4.1 m deep. Turn {ANGLE}-37 degrees and step {COORD}+1.3 m.')


def settings(**extra):
    return config.normalize({'reason_weight': .5, 'head_width': 16, **extra})


def reason_row(tokenizer, target=TARGET, qid='q'):
    row, batch, audit = encoded_row(tokenizer, QUESTION, target, qid=qid, record={'reason': True})
    return row, targets.add_to_batch(batch, row, tokenizer, audit), audit


class ContractTests(unittest.TestCase):
    def test_mapping_is_one_constant_of_five_distinct_single_id_tokens(self):
        self.assertEqual(reason.KINDS, ('COUNT', 'DIST', 'SIZE', 'TIME', 'DEPTH', 'ANGLE', 'COORD'))
        self.assertEqual(reason.QUERY_TOKENS, {'COUNT': '<|box_start|>', 'DIST': '<|box_end|>', 'SIZE': '<|quad_start|>',
                                               'TIME': '<|quad_end|>', 'DEPTH': '<|object_ref_start|>',
                                               'ANGLE': '<|object_ref_end|>', 'COORD': '<|fim_prefix|>'})
        table = reason.token_table(ToyTokenizer())
        self.assertEqual(sorted(table['query'].values()), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(len(table['digits']), 10)
        # A tokenizer that does not keep a query token whole is refused.
        broken = ToyTokenizer([token for token in SPECIALS if token != '<|quad_end|>'])
        with self.assertRaisesRegex(ValueError, 'not one tokenizer id'):
            reason.token_table(broken)

    def test_target_text_values_and_malformed_values(self):
        self.assertEqual(reason.text_queries(TARGET), [('TIME', 6.0), ('COUNT', 3.0), ('DIST', 2.4), ('SIZE', 185.0),
                                                       ('DEPTH', 4.1), ('ANGLE', -37.0), ('COORD', 1.3)])
        self.assertEqual(reason.text_queries(f'x {COORD}-0.4, z {COORD}+12.0, y {COORD}3.5'),
                         [('COORD', -0.4), ('COORD', 12.0), ('COORD', 3.5)])
        self.assertEqual(reason.text_queries(f'{COUNT}3.\nDone.'), [('COUNT', 3.0)])
        self.assertEqual(reason.text_queries(f'{ANGLE}+63, {ANGLE}180 and {ANGLE}-0.'), [('ANGLE', 63.0), ('ANGLE', 180.0), ('ANGLE', 0.0)])
        for bad, message in [(f'{COUNT} 3 tables', 'immediately'), (f'{DIST}m', 'immediately'), (f'{COUNT}3.5', 'integer'),
                             (f'{SIZE}12.0 cm', 'integer'), (f'{ANGLE}+12.5', 'integer'), (f'{ANGLE}-181', r'\[-180, 180\]'),
                             (f'{COUNT}-3', 'immediately'), (f'{ANGLE}+ 3', 'immediately'), (f'{COORD}+.5', 'immediately'),
                             (f'{COORD}-250.0', 'meters')]:
            with self.assertRaisesRegex(ValueError, message):
                reason.text_queries(bad)
        rows = [{'qid': 'a', 'target': TARGET, 'student_input': {'question': QUESTION, 'options': []}},
                {'qid': 'b', 'target': 'Plain.', 'student_input': {'question': QUESTION, 'options': None}}]
        census = reason.validate_rows(rows)
        self.assertEqual((census['rows_with_queries'], census['queries']['DIST']), (1, 1))
        rows[1]['student_input']['options'] = [f'A. {COUNT}2']
        with self.assertRaisesRegex(ValueError, 'prompt contains a query token: b'):
            reason.validate_rows(rows)

    def test_token_parse_gives_positions_values_and_spans(self):
        tokenizer = ToyTokenizer()
        row, batch, _ = reason_row(tokenizer)
        ids = batch['input_ids'][0]
        found = [(int(p), reason.KINDS[int(k)], float(v), int(s)) for p, k, v, s in zip(
            batch['aux_reason_pos'][0], batch['aux_reason_kind'][0], batch['aux_reason_value'][0], batch['aux_reason_span'][0])]
        self.assertEqual([(kind, round(value, 3), span) for _, kind, value, span in found],
                         [('TIME', 6.0, 3), ('COUNT', 3.0, 1), ('DIST', 2.4, 3), ('SIZE', 185.0, 3), ('DEPTH', 4.1, 3),
                          ('ANGLE', -37.0, 3), ('COORD', 1.3, 4)])
        for position, kind, _, span in found:
            self.assertEqual(tokenizer.decode([ids[position]]), reason.QUERY_TOKENS[kind])
            self.assertNotEqual(int(batch['labels'][0, position]), -100)
            self.assertTrue(torch.all(batch['labels'][0, position + 1:position + 1 + span] != -100))
        self.assertEqual(batch['aux_group_times'][0].tolist(), [float(f'{t:.1f}') for t in TIMES])

    def test_query_token_in_the_prompt_or_without_value_is_refused(self):
        tokenizer = ToyTokenizer()
        table = reason.token_table(tokenizer)
        ids = tokenizer.encode(f'x{COUNT}3')
        with self.assertRaisesRegex(ValueError, 'supervised target'):
            reason.parse_tokens(ids, [-100] * len(ids), table)
        ids = tokenizer.encode(f'{COUNT}x')
        with self.assertRaisesRegex(ValueError, 'immediately'):
            reason.parse_tokens(ids, ids, table)
        ids = tokenizer.encode(f'{DIST}2.5')
        labels = list(ids)
        labels[-1] = -100
        with self.assertRaisesRegex(ValueError, 'supervised target tokens'):
            reason.parse_tokens(ids, labels, table)

    def test_value_formatting_and_targets(self):
        self.assertEqual(reason.format_value('COUNT', math.log1p(3.2)), '3')
        self.assertEqual(reason.format_value('COUNT', -5.0), '0')
        self.assertEqual(reason.format_value('COUNT', 99.0), str(reason.COUNT_MAX))
        self.assertEqual(reason.format_value('DIST', math.log(2.44)), '2.4')
        self.assertEqual(reason.format_value('DEPTH', -9.0), '0.1')
        self.assertEqual(reason.format_value('DIST', 9.0), '30.0')
        self.assertEqual(reason.format_value('SIZE', math.log(184.6)), '185')
        self.assertEqual(reason.format_value('SIZE', 99.0), '1000')
        self.assertEqual(reason.format_value('TIME', 2, [1.0, 3.5, 6.0]), '6.0')
        self.assertAlmostEqual(reason.regression_target('DIST', 100.), math.log(30.))
        self.assertAlmostEqual(reason.regression_target('SIZE', .2), 0.)
        self.assertEqual(reason.time_class(4.8, [1.0, 3.5, 6.0]), 2)
        self.assertEqual(reason.time_class(2.25, [1.0, 3.5]), 0)
        for degrees in (-179, -90, -37, 0, 63, 90, 180):
            self.assertEqual(reason.format_value('ANGLE', reason.angle_target(degrees)), f'{degrees:+d}')
        self.assertEqual(reason.format_value('ANGLE', reason.angle_target(-180)), '+180')
        self.assertEqual(reason.format_value('ANGLE', (0.0, 0.0)), '+0')
        self.assertEqual(reason.format_value('ANGLE', (2.0, -2.0)), '+135')
        for meters in (-12.3, -0.4, 0.0, 1.3, 25.0):
            self.assertEqual(reason.format_value('COORD', reason.coord_target(meters)), f'{meters:+.1f}')
        self.assertEqual(reason.format_value('COORD', reason.coord_target(-0.04)), '+0.0')
        self.assertEqual(reason.format_value('COORD', 99.0), f'+{reason.COORD_LIMIT:.1f}')
        self.assertAlmostEqual(reason.coord_target(0.5), math.asinh(0.5))


class HeadTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_loss_path_reaches_backbone_and_every_query_head(self):
        tokenizer = ToyTokenizer()
        model = Toy()
        attach(model, settings(), tokenizer)
        _, batch, _ = reason_row(tokenizer)
        loss = row_losses(model, collate_rows([batch], 0))
        loss.sum().backward()
        self.assertGreater(model.embedding.weight.grad.norm().item(), 0)
        for name, p in model.auxiliary_heads.named_parameters():
            self.assertGreater(p.grad.abs().sum().item(), 0, name)
        self.assertIn('reason', model.auxiliary_heads.last_terms)

    def test_every_head_gets_a_gradient_even_without_queries(self):
        # DDP (no unused-parameter search) and FSDP adapter reduction need a gradient on every head tensor.
        tokenizer = ToyTokenizer()
        model = Toy()
        attach(model, settings(), tokenizer)
        _, batch, _ = reason_row(tokenizer, target='No query here.')
        self.assertEqual(batch['aux_reason_pos'].tolist(), [[-1]])
        row_losses(model, collate_rows([batch], 0)).sum().backward()
        for name, p in model.auxiliary_heads.named_parameters():
            self.assertIsNotNone(p.grad, name)
            self.assertTrue(torch.equal(p.grad, torch.zeros_like(p.grad)), name)

    def test_query_heads_converge_on_a_tiny_batch(self):
        tokenizer = ToyTokenizer()
        rows = [reason_row(tokenizer)[1], reason_row(tokenizer, f'There are {COUNT}7 tables at {TIME}13.5 seconds, {ANGLE}+120, {COORD}-8.2.')[1]]
        batch = collate_rows(rows, 0)
        heads = AuxiliaryHeads(12, settings())
        hidden = torch.randn(*batch['input_ids'].shape, 12)
        frames = video_features(hidden, batch, 3, 2).mean(dim=(2, 3))
        initial = heads.reason_loss(hidden, frames, batch).mean().item()
        optimizer = torch.optim.Adam(heads.parameters(), lr=1e-2)
        for _ in range(300):
            optimizer.zero_grad(set_to_none=True)
            heads.reason_loss(hidden, frames, batch).mean().backward()
            optimizer.step()
        final = heads.reason_loss(hidden, frames, batch).mean().item()
        self.assertLess(final, initial * .05, (initial, final))
        with torch.no_grad():
            texts = heads.reason_texts(hidden, frames, batch)
        self.assertEqual(texts, [['6.0', '3', '2.4', '185', '4.1', '-37', '+1.3'], ['7', '13.5', '+120', '-8.2']])
        print('query_toy_loss', json.dumps({'initial': initial, 'final': final}), flush=True)

    def test_collation_pads_the_query_axis(self):
        tokenizer = ToyTokenizer()
        rows = [reason_row(tokenizer)[1], reason_row(tokenizer, 'Nothing to ask.')[1]]
        batch = collate_rows(rows, 0)
        self.assertEqual(batch['aux_reason_pos'].shape, (2, 7))
        self.assertEqual(batch['aux_reason_pos'][1].tolist(), [-1] * 7)
        self.assertEqual(batch['aux_reason_kind'][1].tolist(), [-1] * 7)
        self.assertEqual(batch['aux_group_times'].shape, (2, 16))


class MixingTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_replacement_rebuilds_ids_labels_masks_and_positions(self):
        tokenizer = ToyTokenizer()
        table = reason.token_table(tokenizer)
        first, second = reason_row(tokenizer)[1], reason_row(tokenizer, f'There are {COUNT}3 tables.')[1]
        batch = collate_rows([first, second], 0)
        texts = [['13.5', '12', '0.4', '7', '10.0', '+5', '-0.7'], ['4']]
        mixed, stats = reason.apply_mixing(batch, [0], texts, table, 0)
        self.assertEqual(stats, {'rows': 1, 'queries': 7})
        length = int(mixed['attention_mask'][0].sum())
        text = tokenizer.decode(mixed['input_ids'][0, :length])
        self.assertIn(f'At {TIME}13.5 seconds', text)
        self.assertIn(f'There are {COUNT}12 tables', text)
        self.assertIn(f'{SIZE}7 cm', text)
        self.assertIn(f'Turn {ANGLE}+5 degrees and step {COORD}-0.7 m.', text)
        labels = mixed['labels'][0]
        for q in range(7):
            position, span = int(mixed['aux_reason_pos'][0, q]), int(mixed['aux_reason_span'][0, q])
            self.assertIn(int(mixed['input_ids'][0, position]), table['query'])
            self.assertEqual(int(labels[position]), int(mixed['input_ids'][0, position]))
            self.assertTrue(torch.all(labels[position + 1:position + 1 + span] == -100))
            self.assertEqual(tokenizer.decode(mixed['input_ids'][0, position + 1:position + 1 + span]), texts[0][q])
            self.assertNotEqual(int(labels[position + 1 + span]), -100)
        # Supervision elsewhere is unchanged: the same tokens, minus the replaced values, stay supervised.
        before = int((batch['labels'][0] != -100).sum()) - int(batch['aux_reason_span'][0].clamp_min(0).sum())
        self.assertEqual(int((labels != -100).sum()), before)
        self.assertTrue(torch.all(mixed['labels'][mixed['attention_mask'] == 0] == -100))
        self.assertEqual(mixed['mm_token_type_ids'].shape, mixed['input_ids'].shape)
        self.assertTrue(torch.equal(mixed['aux_reason_value'], batch['aux_reason_value']))
        # The unselected row is untouched apart from padding to the new width.
        width = int(batch['attention_mask'][1].sum())
        for key in ('input_ids', 'labels', 'attention_mask', 'mm_token_type_ids'):
            self.assertTrue(torch.equal(mixed[key][1, :width], batch[key][1, :width]), key)
        self.assertTrue(torch.equal(mixed['aux_reason_pos'][1], batch['aux_reason_pos'][1]))

    def test_mix_microbatch_trains_mixed_rows_with_correct_padding_weights(self):
        tokenizer = ToyTokenizer()
        model = Toy()
        heads = attach(model, settings(reason_mix_prob=1.0), tokenizer)
        batch = collate_rows([reason_row(tokenizer)[1], reason_row(tokenizer, f'There are {COUNT}3 tables.')[1]], 0)
        state = torch.random.get_rng_state().clone()
        mixed, stats = mix_microbatch(model, heads, batch, [1.0, 0.0], 'seed:5:0:0', 0)
        self.assertTrue(torch.equal(state, torch.random.get_rng_state()))
        self.assertTrue(model.training)
        self.assertEqual(stats['rows'], 1)
        predicted = reason_predict(model, batch)
        self.assertEqual(len(predicted[0]), 7)
        length = int(mixed['attention_mask'][0].sum())
        for q, text in enumerate(predicted[0]):
            position, span = int(mixed['aux_reason_pos'][0, q]), int(mixed['aux_reason_span'][0, q])
            self.assertEqual(tokenizer.decode(mixed['input_ids'][0, position + 1:position + 1 + span]), text)
        self.assertLessEqual(length, mixed['input_ids'].shape[1])
        losses = backward_batch(model, mixed, [1, 0], 1, 2)
        self.assertTrue(torch.isfinite(losses).all())
        # Row losses equal a fresh forward over each row alone: padding and weighting stay exact.
        model.zero_grad(set_to_none=True)
        alone = row_losses(model, {k: v[:1] for k, v in mixed.items()})
        self.assertTrue(torch.allclose(alone, losses[:1], atol=1e-6))
        # Rows with zero weight or no queries are never chosen.
        self.assertEqual(reason.choose_rows(batch['aux_reason_pos'], [0.0, 0.0], 1.0, 'k'), [])
        self.assertEqual(reason.choose_rows(torch.tensor([[-1]]), [1.0], 1.0, 'k'), [])
        self.assertEqual(reason.choose_rows(batch['aux_reason_pos'], [1.0, 1.0], 0.0, 'k'), [])

    def test_collective_mode_runs_the_prediction_forward_even_without_selection(self):
        tokenizer = ToyTokenizer()
        model = Toy()
        heads = attach(model, settings(reason_mix_prob=0.0), tokenizer)
        batch = collate_rows([reason_row(tokenizer)[1]], 0)
        calls = []
        handle = model.language_model.norm.register_forward_hook(lambda *args: calls.append(1))
        unchanged, stats = mix_microbatch(model, heads, batch, [1.0], 'k', 0, collective=True)
        self.assertEqual((len(calls), stats['rows']), (1, 0))
        unchanged, stats = mix_microbatch(model, heads, batch, [1.0], 'k', 0, collective=False)
        handle.remove()
        self.assertEqual(len(calls), 1)
        self.assertIs(unchanged, batch)


if __name__ == '__main__':
    unittest.main()
