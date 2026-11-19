"""Restore a small named fixture alias from the inherited sealed upload bytes."""
from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
name,h=sys.argv[1:];source=L/'work/build21/upload/u'/h;target=L/name
assert target.is_relative_to(L) and not target.exists()
raw=source.read_bytes();assert len(raw)<5_000_000 and hashlib.sha256(raw).hexdigest()==h
target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
p=D/'FIXTURE_PREREQUISITES.json';value=json.loads(p.read_text())
value.append(dict(path=name,source=str(source.relative_to(L)),bytes=len(raw),sha256=h))
p.write_text(json.dumps(value,indent=2)+'\n');print(name,len(raw),h)
