import hashlib,json,tarfile,sys
from pathlib import Path
p=Path(__file__).resolve().parent
c=json.loads((p/'0.json').read_text())
assert hashlib.sha256((p/'0.tgz').read_bytes()).hexdigest()==c['payload_sha256']
if len(sys.argv)>1 and sys.argv[1]=='fetch':
    raw=(p/'a/7.py').read_bytes()
    manifest=json.loads((p/'PACKAGE.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=manifest['files']['a/7.py']:
        raise ValueError('Fetch helper differs')
    sys.argv[1:]=['--package',str(p)]+sys.argv[2:]
    exec(compile(raw,str(p/'a/7.py'),'exec'),dict(__name__='__main__',__file__=str(p/'a/7.py')))
    raise SystemExit(0)
with tarfile.open(p/'0.tgz') as t:
    exec(compile(t.extractfile('8.py').read(),__file__,'exec'))

