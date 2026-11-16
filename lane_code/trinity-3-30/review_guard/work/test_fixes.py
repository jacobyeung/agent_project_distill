"""Failing tests for REVIEW_VERDICT_GUARD.md fixes 1-3 (run: python -I -s -B test_fixes.py)."""
import re, sys, tarfile, unittest
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit')
sys.path.insert(0, str(K/'report'))
import guard_read as G
FIX = str(K/'report/tests/fixtures/R1_544_COMPACT.json')
class Fix1(unittest.TestCase):
    def test_step544_as_candidate_refuses(self):
        rc = G.main(['--candidate', FIX, '--step544', FIX, '--out', '/scratch/jjyeung/orch_n30/review_guard/work/fix1_out'])
        self.assertEqual(rc, 3, 'step 544 passed as candidate yields a PASS verdict')
class Fix2(unittest.TestCase):
    def test_diff_md_lists_every_new_module(self):
        names = {Path(m).name for m in tarfile.open(K/'build2/out/code_g2.tar').getnames()
                 if m.endswith('.py') and not m.startswith(('sj/', './sj/', 'reviewed/', './reviewed/'))}
        listed = set(re.findall(r'`out/guard_kit/([a-z_]+\.py)`', (K/'build2/out/DIFF.md').read_text()))
        self.assertEqual(sorted(names - listed), [])
class Fix3(unittest.TestCase):
    def test_return_carries_candidate_stage_receipts(self):
        t = K/'build2/out/rehearsal/whole/6bcb6c74a28545f48cb24a05517ca0c6/fetched/result.tar.gz'
        names = {Path(n).name for n in tarfile.open(t).getnames()}
        self.assertTrue({'CANDIDATE_STAGE.json', 'CHECK.json'} <= names, 'export stage/checker receipts not returned')
if __name__ == '__main__': unittest.main(verbosity=2)
