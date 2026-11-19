"""Exercise r.sh's real control flow with CPU stubs; no cluster or GPU commands."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import torch
torch.set_num_threads(8)


class PreparedWrapperTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='pc-wrapper-', dir=os.environ['TEST_TMP_ROOT']))
        for name in ('b', 'k', 'o', 'runtime/bin'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        source = Path(__file__).resolve().parents[1] / 'launch_s1/b/r.sh'
        # Redirect only the wrapper's hard-coded scratch prefix into this fixture.
        (self.root / 'b/r.sh').write_text(source.read_text().replace('/tmp/jjyeung', str(self.root / 'tmp')))
        (self.root / 'runtime/bin/python').symlink_to(sys.executable)
        for name in ('a', 'g', 'i', 'pc'):
            (self.root / 'b' / (name + '.py')).write_text(
                'import os,sys\nfrom pathlib import Path\n'
                'name=Path(__file__).stem\n'
                'with open(os.environ["TRACE"], "a") as f: f.write(name+" "+" ".join(sys.argv[1:2])+"\\n")\n'
                'if name == "i": sys.exit(int(os.environ.get("CHILD_RC", "0")))\n')
        (self.root / 'b/c.sh').write_text('''
K=fixture
HM="$HX"
NX="$HX"
X="$HX"
S="$HX/node"
NR="$TK_RUNS_DIR"
mkdir -p "$S"
tk_stage() { TK_PC_HIT="${TEST_HIT:-0}"; printf 'stage %s\n' "$1" >> "$TRACE"; }
tk_bwrap() { BW=(); }
tk_env() { PILOT_VENV="$HX/runtime"; }
tk_pythonpath() { :; }
tk_step() { printf '%s\n' "$*" >> "$TRACE"; }
tk_persist_small() { :; }
tk_persist_exports() { :; }
sleep() { return 1; }
''')
        (self.root / 'k/launch.json').write_text(json.dumps(dict(run_directory=str(self.root / 'runs/run'), in_job_admission={'schema':'fixture'})))

    def run_wrapper(self, enabled, hit, child_rc=0, mode='p'):
        trace = self.root / 'trace'
        env = {**os.environ, 'CUDA_VISIBLE_DEVICES':'', 'SLURM_JOB_ID':'23456', 'TRACE':str(trace),
               'TK_PREPARED_INPUT_CACHE':str(int(enabled)), 'TK_PREPARED_CACHE_ROOT':str(self.root / 'cache'),
               'TEST_HIT':str(int(hit)), 'CHILD_RC':str(child_rc)}
        result = subprocess.run(['bash', str(self.root / 'b/r.sh'), mode, '0'], env=env,
                                capture_output=True, text=True, timeout=20)
        return result, trace.read_text()

    def test_hit_reuses_verified_phases_without_launching_native_builder(self):
        result, trace = self.run_wrapper(True, True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('stage prep', trace)
        self.assertIn('CPU admission phases reused', trace)
        self.assertNotIn('\ni ', trace)
        self.assertNotIn('\npc ', trace)

    def test_miss_runs_native_builder_then_publishes(self):
        result, trace = self.run_wrapper(True, False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\ni ', trace)
        self.assertIn('\npc seal', trace)

    def test_default_off_uses_native_path_and_writes_no_cache(self):
        result, trace = self.run_wrapper(False, False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\ni ', trace)
        self.assertNotIn('\npc ', trace)
        self.assertFalse((self.root / 'runs/.prepare-locks').exists())

    def test_failed_native_preparation_is_not_published(self):
        result, trace = self.run_wrapper(True, False, 9)
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertIn('\ni ', trace)
        self.assertNotIn('\npc ', trace)

    def test_recursive_resume_inherits_lock_and_still_launches_training(self):
        result, trace = self.run_wrapper(True, True, mode='u')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(line.startswith('i ') for line in trace.splitlines()), 1)
        self.assertIn('CPU admission phases reused', trace)
        self.assertIn('launch u 0', trace)

    def test_two_jobs_for_one_run_serialize_native_preparation(self):
        (self.root / 'b/i.py').write_text(
            'import os,time\n'
            'def event(name):\n'
            '    with open(os.environ["TRACE"], "a") as f: f.write(name+" "+os.environ["SLURM_JOB_ID"]+"\\n")\n'
            'event("i-start")\ntime.sleep(.15)\nevent("i-end")\n')
        trace = self.root / 'concurrent-trace'
        environment = {**os.environ, 'CUDA_VISIBLE_DEVICES':'', 'TRACE':str(trace),
                       'TK_PREPARED_INPUT_CACHE':'1', 'TK_PREPARED_CACHE_ROOT':str(self.root / 'cache'),
                       'TEST_HIT':'0'}
        processes = [subprocess.Popen(['bash', str(self.root / 'b/r.sh'), 'p', '0'],
                                      env={**environment, 'SLURM_JOB_ID':job},
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for job in ('23457', '23458')]
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        events = [line.split() for line in trace.read_text().splitlines() if line.startswith('i-')]
        self.assertEqual([row[0] for row in events], ['i-start', 'i-end', 'i-start', 'i-end'])
        self.assertEqual(events[0][1], events[1][1])
        self.assertEqual(events[2][1], events[3][1])
        self.assertNotEqual(events[0][1], events[2][1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
