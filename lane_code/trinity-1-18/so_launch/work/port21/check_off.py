"""Compare actual OFF results against build 21 before running ON suites."""
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import patch
import torch

torch.set_num_threads(8)
W = Path(__file__).resolve().parent
BASE = W / 'baseline'
TREE = Path(sys.argv.pop(1)).resolve()
for key in ('TK_CHECKPOINT_VERIFY_MEMO', 'TK_PARALLEL_FRAME_SHA', 'TK_LAUNCH_TIMING', 'TK_PREPARED_INPUT_CACHE'):
    os.environ.pop(key, None)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


memo = load('memo_fixture', W / '03_checkpoint_verify_memo/tests/test_checkpoint_verify_memo.py')
frames = load('frame_fixture', W / '02_parallel_frame_sha/tests/test_parallel_frame_sha.py')
timing = load('timing_fixture', W / '04_launch_phase_timing/tests/test_launch_phase_timing.py')


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def observed(function):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            result = ('return', function())
        except Exception as exc:
            result = (type(exc).__name__, str(exc))
    return result, out.getvalue().encode(), err.getvalue().encode()


class OffIdentity(unittest.TestCase):
    def test_checkpoint_verdict_stdout_stderr_and_fixture_bytes(self):
        fixture = memo.CheckpointMemoTests()
        fixture.setUp()
        fixture.doCleanups()
        original = load('original_r8', BASE / 'launch_s1/b/r8.py')
        candidate = load('candidate_r8', TREE / 'launch_s1/b/r8.py')
        for switch in (None, '0'):
            with patch.dict(os.environ):
                if switch is None:
                    os.environ.pop('TK_CHECKPOINT_VERIFY_MEMO', None)
                else:
                    os.environ['TK_CHECKPOINT_VERIFY_MEMO'] = switch
                for binding in (fixture.binding, dict(fixture.binding, world_size=4)):
                    before = snapshot(fixture.root)
                    expected = observed(lambda: original.complete(fixture.marker, binding))
                    actual = observed(lambda: candidate.complete(fixture.marker, binding))
                    self.assertEqual(actual, expected)
                    self.assertEqual(snapshot(fixture.root), before)
        (fixture.directory / 'replicated.pt').write_bytes(b'corrupt')
        self.assertEqual(observed(lambda: candidate.complete(fixture.marker, fixture.binding)),
                         observed(lambda: original.complete(fixture.marker, fixture.binding)))
        self.assertFalse((fixture.root / '.checkpoint-verification').exists())

    def test_frame_verdict_stdout_stderr_and_fixture_bytes(self):
        fixture = frames.FrameHashTests()
        fixture.setUp()
        fixture.manifest.write_text(json.dumps(fixture.values))
        original = load('original_f2', BASE / 'launch_s1/b/f2.py')
        candidate = load('candidate_f2', TREE / 'launch_s1/b/f2.py')
        digest = frames.hashlib.sha256(fixture.manifest.read_bytes()).hexdigest()
        for corrupt in (False, True):
            if corrupt:
                fixture.paths[-1].write_bytes(b'corrupt')
            for switch in (None, '0'):
                with patch.dict(os.environ):
                    if switch is None:
                        os.environ.pop('TK_PARALLEL_FRAME_SHA', None)
                    else:
                        os.environ['TK_PARALLEL_FRAME_SHA'] = switch
                    before = snapshot(fixture.root)
                    expected = observed(lambda: original.verify(fixture.manifest, fixture.data, digest))
                    actual = observed(lambda: candidate.verify(fixture.manifest, fixture.data, digest))
                    self.assertEqual(actual, expected)
                    self.assertEqual(snapshot(fixture.root), before)

    def test_job_commands_and_output_bytes(self):
        fixture = timing.LaunchTimingTests()
        fixture.setUp()
        for switch in (None, '0'):
            for fail in (False, True):
                results = []
                for tree in (BASE, TREE):
                    (fixture.root / 'job.sh').write_bytes((tree / 'launch_s1/job.sh').read_bytes())
                    trace = fixture.root / 'trace'
                    trace.write_bytes(b'')
                    env = dict(os.environ, TRACE=str(trace), SLURM_JOB_ID='12345')
                    env.pop('TK_LAUNCH_TIMING', None)
                    if switch is not None:
                        env['TK_LAUNCH_TIMING'] = switch
                    if fail:
                        env['FAIL_G'] = '1'
                    result = subprocess.run(['bash', str(fixture.root / 'job.sh')], env=env,
                                            capture_output=True, timeout=15)
                    results.append((result.returncode, result.stdout, result.stderr, trace.read_bytes()))
                self.assertEqual(results[0], results[1])
                self.assertEqual(results[0][0], 7 if fail else 0)
                self.assertFalse((fixture.root / 'o/12345.steps').exists())

    def test_real_stage_output_and_steps_bytes(self):
        # Reuse the shipped real-c.sh fixture, with its ON execution removed.
        import inspect
        source = ast.unparse(ast.parse('class Harness:\n' + inspect.getsource(timing.LaunchTimingTests.test_real_stage_lock_timing_prep_and_preflight_on_off)).body[0].body[0])
        start = source.index('            on = execute(')
        end = source.index('            if os.environ.get(', start)
        source = source[:start] + source[end:]
        ns = dict(timing.__dict__)
        ns['__file__'] = str(TREE / 'tests/test_launch_phase_timing.py')
        exec(source, ns)
        fixture = timing.LaunchTimingTests()
        fixture.setUp()
        with patch.dict(os.environ, TIMING_INPUT_C=str(BASE / 'launch_s1/b/c.sh')):
            ns['test_real_stage_lock_timing_prep_and_preflight_on_off'](fixture)

    def test_recursive_and_parent_run_output_and_command_bytes(self):
        import inspect
        source = ast.unparse(ast.parse('class Harness:\n' + inspect.getsource(timing.LaunchTimingTests.test_recursive_and_parent_guards_have_timing_and_preserve_failure)).body[0].body[0])
        source = source[:source.index('    for fail in (False, True):')]
        ns = dict(timing.__dict__)
        exec(source, ns)
        fixture = timing.LaunchTimingTests()
        fixture.setUp()
        ns['test_recursive_and_parent_guards_have_timing_and_preserve_failure'](fixture)
        root = fixture.root
        (root / 'b/g.py').write_text('import os,sys\nwith open(os.environ["TRACE"], "a") as f: f.write("g "+sys.argv[-1]+"\\n")\nsys.exit(7 if os.environ.get("FAIL_G") else 0)\n')
        for switch in (None, '0'):
            for fail in (False, True):
                results = []
                for tree in (BASE, TREE):
                    (root / 'b/r.sh').write_text((tree / 'launch_s1/b/r.sh').read_text().replace('/tmp/jjyeung', str(root / 'tmp')))
                    trace = root / 'run-trace'
                    trace.write_bytes(b'')
                    env = dict(os.environ, TRACE=str(trace), SLURM_JOB_ID='23461')
                    env.pop('TK_LAUNCH_TIMING', None)
                    env.pop('FAIL_G', None)
                    if switch is not None:
                        env['TK_LAUNCH_TIMING'] = switch
                    if fail:
                        env['FAIL_G'] = '1'
                    result = subprocess.run(['bash', str(root / 'b/r.sh'), 'u', '0'], env=env,
                                            capture_output=True, timeout=15)
                    results.append((result.returncode, result.stdout, result.stderr, trace.read_bytes()))
                self.assertEqual(results[0], results[1])
                self.assertEqual(results[0][0], 7 if fail else 0)
                self.assertFalse((root / 'o/23461.steps').exists())


unittest.main(verbosity=2)
