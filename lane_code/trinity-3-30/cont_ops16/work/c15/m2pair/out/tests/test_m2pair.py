"""CPU integration tests; generated fixtures remain under out/tests/artifacts/."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parent
spec = importlib.util.spec_from_file_location('m2pair', OUT / 'm2pair.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.source = m.read_rows(ROOT / 'in/result.tar.gz')
        cls.items = m.manifest_items()
        cls.same = m.compare(cls.rows, cls.rows, cls.items)
        cls.curve = json.loads((ROOT / 'in/curve.json').read_text())
        artifacts = OUT / 'tests/artifacts'
        artifacts.mkdir(exist_ok=True)
        cls.artifacts = Path(tempfile.mkdtemp(prefix='run-', dir=artifacts))

    def test_a_equals_curve_and_all_deltas_zero(self):
        self.assertEqual(self.source['camera_reads'], 1050)
        self.assertEqual(len(self.same['per_item']), 1050)
        self.assertEqual(self.same['bootstrap']['draws'], 10000)
        self.assertEqual(self.same['bootstrap']['seed'], 20261115)
        metrics_checked = 0
        for kind, modes in self.same['per_type'].items():
            self.assertEqual(self.same['counts'][kind]['shared_items'], 150)
            for mode, record in modes.items():
                expected = self.curve['per_type'][kind]['own'][mode]
                for name, metric in record['metrics'].items():
                    family, key = name.split('.')
                    with self.subTest(type=kind, mode=mode, metric=name):
                        # Exact equality includes the point, both CI endpoints, n and rooms.
                        self.assertEqual(metric['a'], expected[family][key])
                        self.assertEqual(metric['b'], expected[family][key])
                        self.assertEqual(metric['b_minus_a']['value'], 0.0)
                        self.assertEqual(metric['b_minus_a']['ci95'], [0.0, 0.0])
                        self.assertEqual(metric['b_minus_a']['valid_draws'], 10000)
                        self.assertFalse(metric['differs'])
                        if family == 'M3' and key == 'follow':
                            self.assertEqual(metric['a']['value'], 1.0)
                        metrics_checked += 1
        self.assertEqual(metrics_checked, 23)
        for kind, approximate, places in zip(m.TYPES, (.605, 17.9, .753), (3, 1, 3)):
            metric = self.same['per_type'][kind]['none']['metrics']['M2.' + m.ERROR[kind]]
            self.assertEqual(round(metric['a']['value'], places), approximate)

    def test_synthetic_displacement_error_shift_uses_scorer(self):
        shifted = copy.deepcopy(self.rows)
        shift = .25
        for row in shifted:
            if row['type'] != 'camera_displacement' or row['mode'] != 'none':
                continue
            scored = m.measure(row['output'], self.items[row['id']])['M2']['calls']
            calls = row['output']['calls']['records']
            self.assertEqual(len(calls), 1)
            value = scored[0]['gt_metres'] + scored[0]['absolute_error_m'] + shift
            calls[0]['response'] = re.sub(r'distance = [^ ]+ m',
                                         f'distance = {value:.15g} m', calls[0]['response'])
            # Existing scores must not override the new per-call measurement.
            row['measurements'] = {'M2': {'calls': [{'absolute_error_m': -999}]}}
        result = m.compare(self.rows, shifted, self.items)
        metric = result['per_type']['camera_displacement']['none']['metrics']['M2.absolute_error_m']
        self.assertAlmostEqual(metric['b']['value'] - metric['a']['value'], shift, places=12)
        self.assertAlmostEqual(metric['b_minus_a']['value'], shift, places=12)
        for bound in metric['b_minus_a']['ci95']:
            self.assertAlmostEqual(bound, shift, places=12)
        self.assertTrue(metric['differs'])
        for kind in ('camera_rotation', 'camera_movement_direction'):
            for record in result['per_type'][kind].values():
                for unchanged in record['metrics'].values():
                    self.assertEqual(unchanged['b_minus_a']['ci95'], [0., 0.])

    def test_mismatched_item_sets_report_counts(self):
        removed = self.rows[0]['id']
        b = [r for r in self.rows if r['id'] != removed]
        with self.assertRaisesRegex(ValueError, 'Item sets differ') as error:
            m.compare(self.rows, b, self.items)
        counts = json.loads(str(error.exception).split(': ', 1)[1])['camera_displacement']
        self.assertEqual((counts['a_items'], counts['b_items'], counts['shared_items']), (150, 149, 149))
        self.assertEqual(counts['only_a'], [removed])

    def test_missing_mode_and_duplicate_refuse(self):
        b = [r for r in self.rows if not (r['id'] == self.rows[0]['id'] and r['mode'] != 'none')]
        with self.assertRaisesRegex(ValueError, 'Read sets differ'):
            m.compare(self.rows, b, self.items)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            m.compare(self.rows, self.rows + [self.rows[0]], self.items)
        with self.assertRaisesRegex(ValueError, 'Incomplete mode plan'):
            m.compare(b, b, self.items)

    def test_room_mismatch_refuses(self):
        b = [dict(r) for r in self.rows]
        b[0]['room_key'] = 'different-room'
        with self.assertRaisesRegex(ValueError, 'room differs'):
            m.compare(self.rows, b, self.items)

    def test_bootstrap_matches_package_for_complete_pairs(self):
        values = [('r1', 1., 3.), ('r1', 2., 5.), ('r2', 20., 10.), ('r3', 5., 6.)]
        actual = m.paired_bootstrap(values)
        expected = m.statistics.bootstrap([(room, b-a) for room, a, b in values])
        self.assertAlmostEqual(actual['value'], expected['value'])
        for a, b in zip(actual['ci95'], expected['ci95']):
            self.assertAlmostEqual(a, b)

    def test_missing_values_keep_separate_denominators(self):
        values = [('r1', 0., 1.), ('r1', None, 9.), ('r2', 10., 7.), ('r2', 2., None)]
        actual = m.paired_bootstrap(values)
        self.assertAlmostEqual(actual['value'], 17/3 - 12/3)
        self.assertEqual(actual['ci95'], [1., 5.])
        self.assertEqual(actual['n_both'], 2)
        self.assertEqual(actual['valid_draws'], 10000)

    def test_undefined_draws_do_not_produce_a_conditional_interval(self):
        result = m.paired_bootstrap([('r1', 0., 1.), ('r2', 2., None)])
        self.assertEqual(result['value'], 0.)
        self.assertIsNone(result['ci95'])
        self.assertGreater(result['undefined_draws'], 0)
        self.assertIsNone(m.paired_bootstrap([('r1', None, 1.)])['value'])

    def fixture_rows(self):
        identifier = self.rows[0]['id']
        rows = copy.deepcopy([r for r in self.rows if r['id'] == identifier])
        for row in rows:
            row['output'] = {k: row['output'][k] for k in ('text', 'finish', 'calls', 'scores')}
        return rows

    def test_tar_directory_and_cli(self):
        rows = self.fixture_rows()
        journal = self.artifacts / 'extracted/metadata/journals/0/0/items.jsonl'
        journal.parent.mkdir(parents=True)
        payload = ''.join(json.dumps(r) + '\n' for r in rows).encode()
        journal.write_bytes(payload)
        archive_path = self.artifacts / 'return.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as archive:
            info = tarfile.TarInfo('metadata/journals/0/0/items.jsonl')
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        actual, _ = m.read_rows(archive_path)
        extracted, _ = m.read_rows(self.artifacts / 'extracted')
        self.assertEqual(actual, extracted)
        output, md = self.artifacts / 'comparison.json', self.artifacts / 'comparison.md'
        run = subprocess.run([sys.executable, '-B', str(OUT / 'm2pair.py'),
                              '--a', str(archive_path), '--b', str(self.artifacts / 'extracted'),
                              '--output', str(output), '--md', str(md)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(output.read_text())
        self.assertEqual(result['counts']['camera_displacement']['shared_items'], 1)
        self.assertIn('B−A [95% CI]', md.read_text())
        self.assertEqual(len(result['per_item']), 3)

    def test_incomplete_jsonl_refuses(self):
        rows = self.fixture_rows()
        rows[0]['complete'] = False
        path = self.artifacts / 'incomplete.jsonl'
        path.write_text(json.dumps(rows[0]) + '\n')
        with self.assertRaisesRegex(ValueError, 'incomplete record'):
            m.read_rows(path)


if __name__ == '__main__':
    unittest.main()
