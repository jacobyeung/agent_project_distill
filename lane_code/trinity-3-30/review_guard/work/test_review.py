import json, copy, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import guard_core as C
REF = json.load(open('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/inputs/reference.json'))

class Proof(unittest.TestCase):
    def run_proof(self, mutate):
        rows = copy.deepcopy(REF); mutate(rows)
        published, cand = [], []
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d)/'PROOF.json'
            with self.assertRaises(ValueError):
                C.pipeline(REF, lambda keys: rows, lambda keys: cand.append(keys) or [], [r['key'] for r in REF],
                           [r['key'] for r in REF][:10], Path(d), published.append)
            rec = json.load(open(dest))
        self.assertEqual(rec['status'], 'FAIL'); self.assertFalse(rec['backend_identity_proven'])
        self.assertEqual(published, [dest]); self.assertEqual(cand, [])
    def test_token(self): self.run_proof(lambda r: r[19]['decode']['tokens'].__setitem__(-1, r[19]['decode']['tokens'][-1]+1))
    def test_call_response(self): self.run_proof(lambda r: r[7]['decode']['calls'][0].__setitem__('response', r[7]['decode']['calls'][0]['response']+' '))
    def test_call_dropped(self): self.run_proof(lambda r: r[3]['decode']['calls'].pop())
    def test_answer(self): self.run_proof(lambda r: r[12]['decode'].__setitem__('text', r[12]['decode']['text'].replace('</think>', '</think> ')))
    def test_score(self): self.run_proof(lambda r: r[0]['scores'].__setitem__('released_answer', 0.123))
    def test_order(self): self.run_proof(lambda r: r.reverse())
    def test_missing(self): self.run_proof(lambda r: r.pop())
    def test_pass_publishes_proof_then_canary_before_tail(self):
        keys=[r['key'] for r in REF]; calls=[]; pub=[]
        def cand(k):
            calls.append(('read', list(k), [p.name for p in pub]))
            return [dict(key=x, arm='unflagged', scores={'answer':1.0}, called=True, no_answer=False) for x in k]
        with tempfile.TemporaryDirectory() as d:
            C.pipeline(REF, lambda k: copy.deepcopy(REF), cand, keys, keys[:10], Path(d), pub.append)
        self.assertEqual(calls[0][2], ['PROOF.json']); self.assertEqual(calls[1][2], ['PROOF.json','CANARY.json'])

class Digest(unittest.TestCase):
    def test_int_key_collapses(self):
        # canonical JSON cannot see int-vs-str keys; the journal (JSON) is admitted, so content admitted equals journal
        self.assertEqual(C.digest({1:'a'}), C.digest({'1':'a'}))
    def test_types_distinct(self):
        self.assertNotEqual(C.digest(1), C.digest(1.0)); self.assertNotEqual(C.digest(True), C.digest(1))
        self.assertNotEqual(C.digest(0.0), C.digest(-0.0)); self.assertNotEqual(C.digest(0.1), C.digest(0.1000000000000001))
    def test_nan_refused(self):
        with self.assertRaises(ValueError): C.digest(float('nan'))
if __name__ == '__main__': unittest.main(verbosity=1)
