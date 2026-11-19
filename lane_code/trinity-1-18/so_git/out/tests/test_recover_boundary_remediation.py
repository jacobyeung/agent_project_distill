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
        root = os.environ.get('REMEDIATION_TEST_ROOT')
        if root:
            root = Path(root).resolve()
            if not str(root).startswith(('/scratch/', '/tmp/')):
                raise ValueError('REMEDIATION_TEST_ROOT must be under /scratch or /tmp')
            root.mkdir(parents=True, exist_ok=True)
        # System temporary storage avoids dirtying either a /home or /scratch checkout.
        # Retain fixtures: the cluster's no-deletion rule forbids cleanup commands.
        self.root = Path(tempfile.mkdtemp(prefix='r1315_pkg_', dir=root))
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

    def check_process_matcher(self, script):
        module = self.load(str(self.package))
        proc = dict(pid=99999, uid=module['UID'], start_ticks='1', state='S',
                    args=['python3', str(script), 'worker', '--config', str(self.root / 'config.json')])
        (self.root / 'config.json').write_text('{"run_root": ' + __import__('json').dumps(str(module['ROOT'])) + '}')
        # run_path returns a copy; patch the function's own globals.
        globals_ = module['processes'].__globals__
        with patch.object(Path, 'iterdir', return_value=[Path('/proc/99999')]), patch.dict(globals_, identity=lambda _: proc):
            self.assertEqual(module['processes'](), [proc])

    def test_override_reaches_process_matcher(self):
        self.check_process_matcher(self.package / 'collect.py')

    def test_override_keeps_default_collectors_visible(self):
        self.check_process_matcher(Path('/home/jjyeung/agent_project_distill/collector/collect.py'))

    def test_default_temp_root_ignores_checkout(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, 'cwd', side_effect=AssertionError('must not use checkout')):
            fixture = PackagePathTests()
            fixture.setUp()
        self.assertEqual(fixture.root.parent, Path(tempfile.gettempdir()))


if __name__ == '__main__':
    unittest.main()
