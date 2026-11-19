from pathlib import Path
import gzip,hashlib,json,os
L=Path(__file__).resolve().parents[2];D=L/'work/build23d';A=L/'attic/build23d'
suites=json.loads((D/'SUITES.json').read_text());assert len(suites)==5 and all(v['successful'] for v in suites)
records=[]
for p in [L/'work/build21/proofs/operator/SCAN.json',D/'regression21c/SCAN.json',D/'regression21d/SCAN.json']:
 raw=p.read_bytes();assert 1_000_000<len(raw)<15_000_000
 encoded=gzip.compress(raw,compresslevel=6,mtime=0);assert gzip.decompress(encoded)==raw
 target=A/'test_scans'/p.relative_to(L);target=target.with_suffix('.json.gz');target.parent.mkdir(parents=True,exist_ok=True)
 assert not target.exists();p.rename(target);target.write_bytes(encoded)
 assert hashlib.sha256(gzip.decompress(target.read_bytes())).digest()==hashlib.sha256(raw).digest()
 records.append(dict(source=str(p.relative_to(L)),retained=str(target.relative_to(L)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(encoded),verified=True))
(D/'RETAINED_TEST_SCANS.json').write_text(json.dumps(records,indent=2)+'\n')
total=0
for root,dirs,files in os.walk(L):
 if Path(root)==L/'work':dirs[:]=[n for n in dirs if n!='build23b']
 for name in files:
  p=Path(root)/name
  if not p.is_symlink():total+=p.stat().st_size
print(json.dumps(dict(saved_bytes=sum(v['bytes']-v['compressed_bytes'] for v in records),workspace_bytes_excluding_active_replay=total)))
