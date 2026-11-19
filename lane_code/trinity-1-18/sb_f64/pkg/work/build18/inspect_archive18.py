from pathlib import Path
import tarfile,json
L=Path(__file__).resolve().parents[2];B=L/'work/build18'
d=json.loads((B/'DELIVERY.json').read_text());rows=[]
with tarfile.open(L/d['path'],'r:gz') as archive:
    for m in archive:
        if not m.isfile():rows.append(dict(name=m.name,type=m.type.decode(),linkname=m.linkname))
(B/'proofs/integrity/NONREGULAR.json').write_text(json.dumps(dict(archive=d,nonregular=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
