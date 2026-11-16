import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from student_pilot import common


class StartupCacheTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='startup_cache_', dir=os.environ['LANE_TEST_OUTPUT']))
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.repo = patch.object(common, 'REPO', self.root)
        self.repo.start()
        self.addCleanup(self.repo.stop)

    def enable(self):
        os.environ['STUDENT_KERNEL_CACHE_ROOT'] = str(self.root / 'shared')
        os.environ['STUDENT_KERNEL_CACHE_TAG'] = 'a100-cu129-fk-receipt'

    def test_default_keeps_the_existing_run_local_cache_paths(self):
        runtime = self.root / 'runtime'
        common.configure_environment(runtime)
        self.assertEqual(os.environ['TRITON_CACHE_DIR'], str(runtime / '.cache/triton'))
        self.assertNotIn('TILELANG_CACHE_DIR', os.environ)

    def test_persistent_paths_survive_reconfiguration_for_another_rank(self):
        self.enable()
        first = common.configure_kernel_cache(self.root / 'rank0')
        common.configure_environment(self.root / 'rank1')
        for name in ('TRITON_CACHE_DIR', 'TILELANG_CACHE_DIR', 'CUDA_CACHE_PATH', 'TORCHINDUCTOR_CACHE_DIR'):
            self.assertEqual(os.environ[name], first[name])
            path = Path(first[name])
            self.assertTrue(path.is_relative_to(self.root / 'shared'))
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        self.assertEqual(os.environ['TMPDIR'], str(self.root / 'rank1/.tmp'))
        self.assertTrue(Path(os.environ['TILELANG_TMP_DIR']).is_relative_to(self.root / 'rank1'))

    def test_versions_and_explicit_tag_partition_cache_entries(self):
        self.enable()
        with patch.object(common, 'kernel_cache_identity', return_value={'torch': 'a'}):
            first = common.configure_kernel_cache(self.root / 'r0')
        with patch.object(common, 'kernel_cache_identity', return_value={'torch': 'b'}):
            second = common.configure_kernel_cache(self.root / 'r1')
        self.assertNotEqual(first['TRITON_CACHE_DIR'], second['TRITON_CACHE_DIR'])
        os.environ['STUDENT_KERNEL_CACHE_TAG'] = 'new-compiler-pin'
        with patch.object(common, 'kernel_cache_identity', return_value={'torch': 'b'}):
            third = common.configure_kernel_cache(self.root / 'r2')
        self.assertNotEqual(second['TRITON_CACHE_DIR'], third['TRITON_CACHE_DIR'])

    def test_rejects_unowned_relative_and_traversal_roots(self):
        self.enable()
        for root in ('relative', '/etc/cache', str(self.root / 'sub/../shared')):
            with self.subTest(root=root), patch.dict(os.environ, STUDENT_KERNEL_CACHE_ROOT=root):
                with self.assertRaises(ValueError):
                    common.configure_kernel_cache(self.root / 'runtime')

    def test_requires_a_safe_explicit_environment_tag(self):
        self.enable()
        for tag in ('', '../escape', 'bad/name', 'x' * 129):
            with self.subTest(tag=tag), patch.dict(os.environ, STUDENT_KERNEL_CACHE_TAG=tag):
                with self.assertRaises(ValueError):
                    common.configure_kernel_cache(self.root / 'runtime')

    def test_refuses_group_writable_cache_root(self):
        self.enable()
        cache = self.root / 'shared'
        cache.mkdir(mode=0o777)
        cache.chmod(0o777)
        with self.assertRaises(ValueError):
            common.configure_kernel_cache(self.root / 'runtime')

    def test_cli_configures_caches_before_importing_diagnostic_dependencies(self):
        from student_pilot import cli
        from types import SimpleNamespace
        calls = []

        def imported(name):
            calls.append('import')
            return SimpleNamespace(main=lambda argv: argv)

        with patch.object(cli, 'configure_kernel_cache', side_effect=lambda root: calls.append('cache')), \
                patch('importlib.import_module', side_effect=imported), \
                patch.object(cli.sys, 'argv', ['cli', 'diagnostic', '--help']):
            self.assertEqual(cli.main(), ['--help'])
        self.assertEqual(calls, ['cache', 'import'])

    def test_phase_events_use_utc_and_monotonic_time_without_importing_cuda(self):
        output = io.StringIO()
        with redirect_stdout(output), patch.dict(os.environ, RANK='3'):
            common.startup_event('weights_begin')
        record = json.loads(output.getvalue())
        self.assertEqual(record['event'], 'startup_phase')
        self.assertEqual(record['phase'], 'weights_begin')
        self.assertEqual(record['rank'], '3')
        self.assertTrue(record['utc'].endswith('+00:00'))
        self.assertGreater(record['monotonic_seconds'], 0)


if __name__ == '__main__':
    unittest.main()
