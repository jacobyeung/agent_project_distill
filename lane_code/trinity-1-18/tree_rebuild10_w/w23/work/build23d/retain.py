"""Retain completed scan and unit-test capsule evidence in compressed attic files."""
from pathlib import Path
import gzip,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23d';A=L/'attic/build23d'
paths=[L/p for p in ('work/build23/SCAN.json','work/build21g/SCAN.json','work/build21e/SCAN.json',
 'work/build21e/regression21c/SCAN.json','work/build21e/regression21d/SCAN.json','work/build21d/SCAN.json','work/build21c/SCAN.json')]
paths += [L/f'work/build23/proofs/unit/kit{i}/k/s.json' for i in range(6)]
records=[]
for p in paths:
 assert p.is_file() and 3_000_000<p.stat().st_size<15_000_000
 raw=p.read_bytes();encoded=gzip.compress(raw,compresslevel=6,mtime=0)
 assert gzip.decompress(encoded)==raw
 target=A/'retained'/p.relative_to(L);target=target.with_suffix(target.suffix+'.gz')
 target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
 p.rename(target);target.write_bytes(encoded)
 assert hashlib.sha256(gzip.decompress(target.read_bytes())).digest()==hashlib.sha256(raw).digest()
 records.append(dict(source=str(p.relative_to(L)),retained=str(target.relative_to(L)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(encoded),compressed_sha256=hashlib.sha256(encoded).hexdigest(),verified=True))
(D/'RETAINED.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(files=len(records),saved_bytes=sum(v['bytes']-v['compressed_bytes'] for v in records))))
