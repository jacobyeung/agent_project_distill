import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'tests':
    ROOT = ROOT.parent
SOURCE = ROOT / 'tools' / 'recover_boundary_remediation.py'


class PackagePathTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ.get('REMEDIATION_TEST_ROOT', str(Path.cwd() / 'work' / 'pkg_tests')))
        root.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='pkg_', dir=root))
        self.package = self.root / 'epoch' / 'collector'
        self.package.mkdir(parents=True)
        (self.package / 'collect.py').write_text('# inert fixture\n')

    def load(self, override=None, unset=False):
        env = dict(os.environ, R1315_RUNTIME=str(self.root / 'runtime'))
        env.pop('R1315_PKG', None)
        if not unset:
            env['R1315_PKG'] = override
        with patch.dict(os.environ, env, clear=True):
            return runpy.run_path(str(SOURCE))

    def test_unset_preserves_current_default(self):
        result = self.load(unset=True)
        self.assertEqual(result['PKG'], Path('/home/jjyeung/agent_project_distill/collector'))

    def test_absolute_epoch_package(self):
        result = self.load(str(self.package))
        self.assertEqual(result['PKG'], self.package)

    def test_relative_path_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'absolute existing directory'):
            self.load('collector')

    def test_empty_path_is_refused(self):
        with self.assertRaises(ValueError):
            self.load('')

    def test_missing_directory_is_refused(self):
        with self.assertRaises(ValueError):
            self.load(str(self.root / 'absent'))

    def test_directory_without_collect_is_refused(self):
        with self.assertRaises(ValueError):
            self.load(str(self.root))

    def test_collect_must_be_a_file(self):
        path = self.root / 'not_package'
        path.mkdir()
        (path / 'collect.py').mkdir()
        with self.assertRaises(ValueError):
            self.load(str(path))

    def test_override_reaches_process_matcher(self):
        module = self.load(str(self.package))
        proc = dict(pid=99999, uid=module['UID'], start_ticks='1', state='S',
                    args=['python3', str(self.package / 'collect.py'), 'worker', '--config', str(self.root / 'config.json')])
        (self.root / 'config.json').write_text('{"run_root": ' + __import__('json').dumps(str(module['ROOT'])) + '}')
        # run_path returns a copy; patch the function's own globals.
        globals_ = module['processes'].__globals__
        with patch.object(Path, 'iterdir', return_value=[Path('/proc/99999')]), patch.dict(globals_, identity=lambda _: proc):
            self.assertEqual(module['processes'](), [proc])


if __name__ == '__main__':
    unittest.main()
