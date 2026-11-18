import base64, io, re, sys, tarfile
from pathlib import Path
K = Path('/scratch/jjyeung/orch_n30/review_h1read5/work/k')
sys.path.insert(0, str(K/'kit/launcher'))
import orchard_launcher as L
out = Path(sys.argv[1]); types = None if sys.argv[2] == 'none' else sys.argv[2]
config = L.prepare('a000000001', out/'prepared', 544, run='469ddece', generation='mstop', families=['a7'], types=types)
script = (out/'prepared/BATCH.sh').read_text()
raw = base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'", script)[1])
def extract(raw, root):
    with tarfile.open(fileobj=io.BytesIO(raw)) as a:
        for m in a:
            assert m.isfile(), m.name
            p = root/m.name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(a.extractfile(m).read())
            print('FILE', m.name, oct(m.mode))
extract(raw, out/'r')
extract((out/'r/bootstrap/payload.tar.gz').read_bytes(), out/'r')
print('PACKAGE', config['spec']['package'], config['spec']['interpreters'])
