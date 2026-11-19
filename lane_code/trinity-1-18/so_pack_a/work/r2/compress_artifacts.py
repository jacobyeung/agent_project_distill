"""Lossless in-place archival encoding of completed local test artifacts; no deletion."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[2];m=root/'work/r2/STORAGE.json';data=json.loads(m.read_text());saved=0
for name in sys.argv[1:]:
 base=(root/'work'/name).resolve();assert str(base).startswith(str(root/'work')+'/')
 for p in sorted(base.rglob('*')):
  if not p.is_file() or p.suffix in ('.gz','.log') or p.name in ('CHECK.json','POSITIVE.json','RESULT.json','D_CHECK.json','BUILD.json','0.json','1.json') or p.stat().st_size<16384:continue
  raw=p.read_bytes()
  if raw[:2]==b'\x1f\x8b':continue
  zipped=gzip.compress(raw,compresslevel=1,mtime=0)
  if len(zipped)>len(raw)*.8:continue
  assert gzip.decompress(zipped)==raw
  data['files'].append(dict(path=str(p.relative_to(root)),encoding='gzip in place',original_bytes=len(raw),original_sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(zipped)))
  p.write_bytes(zipped);saved+=len(raw)-len(zipped)
data['saved_bytes']+=saved;m.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(dict(additional_saved_bytes=saved,total_saved_bytes=data['saved_bytes'])))
