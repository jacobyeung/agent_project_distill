import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';records=[]
for entry in json.loads((L/'work/build6/PACKET_INPUTS.json').read_text()):
 source=L/entry['source'];target=L/entry['target'].replace('work/build6/','work/n1fix3/')
 assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256']
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():target.symlink_to(source)
 assert target.resolve()==source.resolve()
 records.append(dict(entry,target=str(target.relative_to(L)),mechanism='read-only source reference; no row copy'))
(B/'PACKET_INPUTS.json').write_text(json.dumps(records,indent=2)+'\n')
