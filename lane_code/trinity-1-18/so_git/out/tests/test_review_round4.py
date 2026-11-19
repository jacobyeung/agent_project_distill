"""Review-parser, remote-boundary, portability and handover regressions; no real Git."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_owner_tools as owner
import test_review_round3 as round3

kit = owner.kit


class ReviewTests(unittest.TestCase):
    def setUp(self):
        switch = patch.dict(os.environ, LCS_REVIEW2_FIXES='1')
        switch.start()
        self.addCleanup(switch.stop)

    def review(self, tail, bind=True):
        return kit.review(('VERDICT: GO\n' + tail).encode(), 's', 'a' * 64,
                          'a' * 64 if bind else None)

    def test_f1_title_case_negative_verdicts_refuse(self):
        for line in ('Verdict: No-Go', 'Verdict: Reject', 'Verdict: HOLD', 'verdict: no-go',
                     'Status: Rejected', 'No-Go for landing', 'Status: Hold',
                     'Verdict: Wait', '  Status: Rejected', 'Verdict: GO AFTER FIXES'):
            with self.subTest(line=line), self.assertRaises(kit.Refusal):
                self.review(line)

    def test_f1_prose_and_references_remain_accepted(self):
        for line in ('rejects symlinks', 'The tool rejects symlinks.', 'Verdict: see above',
                     'Rejects symlinks and unsafe paths.', 'The Reject class handles errors.',
                     'Status: rejects symlinks', 'Verdict: rejects symlinks',
                     'Wait times are bounded.', 'Hold the lock during landing.'):
            with self.subTest(line=line):
                self.assertEqual(self.review(line)[0], 'GO')

    # The review lists six inline formats and a seventh, column-table format.
    FORMATS = ('kit.tar SHA256: {}', '`kit.tar` sha256: {}',
               'SHA256 of the archive: {}', 'SHA256 (kit.tar): {}',
               'Archive (kit.tar) SHA256: {}', 'sha256sum: {}',
               '| Archive | SHA256 |\n| --- | --- |\n| kit.tar | {} |')

    def test_f2_all_listed_conflicting_formats_refuse(self):
        for template in self.FORMATS:
            with self.subTest(template=template), self.assertRaisesRegex(kit.Refusal, 'SHA256 differs'):
                self.review(template.format('b' * 64))

    def test_f2_line_backstop_checks_every_hash_and_sha_spelling(self):
        for line in ('Review archive sha-256: {}', 'SHA-256 (kit.tgz) = `{}`',
                     'kit.tar SHA256: ' + 'a' * 64 + ' versus {}',
                     'SHA256 for an ARCHIVE in prose equals {}',
                     '| Archive | SHA-256 |\n| --- | --- |\n| kit.tar | ' + 'a' * 64 +
                     ' |\n| next.tar | {} |'):
            with self.subTest(line=line), self.assertRaisesRegex(kit.Refusal, 'SHA256 differs'):
                self.review(line.format('B' * 64))

    def test_f2_matching_formats_allow_owner_binding(self):
        for template in self.FORMATS:
            with self.subTest(template=template):
                self.assertEqual(self.review(template.format('A' * 64))[0], 'GO')

    def test_f2_backstop_does_not_grant_binding_or_leak_past_table(self):
        for template in self.FORMATS:
            with self.subTest(template=template), self.assertRaisesRegex(kit.Refusal, 'review needs matching'):
                self.review(template.format('a' * 64), bind=False)
        self.assertEqual(self.review(self.FORMATS[-1].format('a' * 64) +
                                    '\nTable ends here.\n| source.py | ' + 'b' * 64 + ' |')[0], 'GO')
        self.assertEqual(self.review('source.py sha256: ' + 'b' * 64)[0], 'GO')


class CoveragePortabilityTests(unittest.TestCase):
    def test_f3_nested_coverage_skips_outside_orchestration_before_writes(self):
        # Synthetic path only: this dispatch cannot write outside its workspace.
        def setup(fixture):
            fixture.root = Path('/scratch/synthetic_outside_orchestration')
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(round3.NestedCoverageTests)
        result = unittest.TestResult()
        with patch.object(owner.Fixture, 'setUp', setup), \
             patch.object(Path, 'mkdir', side_effect=AssertionError('must skip before writes')):
            suite.run(result)
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertEqual(len(result.skipped), 2)
        self.assertTrue(all('under /scratch/jjyeung/orch_n30' in why for _, why in result.skipped))


class RemoteTests(owner.Fixture):
    def test_f4_leading_tilde_fetch_and_push_refuse_before_mutation(self):
        self.env['LCS_REVIEW2_FIXES'] = '1'
        for remote in ('origin', 'home'):
            for push in (False, True):
                for n, value in enumerate(('~', '~/repo.git', '~someone/repo.git', '~repo.git')):
                    fake, run = round3.RemoteBoundaryTests.remote_double(self, remote, push, [value])
                    name = '{}_{}_{}'.format(remote, int(push), n)
                    with self.subTest(remote=remote, push=push, value=value), \
                         patch.object(kit, 'run', side_effect=run), \
                         self.assertRaisesRegex(kit.Refusal, 'test remote'):
                        self.invoke(dry=False, name=name)
                    self.assertFalse(any(c[0] in ('add', 'commit', 'push') for c in fake.calls))
                    self.assertFalse((self.repo / 'kits' / name).exists())

    def test_f4_embedded_tilde_is_a_local_path(self):
        self.env['LCS_REVIEW2_FIXES'] = '1'
        fake, run = round3.RemoteBoundaryTests.remote_double(self, 'origin', True, ['./~repo.git'])
        with patch.object(kit, 'run', side_effect=run):
            self.assertEqual(self.invoke(dry=False)[0], 0)
        self.assertEqual(sum(c[0] == 'push' for c in fake.calls), 2)


class DocumentationTests(unittest.TestCase):
    def doc(self, name):
        path = owner.BASE / name
        if not path.exists():
            path = owner.BASE / 'docs' / name
        return path.read_text()

    def test_f4_lzma_owner_preflight_is_explicit(self):
        self.assertIn("python3 -I -c 'import lzma'", self.doc('HANDOVER.md'))
        self.assertIn('import lzma', (owner.TOOLS / 'land_kit.py').read_text())

    def test_f5_hook_evidence_and_new_runner_are_current(self):
        handover = self.doc('HANDOVER.md')
        self.assertIn('realgit4_by_swarm_opt', handover)
        self.assertIn('3 tests, 0 skips', handover)
        self.assertIn('realgit5_by_swarm_opt', handover)
        self.assertIn('review_round4_source/tests/run_real_git_owner.sh', handover)
        self.assertNotIn('await authorized Git execution', handover)
        guide = self.doc('GIT_OWNER.md')
        self.assertIn('realgit4_by_swarm_opt', guide)
        self.assertIn('any path is pruned', guide)
        self.assertIn('duplicates are nonzero or their count is unavailable', guide)


if __name__ == '__main__':
    unittest.main()
