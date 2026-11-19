"""Local fixtures only: never invoke real SSH or Git; retain fixtures for review."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import unittest

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / 'tools'
INPUT = Path(os.environ.get('LCS_INPUT', str(BASE / 'inputs')))
FIXTURES = Path(os.environ['LCS_TEST_WORK'])
FIXTURES.mkdir(parents=True, exist_ok=True)
PY = [sys.executable, '-I', '-s', '-B']


def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(0o755)


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='filter_', dir=str(FIXTURES)))

    def scan(self, enabled=True, source=None, injection='', manifest=None):
        source = source or TOOLS / 'lane_code_filter.py'
        env = dict(os.environ, LCS_ROBUST_SYNC='1' if enabled else '0', LCS_FILE_SECONDS='0.05')
        argv = [str(source), 'fixture'] + ([manifest] if manifest else [])
        if injection:
            code = 'import os, sys, time, stat\n' + injection + '\n' + \
                'sys.argv = ' + repr(argv) + '\nexec(compile(open(sys.argv[0]).read(), sys.argv[0], "exec"))\n'
            command = PY + ['-c', code]
        else:
            command = PY + argv
        return subprocess.run(command, cwd=str(self.root), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)

    def test_regular_tree_byte_identical_and_default_off(self):
        for i in range(120):
            write(self.root / ('lane%02d' % (i % 9)) / ('file%03d.py' % i), 'value = %d\n' % (i % 31))
        for name in ('space name.md', 'new\nline.txt', 'unicode_é.yaml', '-option.py'):
            write(self.root / name, name)
        write(self.root / 'runs' / 'hidden.py', 'excluded')
        write(self.root / 'large.json', 'x' * (256 * 1024 + 1))
        write(self.root / 'large.py', 'x' * (512 * 1024 + 1))
        original = self.scan(False, INPUT / 'lane_code_filter.py')
        off, on = self.scan(False), self.scan(True)
        self.assertEqual((original.returncode, off.returncode, on.returncode), (0, 0, 0))
        self.assertEqual((off.stdout, off.stderr), (original.stdout, original.stderr))
        self.assertEqual(on.stdout, original.stdout)
        print('MEASURE regular_paths_sha256=' + hashlib.sha256(on.stdout).hexdigest(), flush=True)

    def test_fifo_socket_symlinks_never_opened(self):
        write(self.root / 'good.py', 'good')
        os.mkfifo(str(self.root / 'DECISION_PART2.json'))
        # A socket inode suffices; no bind/listen or network access is required.
        os.mknod(str(self.root / 'socket.json'), stat.S_IFSOCK | 0o600)
        outside = self.root.parent / (self.root.name + '_outside')
        write(outside / 'outside.py', 'outside')
        os.symlink(str(outside / 'outside.py'), str(self.root / 'link.py'))
        os.symlink(str(outside), str(self.root / 'linked_directory'))
        injection = '''original_open = os.open
def checked_open(path, flags, *args, **kw):
    if path in ('DECISION_PART2.json', 'socket.json', 'link.py', 'linked_directory'):
        raise AssertionError('opened a nonregular fixture: ' + path)
    return original_open(path, flags, *args, **kw)
os.open = checked_open'''
        result = self.scan(injection=injection)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'good.py\0')
        self.assertIn(b'skipped_nonregular=2', result.stderr)
        self.assertIn(b'skipped_symlink=2', result.stderr)

    def test_device_mode_is_rejected_before_open(self):
        write(self.root / 'device.json', 'simulated device')
        result = self.scan(injection='''original_lstat = os.lstat
original_open = os.open
def device_lstat(path, *args, **kw):
    result = original_lstat(path, *args, **kw)
    if path == 'device.json':
        fields = list(result); fields[0] = stat.S_IFCHR | 0o600
        return os.stat_result(fields)
    return result
def checked_open(path, *args, **kw):
    if path == 'device.json': raise AssertionError('opened device')
    return original_open(path, *args, **kw)
os.lstat = device_lstat
os.open = checked_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_nonregular=1', result.stderr)

    def test_slow_read_deadline_counts_and_continues(self):
        write(self.root / 'a.py', 'slow')
        write(self.root / 'b.py', 'good')
        started = time.monotonic()
        result = self.scan(injection='''original_read = os.read
slow = [True]
def slow_read(fd, size):
    if slow[0]:
        slow[0] = False
        time.sleep(2)
    return original_read(fd, size)
os.read = slow_read''')
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'b.py\0')
        self.assertIn(b'skipped_timeout=1', result.stderr)
        self.assertLess(elapsed, 1)
        print('MEASURE slow_file_elapsed=%.3fs deadline=0.05s' % elapsed, flush=True)

    def test_replacement_fifo_is_nonblocking_and_fstat_rejected(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        assert flags & os.O_NONBLOCK and flags & os.O_NOFOLLOW
        os.rename('race.py', 'saved.bin')
        os.mkfifo('race.py')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_nonregular=1', result.stderr)

    def test_replacement_symlink_is_not_followed(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        os.rename('race.py', 'saved.bin')
        os.symlink('saved.bin', 'race.py')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_symlink=1', result.stderr)

    def test_directory_replacement_never_follows_link_or_blocks_on_fifo(self):
        for replacement in ('symlink', 'fifo'):
            root = self.root
            self.root = root / replacement
            write(self.root / 'adir' / 'good.py', 'inside')
            outside = root / (replacement + '_outside')
            write(outside / 'outside.py', 'outside')
            injection = '''original_open = os.open
count = [0]
def racing_open(path, flags, *args, **kw):
    if path == 'adir':
        assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK and flags & os.O_DIRECTORY
        count[0] += 1
        if count[0] == 2:
            os.rename('adir', 'saved_dir')
            REPLACEMENT
    return original_open(path, flags, *args, **kw)
os.open = racing_open'''
            action = 'os.symlink(%r, "adir")' % str(outside) if replacement == 'symlink' else 'os.mkfifo("adir")'
            result = self.scan(injection=injection.replace('REPLACEMENT', action))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b'')
            self.root = root

    def test_manifest_content_matches_and_link_parent_refused(self):
        write(self.root / 'a.py', 'same')
        write(self.root / 'b.py', 'same')
        result = self.scan(manifest='meta')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'a.py\0meta/DEDUP_fixture.tsv.gz\0')
        with gzip.open(str(self.root / 'meta' / 'DEDUP_fixture.tsv.gz'), 'rb') as f:
            self.assertEqual(f.read(), b'b.py\ta.py\n')
        outside = self.root.parent / (self.root.name + '_outside')
        outside.mkdir()
        os.symlink(str(outside), str(self.root / 'badmeta'))
        refused = self.scan(manifest='badmeta')
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_growth_is_capped_and_io_errors_counted(self):
        write(self.root / 'a.py', 'small')
        write(self.root / 'b.py', 'unreadable')
        result = self.scan(injection='''original_read, original_open = os.read, os.open
def growing_read(fd, size):
    return b'x' * size
def bad_open(path, *args, **kw):
    if path == 'b.py': raise PermissionError('simulated denial')
    return original_open(path, *args, **kw)
os.read, os.open = growing_read, bad_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_oversize=1', result.stderr)
        self.assertIn(b'skipped_io=1', result.stderr)

    def test_changed_regular_inode_is_rejected(self):
        write(self.root / 'race.py', 'before')
        result = self.scan(injection='''original_open = os.open
def racing_open(path, flags, *args, **kw):
    if path == 'race.py':
        os.rename('race.py', 'saved.bin')
        with open('race.py', 'w') as f: f.write('after')
    return original_open(path, flags, *args, **kw)
os.open = racing_open''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'skipped_changed=1', result.stderr)

    def test_original_fifo_reproduces_and_hotfix_skips(self):
        os.mkfifo(str(self.root / 'DECISION_PART2.json'))
        started = time.monotonic()
        original = subprocess.run(['timeout', '--kill-after=0.1', '0.15'] + PY +
                                  [str(INPUT / 'lane_code_filter.py.orig'), 'original'],
                                  cwd=str(self.root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        elapsed = time.monotonic() - started
        self.assertEqual(original.returncode, 124, original.stderr)
        hotfix = self.scan(False, INPUT / 'lane_code_filter.py')
        self.assertEqual(hotfix.returncode, 0, hotfix.stderr)
        self.assertEqual(hotfix.stdout, b'')
        print('MEASURE original_fifo_timeout_rc=124 elapsed=%.3fs hotfix_rc=0' % elapsed, flush=True)


FAKE_SSH = r'''import json, os, shlex, signal, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['FAKE_SSH_LOG'], 'a') as f: f.write(json.dumps(args) + '\n')
while args and args[0] == '-o': args = args[2:]
host, command = args[0], ' '.join(args[1:])
root = Path(os.environ['FAKE_ROOT'])
if host == 'trinity-3-30.ib':
    if os.environ.get('FAKE_RECEIVER_HANG') == '1':
        signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(5)
    rc = subprocess.call(['bash', '-c', command])
    if os.environ.get('FAKE_STAGE_FIFO') == '1' and os.environ.get('FAKE_ACTIVE_HOST') == 'trinity-1-18':
        dest = shlex.split(command)[-1]
        os.mkfifo(str(Path(dest) / 'aaa_raced.json'))
    sys.exit(rc)
mode = os.environ.get('FAKE_' + host.replace('-', '_'), 'success')
if mode == 'unreachable':
    assert 'ConnectTimeout=20' in sys.argv
    time.sleep(0.10)
    print('ssh: connect to host ' + host + ': Connection timed out', flush=True)
    sys.exit(255)
if mode.startswith('held'):
    (root / 'ssh.pid').write_text(str(os.getpid()))
    code = ('import os,time; os.setsid(); '
            'open(' + repr(str(root / 'holder.pid')) + ', "w").write(str(os.getpid())); '
            'time.sleep(' + ('1.2' if mode == 'held_exit' else '4') + ')')
    subprocess.Popen([sys.executable, '-I', '-s', '-B', '-c', code],
                     stdin=subprocess.DEVNULL, close_fds=False)
    print('held stdout fixture', flush=True)
    if mode == 'held_exit': sys.exit(0)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(5)
    sys.exit(99)
script = sys.stdin.read()
source = str(root / 'sources' / host)
if mode == 'missing': source += '_absent'
script = script.replace(shlex.quote(os.environ['LCS_LANES_ROOT']), shlex.quote(source), 1)
if mode == 'scanner_hang':
    script = script.replace('python3 - ', 'python3 -c "import time; time.sleep(5)" ', 1)
result = subprocess.run(['bash', '-c', command], input=script.encode(),
                        env=dict(os.environ, FAKE_ACTIVE_HOST=host))
sys.exit(23 if mode == 'partial' else result.returncode)
'''

FAKE_GIT = r'''import json, os, sys
args = sys.argv[1:]
with open(os.environ['FAKE_GIT_LOG'], 'a') as f: f.write(json.dumps(args) + '\n')
if args[:1] == ['-C']: args = args[2:]
if args[:3] == ['diff', '--cached', '--quiet']: sys.exit(1)
if args[:3] == ['diff', '--cached', '--name-only']: print('lane_code/trinity-2-28/good.py')
elif args[:1] == ['rev-parse']: print('a' * 40)
elif args[:1] == ['ls-remote']: print('a' * 40 + '\trefs/heads/lane-code')
elif args[:1] not in (['add'], ['commit'], ['push']):
    raise SystemExit('unexpected fake Git call: ' + repr(args))
'''


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='driver_', dir=str(FIXTURES)))
        self.bin = self.root / 'bin'
        self.state = self.root / 'state'
        self.repo = self.state / 'repo'
        self.b = self.root / 'orchestrator'
        self.local = self.root / 'sources' / 'trinity-3-30'
        for p in (self.bin, self.repo, self.b / 'tools', self.b / 'briefs', self.root / 'events'):
            p.mkdir(parents=True, exist_ok=True)
        for name in ('lane_code_sync.sh', 'lane_code_filter.py', 'lane_code_stage.sh', 'lane_code_scan.py'):
            (self.b / 'tools' / name).write_bytes((TOOLS / name).read_bytes())
        write(self.b / 'briefs' / 'brief.md', 'brief')
        # Use the real wrapper, relocating its lock and removing only its 35 s rate delay.
        wrapper = (TOOLS / 'tssh.sh').read_text()
        wrapper = wrapper.replace('L=/scratch/jjyeung/.tssh_$(hostname -s)',
                                  'L=' + shlex.quote(str(self.root / 'tssh')))
        write(self.b / 'tools' / 'tssh.sh', wrapper.replace('last + 35', 'last + 0'))
        write(self.bin / 'ssh', '#!' + sys.executable + '\n' + FAKE_SSH, True)
        write(self.bin / 'git', '#!' + sys.executable + '\n' + FAKE_GIT, True)
        write(self.bin / 'hostname', '#!/bin/bash\necho trinity-3-30\n', True)
        write(self.bin / 'python3', '#!/bin/bash\nexec ' + shlex.quote(sys.executable) + ' -I -s -B "$@"\n', True)
        for node in ('trinity-1-18', 'trinity-2-28', 'trinity-3-30'):
            write(self.root / 'sources' / node / 'good.py', 'value = ' + repr(node))
        write(self.repo / 'lane_code' / 'trinity-1-18' / 'prior.py', 'prior-clone')
        write(self.repo / 'lane_code' / 'trinity-1-18' / 'good.py', 'prior-good')
        write(self.state / 'stage' / 'trinity-1-18' / 'prior.py', 'prior-stage')
        self.env = dict(os.environ, PATH=str(self.bin) + ':/usr/bin:/bin',
                        LCS_ROBUST_SYNC='1', LCS_B=str(self.b), LCS_S=str(self.state),
                        LCS_R=str(self.repo), LCS_EV=str(self.root / 'events'),
                        LCS_LANES_ROOT=str(self.local), FAKE_ROOT=str(self.root),
                        FAKE_GIT_LOG=str(self.root / 'git.jsonl'), FAKE_SSH_LOG=str(self.root / 'ssh.jsonl'),
                        LCS_SCAN_SECONDS='0.4', LCS_COPY_SECONDS='0.4', LCS_LEG_SECONDS='0.7', LCS_REMOTE_SECONDS='1.0',
                        LCS_NODE_SECONDS='1.3', LCS_KILL_SECONDS='0.15', LCS_FILE_SECONDS='0.1')

    def run_driver(self, extra=()):
        started = time.monotonic()
        result = subprocess.run(['bash', str(self.b / 'tools' / 'lane_code_sync.sh')] + list(extra),
                                env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        self.elapsed = time.monotonic() - started
        (self.root / 'driver.stdout').write_bytes(result.stdout)
        (self.root / 'driver.stderr').write_bytes(result.stderr)
        return result

    def check_partial_success(self, result):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual((self.repo / 'lane_code' / 'trinity-1-18' / 'prior.py').read_text(), 'prior-clone')
        self.assertEqual((self.repo / 'lane_code' / 'trinity-1-18' / 'good.py').read_text(), 'prior-good')
        self.assertEqual((self.state / 'stage' / 'trinity-1-18' / 'prior.py').read_text(), 'prior-stage')
        self.assertTrue((self.repo / 'lane_code' / 'trinity-2-28' / 'good.py').is_file())
        self.assertTrue((self.repo / 'lane_code' / 'trinity-3-30' / 'good.py').is_file())
        calls = [json.loads(line)[2:] for line in (self.root / 'git.jsonl').read_text().splitlines()]
        self.assertEqual(sum(args[0] == 'commit' for args in calls), 1)
        self.assertEqual(sum(args[0] == 'push' for args in calls), 2)
        self.assertEqual(len(list((self.root / 'events').glob('*_BLOCKER_sync_failed.md'))), 1)
        self.assertIn(b'PIPE 0 0 0', result.stdout)

    def test_all_sources_success_and_new_node(self):
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'STAGED trinity-2-28 rc=0', result.stdout)
        self.assertIn(b'verified GitHub lane-code', result.stdout)
        calls = [json.loads(line) for line in (self.root / 'ssh.jsonl').read_text().splitlines()]
        receiver = [args for args in calls if 'trinity-3-30.ib' in args]
        self.assertEqual(len(receiver), 2)
        self.assertTrue(all('ConnectionAttempts=1' in args for args in receiver))

    def test_partial_failed_node_cannot_overwrite_or_delete_previous(self):
        self.env['FAKE_trinity_1_18'] = 'partial'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 stage rc=23', result.stdout)
        print('MEASURE partial_failure_elapsed=%.3fs commit=1 pushes=2 preserved=1' % self.elapsed, flush=True)

    def test_unreachable_skipped_other_sources_publish(self):
        self.env['FAKE_trinity_1_18'] = 'unreachable'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'Connection timed out', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_missing_root_skipped_other_sources_publish(self):
        self.env['FAKE_trinity_1_18'] = 'missing'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'SKIP trinity-1-18 no orch_n30/source', result.stdout)

    def test_held_stdout_deadline_and_lock_release(self):
        self.env['FAKE_trinity_1_18'] = 'held_hang'
        self.env['LCS_NODE_SECONDS'] = '0.35'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertLess(self.elapsed, 3)
        pid = int((self.root / 'holder.pid').read_text())
        os.kill(pid, 0)  # The child still holds stdout after the driver has returned.
        ssh_pid = int((self.root / 'ssh.pid').read_text())
        # A zombie has exited; it is waiting for PID 1 to reap it.
        proc = Path('/proc') / str(ssh_pid) / 'stat'
        if proc.exists():
            self.assertEqual(proc.read_text().split(') ', 1)[1].split()[0], 'Z')
        locked = subprocess.run(['flock', '-n', str(self.state / '.sync.lock'), 'true'])
        self.assertEqual(locked.returncode, 0)
        self.assertRegex(result.stdout.decode(), r'trinity-1-18 stage rc=(124|137)')
        run = next((self.state / 'stage-runs').iterdir())
        node_elapsed = (run / 'trinity-1-18.snapshot').stat().st_mtime - (run / 'trinity-1-18.sh').stat().st_mtime
        self.assertLess(node_elapsed, 0.9)
        self.assertGreater(node_elapsed, 0.35)
        print('MEASURE held_stdout_driver_elapsed=%.3fs node_limit=0.35s kill_after=0.15s holder_alive=1 lock_free=1' % self.elapsed, flush=True)
        print('MEASURE held_stdout_node_elapsed=%.3fs' % node_elapsed, flush=True)

    def test_legacy_substitution_reproduces_held_pipe(self):
        self.env['FAKE_trinity_1_18'] = 'held_exit'
        command = 'out=$(timeout --kill-after=0.1 0.2 ssh trinity-1-18 ignored 2>&1); echo finished'
        started = time.monotonic()
        result = subprocess.run(['bash', '-c', command], env=self.env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=4)
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0)
        self.assertGreater(elapsed, 1)
        print('MEASURE legacy_substitution_elapsed=%.3fs timeout=0.2s holder_lifetime=1.2s' % elapsed, flush=True)

    def test_remote_scanner_timeout_reports_pipestatus(self):
        self.env['FAKE_trinity_1_18'] = 'scanner_hang'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'PIPE 124 0 0', result.stdout)

    def test_receiver_timeout_does_not_block_local_publish(self):
        self.env['FAKE_RECEIVER_HANG'] = '1'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'PIPE 0 0 137', result.stdout)
        self.assertTrue((self.repo / 'lane_code' / 'trinity-3-30' / 'good.py').is_file())
        self.assertIn(b'committed', result.stdout)
        self.assertLess(self.elapsed, 4)

    def test_dry_mode_and_stage_only_keep_existing_semantics(self):
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'PIPE 0', result.stdout)
        self.assertFalse((self.root / 'git.jsonl').exists())
        result = self.run_driver(('--stage-only',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / 'lane_code' / 'trinity-2-28' / 'good.py').is_file())
        self.assertFalse((self.root / 'git.jsonl').exists())

    def test_invalid_zero_timeout_refused(self):
        self.env['LCS_NODE_SECONDS'] = '0'
        result = self.run_driver()
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'invalid LCS_NODE_SECONDS=0', result.stdout)
        self.assertFalse((self.root / 'ssh.jsonl').exists())

    def test_tssh_rate_lock_wait_is_also_bounded(self):
        wrapper = self.b / 'tools' / 'tssh.sh'
        wrapper.write_text(wrapper.read_text().replace('last + 0', 'last + 35'))
        write(self.root / 'tssh' / 'last', str(int(time.time())))
        self.env['LCS_NODE_SECONDS'] = '0.15'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'trinity-1-18 stage rc=124', result.stdout)
        self.assertIn(b'trinity-2-28 stage rc=124', result.stdout)
        self.assertFalse((self.root / 'ssh.jsonl').exists())
        self.assertTrue((self.repo / 'lane_code' / 'trinity-3-30' / 'good.py').is_file())
        self.assertIn(b'committed', result.stdout)
        self.assertLess(self.elapsed, 2)

    def test_outer_remote_timeout(self):
        self.env.update(FAKE_trinity_1_18='scanner_hang', LCS_SCAN_SECONDS='2',
                        LCS_LEG_SECONDS='2', LCS_REMOTE_SECONDS='0.3')
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 stage rc=124', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_copy_scanner_fifo_is_bounded_per_source(self):
        self.env['FAKE_STAGE_FIFO'] = '1'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 scan/copy rc=124', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_tar_leg_kill_after_and_other_sources_publish(self):
        write(self.bin / 'tar', '#!/bin/bash\n'
              'if [[ "$PWD" == */sources/trinity-1-18 ]] && [[ " $* " == *" -cf "* ]]; then\n'
              '  trap "" TERM; sleep 4\n'
              'else exec /usr/bin/tar "$@"; fi\n', True)
        self.env['LCS_LEG_SECONDS'] = '0.25'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertRegex(result.stdout.decode(), r'PIPE 0 137 (2|124|137)')
        self.assertLess(self.elapsed, 3)

    def test_default_off_driver_matches_input_behavior(self):
        self.env['LCS_ROBUST_SYNC'] = '0'
        # Rewrite only fixed source paths in fixture copies; neither driver can touch a real lane.
        baseline = (INPUT / 'lane_code_sync.sh').read_text()
        candidate = (TOOLS / 'lane_code_sync.sh').read_text()
        outputs, trees = [], []
        for name, text in (('baseline', baseline), ('candidate', candidate)):
            script = self.root / (name + '.sh')
            script.write_text(text.replace('/scratch/jjyeung/orch_n30', str(self.local)).replace('code_sync/meta', ''))
            state = self.root / name
            repo = state / 'repo'
            repo.mkdir(parents=True)
            env = dict(self.env, LCS_S=str(state), LCS_R=str(repo))
            result = subprocess.run(['bash', str(script)], env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=5)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            normalized = result.stdout.decode().replace(str(state), '<STATE>')
            outputs.append(re.sub(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', '<UTC>', normalized))
            trees.append({str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()})
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(trees[0], trees[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
