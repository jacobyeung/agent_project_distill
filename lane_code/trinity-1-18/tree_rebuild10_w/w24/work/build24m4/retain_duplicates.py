from common import *
import gzip,lzma
archive=next(D.glob('t_*.tar'));h=J.sha(archive);size=archive.stat().st_size;count=0
for filename in ('RETENTION.json','RETENTION_REPORTS.json','RETENTION_COMPLETE.json'):
 value=J.load(D/filename)
 for row in value['records']:
  if row['original_sha256']!=h:continue
  p=L/row['retained'];raw=p.read_bytes()
  decoded=lzma.decompress(raw) if row.get('encoding')=='xz' else gzip.decompress(raw)
  assert hashlib.sha256(decoded).hexdigest()==h and len(decoded)==size
  ref=dict(schema='lossless-sha256-reference-v1',path=str(archive.relative_to(L)),sha256=h,bytes=size)
  target=p.with_suffix('.ref.json');body=(json.dumps(ref,sort_keys=True,indent=2)+'\n').encode()
  p.write_bytes(body);p.rename(target)
  row.update(retained=str(target.relative_to(L)),encoding='sha256-reference',compressed_bytes=len(body));count+=1
 replace(D/filename,json.dumps(value,sort_keys=True,indent=2)+'\n')
print('Duplicate completed fixture archives retained by verified source reference',count)
