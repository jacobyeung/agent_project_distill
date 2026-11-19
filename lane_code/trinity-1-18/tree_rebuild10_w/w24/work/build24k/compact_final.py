"""Retain completed fixture payloads without deleting files."""
from pathlib import Path
import gzip,hashlib,json,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';blobroot=D/'fixture_blobs_3';blobroot.mkdir(exist_ok=True)
protected={'upload','scanners','retained_evidence','evidence_a','evidence_b','fixture_blobs','fixture_blobs_2','fixture_blobs_3'}
records=[];known={p.stem:p for root in ('fixture_blobs','fixture_blobs_2','fixture_blobs_3') for p in (D/root).glob('*.gz')}
for root in sorted(D.iterdir()):
 if not root.is_dir() or root.name in protected:continue
 for p in sorted(root.rglob('*')):
  if p.is_symlink() or not p.is_file() or p.suffix=='.gz' or p.name.endswith('.ref.json') or p.stat().st_size<100000:continue
  raw=p.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
  if len(packed)>=len(raw):continue
  h=hashlib.sha256(raw).hexdigest();ch=hashlib.sha256(packed).hexdigest();blob=known.get(ch,blobroot/(ch+'.gz'))
  if not blob.exists():blob.write_bytes(packed);known[ch]=blob
  assert hashlib.sha256(gzip.decompress(blob.read_bytes())).hexdigest()==h
  ref=p.with_name(p.name+'.gz3.ref.json');assert not ref.exists()
  original=str(p.relative_to(L));p.rename(ref)
  temp=ref.with_name(ref.name+'.pending');entry=dict(original=original,retained_blob=str(blob.relative_to(L)),original_sha256=h,original_bytes=len(raw),compressed_sha256=ch,compressed_bytes=len(packed))
  temp.write_text(json.dumps(entry,sort_keys=True)+'\n');os.replace(temp,ref);records.append(entry)
(D/'COMPRESSED_FIXTURES_3.json').write_text(json.dumps(dict(files=records,method='Lossless retained blobs; atomic replacement preserves shared original inodes.'),indent=2)+'\n')
# Deduplicate identical generated files by inode while preserving every path and byte.
seen={};linked=0
for p in sorted(D.rglob('*')):
 if p.is_symlink() or not p.is_file() or p.stat().st_size<4096:continue
 h=hashlib.sha256(p.read_bytes()).hexdigest();key=(h,p.stat().st_mode&0o777)
 if key in seen:
  source=seen[key]
  if source.stat().st_ino==p.stat().st_ino:continue
  temp=p.with_name(p.name+'.dedup_pending');os.link(source,temp);os.replace(temp,p);linked+=1
 else:seen[key]=p
unique={};total=0
for p in D.rglob('*'):
 if not p.is_symlink() and p.is_file():
  s=p.stat();unique[(s.st_dev,s.st_ino)]=s.st_size
total=sum(unique.values())
(D/'STORAGE.json').write_text(json.dumps(dict(build24k_unique_bytes=total,compressed_payloads=len(records),deduplicated_paths=linked,method='Lossless gzip plus hardlinks; all original paths represented and every unique byte retained.'),indent=2)+'\n')
print('Retained',len(records),'payloads;',linked,'deduplicated paths;',total,'unique bytes')
