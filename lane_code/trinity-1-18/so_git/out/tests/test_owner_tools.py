from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
TOOLS = BASE / 'tools'
FIXTURES = Path(os.environ.get('LCS_TEST_WORK', str(BASE / 'work' / 'test_runs')))
FIXTURES.mkdir(parents=True, exist_ok=True)


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kit = load('land_kit')
health = load('sync_health')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix=self.__class__.__name__ + '_', dir=FIXTURES))
        self.state = self.root / 'state'
        self.state.mkdir()
        self.repo = self.state / 'repo'
        self.repo.mkdir()
        self.events = self.root / 'events'
        self.events.mkdir()
        self.log = self.state / 'sync.log'
        self.review = self.root / 'review.md'
        self.review.write_text('VERDICT: GO\n')
        self.env = dict(LCS_ENABLE_KIT_LANDING='1', LCS_ENABLE_SYNC_HEALTH='1',
                        LCS_ENABLE_DRY_COUNT='1', LCS_S=str(self.state), LCS_R=str(self.repo),
                        LCS_EV=str(self.events), LCS_FILTER=str(TOOLS / 'lane_code_filter.py'),
                        LCS_SCAN=str(TOOLS / 'lane_code_scan.py'), LCS_TEST_ROOT=str(self.root),
                        LCS_LOCK_TIMEOUT='0.05')
        self.archive({'module.py': b'VALUE = 1\n', 'in/helper.py': b'VALUE = 2\n'})

    def archive(self, files=None, members=None):
        p = self.root / f'kit_{len(list(self.root.glob("kit_*.tar")))}.tar'
        with tarfile.open(p, 'w') as tf:
            for name, data in (files or {}).items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                member.mode = 0o755 if name.endswith('.sh') else 0o644
                tf.addfile(member, io.BytesIO(data))
            for member in members or []:
                tf.addfile(member)
        self.tar = p
        self.sha = hashlib.sha256(p.read_bytes()).hexdigest()
        return p

    def invoke(self, dry=True, sha=None, name='_probe', extra=()):

        argv = [str(self.tar), 'seal-test', sha or self.sha, str(self.review), name,
                '--builder', 'lane_builder', '--reviewer', 'lane_reviewer', '--bind-sha', self.sha]
        argv.extend(extra)
        if dry:
            argv.append('--dry')
        with patch.dict(os.environ, self.env), redirect_stdout(io.StringIO()) as out:
            code = kit.main(argv)
        return code, out.getvalue()

    def check(self, now):
        with redirect_stdout(io.StringIO()):
            health.check(self.state, self.events, self.log, now)


