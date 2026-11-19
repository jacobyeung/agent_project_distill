from pathlib import Path
import gzip,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23c';A=L/'attic/build23c'
records=[]
for label,name in [('operator','work/build21/proofs/operator/SCAN.json'),('naming21c','work/build21g/regression21c/SCAN.json'),('naming21d','work/build21g/regression21d/SCAN.json')]:
 p=L/name;raw=p.read_bytes();assert 1_000_000<len(raw)<15_000_000
 encoded=gzip.compress(raw,compresslevel=9,mtime=0);assert gzip.decompress(encoded)==raw
 target=A/(label+'_SCAN.json.gz');assert not target.exists()
 p.rename(target);target.write_bytes(encoded)
 assert hashlib.sha256(gzip.decompress(target.read_bytes())).digest()==hashlib.sha256(raw).digest()
 records.append(dict(source=name,retained=str(target.relative_to(L)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(encoded),compressed_sha256=hashlib.sha256(encoded).hexdigest(),verified=True))
(D/'RETAINED_SCANS.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(saved_bytes=sum(x['bytes']-x['compressed_bytes'] for x in records),files=len(records))))
