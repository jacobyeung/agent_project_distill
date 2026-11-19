"""Losslessly encode finished scratch fixtures; no files are removed."""
from pathlib import Path
import gzip,hashlib,io,json,sys
root=Path(__file__).resolve().parents[2];manifest=root/'work/r4/STORAGE.json'
data=json.loads(manifest.read_text()) if manifest.exists() else dict(saved_bytes=0,files=[])
blocks=root/'work/r4/blocks';blocks.mkdir(exist_ok=True)
def compress(raw):
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',compresslevel=1,mtime=0) as stream:stream.write(raw)
    return out.getvalue()
seen={};known={}
for m in (root/'work/r3/STORAGE.json',manifest):
    if m.exists():
        for row in json.loads(m.read_text())['files']:
            known[row['path']]=row
            if row['encoding']=='PACKREF1':seen[row['sha256']]=row['reference']
def compact(base):
    saved=0;base=Path(base).resolve();assert str(base).startswith(str(root/'work')+'/')
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.is_symlink() or p.stat().st_size<16384 or p.suffix=='.log' or p.name in ('CHECK.json','POSITIVE.json','RESULT.json','D_CHECK.json','BUILD.json','0.json','1.json'):continue
        raw=p.read_bytes();original_size=len(raw)
        old=known.get(str(p.relative_to(root)))
        if old and old['encoding']=='gzip in place' and raw[:2]==b'\x1f\x8b':
            raw=gzip.decompress(raw)
            if p.suffix not in ('.py','.sh') or not any(len(line)>16384 for line in raw.splitlines(True)):continue
        if raw.startswith(b'PACKLINES1\n'):continue
        sha=hashlib.sha256(raw).hexdigest()
        if p.suffix in ('.tgz','.tgz2','.tgz3') and len(raw)>1000000:
            if sha not in seen:seen[sha]=str(p.relative_to(root));continue
            if seen[sha]==str(p.relative_to(root)):continue
            row=dict(path=str(p.relative_to(root)),encoding='PACKREF1',reference=seen[sha],sha256=sha,bytes=len(raw))
            encoded=(json.dumps({k:v for k,v in row.items() if k!='path'},sort_keys=True)+'\n').encode()
        elif p.suffix in ('.py','.sh') and any(len(line)>16384 for line in raw.splitlines(True)):
            refs=[]
            for line in raw.splitlines(True):
                if len(line)<16384:refs.append(dict(text=line.decode('utf-8')));continue
                key=hashlib.sha256(line).hexdigest();block=blocks/(key+'.gz')
                if not block.exists():block.write_bytes(compress(line))
                refs.append(dict(block=key))
            row=dict(path=str(p.relative_to(root)),encoding='PACKLINES1',sha256=sha,bytes=len(raw))
            encoded=b'PACKLINES1\n'+json.dumps(dict(row,lines=refs),sort_keys=True).encode()+b'\n'
        else:
            if raw[:2]==b'\x1f\x8b':continue
            encoded=compress(raw)
            if len(encoded)>len(raw)*.8:continue
            assert gzip.decompress(encoded)==raw
            row=dict(path=str(p.relative_to(root)),encoding='gzip in place',sha256=sha,bytes=len(raw),compressed_bytes=len(encoded))
        p.write_bytes(encoded);data['files'].append(row);known[row['path']]=row;saved+=original_size-len(encoded)
    data['saved_bytes']+=saved;manifest.write_text(json.dumps(data,indent=2)+'\n');return saved
if __name__=='__main__':
    for name in sys.argv[1:]:print(json.dumps(dict(path=name,saved_bytes=compact(name))))
