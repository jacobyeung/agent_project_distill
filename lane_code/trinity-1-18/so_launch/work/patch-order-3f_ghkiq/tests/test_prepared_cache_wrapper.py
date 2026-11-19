"""Exercise r.sh's real control flow with CPU stubs; no cluster or GPU commands."""
import json
import fcntl
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
        result = subprocess.run(['timeout', '--kill-after=1', '3', 'bash', str(self.root / 'b/r.sh'), mode, '0'], env=env,
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

    def test_recursive_resume_with_symlinked_parent_inherits_lock(self):
        real = self.root / 'physical-runs'
        real.mkdir()
        (self.root / 'runs').symlink_to(real, target_is_directory=True)
        result, trace = self.run_wrapper(True, True, mode='u')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CPU admission phases reused', trace)
        self.assertEqual(sum(line.startswith('i ') for line in trace.splitlines()), 1)

    def test_duplicate_training_or_resume_job_times_out_with_75(self):
        locks = self.root / 'runs/.prepare-locks'
        locks.mkdir(parents=True)
        # Scale only the waiting time. The real flock still contends on the
        # descriptor held here; assert the production request remains 600 s.
        hook = self.root / 'flock-test.sh'
        hook.write_text('''flock() {
    printf 'flock %s\\n' "$*" >> "$TRACE"
    if [[ "$1" == -w ]]; then shift 2; fi
    /usr/bin/flock -w 0.1 "$@"
}
''')
        with (locks / 'run.lock').open('a+b') as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            for mode, marker in ((m, k) for m in ('t', 'u') for k in ('unset', '1', '99999999')):
                with self.subTest(mode=mode, marker=marker):
                    trace = self.root / ('duplicate-' + mode + '-' + marker)
                    env = {**os.environ, 'SLURM_JOB_ID':'23459', 'TRACE':str(trace),
                           'TK_PREPARED_INPUT_CACHE':'1', 'BASH_ENV':str(hook)}
                    env.pop('TK_PC_LOCK_HELD', None)
                    if marker != 'unset':
                        env['TK_PC_LOCK_HELD'] = marker
                    result = subprocess.run(['bash', str(self.root / 'b/r.sh'), mode, '0'],
                                            env=env, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 75, result.stderr)
                    self.assertIn('flock -w 600 7', trace.read_text())
                    self.assertNotIn('stage prep', trace.read_text())

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


class RealStageTests(unittest.TestCase):
    def test_real_c_stage_hit_miss_error_and_missing_root(self):
        root = Path(tempfile.mkdtemp(prefix='real-stage-', dir=os.environ['TEST_TMP_ROOT']))
        tree = Path(__file__).resolve().parents[1]
        kit = root / 'kit'
        for directory in ('b/sa', 'k', 'o'):
            (kit / directory).mkdir(parents=True)
        # Source the entire real c.sh. Only host scratch constants and staging
        # dependencies change; tk_stage itself executes without substitution.
        (kit / 'b/c.sh').write_text((tree / 'launch_s1/b/c.sh').read_text().replace('/tmp/jjyeung', str(root / 'tmp')))
        for name in ('sitecustomize.py', 'prestage_hooks.py'):
            (kit / 'b/sa' / name).write_text('# fixture\n')
        record = root / 'record.json'
        record.write_text('{}')
        (kit / 'k/0.json').write_text(json.dumps(dict(commit='fixture',
            closure=dict(file='closure.tar', sha256='a'*64), record=dict(file=str(record), sha256='b'*64))))
        for name in ('pc', 's'):
            (kit / 'b' / (name + '.py')).write_text(
                'import os,sys\nfrom pathlib import Path\n'
                'name=Path(__file__).stem\n'
                'with open(os.environ["TRACE"], "a") as f: f.write(name+" "+" ".join(sys.argv[1:])+"\\n")\n'
                'sys.exit(int(os.environ["CACHE_RC"]) if name == "pc" else 0)\n')
        shell = '''source "$TK_KIT_HOME/b/c.sh"
tk_nx() { :; }
tk_kitx() {
    mkdir -p "$2" "$S/.stamp"
    if [[ "$1" == art ]]; then mkdir -p "$2/lb"; touch "$2/lb/51f013139e77.npz"; fi
}
tk_venv_shebangs() { :; }
tk_has() { return 1; }
sha_is() { :; }
tk_stage_model() { :; }
tk_stage_small() { :; }
tk_stage_extra() { :; }
tk_stage_tars() { :; }
tk_stage_fla() { :; }
tk_stage_bundle() { printf 'bundle %s\\n' "$1" >> "$TRACE"; }
tk_stage_init() { printf 'init\\n' >> "$TRACE"; }
tk_stage prep
printf 'hit %s\\n' "$TK_PC_HIT" >> "$TRACE"
'''
        for label, enabled, rc, has_root, expected in (
                ('hit', '1', '0', True, 0), ('miss', '1', '1', True, 0),
                ('error', '1', '7', True, 7), ('missing-root', '1', '0', False, 1),
                ('off', '0', '7', False, 0)):
            with self.subTest(case=label):
                trace = root / (label + '.trace')
                trace.touch()
                env = {**os.environ, 'TK_KIT_HOME':str(kit), 'TK_JOBDIR':str(root / 'job'),
                       'SLURM_JOB_ID':'23460', 'TRACE':str(trace), 'TK_PC_PREPARE':'1',
                       'TK_PREPARED_INPUT_CACHE':enabled, 'CACHE_RC':rc}
                env.pop('TK_LIGHT', None)
                env.pop('TK_PREPARED_CACHE_ROOT', None)
                if has_root:
                    env['TK_PREPARED_CACHE_ROOT'] = str(root / 'cache')
                result = subprocess.run(['bash', '-euo', 'pipefail', '-c', shell], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected, result.stderr)
                lines = trace.read_text().splitlines()
                if label == 'hit':
                    self.assertIn('hit 1', lines)
                    self.assertFalse(any(line.startswith('bundle ') for line in lines))
                    self.assertIn('init', lines)
                if label in ('miss', 'off'):
                    self.assertIn('hit 0', lines)
                    self.assertEqual(sum(line.startswith('bundle ') for line in lines), 12)
                if label == 'error':
                    self.assertFalse(any(line.startswith(('bundle ', 's ', 'hit ')) for line in lines))
                if label == 'missing-root':
                    self.assertIn('TK_PREPARED_CACHE_ROOT', result.stderr)
                    self.assertEqual(lines, [])
                if label == 'off':
                    self.assertFalse(any(line.startswith('pc ') for line in lines))


if __name__ == '__main__':
    unittest.main(verbosity=2)
