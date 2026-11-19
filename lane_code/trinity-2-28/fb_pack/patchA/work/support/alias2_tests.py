"""CPU source-mutation and environment-contract tests; no launch authorization."""
import ast
import inspect
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from launch_r2 import distributed, host, runtime
from student_pilot import job_env, r2_intake, r2_materialize, source_seal

AFTER = 'STUDENT_R2_FRAME_HOST' in job_env.ALIASES
NATIVE = 'STUDENT_R2_FRAME_HOST'

class AliasIntegration(unittest.TestCase):
    def test_receipt_shape(self):
        records = runtime.obligations()
        self.assertEqual(len(records), 5)
        self.assertEqual([r['category'] for r in records], ['frame-host']*3+['model-loader']*2)
        for r in records:
            self.assertTrue(Path(r['source']['path']).is_file())
            self.assertGreater(r['line'], 0)

    def mutated(self, module, function, transform):
        path = Path(tempfile.mkdtemp(prefix='obligation_mutation_')) / Path(module.__file__).name
        source = Path(module.__file__).read_text()
        altered = transform(source)
        self.assertNotEqual(source, altered)
        path.write_text(altered)
        namespace = dict(vars(module), __file__=str(path))
        exec(compile(altered, str(path), 'exec'), namespace)
        return patch.object(module, function, namespace[function])

    def test_intake_guard_removed(self):
        lookup = "os.environ.get(env_key('STUDENT_R2_FRAME_HOST')) == '1'" if AFTER else "os.environ.get('STUDENT_R2_FRAME_HOST') == '1'"
        with self.mutated(r2_intake, 'intake', lambda s: s.replace(lookup, 'True')):
            if AFTER:
                with self.assertRaisesRegex(ValueError, 'Statement obligation is ambiguous or absent'):
                    runtime.obligations()
            else:
                # Baseline has no intake-source obligation; record that gap explicitly.
                self.assertEqual(len(runtime.obligations()), 5)

    def test_intake_guard_duplicate(self):
        def duplicate(s):
            lines = s.splitlines(True)
            i = next(i for i, line in enumerate(lines) if 'remote_full = (limit is None' in line)
            return ''.join(lines[:i] + lines[i:i+3] + lines[i:])
        with self.mutated(r2_intake, 'intake', duplicate):
            if AFTER:
                with self.assertRaisesRegex(ValueError, 'ambiguous or absent'): runtime.obligations()
            else: self.assertEqual(len(runtime.obligations()), 5)

    def test_materializer_guard_removed(self):
        lookup = "os.environ.get(env_key('STUDENT_R2_FRAME_HOST'))" if AFTER else "os.environ.get('STUDENT_R2_FRAME_HOST')"
        with self.mutated(r2_materialize, 'materialize', lambda s: s.replace('if '+lookup+" != '1':", 'if False:')):
            with self.assertRaisesRegex(ValueError, 'ambiguous or absent'): runtime.obligations()

    def test_materializer_guard_duplicate(self):
        def duplicate(s):
            lines = s.splitlines(True)
            i = next(i for i, line in enumerate(lines) if 'if os.environ.get(' in line and NATIVE in line)
            return ''.join(lines[:i] + lines[i:i+2] + lines[i:])
        with self.mutated(r2_materialize, 'materialize', duplicate):
            with self.assertRaisesRegex(ValueError, 'ambiguous or absent'): runtime.obligations()

    def test_host_clears_alias_before_scene_preparation(self):
        class StopBeforePreparation(Exception): pass
        for alias in ('0','1'):
            with self.subTest(alias=alias), patch.dict(os.environ, {'Q_E7':alias,NATIVE:'0'}), patch.object(host,'begin_checks',side_effect=StopBeforePreparation):
                with self.assertRaises(StopBeforePreparation):
                    host.execute_packet(Path(tempfile.gettempdir()), {}, None, full=True)
                self.assertEqual(os.environ.get(job_env.key(NATIVE)), '0')
                if AFTER: self.assertNotIn('Q_E7', os.environ)

    def test_worker_translation(self):
        class StopBeforeSourceCheck(Exception): pass
        for alias in (None, '0', '1'):
            for k6 in (None, '0', '1'):
                for native in (None, '0', '1'):
                    env = {'K2': str(Path(source_seal.__file__).parent.parent)}
                    if alias is not None: env['Q_E7'] = alias
                    if k6 is not None: env['K6'] = k6
                    if native is not None: env[NATIVE] = native
                    with self.subTest(alias=alias,k6=k6,native=native), patch.dict(os.environ, env, clear=True), patch.object(source_seal, 'inventory', side_effect=StopBeforeSourceCheck):
                        with self.assertRaises(StopBeforeSourceCheck):
                            distributed.worker(Path(tempfile.gettempdir()), 't', '0')
                        self.assertEqual(os.environ.get(job_env.key(NATIVE)), k6 if k6 is not None else native)
                        if AFTER: self.assertNotIn('Q_E7', os.environ)

    def test_full_host_native_mutation_block(self):
        # Execute the unchanged AST statements from the actual host function.
        # Only the surrounding production setup is omitted; the materializer is real.
        tree = ast.parse(inspect.getsource(host.execute_packet))
        block = next(n for n in ast.walk(tree) if isinstance(n, ast.With) and any(isinstance(v, ast.Assign) and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value == NATIVE for t in v.targets) for v in n.body))
        start = next(i for i, n in enumerate(block.body) if isinstance(n, ast.If) and any(isinstance(v, ast.Constant) and v.value == '0' for v in ast.walk(n)))
        end = next(i for i, n in enumerate(block.body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value == NATIVE for t in n.targets))
        prefix = [n for n in tree.body[0].body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'pop'] if AFTER else []
        self.assertEqual(len(prefix), int(AFTER))
        code = compile(ast.Module(body=prefix+block.body[start:end+1], type_ignores=[]), host.__file__, 'exec')
        u = os.uname()
        for alias in (None, '0', '1'):
            env = {NATIVE:'1'}
            if alias is not None: env['Q_E7'] = alias
            folder = Path(tempfile.mkdtemp(prefix='native_host_block_'))
            with self.subTest(alias=alias), patch.dict(os.environ, env, clear=True), patch.object(os, 'uname', return_value=os.uname_result((u.sysname,'fixture-frame-host',u.release,u.version,u.machine))):
                exec(code, dict(os=os, full=True, materialize=r2_materialize.materialize, paths={'manifests':[]}, output=folder))
                self.assertFalse((folder/'e').exists(), 'negative probe must refuse before creating output')
                self.assertEqual(os.environ.get(job_env.key(NATIVE)), '1')
                with self.assertRaisesRegex(ValueError, 'bound sampling table'):
                    r2_materialize.materialize([],folder/'positive',full=True)

    def test_host_regression_inherited_alias(self):
        from tests.test_r2_build3 import Build3
        for alias in ('0','1'):
            with self.subTest(alias=alias), patch.dict(os.environ, {'Q_E7':alias}):
                Build3('test_native_prepare_and_every_rank_encode').test_native_prepare_and_every_rank_encode()
