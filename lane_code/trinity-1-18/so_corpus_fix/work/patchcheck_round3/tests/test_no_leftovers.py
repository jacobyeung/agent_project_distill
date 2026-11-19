import os, subprocess, sys, tempfile, unittest
TOOL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched'

def listing(d):
    out = set()
    for r, ds, fs in os.walk(d):
        for f in fs:
            out.add(os.path.join(r, f))
    return out

@unittest.skipUnless(os.path.isdir(SRC), 'real return absent')
class NoLeftovers(unittest.TestCase):
    def test_full_ingest_leaves_only_outputs(self):
        before = listing(os.path.join(TOOL, 't'))
        out = tempfile.mkdtemp(prefix='noleft-', dir='/dev/shm')
        r = subprocess.run([sys.executable, os.path.join(TOOL, 'ingest_read.py'), 'ingest', '--source', SRC,
                            '--read-id', 'noleft', '--set', 'facing-twins', '--vehicle', 'direct', '--out', out],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(listing(os.path.join(TOOL, 't')) - before, set())
        left = sorted(os.path.relpath(p, out) for p in listing(out))
        bad = [p for p in left if os.path.basename(p).startswith('.corpus-') or p.endswith('.sqlite')]
        self.assertEqual(bad, [], left)

if __name__ == '__main__':
    unittest.main()
