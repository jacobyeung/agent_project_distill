from common import *
import gzip
records=[]
for folder in ('native_hosts','discovery_shell_protected','discovery_shell_protected_final'):
 for p in (D/folder).rglob('*.json'):
  if p.is_symlink() or not p.is_file() or p.stat().st_nlink!=1 or p.stat().st_size<100000:continue
  raw=p.read_bytes();packed=gzip.compress(raw,mtime=0)
  if len(packed)>=len(raw):continue
  assert gzip.decompress(packed)==raw
  original=str(p.relative_to(L));target=L/'attic/build24m3/retained_final'/(original+'.gz')
  target.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(packed);p.rename(target)
  assert hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()==hashlib.sha256(raw).hexdigest()
  records.append(dict(original=original,retained=str(target.relative_to(L)),original_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),compressed_bytes=len(packed)))
J.write(D/'RETENTION_FINAL.json',dict(lossless_verified=True,files_deleted=0,records=records))
print('Retained losslessly',len(records),'bytes saved',sum(v['bytes']-v['compressed_bytes'] for v in records))
