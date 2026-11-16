"""Tests for orchkit.pins: build, verify, the single-place invariant and the old-kit audit."""
import io
import json
import os
import sys
import tarfile
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import pins, util  # noqa: E402

REF = '/scratch/jjyeung/distill_sync/stage'
NATIVE_CODE = REF + '/trinity-3-30/recover_k1/work/code4d/sj/orch_cd/evalx/work/milestone/orchard_native'
VSTI_KIT = REF + '/trinity-1-3/native_r4/builds/01_vsti/out'


def write(path, data):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))


def tar_bytes(files):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w') as archive:
        for name, data in sorted(files.items()):
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
    return raw.getvalue()


class PinsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='orchkit_pins_')
        write(os.path.join(self.root, 'lib/a.py'), 'print(1)\n')
        write(os.path.join(self.root, 'lib/b.py'), 'print(2)\n')
        write(os.path.join(self.root, 'inputs/x.bin'), b'\x00\x01' * 100)
        self.spec = {'commit': None, 'source_seal': None, 'entries': [
            {'role': 'code', 'logical_path': 'lib/b.py'},
            {'role': 'code', 'logical_path': 'lib/a.py'},
            {'role': 'input', 'logical_path': 'inputs/x.bin',
             'source': {'kind': 'gcs', 'uri': 'gs://bucket/obj', 'generation': '17'}}]}

    def manifest(self):
        return pins.build(self.root, self.spec)

    def test_build_sorts_and_verify_round_trip(self):
        manifest = self.manifest()
        self.assertEqual([e['logical_path'] for e in manifest['entries']],
                         ['inputs/x.bin', 'lib/a.py', 'lib/b.py'])
        self.assertEqual(pins.verify(manifest, self.root), [])
        out = os.path.join(self.root, 'PINS.json')
        self.assertEqual(pins.main(['build', '--root', self.root, '--spec', self._spec_file(),
                                    '--out', out]), 0)
        self.assertEqual(pins.main(['verify', '--manifest', out, '--root', self.root]), 0)
        self.assertEqual(pins.kit_identity(util.read_json(out)),
                         util.canonical_sha256(util.read_json(out)))

    def _spec_file(self):
        path = os.path.join(tempfile.mkdtemp(prefix='orchkit_spec_'), 'SPEC.json')
        util.write_json(path, self.spec)
        return path

    def test_one_changed_byte_names_its_entry(self):
        manifest = self.manifest()
        write(os.path.join(self.root, 'lib/a.py'), 'print(3)\n')
        report = pins.differences(pins.verify(manifest, self.root))
        self.assertEqual([row['logical_path'] for row in report], ['lib/a.py'])
        self.assertEqual(report[0]['problem'], 'differs')

    def test_remote_entry_without_local_copy_is_not_a_difference(self):
        manifest = self.manifest()
        os.rename(os.path.join(self.root, 'inputs/x.bin'), os.path.join(self.root, 'inputs/x.moved'))
        report = pins.verify(manifest, self.root)
        self.assertEqual(report, [{'logical_path': 'inputs/x.bin', 'problem': 'remote-not-present'}])
        self.assertEqual(pins.differences(report), [])

    def test_repeated_logical_path_is_refused(self):
        self.spec['entries'].append({'role': 'code', 'logical_path': 'lib/a.py', 'file': 'lib/b.py'})
        with self.assertRaises(pins.PinError):
            self.manifest()
        manifest = pins.build(self.root, {'entries': [{'role': 'code', 'logical_path': 'lib/a.py'}]})
        manifest['entries'].append(dict(manifest['entries'][0]))
        with self.assertRaises(pins.PinError):
            pins.validate_manifest(manifest)

    def test_unnormalized_path_and_missing_generation_refused(self):
        with self.assertRaises(pins.PinError):
            pins.build(self.root, {'entries': [{'role': 'code', 'logical_path': 'lib/../lib/a.py'}]})
        self.spec['entries'][2]['source']['generation'] = None
        with self.assertRaises(pins.PinError):
            self.manifest()

    def kit(self):
        manifest = self.manifest()
        util.write_json(os.path.join(self.root, 'PINS.json'), manifest)
        return manifest

    def test_single_place_invariant_passes_clean_kit_with_identity_and_records(self):
        manifest = self.kit()
        entry = [e for e in manifest['entries'] if e['logical_path'] == 'lib/a.py'][0]
        config = {'schema': 'orchkit-config-v1', 'kit_pins_sha256': pins.kit_identity(manifest),
                  'records': [{'logical_path': 'lib/a.py', 'sha256': entry['sha256']}]}
        util.write_json(os.path.join(self.root, 'CONFIG.json'), config)
        config_sha = util.sha256_file(os.path.join(self.root, 'CONFIG.json'))[0]
        util.write_json(os.path.join(self.root, 'DRYRUN_REPORT.json'),
                        {'kit_pins_sha256': pins.kit_identity(manifest), 'config_sha256': config_sha})
        self.assertEqual(pins.check_single_place(self.root), [])

    def test_single_place_invariant_fails_copied_hash(self):
        manifest = self.kit()
        sha = manifest['entries'][1]['sha256']
        write(os.path.join(self.root, 'lib/c.py'), 'EXPECTED = %r\n' % sha)
        found = pins.check_single_place(self.root)
        self.assertEqual([(row['where'], row['value']) for row in found], [('lib/c.py', sha)])
        self.assertIn('copy of a pinned hash', found[0]['reason'])

    def test_single_place_invariant_fails_stale_hash_and_stale_record(self):
        self.kit()
        stale = 'ab' * 32
        write(os.path.join(self.root, 'lib/d.json'), json.dumps({'worker': {'sha256': stale}}))
        util.write_json(os.path.join(self.root, 'CONFIG.json'),
                        {'records': [{'logical_path': 'lib/a.py', 'sha256': 'cd' * 32}]})
        found = sorted((row['where'], row['field']) for row in pins.check_single_place(self.root))
        self.assertEqual(found, [('CONFIG.json', 'records.0.sha256'), ('lib/d.json', 'worker.sha256')])

    def test_single_place_invariant_record_must_match_its_own_entry(self):
        manifest = self.kit()
        other = [e for e in manifest['entries'] if e['logical_path'] == 'lib/b.py'][0]['sha256']
        util.write_json(os.path.join(self.root, 'CONFIG.json'),
                        {'records': [{'logical_path': 'lib/a.py', 'sha256': other}]})
        self.assertEqual(len(pins.check_single_place(self.root)), 1)

    def test_single_place_invariant_scans_nested_tar_members(self):
        manifest = self.kit()
        sha = manifest['entries'][0]['sha256']
        inner = tar_bytes({'deep/pin.txt': sha.encode()})
        write(os.path.join(self.root, 'lib/outer.tar'), tar_bytes({'inner.tar': inner}))
        found = pins.check_single_place(self.root)
        self.assertEqual([row['where'] for row in found], ['lib/outer.tar!/inner.tar!/deep/pin.txt'])

    def test_check_cli_exit_codes(self):
        self.kit()
        self.assertEqual(pins.main(['check', '--kit', self.root]), 0)
        write(os.path.join(self.root, 'x.txt'), 'ef' * 32)
        self.assertEqual(pins.main(['check', '--kit', self.root]), 1)

    def test_audit_groups_disagreeing_copies(self):
        old = tempfile.mkdtemp(prefix='orchkit_old_')
        good, stale = '11' * 32, '22' * 32
        write(os.path.join(old, 'FAMILY.json'), json.dumps(
            {'assets': {'worker_entrypoint': {'path': '/x/native_worker.py', 'sha256': stale}}}))
        write(os.path.join(old, 'CONFIG.json'), json.dumps({'code_pins': {'/x/native_worker.py': good}}))
        write(os.path.join(old, 'seal.py'), "PIN = '%s'  # native_worker.py\n" % good)
        report = pins.audit(old)
        rows = [row for row in report['rows'] if row['subject'] == 'native_worker.py']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['places'], 3)
        self.assertFalse(rows[0]['agree'])
        self.assertEqual(report['disagreeing'], 1)

    @unittest.skipUnless(os.path.isdir(NATIVE_CODE) and os.path.isdir(VSTI_KIT), 'reference kits absent')
    def test_audit_reference_kits(self):
        code = pins.audit(NATIVE_CODE)
        full = pins.audit(VSTI_KIT)
        self.assertGreaterEqual(code['groups'], 0)
        self.assertGreater(full['groups'], code['groups'])
        self.assertGreaterEqual(full['disagreeing'], 1)


if __name__ == '__main__':
    unittest.main()
