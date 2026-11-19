"""Check generated questions against templates extracted from benchmark text only."""
import copy
import itertools
import json
import os
from pathlib import Path
import re
import unittest
from collections import Counter, defaultdict

from derivgen.ground_v312_quality import direction_question, distance_question, shuffled_item, selection_refusal
from derivgen.ground_v312_pack import training_row
from test_v312_ground import item

BENCHMARK = Path(os.environ.get('GROUND_BENCHMARK_TEXT',
    '/scratch/jjyeung/orch_cd/aws_32/a_build/eval/orchard_bin/cp4tk_eval/official/meta_5130.jsonl'))
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(os.environ.get('GROUND_FIXTURE', ROOT/'out/pilot_v5'))
# Directions are literal benchmark text, never template slots.
SLOTS = {'a', 'b', 'cands', 'target', 'stand', 'face', 'query', 'obj'}
PATTERNS = {
    'object_counting': r'^How many (?P<obj>.+?)\(s\) are in this room\?$',
    'object_rel_direction_easy': (r'^If I am standing by the (?P<stand>.+?) and facing the '
        r'(?P<face>.+?), is the (?P<query>.+?) to the left or the right of the (?P=face)\?$'),
    'object_abs_distance': r'^(?P<prefix>.*?distance between the )(?P<a>.+?)(?P<middle> and the )(?P<b>.+?)(?P<suffix> \(in meters\)\?)$',
    'object_rel_distance': r'^(?P<prefix>.*?objects \()(?P<cands>.+?)(?P<middle>\) is the closest to the )(?P<target>.+?)(?P<suffix>\?)$',
}
for kind in ('medium', 'hard'):
    PATTERNS['object_rel_direction_'+kind] = (
        r'^(?P<prefix>If I am standing by the )(?P<stand>.+?)(?P<middle> and facing the )'
        r'(?P<face>.+?)(?P<verb>, is the )(?P<query>.+?)(?P<prep> to my )(?P<choices>.+?)(?P<suffix>\?\n.*)$')


def benchmark_templates():
    templates = defaultdict(Counter)
    with BENCHMARK.open() as stream:
        for line in stream:
            source = json.loads(line)
            # Do not consume options, answers, scenes, or any other benchmark fields.
            typ, question = source['question_type'], source['question']
            if typ not in PATTERNS:
                continue
            match = re.fullmatch(PATTERNS[typ], question)
            if match is None:
                raise AssertionError(('unrecognized benchmark question', typ, question))
            for name in sorted(SLOTS & match.groupdict().keys(), key=match.start, reverse=True):
                a, b = match.span(name)
                question = question[:a]+'{'+name+'}'+question[b:]
            if typ == 'object_rel_direction_easy':
                question = question.rsplit(' of the ', 1)[0] + ' of the {face}?'
            templates[typ][question] += 1
    return templates


def expected_question(row, templates):
    if row['type'] in ('absolute_direction_object', 'relative_count'):
        from derivgen.gaps_v314 import question
        return question(row)
    values = dict(row['roles'])
    options = [o.split('. ', 1)[1] for o in row['options']]
    values['cands'] = ', '.join(options)
    template, = templates[row['type']]
    return template.format(**values)


def matches_template(row, templates):
    return row['question'] == expected_question(row, templates)


