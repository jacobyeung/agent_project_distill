"""index_add.py: one row lands in the table, a duplicate is refused, parallel adds both land."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(DOCS))
sys.path.insert(0, DOCS)
import index_add  # noqa: E402
import index_lint  # noqa: E402
import indexfmt  # noqa: E402

BASE = ('# Index\n\n## Results that bind\n\n| Topic | File | Status | Verdict | Evidence |\n'
        '|---|---|---|---|---|\n| r | `R.md` | read | RESULT | OK |\n\n## Archive\n\n'
        '| Topic | File | Status | Verdict | Evidence |\n|---|---|---|---|---|\n'
        '| o | `O.md` | SUPERSEDED_BY: `R.md` | RESULT | OK |\n')


class IndexAddTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='index_add_')
        self.index = os.path.join(self.tmp, 'INDEX.md')
        with open(self.index, 'w') as handle:
            handle.write(BASE)

    def text(self):
        with open(self.index, 'r') as handle:
            return handle.read()

    def run_cli(self, name, extra=()):
        cmd = [sys.executable, os.path.join(DOCS, 'index_add.py'), '--index', self.index,
               '--topic', 'topic ' + name, '--file', name, '--status', 'status of ' + name,
               '--verdict', 'DESIGN', '--evidence', 'OK'] + list(extra)
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_appends_one_row_above_archive(self):
        proc = self.run_cli('N1.md')
        out, err = proc.communicate()
        self.assertEqual(proc.returncode, 0, err)
        text = self.text()
        self.assertIn('| topic N1.md | `N1.md` | status of N1.md | DESIGN | OK |', text)
        self.assertLess(text.index('N1.md'), text.index('## Archive'))
        self.assertIn('## New records', text)
        defects = index_lint.lint(text, ['R.md', 'O.md', 'N1.md'])
        self.assertEqual(defects, [])
        proc = self.run_cli('N2.md')
        proc.communicate()
        rows, _ = indexfmt.parse(self.text())
        self.assertEqual([r.files for r in rows if r.section == 'New records'],
                         [['N1.md'], ['N2.md']])

    def test_refuses_duplicate(self):
        proc = self.run_cli('R.md')
        out, err = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertIn(b'already listed', err)
        proc = self.run_cli('O.md')
        proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.text(), BASE)

    def test_refuses_bad_fields(self):
        with self.assertRaises(index_add.Refused):
            index_add.add(self.index, 't', ['X.md'], 'a | b', 'GO', 'OK')
        with self.assertRaises(index_add.Refused):
            index_add.add(self.index, 't', ['X.md'], 's' * 161, 'GO', 'OK')
        with self.assertRaises(index_add.Refused):
            index_add.add(self.index, 't', ['X.md'], 's', 'MAYBE', 'OK')
        with self.assertRaises(index_add.Refused):
            index_add.add(self.index, 't', ['../x/X.md'], 's', 'GO', 'OK')
        with self.assertRaises(index_add.Refused):
            index_add.add(self.index, 't', ['X.md'], 's', 'GO', 'OK', folder=self.tmp)
        self.assertEqual(self.text(), BASE)

    def test_parallel_adds_all_land(self):
        names = ['P%02d.md' % i for i in range(12)]
        procs = [self.run_cli(name) for name in names]
        for proc in procs:
            proc.communicate()
            self.assertEqual(proc.returncode, 0)
        rows, _ = indexfmt.parse(self.text())
        listed = indexfmt.listed_files(rows)
        for name in names:
            self.assertEqual(listed.count(name), 1)
        self.assertEqual(len(listed), 2 + len(names))

    def test_multi_file_row(self):
        index_add.add(self.index, 't', ['M.md', 'M_evidence.tgz'], 's', 'RESULT', 'PARTIAL')
        rows, _ = indexfmt.parse(self.text())
        self.assertIn(['M.md', 'M_evidence.tgz'], [r.files for r in rows])


if __name__ == '__main__':
    unittest.main()
