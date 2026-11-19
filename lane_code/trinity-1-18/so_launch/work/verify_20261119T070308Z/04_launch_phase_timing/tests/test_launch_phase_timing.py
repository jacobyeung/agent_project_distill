import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import torch
torch.set_num_threads(8)


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
        return result, trace.read_text()

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
