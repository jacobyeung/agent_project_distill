"""Index new/modified local files without rehashing retained model artifacts."""
import hashlib
import json
import os
from pathlib import Path

K=Path(__file__).resolve().parents[1]
baseline=K/'tmp/b3/before_sizes.json'
before=json.loads(baseline.read_text())
cutoff=baseline.stat().st_mtime_ns
old={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (K/'SHA256SUMS').read_text().splitlines()}
log=K/'logs/b3/seal.json'
# Include this log before calculating the complete index.
log.write_text('{}\n')
files={str(p.relative_to(K)):p for p in sorted(K.rglob('*')) if p.is_file() and p!=K/'SHA256SUMS'}
reuse={n for n,p in files.items() if n in old and n.startswith('tmp/') and not n.startswith('tmp/b3/')
       and p.stat().st_mtime_ns<cutoff and p.stat().st_size==before.get(n)}
log.write_text(json.dumps(dict(indexed_files=len(files),retained_tmp_hashes=len(reuse),
    fresh_hashes=len(files)-len(reuse),policy='Retain prior hashes only for unchanged pre-build temporary artifacts; hash all new files and all code/data/docs.'),indent=2)+'\n')
projected_index_bytes=sum(67+len(n.encode()) for n in files)
for _ in range(3):
    sizes={n:p.stat().st_size for n,p in files.items()}
    sizes['SHA256SUMS']=projected_index_bytes
    st=os.statvfs(K)
    size=dict(new_file_bytes=sum(v for n,v in sizes.items() if n not in before),
        positive_size_growth_bytes=sum(max(0,v-before.get(n,0)) for n,v in sizes.items()),
        total_regular_file_bytes=sum(sizes.values()),free_bytes=st.f_bavail*st.f_frsize,limit_bytes=300000000)
    assert size['positive_size_growth_bytes']<size['limit_bytes']
    assert size['free_bytes']>=200*1024**3
    (K/'BUILD3_SIZE.json').write_text(json.dumps(size,indent=2)+'\n')
hashes={}
for n,p in files.items():
    if n in reuse:hashes[n]=old[n]
    else:
        with p.open('rb') as f:hashes[n]=hashlib.file_digest(f,'sha256').hexdigest()
text=''.join(hashes[n]+'  '+n+'\n' for n in sorted(hashes))
assert len(text.encode())==projected_index_bytes
(K/'SHA256SUMS').write_text(text)
assert set(hashes)=={str(p.relative_to(K)) for p in K.rglob('*') if p.is_file() and p!=K/'SHA256SUMS'}
print(json.dumps(dict(size=size,checksum_files=len(hashes),fresh_hashes=len(hashes)-len(reuse))))
