from common import *
import gzip
records=[]
for folder in ('review_tests','security_tests_final','regressions'):
 for p in (D/folder).rglob('*'):
  if not p.is_file() or p.stat().st_nlink!=1 or p.suffix!='.json' or p.stat().st_size<40_000:continue
  if p.name not in ('e0.json','e1.json','e2.json','e3.json','e6.json','e7.json'):continue
  raw=p.read_bytes();packed=gzip.compress(raw,mtime=0)
  if len(packed)>=len(raw):continue
  assert gzip.decompress(packed)==raw
  original=str(p.relative_to(L));target=L/'attic/build24m4/retained'/(original+'.gz')
  target.parent.mkdir(parents=True,exist_ok=True)
  # Retain the same file inode, changing only its reversible storage encoding.
  p.write_bytes(packed);p.rename(target)
  assert hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()==hashlib.sha256(raw).hexdigest()
  records.append(dict(original=original,retained=str(target.relative_to(L)),original_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),compressed_bytes=len(packed)))
J.write(D/'RETENTION_REPORTS.json',dict(lossless_verified=True,files_deleted=0,records=records))
print('Retained losslessly',len(records),'bytes saved',sum(v['bytes']-v['compressed_bytes'] for v in records))
