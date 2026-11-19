"""Synthetic regressions for the opt-in review-two ingest checks."""
import contextlib
import gzip
import io
import json
import os
import tempfile
import unittest

import ingest_read as ingest


class Review2Tests(unittest.TestCase):
    def setUp(self):
        self.store = ingest.Store()
        # Also works against the input implementation: it ignores this attribute.
        self.store.review2_checks = True
        self.addCleanup(self.store.db.close)

    def document(self, path, value):
        self.store.consume(path, io.BytesIO(ingest.dumps(value).encode('utf-8')))

    def kit(self, report):
        self.document('SPEC.json', {'families': ['main']})
        self.document('SUMMARY.json', {'families': {'main': {'items': 1}}})
        self.document('COMPLETE.json', {'items': 1})
        self.document('main/COMPLETE.json', {'items': 1})
        for arm in ('0', 'budget_2048', 'budget_4096'):
            self.store.record('main/a0/results/' + arm + '/0/items_a0.jsonl',
                              dict(id='q', question='Which?', answer='A', score=1.0))
        self.document('main/report/B2048.json', {'rows': report})

    def native(self, scripted='devrows:q', unflagged='devrows:q'):
        self.document('COMPLETE.json', {'items': 1})
        self.document('native/paired/results/COMPLETE.json', {'items': 1})
        self.document('native/paired/request.json', {'arm': 'paired', 'keys': ['devrows:q']})
        arms = {}
        for arm, key in [('scripted', scripted), ('unflagged', unflagged)]:
            rows = [] if key is None else [dict(key=key, arm=arm, scores={'answer': 1.0})]
            arms[arm] = rows
            if arm == 'unflagged':
                for row in rows:
                    self.store.record('native/paired/results/items.jsonl', row)
        self.document('native/R1.json', {'expected_keys': ['devrows:q'], 'arms': arms})

    def test_kit_alias_rejects_actual_id(self):
        self.kit([dict(id='devrows:q', scores={'answer': 0.25})])
        adapter = ingest.KitAdapter(self.store)
        adapter.prepare()
        value = json.loads(self.store.db.execute(
            "SELECT data FROM normalized WHERE arm='B2048'").fetchone()[0])
        self.assertIsNone(value['arm']['scores'])

    def test_native_requires_exact_arm_populations(self):
        self.native(scripted='devrows:undeclared')
        with self.assertRaisesRegex(ingest.Refusal, 'native.*(arm|keys|population)'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_rejects_full_task_identity_conflict(self):
        self.native()
        self.store.record('inputs/a.jsonl', dict(id='q', question='Which?', answer='A',
                                                options=['A', 'B'], scene='one'))
        self.store.record('inputs/b.jsonl', dict(id='q', question='Which?', answer='A',
                                                options=['B', 'A'], scene='two'))
        with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
            ingest.NativeAdapter(self.store).prepare()

    def normalized(self, arm):
        return json.loads(self.store.db.execute(
            'SELECT data FROM normalized WHERE arm=?', (arm,)).fetchone()[0])

    def test_kit_key_only_alias_still_supplies_scores(self):
        self.kit([dict(key='devrows:q', scores={'answer': 0.5})])
        ingest.KitAdapter(self.store).prepare()
        self.assertEqual(self.normalized('B2048')['arm']['scores'], {'answer': 0.5})

    def test_kit_skips_actual_id_before_valid_key_only_alias(self):
        self.kit([dict(id='devrows:q', scores={'answer': 0.25}),
                  dict(key='devrows:q', scores={'answer': 0.5})])
        ingest.KitAdapter(self.store).prepare()
        self.assertEqual(self.normalized('B2048')['arm']['scores'], {'answer': 0.5})

    def test_kit_exact_id_precedes_alias(self):
        self.kit([dict(key='devrows:q', scores={'answer': 0.25}),
                  dict(id='q', scores={'answer': 0.75})])
        ingest.KitAdapter(self.store).prepare()
        self.assertEqual(self.normalized('B2048')['arm']['scores'], {'answer': 0.75})

    def test_kit_colon_id_is_exact(self):
        self.kit([dict(id='namespace:q', scores={'answer': 0.75})])
        records = list(self.store.db.execute("SELECT seq,data FROM records WHERE path LIKE '%items_a0.jsonl'"))
        for seq, data in records:
            row = dict(json.loads(data), id='namespace:q')
            self.store.db.execute('UPDATE records SET id=?,data=? WHERE seq=?',
                                  ('namespace:q', ingest.dumps(row), seq))
        ingest.KitAdapter(self.store).prepare()
        self.assertEqual(self.normalized('B2048')['arm']['scores'], {'answer': 0.75})

    def test_native_equal_counts_with_different_keys_refused(self):
        self.native(scripted='devrows:other')
        with self.assertRaisesRegex(ingest.Refusal, 'Mismatched native keys'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_matching_arms_with_wrong_declared_key_refused(self):
        self.native(scripted='devrows:other', unflagged='devrows:other')
        with self.assertRaisesRegex(ingest.Refusal, 'Mismatched native keys'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_request_and_report_keys_must_agree(self):
        self.native()
        self.store.db.execute('UPDATE docs SET data=? WHERE path=?',
                              (ingest.dumps({'arm': 'paired', 'keys': ['devrows:other']}),
                               'native/paired/request.json'))
        with self.assertRaisesRegex(ingest.Refusal, 'Contradictory native keys declarations'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_empty_report_arm_is_required_without_request_arm(self):
        self.native(scripted=None)
        self.store.db.execute('UPDATE docs SET data=? WHERE path=?',
                              ('{}', 'native/paired/request.json'))
        adapter = ingest.NativeAdapter(self.store)
        adapter.prepare()
        self.assertTrue(any('Missing native arms: scripted' in issue for issue in adapter.issues))

    def test_native_unexpected_arm_refused(self):
        self.native()
        self.store.record('native/paired/results/items.jsonl', dict(key='devrows:q', arm='extra'))
        with self.assertRaisesRegex(ingest.Refusal, 'Mismatched native arms'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_report_arm_label_must_match_row(self):
        self.native()
        self.store.db.execute("UPDATE records SET field='arms.wrong' WHERE path='native/R1.json' AND field='arms.scripted'")
        with self.assertRaisesRegex(ingest.Refusal, 'Contradictory native arm in report array'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_duplicate_declared_keys_refused(self):
        self.native()
        self.store.db.execute('UPDATE docs SET data=? WHERE path=?',
                              (ingest.dumps({'arm': 'paired', 'keys': ['devrows:q', 'devrows:q']}),
                               'native/paired/request.json'))
        with self.assertRaisesRegex(ingest.Refusal, 'Invalid native keys declaration'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_every_supplied_task_field_is_compared(self):
        base = dict(id='q', question='Which?', options=['A', 'B'], answer='A',
                    ground_truth='A', scene='one', video='video1', room='r1', room_key='rk1',
                    question_type='t', released_answer='B', released_answer_in_options=True,
                    stratum='primary', scorer='exact', units='m', unit='m', family='f',
                    arbitrary_identity={'capture': 'c1'})
        changes = dict(question='Other?', options=['B', 'A'], answer='B', ground_truth='B',
                       scene='two', video='video2', room='r2', room_key='rk2', question_type='u',
                       released_answer='C', released_answer_in_options=False, stratum='secondary',
                       scorer='different', units='cm', unit='cm', family='g',
                       arbitrary_identity={'capture': 'c2'})
        for field, value in changes.items():
            with self.subTest(field=field):
                store = ingest.Store(review2_checks=True)
                self.addCleanup(store.db.close)
                self.store = store
                self.native()
                store.record('inputs/a.jsonl', base)
                store.record('inputs/b.jsonl', dict(base, **{field: value}))
                with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
                    ingest.NativeAdapter(store).prepare()

    def test_native_compares_fields_missing_from_first_candidate(self):
        self.native()
        task = dict(id='q', question='Which?', answer='A')
        for path, row in [('a', task), ('b', dict(task, video='v1')), ('c', dict(task, video='v2'))]:
            self.store.record('inputs/' + path + '.jsonl', row)
        with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_truth_aliases_cannot_hide_contradictions(self):
        self.native()
        task = dict(id='q', question='Which?', answer='A')
        self.store.record('inputs/a.jsonl', task)
        self.store.record('inputs/b.jsonl', dict(task, ground_truth='B'))
        with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_unit_aliases_cannot_hide_contradictions(self):
        self.native()
        task = dict(id='q', question='Which?', answer=1)
        self.store.record('inputs/a.jsonl', dict(task, unit='m'))
        self.store.record('inputs/b.jsonl', dict(task, units='cm'))
        with self.assertRaisesRegex(ingest.Refusal, 'Ambiguous native task'):
            ingest.NativeAdapter(self.store).prepare()

    def test_native_identical_and_additive_task_evidence_keeps_selected_task(self):
        self.native()
        task = dict(id='q', question='Which?', answer='A', options=['A', 'B'])
        self.store.record('inputs/a.jsonl', task)
        self.store.record('inputs/b.jsonl', dict(task))
        self.store.record('inputs/c.jsonl', dict(task, room_key='known-room'))
        adapter = ingest.NativeAdapter(self.store)
        adapter.prepare()
        self.assertEqual(adapter.issues, [])
        self.assertEqual(self.normalized('scripted')['input'], task)

    def source(self):
        root = tempfile.mkdtemp(prefix='review2-', dir=ingest.SCRATCH)
        source = os.path.join(root, 'source')
        for path in self.store.paths():
            target = os.path.join(source, path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if path.endswith('.jsonl'):
                text = ''.join(ingest.dumps(row) + '\n' for row in self.store.rows(path))
            else:
                doc = self.store.doc(path)
                for field in self.store.array_fields[path]:
                    parent = doc
                    parts = field.split('.')
                    for part in parts[:-1]:
                        parent = parent.setdefault(part, {})
                    parent[parts[-1]] = []
                for field, data in self.store.db.execute('SELECT field,data FROM records WHERE path=?', (path,)):
                    parent = doc
                    parts = field.split('.')
                    for part in parts[:-1]:
                        parent = parent.setdefault(part, {})
                    parent.setdefault(parts[-1], []).append(json.loads(data))
                text = ingest.dumps(doc)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(text)
        return root, source

    def cli(self, root, source, name, *flags):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = ingest.main(['ingest', '--source', source, '--read-id', 'review2',
                                '--out', os.path.join(root, name)] + list(flags))
        return code, stderr.getvalue()

    def test_cli_switch_defaults_off_and_missing_arm_is_partial(self):
        self.native(scripted=None)
        root, source = self.source()
        self.assertEqual(self.cli(root, source, 'default')[0], 0)
        code, err = self.cli(root, source, 'strict', '--review2-checks')
        self.assertEqual(code, 2, err)
        self.assertIn('Missing native arms', err)
        self.assertFalse(os.path.exists(os.path.join(root, 'strict', 'reads')))
        code, err = self.cli(root, source, 'partial', '--review2-checks', '--archive-partial')
        self.assertEqual(code, 0, err)
        with open(os.path.join(root, 'partial/index/review2.json')) as f:
            self.assertTrue(json.load(f)['partial'])

    def test_cli_task_contradiction_cannot_be_archived_partial(self):
        self.native()
        for name, scene in [('a', 'one'), ('b', 'two')]:
            self.store.record('native/' + name + '.jsonl', dict(id='q', question='Q', answer='A', scene=scene))
        root, source = self.source()
        self.assertEqual(self.cli(root, source, 'default')[0], 0)
        for flags in [('--review2-checks',), ('--review2-checks', '--archive-partial')]:
            code, err = self.cli(root, source, 'strict', *flags)
            self.assertEqual(code, 2, err)
            self.assertIn('Ambiguous native task', err)

    def test_valid_native_outputs_byte_identical_with_switch(self):
        self.native()
        root, source = self.source()
        self.assertEqual(self.cli(root, source, 'default')[0], 0)
        self.assertEqual(self.cli(root, source, 'strict', '--review2-checks')[0], 0)
        for filename in ['reads/review2.jsonl.gz', 'index/review2.orphans.jsonl.gz', 'index/review2.json']:
            with open(os.path.join(root, 'default', filename), 'rb') as a:
                with open(os.path.join(root, 'strict', filename), 'rb') as b:
                    self.assertEqual(a.read(), b.read(), filename)

    def test_cli_bad_alias_stays_orphan_and_does_not_supply_scores(self):
        bad = dict(id='devrows:q', scores={'answer': 0.25})
        self.kit([bad])
        root, source = self.source()
        self.assertEqual(self.cli(root, source, 'strict', '--review2-checks')[0], 0)
        with gzip.open(os.path.join(root, 'strict/reads/review2.jsonl.gz'), 'rt') as f:
            row = json.loads(next(f))
        self.assertIsNone(row['arms']['B2048']['scores'])
        with gzip.open(os.path.join(root, 'strict/index/review2.orphans.jsonl.gz'), 'rt') as f:
            self.assertIn(bad, [json.loads(line)['row'] for line in f])
