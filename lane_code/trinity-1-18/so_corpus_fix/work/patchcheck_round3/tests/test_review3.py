"""Regression cases for the opt-in corpus review findings."""
import gzip
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest

import ingest_read as ingest
try:
    from . import test_review2 as fixtures
except ImportError:
    import test_review2 as fixtures


class Review3Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.Review2Tests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store = self.fixture.store

    def update_rows(self, path, change):
        for seq, data in list(self.store.db.execute(
                'SELECT seq,data FROM records WHERE path=?', (path,))):
            row = change(json.loads(data))
            self.store.db.execute('UPDATE records SET data=? WHERE seq=?', (ingest.dumps(row), seq))

    def partial_cli(self, subset=False):
        self.fixture.native(scripted='devrows:q' if subset else None)
        if subset:
            for path, field in [('native/paired/request.json', 'keys'), ('native/R1.json', 'expected_keys')]:
                doc = self.store.doc(path)
                doc[field].append('devrows:missing')
                self.store.db.execute('UPDATE docs SET data=? WHERE path=?', (ingest.dumps(doc), path))
        root, source = self.fixture.source()
        code, err = self.fixture.cli(root, source, 'strict', '--review2-checks')
        self.assertEqual(code, 2, err)
        self.assertFalse(os.path.exists(os.path.join(root, 'strict', 'reads')))
        code, err = self.fixture.cli(root, source, 'partial', '--review2-checks', '--archive-partial')
        self.assertEqual(code, 0, err)
        with open(os.path.join(root, 'partial/index/review2.json')) as f:
            entry = json.load(f)
        self.assertEqual(entry['status'], 'partial')
        self.assertTrue(entry['partial'])
        self.assertTrue(entry['partial_reasons'])
        with gzip.open(os.path.join(root, 'partial/reads/review2.jsonl.gz'), 'rt') as f:
            self.assertTrue(all(json.loads(line)['partial'] for line in f))

    def test_f1_missing_arm_can_be_archived_partial(self):
        self.partial_cli()

    def test_f1_subset_keys_can_be_archived_partial(self):
        self.partial_cli(subset=True)

    def test_f2_documented_new_read_command_enables_checks(self):
        tool = Path(ingest.__file__).parent
        howto = (tool / 'HOWTO.md').read_text()
        command = next(line for line in howto.splitlines() if 'bash tool/add_read.sh ' in line)
        self.assertIn('--review2-checks', shlex.split(command))
        schema = (tool / 'SCHEMA.md').read_text()
        self.assertIn('--review2-checks', schema)
        # Execute only the wrapper's ingest line, with all commands mocked.
        # No staging, publication, hostname spoofing or external writes occur.
        line = next(line for line in (tool / 'add_read.sh').read_text().splitlines()
                    if line.startswith('python3 tool/ingest_read.py ingest '))
        script = '''python3() { printf '%s\\n' "$@"; }
tee() { cat; }
SRC=fixture RID=new_id M=metadata
set -- --review2-checks --inputs 'input package'
''' + line
        result = subprocess.run(['bash', '-c', script], text=True, capture_output=True, check=True)
        args = result.stdout.splitlines()
        self.assertEqual(args.count('--review2-checks'), 1)
        self.assertEqual(args[-2:], ['--inputs', 'input package'])

    def test_f3_conflicting_key_only_scores_refused(self):
        self.fixture.kit([dict(key='devrows:q', scores={'answer': x}) for x in (0.25, 0.75)])
        with self.assertRaisesRegex(ingest.Refusal, 'Conflicting kit report scores'):
            ingest.KitAdapter(self.store).prepare()

    def test_f3_conflicting_exact_scores_refused(self):
        self.fixture.kit([dict(id='q', scores={'answer': x}) for x in (0.25, 0.75)])
        with self.assertRaisesRegex(ingest.Refusal, 'Conflicting kit report scores'):
            ingest.KitAdapter(self.store).prepare()

    def test_f3_identical_scores_and_exact_precedence_accepted(self):
        self.fixture.kit([dict(id='q', scores={'answer': 0.75})] * 2 +
                         [dict(key='devrows:q', scores={'answer': x}) for x in (0.1, 0.2)])
        ingest.KitAdapter(self.store).prepare()
        self.assertEqual(self.fixture.normalized('B2048')['arm']['scores'], {'answer': 0.75})

    def test_f3_conflict_cannot_be_archived_partial(self):
        self.fixture.kit([dict(id='q', scores={'answer': x}) for x in (0.25, 0.75)])
        root, source = self.fixture.source()
        code, err = self.fixture.cli(root, source, 'strict', '--review2-checks', '--archive-partial')
        self.assertEqual(code, 2, err)
        self.assertIn('Conflicting kit report scores', err)

    def unlabeled_report(self, conflict=False):
        self.fixture.native()
        if conflict:
            self.store.record('native/paired/results/items.jsonl',
                              dict(key='devrows:q', arm='scripted', scores={'answer': 1.0}))
        def change(row):
            row.pop('arm')
            if conflict:
                row['scores']['answer'] = 0.0
            return row
        self.update_rows('native/R1.json', change)

    def test_f4_unlabeled_report_contradiction_refused(self):
        self.unlabeled_report(conflict=True)
        with self.assertRaisesRegex(ingest.Refusal, 'Contradictory native journal/report row'):
            ingest.NativeAdapter(self.store).prepare()

    def test_f4_unlabeled_report_only_arm_is_preserved(self):
        self.unlabeled_report()
        root, source = self.fixture.source()
        code, err = self.fixture.cli(root, source, 'strict', '--review2-checks')
        self.assertEqual(code, 0, err)
        with gzip.open(os.path.join(root, 'strict/reads/review2.jsonl.gz'), 'rt') as f:
            row = json.loads(next(f))
        self.assertEqual(set(row['arms']), {'scripted', 'unflagged'})
        self.assertNotIn('arm', row['raw']['arms']['scripted'])
        self.assertTrue(all('arm' not in r for r in row['raw']['records']['native/R1.json']))

    def test_f4_unlabeled_contradiction_cannot_be_archived_partial(self):
        self.unlabeled_report(conflict=True)
        root, source = self.fixture.source()
        code, err = self.fixture.cli(root, source, 'strict', '--review2-checks', '--archive-partial')
        self.assertEqual(code, 2, err)
        self.assertIn('Contradictory native journal/report row', err)

    def test_f5_row_task_room_conflict_refused(self):
        self.fixture.native()
        self.store.record('inputs/tasks.jsonl', dict(id='q', question='Q', room='r1'))
        for path in ('native/paired/results/items.jsonl', 'native/R1.json'):
            self.update_rows(path, lambda row: dict(row, room='r2'))
        with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict.*room'):
            ingest.NativeAdapter(self.store).prepare()

    def test_f5_each_shared_identity_field_checked(self):
        fields = dict(question='Q', options=['A'], room='r1', room_key='rk', scene='s', video='v',
                      question_type='t', stratum='primary', ground_truth='A', scorer='exact',
                      units='m', unit='m', released_answer='A', released_answer_in_options=True)
        for field, value in fields.items():
            with self.subTest(field=field):
                fixture = fixtures.Review2Tests()
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                fixture.native()
                fixture.store.record('inputs/tasks.jsonl', dict(id='q', **fields))
                for seq, data in list(fixture.store.db.execute(
                        "SELECT seq,data FROM records WHERE path IN ('native/paired/results/items.jsonl', 'native/R1.json')")):
                    row = dict(json.loads(data), **{field: ['different'] if isinstance(value, list) else 'different'})
                    fixture.store.db.execute('UPDATE records SET data=? WHERE seq=?', (ingest.dumps(row), seq))
                with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict'):
                    ingest.NativeAdapter(fixture.store).prepare()

    def test_f5_additive_candidate_field_is_also_checked(self):
        self.fixture.native()
        self.store.record('inputs/a.jsonl', dict(id='q', question='Q'))
        self.store.record('inputs/b.jsonl', dict(id='q', question='Q', room='r1'))
        for path in ('native/paired/results/items.jsonl', 'native/R1.json'):
            self.update_rows(path, lambda row: dict(row, room='r2'))
        with self.assertRaisesRegex(ingest.Refusal, 'Native row/task identity conflict.*room'):
            ingest.NativeAdapter(self.store).prepare()

    def test_f5_matching_fields_and_prediction_are_accepted(self):
        self.fixture.native()
        task = dict(id='q', question='Q', room='r1', answer='truth')
        self.store.record('inputs/a.jsonl', task)
        for path in ('native/paired/results/items.jsonl', 'native/R1.json'):
            self.update_rows(path, lambda row: dict(row, room='r1', answer='prediction'))
        adapter = ingest.NativeAdapter(self.store)
        adapter.prepare()
        self.assertEqual(adapter.issues, [])
        self.assertEqual(self.fixture.normalized('unflagged')['truth']['scored'], 'truth')

    def test_f6_missing_input_task_refused(self):
        self.fixture.native()
        self.store.record('inputs/tasks.jsonl', dict(id='other', question='Q', answer='A'))
        with self.assertRaisesRegex(ingest.Refusal, 'Missing native task'):
            ingest.NativeAdapter(self.store).prepare()

    def test_f6_empty_explicit_inputs_cannot_archive_null_task(self):
        self.fixture.native()
        root, source = self.fixture.source()
        inputs = os.path.join(root, 'empty_inputs')
        os.makedirs(inputs)
        code, err = self.fixture.cli(root, source, 'strict', '--review2-checks', '--archive-partial',
                                    '--inputs', inputs)
        self.assertEqual(code, 2, err)
        self.assertIn('Missing native task', err)

    def test_f6_no_inputs_still_allows_null_task(self):
        self.fixture.native()
        adapter = ingest.NativeAdapter(self.store)
        adapter.prepare()
        self.assertEqual(adapter.issues, [])
        self.assertIsNone(self.fixture.normalized('scripted')['input'])
