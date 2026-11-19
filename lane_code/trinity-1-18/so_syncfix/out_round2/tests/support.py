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
TOOLS = Path(os.environ.get('LCS_TOOLS', str(BASE / 'tools')))
INPUT = Path(os.environ.get('LCS_INPUT', str(BASE / 'inputs')))
FIXTURES = Path(os.environ['LCS_TEST_WORK'])
FIXTURES.mkdir(parents=True, exist_ok=True)
PY = [sys.executable, '-I', '-s', '-B']


def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(0o755)




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
        import tarfile
        writer = shlex.split(command)[-1]
        if writer.startswith('cat > '):
            archive = shlex.split(writer)[-1]
            with tarfile.open(archive, 'a') as stream:
                member = tarfile.TarInfo('aaa_raced.json')
                member.type = tarfile.FIFOTYPE
                stream.addfile(member)
        else:
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
    for token in ('python3 -I -s -B - ', 'python3 - '):
        if token in script:
            script = script.replace(token, 'python3 -I -s -B -c \"import time; time.sleep(5)\" ', 1)
            break
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



class DriverFixture(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='driver_', dir=str(FIXTURES)))
        self.bin = self.root / 'bin'
        self.state = self.root / 'state'
        self.repo = self.state / 'repo'
        self.b = self.root / 'orchestrator'
        self.local = self.root / 'sources' / 'trinity-3-30'
        for p in (self.bin, self.repo, self.b / 'tools', self.b / 'briefs', self.root / 'events'):
            p.mkdir(parents=True, exist_ok=True)
        for name in ('lane_code_sync.sh', 'lane_code_filter.py', 'lane_code_stage.sh', 'lane_code_scan.py', 'lane_code_log.py'):
            if not (TOOLS / name).exists():
                continue
            (self.b / 'tools' / name).write_text((TOOLS / name).read_text().replace(
                '/scratch/jjyeung/orch_n30', str(self.local)) if name == 'lane_code_sync.sh'
                else (TOOLS / name).read_text())
        write(self.b / 'briefs' / 'brief.md', 'brief')
        # Use the real wrapper, relocating its lock and removing only its 35 s rate delay.
        wrapper = (TOOLS / 'tssh.sh').read_text()
        wrapper = wrapper.replace('L=/scratch/jjyeung/.tssh_$(hostname -s)',
                                  'L=' + shlex.quote(str(self.root / 'tssh')))
        write(self.b / 'tools' / 'tssh.sh', wrapper.replace('last + 35', 'last + 0'))
        write(self.bin / 'ssh_impl.py', FAKE_SSH)
        write(self.bin / 'git_impl.py', FAKE_GIT)
        for command in ('ssh', 'git'):
            write(self.bin / command, '#!/bin/bash\nexec ' + shlex.quote(sys.executable) +
                  ' -I -s -B ' + shlex.quote(str(self.bin / (command + '_impl.py'))) + ' \"$@\"\n', True)
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

