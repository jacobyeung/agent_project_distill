"""Regression tests for review round 2; Git is replaced by command doubles."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import timedelta
import gzip
import io
import json
import lzma
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zlib
from unittest.mock import patch

import test_owner_tools as owner

kit, health = owner.kit, owner.health


class Round2Fixture(owner.Fixture):
    def setUp(self):
        super().setUp()
        self.env['LCS_REVIEW2_FIXES'] = '1'
        self.switch = patch.dict(os.environ, LCS_REVIEW2_FIXES='1')
        self.switch.start()
        self.addCleanup(self.switch.stop)


class LandingFailures(Round2Fixture):
    def test_f1_origin_rejection_requires_user_and_never_pushes_home(self):
        fake = owner.FakeGit()
        fake.fail = ['push', '-q', 'origin']
        with patch.object(kit, 'run', side_effect=fake), self.assertRaisesRegex(
                kit.Refusal, 'STOP.*user.*hourly'):
            self.invoke(dry=False)
        self.assertEqual([c for c in fake.calls if c[0] == 'push'],
                         [['push', '-q', 'origin', 'HEAD:refs/heads/lane-code']])
        self.assertFalse(any(c[0] == 'reset' for c in fake.calls))
        self.assertFalse((self.state / 'KITS_LANDED.txt').exists())
        self.assertEqual(list(self.events.iterdir()), [])

    def test_f2_failed_commit_unstages_only_kit(self):
        self.check_failed_stage(['commit'])

    def test_f2_failed_add_unstages_only_kit(self):
        self.check_failed_stage(['add'])

    def check_failed_stage(self, failure):
        fake = owner.FakeGit()
        fake.fail = failure
        with patch.object(kit, 'run', side_effect=fake), self.assertRaisesRegex(
                kit.Refusal, 'move.*kits/_probe.*aside'):
            self.invoke(dry=False)
        self.assertEqual([c for c in fake.calls if c[0] == 'reset'],
                         [['reset', '-q', '--', 'kits/_probe']])
        self.assertEqual(fake.calls[-1], ['diff', '--cached', '--quiet'])
        self.assertFalse(any(c[0] == 'push' for c in fake.calls))
        self.assertTrue((self.repo / 'kits/_probe/KIT.json').is_file())

    def test_f2_partial_copy_explains_recovery_without_staging(self):
        fake = owner.FakeGit()
        with patch.object(kit, 'run', side_effect=fake), \
             patch.object(kit.shutil, 'copytree', side_effect=OSError('copy interrupted')), \
             self.assertRaisesRegex(kit.Refusal, 'move.*kits/_probe.*aside'):
            self.invoke(dry=False)
        self.assertFalse(any(c[0] in ('add', 'commit', 'push') for c in fake.calls))

    def test_f2_reset_failure_requires_user_before_hourly(self):
        fake = owner.FakeGit()

        def fail(argv, **kwargs):
            if argv[0] == 'git' and argv[7] in ('commit', 'reset'):
                fake.calls.append(argv[7:])
                raise kit.Refusal('injected failure')
            return fake(argv, **kwargs)

        with patch.object(kit, 'run', side_effect=fail), self.assertRaisesRegex(
                kit.Refusal, 'STOP.*index.*user.*hourly'):
            self.invoke(dry=False)
        self.assertFalse(any(c[0] == 'push' for c in fake.calls))


class TestIsolation(Round2Fixture):
    def test_f3_kit_test_mode_cannot_target_production_state(self):
        self.env.update(LCS_TEST_ROOT='/scratch/jjyeung',
                        LCS_S='/scratch/jjyeung/distill_sync',
                        LCS_R='/scratch/jjyeung/distill_sync/repo')
        with patch.object(kit, 'owner_lock', side_effect=AssertionError('must not lock production')), \
             self.assertRaisesRegex(kit.Refusal, 'production'):
            self.invoke()

    def test_f3_kit_test_mode_cannot_target_production_repo_or_events(self):
        self.env['LCS_TEST_ROOT'] = '/scratch/jjyeung'
        for key, value in (('LCS_R', '/scratch/jjyeung/distill_sync/repo'),
                           ('LCS_EV', '/scratch/jjyeung/distill_sync/health')):
            with self.subTest(key=key), patch.dict(self.env, {key: value}), \
                 patch.object(kit, 'owner_lock', side_effect=AssertionError('must not lock')), \
                 self.assertRaisesRegex(kit.Refusal, 'production'):
                self.invoke()

    def test_f3_health_fake_clock_cannot_write_production(self):
        env = dict(self.env, LCS_TEST_ROOT='/scratch/jjyeung',
                   LCS_S='/scratch/jjyeung/distill_sync', LCS_HEALTH_NOW='2099-01-01T00:00:00Z')
        with patch.dict(os.environ, env), patch.object(health, 'check') as check:
            with self.assertRaisesRegex(ValueError, 'production'):
                health.main()
            check.assert_not_called()

    def test_f3_resolved_symlink_to_production_is_refused(self):
        alias = self.root / 'alias'
        alias.symlink_to('/scratch/jjyeung/distill_sync', target_is_directory=True)
        self.env.update(LCS_TEST_ROOT='/scratch/jjyeung', LCS_S=str(alias), LCS_R=str(alias / 'repo'))
        with patch.object(kit, 'owner_lock', side_effect=AssertionError('must not lock')), \
             self.assertRaisesRegex(kit.Refusal, 'production'):
            self.invoke()


class BindingAndVerdicts(unittest.TestCase):
    def setUp(self):
        switch = patch.dict(os.environ, LCS_REVIEW2_FIXES='1')
        switch.start()
        self.addCleanup(switch.stop)

    def review(self, tail, bind=True):
        return kit.review(('VERDICT: GO\n' + tail).encode(), 'seal value', 'a' * 64,
                          'a' * 64 if bind else None)

    def test_f4_formatted_contradictory_hashes_cannot_hide_behind_owner_binding(self):
        for template in ('- SHA256: {}', '| SHA256 | {} |', '**SHA256:** {}',
                         '> **SHA-256**: `{}`', '  * SHA256: {} (archive)'):
            with self.subTest(template=template), self.assertRaises(kit.Refusal):
                self.review(template.format('b' * 64))

    def test_f4_matching_formatted_bindings_authorize_and_conflicts_refuse(self):
        for template in ('- SHA256: {}', '| SHA256 | `{}` |', '**SHA256:** `{}`',
                         '> **SHA-256**: {} (archive)'):
            with self.subTest(template=template):
                self.assertEqual(self.review(template.format('a' * 64), False)[1]['methods'], ['sha256'])
        for tail in ('Seal: seal value\n- Seal: wrong', 'SHA256: ' + 'a' * 64 + '\n- SHA256: ' + 'b' * 64,
                     '- SHA256:', '**Seal:** wrong'):
            with self.subTest(tail=tail), self.assertRaises(kit.Refusal):
                self.review(tail)
        self.assertEqual(self.review('Seal: seal value', False)[1]['methods'], ['seal'])

    def test_f5_ordinary_prose_does_not_override_accepting_verdict(self):
        for tail in ('There is no good reason to block.', 'The tool rejects symlinks.',
                     'Verdict: see above', 'XREJECTY is a fixture.'):
            with self.subTest(tail=tail):
                self.assertEqual(self.review(tail)[0], 'GO')

    def test_f5_explicit_negative_tokens_still_refuse_even_when_quoted(self):
        for tail in ('NO-GO', 'NO GO', 'REJECT', 'REJECTION tests passed.',
                     '`GO AFTER FIXES` or `NO-GO`', 'VERDICT: WAIT'):
            with self.subTest(tail=tail), self.assertRaises(kit.Refusal):
                self.review(tail)


class HealthRegressions(Round2Fixture):
    T = owner.HealthTests.T
    write_log = owner.HealthTests.write_log

    def test_f6_split_stale_and_failed_recovery_emits_both_results(self):
        self.write_log(failed=True)
        self.check(self.T + timedelta(minutes=91))
        verified = self.T + timedelta(minutes=92)
        self.write_log(verified, end_ok=False)
        self.check(verified)
        with self.log.open('a') as f:
            f.write(health.iso(verified + timedelta(seconds=1)) + ' END ok\n')
        self.check(verified + timedelta(seconds=2))
        results = sorted(self.events.glob('*RESULT*'))
        self.assertEqual(len(results), 2)
        self.assertEqual({p.read_text().split('recovered: ')[1].split(';')[0] for p in results},
                         {'stale', 'failed'})
        self.check(verified + timedelta(minutes=1))
        self.assertEqual(sorted(self.events.glob('*RESULT*')), results)

    def test_f7_own_blocker_is_read_once_even_after_consumer_moves_it(self):
        self.write_log(failed=True)
        blocker = self.events / '20261119T0100Z_BLOCKER_sync_failed.md'
        blocker.write_text(health.iso(self.T + timedelta(seconds=1)) + ' code_sync run failed\n')
        with patch.object(health, 'own_blocker', wraps=health.own_blocker) as read:
            self.check(self.T + timedelta(minutes=1))
            blocker.rename(self.root / 'consumed_blocker.md')
            self.check(self.T + timedelta(minutes=2))
            self.check(self.T + timedelta(minutes=3))
        self.assertEqual(read.call_count, 1)
        self.assertEqual(list(self.events.glob('*BLOCKER_code_sync_failed.md')), [])
        state = json.loads((self.state / 'health/state.json').read_text())
        self.assertEqual(state['last_failed_run'], health.iso(self.T + timedelta(seconds=1)))

    def test_f7_absent_own_blocker_is_checked_once_per_failure(self):
        self.write_log(failed=True)
        with patch.object(health, 'own_blocker', wraps=health.own_blocker) as read:
            self.check(self.T + timedelta(minutes=1))
            self.write_log(self.T + timedelta(minutes=2))
            self.check(self.T + timedelta(minutes=3))
            # Re-reading the same completed failure must not scan event storage.
            self.write_log(failed=True)
            self.check(self.T + timedelta(minutes=4))
        self.assertEqual(read.call_count, 1)


class CoverageAndFixtureSafety(Round2Fixture):
    def test_f8_nested_excluded_ancestor_has_no_hourly_coverage(self):
        if not str(self.root).startswith('/scratch/jjyeung/orch_n30/'):
            self.skipTest('set LCS_TEST_WORK under /scratch/jjyeung/orch_n30 for dry-count integration')
        for name in ('allowed/sub', 'runs/sub', 'out/devin_traces/sub'):
            folder = self.root / name
            folder.mkdir(parents=True)
            (folder / 'code.py').write_text('x=1\n')
            result = subprocess.run([sys.executable, '-I', '-s', '-B', str(owner.TOOLS / 'dry_count.py'), str(folder)],
                                    env=dict(os.environ, **self.env), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data['files'], 1)
            if name == 'allowed/sub':
                self.assertEqual(data['hourly_files'], 1)
                self.assertIsNone(data['hourly_root_gate_reason'])
            else:
                self.assertEqual(data['hourly_files'], 0)
                self.assertTrue(data['hourly_root_gate_reason'])

    def test_f9_owner_default_temp_root_ignores_checkout(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, 'mkdir') as mkdir, \
             patch.object(tempfile, 'gettempdir', return_value=str(self.root)), \
             patch.object(tempfile, 'mkdtemp', return_value=str(self.root / 'owner_temp')) as make:
            module = runpy.run_path(str(owner.BASE / 'tests/test_owner_tools.py'))
        self.assertEqual(module['FIXTURES'], self.root / 'owner_temp')
        self.assertEqual(Path(make.call_args[1]['dir']), self.root)
        self.assertFalse(any('work/test_runs' in str(c) for c in mkdir.call_args_list))

    def test_f9_owner_rejects_unsafe_root_before_writes(self):
        for root in ('/home/fake_test', '/data2/fake_test', '/scratch_evil/fake_test'):
            with patch.dict(os.environ, LCS_TEST_WORK=root), patch.object(Path, 'mkdir') as mkdir, \
                 patch.object(tempfile, 'mkdtemp') as make:
                with self.subTest(root=root), self.assertRaisesRegex(ValueError, '/scratch or /tmp'):
                    runpy.run_path(str(owner.BASE / 'tests/test_owner_tools.py'))
                mkdir.assert_not_called()
                make.assert_not_called()

    def test_f9_filter_default_temp_root_ignores_checkout(self):
        path = owner.BASE / 'tests/test_filter_shell_copies.py'
        if not path.exists():
            self.skipTest('optional filter tests are delivered in patch 03')
        module = runpy.run_path(str(path))
        fixture = module['ShellCopiesTests']()
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, 'mkdir') as mkdir, \
             patch.object(Path, 'write_text'), patch.object(Path, 'write_bytes'), \
             patch.object(tempfile, 'gettempdir', return_value=str(self.root)), \
             patch.object(tempfile, 'mkdtemp', return_value=str(self.root / 'filter_temp')) as make:
            fixture.setUp()
        self.assertEqual(Path(make.call_args[1]['dir']), self.root)
        self.assertFalse(any('work/filter_tests' in str(c) for c in mkdir.call_args_list))

    def test_f9_filter_rejects_unsafe_root_before_writes(self):
        path = owner.BASE / 'tests/test_filter_shell_copies.py'
        if not path.exists():
            self.skipTest('optional filter tests are delivered in patch 03')
        fixture = runpy.run_path(str(path))['ShellCopiesTests']()
        with patch.dict(os.environ, LCS_TEST_WORK='/data2/fake_test'), \
             patch.object(Path, 'mkdir') as mkdir, patch.object(Path, 'write_text'), \
             patch.object(Path, 'write_bytes'), patch.object(tempfile, 'mkdtemp', return_value=str(self.root)) as make:
            with self.assertRaisesRegex(ValueError, '/scratch or /tmp'):
                fixture.setUp()
            mkdir.assert_not_called()
            make.assert_not_called()


class MalformedInputs(Round2Fixture):
    def test_f12_decoder_errors_return_refused_without_traceback(self):
        args = [str(owner.TOOLS / 'land_kit.py'), str(self.tar), 's', self.sha,
                str(self.review), '_probe', '--builder', 'b', '--reviewer', 'r',
                '--bind-sha', self.sha, '--dry']
        for error in (zlib.error('bad deflate'), lzma.LZMAError('bad xz')):
            with self.subTest(error=type(error).__name__), patch.dict(os.environ, self.env), \
                 patch.object(sys, 'argv', args), patch.object(tarfile, 'open', side_effect=error), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(owner.TOOLS / 'land_kit.py'), run_name='__main__')
                self.assertEqual(result.exception.code, 2)
                self.assertIn('REFUSED:', err.getvalue())
                self.assertNotIn('Traceback', err.getvalue())

    def test_f12_truncated_gzip_returns_refused_without_traceback(self):
        self.tar.write_bytes(gzip.compress(self.tar.read_bytes())[:12])
        self.sha = kit.digest(self.tar)
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(owner.TOOLS / 'land_kit.py'),
                                 str(self.tar), 's', self.sha, str(self.review), '_probe',
                                 '--builder', 'b', '--reviewer', 'r', '--bind-sha', self.sha, '--dry'],
                                env=dict(os.environ, **self.env), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('REFUSED:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_f12_nondict_kit_metadata_is_refused(self):
        target = self.repo / 'kits/_probe'
        target.mkdir(parents=True)
        (target / 'KIT.json').write_text('[]')
        with self.assertRaisesRegex(kit.Refusal, 'KIT.json.*object'):
            self.invoke()


class Documentation(unittest.TestCase):
    def test_f9_default_tmp_root_skips_scratch_integration_before_writes(self):
        with patch.object(owner, 'FIXTURES', Path('/tmp/synthetic_owner_tests')), \
             patch.object(tempfile, 'mkdtemp', side_effect=AssertionError('no fixture writes')):
            with self.assertRaises(unittest.SkipTest):
                owner.Fixture().setUp()

    def test_f10_guide_matches_installation_receipts_queue_and_dry_lock(self):
        guide = owner.BASE / 'GIT_OWNER.md'
        if not guide.exists():
            guide = owner.BASE / 'docs/GIT_OWNER.md'
        text = guide.read_text()
        self.assertNotIn('have not been installed', text)
        self.assertIn('installed', text)
        self.assertIn('/scratch/jjyeung/orch_n30/<lane>/clone', text)
        self.assertIn('trinity-3-30 only', text)
        self.assertIn('local to trinity-3-30', text)
        self.assertIn('`--dry` takes the same lock', text)


if __name__ == '__main__':
    unittest.main()
