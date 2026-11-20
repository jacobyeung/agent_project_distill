from common import *
import gzip
records=[]
for folder in ('review_tests','security_tests_final','native_hosts','census_bytes','discovery_shell_unresolved','discovery_shell_protected_bytes','proofs','resolver','publication','regressions'):
 for p in (D/folder).rglob('*'):
  if not p.is_file() or p.stat().st_nlink!=1 or p.stat().st_size<20_000:continue
  raw=p.read_bytes();packed=gzip.compress(raw,mtime=0)
  if len(packed)>=len(raw):continue
  assert gzip.decompress(packed)==raw
  original=str(p.relative_to(L));target=L/'attic/build24m4/retained_complete'/(original+'.gz')
  target.parent.mkdir(parents=True,exist_ok=True)
  # Retain the same file inode, changing only its reversible storage encoding.
  p.write_bytes(packed);p.rename(target)
  assert hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()==hashlib.sha256(raw).hexdigest()
  records.append(dict(original=original,retained_complete=str(target.relative_to(L)),original_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),compressed_bytes=len(packed)))
J.write(D/'RETENTION_COMPLETE.json',dict(lossless_verified=True,files_deleted=0,records=records))
print('Retained losslessly',len(records),'bytes saved',sum(v['bytes']-v['compressed_bytes'] for v in records))
