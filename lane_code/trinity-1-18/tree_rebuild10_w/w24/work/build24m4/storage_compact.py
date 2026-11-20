from common import *
import gzip,lzma
records=[]
# Re-encode completed retained evidence; every original byte hash remains checked.
for filename in ('RETENTION.json','RETENTION_REPORTS.json','RETENTION_COMPLETE.json'):
 value=J.load(D/filename)
 for row in value['records']:
  p=L/row['retained']
  if p.stat().st_size<500000 or row.get('encoding')=='xz':continue
  raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==row['original_sha256']
  packed=lzma.compress(raw,preset=6)
  if len(packed)>=p.stat().st_size:continue
  assert lzma.decompress(packed)==raw
  target=p.with_suffix('.xz');p.write_bytes(packed);p.rename(target)
  row.update(retained=str(target.relative_to(L)),encoding='xz',compressed_bytes=len(packed))
 replace(D/filename,json.dumps(value,sort_keys=True,indent=2)+'\n')
# These are superseded fixture-only capsule bytes, with no live consumers.
for p in (L/'attic/build24m4/work/build24m4').rglob('*.json'):
 if p.stat().st_nlink!=1 or p.stat().st_size<100000:continue
 raw=p.read_bytes();packed=lzma.compress(raw,preset=6)
 if len(packed)>=len(raw):continue
 assert lzma.decompress(packed)==raw
 target=p.with_suffix('.json.xz');p.write_bytes(packed);p.rename(target)
 records.append(dict(original=str(p.relative_to(L)),retained=str(target.relative_to(L)),original_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),compressed_bytes=len(packed),encoding='xz'))
J.write(D/'RETENTION_ATTIC.json',dict(lossless_verified=True,files_deleted=0,records=records))
print('Completed evidence compacted without deletion')
