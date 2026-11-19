from pathlib import Path
import gzip,json,hashlib,sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e"
records=[]
# Preserve completed fixture bytes losslessly, without removing any file.
for folder in ("path_tests",):
 for p in (D/folder).rglob("*"):
  if not p.is_file() or p.is_symlink() or p.stat().st_size<100000 or p.suffix==".gz":continue
  raw=p.read_bytes();z=gzip.compress(raw,compresslevel=6,mtime=0)
  if len(z)>=len(raw):continue
  target=p.with_name(p.name+".gz");assert not target.exists();p.write_bytes(z);p.rename(target)
  records.append(dict(path=str(p.relative_to(L)),compressed=str(target.relative_to(L)),bytes=len(raw),gzip_bytes=len(z),sha256=hashlib.sha256(raw).hexdigest()))
(D/"COMPRESSED_EVIDENCE.json").write_text(json.dumps(records,indent=2)+"\n")
print("lossless fixture evidence",len(records),"saved",sum(r["bytes"]-r["gzip_bytes"] for r in records))
