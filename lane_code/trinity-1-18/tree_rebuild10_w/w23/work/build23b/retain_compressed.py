"""Retain superseded fixture bytes as gzip files without removing any file."""
from pathlib import Path
import gzip,hashlib,json,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
source=L/'work/build23/proofs/capacity/400/q/retained_0';dest=L/'attic/build23b/capacity_retained_400'
assert source.is_dir() and not dest.exists()
assert shutil.disk_usage('/scratch').free>85*1024**3
source.rename(dest)
records=[]
for p in sorted(dest.glob('prepare_*/*/rows.sqlite')):
 raw=p.read_bytes();encoded=gzip.compress(raw,compresslevel=6,mtime=0)
 assert gzip.decompress(encoded)==raw
 record=dict(source=str(source/p.relative_to(dest)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(encoded),compressed_sha256=hashlib.sha256(encoded).hexdigest())
 # Replace this retained artifact with its lossless encoding, then name that encoding.
 p.write_bytes(encoded);target=p.with_suffix(p.suffix+'.gz');p.rename(target)
 assert hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest()==record['sha256']
 record['retained_path']=str(target);records.append(record)
(D/'RETAINED_STORAGE.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(files=len(records),retained_original_bytes=sum(x['bytes'] for x in records),compressed_bytes=sum(x['compressed_bytes'] for x in records))))
