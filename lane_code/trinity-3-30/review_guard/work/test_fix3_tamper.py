"""Fix 3 refute: verify_return (code_g2 6024aa2b transport.py) on the rehearsal ffdbd8e3 return and tampered copies."""
import hashlib, io, json, sys, tarfile, tempfile, unittest
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_guard/work/g2v6')
import transport as T
W = Path('/scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build2/out/rehearsal/whole/ffdbd8e316a04872a588fcb8eeabc96a/fetched')
EXIT = json.loads((W/'EXIT.json').read_text()); PLAN = EXIT['plan_sha256']
def rebuild(mutate):
    d = Path(tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/review_guard/work/tmp'))
    members = {}
    with tarfile.open(W/'result.tar.gz') as t:
        for m in t.getmembers():
            if m.isfile(): members[m.name] = t.extractfile(m).read()
    mutate(members)
    p = d/'result.tar.gz'
    with tarfile.open(p, 'w:gz') as t:
        for n, b in sorted(members.items()):
            i = tarfile.TarInfo(n); i.size = len(b); t.addfile(i, io.BytesIO(b))
    raw = p.read_bytes(); rec = dict(EXIT, archive=dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return rec, p
class Fix3Tamper(unittest.TestCase):
    def test_original_verifies(self):
        T.verify_return(EXIT, W/'result.tar.gz', PLAN, allow_fixture=True)
    def test_rebuilt_unchanged_verifies(self):
        T.verify_return(*rebuild(lambda m: None), PLAN, allow_fixture=True)
    def bad(self, fn):
        rec, p = rebuild(fn)
        with self.assertRaises(ValueError): T.verify_return(rec, p, PLAN, allow_fixture=True)
    def test_missing_check(self): self.bad(lambda m: m.pop('CHECK.json'))
    def test_missing_stage(self): self.bad(lambda m: m.pop('CANDIDATE_STAGE.json'))
    def test_missing_inventory(self): self.bad(lambda m: m.pop('STAGE_RECEIPTS.json'))
    def test_stage_byte_changed(self): self.bad(lambda m: m.__setitem__('CANDIDATE_STAGE.json', m['CANDIDATE_STAGE.json'].replace(b'complete', b'complexe')))
    def test_check_unverified_resealed(self):
        def f(m):
            c = json.loads(m['CHECK.json']); c['status'] = 'FAILED'; b = json.dumps(c).encode(); m['CHECK.json'] = b
            s = json.loads(m['STAGE_RECEIPTS.json']); s['members']['CHECK.json'] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
            m['STAGE_RECEIPTS.json'] = json.dumps(s).encode()
        self.bad(f)
    def test_step544_inventory(self):
        def f(m):
            s = json.loads(m['STAGE_RECEIPTS.json']); s['step'] = 544; m['STAGE_RECEIPTS.json'] = json.dumps(s).encode()
        self.bad(f)
if __name__ == '__main__': unittest.main(verbosity=2)
