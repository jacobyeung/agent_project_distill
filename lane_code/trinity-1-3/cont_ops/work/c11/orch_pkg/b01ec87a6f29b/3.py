import hashlib,json,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))
