"""Streaming row checks and CLI regressions."""
import copy
import gzip
import os
import subprocess
import sys
import tempfile
import unittest

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE)
import rowschema
import util

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures', 'dryrun', 'rows')


class RowSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='rowschema_')
        self.profile = rowschema.load_profile(os.path.join(FIXTURES, 'd0_rows.profile.json'))
        self.row = {'qid': 'q1', 'family': 'a',
                    'student_input': {'fps': 30, 'total_num_frames': 10}}

    def test_null_frame_count_depends_on_layout(self):
        self.row['student_input']['total_num_frames'] = None
        bad = rowschema.check(iter([self.row]), self.profile, {'frame_layout': 'duplicate'})
        self.assertEqual(bad['violations'], {'positive_int': 1})
        self.assertEqual(bad['families']['a']['examples'][0]['id'], 'q1')
        self.assertTrue(rowschema.check([self.row], self.profile, {'frame_layout': 'spread'})['ok'])

    def test_positive_int_excludes_bools_floats_missing_and_zero(self):
        for value in (True, 0, -1, 1.5, '1', None):
            with self.subTest(value=value):
                self.row['student_input']['fps'] = value
                self.assertEqual(rowschema.check([self.row], self.profile,
                    {'frame_layout': 'duplicate'})['violations'], {'positive_int': 1})
        self.row['student_input'].pop('fps')
        self.assertFalse(rowschema.check([self.row], self.profile,
                                        {'frame_layout': 'duplicate'})['ok'])

    def test_required_missing_and_null(self):
        for value in ({'qid': 'q1'}, {'qid': 'q1', 'student_input': None}):
            self.assertEqual(rowschema.check([value], self.profile, {})['violations'], {'required': 1})
        self.assertTrue(rowschema.check([self.row], self.profile, {})['ok'])

    def test_substrings_first_path_and_case(self):
        self.row['metadata'] = {'source': '/scratch/jjyeung/orch_n30/x'}
        result = rowschema.check([self.row], self.profile, {})
        self.assertFalse(result['ok'])
        self.assertEqual(result['families']['a']['examples'][0]['path'], 'metadata.source')
        profile = {'forbid_substrings': ['blocked']}
        self.assertTrue(rowschema.check([{'x': 'safe'}], profile, {})['ok'])
        for row in ({'frames': [{'x': 'BLOCKED'}, {'x': 'blocked'}]}, {'BLOCKED': 1}):
            self.assertEqual(rowschema.check([row], profile, {})['violations'], {'forbid_substrings': 1})
        result = rowschema.check([{'x': 'a\nb'}], {'forbid_substrings': ['\\n']}, {})
        self.assertEqual(result['families']['<none>']['examples'][0]['path'], 'x')

    def test_vocab_missing_optional_and_bool_distinct(self):
        profile = {'vocab': {'answer.unit': ['m', 1]}}
        self.assertTrue(rowschema.check([{}, {'answer': {'unit': 'm'}}], profile, {})['ok'])
        for value in ('cm', True, None):
            self.assertEqual(rowschema.check([{'answer': {'unit': value}}], profile, {})['violations'],
                             {'vocab': 1})

    def test_groups_half_pair_and_complete(self):
        profile = {'groups': [{'key': 'pair.id', 'size': 2}]}
        row = {'pair': {'id': 'a'}}
        self.assertEqual(rowschema.check([row], profile, {})['violations'], {'groups': 1})
        self.assertTrue(rowschema.check([row, row], profile, {})['ok'])
        self.assertEqual(rowschema.check([{}], profile, {})['violations'], {'groups': 1})

    def test_groups_across_families(self):
        profile = {'groups': [{'key': 'pair', 'size': 2}]}
        rows = [{'family': 'a', 'pair': 1}, {'family': 'b', 'pair': 1}]
        self.assertTrue(rowschema.check(iter(rows), profile, {})['ok'])
        rows.append({'family': 'a', 'pair': 1})
        result = rowschema.check(iter(rows), profile, {})
        self.assertEqual(result['families']['a']['violations'], {'groups': 1})
        self.assertEqual(result['families']['b']['violations'], {'groups': 1})

    def test_unique(self):
        second = copy.deepcopy(self.row)
        self.assertEqual(rowschema.check([self.row, second], self.profile, {})['violations'], {'unique': 1})
        second['qid'] = 'q2'
        self.assertTrue(rowschema.check([self.row, second], self.profile, {})['ok'])
        self.assertTrue(rowschema.check([{'x': True}, {'x': 1}, {}], {'unique': ['x']}, {})['ok'])

    def test_forbid_values_files_relative_to_profile(self):
        path = os.path.join(self.tmp, 'profile.json')
        values = os.path.join(self.tmp, 'values.txt')
        with open(values, 'w') as handle:
            handle.write('blocked\nsecond\n')
        util.write_json(path, {'forbid_values_files': {'scene': 'values.txt'},
                              'forbid_values': {'scene': ['inline']}})
        profile = rowschema.load_profile(path)
        for value in ('blocked', 'inline'):
            self.assertEqual(rowschema.check([{'scene': value}], profile, {})['violations'],
                             {'forbid_values': 1})
        self.assertTrue(rowschema.check([{'scene': 'allowed'}, {}], profile, {})['ok'])

    def test_when_dotted_config_required_enum(self):
        profile = {'when': [{'config': {'layout.mode': 'x', 'enabled': True},
                             'required': ['x'], 'enum': {'kind': ['ok']}}]}
        row = {'kind': 'bad'}
        self.assertTrue(rowschema.check([row], profile, {'layout': {'mode': 'x'}})['ok'])
        self.assertTrue(rowschema.check([row], profile, {'layout': {'mode': 'x'}, 'enabled': 1})['ok'])
        config = {'layout': {'mode': 'x'}, 'enabled': True}
        self.assertEqual(rowschema.check([row], profile, config)['violations'], {'enum': 1, 'required': 1})
        self.assertTrue(rowschema.check([{'kind': 'ok', 'x': 0}], profile, config)['ok'])
        self.assertTrue(rowschema.check([{}], {'when': [{'config': {'absent': None},
                                         'required': ['x']}]}, {})['ok'])

    def test_paths_and_family_id_fields(self):
        row = {'frames': [{'name': 'x'}], 'meta': {'family': 'b', 'id': 7}}
        profile = {'required': ['frames.0.name'], 'family_field': 'meta.family', 'id_field': 'meta.id'}
        self.assertTrue(rowschema.check([row], profile, {})['ok'])
        profile['required'].append('frames.1')
        result = rowschema.check([row], profile, {})
        self.assertEqual(result['families']['b']['examples'][0]['id'], 7)
        self.assertIs(rowschema.get_path(row, 'frames.-1'), rowschema.MISSING)
        self.assertEqual(rowschema.get_path({'0': 'value'}, '0'), 'value')

    def test_one_pass_bounded_examples(self):
        class Once:
            def __init__(self):
                self.called = False

            def __iter__(self):
                if self.called:
                    raise AssertionError('iterated twice')
                self.called = True
                for _ in range(1000):
                    yield {'family': 'a'}
        result = rowschema.check(Once(), {'required': ['x']}, {}, max_examples=3)
        self.assertEqual(result['rows'], 1000)
        self.assertEqual(result['violations'], {'required': 1000})
        self.assertEqual(len(result['families']['a']['examples']), 3)
        self.assertTrue(rowschema.check(iter([]), {}, {})['ok'])

    def write_rows(self, filename, rows, compressed=False):
        path = os.path.join(self.tmp, filename)
        opener = gzip.open if compressed else open
        with opener(path, 'wb') as handle:
            for row in rows:
                handle.write(util.canonical_json(row) + b'\n')
        return path

    def cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(PACKAGE, 'rowschema.py'), 'check'] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    def test_gzip_suffix_and_magic(self):
        for name in ('rows.jsonl.gz', 'rows.magic'):
            path = self.write_rows(name, [self.row], compressed=True)
            self.assertEqual(list(rowschema.iter_rows(path)), [self.row])
            result = self.cli('--rows', path, '--profile', os.path.join(FIXTURES, 'd0_rows.profile.json'))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('a: rows=1 violations={}', result.stdout)

    def test_cli_exit_codes_and_json(self):
        profile = os.path.join(FIXTURES, 'd0_rows.profile.json')
        rows = self.write_rows('good.jsonl', [self.row])
        output = os.path.join(self.tmp, 'report.json')
        result = self.cli('--rows', rows, '--profile', profile, '--json', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(util.read_json(output)['ok'])
        self.row['student_input']['total_num_frames'] = None
        rows = self.write_rows('bad.jsonl', [self.row])
        config = os.path.join(self.tmp, 'config.json')
        util.write_json(config, {'frame_layout': 'duplicate'})
        result = self.cli('--rows', rows, '--profile', profile, '--config', config, '--max-print', '0',
                          '--json', output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn('  row ', result.stdout)
        self.assertFalse(util.read_json(output)['ok'])
        self.assertEqual(self.cli('--rows', os.path.join(self.tmp, 'absent'), '--profile', profile).returncode, 2)
        invalid = os.path.join(self.tmp, 'invalid.jsonl')
        with open(invalid, 'w') as handle:
            handle.write('{\n')
        self.assertEqual(self.cli('--rows', invalid, '--profile', profile).returncode, 2)
        self.assertEqual(self.cli('--rows', rows, '--profile', profile, '--max-print', '-1').returncode, 2)

    def test_cli_unreadable_exclusions(self):
        profile = os.path.join(self.tmp, 'profile.json')
        util.write_json(profile, {'forbid_values_files': {'x': 'absent.txt'}})
        rows = self.write_rows('rows.jsonl', [self.row])
        self.assertEqual(self.cli('--rows', rows, '--profile', profile).returncode, 2)

    def test_cli_corrupt_gzip(self):
        path = os.path.join(self.tmp, 'corrupt.jsonl.gz')
        with open(path, 'wb') as handle:
            handle.write(b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff')
        result = self.cli('--rows', path, '--profile', os.path.join(FIXTURES, 'd0_rows.profile.json'))
        self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == '__main__':
    unittest.main()
