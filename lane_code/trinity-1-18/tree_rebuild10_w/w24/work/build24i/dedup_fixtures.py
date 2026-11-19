"""Retain duplicate generated fixture payloads once, with reversible references."""
from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24i'
blobs=D/'fixture_blobs';blobs.mkdir(exist_ok=True)
manifest=json.loads((D/'COMPRESSED_FIXTURES.json').read_text())
seen={};records=[]
for entry in manifest['files']:
 p=L/entry['path'];raw=p.read_bytes()
 if len(raw)<100_000:continue
 h=hashlib.sha256(raw).hexdigest();blob=blobs/(h+'.gz')
 if h not in seen:
  assert not blob.exists();p.rename(blob);seen[h]=blob
 reference=p.with_name(p.name+'.ref.json')
 value=dict(retained_blob=str(blob.relative_to(L)),compressed_sha256=h,compressed_bytes=len(raw),original_sha256=entry['sha256'],original_bytes=entry['bytes'])
 # Every unique byte remains in its blob. The generated duplicate becomes a
 # reference representation, just as the package uses tar hardlinks.
 if p.exists():p.rename(reference)
 reference.write_text(json.dumps(value,sort_keys=True)+'\n')
 assert hashlib.sha256(blob.read_bytes()).hexdigest()==h
 records.append(dict(original_compressed_path=entry['path'],reference=str(reference.relative_to(L)),**value))
(D/'DEDUP_FIXTURES.json').write_text(json.dumps(dict(files=records,unique_blobs=len(seen),method='Every generated compressed payload is retained in fixture_blobs; references reconstruct the exact recorded paths and hashes. No file-deletion operation is used.'),indent=2)+'\n')
print('retained',len(records),'fixture payloads in',len(seen),'unique blobs')
