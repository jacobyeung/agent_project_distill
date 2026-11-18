import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT
sys.path.insert(0, str(ROOT))
from fixture_attestation import capture_fixture_attestation
spec = importlib.util.spec_from_file_location('warm_fixture_support', PREVIOUS / 'test_warm_start.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
support.ROOT = ROOT
import student_pilot
student_pilot.__path__.insert(0, str(ROOT / 'student_pilot'))
from student_pilot import s1_row_order as rows, s1_warm_start as warm
from student_pilot.p3_provenance import file_pin, load, write


class OrderedRows(unittest.TestCase):
    def setUp(self):
        self.root, self.cfg, self.donor, self.receipt, self.model = support.fixture()

    def rebuild(self, name, page_size=8192, swap=False):
        original = Path(self.receipt['streams'][name]['database']['path'])
        path = self.root / (name + '_rebuilt_' + str(page_size) + ('_swap' if swap else '') + '.sqlite')
        with sqlite3.connect(original.as_uri() + '?mode=ro', uri=True) as source:
            values = list(source.execute('SELECT i,row,target FROM rows ORDER BY i'))
        if swap:
            values[0], values[1] = (0, *values[1][1:]), (1, *values[0][1:])
        with sqlite3.connect(path) as conn:
            conn.execute('PRAGMA page_size=' + str(page_size))
            conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
            conn.executemany('INSERT INTO rows VALUES (?, ?, ?)', values)
        receipt = copy.deepcopy(self.receipt)
        receipt['streams'][name]['database'] = file_pin(path)
        return receipt

    def attest(self):
        path = self.root / 'donor_order.json'
        write(path, capture_fixture_attestation(self.cfg['warm_start']['donor_config']))
        return file_pin(path)

    def test_same_rows_survive_sqlite_byte_difference_only_with_donor_attestation(self):
        rebuilt = self.rebuild('vqa')
        self.assertNotEqual(rebuilt['streams']['vqa']['database']['sha256'],
                            self.receipt['streams']['vqa']['database']['sha256'])
        self.assertEqual(rows.fingerprint(rebuilt), rows.fingerprint(self.receipt))
        with self.assertRaisesRegex(ValueError, 'row content/order'):
            warm.bind(self.cfg, rebuilt)
        cfg = copy.deepcopy(self.cfg)
        cfg['warm_start']['donor_row_order'] = self.attest()
        lineage = warm.bind(cfg, rebuilt)
        self.assertEqual(lineage['row_identity_method'], rows.SCHEMA)
        write(self.root / 'physical_vs_semantic.json', dict(
            donor=self.receipt['streams']['vqa']['database'], rebuilt=rebuilt['streams']['vqa']['database'],
            rows=rows.fingerprint(rebuilt), lineage=lineage))

    def test_equal_counts_and_indices_cannot_hide_reordered_rows(self):
        pin = self.attest()
        rebuilt = self.rebuild('vqa', swap=True)
        self.assertEqual(rebuilt['streams']['vqa']['count'], self.receipt['streams']['vqa']['count'])
        with self.assertRaisesRegex(ValueError, 'row content'):
            rows.verify(pin, self.cfg['warm_start']['donor_config'], self.donor['preparation'], rebuilt)

    def test_stream_order_target_changes_and_bad_donor_pins_refuse(self):
        pin = self.attest()
        reordered = copy.deepcopy(self.receipt)
        reordered['streams'] = dict(reversed(list(reordered['streams'].items())))
        with self.assertRaisesRegex(ValueError, 'row content'):
            rows.verify(pin, self.cfg['warm_start']['donor_config'], self.donor['preparation'], reordered)
        with self.assertRaisesRegex(ValueError, 'bound to this donor'):
            rows.verify(pin, {'path': '/wrong', 'sha256': 'f' * 64}, self.donor['preparation'], self.receipt)
        with self.assertRaisesRegex(ValueError, 'changed pinned'):
            rows.verify({**pin, 'sha256': 'f' * 64}, self.cfg['warm_start']['donor_config'],
                        self.donor['preparation'], self.receipt)

    def test_pose_mixture_mapping_is_ordered_and_not_just_a_count(self):
        receipt = copy.deepcopy(self.receipt)
        source = receipt['streams']['pose']
        path = self.root / 'pose_order.json'
        write(path, [[0, i] for i in range(source['count'])])
        receipt['streams']['pose'] = dict(kind='mix', count=source['count'], order=file_pin(path),
                                          sources=[dict(kind='rows', database=source['database'])])
        original = rows.fingerprint(receipt)
        alternate = self.root / 'pose_reordered.json'
        write(alternate, [[0, i] for i in reversed(range(source['count']))])
        receipt['streams']['pose']['order'] = file_pin(alternate)
        self.assertNotEqual(original, rows.fingerprint(receipt))

    def test_json_key_order_and_pin_relocation_are_canonical_but_targets_are_not_erased(self):
        a = dict(qid='one', frame=dict(path='/first', sha256='a' * 64), target=dict(value=1))
        b = dict(target=dict(value=1), frame=dict(sha256='a' * 64, path='/second'), qid='one')
        self.assertEqual(rows.canonical(a), rows.canonical(b))
        self.assertNotEqual(rows.canonical(a), rows.canonical({**b, 'target': {'value': 2}}))

    def test_attested_choice_derives_a_distinct_blocked_configuration(self):
        spec = importlib.util.spec_from_file_location('row_identity_template', ROOT / 'config_template.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        choice = dict(schema=module.SCHEMA, run='469ddece', artifact=self.cfg['init_artifact']['artifact'],
                      donor_config=self.cfg['warm_start']['donor_config'])
        first = module.instantiate(self.donor, choice)
        choice['donor_row_order'] = self.attest()
        attested = module.instantiate(self.donor, choice)
        self.assertNotEqual(first['run_key'], attested['run_key'])
        self.assertEqual(attested['status'], 'BLOCKED_UNSEALED')
        self.assertEqual(attested['config']['warm_start']['donor_row_order'], choice['donor_row_order'])
        receipt = self.rebuild('vqa')
        receipt['init_artifact'] = attested['config']['init_artifact']
        warm.bind(attested['config'], receipt)


if __name__ == '__main__':
    unittest.main()
