import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import torch
torch.set_num_threads(8)
sys.path.insert(0, str(Path(__file__).resolve().parent))


class LaunchTimingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='launch-timing-', dir=os.environ['TEST_TMP_ROOT']))
        for name in ('b', 'k', 'o'):
            (self.root / name).mkdir()
        source = Path(__file__).resolve().parents[1] / 'launch_s1/job.sh'
        shutil.copyfile(source, self.root / 'job.sh')
        for name in ('a', 'g', 'r8'):
            (self.root / 'b' / (name + '.py')).write_text(
                'import os,sys\nfrom pathlib import Path\n'
                'with open(os.environ["TRACE"], "a") as f: f.write(Path(__file__).stem+"\\n")\n'
                'if Path(__file__).stem == "g" and os.environ.get("FAIL_G"): sys.exit(7)\n'
                'if Path(__file__).stem == "r8": print("t")\n')
        (self.root / 'b/p0.sh').write_text('printf "p0\\n" >> "$TRACE"\n')
        (self.root / 'b/r.sh').write_text('printf "r %s %s\\n" "$1" "$2" >> "$TRACE"\nprintf "baseline-output\\n"\n')
        (self.root / 'k/launch.json').write_text('{"run_directory":"/fixture/run"}')

    def launch(self, timing, fail=False):
        trace = self.root / ('trace-' + str(timing) + str(fail))
        env = {**os.environ, 'TK_LAUNCH_TIMING': str(int(timing)), 'TRACE': str(trace), 'SLURM_JOB_ID': '12345'}
        if fail:
            env['FAIL_G'] = '1'
        result = subprocess.run(['bash', str(self.root / 'job.sh')], env=env, capture_output=True, text=True, timeout=15)
        return result, trace.read_text() if trace.exists() else ''

    def test_default_path_runs_same_commands_and_produces_no_timing(self):
        result, trace = self.launch(False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'baseline-output\n')
        self.assertEqual(trace, 'a\np0\ng\nr8\nr t 0\n')
        self.assertFalse((self.root / 'o/12345.steps').exists())

    def test_enabled_logs_boundaries_without_polluting_mode_stdout(self):
        result, trace = self.launch(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'baseline-output\n')
        self.assertEqual(trace, 'a\np0\ng\nr8\nr t 0\n')
        events = (self.root / 'o/12345.steps').read_text().splitlines()
        self.assertEqual([line.split()[-1] for line in events], [
            'capsule_start', 'capsule_done', 'import_preflight_start', 'import_preflight_done',
            'launch_guard_start', 'launch_guard_done', 'resume_choice_start', 'resume_choice_done', 'dispatch_start'])

    def test_failed_guard_preserves_exit_status_and_stops_dispatch(self):
        result, trace = self.launch(True, True)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(trace, 'a\np0\ng\n')
        self.assertTrue((self.root / 'o/12345.steps').read_text().rstrip().endswith('launch_guard_start'))

    def test_missing_output_directory_does_not_abort_or_create_logs(self):
        (self.root / 'o').rename(self.root / 'unused-output')
        result, trace = self.launch(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'baseline-output\n')
        self.assertEqual(trace, 'a\np0\ng\nr8\nr t 0\n')
        self.assertFalse((self.root / 'o').exists())

    def test_unwritable_steps_destination_does_not_abort(self):
        (self.root / 'o/12345.steps').mkdir()
        result, trace = self.launch(True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(trace, 'a\np0\ng\nr8\nr t 0\n')

    def test_recursive_and_parent_guards_have_timing_and_preserve_failure(self):
        # Standalone patch 04 has no dependency on patch 01's test fixture.
        root = self.root
        source = Path(__file__).resolve().parents[1] / 'launch_s1/b/r.sh'
        (root / 'b/r.sh').write_text(source.read_text().replace('/tmp/jjyeung', str(root / 'tmp')))
        (root / 'runtime/bin').mkdir(parents=True)
        (root / 'runtime/bin/python').symlink_to(sys.executable)
        (root / 'b/c.sh').write_text('''K=fixture
HM="$HX"; NX="$HX"; X="$HX"; S="$HX/node"
tk_stage() { :; }
tk_bwrap() { BW=(); }
tk_env() { PILOT_VENV="$HX/runtime"; }
tk_pythonpath() { :; }
tk_step() { :; }
tk_persist_small() { :; }
tk_persist_exports() { :; }
sleep() { return 1; }
''')
        (root / 'b/i.py').write_text('pass\n')
        (root / 'b/g.py').write_text('import os,sys\nsys.exit(7 if os.environ.get("FAIL_G") else 0)\n')
        import json
        (root / 'k/launch.json').write_text(json.dumps(dict(
            run_directory=str(root / 'runs/run'), in_job_admission={'schema':'fixture'})))
        for fail in (False, True):
            with self.subTest(fail=fail):
                job = '23462' if fail else '23461'
                env = {**os.environ, 'TK_LAUNCH_TIMING':'1', 'TK_PREPARED_INPUT_CACHE':'0',
                       'SLURM_JOB_ID':job, 'TRACE':str(root / ('run-' + job))}
                env.pop('FAIL_G', None)
                if fail:
                    env['FAIL_G'] = '1'
                result = subprocess.run(['bash', str(root / 'b/r.sh'), 'u', '0'], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 7 if fail else 0, result.stderr)
                events = (root / 'o' / (job + '.steps')).read_text().splitlines()
                self.assertEqual([line.split()[-1] for line in events],
                    ['run_p_launch_guard_start'] if fail else [
                    'run_p_launch_guard_start', 'run_p_launch_guard_done',
                    'run_u_launch_guard_start', 'run_u_launch_guard_done'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
