"""Retain completed fixture bytes as gzip files; never remove a file."""
from pathlib import Path
import gzip,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24i'
names=('proofs','resolver','review_tests','security_tests','security_tests_final','live_tests','runtime_verified','armed_fixture','armed_fixture_final','sequence_final','copier_tests','copier_go_tests','signal_final_tests','session_tests')
roots=[D/n for n in names]+[L/'attic/build24i'/n for n in ('resolver600_first','review_tests_first','sequence_first','sequence_second')]
records=[]
for root in roots:
 if not root.exists():continue
 for p in sorted(root.rglob('*')):
  if p.is_symlink() or not p.is_file() or p.stat().st_size<100_000 or p.suffix=='.gz':continue
  raw=p.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
  if len(packed)>=len(raw):continue
  target=p.with_name(p.name+'.gz')
  assert not target.exists(),target
  old=str(p.relative_to(L));p.rename(target);target.write_bytes(packed)
  assert gzip.decompress(target.read_bytes())==raw
  records.append(dict(original=old,path=str(target.relative_to(L)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(packed)))
(D/'COMPRESSED_FIXTURES.json').write_text(json.dumps(dict(files=records,original_bytes=sum(r['bytes'] for r in records),compressed_bytes=sum(r['compressed_bytes'] for r in records),method='In-place reversible gzip after tests; no deletion. Decompress to the recorded original path to inspect a fixture.'),indent=2)+'\n')
print('retained',len(records),'compressed fixture files')
