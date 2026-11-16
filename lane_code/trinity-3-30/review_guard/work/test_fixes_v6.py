"""REVIEW_VERDICT_GUARD fixes 1-4 rerun against guard_read 5424e41c and code_g2 6024aa2b (paths adapted, assertions kept).
Run: python -I -s -B test_fixes_v6.py  (env RESULT_DIR = rehearsal whole/<hex>)."""
import os, re, sys, tarfile, unittest, json, hashlib
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit')
W = Path('/scratch/jjyeung/orch_n30/review_guard/work')
sys.path.insert(0, str(W/'v6/report'))
import guard_read as G
FIX = str(W/'v6/report/tests/fixtures/R1_544_COMPACT.json')
class Fix1(unittest.TestCase):
    def test_source_pinned(self):
        self.assertEqual(hashlib.sha256(Path(G.__file__).read_bytes()).hexdigest(), '5424e41c68fc1918386c62865a68d7b3c1af2802f2800b1f0455837568a3cd11')
    def test_step544_as_candidate_refuses(self):
        rc = G.main(['--candidate', FIX, '--step544', FIX, '--candidate-artifact', G.STEP544_ARTIFACT, '--out', str(W/'fix1_v6_out')])
        self.assertEqual(rc, 3, 'step 544 passed as candidate yields a PASS verdict')
        self.assertFalse((W/'fix1_v6_out').exists())
    def test_missing_artifact_refuses(self):
        with self.assertRaises(SystemExit) as e:
            G.main(['--candidate', FIX, '--step544', FIX, '--out', str(W/'fix1_v6_out')])
        self.assertNotEqual(e.exception.code, 0)
    def test_empty_artifact_refuses(self):
        self.assertEqual(G.main(['--candidate', FIX, '--step544', FIX, '--candidate-artifact', '', '--out', str(W/'fix1_v6_out')]), 3)
    def test_run_md_no_self_pair_and_binds_config(self):
        cmd = [l for l in (K/'build2/out/RUN.md').read_text().splitlines() if 'guard_read.py --candidate' in l]
        self.assertEqual(len(cmd), 1); self.assertNotIn('--self-pair', cmd[0]); self.assertIn('--candidate-artifact "$CANDIDATE_ARTIFACT"', cmd[0])
class Fix2(unittest.TestCase):
    def test_diff_md_lists_every_new_module(self):
        names = {Path(m).name for m in tarfile.open(K/'build2/out/code_g2.tar').getnames()
                 if m.endswith('.py') and not m.startswith(('sj/', './sj/', 'reviewed/', './reviewed/'))}
        listed = set(re.findall(r'`out/guard_kit/([a-z_]+\.py)`', (K/'build2/out/DIFF.md').read_text()))
        self.assertEqual(sorted(names - listed), [])
class Fix3(unittest.TestCase):
    def test_return_carries_candidate_stage_receipts(self):
        d = Path(os.environ['RESULT_DIR'])
        tars = sorted(d.rglob('result.tar.gz'))
        self.assertTrue(tars, 'no result.tar.gz in ' + str(d))
        for t in tars:
            names = {Path(n).name for n in tarfile.open(t).getnames()}
            self.assertTrue({'CANDIDATE_STAGE.json', 'CHECK.json'} <= names, 'export stage/checker receipts not returned: %s' % t)
class Fix4(unittest.TestCase):
    def test_no_pv_paced_fetch(self):
        t = (K/'build2/out/RUN.md').read_text()
        self.assertNotIn('pv -q -L', t); self.assertNotIn('pv -L', t)
        for l in t.splitlines():
            if re.search(r'\b(gsutil cat|curl|ssh|OSSH)\b.*(result\.tar|EXIT\.json|closure\.tar|\.done|packet\.tar)', l) and not l.startswith('governed_transfer'):
                self.fail('ungoverned transfer line: ' + l)
if __name__ == '__main__': unittest.main(verbosity=2)
