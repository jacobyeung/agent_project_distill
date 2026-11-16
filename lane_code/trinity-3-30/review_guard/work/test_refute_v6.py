"""Refute attempts on guard_read 5424e41c (no wrong PASS). Run: python -I -s -B test_refute_v6.py"""
import copy, json, sys, tempfile, unittest
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/review_guard/work/v6/report')
sys.path.insert(0, str(W/'tests')); sys.argv[1:] = []
import test_guard_read as T
G = T.G
def fx(): return T.Fixture()
def run_main(f, extra=(), out=None):
    c, b = f.write('cand.json', f.cand), f.write('base.json', f.base)
    return G.main(['--candidate', str(c), '--step544', str(b), '--candidate-artifact', T.CAND_ART, '--out', str(out or f.dir/'o')] + list(extra))
class Strict(unittest.TestCase):
    def mut(self, fn):
        f = fx(); [fn(r) for r in f.cand['arms']['unflagged']]; return run_main(f)
    def test_called_string_true_refuses(self):
        self.assertEqual(self.mut(lambda r: r.__setitem__('called', 'true')), 3)
    def test_no_answer_string_false_refuses(self):
        self.assertEqual(self.mut(lambda r: r.__setitem__('no_answer', 'false')), 3)
    def test_no_answer_missing_refuses(self):
        self.assertEqual(self.mut(lambda r: r.pop('no_answer', None)), 3)
    def test_refusal_string_refuses(self):
        self.assertEqual(self.mut(lambda r: r.__setitem__('refusal', 'yes')), 3)
    def test_decode_list_refuses(self):
        self.assertEqual(self.mut(lambda r: r.__setitem__('decode', [])), 3)
    def test_decode_text_int_refuses(self):
        self.assertEqual(self.mut(lambda r: r.__setitem__('decode', {'text': 5})), 3)
    def test_mixed_checkpoint_refuses(self):
        f = fx(); f.cand['arms']['unflagged'][0]['checkpoint_sha256'] = 'd' * 64
        self.assertEqual(run_main(f), 3)
    def test_seed_override_refuses(self):
        self.assertEqual(run_main(fx(), ['--seed', '1']), 3)
    def test_draws_override_refuses(self):
        self.assertEqual(run_main(fx(), ['--draws', '20000']), 3)
    def test_wrong_baseline_refuses(self):
        f = fx(); [r.__setitem__('checkpoint_sha256', 'e' * 64) for r in f.base['arms']['unflagged']]
        self.assertEqual(run_main(f), 3)
class Advisory(unittest.TestCase):
    """Expected to fail today; non-blocking (not reachable from RUN.md)."""
    def test_self_pair_requires_step544(self):
        self.assertEqual(run_main(fx(), ['--self-pair']), 3, '--self-pair accepted a non-544 candidate; report labels a real read as a self-pair')
    def test_refusal_clears_stale_report(self):
        f = fx(); out = f.dir/'o'
        self.assertEqual(run_main(f, out=out), 0)
        self.assertEqual(run_main(f, ['--seed', '1'], out=out), 3)
        self.assertFalse((out/'GUARD_READ.json').exists(), 'stale PASS report survives a later refusal into the same --out')
    def test_string_score_refuses(self):
        f = fx(); [r['scores'].__setitem__(G.label(r), '1') for r in f.cand['arms']['unflagged']]
        self.assertEqual(run_main(f), 3, 'string score accepted')
if __name__ == '__main__': unittest.main(verbosity=2)