class ReviewTests(unittest.TestCase):
    def review(self, text, bind_sha='a' * 64):
        return kit.review(text.encode(), 's', 'a' * 64, bind_sha)

    def test_supported_forms(self):
        for text in ('VERDICT: GO', 'VERDICT: ACCEPT', 'VERDICT: ACCEPT WITH FINDINGS',
                     '\n\nVERDICT: GO\nFindings: none'):
            with self.subTest(text=text):
                self.assertTrue(self.review(text)[1]['checked'])

    def test_first_nonempty_line_must_be_unindented_verdict(self):
        for text in ('GO', 'ACCEPT', '**VERDICT: ACCEPT**', '# VERDICT: GO',
                     'Builder: b\nVERDICT: GO', '    VERDICT: GO', 'We should GO',
                     '> VERDICT: GO', '```\nVERDICT: GO\n```', ''):
            with self.subTest(text=text), self.assertRaises(kit.Refusal):
                self.review(text)

    def test_conditional_even_with_later_same_file_go_is_refused(self):
        for tail in ('Fixes recorded: all done', 'VERDICT: GO', 'VERDICT: ACCEPT'):
            with self.subTest(tail=tail), self.assertRaises(kit.Refusal):
                self.review('VERDICT: GO AFTER FIXES\n' + tail)
        # The owner supplies a separate, later unconditional verdict file.
        self.assertEqual(self.review('VERDICT: GO')[0], 'GO')

    def test_negative_anywhere_is_refused(self):
        for word in ('NO-GO', 'NO GO', 'REJECT', 'no-go', 'reject', 'REJECTED'):
            for text in (f'VERDICT: {word}\nVERDICT: GO',
                         f'VERDICT: {word}\n## Accept',
                         f'VERDICT: {word}\n    VERDICT: GO',
                         f'VERDICT: GO\n```\n{word}\n```'):
                with self.subTest(text=text), self.assertRaises(kit.Refusal):
                    self.review(text)

    def test_unknown_and_later_conditional_verdicts_are_refused(self):
        for text in ('VERDICT: WAIT\nVERDICT: GO', 'VERDICT: GO\nVERDICT: WAIT',
                     'VERDICT: GO\nVERDICT: GO AFTER FIXES'):
            with self.subTest(text=text), self.assertRaises(kit.Refusal):
                self.review(text)

    def test_binding_required_and_all_present_fields_must_match(self):
        self.assertEqual(self.review('VERDICT: GO\nSeal: s', None)[1]['methods'], ['seal'])
        self.assertEqual(self.review('VERDICT: GO\nSHA256: ' + 'a' * 64, None)[1]['methods'], ['sha256'])
        self.assertEqual(self.review('VERDICT: GO')[1]['methods'], ['owner_bind_sha256'])
        for text, bind in (('VERDICT: GO', None), ('VERDICT: GO', 'b' * 64),
                           ('VERDICT: GO\nSeal: wrong', 'a' * 64),
                           ('VERDICT: GO\nSHA256: 123', 'a' * 64),
                           ('VERDICT: GO\nSeal: s\nSeal: other', None)):
            with self.subTest(text=text, bind=bind), self.assertRaises(kit.Refusal):
                self.review(text, bind)


