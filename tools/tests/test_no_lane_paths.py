"""Lane-path ratchet: trainer/**/*.py may not gain literal lane paths beyond tools/treegit/LANE_PATH_BASELINE.json.

Python 3.6 safe. Fixtures live in a fresh directory under TMPDIR.
"""
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from tools.treegit import lane_paths as lp  # noqa: E402

TRAINER = os.path.join(REPO, 'trainer')
LIT = '/scratch/jjyeung/' + 'orch_cd/x/work'  # split so this file never matches a scan of tools/


class TrainerRatchetTest(unittest.TestCase):

    @unittest.skipUnless(os.path.isdir(TRAINER), 'trainer/ not checked out')
    def test_trainer_within_baseline(self):
        bad = lp.compare(lp.load_baseline(), lp.scan(TRAINER))
        self.assertEqual(bad, [], '\n'.join(bad))

    def test_baseline_totals_match_counts(self):
        b = lp.read_json(lp.BASELINE)
        self.assertEqual(b['files'], len(b['counts']))
        self.assertEqual(b['total'], sum(b['counts'].values()))
        self.assertEqual(b['literals'], list(lp.LITERALS))


class FixtureRatchetTest(unittest.TestCase):

    def setUp(self):
        self.t = tempfile.mkdtemp(prefix='lanepaths_')
        self.root = os.path.join(self.t, 'trainer')
        self.write('pkg/a.py', 'ROOT = "%s"\n' % LIT)
        self.write('pkg/b.py', 'x = 1\n')
        self.write('pkg/__pycache__/a.py', 'R = "%s"\n' % LIT)
        self.write('notes.md', 'see %s\n' % LIT)
        self.base = os.path.join(self.t, 'BASELINE.json')
        self.assertEqual(lp.main(['--root', self.root, '--baseline', self.base, '--write-baseline']), 0)

    def tearDown(self):
        shutil.move(self.t, self.t + '.done')  # left in place under TMPDIR; nothing is removed

    def write(self, rel, text, mode='w'):
        p = os.path.join(self.root, rel)
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, mode) as f:
            f.write(text)

    def check(self):
        return lp.compare(lp.load_baseline(self.base), lp.scan(self.root))

    def test_baseline_counts_only_py_outside_skipped_dirs(self):
        self.assertEqual(lp.load_baseline(self.base), {'pkg/a.py': 1})
        self.assertEqual(self.check(), [])

    def test_added_literal_fails(self):
        self.write('pkg/a.py', 'DATA = "/data2/jjyeung/' + 'x"\n', mode='a')
        self.assertEqual(self.check(), ['pkg/a.py: 2 lane-path literal(s), baseline 1'])
        self.assertEqual(lp.main(['--root', self.root, '--baseline', self.base, '--check']), 1)

    def test_new_file_fails(self):
        self.write('pkg/b.py', 'H = "/home/jjyeung/' + 'y"\n', mode='a')
        self.assertEqual(self.check(), ['pkg/b.py: new file holds 1 lane-path literal(s)'])

    def test_lowered_count_passes(self):
        self.write('pkg/a.py', 'import os\nROOT = os.environ["DISTILL_LANE_ROOT"]\n')
        self.assertEqual(self.check(), [])
        self.assertEqual(lp.main(['--root', self.root, '--baseline', self.base, '--check']), 0)


if __name__ == '__main__':
    unittest.main()
