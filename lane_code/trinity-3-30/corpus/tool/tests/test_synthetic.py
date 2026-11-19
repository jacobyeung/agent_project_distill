import contextlib
import gzip
import io
import json
import os
import tarfile
import tempfile
import unittest

import corpus_score
import ingest_read as ingest


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='unit-', dir=ingest.SCRATCH)
        self.source = os.path.join(self.root, 'source')
        self.out = os.path.join(self.root, 'out')

    def write(self, name, value, lines=False):
        path = os.path.join(self.source, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = ''.join(ingest.dumps(r) + '\n' for r in value) if lines else ingest.dumps(value)
        if name.endswith('.gz'):
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(data)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(data)
        return path

    def kit(self, partial=False):
        self.write('SPEC.json', {'families': ['main'], 'export_binding': {'run': 'x', 'step': 2}})
        self.write('SUMMARY.json', {'complete': not partial, 'items': 2, 'families': {'main': {'items': 2}}})
        self.write('COMPLETE.json', {'items': 2})
        self.write('main/COMPLETE.json', {'items': 2})
        for arm in ('0', 'budget_2048', 'budget_4096'):
            rows = [dict(id=i, question='Q café', question_type='t', ground_truth='B', answer='B',
                         extracted_answer='A', raw_generation='think\n</think>\nA', response_text='A', score=score,
                         status='complete', opaque={'keep': [1, 'é']}) for i, score in [('z', 0.0), ('a', 1.0)]]
            self.write('main/a0/results/' + arm + '/0/items_a0.jsonl', rows, True)
        return self.source

    def routed(self, multi=False, missing=False):
        reads = ['0', '1'] if multi else ['0']
        self.write('SUMMARY.json', {'complete': True, 'completed': len(reads), 'expected': len(reads),
                                    'reads': [dict(read=int(r), expected=1, completed=1, complete=True) for r in reads]})
        self.write('COMPLETE.json', {'items': len(reads)})
        task = dict(id='q', question='What?', answer='A', question_type='t')
        if not missing:
            self.write('metadata/reads/0/metadata/a/3.json', {'items': [task]})
        for r in reads:
            prefix = 'metadata/reads/' + r
            self.write(prefix + '/SUMMARY.json', dict(expected=1, completed=1, complete=True,
                       shards=[dict(type=0, shard='0/1', expected=1, completed=1)]))
            prefix += '/metadata/journals/0/0'
            self.write(prefix + '/SUMMARY.json', dict(expected=1, completed=1))
            self.write(prefix + '/item_mapping.json', {'items': [dict(id='q', task_sha256=ingest.digest(task))]})
            self.write(prefix + '/items.jsonl.gz', [dict(id='q', type='t', arm='tower', mode='none', complete=True,
                       output=dict(text='tool response\n</think>\nA<|im_end|>', arm='own_depth', tokens=[1, 2],
                       finish='eos', scores={'answer': 0.5, 'released_answer': None},
                       calls={'records': [dict(call='x()', response='y', served=True, extra=3)]}))], True)
        return self.source

    def run_ingest(self, *extra):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = ingest.main(['ingest', '--source', self.source, '--read-id', 'test', '--out', self.out] + list(extra))
        return code, stdout.getvalue(), stderr.getvalue()

    def read(self, ident='test'):
        with gzip.open(os.path.join(self.out, 'reads', ident + '.jsonl.gz'), 'rt', encoding='utf-8') as f:
            return [json.loads(line) for line in f]

    def test_kit_lossless_and_idempotent(self):
        self.kit()
        code, _, err = self.run_ingest()
        self.assertEqual(code, 0, err)
        rows = self.read()
        self.assertEqual([r['item_id'] for r in rows], ['a', 'z'])
        self.assertEqual(rows[0]['truth']['scored'], 'B')
        self.assertEqual(rows[0]['arms']['full']['answer'], 'A')
        self.assertEqual(rows[0]['raw']['full']['opaque'], {'keep': [1, 'é']})
        self.assertEqual(self.run_ingest()[0], 0)
        self.assertIn('SAME', self.run_ingest()[1])
        target = os.path.join(self.out, 'reads', 'test.jsonl.gz')
        before = ingest.fingerprint(target)
        code, _, _ = self.run_ingest('--vehicle', 'changed')
        self.assertEqual(code, 3)
        self.assertEqual(before, ingest.fingerprint(target))

    def test_tar_equivalence(self):
        self.kit()
        self.assertEqual(self.run_ingest()[0], 0)
        archive = os.path.join(self.root, 'return.tgz')
        with tarfile.open(archive, 'w:gz') as tf:
            tf.add(self.source, arcname='x')
        self.source = archive
        code, text, err = self.run_ingest()
        self.assertEqual(code, 0, err)
        self.assertIn('SAME', text)

    def test_partial_and_truncated(self):
        self.kit()
        self.write('main/a0/results/budget_2048/0/items_a0.jsonl', [], True)
        self.assertEqual(self.run_ingest()[0], 2)
        code, _, err = self.run_ingest('--archive-partial')
        self.assertEqual(code, 0, err)
        self.assertTrue(all(r['partial'] for r in self.read()))

    def test_false_completion(self):
        self.kit(partial=True)
        self.assertEqual(self.run_ingest()[0], 2)

    def test_bad_row_status(self):
        self.kit()
        self.write('main/a0/results/0/0/items_a0.jsonl', [dict(id='x', status='failed')], True)
        self.assertEqual(self.run_ingest()[0], 2)

    def test_missing_completion(self):
        self.kit()
        os.rename(os.path.join(self.source, 'COMPLETE.json'), os.path.join(self.source, 'saved.json'))
        self.assertEqual(self.run_ingest()[0], 2)

    def test_routed_gzip_multiread(self):
        self.routed(multi=True)
        code, _, err = self.run_ingest()
        self.assertEqual(code, 0, err)
        for ident in ('test.r0', 'test.r1'):
            row = self.read(ident)[0]
            self.assertTrue(row['reader']['task_hash_verified'])
            self.assertEqual(row['arms']['tower']['output_arm'], 'own_depth')
            self.assertEqual(row['arms']['tower']['tool_calls'][0]['extra'], 3)
            self.assertEqual(row['arms']['tower']['answer'], 'A')
            self.assertEqual(row['raw']['input']['question'], 'What?')

    def test_read_selection(self):
        self.routed(multi=True)
        code, _, err = self.run_ingest('--read-index', '1')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.read()), 1)

    def test_missing_inputs_refused(self):
        self.routed(missing=True)
        code, _, err = self.run_ingest()
        self.assertEqual(code, 1)
        self.assertIn('--inputs', err)

    def test_metadata_precedence(self):
        self.kit()
        meta = self.write('meta.json', dict(vehicle='meta', export={'step': 9}, official=False, notes='note'))
        code, _, err = self.run_ingest('--meta', meta, '--vehicle', 'cli', '--official')
        self.assertEqual(code, 0, err)
        row = self.read()[0]
        self.assertEqual(row['vehicle'], 'cli')
        self.assertEqual(row['export']['run'], 'x')
        self.assertEqual(row['export']['step'], 9)
        self.assertTrue(row['official'])
        with open(os.path.join(self.out, 'index', 'test.json')) as f:
            self.assertEqual(json.load(f)['provenance']['vehicle'], 'cli')

    def test_score_and_percent(self):
        self.kit()
        self.assertEqual(self.run_ingest()[0], 0)
        result = corpus_score.collect(os.path.join(self.out, 'reads', 'test.jsonl.gz'), arm='full', by='question_type')
        self.assertEqual(result['arms']['full']['overall']['mean_score'], 0.5)
        self.assertEqual(corpus_score.compare(result, {'score_pct': 50}, 'score_pct')['full']['result'], 'MATCH')
        self.assertEqual(corpus_score.compare(result, {'score': 0.5}, 'score')['full']['result'], 'MATCH')
        self.assertEqual(corpus_score.compare(result, {'score_pct': 0.5}, 'score_pct')['full']['result'], 'DIFF')

    def test_lost_and_index(self):
        meta = self.write('lost.json', dict(status='orchard_only', reported_score=0.7, completed=10))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ingest.main(['lost', '--read-id', 'lost', '--out', self.out, '--meta', meta]), 0)
            self.assertEqual(ingest.main(['index', '--out', self.out]), 0)
        with open(os.path.join(self.out, 'INDEX.jsonl')) as f:
            row = json.loads(next(f))
        self.assertEqual(row['reported_score'], 0.7)
        self.assertIsNone(row['output'])

    def test_unsafe_id(self):
        self.kit()
        self.assertEqual(self.run_ingest('--read-id', '../escape')[0], 1)

    def test_stream_arrays_cross_chunks(self):
        task = {'question': 'é' * 70000, 'id': 'x', 'answer': 1}
        parser = ingest.JSONStream(io.StringIO(ingest.dumps({'items': [task], 'count': 1})))
        rows = []
        self.assertEqual(parser.document(lambda k, v: rows.append(v)), {'count': 1})
        self.assertEqual(rows, [task])

    def test_source_hashes_and_raw_reports(self):
        self.kit()
        report = dict(key='devrows:a', scores={'answer': 1}, extra={'untouched': True})
        self.write('main/report/B2048.json', {'rows': [report], 'note': 'kept'})
        code, _, err = self.run_ingest()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read()[0]['raw']['records']['main/report/B2048.json'], [report])
        self.assertEqual(self.read()[0]['arms']['B2048']['scores'], {'answer': 1})
        with open(os.path.join(self.out, 'index', 'test.json')) as f:
            index = json.load(f)
        for source in index['sources']:
            expected = ingest.fingerprint(source['path'])
            self.assertEqual(source['sha256'], expected['sha256'])
            self.assertEqual(source['bytes'], expected['bytes'])

    def test_torn_line_preserved(self):
        self.kit()
        path = os.path.join(self.source, 'main/a0/results/0/0/items_a0.jsonl')
        with open(path, 'a') as f:
            f.write('{"torn":')
        self.assertEqual(self.run_ingest()[0], 2)
        code, _, err = self.run_ingest('--archive-partial')
        self.assertEqual(code, 0, err)
        with open(os.path.join(self.out, 'index', 'test.json')) as f:
            index = json.load(f)
        self.assertEqual(next(iter(index['unparsed_records'].values()))[0]['text'], '{"torn":')

    def test_duplicate_rows_refused(self):
        self.kit()
        path = os.path.join(self.source, 'main/a0/results/0/0/items_a0.jsonl')
        with open(path) as f:
            line = next(f)
        with open(path, 'a') as f:
            f.write(line)
        code, _, err = self.run_ingest()
        self.assertEqual(code, 1)
        self.assertIn('Duplicate item/arm', err)

    def test_tar_preference_and_archive_hash(self):
        self.kit()
        fetched = os.path.join(self.root, 'fetched')
        os.makedirs(fetched)
        archive = os.path.join(fetched, 'result.tar.gz')
        with tarfile.open(archive, 'w:gz') as tf:
            tf.add(self.source, arcname='x')
        os.rename(self.source, os.path.join(fetched, 'x'))
        self.source = fetched
        code, _, err = self.run_ingest()
        self.assertEqual(code, 0, err)
        with open(os.path.join(self.out, 'index', 'test.json')) as f:
            index = json.load(f)
        self.assertIn(ingest.fingerprint(archive), index['sources'])

    def test_index_sorts_ids_with_corpus_prefix(self):
        meta = self.write('lost.json', dict(status='lost'))
        with contextlib.redirect_stdout(io.StringIO()):
            for ident in ('z', 'corpus-read', 'a'):
                self.assertEqual(ingest.main(['lost', '--read-id', ident, '--out', self.out, '--meta', meta]), 0)
            self.assertEqual(ingest.main(['index', '--out', self.out]), 0)
        with open(os.path.join(self.out, 'INDEX.jsonl')) as f:
            self.assertEqual([json.loads(line)['read_id'] for line in f], ['a', 'corpus-read', 'z'])

    def test_input_tar_and_intervention_identity(self):
        self.routed(missing=True)
        tasks = os.path.join(self.root, 'tasks.tgz')
        task = dict(id='q', question='What?', answer='A', question_type='t')
        with tarfile.open(tasks, 'w:gz') as tf:
            data = (ingest.dumps(task) + '\n').encode('utf-8')
            info = tarfile.TarInfo('native/TASKS.jsonl')
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        code, _, err = self.run_ingest('--inputs', tasks)
        self.assertEqual(code, 0, err)
        self.assertTrue(self.read()[0]['reader']['task_hash_verified'])