def read_rows(name):
    with (FIXTURE/(name+'.jsonl')).open() as stream:
        return [json.loads(line) for line in stream]


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.templates = benchmark_templates()

    def test_templates_come_from_all_benchmark_questions_of_each_type(self):
        self.assertEqual({t:sum(c.values()) for t,c in self.templates.items()}, {
            'object_abs_distance':834, 'object_rel_distance':710,
            'object_rel_direction_easy':217, 'object_counting':565,
            'object_rel_direction_medium':378, 'object_rel_direction_hard':373})
        self.assertTrue(all(len(c)==1 for c in self.templates.values()))

    def test_every_direction_permutation_matches_benchmark_template(self):
        for typ in ('object_rel_direction_medium', 'object_rel_direction_hard'):
            q = item(typ)
            for order in itertools.permutations(o.split('. ',1)[1] for o in q['options']):
                row = dict(q, options=[f'{chr(65+i)}. {v}' for i,v in enumerate(order)],
                           question=direction_question(q, order))
                self.assertEqual(row['question'], expected_question(row, self.templates))
                choices = ', '.join(order[:-1])+', or '+order[-1]
                shuffled_question = re.sub(r' to my .*?\?', ' to my '+choices+'?', row['question'], count=1)
                if shuffled_question != row['question']:
                    self.assertFalse(matches_template(dict(row,question=shuffled_question), self.templates))
                for wrong in (row['question'].replace(', is the ', ', are the '),
                              row['question'].split('\n')[0]):
                    self.assertFalse(matches_template(dict(row,question=wrong), self.templates))

    def test_distance_templates_match_complete_question_strings(self):
        for typ in ('object_abs_distance', 'object_rel_distance'):
            q = item(typ)
            orders = itertools.permutations(o.split('. ',1)[1] for o in q['options'])
            for order in orders:
                row = dict(q, options=[f'{chr(65+i)}. {v}' for i,v in enumerate(order)],
                           question=distance_question(q, order))
                self.assertEqual(row['question'], expected_question(row, self.templates))
                wrong = row['question'].replace('Measuring from the closest point of each object, ', '')
                self.assertFalse(matches_template(dict(row, question=wrong), self.templates))

    def test_already_shuffled_directions_get_fixed_question_without_reshuffling(self):
        for typ in ('object_rel_direction_medium', 'object_rel_direction_hard'):
            row = shuffled_item(dict(item(typ), gt_answer='A'))
            stale = dict(row, question=row['question'].replace('left, right, or back', 'back, left, or right')
                         .replace('front-left, front-right, back-left, or back-right',
                                  'back-left, front-left, back-right, or front-right'))
            self.assertEqual(shuffled_item(stale), row)

    def test_every_fixture_question_matches_its_benchmark_template(self):
        rows = read_rows('candidates')
        self.assertEqual(len(rows), 310)
        for row in rows:
            with self.subTest(candidate_id=row['candidate_id']):
                self.assertEqual(row['question'], expected_question(row, self.templates))

    def test_selection_files_flags_and_diagnostic_misses_agree(self):
        rows = read_rows('candidates')
        by_id = {r['candidate_id']:r for r in rows}
        self.assertEqual(len(by_id),len(rows))
        selected = {name:{r['candidate_id'] for r in read_rows(name)} for name in ('gt_accepted','balanced')}
        self.assertEqual(selected['gt_accepted'], {r['candidate_id'] for r in rows if not r['not_seen'] and r['gt_agrees']})
        self.assertTrue(selected['balanced'] <= selected['gt_accepted'])
        for name in selected:
            for row in read_rows(name):
                self.assertEqual(row, by_id[row['candidate_id']])
            for row in rows:
                self.assertEqual(row[name], row['candidate_id'] in selected[name])
        misses = [r for r in rows if r['not_seen']]
        self.assertEqual(len(misses),20)
        self.assertEqual({r['candidate_id'] for r in read_rows('not_seen')}, {r['candidate_id'] for r in misses})
        for row in misses:
            self.assertTrue(row['diagnostic_only'])
            self.assertFalse(row['training_admitted'])
            self.assertEqual(row['selection_refusal'], 'diagnostic_miss_without_admitted_vqa')
            self.assertFalse(row['gt_accepted'])
            self.assertFalse(row['balanced'])
        for row in rows:
            self.assertEqual(row['selection_refusal'], selection_refusal(row))
        for d in read_rows('dispositions'):
            if d['candidate_id'] in by_id:
                row = by_id[d['candidate_id']]
                self.assertEqual(d['reason'],row['selection_refusal'] or 'gt_match')
                self.assertEqual(d['gt_accepted'],row['gt_accepted'])

    def test_packer_rejects_misses_even_if_selection_flags_are_forged(self):
        for row in read_rows('not_seen'):
            with self.assertRaisesRegex(ValueError, 'diagnostic_miss_without_admitted_vqa'):
                training_row(dict(row,gt_accepted=True,balanced=True,training_admitted=True))
        for row in read_rows('gt_accepted'):
            packed = training_row(row)
            self.assertEqual(packed['candidate_id'],row['candidate_id'])
            self.assertFalse(packed['training_admitted'])

    def test_tool_evidence_and_absolute_distance_rule_unchanged(self):
        with (ROOT/'out/pilot_v4/candidates.jsonl').open() as stream:
            previous = {(r['qid'],tuple(r['simulated_misses'])):r for r in map(json.loads, stream)}
        rows = read_rows('candidates')
        self.assertEqual(len(rows),len(previous))
        for row in rows:
            old = previous[(row['qid'],tuple(row['simulated_misses']))]
            for key in ('events','suffix','answer','gt_agrees','gt_answer','options',
                        'question_identity','source_join','program_audit'):
                self.assertEqual(row[key],old[key],(row['candidate_id'],key))
        self.assertEqual(sum(r['type']=='object_abs_distance' and r['gt_accepted'] for r in rows),22)


if __name__ == '__main__':
    unittest.main()
