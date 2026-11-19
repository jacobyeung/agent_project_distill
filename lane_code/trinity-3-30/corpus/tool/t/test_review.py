"""Review regressions; fixtures and generated artifacts stay in t/."""
import gzip
import json
import os
import unittest

import ingest_read as ingest
import corpus_score
from tests import test_synthetic as fixtures


class ReviewTests(unittest.TestCase):
    setUp = fixtures.CorpusTests.setUp
    write = fixtures.CorpusTests.write
    kit = fixtures.CorpusTests.kit
    routed = fixtures.CorpusTests.routed
    run_ingest = fixtures.CorpusTests.run_ingest
    read = fixtures.CorpusTests.read

    def index(self):
        with open(os.path.join(self.out, 'index/test.json')) as f:
            return json.load(f)

    def orphans(self):
        with gzip.open(os.path.join(self.out, self.index()['orphans']['path']), 'rt') as f:
            return [json.loads(line)['row'] for line in f]

    def test_a1_every_consumed_row_survives(self):
        self.kit()
        unmatched = [{'key': 'devrows:orphan', 'extra': 'KEEP'}, {'no_id': True}, 42]
        matched = {'id': 'a', 'room_key': 'KEEP', 'question': 'Q café'}
        self.write('main/report/B2048.json', {'rows': unmatched + [matched]})
        self.write('ITEMS.jsonl', [{'id': 'missing', 'extra': 7}], True)
        self.assertEqual(self.run_ingest()[0], 0)
        self.assertEqual(self.index()['orphan_count'], 4)
        for row in unmatched:
            self.assertIn(row, self.orphans())
        self.assertIn(matched, self.read()[0]['raw']['records']['main/report/B2048.json'])

    def test_a1_routed_manifest_mapping_and_extra_tasks(self):
        self.routed()
        task = dict(id='q', question='What?', answer='A', question_type='t', room_key='KEEP')
        other = dict(id='unused', question='Unused?', answer='B')
        self.write('metadata/reads/0/metadata/a/3.json', {'items': [task, other]})
        mapping = dict(id='q', task_sha256=ingest.digest(task))
        unused_mapping = dict(id='unused', task_sha256='unused')
        self.write('metadata/reads/0/metadata/journals/0/0/item_mapping.json', {'items': [mapping, unused_mapping]})
        self.assertEqual(self.run_ingest()[0], 0)
        self.assertEqual(self.read()[0]['raw']['input'], task)
        self.assertIn(other, self.orphans())
        self.assertIn(unused_mapping, self.orphans())

    def test_a2_contradictory_hash_never_archived(self):
        self.routed()
        self.write('metadata/reads/0/metadata/a/3.json', {'items': [dict(id='q', question='Wrong', answer='B')]})
        for flags in [(), ('--archive-partial',)]:
            code, _, err = self.run_ingest(*flags)
            self.assertEqual(code, 2, err)
            self.assertIn('task_sha256', err)

    def replace_arm(self, change):
        path = 'main/a0/results/budget_2048/0/items_a0.jsonl'
        with open(os.path.join(self.source, path)) as f:
            rows = [json.loads(line) for line in f]
        change(rows)
        self.write(path, rows, True)

    def test_a2_documented_room134_binding(self):
        self.routed()
        task = dict(id='q', question='Area?', answer='15.34', ground_truth=15.340000000000002,
                    question_type='room_size_estimation', r0_split='R0-dev', room_key='KEEP')
        self.write('metadata/reads/0/metadata/a/3.json', {'items': [task]})
        self.write('metadata/reads/0/metadata/journals/0/0/item_mapping.json',
                   {'items': [dict(id='q', task_sha256=ingest.digest(dict(task, answer=task['ground_truth'])))]})
        self.assertEqual(self.run_ingest()[0], 0)
        row = self.read()[0]
        self.assertEqual(row['raw']['input'], task)
        self.assertEqual(row['reader']['task_join_rule'], 'room134.bind:answer=ground_truth')
        self.assertTrue(row['reader']['task_hash_verified'])

    def test_a3_population_mismatch(self):
        self.kit()
        self.replace_arm(lambda rows: rows[0].update(id='different'))
        self.assertEqual(self.run_ingest()[0], 2)
        self.assertEqual(self.run_ingest('--archive-partial')[0], 0)
        self.assertTrue(any('populations' in x for x in self.index()['partial_reasons']))

    def test_a3_question_and_truth_conflict(self):
        self.kit()
        self.replace_arm(lambda rows: rows[0].update(question='Other?', ground_truth='C'))
        self.assertEqual(self.run_ingest()[0], 2)
        self.assertEqual(self.run_ingest('--archive-partial')[0], 0)
        self.assertTrue(any('question/truth' in x for x in self.index()['partial_reasons']))

    def test_a3_counts_must_equal(self):
        self.kit()
        self.write('SUMMARY.json', {'items': 1, 'families': {'main': {'items': 1}}})
        code, _, err = self.run_ingest()
        self.assertEqual(code, 2)
        self.assertIn('!= expected', err)

    def test_a4_exact_colon_ids(self):
        self.kit()
        for arm in ('0', 'budget_2048', 'budget_4096'):
            path = 'main/a0/results/' + arm + '/0/items_a0.jsonl'
            with open(os.path.join(self.source, path)) as f:
                rows = [json.loads(line) for line in f]
            for row in rows:
                row['id'] = 'namespace:' + row['id']
            self.write(path, rows, True)
        report = dict(id='namespace:a', scores={'answer': 0.25})
        self.write('main/report/B2048.json', {'rows': [report]})
        self.assertEqual(self.run_ingest()[0], 0)
        row = self.read()[0]
        self.assertEqual(row['item_id'], 'namespace:a')
        self.assertEqual(row['arms']['B2048']['scores'], report['scores'])
        self.assertIn(report, row['raw']['records']['main/report/B2048.json'])

    def test_a5_reserved_arm_names(self):
        self.routed()
        path = 'metadata/reads/0/metadata/journals/0/0/items.jsonl.gz'
        with gzip.open(os.path.join(self.source, path), 'rt') as f:
            row = json.loads(next(f))
        row['arm'] = 'input'
        self.write(path, [row], True)
        self.assertEqual(self.run_ingest()[0], 0)
        raw = self.read()[0]['raw']
        self.assertEqual(raw['input']['question'], 'What?')
        self.assertEqual(raw['arms']['input'], row)

    def test_a6_supplementary_status(self):
        self.kit()
        self.write('ITEMS.jsonl', [{'id': 'a', 'status': 'failed'}], True)
        self.assertEqual(self.run_ingest()[0], 2)

    def test_a6_report_status_even_orphan(self):
        self.kit()
        self.write('main/report/B2048.json', {'rows': [{'id': 'orphan', 'status': 'failed'}]})
        self.assertEqual(self.run_ingest()[0], 2)

    def test_a6_task_status(self):
        self.routed()
        self.write('metadata/extra.json', {'items': [{'id': 'unused', 'status': 'failed'}]})
        self.assertEqual(self.run_ingest()[0], 2)

    def test_a7_zero_generations(self):
        self.write('SPEC.json', {'families': ['main']})
        self.write('FAILED.json', {})
        self.assertEqual(self.run_ingest()[0], 2)
        self.assertEqual(self.run_ingest('--archive-partial')[0], 2)
        self.assertFalse(os.path.exists(os.path.join(self.out, 'reads/test.jsonl.gz')))

    def test_a8_manifest_content(self):
        self.routed()
        old = os.path.join(self.source, 'metadata/reads/0/metadata/a/3.json')
        with open(old) as f:
            manifest = json.load(f)
        manifest['name'] = 'room134'
        os.rename(old, old + '.saved')
        self.write('metadata/reads/0/metadata/a/4.json', manifest)
        self.assertEqual(self.run_ingest()[0], 0)
        self.assertEqual(self.read()[0]['set'], 'room134')

    def test_mean_of_types_nested_categories(self):
        path = os.path.join(self.root, 'scores.jsonl.gz')
        rows = [('x', 'x1', 1), ('x', 'x1', 1), ('x', 'x2', 0), ('y', 'y1', 1)]
        with gzip.open(path, 'wt') as f:
            for category, typ, score in rows:
                f.write(json.dumps(dict(category=category, question_type=typ, arms={'a': {'score': score}})) + '\n')
        result = corpus_score.collect(path, arm='a', by='category', mean_of_types=True)['arms']['a']
        self.assertEqual(result['groups']['x']['mean_score'], 0.5)
        self.assertEqual(result['overall']['mean_score'], 0.75)

    def test_mean_of_types_null_group(self):
        path = os.path.join(self.root, 'null-group.jsonl.gz')
        with gzip.open(path, 'wt') as f:
            for score in (0, 1):
                f.write(json.dumps(dict(family=None, question_type='t', arms={'a': {'score': score}})) + '\n')
        result = corpus_score.collect(path, by='family', mean_of_types=True)
        self.assertEqual(result['arms']['a']['groups']['null']['mean_score'], 0.5)

    def test_offread_categories_and_budget_paths(self):
        self.write('SPEC.json', {'step': 544})
        self.write('COMPLETE.json', {'items': 1})
        self.write('report/B2048.json', {'groups': {'direction': {'score': 0.5}}})
        row = dict(id='ns:q', question='Q', ground_truth='A', question_type='direction_easy',
                   raw_generation='trace', extracted_answer='A', score=0.5)
        for path in ('a0/results/0/items_a0.jsonl', 'a0/results/0/budget_2048.jsonl',
                     'a0/results/budget_4096/0/items_a0.jsonl'):
            self.write(path, [row], True)
        self.assertEqual(self.run_ingest()[0], 0)
        item = self.read()[0]
        self.assertEqual(item['reader']['format'], 'offread')
        self.assertEqual(item['category'], 'direction')
        self.assertEqual(set(item['arms']), {'full', 'B2048', 'B4096'})

    def test_native_calls_and_scored_refusals(self):
        self.write('COMPLETE.json', {'step': 544})
        self.write('native/paired/results/COMPLETE.json', {'items': 2})
        call = dict(call='move()', response='1m', at_token=3, audit={'keep': True})
        row = dict(key='devrows:q', arm='unflagged', scores={'answer': 1.0},
                   decode=dict(text='trace</think>A', calls=[call], generated_tokens=10))
        refused = dict(key='devrows:r', arm='unflagged', scores={'answer': 0.0}, no_answer=True,
                       decode_executed=False, total_tokens=0, geometry_refusal={'code': 'refused'})
        self.write('native/paired/results/items.jsonl', [row, refused], True)
        self.write('native/R1.json', {'arms': {'unflagged': [row, refused]}})
        self.assertEqual(self.run_ingest()[0], 0)
        rows = self.read()
        self.assertEqual(rows[0]['arms']['unflagged']['tool_calls'], [call])
        self.assertEqual(rows[1]['raw']['arms']['unflagged'], refused)
        self.assertEqual(rows[1]['arms']['unflagged']['output_tokens'], 0)
        self.assertIsNone(rows[1]['arms']['unflagged']['trace'])

    def test_nested_native_arrays_streamed(self):
        rows = []
        import io
        value = {'arms': {'scripted': [{'key': 'a'}], 'unflagged': [{'key': 'b'}]}, 'expected_keys': ['a', 'b']}
        doc = ingest.JSONStream(io.StringIO(ingest.dumps(value))).document(lambda k, r: rows.append((k, r)))
        self.assertEqual(rows, [('arms.scripted', {'key': 'a'}), ('arms.unflagged', {'key': 'b'})])
        self.assertEqual(doc['expected_keys'], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
