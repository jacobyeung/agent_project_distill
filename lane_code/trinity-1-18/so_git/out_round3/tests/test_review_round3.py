"""Round-3 regressions; all Git commands use doubles unless separately opted in."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_owner_tools as owner

kit = owner.kit


class VerdictAndBindingTests(unittest.TestCase):
    def setUp(self):
        switch = patch.dict(os.environ, LCS_REVIEW2_FIXES='1')
        switch.start()
        self.addCleanup(switch.stop)

    def review(self, tail, bind=True):
        return kit.review(('VERDICT: GO\n' + tail).encode(), 'seal value', 'a' * 64,
                          'a' * 64 if bind else None)

    def test_f1_negative_suffixes_refuse(self):
        for tail in ('REJECTED', 'Status: REJECTED', 'REJECTION', 'NO-GOOD',
                     'Verdict: REJECTED', 'REJECTION tests passed.'):
            with self.subTest(tail=tail), self.assertRaisesRegex(kit.Refusal, 'negative review'):
                self.review(tail)

    def test_f1_mixed_case_conditional_verdict_refuses(self):
        for label in ('Verdict', 'verdict', 'VeRdIcT'):
            with self.subTest(label=label), self.assertRaises(kit.Refusal):
                self.review(label + ': GO AFTER FIXES')

    TEMPLATES = ('- **Archive SHA256:** {}', 'Archive SHA256: {}', '1. SHA256: {}',
                 '## SHA256: {}', '`SHA256`: {}', '_SHA256_: {}', 'SHA256 = {}',
                 '> - **Reviewed archive SHA-256** = `{}`', '| _Archive SHA256_ | {} |')

    def test_f2_formatted_conflicting_hashes_refuse_with_owner_binding(self):
        for template in self.TEMPLATES:
            with self.subTest(template=template), self.assertRaisesRegex(kit.Refusal, 'SHA256 differs'):
                self.review(template.format('b' * 64))

    def test_f2_matching_hashes_bind_without_owner_override(self):
        for template in self.TEMPLATES:
            with self.subTest(template=template):
                self.assertEqual(self.review(template.format('a' * 64), False)[1]['methods'], ['sha256'])

    def test_f2_duplicate_conflicting_hashes_refuse(self):
        with self.assertRaisesRegex(kit.Refusal, 'ambiguous sha256'):
            self.review('SHA256: ' + 'a' * 64 + '\n- **Archive SHA256:** ' + 'b' * 64)


class RunnerEvidenceTests(unittest.TestCase):
    def test_f3_disabled_runner_records_switch_without_git(self):
        for value in (None, '', '0', '1'):
            env = dict(os.environ, LCS_RUN_REAL_GIT_TESTS='0')
            env.pop('LCS_REVIEW2_FIXES', None)
            if value is not None:
                env['LCS_REVIEW2_FIXES'] = value
            result = subprocess.run(['bash', str(owner.BASE / 'tests/run_real_git_owner.sh')],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, timeout=10)
            with self.subTest(value=value):
                self.assertEqual(result.returncode, 2)
                self.assertIn('LCS_REVIEW2_FIXES=' + ('<unset>' if value is None else value) + '\n',
                              result.stdout)
                self.assertIn('REFUSED: set LCS_RUN_REAL_GIT_TESTS=1', result.stderr)


class RemoteBoundaryTests(owner.Fixture):
    def setUp(self):
        super().setUp()
        self.env['LCS_REVIEW2_FIXES'] = '1'

    def remote_double(self, remote, push, urls):
        fake = owner.FakeGit()

        def run(argv, **kwargs):
            if argv[0] == 'git' and argv[7:9] == ['remote', 'get-url']:
                fake.calls.append(argv[7:])
                if argv[-1] == remote and ('--push' in argv) == push:
                    return ('\n'.join(urls) + '\n').encode()
                return (str(self.root / (argv[-1] + '.git')) + '\n').encode()
            return fake(argv, **kwargs)
        return fake, run

    def test_f4_external_fetch_and_push_remotes_refuse_before_mutation(self):
        outside = self.root.parent / 'outside_remote.git'
        alias = self.root / 'remote_alias'
        alias.symlink_to(outside, target_is_directory=True)
        for remote in ('origin', 'home'):
            for push in (False, True):
                for value in ('https://example.invalid/repo', 'owner@example.invalid:repo',
                              'file://' + str(self.root / 'origin.git'), str(outside),
                              str(alias), '../../../outside_remote.git'):
                    fake, run = self.remote_double(remote, push, [value])
                    with self.subTest(remote=remote, push=push, value=value), \
                         patch.object(kit, 'run', side_effect=run), \
                         self.assertRaisesRegex(kit.Refusal, 'test remote'):
                        self.invoke(dry=False)
                    self.assertFalse(any(c[0] in ('add', 'commit', 'push') for c in fake.calls))
                    self.assertFalse((self.repo / 'kits/_probe').exists())

    def test_f4_second_push_destination_outside_boundary_refuses(self):
        fake, run = self.remote_double('origin', True,
                                      [str(self.root / 'origin.git'), str(self.root.parent / 'outside.git')])
        with patch.object(kit, 'run', side_effect=run), self.assertRaisesRegex(kit.Refusal, 'test remote'):
            self.invoke(dry=False)
        self.assertFalse(any(c[0] in ('add', 'commit', 'push') for c in fake.calls))

    def test_f4_relative_local_remotes_are_allowed(self):
        fake, run = self.remote_double('origin', True, ['../../origin.git'])
        with patch.object(kit, 'run', side_effect=run):
            self.assertEqual(self.invoke(dry=False)[0], 0)
        self.assertEqual(sum(c[0] == 'push' for c in fake.calls), 2)

    def test_f4_dry_run_still_calls_no_git(self):
        fake = owner.FakeGit()
        with patch.object(kit, 'run', side_effect=fake):
            self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(fake.calls, [])


class NestedCoverageTests(owner.Fixture):
    def test_f5_excluded_duplicate_representative_refuses_ambiguous_count(self):
        folder = self.root / 'out'
        for name in ('devin_traces', 'z_kept'):
            (folder / name).mkdir(parents=True)
            (folder / name / 'same.py').write_text('SAME = 1\n')
        env = dict(os.environ, **self.env)
        env['LCS_REVIEW2_FIXES'] = '1'
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(owner.TOOLS / 'dry_count.py'), str(folder)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('count the containing lane root', result.stderr)

    def test_f5_exclusion_spanning_folder_boundary_matches_whole_tree(self):
        folder = self.root / 'out'
        (folder / 'devin_traces').mkdir(parents=True)
        (folder / 'devin_traces/trace.py').write_text('TRACE = 1\n')
        (folder / 'keep.py').write_text('KEEP = 1\n')
        env = dict(os.environ, **self.env)
        env['LCS_REVIEW2_FIXES'] = '1'
        result = subprocess.run([sys.executable, '-I', '-s', '-B', str(owner.TOOLS / 'dry_count.py'), str(folder)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        counts = json.loads(result.stdout)
        whole = subprocess.run([sys.executable, '-I', '-s', '-B', str(owner.TOOLS / 'lane_code_filter.py'), 'whole'],
                               cwd=str(self.root), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=10)
        self.assertEqual(whole.returncode, 0, whole.stderr)
        selected = [os.fsdecode(p) for p in whole.stdout.split(b'\0') if p.startswith(b'out/')]
        self.assertEqual(selected, ['out/keep.py'])
        self.assertEqual(counts['hourly_files'], len(selected))
        self.assertEqual(counts['hourly_bytes'], sum((self.root / p).stat().st_size for p in selected))
        self.assertEqual(counts['files'], 2)  # Raw filter statistics remain observable.


if __name__ == '__main__':
    unittest.main()
