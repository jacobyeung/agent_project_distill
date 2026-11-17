"""Reviewer refute tests for fix 2 (H1 deployment binding)."""
import hashlib, importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/review_h1read2/work/k')
H1 = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1')
sys.path.insert(0, str(K/'kit/launcher'))
import binding as NEW

def load_old():
    src = (K/'kit/launcher/binding.py').read_bytes().replace(b"'17c4ffa4':'x_3fdda0fb'", b"'17c4ffa4':'x_4b3114cf'")
    d = tempfile.mkdtemp(); p = Path(d)/'binding_old.py'; p.write_bytes(src)
    spec = importlib.util.spec_from_file_location('binding_old', p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m, hashlib.sha256(src).hexdigest()

def outcome(f, *a):
    try: return ('ok', json.dumps(f(*a), sort_keys=True))
    except Exception as e: return ('err', type(e).__name__, str(e))

class Refute(unittest.TestCase):
    def test_old_is_sealed_predecessor_and_only_line6_differs(self):
        old, h = load_old()
        before = json.loads((K/'evidence/FIX2_BEFORE_PINS.json').read_bytes())
        self.assertEqual(hashlib.sha256((K/'evidence/FIX2_BEFORE_PINS.json').read_bytes()).hexdigest()[:8], 'c2bb6c9e')
        self.assertEqual(h, before['kit/launcher/binding.py'])

    def test_d0_identical_across_inputs(self):
        old, _ = load_old()
        cases = [('359fcc3c', s, g, ns) for s in (0, 1, 99, 100, 137, 200, 201, '100', 100.0) for g in (None, 'mstop', 'mstopB', 'mstopC', 'm100', 'x') for ns in ('8865619b', 'zz')]
        for c in cases:
            self.assertEqual(outcome(old.expected, *c), outcome(NEW.expected, *c), c)
        for s in (100, 200):
            v = NEW.expected('359fcc3c', s)
            self.assertEqual(v['done'], f'/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m{s}.done')
            self.assertEqual(outcome(old.validate, dict(v)), outcome(NEW.validate, dict(v)))
            raw = f'{v["object"]} 123 {"a"*64}\n'.encode()
            self.assertEqual(outcome(old.parse, raw, dict(v)), outcome(NEW.parse, raw, dict(v)))

    def test_h1_only_new_root_old_refused(self):
        old, _ = load_old()
        for s, g in [(100, None), (200, None)] + [(s, g) for s in (1, 137, 200) for g in NEW.STOPS]:
            v = NEW.expected('17c4ffa4', s, g)
            self.assertTrue(v['done'].startswith('/project/community/jjyeung/okh7/x_3fdda0fb/o/'))
            if v['claim']: self.assertTrue(v['claim'].startswith('/project/community/jjyeung/okh7/x_3fdda0fb/o/'))
            stale = old.expected('17c4ffa4', s, g)
            self.assertIn('x_4b3114cf', stale['done'])
            with self.assertRaisesRegex(ValueError, 'Export binding differs'): NEW.validate(stale)
            mixed = dict(v); mixed['done'] = stale['done']
            with self.assertRaises(ValueError): NEW.validate(mixed)
        self.assertNotIn(b'4b3114cf', (K/'kit/launcher/binding.py').read_bytes())
        for f in (K/'kit').rglob('*'):
            if f.is_file(): self.assertNotIn(b'4b3114cf', f.read_bytes(), str(f))

    def test_production_exporter_receipts_parse(self):
        # Run the production tk_persist_exports (h1/build/fx/b/c.sh, sha c519e62b) on a fake deployment.
        c = (H1/'build/fx/b/c.sh').read_text()
        self.assertEqual(hashlib.sha256(c.encode()).hexdigest()[:8], 'c519e62b')
        start = c.index('tk_persist_exports() {'); end = c.index('\n}\n', start)+3
        fn = c[start:end]
        d = Path(tempfile.mkdtemp()); HM = d/'x_3fdda0fb'; NR = d/'runs'; S = d/'s'
        (HM/'o').mkdir(parents=True); (HM/'b').mkdir(); S.mkdir()
        (HM/'b/gcsput.py').write_text('import sys; sys.exit(0)\n')
        sess = {f'q8/8865619b/17c4ffa4_{m}.tar.part0{i}-of-04': 'u' for m in ('m100', 'm200') for i in range(4)}
        (HM/'sess.json').write_text(json.dumps(sess))
        for m in ('m100', 'm200', 'm137', 'm150'):
            (NR/'17c4ffa4'/m).mkdir(parents=True); (NR/'17c4ffa4'/m/'artifact.json').write_text('{"m":"%s"}' % m)
        script = f'set -euo pipefail\nK=8865619b\nHM={HM}\nHX={HM}\nNR={NR}\nS={S}\ntk_step(){{ echo "$*"; }}\n{fn}\ntk_persist_exports\n'
        r = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        root = '/project/community/jjyeung/okh7/x_3fdda0fb/o/'
        def check(step, gen):
            v = NEW.expected('17c4ffa4', step, gen)
            done = HM/'o'/Path(v['done']).name
            self.assertEqual(v['done'], root+done.name)
            claim = (HM/'o'/Path(v['claim']).name).read_bytes() if v['claim'] else None
            got = NEW.parse(done.read_bytes(), v, claim)
            tar = Path(str(S)+'/../up')/f'17c4ffa4_m{step}.tar'
            self.assertEqual(got['bytes'], tar.stat().st_size)
            self.assertEqual(got['sha256'], hashlib.sha256(tar.read_bytes()).hexdigest())
            return got
        self.assertEqual(check(100, None)['object'], 'q8/8865619b/17c4ffa4_m100.tar')
        check(200, None)
        claims = {g: (HM/'o'/f'gcs_17c4ffa4_{g}.claim').read_bytes() for g in ('mstop', 'mstopB') }
        gen137 = [g for g, b in claims.items() if b == b'm137\n'][0]
        self.assertEqual(check(137, gen137)['object'], f'q8/8865619b/17c4ffa4_{gen137}.tar')
        gen150 = [g for g, b in claims.items() if b == b'm150\n'][0]
        check(150, gen150)
        other = 'mstopB' if gen137 == 'mstop' else 'mstop'
        with self.assertRaises(ValueError): check(137, other)

if __name__ == '__main__':
    unittest.main()
