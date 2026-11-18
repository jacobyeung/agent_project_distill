import base64, io, re, sys, tarfile
from pathlib import Path
src = Path(sys.argv[1]); out = Path(sys.argv[2])
script = (src/'BATCH.sh').read_text()
raw = base64.b64decode(re.search(r"raw=base64.b64decode\('([^']+)'", script)[1])
def extract(raw, root):
    with tarfile.open(fileobj=io.BytesIO(raw)) as a:
        for m in a:
            assert m.isfile(), m.name
            p = root/m.name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(a.extractfile(m).read())
extract(raw, out); extract((out/'bootstrap/payload.tar.gz').read_bytes(), out)
