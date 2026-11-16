"""CLI regression tests with a stub manifest and an F.run recorder."""
import contextlib
import inspect
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'kit_k1a'
assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
sys.path[:0] = [str(KIT / 'native_kit'), str(KIT / 'work')]
import k1_cli as C
import run


class MaxBytesTests(unittest.TestCase):
    def invoke(self, extra=(), phase='tower_sam', stage='cache', entry=None):
        manifest = {'synthetic': True, 'captures': [{'canonical': 'stub/room'}]}
        calls = []

        def recorder(*args, **kwargs):
            calls.append((args, kwargs))
            return 4

        argv = ['k1_pipeline.py', stage, '--manifest', 'stub.json',
                '--out', str(ROOT / 'tmp/cli-output'), '--phase', phase,
                '--cpu-fixture', *extra]
        with patch.object(sys, 'argv', argv), \
             patch.object(C.B, 'load', return_value=manifest) as load, \
             patch.object(run, 'validate_manifest') as validate, \
             patch.object(C.F, 'run', side_effect=recorder), \
             patch.object(C.B, 'write') as write:
            result = (entry or C.main)()
        return result, calls, manifest, load, validate, write

    def test_default_matches_phase_default_for_every_phase(self):
        default = inspect.signature(C.F.run).parameters['max_bytes'].default
        self.assertEqual(default, 1_500_000_000)
        for phase in C.F.PHASES:
            with self.subTest(phase=phase):
                result, calls, manifest, _, validate, _ = self.invoke(phase=phase)
                self.assertEqual(result, 4)
                self.assertEqual(len(calls), 1)
                args, kwargs = calls[0]
                self.assertIs(args[0], manifest)
                self.assertTrue(args[2].synthetic)
                self.assertEqual(args[3:], (phase, 14400, None, None))
                self.assertEqual(kwargs, {'max_bytes': default})
                validate.assert_called_once_with(manifest, synthetic=True)

    def test_explicit_cap_and_other_arguments_reach_run(self):
        for phase in C.F.PHASES:
            with self.subTest(phase=phase):
                result, calls, *_ = self.invoke([
                    '--max-bytes', '4000000000', '--max-seconds', '123',
                    '--tower-cache', 'tower', '--own-cache', 'own'], phase=phase)
                self.assertEqual(result, 4)
                args, kwargs = calls[0]
                self.assertEqual(args[3:], (phase, 123, 'tower', 'own'))
                self.assertEqual(kwargs, {'max_bytes': 4_000_000_000})
                self.assertIs(type(kwargs['max_bytes']), int)

    def test_one_byte_is_positive(self):
        _, calls, *_ = self.invoke(['--max-bytes', '1'])
        self.assertEqual(calls[0][1], {'max_bytes': 1})

    def test_invalid_values_refused_before_manifest_or_run(self):
        for value in ('0', '-1', '-4000000000', '1.5', 'abc'):
            with self.subTest(value=value), \
                 patch.object(C.B, 'load') as load, \
                 patch.object(C.F, 'run') as phase_run, \
                 patch.object(sys, 'argv', ['cli', 'cache', '--phase', 'tower_sam',
                     '--manifest', 'unused', '--out', 'unused', '--max-bytes', value]), \
                 contextlib.redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as exc:
                    C.main()
                self.assertEqual(exc.exception.code, 2)
                self.assertIn('--max-bytes', stderr.getvalue())
                load.assert_not_called()
                phase_run.assert_not_called()

    def test_preflight_does_not_run_cache(self):
        result, calls, manifest, _, _, write = self.invoke(
            ['--max-bytes', '4000000000'], stage='preflight')
        self.assertEqual(result, 0)
        self.assertEqual(calls, [])
        self.assertEqual(write.call_args.args[1]['manifest_sha256'], C.B.digest(manifest))

    def test_pipeline_entry_delegates_to_cli(self):
        # _native verifies absolute deployment paths; pin verification is tested
        # separately with scratch paths mapped to those deployment paths.
        with patch.object(C.K, '_native') as native:
            result, calls, *_ = self.invoke(
                ['--max-bytes', '4000000000'], entry=C.K.main)
        native.assert_called_once_with()
        self.assertEqual(result, 4)
        self.assertEqual(calls[0][1], {'max_bytes': 4_000_000_000})

    def test_wrapper_forwards_extra_arguments(self):
        script = (KIT / 'work/run_k1.sh').read_text()
        self.assertIn('shift 8\n', script)
        command = script.splitlines()[-1]
        self.assertIn('"$work/k1_pipeline.py" cache ', command)
        self.assertTrue(command.endswith('"$@"'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
