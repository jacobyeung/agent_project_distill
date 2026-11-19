"""Retain completed synthetic payloads as reversible gzip blobs and references."""
from pathlib import Path
import gzip,hashlib,json,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';blobs=D/'fixture_blobs_2';blobs.mkdir(exist_ok=True)
roots=[D/n for n in ('mode_r_test_v4','mode_r_test_v5','proofs','integration_final','sequence_verified','sequence_completed')]
records=[]
for root in roots:
 if not root.exists():continue
 for p in sorted(root.rglob('*')):
  if p.is_symlink() or not p.is_file() or p.stat().st_size<100000 or p.suffix=='.gz':continue
  raw=p.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
  if len(packed)>=len(raw):continue
  h=hashlib.sha256(raw).hexdigest();ch=hashlib.sha256(packed).hexdigest();blob=blobs/(ch+'.gz')
  if not blob.exists():blob.write_bytes(packed)
  assert hashlib.sha256(gzip.decompress(blob.read_bytes())).hexdigest()==h
  ref=p.with_name(p.name+'.gz.ref.json');assert not ref.exists()
  original=str(p.relative_to(L));p.rename(ref)
  # Atomic replacement breaks any inode shared with a preexisting fixture.
  temp=ref.with_name(ref.name+'.pending')
  entry=dict(original=original,retained_blob=str(blob.relative_to(L)),original_sha256=h,original_bytes=len(raw),compressed_sha256=ch,compressed_bytes=len(packed))
  temp.write_text(json.dumps(entry,sort_keys=True)+'\n');os.replace(temp,ref)
  records.append(entry)
(D/'COMPRESSED_FIXTURES_2.json').write_text(json.dumps(dict(files=records,method='Lossless gzip blobs and per-path references; atomic replacement preserves external hardlinks.'),indent=2)+'\n')
print('Retained',len(records),'fixture payloads; blob bytes',sum(p.stat().st_size for p in blobs.iterdir()))
