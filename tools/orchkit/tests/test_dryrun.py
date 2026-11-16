"""Dry run on the toy kit: one passing run and one mutant per failure class."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import dryrun  # noqa: E402
import util  # noqa: E402

FIX = os.path.join(HERE, 'fixtures', 'dryrun')
KIT_PY = os.environ.get('ORCHKIT_DRYRUN_PY', '/scratch/jjyeung/envs/p1cpu/bin/python')
BWRAP = '/usr/bin/bwrap'
CONFIG_AT = '/tmp/job/CONFIG.json'
URI = 'gs://toy-bucket/obj/items.json'
MARK = re.compile(r'#\s*never-run:\s*(\w+)\s+(.*)$')


def classify(kit):
    ranges = []
    for name in sorted(os.listdir(kit)):
        if not name.endswith('.py'):
            continue
        with open(os.path.join(kit, name)) as handle:
            for number, line in enumerate(handle, 1):
                m = MARK.search(line)
                if m:
                    ranges.append({'file': name, 'start': number, 'end': number,
                                   'class': m.group(1), 'reason': m.group(2)})
    return {'schema': dryrun.CLASSIFY_SCHEMA, 'ranges': ranges, 'caps': []}


def patch(path, old, new):
    with open(path) as handle:
        text = handle.read()
    assert text.count(old) == 1, old
    with open(path, 'w') as handle:
        handle.write(text.replace(old, new))


class Case(object):
    def __init__(self, mutate=None):
        self.dir = tempfile.mkdtemp(prefix='dryrun_')
        self.kit = os.path.join(self.dir, 'kit')
        shutil.copytree(os.path.join(FIX, 'toykit'), self.kit)
        if mutate:
            mutate(self.kit)
        store = os.path.join(self.dir, 'store')
        os.makedirs(store)
        digest, size = util.sha256_file(os.path.join(FIX, 'items.json'))
        shutil.copyfile(os.path.join(FIX, 'items.json'), os.path.join(store, digest))
        self.store = store
        self.pins = {'schema': 'orchkit-pins-v1', 'created_utc': '2026-11-16T12:00:00Z',
                     'commit': None, 'source_seal': None,
                     'entries': [{'role': 'input', 'logical_path': '/tmp/job/items.json',
                                  'bytes': size, 'sha256': digest,
                                  'source': {'kind': 'gcs', 'uri': URI, 'generation': '17'}}]}
        self.config = {
            'schema': 'orchkit-config-v1', 'kit_pins_sha256': util.canonical_sha256(self.pins),
            'job': {'partition': 'general', 'gpus': 1, 'cpus': 8, 'mem_gb': 64,
                    'time_limit_s': 3600, 'signal_s': 600, 'nice': 0},
            'entry': ['entry.py', CONFIG_AT], 'n_items': 5,
            'budgets': {'out': {'max_bytes': 1000000, 'per_item_bytes': 1000},
                        'time': {'per_item_s': 1, 'fixed_s': 60}},
            'records': [],
            'spec': {'object': URI, 'generation': '17', 'items_path': '/tmp/job/items.json',
                     'work_dir': '/tmp/job/work', 'return_dir': '/ret'}}
        self.ret = os.path.join(self.dir, 'ret')
        os.makedirs(self.ret)
        self.out = os.path.join(self.dir, 'out')

    def write(self, name, obj):
        path = os.path.join(self.dir, name)
        with open(path, 'w') as handle:
            json.dump(obj, handle, indent=1, sort_keys=True)
        return path

    def argv(self, config=None, extra=()):
        config_path = self.write('CONFIG.json', self.config)
        production = util.sha256_file(config_path)[0]
        if config is not None:
            config_path = self.write('FIXTURE_CONFIG.json', config)
        return ['run', '--kit', self.kit, '--config', config_path, '--config-at', CONFIG_AT,
                '--expect-config-sha256', production,
                '--pins', self.write('PINS.json', self.pins), '--store', self.store,
                '--map', self.ret + '=/ret:rw', '--out', self.out,
                '--classify', self.write('CLASSIFY.json', classify(self.kit)),
                '--stage', 'stage=^STAGE stage$', '--stage', 'admit=^STAGE admit$',
                '--stage', 'first_batch=^STAGE first_batch$', '--stage', 'return=^STAGE return$',
                '--item-regex', '^ITEM ', '--timeout', '120'] + list(extra) + [
                '--', KIT_PY, os.path.join(self.kit, 'entry.py'), CONFIG_AT]

    def run(self, **kwargs):
        rc = dryrun.main(self.argv(**kwargs))
        return rc, util.read_json(os.path.join(self.out, 'DRYRUN_REPORT.json'))


@unittest.skipUnless(os.path.exists(KIT_PY) and os.path.exists(BWRAP), 'needs bwrap and the kit python')
class ToyKit(unittest.TestCase):
    def expect_fail(self, case, reason, **kwargs):
        rc, rep = case.run(**kwargs)
        self.assertEqual(rep['verdict'], 'FAIL', rep)
        self.assertEqual(rep['fail_reason'], reason, rep['fail_reasons'])
        self.assertEqual(rc, 1)
        return rep

    def test_toy_kit_passes(self):
        case = Case()
        rc, rep = case.run()
        self.assertEqual((rc, rep['verdict'], rep['fail_reason']), (0, 'PASS', None),
                         json.dumps(rep['checks'], indent=1))
        self.assertEqual(rep['schema'], 'orchkit-dryrun-v1')
        self.assertEqual((rep['items_total'], rep['items_prepared']), (5, 5))
        self.assertEqual(rep['shim_calls'], 1)
        self.assertEqual([s['name'] for s in rep['stages']],
                         ['stage', 'admit', 'first_batch', 'return', 'entry'])
        self.assertTrue(all(s['rc'] == 0 for s in rep['stages']))
        self.assertEqual(rep['kit_pins_sha256'], util.canonical_sha256(case.pins))
        with open(os.path.join(case.ret, 'RETURN.json')) as handle:
            self.assertEqual(json.load(handle)['prepared'], 5)
        never = [r for r in rep['coverage']['lines_never_run']]
        self.assertEqual([(r['file'], r['class']) for r in never], [('helper.py', 'error_path')])
        with open(os.path.join(case.out, 'shim_calls.jsonl')) as handle:
            calls = [json.loads(line) for line in handle]
        self.assertEqual([c['cmd'] for c in calls], ['gsutil'])
        self.assertTrue(calls[0]['planned'])
        self.assertEqual(os.listdir(os.path.join(case.kit)), os.listdir(case.kit))

    def test_cli_exit_code(self):
        case = Case()
        proc = subprocess.Popen([sys.executable, os.path.join(PKG, 'dryrun.py')] + case.argv(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        self.assertEqual(proc.returncode, 0, err)
        self.assertTrue(out.startswith(b'PASS - '))

    def test_fixture_config_differs(self):
        case = Case()
        fixture = json.loads(json.dumps(case.config))
        fixture['spec']['generation'] = '18'
        rep = self.expect_fail(case, 'config_mismatch', config=fixture)
        self.assertEqual(rep['stages'], [])

    def test_unplanned_gsutil_cat(self):
        def mutate(kit):
            patch(os.path.join(kit, 'entry.py'), "    print('STAGE stage', flush=True)\n",
                  "    subprocess.call(['gsutil', 'cat', 'gs://toy-bucket/obj/other.json'])\n"
                  "    print('STAGE stage', flush=True)\n")
        rep = self.expect_fail(Case(mutate), 'unplanned_call')
        self.assertEqual(rep['shim_calls'], 2)

    def test_hidden_data_read(self):
        def mutate(kit):
            patch(os.path.join(kit, 'entry.py'), "    spec = config['spec']\n",
                  "    spec = config['spec']\n"
                  "    open('/data2/shared/frames/index.json').read()\n")
        rep = self.expect_fail(Case(mutate), 'hidden_path')
        self.assertIn('entry_failed', rep['fail_reasons'])
        self.assertEqual(rep['checks']['hidden_path'][0]['path'], '/data2/shared/frames/index.json')

    def test_two_stages_create_one_directory(self):
        def mutate(kit):
            patch(os.path.join(kit, 'entry.py'), "    print('STAGE admit', flush=True)\n",
                  "    subprocess.check_call([sys.executable, '-c', 'import os, sys; "
                  "os.makedirs(sys.argv[1], exist_ok=True)', spec['work_dir']])\n"
                  "    print('STAGE admit', flush=True)\n")
        rep = self.expect_fail(Case(mutate), 'dir_collision')
        self.assertEqual(rep['checks']['dir_collision'][0]['path'], '/tmp/job/work')

    def test_unclassified_never_run_line(self):
        def mutate(kit):
            patch(os.path.join(kit, 'helper.py'), "def prepare(item, work_dir):\n",
                  "def prepare(item, work_dir):\n"
                  "    if item.get('skip'):\n"
                  "        return None\n")
        rep = self.expect_fail(Case(mutate), 'unclassified_lines')
        self.assertEqual(rep['fail_reasons'], ['unclassified_lines'])

    def test_missing_staged_pin_fails_closure(self):
        case = Case()
        case.pins['entries'].append({'role': 'weights', 'logical_path': '/tmp/job/depth/0001.npy',
                                     'bytes': 4, 'sha256': 'a' * 64,
                                     'source': {'kind': 'gcs', 'uri': 'gs://toy-bucket/depth/0001.npy',
                                                'generation': '3'}})
        case.pins['entries'].sort(key=lambda e: e['logical_path'])
        case.config['kit_pins_sha256'] = util.canonical_sha256(case.pins)
        rep = self.expect_fail(case, 'closure_missing')
        self.assertEqual(rep['checks']['closure_missing'][0]['logical_path'], '/tmp/job/depth/0001.npy')

    def test_hard_link_in_archive(self):
        import tarfile
        case = Case()
        src = os.path.join(case.dir, 'payload')
        os.makedirs(src)
        with open(os.path.join(src, 'a.txt'), 'w') as handle:
            handle.write('x')
        os.link(os.path.join(src, 'a.txt'), os.path.join(src, 'b.txt'))
        archive = os.path.join(case.dir, 'payload.tar')
        with tarfile.open(archive, 'w') as tar:
            tar.add(src, arcname='payload')
        digest, size = util.sha256_file(archive)
        shutil.copyfile(archive, os.path.join(case.store, digest))
        case.pins['entries'].append({'role': 'input', 'logical_path': '/tmp/job/payload.tar',
                                     'bytes': size, 'sha256': digest,
                                     'source': {'kind': 'file', 'uri': 'payload.tar',
                                                'generation': None}})
        case.pins['entries'].sort(key=lambda e: e['logical_path'])
        case.config['kit_pins_sha256'] = util.canonical_sha256(case.pins)
        rep = self.expect_fail(case, 'tar_member_type')
        self.assertEqual(rep['checks']['tar_member_type'][0]['type'], 'hardlink')
        self.assertEqual(rep['fail_reasons'], ['tar_member_type'])

    def test_prose_in_config_fails_lint(self):
        case = Case()
        case.config['spec']['anchors'] = {'members': 'xx/<sha>.png plus ANCHORS_MANIFEST.json'}
        rep = self.expect_fail(case, 'config_lint')
        self.assertTrue(any(f['rule'] == 'prose' for f in rep['checks']['config_lint']))


class Helpers(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(dryrun.ranges([1, 2, 3, 5, 6, 9], {1, 6}), [(2, 5), (9, 9)])

    def test_classified_needs_reason_or_test(self):
        rules = [{'file': 'a.py', 'start': 1, 'end': 9, 'class': 'unit_test'},
                 {'file': 'a.py', 'start': 1, 'end': 9, 'class': 'gpu_only', 'reason': 'cuda'}]
        self.assertEqual(dryrun.classified(rules, 'a.py', 2, 3)['class'], 'gpu_only')
        self.assertIsNone(dryrun.classified(rules[:1], 'a.py', 2, 3))
        self.assertIsNone(dryrun.classified(rules, 'a.py', 8, 10))

    def test_pins_must_be_sorted_and_unique(self):
        entry = {'role': 'input', 'logical_path': '/b', 'sha256': 'a' * 64}
        manifest = {'schema': 'orchkit-pins-v1', 'entries': [entry, dict(entry, logical_path='/a')]}
        self.assertIn('entries are not sorted by logical_path', dryrun.check_pins(manifest))
        manifest['entries'] = [entry, entry]
        self.assertIn('a logical_path repeats', dryrun.check_pins(manifest))


if __name__ == '__main__':
    unittest.main()
