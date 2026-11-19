from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';A=L/'attic/build24b'
p=B/'tests23b.py';shutil.copyfile(p,A/'tests23b.py');s=p.read_text().replace("D=L/'work/build24/proofs/tests23b'","D=L/'work/build24b/proofs/tests23b'");p.write_text(s)
p=D/'suites.py';s=p.read_text().replace("records=[]\nfor name,path in steps:","records=json.loads((D/'SUITES.json').read_text()) if (D/'SUITES.json').exists() else []\nfor name,path in steps:\n if any(x['name']==name and x['returncode']==0 for x in records):continue")
s=s.replace("records.append(dict(name=name,returncode=r.returncode))", "records=[x for x in records if x['name']!=name];records.append(dict(name=name,returncode=r.returncode))");p.write_text(s)
