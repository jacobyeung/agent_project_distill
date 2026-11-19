"""V7 delivery checks over the actual five-scene artifact and private audit records."""
import copy
import json
import os
from collections import Counter
from decimal import Decimal
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import numpy as np
from scipy.spatial.distance import cdist

from derivgen import box_v313 as B
from derivgen.ground_v312 import option_map, validate_evidence
from derivgen.ground_v312_pack import training_row
from derivgen.ground_v312_quality import selection_refusal
from derivgen.ground_v312_tokens import tokenizer_for_rows
from derivgen.ground_v313_tokens import gate_positions
from test_v312_benchmark import benchmark_templates, expected_question

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(os.environ.get('V313_PILOT', ROOT/'out/pilot_v7'))


def read(name):
    return [json.loads(s) for s in (FIXTURE/(name+'.jsonl')).read_text().splitlines()]


def native_distances(row):
    """Independent reference in the annotation frame, without the provider transform."""
    audit = row.get('program_audit', row)
    boxes = audit['independent_ordered_boxes']
    values = []
    for other in boxes[1:]:
        rng = np.random.Generator(np.random.PCG64(0))
        points = []
        for value in (boxes[0], other):
            u = rng.uniform(-1., 1., size=(512, 3))
            points.append((u * (np.asarray(value['axesLengths'], np.float64)/2.))
                          @ np.asarray(value['normalizedAxes'], np.float64).reshape(3, 3)
                          + np.asarray(value['centroid'], np.float64))
        values.append(float(cdist(*points).min()))
    return values


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read('candidates')
        cls.dispositions = read('dispositions')
        cls.box_rows = [r for r in cls.rows if r['spec_version'] == '3.13']
        cls.numeric = [r for r in cls.box_rows + cls.dispositions
                       if any(B.GAP.fullmatch(e['call']) for e in r.get('events', []))]

    def test_directions_are_byte_identical_to_v5(self):
        def directions(path):
            return {json.loads(line)['candidate_id']: line for line in path.read_text().splitlines()
                    if json.loads(line)['type'].startswith('object_rel_direction')}
        old = directions(ROOT/'out/pilot_v5/candidates.jsonl')
        self.assertEqual(len(old), 48)
        self.assertEqual(directions(FIXTURE/'candidates.jsonl'), old)

    def test_templates_options_flags_misses_and_unique_ids(self):
        templates = benchmark_templates()
        by_id = {r['candidate_id']: r for r in self.rows}
        self.assertEqual(len(by_id), len(self.rows))
        for row in self.rows:
            self.assertEqual(row['question'], expected_question(row, templates))
            self.assertFalse(row['training_admitted'])
            self.assertEqual(row['selection_refusal'], selection_refusal(row))
            validate_evidence(row)
        for name in ('gt_accepted', 'balanced', 'not_seen'):
            selected = read(name)
            self.assertEqual({r['candidate_id'] for r in selected},
                             {r['candidate_id'] for r in self.rows if r[name]})
            for row in selected:
                self.assertEqual(row, by_id[row['candidate_id']])
        self.assertEqual(len(read('not_seen')), 22)
        old_misses = {json.loads(l)['qid'] for l in (ROOT/'out/pilot_v6/not_seen.jsonl').read_text().splitlines()}
        self.assertTrue(old_misses <= {r['qid'] for r in read('not_seen')})
        for row in read('not_seen'):
            self.assertFalse(row['gt_accepted'])
            self.assertFalse(row['balanced'])
            with self.assertRaisesRegex(ValueError, 'diagnostic_miss_without_admitted_vqa'):
                training_row(dict(row, gt_accepted=True, balanced=True))
        receipt = json.loads((FIXTURE/'RECEIPT.json').read_text())
        self.assertEqual(receipt['status'], 'REVIEW-ONLY')
        self.assertFalse(receipt['training_admitted'])
        self.assertEqual(receipt['numpy_version'], '2.2.6')
        self.assertEqual(sum(v['replay_equal'] for v in receipt['agreement'].values()), len(self.rows))
        self.assertEqual(sum(v['attempted'] for v in receipt['agreement'].values()), len(self.dispositions))

    def test_box_grammar_plan_and_private_audit(self):
        for row in self.box_rows:
            relative = row['type'] == 'object_rel_distance'
            noun = 'distances' if relative else 'distance'
            self.assertIn(f'their sampled-box {noun}.', row['suffix'].splitlines()[1])
            if not row['not_seen']:
                self.assertNotRegex(row['suffix'], r'(?i)witness|exact minimum|recomput')
            for hidden in ('full_precision_box', 'ordered_box_labels', 'PCG64', 'annotation_full_box_v1'):
                self.assertNotIn(hidden, row['suffix'])
            labels = []
            for event in row['events']:
                self.assertEqual(event['audit']['box_provider'], 'annotation_full_box_v1')
                self.assertEqual(event['audit']['numpy_version'], '2.2.6')
                body = event['response'].split('\n', 1)[1].rsplit('\n', 1)[0]
                self.assertNotRegex(body, r'\d+\.\d{3}')
                if B.GROUND.fullmatch(event['call']) and 'not seen' not in body:
                    self.assertEqual(len(body.splitlines()), 4)
                    record = B.parse(body)
                    labels.append(record['label'])
                    self.assertEqual(event['audit']['box_label'], record['label'])
                    self.assertEqual(B.serialize(record['name'], record['label'], record['frames'],
                                                record['best'], event['audit']['full_precision_box']), body)
                elif B.GAP.fullmatch(event['call']):
                    self.assertEqual(event['audit']['ordered_box_labels'], labels)
                    if relative:
                        names = re.findall(r' b="([^"]+)"', event['call'])
                        self.assertEqual(names, list(option_map(row['options']).values()))
                        self.assertEqual(len(body.splitlines()), len(names)+1)
                    else:
                        self.assertRegex(body, r'^distance \d+\.\d{2} m$')
                else:
                    self.assertTrue(B.GROUND.fullmatch(event['call']))
            self.assertEqual(labels, [f'B{i+1}' for i in range(len(labels))])

    def test_every_printed_gap_replays_and_matches_annotation_transform(self):
        self.assertGreater(len(self.numeric), 250)
        for row in self.numeric:
            values = B.replay_audit(row['events'])
            expected = native_distances(row)
            np.testing.assert_allclose(values, expected, rtol=0., atol=1e-12)
            self.assertEqual(list(map(lambda x: B.number(x, 2), values)),
                             list(map(lambda x: B.number(x, 2), expected)))

    def test_reversed_draws_fail_actual_measurement_replay(self):
        original = B.sampled_box_512
        detected = 0
        with patch.object(B, 'sampled_box_512', lambda a, b: original(b, a)):
            for row in self.numeric:
                try:
                    B.replay_audit(row['events'])
                except ValueError as exc:
                    self.assertEqual(str(exc), 'audit_box_replay_mismatch')
                    detected += 1
        # Some two-decimal answers coincide under reversal; the full artifact must fail.
        self.assertGreater(detected, 0)

    def test_every_gap_rejects_mutated_draw_order_seed_or_label_order(self):
        for row in self.numeric:
            for field, value in (('draw_order', 'b_then_a'), ('seed', 1), ('samples', 511)):
                events = copy.deepcopy(row['events'])
                events[-1]['audit']['sampler'][field] = value
                with self.assertRaisesRegex(ValueError, 'audit_sampler_mismatch'):
                    B.replay_audit(events)
            events = copy.deepcopy(row['events'])
            events[-1]['audit']['ordered_box_labels'].reverse()
            with self.assertRaisesRegex(ValueError, 'audit_draw_order_mismatch'):
                B.replay_audit(events)

    def test_accepted_label_margin_token_and_package_contract(self):
        receipt = json.loads((FIXTURE/'RECEIPT.json').read_text())
        tokenizer = tokenizer_for_rows(receipt['input_pins']['tokenizer']['path'])
        for row in read('gt_accepted'):
            packed = training_row(row)
            self.assertFalse(packed['training_admitted'])
            self.assertEqual(packed['events'], row['events'])
            if row['spec_version'] != '3.13':
                continue
            values = B.replay_audit(row['events'])
            if row['type'] == 'object_abs_distance':
                self.assertEqual(row['answer'], B.number(float(row['gt_answer']), 2))
                self.assertEqual(row['answer'], B.number(values[0], 2))
                self.assertLessEqual(abs(float(row['answer'])-float(row['gt_answer'])),
                                     .05*abs(float(row['gt_answer'])))
            else:
                names = list(option_map(row['options']).values())
                printed = sorted((Decimal(B.number(v, 2)), n) for v, n in zip(values, names))
                self.assertGreaterEqual(printed[1][0]-printed[0][0], Decimal('.02'))
                self.assertEqual(row['answer'], row['gt_answer'])
                self.assertEqual(printed[0][1], option_map(row['options'])[row['answer']])
                self.assertEqual(names[int(np.argmin(values))], printed[0][1])
            self.assertEqual(row['suffix_tokens'], len(tokenizer.encode(row['suffix'], add_special_tokens=False).ids))
            self.assertLessEqual(row['suffix_tokens'], 5000)
            self.assertEqual(row['mdg_gate_token_positions'], gate_positions(tokenizer, row['suffix']))
            self.assertTrue(row['mdg_gate_token_positions'])
            self.assertEqual(packed['trace_revision'], '3.13')


if __name__ == '__main__':
    unittest.main()
