"""Seal current files, counting shared model hardlinks only once for disk growth."""
import hashlib
import json
import os
from pathlib import Path

K=Path(__file__).resolve().parents[1]
before=json.loads((K/'tmp/b4/before_sizes.json').read_text())
old={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (K/'SHA256SUMS').read_text().splitlines()}
size_path=K/'BUILD4_SIZE.json';log=K/'logs/b4/seal.json'
size_path.write_text('{}\n');log.write_text('{}\n')
files={str(p.relative_to(K)):p for p in sorted(K.rglob('*')) if p.is_file() and p!=K/'SHA256SUMS'}
prior_inodes={}
for name in before:
    path=K/name
    if path.is_file():
        s=path.stat();prior_inodes[(s.st_dev,s.st_ino)]=max(prior_inodes.get((s.st_dev,s.st_ino),0),before[name]['size'])
projected_index_bytes=sum(67+len(n.encode()) for n in files)
# Carry only unchanged old temporary hashes; hash every source and modified/new artifact.
reused={}
for name,path in files.items():
    s=path.stat();baseline=before.get(name)
    if name.startswith('tmp/') and name in old and baseline and s.st_size==baseline['size'] and s.st_mtime_ns==baseline['mtime']:
        reused[(s.st_dev,s.st_ino)]=old[name]
fresh=sum(not (n.startswith('tmp/') and (p.stat().st_dev,p.stat().st_ino) in reused) for n,p in files.items())
report=dict(checksum_files=len(files),fresh_hashes=fresh,retained_unchanged_tmp_hashes=len(files)-fresh,
            reviewer_sha256='eed915be8bf3c08de67045ff7adbfc3ab899d244da0d942be03e5a28f8657239')
for _ in range(8):
    unique={};new_hardlinks=0
    for name,path in files.items():
        s=path.stat();key=(s.st_dev,s.st_ino);unique[key]=max(unique.get(key,0),s.st_size)
        if name not in before and key in prior_inodes:new_hardlinks+=s.st_size
    st=os.statvfs(K)
    added=sum(max(0,size-prior_inodes.get(key,0)) for key,size in unique.items())
    added+=max(0,projected_index_bytes-before['SHA256SUMS']['size'])
    sizes=dict(added_unique_file_bytes=added,shared_existing_payload_bytes=new_hardlinks,
               positive_apparent_growth_bytes=sum(max(0,p.stat().st_size-before.get(n,{}).get('size',0)) for n,p in files.items()),
               free_bytes=st.f_bavail*st.f_frsize,limit_bytes=100000000,
               minimum_free_bytes=200*1024**3,
               policy='Shared fixture payloads are hardlinks to unchanged retained files; count each inode once.')
    assert sizes['added_unique_file_bytes']<sizes['limit_bytes'],sizes
    assert sizes['free_bytes']>=sizes['minimum_free_bytes'],sizes
    size_path.write_text(json.dumps(sizes,indent=2)+'\n')
    report['size']=sizes
    log.write_text(json.dumps(report,indent=2)+'\n')
hashes={}
for name,path in files.items():
    s=path.stat();key=(s.st_dev,s.st_ino)
    if name.startswith('tmp/') and key in reused:hashes[name]=reused[key]
    else:
        with path.open('rb') as handle:hashes[name]=hashlib.file_digest(handle,'sha256').hexdigest()
text=''.join(hashes[n]+'  '+n+'\n' for n in sorted(hashes))
assert len(text.encode())==projected_index_bytes
(K/'SHA256SUMS').write_text(text)
assert set(hashes)=={str(p.relative_to(K)) for p in K.rglob('*') if p.is_file() and p!=K/'SHA256SUMS'}
print(json.dumps(report,indent=2))
