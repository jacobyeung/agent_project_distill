"""Production isolation, unchanged plans and bounded diagnostic recovery."""
import offline_guard
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'kit/launcher'))
import orchard_launcher as L
import chain_save as A
import isolated_fixture as isolated


def folder():
    root = ROOT/'evidence'/('test_fix5_'+uuid.uuid4().hex)
    root.mkdir()
    return root


class IsolationTests(unittest.TestCase):
    def test_runtime_rejects_fix4_import_order_before_mocks(self):
        root = folder(); payload = isolated.package(root)
        worker = payload/'reader/worker.py'
        text = worker.read_text().replace('import read_filter as F\n', '')
        worker.write_text(text.replace('HERE = ', 'import read_filter as F\n\nHERE = ', 1))
        result = isolated.launch(root, payload/'vllm_isolated.sh', 'runtime', worker, '1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ModuleNotFoundError: No module named 'read_filter'", result.stderr)
        self.assertFalse((root/'runtime').exists())

    def test_every_packaged_entry_imports_in_fresh_isolated_process(self):
        root = folder(); payload = isolated.package(root)
        entries = sorted((root/'bootstrap').glob('*.py')) + sorted(payload.glob('*/*.py'))
        self.assertTrue(any(p.name == 'worker.py' for p in entries))
        for path in entries:
            with self.subTest(entry=str(path.relative_to(root))):
                result = isolated.launch(root, payload/'vllm_isolated.sh', 'import', path)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        for path in (payload/'reader/worker.py', payload/'reader/chain.py',
                     root/'bootstrap/orchard_job.py', root/'bootstrap/trace_runtime.py',
                     root/'bootstrap/orchard_launcher.py',
                     root/'bootstrap/chain_save.py', root/'bootstrap/return_io.py'):
            with self.subTest(help=str(path.relative_to(root))):
                result = isolated.launch(root, payload/'vllm_isolated.sh', 'help', path)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertIn('usage:', result.stdout)
        print('FIX5_ISOLATED_ENTRIES '+json.dumps([str(p.relative_to(root)) for p in entries]), flush=True)

    def test_filtered_and_unfiltered_plan_bytes_match_fix4(self):
        base = Path(str(ROOT)+'/evidence/test_fix3_fix4_5281c79473cf4f04b58e160c9d2dd9f8')
        fixtures = ((None, 'test_fix4_c97e13bd02094367b13e2e986559d4a8'),
                    ('direct', 'test_fix4_04971b3698014a218c7a77cc28f60cac'))
        integrity = {'payload_pins', 'payload_sha256', 'launcher_pins', 'launcher_review', 'launcher_review_pin'}
        for selection, fixture in fixtures:
            old = json.loads((base/fixture/'prepared/CONFIG.json').read_text())
            new = L.prepare('a000000001', folder()/'prepared', 544, run='469ddece',
                            generation='mstop', families=['a7'], types=selection)
            before = json.dumps(old['spec'], sort_keys=True).encode()
            after = json.dumps(new['spec'], sort_keys=True).encode()
            self.assertEqual(before, after)
            self.assertEqual(old['plan_sha256'], new['plan_sha256'])
            self.assertEqual({k:v for k,v in old.items() if k not in integrity},
                             {k:v for k,v in new.items() if k not in integrity})
            changed = {k for k in new if old.get(k) != new[k]}
            self.assertEqual(changed, integrity)
            print('FIX5_PLAN '+json.dumps(dict(types=selection, plan_sha256=new['plan_sha256'],
                bytes=len(after), serialized_sha256=hashlib.sha256(after).hexdigest(),
                baseline=str((base/fixture/'prepared/CONFIG.json').relative_to(ROOT)),
                changed_config_fields=sorted(changed))), flush=True)


class LogTests(unittest.TestCase):
    def fixture(self):
        root = folder(); source = root/'source'; (source/'logs').mkdir(parents=True)
        config = dict(plan_sha256='a'*64, spec=dict(step=544), families=['main','a7'])
        (source/'FAILED.json').write_text('{"error":"worker import"}\n')
        path = source/'a7/a0/results/0/g0.jsonl'; path.parent.mkdir(parents=True)
        path.write_text('{"id":"one","status":"complete","question_type":"object_counting"}\n')
        return root, source, config, path

    def test_log_tails_whole_lines_hex_and_manifest(self):
        root, source, config, journal = self.fixture()
        lines = [('diagnostic %06d café\n'%i).encode() for i in range(18000)]
        samples = {'launcher_chain.log': b''.join(lines)+b'Traceback: ModuleNotFoundError\n',
                   'launcher_staging.log': b'staged\n',
                   'main.hex': (b'1234\n'*60000)+b'abcdef\n',
                   'a7.hex': b'012345\npartial'}
        for name, data in samples.items(): (source/'logs'/name).write_bytes(data)
        target = root/'partial.tar.gz'
        report = A.pack_partial(source, target, config, 19_900_000-1)
        self.assertLess(target.stat().st_size, 19_900_000)
        self.assertEqual(report['families']['a7']['finished_items'], 1)
        with tarfile.open(target) as archive:
            saved = json.load(archive.extractfile('PARTIAL.json'))
            self.assertEqual(saved['logs'], report['logs'])
            self.assertEqual(archive.extractfile(str(journal.relative_to(source))).read(), journal.read_bytes())
            for name, original in samples.items():
                name = 'logs/'+name
                data = archive.extractfile(name).read(); detail = saved['logs'][name]
                self.assertLessEqual(len(data), A.LOG_TAIL_LIMIT)
                self.assertEqual(data, original[detail['offset']:detail['offset']+len(data)])
                self.assertEqual(data, b''.join(original.splitlines(keepends=True)[-len(data.splitlines()):]) if original.endswith(b'\n') else b'012345\n')
                self.assertTrue(data.endswith(b'\n'))
                self.assertEqual(detail['retained_bytes'], len(data))
                self.assertEqual(detail['retained_lines'], len(data.splitlines()))
                self.assertEqual(detail['truncated'], data != original)
            self.assertTrue(archive.extractfile('logs/launcher_chain.log').read().endswith(b'ModuleNotFoundError\n'))

    def test_logs_yield_to_identity_and_journals_under_cap(self):
        root, source, config, journal = self.fixture()
        (source/'logs/launcher_chain.log').write_bytes(b'x'*300000+b'\n')
        # Exactly enough raw budget for identity and journal, with no log header.
        limit = 262144+4096+(source/'FAILED.json').stat().st_size+journal.stat().st_size
        target = root/'small.tar.gz'; report = A.pack_partial(source, target, config, limit)
        self.assertLess(target.stat().st_size, limit)
        self.assertTrue(report['truncated'])
        self.assertEqual(report['logs']['logs/launcher_chain.log']['retained_bytes'], 0)
        self.assertIn('logs/launcher_chain.log', report['omitted'])
        with tarfile.open(target) as archive:
            self.assertIn('FAILED.json', archive.getnames())
            self.assertEqual(archive.extractfile(str(journal.relative_to(source))).read(), journal.read_bytes())
            self.assertNotIn('logs/launcher_chain.log', archive.getnames())

    def test_oversized_line_and_symlink_refuse_without_unbounded_read(self):
        root, source, config, _ = self.fixture()
        (source/'logs/launcher_chain.log').write_bytes(b'x'*(A.LOG_TAIL_LIMIT+10)+b'\n')
        report = A.pack_partial(source, root/'long.tar.gz', config, 89900000-1)
        self.assertIn('logs/launcher_chain.log', report['omitted'])
        (source/'logs/a7.hex').symlink_to(source/'FAILED.json')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            A.pack_partial(source, root/'link.tar.gz', config, 89900000-1)


if __name__ == '__main__':
    unittest.main()
