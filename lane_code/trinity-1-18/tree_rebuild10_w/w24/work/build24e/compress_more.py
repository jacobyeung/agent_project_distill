from pathlib import Path
import gzip,json,hashlib
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";record=json.loads((D/"COMPRESSED_EVIDENCE.json").read_text())
for folder in (L/"attic/build24e/resolver600_used",):
 for p in folder.rglob("*"):
  if not p.is_file() or p.is_symlink() or p.stat().st_size<50000 or p.suffix==".gz":continue
  raw=p.read_bytes();z=gzip.compress(raw,6,mtime=0)
  if len(z)>=len(raw):continue
  target=p.with_name(p.name+".gz");assert not target.exists();p.write_bytes(z);p.rename(target)
  record.append(dict(path=str(p.relative_to(L)),compressed=str(target.relative_to(L)),bytes=len(raw),gzip_bytes=len(z),sha256=hashlib.sha256(raw).hexdigest()))
(D/"COMPRESSED_EVIDENCE.json").write_text(json.dumps(record,indent=2)+"\n")
print("saved total",sum(r["bytes"]-r["gzip_bytes"] for r in record))
