"""Tests for the job-side stager: policies, the rehearsal, the safe extractor and the sha checks."""
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, TOOLS)
from orchkit import pins, stage, util  # noqa: E402


def write(path, data):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode('utf-8'))


def tar_bytes(files, links=(), extra=()):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w') as archive:
        for name, data in files:
            item = tarfile.TarInfo(name)
            item.size = len(data)
            archive.addfile(item, io.BytesIO(data))
        for name, target, kind in links:
            item = tarfile.TarInfo(name)
            item.type = tarfile.SYMTYPE if kind == 'sym' else tarfile.LNKTYPE
            item.linkname = target
            archive.addfile(item)
        for item in extra:
            archive.addfile(item)
    return raw.getvalue()


class StageTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix='orchkit_stage_')
        self.kit = os.path.join(self.base, 'kit')
        self.root = os.path.join(self.base, 'root')
        os.makedirs(self.kit)
        self.spec = []

    def add(self, logical, data, **extra):
        write(os.path.join(self.kit, logical), data)
        row = {'role': 'input', 'logical_path': logical}
        row.update(extra)
        self.spec.append(row)

    def seal(self, items):
        manifest = pins.build(self.kit, {'entries': self.spec})
        util.write_json(os.path.join(self.kit, 'PINS.json'), manifest)
        config = {'stage': items}
        util.write_json(os.path.join(self.kit, 'CONFIG.json'), config)
        return config, manifest

    def test_file_and_tar_round_trip_with_parts(self):
        whole = tar_bytes([('a/x.txt', b'x' * 3000), ('b.txt', b'b')])
        cut = len(whole) // 2
        self.add('in/w.tar.p0', whole[:cut])
        self.add('in/w.tar.p1', whole[cut:])
        self.add('in/one.bin', b'\x01\x02')
        self.seal([{'parts': ['in/w.tar.p0', 'in/w.tar.p1'], 'unpack': 'tar', 'dest': 'w',
                    'policy': 'new'},
                   {'logical_path': 'in/one.bin', 'unpack': 'file', 'dest': 'bin/one.bin',
                    'policy': 'new'}])
        report = stage.rehearse(self.kit, self.root)
        self.assertTrue(report['ok'], report)
        receipt = stage.run(self.kit, self.root)
        self.assertTrue(receipt['ok'])
        with open(os.path.join(self.root, 'w/a/x.txt'), 'rb') as handle:
            self.assertEqual(handle.read(), b'x' * 3000)
        with open(os.path.join(self.root, 'bin/one.bin'), 'rb') as handle:
            self.assertEqual(handle.read(), b'\x01\x02')
        self.assertNotIn(util.sha256_bytes(b'\x01\x02'), json.dumps(receipt))

    def test_two_new_items_on_one_directory_fail_and_name_both(self):
        self.add('in/a.tar', tar_bytes([('x.txt', b'1')]))
        self.add('in/b.tar', tar_bytes([('y.txt', b'2')]))
        self.seal([{'logical_path': 'in/a.tar', 'unpack': 'tar', 'dest': 'env', 'policy': 'new'},
                   {'logical_path': 'in/b.tar', 'unpack': 'tar', 'dest': 'env', 'policy': 'new'}])
        report = stage.rehearse(self.kit, self.root)
        self.assertFalse(report['ok'])
        named = set(name for row in report['collisions'] for name in row['items'])
        self.assertEqual(named, {'in/a.tar', 'in/b.tar'})
        with self.assertRaises(stage.StageError):
            stage.run(self.kit, self.root)
        self.assertFalse(os.path.exists(os.path.join(self.root, 'env')))

    def test_new_refuses_an_existing_destination(self):
        self.add('in/a.tar', tar_bytes([('x.txt', b'1')]))
        self.seal([{'logical_path': 'in/a.tar', 'unpack': 'tar', 'dest': 'env', 'policy': 'new'}])
        os.makedirs(os.path.join(self.root, 'env'))
        self.assertFalse(stage.rehearse(self.kit, self.root)['ok'])
        with self.assertRaises(stage.StageError):
            stage.run(self.kit, self.root)

    def test_disjoint_allows_existing_directory_but_not_a_colliding_member(self):
        self.add('in/a.tar', tar_bytes([('x.txt', b'1')]))
        self.add('in/b.tar', tar_bytes([('y.txt', b'2')]))
        self.add('in/c.tar', tar_bytes([('y.txt', b'3')]))
        os.makedirs(os.path.join(self.root, 'env'))
        write(os.path.join(self.root, 'env/old.txt'), 'old')
        items = [{'logical_path': 'in/a.tar', 'unpack': 'tar', 'dest': 'env', 'policy': 'disjoint'},
                 {'logical_path': 'in/b.tar', 'unpack': 'tar', 'dest': 'env', 'policy': 'disjoint'}]
        self.seal(items)
        self.assertTrue(stage.rehearse(self.kit, self.root)['ok'])
        stage.run(self.kit, self.root)
        self.assertTrue(os.path.isfile(os.path.join(self.root, 'env/y.txt')))
        self.seal(items + [{'logical_path': 'in/c.tar', 'unpack': 'tar', 'dest': 'env',
                            'policy': 'disjoint'}])
        fresh = os.path.join(self.base, 'root2')
        report = stage.rehearse(self.kit, fresh)
        self.assertEqual([row['path'] for row in report['collisions']], ['env/y.txt'])
        self.assertEqual(report['collisions'][0]['items'], ['in/b.tar', 'in/c.tar'])

    def test_same_allows_identical_bytes_only(self):
        self.add('in/a.tar', tar_bytes([('lib/x.py', b'same')]))
        self.add('in/b.tar', tar_bytes([('lib/x.py', b'same'), ('lib/z.py', b'z')]))
        self.add('in/c.tar', tar_bytes([('lib/x.py', b'different')]))
        good = [{'logical_path': 'in/a.tar', 'unpack': 'tar', 'dest': 'e', 'policy': 'same'},
                {'logical_path': 'in/b.tar', 'unpack': 'tar', 'dest': 'e', 'policy': 'same'}]
        self.seal(good)
        self.assertTrue(stage.rehearse(self.kit, self.root)['ok'])
        stage.run(self.kit, self.root)
        self.seal([{'logical_path': 'in/c.tar', 'unpack': 'tar', 'dest': 'e', 'policy': 'same'}])
        self.assertFalse(stage.rehearse(self.kit, self.root)['ok'])
        with self.assertRaises(stage.StageError):
            stage.run(self.kit, self.root)

    def test_unsafe_members_are_refused(self):
        device = tarfile.TarInfo('dev')
        device.type = tarfile.CHRTYPE
        cases = {
            'absolute': tar_bytes([('/etc/x', b'1')]),
            'climb': tar_bytes([('a/../../x', b'1')]),
            'duplicate': tar_bytes([('x', b'1'), ('./x', b'2')]),
            'link-out': tar_bytes([('a', b'1')], links=[('l', '../../etc/passwd', 'sym')]),
            'link-abs': tar_bytes([('a', b'1')], links=[('l', '/etc/passwd', 'sym')]),
            'hard-out': tar_bytes([('a', b'1')], links=[('h', '../outside', 'hard')]),
            'device': tar_bytes([('a', b'1')], extra=[device]),
        }
        for name, data in sorted(cases.items()):
            self.add('in/%s.tar' % name, data)
        for index, name in enumerate(sorted(cases)):
            self.seal([{'logical_path': 'in/%s.tar' % name, 'unpack': 'tar',
                        'dest': 'd%d' % index, 'policy': 'new'}])
            report = stage.rehearse(self.kit, self.root)
            self.assertFalse(report['ok'], name)
            with self.assertRaises(stage.StageError, msg=name):
                stage.run(self.kit, self.root)
        self.assertFalse(os.path.exists(os.path.join(self.base, 'outside')))

    def test_safe_extractor_refuses_before_writing_anything(self):
        data = tar_bytes([('ok.txt', b'1'), ('/abs', b'2')])
        dest = os.path.join(self.base, 'x')
        with self.assertRaises(stage.StageError):
            stage.safe_extract(lambda: io.BytesIO(data), dest, 'new')
        self.assertFalse(os.path.exists(dest))

    def test_sha_mismatch_names_the_entry(self):
        self.add('in/a.bin', b'good bytes')
        self.seal([{'logical_path': 'in/a.bin', 'unpack': 'file', 'dest': 'a.bin', 'policy': 'new'}])
        write(os.path.join(self.kit, 'in/a.bin'), b'evil bytes')
        with self.assertRaises(stage.StageError) as caught:
            stage.run(self.kit, self.root)
        self.assertIn('in/a.bin', str(caught.exception))
        self.assertFalse(os.path.exists(os.path.join(self.root, 'a.bin')))

    def test_gcs_entry_fetched_by_generation_and_checked(self):
        payload = tar_bytes([('w.bin', b'w' * 100)])
        self.add('in/w.tar', payload, source={'kind': 'gcs', 'uri': 'gs://b/o', 'generation': '42'},
                 standin='standin/w.tar')
        write(os.path.join(self.kit, 'standin/w.tar'), tar_bytes([('w.bin', b'')]))
        config, manifest = self.seal([{'logical_path': 'in/w.tar', 'unpack': 'tar', 'dest': 'w',
                                       'policy': 'new'}])
        os.rename(os.path.join(self.kit, 'in/w.tar'), os.path.join(self.base, 'remote.tar'))
        calls = []

        def fetch(uri, generation, target, env=None):
            calls.append((uri, generation))
            with open(os.path.join(self.base, 'remote.tar'), 'rb') as src, open(target, 'xb') as out:
                out.write(src.read())

        report = stage.rehearse(self.kit, self.root)
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['unknown'], [])
        self.assertEqual(calls, [])
        stage.run(self.kit, self.root, gcs_fetch=fetch)
        self.assertEqual(calls, [('gs://b/o', '42')])
        self.assertEqual(os.path.getsize(os.path.join(self.root, 'w/w.bin')), 100)

    def test_rehearsal_without_bytes_uses_member_list_or_reports_unknown(self):
        self.add('in/w.tar', tar_bytes([('a', b'1')]),
                 source={'kind': 'orchard', 'uri': '/nonexistent/pool/w.tar', 'generation': None})
        self.add('in/v.tar', tar_bytes([('b', b'1')]),
                 source={'kind': 'orchard', 'uri': '/nonexistent/pool/v.tar', 'generation': None})
        self.seal([{'logical_path': 'in/w.tar', 'unpack': 'tar', 'dest': 'e', 'policy': 'disjoint',
                    'members': ['bin/python']},
                   {'logical_path': 'in/v.tar', 'unpack': 'tar', 'dest': 'e', 'policy': 'disjoint'}])
        report = stage.rehearse(self.kit, self.root)
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['unknown'], ['in/v.tar'])
        with self.assertRaises(stage.StageError):
            stage.run(self.kit, self.root)

    def test_cli_runs_as_a_module_of_any_package_name(self):
        lib = os.path.join(self.base, 'pk', 'lib')
        os.makedirs(lib)
        for name in ('util.py', 'stage.py'):
            with open(os.path.join(TOOLS, 'orchkit', name), 'rb') as src:
                write(os.path.join(lib, name), src.read())
        write(os.path.join(lib, '__init__.py'), '')
        self.add('in/a.bin', b'1')
        self.seal([{'logical_path': 'in/a.bin', 'unpack': 'file', 'dest': 'a', 'policy': 'new'}])
        code = subprocess.call([sys.executable, '-E', '-s', '-B', '-m', 'lib.stage', 'rehearse',
                                '--kit', self.kit], cwd=os.path.dirname(lib),
                               stdout=subprocess.DEVNULL)
        self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main()
