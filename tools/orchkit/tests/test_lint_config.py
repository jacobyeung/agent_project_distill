"""Config and source lint regressions, including command-line exit codes."""
import base64
import copy
import os
import subprocess
import sys
import tempfile
import unittest

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PACKAGE)
import lint_config
import util

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures', 'dryrun', 'lint')


class LintConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='lint_config_')
        self.schema = util.read_json(os.path.join(FIXTURES, 'toy.schema.json'))
        self.config = {
            'schema': 'orchkit-config-v1', 'kit_pins_sha256': 'a' * 64,
            'job': {'partition': 'general', 'gpus': 1, 'cpus': 8, 'mem_gb': 64,
                    'time_limit_s': 10800, 'signal_s': 600, 'nice': 0},
            'entry': ['python3', 'entry.py'], 'n_items': 300,
            'budgets': {'out': {'max_bytes': 3000000000, 'per_item_bytes': 10000000},
                        'time': {'per_item_s': 30, 'fixed_s': 100}},
            'records': [], 'spec': {}}

    def rules(self, value, **kwargs):
        return [item['rule'] for item in lint_config.lint(value, **kwargs)]

    def test_clean_with_schema_and_old_config(self):
        self.assertEqual(lint_config.lint(self.config, self.schema), [])
        self.assertEqual(lint_config.lint({'arbitrary': 'ordinary prose allowed here'}), [])

    def test_members_prose_regression(self):
        value = {'anchors': {'members': 'xx/<sha>.png plus ANCHORS_MANIFEST.json'}}
        self.assertIn('prose', self.rules(value))

    def test_byte_and_time_budgets(self):
        self.config['budgets']['out']['max_bytes'] = 1500000000
        self.assertIn('budget', self.rules(self.config))
        self.config['budgets']['out'].pop('per_item_bytes')
        self.assertIn('budget', self.rules(self.config))
        self.config['budgets'] = {'time': {'per_item_s': 40, 'fixed_s': 20}}
        self.assertIn('budget', self.rules(self.config))
        self.config['budgets']['time'].pop('per_item_s')
        self.assertIn('budget', self.rules(self.config))
        self.config.pop('n_items')
        self.assertIn('budget', self.rules(self.config))

    def test_bad_budget_types(self):
        for per in (None, True, 0, -1, '10', 1.5):
            with self.subTest(per=per):
                self.config['budgets']['out']['per_item_bytes'] = per
                self.assertIn('budget', self.rules(self.config))
        self.assertIn('budget', self.rules({'budgets': []}))
        self.assertIn('budget', self.rules({'budgets': {'x': None}, 'n_items': 1}))

    def test_zero_item_and_zero_time_budget(self):
        self.assertEqual(lint_config.lint({'n_items': 0, 'budgets': {
            'out': {'per_item_bytes': 1, 'max_bytes': 0},
            'time': {'per_item_s': 0}}, 'job': {'time_limit_s': 0}}), [])

    def test_schema_errors(self):
        changes = [('n_items', True), ('schema', 'wrong'), ('entry', [1]), ('extra', 1)]
        for key, value in changes:
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key):
                self.assertIn('schema', self.rules(config, schema=self.schema))
        self.config.pop('spec')
        self.assertIn('schema', self.rules(self.config, schema=self.schema))

    def test_schema_subset(self):
        pairs = [({'type': ['null', 'string']}, None, 1),
                 ({'type': 'boolean'}, False, 0),
                 ({'type': 'number'}, 2.5, True),
                 ({'type': 'integer'}, 2, False),
                 ({'pattern': '^x$'}, 'x', 'xy'),
                 ({'pattern': 'x'}, 'axb', 'ab'),
                 ({'minimum': 2}, 2, 1),
                 ({'enum': [1]}, 1, True),
                 ({'type': 'object', 'additionalProperties': {'type': 'integer'}},
                  {'x': 1}, {'x': '1'})]
        for schema, good, bad in pairs:
            with self.subTest(schema=schema):
                self.assertEqual(lint_config.check_schema(good, schema), [])
                self.assertTrue(lint_config.check_schema(bad, schema))

    def test_prose_nested_and_inventory_keys(self):
        for value in ('a b', 'a<z>', 'a...b', 'TODO', 'a/plus/b', '../x', 'x//y'):
            with self.subTest(value=value):
                self.assertIn('prose', self.rules({'pin': {'nested': [value]}}))
        self.assertIn('prose', self.rules({'inventory': [{'bad key': 'ok'}]}))
        for value in ('a/b', '/opt/x', 'gs://b/object', '42', 'A' * 64):
            self.assertEqual(lint_config.lint({'path': value}), [])

    def test_pinned_field_rules(self):
        good = {'generation': '12', 'md5': base64.b64encode(b'x' * 16).decode('ascii'),
                'crc32c': base64.b64encode(b'x' * 4).decode('ascii'),
                'sha256': 'A' * 64, 'x_sha256': 'a' * 64, 'digest': 'b' * 64,
                'members': {'a/b': 'c' * 64, 'c': {'bytes': 0, 'sha256': 'd' * 64}}}
        self.assertEqual(lint_config.lint(good), [])
        for key, value in [('generation', 0), ('generation', True), ('generation', {}),
                           ('md5', 'bad'), ('crc32c', []), ('sha256', {}),
                           ('x_sha256', 'short'), ('digest', None),
                           ('members', {'/absolute': 'a' * 64}),
                           ('members', {'a': {'bytes': True, 'sha256': 'a' * 64}}),
                           ('members', {'a': {'bytes': 0, 'sha256': []}})]:
            with self.subTest(key=key, value=value):
                self.assertIn('prose', self.rules({key: value}))

    def test_host_paths_and_opacity(self):
        for value in ('/scratch/jjyeung/x', 'file=/home/x', '/data/x', '/data2/x',
                      '/data3/x', '/data4/x', 'trinity', 'trinity-1-3',
                      'x.vision.cs.cmu.edu'):
            with self.subTest(value=value):
                self.assertIn('host_path', self.rules({'free': [{'text': value}]}))
        self.assertIn('host_path', self.rules({'text': 'A SeCrEt token'}, opacity_words=['secret']))
        self.assertIn('host_path', self.rules({'/home/x': 'ok'}))
        self.assertEqual(lint_config.lint({'text': '/database/x trinityish'}), [])

    def manifest(self):
        return {'schema': 'orchkit-pins-v1', 'entries': [
            {'role': 'record', 'logical_path': 'records/a', 'bytes': 2, 'sha256': 'b' * 64,
             'source': {'kind': 'gs', 'uri': 'gs://bucket/a', 'generation': '1'}}]}

    def test_pins_identity_and_records(self):
        pins = self.manifest()
        self.config['kit_pins_sha256'] = util.canonical_sha256(pins)
        self.config['records'] = [{'logical_path': 'records/a', 'sha256': 'b' * 64}]
        self.assertEqual(lint_config.lint(self.config, pins=pins), [])
        self.config['kit_pins_sha256'] = 'c' * 64
        self.assertIn('pins', self.rules(self.config, pins=pins))
        self.config['kit_pins_sha256'] = util.canonical_sha256(pins)
        for key, value in [('sha256', 'd' * 64), ('logical_path', 'missing'), ('logical_path', [])]:
            config = copy.deepcopy(self.config)
            config['records'][0][key] = value
            self.assertIn('pins', self.rules(config, pins=pins))
        pins['entries'][0]['role'] = 'asset'
        self.config['kit_pins_sha256'] = util.canonical_sha256(pins)
        self.assertIn('pins', self.rules(self.config, pins=pins))

    def test_pin_order_and_uniqueness(self):
        pins = self.manifest()
        pins['entries'].append(copy.deepcopy(pins['entries'][0]))
        self.config['kit_pins_sha256'] = util.canonical_sha256(pins)
        self.assertIn('pins', self.rules(self.config, pins=pins))
        pins['entries'][0]['logical_path'] = 'z'
        self.config['kit_pins_sha256'] = util.canonical_sha256(pins)
        self.assertIn('pins', self.rules(self.config, pins=pins))

    def test_hardcoded_caps_required_regression(self):
        source = "parser.add_argument('--max-bytes', type=int, default=1500000000)\ndef run(out_cap=1.5e9): pass\n"
        findings = lint_config.hardcoded_caps(source, 'entry.py')
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(item['rule'] == 'cap_default' for item in findings))
        self.assertEqual(lint_config.hardcoded_caps(
            "parser.add_argument('--max-bytes', type=int, required=True)", 'entry.py'), [])

    def test_hardcoded_caps_scope_and_dest(self):
        source = """MAX_OUT_BYTES = 1500000000
if True:
    timeout: int = -2
parser.add_argument('-x', dest='quota', default=+10)
async def run(*, budget=3):
    local_cap = 1
    return local_cap
class Example:
    class_cap = 1
    def method(self, limit=4): pass
f = lambda cap=5: cap
"""
        self.assertEqual(len(lint_config.hardcoded_caps(source, 'entry.py')), 6)
        self.assertEqual(lint_config.hardcoded_caps(
            'max_ok = True\ncap = None\nx = 4\ndef f(timeout=None): pass', 'entry.py'), [])
        with self.assertRaises(SyntaxError):
            lint_config.hardcoded_caps('def broken(', 'entry.py')

    def test_hardcoded_cap_expressions_and_unpacking(self):
        source = 'MAX_BYTES, other = (1024 ** 3, 1)\ndef f(timeout=60 * 5): pass\n'
        self.assertEqual(len(lint_config.hardcoded_caps(source, 'entry.py')), 2)

    def cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(PACKAGE, 'lint_config.py')] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    def test_cli_exit_codes_and_json(self):
        path = os.path.join(self.tmp, 'config.json')
        output = os.path.join(self.tmp, 'report.json')
        util.write_json(path, self.config)
        result = self.cli(path, '--schema', os.path.join(FIXTURES, 'toy.schema.json'), '--json', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(util.read_json(output)['ok'])
        self.config['free'] = '/scratch/jjyeung/x'
        util.write_json(path, self.config)
        result = self.cli(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn('host_path free:', result.stdout)
        self.assertEqual(self.cli(os.path.join(self.tmp, 'absent')).returncode, 2)
        with open(path, 'w') as handle:
            handle.write('{')
        self.assertEqual(self.cli(path).returncode, 2)

    def test_cli_code_and_opacity_and_pins(self):
        config = os.path.join(self.tmp, 'config.json')
        code = os.path.join(self.tmp, 'entry.py')
        clean = os.path.join(self.tmp, 'clean.py')
        words = os.path.join(self.tmp, 'words.txt')
        pins = os.path.join(self.tmp, 'pins.json')
        util.write_json(config, self.config)
        with open(code, 'w') as handle:
            handle.write('MAX_BYTES = 1\n')
        with open(clean, 'w') as handle:
            handle.write('x = 1\n')
        result = self.cli(config, '--code', code, '--code', clean)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.count('cap_default '), 1)
        with open(code, 'w') as handle:
            handle.write('def broken(')
        self.assertEqual(self.cli(config, '--code', code).returncode, 2)
        with open(words, 'w') as handle:
            handle.write('GENERAL\n')
        self.assertEqual(self.cli(config, '--opacity-words', words).returncode, 1)
        util.write_json(pins, self.manifest())
        self.assertEqual(self.cli(config, '--pins', pins).returncode, 1)


if __name__ == '__main__':
    unittest.main()