class KitValidationTests(Fixture):
    def test_dry_uses_filter_and_scan_without_git(self):
        with patch.object(kit, 'land', side_effect=AssertionError('Git reached')):
            code, out = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn('COUNT files=2', out)
        self.assertIn('DRY validated', out)
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_disabled_has_no_writes(self):
        self.env['LCS_ENABLE_KIT_LANDING'] = '0'
        with self.assertRaisesRegex(kit.Refusal, 'disabled'):
            self.invoke()
        self.assertFalse((self.state / '.sync.lock').exists())

    def test_builder_and_reviewer_must_differ(self):
        for builder in ('LANE_REVIEWER', ' lane_reviewer '):
            with self.subTest(builder=builder), self.assertRaisesRegex(kit.Refusal, 'must differ'):
                self.invoke(extra=['--builder', builder])
        with self.assertRaisesRegex(kit.Refusal, 'builder must be nonempty'):
            self.invoke(extra=['--builder', ' '])

    def test_production_tool_overrides_refuse_before_tool_reads(self):
        for key in ('LCS_FILTER', 'LCS_SCAN', 'LCS_B', 'LCS_EV'):
            self.env = {'LCS_ENABLE_KIT_LANDING': '1', key: '/nonexistent'}
            with self.subTest(key=key), patch.dict(os.environ, {}, clear=True), \
                 self.assertRaisesRegex(kit.Refusal, 'overrides require LCS_TEST_ROOT'):
                self.invoke()

    def test_default_lock_wait_is_600_seconds(self):
        self.env.pop('LCS_LOCK_TIMEOUT')
        with patch.object(kit, 'owner_lock', wraps=kit.owner_lock) as lock:
            self.invoke()
        self.assertEqual(lock.call_args[0][1], 600)

    def test_bad_hash_and_missing_review(self):
        with self.assertRaisesRegex(kit.Refusal, 'SHA256 mismatch'):
            self.invoke(sha='0' * 64)
        self.review = self.root / 'missing.md'
        with self.assertRaises(FileNotFoundError):
            self.invoke()

    def test_bad_names(self):
        for name in ('../escape', 'UPPER', 'a-b', '', '-x'):
            # Leading option/empty name parsing is covered by the CLI parser itself.
            if name.startswith('-'):
                continue
            with self.subTest(name=name), self.assertRaises(kit.Refusal):
                self.invoke(name=name)

    def test_traversal_absolute_links_and_duplicates_refused(self):
        for name, type_ in (('../escape.py', tarfile.REGTYPE), ('/escape.py', tarfile.REGTYPE),
                            ('x', tarfile.SYMTYPE), ('x', tarfile.LNKTYPE), ('x', tarfile.FIFOTYPE)):
            member = tarfile.TarInfo(name)
            member.type = type_
            member.linkname = 'target'
            self.archive(members=[member])
            with self.subTest(name=name, type=type_), self.assertRaises(kit.Refusal):
                self.invoke()
        self.archive(members=[tarfile.TarInfo('x.py'), tarfile.TarInfo('./x.py')])
        with self.assertRaisesRegex(kit.Refusal, 'duplicate'):
            self.invoke()
        self.assertFalse((self.state / 'escape.py').exists())

    def test_reserved_metadata_and_empty_filter(self):
        self.archive({'KIT.json': b'{}'})
        with self.assertRaisesRegex(kit.Refusal, 'reserved'):
            self.invoke()
        self.archive({'image.bin': b'not source'})
        with self.assertRaisesRegex(kit.Refusal, 'skipped files'):
            self.invoke()

    def test_size_and_name_filter_and_duplicate_paths(self):
        self.archive({'small.py': b'x=1\n', 'same.py': b'x=1\n', 'runs/skip.py': b'run=1\n',
                      'big.py': b'#' * (512 * 1024 + 1), 'big.json': b' ' * (256 * 1024 + 1),
                      'kit/ok.py': b'k=1\n', 'work/tree/ok.sh': b'echo ok\n'})
        with self.assertRaisesRegex(kit.Refusal, 'skipped files'):
            self.invoke()
        _, out = self.invoke(extra=['--allow-skips'])
        self.assertIn('COUNT files=4', out)
        self.assertIn('"same.py"', out)
        self.assertIn('SKIPPED "runs/skip.py"', out)
        self.assertIn('SKIPPED "big.py"', out)
        audit = Path(out.splitlines()[0].split(' ', 1)[1])
        metadata = json.loads((audit / 'payload' / 'KIT.json').read_text())
        self.assertEqual(metadata['skipped'], ['big.json', 'big.py', 'runs/skip.py'])

    def test_all_filter_exclusions_are_reported_and_require_opt_in(self):
        excluded = {'Makefile': b'all:', 'x.c': b'int x;', 'x.js': b'let x;',
                    'kv_cache/source.py': b'cache=1', 'frames/source.py': b'frames=1',
                    'torch/source.py': b'torch=1', 'root/source.py': b'root=1',
                    'evidence/source.py': b'evidence=1'}
        # MAXDIR pruning must report even otherwise eligible code within the directory.
        excluded.update({f'crowded/{i}.py': b'x=1' for i in range(2001)})
        self.archive(dict(excluded, **{'ok.py': b'ok=1'}))
        with self.assertRaisesRegex(kit.Refusal, 'skipped files'):
            self.invoke()
        _, out = self.invoke(extra=['--allow-skips'])
        observed = {json.loads(line[len('SKIPPED '):]) for line in out.splitlines()
                    if line.startswith('SKIPPED ')}
        self.assertEqual(observed, set(excluded))

    def test_empty_archive_directory_is_reported_but_payload_parents_are_preserved(self):
        empty = tarfile.TarInfo('empty')
        empty.type = tarfile.DIRTYPE
        parent = tarfile.TarInfo('package')
        parent.type = tarfile.DIRTYPE
        self.archive({'package/source.py': b'x=1'}, members=[empty, parent])
        with self.assertRaisesRegex(kit.Refusal, 'skipped files'):
            self.invoke()
        _, out = self.invoke(extra=['--allow-skips'])
        self.assertIn('SKIPPED "empty"', out)
        self.assertNotIn('SKIPPED "package"', out)

    def test_git_children_cannot_prompt(self):
        result = subprocess.CompletedProcess(['git'], 0, stdout=b'ok', stderr=b'')
        with patch.object(subprocess, 'run', return_value=result) as spawn:
            self.assertEqual(kit.run(['git', '--version']), b'ok')
        options = spawn.call_args[1]
        self.assertEqual(options['stdin'], subprocess.DEVNULL)
        self.assertEqual(options['env']['GIT_TERMINAL_PROMPT'], '0')

    def test_exact_size_caps_are_inclusive(self):
        self.archive({'at_limit.py': b'#' * (512 * 1024), 'at_limit.json': b' ' * (256 * 1024),
                      'over.py': b'#' * (512 * 1024 + 1), 'over.jsonl': b' ' * (256 * 1024 + 1)})
        _, out = self.invoke(extra=['--allow-skips'])
        self.assertIn('COUNT files=2 bytes=786432', out)
        self.assertIn('SKIPPED "over.py"', out)
        self.assertIn('SKIPPED "over.jsonl"', out)

    def test_shell_wrapper_dry_path(self):
        result = subprocess.run(['bash', str(TOOLS / 'land_kit.sh'), str(self.tar), 'seal-test', self.sha,
                                 str(self.review), '_probe', '--dry', '--builder', 'b', '--reviewer', 'r', '--bind-sha', self.sha],
                                env=dict(os.environ, **self.env, LCS_PYTHON=sys.executable),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRY validated', result.stdout)
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_shell_wrapper_default_system_python(self):
        env = dict(os.environ, **self.env)
        env.pop('LCS_PYTHON', None)
        env['PATH'] = '/usr/bin:/bin'
        result = subprocess.run(['bash', str(TOOLS / 'land_kit.sh'), str(self.tar), 'seal-test', self.sha,
                                 str(self.review), '_probe', '--dry', '--builder', 'b',
                                 '--reviewer', 'r', '--bind-sha', self.sha], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRY validated', result.stdout)

    def test_inherited_git_selector_refused_before_spawn(self):
        with patch.dict(os.environ, GIT_DIR='/not/a/repository'), \
             patch.object(subprocess, 'run', side_effect=AssertionError('must not spawn')), \
             self.assertRaisesRegex(kit.Refusal, 'selector refused'):
            kit.run(['git', '-C', str(self.repo), 'symbolic-ref', '--quiet', '--short', 'HEAD'])

    def test_any_secret_including_filtered_out_file_refuses(self):
        for path in ('secret.py', 'runs/secret.bin'):
            self.archive({path: ('hf_' + 'X' * 35).encode(), 'ok.py': b'x=1'})
            with self.subTest(path=path), self.assertRaisesRegex(kit.Refusal, 'secret scan flagged'):
                self.invoke()

    def test_scanner_error_and_scanner_omission_refuse(self):
        bad = self.root / 'bad_scan.py'
        bad.write_text('raise SystemExit(7)\n')
        self.env['LCS_SCAN'] = str(bad)
        with self.assertRaisesRegex(kit.Refusal, 'command failed'):
            self.invoke()
        bad.write_text('import pathlib,sys\np=pathlib.Path(sys.argv[3]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text("")\n')
        with self.assertRaisesRegex(kit.Refusal, 'scanner omitted'):
            self.invoke()

    def test_shared_flock_timeout(self):
        with (self.state / '.sync.lock').open('a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(kit.Refusal, 'timed out waiting'):
                self.invoke()

    def test_shared_flock_wait_then_acquire(self):
        # A separate process holds a real flock; no Git executable is used.
        ready = self.root / 'locked'
        code = ('import fcntl,pathlib,sys,time\n'
                'with open(sys.argv[1],"a") as f:\n'
                ' fcntl.flock(f,fcntl.LOCK_EX);pathlib.Path(sys.argv[2]).write_text("ready");time.sleep(0.3)\n')
        child = subprocess.Popen([sys.executable, '-I', '-s', '-B', '-c', code, str(self.state / '.sync.lock'), str(ready)])
        import time
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(ready.exists())
        self.env['LCS_LOCK_TIMEOUT'] = '2'
        try:
            self.assertEqual(self.invoke()[0], 0)
        finally:
            self.assertEqual(child.wait(timeout=5), 0)


class FakeGit:
    """Command double only: this is not a Git implementation or Git proof."""
    def __init__(self):
        self.calls = []
        self.head = 'a' * 40
        self.branch = b'lane-code\n'
        self.fail = None
        self.bad_remote = None
        self.original = kit.run

    def __call__(self, argv, **kw):
        if argv[0] != 'git':
            return self.original(argv, **kw)
        self_test_prefix = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C']
        if argv[:6] != self_test_prefix:
            raise AssertionError('Git must disable detached maintenance')
        args = argv[7:]
        self.calls.append(args)
        if self.fail and args[:len(self.fail)] == self.fail:
            raise kit.Refusal('simulated command failure')
        if args[0] == 'symbolic-ref':
            return self.branch
        if args[:2] == ['rev-parse', 'HEAD']:
            return (self.head + '\n').encode()
        if args[0] == 'ls-remote':
            head = 'b' * 40 if args[1] == self.bad_remote else self.head
            return (head + '\trefs/heads/lane-code\n').encode()
        if args[0] == 'ls-files':
            repo = Path(argv[6])
            return b''.join(str(p.relative_to(repo)).encode() + b'\0' for p in sorted((repo / args[-1]).rglob('*')) if p.is_file())
        return b''


class KitCommandTests(Fixture):
    def test_landing_and_idempotence_command_contract(self):
        fake = FakeGit()
        with patch.object(kit, 'run', side_effect=fake):
            self.assertEqual(self.invoke(dry=False)[0], 0)
            self.assertEqual(self.invoke(dry=False)[0], 0)
        path = self.repo / 'kits' / '_probe'
        metadata = json.loads((path / 'KIT.json').read_text())
        self.assertEqual(metadata['file_count'], 2)
        self.assertEqual(metadata['seal'], 'seal-test')
        self.assertEqual(metadata['verdict_sha256'], hashlib.sha256(self.review.read_bytes()).hexdigest())
        self.assertEqual(sum(call[0] == 'commit' for call in fake.calls), 1)
        self.assertEqual(sum(call[0] == 'push' for call in fake.calls), 4)
        for call in fake.calls:
            self.assertNotIn('checkout', call)
            self.assertNotIn('--force', call)
            self.assertNotIn('main', call)
        self.assertIn(['push', '-q', 'origin', 'HEAD:refs/heads/lane-code'], fake.calls)
        self.assertIn(['push', '-q', 'home', 'HEAD:refs/heads/lane-code'], fake.calls)
        receipts = (self.state / 'KITS_LANDED.txt').read_text().splitlines()
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all('commit=' + fake.head in line for line in receipts))
        events = list(self.events.glob('*_RESULT_kit__probe_landed.md'))
        self.assertTrue(events)
        self.assertIn('commit=' + fake.head, events[0].read_text())

    def test_conflicting_name_refuses_without_add(self):
        with patch.object(kit, 'run', side_effect=FakeGit()):
            self.invoke(dry=False)
        self.archive({'different.py': b'y=2\n'})
        fake = FakeGit()
        with patch.object(kit, 'run', side_effect=fake), self.assertRaisesRegex(kit.Refusal, 'different content'):
            self.invoke(dry=False)
        self.assertFalse(any(call[0] in ('add', 'commit', 'push') for call in fake.calls))

    def test_wrong_branch_and_dirty_index_refuse(self):
        fake = FakeGit()
        fake.branch = b'main\n'
        with patch.object(kit, 'run', side_effect=fake), self.assertRaisesRegex(kit.Refusal, 'already be on lane-code'):
            self.invoke(dry=False)
        fake = FakeGit()
        fake.fail = ['diff', '--cached']
        with patch.object(kit, 'run', side_effect=fake), self.assertRaises(kit.Refusal):
            self.invoke(dry=False)
        self.assertFalse(any(call[0] == 'add' for call in fake.calls))

    def test_each_remote_must_verify(self):
        for remote in ('origin', 'home'):
            fake = FakeGit()
            fake.bad_remote = remote
            with patch.object(kit, 'run', side_effect=fake), self.subTest(remote=remote), self.assertRaisesRegex(kit.Refusal, 'verification failed'):
                self.invoke(dry=False)

    def test_failed_push_stops_without_retry(self):
        fake = FakeGit()
        fake.fail = ['push', '-q', 'origin']
        with patch.object(kit, 'run', side_effect=fake), self.assertRaises(kit.Refusal):
            self.invoke(dry=False)
        self.assertEqual(sum(call[0] == 'push' for call in fake.calls), 1)
        self.assertFalse((self.state / 'KITS_LANDED.txt').exists())
        self.assertEqual(list(self.events.glob('*kit*')), [])


class HealthTests(Fixture):
    T = datetime(2026, 11, 19, 1, 0, tzinfo=timezone.utc)

    def write_log(self, good=None, failed=False, end_ok=True):
        good = good or self.T
        lines = [f'{health.iso(good - timedelta(minutes=1))} START dry=0 queue_only=0',
                 f'{health.iso(good)} verified GitHub lane-code = {"a" * 40}']
        if failed:
            lines.append(f'{health.iso(good + timedelta(seconds=1))} END with failures')
        elif end_ok:
            lines.append(f'{health.iso(good + timedelta(seconds=1))} END ok')
        self.log.write_text('\n'.join(lines) + '\n')

    def files(self, pattern):
        return list(self.events.glob(pattern))

    def test_exact_stale_boundary_once_and_recovery(self):
        self.write_log()
        self.check(self.T + timedelta(minutes=90))
        self.assertEqual(self.files('*BLOCKER*'), [])
        self.check(self.T + timedelta(minutes=90, seconds=1))
        self.check(self.T + timedelta(minutes=100))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_stale.md')), 1)
        self.write_log(self.T + timedelta(minutes=101))
        self.check(self.T + timedelta(minutes=102))
        self.check(self.T + timedelta(minutes=103))
        result = self.files('*RESULT*')
        self.assertEqual(len(result), 1)
        self.assertIn('recovered', result[0].read_text())

    def test_failed_without_own_blocker_once_and_recovery(self):
        self.write_log(failed=True)
        self.check(self.T + timedelta(minutes=1))
        self.check(self.T + timedelta(minutes=2))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_failed.md')), 1)
        self.write_log(self.T + timedelta(minutes=3))
        self.check(self.T + timedelta(minutes=4))
        self.assertEqual(len(self.files('*RESULT*')), 1)

    def test_failed_with_own_blocker_is_suppressed(self):
        self.write_log(failed=True)
        (self.events / '20261119T0100Z_BLOCKER_sync_failed.md').write_text(
            f'{health.iso(self.T + timedelta(seconds=1))} code_sync run failed; scan error\n')
        self.check(self.T + timedelta(minutes=1))
        self.assertEqual(self.files('*BLOCKER_code_sync_failed.md'), [])

    def test_unrelated_own_blocker_does_not_suppress(self):
        self.write_log(failed=True)
        (self.events / 'old_BLOCKER_sync_failed.md').write_text('2026-11-18T01:00:01Z code_sync run failed\n')
        self.check(self.T + timedelta(minutes=1))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_failed.md')), 1)

    def test_new_good_push_with_failing_end_does_not_recover_failure(self):
        self.write_log(failed=True)
        self.check(self.T + timedelta(minutes=1))
        self.write_log(self.T + timedelta(minutes=2), failed=True)
        self.check(self.T + timedelta(minutes=3))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_failed.md')), 1)
        self.assertEqual(self.files('*RESULT*'), [])

    def test_missing_log_stale_once(self):
        self.check(self.T)
        self.check(self.T + timedelta(minutes=1))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_stale.md')), 1)

    def test_queue_only_failure_and_hung_run(self):
        self.log.write_text('2026-11-19T01:00:00Z START dry=0 queue_only=1\n2026-11-19T01:00:01Z QUEUE-ONLY END with failures; fetch\n')
        self.check(self.T + timedelta(minutes=1))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_failed.md')), 1)

    def test_incomplete_new_run_does_not_make_failure(self):
        self.write_log()
        with self.log.open('a') as f:
            f.write('2026-11-19T01:02:00Z START dry=0 queue_only=0\n2026-11-19T01:02:01Z FAIL stage\n')
        self.check(self.T + timedelta(minutes=3))
        self.assertEqual(self.files('*BLOCKER*'), [])

    def test_delivered_event_moved_by_consumer_is_not_replayed(self):
        self.check(self.T)
        event = self.files('*BLOCKER*')[0]
        event.rename(self.root / 'held_event.md')
        self.check(self.T + timedelta(minutes=1))
        self.assertFalse(event.exists())
        data = json.loads((self.state / 'health' / 'state.json').read_text())
        self.assertTrue(data['events'][event.name]['delivered'])

    def test_only_undelivered_events_are_replayed_after_write_error(self):
        original = Path.open

        def fail_event(path, mode='r', *args, **kwargs):
            if path.parent == self.events and mode == 'x':
                raise OSError('temporary event storage error')
            return original(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', fail_event), self.assertRaises(OSError):
            self.check(self.T)
        state = json.loads((self.state / 'health/state.json').read_text())
        self.assertFalse(next(iter(state['events'].values()))['delivered'])
        self.check(self.T + timedelta(minutes=1))
        self.assertEqual(len(self.files('*BLOCKER*')), 1)
        state = json.loads((self.state / 'health/state.json').read_text())
        self.assertTrue(next(iter(state['events'].values()))['delivered'])

    def test_delivered_history_does_not_touch_event_storage(self):
        self.check(self.T)
        # A later tick must not stat/read any previously delivered event.
        original = Path.exists

        def no_event_stat(path):
            if path.parent == self.events:
                raise AssertionError('delivered history touched event storage')
            return original(path)

        with patch.object(Path, 'exists', no_event_stat):
            self.check(self.T + timedelta(minutes=1))

    def test_legacy_delivered_journal_is_not_replayed(self):
        self.check(self.T)
        path = self.state / 'health/state.json'
        state = json.loads(path.read_text())
        for name, entry in state['events'].items():
            state['events'][name] = entry['content']
        path.write_text(json.dumps(state))
        event = self.files('*BLOCKER*')[0]
        event.rename(self.root / 'legacy_consumed.md')
        self.check(self.T + timedelta(minutes=1))
        self.assertFalse(event.exists())

    def test_stale_event_quotes_hourly_lock_skip(self):
        self.write_log()
        with self.log.open('a') as f:
            f.write('2026-11-19T02:00:00Z FAIL previous run still holds the lock\n')
        self.check(self.T + timedelta(minutes=91))
        event, = self.files('*BLOCKER_code_sync_stale.md')
        self.assertIn('2026-11-19T02:00:00Z FAIL previous run still holds the lock', event.read_text())

    def test_second_stale_incident_gets_new_event(self):
        self.write_log()
        self.check(self.T + timedelta(minutes=91))
        self.write_log(self.T + timedelta(minutes=92))
        self.check(self.T + timedelta(minutes=93))
        self.check(self.T + timedelta(minutes=183))
        self.assertEqual(len(self.files('*BLOCKER_code_sync_stale.md')), 2)

    def test_fake_clock_cli_local_only(self):
        self.write_log()
        env = dict(os.environ, **self.env, LCS_HEALTH_NOW='2026-11-19T03:00:00Z')
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'sync_health.py')],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('active=stale', result.stdout)


class CoverageTests(Fixture):
    def test_dry_count_refuses_symlinked_and_outside_folders(self):
        (self.root / 'lane').mkdir()
        (self.root / 'link').symlink_to(self.root / 'lane', target_is_directory=True)
        (self.root / 'lane' / 'nested').mkdir()
        for folder in (self.root / 'link', self.root / 'link/nested', Path('/data2'), Path('/tmp'),
                       Path('/scratch/jjyeung/orch_n30')):
            result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'dry_count.py'), str(folder)],
                                    env=dict(os.environ, **self.env), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('REFUSED', result.stderr)
            self.assertEqual(result.stdout, '')

    def test_dry_count_default_system_python(self):
        lane = self.root / 'sb_system'
        lane.mkdir()
        (lane / 'a.py').write_text('a=1\n')
        env = dict(os.environ, **self.env)
        env.pop('LCS_PYTHON', None)
        env['PATH'] = '/usr/bin:/bin'
        result = subprocess.run(['bash', str(TOOLS / 'dry_count.sh'), str(lane)], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['files'], 1)

    def test_directory_rules_include_and_exclude_named_examples(self):
        for name in ('in', 'out', 'work/tree', 'kit', 'unit_proof', 'proofs', 'runs', 'evidence'):
            p = self.root / 'lane' / name
            p.mkdir(parents=True, exist_ok=True)
            (p / 'source.py').write_text(repr(name))
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'lane_code_filter.py'), 'test'],
                                cwd=self.root / 'lane', stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({x.decode() for x in result.stdout.split(b'\0') if x},
                         {'in/source.py', 'out/source.py', 'work/tree/source.py', 'kit/source.py'})

    def test_maxdir_prunes_code_and_root_gate_is_reported(self):
        lane = self.root / 'so_proof'
        lane.mkdir()
        (lane / 'source.py').write_text('x=1\n')
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'dry_count.py'), str(lane)],
                                env=dict(os.environ, **self.env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['files'], 1)
        self.assertEqual(report['hourly_files'], 0)
        self.assertIn('directory name', report['hourly_root_gate_reason'])
        # Exercise the filter's exact MAXDIR=2000 threshold on local scratch only.
        big = self.root / 'big'
        big.mkdir()
        for i in range(2000):
            (big / f'{i}.bin').touch()
        (big / 'source.py').write_text('code=1\n')
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'lane_code_filter.py'), 'test'],
                                cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(b'big/source.py', result.stdout)
        self.assertIn(b'skipped_bigdirs=1', result.stderr)

    def test_dry_count_has_no_copy_and_reports_dedup(self):
        lane = self.root / 'sb_example'
        lane.mkdir()
        (lane / 'a.py').write_text('a=1\n')
        (lane / 'b.py').write_text('a=1\n')
        (lane / 'runs').mkdir()
        (lane / 'runs' / 'skip.py').write_text('skip=1\n')
        before = kit.inventory(lane)
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(TOOLS / 'dry_count.py'), str(lane)],
                                env=dict(os.environ, **self.env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual((report['files'], report['bytes']), (1, 4))
        self.assertEqual(before, kit.inventory(lane))

    def test_current_hourly_add_is_scoped_away_from_kits(self):
        source = Path(__file__).resolve().parent / 'fixtures' / 'lane_code_sync.sh'
        lines = source.read_text().splitlines()
        adds = [line for line in lines if line.startswith('git -C "$R" add ')]
        self.assertEqual(len(adds), 1)
        self.assertEqual(adds[0].split(' || ')[0],
                         'git -C "$R" add -f -A lane_code tools/lane_code_sync.sh tools/lane_code_filter.py tools/lane_code_scan.py')
        # This assertion checks command scope only. A separate real-Git test proves tree preservation.
        self.assertNotIn('kits', adds[0])


class HealthLoopTests(Fixture):
    def run_loop(self, first_exit):
        scripts = self.root / 'loop'
        scripts.mkdir()
        (scripts / 'sync_health_loop.sh').write_text((TOOLS / 'sync_health_loop.sh').read_text())
        (scripts / 'sync_health.sh').write_text(
            'if [ ! -e "$LCS_S/first_check" ]; then\n'
            f'  echo first > "$LCS_S/first_check"; exit {first_exit}\n'
            'fi\necho second > "$LCS_S/second_check"\n')
        bin_ = self.root / 'bin'
        bin_.mkdir()
        (bin_ / 'hostname').write_text('#!/bin/bash\necho trinity-3-30\n')
        (bin_ / 'sleep').write_text(
            '#!/bin/bash\n[ "$1" = 600 ] || exit 3\n'
            'if [ -e "$LCS_S/second_check" ]; then exit 1; fi\n')
        for script in bin_.iterdir():
            script.chmod(0o755)
        return subprocess.run(['bash', str(scripts / 'sync_health_loop.sh')],
                              env=dict(os.environ, **self.env, PATH=str(bin_) + ':/usr/bin:/bin'),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)

    def test_transient_error_is_logged_and_next_tick_runs(self):
        self.assertEqual(self.run_loop(2).returncode, 1)  # Test sleep ends after two checks.
        self.assertTrue((self.state / 'second_check').exists())
        self.assertIn('health check failed exit=2', (self.state / 'health.log').read_text())

    def test_signal_exit_stops_without_automatic_rerun(self):
        self.assertEqual(self.run_loop(137).returncode, 137)
        self.assertFalse((self.state / 'second_check').exists())
        self.assertIn('health check failed exit=137', (self.state / 'health.log').read_text())


if __name__ == '__main__':
    unittest.main()
