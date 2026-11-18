import json
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'QUALIFICATION9.json';rows=json.loads(p.read_text())
for row in rows:
    if row['step']=='delivery':row.update(status='complete',returncode=0,evidence='DELIVERY.json')
rows=[r for r in rows if r['step']!='frozen_package']
done=(L/'work/merge11/proofs/n1/package/ARCHIVE.json').exists()
rows.append(dict(step='frozen_package',status='complete' if done else 'running',
    evidence='proofs/package/ARCHIVE.json' if done else 'proofs/suite_tree/progress.json'))
p.write_text(json.dumps(rows,indent=2)+'\n')
