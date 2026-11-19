"""Run with run_all.sh. Every fixture and bare Git remote stays in work/tmp_*.

The tssh fixture changes only its hardcoded lock-directory assignment. Fake ssh
executes remote filter programs locally and routes .ib receivers to local slots.
No installed tool, network connection, or production state is used.
"""
from datetime import datetime, timedelta
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
L = PACKAGE.parent
INPUT = L / 'in' / 'tools'
SUITE = Path(tempfile.mkdtemp(prefix='tmp_syncmove_', dir=str(L / 'work')))
NOW = '2026-11-19T21:00:00Z'


def run(args, env, cwd=None):
    return subprocess.run([str(a) for a in args], env=env, cwd=str(cwd or SUITE),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          universal_newlines=True, timeout=90)


def write(path, text, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if mode is not None:
        path.chmod(mode)


def fixture(name, changed=True, host='trinity-3-30', init=True):
    root = SUITE / name
    root.mkdir()
    for sub in ('bin', 'B/tools', 'B/briefs', 'state', 'events', 'lanes/e_probe',
                'remote/trinity-1-18/e_probe', 'remote/trinity-2-28/e_probe',
                'remote/trinity-3-30/e_probe'):
        (root / sub).mkdir(parents=True)
    for src in INPUT.iterdir():
        shutil.copyfile(str(src), str(root / 'B/tools' / src.name))
    # Both comparison sides see the same inventory, including the new wrapper.
    shutil.copyfile(str(PACKAGE / 'tools/lane_code_sync_loop.sh'),
                    str(root / 'B/tools/lane_code_sync_loop.sh'))
    if changed:
        for src in (PACKAGE / 'tools').iterdir():
            shutil.copyfile(str(src), str(root / 'B/tools' / src.name))
    tssh = root / 'B/tools/tssh.sh'
    tssh.write_text(tssh.read_text().replace('L=/scratch/jjyeung/.tssh_', 'L=$TEST_ROOT/tssh_'))
    for name in ('hostname', 'ssh', 'git', 'bash', 'date', 'sleep'):
        path = root / 'bin' / name
        write(path, '#!/bin/bash\nexec ' + sys.executable + ' -I -s -B ' +
              str(PACKAGE / 'tests/fake_command.py') + ' "$0" "$@"\n', 0o755)
    write(root / 'bin/python3', '#!/bin/bash\nexec ' + sys.executable + ' "$@"\n', 0o755)
    write(root / 'state/LCS_ROBUST_SYNC', '1\n')
    write(root / 'state/LCS_ROBUST_BUDGETS', (L / 'in/LCS_ROBUST_BUDGETS').read_text())
    write(root / 'lanes/e_probe/local.py', 'answer = 28\n')
    for node in ('trinity-1-18', 'trinity-2-28', 'trinity-3-30'):
        write(root / 'remote' / node / 'e_probe/remote.py', 'node = %r\n' % node)
    write(root / 'B/briefs/brief.md', 'A local synthetic lane.\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('LCS_', 'GIT_', 'FAKE_', 'TEST_'))}
    env.update(PATH=str(root / 'bin') + ':/usr/bin:/bin', TEST_ROOT=str(root), TEST_SUITE_ROOT=str(SUITE),
               FAKE_HOST=host, FAKE_DATE=NOW, LCS_B=str(root / 'B'), LCS_S=str(root / 'state'),
               LCS_EV=str(root / 'events'), LCS_LANES_ROOT=str(root / 'lanes'),
               CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', GIT_ALLOW_PROTOCOL='file',
               GIT_TERMINAL_PROMPT='0', GIT_SSH_COMMAND='/bin/false',
               GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
               GIT_AUTHOR_DATE=NOW, GIT_COMMITTER_DATE=NOW)
    if init:
        for sub in ('origin.git', 'home.git'):
            p = run(['/usr/bin/git', 'init', '--bare', root / sub], env)
            assert p.returncode == 0, p.stdout
        repo = root / 'state/repo'
        for args in (['init', str(repo)], ['-C', str(repo), 'checkout', '-b', 'lane-code'],
                     ['-C', str(repo), 'config', 'gc.auto', '0'],
                     ['-C', str(repo), 'commit', '--allow-empty', '-m', 'seed'],
                     ['-C', str(repo), 'branch', 'main'],
                     ['-C', str(repo), 'remote', 'add', 'origin', str(root / 'origin.git')],
                     ['-C', str(repo), 'remote', 'add', 'home', str(root / 'home.git')]):
            p = run(['/usr/bin/git'] + args, env)
            assert p.returncode == 0, p.stdout
    return root, env


def queue_fixture(root, env):
    clone = root / 'lanes/e_queue/clone'
    clone.parent.mkdir()
    commands = [
        ['clone', '--no-hardlinks', str(root / 'state/repo'), str(clone)],
        ['-C', str(clone), 'checkout', '-b', 'eff/probe'],
        ['-C', str(clone), 'config', 'gc.auto', '0'],
    ]
    for args in commands:
        p = run(['/usr/bin/git'] + args, env)
        assert p.returncode == 0, p.stdout
    write(clone / 'probe.py', 'queued = True\n')
    for args in (['add', 'probe.py'], ['commit', '-m', 'queued fixture']):
        p = run(['/usr/bin/git', '-C', clone] + args, env)
        assert p.returncode == 0, p.stdout
    head = run(['/usr/bin/git', '-C', clone, 'rev-parse', 'HEAD'], env).stdout.strip()
    write(clone.parent / 'PUSH_QUEUE.txt', NOW + ' eff/probe ' + head + ' ' + str(clone) + '\n')


class SyncMove(unittest.TestCase):
    def driver(self, root, env, *args):
        p = run(['/bin/bash', root / 'B/tools/lane_code_sync.sh'] + list(args), env)
        write(root / 'driver.log', p.stdout)
        return p

    def assert_ok(self, p):
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_01_default_programs_and_commands_identical(self):
        root, env = fixture('default', changed=False)
        queue_fixture(root, env)
        p = self.driver(root, env)
        self.assert_ok(p)
        self.assertIn('QUEUE pushed eff/probe', p.stdout)
        programs = {str(p.relative_to(root)): p.read_bytes()
                    for p in (root / 'state/stage-robust').rglob('program.sh')}
        commands = (root / 'commands.jsonl').read_bytes()
        # Recreate at exactly the same paths so comparisons require no normalization.
        saved = root.with_name('default_input_saved')
        root.rename(saved)
        root, env = fixture('default', changed=True)
        queue_fixture(root, env)
        p = self.driver(root, env)
        self.assert_ok(p)
        actual = {str(p.relative_to(root)): p.read_bytes()
                  for p in (root / 'state/stage-robust').rglob('program.sh')}
        self.assertEqual(programs, actual)
        self.assertEqual(commands, (root / 'commands.jsonl').read_bytes())
        self.assertEqual(len(programs), 5)
        records = [json.loads(line) for line in commands.splitlines()]
        counts = {name: sum(row[0] == name for row in records) for name in ('git', 'ssh', 'bash')}
        print('MEASURED default: %d program.sh files; command counts %s; byte-identical' % (len(programs), counts))

    def test_02_moved_full_push_heartbeat_and_health(self):
        root, env = fixture('moved', host='trinity-2-28')
        heartbeat = root / 'heartbeat.log'
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(heartbeat))
        p = self.driver(root, env)
        self.assert_ok(p)
        self.assertIn('END ok', p.stdout)
        programs = root / 'state/stage-robust'
        for node in ('trinity-1-18', 'trinity-3-30'):
            script = (programs / node / 'program.sh').read_text()
            self.assertIn('BatchMode=yes trinity-2-28.ib ', script)
        local = (programs / 'trinity-2-28/program.sh').read_text()
        self.assertNotIn(' ssh ', local)
        self.assertIn('cd ' + str(root / 'lanes'), local)
        calls = [json.loads(line) for line in (root / 'commands.jsonl').read_text().splitlines()]
        self.assertEqual([row[1][1] for row in calls if row[0] == 'bash'], ['trinity-1-18', 'trinity-3-30'])
        repo = root / 'state/repo'
        head = run(['/usr/bin/git', '-C', repo, 'rev-parse', 'HEAD'], env).stdout.strip()
        for remote in ('origin.git', 'home.git'):
            remote_head = run(['/usr/bin/git', '-C', root / remote, 'rev-parse', 'lane-code'], env)
            self.assertEqual(remote_head.stdout.strip(), head)
        for node, filename in (('trinity-1-18', 'remote.py'), ('trinity-2-28', 'local.py'), ('trinity-3-30', 'remote.py')):
            self.assertTrue((repo / 'lane_code' / node / 'e_probe' / filename).is_file())
        expected = [line for line in p.stdout.splitlines() if any(x in line for x in
                    (' START ', ' verified GitHub lane-code = ', ' END '))]
        lines = heartbeat.read_text().splitlines()
        self.assertEqual(lines[:-1], expected)
        self.assertEqual(lines[-1], NOW + ' HOST trinity-2-28')
        self.assertEqual(len(lines), 4)
        healthenv = dict(env, LCS_TEST_ROOT=str(root), LCS_LOG=str(heartbeat),
                         LCS_ENABLE_SYNC_HEALTH='1', LCS_REVIEW2_FIXES='1', LCS_HEALTH_NOW=NOW)
        command = [sys.executable, '-I', '-s', '-B', INPUT / 'sync_health.py']
        health = run(command, healthenv)
        self.assert_ok(health)
        self.assertIn('HEALTH last_verified=' + NOW + ' active=none', health.stdout)
        print('HEALTH fresh: ' + health.stdout.strip())
        healthenv['LCS_HEALTH_NOW'] = '2026-11-19T22:30:00Z'
        health = run(command, healthenv)
        self.assert_ok(health)
        self.assertIn('active=none', health.stdout)
        print('HEALTH at 90m: ' + health.stdout.strip())
        healthenv['LCS_HEALTH_NOW'] = '2026-11-19T22:30:01Z'
        health = run(command, healthenv)
        self.assert_ok(health)
        self.assertIn('active=stale', health.stdout)
        self.assertEqual(len(list((root / 'events').glob('*_BLOCKER_code_sync_stale.md'))), 1)
        print('HEALTH at 90m+1s: ' + health.stdout.strip())

    def test_03_failure_heartbeat_and_retention(self):
        root, env = fixture('failure', host='trinity-2-28')
        heartbeat = root / 'heartbeat.log'
        old = ['old line %d\n' % i for i in range(350)]
        write(heartbeat, ''.join(old))
        old_inode = heartbeat.stat().st_ino
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(heartbeat),
                   FAKE_REMOTE_MODES=json.dumps({'trinity-3-30': 'badpipe'}))
        p = self.driver(root, env)
        self.assertEqual(p.returncode, 1, p.stdout)
        lines = heartbeat.read_text().splitlines(True)
        self.assertEqual(lines[:300], old[-300:])
        self.assertIn(NOW + ' END with failures\n', lines)
        self.assertEqual(lines[-1], NOW + ' HOST trinity-2-28\n')
        self.assertEqual(len(lines), 304)
        self.assertNotEqual(old_inode, heartbeat.stat().st_ino)
        self.assertEqual(list(root.glob('.lcs-heartbeat-*')), [])
        self.assertIn(' END with failures\n', p.stdout)
        self.assertTrue(list((root / 'events').glob('*_BLOCKER_sync_failed.md')))
        print('MEASURED heartbeat retention: 300 old + 4 current = %d lines' % len(lines))

    def test_04_wrong_and_forbidden_hosts_all_entrypoints(self):
        root, env = fixture('hosts', init=False)
        tools = root / 'B/tools'
        land = [sys.executable, '-I', '-s', '-B', tools / 'land_kit.py', 'unused.tar', 'seal', 'a' * 64,
                'review.md', 'probe', '--builder', 'builder', '--reviewer', 'reviewer']
        commands = [['/bin/bash', tools / name] for name in
                    ('lane_code_sync.sh', 'lane_code_stage.sh', 'lane_code_sync_loop.sh')] + [land]
        hosts = ['trinity', 'trinity-2-18', 'trinity-0-8', 'trinity-0-18', 'trinity-0-23',
                 'trinity-3-23', 'bad', 'trinity-2-28.ib', 'trinity-2-28;echo nope', 'trinity-1-18']
        for host in hosts:
            e = dict(env, LCS_HOST=host, LCS_ENABLE_KIT_LANDING='1', LCS_TEST_ROOT=str(root))
            for command in commands:
                p = run(command, e)
                self.assertEqual(p.returncode, 2, (host, command, p.stdout))
                self.assertTrue(any(w in p.stdout for w in ('LCS_HOST', 'only on', 'not on')), p.stdout)
        print('MEASURED host refusals: %d checks' % (len(hosts) * len(commands)))

    def test_05_legacy_moved_refused_and_early_heartbeat(self):
        root, env = fixture('legacy', host='trinity-2-28', init=False)
        (root / 'state/LCS_ROBUST_SYNC').rename(root / 'state/robust.saved')
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(root / 'heartbeat'))
        p = self.driver(root, env)
        self.assertEqual(p.returncode, 2)
        self.assertIn('legacy staging requires LCS_HOST=trinity-3-30', p.stdout)
        self.assertIn(NOW + ' END with failures', (root / 'heartbeat').read_text())
        env['LCS_HOST'] = 'trinity-3-30'
        p = self.driver(root, env)
        self.assertEqual(p.returncode, 2)
        self.assertIn('FAIL not on trinity-3-30', p.stdout)
        self.assertIn(NOW + ' HOST trinity-3-30', (root / 'heartbeat').read_text())

    def test_06_remote_skip_scope_and_override(self):
        root, env = fixture('skip', host='trinity-2-28')
        env.update(LCS_HOST='trinity-2-28', FAKE_REMOTE_MODES=json.dumps({'trinity-3-30': 'missing'}))
        p = self.driver(root, env, '--dry')
        self.assert_ok(p)
        self.assertIn('SKIP trinity-3-30 (no source root)', p.stdout)
        # A direct finish harness covers every code without additional full syncs.
        write(root / 'finish.sh', '''source "$LCS_B/tools/lane_code_stage.sh" || exit $?
log() { echo "$*"; }
fail() { echo "FAILED $*"; }
RUN="$TEST_ROOT/finish"
DRY=1
mkdir -p "$RUN/$LABEL"
printf '%s\\n' "$SNAPSHOT" > "$RUN/$LABEL/run.log"
robust_finish "$LABEL" "$RC" "$REMOTE"
''')
        for node in ('trinity-1-18', 'trinity-2-28', 'trinity-3-30', 'trinity-4-9'):
            e = dict(env, LABEL=node, RC='66', REMOTE='1', SNAPSHOT='SKIP ' + node + ' no orch_n30/source')
            p = run(['/bin/bash', root / 'finish.sh'], e)
            self.assertIn('SKIP ' + node + ' (no source root)', p.stdout)
            for rc in ('124', '137', '255'):
                for remote in ('0', '1'):
                    e.update(RC=rc, REMOTE=remote, SNAPSHOT='')
                    p = run(['/bin/bash', root / 'finish.sh'], e)
                    want = 'SKIP' if node == 'trinity-2-28' and remote == '1' else 'FAILED'
                    self.assertTrue(any(line.startswith(want) for line in p.stdout.splitlines()), p.stdout)
        env['LCS_REMOTE_NODES'] = 'trinity-3-30'
        p = self.driver(root, env, '--dry')
        self.assert_ok(p)
        self.assertNotIn('ROBUST stage trinity-1-18', p.stdout)

    def test_07_heartbeat_failure_does_not_change_run_status(self):
        root, env = fixture('heartbeat_error', host='trinity-2-28')
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(root / 'absent/heartbeat'))
        p = self.driver(root, env, '--queue-only')
        self.assert_ok(p)
        self.assertIn('WARN heartbeat write failed', p.stdout)
        self.assertIn('END ok', p.stdout)

    def test_08_loop_signal_exit_and_hourly_sleep(self):
        root, env = fixture('loop', host='trinity-2-28', init=False)
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(root / 'heartbeat'), FAKE_SLEEP_RC='7')
        driver = root / 'B/tools/lane_code_sync.sh'
        write(driver, 'echo "driver $LCS_HOST $LCS_HEARTBEAT"\nexit 143\n')
        p = run(['/bin/bash', root / 'B/tools/lane_code_sync_loop.sh'], env)
        self.assertEqual(p.returncode, 143, p.stdout)
        text = (root / 'state/sync.log').read_text()
        self.assertEqual(text.count('driver trinity-2-28'), 1)
        self.assertIn('STOP driver signal exit rc=143', text)
        self.assertFalse((root / 'commands.jsonl').exists())
        write(driver, 'echo ordinary_failure\nexit 1\n')
        p = run(['/bin/bash', root / 'B/tools/lane_code_sync_loop.sh'], env)
        self.assertEqual(p.returncode, 7, p.stdout)
        self.assertEqual(json.loads((root / 'commands.jsonl').read_text()), ['sleep', ['3600']])
        self.assertNotIn('export ', (PACKAGE / 'tools/lane_code_sync_loop.sh').read_text())

    def test_09_install_rollback_and_lock(self):
        root, env = fixture('install', changed=False, init=False)
        # fixture() includes the loop for command comparisons; installation must add it.
        (root / 'B/tools/lane_code_sync_loop.sh').rename(root / 'saved_loop.sh')
        env.update(B=str(root / 'B'), S=str(root / 'state'))
        command = ['/bin/bash', PACKAGE / 'install.sh']
        p = run(command, dict(env, FAKE_HOST='trinity-2-28'))
        self.assertEqual(p.returncode, 2)
        with (root / 'state/.sync.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            p = run(command, env)
            self.assertEqual(p.returncode, 3, p.stdout)
            self.assertIn('holds the lock', p.stdout)
        write(root / 'B/tools/lane_code_sync_loop.sh', 'existing\n')
        p = run(command, env)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn('new helper already exists', p.stdout)
        (root / 'B/tools/lane_code_sync_loop.sh').rename(root / 'existing_loop.saved')
        before = {p.name: p.read_bytes() for p in (root / 'B/tools').iterdir()}
        p = run(command, env)
        write(root / 'install.log', p.stdout)
        self.assert_ok(p)
        self.assertIn('robust flag and budgets unchanged', p.stdout)
        for src in (PACKAGE / 'tools').iterdir():
            self.assertEqual((root / 'B/tools' / src.name).read_bytes(), src.read_bytes())
        for name in ('lane_code_filter.py', 'dry_count.py', 'sync_health.py', 'sync_health_loop.sh', 'land_kit.sh'):
            self.assertEqual((root / 'B/tools' / name).read_bytes(), before[name])
        self.assertEqual((root / 'state/LCS_ROBUST_SYNC').read_text(), '1\n')
        backups = list((root / 'state/install-backups').iterdir())
        self.assertEqual(len(backups), 1)
        p = run(command, env)
        self.assertEqual(p.returncode, 2)
        with (root / 'state/.sync.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            p = run(['/bin/bash', PACKAGE / 'rollback.sh', backups[0]], env)
            self.assertEqual(p.returncode, 3, p.stdout)
        p = run(['/bin/bash', PACKAGE / 'rollback.sh', backups[0]], env)
        write(root / 'rollback.log', p.stdout)
        self.assert_ok(p)
        for name, data in before.items():
            self.assertEqual((root / 'B/tools' / name).read_bytes(), data)
        self.assertFalse((root / 'B/tools/lane_code_sync_loop.sh').exists())
        self.assertEqual(len(list((root / 'B/tools').glob('.lane_code_sync_loop.sh.rollback-*'))), 1)
        self.assertEqual((root / 'state/LCS_ROBUST_BUDGETS').read_bytes(), (L / 'in/LCS_ROBUST_BUDGETS').read_bytes())

    def test_10_input_integrity_and_syntax(self):
        for line in (L / 'in/TOOLS.sha256').read_text().splitlines():
            sha, name = line.split()
            self.assertEqual(hashlib.sha256((INPUT / name).read_bytes()).hexdigest(), sha)
        for p in (PACKAGE / 'tools').iterdir():
            if p.suffix == '.sh':
                self.assertEqual(subprocess.call(['/bin/bash', '-n', str(p)]), 0)
            else:
                compile(p.read_bytes(), str(p), 'exec')
        compile((PACKAGE / 'install_tools.py').read_bytes(), 'install_tools.py', 'exec')

    def test_11_legacy_default_generator_and_command_text_unchanged(self):
        old = (INPUT / 'lane_code_sync.sh').read_text()
        new = (PACKAGE / 'tools/lane_code_sync.sh').read_text()
        def legacy(text):
            return text.split('# Remote script:', 1)[1].split('\nfi\n[ $DRY', 1)[0]
        self.assertEqual(legacy(old), legacy(new))
        # This also covers queue refusal/failure branches that the successful fixture does not take.
        def commands(text):
            return [line for line in text.splitlines() if any(word in line for word in
                    ('git -C ', ' ssh ', 'tssh.sh'))]
        self.assertEqual(commands(old), commands(new))
        print('LEGACY: generator/staging block and every driver Git/SSH/tssh source line byte-identical')

    def test_12_heartbeat_for_lock_and_stage_only(self):
        root, env = fixture('early', host='trinity-2-28')
        heartbeat = root / 'heartbeat'
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(heartbeat))
        with (root / 'state/.sync.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            p = self.driver(root, env)
            self.assertEqual(p.returncode, 3, p.stdout)
        self.assertEqual(heartbeat.read_text().splitlines(), [
            NOW + ' FAIL previous run still holds the lock', NOW + ' HOST trinity-2-28'])
        self.assertEqual(p.stdout, NOW + ' FAIL previous run still holds the lock\n')
        p = self.driver(root, env, '--stage-only')
        self.assert_ok(p)
        self.assertIn('STAGE-ONLY done', p.stdout)
        self.assertEqual(heartbeat.read_text().splitlines()[-3:], [
            NOW + ' START dry=0 queue_only=0', NOW + ' END ok', NOW + ' HOST trinity-2-28'])

    def test_14_lock_skip_health_matches_sync_log(self):
        root, env = fixture('lock_health', host='trinity-2-28', init=False)
        heartbeat = root / 'heartbeat.log'
        history = (NOW + ' START dry=0 queue_only=0\n' + NOW +
                   ' verified GitHub lane-code = ' + 'a' * 40 + '\n' + NOW + ' END ok\n')
        write(heartbeat, history)
        skip_time = '2026-11-19T22:00:00Z'
        env.update(LCS_HOST='trinity-2-28', LCS_HEARTBEAT=str(heartbeat), FAKE_DATE=skip_time)
        with (root / 'state/.sync.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            hb_run = self.driver(root, env)
            plain_env = dict(env)
            plain_env.pop('LCS_HEARTBEAT')
            plain_run = self.driver(root, plain_env)
        self.assertEqual(hb_run.returncode, 3, hb_run.stdout)
        self.assertEqual(plain_run.returncode, 3, plain_run.stdout)
        sync_log = root / 'sync.log'
        write(sync_log, history + plain_run.stdout)
        command = [sys.executable, '-I', '-s', '-B', INPUT / 'sync_health.py']
        for now, expected in ((skip_time, 'none'), ('2026-11-19T22:30:01Z', 'stale')):
            verdicts, events = [], []
            for label, log in (('heartbeat', heartbeat), ('sync', sync_log)):
                monitor = root / ('monitor_' + label)
                healthenv = dict(env, LCS_TEST_ROOT=str(root), LCS_LOG=str(log),
                                 LCS_S=str(monitor), LCS_EV=str(monitor / 'events'),
                                 LCS_ENABLE_SYNC_HEALTH='1', LCS_REVIEW2_FIXES='1',
                                 LCS_HEALTH_NOW=now)
                p = run(command, healthenv)
                self.assert_ok(p)
                verdicts.append([line for line in p.stdout.splitlines() if line.startswith('HEALTH ')])
                events.append({p.name: p.read_text().replace(str(log), '<log>')
                               for p in (monitor / 'events').glob('*.md')})
            print('LOCK HEALTH %s: heartbeat=%s; sync.log=%s' %
                  (now, verdicts[0], verdicts[1]))
            self.assertEqual(verdicts[0], verdicts[1])
            self.assertEqual(verdicts[0], ['HEALTH last_verified=' + NOW + ' active=' + expected])
            self.assertEqual(events[0], events[1])
            self.assertFalse(any('code_sync_failed' in name for name in events[0]))
            if expected == 'stale':
                self.assertEqual(len(events[0]), 1)
                self.assertIn('Latest hourly lock skip: ' + skip_time +
                              ' FAIL previous run still holds the lock', next(iter(events[0].values())))
        self.assertEqual(hb_run.stdout, plain_run.stdout)
        self.assertEqual(heartbeat.read_text(), history + plain_run.stdout +
                         skip_time + ' HOST trinity-2-28\n')

    def test_15_hostname_failure_refuses_without_traceback(self):
        root, env = fixture('hostname_failure', init=False)
        env.update(FAKE_HOSTNAME_RC='7', LCS_ENABLE_KIT_LANDING='1', LCS_TEST_ROOT=str(root))
        p = run([sys.executable, '-I', '-s', '-B', root / 'B/tools/land_kit.py',
                 'missing.tar', 'seal', 'a' * 64, 'missing.md', 'probe',
                 '--builder', 'builder', '--reviewer', 'reviewer'], env)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn('REFUSED: hostname -s failed', p.stdout)
        self.assertNotIn('Traceback', p.stdout)
        self.assertFalse((root / 'state/.sync.lock').exists())
        print('HOSTNAME FAILURE: ' + p.stdout.strip())

    def test_16_documented_bundle_restore_preserves_config_and_main(self):
        document = (PACKAGE / 'GIT_OWNER_patch.md').read_text()
        restore = document.split('# BEGIN bundle restore\n', 1)[1].split('# END bundle restore', 1)[0]
        for case in ('remote_only_main', 'local_main', 'missing_main'):
            root, env = fixture('bundle_' + case)
            source = root / 'state/repo'
            def git(*args):
                p = run(['/usr/bin/git', '-C', source] + list(args), env)
                self.assert_ok(p)
                return p.stdout.strip()
            git('config', 'user.name', 'Preserved Owner')
            git('config', 'user.email', 'preserved@example.invalid')
            git('push', 'origin', 'main')
            # Move, rather than delete, the local main ref to model a lane-only clone.
            if case != 'local_main':
                git('branch', '-m', 'main', 'preserved-main')
            if case != 'remote_only_main':
                # Keep its contents under another ref while main is absent from origin/*.
                ref = source / '.git/refs/remotes/origin/main'
                ref.rename(ref.with_name('main.saved'))
            head = git('rev-parse', 'HEAD')
            destination = root / 'destination'
            destination.mkdir()
            config = destination / 'transfer-state/repo/.git/config'
            config.parent.mkdir(parents=True)
            shutil.copyfile(str(source / '.git/config'), str(config))
            bundle = destination / 'clone.bundle'
            with bundle.open('wb') as stream:
                p = subprocess.run(['/usr/bin/git', '-C', str(source), 'bundle', 'create', '-', '--all'],
                                   env=env, cwd=str(root), stdout=stream, stderr=subprocess.PIPE,
                                   universal_newlines=True, timeout=90)
            self.assertEqual(p.returncode, 0, p.stderr)
            p = run(['/bin/bash', '-c', restore], dict(env, S=str(destination)))
            self.assert_ok(p)
            repo = destination / 'repo'
            self.assertEqual((repo / '.git/config').read_bytes(), config.read_bytes())
            p = run(['/usr/bin/git', '-C', repo, 'rev-parse', 'refs/remotes/origin/main'], env)
            self.assert_ok(p)
            self.assertEqual(p.stdout.strip(), head)
            calls = [json.loads(line) for line in (root / 'commands.jsonl').read_text().splitlines()]
            fetches = [args for name, args in calls if name == 'git' and 'fetch' in args]
            self.assertEqual(len(fetches), 1)
            remote = fetches[0][fetches[0].index('fetch') + 1]
            self.assertEqual(remote, 'origin' if case == 'missing_main' else str(bundle))
            print('BUNDLE %s: config byte-identical; origin/main=%s; fetch=%s' %
                  (case, head, 'origin' if remote == 'origin' else 'local bundle'))

    def test_17_owner_procedure_requirements(self):
        document = (PACKAGE / 'GIT_OWNER_patch.md').read_text()
        failover = document.split('### If the sync host fails\n', 1)[1].splitlines()
        self.assertEqual(len(failover), 3)
        self.assertEqual([line[:3] for line in failover], ['1. ', '2. ', '3. '])
        for required in ('Consumers may move delivered events; only undelivered events replay.',
                         '$B/code_sync_heartbeat/HEARTBEAT.log', 'git -C "$S/repo" bundle create - --all',
                         'bash "$B/tools/tssh.sh" "$NEW.ib"',
                         'ssh -o BatchMode=yes <new>.ib true',
                         'git -C "$S/repo" fetch origin lane-code && git -C "$S/repo" merge --ff-only FETCH_HEAD',
                         'Only after this heartbeat shows its first', 'empty `/scratch/jjyeung/orch_n30`',
                         '18 MB/s', '--dry'):
            self.assertIn(required, document)
        self.assertNotIn('--single-branch', document)
        self.assertNotIn('reset --hard', document)
        self.assertNotIn('$B/events/code_sync/lane_code_heartbeat.log', document)

    def test_13_installer_preimage_checksum_and_syntax_refusals(self):
        root, env = fixture('install_refusals', changed=False, init=False)
        (root / 'B/tools/lane_code_sync_loop.sh').rename(root / 'saved_loop.sh')
        env.update(B=str(root / 'B'), S=str(root / 'state'))
        command = ['/bin/bash', PACKAGE / 'install.sh']
        tool = root / 'B/tools/lane_code_sync.sh'
        before = tool.read_bytes()
        tool.write_bytes(before + b'\n# changed installed file\n')
        p = run(command, env)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn('preimage/postimage mismatch', p.stdout)
        self.assertFalse((root / 'state/install-backups').exists())
        tool.write_bytes(before)
        # Prepare a separate package copy entirely inside the test fixture.
        package = root / 'package'
        shutil.copytree(str(PACKAGE), str(package))
        changed = package / 'tools/lane_code_sync.sh'
        changed.write_bytes(changed.read_bytes() + b'\nif then\n')
        command = ['/bin/bash', package / 'install.sh']
        p = run(command, env)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn('FAILED', p.stdout)
        self.assertFalse((root / 'state/install-backups').exists())
        # A self-consistent package with broken shell syntax must stage nothing live.
        post = package / 'POSTIMAGE.sha256'
        post.write_text(''.join(hashlib.sha256((package / name).read_bytes()).hexdigest() +
                               '  ' + name + '\n' for _, name in
                               (line.split() for line in post.read_text().splitlines())))
        sums = package / 'SHA256SUMS'
        sums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
                               str(p.relative_to(package)) + '\n' for p in sorted(package.rglob('*'))
                               if p.is_file() and p != sums))
        prior = {p.name: p.read_bytes() for p in (root / 'B/tools').iterdir()}
        p = run(command, env)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn('syntax error', p.stdout)
        for name, data in prior.items():
            self.assertEqual((root / 'B/tools' / name).read_bytes(), data)
        self.assertFalse((root / 'B/tools/lane_code_sync_loop.sh').exists())
        backups = list((root / 'state/install-backups').iterdir())
        self.assertEqual(len(backups), 1)
        # Rollback is safe even if installation stopped before any replacement.
        p = run(['/bin/bash', PACKAGE / 'rollback.sh', backups[0]], env)
        self.assert_ok(p)


if __name__ == '__main__':
    print('INTERPRETER: ' + sys.version.split()[0], flush=True)
    print('FIXTURES: ' + str(SUITE), flush=True)
    unittest.main(verbosity=2)
