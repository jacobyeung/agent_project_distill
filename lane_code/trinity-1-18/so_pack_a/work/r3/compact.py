"""Losslessly encode completed disposable fixtures without deleting files."""
from pathlib import Path
import gzip,hashlib,json,sys
root=Path(__file__).resolve().parents[2];manifest=root/'work/r3/STORAGE.json'
data=json.loads(manifest.read_text());seen={};saved=0
for row in data['files']:
    if row['encoding']=='PACKREF1':seen[row['sha256']]=row['reference']
for name in sys.argv[1:]:
    base=(root/'work/r3'/name).resolve();assert str(base).startswith(str(root/'work/r3')+'/')
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.stat().st_size<16384 or p.suffix in ('.log',) or p.name in ('CHECK.json','POSITIVE.json','RESULT.json','D_CHECK.json','BUILD.json','0.json','1.json'):continue
        raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        if p.suffix in ('.tgz','.tgz2','.tgz3') and len(raw)>1000000:
            if sha not in seen:seen[sha]=str(p.relative_to(root));continue
            if seen[sha]==str(p.relative_to(root)):continue
            row=dict(path=str(p.relative_to(root)),encoding='PACKREF1',reference=seen[sha],sha256=sha,bytes=len(raw))
            encoded=(json.dumps({k:v for k,v in row.items() if k!='path'},sort_keys=True)+'\n').encode()
        else:
            if raw[:2]==b'\x1f\x8b':continue
            encoded=gzip.compress(raw,compresslevel=1,mtime=0)
            if len(encoded)>len(raw)*.8:continue
            assert gzip.decompress(encoded)==raw
            row=dict(path=str(p.relative_to(root)),encoding='gzip in place',sha256=sha,bytes=len(raw),compressed_bytes=len(encoded))
        p.write_bytes(encoded);data['files'].append(row);saved+=len(raw)-len(encoded)
data['saved_bytes']+=saved;manifest.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(additional_saved_bytes=saved,total_saved_bytes=data['saved_bytes'])))
