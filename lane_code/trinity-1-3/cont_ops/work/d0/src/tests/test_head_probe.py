"""head_probe: teacher-forced readout of every head on a toy model, and its summary metrics."""
import importlib.util
import math
import unittest

import torch

from tests.auxiliary_toys import ROOT, TIMES, Toy, ToyTokenizer, encoded_row, install_runner

install_runner()
from student_pilot import auxiliary_config as config  # noqa: E402
from student_pilot import auxiliary_reason as reason  # noqa: E402
from student_pilot.auxiliary_losses import attach  # noqa: E402
from student_pilot.auxiliary_targets import category_positions  # noqa: E402

COUNT, DIST, SIZE, TIME, DEPTH, ANGLE, COORD = (reason.QUERY_TOKENS[kind] for kind in reason.KINDS)
QUESTION = 'How many tables are next to the sofa?'
PREFIX = (f'- Table: first seen at {TIME}6.0 seconds.\nThere are {COUNT}3 tables, {DIST}2.4 m apart; the sofa is '
          f'{SIZE}185 cm long and {DEPTH}4.1 m away. Turn {ANGLE}-37 degrees; the lamp is at x {COORD}-0.4 m.\n')
PIN = {'path': '/fixture/sidecar', 'sha256': '0' * 64}


def load_probe():
    spec = importlib.util.spec_from_file_location('head_probe', ROOT / 'scripts/head_probe.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def teacher_forced(model, tokenizer, prefix):
    _, batch, _ = encoded_row(tokenizer, QUESTION, 'x')
    prompt_length = int((batch['labels'][0] == -100).sum() - (batch['attention_mask'][0] == 0).sum())
    prompt = batch['input_ids'][0, :prompt_length].tolist()
    ids = prompt + tokenizer.encode(prefix)
    view = {'input_ids': torch.tensor([ids]), 'attention_mask': torch.ones(1, len(ids), dtype=torch.long),
            'labels': torch.full((1, len(ids)), -100), 'video_grid_thw': batch['video_grid_thw']}
    captured = []
    handle = model.language_model.norm.register_forward_hook(lambda module, args, output: captured.append(output))
    with torch.inference_mode():
        model(**view, logits_to_keep=1)
    handle.remove()
    return captured[0], view, prompt


class HeadProbeTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_reads_every_query_and_category_head(self):
        module = load_probe()
        tokenizer = ToyTokenizer()
        model = Toy()
        heads = attach(model, config.normalize({'count_weight': .1, 'object_weight': .1, 'reason_weight': .1,
                                                'head_width': 16, 'supervision': PIN}), tokenizer)
        hidden, view, prompt = teacher_forced(model, tokenizer, PREFIX)
        categories = [{'name': 'Tables', 'scene_count': 4, 'object': [0.5, 0.1, 2.0, -0.7, -0.4, -1.2]},
                      {'name': 'sofa', 'span': [QUESTION.index('sofa'), QUESTION.index('sofa') + 4]},
                      {'name': 'lamp'}]
        spans = module.category_spans(QUESTION, categories)
        self.assertEqual(spans, [[9, 15], [32, 36], None])
        for category, span in zip(categories, spans):
            category['span'] = span
        positions = [category_positions(tokenizer, prompt, QUESTION, [span])[0] if span else [] for span in spans]
        times = [float(f'{t:.1f}') for t in TIMES]
        result = module.probe(heads, hidden, view, len(prompt), heads.reason_table, times, categories, positions, 3, 2)
        queries = result['queries']
        self.assertEqual([(q['kind'], q['gt']) for q in queries],
                         [('TIME', 6.0), ('COUNT', 3.0), ('DIST', 2.4), ('SIZE', 185.0), ('DEPTH', 4.1), ('ANGLE', -37.0),
                          ('COORD', -0.4)])
        for q in queries:
            self.assertEqual(q['pred'], float(q['pred_text']))
            self.assertIn(int(view['input_ids'][0, q['position']]), heads.reason_table['query'])
        timing = queries[0]
        self.assertEqual(timing['gt_group'], 2)
        self.assertEqual(timing['pred'], times[timing['pred_group']])
        self.assertTrue(-180 < queries[-2]['pred'] <= 180)
        self.assertRegex(queries[-1]['pred_text'], r'^[+-]\d+\.\d$')
        tables, sofa, lamp = result['categories']
        self.assertEqual(len(tables['group_count_pred']), 16)
        self.assertGreaterEqual(tables['scene_count_pred'], 0)
        self.assertEqual(set(tables['object_pred']), {'centroid_m', 'log_extent', 'extent_m'})
        self.assertAlmostEqual(tables['object_pred']['extent_m'][0], math.exp(tables['object_pred']['log_extent'][0]))
        self.assertEqual((tables['scene_count'], 'object' in sofa), (4, False))
        self.assertIn('skipped', lamp)
        summary = module.summarize([result])
        self.assertEqual(summary['kinds']['COUNT']['n'], 1)
        self.assertEqual(summary['categories']['scene_count']['n'], 1)
        self.assertEqual(summary['categories']['object']['n'], 1)

    def test_training_only_checkpoints_skip_queries_but_read_categories(self):
        module = load_probe()
        tokenizer = ToyTokenizer()
        model = Toy()
        heads = attach(model, config.normalize({'count_weight': .1, 'head_width': 16, 'supervision': PIN}), tokenizer)
        hidden, view, prompt = teacher_forced(model, tokenizer, PREFIX)
        table = reason.token_table(tokenizer)
        positions = [category_positions(tokenizer, prompt, QUESTION, [[9, 15]])[0]]
        result = module.probe(heads, hidden, view, len(prompt), table, [float(t) for t in range(16)],
                              [{'name': 'tables', 'span': [9, 15]}], positions, 3, 2)
        self.assertTrue(all(q['pred'] is None and 'skipped' in q for q in result['queries']))
        self.assertEqual(len(result['categories'][0]['group_count_pred']), 16)
        self.assertNotIn('object_pred', result['categories'][0])

    def test_summary_metrics(self):
        module = load_probe()
        queries = [{'kind': 'COUNT', 'gt': 3, 'pred': 3}, {'kind': 'COUNT', 'gt': 3, 'pred': 4},
                   {'kind': 'COUNT', 'gt': 5, 'pred': 2},
                   {'kind': 'TIME', 'gt': 6.0, 'pred': 6.0, 'gt_group': 2, 'pred_group': 2},
                   {'kind': 'TIME', 'gt': 6.0, 'pred': 8.5, 'gt_group': 2, 'pred_group': 3},
                   {'kind': 'DIST', 'gt': 2.0, 'pred': 2.0}, {'kind': 'DIST', 'gt': 2.0, 'pred': 3.0},
                   {'kind': 'SIZE', 'gt': 0.0, 'pred': 5.0},
                   {'kind': 'ANGLE', 'gt': 170.0, 'pred': -170.0}, {'kind': 'ANGLE', 'gt': -37.0, 'pred': -60.0},
                   {'kind': 'DEPTH', 'gt': 1.0, 'pred': None},
                   {'kind': 'COORD', 'gt': 1.3, 'pred': 1.1}, {'kind': 'COORD', 'gt': -0.4, 'pred': 0.6},
                   {'kind': 'COORD', 'gt': 0.0, 'pred': -0.1}]
        summary = module.summarize([{'queries': queries}, {'error': 'ValueError: x', 'queries': []}])
        kinds = summary['kinds']
        self.assertEqual((summary['questions'], summary['errors']), (2, 1))
        self.assertEqual((kinds['COUNT']['exact'], kinds['COUNT']['within_1']), (1 / 3, 2 / 3))
        self.assertEqual(kinds['TIME']['group_hit'], .5)
        self.assertAlmostEqual(kinds['DIST']['mean_relative_accuracy'], .5)
        self.assertAlmostEqual(kinds['DIST']['median_relative_error'], .25)
        self.assertEqual((kinds['SIZE']['n'], kinds['SIZE']['excluded_zero_gt']), (0, 1))
        self.assertEqual(kinds['DEPTH']['n'], 0)
        self.assertAlmostEqual(kinds['ANGLE']['median_abs_error_deg'], 21.5)
        self.assertEqual((kinds['ANGLE']['label_agreement'], kinds['ANGLE']['side_agreement']), (.5, .5))
        coord = kinds['COORD']
        self.assertEqual(coord['n'], 3)
        self.assertAlmostEqual(coord['median_abs_error_m'], 0.2)
        self.assertAlmostEqual(coord['mean_abs_error_m'], (0.2 + 1.0 + 0.1) / 3)
        self.assertAlmostEqual(coord['within_0.5m'], 2 / 3)
        self.assertEqual(coord['sign_agreement'], .5)
        self.assertAlmostEqual(module.relative_accuracy(1.04, 1.0), 1.0)
        self.assertAlmostEqual(module.relative_accuracy(1.22, 1.0), .6)
        self.assertEqual([module.angle_label(a) for a in (0, 45, 46, 135, 136, -45, -46, -135, -136, 180)],
                         ['front', 'front', 'left', 'left', 'back', 'front', 'right', 'right', 'back', 'back'])


if __name__ == '__main__':
    unittest.main()
