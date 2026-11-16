"""Tests for pack.py: the packed kit carries no listed word, no cluster path and no copied pin."""
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import anon, pack, pins, util  # noqa: E402


def write(path, data):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))


def toy_config(pool):
    return {'schema': 'orchkit-config-v1', 'family': 'generic', 'kit_pins_sha256': '0' * 64,
            'job': {'partition': 'general', 'gpus': 0, 'cpus': 1, 'mem_gb': 1,
                    'time_limit_s': 600, 'signal_s': 60, 'nice': 0, 'root_parent': '/tmp'},
            'entry': ['python3', '{kit}/code/entry.py', '{out}'], 'n_items': 1,
            'budgets': {'return': {'max_bytes': 10 ** 7}, 'pool': {'max_bytes': 10 ** 8},
                        'home': {'max_bytes': 1024}},
            'records': [], 'spec': {}, 'stage': [],
            'return': {'pool': pool, 'gcs_prefix': 'gs://bucket/p'}}


def toy_kit(base, entry_code="print('ok')\n", config=None, out=None, rules=None):
    code = os.path.join(base, 'code_src')
    write(os.path.join(code, 'entry.py'), entry_code)
    config_path = os.path.join(base, 'config_in.json')
    util.write_json(config_path, config or toy_config('/project/x/pool'))
    return pack.pack(code, config_path, out or os.path.join(base, 'kit'), rules=rules)


class PackTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix='orchkit_pack_')

    def test_packed_toy_kit_is_opaque_and_single_place(self):
        summary = toy_kit(self.base)
        kit = summary['kit']
        self.assertEqual(anon.scan_tree(kit, anon.load_rules()), [])
        self.assertEqual(pins.check_single_place(kit), [])
        names = sorted(os.listdir(kit))
        self.assertEqual(names, ['CONFIG.json', 'PINS.json', 'code', 'lib'])
        self.assertEqual(sorted(os.listdir(os.path.join(kit, 'lib'))),
                         ['__init__.py', 'ret.py', 'stage.py', 'util.py'])
        config = util.read_json(os.path.join(kit, 'CONFIG.json'))
        manifest = util.read_json(os.path.join(kit, 'PINS.json'))
        self.assertEqual(config['kit_pins_sha256'], pins.kit_identity(manifest))
        self.assertEqual(pins.differences(pins.verify(manifest, kit)), [])
        for where, data in anon.walk_blobs(kit):
            self.assertNotIn(b'/scratch/', data, where)
            self.assertNotIn(b'import orchkit', data, where)

    def test_job_side_package_runs_from_the_kit(self):
        kit = toy_kit(self.base)['kit']
        code = subprocess.call(['/usr/bin/python3' if os.path.exists('/usr/bin/python3')
                                else sys.executable, '-E', '-s', '-B', '-m', 'lib.stage',
                                'rehearse', '--kit', kit], cwd=kit, stdout=subprocess.DEVNULL)
        self.assertEqual(code, 0)

    def test_library_name_and_bad_package_names_are_refused(self):
        for name in ('orchkit', 'Lib', 'a-b', 'split', 'x' * 17):
            with self.assertRaises(pack.PackError, msg=name):
                pack.pack(self.base, os.path.join(self.base, 'c.json'),
                          os.path.join(self.base, 'k_' + str(len(name))), package=name)

    def test_cluster_path_in_code_is_refused(self):
        with self.assertRaises(pack.PackError) as caught:
            toy_kit(self.base, entry_code="ROOT = '/scratch/jjyeung/x'\n")
        self.assertIn('opacity_hits', str(caught.exception))

    def test_copied_pin_in_code_is_refused(self):
        digest = util.sha256_file(os.path.join(TOOLS, 'orchkit', 'util.py'))[0]
        with self.assertRaises(pack.PackError) as caught:
            toy_kit(self.base, entry_code="PIN = '%s'\n" % digest)
        self.assertIn('single_place_violations', str(caught.exception))

    def test_remote_entries_join_the_manifest(self):
        remote = os.path.join(self.base, 'remote.json')
        util.write_json(remote, [{'role': 'weights', 'logical_path': 'inputs/w.tar', 'bytes': 9,
                                  'sha256': 'a' * 64, 'source': {'kind': 'gcs', 'uri': 'gs://b/w',
                                                                 'generation': '5'}}])
        code = os.path.join(self.base, 'code_src')
        write(os.path.join(code, 'entry.py'), 'pass\n')
        config_path = os.path.join(self.base, 'config_in.json')
        util.write_json(config_path, toy_config('/x/pool'))
        summary = pack.pack(code, config_path, os.path.join(self.base, 'kit'), remote=remote)
        manifest = util.read_json(os.path.join(summary['kit'], 'PINS.json'))
        self.assertIn('inputs/w.tar', [row['logical_path'] for row in manifest['entries']])


if __name__ == '__main__':
    unittest.main()
