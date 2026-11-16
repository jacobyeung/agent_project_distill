"""state_lint.py on the CURRENT_STATE.md draft and on three broken variants."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(DOCS))
sys.path.insert(0, DOCS)
import indexfmt  # noqa: E402
import state_lint  # noqa: E402

FIX = os.path.join(HERE, 'fixtures')
DRAFT = os.path.join(FIX, 'CURRENT_STATE_DRAFT.md')
LISTING = os.path.join(FIX, 'design_ls_20261116.txt')
INDEX = os.path.join(FIX, 'INDEX_PROPOSED.md')
KNOWN = os.path.join(FIX, 'state_known_paths.txt')


def read(path):
    with open(path, 'r') as handle:
        return handle.read()


def never_exists(_path):
    return False


class StateLintTest(unittest.TestCase):
    def setUp(self):
        self.text = read(DRAFT)
        self.listing = indexfmt.read_listing(LISTING, ignore=())
        self.registered = state_lint.registered_from_index(read(INDEX))
        self.known = [line.strip() for line in read(KNOWN).splitlines() if line.strip()]

    def lint(self, text):
        return state_lint.lint(text, self.listing, self.registered, self.known,
                               exists=never_exists)

    def classes(self, text):
        return sorted(d['class'] for d in self.lint(text))

    def test_registered_set(self):
        self.assertEqual(sorted(self.registered), [
            'D0_STOP_RULE_20261116.md', 'LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md',
            'NEXT_LEG_INIT_RULE_20261116.md',
            'REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md',
            'REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md',
            'REFREEZE_AMENDMENT_3_D1_D2_ROUTE_DECISIONS_20261116.md',
            'REFREEZE_PREREGISTRATION_20261115.json', 'REFREEZE_PREREGISTRATION_20261115.md'])

    def test_draft_passes(self):
        self.assertEqual(self.lint(self.text), [])
        self.assertLessEqual(len(self.text.splitlines()), 150)

    def test_151_lines_fail(self):
        lines = self.text.splitlines()
        padded = '\n'.join(lines + ['filler'] * (151 - len(lines))) + '\n'
        self.assertEqual(len(padded.splitlines()), 151)
        self.assertEqual(self.classes(padded), ['too_long'])

    def test_missing_section_fails(self):
        text = self.text.replace('## Do not redo', '## Things to skip')
        defects = self.lint(text)
        self.assertEqual([(d['class'], d['text']) for d in defects],
                         [('missing_section', 'Do not redo')])

    def test_registered_record_without_sha_fails(self):
        text = self.text.replace('`D0_STOP_RULE_20261116.md` sha256 7a487e63 (amended',
                                 '`D0_STOP_RULE_20261116.md` (amended')
        self.assertNotEqual(text, self.text)
        self.assertEqual(self.classes(text), ['no_sha'])

    def test_unknown_file_fails(self):
        text = self.text + '- see `NO_SUCH_RECORD_20261116.md` and `/data2/x/y.md`\n'
        self.assertEqual(self.classes(text), ['missing_file', 'missing_file'])

    def test_cli(self):
        cmd = [sys.executable, os.path.join(DOCS, 'state_lint.py'), '--state', DRAFT,
               '--listing', LISTING, '--index', INDEX, '--known', KNOWN]
        self.assertEqual(subprocess.call(cmd, stdout=subprocess.DEVNULL), 0)


if __name__ == '__main__':
    unittest.main()
