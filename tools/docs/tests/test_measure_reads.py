"""measure_reads.py: whole files, partial reads, stat sizes and the CLI."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
sys.path.insert(0, DOCS)
import measure_reads  # noqa: E402

TEXT = '# T\nintro\n## Goal\ng1\n## Live runs\nr1\n## Archive\nold\n'


class MeasureTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'page.md')
        with open(self.path, 'w') as handle:
            handle.write(TEXT)

    def test_modes(self):
        self.assertEqual(measure_reads.measure_spec('a=' + self.path), ('a', len(TEXT)))
        above = TEXT.split('## Archive')[0]
        self.assertEqual(measure_reads.measure_spec('b=%s#above=## Archive' % self.path)[1],
                         len(above))
        self.assertEqual(measure_reads.measure_spec('c=%s#sections=Goal' % self.path)[1],
                         len('## Goal\ng1\n'))
        self.assertEqual(measure_reads.measure_spec('d=@1234'), ('d', 1234))

    def test_totals_and_tokens(self):
        result = measure_reads.measure([('x', ['a=@4000', 'b=@400'])], 4.0)
        self.assertEqual(result[0]['bytes'], 4400)
        self.assertEqual(result[0]['tokens'], 1100)

    def test_bad_spec_refused(self):
        with self.assertRaises(ValueError):
            measure_reads.measure_spec(self.path)
        with self.assertRaises(ValueError):
            measure_reads.measure_spec('a=%s#lines=1-2' % self.path)

    def test_cli_saving_line(self):
        out = subprocess.check_output([sys.executable, os.path.join(DOCS, 'measure_reads.py'),
                                       '--set', 'today', 'a=@8000', '--set', 'after', 'a=@2000'])
        self.assertIn(b'saving today -> after: 6000 bytes, ~1500 tokens (75%)', out)


if __name__ == '__main__':
    unittest.main()
