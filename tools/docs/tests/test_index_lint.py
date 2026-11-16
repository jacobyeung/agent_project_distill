"""index_lint.py on the saved index of 2026-11-16 and on the proposed grouped index."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(DOCS))
sys.path.insert(0, DOCS)
import index_lint  # noqa: E402
import indexfmt  # noqa: E402

FIX = os.path.join(HERE, 'fixtures')
OLD = os.path.join(FIX, 'INDEX_20261116.md')
LISTING = os.path.join(FIX, 'design_ls_20261116.txt')
PROPOSED = os.path.join(FIX, 'INDEX_PROPOSED.md')


def read(path):
    with open(path, 'r') as handle:
        return handle.read()


class CurrentIndexTest(unittest.TestCase):
    """The saved index holds the defects the audit counted."""

    def setUp(self):
        listing = indexfmt.read_listing(LISTING)
        self.defects = index_lint.lint(read(OLD), listing)
        self.counts = index_lint.summarize(self.defects)

    def files_of(self, cls):
        return sorted(d['file'] for d in self.defects if d['class'] == cls)

    def test_four_files_listed_twice(self):
        self.assertEqual(self.files_of('duplicate'), [
            'DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT_20261112.md',
            'E2E_BUILD_ground_backend_20261110.md',
            'E2E_BUILD_ground_rows_20261110.md',
            'E2E_BUILD_tower_read_20261110.md'])

    def test_unlisted_files(self):
        unlisted = self.files_of('unlisted')
        self.assertEqual(len(unlisted), 25)
        for name in ('FIRST_CONFIG_20261115.md', 'ORCHARD_POSE_KIT_20261109.md',
                     'SPLIT_FLASH_SUBSETS_20261112.md', 'REFREEZE_PREREGISTRATION_20261115.json',
                     'if_p0_20261114', 'legs1_warm_start_20261113'):
            self.assertIn(name, unlisted)

    def test_rows_without_a_folder_file_and_without_verdict(self):
        self.assertEqual(self.counts.get('empty_row', 0), 0)
        self.assertEqual(self.counts['outside_folder'], 4)
        self.assertEqual(self.files_of('missing'), ['FINAL_VERDICTS.tsv'])
        self.assertEqual(self.counts['no_verdict'], 196)
        self.assertEqual(self.counts['long_row'], 145)

    def test_cli_exits_one(self):
        rc = subprocess.call([sys.executable, os.path.join(DOCS, 'index_lint.py'), '--index', OLD,
                              '--listing', LISTING], stdout=subprocess.DEVNULL)
        self.assertEqual(rc, 1)


class ProposedIndexTest(unittest.TestCase):
    def test_proposed_passes(self):
        listing = indexfmt.read_listing(LISTING)
        defects = index_lint.lint(read(PROPOSED), listing, max_main_lines=115)
        self.assertEqual(defects, [])

    def test_every_entry_exactly_once(self):
        rows, _ = indexfmt.parse(read(PROPOSED))
        named = indexfmt.listed_files(rows)
        self.assertEqual(sorted(named), sorted(indexfmt.read_listing(LISTING)))

    def test_cli_exits_zero(self):
        rc = subprocess.call([sys.executable, os.path.join(DOCS, 'index_lint.py'), '--index',
                              PROPOSED, '--listing', LISTING, '--max-main-lines', '115'],
                             stdout=subprocess.DEVNULL)
        self.assertEqual(rc, 0)


class DefectClassTest(unittest.TestCase):
    HEAD = ('## Results\n\n| Topic | File | Status | Verdict | Evidence |\n'
            '|---|---|---|---|---|\n')

    def lint(self, body, listing=('A.md', 'B.md')):
        return index_lint.summarize(index_lint.lint(self.HEAD + body, list(listing)))

    def test_clean(self):
        self.assertEqual(self.lint('| a | `A.md` | s | GO | OK |\n| b | `B.md` | s | OPEN | OK |\n'),
                         {})

    def test_each_class(self):
        counts = self.lint('| a | `A.md` |  | MAYBE | LOST |\n| b | `C.md` | s | GO | OK |\n'
                           '| c |  | s | GO | OK |\n| d | `A.md` | ' + 'x' * 290 + ' | GO | OK |\n')
        self.assertEqual(counts['no_status'], 1)
        self.assertEqual(counts['no_verdict'], 1)
        self.assertEqual(counts['bad_evidence'], 1)
        self.assertEqual(counts['missing'], 1)
        self.assertEqual(counts['empty_row'], 1)
        self.assertEqual(counts['duplicate'], 1)
        self.assertEqual(counts['long_row'], 1)
        self.assertEqual(counts['long_status'], 1)
        self.assertEqual(counts['unlisted'], 1)

    def test_archive_rows(self):
        text = (self.HEAD + '| a | `A.md` | s | GO | OK |\n\n## Archive\n\n'
                '| Topic | File | Status | Verdict | Evidence |\n|---|---|---|---|---|\n'
                '| b | `B.md` | still live | GO | OK |\n')
        counts = index_lint.summarize(index_lint.lint(text, ['A.md', 'B.md']))
        self.assertEqual(counts, {'archive_status': 1})
        text = text.replace('still live', 'SUPERSEDED_BY: `Z.md`')
        counts = index_lint.summarize(index_lint.lint(text, ['A.md', 'B.md']))
        self.assertEqual(counts, {'dangling_supersede': 1})

    def test_multi_file_cell_and_directory(self):
        counts = self.lint('| a | `A.md` + `A.tgz` + `ev/` | s | RESULT | OK |\n'
                           '| b | `B.md` | s | GO | PARTIAL |\n',
                           listing=('A.md', 'A.tgz', 'ev', 'B.md'))
        self.assertEqual(counts, {})

    def test_main_too_long(self):
        body = ''.join('| t | `F%d.md` | s | GO | OK |\n' % i for i in range(20))
        listing = ['F%d.md' % i for i in range(20)]
        defects = index_lint.lint(self.HEAD + body + '\n## Archive\n', listing, max_main_lines=10)
        self.assertEqual(index_lint.summarize(defects), {'main_too_long': 1})


if __name__ == '__main__':
    unittest.main()
