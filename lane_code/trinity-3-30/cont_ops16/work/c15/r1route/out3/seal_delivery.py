from pathlib import Path
import gzip,hashlib,io,json,tarfile
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
records=[]
for label,k in [('A','b1'),('B','b2')]:
 d=R/label
 with tarfile.open(d/'1.tgz') as t:files={m.name:t.extractfile(m).read() for m in t}
 for n in ['3.py','a/4.py','a/7.py']:files[n]=(d/'package'/n).read_bytes()
 m=json.loads(files['PACKAGE.json'])
 for n in ['3.py','a/4.py','a/7.py']:m['files'][n]=sha(files[n])
 files['PACKAGE.json']=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode()
 (d/'PACKAGE.json').write_bytes(files['PACKAGE.json']);(d/'package/PACKAGE.json').write_bytes(files['PACKAGE.json'])
 b=io.BytesIO()
 with gzip.GzipFile(fileobj=b,mode='wb',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w') as t:
   for n,raw in sorted(files.items()):
    entry=tarfile.TarInfo(n);entry.size=len(raw);entry.mode=0o600;t.addfile(entry,io.BytesIO(raw))
 (d/'1.tgz').write_bytes(b.getvalue())
 p=d/'o_place.sh';s=p.read_text();import re
 s=re.sub(r"(printf '%s  %s\\n' )[0-9a-f]{64}",lambda x:x[1]+sha(b.getvalue()),s);p.write_text(s)
 # Update only mutable delivery helpers in the release gate fixture.
 gate=R/'gates/release'/k
 for n in ['3.py','a/4.py','a/7.py','PACKAGE.json']:(gate/'package'/n).write_bytes(files[n])
 for n in ['fill_export.py','fetch_return.py','PACKAGE.json']:(gate/n).write_bytes((d/n).read_bytes())
 records.append(dict(package=label,files={n:dict(sha256=sha((d/n).read_bytes()),prior_sha256=sha((R.parent/'out2'/label/n).read_bytes()),identical=(d/n).read_bytes()==(R.parent/'out2'/label/n).read_bytes()) for n in ['0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json']}))
(R/'BYTE_IDENTITY.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
