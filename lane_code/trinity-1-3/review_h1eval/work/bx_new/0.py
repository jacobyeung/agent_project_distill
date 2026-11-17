import sys,json,hashlib,tarfile
from pathlib import Path
r=Path(sys.argv[1]);c=json.loads((r/'0.json').read_text())
a=Path('/project/community/jjyeung')/c['token']/'0.tgz'
assert hashlib.sha256(a.read_bytes()).hexdigest()==c['payload_sha256']
with tarfile.open(a) as t:
 for e in t:
  if not e.name.startswith('orchard_h10/'):continue
  if not e.isfile() or '..' in Path(e.name).parts:raise ValueError('Unsafe input')
  p=r/'p'/e.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(e).read())
sys.path.insert(0,str(r/'p'))
from orchard_h10.job import main
main(r)
